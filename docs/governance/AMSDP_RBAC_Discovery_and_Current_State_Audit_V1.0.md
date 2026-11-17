# AMSDP Operational RBAC and SaaS Platform RBAC — Current-State Discovery and Design Report

## 1. Document Metadata and Evidence Baseline

| Field | Value |
|---|---|
| Report title | AMSDP Operational RBAC and SaaS Platform RBAC — Current-State Discovery and Design Report |
| Report path | `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` |
| Version | V1.0 |
| Task type | Discovery and documentation only — READ-ONLY. No application code changes. |
| Repository | shomonrobie/amsdp |
| Target branch | `hackathon-mvp` |
| Starting commit | `7c039fa68835b84fa371cf8fa2c64e3658a5bf2a` |
| Starting commit message | `docs(saas): correct MFA launch requirement and reconciliation record` |
| Final commit | Same as starting commit (no commits made) |
| Final branch | `hackathon-mvp` (no branch switch) |
| Database inspected | No — live database not accessed. State derived from models, migrations, and source code. Live DB state marked UNKNOWN. |
| Git working tree | Inspected via `git status --short` and `git status -sb` — preserved, no modifications |
| Classification | Security-sensitive audit report |

### Evidence standard applied

Every important finding cites concrete repository evidence: file path, function/class/model/route, line numbers where practical, database table/column or migration, test file and test name where applicable.

Status labels used: OWNER-APPROVED, SPECIFIED, IMPLEMENTED, PARTIALLY IMPLEMENTED, TESTED, VERIFIED, ABSENT, UNKNOWN, OPEN, DEFERRED, FORBIDDEN, BLOCKED.

Never infer IMPLEMENTED from a specification. Never infer TESTED from the existence of a test. Never infer VERIFIED from a successful build or static inspection.

### Authoritative documents consulted

- `docs/product/AMSDP_Business_Rules_V1.0.md`
- `docs/AMSDP_Business_Rules_V1.1.md`
- `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
- `docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md`
- `docs/chatgpt/AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md`
- `docs/governance/AMSDP_Docs_Index_V1.0.md`
- `docs/governance/AMSDP_Engineering_Governance_Assessment.md`
- `docs/governance/AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md`
- `docs/architecture/saas/AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md`
- `docs/architecture/saas/AMSDP_Identity_and_Access_Management_Specification_V1.0.md`
- `docs/architecture/saas/AMSDP_Tenant_and_Organization_Management_Specification_V1.0.md`
- `docs/architecture/saas/AMSDP_Subscription_and_Entitlement_Management_Specification_V1.0.md`
- `docs/architecture/saas/AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md`
- `docs/architecture/saas/AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md`

### Files inspected (evidence base, partial)

- `backend/common/permissions.py` — PERMISSIONS matrix, PLATFORM_CAPABILITIES, `check()` function
- `backend/common/auth.py` — AuthContext, `decode_token`, `get_current_user`, `require_permission`, `require_org_access`, `require_branch_access`, `record_platform_access`
- `backend/common/models.py` — Organization, Branch, FacilityFloor, FacilityDepartment, FacilityRoom, Doctor, DoctorBranch, DoctorSpecialty, StaffUser, Patient, Appointment, QueueEntry, QueueSequence, AuditEvent, TrackingToken, Notification
- `backend/common/audit.py` — `record_audit`
- `backend/identity/main.py`, `backend/identity/routes.py`, `backend/identity/models.py`
- `backend/organization/main.py`, `backend/organization/facility.py`, `backend/organization/notification_config.py`
- `backend/patient/main.py`
- `backend/doctor/main.py`, `backend/doctor/profile.py`
- `backend/scheduling/main.py`
- `backend/appointment/main.py`, `backend/appointment/dashboard.py`, `backend/appointment/tracking.py`
- `backend/queuing/main.py`, `backend/queuing/display.py`, `backend/queuing/recovery.py`
- `backend/audit/main.py`
- `frontend/lib/auth.js`
- `backend/tests/test_security.py`
- `docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md` — H1 P0 branch-authorization findings

### Task boundaries observed

This task is READ-ONLY application discovery plus creation of ONE Markdown report. No application code was modified, no database/schema/migration/Docker/dependency/test/fixture changes were made, no commits or pushes occurred. The working tree was preserved exactly as found.

---

## 2. Executive Summary

### Two authorization domains

AMSDP operates two distinct authorization domains that must remain strictly separated:

| Domain | Scope | Governing identities | Status |
|---|---|---|---|
| **A. Operational RBAC — tenant plane** | Healthcare organization staff operating appointments and queues | StaffUser (role: org_admin, branch_admin, receptionist, doctor, assistant, super_admin) | IMPLEMENTED — with material P0 defects |
| **B. SaaS Platform RBAC — platform plane** | AMSDP platform operators administering tenants, subscriptions, lifecycle | Not implemented as separate platform identity | ABSENT in code — specified only in docs |

### Operational RBAC (tenant plane) — current state

**What is implemented:** A role-based permission matrix (`PERMISSIONS` in `backend/common/permissions.py`) maps six roles to permission keys. JWT tokens carry `sub`, `org`, `branch`, `role`. Every service enforces `require_permission` on mutating endpoints. Audit events are written to `audit_events` table. Cross-tenant access returns non-disclosing 404. DQDS is public and token-only; PQT is private and account-free.

**Most serious security gaps (operational):**

1. **`_scoped_entry_or_404()` missing branch scope** (`backend/queuing/main.py:98-105`): Checks organization ownership but NOT branch ownership. Queue call/cancel/recovery/reposition/reorder paths using this helper can read/modify another branch's queue entries within the same org.

2. **`GET /api/v1/queue` caller-supplied `branch_id`** (`backend/queuing/main.py:108-136`): Accepts `branch_id` as a query parameter and filters by it without first enforcing the caller's branch authorization. A branch administrator can change `branch_id` to read another branch's queue.

3. **Check-in/enqueue trust caller-supplied `branch_id`** (`backend/queuing/main.py:146-215`): `CheckInRequest.branch_id` and `QueueEnqueueRequest.branch_id` are accepted from the request body and used directly (`entry.branch_id = data.branch_id or appt.branch_id`) without validating the caller is authorized for that branch.

4. **Schedule creation lacks branch/doctor ownership validation** (`backend/scheduling/main.py:68-88`): `ScheduleCreate` accepts `organization_id` and `branch_id` from the body. `organization_id` is overwritten from the auth token, but `branch_id` is taken from the body without `require_branch_access` validation.

5. **`queue_action()` uses `_scoped_entry_or_404()` without branch check** (`backend/queuing/main.py:294-348`): Call/cancel/mark_no_show/reinsert are authorized by `queue.manage` permission but the entry scope check lacks branch ownership.

6. **Frontend `can()` grants `super_admin` bypass** (`frontend/lib/auth.js:17-45`): `role === 'super_admin'` returns `true` for every permission — a hard-coded wildcard bypass in the UI layer (presentation only, not authorization, but inconsistent with backend Q-1 fix).

7. **`queue.recover` / `queue.reposition` are present for doctors** (`permissions.py:99`) — the recovery module (`recovery.py`) requires `queue.recover`, and the doctor role holds this permission. No permission gap exists for doctors on recovery/reposition. (The SEQ_03 assessment note about a missing permission was incorrect; the matrix and module are consistent.)

### SaaS Platform RBAC (platform plane) — current state

**No separate platform identity exists in code.** The following are ABSENT:

- `platform_users` table/model — ABSENT
- Platform authentication endpoint — ABSENT
- Platform token scope — ABSENT
- Separate platform signing secret — ABSENT
- Platform principal resolver — ABSENT
- Platform permission catalogue — ABSENT as enforced code (only `PLATFORM_CAPABILITIES` tuple exists in `permissions.py`)
- Platform-only audit trail — ABSENT (audit_events is tenant-scoped)
- Platform operator provisioning and deactivation — ABSENT

The IAM specification (`docs/architecture/saas/AMSDP_Identity_and_Access_Management_Specification_V1.0.md`) specifies platform roles (`platform_admin`, `platform_ops`, `platform_support`) and capabilities (`platform.tenant.read`, `platform.tenant.manage`, etc.), but these are **SPECIFIED, not IMPLEMENTED**.

The legacy `super_admin` role conflates tenant and platform authority. It holds `platform.admin` and `platform.cross_org` capabilities plus all clinic namespaces. The staged migration (R-1 introduce `org_super_admin`, R-2 migrate users with alias, R-3 remove alias after testing) is NOT implemented — `super_admin` remains an active role with wildcard-like behavior in the frontend and enumerated capabilities in the backend matrix.

### Overall verdict

The operational RBAC has a functional role-permission matrix and server-side enforcement on most mutating endpoints, but P0 branch-authorization defects remain unfixed in current code. The SaaS Platform RBAC does not exist as implemented code — it exists only in specification. The two domains are not cleanly separated: `super_admin` bridges tenant and platform authority.

---

## 3. Current Security Ecosystem — Two Authorization Domains

### Domain A: Operational RBAC (tenant plane)

Governed by `backend/common/permissions.py` (`PERMISSIONS` dict) and `backend/common/auth.py` (`AuthContext`, `require_permission`, `require_org_access`, `require_branch_access`). Identities are `StaffUser` rows keyed by `organization_id` (the sole tenant key — no second tenant column exists). Roles: `super_admin`, `org_admin`, `branch_admin`, `receptionist`, `doctor`, `assistant`.

### Domain B: SaaS Platform RBAC (platform plane)

Specified in the IAM document but not implemented as separate code. Platform capabilities exist only as the `PLATFORM_CAPABILITIES` tuple (`platform.admin`, `platform.cross_org`) in `permissions.py`, and `AuthContext.is_super_admin` derives from that matrix instead of a role-string comparison. There is no `platform_users` table, no platform auth endpoint, no separate platform JWT scope, no separate platform signing secret.

### Separation invariant — current status

| Invariant | Current status | Evidence |
|---|---|---|
| Tenant role must not silently become platform role | PARTIALLY ENFORCED | `super_admin` holds both tenant and platform capabilities (`permissions.py:38-52`) |

---

## 4. Operational RBAC Current State

### 4.1 Identity and role sources

| Item | File/table/model | Current behavior | Authority | Consumers | Risks | Status |
|---|---|---|---|---|---|---|
| Identity table | `backend/common/models.py` `StaffUser` (`staff_users`) | Columns: id, organization_id, branch_id, doctor_id, username, password_hash, display_name, role, status, locale, created_at | Authoritative for operational staff | All services via `get_current_user` | None known | IMPLEMENTED |
| Role field | `StaffUser.role` (String) | Accepts any string; matrix keys: super_admin, org_admin, branch_admin, receptionist, doctor, assistant | Authoritative | `permissions.check()`, `auth.is_super_admin`, `auth.is_org_admin` | No DB constraint on accepted role values; legacy aliases possible | IMPLEMENTED |
| Permission matrix | `backend/common/permissions.py` `PERMISSIONS` dict | Maps 6 roles to permission key lists; namespaced wildcards (`patient.*`, `doctor.*`, etc.) | Authoritative | `permissions.check()` | `super_admin` holds platform capabilities mixed with tenant capabilities | IMPLEMENTED |
| Platform capabilities | `backend/common/permissions.py` `PLATFORM_CAPABILITIES` | `platform.admin`, `platform.cross_org` | Specified + partially enforced | `auth.is_super_admin`, `require_org_access`, `require_branch_access`, `record_platform_access` | No separate platform identity table | PARTIALLY IMPLEMENTED |
| Branch assignment | `StaffUser.branch_id` FK to `branches.id` | Nullable; branch-scoped users (receptionist, branch_admin, assistant, doctor) carry one branch | Authoritative | `require_branch_access`, `_scoped_entry_or_404` | No validation that branch belongs to user's org at token issue time | IMPLEMENTED |
| Doctor assignment | `StaffUser.doctor_id` FK to `doctors.id` | Nullable; links staff to a doctor record | Authoritative | `doctor/main.py` update path validates `doctor_id` same org | Not used for scope enforcement on queue/appointment reads | IMPLEMENTED |
| Organization scope | `StaffUser.organization_id` FK to `organizations.id` | Derived from JWT `org` claim at login; never from request body | Authoritative | All scoped queries (`Appointment.organization_id == auth.organization_id` etc.) | None known | IMPLEMENTED |
| User-specific permission overrides | None | No per-user override mechanism exists | ABSENT | N/A | N/A | ABSENT |
| Hard-coded role checks | `frontend/lib/auth.js:20` `role === 'super_admin'` returns true for all | Frontend presentation bypass | Presentation only | Frontend `can()` calls | Inconsistent with backend Q-1 (no bare `*` honored) | IMPLEMENTED (frontend) |
| Legacy role aliases | `super_admin` | Functions as both tenant org-super-admin and platform admin | Transitional/conflated | `auth.is_super_admin`, `identity/routes.py` | Conflates two domains; no staged migration (R-1/R-2/R-3) implemented | IMPLEMENTED |

### 4.2 Permission catalogue (extracted from code)

All permission keys actually present in `backend/common/permissions.py` `PERMISSIONS` dict:

**Organization administration**
- `org.create` — super_admin, org_admin
- `org.read` — super_admin, org_admin
- `org.manage` — super_admin, org_admin

**Branch administration**
- `branch.read` — super_admin, branch_admin
- `branch.manage` — super_admin, org_admin, branch_admin

**Facility (floor/department/room)**
- `facility.read` — super_admin, org_admin, branch_admin, receptionist, doctor, assistant
- `facility.manage` — super_admin, org_admin, branch_admin

**Symptom catalogue**
- `symptom.read` — super_admin, org_admin, branch_admin, receptionist, doctor, assistant
- `symptom.manage` — super_admin, org_admin, branch_admin

**Staff management**
- `staff.read` — super_admin, org_admin, branch_admin
- `staff.manage` — super_admin, org_admin

**Patient registration and lookup**
- `patient.create` — super_admin, org_admin, branch_admin, receptionist
- `patient.read` — all roles
- `patient.search` — all roles
- `patient.*` (namespace wildcard) — super_admin, org_admin, branch_admin, receptionist

**Doctor management**
- `doctor.*` (namespace wildcard) — super_admin, org_admin, branch_admin
- Individual keys not separately listed (covered by `doctor.*`)

**Schedule management**
- `schedule.*` (namespace wildcard) — super_admin, org_admin, branch_admin
- Individual keys not separately listed

**Appointment operations**
- `appointment.*` (namespace wildcard) — super_admin, org_admin, branch_admin, receptionist
- `appointment.create` — receptionist (and wildcard holders)
- `appointment.read` — all roles
- `appointment.modify` — receptionist (and wildcard holders)

**Walk-in operations**
- `queue.checkin` — receptionist (and wildcard holders) — used for both check-in and enqueue

**Check-in and attendance**
- `queue.checkin` — receptionist (and wildcard holders)

**Queue operations**
- `queue.view` — receptionist, doctor, assistant
- `queue.manage` — super_admin, org_admin, branch_admin, receptionist
- `queue.reorder` — receptionist (and wildcard holders) — covered by `queue.*` wildcard for super_admin/org_admin/branch_admin
- `queue.recover` — receptionist, doctor — Sequence 3 / BR §27A
- `queue.reposition` — receptionist, doctor — Sequence 3 / BR §27A
- `queue.consult` — doctor — start/complete consultation

**Token operations**
- No separate token permission keys; `queue.checkin` governs check-in which creates queue entries with tokens

**DQDS configuration**
- No separate DQDS permission; DQDS is public (no auth)

### 4.3 Operational role matrix — current state

| Resource | Action | super_admin | org_admin | branch_admin | receptionist | doctor | assistant |
|---|---|---|---|---|---|---|---|
| Organization | create | CREATE | CREATE | — | — | — | — |
| Organization | read | VIEW | VIEW | — | — | — | — |
| Organization | manage | MANAGE | MANAGE | — | — | — | — |
| Branch | read | VIEW | — | VIEW | — | — | — |
| Branch | manage | MANAGE | MANAGE | MANAGE | — | — | — |
| Facility | read | VIEW | VIEW | VIEW | VIEW | VIEW | VIEW |
| Facility | manage | MANAGE | MANAGE | MANAGE | — | — | — |
| Symptom | read | VIEW | VIEW | VIEW | VIEW | VIEW | VIEW |
| Symptom | manage | MANAGE | MANAGE | MANAGE | — | — | — |
| Staff | read | VIEW | VIEW | VIEW | — | — | — |
| Staff | manage | MANAGE | MANAGE | — | — | — | — |
| Patient | create | CREATE | CREATE | CREATE | CREATE | — | — |
| Patient | read | VIEW | VIEW | VIEW | VIEW | VIEW | VIEW |
| Patient | search | VIEW | VIEW | VIEW | VIEW | VIEW | VIEW |
| Doctor | all | MANAGE | MANAGE | MANAGE | — | — | — |
| Schedule | all | MANAGE | MANAGE | MANAGE | — | — | — |
| Appointment | create | CREATE | CREATE | CREATE | CREATE | — | — |
| Appointment | read | VIEW | VIEW | VIEW | VIEW | VIEW | VIEW |
| Appointment | modify | MANAGE | MANAGE | MANAGE | MANAGE | — | — |
| Queue | view | VIEW | VIEW | VIEW | VIEW | VIEW | VIEW |
| Queue | manage | MANAGE | MANAGE | MANAGE | MANAGE | — | — |
| Queue | reorder | MANAGE | MANAGE | MANAGE | MANAGE | — | — |
| Queue | recover | MANAGE | MANAGE | MANAGE | MANAGE | MANAGE | — |
| Queue | reposition | MANAGE | MANAGE | MANAGE | MANAGE | MANAGE | — |
| Queue | consult | MANAGE | MANAGE | MANAGE | — | MANAGE | — |
| Audit | read | VIEW | VIEW | VIEW | VIEW | — | — |
| Platform | admin | MANAGE | — | — | — | — | — |
| Platform | cross_org | MANAGE | — | — | — | — | — |

Legend: VIEW = read, CREATE = create, UPDATE/MANAGE = write, DELETE/CANCEL = cancel, ASSIGNED-ONLY = own branch/doctor only, DENIED = not granted, CONDITIONAL = depends on scope, UNKNOWN = cannot determine from code.

Notes:
- `queue.reorder` is NOT explicitly in the matrix; covered by `queue.*` wildcard for super_admin/org_admin/branch_admin, and receptionist holds `queue.view`, `queue.reorder`, `queue.checkin`, `queue.manage` explicitly (`permissions.py:86`).
- Doctor has `queue.recover` and `queue.reposition` (`permissions.py:99`) but NOT `queue.manage` or `queue.reorder` — consistent with BR §27A.3. The recovery module (`recovery.py:78-89`) requires `queue.recover`, which doctors hold; recovery is correctly scoped by branch (`recovery.py:86-88`).
- No DELETE permission exists anywhere; cancellations are status transitions (CANCELLED/NO_SHOW).

### 4.4 Scope enforcement

| Scope type | Enforcement mechanism | Gaps |
|---|---|---|
| Tenant/organization | JWT `org` claim → `auth.organization_id`; all queries filter `organization_id == auth.organization_id` | None known at code level; `super_admin` bypasses via `is_super_admin` |
| Branch | `auth.branch_id` from JWT; `require_branch_access(target_branch_id)` | `_scoped_entry_or_404()` does NOT check branch (queuing/main.py:98-105); `GET /queue` caller-supplied `branch_id` not validated (queuing/main.py:119-120); check-in/enqueue accept `branch_id` from body (queuing/main.py:170, 223) |
| Doctor assignment | `StaffUser.doctor_id`; `scoped_doctor()` in doctor/profile.py checks org | Not enforced on queue/appointment reads by doctor_id |
| Appointment | `_scoped_appointment()` filters by organization_id only (appointment/main.py:249-265) | No branch scope on appointment lookup |
| Queue | `QueueEntry.organization_id == auth.organization_id` in recovery.py scope; main.py `_scoped_entry_or_404` lacks branch | Cross-branch within same org possible |

### 4.5 Endpoint inventory — operational services

| Service | Method + path | Action/resource | Authentication | Permission check | Tenant scope | Branch/doctor scope | Finding |
|---|---|---|---|---|---|---|---|
| Identity | POST /api/v1/staff/register | staff.create | JWT (require_permission staff.manage) | staff.manage | org from token | branch from body, no branch check | Org override rejected (422) if body org != token org |
| Identity | POST /api/v1/staff/login | auth | None (public) | None | N/A | N/A | Throttled per (IP, username) |
| Identity | GET /api/v1/staff/validate | auth | Bearer token | None | N/A | N/A | Returns 401/403 for invalid/inactive |
| Identity | GET /api/v1/staff/users | staff.read | require_permission(staff.read) | staff.read | org from token (super_admin sees all) | None | super_admin cross-org allowed |
| Identity | GET /api/v1/staff/users/{id} | staff.read | get_current_user | None | org match or super_admin | branch match for non-admin | Non-disclosing 404 for cross-org |
| Identity | PATCH /api/v1/staff/users/{id} | staff.manage | require_permission(staff.manage) | staff.manage | org match or super_admin | branch match for non-admin | Role/status changes audited |
| Identity | POST /api/v1/staff/check-permission | permission.check | get_current_user | None | org match | None | Checks perm_check(target.role, resource) |
| Organization | POST /api/v1/orgs | org.create | require_permission(org.create) | org.create | org from token | N/A | |
| Organization | GET /api/v1/orgs | org.read | get_current_user | None | None listed | None | |
| Organization | GET /api/v1/orgs/{id} | org.read | get_current_user | None | require_org_access | None | Non-disclosing 404 for foreign org |
| Organization | PATCH /api/v1/orgs/{id} | org.manage | require_permission(org.manage) | org.manage | require_org_access | None | |
| Organization | POST /api/v1/branches | branch.create | require_permission(branch.manage) | branch.manage | `require_org_access(data.organization_id)(auth)` at line 196 | body branch_id, no branch check | **ADEQUATELY ENFORCED** — `require_org_access` verifies caller's org; `branch.manage` permission required |
| Organization | GET /api/v1/orgs/{org_id}/branches | branch.read | get_current_user + require_org_access(org_id) | None | require_org_access | None | Non-disclosing 404 |
| Organization | GET /api/v1/branches/{id} | branch.read | get_current_user | None | require_org_access(branch.org_id) | None | Non-disclosing 404 |
| Organization | PATCH /api/v1/branches/{id} | branch.manage | require_permission(branch.manage) | branch.manage | require_org_access | None | |
| Organization | GET /api/v1/me/branches | branch.list | get_current_user | None | org from token | own branch for non-admin | |
| Patient | POST /api/v1/patients | patient.create | require_permission(patient.create) | patient.create | org from token | None | |
| Patient | GET /api/v1/patients | patient.read/search | get_current_user | None | org from token | None | |
| Patient | GET /api/v1/patients/{id} | patient.read | get_current_user | None | org from token | None | |
| Patient | PATCH /api/v1/patients/{id} | patient.update | require_permission(patient.create) | patient.create (mismatch) | org from token | None | **GAP: uses patient.create not patient.* or patient.update** |
| Patient-record | `Patient.organization_id == auth.organization_id` (patient/main.py:160-161, 182-183) | None known |
| Public endpoint | DQDS: no auth, org+branch path scope, 404 for unknown/inactive | Rate limit is in-process only (not durable across workers) |
| Public endpoint | PQT: token-gated, no auth, no-store headers | Rate limit is in-process only |

Where a permission is present but resource scope is missing:
- `queue.manage` on `queue_action()` — entry scoped by org only via `_scoped_entry_or_404()` (no branch check)
- `queue.recover`/`queue.reposition` — recovery.py `_scoped_entry` does check branch (lines 86-88), so this one is OK
- `schedule.*` on `create_schedule()` — `branch_id` from body, no `require_branch_access` (scheduling/main.py:80)

**PQT management**
| Doctor | POST /api/v1/doctors | doctor.create | require_permission(doctor.*) | doctor.* | org from token | branch_ids from body, validated same org | |
| Doctor | GET /api/v1/doctors | doctor.read | require_permission(doctor.*) | doctor.* | org from token | None | |
| Doctor | GET /api/v1/doctors/{id} | doctor.read | require_permission(doctor.*) | doctor.* | scoped_doctor (org) | None | Non-disclosing 404 |
| Doctor | PATCH /api/v1/doctors/{id} | doctor.update | require_permission(doctor.*) | doctor.* | scoped_doctor (org) | branch_ids validated same org | |
| Scheduling | POST /api/v1/schedules | schedule.create | require_permission(schedule.*) | schedule.* | org from token (overrides body) | **GAP: branch_id from body, no require_branch_access** | Doctor ownership not validated |
| Scheduling | GET /api/v1/schedules | schedule.read | get_current_user | None | org from token | branch_id query, no scope check | **GAP: no branch/doctor scope validation** |
| Scheduling | PATCH /api/v1/schedules/{id} | schedule.update | require_permission(schedule.*) | schedule.* | org match (404) | None | |
| Scheduling | GET /api/v1/schedules/{id}/available-slots | schedule.read | get_current_user | None | org match (404) | None | |
| Appointment | POST /api/v1/appointments | appointment.create | require_permission(appointment.*) | appointment.* | org from token | doctor/branch from body, resolved via _resolve_location | |
| Appointment | GET /api/v1/appointments | appointment.read | get_current_user | None | org from token | branch_id query, applied via apply_branch_scope | Calendar filter fixed (F-3/F-4 resolved) |
| Appointment | PATCH /api/v1/appointments/{id} | appointment.modify | require_permission(appointment.*) | appointment.* | _scoped_appointment (org only) | No branch scope | **GAP: no branch scope on appointment lookup** |
| Appointment | POST /api/v1/appointments/{id}/reschedule | appointment.modify | require_permission(appointment.*) | appointment.* | org from token | New branch from resolved schedule | |
| Appointment | POST /api/v1/appointments/{id}/tracking-token | pqt.issue | require_permission(appointment.modify) | appointment.modify | org from token | None | |
| Appointment | GET /api/v1/track/{token} | pqt.view | None (token-gated) | None | Via appointment org | None | Public, account-free |
| Appointment | GET /api/v1/track/{token}/qr | pqt.qr | None (token-gated) | None | Via appointment org | None | Public, token-gated |
| Queuing | GET /api/v1/queue | queue.read | get_current_user | None | org from token | **GAP: caller-supplied branch_id unvalidated** | Cross-branch read possible |
| Queuing | POST /api/v1/queue/check-in | queue.checkin | require_permission(queue.checkin) | queue.checkin | org from token | **GAP: body branch_id unvalidated** | entry.branch_id = body or appt.branch_id |
| Queuing | POST /api/v1/queue/enqueue | queue.checkin | require_permission(queue.checkin) | queue.checkin | org from token | **GAP: body branch_id unvalidated** | entry.branch_id = body value |
| Queuing | PATCH /api/v1/queue/{entry_id} | queue.manage/cancel | get_current_user + inline require_permission | queue.manage/queue.consult | _scoped_entry_or_404 (org only) | **GAP: no branch check** | Cross-branch mutate possible |
| Queuing | POST /api/v1/queue/reorder | queue.reorder | require_permission(queue.reorder) | queue.reorder | org from token | **GAP: no branch/queue homogeneity check** | Can mix unrelated queues |
| Queuing | POST /api/v1/queue/recover | queue.recover | require_permission(queue.recover) | queue.recover | _scoped_entry (org+branch) | Branch checked | Correctly scoped |
| Queuing | GET /api/v1/queue/history | queue.read | get_current_user | None | org from token | branch_id query, filtered | |
| Queuing | GET /api/v1/queue/display/{org_code}/{branch_code} | dqds.read | None (public) | None | Path-scoped org+branch | Branch from path | Public, zero PII, rate-limited |
| Audit | GET /api/v1/audit/organization/{org_id} | audit.read | require_permission(audit.read) | audit.read | _scoped_org (404 for foreign) | _apply_branch_scope | Non-disclosing 404 |
| Audit | GET /api/v1/audit/{target_id} | audit.read | require_permission(audit.read) | audit.read | org from token | _apply_branch_scope | Empty list for foreign target |
| Dashboard | GET /api/v1/dashboard/today | dashboard.read | get_current_user | None | org from token | require_branch_access if branch_id | Branch scope enforced when provided |
| Dashboard | GET /api/v1/dashboard/period | dashboard.read | get_current_user | None | org from token | `require_branch_access(branch_id)(auth)` at line 81 when branch_id provided | **ADEQUATELY ENFORCED** — branch access checked when branch filter provided |
| Dashboard | GET /api/v1/dashboard/audit | audit.read | get_current_user | None | org from token | require_branch_access if branch_id | |
- `appointment.modify` — required to issue tracking token (`tracking.py:63`)

**Reports**
- `audit.read` — super_admin, org_admin, branch_admin, receptionist

**Audit access**
- `audit.read` — as above
Key findings from endpoint inventory:
- Most mutating endpoints have `require_permission` — GOOD
- Most reads use `get_current_user` only, with org-level scoping via query filters — PARTIAL
- Branch scope missing on: `GET /api/v1/queue` (caller-supplied `branch_id`), `PATCH /api/v1/queue/{entry_id}` (via `_scoped_entry_or_404()`), `POST /api/v1/queue/check-in` (body `branch_id`), `POST /api/v1/queue/enqueue` (body `branch_id`), `POST /api/v1/queue/reorder` (no queue homogeneity), `POST /api/v1/schedules` (body `branch_id`, no `require_branch_access`) — CRITICAL GAPS
- `_scoped_entry_or_404()` lacks branch check — ROOT CAUSE for `queue_action()` cross-branch mutation
- `queue/recover` endpoint correctly scoped by branch (`recovery.py:78-89`) — ADEQUATELY ENFORCED
- `POST /api/v1/branches` calls `require_org_access` (`organization/main.py:196`) — ADEQUATELY ENFORCED
- `GET /api/v1/dashboard/*` calls `require_branch_access` when branch_id provided — ADEQUATELY ENFORCED
- Cross-tenant consistently returns non-disclosing 404 — GOOD

### 4.5a Endpoint scope classification summary

| Endpoint | Classification | Basis |
|---|---|---|
| `GET /api/v1/queue` | CONFIRMED DEFECT | Caller-supplied `branch_id` used without branch authorization (`queuing/main.py:119-120`) |
| `POST /api/v1/queue/check-in` | CONFIRMED DEFECT | Body `branch_id` used without caller branch authorization (`queuing/main.py:170`) |
| `POST /api/v1/queue/enqueue` | CONFIRMED DEFECT | Body `branch_id` used without caller branch authorization (`queuing/main.py:241`) |
| `PATCH /api/v1/queue/{entry_id}` (`queue_action`) | CONFIRMED DEFECT | Uses `_scoped_entry_or_404()` which lacks branch check (`queuing/main.py:307`) |
| `POST /api/v1/queue/reorder` | CONFIRMED DEFECT | Org-only filter, no queue homogeneity check (`queuing/main.py:373-376`) |
| `POST /api/v1/schedules` | CONFIRMED DEFECT | Body `branch_id` used without `require_branch_access` (`scheduling/main.py:80`) |
| `POST /api/v1/branches` | ADEQUATELY ENFORCED | Calls `require_org_access(data.organization_id)(auth)` (`organization/main.py:196`) |
| `GET /api/v1/dashboard/today` | ADEQUATELY ENFORCED | Calls `require_branch_access(branch_id)(auth)` when branch_id provided (`dashboard.py:24`) |
| `GET /api/v1/dashboard/period` | ADEQUATELY ENFORCED | Calls `require_branch_access(branch_id)(auth)` when branch_id provided (`dashboard.py:81`) |
| `GET /api/v1/dashboard/audit` | ADEQUATELY ENFORCED | Calls `require_branch_access(branch_id)(auth)` when branch_id provided (`dashboard.py:147`) |
| `GET /api/v1/queue/recover` | ADEQUATELY ENFORCED | `_scoped_entry` checks branch (`recovery.py:86-88`) |
| `GET /api/v1/queue/display/{org_code}/{branch_code}` | ADEQUATELY ENFORCED | Public, path-scoped org+branch, 404 for unknown/inactive (`display.py:127-137`) |
| Cross-tenant access (all services) | ADEQUATELY ENFORCED | Non-disclosing 404 via `require_org_access` and `_scoped_org` |

### 4.6 Existing operational authorization defects — P0 branch-authorization findings revisited

The Hackathon Implementation Backlog H1 (P0, security blocker) identified these findings. Current-code status:

| Backlog finding | Location | Current status | Evidence |
|---|---|---|---|

**Root-cause defects** (authorization helpers missing scope checks):

| Root cause | Location | Defect | Affected endpoints |
|---|---|---|---|
| `_scoped_entry_or_404()` missing branch check | `queuing/main.py:98-105` | Filters by `organization_id` only; no `branch_id` comparison for non-admin/non-org-admin callers | `PATCH /api/v1/queue/{entry_id}` (`queue_action`) — call, cancel, mark_no_show, reinsert |
| `GET /api/v1/queue` caller-supplied `branch_id` unvalidated | `queuing/main.py:119-120` | `branch_id` query param used to filter without first enforcing caller's branch authorization | `GET /api/v1/queue` |
| Check-in body `branch_id` unvalidated | `queuing/main.py:170` | `entry.branch_id = data.branch_id or appt.branch_id` — body value used without caller branch authorization | `POST /api/v1/queue/check-in` |
| Enqueue body `branch_id` unvalidated | `queuing/main.py:241` | `branch_id=data.branch_id or auth.branch_id or ""` — body value used without caller branch authorization | `POST /api/v1/queue/enqueue` |
| Queue reorder no queue-homogeneity check | `queuing/main.py:373-376` | Filters by `organization_id` only; no check that all entries share the same doctor/date/branch | `POST /api/v1/queue/reorder` |
| Schedule creation body `branch_id` unvalidated | `scheduling/main.py:80` | `branch_id=data.branch_id` from body; no `require_branch_access` call | `POST /api/v1/schedules` |

**Correctly scoped (not a defect):**
- `POST /api/v1/queue/recover` — uses `_scoped_entry()` in `recovery.py:78-89` which checks branch (`recovery.py:86-88`)

**Not part of H1 but identified during this audit:**
- `PATCH /api/v1/patients/{id}` uses `require_permission("patient.create")` instead of a distinct `patient.update` key (`patient/main.py:195`) — permission-key mismatch, low severity

All six H1 P0 root-cause defects remain present in current code. None have been remediated.

## 5. SaaS Platform RBAC Current State

### 5.1 Platform identity — implementation status

| Component | Specified in IAM doc | Implemented in code | Evidence | Status |
|---|---|---|---|---|
| `platform_users` table/model | Yes | No | No `platform_users` in `backend/common/models.py`; 22 tables declared, none platform identity | ABSENT |
| Platform authentication endpoint | Yes | No | No platform login route in any service; only `/api/v1/staff/login` in identity service | ABSENT |
| Platform token scope | Yes | No | JWT carries `sub`, `org`, `branch`, `role` only; no platform scope claim | ABSENT |
| Separate platform signing secret | Yes | No | Single `AMSDP_JWT_SECRET` / `_SECRET` used for all tokens (`auth.py:43-51`, `identity/models.py:15-23`) | ABSENT |
| Platform principal resolver | Yes | No | `AuthContext` derived from staff JWT; no platform principal type | ABSENT |
| Platform role definitions | `platform_admin`, `platform_ops`, `platform_support` | No | Only `super_admin` in `PERMISSIONS` dict; holds `platform.admin` + `platform.cross_org` | ABSENT |
| Platform permission catalogue | `platform.tenant.read`, etc. | Partial | `PLATFORM_CAPABILITIES = ("platform.admin", "platform.cross_org")` only; no `platform.tenant.*`, `platform.plan.*`, etc. | PARTIALLY IMPLEMENTED |
| Platform-only audit trail | Yes | No | `audit_events` table is tenant-scoped (`organization_id` column); no separate platform audit table | ABSENT |
| Platform operator provisioning/deactivation | Yes | No | No platform operator CRUD routes; staff CRUD is tenant-scoped | ABSENT |

### 5.2 Platform capabilities — specified vs implemented

| Capability | Specified | Implemented | Evidence | Status |
|---|---|---|---|---|
| `platform.tenant.read` | Yes | No | No route or permission key | ABSENT |
| `platform.tenant.manage` | Yes | No | No route or permission key | ABSENT |

---

## 6. Legacy `super_admin` Migration Status

### 6.1 Existing role definition

- Defined in `backend/common/permissions.py:38-52` as a role key in `PERMISSIONS` dict
- Holds `PLATFORM_CAPABILITIES` (`platform.admin`, `platform.cross_org`) plus all org capabilities and all clinic namespace wildcards
- Frontend `frontend/lib/auth.js:20-22` grants `super_admin` a bare `['*']` wildcard — every permission returns true

### 6.2 Existing permission grants

| Capability | Granted to super_admin | Source |
|---|---|---|
| platform.admin | YES | `permissions.py:40` |
| platform.cross_org | YES | `permissions.py:40` |
| org.create/read/manage | YES | `permissions.py:42` |
| branch.read/manage | YES | `permissions.py:43-44` |
| facility.read/manage | YES | `permissions.py:44` |
| symptom.read/manage | YES | `permissions.py:48-49` |
| staff.read/manage | YES | `permissions.py:49` |
| audit.read | YES | `permissions.py:49` |
| patient/doctor/schedule/appointment/queue.* | YES | `permissions.py:51` |

### 6.3 Actual cross-tenant capabilities


---

## 7. Tenant Lifecycle and Entitlement Enforcement

### 7.1 `lifecycle_state` vs legacy `organizations.status`

The `Organization` model (`backend/common/models.py:31-45`) has a `status` column (String(20), default="active") but NO `lifecycle_state` column. There is no separate lifecycle state machine in code.

### 7.2 Platform-owned lifecycle decisions

No platform-owned lifecycle decisions exist in code. No platform routes for tenant suspension, activation, or closure.

### 7.3 Tenant-local enforcement

Organization status is stored but not consistently checked by endpoints:
- `organization/main.py`: `OrgUpdate` allows `status` field but no endpoint enforces that a `suspended` org's users cannot access
- `identity/main.py:207-208`: login checks `user.status != "active"` but not organization status

---

## 8. MFA and Support-Grant Implementation Status

### 8.1 MFA — approved requirement

| Context | Requirement | Source |
|---|---|---|
| Hackathon MVP | Temporary, documented exception may exist for a restricted, named operator group | IAM spec / roadmap |
| Production launch | Operator MFA mandatory before production platform access | IAM spec / roadmap |
| Post-launch | MFA must already be implemented; not a deferred enhancement | IAM spec / roadmap |

### 8.2 Actual MFA implementation

| Component | Status | Evidence |
|---|---|---|
| MFA enrollment endpoint | ABSENT | No MFA routes in any service |
| MFA verification endpoint | ABSENT | No MFA verification routes |
| TOTP/SMS MFA challenge in login flow | ABSENT | `staff_login` (`identity/main.py:184-219`) checks password only, no MFA |
| MFA enforcement on platform routes | ABSENT | No platform routes exist |
| MFA on `super_admin` | ABSENT | `super_admin` authenticates with password only |
| MFA for support operators | ABSENT | No support operator identity exists |

MFA is NOT IMPLEMENTED, NOT TESTED, NOT VERIFIED.

### 8.3 Support access — approved model vs implementation

---

## 9. Authorization Test Coverage and Security Gaps

### 9.1 Existing tests

`backend/tests/test_security.py` — M2 Security Tests. Test classes and coverage:

| Test class | Test names | Coverage | Status |
|---|---|---|---|
| TestCrossOrgIs404 | test_cross_get, test_cross_update, test_unknown_id_is_indistinguishable | Cross-tenant staff access returns 404 | TESTED (in suite) |
| TestBranchAdminCrossDenied | test_branch_admin_cross_denied | Cross-branch staff user access | TESTED (in suite) |
| TestLoginThrottle | test_repeated_failures_get_429, test_limit_is_per_username, test_success_clears_the_bucket | Login throttling per (IP, username) | TESTED (in suite) |
| TestOrgOverride | test_cannot_force_other_org | Organization ID override in registration body | TESTED (in suite) |
| TestSuperBoundaries | test_super_cross_org_read, test_super_cross_org_create | Super admin cross-org read/create | TESTED (in suite) |
| TestValidate | test_valid, test_no_token | Token validation | TESTED (in suite) |

### 9.2 Test coverage gaps

| Coverage area | Tests exist? | Tests run in this task? | Status |
|---|---|---|---|
| Unauthenticated requests | PARTIAL (test_no_token only) | No | MISSING for most endpoints |
| Wrong-role requests | PARTIAL | No | MISSING for most role combinations |
| Missing permission | PARTIAL | No | MISSING |
| Cross-tenant access | YES (test_security.py) | No | EXISTS but not run in this task |
| Cross-branch access | YES (test_branch_admin_cross_denied) | No | EXISTS but limited to staff users |
| Wrong-doctor assignment | No | No | MISSING |
| Resource ID substitution | PARTIAL | No | PARTIAL |
| Queue mutation authorization | No | No | MISSING — no tests for queue call/cancel/recover authorization |

---

## 10. Current-to-Target Mapping

| Area | Current state | Target state (approved) | Gap |
|---|---|---|---|
| Identity model | `StaffUser` with `organization_id`, `branch_id`, `role` | Separate `platform_users` + tenant `StaffUser` | Platform identity table ABSENT |
| Authentication | JWT staff login, single secret | Separate platform JWT scope/signing secret | ABSENT |
| Role matrix | 6 operational roles + `super_admin` conflated | `platform_admin`/`platform_ops`/`platform_support` separate from tenant roles | `super_admin` not migrated |

---

## 11. Consolidated Risk Register

| ID | Risk | Severity | Current evidence | Status |
|---|---|---|---|---|
| R-01 | Cross-branch queue read via `GET /api/v1/queue?branch_id=` | P0 / Critical | `queuing/main.py:119-120` — caller-supplied `branch_id` unvalidated | DEFECT PRESENT |
| R-02 | Cross-branch queue mutation via `queue_action()` | P0 / Critical | `queuing/main.py:294-348` — `_scoped_entry_or_404()` no branch check | DEFECT PRESENT |
| R-03 | Cross-branch check-in/enqueue via caller-supplied `branch_id` | P0 / Critical | `queuing/main.py:146-215` — body `branch_id` used directly | DEFECT PRESENT |
| R-04 | Cross-branch queue reorder mixing unrelated queues | P0 / High | `queuing/main.py:367-409` — org-only filter, no queue homogeneity | DEFECT PRESENT |
| R-05 | Schedule creation for unauthorized branch | P0 / High | `scheduling/main.py:68-88` — `branch_id` from body, no branch check | DEFECT PRESENT |
| R-06 | `super_admin` conflates platform + tenant authority | P0 / High | `permissions.py:38-52` — single role holds both domains | NOT MITIGATED |
| R-07 | Frontend `super_admin` wildcard bypass | Medium | `frontend/lib/auth.js:20-22` — `role === 'super_admin'` returns true for all | PRESENT (presentation only) |
| R-08 | No platform identity, authentication, or authorization | P0 / Critical | No `platform_users`, no platform routes, no platform JWT scope | ABSENT |
| R-09 | No MFA for platform operators | P0 / High | No MFA endpoints or enforcement | ABSENT |
| R-10 | No support-grant mechanism | P0 / High | No support-grant routes, consent recording, or time-limited grants | ABSENT |
| R-11 | No tenant suspension/access revocation enforcement | Medium | `Organization.status` column exists but not checked by endpoints | NOT ENFORCED |
| R-12 | `queue.recover`/`queue.reposition` permission gap for doctors | RESOLVED — NOT A GAP | Doctors hold `queue.recover` + `queue.reposition` (`permissions.py:99`); recovery module correctly scoped by branch (`recovery.py:86-88`) | RESOLVED |
| R-13 | Patient update uses `patient.create` permission (not `patient.update`) | Low | `patient/main.py:195` — `require_permission("patient.create")` on PATCH | PERMISSION MISMATCH |
| R-14 | Branch create scope validation | RESOLVED — ADEQUATELY ENFORCED | `create_branch` calls `require_org_access(data.organization_id)(auth)` (`organization/main.py:196`) | RESOLVED |
| R-15 | No self-escalation protection on staff role assignment | Medium | `PATCH /api/v1/staff/users/{id}` allows role change with `staff.manage` | NOT PROTECTED |
| R-16 | No last-active-org-admin protection | Medium | No endpoint prevents deactivating the last org_admin | NOT PROTECTED |
| Permission matrix | `PERMISSIONS` dict with namespace wildcards | Platform capability enumeration + operational permissions | Platform capabilities only as `PLATFORM_CAPABILITIES` tuple |
| Branch scope | Missing on queue/call/cancel/check-in/enqueue/reorder/schedule | Consistent `require_branch_access` on all scoped endpoints | 6 P0 defects present |
| Cross-tenant | Non-disclosing 404 | Non-disclosing 404 + platform `cross_org` audit | Partially implemented (audit exists, no platform identity) |
| super_admin | Active role with platform + tenant capabilities | Migrated to `org_super_admin` + separate platform admin | R-1/R-2/R-3 NOT implemented |
| MFA | Not implemented | Mandatory before production launch | ABSENT |

---

## 12. Owner Decisions and Engineering Questions

### 12.1 Owner decisions (require Product Owner approval)

| ID | Question | Status | Why it matters | Security/product impact | Current evidence | Recommended resolution | Blocks implementation |
|---|---|---|---|---|---|---|---|
| OD-1 | Staged `super_admin` migration: R-1 introduce `org_super_admin` (tenant role, no platform capabilities), R-2 migrate users with alias, R-3 remove alias after testing | OWNER-APPROVED (migration plan R-1/R-2/R-3 approved; timing OPEN) | `super_admin` conflates platform + tenant authority, violating the separation invariant | Uncontrolled cross-tenant + platform access via a single role | `super_admin` active with `platform.admin` + `platform.cross_org` + all clinic namespaces (`permissions.py:38-52`) | Implement R-1/R-2/R-3 per approved staged migration | Yes — platform RBAC cannot be cleanly separated until `super_admin` is split |
| OD-2 | Operational permission catalogue as authoritative baseline | OWNER-APPROVED (BR §8 FINALIZED per `permissions.py` header) | The `PERMISSIONS` dict is the single source of truth for operational RBAC | Inconsistent permissions across frontend/backend cause enforcement gaps | `permissions.py` vs `frontend/lib/auth.js` diverge (`super_admin` `['*']` in frontend only) | Align frontend `can()` to match backend matrix | No |
| OD-3 | Approve `patient.update` as a distinct permission (currently uses `patient.create` on PATCH) | OPEN | Permission-action mismatch weakens authorization clarity | Update authorized under create permission — semantically incorrect | `patient/main.py:195` `require_permission("patient.create")` on PATCH | Add `patient.update` to matrix; assign to appropriate roles | No |
| OD-4 | Approve whether organization status (suspended) should block endpoint access | OPEN | Suspended tenants can still operate through staff tokens | No revocation path for suspended organizations | `Organization.status` column exists but not checked by any endpoint | Decide whether to enforce status checks globally or per-endpoint | Yes — affects tenant lifecycle enforcement |
| OD-5 | `org_admin` multi-branch scope (vs own-branch-only) | OWNER-APPROVED (business rules specify org_admin multi-branch access) | Determines `org_admin` authority across branches | Over-broad org_admin could bypass branch isolation | `permissions.py` gives `org_admin` `branch.manage` + all clinic namespaces; `auth.is_org_admin` bypasses `require_branch_access` | Confirm `org_admin` multi-branch scope is intended (already reflected in matrix) | No |

### 12.2 Engineering questions (technical design, preserve approved decisions)

| ID | Question | Why it matters | Security/product impact | Current evidence | Recommended resolution | Blocks implementation |
|---|---|---|---|---|---|---|
| EQ-1 | Should `require_branch_access` be applied automatically to all scoped endpoints, or per-endpoint? | Consistency of branch enforcement | Missed endpoints create cross-branch access holes | `require_branch_access` used on dashboard/today, dashboard/period, dashboard/audit when branch_id provided; NOT used on queue endpoints or schedule creation | Centralize branch scope in a dependency or decorator applied to all resource-scoped routes | No |
| EQ-2 | Should `_scoped_entry_or_404()` be fixed to include branch check, or replaced with per-action scope helpers? | Queue actions are the highest-risk P0 area | Cross-branch queue mutation exposes patient queue data | `queuing/main.py:98-105` `_scoped_entry_or_404()` lacks branch; `recovery.py:78-89` has correct branch check | Fix `_scoped_entry_or_404()` to include branch scope for non-org-admin/non-super_admin callers | Yes — blocks P0 remediation |
| EQ-3 | Should `queue.recover`/`queue.reposition` be added to doctor's permissions, or should doctors use a different path? | RESOLVED — NOT NEEDED | Doctors already hold `queue.recover` + `queue.reposition` (`permissions.py:99`); recovery module correctly scoped by branch (`recovery.py:86-88`). No permission change required. | No |
| EQ-4 | [RESERVED — DO NOT RESOLVE] | | | | | |
| EQ-5 | [RESERVED — DO NOT RESOLVE] | | | | | |
| EQ-6 | Should platform JWT use a separate signing secret from staff JWT? | Platform identity separation | Shared secret compromises both domains if one is breached | Single `_SECRET` used everywhere (`auth.py:43-51`, `identity/models.py:15-23`) | Use separate `AMSDP_PLATFORM_JWT_SECRET` for platform tokens | Yes — required for platform identity separation |
| EQ-7 | [RESERVED — DO NOT RESOLVE] | | | | | |
| EQ-8 | Should denial audit record the requesting principal's branch for cross-branch denials? | Audit completeness for security investigations | Denials without branch context reduce forensic value | `denial_audit.py` records 403/404/422; branch context from token available | Include `branch_id` from `AuthContext` in denial audit records | No |
| EQ-9 | Should rate limiting for DQDS/PQT be durable (PostgreSQL-backed) instead of in-process? | Rate limit bypass via multiple workers | Attacker can exceed limits by hitting different replicas | `_DQDS_RATE` and `_RATE` are in-process dicts (`queuing/display.py:30`, `tracking.py:22`) | Migrate to database-backed sliding window (deferred to M9-F per DQDS doc) | No |
| Support grant | Not implemented | Consent-based, time-limited, audited | ABSENT |
| Platform audit | Tenant-scoped `audit_events` only | Separate platform audit trail | ABSENT |
| Lifecycle/entitlement | `status` column, not enforced | Platform lifecycle decisions, entitlement checks | ABSENT |
| Schedule ownership | No | No | MISSING — no tests for schedule branch/doctor ownership |
| Staff role assignment | PARTIAL | No | PARTIAL |
| Self-escalation | No | No | MISSING — no test that a user cannot escalate their own role |
| Privilege escalation | No | No | MISSING |
| Last active organization administrator protection | No | No | MISSING |
| Tenant role attempting platform access | No | No | MISSING — no platform routes to test against |

---

## 13. Proposed Phased Implementation Roadmap

### Phase 1 — Operational RBAC P0 repairs (hackathon priority, DO NOT DEFER)

1. **Baseline and authorization helper audit** — Document all authorization helpers, identify every endpoint lacking branch scope
2. **P0 tenant/branch/doctor/resource authorization repairs** — Fix all six H1 defects:
   - Fix `_scoped_entry_or_404()` to include branch check (`queuing/main.py:98-105`)
   - Validate caller branch authorization on `GET /api/v1/queue` `branch_id` param (`queuing/main.py:108-136`)
   - Validate caller branch authorization on check-in/enqueue `branch_id` body fields (`queuing/main.py:146-215`)
   - Add `require_branch_access` to schedule creation (`scheduling/main.py:68-88`)
   - Add branch check to `queue_action()` entry scope (`queuing/main.py:294-348`)
   - Add queue homogeneity check to reorder (`queuing/main.py:367-409`)
3. **Complete role-permission enforcement** — Add `patient.update` permission (OD-3); verify doctor `queue.recover`/`queue.reposition` already present (`permissions.py:99`) — no change needed
4. **Staff role assignment and privilege-escalation protection** — Self-escalation protection, last-active-org-admin protection

### Phase 2 — Operational RBAC hardening (post-hackathon)

5. **Frontend permission-aware experience** — Align `frontend/lib/auth.js` with backend matrix; remove `super_admin` `['*']` wildcard
6. **Audit coverage and negative authorization tests** — Tests for cross-branch, wrong-role, missing-permission, self-escalation
7. **Full role-based browser verification** — End-to-end verification of each role's permitted/denied actions

### Phase 3 — SaaS Platform RBAC foundation (post-hackathon, depends on Phase 1)

1. **Platform identity and tenant/platform boundary** — `platform_users` table, platform auth endpoint, separate platform JWT scope
2. **Safe legacy `super_admin` transition** — R-1: `org_super_admin` tenant role; R-2: migrate users with alias; R-3: remove alias after testing
3. **Platform permission enforcement** — `platform.tenant.read/manage`, `platform.plan.manage`, `platform.subscription.manage`, `platform.usage.read`, `platform.audit.read`, `platform.operator.manage`, `platform.support.grant`
4. **Platform audit separation** — Separate platform audit trail
5. **Tenant lifecycle and entitlement enforcement integration** — Organization status checks, subscription entitlement gating
6. **Support-grant controls** — Consent-based, time-limited, audited support access
7. **MFA before production launch** — Operator MFA mandatory
8. **Operator governance, suspension and closure controls** — Platform operator lifecycle management


---

## 14. Explicit Non-Goals and Exclusions

The following are explicitly OUT OF SCOPE for this discovery task and for AMSDP's current product:

- Clinical records, prescriptions, EMR/EHR
- Payment processing or financial transaction records
- Insurance, pharmacy, laboratory
- Patient accounts or patient self-service / self-booking
- Public doctor directory or public schedules
- Any implementation of RBAC, permissions, roles, or authorization code

---

## 15. Final Verdict and Owner-Review Checklist

### Overall verdict

**Operational RBAC** is IMPLEMENTED with a functional role-permission matrix and server-side enforcement on most mutating endpoints, but contains P0 branch-authorization defects that allow cross-branch reads and mutations. These defects are present in current code and must be remediated before the hackathon demonstration.

**SaaS Platform RBAC** is NOT IMPLEMENTED. It exists only in specification documents. There is no platform identity, no platform authentication, no platform authorization, no separate platform JWT scope, no platform audit trail, no MFA, and no support-grant mechanism. The legacy `super_admin` role conflates tenant and platform authority.

### Owner-review checklist

| Item | Status | Owner action required |
|---|---|---|
| P0 branch-authorization defects (R-01–R-05) confirmed present | CONFIRMED | Approve remediation plan |
| `super_admin` conflates platform + tenant (R-06) | CONFIRMED | Approve staged migration (OD-1) |
| Platform RBAC absent (R-08) | CONFIRMED | Approve platform identity build (Phase 3) |
| MFA absent (R-09) | CONFIRMED | Confirm MFA mandatory before production launch |
| Support-grant absent (R-10) | CONFIRMED | Approve support-grant design |

---

## 16. Evidence Appendix: Inspected Paths, Symbols, Models, Migrations, Routes and Tests

### Backend source files inspected

| File | Key symbols | Relevance |
|---|---|---|
| `backend/common/permissions.py` | `PERMISSIONS`, `PLATFORM_CAPABILITIES`, `check()` | Permission matrix |
| `backend/common/auth.py` | `AuthContext`, `is_super_admin`, `is_org_admin`, `can_cross_org`, `get_current_user`, `require_permission`, `require_org_access`, `require_branch_access`, `record_platform_access` | Auth dependencies |
| `backend/common/audit.py` | `record_audit` | Audit write path |
| `backend/common/models.py` | `Organization`, `Branch`, `StaffUser`, `Patient`, `Doctor`, `Appointment`, `QueueEntry`, `AuditEvent`, `TrackingToken`, `QueueSequence` | Data models |
| `backend/common/denial_audit.py` | `install_denial_audit` | Denial audit middleware |
| `backend/identity/main.py` | `staff_login`, `validate_token`, staff registration | Identity service |
| `backend/identity/routes.py` | `list_staff`, `get_staff_user`, `update_staff_user`, `check_permission` | Staff management routes |
| `backend/organization/main.py` | org/branch CRUD, `require_org_access` usage | Organization service |
| `backend/appointment/main.py` | `_scoped_appointment`, appointment CRUD | Appointment service |
| `backend/appointment/dashboard.py` | dashboard endpoints | Dashboard service |
| `backend/appointment/tracking.py` | PQT token issue/view | Tracking service |
| `backend/queuing/main.py` | `_scoped_entry_or_404`, `get_queue`, `check_in_appointment`, `enqueue_patient`, `queue_action`, `reorder_queue` | Queue service |
| `backend/queuing/display.py` | DQDS public endpoint | DQDS |
| `backend/queuing/recovery.py` | `_scoped_entry`, queue recovery | Recovery |
| `backend/audit/main.py` | audit read endpoints | Audit service |
| `frontend/lib/auth.js` | `can()`, `getUser()`, `getToken()` | Frontend auth |

### Database tables (from models, live DB not inspected)

| Table | Columns relevant to RBAC |
|---|---|
| `organizations` | id, code, status, config |
| `branches` | id, organization_id, code, status |
| `staff_users` | id, organization_id, branch_id, doctor_id, username, role, status |
| `doctors` | id, organization_id, status |
| `doctor_branch` | doctor_id, branch_id |
| `patients` | id, organization_id |
| `appointments` | id, organization_id, branch_id, doctor_id, patient_id, status |
| `queue_entries` | id, organization_id, branch_id, doctor_id, patient_id, appointment_id, status, position |
| `audit_events` | id, organization_id, branch_id, action, actor_id, actor_role, target_type, target_id |
| `tracking_tokens` | id, appointment_id, token_hash, status |

### Migrations (alembic chain, 9 revisions, one head)

Single linear chain: `5f3fce6757cf → ccf34da72c1b → c7d3601e2486 → 9d8a1f2b3c4d → 3c8e5d0a9b2f → a1f2b3c4d5e6 → b7c1e4d90a52 → d4b2c8e1f7a3 → e6c1a9b3d5f8` (head). No platform identity migrations exist.

### Test files inspected

| File | Coverage |
|---|---|
| `backend/tests/test_security.py` | Cross-tenant 404, cross-branch denial, login throttling, org override, super admin boundaries, token validation |

### Key line references

- `backend/common/permissions.py:38-52` — `super_admin` permissions including platform capabilities
- `backend/common/auth.py:88-94` — `is_super_admin` derives from `platform.admin`
- `backend/common/auth.py:263-284` — `require_org_access` with cross-org 404
- `backend/common/auth.py:287-313` — `require_branch_access` with cross-branch 404/403
- `backend/queuing/main.py:98-105` — `_scoped_entry_or_404()` missing branch check
- `backend/queuing/main.py:108-136` — `GET /queue` caller-supplied `branch_id`
- `backend/queuing/main.py:140,170` — Check-in `branch_id` from body
- `backend/queuing/main.py:206,223` — Enqueue `branch_id` from body
- `backend/queuing/main.py:294-348` — `queue_action()` using `_scoped_entry_or_404()`
- `backend/queuing/main.py:367-409` — Queue reorder org-only filter
- `backend/scheduling/main.py:68-88` — Schedule creation `branch_id` from body
- `backend/identity/routes.py:40-43,57-65,86-88` — `super_admin` bypasses org/branch checks
- `frontend/lib/auth.js:20-22` — Frontend `super_admin` `['*']` wildcard
- `backend/identity/main.py:207-208` — Login checks user status, not org status

---

**Report completion confirmation: No application code, schema, migration, test, deployment, or existing document was modified during this discovery task. The report file `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` is the only new artifact, created as an untracked file on branch `hackathon-mvp` at commit `7c039fa68835b84fa371cf8fa2c64e3658a5bf2a`.**

## 12. Phase 1 implementation outcome (dated)

**Recorded implementation date: 2026-11-17.** This section records the outcome of the Operational RBAC hardening work (AMSDP Phase 1) and must not be read as though it predates that work. The discovery report above (sections 1–11) remains the pre-implementation record; this section records what was changed and verified.

All six confirmed P0 authorization defects were fixed in application code and verified with automated tests:

| Risk | Defect | Fix | Status |
|---|---|---|---|
| R-01 | `GET /api/v1/queue?branch_id=` caller-supplied branch unvalidated | Validate caller branch via `branch_accessible()` before filtering; non-disclosing 404 for unauthorized selection | FIXED — TESTED |
| R-02 | `_scoped_entry_or_404()` missing branch check (queue call/cancel/recover/reposition) | Enforce the entry's stored branch against the authenticated actor's branch scope | FIXED — TESTED |
| R-03 | Check-in / enqueue trust caller-supplied `branch_id` | Check-in pins to the appointment's stored branch and rejects body tampering; enqueue validates caller-supplied branch against token scope | FIXED — TESTED |
| R-04 | Queue reorder mixes unrelated queues | Validate all entries share one branch/doctor/date and are branch-accessible; raise before any mutation (no partial apply) | FIXED — TESTED |
| R-05 | `create_schedule` branch_id from body, no branch check | Validate caller branch scope, doctor and branch membership in the caller's organization; `organization_id` from token only | FIXED — TESTED |
| R-06 | `super_admin` conflates platform + tenant | Preserved as legacy compatibility (not expanded, not removed) — out of scope for operational hardening | PRESERVED (compatibility) |

New shared helper: `common.auth.branch_accessible(auth, branch_id)` — `org_admin` and `platform.cross_org` callers may act on any branch; branch-scoped actors must match their token's branch; a `None` target imposes no constraint. Used by all six fixes.

Tests added:
- `backend/queuing/tests/test_queue.py` — `TestQueueBranchAuthorization`: 8 tests covering P0-1..P0-5 (authorized same-branch succeeds; unauthorized branch denied; cross-org denied; caller tampering denied; org-wide org-admin access preserved; mixed-branch reorder rejected with no partial mutation).
- `backend/scheduling/tests/test_scheduling.py` — `TestScheduleBranchAuthorization`: 6 tests covering P0-6 and finding 8.2 (foreign branch create/list denied; own branch succeeds; org-admin org-wide preserved; foreign doctor rejected).

Not implemented (out of scope, per finding 8.8): SaaS Platform RBAC (`platform_admin`, `platform_ops`, `platform_support`, platform identity, MFA, support grants, lifecycle enforcement), `super_admin` migration to `org_super_admin`, last-admin/self-escalation protection.

Additional findings classified:
- R-13 patient update `patient.create` vs `patient.update`: NOT A CODE CHANGE — the correct role policy is unclear; left blocked for product-owner decision.
- R-15 self-escalation / R-16 last-admin protection: NOT IMPLEMENTED — no existing approved rule; reported unresolved.
- R-07 frontend `super_admin` wildcard bypass: presentation only, not an authorization boundary; no code change.

Verification: `backend/queuing/tests/test_queue.py` 28 passed; `backend/scheduling/tests/test_scheduling.py` 28 passed; `tests/test_security.py`, `patient/tests/`, `identity/tests/` 59 passed; `appointment/tests/` 108 passed. No commit or push was made; the working tree was preserved.

## 13. Phase 1B Implementation Outcome (dated)

**Recorded implementation date: 2026-11-17.** This section records the outcome of the remaining Operational RBAC corrections (AMSDP Phase 1B).

### RBAC-R1 — Queue enqueue branch ownership (VERIFIED DEFECT — FIXED)
- **Finding:** `POST /api/v1/queue/enqueue` accepted caller-supplied `branch_id` without verifying the branch belongs to the caller's organization. An org_admin could enqueue into a branch in another org. Empty branch_id was allowed.
- **Fix:** `backend/queuing/main.py` — Resolve target branch from body or token branch. Require a valid, existing branch. Verify `Branch.id == target_branch AND Branch.organization_id == auth.organization_id`. Reject missing, invalid, nonexistent, or foreign-tenant branches with non-disclosing 404.
- **Tests:** `TestQueueEnqueueBranchOwnership` — 7 tests covering cross-org enqueue denial, same-org cross-branch enqueue for org_admin, own-branch enqueue for receptionist, foreign-branch denial, missing branch rejection, nonexistent branch rejection, and valid enqueue with DB row verification.

### RBAC-R2 — Complete schedule resource branch authorization (VERIFIED DEFECT — FIXED)
- **Finding:** Schedule endpoints did not consistently enforce branch scope:
  - `GET /api/v1/schedules`: branch-scoped users could see all branches when `branch_id` omitted
  - `GET /api/v1/schedules/{id}`: no branch authorization check
  - `PATCH /api/v1/schedules/{id}`: no branch authorization check
  - `GET /api/v1/schedules/{id}/available-slots`: no branch authorization check
- **Fix:** `backend/scheduling/main.py` — Added branch scope filter for listing when `branch_id` omitted; added `branch_accessible()` checks on get, update, and available-slots endpoints.
- **Tests:** `TestScheduleRBACR2` — 8 tests covering branch-scoped listing restrictions, foreign branch param rejection, org-admin org-wide access, foreign schedule read/update/slots denial, and cross-tenant non-disclosure.

### RBAC-R3 — Doctor ownership and assistant assignment (PARTIALLY RESOLVED)
- **Doctor ownership (VERIFIED DEFECT — FIXED):**
  - Added `doctor_id` to `AuthContext` (`backend/common/auth.py`), populated from `StaffUser.doctor_id` in `get_current_user`/`get_optional_user`
  - `GET /api/v1/queue`: doctors and assistants restricted to their assigned doctor's queue
  - `GET /api/v1/queue/history`: same restriction
  - `PATCH /api/v1/queue/{id}`: consultation actions restricted to the doctor's own entries
  - **Tests:** `TestQueueDoctorAssistantOwnership` — 8 tests covering doctor cross-queue denial, own queue access, cross-doctor consultation denial, own consultation, assistant unassigned denial, assistant assigned access, assistant consultation denial (403)
- **Assistant assignment:** Uses existing `StaffUser.doctor_id` FK (single assignment per assistant). No new assignment model created. Backward compatible: when `auth.doctor_id` is unset, checks are skipped.

### Not implemented (out of scope, per finding 8.8): SaaS Platform RBAC, `super_admin` migration, last-admin/self-escalation protection.

Additional findings classified:
- R-13 patient update `patient.create` vs `patient.update`: NOT A CODE CHANGE — correct role policy unclear; left blocked for product-owner decision.
- R-15 self-escalation / R-16 last-admin protection: NOT IMPLEMENTED — no existing approved rule; reported unresolved.
- R-07 frontend `super_admin` wildcard bypass: presentation only, not an authorization boundary; no code change.

Verification: `backend/queuing/tests/test_queue.py` 41 passed; `backend/scheduling/tests/test_scheduling.py` 36 passed; `tests/test_security.py`, `patient/tests/`, `identity/tests/` 59 passed; `appointment/tests/` 108 passed. Total: 244 passed, 0 failed.

## 13. Phase 1C Implementation Outcome (dated)

**Recorded implementation date: 2026-11-17.** This section records the outcome of the remaining Operational RBAC authorization closure work (AMSDP Phase 1C).

### C1 — Queue history branch authorization (VERIFIED DEFECT — FIXED)
- **Finding:** `GET /api/v1/queue/history` accepted caller-supplied `branch_id` without validating authorization via `branch_accessible()`. Branch-scoped users could request history for another branch in the same organization. When `branch_id` was omitted, branch-scoped users could see all branches.
- **Fix:** `backend/queuing/main.py` (`queue_history` endpoint): Validate caller-supplied `branch_id` via `branch_accessible()`. When `branch_id` omitted, restrict branch-scoped users to their token branch via `auth.branch_id`. `org_admin` retains organization-wide access.
- **Tests:** `TestQueueHistoryBranchAuth` — 5 tests covering own-branch history, foreign-branch denial, branch_id omission scoping, org-admin org-wide access, cross-tenant branch rejection.

### C2 — Doctor and assistant ownership across all queue actions (VERIFIED DEFECT — FIXED)
- **Finding:** Phase 1B only checked doctor ownership for `start_consultation`/`complete_consultation` in `queue_action()`. Other actions (`call`, `cancel`, `mark_no_show`, `reinsert`) and other endpoints (`check_in_appointment`, `enqueue_patient`, `reorder_queue`, `queue/recover`) did not enforce doctor ownership for doctor/assistant roles.
- **Fix:** 
  - `backend/common/auth.py`: Added `AuthContext.can_access_doctor(doctor_id)` method — returns `False` for doctor/assistant roles when `auth.doctor_id` is unset (fail closed); returns `True` for all other roles.
  - `backend/queuing/main.py`: Applied `can_access_doctor()` to `get_queue`, `queue_history`, `check_in_appointment`, `enqueue_patient`, `reorder_queue`, and `queue_action` (all actions, not just consult).
  - `backend/queuing/recovery.py`: Applied `can_access_doctor()` to `_scoped_entry()` for recover/reposition actions.
- **Tests:** `TestQueueRecoveryDoctorAuth` — 1 test covering doctor cannot recover another doctor's entry. Combined with existing `TestQueueDoctorAssistantOwnership` — 8 tests covering doctor cross-queue denial, own queue access, cross-doctor consultation denial, own consultation, assistant unassigned denial, assistant assigned access, assistant consultation denial (403).

### C3 — Missing or invalid doctor assignment fails closed (VERIFIED DEFECT — FIXED)
- **Finding:** Phase 1B skipped doctor/assistant ownership checks when `auth.doctor_id` was unset, potentially granting unrestricted access to doctor-specific resources for users with doctor/assistant roles but no assignment.
- **Fix:** `backend/common/auth.py` `can_access_doctor()` returns `False` when `auth.doctor_id` is unset for doctor/assistant roles. All callers in `queuing/main.py` and `recovery.py` now fail closed.
- **Tests:** `TestQueueMissingDoctorAssignment` — 3 tests covering doctor with no assignment denied, assistant with no assignment denied, valid assignment allowed.

### C4 — Assistant assignment architecture limitation (BLOCKED — PRODUCT DECISION REQUIRED)
- **Finding:** `StaffUser.doctor_id` is a single nullable foreign key. BR §7.5 states assistants may support "assigned doctor(s)" and "Platform policy may allow one or multiple doctors per assistant."
- **Disposition:** Multi-doctor assistant assignment is UNSUPPORTED in the current data model. Single-doctor assignment via `StaffUser.doctor_id` is enforced. No new assignment model or migration created. Multi-doctor support requires explicit Product Owner/architecture decision.
- **Status:** BLOCKED — pending explicit Product Owner decision on multi-doctor assistant assignment policy.

### Additional findings classified:
- R-13 patient update `patient.create` vs `patient.update`: NOT A CODE CHANGE — correct role policy unclear; left blocked for product-owner decision.
- R-15 self-escalation / R-16 last-admin protection: NOT IMPLEMENTED — no existing approved rule; reported unresolved.
- R-07 frontend `super_admin` wildcard bypass: presentation only, not an authorization boundary; no code change.

Verification: `backend/queuing/tests/test_queue.py` 50 passed; `backend/scheduling/tests/test_scheduling.py` 36 passed; `tests/test_security.py`, `patient/tests/`, `identity/tests/` 59 passed; `appointment/tests/` 108 passed. Total: 253 passed, 0 failed.
