# AMSDP M4 Appointment Implementation Report

**Date:** 7 November 2026
**Status:** COMPLETE

---

## 1. M3 Integration Gaps Closed

| Gap | Status | Notes |
|-----|--------|-------|
| Build org/patient/doctor Docker images | ✅ | All 3 built with updated Dockerfiles |
| Start full stack | ✅ | All 10 services running |
| Service reqs updated | ✅ | pyjwt, bcrypt added to all services |
| Frontend builds | ✅ | 10/10 pages compile |

## 2. Scheduling Service (PostgreSQL)

**File:** `backend/scheduling/main.py` — full SQLAlchemy rewrite

| Feature | Status |
|---------|--------|
| Schedule creation with auth | ✅ |
| Search/filter by doctor/branch | ✅ |
| Weekly templates (time-slot, serial, hybrid models) | ✅ |
| Available-slot from actual appointment counts | ✅ |
| DB-level capacity enforcement (atomic COUNT) | ✅ |
| All 3 appointment models | ✅ |

## 3. Appointment Service (PostgreSQL)

**File:** `backend/appointment/main.py` — full lifecycle rewrite

| Feature | Status |
|---------|--------|
| Create + capacity check (DB atomic, schedule-based) | ✅ |
| BR §18 lifecycle (10 statuses) with server-side transition validation | ✅ |
| Cancel with required reason | ✅ |
| Reschedule with linked history | ✅ |
| Check-in → IN_QUEUE + auto queue entry | ✅ |
| No-show (staff confirmed) | ✅ |
| Same-org transfer | ✅ |
| Walk-in registration (appointment source) | ✅ |
| Token/serial generation | ✅ |
| Booking source tracking | ✅ |
### BR §18 Status Lifecycle

```
BOOKED → AWAITING_CONFIRMATION → CONFIRMED → CHECKED_IN → IN_QUEUE → IN_CONSULTATION → COMPLETED
         ↓                       ↓            ↓            ↓
       CANCELLED              CANCELLED    CANCELLED    CANCELLED
       RESCHEDULED          RESCHEDULED  RESCHEDULED  RESCHEDULED
                                            ↓
                                         NO_SHOW
```

Terminal: COMPLETED, CANCELLED, NO_SHOW, RESCHEDULED — no further transitions.

## 4. Walk-in Support

Walk-in = `appointment_type: "walk_in"`, `booking_source: "walk_in"`, initial status CONFIRMED.

Four policies (config-ready):
1. **End of queue** — default
2. **First-come, first-served**
3. **Reserved capacity**
4. **Staff placement**

## 5. Frontend

| Page | Route | Functionality |
|------|-------|---------------|
| Schedules | `/schedules` | List, create, view available slots with real-time capacity |
| Appointments | `/appointments` | List w/ date/doctor filter, book, walk-in, action buttons, check-in w/ auto-queue |

Actions shown by status: Confirm, Check-In, Start Consultation, Complete, Cancel.

## 6. API Endpoints Added

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/schedules` | POST/GET | CRUD |
| `/api/v1/schedules/{id}` | GET/PATCH | CRUD |
| `/api/v1/schedules/{id}/available-slots` | GET | Real capacity |
| `/api/v1/appointments` | POST/GET | CRUD w/ capacity check |
| `/api/v1/appointments/{id}` | GET | Details |
| `/api/v1/appointments/{id}/status` | PATCH | Lifecycle transition |
| `/api/v1/appointments/{id}/cancel` | POST | Cancel w/ reason |
| `/api/v1/appointments/{id}/check-in` | POST | Check-in + auto queue |
| `/api/v1/appointments/{id}/reschedule` | POST | Linked reschedule |
| `/api/v1/appointments/{id}/transfer` | POST | Same-org transfer |
| `/api/v1/appointments/{id}/no-show` | POST | Staff no-show |
| `/api/v1/appointments/walk-in` | POST | Walk-in register |

## 7. Running Services

All 10 containers run: db, identity, organization, patient, doctor, scheduling, appointment, queuing, audit, frontend. Ports 8110-8117 and 3100.

Port 5432 and 3000 remain untouched. ✅

## 8. Known Limitations

| Issue | Priority | Notes |
|-------|----------|-------|
| Queuing service still in-memory | High | M5 scope |
| Audit service still in-memory | High | M5 scope |
| Formal concurrency test needed | Medium | DB atomic count works; dedicated test pending |
| Reschedule/transfer/no-show frontend | Low | API exists, UI buttons pending |

## 9. Diff Summary

**M4 changes:** ~1700 lines across scheduling, appointment, frontend, Docker.

**Key files:** `backend/scheduling/main.py`, `backend/appointment/main.py`, `frontend/pages/schedules.js`, `frontend/pages/appointments.js`.

---

**M4 complete. Ready for M5 authorization — queue operations.**

---

## 10. Later extension — optional symptoms and onset (AMSDP-SYMPTOM-01, 2026-11-16)

This report documents the M4 appointment service as it was built. A later task
added an **optional** symptom-recording capability inside the same booking flow.
It is recorded here so this report does not read as the current state of the
service without it; the full account is
`docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md`.

| Area | What was added |
|---|---|
| Database | `symptom_catalog` (org-owned bilingual catalogue), `appointment_symptoms` (one row per recorded symptom, `kind` = catalogue \| free_text, with a booking-time name snapshot), and `appointments.symptom_onset_code` / `.symptom_onset_note`. Migration `b3d7e91f6a24`. |
| Endpoints | `GET /api/v1/symptoms` and `GET /api/v1/symptoms/onset-options` (both `symptom.read`). |
| Booking | `POST /api/v1/appointments` and `POST /api/v1/appointments/walk-in` accept four optional fields: `symptom_ids`, `symptom_texts`, `symptom_onset`, `symptom_onset_note`. |
| Responses | Every appointment payload now carries `symptoms[]`, `symptom_onset`, `symptom_onset_note`. |
| Lifecycle | Reschedule and transfer copy the recorded symptoms and onset to the new appointment; the original rows stay with the original visit. |
| Audit | `appointment.created` / `appointment.walk_in_created` add `symptom_count`, `symptom_ids`, `symptom_text_count`, `symptom_onset` — never the free text. |

What did **not** change: the §18 status lifecycle, capacity enforcement, the
token/serial authority, walk-in placement, the chamber resolution and the
existing booking contract — a booking with no symptoms behaves exactly as
before, which the M4 test module still proves (25 tests) alongside the 25 new
ones.
