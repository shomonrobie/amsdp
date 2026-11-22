"""Chamber location helpers — one definition of how a snapshot reads.

AMSDP-FACILITY-DOCTOR-01 snapshots floor / department / room onto an
``appointments`` row **at booking time**, deliberately denormalised: a
receptionist must be able to reprint yesterday's slip showing room 204 after the
facility has been re-organised, so a historical row is never re-read from the
doctor's *current* schedule session or chamber.

QUE-006 (F4) needs exactly that snapshot — not the live schedule — because an
announcement must send the patient to the room they were actually told at
booking or check-in.  The label format therefore lives here, in one place, so the
appointment API and the queue announcement cannot disagree about how a location
reads.

Nothing in this module queries the database: it takes an already-loaded
snapshot (§9.2 of the QUE-006 plan — the caller owns the query so a page of
entries costs one query, not one per row).
"""

#: The location a queue entry inherits from its appointment's booking snapshot.
ROOM_SOURCE_APPOINTMENT = "appointment_snapshot"
#: Reserved for a future walk-in room capture (plan option R2). Nothing writes it yet.
ROOM_SOURCE_WALK_IN = "walk_in_capture"

#: The empty answer, used whenever no room was snapshotted. Callers must treat it
#: as "no room", never as Room 0 or a fallback to the doctor's current chamber.
NO_ROOM = {"room_id": "", "room_name": "", "label": "", "source": ""}


def location_label(snapshot) -> str:
    """Human-readable chamber snapshot, e.g. ``2nd Floor / Cardiology / 204``.

    ``snapshot`` is anything carrying ``floor_name``, ``department_name`` and
    ``room_name`` (an ``Appointment`` in practice). Missing parts are simply
    omitted — a clinic with no building model still reads sensibly.
    """
    if snapshot is None:
        return ""
    parts = [p for p in (
        getattr(snapshot, "floor_name", None),
        getattr(snapshot, "department_name", None),
        getattr(snapshot, "room_name", None),
    ) if p]
    return " / ".join(parts)


def room_payload(snapshot, source: str = ROOM_SOURCE_APPOINTMENT) -> dict:
    """The room fields a queue payload carries, derived from a location snapshot.

    ``label`` is for display (a row caption, a printed slip). The *announcement*
    uses ``room_name`` only, because the approved sentence names a room and no
    approved sentence names a floor or a department alone. When the snapshot
    carries no room name the payload reports ``source: ''`` and the caller
    announces the approved room-less variant — never "Room", never Room 0, and
    never the doctor's current chamber substituted for the booking snapshot.
    """
    if snapshot is None:
        return dict(NO_ROOM)
    room_id = getattr(snapshot, "room_id", None) or ""
    room_name = getattr(snapshot, "room_name", None) or ""
    label = location_label(snapshot)
    return {
        "room_id": room_id,
        "room_name": room_name,
        "label": label,
        "source": source if room_name else "",
    }
