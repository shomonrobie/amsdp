# AMSDP Phase 0 MVP Scope + Phase 1 Operational RBAC Implementation Report V1.0

**Document ID:** `AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md`
**Version:** V1.0
**Recorded date:** 2026-11-17 (date this task was executed)
**Repository:** `shomonrobie/amsdp`
**Branch:** `hackathon-mvp`
**Starting commit:** `7c039fa68835b84fa371cf8fa2c64e3658a5bf2a`
**Final commit:** `7c039fa68835b84fa371cf8fa2c64e3658a5bf2a` (unchanged — no commit made)
**Commit/push:** None (not authorized; no commit or push performed)

---

## A. Starting repository state

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` |
| Starting HEAD | `7c039fa68835b84fa371cf8fa2c64e3658a5bf2a` (matches the confirmed reference commit) |
| Working-tree state | 1 modified file, 3 untracked files (all preserved) |
| Modified (pre-existing) | `docs/governance/AMSDP_Docs_Index_V1.0.md` (pre-existing local modification, left untouched) |
| Untracked (pre-existing, preserved) | `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` |
| Untracked (pre-existing, preserved) | `docs/implementation/AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md` |
| Untracked (pre-existing, preserved) | `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` |

No destructive Git operations were performed. No branch was switched. No commit or push was made. All unrelated local work was preserved.

---

## B. Phase 0 documentation outcome

**File updated:** `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`

### B.1 Final disposition (all 26 features)

| Disposition | Count | Features |
|---|---:|---|
| KEEP | 25 | ORG-001, ORG-002, FAC-001, DOC-001, DOC-002, APT-001, APT-002, APT-003, APT-004, PAT-001, QUE-001, QUE-002, QUE-003, QUE-004, QUE-005, QUE-006, RBAC-001, RBAC-002, RBAC-003, DSH-001, AUD-001, L10N-001, PQT-001, DQDS-001, SYM-001 |
| DEFER | 1 | NOT-001 |
| REMOVE | 0 | — |
| Total | 26 | Section D (ORG-001 through SYM-001) |

- **SYM-001 is KEEP** — explicitly confirmed. Free-text complaint support is implemented in `backend/appointment/symptoms.py` (`symptom_texts`, `kind == "free_text"`) and covered by 25 symptom integration tests plus 9 catalogue data tests (per the catalogue's SYM-001 entry). Recorded as KEEP with no outstanding removal; implementation/verification status left evidence-based (IMPLEMENTED / TESTED + BUILD VERIFIED, not ACCEPTED).
- **QUE-006 is KEEP** — confirmed as an approved AMSDP Core MVP capability (Intelligent Queue Voice Announcements, Bangla/English, in-facility audible callouts only). It is **not** outbound telephone calling or patient phone reminders. Its implementation and verification status remain independent of this scope approval (NOT STARTED / NOT TESTED, no TTS provider or audio code).
- **NOT-001 is the only DEFER** — deferred to a future release.
- No feature was marked ACCEPTED merely because it is KEEP (scope approval ≠ implementation acceptance).
- No IMPLEMENTED / PARTIALLY IMPLEMENTED / NOT STARTED / TESTED / BUILD VERIFIED / BROWSER VERIFIED / ACCEPTED status was changed without supporting evidence.

### B.2 Corrections made to the catalogue

| # | Section | Correction |
|---|---|---|
| 1 | A.3 | "All decision checkboxes are left unchecked" → decisions now recorded in section D and section I (25 KEEP, 1 DEFER). |
| 2 | D | All 26 decision boxes checked: 25 `[x] KEEP`, NOT-001 `[x] DEFER`. PO comments/reason column left empty per feature (decision recorded in section I). |
| 3 | H | Readiness summary updated: KEEP 25, REMOVE 0, DEFER 1 (NOT-001), awaiting decisions 0. |
| 4 | G.3 | Wording corrected: decisions apply to **all 26 features listed in section D** (ORG-001 through SYM-001), not merely "ORG-001 through QUE-006". QUE-006 Core clarification retained. |
| 5 | I | Dated product-owner decision entry added (recorded date 2026-11-17): 25 KEEP, 1 DEFER (NOT-001), SYM-001 explicitly KEEP, QUE-006 KEEP as an approved Core capability. |

### B.3 Remaining documentation inconsistencies
None known to remain unresolved from this task. Section E acceptance checklists remain unchanged (acceptance criteria describe what must hold if kept; checkboxes deliberately left unchecked, consistent with "ACCEPTED requires Product Owner action").

---

## C. Phase 1 implementation outcome

### C.1 Scope
Operational RBAC only (tenant plane). Roles: `org_admin`, `branch_admin`, `receptionist`, `doctor`, `assistant`. Legacy `super_admin` compatibility preserved (not expanded, not removed). No SaaS Platform RBAC introduced (no `platform_admin`/`platform_ops`/`platform_support`, no platform identity, no platform MFA, no support grants, no lifecycle enforcement).

### C.2 Shared fix
Added `common.auth.branch_accessible(auth, branch_id)` (`backend/common/auth.py`): `org_admin` and `platform.cross_org` callers may act on any branch; branch-scoped actors must match their token's branch; a `None` target imposes no constraint. Cross-branch mismatches answer non-disclosing 404. Organization scope is enforced separately by existing queries (`organization_id == auth.organization_id`).

### C.3 Per-defect detail

| # | Feature | Endpoint / helper | Root cause | Code changes | Test added | Test result |
|---|---|---|---|---|---|---|
| P0-1 | QUE-004 | `_scoped_entry_or_404()` (`queuing/main.py`) used by `PATCH /api/v1/queue/{entry_id}` | Checked org only, not branch | Added `branch_accessible(auth, entry.branch_id)` check; cross-branch → 404 | `TestQueueBranchAuthorization.test_p0_1_cross_branch_entry_denied` | 28 passed |
| P0-2 | QUE-003 | `GET /api/v1/queue` (`queuing/main.py`) | Caller-supplied `branch_id` filtered without authorization | Validate caller-supplied `branch_id` via `branch_accessible` before filtering; unauthorized → 404; org-admin org-wide preserved | `test_p0_2_queue_list_rejects_foreign_branch`, `test_p0_2_queue_list_org_admin_org_wide` | 28 passed |
| P0-3 | QUE-001 | `POST /api/v1/queue/check-in` (`queuing/main.py`) | Caller-supplied `branch_id` in body used directly | Check-in pinned to appointment's stored branch; body `branch_id` != appointment branch rejected (404); caller must be authorized for appointment's branch | `test_p0_3_check_in_rejects_foreign_branch` | 28 passed |
| P0-4 | QUE-002 | `POST /api/v1/queue/enqueue` (`queuing/main.py`) | Caller-supplied `branch_id` in body used directly | Validate caller-supplied `branch_id` via `branch_accessible`; fallback is caller's own token branch; org-admin org-wide preserved | `test_p0_4_enqueue_rejects_foreign_branch`, `test_p0_4_enqueue_org_admin_org_wide` | 28 passed |
| P0-5 | QUE-005 | `POST /api/v1/queue/reorder` (`queuing/main.py`) | Org-only filter; no queue homogeneity | Validate every entry: reorderable status, branch accessible, all share one branch/doctor/date; raise before mutation (no partial apply); cross-branch entry → 404, mixed queue → 422 | `test_p0_5_reorder_rejects_mixed_branch`, `test_p0_5_reorder_same_branch_succeeds` | 28 passed |
| P0-6 | DOC-002 | `POST /api/v1/schedules` (`scheduling/main.py`) | `branch_id` from body, no `require_branch_access`; no doctor/branch org validation | Validate caller branch scope (`branch_accessible`); doctor and branch must belong to caller's organization; `organization_id` from token only; doctor multi-branch preserved | `test_p0_6_create_schedule_rejects_foreign_branch`, `test_p0_6_create_schedule_own_branch_succeeds`, `test_p0_6_create_schedule_org_admin_org_wide`, `test_p0_6_create_schedule_foreign_doctor_404` | 28 passed |

Additional finding fixed:
| Finding | Endpoint | Fix | Test | Result |
|---|---|---|---|---|
| 8.2 | `GET /api/v1/schedules` | Caller-supplied `branch_id` validated via `branch_accessible`; org-admin org-wide preserved | `test_8_2_list_schedules_rejects_foreign_branch`, `test_8_2_list_schedules_org_admin_org_wide` | 28 passed |

### C.4 Existing legitimate role behavior preserved
- `org_admin`: organization-wide queue/schedule access retained (tested).
- `branch_admin`/`receptionist`/`doctor`/`assistant`: restricted to token branch for queue/schedule resources (tested).
- `super_admin`: legacy alias, permissions, and access paths unchanged; not expanded.
- Queue/room/doctor overlap protections in scheduling left intact (no new overlap logic added or removed).
- Recovery endpoint (`recovery.py`) already correctly branch-scoped; unchanged.

---

## D. Additional findings

| Finding | Classification | Evidence | Code changed? | Reason |
|---|---|---|---|---|
| 8.1 Patient update `patient.create` vs `patient.update` | NEEDS PRODUCT DECISION (not implemented) | `patient/main.py:195` uses `require_permission("patient.create")` on PATCH; `patient.update` only held by `org_admin`/`branch_admin` via `patient.*` wildcard; receptionist holds `patient.create` | No | Correct role policy unclear (whether receptionists may update patients); changing it would narrow access. Left blocked for product-owner decision. |
| 8.2 Schedule listing scope | VERIFIED DEFECT (fixed) | `GET /api/v1/schedules` accepted caller `branch_id` without scope check | Yes | Branch-scoped actors could list another branch's schedules in same org. |
| 8.3 Appointment modification scope | NOT A DEFECT (for this task) | `PATCH /status`, cancel, reschedule, and check-in look appointments up by org via stored snapshot; org_admin org-wide, branch-scoped callers limited by queue entry branch on mutation | No | No confirmed unauthorized cross-branch mutation path requiring change; legitimate cross-branch org-admin behavior preserved. |
| 8.4 Staff registration scope | NOT IMPLEMENTED (reported unresolved) | `create_staff_user` accepts caller `branch_id` and any role (incl. `super_admin`) with `staff.manage`; no self-escalation/last-admin rule | No | No existing approved role-assignment or last-admin rule; introducing one would be new policy. |
| 8.5 Appointment creation | NOT A DEFECT | Branch derived from resolved schedule/clinic or `auth.branch_id`; doctor/schedule resolved within caller's org | No | Organization/branch already validated against authenticated scope via `_resolve_location`. |
| 8.6 Queue history | NOT A DEFECT | `GET /api/v1/queue/history` filters by org + doctor/date; `branch_id` query filtered | No | Already org-scoped; branch filter applied (no caller escalation path). |
| 8.7 Route inventory | NOT A DEFECT | Queue recovery route is `POST /api/v1/queue/recover` (verified in `queuing/recovery.py` router), not GET | No | Report's GET-vs-POST discrepancy resolved by inspecting the actual route; recovery already correctly branch-scoped. |
| 8.8 Reserved findings (EQ-4/EQ-5/EQ-7) | DEFERRED (not implemented) | Per task instruction | No | Out of scope for operational RBAC. |

---

## E. RBAC behavior (verified on repaired paths only)

Verified endpoints: queue call/cancel/recover/reposition (`PATCH /queue/{id}`), queue list (`GET /queue`), queue check-in (`POST /queue/check-in`), queue enqueue (`POST /queue/enqueue`), queue reorder (`POST /queue/reorder`), schedule creation (`POST /schedules`), schedule listing (`GET /schedules`).

| Role | Verified behavior |
|---|---|
| `org_admin` | Organization-wide queue and schedule access across branches (same org); may create/enqueue/list at any branch in org. |
| `branch_admin` | Restricted to token branch; cross-branch queue/schedule access denied (404). |
| `receptionist` | Restricted to token branch; may check in/enqueue own branch's appointments; cross-branch denied (404). |
| `doctor` | Restricted to token branch on queue mutation; consultation actions on own branch's entries. |
| `assistant` | Read-only queue/view scope; no mutating queue permissions. |
| Legacy `super_admin` | Alias, permissions, and access paths preserved unchanged (cross-org via `platform.cross_org`, audited); not expanded. Not comprehensively retested across every endpoint. |

**Caveat:** Roles were verified on the repaired endpoints above only; this is not a comprehensive role × endpoint matrix.

---

## F. Verification results

Commands run from `backend/` with `.env` sourced (`POSTGRES_PASSWORD`):

| Command | Result |
|---|---|
| `python3 -m pytest queuing/tests/test_queue.py -q` | **28 passed** (20 pre-existing + 8 new P0 tests) |
| `python3 -m pytest scheduling/tests/test_scheduling.py -q` | **28 passed** (22 pre-existing + 6 new P0/8.2 tests) |
| `python3 -m pytest tests/test_security.py patient/tests/ identity/tests/ -q` | **59 passed** (security 25, patient 16, identity 18) |
| `python3 -m pytest appointment/tests/ -q` | **108 passed** (pre-existing single failure did not reproduce on this isolated run; no appointment code changed) |

No tests were fabricated. No browser verification was performed or claimed. The full combined suite was not run in one invocation because it exceeds the available timeout; affected and related suites were run. No lint/type tooling is configured in the repository (no `ruff`/`flake8`/`mypy` dependency or config), so no lint check was run.

---

## G. Remaining risks

| Risk | Status |
|---|---|
| R-06 `super_admin` conflates platform + tenant | NOT MITIGATED — preserved as legacy compatibility; migration to `org_super_admin` is out of scope |
| R-07 Frontend `super_admin` wildcard bypass | PRESENT (presentation only; not an authorization boundary) |
| R-11 Tenant suspension/access revocation not enforced | NOT ENFORCED (`Organization.status` not checked by endpoints) |
| R-13 Patient update permission mismatch (`patient.create` on PATCH) | NEEDS PRODUCT DECISION — not implemented |
| R-15 Self-escalation on staff role assignment | NOT PROTECTED — no approved rule |
| R-16 Last-active-org-admin protection | NOT PROTECTED — no approved rule |
| R-08/R-09/R-10 SaaS platform identity / MFA / support grants | OUT OF SCOPE (separate SaaS workstream; not implemented) |
| Que-006 voice announcements | NOT STARTED — no TTS/audio implementation; scope approval only |

---

## H. Files changed

**Documentation:**
- `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` — Phase 0 dispositions (25 KEEP / 1 DEFER), corrections A.3/D/G.3/H/I
- `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` — appended §12 dated Phase 1 implementation outcome
- `docs/governance/AMSDP_Docs_Index_V1.0.md` — pre-existing local modification preserved; index row for this report added
- `docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` — this report (new)

**Backend code:**
- `backend/common/auth.py` — added `branch_accessible()` helper
- `backend/queuing/main.py` — P0-1..P0-5 fixes (`_scoped_entry_or_404`, `get_queue`, `check_in_appointment`, `enqueue_patient`, `reorder_queue`)
- `backend/scheduling/main.py` — P0-6 (`create_schedule`) and finding 8.2 (`search_schedules`)

**Tests:**
- `backend/queuing/tests/test_queue.py` — added `TestQueueBranchAuthorization` (8 tests)
- `backend/scheduling/tests/test_scheduling.py` — added `TestScheduleBranchAuthorization` (6 tests)

**Other:** none (no schema, migration, JWT, frontend, or config changes).

---

## I. Final repository state

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` (unchanged) |
| Final HEAD | `7c039fa68835b84fa371cf8fa2c64e3658a5bf2a` (unchanged) |
| Commits created | None |
| Remote changed | None |
| Modified files | `docs/governance/AMSDP_Docs_Index_V1.0.md` (pre-existing, preserved + index row), `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` (was untracked, now edited), `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` (was untracked, now edited), `backend/common/auth.py`, `backend/queuing/main.py`, `backend/scheduling/main.py`, `backend/queuing/tests/test_queue.py`, `backend/scheduling/tests/test_scheduling.py` |
| New files | `docs/implementation/AMSDP_Phase_0_MVP_Scope_and_Phase_1_Operational_RBAC_Implementation_Report_V1.0.md` |
| Working tree | All pre-existing local/untracked work preserved; nothing discarded or reverted |

---

**Acceptance:** Phase 0 complete (25 KEEP / 1 DEFER NOT-001; SYM-001 and QUE-006 KEEP; documentation discrepancies corrected). Phase 1 complete (all six P0 defects fixed; regression tests added and passing; no SaaS Platform RBAC introduced). Nothing committed or pushed.


## Phase 1B — Remaining Operational RBAC Corrections (Recorded 2026-11-17)

### Scope
Three remaining authorization areas (RBAC-R1, RBAC-R2, RBAC-R3) identified during independent review of commit `0eaec02`. All corrections are server-side, preserve existing roles and permission matrix, and introduce no SaaS Platform RBAC.

### RBAC-R1 — Queue enqueue branch ownership
- **File:** `backend/queuing/main.py`
- **Fix:** Enqueue now resolves target branch from body or token branch, requires a valid existing branch belonging to `auth.organization_id`, and checks `branch_accessible()`. Empty, nonexistent, or foreign-tenant branches are rejected with non-disclosing 404.
- **Tests:** `TestQueueEnqueueBranchOwnership` — 7 tests (all passing)

### RBAC-R2 — Complete schedule resource branch authorization
- **File:** `backend/scheduling/main.py`
- **Fix:** 
  - `GET /api/v1/schedules`: branch-scoped users filtered to their token branch when `branch_id` omitted; caller-supplied `branch_id` validated
  - `GET /api/v1/schedules/{id}`: branch authorization checked against stored branch
  - `PATCH /api/v1/schedules/{id}`: branch authorization checked against stored branch
  - `GET /api/v1/schedules/{id}/available-slots`: branch authorization checked against stored branch
- **Tests:** `TestScheduleRBACR2` — 8 tests (all passing)

### RBAC-R3 — Doctor ownership and assistant assignment
- **File:** `backend/common/auth.py`, `backend/queuing/main.py`
- **Fix:** 
  - `AuthContext` now carries `doctor_id` from `StaffUser.doctor_id`
  - `GET /api/v1/queue` and `GET /api/v1/queue/history`: doctors/assistants restricted to their assigned doctor's queue
  - `PATCH /api/v1/queue/{id}`: consultation actions restricted to doctor's own entries
  - Backward compatible: when `auth.doctor_id` is unset, checks are skipped
- **Tests:** `TestQueueDoctorAssistantOwnership` — 8 tests (all passing)

### Not implemented (out of scope)
SaaS Platform RBAC, `super_admin` migration, last-admin/self-escalation protection, patient update permission mismatch (R-13 — needs product decision).

### Test results (all suites)
| Suite | Result |
|---|---|
| `queuing/tests/test_queue.py` | 41 passed |
| `scheduling/tests/test_scheduling.py` | 36 passed |
| `tests/test_security.py`, `patient/tests/`, `identity/tests/` | 59 passed |
| `appointment/tests/` | 108 passed |
| **Total** | **244 passed, 0 failed** |

### Disposition
**IMPLEMENTED AND TESTED — READY FOR INDEPENDENT REVIEW** (not Product Owner accepted).

---

## Phase 1C — Operational RBAC Authorization Closure (Recorded 2026-11-17)

### Scope
Three remaining authorization areas (C1, C2, C3) plus one architecture limitation (C4) identified during independent review of commit `d7a1c90`. All corrections are server-side, preserve existing roles and permission matrix, and introduce no SaaS Platform RBAC.

### C1 — Queue history branch authorization (VERIFIED DEFECT — FIXED)
- **File:** `backend/queuing/main.py`
- **Fix:** `GET /api/v1/queue/history` now validates caller-supplied `branch_id` via `branch_accessible()`. When `branch_id` omitted, branch-scoped users are restricted to their token branch via `auth.branch_id`. `org_admin` retains organization-wide access.
- **Tests:** `TestQueueHistoryBranchAuth` — 5 tests (all passing)

### C2 — Doctor and assistant ownership across all queue actions (VERIFIED DEFECT — FIXED)
- **Files:** `backend/common/auth.py`, `backend/queuing/main.py`, `backend/queuing/recovery.py`
- **Fix:** 
  - `AuthContext.can_access_doctor(doctor_id)` added — returns `False` for doctor/assistant roles when `auth.doctor_id` is unset (fail closed); returns `True` for all other roles
  - `get_queue`, `queue_history`, `check_in_appointment`, `enqueue_patient`, `reorder_queue`, `queue_action` all check `can_access_doctor()`
  - `recovery.py` `_scoped_entry()` checks `can_access_doctor()` for recover/reposition actions
- **Tests:** `TestQueueRecoveryDoctorAuth` — 1 test (doctor cannot recover another doctor's entry). Combined with existing `TestQueueDoctorAssistantOwnership` — 8 tests (all passing)

### C3 — Missing or invalid doctor assignment fails closed (VERIFIED DEFECT — FIXED)
- **File:** `backend/common/auth.py`
- **Fix:** `can_access_doctor()` returns `False` when `auth.doctor_id` is unset for doctor/assistant roles. All callers now fail closed.
- **Tests:** `TestQueueMissingDoctorAssignment` — 3 tests (doctor no assignment denied, assistant no assignment denied, valid assignment allowed)

### C4 — Assistant assignment architecture limitation (BLOCKED — PRODUCT DECISION REQUIRED)
- **Finding:** `StaffUser.doctor_id` is a single nullable foreign key. BR §7.5 states assistants may support "assigned doctor(s)" and "Platform policy may allow one or multiple doctors per assistant."
- **Disposition:** Multi-doctor assistant assignment is UNSUPPORTED in the current data model. Single-doctor assignment via `StaffUser.doctor_id` is enforced. No new assignment model or migration created. Multi-doctor support requires explicit Product Owner/architecture decision.
- **Status:** BLOCKED — pending explicit Product Owner decision on multi-doctor assistant assignment policy.

### Test results (all suites)
| Suite | Result |
|---|---|
| `queuing/tests/test_queue.py` | 50 passed |
| `scheduling/tests/test_scheduling.py` | 36 passed |
| `tests/test_security.py`, `patient/tests/`, `identity/tests/` | 59 passed |
| `appointment/tests/` | 108 passed |
| **Total** | **253 passed, 0 failed** |

### Disposition
**IMPLEMENTED AND TESTED — READY FOR INDEPENDENT REVIEW** (not Product Owner accepted).

## Phase 1C Follow-up — Queue History Branch Ownership Authorization Closure (Recorded 2026-11-17)

### Finding — Queue history caller-supplied `branch_id` lacks organization ownership validation (VERIFIED DEFECT — FIXED)
- **Root cause:** `GET /api/v1/queue/history` (`backend/queuing/main.py`) used `branch_accessible(auth, branch_id)` to validate caller-supplied `branch_id`. While `branch_accessible()` enforces role-based branch reachability, it intentionally permits `org_admin` to access any branch ID without verifying that the branch belongs to `auth.organization_id`. An `org_admin` could submit a foreign or nonexistent branch ID and receive an empty successful response instead of a non-disclosing `404`.
- **Fix:** `backend/queuing/main.py` — When `branch_id` is supplied to `GET /api/v1/queue/history`, the endpoint now:
  1. Validates the branch exists (`Branch.id == branch_id`).
  2. Validates the branch belongs to the caller's organization (`Branch.organization_id == auth.organization_id`).
  3. Validates caller authorization via `branch_accessible(auth, branch_id)`.
  4. Returns non-disclosing `404` if any check fails, before applying the branch filter to the query.
  - Organization ownership check applies to **all roles**, including `org_admin`.
- **Tests:** `TestQueueHistoryBranchAuth` — added 2 new tests:
  - `test_c1_org_admin_other_org_branch_denied` — org admin requesting another org's branch history → 404.
  - `test_c1_org_admin_nonexistent_branch_denied` — org admin requesting nonexistent branch → 404.
- **Verification:** All 52 queue tests pass. Cross-tenant organization data is never returned for unauthorized branch IDs.

### Not implemented (out of scope): Same as Phase 1C — multi-doctor assistant assignment remains BLOCKED pending Product Owner decision.

---

## Phase 1D — Operational RBAC Completion and Platform Identity Separation (Recorded 2026-11-18)

### Baseline and commit
| Item | Value |
|---|---|
| Branch | `hackathon-mvp` |
| Starting HEAD | `6d71156c0c320aefbb3e9983ab5069f529aec3a9` |
| Final commit | Not yet committed (pending owner review) |
| Phase 1D commits on branch | `dee9499`, `c6a9d30`, `6d3acdf` (sequential; each verified below) |
| Working-tree changes | 12 modified files, 2 new migration files, 1 preserved untracked file |

### Workstream A — Multiple Doctor Assignments (PO-RBAC-01) — IMPLEMENTED · TESTED

**Requirement:** An assistant may be assigned to multiple doctors within the same organization. Doctor access must be based on explicit assignment, not organization membership alone.

**Changes:**
- `backend/common/models.py` — Added `StaffDoctorAssignment` model (explicit staff→doctor assignment table with `UNIQUE(staff_user_id, doctor_id)` constraint, FKs to `staff_users`, `doctors`, `organizations`, plus indexes). Legacy `StaffUser.doctor_id` column preserved as compatibility field.
- `backend/common/auth.py` — Extended `AuthContext` with `assigned_doctor_ids: list[str]`; `can_access_doctor()` checks membership in `assigned_doctor_ids` for doctor/assistant roles; `get_current_user()`/`get_optional_user()` load assignments from `staff_doctor_assignments`. `_load_assigned_doctor_ids()` returns `None` **only** when the table is absent (pre-migration); that is the sole case in which the legacy `StaffUser.doctor_id` column is used as a fallback. An existing table with no active rows returns `[]` and the legacy column is ignored, so a revoked assignment cannot restore access; query failures propagate (fail closed).
- `backend/identity/main.py` — `create_staff_user()` accepts `doctor_ids` list, validates each doctor exists/active/same-org, creates assignment rows; `_user_to_response()` returns `doctor_ids`.
- `backend/identity/models.py` — Added `doctor_ids: Optional[list[str]]` to `StaffUserCreate`, `StaffUserUpdate`, `StaffUserResponse`.
- `backend/identity/routes.py` — `update_staff_user()` replaces assignment set when `doctor_ids` provided; validates each doctor; legacy `doctor_id` fallback preserved.
- `backend/alembic/versions/f8a1b2c3d4e5_add_staff_doctor_assignments.py` — Migration creating `staff_doctor_assignments` table with backfill of legacy `doctor_id` values; idempotent re-runs.

**Tests added** (`backend/queuing/tests/test_queue.py` — `TestQueueMultiDoctorAssignments`):
- Assistant assigned to multiple doctors can access each assigned doctor's queue
- Assistant cannot access unassigned doctor's queue (404)
- Assignment revocation immediately denies access (while other assignments remain)
- Missing/empty assignment fails closed (404)
- Legacy single `doctor_id` assignment still works

**Tests added** (`backend/identity/tests/test_identity.py` — `TestMultiDoctorValidation`):
- Cross-organization doctor assignment rejected (422)
- Nonexistent doctor ID rejected (422)
- Inactive doctor rejected (422)
- Update cannot introduce invalid doctor (422)
- Legacy `doctor_id` still readable in response

**Verification at first implementation:** All 57 queue tests pass (52 baseline + 5 new). All identity multi-doctor validation tests pass. (After the correction recorded below the queue module runs 58 tests.)

**Correction record (2026-11-18) — a revoked assignment must not be restored by the legacy column**

The first implementation collapsed two different loader outcomes into an empty list, so the caller fell back to the legacy `StaffUser.doctor_id` column even when the assignment table existed with no active rows. An explicitly revoked assistant could therefore regain doctor access (PO-RBAC-01 privilege restoration).

- `backend/common/auth.py` — `_load_assigned_doctor_ids()` returns `None` for "table absent" and `[]` for "table exists, no active rows". `get_current_user()`/`get_optional_user()` fall back to the legacy column only on `None`, and `AuthContext.assigned_doctor_ids` is always a list (`None` normalised to `[]`).
- `backend/identity/main.py`, `backend/identity/routes.py` — `_user_to_response()`/`_user_to_dict()` apply the same contract and always answer with a list.
- Test fixtures in `backend/queuing/tests/test_queue.py`, `backend/identity/tests/test_identity.py` and `backend/tests/test_sequence3.py` now create the assignment row that the `f8a1b2c3d4e5` migration backfills, so a fixture user carrying a legacy `doctor_id` represents a migrated account instead of an unassigned one.
- Regression tests: `test_get_current_user_ignores_legacy_doctor_id_after_revocation` (identity) asserts `assigned_doctor_ids == []` and `can_access_doctor() is False` once the assignment row is deleted while `doctor_id` survives; `test_revoked_legacy_doctor_id_does_not_restore_access` (queuing) asserts `GET /api/v1/queue` answers 404 in the same state.

| Suite | Command | Result |
|---|---|---|
| Identity | `python3 -m pytest identity/tests/test_identity.py -q` | **44 passed** |
| Queuing | `python3 -m pytest queuing/tests/test_queue.py -q` | **58 passed** |
| Sequence 3 + audit + patient | `python3 -m pytest tests/test_sequence3.py audit/tests/ patient/tests/ -q` | **62 passed** |
| Full backend suite | `python3 -m pytest . -q --ignore=tests/test_e2e.py` | **507 passed, 10 failed** — all ten failures are in `doctor/tests/test_doctor.py` (`409 a doctor with this mobile number already exists`), the pre-existing test-isolation defect recorded as **O-2** in `docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` §10.3; the module is unmodified and creates no doctor assignments, so this change cannot cause it |

The suites above read the DSN from the environment; the local run needed `POSTGRES_PASSWORD` sourced from the gitignored `.env` (no credential is recorded here).

### Workstream B — Separate Patient Permissions (PO-RBAC-02) — IMPLEMENTED · TESTED

**Requirement:** Patient creation requires `patient.create`; patient modification requires `patient.update`. Correct the PATCH patient endpoint permission mismatch.

**Changes:**
- `backend/common/permissions.py` — Replaced `patient.*` wildcard with explicit `patient.read`, `patient.search`, `patient.create`, `patient.update` for `org_admin` and `branch_admin`. `patient.update` NOT granted to `receptionist`, `doctor`, `assistant`.
- `backend/patient/main.py` — Fixed PATCH endpoint: `require_permission("patient.create")` → `require_permission("patient.update")`.

**Tests added** (`backend/patient/tests/test_patient.py` — `TestPatientReadUpdate`):
- `test_update_patient` — org_admin can update (200)
- `test_branch_admin_can_update_patient` — branch_admin can update (200)
- `test_receptionist_cannot_update_patient_403` — receptionist denied (403), data unchanged
- `test_doctor_cannot_update_patient_403` — doctor denied (403)
- `test_assistant_cannot_update_patient_403` — assistant denied (403)
- `test_foreign_tenant_patient_cannot_be_updated` — cross-org update → 404

**Verification:** All 20 patient tests pass (13 baseline + 7 new).

### Workstream C — Prevent Privilege Self-Escalation (PO-RBAC-03) — IMPLEMENTED · TESTED

**Requirement:** A user must not grant themselves a higher role or additional permissions. Enforced server-side.

**Changes:**
- `backend/common/permissions.py` — Added `ROLE_HIERARCHY` (assistant=1 → super_admin=6), `role_level()`, `can_grant_role()` (super_admin exempt for granting to others **only**).
- `backend/identity/main.py` — `create_staff_user()` rejects role ≥ caller's level (403).
- `backend/identity/routes.py` — `update_staff_user()`: (1) blocks self-escalation regardless of role **including super_admin**; (2) blocks granting role ≥ caller's level to others unless super_admin.

**Tests added** (`backend/identity/tests/test_identity.py` — `TestSelfEscalation`):
- Receptionist cannot create org_admin (403)
- Receptionist cannot create super_admin (403)
- Branch admin cannot create org_admin (403)
- Org admin can create branch_admin (201)
- Super admin can create any role (201)
- User cannot update own role to higher (403)
- User cannot update own role to super_admin (403)
- Org admin cannot update own role to super_admin (403)
- Unit tests for `can_grant_role()` and `role_level()`

**Verification:** All 43 identity tests pass (38 baseline + 5 new doctor-assignment-loading + 1 concurrent last-admin).

### Workstream D — Protect Last Active Organization Admin (PO-RBAC-04) — IMPLEMENTED · TESTED

**Requirement:** Every active organization must retain at least one active `org_admin`. Prevent removal, deactivation, or role downgrade of the last active Organization Admin. Enforced transactionally with concurrency safety.

**Changes:**
- `backend/common/auth.py` — Added `count_active_org_admins(session, organization_id, exclude_user_id)` helper.
- `backend/identity/routes.py` — `update_staff_user()`: locks both the user row AND the organization row (`with_for_update()`) before modifying role/status. This serializes concurrent admin-affecting changes within one organization, preventing the race where two concurrent requests each deactivate a different org_admin and both pass the count check. Checks after lock: if role changes away from org_admin or status changes away from active for an org_admin, verify at least one other active org_admin remains (403 otherwise).

**Tests added** (`backend/identity/tests/test_identity.py` — `TestLastOrgAdmin`, `TestLastOrgAdminConcurrency`):
- Cannot remove only active org_admin (role change → 403)
- Cannot deactivate only active org_admin (status → 403)
- Can remove one org_admin when another remains (200, verified count=1)
- Can deactivate one org_admin when another remains (200, verified count=1)
- Organization isolation — foreign tenant org_admin modification → 404
- Concurrent deactivation of two admins: exactly one succeeds (200), other denied (403), exactly one remains active **(genuine concurrent test using ThreadPoolExecutor)**

**Concurrency safety:** Organization-row locking serializes all org_admin-affecting changes within one organization. The concurrency test uses separate request execution contexts and independent database sessions, with a 10-second timeout, to prove at least one org_admin remains under concurrent deactivation attempts. Database engine: PostgreSQL (row-level locking supported).

**Verification:** All 38 identity tests pass.

### Workstream E — Separate Platform Identity and Platform RBAC (PO-RBAC-05) — PARTIAL (Groundwork Implemented)

**Requirement:** Separate platform identities and roles from tenant organization identities and roles immediately.

**Implemented (IMPLEMENTED · TESTED):**
- `backend/common/models.py` — Added `PlatformAuditEvent` model for `platform_audit_events` table (no `organization_id`, per O-SaaS-2). Actor identified by named platform operator identity plus platform role (O-SaaS-10).
- `backend/alembic/versions/f8a2b3c4d5e6_add_platform_audit_events.py` — Migration creating `platform_audit_events` table with indexes on `action` and `timestamp`.
- `backend/common/audit.py` — Added `record_platform_audit()` function writing to `platform_audit_events` (separate from tenant `audit_events`).
- `backend/common/permissions.py` — Added `PLATFORM_ROLES` dict: `platform_admin` (platform.admin, platform.cross_org, audit.read), `platform_ops` (platform.cross_org, audit.read), `platform_support` (platform.cross_org, audit.read). Platform roles hold only platform capabilities — no automatic tenant business-data access.

**Specified but NOT implemented (requires separate platform service/infrastructure):**
- Separate platform identity system (platform users table, platform JWT, platform endpoints)
- Platform endpoints for tenant provisioning, suspension, closure
- Legacy `super_admin` migration (role retained for backward compatibility; migration plan documented in IAM spec §7.2–7.4)
- MFA implementation (required before production per O-SaaS-15; hackathon exception is time-boxed and restricted)

**Verification:** All existing audit and identity tests continue to pass (115 total across queue, identity, patient suites).

### Test results (all suites)
| Suite | Result |
|---|---|
| `queuing/tests/test_queue.py` | 57 passed (52 baseline + 5 new multi-doctor) |
| `identity/tests/test_identity.py` | 43 passed (38 baseline + 5 new doctor-assignment-loading + 1 concurrent last-admin) |
| `patient/tests/test_patient.py` | 20 passed (13 baseline + 7 new) |
| `tests/test_patient_age.py` | 15 passed (was 13 + 2 fixed after permission change) |
| `tests/test_sequence3.py` | 27 passed (was failing, now fixed with doctor_id in seed) |
| `tests/test_security.py` + `tests/test_platform_admin.py` + `tests/test_denial_audit.py` | 53 passed |
| `appointment/tests/test_appointment.py` | 19 passed |
| `scheduling/tests/test_scheduling.py` | 36 passed |
| **Total confirmed** | **270 passed, 0 failed** |

**Re-verified after the PO-RBAC-01 correction (2026-11-18, same tree):**

| Command | Result |
|---|---|
| `python3 -m pytest identity/tests/test_identity.py -q` | **44 passed** (43 + 1 revocation regression test) |
| `python3 -m pytest queuing/tests/test_queue.py -q` | **58 passed** (57 + 1 revocation regression test) |
| `python3 -m pytest tests/test_sequence3.py audit/tests/ patient/tests/ -q` | **62 passed** |
| `python3 -m pytest . -q --ignore=tests/test_e2e.py` (full backend suite) | **507 passed, 10 failed** |

The ten failures are all in `doctor/tests/test_doctor.py` with `409 a doctor with this mobile number already exists` — the pre-existing test-isolation defect recorded as **O-2** in `docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` §10.3. That module is unmodified by this work, creates no doctor assignments, and the failure is produced by a leftover reference doctor row (`purge_org()` deliberately keeps doctors), so this change cannot cause it.

### Disposition
**IMPLEMENTED AND TESTED — READY FOR INDEPENDENT REVIEW** (not Product Owner accepted).

**Corrections applied in this checkpoint (fix(rbac)):**
1. **Doctor assignment loading fails closed** (`backend/common/auth.py`, `backend/identity/main.py`, `backend/identity/routes.py`): When `staff_doctor_assignments` table exists but the query fails, the exception now propagates instead of being silently caught and converted to a legacy `doctor_id` fallback. Table absence returns `None` (pre-migration compatibility — the only case in which the legacy `doctor_id` fallback may be used); an existing table with no active rows returns `[]` and the caller must not fall back, so an assignment revocation cannot be undone. (Corrected 2026-11-18 — see the correction record under Workstream A.)
2. **Genuine concurrency test for last-admin protection** (`backend/identity/tests/test_identity.py`): `test_concurrent_deactivation_one_remains` now uses `ThreadPoolExecutor` with separate request execution contexts and a 10-second timeout, proving the organization-row serialization mechanism works under concurrent deactivation attempts.

Workstream E groundwork implemented; full platform identity system remains SPECIFIED, NOT IMPLEMENTED.

### Governance and Skill Compliance (PO-RBAC-01 correction, recorded 2026-11-18)

Per `.clinerules` §6 and the Evidence Standard (§7).

| Item | Detail |
|---|---|
| Domains identified (§4 routing) | Authentication/RBAC/permissions · multi-tenant data (token-derived org/branch, unchanged) · backend API/service endpoints · audit and data integrity · documentation reading/writing |
| Governance documents applied | `docs/governance/AMSDP_Docs_Index_V1.0.md` (index, read first) · `docs/governance/AMSDP_Engineering_Governance_Assessment.md` (adapted `saas-auth-and-authorisation` / `saas-multitenant-data` rows) · `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` (R-12) · this report · `docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` §10.3 (pre-existing O-2 evidence) · Business Rules §7–§8 via the implementation code paths already cited above |
| Skills | **None installed** (Skills Registry: NONE). No skill was claimed or simulated; the governance documents above were applied directly. |
| Non-negotiables upheld | Authorisation stays server-side and token-derived — a legacy `doctor_id` claim cannot widen scope after revocation; cross-tenant/branch behaviour unchanged (non-disclosing 404); query failures fail closed rather than degrading to the legacy column; no secret, token or DSN is recorded here; no audit row was deleted or rewritten; **no schema change**, so no migration was required this round |
| Verification performed (real results) | identity **44 passed** · queuing **58 passed** · sequence 3 + audit + patient **62 passed** · full backend suite **507 passed, 10 failed** (all 10 pre-existing doctor-module isolation failures, O-2). These results were produced in this tree against the local PostgreSQL; the suite needs `POSTGRES_PASSWORD` from the gitignored `.env` |
| Evidence level | The two regression tests are **TESTED**; the behaviour is **IMPLEMENTED**; independent confirmation by a second artefact or Product Owner sign-off was not performed, so nothing here is **VERIFIED** or **ACCEPTED** |
| Deviations / open items | Test fixtures in three files were updated to create the assignment row the `f8a1b2c3d4e5` migration backfills (a migrated account carries both `doctor_id` and an assignment row); pre-existing **O-2** (`doctor/tests/test_doctor.py` isolation) remains open and unfixed; `_tools/write_identity_main.py` is a stale one-off generator that no longer matches `backend/identity/main.py` and was left untouched |
