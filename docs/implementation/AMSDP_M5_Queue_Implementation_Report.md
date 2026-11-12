# AMSDP M5 Queue Management Implementation Report

**Date:** 8 November 2026
**Status:** COMPLETE

---

## 1. Features Implemented

| Feature | Status |
|---------|--------|
| Queue persistence (PostgreSQL via SQLAlchemy) | ✅ |
| Check-in for booked appointments | ✅ |
| Duplicate/invalid check-in prevention | ✅ |
| Walk-in registration (4 policies) | ✅ |
| Role-based authorization | ✅ |
| Unique daily token generation (concurrency-safe) | ✅ |
| Manual queue reordering with position history | ✅ |
| Waiting/consultation status transitions | ✅ |
| Doctor consultation start/complete | ✅ |
| Cancellation/no-show handling | ✅ |
| Tenant/branch isolation | ✅ |
| Persistence across container restart | ✅ |
| Frontend — receptionist & doctor workflows | ✅ |

## 2. Files Changed / Created

| File | Change |
|------|--------|
| `backend/queuing/main.py` | Full rewrite — PostgreSQL + auth (405 lines changed) |
| `backend/queuing/Dockerfile` | New build context (uses `common/`) |
| `backend/queuing/requirements.txt` | Added sqlalchemy, psycopg2, pyjwt, bcrypt |
| `backend/queuing/tests/test_queue.py` | New M5 test suite (336 lines) |
| `backend/common/models.py` | Added `QueueSequence` concurrency model |
| `backend/common/permissions.py` | Added `queue.checkin`, `queue.manage`, `queue.consult` |
| `backend/alembic/versions/ccf34da72c1b_add_queue_sequences.py` | New migration |
| `frontend/pages/queue.js` | Full rewrite — receptionist + doctor workflows |
| `docker-compose.yml` | Queuing build context + env |

## 3. Database Migration

Migration `ccf34da72c1b` — added `queue_sequences` table:

| Column | Type | Notes |
|--------|------|-------|
| doctor_id | VARCHAR | PK, FK → doctors |
| date | DATE | PK |
| last_value | INTEGER | Atomic daily counter |

The `QueueSequence` table powers the **atomic UPSERT** token generator: concurrent enqueues each receive a unique daily sequence value.

## 4. API Endpoints

| Endpoint | Method | Permission | Purpose |
|----------|--------|------------|---------|
| `/api/v1/queue` | GET | any authenticated | View live queue (org+branch scoped) |
| `/api/v1/queue/check-in` | POST | `queue.checkin` | Check in a booked appointment → queue |
| `/api/v1/queue/enqueue` | POST | `queue.checkin` | Walk-in / extra entry |
| `/api/v1/queue/{entry_id}` | PATCH | `queue.manage`/`queue.consult` | Status transitions |
| `/api/v1/queue/reorder` | POST | `queue.reorder` | Manual reorder with position history |
## 5. Walk-in Policies (all four)

| Policy | Behavior |
|--------|----------|
| `end_of_queue` | Appended at next sequence position |
| `first_come` | Append in arrival order (sequence ordering) |
| `reserved_capacity` | Accepted; capacity-aware allocation hook |
| `staff_placement` | Staff supplies explicit `position` |

## 6. Status Lifecycle (queue entries)

```
waiting → call → called → start_consultation → in_consultation → complete_consultation → completed
  └─→ cancel (reason required) → cancelled
  └─→ mark_no_show → no_show
waiting ⇄ skipped (reinsert)
```

Terminal: completed / cancelled / no_show. Completing consultation also marks the linked appointment COMPLETED.

## 7. Security

- **Authentication:** every endpoint requires a JWT; no token → 401.
- **RBAC:** per-action permission checks via the shared matrix.
- **Tenant isolation:** all queries filter by `auth.organization_id`; cross-org IDs → 404.
- **Branch scope:** branch-scoped roles restricted to their branch; super/org admins across branches.

## 8. Automated Test Results

### Queue tests — 17/17 PASS
Check-in create + duplicate rejection + completed-appointment rejection; 4 walk-in policies + invalid policy; unique tokens; reorder preserves token with position history; lifecycle transitions; invalid transition 422; receptionist/doctor authorization; 401 no-token; cross-org 404; DB-reopen persistence.

### Identity regression — 13/13 PASS

### Live Docker e2e — 14/14 PASS
login → list doctors/patients → create+confirm appointment → check-in → queue view → walk-in → reorder → start → complete → history → invalid transition 422 → unauth 401.

### Concurrency — PASS
20 concurrent enqueues → 20 created, 20 unique tokens, 20 unique positions.

### Persistence — PASS
`docker restart amsdp-queuing-1` → history intact (token, position history, actor, appointment link).

## 9. Frontend (`/queue`)

Receptionist: doctor+date selectors, live queue table, move up/down reorder, start consultation, cancel-with-reason, complete; **Check-in** modal (picks bookable appointments); **Walk-in** modal (existing patient + 4-policy selector).
Doctor: same page with Start Consultation / Complete actions.
Loading, empty, error states included. All actions call real APIs.

Verified HTTP 200: `/dashboard`, `/appointments`, `/patients`, `/doctors`, `/queue`.

## 10. Live Docker State

All 10 services running (queuing on 8116; identity 8110; org 8111; patient 8112; doctor 8113; scheduling 8114; appointment 8115; audit 8117; frontend 3100; db 5433). Ports 5432/3000 untouched.

## 11. Remaining Gaps

| Gap | Priority |
|-----|----------|
| Token numbering config (doctor vs room) not surfaced in UI | Low |
| Frontend reschedule/transfer buttons pending (APIs exist) | Low |
| Audit events not emitted by queue service (audit still in-memory) | Medium |
| Reserved-capacity walk-in allocation sequential, not quota-aware | Medium |
| `/api/v1/queue/history` | GET | any authenticated | Full status/position history |