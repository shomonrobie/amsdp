"""Single authority for AMSDP daily queue token allocation.

BR §24–§31: a queue token identifies one patient for one doctor on one day, so
the token must be issued exactly once.  Every service that enqueues a patient
must allocate through :func:`allocate_daily_token` -- never through ``count(*)``
of its own table -- otherwise two counters drift apart and two live entries end
up sharing a token.

Finding SEQ4-TOKEN-P1 (Sequence 4 acceptance run): the appointment service's
``POST /api/v1/appointments/{id}/check-in`` allocated ``count(*) + 1`` over
``queue_entries`` while the queuing service used the atomic
``queue_sequences`` row.  A walk-in enqueued after a scheduled check-in was
therefore issued ``T-<DOC>-001`` a second time (two *active* entries with the
same token for the same doctor and day), which is a patient-identification
hazard on the DQD screen and on printed slips.
"""
from sqlalchemy import text


def token_for(doctor_id: str, serial: int) -> str:
    """The display token for an already reserved daily serial."""
    return f"T-{doctor_id[:6].upper()}-{serial:03d}"


def allocate_daily_token(session, doctor_id: str, day):
    """Atomically reserve the next daily serial for ``doctor_id`` on ``day``.

    Returns ``(serial, token)``.  The ``INSERT ... ON CONFLICT`` keeps the
    counter atomic under concurrent check-ins, and the row belongs to the
    caller's transaction, so a rolled-back enqueue does not burn a serial.
    """
    row = session.execute(
        text(
            "INSERT INTO queue_sequences (doctor_id, date, last_value) "
            "VALUES (:d, :dt, 1) "
            "ON CONFLICT (doctor_id, date) "
            "DO UPDATE SET last_value = queue_sequences.last_value + 1 "
            "RETURNING last_value"
        ),
        {"d": doctor_id, "dt": day},
    ).fetchone()
    serial = row[0]
    return serial, token_for(doctor_id, serial)
