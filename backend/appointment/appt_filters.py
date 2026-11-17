"""Shared search, filter and branch-scope predicates for the appointment reads.

AMSDP-CALENDAR-FILTER-01 — the fix for the defects recorded in
``docs/audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md`` (F-1 … F-7)
under owner decisions **D-1** (role-authorized branch scope everywhere) and
**D-2** (a search reaches every authorized date).

Three read routes answer the *same* question — *which appointments match what the
receptionist typed?* — for three presentations:

* ``GET /api/v1/appointments``          the week/day grid, one date window, no paging
* ``GET /api/v1/appointments/list``     the paged list view
* ``GET /api/v1/appointments/matches``  the date index that tells the grid where the
  matches *outside* its window are

When each route carried its own copy of the predicates, the calendar and the list
disagreed: the grid applied no branch scope and no search at all, while the list
applied both (F-1, F-3).  So the predicates live here, once.  Every read path
applies the same helpers in the same order:

1. **tenant** — ``organization_id`` from the token (the one tenant key);
2. **branch scope** — from the token, never from the request;
3. **filters** — doctor, status, explicit date bounds;
4. **search** — patient name, patient mobile (digits only), appointment id, token.

The order is not cosmetic: the branch scope is applied *before* anything the
caller sent, so a ``branch_id`` in the query string can only narrow a scope the
token already carries.  A caller asking for a branch outside its scope is
answered with a non-disclosing **404** — the same answer an unknown id gets —
exactly as ``require_branch_access`` does (``.clinerules`` §3).

Nothing in this module reads or changes an appointment's lifecycle, capacity or
token allocation: it only decides which rows a read may see.
"""

from datetime import date, datetime
from typing import Iterable, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, or_

from common.models import Appointment, Branch, Doctor, Patient

#: Longest search term the read paths accept.  Longer is a paste accident, not a
#: name — the bound keeps an unbounded LIKE pattern off the database.
SEARCH_MAX_LENGTH = 120

#: Most distinct dates ``/appointments/matches`` will return.  A search that
#: matches more dates than this is still counted correctly (``total``), but the
#: navigation list is capped so one query can never become an unbounded dump.
MATCH_DATE_LIMIT = 120


# ---------------------------------------------------------------------------
# Value validation — a typo must never silently widen or empty a result set
# ---------------------------------------------------------------------------

def parse_day(value: str, field: str) -> date:
    """``value`` as a :class:`date`, or **422**.

    A malformed bound is rejected rather than ignored: ignoring ``date_from``
    turns "this week" into "every appointment in the organization", which is both
    a wrong answer and an expensive one (the same rule the list route has always
    applied to ``date_from``/``date_to``).
    """
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(422, f"invalid {field}, use YYYY-MM-DD")


def validate_status(status: Optional[str], statuses: Iterable[str]) -> Optional[str]:
    """``status`` if it is one of the lifecycle values, ``None`` if absent.

    An unknown status is a **422**, not an empty page: the UI offers exactly
    ``VALID_TRANSITIONS``' keys, so a value outside them means the request is
    wrong, and answering "no results" would hide that behind a plausible-looking
    empty table (``.clinerules`` §3 — never claim what is not verified).
    """
    if status is None:
        return None
    value = str(status).strip()
    if not value:
        return None
    allowed = tuple(statuses)
    if value not in allowed:
        raise HTTPException(
            422, "invalid status, use one of " + ", ".join(sorted(allowed)))
    return value


# ---------------------------------------------------------------------------
# Search — the four ways a receptionist identifies an appointment
# ---------------------------------------------------------------------------

def like_pattern(term: str) -> str:
    """``term`` as a contained ILIKE pattern with LIKE metacharacters escaped.

    Without this, a patient's name containing ``%`` would match everything, and a
    receptionist typing ``_`` would get a silently wrong result set.
    """
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def search_conditions(term: str) -> list:
    """The OR-ed match conditions for one search term.

    Bangla works because ILIKE on UTF-8 compares bytes and Bengali has no case,
    so a substring match is exactly what the search box intends.  The symptom
    catalogue's romanization normaliser is deliberately *not* applied here — that
    would be a second, divergent name-matching rule.

    The mobile comparison is digit-only, so ``017-0000-0001`` and ``01700000001``
    agree; it is added only when the term actually contains digits, otherwise a
    name would be compared against a number column for nothing.
    """
    pattern = like_pattern(term)
    conditions = [
        Patient.name.ilike(pattern, escape="\\"),
        Appointment.id.ilike(pattern, escape="\\"),
        Appointment.token_number.ilike(pattern, escape="\\"),
    ]
    digits = "".join(ch for ch in term if ch.isdigit())
    if digits:
        conditions.append(Patient.mobile.ilike(f"%{digits}%", escape="\\"))
    return conditions


def apply_search(query, term: Optional[str]):
    """Apply the search term to a query already joined to ``Patient``."""
    text = (term or "").strip()
    if not text:
        return query
    return query.filter(or_(*search_conditions(text)))


# ---------------------------------------------------------------------------
# Filters — combine, never replace one another
# ---------------------------------------------------------------------------

def apply_filters(query, *, q: str = "", doctor_id: Optional[str] = None,
                  status: Optional[str] = None, date_from: Optional[str] = None,
                  date_to: Optional[str] = None,
                  statuses: Iterable[str] = ()):
    """Apply every toolbar filter the caller supplied.

    Each filter is independent and additive: passing a search *and* a status
    narrows to rows matching both.  An absent filter is absent, never "empty
    string means no results".
    """
    status_value = validate_status(status, statuses)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status_value:
        query = query.filter(Appointment.status == status_value)
    if date_from:
        query = query.filter(Appointment.appointment_date >= parse_day(date_from, "date_from"))
    if date_to:
        query = query.filter(Appointment.appointment_date <= parse_day(date_to, "date_to"))
    return apply_search(query, q)


# ---------------------------------------------------------------------------
# Authorization — branch scope from the token (D-1)
# ---------------------------------------------------------------------------

def apply_branch_scope(query, auth, branch_id: Optional[str] = None):
    """Narrow ``query`` to the branches ``auth`` may read.

    ``super_admin``/``org_admin`` see every branch of their organization and may
    narrow to one.  Every other role is confined to the branch stamped in its
    token: naming another branch is answered with the same non-disclosing 404 an
    unknown id gets, so a probe cannot tell "exists but not yours" from "does not
    exist" (``.clinerules`` §3).  A branch-scoped role whose token carries no
    branch is a 403: it can read no appointments at all, and saying so is honest.

    The frontend never decides this.  The branch picker offers only the branches
    ``/api/v1/me/branches`` returns, but the grant is here, server-side.
    """
    if auth.is_org_admin or auth.is_super_admin:
        if branch_id:
            return query.filter(Appointment.branch_id == branch_id)
        return query
    if branch_id and branch_id != auth.branch_id:
        raise HTTPException(404, "not found")
    if not auth.branch_id:
        raise HTTPException(403, "branch scope required")
    return query.filter(Appointment.branch_id == auth.branch_id)


# ---------------------------------------------------------------------------
# Row shapes — one join shape, so both read paths carry the same context
# ---------------------------------------------------------------------------

def appointment_rows(session, auth):
    """``(Appointment, patient name, patient mobile, doctor name, branch name)``.

    The display context travels with the row: the calendar used to resolve a
    patient name with one ``GET /api/v1/patients/{id}`` per distinct patient per
    week (F-7), and fell back to ``#<id>`` for doctors and branches.  One query
    answers all of it inside the caller's authorized scope.

    The organization condition sits **inside** the join, because a bare
    ``Patient.organization_id ==`` in the WHERE clause would quietly turn the
    outer join back into an inner one and drop appointments whose patient row is
    gone.  An appointment must stay visible even when its patient, doctor or
    branch record was retired: the appointment carries its own snapshot columns.
    """
    org = auth.organization_id
    return (
        session.query(Appointment, Patient.name, Patient.mobile,
                      Doctor.name, Branch.name)
        .outerjoin(Patient, and_(Patient.id == Appointment.patient_id,
                                 Patient.organization_id == org))
        .outerjoin(Doctor, and_(Doctor.id == Appointment.doctor_id,
                                Doctor.organization_id == org))
        .outerjoin(Branch, and_(Branch.id == Appointment.branch_id,
                                Branch.organization_id == org))
        .filter(Appointment.organization_id == org)
    )


def search_rows(session, auth):
    """Appointments joined only to the patient data the search compares against.

    Used by the aggregating read (``/appointments/matches``): it needs the
    patient name and mobile for the WHERE clause but returns no patient data, so
    the doctor/branch joins of :func:`appointment_rows` would be dead weight.
    """
    org = auth.organization_id
    return (
        session.query(Appointment)
        .outerjoin(Patient, and_(Patient.id == Appointment.patient_id,
                                 Patient.organization_id == org))
        .filter(Appointment.organization_id == org)
    )


def row_context(row, can_see_mobile: bool) -> dict:
    """The display columns of one :func:`appointment_rows` row, mobile gated.

    Contact details follow the *patient-record* permission, not the appointment
    permission: a role that may not read patients is not shown their number, in
    the table or anywhere else.
    """
    _, patient_name, patient_mobile, doctor_name, branch_name = row
    return {
        "patient_name": patient_name or "",
        "patient_mobile": (patient_mobile or "") if can_see_mobile else "",
        "doctor_name": doctor_name or "",
        "branch_name": branch_name or "",
    }


# ---------------------------------------------------------------------------
# Date index — where the matches outside the visible window are (D-2)
# ---------------------------------------------------------------------------

def match_index(session, auth, *, q: str = "", branch_id: Optional[str] = None,
                doctor_id: Optional[str] = None, status: Optional[str] = None,
                date_from: Optional[str] = None, date_to: Optional[str] = None,
                near: Optional[str] = None,
                statuses: Iterable[str] = (),
                limit: int = MATCH_DATE_LIMIT) -> dict:
    """``{"total": n, "dates": [{"date", "count"}], "truncated": bool}``.

    Counts only — never a patient name and never the records themselves — so the
    browser can tell the receptionist *"there are 6 matches on other dates"* and
    navigate to one without ever downloading the organization's history to answer
    a search (which is what "load everything and filter in the client" would mean).

    ``near`` orders the date list by distance from that day, so the cap keeps the
    dates closest to the calendar on screen rather than the oldest in the
    database.  ``truncated`` says that more dates exist than are listed.
    """
    query = search_rows(session, auth)
    query = apply_branch_scope(query, auth, branch_id)
    query = apply_filters(query, q=q, doctor_id=doctor_id, status=status,
                          date_from=date_from, date_to=date_to,
                          statuses=statuses)

    total = query.with_entities(func.count(Appointment.id)).scalar() or 0

    grouped = query.with_entities(
        Appointment.appointment_date, func.count(Appointment.id)
    ).group_by(Appointment.appointment_date)
    if near:
        day = parse_day(near, "near")
        grouped = grouped.order_by(func.abs(Appointment.appointment_date - day),
                                   Appointment.appointment_date.asc())
    else:
        grouped = grouped.order_by(Appointment.appointment_date.asc())

    rows = grouped.limit(limit + 1).all()
    truncated = len(rows) > limit
    return {
        "total": int(total),
        "dates": [{"date": str(day), "count": int(count)}
                  for day, count in rows[:limit]],
        "truncated": bool(truncated),
    }

