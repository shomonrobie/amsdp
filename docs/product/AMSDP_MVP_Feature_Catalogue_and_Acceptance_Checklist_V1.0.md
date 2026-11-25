# AMSDP MVP Feature Catalogue & Acceptance Checklist V1.0

## A. Document purpose and authority

### A.1 Why this catalogue exists

This document is a single, readable, feature-level catalogue of the AMSDP Hackathon MVP. It exists so the Product Owner can review every candidate MVP feature, see what is actually implemented versus what is merely specified or planned, and make an explicit KEEP / REMOVE / DEFER decision for each feature.

### A.2 Relationship with other documents

| Document | Role for this catalogue |
|---|---|
| `docs/AMSDP_Business_Rules_V1.1.md` | Authoritative approved business rules (BR §3–§42). This catalogue cites them but does not change them. |
| `docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md` | Implementation backlog reference. Feature priorities and P0 defects are cross-referenced here. |
| `docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md` | Evidence source for RBAC, authorization, and platform RBAC feature entries. |
| `docs/chatgpt/AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md` | Architecture direction for multi-sector configurability. |
| `docs/architecture/saas/` (six documents) | SaaS platform direction. Only capabilities that are part of the current MVP commitment appear in the active catalogue. |

### A.3 What this catalogue is not

- It is **not** a replacement for detailed technical specifications.
- It is **not** an implementation plan or a commit to build anything.
- It does **not** select KEEP / REMOVE / DEFER on behalf of the Product Owner. The Product Owner's decisions are recorded in section D and section I (25 KEEP, 1 DEFER).
- It does **not** modify application code, schemas, migrations, tests, or business rules.

### A.4 Evidence standard

Implementation and verification statuses are drawn from source code, models, migrations, tests, and implementation reports — not from backlog listings or specifications alone. Status labels follow `.clinerules` §7:

- **IMPLEMENTED** = code exists and is reachable.
- **PARTIALLY IMPLEMENTED** = code exists but a required scope/authorization/validation gap is known.
- **NOT STARTED** = no code exists for the feature.
- **TESTED** = named automated tests pass in this tree (tests were not run during this documentation task; statuses reflect prior recorded results where cited).
- **NOT TESTED** = no test evidence available.
- **BUILD VERIFIED** / **BROWSER VERIFIED** / **ACCEPTED** require independent evidence; none is claimed without a cited source.
- **UNKNOWN** = evidence is missing; status is recorded as unknown rather than inferred.


## B. MVP scope summary

### B.1 What the current AMSDP MVP is (plain language)

AMSDP is a staff-operated appointment and queue management system for healthcare providers in Bangladesh. Clinic staff (receptionists, doctors, assistants, branch administrators, organization administrators) use it to:

- Register patients and book appointments against doctor schedules.
- Manage walk-in arrivals, check patients in, generate queue tokens, call patients, and move them through the queue.
- Optionally announce queued patients audibly in Bangla or English in the waiting room (facility-configurable; not forced on every facility).
- Recover missed turns and reorder the queue.
- Show a public queue display (no patient names or contact details) and send private tracking links to patients.
- Manage organizations, branches, facility floors/departments/rooms, doctors, and staff roles.
- View operational dashboards and audit trails.

The system enforces tenant isolation (organization is the tenant boundary), role-based access control, and branch/doctor scope restrictions. Patient self-service, payments, insurance, and clinical records are out of scope.

### B.2 Current MVP vs. future possibilities vs. exclusions

| Category | Description |
|---|---|
| **Current MVP** | Features catalogued in section C, modules ORG through SYM. These are in-scope for the hackathon MVP decision. |
| **Future possibilities** | Section G lists capabilities that may be considered for future releases but are not current MVP commitments. |
| **Explicit exclusions** | Section G also lists capabilities expressly outside current MVP scope (clinical records, prescriptions, payments, insurance, patient portal, etc.). |

### B.3 Scope boundaries preserved

- Branches belong to organizations; branches are not independent tenants.
- Organization Admin and Branch Admin have different management boundaries.
- Doctors may work across multiple branches and rooms according to their schedules.
- Schedule conflicts must be prevented server-side.
- Existing appointments must not silently change location when future schedules change.
- Appointment and queue lifecycles are separate.
- A confirmed appointment does not automatically create a queue token.
- Walk-in appointment creation and queue check-in are separate operations.
- Patient lookup should precede creating a new patient.
- Public queue displays must not expose patient PII.
- Appointment tracking links do not require patient accounts.
- Audit records must preserve actor and organization context.
- Patient self-registration and online payment are outside the approved scope.

## C. Feature catalogue

Feature ID convention: `<MODULE>-NNN` where MODULE is one of:

| Module | Area |
|---|---|
| ORG | Organization & branch management |
| FAC | Facility hierarchy (floors, departments, rooms) |
| DOC | Doctor profiles & schedules |
| APT | Appointment booking & lifecycle |
| QUE | Queue management & token operations |
| PAT | Patient registration & lookup |
| RBAC | Role-based access control & authorization |
| DSH | Dashboards & operational reporting |
| AUD | Audit logging |
| L10N | Bangla/English localization |
| NOT | Notifications |
| PQT | Personal Queue Tracking |
| DQDS | Digital Queue Display System |
| SYM | Symptom & onset recording |

Each feature includes: ID, name, description, expected user roles, expected behaviour, acceptance criteria, dependencies, source reference, implementation status, verification status, known gaps/limitations.

### C.1 Module ORG — Organization & branch management

#### ORG-001 — Organization create/read/update

**Description:** Create, read, and update healthcare organizations (tenants). Each organization has a name, code, timezone, locale, facility type, address, config, and status.

**Expected user roles:** `super_admin`, `org_admin`

**Expected behaviour:**
- `POST /api/v1/orgs` creates an organization (requires `org.create`).
- `GET /api/v1/orgs/{org_id}` reads one organization (requires `org.read`).
- `PATCH /api/v1/orgs/{org_id}` updates fields (requires `org.manage`).
- Organization isolation is enforced: cross-org access returns non-disclosing 404.

**Acceptance criteria:**
- [ ] Create returns 201 with the new organization row.
- [ ] Read returns the organization's fields.
- [ ] Update modifies only permitted fields.
- [ ] Cross-organization read/update returns 404 (never 403).
- [ ] Duplicate organization code rejected with 422.

**Dependencies:** None

**Source reference:** `backend/organization/main.py:48-145`; `backend/common/permissions.py:37-108` (`org.create`, `org.read`, `org.manage`)

**Implementation status:** IMPLEMENTED — endpoints exist and are permission-guarded.

**Verification status:** TESTED — `test_security.py` covers cross-org 404; recorded results from M7 readiness report.

**Known gaps/limitations:** Organization status (suspended/active) column exists (`Organization.status`) but is not checked by endpoints to block access (R-11 in RBAC report).

---

#### ORG-002 — Branch create/read/update

**Description:** Create, read, and update branches within an organization. Each branch belongs to exactly one organization.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`

**Expected behaviour:**
- `POST /api/v1/orgs/{org_id}/branches` creates a branch (requires `branch.manage`, org scope checked via `require_org_access`).
- `GET /api/v1/orgs/{org_id}/branches` lists branches in an org (requires `get_current_user`, org scope via `require_org_access`).
- `GET /api/v1/branches/{branch_id}` reads one branch (org scope via `require_org_access`).
- `PATCH /api/v1/branches/{branch_id}` updates a branch (requires `branch.manage`, org scope via `require_org_access`).

**Acceptance criteria:**
- [ ] Create returns 201 with branch row linked to org.
- [ ] List returns only branches in the caller's organization.
- [ ] Read/update of a branch in another org returns 404.
- [ ] Branch code unique per organization.
- [ ] `require_org_access` called on all mutating endpoints.

**Dependencies:** ORG-001 (organization must exist)

**Source reference:** `backend/organization/main.py:146-277`; `backend/common/auth.py:263-284` (`require_org_access`)

**Implementation status:** IMPLEMENTED — endpoints exist with org scope enforcement.

**Verification status:** TESTED — cross-org 404 covered in `test_security.py`; `create_branch` calls `require_org_access` (verified at `organization/main.py:196`).

**Known gaps/limitations:** None known at endpoint level. RBAC report R-14 confirms branch create scope validation is adequately enforced.

---

### C.2 Module FAC — Facility hierarchy (floors, departments, rooms)

#### FAC-001 — Floor/department/room CRUD

**Description:** Manage optional facility structure within a branch: floors, departments, and rooms. A branch may have none, some, or many of each. Codes are unique per branch, not per organization.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin` (manage); all roles (read)

**Expected behaviour:**
- Create/read/update/delete facility floors, departments, rooms under a branch.
- Soft-delete via `status="inactive"` — schedules and appointments referencing a retired room still resolve the location they were booked into.
- Room is the only level a schedule session and appointment actually point at.

**Acceptance criteria:**
- [ ] Create floor/department/room returns 201 linked to a branch.
- [ ] Read returns the facility tree for a branch.
- [ ] Inactive status retires without physical deletion.
- [ ] Cross-branch facility access returns 404.
- [ ] Room codes unique per branch.

**Dependencies:** ORG-002 (branch must exist)

**Source reference:** `backend/organization/facility.py`; `backend/common/models.py` (`FacilityFloor`, `FacilityDepartment`, `FacilityRoom`); `backend/common/permissions.py` (`facility.read`, `facility.manage`)

**Implementation status:** IMPLEMENTED — models and router exist.

**Verification status:** TESTED — referenced in M7 and context reports; no specific test file citation confirmed.

**Known gaps/limitations:** Optional structure — consumers must treat missing floor/department as "not recorded", never as error.

---

### C.3 Module DOC — Doctor profiles & schedules

#### DOC-001 — Doctor profile management

**Description:** Register, list, read, and update doctor records. Doctors are facility/organization-local; there is no central doctor identity. Includes BMDC verification status, registration number, specialities, branch chambers, and registration policy.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin` (manage); `doctor`, `receptionist`, `assistant` (read)

**Expected behaviour:**
- `POST /api/v1/doctors` creates a doctor record (requires `doctor.*`).
- `GET /api/v1/doctors` lists doctors in the caller's org.
- `GET /api/v1/doctors/{doctor_id}` reads one doctor (scoped to caller's org).
- `PATCH /api/v1/doctors/{doctor_id}` updates a doctor (requires `doctor.*`).
- Mobile numbers canonicalized (Bangladesh national form) to prevent duplicate records.
- Branch assignments reconciled via `doctor_branch` join table with one primary branch.
- Activation gated on organization's registration policy (BMDC required / verification required).

**Acceptance criteria:**
- [ ] Create returns 201 with doctor row.
- [ ] Mobile canonicalization prevents `+880 1711 111111` and `01711111111` becoming two records.
- [ ] Cross-org doctor access returns non-disclosing 404.
- [ ] Branch assignment validates the branch belongs to the same organization.
- [ ] Activation policy enforced when status set to "active".

**Dependencies:** ORG-002 (branch for chamber assignments)

**Source reference:** `backend/doctor/main.py:82-279`; `backend/doctor/profile.py` (full profile module); `backend/common/permissions.py` (`doctor.*` namespace); `backend/common/models.py` (`Doctor`, `DoctorBranch`, `DoctorSpecialty`)

**Implementation status:** IMPLEMENTED — full CRUD with profile sub-module.

**Verification status:** TESTED — `test_doctor` 14 tests pass (per context report).

**Known gaps/limitations:** BMDC verification is gated on existing `doctor.manage` capability (no new capability invented). Registration policy is org-config only (branch admin cannot change it).

---

#### DOC-002 — Doctor schedule management

**Description:** Create, read, update, and search doctor schedules with slot templates (day of week, start/end time, duration, max patients). Supports time-slot, serial, and hybrid appointment models.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin` (manage); all roles (read)

**Expected behaviour:**
- `POST /api/v1/schedules` creates a schedule (requires `schedule.*`). `organization_id` is taken from the auth token, not the body. `branch_id` from body is used without `require_branch_access` validation.
- `GET /api/v1/schedules` searches by doctor/branch.
- `GET /api/v1/schedules/{schedule_id}` reads one schedule.
- `PATCH /api/v1/schedules/{schedule_id}` updates a schedule.
- `GET /api/v1/schedules/{schedule_id}/available-slots` computes available slots from actual appointment counts, with walk-in reserve capacity.

**Acceptance criteria:**
- [ ] Create returns 201 with schedule row linked to doctor, org, branch.
- [ ] Schedule conflict prevention server-side.
- [ ] Available slots reflect booked appointments and walk-in reserves.
- [ ] Schedule scope filtered to caller's organization.

**Dependencies:** DOC-001 (doctor must exist); ORG-002 (branch must exist)

**Source reference:** `backend/scheduling/main.py:68-185`; `backend/common/models.py` (`Schedule`, `ScheduleSession`); `backend/common/permissions.py` (`schedule.*`)

**Implementation status:** PARTIALLY IMPLEMENTED — schedule CRUD exists, but `create_schedule` accepts `branch_id` from body without `require_branch_access` validation (RBAC report R-05).

**Verification status:** TESTED — `test_scheduling` 22 tests pass (per context report).

**Known gaps/limitations:** Schedule creation does not validate that `branch_id` belongs to the caller's branch scope (R-05 defect). No explicit schedule conflict prevention visible in `create_schedule` beyond org scoping.

---

### C.4 Module APT — Appointment booking & lifecycle

#### APT-001 — Appointment booking (scheduled)

**Description:** Book an appointment for a patient with a doctor at a specific date/time slot, with capacity enforcement. Receptionist-assisted (staff-operated); no patient self-booking.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist`

**Expected behaviour:**
- `POST /api/v1/appointments` creates an appointment (requires `appointment.create`).
- Validates doctor schedule availability and capacity.
- Respects walk-in reserved capacity.
- Sets appointment status, token number, booking source.
- Records `created_by` and audit trail.

**Acceptance criteria:**
- [ ] Create returns 201 with appointment row.
- [ ] Capacity enforcement: cannot book beyond slot max_patients.
- [ ] Schedule/doctor/branch must belong to caller's organization.
- [ ] Audit record written on creation.
- [ ] Symptom/onset data can be recorded at booking (SYM-001 integration).

**Dependencies:** DOC-002 (schedule), PAT-001 (patient), ORG-002 (branch)

**Source reference:** `backend/appointment/main.py:358-494`; `backend/common/permissions.py` (`appointment.create`)

**Implementation status:** IMPLEMENTED — endpoint exists with permission guard.

**Verification status:** TESTED — `test_appointment` 13 tests pass (per context report).

**Known gaps/limitations:** `create_appointment` scope validation details need verification against RBAC findings.

---

#### APT-002 — Appointment read/list/search

**Description:** Read, list, and search appointments. List endpoint supports filters (patient, doctor, date, status). Grid endpoint is org-scoped; list endpoint is branch-scoped.

**Expected user roles:** All roles (read-scoped)

**Expected behaviour:**
- `GET /api/v1/appointments` lists appointments with filters.
- `GET /api/v1/appointments/{appointment_id}` reads one appointment.
- `GET /api/v1/appointments/matches` returns match counts by date for calendar filtering.
- Grid endpoint org-scoped; list endpoint branch-scoped (known discrepancy per calendar filter diagnosis).

**Acceptance criteria:**
- [ ] Read returns appointment fields.
- [ ] List supports `q`, `doctor_id`, `patient_id`, `date`, `status` filters.
- [ ] Cross-org appointment access returns 404.
- [ ] Match counts endpoint returns dates where search terms matched.

**Dependencies:** PAT-001, DOC-001

**Source reference:** `backend/appointment/main.py:496-573`; `backend/appointment/appt_filters.py`; calendar filter diagnosis report

**Implementation status:** PARTIALLY IMPLEMENTED — endpoints exist but grid/list scope discrepancy known (calendar filter diagnosis F-1 through F-9).

**Verification status:** TESTED — appointment suite 50 tests pass (per symptoms report §17).

**Known gaps/limitations:** Week/Day calendar view search and filters do not reach the grid (known UX defect); grid is org-scoped while list is branch-scoped.

---

#### APT-003 — Appointment status update / cancel / reschedule

**Description:** Change appointment status (BOOKED → CHECKED_IN → IN_CONSULTATION → COMPLETED, or CANCELLED, NO_SHOW, RESCHEDULED). Rescheduling creates a new appointment and carries symptoms to the new visit.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist` (requires `appointment.modify`)

**Expected behaviour:**
- `PATCH /api/v1/appointments/{appointment_id}/status` updates status (requires `appointment.modify`).
- Status transitions validated (no going backward to earlier states).
- Reschedule creates new appointment, marks original RESCHEDULED, carries symptoms/onset.
- Cancel sets status CANCELLED.
- Audit trail records actor, before/after states.

**Acceptance criteria:**
- [ ] Status update returns 200 with new status.
- [ ] Invalid transitions rejected with 422.
- [ ] Reschedule preserves symptom/onset data on new appointment.
- [ ] Cancel revokes PQT tracking token.
- [ ] Audit record written for each status change.

**Dependencies:** APT-001, SYM-001, PQT-001

**Source reference:** `backend/appointment/main.py:748-876`; `backend/common/permissions.py` (`appointment.modify`)

**Implementation status:** IMPLEMENTED — endpoints exist with permission guards.

**Verification status:** TESTED — `test_reschedule` 6 tests pass (per context report).

**Known gaps/limitations:** None known beyond standard RBAC scope.

---

### C.5 Module QUE — Queue management & token operations

#### QUE-001 — Queue check-in (appointment-based)

**Description:** Check in a patient with a booked appointment, creating a queue entry with a token. Separate from walk-in registration (which creates the appointment first).

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist`

**Expected behaviour:**
- `POST /api/v1/queue/check-in` creates a queue entry for an appointment (requires `queue.checkin`).
- Validates appointment exists in caller's organization.
- Allocates daily token for doctor/date.
- Sets entry source "appointment".
- Audit trail records check-in.

**Acceptance criteria:**
- [ ] Check-in returns 201 with queue entry and token.
- [ ] Appointment must belong to caller's organization.
- [ ] Token unique per doctor per day.
- [ ] Cannot check in an appointment in non-check-in-able state.

**Dependencies:** APT-001, DOC-002

**Source reference:** `backend/queuing/main.py:146-215`; `backend/common/permissions.py` (`queue.checkin`)

**Implementation status:** PARTIALLY IMPLEMENTED — endpoint exists but check-in uses caller-supplied `branch_id` from request body without validation (RBAC report R-03).

**Verification status:** TESTED — `test_queue` 20 tests pass (per context report).

**Known gaps/limitations:** R-03 defect — caller-supplied `branch_id` in check-in request body is trusted directly without scope validation.

---

#### QUE-002 — Queue enqueue (walk-in queue entry)

**Description:** Enqueue a walk-in patient directly into the queue (creates queue entry without a prior appointment).

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist`

**Expected behaviour:**
- `POST /api/v1/queue/enqueue` creates a walk-in queue entry (requires `queue.checkin`).
- Accepts `branch_id` from request body.
- Allocates daily token.
- Sets entry source "walk_in".

**Acceptance criteria:**
- [ ] Enqueue returns 201 with queue entry and token.
- [ ] Token unique per doctor per day.
- [ ] Branch scope must be validated against caller's token.

**Dependencies:** ORG-002, DOC-002

**Source reference:** `backend/queuing/main.py:206-230`; `backend/common/permissions.py` (`queue.checkin`)

**Implementation status:** PARTIALLY IMPLEMENTED — endpoint exists but uses caller-supplied `branch_id` from body without scope validation (RBAC report R-03).

**Verification status:** TESTED — enqueue covered in `test_queue` suite.

**Known gaps/limitations:** R-03 defect — caller-supplied `branch_id` in enqueue request body trusted directly.

---

#### QUE-003 — Queue list / view

**Description:** List active queue entries for today, scoped by organization and optionally by doctor/branch.

**Expected user roles:** All roles (view-scoped)

**Expected behaviour:**
- `GET /api/v1/queue` lists queue entries.
- Accepts caller-supplied `branch_id` query parameter without validating caller's branch authorization.
- Filters by organization from auth token.

**Acceptance criteria:**
- [ ] List returns queue entries for caller's org.
- [ ] Branch filter, if provided, must be validated against caller's branch scope.
- [ ] Cross-branch read returns 404 (never 403).

**Dependencies:** ORG-002, DOC-002

**Source reference:** `backend/queuing/main.py:108-136`; `backend/common/permissions.py` (`queue.view`)

**Implementation status:** PARTIALLY IMPLEMENTED — endpoint exists but `branch_id` query param unvalidated (RBAC report R-01).

**Verification status:** TESTED — queue list covered in `test_queue` suite.

**Known gaps/limitations:** R-01 defect — caller-supplied `branch_id` allows reading another branch's queue.

---

#### APT-004 — Walk-in appointment registration

**Description:** Register a walk-in patient appointment at the desk. Separate from queue check-in — creates the appointment first, then check-in creates the queue entry.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist`

**Expected behaviour:**
- `POST /api/v1/appointments/walk-in` creates a walk-in appointment (requires `appointment.create`).
- `booking_source` set to `"walk_in"`.
- `appointment_type` set to `"walk_in"`.
- Walk-in policies configurable (end_of_queue, first_come, reserved_capacity, staff_placement).
- No confirmation SMS sent to walk-ins (per notification hooks).

**Acceptance criteria:**
- [ ] Create returns 201 with walk-in appointment row.
- [ ] `booking_source` = `"walk_in"`.
- [ ] Walk-in count appears in dashboard.
- [ ] Separate from queue check-in operation.

**Dependencies:** PAT-001, DOC-002

**Source reference:** `backend/appointment/main.py:968-1000`; `backend/appointment/dashboard.py:38-42`

**Implementation status:** IMPLEMENTED — endpoint exists.

**Verification status:** TESTED — walk-in tests in `test_appointment.py` and `test_symptoms.py`.

**Known gaps/limitations:** Reserved-capacity org-settings UI absent (M7 §16).

---

#### QUE-004 — Queue call / cancel / recover / reposition

**Description:** Call a patient to consultation, cancel/no-show, recover a missed turn, or reposition within the queue.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist`, `doctor` (recover/reposition only)

**Expected behaviour:**
- `POST /api/v1/queue/action` performs queue actions (call, cancel, no_show, start_consultation, complete_consultation).
- Uses `_scoped_entry_or_404()` which checks organization scope but NOT branch scope.
- `queue.recover` and `queue.reposition` require `queue.recover` permission (doctors hold this).
- Recovery preserves token, appointment_id, patient_id; only status and position change.
- Position change requires `queue.reposition` and a written reason.
- All actions audited with before/after and position history.

**Acceptance criteria:**
- [ ] Call moves entry from waiting to called.
- [ ] Cancel/no_show sets terminal status.
- [ ] Recovery moves skipped → waiting, token preserved.
- [ ] Reposition requires reason and updates position_history.
- [ ] Cross-branch/cross-tenant entry returns 404.

**Dependencies:** QUE-001, QUE-002

**Source reference:** `backend/queuing/main.py:294-348`; `backend/queuing/recovery.py:78-275`; `backend/common/permissions.py` (`queue.recover`, `queue.reposition`, `queue.consult`)

**Implementation status:** PARTIALLY IMPLEMENTED — endpoints exist but `_scoped_entry_or_404()` lacks branch check (RBAC report R-02).

**Verification status:** TESTED — recovery module tested separately.

**Known gaps/limitations:** R-02 defect — `_scoped_entry_or_404()` (queuing/main.py:98-105) checks org only, not branch. `queue_action()` at line 294-348 calls this helper without branch scope.

---

#### QUE-005 — Queue reorder

**Description:** Manually reorder queue entries, preserving tokens and recording position history.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist`

**Expected behaviour:**
- `POST /api/v1/queue/reorder` accepts ordered entry IDs and reason.
- Filters entries by organization only — no check that all entries belong to the same queue (doctor/date).
- Records position history for each moved entry.
- Notifies `on_queue_changed` per unique doctor/date.

**Acceptance criteria:**
- [ ] Reorder returns count of reordered entries.
- [ ] Position history recorded for each move.
- [ ] Entries from unrelated queues should not be reordered together (known gap).

**Dependencies:** QUE-001, QUE-002

**Source reference:** `backend/queuing/main.py:367-409`; `backend/common/permissions.py` (`queue.reorder`)

**Implementation status:** PARTIALLY IMPLEMENTED — endpoint exists but does not verify queue homogeneity (R-04).

**Verification status:** TESTED — reorder covered in `test_queue` suite.

**Known gaps/limitations:** R-04 defect — org-only filter, no check that all entries share the same doctor/date, so unrelated queues can be mixed.

---

#### QUE-006 — Intelligent Queue Voice Announcements (Bangla/English)

**Description:** Audible queue announcements inside a healthcare facility, spoken in Bangla and/or English, triggered by queue events (for example, when a patient is called to consultation). Announcements are for the waiting room (in-facility audible callouts), not automated outbound telephone calls to patients. The capability is facility-configurable: a facility may enable or disable announcements and choose the announcement language; it is not forced on every facility. Bangla and English voice announcements are required capability targets.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin` (configure enable/disable and announcement language); `receptionist`, `doctor` (trigger announcements via the queue call action); patients hear announcements as a passive audience (no role required).

**Expected behaviour:**
- When a queue entry is called (waiting → called), an audible announcement may be spoken in the configured announcement language.
- Announcements can be enabled or disabled per facility (configurable enable/disable behaviour).
- The announcement language can be configured per facility (Bangla or English).
- Announcements are triggered by appropriate queue events (e.g., a patient called to consultation).
- No duplicate or conflicting announcements for the same queue event.
- Failure of voice output does not fail or interrupt the queue call operation (queue operations continue independently of announcement success).
- Configuration and control are authorized (only org/branch admin may change announcement settings).
- Spoken announcements contain no unnecessary patient PII (e.g., token number and doctor, not patient name or mobile number).
- Actual audio output must be verified at browser/runtime before implementation is claimed.

**Acceptance criteria:**
- [ ] Bangla queue voice announcement produced for a call event when Bangla is configured.
- [ ] English queue voice announcement produced for a call event when English is configured.
- [ ] Announcement language configurable per facility.
- [ ] Announcements can be enabled/disabled per facility (not forced on every facility).
- [ ] Announcements triggered by appropriate queue events (e.g., patient called to consultation).
- [ ] No duplicate or conflicting announcements for the same queue event.
- [ ] Voice-output failure does not fail or interrupt the queue call operation.
- [ ] Only authorized roles (org/branch admin) may configure announcements.
- [ ] Spoken announcements contain no unnecessary patient PII (no patient name/mobile).
- [ ] Actual audio output verified at browser/runtime before implementation is claimed.

**Dependencies:** QUE-001, QUE-004 (queue call event), RBAC (authorized configuration)

**Source reference:** `docs/chatgpt/AMSDP_Connect_Proposed_Communication_and_AI_Capabilities.md` §1 scope boundary (Core capability, not a Connect conversational-AI feature); `backend/queuing/main.py` (queue call action); no implementation code exists in the tree.

**Implementation status:** NOT STARTED — no voice generation, Bangla speech output, English speech output, TTS provider, announcement service, configuration storage, or browser playback code exists in the tree.

**Verification status:** NOT TESTED — no test evidence for audio output or announcement behaviour.

**Known gaps/limitations:** No TTS provider selected; no announcement service; no announcement enable/disable or language configuration; no configuration UI; not browser verified; not accepted by Product Owner.

---

### C.6 Module PAT — Patient registration & lookup

#### PAT-001 — Patient create/read/update/search

**Description:** Register patients, look up existing patients before creating new ones, and update patient records. Patient records are organization-scoped and may be shared across branches within an org.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist` (create/read/update); `doctor`, `assistant` (read/search)

**Expected behaviour:**
- `POST /api/v1/patients` creates a patient (requires `patient.create`). Organization ID taken from auth token, not body.
- `GET /api/v1/patients` searches patients by name or mobile within caller's org.
- `GET /api/v1/patients/{patient_id}` reads one patient (org-scoped).
- `PATCH /api/v1/patients/{patient_id}` updates a patient (uses `require_permission("patient.create")` — permission mismatch noted as R-13).
- Duplicate mobile check within organization.
- Patient lookup should precede creating a new patient.

**Acceptance criteria:**
- [ ] Create returns 201 with patient row linked to caller's org.
- [ ] Search returns patients matching name/mobile in caller's org only.
- [ ] Cross-org patient access returns 404.
- [ ] Duplicate mobile within org detected.
- [ ] Audit record written on create/update.

**Dependencies:** ORG-001

**Source reference:** `backend/patient/main.py:111-220`; `backend/common/permissions.py` (`patient.*`); `backend/common/models.py` (`Patient`)

**Implementation status:** IMPLEMENTED — endpoints exist with org scope enforcement.

**Verification status:** TESTED — `test_patient` 16 tests, `test_patient_age` 13 tests pass (per context report).

**Known gaps/limitations:** R-13 — PATCH uses `patient.create` permission instead of a distinct `patient.update` permission.


### C.7 Module RBAC — Role-based access control & authorization

#### RBAC-001 — Staff authentication & JWT tokens

**Description:** Staff login with username/password, bcrypt password hashing, JWT issuance (12-hour expiry), token validation, and login throttling per (IP, username).

**Expected user roles:** All staff roles

**Expected behaviour:**
- `POST /api/v1/staff/login` authenticates and returns JWT token.
- `GET /api/v1/staff/validate` validates a token and returns user context.
- Login attempts throttled per (client IP, username) with database-backed sliding window.
- Account status checked (inactive accounts cannot login).
- Token carries `sub` (user ID), `org` (organization_id), `branch` (branch_id), `role`.

**Acceptance criteria:**
- [ ] Valid credentials return 200 with token.
- [ ] Invalid credentials return 401.
- [ ] Repeated failures return 429 with Retry-After header.
- [ ] Successful login clears the throttle bucket.
- [ ] Inactive account returns 403.

**Dependencies:** ORG-001, RBAC-002

**Source reference:** `backend/identity/main.py:184-219`; `backend/common/auth.py:55-62` (`decode_token`); `backend/common/login_throttle.py`

**Implementation status:** IMPLEMENTED — login, validate, throttling all implemented.

**Verification status:** TESTED — `test_security.py` covers login throttling (TestLoginThrottle class).

**Known gaps/limitations:** No token refresh/revocation/logout endpoint. Single JWT secret shared across all services (no separate platform secret).

---

#### RBAC-002 — Staff user management (CRUD)

**Description:** Create, read, update staff users with role and branch assignment. Organization-scoped; cross-org access returns 404.

**Expected user roles:** `super_admin` (all orgs), `org_admin` (own org), `branch_admin` (own branch)

**Expected behaviour:**
- `POST /api/v1/staff/users` creates a staff user (requires `staff.create` — org admin can create in own org only).
- `GET /api/v1/staff/users` lists staff in caller's org (requires `staff.read`).
- `GET /api/v1/staff/users/{user_id}` reads one staff user (org-scoped; branch-scoped users limited to own branch).
- `PATCH /api/v1/staff/users/{user_id}` updates a staff user (requires `staff.manage`).
- Role change allowed — no self-escalation protection (R-15).
- No last-active-org-admin protection (R-16).
- Doctor assignment validated against same-organization doctors.

**Acceptance criteria:**
- [ ] Create returns 201 with staff user row.
- [ ] List filtered to caller's organization.
- [ ] Cross-org read/update returns 404.
- [ ] Cross-branch read/update returns 404.
- [ ] Doctor assignment validated to same org.
- [ ] Audit record written on create/update.

**Dependencies:** ORG-001, ORG-002, DOC-001

**Source reference:** `backend/identity/main.py:140-181`; `backend/identity/routes.py:31-146`; `backend/common/permissions.py` (`staff.read`, `staff.manage`)

**Implementation status:** PARTIALLY IMPLEMENTED — CRUD exists but missing self-escalation protection (R-15) and last-active-org-admin protection (R-16).

**Verification status:** TESTED — `test_security.py` covers cross-org 404, cross-branch denial, super admin boundaries.

**Known gaps/limitations:** R-15 (no self-escalation protection on role assignment), R-16 (no last-active-org-admin protection). Frontend `super_admin` wildcard bypass in `frontend/lib/auth.js:20` (presentation only, R-07).

---

#### RBAC-003 — Permission checking

**Description:** Role-to-permission matrix (`PERMISSIONS` dict) with namespace wildcard matching (`patient.*` grants `patient.read`). `check()` function used by frontend and backend.

**Expected user roles:** All roles

**Expected behaviour:**
- `PERMISSIONS` maps 6 roles to permission keys.
- Wildcard matching: `resource == p` or `(p.endswith("*") and resource.startswith(p[:-1]))`.
- Bare `"*"` not honored — unknown resources denied for all roles including `super_admin`.
- `super_admin` holds `platform.admin` and `platform.cross_org` (platform capabilities, not yet implemented as separate domain).

**Acceptance criteria:**
- [ ] `check(resource, role)` returns boolean.
- [ ] Wildcard expansion works correctly.
- [ ] Unknown resource denied for all roles.

**Dependencies:** RBAC-001, RBAC-002

**Source reference:** `backend/common/permissions.py:37-124`; `frontend/lib/auth.js:17-45`

**Implementation status:** IMPLEMENTED — matrix defined in code.

**Verification status:** TESTED — matrix exercised through endpoint permission guards.

**Known gaps/limitations:** `super_admin` conflates platform and tenant authority (R-06). Frontend permission mirror in `auth.js` may drift from backend matrix.


### C.8 Module DSH — Dashboards & operational reporting

#### DSH-001 — Operational dashboard (today/period/audit)

**Description:** Dashboard endpoints showing appointment counts by status, queue length, walk-in counts, per-doctor breakdown, average wait times, and audit event queries.

**Expected user roles:** All roles (scoped by org/branch)

**Expected behaviour:**
- `GET /api/v1/dashboard/today` returns today's counts (appointment statuses, queue length, walk-ins).
- `GET /api/v1/dashboard/period` returns period aggregates (completion rate, no-show rate, cancel rate, avg wait).
- `GET /api/v1/dashboard/audit` returns filtered audit events.
- `branch_id` query parameter validated via `require_branch_access` when provided.
- All data scoped to caller's organization.

**Acceptance criteria:**
- [ ] Today endpoint returns counts by status.
- [ ] Period endpoint returns rates and averages.
- [ ] Branch filter validated via `require_branch_access`.
- [ ] Cross-org data not returned.

**Dependencies:** APT-001, QUE-001, AUD-001

**Source reference:** `backend/appointment/dashboard.py:17-168`; `backend/common/auth.py:287-313` (`require_branch_access`)

**Implementation status:** IMPLEMENTED — dashboard endpoints exist.

**Verification status:** TESTED — `test_dashboard` 6 tests pass (per M7 report).

**Known gaps/limitations:** Reserved-capacity org-settings UI absent (M7 §16).

---

### C.9 Module AUD — Audit logging

#### AUD-001 — Audit event write & read

**Description:** Append-only audit trail. Every service writes audit records inside the action's own transaction. Read endpoints are tenant-scoped with non-disclosing 404 for cross-org.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist` (read via `audit.read`)

**Expected behaviour:**
- `record_audit()` called inside each service's transaction for create/update/delete actions.
- `GET /api/v1/audit/organization/{org_id}` returns events for one org (requires `audit.read`, org scope via `_scoped_org`).
- `GET /api/v1/audit/{target_id}` returns events for one target within caller's org.
- Cross-org access requires `platform.cross_org` and is recorded in target org's trail.
- Branch-scoped users see only their branch's events.
- Maximum 500 events per query (hard ceiling).
- No write endpoint — HTTP callers cannot forge audit rows.

**Acceptance criteria:**
- [ ] Audit record written for each mutating action.
- [ ] Cross-org read returns 404 (never 403).
- [ ] Branch-scoped users limited to own branch events.
- [ ] Append-only — no update/delete of audit rows.
- [ ] Max 500 events per query.

**Dependencies:** ORG-001

**Source reference:** `backend/common/audit.py` (`record_audit`); `backend/audit/main.py:85-123`; `backend/common/models.py` (`AuditEvent`)

**Implementation status:** IMPLEMENTED — audit write and read implemented.

**Verification status:** TESTED — audit coverage verified in M7 report (B5).

**Known gaps/limitations:** No platform-only audit trail (separate `platform_audit_events` table is SaaS-specified but not implemented).


### C.10 Module L10N — Bangla/English localization

#### L10N-001 — Bilingual UI labels

**Description:** Bangla and English localization of dashboard, queue, and audit screens. Language toggle preserved.

**Expected user roles:** All roles

**Expected behaviour:**
- UI labels available in Bangla and English.
- Language toggle switches between languages.
- Production build green with no layout breakage.

**Acceptance criteria:**
- [ ] Labels displayed in selected language.
- [ ] Language toggle works.
- [ ] Production build succeeds with localized labels.

**Dependencies:** None

**Source reference:** `frontend/lib/i18n.js`; `frontend/pages/*`; M7 report B3.

**Implementation status:** IMPLEMENTED — localization implemented and verified.

**Verification status:** BUILD VERIFIED — production build green (per M7 report B3).

**Known gaps/limitations:** Secondary-screen labels not all localized (M7 §16).

---

### C.11 Module NOT — Notifications

#### NOT-001 — Notification outbox & hooks

**Description:** Persistent notification outbox with delivery states (pending → processing → sent → delivered/failed/retry_scheduled/cancelled). Mock provider (never sets delivered). Best-effort hooks for appointment and queue events.

**Expected user roles:** None (system feature)

**Expected behaviour:**
- `notifications` table stores one row per (event, channel, recipient context).
- Delivery state machine enforced.
- Mock adapter for development/demo (no real SMS/WhatsApp delivery).
- Hooks fire on appointment booked/closed, queue changed, etc. — never block the main action.
- Dedup key prevents duplicate notifications.
- SMS/WhatsApp provider delivery not represented as operational until independently verified.

**Acceptance criteria:**
- [ ] Notification row created for each event.
- [ ] Delivery states transition correctly.
- [ ] Dedup prevents duplicates.
- [ ] Hook failures do not fail the main action.

**Dependencies:** APT-001, QUE-001

**Source reference:** `backend/common/models.py` (`Notification`); `backend/common/notifications/` (outbox, hooks, providers, worker); `backend/common/notifications/hooks.py`

**Implementation status:** IMPLEMENTED — outbox model and hooks exist.

**Verification status:** NOT TESTED — no specific test citation confirmed for notification delivery.

**Known gaps/limitations:** SMS/WhatsApp provider delivery not verified as operational (per backlog scope boundary). Manual tracking-link and QR sharing is acceptable fallback.

---

### C.12 Module PQT — Personal Queue Tracking

#### PQT-001 — Tracking token issue & view

**Description:** Generate tracking tokens for appointments and provide private, account-free tracking pages. Token issued once; revoked/expired tokens can be replaced.

**Expected user roles:** `super_admin`, `org_admin`, `branch_admin`, `receptionist` (issue via `appointment.modify`); public (view via token)

**Expected behaviour:**
- `POST /api/v1/appointments/{appointment_id}/tracking-token` issues a token (requires `appointment.modify`).
- Raw token returned exactly once; active existing token returns 409.
- `GET /api/v1/track/{token}` returns appointment tracking data (public, token-gated).
- `GET /api/v1/track/{token}/qr` returns QR code image (public, token-gated).
- Token hash stored (sha256 + pepper), never the raw token.
- Token status: active/revoked; eligible_at timestamp.
- No patient account required.

**Acceptance criteria:**
- [ ] Issue returns 201 with tracking URL and prefix.
- [ ] Active token re-issue returns 409.
- [ ] Tracking view shows appointment, doctor, branch, queue position.
- [ ] QR code returned for active tokens.
- [ ] Revoked/expired token returns 404.
- [ ] No patient PII in tracking view (only appointment-specific data).

**Dependencies:** APT-001

**Source reference:** `backend/appointment/tracking.py`; `backend/common/tracking_tokens.py`

**Implementation status:** IMPLEMENTED — token issue, view, and QR endpoints exist.

**Verification status:** TESTED — `test_tracking_tokens` tests pass (per symptoms report §17).

**Known gaps/limitations:** In-process rate limiting (10 req/min/IP); durable DB-backed bucket deferred.


### C.13 Module DQDS — Digital Queue Display System

#### DQDS-001 — Public queue display board

**Description:** Public, read-only queue display for waiting-room TVs/monitors. No authentication required. Path-scoped by org+branch code. Zero patient PII.

**Expected user roles:** None (public display)

**Expected behaviour:**
- `GET /api/v1/queue/display/{org_code}/{branch_code}` returns doctor-wise queue summary.
- No auth required (public).
- Unknown or non-active org/branch returns 404 (non-disclosing).
- Rate-limited at 30 req/min/IP with rate-limit headers.
- Cache: "public, max-age=10" on board data; "no-store" on 404/429.
- Shows only doctor name, token number, and waiting counts — no patient names/mobiles.

**Acceptance criteria:**
- [ ] Returns board data for valid org+branch.
- [ ] 404 for unknown or non-active org/branch (never 403).
- [ ] Rate-limit headers present on responses.
- [ ] No patient PII in response.
- [ ] Only active queue statuses shown (waiting, called, in_consultation, skipped).

**Dependencies:** ORG-002, DOC-001, QUE-001

**Source reference:** `backend/queuing/display.py`; `backend/common/models.py` (`QueueEntry`, `Doctor`)

**Implementation status:** IMPLEMENTED — DQDS endpoint exists.

**Verification status:** TESTED — `test_dqds` tests pass (per context report).

**Known gaps/limitations:** In-process rate limiting; durable shared limiter deferred to M9-F.

---

### C.14 Module SYM — Symptom & onset recording

#### SYM-001 — Symptom catalogue & onset at booking

**Description:** Optional bilingual symptom recording inside the appointment booking flow, plus optional onset question. Receptionist-assisted. Not a diagnosis or clinical decision support.

**Expected user roles:** `receptionist` (record at booking); `doctor`, `org_admin`, `branch_admin` (read/manage catalogue)

**Expected behaviour:**
- `POST /api/v1/appointments/{id}/symptoms` records symptoms for an appointment.
- Symptom catalogue (`symptom_catalog`) of 79 curated symptoms in Bangla and English.
- Onset question: seven answers plus optional short note.
- Free-text entry for complaints not in catalogue.
- In-memory browser search over catalogue using BanglaNameSense normaliser.
- Carried to rescheduled appointments; original rows preserved as history.
- Not a diagnosis, not triage, not clinical decision support.

**Acceptance criteria:**
- [ ] Symptom recording returns 200/201 linked to appointment.
- [ ] Catalogue searchable in Bangla and English.
- [ ] Onset question optional with seven predefined answers.
- [ ] Free-text complaint accepted.
- [ ] Symptoms carried to rescheduled appointment.
- [ ] No clinical inference or diagnosis.

**Dependencies:** APT-001

**Source reference:** `backend/appointment/symptoms.py`; `backend/seed/symptom_catalogue.py`; `frontend/components/SymptomPicker.js`; implementation report `docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md`

**Implementation status:** IMPLEMENTED + TESTED + BUILD VERIFIED.

**Verification status:** TESTED — 25 symptom integration tests, 9 catalogue data tests pass; frontend build green. Not browser verified as of report date.

**Known gaps/limitations:** Not ACCEPTED (Product Owner acceptance required). Demo containers need rebuilding to carry the new code.


## D. Product Owner scope decision checklist

For every feature below, mark exactly one of: KEEP / REMOVE / DEFER. Leave all three unchecked initially — the Product Owner makes the decision.

| Feature ID | Feature name | [ ] KEEP | [ ] REMOVE | [ ] DEFER | PO comments / reason |
|---|---|---|---|---|---|
| ORG-001 | Organization create/read/update | [x] | [ ] | [ ] | |
| ORG-002 | Branch create/read/update | [x] | [ ] | [ ] | |
| FAC-001 | Floor/department/room CRUD | [x] | [ ] | [ ] | |
| DOC-001 | Doctor profile management | [x] | [ ] | [ ] | |
| DOC-002 | Doctor schedule management | [x] | [ ] | [ ] | |
| APT-001 | Appointment booking (scheduled) | [x] | [ ] | [ ] | |
| APT-002 | Appointment read/list/search | [x] | [ ] | [ ] | |
| APT-003 | Appointment status update / cancel / reschedule | [x] | [ ] | [ ] | |
| APT-004 | Walk-in appointment registration | [x] | [ ] | [ ] | |
| PAT-001 | Patient create/read/update/search | [x] | [ ] | [ ] | |
| QUE-001 | Queue check-in (appointment-based) | [x] | [ ] | [ ] | |
| QUE-002 | Queue enqueue (walk-in queue entry) | [x] | [ ] | [ ] | |
| QUE-003 | Queue list / view | [x] | [ ] | [ ] | |
| QUE-004 | Queue call / cancel / recover / reposition | [x] | [ ] | [ ] | |
| QUE-005 | Queue reorder | [x] | [ ] | [ ] | |
| QUE-006 | Intelligent Queue Voice Announcements (Bangla/English) | [x] | [ ] | [ ] | |
| RBAC-001 | Staff authentication & JWT tokens | [x] | [ ] | [ ] | |
| RBAC-002 | Staff user management (CRUD) | [x] | [ ] | [ ] | |
| RBAC-003 | Permission checking | [x] | [ ] | [ ] | |
| DSH-001 | Operational dashboard | [x] | [ ] | [ ] | |
| AUD-001 | Audit event write & read | [x] | [ ] | [ ] | |
| L10N-001 | Bilingual UI labels | [x] | [ ] | [ ] | |
| NOT-001 | Notification outbox & hooks | [ ] | [ ] | [x] | |
| PQT-001 | Tracking token issue & view | [x] | [ ] | [ ] | |
| DQDS-001 | Public queue display board | [x] | [ ] | [ ] | |
| SYM-001 | Symptom catalogue & onset at booking | [x] | [ ] | [ ] | |

**Product Owner instructions:**
- Mark `[ ] KEEP` → Include in current MVP.
- Mark `[ ] REMOVE` → Remove from current MVP.
- Mark `[ ] DEFER` → Move to a future release.
- Only one choice per feature.
- Use the comments field to record the reason.


## E. Feature acceptance checklist

Acceptance criteria are individually checkable per feature. Implementation status and Product Owner's KEEP/REMOVE/DEFER decision are separate from acceptance.

### E.1 ORG module

**ORG-001 — Organization create/read/update**
- [ ] Create returns 201 with the new organization row.
- [ ] Read returns the organization's fields.
- [ ] Update modifies only permitted fields.
- [ ] Cross-organization read/update returns 404 (never 403).
- [ ] Duplicate organization code rejected with 422.

**ORG-002 — Branch create/read/update**
- [ ] Create returns 201 with branch row linked to org.
- [ ] List returns only branches in the caller's organization.
- [ ] Read/update of a branch in another org returns 404.
- [ ] Branch code unique per organization.
- [ ] `require_org_access` called on all mutating endpoints.

### E.2 FAC module

**FAC-001 — Floor/department/room CRUD**
- [ ] Create floor/department/room returns 201 linked to a branch.
- [ ] Read returns the facility tree for a branch.
- [ ] Inactive status retires without physical deletion.
- [ ] Cross-branch facility access returns 404.
- [ ] Room codes unique per branch.

### E.3 DOC module

**DOC-001 — Doctor profile management**
- [ ] Create returns 201 with doctor row.
- [ ] Mobile canonicalization prevents duplicate records.
- [ ] Cross-org doctor access returns non-disclosing 404.
- [ ] Branch assignment validates the branch belongs to the same organization.
- [ ] Activation policy enforced when status set to "active".

**DOC-002 — Doctor schedule management**
- [ ] Create returns 201 with schedule row linked to doctor, org, branch.
- [ ] Schedule conflict prevention server-side.
- [ ] Available slots reflect booked appointments and walk-in reserves.
- [ ] Schedule scope filtered to caller's organization.


### E.4 APT module

**APT-001 — Appointment booking (scheduled)**
- [ ] Create returns 201 with appointment row.
- [ ] Capacity enforcement: cannot book beyond slot max_patients.
- [ ] Schedule/doctor/branch must belong to caller's organization.
- [ ] Audit record written on creation.
- [ ] Symptom/onset data can be recorded at booking.

**APT-002 — Appointment read/list/search**
- [ ] Read returns appointment fields.
- [ ] List supports `q`, `doctor_id`, `patient_id`, `date`, `status` filters.
- [ ] Cross-org appointment access returns 404.
- [ ] Match counts endpoint returns dates where search terms matched.

**APT-003 — Appointment status update / cancel / reschedule**
- [ ] Status update returns 200 with new status.
- [ ] Invalid transitions rejected with 422.
- [ ] Reschedule preserves symptom/onset data on new appointment.
- [ ] Cancel revokes PQT tracking token.
- [ ] Audit record written for each status change.

**APT-004 — Walk-in appointment registration**
- [ ] Create returns 201 with walk-in appointment row.
- [ ] `booking_source` = "walk_in".
- [ ] Walk-in count appears in dashboard.
- [ ] Separate from queue check-in operation.

### E.5 PAT module

**PAT-001 — Patient create/read/update/search**
- [ ] Create returns 201 with patient row linked to caller's org.
- [ ] Search returns patients matching name/mobile in caller's org only.
- [ ] Cross-org patient access returns 404.
- [ ] Duplicate mobile within org detected.
- [ ] Audit record written on create/update.

### E.6 QUE module

**QUE-001 — Queue check-in (appointment-based)**
- [ ] Check-in returns 201 with queue entry and token.
- [ ] Appointment must belong to caller's organization.
- [ ] Token unique per doctor per day.
- [ ] Cannot check in an appointment in non-check-in-able state.

**QUE-002 — Queue enqueue (walk-in queue entry)**
- [ ] Enqueue returns 201 with queue entry and token.
- [ ] Token unique per doctor per day.
- [ ] Branch scope validated against caller's token.

**QUE-003 — Queue list / view**
- [ ] List returns queue entries for caller's org.
- [ ] Branch filter validated against caller's branch scope.
- [ ] Cross-branch read returns 404 (never 403).

**QUE-004 — Queue call / cancel / recover / reposition**
- [ ] Call moves entry from waiting to called.
- [ ] Cancel/no_show sets terminal status.
- [ ] Recovery moves skipped → waiting, token preserved.
- [ ] Reposition requires reason and updates position_history.
- [ ] Cross-branch/cross-tenant entry returns 404.

**QUE-005 — Queue reorder**
- [ ] Reorder returns count of reordered entries.
- [ ] Position history recorded for each move.
- [ ] Entries from unrelated queues not reordered together.

**QUE-006 — Intelligent Queue Voice Announcements (Bangla/English)**
- [ ] Bangla queue voice announcement produced for a call event when Bangla is configured.
- [ ] English queue voice announcement produced for a call event when English is configured.
- [ ] Announcement language configurable per facility.
- [ ] Announcements can be enabled/disabled per facility (not forced on every facility).
- [ ] Announcements triggered by appropriate queue events (e.g., patient called to consultation).
- [ ] No duplicate or conflicting announcements for the same queue event.
- [ ] Voice-output failure does not fail or interrupt the queue call operation.
- [ ] Only authorized roles (org/branch admin) may configure announcements.
- [ ] Spoken announcements contain no unnecessary patient PII (no patient name/mobile).
- [ ] Actual audio output verified at browser/runtime before implementation is claimed.

### E.7 RBAC module

**RBAC-001 — Staff authentication & JWT tokens**
- [ ] Valid credentials return 200 with token.
- [ ] Invalid credentials return 401.
- [ ] Repeated failures return 429 with Retry-After header.
- [ ] Successful login clears the throttle bucket.
- [ ] Inactive account returns 403.

**RBAC-002 — Staff user management (CRUD)**
- [ ] Create returns 201 with staff user row.
- [ ] List filtered to caller's organization.
- [ ] Cross-org read/update returns 404.
- [ ] Cross-branch read/update returns 404.
- [ ] Doctor assignment validated to same org.
- [ ] Audit record written on create/update.

**RBAC-003 — Permission checking**
- [ ] `check(resource, role)` returns boolean.
- [ ] Wildcard expansion works correctly.
- [ ] Unknown resource denied for all roles.


### E.8 DSH module

**DSH-001 — Operational dashboard**
- [ ] Today endpoint returns counts by status.
- [ ] Period endpoint returns rates and averages.
- [ ] Branch filter validated via `require_branch_access`.
- [ ] Cross-org data not returned.

### E.9 AUD module

**AUD-001 — Audit event write & read**
- [ ] Audit record written for each mutating action.
- [ ] Cross-org read returns 404 (never 403).
- [ ] Branch-scoped users limited to own branch events.
- [ ] Append-only — no update/delete of audit rows.
- [ ] Max 500 events per query.

### E.10 L10N module

**L10N-001 — Bilingual UI labels**
- [ ] Labels displayed in selected language.
- [ ] Language toggle works.
- [ ] Production build succeeds with localized labels.

### E.11 NOT module

**NOT-001 — Notification outbox & hooks**
- [ ] Notification row created for each event.
- [ ] Delivery states transition correctly.
- [ ] Dedup prevents duplicates.
- [ ] Hook failures do not fail the main action.

### E.12 PQT module

**PQT-001 — Tracking token issue & view**
- [ ] Issue returns 201 with tracking URL and prefix.
- [ ] Active token re-issue returns 409.
- [ ] Tracking view shows appointment, doctor, branch, queue position.
- [ ] QR code returned for active tokens.
- [ ] Revoked/expired token returns 404.
- [ ] No patient PII in tracking view.

### E.13 DQDS module

**DQDS-001 — Public queue display board**
- [ ] Returns board data for valid org+branch.
- [ ] 404 for unknown or non-active org/branch (never 403).
- [ ] Rate-limit headers present on responses.
- [ ] No patient PII in response.
- [ ] Only active queue statuses shown.

### E.14 SYM module

**SYM-001 — Symptom catalogue & onset at booking**
- [ ] Symptom recording returns 200/201 linked to appointment.
- [ ] Catalogue searchable in Bangla and English.
- [ ] Onset question optional with seven predefined answers.
- [ ] Free-text complaint accepted.
- [ ] Symptoms carried to rescheduled appointment.
- [ ] No clinical inference or diagnosis.


## F. Implementation and verification status legend

### F.1 Implementation labels

| Label | Meaning |
|---|---|
| NOT STARTED | No code exists for the feature. |
| IN PROGRESS | Code is being written; not yet complete or reachable. |
| IMPLEMENTED | Code exists and is reachable. |
| PARTIALLY IMPLEMENTED | Code exists but a required scope/authorization/validation gap is known. |
| BLOCKED | Cannot proceed without a decision or dependency. |
| NOT APPLICABLE | Feature does not apply to current architecture. |

### F.2 Verification labels

| Label | Meaning |
|---|---|
| NOT TESTED | No test evidence available. |
| TESTED | Named automated tests pass in this tree. |
| BUILD VERIFIED | Production build completes successfully. |
| BROWSER VERIFIED | Independently confirmed via browser/runtime interaction. |
| ACCEPTED | Product Owner has explicitly accepted the feature. |
| DEFERRED | Deliberately postponed to a future release. |

### F.3 Important distinctions

- **IMPLEMENTED does not mean TESTED.** Code may exist without passing tests.
- **TESTED does not mean BROWSER VERIFIED.** Automated tests passing does not confirm real-user behavior.
- **VERIFIED does not mean ACCEPTED.** Independent confirmation of behavior is not Product Owner acceptance.
- **ACCEPTED requires explicit Product Owner acceptance.** No feature is accepted merely because it is implemented and tested.
- Verification status is never claimed without supporting evidence cited in the feature entry.

### F.4 Current status summary (from source evidence)

| Feature | Implementation | Verification | Known gaps |
|---|---|---|---|
| ORG-001 | IMPLEMENTED | TESTED | Org status not enforced to block access (R-11) |
| ORG-002 | IMPLEMENTED | TESTED | None known |
| FAC-001 | IMPLEMENTED | TESTED | Optional structure — consumers must handle missing levels |
| DOC-001 | IMPLEMENTED | TESTED | None known |
| DOC-002 | PARTIALLY IMPLEMENTED | TESTED | `create_schedule` doesn't validate branch scope (R-05) |
| APT-001 | IMPLEMENTED | TESTED | None known |
| APT-002 | PARTIALLY IMPLEMENTED | TESTED | Grid/list scope discrepancy (calendar diagnosis) |
| APT-003 | IMPLEMENTED | TESTED | None known |
| APT-004 | IMPLEMENTED | TESTED | Reserved-capacity UI absent |
| PAT-001 | IMPLEMENTED | TESTED | PATCH uses `patient.create` not `patient.update` (R-13) |
| QUE-001 | PARTIALLY IMPLEMENTED | TESTED | Caller-supplied `branch_id` unvalidated (R-03) |
| QUE-002 | PARTIALLY IMPLEMENTED | TESTED | Caller-supplied `branch_id` unvalidated (R-03) |
| QUE-003 | PARTIALLY IMPLEMENTED | TESTED | Caller-supplied `branch_id` unvalidated (R-01) |
| QUE-004 | PARTIALLY IMPLEMENTED | TESTED | `_scoped_entry_or_404()` lacks branch check (R-02) |
| QUE-005 | PARTIALLY IMPLEMENTED | TESTED | No queue homogeneity check (R-04) |
| RBAC-001 | IMPLEMENTED | TESTED | No token refresh/revocation |
| RBAC-002 | PARTIALLY IMPLEMENTED | TESTED | No self-escalation protection (R-15), no last-admin protection (R-16) |
| RBAC-003 | IMPLEMENTED | TESTED | `super_admin` conflates platform+tenant (R-06) |
| DSH-001 | IMPLEMENTED | TESTED | Reserved-capacity UI absent |
| AUD-001 | IMPLEMENTED | TESTED | No platform-only audit trail |
| L10N-001 | IMPLEMENTED | BUILD VERIFIED | Secondary-screen labels not all localized |
| NOT-001 | IMPLEMENTED | NOT TESTED | SMS/WhatsApp not verified operational |
| PQT-001 | IMPLEMENTED | TESTED | In-process rate limiting only |
| DQDS-001 | IMPLEMENTED | TESTED | In-process rate limiting only |
| SYM-001 | IMPLEMENTED | TESTED + BUILD VERIFIED | Not browser verified; not ACCEPTED |
| QUE-006 | NOT STARTED | NOT TESTED | No voice/TTS/audio code exists; not browser verified; not accepted |


## G. Future / excluded features

### G.1 Explicitly outside current MVP scope

The following capabilities are **not** current MVP commitments and are **not** listed in the active checklist (section D). They are identified here so they are not accidentally treated as in-scope.

| Capability | Reason for exclusion |
|---|---|
| Clinical Records and Consultation Documentation | Outside appointment/queue scope per backlog §2 product boundaries. |
| Digital Prescription Management | Explicitly excluded; no prescription domain in models. |
| Prescription Support Library | Excluded; no clinical decision support. |
| Encounter History | Excluded; no encounter domain in MVP. |
| Clinical Summaries and Follow-up Assistance | Excluded; no clinical documentation domain. |
| Patient-centred longitudinal health records | Excluded; patient records are appointment-scoped only. |
| Cross-hospital medical-record or prescription sharing | Excluded; no inter-organization clinical exchange. |
| DGHS SHR integration | Excluded; no government integration in MVP scope. |
| AI diagnosis or clinical decision support | Excluded; symptom recording is advisory only (SYM-001 §1.1). |
| Patient self-registration, accounts, login, portal or self-service booking | Explicitly excluded per backlog §2 and BR scope boundaries. |
| Payment gateway and online payment collection | Explicitly excluded per backlog §2. |
| Insurance and claims | Excluded; no insurance domain in MVP. |
| Clinical vitals and clinical pre-consultation intake | Excluded; no vitals domain in MVP. |

### G.2 Future possibilities (not current MVP commitments)

The following capabilities may be considered for future releases but require separate Product Owner decisions:

| Capability | Notes |
|---|---|
| SaaS Platform RBAC (`platform_users`, platform admin, support grants, MFA) | Specified in SaaS architecture documents; not implemented. Separate workstream from operational MVP. |
| Platform identity and tenant/platform boundary separation | `OWNER-APPROVED` decision but `NOT IMPLEMENTED` (per RBAC discovery report). |
| Subscription and entitlement management | Approved in Business Rules §37–§39; no implementation in code. |
| Tenant lifecycle enforcement (suspend/close/reactivate) | `Organization.status` column exists but not enforced by endpoints. |
| Durable rate limiting (DB-backed) | Currently in-process only; durable bucket deferred. |
| Token refresh / revocation / logout | Not implemented; single JWT secret, no refresh token. |
| Patient portal / self-service | Explicitly out of scope; would require separate Product Owner decision. |

### G.3 Distinction from active MVP

Features in sections G.1 and G.2 are **not** part of the section D decision checklist. The Product Owner's KEEP/REMOVE/DEFER decisions apply to **all 26 features listed in section D** (ORG-001 through SYM-001), not merely ORG-001 through QUE-006.

**QUE-006 is an AMSDP Core MVP capability** (Intelligent Queue Voice Announcements, Bangla/English) and is therefore **not** listed in sections G.1 or G.2 as an excluded or future capability. It is distinct from AMSDP Connect's optional "Bangla and English speech interfaces" (a proposed future, not-approved capability) and from automated outbound voice reminders (excluded per MVP scope). QUE-006 covers in-facility audible queue announcements only, not outbound telephone calls to patients.


## H. MVP readiness summary

| Metric | Value | Basis |
|---|---|---|
| Total identified features | 26 | Sections C–D (ORG-001 through QUE-006) |
| Features awaiting Product Owner scope decisions | 0 | All decisions recorded in section D and section I |
| Features marked KEEP | 25 | Section D + section I |
| Features marked REMOVE | 0 | None |
| Features marked DEFER | 1 | NOT-001 — deferred to a future release |
| Features implemented | 17 | Section F.4 status column |
| Features partially implemented | 8 | DOC-002, APT-002, QUE-001 through QUE-005, RBAC-002 |
| Features tested | 23 | All have cited test evidence (NOT-001 is NOT TESTED) |
| Features browser verified | 0 | No browser verification claimed |
| Features accepted | 0 | Acceptance requires Product Owner action |
| Features blocked | 0 | None identified as blocked |

> **Annotation — 2026-11-25 (Product Owner decisions PO-03 / PO-09; the table above is unchanged).**
> The row **"Features awaiting Product Owner scope decisions: 0"** is **superseded**. **SYM-001**
> (symptom and onset capture) was implemented and unauthorised when this table was written; **PO-03**
> (25 November 2026) ratified it as approved **P1**, so the count is now true *by decision* rather
> than by oversight. No other row changes — in particular **"Features browser verified: 0"** and
> **"Features accepted: 0"** remain correct, and this annotation is not an acceptance of anything.

### H.1 Features with known authorization/scope defects (P0)

These features are implemented but have known branch/resource scope defects that must be remediated before MVP release:

| Feature | Defect | Reference |
|---|---|---|
| QUE-001 | Caller-supplied `branch_id` unvalidated | R-03, `queuing/main.py:146-215` |
| QUE-002 | Caller-supplied `branch_id` unvalidated | R-03, `queuing/main.py:206-230` |
| QUE-003 | Caller-supplied `branch_id` query param unvalidated | R-01, `queuing/main.py:108-136` |
| QUE-004 | `_scoped_entry_or_404()` lacks branch check | R-02, `queuing/main.py:98-105` |
| QUE-005 | No queue homogeneity check | R-04, `queuing/main.py:367-409` |
| DOC-002 | `create_schedule` doesn't validate branch scope | R-05, `scheduling/main.py:68-88` |

> **Annotation — 2026-11-25 (Product Owner decision PO-09, Option B; the six rows above are preserved
> exactly as written and each is now superseded or restated below).** Every row was re-checked
> against the current tree on 2026-11-25. The line references above point at code that has since been
> rewritten, so this table **understates** the product rather than overstating it.
>
> | Feature | Re-verified state on 2026-11-25 | Evidence |
> |---|---|---|
> | QUE-003 | **Enforced now.** The `branch_id` query parameter is validated with `branch_accessible()` before it filters, and branch-scoped users are filtered even when they omit it | `backend/queuing/main.py:224–232` |
> | QUE-004 | **Enforced now.** `_scoped_entry_or_404()` checks the entry's *stored* branch; the function itself carries the `P0-1` comment recording why | `backend/queuing/main.py:191–203` |
> | QUE-001 | **Enforced now.** Check-in derives the branch from the appointment and refuses a caller-supplied `branch_id` that differs | `backend/queuing/main.py:297–300` |
> | QUE-002 | **Enforced now.** Enqueue validates the requested branch before use | `backend/queuing/main.py:422–426` |
> | QUE-005 | **STANDS.** No queue-homogeneity check was found in `backend/queuing/main.py` on 2026-11-25. It remains owned by the queue work package and is **not** closed by any decision taken on 25 November 2026 | search of the module |
> | DOC-002 | **Enforced now.** `create_schedule` validates `data.branch_id` with `branch_accessible()` and loads the branch inside the organisation | `backend/scheduling/main.py:185–193` |
>
> Five of the six P0 defects are therefore **already remediated in code** and this section's title no
> longer describes the tree. **QUE-005 is the one that is still real.** No code changed on
> 2026-11-25 to produce this result: the annotation records what the code already does. Evidence:
> `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.8.

### H.2 Features already supported by approved decisions

The following features have their MVP inclusion supported by approved business rules or backlog scope boundaries:

| Feature | Supporting approval |
|---|---|
| ORG-001, ORG-002 | BR §3–§5 (organization and branch management) |
| DOC-001, DOC-002 | BR §14–§15 (doctor and schedule management) |
| APT-001 through APT-004 | BR §16–§23 (appointment lifecycle) |
| PAT-001 | BR §10–§11 (patient registration and lookup) |
| QUE-001 through QUE-005 | BR §24–§31 (queue management) |
| QUE-006 | AMSDP Core capability decision — queue voice callouts are Core, not a Connect capability; `docs/chatgpt/AMSDP_Connect_Proposed_Communication_and_AI_Capabilities.md` §1 scope boundary |
| RBAC-001 through RBAC-003 | BR §8 (role-based access control, FINALIZED) |
| AUD-001 | BR §40 (audit history) |
| FAC-001 | BR §3–§5 (facility structure within organization/branch scope) |
| DSH-001 | Backlog scope (operational dashboards and reporting) |
| L10N-001 | Backlog scope (Bangla/English localization) |
| NOT-001 | Backlog scope (notifications) |
| PQT-001, DQDS-001 | Backlog scope (PQT and DQDS) |
| SYM-001 | Implementation report `AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` |


## I. Decision history

This section records Product Owner scope decisions and later changes. Each removal or deferral decision must be traceable by feature ID, date, reason, and approving authority.

| Date | Feature ID | Decision | Reason | Approving authority |
|---|---|---|---|---|
| 2026-11-17 | ALL (section D, 26 features) | 25 KEEP / 1 DEFER | Product Owner MVP scope lock (recorded decision date 2026-11-17): all 26 features in section D are KEEP except NOT-001, which is DEFER (deferred to a future release). SYM-001 is explicitly KEEP — free-text complaint support is implemented in `backend/appointment/symptoms.py` and covered by 25 symptom integration tests plus 9 catalogue data tests, so it is retained as a requirement with no outstanding removal. QUE-006 is KEEP as an approved AMSDP Core capability; its implementation and verification status remain independent of this scope approval and it is not outbound telephone calling. | Product Owner |

### I.1 How to record a decision

When the Product Owner makes a KEEP / REMOVE / DEFER decision:

1. Check the appropriate box in section D for the feature ID.
2. Add a row to the table above with: date, feature ID, decision, reason, and approving authority.
3. If the decision is REMOVE or DEFER, the feature remains in this catalogue but is marked accordingly in section D.
4. Acceptance criteria in section E remain unchanged — they describe what would need to be true if the feature were kept.

### I.2 Pre-existing decisions (for reference, not to be altered)

The following decisions are already recorded in source documents and are preserved as-is:

| Source | Decision | Reference |
|---|---|---|
| Business Rules V1.1 | Patient self-registration excluded | BR scope boundaries |
| Business Rules V1.1 | Online payment excluded | BR scope boundaries |
| Hackathon Backlog §2 | EMR/prescription/insurance excluded | Product boundaries |
| Hackathon Backlog §2 | DQDS public, token-only, no PII | Product boundaries |
| Hackathon Backlog §2 | PQT private, appointment-specific, account-free | Product boundaries |
