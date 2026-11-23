# QUE-006 W4 — Room and Announcement Data Support (implementation report)

**Assignment ID:** `AMSDP-QUE-006-W4-ROOM-SUPPORT`
**Date:** 2026-11-21
**Status:** **BLOCKED — REQUIRES PRODUCT OWNER DECISION (POD-2).** No schema change, no field and no
payload was invented. This report narrows the decision considerably: the room data already exists.

---

## 1. What was inspected (verified in this session)

| Fact | Location |
|---|---|
| `queue_entries` has **no** room column and no room in its response | `backend/common/models.py:854-884`; `backend/queuing/main.py:_entry_to_dict` (82-92) |
| A facility room hierarchy **does** exist | `FacilityRoom` (`models.py:134-162`), `facility_floors`, `facility_departments` |
| A doctor has a **default chamber per branch** | `doctor_branches.room_id` (`models.py:436-449`) |
| A schedule session is **assigned a room** | `schedule_sessions.room_id` (`models.py:555-582`) |
| An appointment **snapshots** its chamber at booking | `appointments.room_id` **and** `appointments.room_name` (`models.py:616-630`) — deliberately denormalised so a reprint shows room 204 after the facility is re-organised |
| A queue entry **links to its appointment** | `queue_entries.appointment_id` (`models.py:866`) |
| The engine already speaks rooms | W1: `resolveSegments({token, room})` builds the room digit clips; 80-case matrix includes rooms `5`, `101`, `৩` |
| The page already passes `room` | `pages/queue.js` `announceEntry` / `announceOnCall`: `room: entry.room` — `undefined` today, never invented |

## 2. Why it stays blocked

The question is no longer "where could a room come from" but **which** source is authoritative for an
announcement, and the three candidates are not equivalent:

| Candidate | Consequence |
|---|---|
| `appointments.room_name` (snapshot at booking) | Needs no schema change. Wrong if the patient is moved on the day, which is common in a clinic. |
| Live `facility_rooms.name` via the doctor's chamber (`doctor_branches.room_id`) | Correct for a same-day move, but the announcement then differs from the printed slip. |
| A room **snapshotted onto the queue entry at call time** | Correct for both, and matches "the room the patient was actually told"; requires a migration. |

The roadmap recommended the third. The owner has not decided, and the assignment forbids silently
choosing (§7, Part 6 "Do not bypass unresolved decisions"). It is also a business decision, not an
engineering one: it decides what the patient hears versus what the slip says.

**Two owner decisions gate this workstream:**

1. **POD-2** — which source, and may a room change mid-queue (recall with a new room)?
2. **POD-1** — the room-number range that validation should accept (the engine currently accepts any
   digit run and refuses a room with no digits).

## 3. What is already done (and what is deliberately not)

**Done, verified:** the client transport accepts a room and plays the approved with-room sentence for both
languages (`en.phrase.proceed-to-room` … `room-suffix`; `bn.phrase.room-prefix` … `room-locative`),
including the multi-digit room and the catalogue's 300 ms pause.

**Not done:** no `queue_entries.room_*` column, no Alembic revision, no change to `_entry_to_dict`, no new
endpoint field, no change to the queue UI. Registering a room source is a backend change that this host
cannot run or test (no `pytest`, no `fastapi`, no `sqlalchemy`), so shipping it would be an unverified
schema change — forbidden by `.clinerules` §3 and the assignment's §9.

## 4. The change set once POD-2 is decided (ready to implement)

1. `queue_entries.room_id`, `room_name` (nullable, snapshot) **if** the owner picks the call-time option;
   a `QueueEntry` migration with `upgrade`/`downgrade`, backfilled from
   `appointments.room_name` for open entries only, and a documented no-op for historical rows.
2. `_entry_to_dict` gains `room` (the snapshot name), **and nothing else**.
3. `queue_action("call")` copies the room from the chosen source into the entry at transition time
   (never at read time, so a later move does not rewrite history).
4. Backend tests: room present, room absent, room changed after a call, cross-branch entry 404, and the
   historical-row read path.
5. Client: nothing — `entry.room` already flows to the engine.

## 5. Governance and skill compliance (`.clinerules` §6)

- **Domains (§4):** Database schema/migrations and multi-tenant data → `saas-multitenant-data.md` §4–5.
  Applied by **not** making the change: no ad-hoc schema modification, no unverified migration.
- **Skills:** none installed (§5) — none claimed.
- **Non-negotiables (§3):** no invented field, no invented business rule, blocker recorded rather than
  bypassed; the tenant key is untouched.
- **Evidence:** every statement in §1 cites a file and line opened in this session.
