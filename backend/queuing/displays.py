"""Display administration — MP-39 (specification MD-11, MD-17, MD-18).

The public board (``queuing/display.py``) can only read.  This module is the
**write** half of the multi-display DQDS: one capability, three routes, one
audit event per write, and a refusal that is recorded like every other denial.

Design rules enforced here
--------------------------
1. **Scope comes from the token.**  ``organization_id`` is taken from the
   authenticated principal and the branch is validated against it, never read
   from the request body as an assertion of authority.  A branch belonging to
   another tenant is a non-disclosing **404**; a *scope target* (department,
   room, doctor) that is not this branch's is a 422 only after the branch itself
   has been proven to be the caller's, so the refusal is a validation message
   and not an oracle about another tenant.
2. **One capability, no new role.**  ``queue.display.manage`` sits inside the
   existing ``queue.*`` namespace, so organization and branch administrators
   hold it through the matrix they already have.  ``DELEGABLE_CAPABILITIES`` is
   unchanged: a display is branch configuration, not a delegable front-desk act.
3. **The check happens here, not only in a dependency.**  A denial must produce
   a ``queue.display.denied`` row (MD-19 / AC-21).  A
   ``Depends(require_permission(...))`` refusal is answered before the route
   body runs, so the capability is decided inside the route through the same
   ``check_granted`` the dependency uses, and the refusal is recorded.
4. **One denial, one row.**  The row is written *and* the response carries
   ``X-AMSDP-Denial-Audit``, which ``common/denial_audit.py`` strips and uses to
   skip its generic ``request.denied`` row.  Without that marker a single
   refusal would be counted twice (Q-2 §10).
5. **Nothing is deleted.**  ``status='disabled'`` is the retirement path, and a
   disabled display 404s exactly like an unknown one — which is how the public
   route already treats it.
6. **Codes are the public handle.**  Lower-case ``[a-z0-9-]``, unique per branch
   (``uq_display_branch_code``), so ``?display=<code>`` stays the only thing a
   screen needs and two screens cannot collide.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from common.audit import record_audit
from common.auth import AuthContext, branch_accessible, get_current_user
from common.database import SessionFactory
from common.denial_audit import DOMAIN_DENIAL_HEADER
from common.models import (Branch, Doctor, DoctorBranch, FacilityDepartment,
                           FacilityRoom, QueueDisplay, QueueDisplayDoctor)
from common.permissions import check_granted

router = APIRouter(prefix="/api/v1/queue/displays", tags=["display-admin"])

SERVICE = "queuing"

#: The capability that guards every route in this module.  It resolves through
#: the role matrix's ``queue.*`` entry — no role was added and the delegable set
#: is untouched.
DISPLAY_MANAGE = "queue.display.manage"

#: Audit action names (MD-19).
DENIED_ACTION = "queue.display.denied"
CREATED_ACTION = "queue.display.created"
UPDATED_ACTION = "queue.display.updated"

SCOPE_TYPES = ("branch", "doctors", "department", "room")
LANGUAGES = ("bn", "en")
STATUSES = ("active", "disabled")

_CODE_MAX = 40
_NAME_MAX = 120
_FOOTER_MAX = 160


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DisplayCreate(BaseModel):
    branch_id: str
    name: str
    code: str
    language: str = "bn"
    scope_type: str = "branch"
    department_id: Optional[str] = None
    room_id: Optional[str] = None
    doctor_ids: Optional[list[str]] = None
    footer_text: str = ""
    show_room: bool = True
    show_estimated_wait: bool = True
    show_waiting_count: bool = True


class DisplayUpdate(BaseModel):
    """Only the fields present are applied, so a partial edit cannot blank a column."""

    name: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    scope_type: Optional[str] = None
    department_id: Optional[str] = None
    room_id: Optional[str] = None
    doctor_ids: Optional[list[str]] = None
    footer_text: Optional[str] = None
    show_room: Optional[bool] = None
    show_estimated_wait: Optional[bool] = None
    show_waiting_count: Optional[bool] = None
    status: Optional[str] = None



# ---------------------------------------------------------------------------
# Denial accounting (MP-46 / MD-19)
# ---------------------------------------------------------------------------

def _denied(session, auth: AuthContext, *, status_code: int, reason: str,
            detail: str, display=None, branch_id: str = "") -> None:
    """Record one denied display action, then answer with *status_code*.

    The audit row is written **before** the refusal, so a denial is never lost.
    The response carries :data:`DOMAIN_DENIAL_HEADER`; the shared middleware
    strips it and skips its generic row, which is what keeps one denial to one
    row.  If the row cannot be written the header is omitted deliberately, so
    the generic recorder still leaves the denial visible somewhere.
    """
    recorded = False
    try:
        record_audit(session, service=SERVICE, org_id=auth.organization_id,
                     branch_id=branch_id or auth.branch_id or None,
                     action=DENIED_ACTION,
                     target_type="queue_display",
                     target_id=(display.id if display is not None else ""),
                     actor_id=auth.user_id, actor_role=auth.role,
                     after={"status": status_code,
                            "code": (display.code if display is not None else ""),
                            "request": detail},
                     reason=reason)
        session.commit()
        recorded = True
    except Exception:                       # pragma: no cover - defensive
        session.rollback()
    headers = {DOMAIN_DENIAL_HEADER: DENIED_ACTION} if recorded else None
    raise HTTPException(status_code, detail, headers=headers)


def _require_manage(session, auth: AuthContext) -> None:
    """``queue.display.manage``, or a recorded 403 (see rule 3 in the docstring)."""
    granted = [row["capability"] for row in auth.capability_grants]
    if not check_granted(DISPLAY_MANAGE, auth.role, granted):
        _denied(session, auth, status_code=403, reason="insufficient permissions",
                detail="insufficient permissions")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_CODE_ALLOWED = "abcdefghijklmnopqrstuvwxyz0123456789-"


def _clean_name(value) -> str:
    name = (value or "").strip()
    if not name:
        raise HTTPException(422, "name is required")
    if len(name) > _NAME_MAX:
        raise HTTPException(422, f"name must be at most {_NAME_MAX} characters")
    return name


def _clean_code(value) -> str:
    """Normalise to the lower-case public handle, or refuse the value.

    Deriving a code from the name is deliberately *not* offered: the code is
    printed beside a television and typed into its browser, so an operator must
    choose it and see it rather than inherit a transliteration.
    """
    code = (value or "").strip().lower()
    if not code:
        raise HTTPException(422, "code is required")
    if len(code) > _CODE_MAX:
        raise HTTPException(422, f"code must be at most {_CODE_MAX} characters")
    if any(c not in _CODE_ALLOWED for c in code) or code.startswith("-") \
            or code.endswith("-") or "--" in code:
        raise HTTPException(422, "code may contain only a-z, 0-9 and single hyphens")
    return code


def _clean_language(value) -> str:
    language = (value or "").strip().lower()
    if language not in LANGUAGES:
        raise HTTPException(422, f"language must be one of {', '.join(LANGUAGES)}")
    return language


def _clean_scope(value) -> str:
    scope = (value or "").strip().lower()
    if scope not in SCOPE_TYPES:
        raise HTTPException(422, f"scope_type must be one of {', '.join(SCOPE_TYPES)}")
    return scope


def _clean_status(value) -> str:
    status = (value or "").strip().lower()
    if status not in STATUSES:
        raise HTTPException(422, f"status must be one of {', '.join(STATUSES)}")
    return status


def _clean_footer(value) -> str:
    footer = (value or "").strip()
    if len(footer) > _FOOTER_MAX:
        raise HTTPException(422, f"footer_text must be at most {_FOOTER_MAX} characters")
    return footer


def _branch_or_404(session, auth: AuthContext, branch_id: str) -> Branch:
    """Resolve the caller's own branch, or fail closed with the shared 404."""
    branch = session.query(Branch).filter(
        Branch.id == branch_id,
        Branch.organization_id == auth.organization_id).first()
    if not branch or not branch_accessible(auth, branch.id):
        raise HTTPException(404, "not found")
    return branch


def _assert_scope_target(session, branch: Branch, scope: str,
                         department_id, room_id, doctor_ids) -> list[str]:
    """Validate the scope's target rows and return the doctor ids to store.

    Every target must belong to *this* branch and organization.  A foreign or
    missing target is a 422 (not a 404): by this point the caller has already
    proved it owns the branch, so the message discloses nothing new, and a
    half-configured display is precisely what would widen a public feed.
    """
    if scope == "department":
        if not department_id:
            raise HTTPException(422, "department_id is required for a department display")
        dept = session.query(FacilityDepartment).filter(
            FacilityDepartment.id == department_id,
            FacilityDepartment.branch_id == branch.id,
            FacilityDepartment.organization_id == branch.organization_id).first()
        if not dept:
            raise HTTPException(422, "department does not belong to this branch")
        return []
    if scope == "room":
        if not room_id:
            raise HTTPException(422, "room_id is required for a room display")
        room = session.query(FacilityRoom).filter(
            FacilityRoom.id == room_id,
            FacilityRoom.branch_id == branch.id,
            FacilityRoom.organization_id == branch.organization_id).first()
        if not room:
            raise HTTPException(422, "room does not belong to this branch")
        return []
    if scope == "doctors":
        ids = [str(d).strip() for d in (doctor_ids or []) if str(d).strip()]
        if not ids:
            raise HTTPException(422, "doctor_ids is required for a doctors display")
        # A display may only name doctors posted to this branch: an unposted id
        # would be a configuration error that silently shows nothing.
        posted = {row[0] for row in session.query(DoctorBranch.doctor_id).filter(
            DoctorBranch.branch_id == branch.id,
            DoctorBranch.doctor_id.in_(ids)).all()}
        owned = {row[0] for row in session.query(Doctor.id).filter(
            Doctor.id.in_(ids),
            Doctor.organization_id == branch.organization_id).all()}
        if [d for d in ids if d not in posted or d not in owned]:
            raise HTTPException(422, "doctor_id does not belong to this branch")
        return ids
    return []


def _code_taken(session, branch_id: str, code: str, exclude_id=None) -> bool:
    query = session.query(QueueDisplay).filter(
        QueueDisplay.branch_id == branch_id, QueueDisplay.code == code)
    if exclude_id:
        query = query.filter(QueueDisplay.id != exclude_id)
    return session.query(query.exists()).scalar()


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def _display_to_dict(session, display: QueueDisplay) -> dict:
    doctor_ids = [row[0] for row in session.query(QueueDisplayDoctor.doctor_id)
                  .filter(QueueDisplayDoctor.display_id == display.id).all()]
    return {
        "id": display.id,
        "organization_id": display.organization_id,
        "branch_id": display.branch_id,
        "name": display.name,
        "code": display.code,
        "language": display.language or "bn",
        "scope_type": display.scope_type or "branch",
        "department_id": display.department_id or "",
        "room_id": display.room_id or "",
        "doctor_ids": sorted(doctor_ids),
        "footer_text": display.footer_text or "",
        # ``False`` is the only value that suppresses, and the public route
        # applies the same rule — what the administrator sees is what the board
        # publishes.
        "show_room": display.show_room is not False,
        "show_estimated_wait": display.show_estimated_wait is not False,
        "show_waiting_count": display.show_waiting_count is not False,
        "status": display.status or "active",
        "created_at": display.created_at.isoformat() if display.created_at else "",
    }


def _audit(session, auth: AuthContext, action: str, display: QueueDisplay,
           *, before=None, after=None) -> None:
    record_audit(session, service=SERVICE, org_id=display.organization_id,
                 branch_id=display.branch_id, action=action,
                 target_type="queue_display", target_id=display.id,
                 actor_id=auth.user_id, actor_role=auth.role,
                 before=before, after=after)


def _set_doctors(session, display: QueueDisplay, doctor_ids: list[str]) -> None:
    """Replace the display's doctor membership in full (the editor sends the list)."""
    session.query(QueueDisplayDoctor).filter(
        QueueDisplayDoctor.display_id == display.id).delete(synchronize_session=False)
    for doctor_id in doctor_ids:
        session.add(QueueDisplayDoctor(display_id=display.id, doctor_id=doctor_id))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
def list_displays(branch_id: str = "",
                  auth: AuthContext = Depends(get_current_user)):
    """List this branch's displays.  Without ``branch_id``: the caller's own branch."""
    session = SessionFactory()
    try:
        _require_manage(session, auth)
        target = (branch_id or auth.branch_id or "").strip()
        if not target:
            # An organization administrator has no single branch; asking for one
            # explicitly is the only honest answer, and never a guess.
            raise HTTPException(422, "branch_id is required")
        branch = _branch_or_404(session, auth, target)
        displays = session.query(QueueDisplay).filter(
            QueueDisplay.branch_id == branch.id,
            QueueDisplay.organization_id == branch.organization_id
        ).order_by(QueueDisplay.name).all()
        return {"branch_id": branch.id, "can_manage": True,
                "displays": [_display_to_dict(session, d) for d in displays]}
    finally:
        session.close()


@router.post("", status_code=201)
def create_display(data: DisplayCreate,
                   auth: AuthContext = Depends(get_current_user)):
    """Create one configured board for the caller's own branch."""
    session = SessionFactory()
    try:
        _require_manage(session, auth)
        branch = _branch_or_404(session, auth, data.branch_id)
        code = _clean_code(data.code)
        scope = _clean_scope(data.scope_type)
        doctor_ids = _assert_scope_target(session, branch, scope,
                                          data.department_id, data.room_id,
                                          data.doctor_ids)
        if _code_taken(session, branch.id, code):
            raise HTTPException(409, "this branch already has a display with that code")
        display = QueueDisplay(
            organization_id=branch.organization_id,
            branch_id=branch.id,
            name=_clean_name(data.name),
            code=code,
            language=_clean_language(data.language),
            scope_type=scope,
            department_id=data.department_id if scope == "department" else None,
            room_id=data.room_id if scope == "room" else None,
            footer_text=_clean_footer(data.footer_text),
            show_room=bool(data.show_room),
            show_estimated_wait=bool(data.show_estimated_wait),
            show_waiting_count=bool(data.show_waiting_count),
            status="active",
            created_by=auth.user_id,
        )
        session.add(display)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            raise HTTPException(409, "this branch already has a display with that code")
        _set_doctors(session, display, doctor_ids)
        _audit(session, auth, CREATED_ACTION, display,
               after=_display_to_dict(session, display))
        session.commit()
        return _display_to_dict(session, display)
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()


@router.patch("/{display_id}")
def update_display(display_id: str, data: DisplayUpdate,
                   auth: AuthContext = Depends(get_current_user)):
    """Change one display.  Every real change is audited with before/after."""
    session = SessionFactory()
    try:
        _require_manage(session, auth)
        display = session.query(QueueDisplay).filter(
            QueueDisplay.id == display_id,
            QueueDisplay.organization_id == auth.organization_id).first()
        if not display or not branch_accessible(auth, display.branch_id):
            # Cross-branch and cross-tenant are indistinguishable from missing.
            _denied(session, auth, status_code=404, reason="display not found",
                    detail="not found", display=display)
        branch = _branch_or_404(session, auth, display.branch_id)
        before = _display_to_dict(session, display)

        scope = (_clean_scope(data.scope_type) if data.scope_type is not None
                 else (display.scope_type or "branch"))
        department_id = (data.department_id if data.department_id is not None
                         else display.department_id)
        room_id = data.room_id if data.room_id is not None else display.room_id
        doctor_ids = (data.doctor_ids if data.doctor_ids is not None
                      else before["doctor_ids"])
        if data.scope_type is not None:
            # Switching scope drops a target that no longer applies, so a room
            # display cannot keep a stale department (or the reverse).
            if scope != "department":
                department_id = None
            if scope != "room":
                room_id = None
        validated_doctors = _assert_scope_target(
            session, branch, scope, department_id, room_id, doctor_ids)

        if data.name is not None:
            display.name = _clean_name(data.name)
        if data.code is not None:
            code = _clean_code(data.code)
            if _code_taken(session, branch.id, code, exclude_id=display.id):
                raise HTTPException(409, "this branch already has a display with that code")
            display.code = code
        if data.language is not None:
            display.language = _clean_language(data.language)
        if data.status is not None:
            display.status = _clean_status(data.status)
        if data.footer_text is not None:
            display.footer_text = _clean_footer(data.footer_text)
        for field_name in ("show_room", "show_estimated_wait", "show_waiting_count"):
            value = getattr(data, field_name)
            if value is not None:
                setattr(display, field_name, bool(value))
        display.scope_type = scope
        display.department_id = department_id if scope == "department" else None
        display.room_id = room_id if scope == "room" else None

        if data.doctor_ids is not None or data.scope_type is not None:
            _set_doctors(session, display, validated_doctors)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            raise HTTPException(409, "this branch already has a display with that code")

        after = _display_to_dict(session, display)
        if before != after:
            _audit(session, auth, UPDATED_ACTION, display, before=before, after=after)
        session.commit()
        return after
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()

