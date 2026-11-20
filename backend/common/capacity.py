"""Seat allocation — the database capacity guarantee (owner decision Q2).

Q2 asks for capacity integrity that a second, independent layer enforces: the
application's ``SELECT … FOR UPDATE`` lock on the doctor row stays, but it is no
longer the only thing standing between two receptionists and the last seat.

The representation is deliberately not ``UNIQUE (doctor_id, slot_start)``: a
capacity-N session seats several patients in the same window, so that
constraint would forbid a legitimate booking.  Instead every appointment *claims
a seat number* in its slot, and ``slot_allocations`` makes
``(doctor_id, appointment_date, slot_key, seat_number)`` unique.  Two
transactions claiming the same seat cannot both commit, whatever the
application layer believes.

The claim runs inside a SAVEPOINT (``session.begin_nested()``), so a losing
request rolls back only its own provisional allocation and can answer a clean
``422`` instead of poisoning the caller's transaction.  A row exists only while
the appointment occupies the seat: :func:`release_seat` is called by every
status transition that frees it, which keeps the allocation table and the
status-based capacity count in agreement.

Nothing here decides *policy* — the caller passes the capacity it is willing to
sell, including the organization's unscheduled limit for an outside-session
appointment.
"""

from sqlalchemy.exc import IntegrityError

from .models import SlotAllocation


class SlotFull(Exception):
    """No free seat left in the requested slot.

    A plain exception rather than an ``HTTPException``: this module is shared by
    services that answer refusals differently, and none of them should have
    FastAPI imported for them.
    """


def _claimed(session, doctor_id, appointment_date, slot_key) -> set:
    rows = session.query(SlotAllocation.seat_number).filter(
        SlotAllocation.doctor_id == doctor_id,
        SlotAllocation.appointment_date == appointment_date,
        SlotAllocation.slot_key == slot_key).all()
    return {row[0] for row in rows}


def claim_seat(session, *, organization_id: str, doctor_id: str,
               appointment_date, slot_key: str, appointment_id: str,
               capacity: int = 1, slot_end: str = None,
               kind: str = "scheduled") -> int:
    """Claim a seat in *slot_key* and return its number.

    The lowest free seat at or below *capacity* is taken.  Raises
    :class:`SlotFull` when every seat is taken — either because the application
    count says so, or because the database constraint won the race.

    The caller must already hold whatever lock it uses for its own count; this
    function does not take one, because the guarantee it provides is the
    constraint, not the lock.
    """
    capacity = max(int(capacity or 1), 1)
    taken = _claimed(session, doctor_id, appointment_date, slot_key)
    seat = next((n for n in range(1, capacity + 1) if n not in taken), None)
    if seat is None:
        raise SlotFull(f"{slot_key} has no free seat of {capacity}")

    row = SlotAllocation(
        organization_id=organization_id, doctor_id=doctor_id,
        appointment_date=appointment_date, slot_key=slot_key, slot_end=slot_end,
        kind=kind, seat_number=seat, appointment_id=appointment_id)
    try:
        # Savepoint: a duplicate-seat winner rolls back only this claim.
        with session.begin_nested():
            session.add(row)
            session.flush()
    except IntegrityError:
        raise SlotFull(f"{slot_key} seat {seat} was claimed concurrently")
    return seat


def release_seat(session, appointment_id: str) -> bool:
    """Give up the seat *appointment_id* holds; True when one was released."""
    rows = session.query(SlotAllocation).filter(
        SlotAllocation.appointment_id == appointment_id).all()
    for row in rows:
        session.delete(row)
    return bool(rows)


def seat_of(session, appointment_id: str):
    """The allocation row for *appointment_id*, or ``None``."""
    return session.query(SlotAllocation).filter(
        SlotAllocation.appointment_id == appointment_id).first()
