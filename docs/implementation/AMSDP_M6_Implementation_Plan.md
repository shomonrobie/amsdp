# AMSDP M6 Implementation Plan

**Date:** 8 November 2026
**Status:** Proposal for project-owner authorization (implementation not started)

Related documents:
- `docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md`
- `docs/implementation/AMSDP_M5_Queue_Implementation_Report.md`

---

## Part A — M5 Outstanding Issues (Review)

### A.1 Reserved-capacity walk-in policy

**Current behavior (verified):** accepted by `POST /api/v1/queue/enqueue` but treated as sequential end-of-queue (`position = seq` unless `staff_placement`). No capacity is actually reserved.

**Proposed quota-aware implementation (consistent with BR §25.3 and §23):**
1. Org/branch `queue_config` (in existing `config` JSON): `walk_in_reserve_mode: "count"|"percent"`, `walk_in_reserve_value`, optional per-schedule `slot_templates[].reserved_walkin`.
2. Scheduling `available-slots` computes booked vs unreserved capacity per slot/serial.
3. Appointment creation enforces the unreserved ceiling (atomic COUNT from M4); walk-ins under `reserved_capacity` draw from the reserved band.
4. Overbooking permission (BR §22) still applies with reason + audit.
5. `available-slots` returns reserved vs unreserved so the UI can show "X walk-in seats left".

**Decision requested:** approve default `reserve_mode=%` value 0 (disabled) so behavior is unchanged until configured — no silent rule change.

### A.2 Audit integration (M6)

- Persistent `audit_events` table already exists (M1 schema).
- **Plan:** `common/audit.py` helper (`record_audit(...)`) called from the queue service for check-in, enqueue, reorder (before/after positions), consultation start/complete, cancel, no-show.
- Same-DB transactional writes (single-writer pattern already in use); the audit HTTP service adds read/search; no broker/outbox in M6.
- `actor_id`/`actor_role` always from the token; events carry `organization_id`.

### A.3 Consultation permissions (verification result)

**Current:** `receptionist` holds `queue.consult` (M5) → a receptionist can start/complete consultations. **Deviation** from the approved doctor-only assignment.

**Proposed correction (M6 batch 0):**
- Remove `queue.consult` from receptionist; keep for doctor; `queue.*` retained for admin roles.
- UI renders Start/Complete only for doctor/admin; receptionist keeps reorder/checkin/cancel/no-show.
- Update tests (doctor fixture) + add negative test: receptionist → 403 on consultation actions.

### A.4 Reschedule and transfer (frontend work required)

M4 APIs (verified live):
- `POST /api/v1/appointments/{id}/reschedule` — `{new_date, new_start_time?, reason}` → linked appointment; original → RESCHEDULED; requires `appointment.modify`.
- `POST /api/v1/appointments/{id}/transfer` — `{new_doctor_id, new_branch_id, new_date, new_start_time?, reason}`; within-org; requires `appointment.modify`.

**Frontend work:** Reschedule + Transfer actions on appointment rows (gated by `appointment.modify`); modals for date/time/doctor/reason; show linked appointment (`rescheduled_to/from`); shared-component states.

### A.5 Room-based token numbering (documented gap)

- Sequences keyed `(doctor_id, date)`; no room entity in Phase-1 scope (rooms are Phase 2 per BR §31/blueprint).
- Token numbering per doctor is the Phase-1 default; room-scoped numbering is a Phase-2 configuration item; `queue_sequences` remains extensible. No rule change; no room model built in M6.
## Part C — M6 Implementation Plan

### Batch 0 — M5 corrections (small)
1. Remove `queue.consult` from receptionist; gate queue UI; update tests (A.3).
2. Add `common/audit.py` helper; wire queue-side audit writes (A.2 foundation).

### Batch 1 — Shared frontend foundation (from assessment)
- `components/AppShell.js` — role-aware sidebar, header w/ org/branch context + locale toggle + logout, breadcrumbs, responsive drawer. Wraps all pages.
- `lib/i18n.js`, `lib/auth.js` (`useAuth`, `apiFetch`, `RequireLogin`, `Permission`).
- `components/ui/` — `DataTable`, `Modal`, `ConfirmDialog`, `StatusBadge`, `Alert`, `FormDialog`.
- Refactor existing pages onto the shell/components; a11y pass (focus trap, aria, aria-live); responsive rules + `.table-wrap`.

### Batch 2 — Dashboard backend (real metrics, no fabrication)
Authenticated, org/branch/role-scoped aggregate endpoints (PostgreSQL):
- `GET /api/v1/dashboard/today` — scheduled/confirmed/checked-in/waiting/consulting/completed/cancelled/no-show + walk-in split + queue length per doctor.
- `GET /api/v1/dashboard/today?doctor_id=` — doctor variant.
- `GET /api/v1/dashboard/period?from&to&branch_id?` — volumes, status disposition, completion rate, avg wait, no-show rate.
- `GET /api/v1/dashboard/audit?filters` — search/filter persistent audit events.
All numbers from live DB counts.

### Batch 3 — Receptionist dashboard
- Today overview cards, recent queue activity, quick actions (check-in/walk-in) reusing existing queue APIs; full state matrix; bn/en.

### Batch 4 — Doctor dashboard
- Personal today queue snapshot, start/complete shortcuts (doctor-scoped, server-enforced per A.3), scheduled patients today, period stats.

### Batch 5 — Audit UI + admin surface
- Audit search/filter page (action, target, actor, org, branch, date range), read-only, `audit.read` gated, paginated; org/branch metric filter controls.

### Batch 6 — Org/branch-level metrics
- Org rollups + doctor aggregates for org/branch admins; branch switch integrated with AppShell context.

### Testing
- Backend: aggregate endpoint tests, isolation/permission tests, audit row assertions.
- Frontend: build + live integration (login → dashboard → today metrics → audit search).
- Live: full stack, receptionist + doctor personas, metrics match direct API counts.

### Localization
- New strings in shared i18n registry; persist locale preference; `Intl.DateTimeFormat` for dates/counts.

---

## Part D — Mandatory Engineering Standards (M6)

1. **Use existing shared UI components; extend, don't duplicate.**
2. **Consistent design system** — tokens from `global.css`; inline styles only for one-off exceptions.
3. **Use relevant available skills** — per `.clinerules` routing.
4. **Frontend and backend developed together** in each batch.
5. **Real APIs and PostgreSQL-backed data only** — no mock metrics.
6. **State matrix on every new screen:** loading / empty / error / permission-denied.
7. **Accessibility and responsive behavior preserved.**
8. **No fabricated metrics** — every dashboard value from a reviewed aggregate endpoint.

## Constraints

- M6 implementation **not** started — awaiting authorization.
- No AILI changes; ports unchanged (8110–8117, 3100, 5433); no DB volume deletion/reset; no commits/pushes; all uncommitted work preserved.