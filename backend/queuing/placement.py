"""Walk-in and queue placement — Business Rules §25 (MP-10).

A new queue entry's position used to be the caller's choice: every request
carried a ``walk_in_policy`` of its own. That made the facility's policy a
property of the HTTP request, so two receptionists could place the same patient
under two different rules, and BR §25's "Facility Admin selects policy" had no
home. This module is the single implementation of the four approved policies:

``end_of_queue``
    the entry joins after every applicable booking — append, nothing moves;
``first_come``
    order follows the recorded arrival time, so a walk-in registered late for a
    patient who arrived early is placed among the patients who arrived before
    them;
``reserved_capacity``
    the facility holds the first *pool* places of the day for walk-ins (the
    pool is a count, or a percentage of the day's published capacity); a walk-in
    takes the end of that block until it is full, and appends after it when it
    is not;
``staff_placement``
    authorised staff name the position; the range is validated rather than
    accepted verbatim.

Every insertion that moves an existing row appends to that row's
``position_history`` and writes one ``queue.reposition`` audit event, exactly
like a manual reorder and a missed-turn recovery — a position change is never
silent (BR §40).

**A policy change never reorders an active queue.** Nothing in this module runs
when the policy is written; placement is computed at insertion time only, from
the configuration that is in force then. That is what makes BR §25's
"apply prospectively" true rather than aspirational.
"""

from datetime import datetime, timezone
from typing import Optional

from common.audit import record_audit
from common.config import get_queue_config, reserved_for_capacity
from common.models import QueueEntry, Schedule
from common.slots import slot_starts, templates_for_day

#: Statuses that are still part of the live queue, and therefore part of the
#: position space a new entry has to fit into.
ACTIVE_STATUSES = ("waiting", "called", "in_consultation", "skipped")

#: Entry sources whose placement follows the organization's walk-in policy.
#: An appointment checking in is BR §24/§25's *booked* patient, not a walk-in:
#: it always takes its place at the end of the live queue.
WALK_IN_SOURCES = ("walk_in", "extra")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _aware(value) -> Optional[datetime]:
    """A UTC-aware datetime, reading a naive value as UTC.

    ``created_at`` is stored timezone-aware, but a value that arrives naive (a
    hand-written fixture, a driver that dropped the offset) must not make the
    comparison raise — comparing aware and naive datetimes is a TypeError.
    """
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_arrival(value) -> Optional[datetime]:
    """Parse an optional ISO-8601 arrival instant.

    Returns ``None`` when nothing was supplied. Raises ``ValueError`` for a
    value that is not a timestamp, so the caller can answer 422 rather than
    silently treating a typo as "just arrived".
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _aware(value)
    try:
        return _aware(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError as exc:
        raise ValueError(f"invalid arrived_at: {value}") from exc


def active_queue(session, *, organization_id: str, doctor_id: str, day,
                 exclude_id: Optional[str] = None) -> list:
    """The doctor's live queue for *day*, locked, in display order.

    The rows are locked for update: two receptionists registering walk-ins at
    the same moment must not both read the same free place in the reserved
    block and both take it. Lock order matches the rest of the service
    (``queue_sequences`` first, then the entries), so it cannot deadlock against
    token allocation or recovery.
    """
    query = session.query(QueueEntry).filter(
        QueueEntry.organization_id == organization_id,
        QueueEntry.doctor_id == doctor_id,
        QueueEntry.date == day,
        QueueEntry.status.in_(ACTIVE_STATUSES),
    )
    if exclude_id:
        query = query.filter(QueueEntry.id != exclude_id)
    return list(query.order_by(QueueEntry.position,
                               QueueEntry.created_at).with_for_update().all())


def day_capacity(session, *, organization_id: str, doctor_id: str, day) -> int:
    """Published capacity for *doctor* on *day*; ``0`` when nothing is published.

    Used only by the percentage form of the reserved pool. It is the same
    arithmetic the availability read performs (templates for the weekday, slots
    per template, seats per slot), kept here so the queue does not have to call
    the scheduling service. The largest covering schedule wins: a doctor's day
    has one capacity, and two active schedules covering the same day is a
    scheduling defect, not a reason to reserve twice.
    """
    schedules = session.query(Schedule).filter(
        Schedule.organization_id == organization_id,
        Schedule.doctor_id == doctor_id,
    ).all()
    best = 0
    for sched in schedules:
        if (sched.status or "active").lower() != "active":
            continue
        if sched.effective_from and day < sched.effective_from:
            continue
        if sched.effective_to and day > sched.effective_to:
            continue
        total = 0
        for template in templates_for_day(sched.slot_templates or [],
                                         day.weekday()):
            total += int(template["max_patients"]) * len(slot_starts(template))
        best = max(best, total)
    return best


def reserve_pool(session, *, organization_id: str, doctor_id: str, day,
                 org_config=None) -> int:
    """How many front-of-queue places the reserve opens for walk-ins.

    ``count`` mode is the configured number. ``percent`` mode is a share of the
    day's published capacity, so a doctor who publishes no hours has no pool to
    reserve and walk-ins simply append — the honest reading of "reserve a
    percentage of capacity" when there is no capacity.
    """
    cfg = get_queue_config(org_config)
    value = cfg["walk_in_reserve_value"]
    if value <= 0:
        return 0
    if cfg["walk_in_reserve_mode"] == "count":
        return value
    capacity = day_capacity(session, organization_id=organization_id,
                            doctor_id=doctor_id, day=day)
    if capacity <= 0:
        return 0
    return reserved_for_capacity(capacity, org_config)


def _shift_from(session, ordered, index: int, *, actor_id: str,
                actor_role: str, reason: str) -> int:
    """Move ``ordered[index:]`` down one place, recording history and audit.

    Returns the number of rows that actually moved. A row whose position does
    not change is never touched, so a compact queue produces no noise.
    """
    shifted = 0
    for row in ordered[index:]:
        old = row.position
        new = old + 1
        history = list(row.position_history or [])
        history.append({"from": old, "to": new, "actor": actor_id,
                        "reason": reason, "at": _now_iso()})
        row.position_history = history
        row.position = new
        record_audit(session, service="queuing", org_id=row.organization_id,
                     branch_id=row.branch_id, action="queue.reposition",
                     target_type="queue_entry", target_id=row.id,
                     actor_id=actor_id, actor_role=actor_role,
                     before={"position": old}, after={"position": new},
                     reason=reason)
        shifted += 1
    return shifted


def place(session, *, organization_id: str, doctor_id: str, day,
          entry_source: str, org_config=None, actor_id: str = "",
          actor_role: str = "", requested_position=None,
          arrived_at=None) -> dict:
    """Decide where a new entry joins the queue, and move what must move.

    Returns the *decision*, which the caller writes with the entry so the audit
    trail can say **why** a token sits where it sits::

        {"policy", "position", "requested_position", "pool", "pool_used",
         "shifted", "basis"}

    ``basis`` is one of ``append``, ``staff``, ``arrival_order`` or
    ``reserved_block``.  A refusal is raised as ``ValueError`` — the route turns
    it into a 422, so the rule is enforced in one place and the caller is told
    what to fix.
    """
    cfg = get_queue_config(org_config)
    # BR §25 governs *walk-ins*.  A booked patient checking in is not placed by
    # the walk-in policy; it keeps the historical append behaviour.
    policy = (cfg["walk_in_policy"] if entry_source in WALK_IN_SOURCES
              else "end_of_queue")
    ordered = active_queue(session, organization_id=organization_id,
                           doctor_id=doctor_id, day=day)
    last = max([row.position for row in ordered], default=0)
    decision = {"policy": policy, "position": last + 1,
                "requested_position": requested_position, "pool": 0,
                "pool_used": 0, "shifted": 0, "basis": "append"}

    if policy == "staff_placement":
        if requested_position is None:
            raise ValueError(
                "staff_placement_position_required: this facility places "
                "walk-ins at a position staff choose")
        try:
            wanted = int(requested_position)
        except (TypeError, ValueError):
            raise ValueError(f"invalid position: {requested_position}")
        if wanted < 1 or wanted > last + 1:
            raise ValueError(f"position must be between 1 and {last + 1}")
        # The insertion index is the first row at or after the wanted position:
        # positions may have gaps after a cancellation, and counting rows whose
        # position is smaller is the only reading that holds for a gapped queue.
        index = sum(1 for row in ordered if row.position < wanted)
        decision.update(position=wanted, basis="staff")
        decision["shifted"] = _shift_from(
            session, ordered, index, actor_id=actor_id, actor_role=actor_role,
            reason="walk-in placement (staff_placement)")
        return decision

    if policy == "first_come":
        arrival = parse_arrival(arrived_at) or datetime.now(timezone.utc)
        index = None
        for position_in_queue, row in enumerate(ordered):
            stamp = _aware(row.created_at)
            if stamp is not None and stamp > arrival:
                index = position_in_queue
                break
        if index is None:
            # Everyone in the queue was registered before this arrival: the
            # entry belongs at the end, and nothing has to move.
            decision["basis"] = "append"
            return decision
        decision.update(position=ordered[index].position, basis="arrival_order")
        decision["shifted"] = _shift_from(
            session, ordered, index, actor_id=actor_id, actor_role=actor_role,
            reason="walk-in placement (first_come)")
        return decision

    if policy == "reserved_capacity":
        pool = reserve_pool(session, organization_id=organization_id,
                            doctor_id=doctor_id, day=day, org_config=org_config)
        block = ordered[:pool] if pool else []
        used = sum(1 for row in block if row.entry_source in WALK_IN_SOURCES)
        decision.update(pool=pool, pool_used=used)
        if pool and used < pool:
            index = min(used, len(ordered))
            if index < len(ordered):
                decision.update(position=ordered[index].position,
                                basis="reserved_block")
                decision["shifted"] = _shift_from(
                    session, ordered, index, actor_id=actor_id,
                    actor_role=actor_role,
                    reason="walk-in placement (reserved_capacity)")
        # The reserved block is full (or there is no pool): append, exactly like
        # end_of_queue.  The reserve is a guarantee, not a cap on walk-ins.
        return decision

    # end_of_queue — and every appointment check-in.
    return decision
