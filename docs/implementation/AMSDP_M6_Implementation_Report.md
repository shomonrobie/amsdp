# AMSDP M6 Implementation Report

**Date:** 8 November 2026
**Status:** COMPLETE — waiting for project-owner acceptance

---

## 1. Batch 0 — Mandatory Corrections

### 1.1 Consultation permissions
- Removed `queue.consult` from `receptionist` in `backend/common/permissions.py`.
- Consultation start/complete remain available to `doctor`, `org_admin`, `branch_admin`, `super_admin`.
- Backend enforced via `require_permission("queue.consult")`; frontend `/queue` renders Start/Complete only when `can('queue.consult')`.
- **Negative tests added:** receptionist start → 403, receptionist complete → 403. Receptionists **cannot** perform consultation actions.

### 1.2 Audit foundation
- New `backend/common/audit.py` — `record_audit(session, *, service, org_id, action, target_type, target_id, actor_id, actor_role, branch_id, before, after, reason)` writing transactionally to `audit_events`.
- Migration `c7d3601e2486` added `audit_events.branch_id`.
- Queue service records audit for check-in, enqueue, reorder (before/after), start/complete, cancel, no-show; actor/role always token-derived.
- Verified live: check-in→start→complete produced `queue.checkin`, `queue.start_consultation`, `queue.complete_consultation` events retrievable via the audit API.

### 1.3 Reserved-capacity configuration
- New `backend/common/config.py` (`walk_in_reserve_mode`: percent|count, `walk_in_reserve_value`).
- **Default disabled** (value 0) — booking unchanged (verified `reserved_walkin: 0`, `unreserved_capacity == max_patients`).
- When enabled: `available-slots` reports `reserved_walkin`/`unreserved_capacity`/`available_unreserved`; appointment creation enforces the unreserved ceiling with the atomic COUNT.
- No unauthorized business-rule change.

## 2. Batch 1 — Shared Frontend Foundation

| Deliverable | File |
|-------------|------|
| AppShell (sidebar, header, breadcrumbs, role-aware nav, responsive drawer) | `components/AppShell.js` |
| i18n (centralized bn/en + formatting) | `lib/i18n.js` |
| Auth/session utilities (`getUser`, `apiFetch`, `can`, `signOut`) | `lib/auth.js` |
| DataTable (loading/empty/error/table) | `components/ui/DataTable.js` |
| Modal (focus, Escape, role=dialog) | `components/ui/Modal.js` |
| ConfirmDialog (optional reason) | `components/ui/ConfirmDialog.js` |
| StatusBadge | `components/ui/StatusBadge.js` |
| Alert states (error/success/loading/empty/permission-denied/RequireLogin) | `components/ui/Alert.js` |
| AppShell styles + responsive `@media` rules | `styles/global.css` |

All 10 authenticated pages refactored onto the shell (dashboard, queue fully rebuilt; patients, doctors, staff, orgs, branches, schedules, appointments wrapped) plus new **audit** page. No page is isolated from navigation anymore.

## 3. Batches 2–6 — Dashboard, Audit, Rollups

### Backend endpoints (org-scoped, token-authenticated, real DB counts)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/dashboard/today` | GET | Today counts + walk-in split + live queue length + per-doctor breakdown (`doctor_id`/`branch_id` filters) |
| `/api/v1/dashboard/period` | GET | Period totals, disposition, completion/no-show/cancel rates, avg queue wait, walk-in total |
| `/api/v1/dashboard/audit` | GET | Audit search/filter (action, target, actor, branch, date, paginated) |

Router in `backend/appointment/dashboard.py`, mounted in the appointment app; proxy rewrites `/api/v1/dashboard/*`.

### Pages
- **Dashboard** (`/dashboard`): today's metric cards from `/dashboard/today`; loading/empty/error states; role-aware.
- **Audit** (`/audit`): filterable event table; `audit.read`-gated with permission-denied state.
- **Queue/Appointments** rebuilt on shared components.

## 4. Skills Actually Used (evidence)

- **Project instructions:** `.clinerules` read and applied (no destructive git; no secrets; routing policy).
- **Tools used:** repository read/search, editor, shell/Docker, python test execution. All M6 code is in the working tree.
- **No skill-library exists** in the repo (searched). The local `qwen2.5-coder:1.5b` option remains unused — M6 was implemented directly by the agent (per Frontier escalation policy).

## 5. Security & Audit Verification

- Tenant isolation: today/period/audit filter by `auth.organization_id`; cross-org token → empty results (tested).
- Audit events with token-derived actor/role + org/branch (tested + live).
- Consultation permissions locked to doctor+admins (backend 403 + UI hidden).
- All dashboard endpoints require auth (401 without token, tested).

## 6. Dashboard Metrics — Data Sources

All values from PostgreSQL aggregate queries over `appointments`, `queue_entries`, `audit_events`. No mock/cached figures.

## 7. Automated Test Results

| Suite | Result |
|-------|--------|
| `tests/test_dashboard.py` (today counts, period rates, audit filters, cross-org, 401) | **6/6 PASS** |
| `queuing/tests/` (incl. negative consultation permissions + audit assertion) | **20/20 PASS** |
| `identity/tests/` | **13/13 PASS** |
| **Total** | **39/39 PASS** |
| Live Docker e2e workflow | **14/14 PASS** |
| Live dashboard pipeline (book→check-in→consult→metrics+audit) | PASS |

## 8. Remaining Gaps

| Gap | Notes |
|-----|-------|
| Branch switch control on dashboard UI | API supports `branch_id`; AppShell shows org context; explicit switcher deferred |
| Staff↔doctor profile linkage | Doctor sees org-wide today + per-doctor variants; formal link is future work |
| Some dashboard card labels remain English | Central i18n registry in place; label sweep pending |
| Audit capture is queue-centric | Appointment/org audit writes can be added incrementally (helper ready) |
| Reserved-capacity UI toggle | Config is API/DB-driven; org-settings screen not built |

## 9. Files Changed (M6)

- `backend/common/permissions.py`, `backend/common/audit.py` (new), `backend/common/config.py` (new), `backend/common/models.py`
- `backend/alembic/versions/c7d3601e2486_add_audit_branch.py` (new)
- `backend/queuing/main.py`, `backend/queuing/tests/test_queue.py`
- `backend/appointment/main.py`, `backend/appointment/dashboard.py` (new), `backend/tests/test_dashboard.py` (new)
- `backend/scheduling/main.py`
- `frontend/lib/i18n.js`, `frontend/lib/auth.js` (new), `frontend/components/AppShell.js` (new), `frontend/components/ui/*` (new)
- `frontend/pages/*.js`, `frontend/styles/global.css`, `frontend/next.config.js`

## 10. Constraints Honoured

Ports unchanged (8110–8117, 3100, 5433); 5432/3000 untouched; no DB deletion/reset; no AILI changes; nothing committed/pushed; all uncommitted work preserved.
No fabricated metrics — verified that completing a real appointment changed dashboard totals and produced audit rows.