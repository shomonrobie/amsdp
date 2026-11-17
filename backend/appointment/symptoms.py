"""Symptom catalogue and appointment symptom recording — AMSDP-SYMPTOM-01.

What this module is, stated as narrowly as the feature actually is
------------------------------------------------------------------
A receptionist asks the patient "আপনার কী কী সমস্যা হচ্ছে?" / "What problems are
you having?", records **what the patient reports** — from a bilingual catalogue
or in the patient's own words — optionally records when it started, and takes
the booking.  That is the whole capability.

It is *not* a diagnosis, a clinical decision-support tool, a triage or urgency
assessment, or an AI inference service.  Nothing here computes a condition from
a symptom, and nothing here computes a symptom from the patient: there is no
code path in this module that reads the patient's age, sex or the chosen
doctor's speciality.  Speciality appears in exactly one place in the system —
as ``specialty_hints`` on a catalogue entry, consumed by the browser-side
ranking in ``frontend/lib/symptom-catalogue/matcher.js``, where it may reorder
equally good text matches and nothing else.  A 74-year-old seeing a
cardiologist gets an empty symptom field until the receptionist asks.

Why the catalogue is served whole
---------------------------------
``GET /api/v1/symptoms`` returns every active entry for the caller's
organization in one response (a few dozen short rows), exactly as BanglaNameSense
bundles its dataset: the booking form then searches in memory, so a keystroke
never costs a request and the search behaves identically in both languages.
Server-side text search is deliberately absent — it would mean a second
implementation of the Bengali normalisation rules, which is the one thing this
feature must not fork (see ``frontend/lib/bangla-name-sense/normalize.js``).

Tenant isolation
----------------
Every query in this module filters on ``organization_id`` derived from the
authenticated token, never from the request body.  A symptom id belonging to
another organization is indistinguishable from an id that does not exist: both
answer the same 422 and neither reveals which case it was.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from common.auth import AuthContext, require_permission
from common.database import SessionFactory
from common.models import AppointmentSymptom, SymptomCatalog
from common.permissions import check

#: The onset question's closed vocabulary.
#:
#: ``(code, English label, Bangla label)``.  A closed list, not a date, on
#: purpose: a patient at a reception desk routinely cannot name a day, and
#: forcing one would either block the booking or invent a fact.  ``UNKNOWN``
#: means "asked, could not say" and is *different* from not answering at all
#: (which is stored as no code — ``None``).
ONSET_OPTIONS = (
    ("TODAY", "Today", "আজ"),
    ("YESTERDAY", "Yesterday", "গতকাল"),
    ("FEW_DAYS", "A few days ago", "কয়েক দিন আগে"),
    ("FEW_WEEKS", "A few weeks ago", "কয়েক সপ্তাহ আগে"),
    ("OVER_MONTH", "More than a month ago", "এক মাসের বেশি আগে"),
    ("LONG_STANDING", "Long-standing", "দীর্ঘদিন ধরে"),
    ("UNKNOWN", "Unknown", "জানা নেই"),
)

ONSET_CODES = tuple(code for code, _en, _bn in ONSET_OPTIONS)

#: Upper bound on one appointment's symptom list.  A reception desk records a
#: handful; the cap exists so a runaway client cannot turn a booking into a
#: bulk insert, not to constrain what a patient may report.
MAX_SYMPTOMS = 20

#: Upper bound on one free-text description (a short phrase, not a paragraph).
MAX_TEXT_LENGTH = 200

#: Review states a catalogue entry may carry.  ``unreviewed`` is the default and
#: is what the API reports until a clinician has actually looked at the wording —
#: the UI must never imply otherwise.
REVIEW_STATES = ("unreviewed", "curated", "clinically_reviewed")


def onset_options_payload():
    """The onset vocabulary as the client receives it (bilingual labels)."""
    return [{"code": code, "name_en": name_en, "name_bn": name_bn}
            for code, name_en, name_bn in ONSET_OPTIONS]


def symptom_payload(row: SymptomCatalog) -> dict:
    """One catalogue entry as the booking form receives it.

    ``name_bn`` falls back to ``name_en``: a half-translated entry stays usable
    rather than rendering an empty chip, and ``review_status`` still says the
    wording has not been signed off.
    """
    return {
        "id": row.id,
        "code": row.code or "",
        "name_en": row.name_en or "",
        "name_bn": row.name_bn or row.name_en or "",
        "synonyms_en": list(row.synonyms_en or []),
        "synonyms_bn": list(row.synonyms_bn or []),
        "category": row.category or "general",
        "specialty_hints": list(row.specialty_hints or []),
        "source": row.source or "",
        "review_status": row.review_status or "unreviewed",
        "sort_order": int(row.sort_order if row.sort_order is not None else 100),
        "status": row.status or "active",
    }


def symptom_record_payload(row: AppointmentSymptom) -> dict:
    """One recorded symptom as it is returned with an appointment."""
    return {
        "id": row.id,
        "kind": row.kind,
        "symptom_id": row.symptom_id or "",
        "name_en": row.name_en or "",
        "name_bn": row.name_bn or "",
        "text": row.text_reported or "",
        "recorded_by": row.recorded_by or "",
        "created_at": str(row.created_at) if row.created_at else "",
    }


def text_key(text: str) -> str:
    """Duplicate-suppression key for a free-text description.

    Case-folded and whitespace-collapsed only.  It is **not** the search
    normaliser: the Unicode/Bengali rules live once, in the frontend engine, and
    duplicating them here would fork the language sense this feature reuses.
    Two descriptions that differ only in spacing or Latin case are the same
    complaint for the purpose of "do not create duplicate selections".
    """
    return " ".join(str(text or "").split()).casefold()


def validate_onset(code, note=""):
    """Validate the optional onset answer; return ``(code|None, note)``.

    An absent code means the question was not answered.  ``UNKNOWN`` means it
    *was* answered with "I am not sure".  Both are legitimate and they are not
    the same fact, so the distinction is kept all the way to the record.
    """
    value = str(code or "").strip().upper()
    text = " ".join(str(note or "").split())
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            422, f"the onset note must be {MAX_TEXT_LENGTH} characters or fewer")
    if not value:
        return None, text
    if value not in ONSET_CODES:
        raise HTTPException(422, "unknown onset option")
    return value, text


def plan_symptoms(session, *, organization_id, symptom_ids=None,
                  symptom_texts=None):
    """Validate and de-duplicate a booking's symptoms *before* any row is made.

    Returns a list of dictionaries ready for :func:`persist_symptoms`, in the
    order the receptionist selected them: catalogue entries first, then the
    free-text descriptions.

    Rejections are 422 and never distinguish "does not exist" from "belongs to
    another organization" — a cross-tenant identifier must stay
    indistinguishable from an unknown one.
    """
    ids = []
    for raw in (symptom_ids or []):
        value = str(raw or "").strip()
        if value and value not in ids:
            ids.append(value)          # never create duplicate selections

    texts = []
    seen_keys = set()
    for raw in (symptom_texts or []):
        value = " ".join(str(raw or "").split())
        if not value:
            continue
        if len(value) > MAX_TEXT_LENGTH:
            raise HTTPException(
                422,
                f"a symptom description must be {MAX_TEXT_LENGTH} characters or fewer")
        key = text_key(value)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        texts.append((value, key))

    if len(ids) + len(texts) > MAX_SYMPTOMS:
        raise HTTPException(
            422,
            f"no more than {MAX_SYMPTOMS} symptoms can be recorded "
            "for one appointment")

    by_id = {}
    if ids:
        rows = session.query(SymptomCatalog).filter(
            SymptomCatalog.organization_id == organization_id,
            SymptomCatalog.id.in_(ids)).all()
        by_id = {row.id: row for row in rows}
        if len(by_id) != len(ids):
            raise HTTPException(
                422, "one or more symptoms are not available in this organization")
        if any((row.status or "active") != "active" for row in rows):
            raise HTTPException(
                422, "one or more symptoms are no longer available for booking")

    plan = []
    for symptom_id in ids:
        row = by_id[symptom_id]
        plan.append({
            "kind": "catalogue",
            "symptom_id": row.id,
            # Snapshot at booking time — a later rename must not rewrite history.
            "name_en": row.name_en or "",
            "name_bn": row.name_bn or row.name_en or "",
            "text_reported": "",
            "text_key": "",
        })
    for value, key in texts:
        plan.append({
            "kind": "free_text",
            "symptom_id": None,
            "name_en": "",
            "name_bn": "",
            "text_reported": value,
            "text_key": key,
        })
    return plan


def apply_onset(appointment, code, note="") -> None:
    """Write the validated onset answer onto an appointment row."""
    value, text = validate_onset(code, note)
    appointment.symptom_onset_code = value
    appointment.symptom_onset_note = text or None


def persist_symptoms(session, *, appointment, plan, recorded_by=""):
    """Insert the planned symptom rows for ``appointment``; return them."""
    rows = []
    for item in plan:
        row = AppointmentSymptom(
            id=str(uuid.uuid4()),
            organization_id=appointment.organization_id,
            appointment_id=appointment.id,
            recorded_by=recorded_by or "",
            **item)
        session.add(row)
        rows.append(row)
    return rows


def copy_symptoms(session, *, source, target, recorded_by=""):
    """Carry a visit's recorded symptoms onto its rescheduled/transferred twin.

    A reschedule is the same complaint on a new day, so dropping the symptoms
    would lose the only record of why the patient came.  The *source* rows stay
    untouched (history), and the snapshot is copied rather than re-derived from
    the catalogue — which is what keeps the two visits' records independent.
    """
    rows = session.query(AppointmentSymptom).filter(
        AppointmentSymptom.organization_id == source.organization_id,
        AppointmentSymptom.appointment_id == source.id).all()
    copied = []
    for row in rows:
        clone = AppointmentSymptom(
            id=str(uuid.uuid4()),
            organization_id=target.organization_id,
            appointment_id=target.id,
            kind=row.kind,
            symptom_id=row.symptom_id,
            name_en=row.name_en or "",
            name_bn=row.name_bn or "",
            text_reported=row.text_reported or "",
            text_key=row.text_key or "",
            recorded_by=recorded_by or row.recorded_by or "")
        session.add(clone)
        copied.append(clone)
    return copied


def symptoms_by_appointment(appointment_ids, session=None):
    """``{appointment_id: [row, …]}`` for the given ids.

    One query for a whole calendar view instead of one per appointment.  Rows
    are ordered by ``created_at, id`` — a total order, so two calls for the same
    data cannot disagree, which matters because the chips render in this order.
    """
    ids = [str(i) for i in (appointment_ids or []) if i]
    if not ids:
        return {}
    own_session = session is None
    session = session or SessionFactory()
    try:
        rows = (session.query(AppointmentSymptom)
                .filter(AppointmentSymptom.appointment_id.in_(ids))
                .order_by(AppointmentSymptom.created_at, AppointmentSymptom.id)
                .all())
        grouped = {}
        for row in rows:
            grouped.setdefault(row.appointment_id, []).append(row)
        if own_session:
            for group in grouped.values():
                for row in group:
                    session.expunge(row)
        return grouped
    finally:
        if own_session:
            session.close()


# ---------------------------------------------------------------------------
# HTTP — the catalogue
# ---------------------------------------------------------------------------

router = APIRouter()


@router.get("/api/v1/symptoms")
def list_symptoms(
    include_inactive: bool = Query(
        False, description="also return retired entries (symptom.manage only)"),
    auth: AuthContext = Depends(require_permission("symptom.read")),
):
    """The caller's organization symptom catalogue, active entries by default.

    The whole catalogue is returned in one response on purpose (see the module
    docstring): the booking form searches it in memory, in both scripts, with
    no request per keystroke.

    Retired entries are excluded for everyone — a retired symptom must not be
    selectable for a new booking — and can be retrieved with
    ``include_inactive=true`` by a caller holding ``symptom.manage``, which is
    how an administrator reviews what used to be offered.  Nothing about an
    existing appointment changes either way: recorded symptoms are stored as
    snapshots on ``appointment_symptoms``.
    """
    if include_inactive and not check("symptom.manage", auth.role):
        raise HTTPException(403, "not permitted to read inactive symptoms")
    session = SessionFactory()
    try:
        query = session.query(SymptomCatalog).filter(
            SymptomCatalog.organization_id == auth.organization_id)
        if not include_inactive:
            query = query.filter(SymptomCatalog.status == "active")
        rows = query.order_by(SymptomCatalog.sort_order,
                              SymptomCatalog.name_en).all()
        for row in rows:
            session.expunge(row)
        return {
            "items": [symptom_payload(row) for row in rows],
            "onset_options": onset_options_payload(),
            "max_symptoms": MAX_SYMPTOMS,
            # Stated in the payload, not only in the docs: nothing here is a
            # diagnosis, and an unreviewed entry is not clinically validated.
            "review_status_values": list(REVIEW_STATES),
            "disclaimer": (
                "Patient-reported symptoms recorded by reception. Not a "
                "diagnosis, not triage, and not clinically validated unless "
                "review_status says so."),
        }
    finally:
        session.close()


@router.get("/api/v1/symptoms/onset-options")
def list_onset_options(
    auth: AuthContext = Depends(require_permission("symptom.read")),
):
    """The onset vocabulary (bilingual), for a client that needs only that."""
    return {"items": onset_options_payload()}


