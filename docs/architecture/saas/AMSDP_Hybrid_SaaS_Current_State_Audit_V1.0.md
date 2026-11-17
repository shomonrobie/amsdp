# AMSDP — Hybrid SaaS Current-State Audit V1.0

> **Document ID:** `AMSDP_Hybrid_SaaS_Current_State_Audit`
> **Version:** V1.0 · **Date:** 2026-11-17 · **Branch audited:** `hackathon-mvp` @ `133ce83`
> **Status:** audit record — **descriptive, not prescriptive**. It changes no code, schema,
> migration or behaviour, and it authorises no implementation.
> **Part of the set:** `docs/architecture/saas/` (six documents, see §14).
>
> **Correction note (2026-11-17, applied with Revision 2 of the sibling documents).** The
> observations in §2–§13 were measured on `133ce83` and are **kept verbatim** — an audit is a record
> of what was true, not a document to rewrite. What changed *after* the audit is recorded here and in
> the bracketed notes at the affected rows (§1.3 vocabulary, §4.1 principal, §8 C-1/C-7, §9 K-8, §13,
> §14.2):
>
> 1. **The owner decided.** All sixteen `O-SaaS` items and directions A1–A4 were ruled on 2026-11-17
>    (architecture specification §1.5, §14.3), and eight engineering questions `EQ-1…8` were opened
>    (§14.3.1). Every question this audit raised — §14.2 A-1…A-5 — is therefore **decided**; §14.2 is
>    retained as the historical question list with the rulings appended.
> 2. **The status vocabulary is now two-axis** (architecture specification §1.3): a decision axis
>    (`OWNER-APPROVED` / `SPECIFIED` / `OPEN` / `DEFERRED` / `SUPERSEDED`) and an evidence axis
>    (`NOT IMPLEMENTED` / `IMPLEMENTED` / `TESTED` / `VERIFIED`). This audit's grades are the evidence
>    axis and are unaffected: **no decision advanced any evidence grade**, and nothing in §2–§13 was
>    implemented by the decision. `PROPOSED` in this document's §1.3 table means what the set now calls
>    `SPECIFIED`.
> 3. **Nothing in this audit's evidence changed.** The commercial layer, the platform identity domain,
>    revocation and the lifecycle enforcement are still absent from the tree exactly as graded; the
>    rulings authorise work, they do not constitute it.
>
> **Governing documents read:** `docs/AMSDP_Business_Rules_V1.1.md` Part II (§3–§6), Part IX
> (§37–§39, subscription lifecycle), §40 (audit history) and §42 (security),
> `docs/AMSDP_Master_Feature_List_V2.5_…md` §C/§C.1/§D (module catalogue), §5.1 (Super Admin
> dashboard), §19.1–§19.3 (subscription lifecycle), §30.1–§30.4 (module activation and
> entitlements), `docs/architecture/AMSDP_System_Architecture_V1.0.md`,
> `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`,
> `docs/chatgpt/AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md`,
> `docs/audit/AMSDP_Project_Context_Report_V1.0.md`,
> `docs/governance/AMSDP_Docs_Index_V1.0.md`.

---

## 1. Purpose, method and limits

### 1.1 What this document answers

The owner asked for the SaaS dimension of AMSDP to be specified properly. Any specification
that is not grounded in the tree becomes fiction, so this audit answers one question before
any target design is drawn:

> **What does the system actually do today with respect to identity, tenancy, subscription
> and entitlement — and does it meet the requirements that are already approved?**

The answer, in one sentence: **the platform is a working single-tier multi-tenant clinic
application with genuinely enforced tenant isolation, one audited platform *capability*
(`platform.cross_org`) and no separate platform identity domain — and it has no subscription,
entitlement, plan, lifecycle or platform-administration layer at all** — even though the
requirements for those layers are already *approved* in the Business Rules and the V2.5
feature list. Details and evidence follow.

### 1.2 Method

Read-only inspection of the tree. Every claim in §2–§6 is cited to a file and, where useful,
a line range. Where a claim rests on another document rather than on code, the document is
named. Nothing was executed against a running stack; nothing was migrated; no test suite was
run in this task (see §1.4).

### 1.3 Evidence standard applied (`.clinerules` §7)

| Grade | Meaning | Used here for |
|---|---|---|
| **IMPLEMENTED** | Code exists and is reachable from a running entry point | table/column/endpoint existence |
| **TESTED** | A named test in this tree asserts the behaviour | isolation, permissions, denial audit |
| **VERIFIED** | A second, independent artefact confirms it | *not claimed anywhere in this audit* |
| **ACCEPTED** | The project owner has signed it | the owner decisions Q-1…Q-6 |
| **ABSENT** | Grep and schema inspection find nothing | subscription, plan, entitlement, billing, reset, refresh, revocation |
| **PROPOSED** | A design proposal in a sibling document, not approved | everything in the other five documents. **Correction note (2026-11-17):** this grade is what the set now calls `SPECIFIED`; decisions made by the owner carry `OWNER-APPROVED` and are recorded in architecture specification §14.3, not here. This audit grades evidence only |

**This audit contains no VERIFIED claim.** It is a static reading of the tree, not a runtime
observation. A capability is not VERIFIED until a browser run, a live API call or a database
read independently confirms it.

### 1.4 What was *not* done (deliberate exclusions)

- **No test suite was executed.** `.clinerules` §9 forbids running suites unless asked. Test
  counts quoted in §12 are *static counts of `def test_` functions*, exactly as the predecessor
  context report did, and are labelled as such.
- **No live database was inspected.** Column nullability is read from `common/models.py` and
  the migration chain, not from `information_schema`.
- **No code, schema, migration, compose file or frontend file was modified.** The only writes
  in this task are the six documents in `docs/architecture/saas/` plus the index registration
  in `docs/governance/AMSDP_Docs_Index_V1.0.md`.
- **Pre-existing uncommitted work was not touched** (`.clinerules` §9). The tree was already
  dirty before this task began: modified tracked files under `backend/`, `frontend/` and
  `docs/`, plus untracked `_tools/` and three untracked backend files. None of it belongs to
  this task and none of it is reported as this task's work.

---

## 2. Verified runtime state — what exists

### 2.1 Process topology

One Docker Compose stack: PostgreSQL + **eight** FastAPI services + one Next.js app.

| Service | Directory | Public prefix(es) |
|---|---|---|
| identity | `backend/identity/` | `/api/v1/staff` |
| organization | `backend/organization/` | `/api/v1/orgs`, `/api/v1/branches`, `/api/v1/me`, `/api/v1/orgs/{org_id}/notification-config` |
| patient | `backend/patient/` | `/api/v1/patients` |
| doctor | `backend/doctor/` | `/api/v1/doctors` |
| scheduling | `backend/scheduling/` | `/api/v1/schedules`, `/api/v1/sessions` |
| appointment | `backend/appointment/` | `/api/v1/appointments`, `/api/v1/dashboard`, `/api/v1/track`, `/api/v1/symptoms` |
| queuing | `backend/queuing/` | `/api/v1/queue`, incl. public `/api/v1/queue/display` |
| audit | `backend/audit/` | `/api/v1/audit` |
| frontend | `frontend/` | `/` (published on 3100; `next.config.js` rewrites the APIs) |
| db | — | one database, `amsdp` (demo overlay `amsdp_demo`) |

**There is no platform-plane service, no billing service and no worker service in Compose.**
The notification worker exists as code (`backend/common/notifications/worker.py`) and is not a
deployed process — a pre-existing finding inherited from `AMSDP_Project_Context_Report_V1.0.md`
(AR-3), not introduced here.

### 2.2 The shared library is the real architectural centre

`backend/common/` is imported by all eight services. Consequence, stated plainly because it
governs every design decision in the sibling documents: **this is a modular monolith deployed
as eight processes.** Service boundaries are real at the HTTP layer and nominal at the data
layer. `backend/app/main.py` is a stub; there is no aggregate app.

### 2.3 Schema size and migration chain

| Fact | Evidence |
|---|---|
| `backend/common/models.py` declares **22** tables | `grep -n '__tablename__' backend/common/models.py` |
| **One** Alembic chain, linear, single head | `backend/alembic/versions/` — 11 files |
| Current head `f7d2b4c6e8a1` (*add facility hierarchy, doctor profile*), `Revises: e6c1a9b3d5f8` | revision file header |

Chain order: `5f3fce6757cf` (initial) → `ccf34da72c1b` (queue sequences) → `c7d3601e2486`
(audit branch) → `9d8a1f2b3c4d` (staff↔doctor link) → `3c8e5d0a9b2f` (patient age) →
`a1f2b3c4d5e6` (tracking tokens) → `b7c1e4d90a52` (notifications) → `d4b2c8e1f7a3` (login
attempts) → `e6c1a9b3d5f8` (drop redundant index) → `b3d7e91f6a24` (symptom catalogue) →
**`f7d2b4c6e8a1`** (facility hierarchy, doctor profile, chamber sessions) = **head**.

> ⚠ `b3d7e91f6a24` is **untracked** in git at the time of this audit (it appears under `??`
> in `git status`). The chain is linear and the head is unambiguous, but the symptom
> migration has never been committed. Any new migration must be authored **on top of
> `f7d2b4c6e8a1`**, not on top of the last committed revision.

### 2.4 Models carry a nominal service owner; the database does not

Every model declares `__service__ = "<service>"` (`models.py:33`, `:49`, `:198`, `:247`,
`:776`, …). That attribute is documentation only: one database, one schema, one migration
chain. The owner document `AMSDP_System_Architecture_V1.0.md` §8.1 states a
**database-per-service principle**. The tree does not implement it. The contradiction is
reported, not resolved — see **C-1** and ADR-SAAS-002.

---

## 3. Data-model inventory (all 22 tables)

Tenant column means: is `organization_id` present and NOT NULL? That single column is what
makes `require_org_access` enforceable. `org-scoped` below means "the service derives the
tenant from the verified token and filters by it".

| # | Table | `__service__` | Tenant column | Key facts |
|---|---|---|---|---|
| 1 | `organizations` | organization | **is the tenant** | `code` UNIQUE; `facility_type` (default `hospital`); `status` default `active`; `timezone` `Asia/Dhaka`; `locale` `bn`; JSON `config` |
| 2 | `branches` | organization | `organization_id` NOT NULL | `UNIQUE(organization_id, code)` `uq_branch_org_code`; `status` |
| 3 | `facility_floors` | organization | `organization_id` NOT NULL **and** `branch_id` NOT NULL | `UNIQUE(branch_id, code)`; index on org and branch |
| 4 | `facility_departments` | organization | same as floors | `UNIQUE(branch_id, code)` |
| 5 | `facility_rooms` | organization | same; optional `floor_id`, `department_id` | `UNIQUE(branch_id, code)`; `room_type`; the only level a session/appointment points at |
| 6 | `specialties` | organization | `organization_id` NOT NULL | `UNIQUE(organization_id, code)`; bilingual `name_en`/`name_bn` |
| 7 | `staff_users` | identity | `organization_id` NOT NULL **and** `branch_id` NULLABLE | `username` UNIQUE globally; `password_hash`; `role`; `status`; nullable `doctor_id` (link to `doctors`) |
| 8 | `login_attempts` | identity | none (no org column) | per-(IP, username) throttle counters — the only table without a tenant column that stores principal-adjacent data |
| 9 | `doctors` | doctor | `organization_id` NOT NULL | doctor profile, speciality text, chamber/fee fields |
| 10 | `doctor_specialties` | doctor | `organization_id` NOT NULL | join to `specialties` |
| 11 | `doctor_branches` | doctor | `organization_id` NOT NULL | doctor ↔ branch membership |
| 12 | `patients` | patient | `organization_id` NOT NULL | `UNIQUE(organization_id, phone)`-style scoping; DOB/age |
| 13 | `schedules` | scheduling | `organization_id` NOT NULL | recurring template; `branch_id`, `doctor_id` |
| 14 | `schedule_sessions` | scheduling | `organization_id` NOT NULL | concrete dated session; optional `room_id` |
| 15 | `appointments` | appointment | `organization_id` NOT NULL | `branch_id`, `doctor_id`, patient link, status machine |
| 16 | `symptom_catalog` | appointment | `organization_id` NULLABLE | 79 curated bilingual symptoms; global rows are shared across tenants — **the one deliberate cross-tenant catalogue** |
| 17 | `appointment_symptoms` | appointment | `organization_id` NOT NULL | patient-reported symptom rows per appointment |
| 18 | `queue_entries` | queuing | `organization_id` NOT NULL | one queue row per session/appointment |
| 19 | `queue_sequences` | queuing | `organization_id` NOT NULL | monotonic per-org/per-day counters |
| 20 | `tracking_tokens` | appointment | `organization_id` NOT NULL | public status-tracking tokens (hashed); no staff auth |
| 21 | `audit_events` | audit | **`organization_id` NOT NULL + FK** | append-only by convention; `service`, `action`, `target_type`, `target_id`, `actor_id`, `actor_role`, `branch_id`, JSON `before`/`after` |
| 22 | `notifications` | notifications | `organization_id` NOT NULL | outbox rows; worker not deployed |

### 3.1 Why the inventory matters

1. **Tenant coverage is near-complete and that is an asset.** Every business table except
   `login_attempts` carries a tenant column. A SaaS layer can therefore be added *around*
   the existing isolation rather than retrofitted into 21 tables.
2. **`audit_events.organization_id` is NOT NULL with a FK.** This one column is the single
   hardest constraint on platform administration, because a platform-level action may belong
   to *no tenant at all*. The consequence is already visible in shipped code:
   `backend/common/denial_audit.py` documents that a `401` is written to the log stream
   rather than the database for exactly this reason, and `audit/main.py` reads the trail
   per tenant. Any platform-plane audit design must confront this — see ADR-SAAS-009.
3. **`symptom_catalog` proves the precedent for shared reference data.** A nullable
   `organization_id` already means "global, readable by every tenant". Plans and modules can
   follow the same pattern instead of inventing a new one.
4. **`staff_users.branch_id` is nullable.** Branch is an *optional narrowing* of the
   principal, not a required scope; org-wide roles (`org_admin`, `super_admin`) carry NULL.
   The principal model therefore already distinguishes "org-wide" from "branch-narrowed".

---

## 4. Identity and access as built

### 4.1 The principal

A principal is a `staff_users` row. One row = one login = one organization = at most one
branch. There is **no membership table** and therefore **no way for one human to hold roles in
two organizations**. Consequences: a locum doctor working at two clinics needs two usernames,
two passwords and two audit identities; a platform operator who also owns a clinic needs a
tenant account *as well as* a platform identity. Both are recorded as open questions, not
decided here (ADR-SAAS-013, `OPEN`).

> **[Correction 2026-11-17]** This paragraph is kept as written because it describes the tree at
> `133ce83`, which is unchanged. The *question* it raised has since been decided: O-SaaS-7 rejected
> one-organization-per-identity and adopted **multi-membership** (ADR-SAAS-014 supersedes
> ADR-SAAS-013), so the two-usernames consequence above is a statement about today's code, not about
> the target design. Evidence grade unchanged: `staff_users` still carries `organization_id` and no
> membership table exists.

### 4.2 Token mechanics — as built

| Property | Actual behaviour | Evidence |
|---|---|---|
| Algorithm | HS256, shared symmetric secret | `identity/models.py` (`_ALGO`, `_SECRET`) |
| Secret source | `AMSDP_JWT_SECRET` from the environment; a **dev-only fallback constant** is used when `AMSDP_ENV` is unset or `development`, and import **fails** (`RuntimeError`) in any other environment | `identity/models.py:15-23`, `common/auth.py:43-51` |
| Claims | `sub`, `org`, `branch`, `role`, `exp` | `identity/main.py:211-215` |
| TTL | **12 hours, fixed** (`_TOKEN_HOURS = 12`), no refresh | `identity/models.py:25`; `identity/main.py:214` |
| Revocation | **none** — no JTI, no denylist, no session table, no `token_version` | ABSENT (grep: `jti`, `revoke`, `refresh`, `logout`) |
| Logout | Client deletes the token; the server has nothing to invalidate | `frontend/lib/auth.js` |
| Password reset | ABSENT — no endpoint, no table, no mailer path | grep across `backend/identity/` |
| Password policy | Length/complexity unenforced (pre-existing limitation, `R16` in the context report) | `identity/models.py` (`StaffUserCreate`) |
| Login throttle | Per-(IP, username), DB-backed, configurable, success clears the bucket; **no lockout by design** | `identity/main.py:184-217`, `common/login_throttle.py`, `d4b2c8e1f7a3` |
| Account state | `staff_users.status != "active"` → `403` at login and at `/validate` | `identity/main.py:207-208`, `:232` |

**The finding that matters for SaaS:** a 12-hour bearer token that cannot be revoked is
acceptable for a single-tenant demo and unacceptable for a multi-tenant commercial platform,
because offboarding a user (or suspending a tenant) leaves a working credential in the wild
for up to twelve hours. The subscription lifecycle in particular *depends* on revocation:
suspending a tenant must take effect on the next request, not after the token expires.

### 4.3 Permission model

`backend/common/permissions.py` holds a static role → permission-set map. The six roles are
`super_admin`, `org_admin`, `branch_admin`, `receptionist`, `doctor`, `assistant`, plus the
`require_permission(...)` / `require_org_access(...)` / `require_branch_access(...)` dependency
factories that every service uses. It is a **closed, code-defined RBAC** model: no table, no
per-tenant role customisation, no permission inheritance beyond the map.

Two `PLATFORM_CAPABILITIES` exist and are reserved to `super_admin` alone (owner decision Q-1):
`platform.admin` and `platform.cross_org`. `AuthContext.can_cross_org` consults the matrix
rather than the role string, and `require_org_access` / `require_branch_access` therefore
**allow a foreign organization or branch when the caller holds `platform.cross_org`**, writing a
`platform.cross_org.access` row into the *target* tenant's trail
(`common/auth.py:98-106`, `:220-284`; asserted by `backend/tests/test_platform_admin.py`).

So the platform-administration *capability* already exists, and it is audited. What is absent is
a separate platform *identity domain* — see §4.5 and finding **C-9**.

### 4.4 Denial auditing (already implemented — an asset)

`common/denial_audit.py` installs ASGI middleware in every service. Every `403`, `404` and
`422` response is written to `audit_events` after the response is sent; `401` goes to the
`amsdp.denial_audit` log stream because there is no verified tenant to attribute the row to.
This satisfies `.clinerules` §3 ("denials are recorded, never silently swallowed") in the
tenant plane **today**, and it is the model the platform plane must extend — not replace.

### 4.5 Platform identity — the capability exists, the domain does not

There is **no `platform_users` table, no `scope` claim, no platform-only route namespace and no
platform UI**. But the picture is more precise than "absent", and the difference changes the
roadmap:

| Element | Today |
|---|---|
| Platform capability | **PRESENT** — `platform.admin`, `platform.cross_org`, reserved to `super_admin` (Q-1) |
| Cross-org data access | **PRESENT and audited** — `require_org_access` permits it and writes `platform.cross_org.access` into the target tenant's trail |
| Separate principal domain | **ABSENT** — `super_admin` is a `staff_users` row that belongs to one organization |
| Platform token scope | **ABSENT** — every token is `{sub, org, branch, role, exp}` with no plane marker |
| Platform service / endpoints | **ABSENT** — no `backend/platform/`, no `/api/v1/platform/*` |
| Plans, subscriptions, entitlements | **ABSENT** (§6) |

**The consequence is finding C-9.** A `super_admin` holds `patient.*` and `doctor.*`, so
`platform.cross_org` lets that account read another organization's patients and appointments.
The access is audited and non-routine in intent, but V2.5 §5.1 explicitly forbids creating
*"routine cross-tenant access to patient or appointment content"*, and nothing in the code
distinguishes a support action from ordinary browsing. The defect is **scope of the capability,
not its existence**: the platform operator needs tenant *metadata* and *usage*, not clinical
content.

The name is also misleading, which is finding **C-4**: `super_admin` reads as a platform
superuser but is created inside a tenant's staff list by that tenant's own administrator.

> **Correction note (§4.6).** An earlier draft of this section described platform
> administration as `ABSENT` and stated that `super_admin` has no cross-tenant reach. Re-reading
> `common/auth.py` and `common/permissions.py` disproved both. The corrected findings are
> narrower, more actionable, and are what the sibling specifications build on.

### 4.6 Correction note — what was fixed and why

Recorded rather than silently rewritten, because an audit that edits itself without trace is
worthless (`.clinerules` §7, §12).

| # | Earlier claim | Verified reality | Documents affected |
|---|---|---|---|
| 1 | JWT secret hardcoded, not environment-sourced | `AMSDP_JWT_SECRET` is environment-sourced; the fallback is dev-only and guarded by `AMSDP_ENV` | this §4.2; R-10; C-8; architecture spec §9.5, §13 |
| 2 | `super_admin` has no cross-tenant reach | it holds `platform.cross_org`; cross-org access is permitted and audited | this §4.3, §4.5; C-4; new C-9; IAM spec §7 |
| 3 | Roles include `queue_manager` | roles are `super_admin`, `org_admin`, `branch_admin`, `receptionist`, `doctor`, `assistant` | this §4.3; IAM spec §3 |

The residual defects after correction are **R-10** (the guard is keyed on an unset-able-by-default
`AMSDP_ENV`, so an unset variable silently yields a public dev secret) and **C-9** (the scope of
`platform.cross_org`). Both are real and both remain S1/S2.

---

## 5. Tenant and organization as built

### 5.1 Isolation mechanism (the strongest asset in the tree)

1. The principal is decoded from the JWT by `common/auth.get_current_user`, which **re-reads
   the `staff_users` row** and rejects inactive accounts.
2. `org` and `branch` come from the verified token. **No endpoint accepts a tenant id from a
   request body**; where a path carries `{org_id}`, `require_org_access(org_id)` compares it
   to the token's org — and permits a foreign org **only** for a caller holding
   `platform.cross_org`, recording `platform.cross_org.access` in the target tenant's trail
   (§4.3, finding C-9).
3. Cross-tenant or cross-branch probes return **404**, not 403 (non-disclosing), per
   `.clinerules` §3; the refusal is then audited by the denial middleware.
4. Test coverage exists: `backend/tests/test_platform_admin.py` plus per-service suites assert
   404 on foreign-org access.

This behaviour is the single most important thing the SaaS layer must **not** weaken. Any
subscription or entitlement check must be *added beside* this gate and must never become the
only gate — a billing lookup is not an authorisation decision.

### 5.2 Lifecycle state — a column with no teeth

`organizations.status` exists (default `active`) and `PATCH /api/v1/orgs/{org_id}` accepts a
`status` value (`organization/main.py:159-180`). But:

- **Nothing enforces it.** `get_current_user` checks `staff_users.status` only. An
  organization whose status is `suspended` still authenticates, reads and writes. Verified by
  reading: no filter on `Organization.status` exists in `common/auth.py`,
  `common/permissions.py` or any service entry point; the only references are the org
  service's own resolve helper (`organization/main.py:110`) and the queue-display lookup
  (`queuing/display.py:112`), neither of which gates on the value.
- **The only writer is the tenant itself.** `org.manage` is held by `org_admin`, so a tenant
  administrator can set its own organisation's status — including back to `active` after a
  platform-side suspension. This is a **privilege inversion** (finding **R-03**) and must be
  closed before any lifecycle state is trusted.
- **The audit record is wrong.** `organization/main.py:170-178` mutates the row and then
  builds `before` **from the already-mutated object**, so `before` and `after` are identical.
  The change is unauditable in effect (finding **R-04**).

### 5.3 Hierarchy

`organization → branch → floor / department / room` is implemented with per-branch unique
codes and soft retirement (`status="inactive"`), optional at every level. This is the model
the Hybrid SaaS tenancy hierarchy reuses rather than reinvents: **a plan attaches to an
organization, never to a branch.**

### 5.4 Provisioning and onboarding

`POST /api/v1/orgs` creates an organization. There is no self-service signup, no invitation
flow, no e-mail verification, no domain claiming, no trial creation and no seed step beyond
`backend/seed/seed_demo.py`. Provisioning today is **manual, platform-operator-imagined but
tool-unassisted** (finding **R-05**).

---

## 6. Subscription and entitlement — the missing layer

### 6.1 Exhaustive negative evidence

| Searched for | Result |
|---|---|
| `subscription`, `Subscription` in `backend/` (any file, any case) | **no matches** |
| `plan`, `Plan` as a model/table/route | **no matches** (only prose in docs) |
| `entitlement`, `feature_flag`, `module_enabled` | **no matches** |
| `billing`, `invoice`, `payment`, `gateway`, `stripe`, `sslcommerz` | **no matches** |
| `trial`, `grace_period`, `seat`, `quota`, `limit` enforcement | **no matches** |
| Frontend: any plan/subscription/billing page or component | **no matches** (`frontend/pages/`, `frontend/components/`) |
| Migrations: any table resembling the above | **no matches** across all 11 revisions |

**Grade: ABSENT.** Not "partially built", not "stubbed with a TODO" — absent. The SaaS surface
of this product is greenfield inside an otherwise mature application.

### 6.2 But the requirements are already approved

The absence is a build gap, not an open question. Already owner-approved:

| Source | Requirement |
|---|---|
| `AMSDP_Business_Rules_V1.1.md` §37 | Subscription is **organizational**: hospitals/clinics/diagnostic centres subscribe for their workspace; an independent chamber may subscribe as its own facility; a doctor needs no separate subscription to be listed; each tenant's data stays isolated |
| `AMSDP_Business_Rules_V1.1.md` §38 | Super Admin configures **plans, user limits, doctor-entry limits, branch/location limits, feature availability, start/expiry, grace period, suspension and reactivation** — this is the canonical entitlement dimension list |
| `AMSDP_Business_Rules_V1.1.md` §39 | Lifecycle: notify before expiry → grace (normal operation) → suspend **write** operations → **preserve read-only** access → never delete data for expiry → renewal restores operations without a new tenant → audit every state change |
| `AMSDP_Business_Rules_V1.1.md` §40 | Audit must include **subscription activation, expiry, suspension and reactivation**, with tenant, branch/context, actor, timestamp, target, before/after |
| `AMSDP_Business_Rules_V1.1.md` §42 | "secure password/session handling" and "**Never embed credentials or production secrets in source code**" — the secret is env-sourced, but the fallback constant plus an unset-able guard (R-10) is a §42 **gap**, not a §42 violation of the kind an earlier draft claimed |
| `AMSDP_Master_Feature_List_V2.5` §C, §C.1, §D | **10** product modules with declared dependencies; "Module entitlements are enforced server-side"; no optional module may disable Core |
| `AMSDP_Master_Feature_List_V2.5` §5.1 | Super Admin is a **platform-governance** role: create/activate/suspend subscriber accounts, manage plans and limits, view tenant-level usage and system health — and **"must not create routine cross-tenant access to patient or appointment content"** |
| `AMSDP_Master_Feature_List_V2.5` §19.1–§19.3 | Subscription model FINALIZED; controls APPROVED; expiration behaviour APPROVED at policy level, with grace duration, export, reactivation and retention **explicitly left as platform-policy decisions** |
| `AMSDP_Master_Feature_List_V2.5` §30.1–§30.4 | Module activation at organization level, branch availability configurable, purchase ≠ user access, and the seven module lifecycle states |
| `AMSDP_Master_Feature_List_V2.5` §30.3 | **Pricing, packaging, trial/refund policy, AI allowance, taxes — explicitly not fixed**; these are OPEN, not defects |
| Owner decisions Q-1…Q-6 | Governance constraints on how this work is recorded (evidence grades, no invented capability) |

### 6.3 The consequence for the audit's verdict

The platform therefore violates no approved rule by lacking SaaS billing — **payments,
invoicing and gateways are explicitly out of scope**. It *does* violate approved requirements
by lacking plan definitions, entitlement enforcement, lifecycle state machine and the
super-admin console. That distinction is the backbone of the roadmap: the **commercial plane
is configuration-only**, while the **control plane and entitlement plane are mandatory**.

---

## 7. Documented intent vs actual behaviour (contradictions)

Per `.clinerules` §12, a conflict between authority documents is **reported, never silently
resolved**. Each item below names what the document says, what the code does, and where the
resolution is proposed.

| # | Document says (source) | Tree does | Resolution |
|---|---|---|---|
| **C-1** | `AMSDP_System_Architecture_V1.0.md` §8.1: database-per-service | one database, one schema, one Alembic chain, one `common/models.py` | ADR-SAAS-002: keep the shared database for V1; database ownership is an `OPEN` question, not an approved decision. **[Correction 2026-11-17]** ADR-SAAS-002 is now `OWNER-APPROVED` as A1 (microservice split is the target, the shared database is the V1 compromise); `OPEN` remains only for the physical split, owned by `EQ-4` |
| **C-2** | `AMSDP_Master_Feature_List_V2.5` §19/§20 place a super-admin console and organization management in the product | no platform plane, no console, no platform route, no page | roadmap Phases 2–3 build it; audit grades it **ABSENT** |
| **C-3** | `AMSDP_Business_Rules_V1.1.md` §38–§39 specify subscription controls (suspension, reactivation) and an expiry/grace/read-only lifecycle | `organizations.status` exists but **nothing reads it**; the tenant can write it | R-03, R-14; tenant spec §5 |
| **C-4** | `super_admin` reads as a platform superuser | it is a tenant-created `staff_users` row holding the two platform capabilities (Q-1) | IAM spec §7 renames the concept: a tenant role becomes `org_super_admin`, and `platform_admin` becomes a separate principal domain |
| **C-5** | product positioning calls AMSDP a multi-tenant SaaS | it is multi-tenant, but **single-tier**: every tenant gets every capability, no plan exists | this audit's core finding; subscription spec |
| **C-6** | architecture presents services as independently deployable domain owners | all eight services import `common/models.py` and one shared schema, so any schema change touches all of them | recorded as a constraint on the roadmap (release coordination), not as a defect to fix now |
| **C-7** | `AMSDP_Business_Rules_V1.1.md` §40 requires auditing subscription activation/expiry/suspension/reactivation, and V2.5 §5.1 requires platform governance actions to be recorded | `audit_events.organization_id` is NOT NULL + FK, so a platform action that belongs to no tenant has nowhere to be written | **[Correction 2026-11-17]** resolved by O-SaaS-2 as **option A**: `platform_audit_events` for platform-only events, the tenant's `audit_events` (real `organization_id`) for tenant-affecting events, and the column is **never** made nullable; ADR-SAAS-009 `OWNER-APPROVED`. Subscription spec §9.3, roadmap 2.15/3.10, `EQ-4` |
| **C-8** | `AMSDP_Business_Rules_V1.1.md` §42 forbids embedding production secrets in source | the secret is environment-sourced (`identity/models.py:15`); the dev fallback is only reached when `AMSDP_ENV` is unset or `development`, so a production host with `AMSDP_ENV` unset silently runs on a public constant | IAM spec §5.2 makes the guard fail **closed** (`AMSDP_ENV` required, or an explicit `AMSDP_ALLOW_DEV_SECRET=1` opt-in) — R-10 |
| **C-9** | `AMSDP_Master_Feature_List_V2.5` §5.1: the Super Admin dashboard **must not create routine cross-tenant access to patient or appointment content** | a `super_admin` holding `platform.cross_org` passes `require_org_access` for any organization and also holds `patient.*`/`doctor.*`, so cross-org patient and appointment reads are possible; each is audited, but nothing bounds the scope to metadata | IAM spec §7.3 splits the capability: platform administration keeps tenant **metadata/usage** reach, and clinical reach requires a tenant-granted, time-boxed support grant (§9.3 of the architecture spec) |

---

## 8. Requirement gap register

Severity: **S1** blocks commercial launch · **S2** blocks the approved lifecycle/entitlement
requirements · **S3** debt that the SaaS layer makes worse if left.

| ID | Gap | Grade today | Sev | Addressed in |
|---|---|---|---|---|
| R-01 | No plan, module, subscription or entitlement **persistence** | ABSENT | S1 | Subscription spec §4 |
| R-02 | No **enforcement point** for entitlements or limits anywhere in the request path | ABSENT | S1 | Subscription spec §6 |
| R-03 | Tenant can write its **own** `organizations.status` (privilege inversion) | IMPLEMENTED | S1 | Tenant spec §3.3, §6.1 |
| R-04 | Organization update audit writes identical `before`/`after` | IMPLEMENTED | S2 | Tenant spec §10.2 rule 6 |
| R-05 | No provisioning/onboarding (invite, trial creation, first-admin bootstrap) | ABSENT | S2 | Tenant spec §4 |
| R-06 | No platform identity domain (table, scope, endpoint) | ABSENT | S1 | IAM spec §7 |
| R-07 | No token revocation, refresh or server-side logout; 12 h TTL | ABSENT | S1 | IAM spec §4.1–§4.5 |
| R-08 | No password reset and no password policy | ABSENT | S2 | IAM spec §4.6, §6 |
| R-09 | No membership model — one human cannot hold roles in two organizations | ABSENT | S3 | IAM spec §8 (`OPEN`) |
| R-10 | JWT secret is environment-sourced, but the dev-only fallback is reached when `AMSDP_ENV` is unset — a public constant, no error | IMPLEMENTED | S1 | IAM spec §5.2 |
| R-11 | No seat/branch/module **counting** (nothing can be compared to a limit) | ABSENT | S2 | Subscription spec §7; Tenant spec §9 |
| R-12 | Modules exist only as prose; no machine-readable capability registry | ABSENT | S2 | Architecture spec §6 |
| R-13 | No way to record a platform-scope audit event | ABSENT | S2 | ADR-SAAS-009; Subscription spec §9.3 |
| R-14 | No read-only tenant mode | ABSENT | S2 | Tenant spec §5, §7 |
| R-15 | No commercial metadata on a tenant (contract dates, billing contact, reseller) | ABSENT | S3 | Architecture spec §7.4 (`OPEN`); Tenant spec §4.3 |
| R-16 | `organizations.config` JSON is unvalidated — any key, any shape | IMPLEMENTED | S3 | Tenant spec §8 |
| R-17 | No platform UI (no `/platform` pages, no plan picker, no tenant list) | ABSENT | S3 | Roadmap Phase 3 |
| R-18 | No tenant closure/offboarding semantics (export, retention, anonymisation) | ABSENT | S2 | Tenant spec §11 |

---

## 9. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| K-1 | Entitlement checks are added as the *primary* gate around a service, accidentally replacing `require_org_access`, creating a cross-tenant read path | Low | Critical | ordering fixed in code review; a test asserting "foreign org still 404 with entitlements enabled" is a release gate |
| K-2 | Suspension is implemented as data-only (status column) and not enforced, so a non-paying tenant keeps operating — commercially the worst outcome | High | High | R-03 + read-only mode + revocation before launch |
| K-3 | Platform plane is built by widening `super_admin` instead of separating identity → every tenant admin becomes a platform admin by rename | Medium | Critical | ADR-SAAS-003 must land before any platform endpoint exists |
| K-4 | The plan catalogue drifts from the module registry (code enables a module the plan does not sell, or vice versa) | High | Medium | single source: `modules` table + code constant asserted equal by a test |
| K-5 | Entitlement cache serves stale state after a downgrade, so a tenant keeps a capability it no longer pays for | Medium | Medium | monotonic `entitlements_version` per org; cache keyed on it |
| K-6 | New platform tables silently create a second migration story in a shared database (C-6) | High | Low | all new tables go into the same single Alembic chain; no second chain |
| K-7 | Tenant closure deletes rows directly, breaking append-only audit (`.clinerules` §3) | Medium | High | closure is soft + anonymisation only; explicit prohibition in tenant spec §11 |
| K-8 | The owner treats these documents as approved architecture and skips the status labels | Medium | Medium | **[Correction 2026-11-17]** the decisions are now genuinely `OWNER-APPROVED`, so the risk inverted: an approved decision still has evidence `NOT IMPLEMENTED`. Mitigation is the two-axis label (architecture §1.3) and the roadmap's gates — no gate in the set is satisfied by a decision |

---

## 10. Reusable assets — build on these, do not rebuild

| Asset | Why it matters to the SaaS layer |
|---|---|
| `require_org_access` + token-derived tenancy | the isolation guarantee already exists; the SaaS layer must sit *above* it |
| `common/denial_audit.py` | denial recording already satisfies §3; platform denials reuse the pattern, not a new one |
| `common/audit.py` append-only writer | one writer for the whole platform; plan/lifecycle events extend its action vocabulary |
| `symptom_catalog.organization_id` nullable | the existing precedent for global reference data, directly applicable to plans |
| `organizations.config` JSON | a ready extension point for tenant feature overrides (validated under R-16) |
| Facility hierarchy | the tenancy tree the "organization owns sites" model needs |
| `common/permissions.py` map | the role vocabulary membership and platform roles must compose with, not replace |
| 22-table inventory with uniform tenant columns | the migration surface for plans/subscriptions is additive, not a rewrite |

---

## 11. Explicit non-findings (things that look broken but are not)

Recorded so a future reader does not "fix" correct behaviour.

1. **Cross-org access returning 404 rather than 403** is required by `.clinerules` §3 and is
   why `test_platform_admin.py` asserts 404. Not a bug.
2. **`401` not appearing in `audit_events`** is a deliberate, documented exclusion
   (`denial_audit.py` docstring): an unverified token has no tenant, and writing it to a
   guessed tenant would be a cross-tenant integrity attack. Not an audit hole.
3. **`symptom_catalog` rows with NULL `organization_id`** are the shared catalogue by design,
   not leaked rows.
4. **No account lockout on repeated failed logins** is an owner-approved decision (lockout
   enables denial of service against a known username); the DB-backed throttle is the control.
5. **Every service importing `common/models.py`** is the current architecture (modular
   monolith), not a dependency mistake to be refactored inside a SaaS feature.

---

## 12. Evidence summary

| Area | Grade | Basis |
|---|---|---|
| Multi-tenant isolation (org + branch) | IMPLEMENTED + TESTED | code path + `backend/tests/test_platform_admin.py` |
| Permission matrix | IMPLEMENTED | `common/permissions.py`, used by all routers |
| Denial auditing (403/404/422) | IMPLEMENTED | `common/denial_audit.py`, installed in every service |
| Append-only audit trail | IMPLEMENTED **by convention only** | `common/audit.py`; there is **no DB-level trigger** preventing UPDATE/DELETE, so "append-only" is a code discipline, not an enforced invariant — recorded as a real weakness, not fixed here |
| Login throttling | IMPLEMENTED | `common/login_throttle.py` + `login_attempts` |
| Platform identity | **PARTIAL** | capability + audited cross-org access exist (Q-1); no separate principal domain, scope claim or platform route (§4.5) |
| Token revocation / refresh / logout / reset | ABSENT | grep + login path |
| Tenant lifecycle enforcement | ABSENT | status column unread |
| Subscription / plan / entitlement / quota | ABSENT | exhaustive negative grep (§6.1) |
| Billing / payments / invoicing | ABSENT **and out of scope** | product documents exclude it |
| Platform admin UI | ABSENT | `frontend/pages/` |

> **Nothing in this audit is VERIFIED** (§1.3). Where a reader needs VERIFIED, the roadmap's
> Phase 0 gate defines the runtime checks that would earn it.

---

## 13. Recommended entry point

Do **not** start with tables. Start with the two decisions everything else depends on:

1. **ADR-SAAS-003 — platform identity is a separate principal.** Without it, every later
   endpoint either widens `super_admin` (K-3) or re-invents authorisation.
2. **ADR-SAAS-002 — tenant key and database ownership.** Confirms `organization_id` as the
   only tenant key and records that a shared database is the V1 choice, not an approved
   architecture principle.

Then, in order: close R-03/R-04 (tenant-owned lifecycle + broken audit) → add revocation
(R-07) → entitlement persistence and one enforcement point (R-01/R-02) → lifecycle state
machine and read-only mode (R-14) → platform console (R-17). The roadmap sequences this with
gates and exit criteria.

> **[Correction 2026-11-17]** Both entry-point decisions were made: ADR-SAAS-003 is
> `OWNER-APPROVED` (O-SaaS-1) and ADR-SAAS-002 is `OWNER-APPROVED` (A1). The recommended *order*
> above is unchanged and still governs, but the sequencing now lives in the implementation roadmap
> Revision 2 — including the corrected placement of multi-membership in Phase 2 (`EQ-1` blocks the
> Phase 2 migration). Note that "close R-03/R-04" remains an evidence statement: the tenant can still
> write its own status in the tree as audited.

---

## 14. Document set, open items and reproduction

### 14.1 The six documents

| Document | Answers |
|---|---|
| `AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` | what "Hybrid SaaS" means for AMSDP: planes, modules, ADR-SAAS-001…017 (001–017 after Revision 2; 013 `SUPERSEDED` by 014) |
| `AMSDP_Identity_and_Access_Management_Specification_V1.0.md` | principals, tokens, sessions, platform identity, membership |
| `AMSDP_Tenant_and_Organization_Management_Specification_V1.0.md` | tenant model, provisioning, lifecycle, read-only mode, closure |
| `AMSDP_Subscription_and_Entitlement_Management_Specification_V1.0.md` | plans, modules, subscriptions, limits, enforcement, audit |
| `AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md` | phases, gates, exit criteria, risk sequencing |
| **this document** | what exists today, graded, with contradictions and gaps |

### 14.2 Questions raised by this audit — all since decided

The audit numbers these questions A-1…A-5 locally; the **canonical ids** are those in the
architecture specification's registry (§14.3), which is the single `O-SaaS` namespace for the whole
six-document set. The right-hand column records that mapping so a reader can follow either number.

> **[Correction 2026-11-17]** Every question below was **ruled by the owner on 2026-11-17**. The
> question list is kept verbatim because it is the audit's historical output; the ruling column is the
> correction. None of the rulings changes an evidence grade in §12.

| Local | Question | Recorded in | Canonical id | Ruling (2026-11-17) |
|---|---|---|---|---|
| A-1 | Is the deployment model shared-database multi-tenant only, or must dedicated per-tenant stacks be supported in V1? | ADR-SAAS-012 | O-SaaS-6 | **Not in MVP.** Shared database for V1; P2 dedicated and P3 institution-controlled are long-term; licence mechanics stay `SPECIFIED` (`EQ-6`) |
| A-2 | Platform-scope audit: a new `platform_audit_events` table, or a nullable `organization_id` on `audit_events`? | ADR-SAAS-009 | O-SaaS-2 | **New table (option A).** `organization_id` is **not** made nullable |
| A-3 | One human, many organizations: membership table now, or defer with separate accounts? | ADR-SAAS-013 | O-SaaS-7 | **Membership now** — multi-membership adopted, ADR-SAAS-013 superseded by ADR-SAAS-014; physical shape is `EQ-1…3` |
| A-4 | Should `super_admin` be renamed (a breaking change to tokens and roles) or deprecated in place? | IAM spec §7.4 | O-SaaS-1 | **Renamed by controlled migration**, never dropped; the legacy alias and its `platform.*` grants survive until the replacement is `TESTED`/`VERIFIED` |
| A-5 | Who may close a tenant, and does closing anonymise clinical data or retain it? | Tenant spec §11 | O-SaaS-16 | **Platform administrator approval plus a second approver**; data **retained by default**; anonymisation only on legal approval, as a separate audited act |

### 14.3 Reproduction (read-only)

```bash
grep -n '__tablename__' backend/common/models.py                                   # 22 tables
grep -rn 'subscription\|entitlement\|billing' backend/ frontend/ --include='*.py' --include='*.js'  # no matches
grep -rn '_TOKEN_HOURS' backend/identity/                                          # _TOKEN_HOURS = 12
grep -rn 'Organization.status' backend/                                            # unenforced
ls backend/alembic/versions/                                                       # one linear chain, head f7d2b4c6e8a1
git log --oneline -1                                                               # 133ce83
```

---

*End of audit. Written to `docs/architecture/saas/` per `.clinerules` §11; registered in
`docs/governance/AMSDP_Docs_Index_V1.0.md` per §12. No code, schema, migration or behaviour
was changed by this document.*
