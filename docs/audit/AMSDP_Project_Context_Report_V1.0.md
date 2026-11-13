# AMSDP — Project Context Report V1.0

> **Task ID:** `AMSDP-PROJECT-CONTEXT-REPORT-2026-11-12`
> **Date of investigation:** 2026-11-12 (Asia/Dhaka) · **HEAD at time of reading:** `hackathon-mvp` @ `485d141`
> **Prepared by:** Cline (read-only repository inspection)
> **Purpose:** Give an external collaborator (ChatGPT) an evidence-based, self-contained picture of
> what AMSDP is, what exists in the repository today, what is proven, what is only claimed, and where
> the documents and the tree disagree — so that product and architecture advice can be given without
> access to this machine.
> **Status:** investigation record. **Nothing was modified except this file's creation** and its
> registration in `docs/governance/AMSDP_Docs_Index_V1.0.md`. No code was changed, nothing was
> staged, committed or pushed, and no server, container or test suite was run during this task.
> **Location rule applied:** `.clinerules` §11 — subject folder `docs/audit/` (existing folder holding
> inventory, readiness and acceptance evidence). Filename follows `AMSDP_<Topic>_<Version>.md`.
> **Companion document (not replaced by this one):** `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md`
> — the *product/governance* handover written for the same collaborator on 2026-11-12 13:22. That
> document carries decisions and intentions; **this** document carries the repository facts and the
> evidence grade for each claim. Where they differ, §9 of this report says which one the tree supports.

---

## 0. How to read this document

### 0.1 Status vocabulary (used for every capability row)

| Label | Meaning (`.clinerules` §7 evidence standard) |
|---|---|
| **VERIFIED** | A second, independent artefact confirms it: a live API call, a database read, a browser run, recorded in a dated report. |
| **TESTED** | Named automated tests exist for it **in this tree** and were reported passing. I did not re-run them in this task. |
| **IMPLEMENTED** | Code exists and is reachable from a route/component. Reachability was checked statically in this task; runtime behaviour was not exercised. |
| **DEFERRED** | Deliberately not done, with a recorded reason. |
| **BLOCKED** | Cannot be completed without a decision or an external account the project does not have. |
| **ABSENT** | Nothing in the tree does it. |
| **OUT OF SCOPE** | Product owner has explicitly excluded it from AMSDP's product direction (not a missing feature). |
| **ACCEPTED** | Product owner has signed it off. **Only a human can grant this.** |

A green test suite does not make anything VERIFIED, and a document does not prove an implementation.

### 0.2 Evidence-citation convention

`path:line` means I opened that file in this session and read that line. `commit` means a git object I
resolved in this session. `(reported)` means the claim comes from an existing dated report and was
**not** re-executed here — it is project history, not fresh proof. Nothing in this report is quoted
from memory of a previous session.

### 0.3 The one caveat that matters most

**The stack was not running during this investigation.** All runtime-state claims below are therefore
either (a) fresh static evidence from the tree, or (b) `(reported)` from a dated report. Any claim of
the form "the API returns X" is history; only a fresh `docker compose up` plus a repeat of the probes
makes it live again. This is a known, recorded weakness of the project, not of this report
(see §7.1 P1-5 and §8.4).

---

## 1. What AMSDP is (product context)

**AMSDP** = *Amader Shastho Seba Digital Platform* (working name used throughout the codebase).
Public positioning, as approved and repeatedly recorded:

> **Less Waiting. Less Crowding. Better Healthcare Experiences.**

### 1.1 The problem it addresses

A small private clinic in Bangladesh typically runs its outpatient flow on paper: a receptionist
writes a patient's name and mobile number in a register, the patient physically queues outside a
doctor's room, and nobody — patient or staff — knows how long the wait is. AMSDP makes that flow
digital **without** asking the patient to own a smartphone app or an account.

### 1.2 The actors the system models

| Actor | Kind | Where it lives |
|---|---|---|
| `super_admin` | platform operator (cross-organization by design) | `staff_users.role` |
| `org_admin` | owns one organization (clinic chain) | `staff_users.role` |
| `branch_admin` | owns one branch of an organization | `staff_users.role` |
| `receptionist` | front desk: registration, booking, check-in, queue operations | `staff_users.role` |
| `doctor` | consultation; may run the queue for their own day | `staff_users` + `doctors` link |
| **patient (unidentified)** | **no account, no login, no portal** — reached only through a display screen and a private token URL | anonymous |

The patient never authenticates. That design decision drives most of the security shape of the
product (§5.6, §5.7, §6.3) and is a standing scope boundary (§2.3).

### 1.3 The two halves of the product

| Half | Today | What it means |
|---|---|---|
| **Practice Operations** | **built (MVP)** | Registration, scheduling, appointments, queue, display, tracking, audit, dashboards, org/branch admin. |
| **Clinical Management / Digital Prescription / Intelligent Clinical Documentation** | **PLANNED** (Master Feature List V2.5) | Encounters, notes, prescriptions, doctor-approved AI documentation. Optional and organization-scoped. |

The hackathon deliverable is the first half. The second half is specified, not built (§2.2).

---

## 2. Scope authority: which document decides what

### 2.1 The chain of authority (as it exists in the tree)

| Rank | Document | What it authoritatively decides |
|---|---|---|
| 1 | `docs/product/AMSDP_Business_Rules_V1.0.md` (**owner-controlled, read-only**) | Business behaviour: tenancy, roles, queue lifecycle, notification policy, audit obligations |
| 2 | `docs/product/AMSDP_MVP_SCOPE_V1.0.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` (**owner-controlled**) | What the MVP is and is not |
| 3 | `docs/AMSDP_Master_Feature_List_V2.5_…md` | The **approved, active** feature set; it declares itself the successor to V2.0–V2.4 |
| 4 | `docs/architecture/AMSDP_System_Architecture_V1.0.md` (**owner-controlled**) | Intended service boundaries and data ownership |
| 5 | `docs/governance/AMSDP_Docs_Index_V1.0.md` | Which documents exist and when to read them |
| 6 | Reports under `docs/implementation/`, `docs/audit/`, `docs/security/`, `docs/demo/` | What was built, tested and observed — **history**, not authority over behaviour |

Six Master Feature List drafts coexist (`V2.0_Draft`, `V2.1`, `V2.2`, `V2.3`, `V2.4`, `V2.5`). Only
**V2.5** is current; the rest are retained for traceability. A reader who opens V2.0 by mistake will
conclude that payment, billing and a patient portal are in scope — they are not (§2.3).

### 2.2 What V2.5 actually specifies (planned modules)

| Module | Content | Status |
|---|---|---|
| **A. Practice Operations** | The MVP: booking, check-in, queue, recovery, DQDS, PQT, RBAC, audit, reporting | **Built** (§5) |
| **B. Clinical Management** | Organization-scoped encounters, clinical notes, structured templates, vitals, practice-specific configuration | **PLANNED — nothing in the tree** |
| **C. Digital Prescription** | Medicine catalogue + search, doctor favourites, instruction library, templates, manual prescription, dosage/frequency/duration, preview/print, history, **explicit doctor approval** | **PLANNED — nothing in the tree** |
| **D. Intelligent Clinical Documentation** | Doctor-only post-consultation voice dictation, AI structuring into note sections, medicine matching, ambiguity warnings, draft review, explicit approval, secure persistence | **PLANNED — nothing in the tree** |

Two rules from V2.5 are load-bearing and easy to get wrong in planning:

1. **A feature listed in V2.5 is not automatically authorised for implementation.** V2.5 is the
   *catalogue*, not the *queue*.
2. **B/C/D must never become prerequisites:** a clinic that wants only Practice Operations must be
   able to run without Clinical Management or prescription.

### 2.3 Explicitly **out of scope** — not deferred (owner clarification, 2026-11-12)

These are **not** missing features and must not appear as roadmap gaps. Reproduced from the handover
`docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md` §4.2 (owner statement, 2026-11-12):

| Excluded | Classification |
|---|---|
| Payment gateway integration; bKash / Nagad / Rocket / Bangla QR; advance or partial payment | OUT OF SCOPE |
| Billing and revenue-cycle management | OUT OF SCOPE |
| Insurance and claims management | OUT OF SCOPE |
| Patient portal, patient accounts, self-service booking, secure-messaging inbox | OUT OF SCOPE |
| External hospital / EHR integrations | OUT OF SCOPE |

**Patient-facing queue visibility is still in scope** even though the patient portal is not: that is
exactly the DQDS/PQT pair (§5.6, §5.7).

### 2.4 Approved operational decisions a collaborator must respect

| Decision | Date / ID | Substance | Verified in code? |
|---|---|---|---|
| **Missed-turn recovery** | MVP decision | Staff-confirmed recovery moves an unavailable patient to the **end of the same queue**; authorised staff may **reposition** to a valid position with a **mandatory reason**; original appointment/token identity preserved; no cancel/recreate; no cross-doctor/branch/date/room movement; no automatic detection; AMSDP does **not** triage | **Yes** — `backend/queuing/recovery.py` (§5.4) |
| **Doctor + receptionist queue authority** | `AMSDP-PRODUCT-DECISION-DOCTOR-RECEPTIONIST-QUEUE-RECOVERY-2026-11-10` — **supersedes the earlier doctor-only decision** | Both `doctor` and `receptionist` hold `queue.recover` and `queue.reposition` | **Yes** — permissions seeded and asserted in tests (§5.4) |
| **Patient notification value ("PQV")** | `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` | WhatsApp + SMS are approved P0 scope, independently configurable per organization; **provider integration is explicitly not assumed implemented**; N1 = confirmation at booking, N2 = pre-visit reminder (default 10 min, admin-configurable 5/10); queue-aware dedup/cooldown; cancel pending reminders on cancel/reschedule/consult-start/check-in; booking must work when messaging is unavailable; never claim delivery without provider confirmation | **Partly** — plumbing only; no real provider, no worker service in compose (§5.8, §7.1 P1-3) |
| **BanglaNameSense** | MVP feature, 2026-11-10 | Bangla patient-name spelling suggestion; **assistive only**, never a filter; gender metadata never read or exposed | **Yes** — 43 frontend tests (§5.10) |

The first two decisions close a finding that an earlier audit raised (an *unapproved* doctor
queue-recovery grant). A reader who finds that older finding should treat it as **resolved by owner
decision on 2026-11-10**, not as an open defect.

---

## 3. Architecture as built — and how it differs from the architecture document

### 3.1 Runtime topology (verified in the tree)

One Docker Compose stack: PostgreSQL + eight FastAPI services + one Next.js app.

| Service | Dir | Port (internal) | Public prefix(es) | Responsibility |
|---|---|---|---|---|
| `identity` | `backend/identity/` | 8000 | `/api/v1/staff` | Login, JWT issue, staff users, login throttling |
| `organization` | `backend/organization/` | 8001 | `/api/v1/orgs`, `/api/v1/branches`, `/api/v1/me`, `/api/v1/orgs/{org_id}/notification-config` | Organizations, branches, caller branch context, notification config |
| `patient` | `backend/patient/` | 8002 | `/api/v1/patients` | Registration, search, duplicate detection, age/DOB |
| `doctor` | `backend/doctor/` | 8003 | `/api/v1/doctors` | Doctor master data, doctor↔branch links |
| `scheduling` | `backend/scheduling/` | 8004 | `/api/v1/schedules` | Weekly availability, slot generation |
| `appointment` | `backend/appointment/` | 8005 | `/api/v1/appointments`, `/api/v1/dashboard`, `/api/v1/track` | Booking, walk-in, lifecycle, reschedule, dashboards, audit search, PQT |
| `queuing` | `backend/queuing/` | 8006 | `/api/v1/queue` incl. `/api/v1/queue/display` | Tokens, call/consult/complete, no-show, reorder, recovery, reposition, public display |
| `audit` | `backend/audit/` | 8007 | `/api/v1/audit` | Read-only audit-trail access |
| `frontend` | `frontend/` | 3000 → published **3100** | `/` | The whole UI plus reverse-proxy rewrites to every service |
| `db` | — | 5432 → published **5433** | — | PostgreSQL, one database (`amsdp`; demo overlay uses `amsdp_demo`) |

Prefixes were read from the routers themselves, e.g. `backend/queuing/display.py:24`
`APIRouter(prefix="/api/v1/queue/display")`, `backend/queuing/recovery.py:36` `prefix="/api/v1/queue"`,
`backend/appointment/tracking.py:17` `prefix="/api/v1"`, `backend/appointment/dashboard.py:12`
`prefix="/api/v1/dashboard"`, `backend/organization/notification_config.py:35` `prefix="/api/v1/orgs/{org_id}"`.

### 3.2 The shared library every service imports

`backend/common/` (14 modules) is the real architectural centre of gravity:

| Module | Role |
|---|---|
| `models.py` (451 lines, **14 tables**) | The **entire** schema for **all eight services** in one file |
| `database.py` | Engine/session factory; `AMSDP_DATABASE_URL` |
| `auth.py` | JWT verification, `AuthContext`, org/branch scope resolved from the token |
| `permissions.py` | Role → permission matrix, `require_permission(...)` dependency |
| `audit.py` | Append-only audit writer used by services |
| `config.py`, `health.py`, `timeutil.py` | Settings, `/health` + `/ready`, facility-day/timezone maths |
| `log_redaction.py` | Log redaction of sensitive values |
| `login_throttle.py` | Durable login limiter (`login_attempts` table) |
| `queue_tokens.py`, `tracking_tokens.py` | Token generation/hashing (queue + PQT) |
| `notifications/` | `outbox.py`, `providers.py`, `worker.py`, `config.py`, `hooks.py` |

**Consequence for any collaborator:** these are *not* independent microservices. They are eight
processes sharing one code library, one ORM model set and one database. That is a legitimate MVP
choice — but it changes what "add a service" or "change a model" means, and it contradicts §3.4.

### 3.3 Database and migrations

- **One** Alembic chain at `backend/alembic/versions/` — the only `versions/` directory in the project
  (verified with `find`; the other two hits are inside `.venv313`). No per-service migration trees exist.
- **Nine** revision modules forming a **single linear chain** with one head:
  `5f3fce6757cf` (initial) → `ccf34da72c1b` (queue sequences) → `c7d3601e2486` (audit branch) →
  `9d8a1f2b3c4d` (staff↔doctor link) → `3c8e5d0a9b2f` (patient age) → `a1f2b3c4d5e6` (tracking tokens) →
  `b7c1e4d90a52` (notifications) → `d4b2c8e1f7a3` (login attempts) → `e6c1a9b3d5f8` (drop redundant index)
  = **head**. Verified by reading every `revision`/`down_revision` pair in this session.
- Reported live state: `alembic_version = e6c1a9b3d5f8` and `alembic check` clean (no model drift)
  — `reported`, `docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` §6.6.

### 3.4 Architecture reality check — document vs tree

| ID | `AMSDP_System_Architecture_V1.0.md` implies… | The tree actually contains… | Consequence |
|---|---|---|---|
| **AR-1** | A catalogue of bounded, independently owned services | Eight FastAPI apps sharing `common/models.py`, `common/auth.py`, `common/audit.py` and **one** database | Service count is real; *ownership boundaries* are not. A model change is platform-wide. |
| **AR-2** | Per-service data ownership and schema evolution | One `backend/alembic/versions` chain, nine revisions, for all services | Every schema edit is one forward migration touching several services' tables |
| **AR-3** | Notification delivery as a platform capability | `notifications` table + `common/notifications/*`, mock-capable providers, a **worker module that is not a compose service** | The system cannot notify a patient in deployment (§7.1 P1-3) |
| **AR-4** | AI Factory as tooling, not runtime | `ai_factory/` is a separate CrewAI subsystem; `grep` finds **no** `ai_factory` reference under `backend/` | AI Factory is development-time only and, per handover §2, **frozen** |
| **AR-5** | Multiple frontends / direct service-to-service calls | **One** Next.js app; `frontend/pages/api/` exists but is **empty** (0 Next API routes); all data flows through 12 `next.config.js` rewrites | Client routing is a maintained prefix list; a missing rewrite silently breaks a page (§6.3 F-1) |
| **AR-6** | — | Authorization enforced **server-side** in every service via `common/auth.py` + `common/permissions.py`; principal org/branch comes from the token, never the request body; cross-tenant/branch access fails **closed with 404** | Matches `.clinerules` §3. Tested by `backend/tests/test_security.py` (25 test functions). |

**How to advise on this honestly:** treat AMSDP as a *modular monolith deployed as eight processes*.
Recommendations that assume independent deployability, independent schemas or a message bus do not
match the tree. AR-1/AR-2 are a **documentation defect**, not (yet) a code defect. Note that the
owner-controlled `AMSDP_System_Architecture_V1.0.md` currently carries uncommitted edits (§9.3) that
add the PQV notification decision — they do **not** address this boundary question.

---

## 4. Data model

All 14 tables are declared in `backend/common/models.py` (451 lines), each tagged with the
`__service__` attribute that names the *nominal* owning service. That attribute is documentation; the
database has no per-service separation (§3.4 AR-1/AR-2).

| # | Table | `__service__` | Key columns / notes |
|---|---|---|---|
| 1 | `organizations` | organization | `code` UNIQUE; `timezone` (default `Asia/Dhaka`), `locale`, `facility_type`, JSON `config`, `status` |
| 2 | `branches` | organization | `organization_id` FK; **`UNIQUE(organization_id, code)`** `uq_branch_org_code`; JSON `config` |
| 3 | `staff_users` | identity | `organization_id` FK, nullable `branch_id`, nullable `doctor_id`; `username` UNIQUE; `password_hash`; `role`; `status` |
| 4 | `login_attempts` | identity | login-throttle buckets; indexes `idx_login_attempts_key(client_ip, username, attempted_at)` and `idx_login_attempts_time(attempted_at)` |
| 5 | `doctors` | doctor | `organization_id` FK; `mobile`, `speciality`, `qualification`, `registration_number`, `consultation_fee`; `idx_doctor_org` |
| 6 | `doctor_branches` | doctor | `UNIQUE(doctor_id, branch_id)` `uq_doctor_branch` — doctor↔branch assignment |
| 7 | `patients` | patient | `organization_id` FK; `name`, `mobile`, `date_of_birth`, **`age`** (reported age, used only when DOB absent), `sex`, `address`, `national_id`, `status`, `merged_into`, `merge_reason`; `idx_patient_org`, `idx_patient_org_mobile` |
| 8 | `schedules` | scheduling | `doctor_id`, `organization_id`, `branch_id` FKs; `appointment_model` (`time_slot`), `effective_from/to`, JSON `slot_templates` |
| 9 | `appointments` | appointment | `organization_id`, `branch_id`, `patient_id`, `doctor_id`; `appointment_date`, `start_time`, `serial_number`, `appointment_type`, `booking_source`, **`status`** (`BOOKED`…), JSON `status_history`, `token_number`, `created_by`, `rescheduled_from/to` + `reschedule_reason`; `idx_appt_doctor_date`, `idx_appt_patient` |
| 10 | `queue_entries` | queuing | `organization_id`, `branch_id`, `doctor_id`, **`date`**, `position`, `token`, `patient_id`, `appointment_id`, `entry_source`, `status`, JSON `status_history` and `position_history`, `added_by` |
| 11 | `queue_sequences` | queuing | **Composite PK `(doctor_id, date)`**, `last_value` — the concurrency-safe daily token/position counter, incremented by an atomic PostgreSQL UPSERT |
| 12 | `tracking_tokens` | appointment | `appointment_id` UNIQUE; `token_hash` **UNIQUE** (`sha256(raw + pepper)`), `token_prefix`; `status` (`active`/revoked), `revoked_at`. Pepper is an env var (`AMSDP_TRACKING_PEPPER`) and is **never stored** |
| 13 | `audit_events` | audit | `service`, `organization_id`, nullable `branch_id`, `action`, `target_type`, `target_id`, **`actor_id` NOT NULL**, `actor_role`, JSON `before`/`after`, `reason`, `timestamp` |
| 14 | `notifications` | notifications | Persistent outbox: `organization_id`, nullable `branch_id`/`appointment_id`/`patient_id`, `notification_type` (`appointment_confirmation`/`pre_visit_reminder`), `channel` (`whatsapp`/`sms`), `recipient_mobile`, JSON `payload`, **`dedup_key` UNIQUE**, `status`, `attempt_count`/`max_attempts`, `scheduled_at`/`next_attempt_at`, `provider` (default `mock`), `provider_message_id`, `error`, `cancel_reason`; `idx_notif_org_status`, `idx_notif_due`, `idx_notif_appointment` |

### 4.1 Three properties a collaborator must not get wrong

1. **The tenant key is `organization_id`** — present on every business table, and never duplicated by a
   second tenant column (`.clinerules` §3). `branch_id` is a *scope within* the tenant, not a second
   tenant key.
2. **Deletes are soft.** `status` columns plus `patients.merged_into` mean patient identity is merged,
   never destroyed. `notifications` rows are moved to `cancelled`, never deleted — the outbox is a
   record of what was scheduled.
3. **Audit rows are append-only and require an actor.** `audit_events.actor_id` is `NOT NULL`, and no
   writer endpoint exists: audit is written by service code only and read through `GET /api/v1/audit`
   and `GET /api/v1/dashboard/audit` (`reported` + `backend/audit/tests/test_audit.py`, 13 tests,
   including one asserting a client cannot write an audit event).

### 4.2 Concurrency mechanism, stated precisely

Daily token allocation uses `queue_sequences` keyed on **`(doctor_id, date)`** with an atomic
UPSERT, so two simultaneous bookings for the same doctor and day cannot receive the same token.
There is **no** branch-wide or global "one active token" constraint: tokens are per doctor per day,
which is what the clinic flow requires (two doctors in one branch run two parallel queues).

An earlier consolidated report describes this as "one active token per branch under contention
(constraint + `ON CONFLICT`)". That phrasing is imprecise — see register entry **C-4** (§9.2). The
mechanism itself is present and is the reason the invariant holds.

---

## 5. Feature matrix — what exists, at what evidence grade

Test counts below are **test functions counted statically in this session** from the 17 files under
`backend/**/tests/` (286 functions total; the project has consistently *reported* **289 passing**,
because parametrised cases expand). I did **not** run the suite in this task.

### 5.1 Identity and access

| Capability | Status | Evidence |
|---|---|---|
| Staff login, JWT issue, `/api/v1/staff/login` | **TESTED** | `backend/identity/tests/test_identity.py` (17); `frontend/pages/index.js:18` posts to it |
| Password hashing + seeded staff accounts | **IMPLEMENTED** | `staff_users.password_hash`; `backend/seed/seed_demo.py` refreshes hashes from `.env` on re-seed (Revision 8 of the docs index) |
| Durable login throttling (429 + `Retry-After`) | **TESTED** | `common/login_throttle.py`, `login_attempts` table; `test_security.py` |
| Role → permission matrix, deny-by-default | **TESTED** | `common/permissions.py`, `require_permission(...)`; `test_security.py` (25) |
| Tenant/branch scope derived from the token, never the body | **TESTED** | `common/auth.py`; `test_security.py`; cross-tenant reads return **404** |
| Both `doctor` and `receptionist` hold `queue.recover` / `queue.reposition` | **TESTED** | owner decision of 2026-11-10 (§2.4); asserted in `tests/test_sequence3.py` |
| `super_admin` may read/create across organizations | **IMPLEMENTED, UNAPPROVED IN WRITING** | `test_super_cross_org_read` / `test_super_cross_org_create` exist; no document approves the scope → §7.2 P2-1 |
| Denials/refusals written to the audit trail | **ABSENT** | 403/404/422 leave no `audit_events` row → §7.1 P1-1, a `.clinerules` §3 breach |

### 5.2 Organizations, branches, staff administration

| Capability | Status | Evidence |
|---|---|---|
| Organization CRUD + branch CRUD | **TESTED** | `backend/organization/tests/test_organization.py` (20) |
| Caller's own branch context (`/api/v1/me`) | **IMPLEMENTED** | proxied rewrite `next.config.js:12` |
| Staff user management (`/api/v1/staff/users`) | **IMPLEMENTED** | `frontend/pages/staff.js:1` fetches it; list/read-oriented UI |
| Per-organization notification configuration (provider + reminder lead) | **TESTED** | `backend/organization/notification_config.py:60,78`; read restricted to `org_admin`, negative case asserted |

### 5.3 Patients

| Capability | Status | Evidence |
|---|---|---|
| Registration, search by name/mobile, pagination | **TESTED** | `backend/patient/tests/test_patient.py` (16) |
| Duplicate detection on mobile (warns, does not block) | **TESTED** | `test_patient.py`; UI surfaces `duplicates` (`frontend/pages/patients.js:25,35`) |
| Age model: DOB is authoritative, reported age is the fallback | **TESTED** | `tests/test_patient_age.py` (13); `patients.age`, `patients.date_of_birth` |
| Patient merge (soft, `merged_into` + reason) | **IMPLEMENTED** | `common/models.py:203-204` |
| **A working registration form in the UI** | **IMPLEMENTED** | `frontend/pages/patients.js:20-27` (POST `/api/v1/patients`), modal at `:40-49`; BanglaNameSense on the name field at `:42` |

> **Correction of public record:** `docs/demo/AMSDP_Limitations_Report_V1.0.md` states there is no
> patient registration form. That is **false in this tree** — see §9.2 C-1. The report is dated
> 2026-11-05 and was never refreshed.

### 5.4 Doctors and scheduling

| Capability | Status | Evidence |
|---|---|---|
| Doctor master data, doctor↔branch assignment | **TESTED** | `backend/doctor/tests/test_doctor.py` (14); `doctor_branches` UNIQUE |
| Weekly availability / slot templates | **TESTED** | `backend/scheduling/tests/test_scheduling.py` (22) |
| Slot generation honouring facility-day/timezone | **TESTED** | `common/timeutil.py`; `scheduling` tests |
| Doctor and schedule admin screens | **IMPLEMENTED** | `frontend/pages/doctors.js` (46 lines), `schedules.js` (46); read + create for schedules |

### 5.5 Appointments and queue

| Capability | Status | Evidence |
|---|---|---|
| Book / reschedule / cancel appointment, status history | **TESTED** | `backend/appointment/tests/test_appointment.py` (13) + `test_reschedule.py` (6) |
| Daily serial + queue token generation under contention | **TESTED** | `queue_sequences` UPSERT; `backend/queuing/tests/test_queue.py` (20); `test_sequence3.py` (26) |
| Queue: add walk-in, call next, start/complete visit, position history | **TESTED** | `queue_entries`; `test_queue.py` |
| **Recovery** — rebuild a doctor-day queue from appointment truth | **TESTED** | `POST /api/v1/queue/recover`; `test_sequence3.py` (Sequence 3, S3-A/B/C) |
| **Reposition** — reorder waiting entries, every move audited | **TESTED** | `POST /api/v1/queue/reposition`; owner decision A-2 (`position_history` append-only) |
| Queue UI (reception + doctor console) | **IMPLEMENTED** | `frontend/pages/queue.js`, `dashboard.js` |

### 5.6 DQDS — public doctor queue display

| Capability | Status | Evidence |
|---|---|---|
| Public, unauthenticated, org+branch-scoped display | **TESTED** | `backend/tests/test_dqds.py` (24) |
| Privacy: token + doctor name only — no patient name/mobile/ID | **TESTED** | `test_dqds.py` asserts the exclusion |
| Polling refresh in the browser | **IMPLEMENTED** | `frontend/pages/queue-display/[org]/[branch].js` (198 lines, 10 s poll) via the `/api/v1/queue/:path*` rewrite |

### 5.7 PQT — patient queue tracking

| Capability | Status | Evidence |
|---|---|---|
| Token issued per eligible appointment, raw value never stored | **TESTED** | `tests/test_tracking_tokens.py` (17); `tracking_tokens.token_hash` |
| Public tracking page by token (`/track/[token]`) | **IMPLEMENTED, FRAGILE** | `frontend/pages/track/[token].js`; **no rewrite for `/api/v1/track/*`** → §6.3 F-1 |
| Revoked/expired/unknown token → 404, indistinguishable | **TESTED** | model docstring + `test_tracking_tokens.py` |
| Pepper rotation and `AMSDP_TRACKING_PEPPER` handling | **IMPLEMENTED** | env-only; absent pepper must fail closed (documented in demo runbook) |

### 5.8 Notifications (WhatsApp / SMS outbox)

| Capability | Status | Evidence |
|---|---|---|
| Outbox row created on appointment events with `dedup_key` uniqueness | **TESTED** | `test_sequence4.py` (13); `notifications.dedup_key` UNIQUE |
| Retry/backoff state machine, `pending→processing→sent→delivered` | **TESTED** | `common/notifications/*`; mock adapter never sets `delivered` |
| Cancellation on appointment cancel/reschedule (moved to `cancelled`) | **TESTED** | PQV §D, `test_sequence4.py` |
| Provider abstraction with mock adapter | **IMPLEMENTED** | `provider` column defaults to `mock` |
| **Delivery worker running in deployment** | **ABSENT** | worker module exists but is **not** a compose service → §7.1 P1-3 |

### 5.9 Dashboard and audit

| Capability | Status | Evidence |
|---|---|---|
| Role-scoped metrics endpoint | **TESTED** | `backend/tests/test_dashboard.py` (6) |
| Audit read API (`/api/v1/audit`, `/api/v1/dashboard/audit`) | **TESTED** | `backend/audit/tests/test_audit.py` (13) |
| Audit writers are services only (no client write path) | **TESTED** | asserted in `test_audit.py` |
| Executive dashboard UI incl. audit view | **IMPLEMENTED** | `frontend/pages/dashboard.js` (52 lines) |

### 5.10 BanglaNameSense (Bangla name transliteration)

| Capability | Status | Evidence |
|---|---|---|
| Bangla → Latin transliteration for patient/doctor name entry | **TESTED** | Reported as **43 frontend tests** (index Revision 8 records 289 backend / 43 frontend); used at `patients.js:42` |
| Deterministic, no network/model dependency | **IMPLEMENTED** | pure module — safe under the 4 GB VRAM constraint |

This is the only "AI-flavoured" component in the shipped product path; it is a rule-based
transliterator, not an LLM call. Nothing in the running stack requires a model server.

### 5.11 Platform surface

| Capability | Status | Evidence |
|---|---|---|
| 8 FastAPI services + 1 Next.js frontend under Docker Compose | **IMPLEMENTED** | `docker-compose.yml`; ports per §3.1 |
| Compose healthchecks gating start order | **IMPLEMENTED** | `docker-compose.yml` healthcheck blocks |
| Seed script for demo data (idempotent, refreshes hashes) | **IMPLEMENTED** | `backend/seed/seed_demo.py` |
| Forward-only idempotent Alembic migrations, single head | **IMPLEMENTED** | §3.3 |
| CI pipeline (lint, tests, migration check) | **ABSENT** | no `.github/workflows`; risk P1-4 |
| Frontend automated tests | **ABSENT** | no test runner configured under `frontend/` |
| Load / concurrency test executed and recorded | **ABSENT** | contention is covered by unit-level tests only |

### 5.12 Declared in product documents, not built in this tree

`OUT OF SCOPE` for the hackathon MVP, and a collaborator must not design around them:
prescription/EMR write-path, clinical documentation, billing/invoicing, insurance, lab/radiology
integration, patient self-service registration, real WhatsApp/SMS credentials, multi-language UI
beyond the bn/en toggle, and the AI clinical-assistant features from the Master Feature List.

### 5.13 Roll-up

| Status | Count of capabilities listed above |
|---|---|
| **TESTED** | 26 |
| **IMPLEMENTED** (code present, no automated proof of the end-to-end path) | 16 |
| **ABSENT** | 5 (denial auditing, delivery worker at runtime, CI, frontend tests, load test) |
| **OUT OF SCOPE / declared-not-built** | the §5.12 list |

**Reading of the roll-up:** the *server-side* product is genuinely tested at unit level and the
invariants that matter (tenant isolation, token concurrency, audit immutability, DQDS privacy) have
dedicated tests. The gap is not code volume — it is **deployment wiring** (worker, CI, frontend
tests) and **process evidence** (nothing in this report is `VERIFIED` by a live run, §8.4).

---

## 6. Frontend surface and a real defect in it

One Next.js app (Pages Router). 14 routes + `_app.js`, ~1,540 lines of page/component/lib code total.

### 6.1 Route inventory

| Route | File (lines) | Auth | Data source |
|---|---|---|---|
| `/login` (`/`) | `pages/index.js` (48) | public | `/api/v1/staff/login` |
| `/dashboard` | `dashboard.js` (52) | staff | `/api/v1/dashboard/*`, audit search |
| `/patients` | `patients.js` (50) | staff | `/api/v1/patients` |
| `/appointments` | `appointments.js` (94) | staff | `/api/v1/appointments/*` |
| `/queue` | `queue.js` (262) | staff | `/api/v1/queue/*` (largest page: call-next, reposition, recover) |
| `/doctors` | `doctors.js` (46) | staff | `/api/v1/doctors` |
| `/schedules` | `schedules.js` (46) | staff | `/api/v1/schedules` |
| `/staff` | `staff.js` (38) | staff | `/api/v1/staff/users` |
| `/audit` | `audit.js` (68) | staff | `/api/v1/audit` |
| `/orgs` | `orgs.js` (35) | org_admin | `/api/v1/orgs` |
| `/branches` | `branches.js` (37) | org_admin | `/api/v1/branches` |
| `/notifications` | `notifications.js` (204) | org_admin | `…/orgs/{id}/notifications` (+ `/status`) |
| `/track/[token]` | `track/[token].js` (75) | **public** | **`/api/v1/track/<token>` → not routed — see F-1** |
| `/queue-display/[org]/[branch]` | `queue-display/[org]/[branch].js` (198) | **public** | `/api/v1/queue/display/…` (10 s poll) |

Shared: `components/AppShell.js` (120), `components/BanglaNameSense.js`, `components/ui/{Alert,ConfirmDialog,DataTable,Modal,StatusBadge}.js`, `lib/auth.js` (66, token storage + `apiFetch`), `lib/i18n.js` (102, bn/en dictionaries), `lib/bangla-name-sense/`.

### 6.2 The single integration seam: `next.config.js` rewrites

There are **no Next API routes** — `frontend/pages/api/` exists and is **empty** (verified with `find`).
Every browser call therefore depends on one of the **12** rewrite entries in `next.config.js`. That is
a deliberate, simple design, but it means the rewrite list *is* the routing table: a path that is not
listed is not proxied, and Next answers 404 from its own router.

### 6.3 F-1 (P1): the PQT tracking page cannot work in a deployed stack

- `next.config.js:26` rewrites **`/track/:path*`** → `http://appointment:8005/api/v1/track/:path*`.
- `frontend/pages/track/[token].js:29,32` fetches **`/api/v1/track/<token>`**.
- No rewrite exists for `/api/v1/track/*`, and `pages/api/` is empty, so the browser request is
  answered by Next itself → **404** → the page renders its error state (`err: 'Failed to load info'`).

The backend side is correct: `backend/appointment/main.py:73` sets no-cache headers for both
`/api/v1/track/` and `/track/`, and `appointment/tracking.py` implements the route. The defect is one
missing (or mis-keyed) rewrite line in the frontend. `next build` cannot catch it — rewrites are
runtime behaviour, which is exactly why the "9/9 static pages built" evidence did not surface it.

**Suggested fix (one line, not applied in this audit):** add
`{ source: '/api/v1/track/:path*', destination: 'http://appointment:8005/api/v1/track/:path*' }`
or change the two `fetch` calls to `/track/<token>`.

### 6.4 F-2 (P3): empty `pages/api/` is a latent trap

The directory exists but contains nothing. A future contributor will reasonably assume Next API routes
are the pattern here and add one, silently diverging from the rewrite-proxy convention. Either delete
the empty directory or add a one-line `README` stating the convention.

### 6.5 What the UI evidence actually is

Frontend verification on record is **build-level** (`next build` exit 0, 9/9 static pages), plus the
UI/UX assessment (`docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md`: 10 shared
components, 8 login-guard blocks). There are **no frontend automated tests** and this audit ran no
browser. So no frontend capability in §5 is above `IMPLEMENTED`, and F-1 is proof that build success
is not behavioural evidence.

---

## 7. Risk register

Severity: **P1** = blocks a claim the project makes about itself; **P2** = material but contained;
**P3** = hygiene. Every row names the evidence I saw in this tree.

### 7.1 P1

| ID | Risk | Evidence in this tree |
|---|---|---|
| **P1-1** | **Denials are not audited.** A refused request (403 wrong role, 404 cross-tenant, 422 invalid) leaves no `audit_events` row. `.clinerules` §3 requires "Denials are recorded (audited), never silently swallowed". | `common/auth.py` imports no audit module; the permission dependency raises `HTTPException` directly; `require_permission` in `common/auth.py` (~line 174) does the same. Only *successful* mutations call `record_audit`. |
| **P1-2** | **PQT page cannot load in a deployed stack** (defect F-1). The feature is called a headline MVP capability, but its only UI path 404s at the Next layer. | `next.config.js:26` vs `pages/track/[token].js:29,32` — §6.3 |
| **P1-3** | **No notification is ever delivered at runtime.** The outbox is written and tested, but nothing in `docker-compose.yml` runs `common/notifications/worker.py`. WhatsApp/SMS "supported" therefore means "queued, never sent". | `docker-compose.yml` service list (§3.1) has no worker; `common/notifications/worker.py` exists |
| **P1-4** | **No CI gate** (carried R-5). Every green number in the project, including the 289, is a *local* run. F-1 is the demonstration: a broken rewrite survived a green build and a green suite. | No `.github/workflows` in the tree |
| **P1-5** | **Runtime state unverified by this audit.** The stack was not running; no endpoint was called, nothing was read from a live database. | §8.4 |

### 7.2 P2

| ID | Risk | Evidence |
|---|---|---|
| **P2-1** | `super_admin` holds the wildcard `"*"` and has cross-organization read/create tests, but **no approved document grants that scope**. This is a written-policy gap around the strongest role in the system. | `common/permissions.py:8`; `tests/test_security.py::test_super_cross_org_*` |
| **P2-2** | M2 security report is **untracked** (carried R-1) — the security review is not part of repository history, so an external reader cannot verify the auth claims from the repo alone. | closeout report R-1 (§ "Open items") |
| **P2-3** | Four **demo-seed** passwords remain printed in the owner-controlled credential sheet (carried R-2). Fine for a private hackathon repo; must be rotated or the sheet dropped before any public mirror. | `docs/demo/AMSDP_Demo_Credentials_V1.0.md` — see R-2 wording in the closeout report |
| **P2-4** | Working tree still dirty: `frontend/pages/patients.js`, `frontend/styles/global.css` plus uncommitted owner-document edits (carried R-3, extended by §9.3). | `git status` (§8) |
| **P2-5** | Reference data and DQDS/PQT paths are documented inconsistently (`/api/v1/display/…` in one report vs `/api/v1/queue/display/…` in code). A collaborator coding to the doc builds the wrong URL. | `docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` vs `backend/queuing/display.py` |

### 7.3 P3

| ID | Risk |
|---|---|
| **P3-1** | Empty `frontend/pages/api/` invites a second, conflicting integration pattern (§6.4 F-2) |
| **P3-2** | Doc claims that are imprecise rather than wrong — "one active token per branch" (§4.2, C-4), "no patient registration form" (C-1) |
| **P3-3** | No frontend test runner; UI regressions can only be found by hand |
| **P3-4** | No recorded load/concurrency **executed** test; the contention guarantee rests on unit tests plus the DB's atomic UPSERT |

### 7.4 The honest one-sentence risk summary

The system's *invariants* are better tested than its *wiring*: tenant isolation, token uniqueness, audit
immutability and DQDS privacy each have dedicated tests, while the three things that decide whether a
demo actually works end-to-end — the PQT rewrite, the notification worker, and CI — are the three that
are missing.

---

## 8. Verification, evidence index, and repository state

### 8.1 What this audit actually did

| Activity | Done? | Notes |
|---|---|---|
| Read backend service trees, `common/`, routers and route prefixes | ✅ | static |
| Read all of `common/models.py` (451 lines) and the 9 Alembic revisions' `revision`/`down_revision` pairs | ✅ | static |
| Read `common/auth.py`, `common/permissions.py`, `common/audit.py` call sites | ✅ | static |
| Read all 14 frontend routes, `components/`, `lib/`, `next.config.js`, `docker-compose.yml` | ✅ | static |
| Count test functions across the 17 test modules | ✅ | static count |
| `git status`, `git log -1`, `git rev-list --count main..HEAD` | ✅ | §8.5 |
| Run `pytest`, `next build`, `alembic check`, `docker compose up` | ❌ | **not run** — §8.3 |
| Call a live endpoint / read a live database | ❌ | stack was down |

### 8.2 Test inventory (functions counted statically, this session)

| Module | Functions | Module | Functions |
|---|---|---|---|
| `identity/tests/test_identity.py` | 17 | `tests/test_security.py` | 25 |
| `organization/tests/test_organization.py` | 20 | `tests/test_dqds.py` | 24 |
| `patient/tests/test_patient.py` | 16 | `tests/test_sequence3.py` | 26 |
| `doctor/tests/test_doctor.py` | 14 | `tests/test_sequence4.py` | 13 |
| `scheduling/tests/test_scheduling.py` | 22 | `tests/test_e2e.py` | 21 |
| `appointment/tests/test_appointment.py` | 13 | `tests/test_tracking_tokens.py` | 17 |
| `appointment/tests/test_reschedule.py` | 6 | `tests/test_patient_age.py` | 13 |
| `queuing/tests/test_queue.py` | 20 | `tests/test_dashboard.py` | 6 |
| `audit/tests/test_audit.py` | 13 | **Total** | **286 functions / 17 modules** |

The project's own figure of **289 passing** is consistent with 286 functions once parametrisation
expands cases. Treat 289 as `(reported)`: it was produced by local runs recorded in earlier reports,
not by this audit.

### 8.3 What was deliberately not run

`.clinerules` §9 restricts this agent to writing code rather than executing suites unless asked, and
the task was an audit. So: no `pytest`, no `next build`, no `alembic check`, no container start, no
HTTP probe. **Consequence —** every "TESTED" row in §5 means *named tests exist in this tree*, not
*I watched them pass today*. Any capability a collaborator intends to rely on should be re-verified
with one command first:

```
cd backend && python -m pytest tests appointment/tests audit/tests doctor/tests \
  identity/tests organization/tests patient/tests queuing/tests scheduling/tests -q
```

then `docker compose up -d` and a single probe of `/health` on each of the 8 services (raw port,
**not** through the frontend, because of F-1).

### 8.4 The evidence-grade ceiling of this report

Nothing here is `VERIFIED`, and nothing can be until a dated report records a live run. The ceiling is
`TESTED` (server-side, reported) and `IMPLEMENTED` (frontend, static). This is stated once here so the
collaborator does not have to infer it from the tables.

### 8.5 Repository state (measured, 2026-11-12)

- Branch **`hackathon-mvp`**, HEAD **`485d141`** `docs(audit): record MVP commit and push execution`,
  **8 commits ahead of `main`**.
- Modified (tracked): `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` ⚠ owner-controlled,
  `docs/architecture/AMSDP_System_Architecture_V1.0.md` ⚠ owner-controlled,
  `frontend/pages/patients.js`, `frontend/styles/global.css`.
- Untracked: `_tools/` (7 helper scripts), `docker-compose.demo.yml`,
  `docs/security/AMSDP_M2_Security_Implementation_Report.md` (the R-1 open item — present on disk,
  deliberately out of history), `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md`, and this report.
- Nothing is staged. No commit, push, reset, stash or checkout was performed by this audit.

---

## 9. Where the documents and the tree disagree

### 9.1 Conflicts

| ID | Document says | The tree says | Which is right |
|---|---|---|---|
| **C-1** | `docs/demo/AMSDP_Limitations_Report_V1.0.md`: there is no patient registration form | `frontend/pages/patients.js` has a working registration modal that POSTs `/api/v1/patients`, with BanglaNameSense on the name field | **The tree.** The limitations report is stale (2026-11-05) and must not be quoted as current |
| **C-2** | `AMSDP_System_Architecture_V1.0.md`: bounded services with per-service data ownership and schema evolution | One shared `common/models.py` and one Alembic chain for all 8 services | **The tree.** AR-1/AR-2: a documentation defect, not a code defect (§3.4) |
| **C-3** | `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md` lists PQT as a delivered MVP capability | Its only UI path 404s at the Next rewrite layer (F-1); the API itself is fine | **The API is real, the page is broken.** Report the capability as "API tested, UI defective" |
| **C-4** | `AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md`: "one active token per branch (DB constraint + `ON CONFLICT`)" | Uniqueness is a per-`(doctor_id, date)` UPSERT in `queue_sequences`; no branch-level constraint exists | **The tree.** The invariant holds for a different, narrower key |
| **C-5** | Reports cite `GET /api/v1/display/{org}/{branch}` | `backend/queuing/display.py` serves it under the queue router; the page calls `/api/v1/queue/display/…` | **The tree** — code the collaborator to `/api/v1/queue/display/…` |
| **C-6** | "289 tests passing" | 286 test functions in 17 modules (parametrisation can explain the difference) | **Reconcilable**; both are `(reported)` until re-run |

### 9.2 Not conflicts, but do not mis-read them

- **"9/9 static pages built"** is a *build* fact. It says nothing about routing (F-1) or behaviour.
- **"MVP scope frozen / V1.0 owner-approved"** refers to the *business-rule* documents, not to the
  feature list drafts, which are still being revised (§9.3).
- **The AI Factory / AILI documents** under `ai_factory/docs/` describe a subsystem that is not part of
  the runtime (§3.4 AR-4). They are not evidence about AMSDP's product surface.

### 9.3 Uncommitted owner-controlled document edits (read-only, flagged not changed)

The working tree carries **uncommitted** changes to two documents the Product Owner controls. They were
not modified by this audit; they are reported because a collaborator reading `HEAD` would see different
text from what is on this machine:

| File | Diff size | What the uncommitted text adds |
|---|---|---|
| `docs/AMSDP_Master_Feature_List_V2.0_Draft.md` | +118 / −11 | PQV positioning statement ("Less Waiting…"), §14.2 resolved by the PQV decision, resolution of open question 9, an "only after adoption" list, a note that SMS+WhatsApp are required not optional, and a new **§25 PQV Decision Addendum (2026-11-08)** |
| `docs/architecture/AMSDP_System_Architecture_V1.0.md` | +63 / −11 | PQV/tracking-token requirements woven into the architecture text |

Implication: the approved *intent* is that WhatsApp **and** SMS are required, organization-configurable
channels, with **manual link sharing as the fallback** when provider integration is unavailable. That
fallback is what keeps P1-3 (no delivery worker) from being a product-level blocker today — the queue
notification still cannot be *sent automatically*, and the demo relies on staff sharing the tracking
link by hand.

---

## 10. Reading list for the external collaborator

Read in this order. "Trust" says what the document is good for; it is not a judgement of quality.

| # | Document | Read it for | Trust |
|---|---|---|---|
| 1 | `docs/product/AMSDP_Business_Rules_V1.0.md` | The authoritative rules: tenant isolation, roles, appointment/queue lifecycle, audit | **Authority.** Owner-approved. If advice conflicts with this, the advice is wrong |
| 2 | `docs/product/AMSDP_MVP_SCOPE_V1.0.md` | What is in and out of the hackathon MVP | **Authority** on scope |
| 3 | `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | The patient-visibility decision (`AMSDP-PRODUCT-DECISION-PQV-2026-11-08`): DQDS + PQT + WhatsApp/SMS | **Authority** on PQV |
| 4 | `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md` | The narrative handover written for you: history, decisions, intentions | High, but it is *intent*; §9.1 corrects several of its claims |
| 5 | `docs/architecture/AMSDP_System_Architecture_V1.0.md` | Intended architecture, service catalogue, security model | **Read with §3.4.** Its ownership model is aspirational (C-2) |
| 6 | **This report** (§3–§9) | What the tree actually contains, with line-level evidence | Facts as of 2026-11-12 |
| 7 | `docs/product/AMSDP_Product_Positioning_V1.0.md` | Wording, audience, value proposition | Authority on messaging |
| 8 | `docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` | The consolidated engineering history (Sequences 1–4): what was built and why | Good history; three imprecise claims (C-4, C-5) |
| 9 | `docs/audit/AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` | Commit/push decisions, open items R-1…R-5, what was excluded from history | High — the most honest document in the set |
| 10 | `docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md` | Route inventory, readiness grading, what M9 would need | Useful; grades are its own, not this report's |
| 11 | `docs/implementation/AMSDP_SEQ_03_COMPLETION_REPORT.md`, `AMSDP_SEQ_02_COMPLETION_REPORT.md`, `AMSDP_M4_Appointment_Implementation_Report.md` | Per-sequence work packages and test evidence | Historical evidence |
| 12 | `docs/governance/AMSDP_Engineering_Governance_Assessment.md` | How the agent rules are adapted for AMSDP (the §3 adaptations) | Authority on process |
| 13 | `docs/governance/AMSDP_Docs_Index_V1.0.md` | The map of the whole document set | Navigation only |
| 14 | `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` | How the demo is meant to be operated | Operational |
| 15 | `docs/demo/AMSDP_Limitations_Report_V1.0.md` | Known demo limitations | **Stale** — at least C-1 is wrong (§9.1) |
| 16 | `docs/security/AMSDP_M2_Security_Implementation_Report.md` | The M2 security review | Present on disk, **untracked** (R-1). Read, do not cite as repository evidence |
| 17 | `docs/deployment/AMSDP_M8_Cloud_Deployment_Architecture.md` | Cloud/deployment intent (assessment only) | Planning, not as-built |
| 18 | `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` | The longer-term product direction (clinical documentation, prescription) | **Vision, not built** (§5.12) |
| 19 | `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` | Detailed UI/UX intent (~320 KB — search it, do not read it whole) | Design intent |

**Do not cite as evidence about the current build:** `ai_factory/docs/*` (a different subsystem),
the `V1.1` root-level drafts where a `V1.0` under `docs/product/` is the approved version, and any
report whose dates precede 2026-11-08.

---

## 11. How to re-verify this report, and what remains open

### 11.1 Re-verification protocol (30 minutes)

1. `docker compose up -d` from the repository root; wait for all healthchecks.
2. `GET http://localhost:8000/health` … `:8007/health` — 8 services, all raw ports.
3. `curl` a login, take the JWT, then call `/api/v1/queue/display/{org}/{branch}` without a token —
   expect 200 and **no** patient identity in the body.
4. Open `http://localhost:3000/track/<32+ char token>` — **this is expected to fail today** (F-1).
   Re-test after the one-line rewrite fix to close P1-2.
5. `psql` (or the compose exec) `select count(*) from notifications; select status, count(*) from notifications group by 1;`
   — if every row stays `pending`, P1-3 is confirmed live.
6. `cd backend && python -m pytest -q` — expect ~289 passed; record the real number.
7. `cd backend && alembic current && alembic check` — expect `e6c1a9b3d5f8` and no drift.

### 11.2 Open questions for the Product Owner (none of them block advice)

| ID | Question | Why it matters |
|---|---|---|
| **Q-1** | Is `super_admin`'s cross-organization read/create **approved**? | P2-1 — it is the widest privilege in the system and is only asserted by tests |
| **Q-2** | Should refusal/denial events be written to the audit trail (`.clinerules` §3 says yes)? | P1-1 — needs a decision because it changes write volume and every 4xx path |
| **Q-3** | Is "no automatic delivery yet, manual link sharing only" an acceptable demo position? | P1-3 vs the PQV fallback in §9.3 |
| **Q-4** | Should the Limitations Report be reissued? | C-1 — it currently misstates a built feature |
| **Q-5** | Will CI be added before the repository is made public? | P1-4 — also gates R-2 (credential rotation) |
| **Q-6** | Are the two uncommitted owner-document edits (§9.3) intended to be committed as-is? | They change what "approved" means for PQV |

---

## 12. Governance and skill compliance (`.clinerules` §6)

### 12.1 Domains identified and governance applied (§2, §4)

| Domain (§4 row) | Governance document applied | How it shaped this report |
|---|---|---|
| Documentation: reading docs, writing reports, placement | §11, §12, `docs/governance/AMSDP_Docs_Index_V1.0.md` | Read the index before acting; wrote to `docs/audit/`; no existing file overwritten; filename follows `AMSDP_<Topic>_<Version>.md` |
| Multi-tenant data, org/branch isolation | Business Rules §4–§6; `backend/common/auth.py` | §4.1 states the tenant key; §5.1 and AR-6 record the 404-fails-closed behaviour |
| Authentication / RBAC | Business Rules §7–§8; `backend/common/permissions.py` | §5.1, P2-1 (wildcard `super_admin`), P1-1 (unaudited denials) |
| Database schema, migrations | Alembic chain; `backend/common/models.py` | §3.3 and §4 verified revision-by-revision and column-by-column |
| Queue / workflow transitions / tokens | Business Rules Parts V–VII; `common/queue_tokens.py`, `common/tracking_tokens.py` | §4.2, §5.5, §5.7 |
| Audit / reporting | `.clinerules` §3; `backend/common/audit.py` | §4.1, §5.9, P1-1 |
| Backend API | Business Rules Parts II–X | §5 route-by-route |
| Frontend UI | `docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md` | §6, including the F-1 defect nobody had caught |
| Docker / deployment | `docker-compose.yml`, M6 constraints | §3.1, P1-3 |
| LLM / AI tooling | §8 routing policy | §3.4 AR-4 (AI Factory is not runtime) |

### 12.2 Skills

- **Installed skill packages: NONE** (`.clinerules` §5 — no `.clinerules/skills/`, `.claude/skills/` or
  repo `skills/` directory exists in this workspace).
- Therefore no skill was used, and none is claimed. The work was governed by the AMSDP documents above,
  applied as adapted by `docs/governance/AMSDP_Engineering_Governance_Assessment.md` §3.

### 12.3 Documents actually opened in this session

`docs/governance/AMSDP_Docs_Index_V1.0.md`; `docs/chatgpt/AMSDP_Project_Handover_2026-11-12.md`;
`docs/audit/AMSDP_Final_PrePush_Decisions_and_Closeout_Report_V1.0.md` (targeted reads and the R-1…R-5
block); `docs/audit/AMSDP_ALL_SEQUENCES_FINAL_SUMMARY.md` and
`docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md` (targeted search hits, not full reads);
`docs/implementation/AMSDP_SEQ_03_*` and `AMSDP_M4_*` (targeted); plus the source files cited throughout.
Product documents (`Business_Rules_V1.0`, `MVP_SCOPE_V1.0`, `Product_Positioning_V1.0`,
`PQV_..._Decision_V1.0`) were **read and cited, never modified** — §11 read-only rule.

### 12.4 Verification performed (real results, not claims)

Executed: filesystem and text inspection; `find` for test modules and migration trees; `grep` for
rewrites, route prefixes and audit call sites; `git status --porcelain`, `git log -1`,
`git rev-list --count main..HEAD`, `git diff --numstat`, `git diff -U0 | grep '^+'`.
Not executed: any test suite, build, migration command, container, or HTTP request (§8.3).
Result: this report is `IMPLEMENTED`/`TESTED`-graded evidence only — no `VERIFIED`, no `ACCEPTED`.

### 12.5 Deviations, exceptions, unresolved issues

| Item | Status |
|---|---|
| Runtime not exercised | **Recorded limitation** (§8.3, P1-5) — not a deviation from instruction |
| `.clinerules` §9 ("do not execute scripts/servers/suites unless asked") | Honoured: read-only shell inspection only |
| Owner-controlled documents | **Not modified.** Two of them carry *pre-existing* uncommitted edits, reported in §9.3, untouched |
| Git safety (§9) | No reset/clean/stash/checkout; nothing staged or committed |
| Unresolved | Q-1…Q-6 (§11.2) — all require an owner decision, none blocks advice |
| Output location | `.clinerules` §11 — `docs/audit/`, closest existing subject folder for an evidence/inventory record; no new folder created |

### 12.6 What this report does *not* establish

It does not establish that the demo runs, that 289 tests pass today, that notifications are delivered,
or that the PQT page works. Each of those is a `VERIFIED`-level claim and needs the §11.1 protocol.

### 12.7 Registration of this document (§12 obligation)

Created and registered in the same task, as `.clinerules` §12 requires:

- `docs/governance/AMSDP_Docs_Index_V1.0.md` — new row in the `audit/` table (60,177-byte file at
  registration time) **and** a new **Revision 10** entry in the header log; the header snapshot count
  moves from 57 to 58 documents (≈2.03 → ≈2.09 MiB).
- `docs/governance/AMSDP_Docs_Inventory_and_Migration_Manifest_V1.0.md` — **no entry added, and none is
  due**: that manifest records *migrations* (moves/renames) of existing documents, and nothing was moved,
  renamed, retired or overwritten in this task. Recording a creation there would misstate its purpose.
- Collision check: `docs/audit/AMSDP_Project_Context_Report_V1.0.md` did not exist before this task
  (confirmed by `git status`, where it appears as untracked rather than modified).

---

## Appendix A — One-page summary

**The product.** A multi-tenant outpatient flow system for small private clinics in Bangladesh:
reception registers and books, staff and doctors run a live queue, a waiting-room screen shows tokens
with no patient identity, and a patient gets a private link that needs no account.
Positioning: *Less Waiting. Less Crowding. Better Healthcare Experiences.*

**The build.** A modular monolith deployed as **8 FastAPI services + 1 Next.js app + PostgreSQL**, all
sharing `backend/common/` (one 451-line `models.py`, 14 tables) and **one** Alembic chain (9 revisions,
single head `e6c1a9b3d5f8`). Tenant key is `organization_id`; branch is a scope inside it; cross-tenant
reads return 404.

**What is solid.** 286 test functions in 17 modules covering the invariants that matter — tenant
isolation, RBAC (25 tests), queue contention and token allocation (26 + 20 + 17), DQDS privacy (24),
audit immutability (13), end-to-end flows (21). Migrations are linear, forward-only and reported clean.

**What is fragile.** The *wiring*, not the logic: **F-1** — the PQT page fetches `/api/v1/track/…`
while `next.config.js` only rewrites `/track/…`, so the page 404s (P1-2); **P1-3** — the notification
worker is not a compose service, so nothing is ever sent; **P1-4** — no CI, so defects like F-1 survive
green runs; **P1-1** — refusals are not audited, contrary to `.clinerules` §3.

**What is not built.** Clinical documentation, prescription, billing, patient self-service, real
WhatsApp/SMS credentials. Do not design around them for the MVP.

**What to trust.** Product authority: `Business_Rules_V1.0`, `MVP_SCOPE_V1.0`, the PQV decision.
Intent: the handover and `System_Architecture_V1.0` (whose service-ownership model the tree does not
implement — C-2). Facts: §3–§8 of this report.

**The one-line judgement.** A well-tested backend core inside a deployment envelope that has three
concrete holes (one rewrite, one worker, one pipeline), none of which is architectural and all of which
are cheap to close.

