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
