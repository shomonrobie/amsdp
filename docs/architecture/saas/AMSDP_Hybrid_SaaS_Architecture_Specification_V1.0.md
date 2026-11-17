# AMSDP — Hybrid SaaS Architecture Specification V1.0

> **Document ID:** `AMSDP_Hybrid_SaaS_Architecture_Specification`
> **Version:** V1.0 · **Date:** 2026-11-17 · **Branch:** `hackathon-mvp` @ `133ce83`
> **Status:** **SPECIFICATION — PROPOSED, NOT APPROVED.** Nothing in this document authorises
> implementation. Every design choice carries an explicit status label; the owner accepts,
> rejects or amends each one through the ADR register in §12.
> **Companion documents (read together):**
> `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` (evidence base — every fact cited here),
> `AMSDP_Identity_and_Access_Management_Specification_V1.0.md`,
> `AMSDP_Tenant_and_Organization_Management_Specification_V1.0.md`,
> `AMSDP_Subscription_and_Entitlement_Management_Specification_V1.0.md`,
> `AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md`.
> **No code, schema, migration, compose file or frontend file was changed to produce it.**

---

## 1. Purpose, authority and reading rules

### 1.1 What this document is

A single coherent architecture for turning AMSDP from *multi-tenant but single-tier* into a
**commercially operable Hybrid SaaS platform** — without weakening the tenant isolation that
already works, and without inventing business rules the owner has not approved.

### 1.2 Authority order applied

1. `.clinerules` §1–§12 (governance, non-negotiables, evidence standard).
2. **Approved business rules**: `AMSDP_Business_Rules_V1.1.md` §37–§39 (subscription
   lifecycle), §40 (audit), §42 (security), Part II §3–§6 (tenancy).
3. **Approved product capability**: `AMSDP_Master_Feature_List_V2.5` §C/§C.1/§D (module
   catalogue and dependencies), §5.1 (Super Admin dashboard scope and its cross-tenant
   prohibition), §19.1–§19.3, §30.1–§30.4.
4. **Owner direction**: *Hybrid SaaS only*; all other technical decisions PROPOSED/OPEN.
5. Everything else in this document: **proposed**.

### 1.3 Status labels used (and enforced)

| Label | Meaning | May an agent implement it? |
|---|---|---|
| `APPROVED` | Traceable to a Business Rules or V2.5 statement quoted in §13 | Yes, once scheduled |
| `PROPOSED` | This document's design; not yet accepted by the owner | **No** — requires owner acceptance of the ADR |
| `OPEN` | A decision the owner must make; both options are described | **No** |
| `DEFERRED` | Explicitly out of scope for V1 | No |
| `FORBIDDEN` | Contradicts a rule or a non-negotiable | Never |

### 1.4 What this document deliberately does **not** do

- It does not decide pricing, packaging, taxes, trial/refund policy or AI allowances — V2.5
  §30.3 lists those as **not fixed**, so they appear here only as `OPEN` configuration hooks.
- It does not authorise a database-per-service refactor; it records the contradiction (audit
  C-1) and proposes the V1 position as an ADR.
- It does not change tenant key semantics: `organization_id` remains the single tenant key
  (`.clinerules` §3).

---

## 2. Definition — what "Hybrid SaaS" means for AMSDP

The phrase is ambiguous and an architecture cannot be built on an ambiguity. This section
pins it down. **The definition below is `PROPOSED`** (ADR-SAAS-001); the owner-approved part
is only the direction *"Hybrid SaaS"* itself.

"Hybrid" applies along **three independent axes**. A deployment picks one value per axis, and
the same codebase serves every combination.

### Axis A — Commercial plane separation (always on)

A **platform/control plane** exists alongside the existing **tenant/exhibition plane**. The
platform plane governs *who may operate, and what they are entitled to*; the tenant plane runs
clinical operations. V2.5 §5.1 already approves a Super Admin dashboard for platform
governance and simultaneously forbids it from creating **routine cross-tenant access to
patient or appointment content**. That single sentence defines the boundary of this axis:

> The platform plane may see *tenant metadata* and *aggregate usage*. It may not browse
> patient records, appointments or clinical content as a normal operating mode.

### Axis B — Deployment shape (configurable per customer)

| Mode | Shape | Who it is for | Status |
|---|---|---|---|
| **B1 Shared** | one stack, many organizations, one database, tenant column isolation (today's model) | clinics, chambers, small hospitals | `PROPOSED` as the default |
| **B2 Dedicated** | one stack per customer (institutional / government / on-premise), same images, same migrations, one organization | institutions that cannot share infrastructure | `OPEN` — ADR-SAAS-012 / O-SaaS-6 (in scope at all? licensing answer?) |
| **B3 Estate** | both B1 and B2 running simultaneously; **no data crosses between them** | platform operator serving both markets | `PROPOSED` |

B1 is what the tree implements today. B2 is a *deployment* variation, not a code fork: the
only difference is configuration (`AMSDP_DEPLOYMENT_MODE`) and that the platform plane is
restricted to a single tenant plus local licensing.

### Axis C — Capability shape (already approved)

**Core + modules.** `AMSDP Core` is the foundation; nine further modules are separately
activatable with declared dependencies (V2.5 §C, §D). This axis is `APPROVED` — it is the
reason a subscription/entitlement layer must exist at all.

### 2.1 What Hybrid does **not** mean here

- It does not mean "hybrid cloud" or split on-prem/cloud data planes. No such requirement is
  approved.
- It does not mean multi-tenant *and* multi-database simultaneously for the same tenant.
- It does not mean per-branch subscriptions: V2.5 §6.1 states branches are **not** separate
  tenants, and the audit confirms a plan must attach to an organization.
- It does not mean payments. Billing gateways, invoicing and collection are **out of scope**
  (V2.5 §30.3, §21) — the platform records commercial *configuration*, not money movement.

---

## 3. Reference architecture

### 3.1 Planes

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  PLATFORM (CONTROL) PLANE — new        "governs who may operate and what      │
│                                         they are entitled to"                │
│                                                                              │
│  platform identity ── platform RBAC ── tenant registry ── plan & subscription │
│  (platform_users)     (3 roles)        (organizations)     (plans, modules)  │
│                              │                                │              │
│                        lifecycle state machine ──── entitlement resolver      │
│                        (active/grace/read_only/     (plan ∪ purchased →      │
│                         suspended/closed)            org → branch)          │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ reads tenant metadata + writes lifecycle /
                                │ entitlement decisions; NEVER routine clinical reads
┌───────────────────────────────▼──────────────────────────────────────────────┐
│  SHARED KERNEL — existing, unchanged contract                                │
│  common/auth.py (principal, tenant scope) · common/permissions.py (RBAC)     │
│  common/audit.py (append-only writer) · common/denial_audit.py (403/404/422) │
│  common/models.py (single schema) · common/database.py (single engine)       │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ every request passes through, in order (§5)
┌───────────────────────────────▼──────────────────────────────────────────────┐
│  TENANT PLANE — existing, 8 services                                         │
│  identity · organization · patient · doctor · scheduling · appointment ·      │
│  queuing · audit                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

Three observations that constrain everything else:

1. **The shared kernel is the enforcement point.** Because all eight services import
   `common/`, the lifecycle gate and the entitlement gate belong there — one implementation,
   eight consumers. Putting them in each service would guarantee drift.
2. **The platform plane is a new service, not a new role.** It must not be reachable through
   tenant tokens and its tokens must not be accepted by tenant services (ADR-SAAS-003).
3. **The tenant plane keeps its own authorisation.** Entitlements are *commercial*
   eligibility; permissions are *role* authority; tenant scope is *isolation*. All three are
   required and none substitutes for another (audit K-1).

### 3.2 Component inventory

| Component | New/existing | Plane | Responsibility | Status |
|---|---|---|---|---|
| `backend/common/auth.py` | existing, **extended** | kernel | principal resolution; add principal-type/`scope` check | `PROPOSED` (additive) |
| `backend/common/permissions.py` | existing, **extended** | kernel | tenant RBAC map; add a **separate** platform permission map | `PROPOSED` |
| `backend/common/lifecycle.py` | **new** | kernel | resolve tenant lifecycle state; `require_operational` / `require_write_access` dependencies | `PROPOSED` |
| `backend/common/entitlements.py` | **new** | kernel | resolve effective modules + limits for an org, cached by version; `require_module(key)` | `PROPOSED` |
| `backend/common/audit.py` | existing | kernel | append-only writer; extend action vocabulary (`subscription.*`, `tenant.*`, `platform.*`) | `APPROVED` (BR §40) |
| `backend/common/denial_audit.py` | existing | kernel | unchanged; will automatically record lifecycle/entitlement denials (403) | `APPROVED` (`.clinerules` §3) |
| `backend/platform/` | **new service** | platform | subscriber registry, plan catalogue, subscriptions, entitlement administration, tenant usage | `PROPOSED` |
| `backend/identity/` | existing, **extended** | tenant | refresh/revoke/reset endpoints; environment-sourced secret | `PROPOSED` |
| `backend/organization/` | existing, **restricted** | tenant | remove tenant self-service `status` write (R-03); keep profile/branch/hierarchy | `PROPOSED` |
| `frontend/pages/platform/*` | **new** | platform | tenant list, plan editor, subscription assignment, usage | `PROPOSED` |
| `frontend/pages/settings/*` | **new/extended** | tenant | "my plan", module visibility for org admins | `PROPOSED` |
| `modules` / `plans` / `subscriptions` tables | **new** | platform (data) | §7.3 | `PROPOSED` |
| Alembic chain | existing | data | **one** chain, head `f7d2b4c6e8a1` → new revisions appended | `PROPOSED` |

### 3.3 Why a separate `backend/platform/` service rather than endpoints inside `organization`

| Criterion | Inside `organization` | Separate `platform` service |
|---|---|---|
| Token acceptance | mixed with tenant tokens in one app | own dependency: platform tokens only |
| Blast radius if misconfigured | tenant org API exposed | isolated |
| Audit surface | interleaved with tenant org events | one service, one action namespace |
| Deployment in B2 dedicated mode | indistinguishable from tenant code | can be restricted per deployment |
| Extra cost | none | one more container (Compose already runs nine) |

`PROPOSED` choice: separate service, published through the frontend rewrite layer like every
other service. No new third-party dependency is introduced.

---

## 4. Runtime topology change

### 4.1 As-is

Postgres + 8 FastAPI services + Next.js. No gateway: the browser talks to the frontend, and
`frontend/next.config.js` rewrites `/api/v1/*` to internal service hosts.

### 4.2 Target (additive only)

Add **one** service (`platform`, internal only) and **no** new infrastructure component. The
frontend gains `/api/v1/platform/*` rewrites. Nothing else moves.

| Concern | Decision | Status |
|---|---|---|
| API gateway | not introduced; Next.js rewrites remain the single browser entry | `PROPOSED` (no change) |
| Service discovery | Compose DNS, unchanged | `PROPOSED` (no change) |
| Message bus | not introduced; lifecycle transitions are transactional DB writes + audit rows | `PROPOSED` |
| Expiry scheduler | **one** in-process scheduler inside the `platform` service guarded by a Postgres advisory lock, so replicas cannot double-fire | `PROPOSED` |
| Notification delivery | reuse the existing `notifications` outbox; its worker is not deployed today (audit AR-3), so deploying it becomes a **Phase-4 prerequisite** for expiry warnings, not a SaaS blocker | `PROPOSED` |
| Read replicas / sharding | not introduced | `DEFERRED` |

> The expiry job is the only time-driven behaviour in the whole SaaS layer. It is specified as
> **idempotent**: running it twice must produce the same state and exactly **one** audit row.
> It only acts when the stored state still matches its expected predecessor (compare-and-set),
> which is also the concurrency control for a platform admin suspending a tenant at the same
> moment.

### 4.3 Deployment modes in practice

| Aspect | B1 Shared (default) | B2 Dedicated |
|---|---|---|
| `AMSDP_DEPLOYMENT_MODE` | `shared` | `dedicated` |
| Organizations per database | many | exactly one (enforced at provisioning) |
| Platform plane | full tenant registry | restricted: single tenant, no cross-tenant surface |
| Subscription source | platform-recorded subscription | local licence record; renewal is an owner/ops action (O-SaaS-6, `OPEN`) |
| Data residency | operator's database | customer's infrastructure |
| Upgrade | one release, all tenants | customer-scheduled window, same migrations |

`AMSDP_DEPLOYMENT_MODE` is `PROPOSED`. Its only permitted effects are: (a) refusing to create a
second organization, (b) hiding multi-tenant platform screens, (c) refusing cross-tenant admin
actions. It must **never** change authorisation logic — the same isolation rules apply in both
modes, because a bug that is masked in B2 becomes a breach in B1.

---

## 5. Request pipeline and enforcement order

This is the most important section in the document: the order determines whether the platform
is safe.

### 5.1 Order (fail closed at every step)

```
1  transport          Bearer token present
2  signature/expiry   verify (jose), reject 401            ── no DB
3  principal type     claim `scope` ∈ {tenant, platform}
4  principal resolve  re-read the principal row; status must be active
5  plane match        tenant endpoint + platform token   → 401 (wrong plane)
                      platform endpoint + tenant token   → 401 (wrong plane)
6  tenant scope       org from token; path org must equal token org, else 404
7  lifecycle gate     state must permit this HTTP method (§5.3)
8  RBAC               require_permission(...) / platform permission
9  entitlement gate   require_module(key) for module-gated routes only
10 handler            performs the operation
11 audit              append event (success) — failure paths audited by denial middleware
```

Rules that make the order non-negotiable:

- **Steps 6 before 7 before 9.** A lifecycle or entitlement check that runs before the tenant
  scope check can leak existence information about another tenant; it must run *after* the
  caller's tenant is verified.
- **Step 9 last, and narrow.** Entitlement checks apply only to routes that belong to an
  optional module. Applying them globally would make an entitlement bug able to switch off
  Core, which V2.5 §D forbids ("no optional module may disable or corrupt the Core appointment
  and queue workflows").
- **Step 5 is symmetric.** A tenant token presented to a platform route is not "a tenant
  token with insufficient role" — it is a **wrong-plane** credential and gets `401`, never a
  polite `403` that reveals the platform surface exists.
- **Nothing is enforced in the frontend.** Hiding a menu item is explicitly insufficient
  (V2.5 §30.1: "Hiding a menu item is not sufficient enforcement"). The frontend renders what
  the API tells it is available; the API is the boundary.

### 5.2 Failure semantics

| Situation | Response | Audited as |
|---|---|---|
| Missing/expired/malformed token | `401` | log stream only (no verified tenant — existing, documented behaviour) |
| Wrong plane (step 5) | `401` | log stream only (no verified tenant yet) |
| Foreign org / foreign branch (step 6) | `404` | `audit_events` via denial middleware |
| Lifecycle forbids the method (step 7) | `403` + machine code `TENANT_READ_ONLY` / `TENANT_SUSPENDED` / `TENANT_CLOSED` | `audit_events` (denial) **plus** the lifecycle event that caused it, written by the platform plane |
| Missing permission (step 8) | `403` | `audit_events` (denial) |
| Module not entitled (step 9) | `403` + machine code `MODULE_NOT_ENTITLED` + module key | `audit_events` (denial) |
| Entitlement resolution error | `503` — **never** allow the request | `audit_events` + error log; the response carries `X-Entitlement-State: unknown` |

The last row is a deliberate distinction: "not entitled" and "cannot determine entitlement"
must not look the same, because the first is a normal commercial outcome and the second is an
incident. Both deny; only one pages an operator.

### 5.3 Lifecycle × method matrix

States are defined once, here, and used identically by every document in this set.

| State | Sign in | Read (GET/HEAD) | Write (POST/PATCH/PUT/DELETE) | Export | Public display / tracking |
|---|---|---|---|---|---|
| `active` | yes | yes | yes | yes | yes |
| `grace` | yes | yes | **yes** (BR §39 item 3: normal operation continues) | yes | yes |
| `read_only` | yes | yes | **403 `TENANT_READ_ONLY`** | yes (BR §39 item 5 "permitted exports") | yes |
| `suspended` | yes (so support can act) | **403 `TENANT_SUSPENDED`** | 403 `TENANT_SUSPENDED` | platform-only | neutral "temporarily unavailable" |
| `closed` | 403 `TENANT_CLOSED` | 403 `TENANT_CLOSED` | 403 `TENANT_CLOSED` | platform-only | 404 / neutral |

Three notes:

1. **`grace` is not a penalty state.** BR §39 item 3 says operation continues during grace. A
   design that degrades service during grace would violate the approved default.
2. **`suspended` is full block, `read_only` is the expiry path.** BR §39 item 5 preserves read-only
   after grace; explicit suspension (BR §38) is a governance action for abuse/legal cases and
   is therefore stronger. Both are `PROPOSED` interpretations recorded in ADR-SAAS-005.
3. **Public, unauthenticated endpoints are gated too.** `/api/v1/queue/display` and
   `/api/v1/track/{token}` resolve a tenant; they must consult the same lifecycle resolver, or
   a suspended tenant keeps broadcasting a live queue. Tracking returns 404 when the owning
   tenant is not `active`/`grace`/`read_only` (non-disclosing), the display returns a neutral
   message and no patient-identifying content.

---

## 6. Module registry (capability model)

V2.5 §C is an `APPROVED` catalogue of 10 modules. The architecture adds a **stable machine key**
per module (`PROPOSED`) so that code, plans, entitlements and audit rows share one vocabulary.

| Module key | Product module (V2.5 §C) | Depends on | Implementation status in this tree (audit evidence) |
|---|---|---|---|
| `core` | AMSDP Core | — | **IMPLEMENTED** — orgs, branches, facilities, staff, patients, doctors, schedules, appointments, queue, audit |
| `pqv` | Patient Queue Visibility (DQDS + PQT) | `core` | **IMPLEMENTED** — `/api/v1/queue/display`, `tracking_tokens` |
| `patient_communication` | Patient Communication | `core` | **PARTIAL** — `notifications` table + org notification config; worker not deployed, no provider integration |
| `analytics_reports` | Analytics & Reports | `core` | **PARTIAL** — operational dashboard endpoint only; no report suite |
| `clinical_records` | Clinical Records & Consultation Documentation | `core` | **ABSENT** |
| `prescriptions` | Digital Prescription Management | `clinical_records` | **ABSENT** |
| `prescription_library` | Prescription Support Library | `clinical_records` | **ABSENT** |
| `encounter_history` | Encounter History & Record Retrieval | `clinical_records` | **ABSENT** |
| `icd_assistant` | Intelligent Clinical Documentation Assistant | `clinical_records` | **ABSENT** |
| `clinical_summaries` | Clinical Summaries & Follow-up Assistance | `clinical_records` | **ABSENT** |

### 6.1 Registry invariants

1. **The registry exists in exactly two places**: a database table (`modules`) and a code
   constant, and a test asserts they are equal. A plan may not reference an unknown key; code
   may not gate on a key the table does not contain.
2. **`core` cannot be disabled.** V2.5 §D: no optional module may disable or corrupt the Core
   workflows. Therefore `require_module("core")` is a no-op by construction and is never
   written.
3. **Dependencies are declarative, not implied.** Enabling `prescriptions` without
   `clinical_records` is a configuration **error**, rejected at write time with a validation
   message — never silently satisfied at request time.
4. **A module key is not a permission.** Purchasing `clinical_records` does not let a
   receptionist read notes (V2.5 §30.1/§30.2). Module entitlement and RBAC compose.
5. **Absent modules are not "disabled by a flag".** For a module that does not exist in the
   codebase, no route may reference `require_module` for it yet; the module is simply sold only
   after its phase lands (roadmap §5).

### 6.2 Why the key set is fixed now, even though most modules are unbuilt

Because plans reference module keys. If keys are invented at implementation time, every plan
row written earlier becomes ambiguous, and a downgrade in production would be unresolvable.
Fixing ten keys costs nothing today and prevents a data migration later.

---

## 7. Data architecture

### 7.1 Invariants (non-negotiable)

| # | Invariant | Source |
|---|---|---|
| D-1 | **`organization_id` is the only tenant key.** No second tenant column is ever introduced; no table is tenanted by branch alone. | `.clinerules` §3 |
| D-2 | **One database, one schema, one Alembic chain.** New SaaS tables are added to the existing chain, on top of head `f7d2b4c6e8a1`. No second chain, no second engine. | audit C-1; ADR-SAAS-002 |
| D-3 | Migrations are **forward-only and idempotent**; every new column is nullable or has a server default; no destructive change without an approved retention decision. | `.clinerules` §3 |
| D-4 | `audit_events` and `subscription_events` are **append-only**. No UPDATE, no DELETE, ever. | `.clinerules` §3; BR §40 |
| D-5 | Platform tables carry **no clinical or patient data**. If a platform query would need patient content, the design is wrong. | V2.5 §5.1 |
| D-6 | Every new table that holds tenant-scoped data carries `organization_id NOT NULL` + FK. Only genuinely global reference data (modules, plans) may omit it. | audit §3; mirrors `symptom_catalog` precedent |

### 7.2 Ownership map

| Data | Owner plane | Read by tenant plane? | Notes |
|---|---|---|---|
| `organizations`, `branches`, facilities, `specialties` | tenant (organization service) | yes | platform plane reads **metadata only** |
| `staff_users`, `login_attempts` | tenant (identity) | — | platform plane never authenticates a staff user |
| patients / doctors / schedules / appointments / queue / symptoms / tracking | tenant services | yes | platform plane: **no access** (D-5) |
| `audit_events` | tenant (audit service) | yes, per tenant | platform-plane actions that concern a tenant are written **into that tenant's trail** so the tenant can see them (transparency) — see §9.4 |
| `modules`, `plans`, `plan_modules`, `plan_limits` | platform | read-only via kernel | global reference data, no tenant column |
| `subscriptions`, `subscription_modules`, `subscription_events` | platform | read via kernel | `organization_id NOT NULL` (D-6) |
| `platform_users` | platform | never | no org column: platform identity is not a tenant |
| platform audit (option B) | platform | never | ADR-SAAS-009 |

### 7.3 New tables (PROPOSED)

Column detail belongs to the subscription and tenant documents; this table fixes **shape and
ownership** so the two documents cannot diverge.

| Table | Tenant column | Purpose | Key constraints |
|---|---|---|---|
| `modules` | — (global) | the 10 module keys of §6 | `key` PK; `dependencies` text[]/JSON; `status` |
| `plans` | — (global) | sellable configuration of modules + limits | `code` UNIQUE; `version` int; `status` ∈ draft/active/retired |
| `plan_modules` | — | which modules a plan includes | PK `(plan_id, module_key)` |
| `plan_limits` | — | `users` / `doctors` / `branches` / future keys | PK `(plan_id, limit_key)`; `limit_value` NULL = unlimited |
| `subscriptions` | **`organization_id` NOT NULL** | one tenant's commercial state | partial-UNIQUE on `organization_id` where state is current; `plan_id`; `starts_at`, `ends_at`, `grace_ends_at`; `lifecycle_state` mirror is **not** stored here (§7.4) |
| `subscription_modules` | `organization_id` NOT NULL | purchased add-ons beyond the plan | PK `(subscription_id, module_key)`; `source` ∈ plan/addon; `state` per V2.5 §30.4; `branch_scope` JSON NULL = all branches |
| `subscription_events` | `organization_id` NOT NULL | append-only commercial history | `event_type`, `from_state`, `to_state`, `actor_type`, `actor_id`, `reason` |
| `platform_users` | **none** | platform identities | `username` UNIQUE; `role` ∈ platform_admin/platform_ops/platform_viewer |
| `platform_audit_events` | none | platform actions with no tenant | ADR-SAAS-009 option B only |

### 7.4 Changes to `organizations`

| Change | Detail | Status |
|---|---|---|
| **New `lifecycle_state` column** | `String(20)`, NOT NULL, server default `'active'`; values `active`/`grace`/`read_only`/`suspended`/`closed`; index for the expiry job | `PROPOSED` (ADR-SAAS-005) |
| `status` | retained for compatibility, **no longer authoritative**; the tenant PATCH stops accepting it (R-03) | `PROPOSED` |
| `entitlements_version` | `Integer`, NOT NULL, default `1`; incremented on any change to plan, modules, or lifecycle-relevant limits; the cache key | `PROPOSED` |
| commercial metadata | `billing_contact_name`, `billing_contact_email`, `billing_contact_phone`, `contract_reference`, `reseller_code` — all nullable, all platform-writable only | `OPEN` (tenant spec §4.3; not required for enforcement) |

Why a **new** column rather than reinterpreting `organizations.status`: existing rows may hold
values written under the old, unenforced semantics. Reinterpreting them silently would either
lock tenants out (if unknown → `suspended`) or fail open (if unknown → `active`). A new column
with an explicit, audited backfill is the only option that is both safe and reviewable. The
cost is one transitional duplicate field, retired in a later revision. This trade-off is
recorded in ADR-SAAS-005 so the owner can reject it with full information.

### 7.5 Migration policy

1. One revision per concern, named `add_<topic>`, `down_revision = <current head>`.
2. Each revision must be re-runnable on a database that already contains the change (guard on
   `inspector`/`IF NOT EXISTS`), per `.clinerules` §3.
3. Data backfill (all organizations → `lifecycle_state='active'`, `entitlements_version=1`) is
   in the same revision as the column.
4. No `downgrade()` that drops tenant data. A `downgrade()` may drop an index it created.
5. The expiry job and the platform service are deployed **after** the migration, never before.

---

## 8. Performance, caching and resilience

### 8.1 Entitlement resolution — one query, no RPC

The kernel resolves entitlements by reading the database **directly**, not by calling the
platform service:

```
effective_modules(org_id) =
      { m : m ∈ plan_modules(active_plan_of(org)) }            -- included by the plan
  ∪   { m : m ∈ subscription_modules(org) with state enabled } -- purchased add-ons
  restricted to branches in branch_scope (NULL = all branches)
```

```python
# backend/common/entitlements.py  — PROPOSED shape
def resolve(org_id: UUID) -> Entitlement:
    row = select(Organization.entitlements_version, Organization.lifecycle_state) …
    if cached and cached.version == row.entitlements_version:
        return cached
    modules = …  # single joined select over subscriptions/plan_modules/subscription_modules
    ent = Entitlement(org_id=org_id, modules=modules, limits=limits, version=row.version)
    cache.put((org_id, row.version), ent)
    return ent
```

**Why this matters:** the platform service being down, slow, or mid-deploy cannot deny service
to tenants, because entitlements are *data*, not a remote call. This is the single largest
architectural advantage of extending the existing shared kernel instead of introducing a
licence server. It is also a hard constraint on the platform service: it may only **write**
subscription state; it must never become a request-path dependency.

### 8.2 Cache contract

| Aspect | Rule | Status |
|---|---|---|
| What is cached | the resolved `Entitlement` object only | `PROPOSED` |
| Key | `(organization_id, entitlements_version)` | `PROPOSED` |
| Invalidation | **version bump** on any plan/add-on/lifecycle change, inside the writing transaction; the writer also evicts the key in its own process | `PROPOSED` |
| TTL | 60 s safety net (bounds staleness if an eviction is lost across processes) | `PROPOSED` |
| Size bound | LRU, 5 000 organizations per worker, then TTL-managed | `PROPOSED` |
| Lifecycle state | **never cached.** It is one primary-key read and must react immediately to a suspension | `PROPOSED` |
| Failure | resolution exception → `503`, never "allow" (§5.2) | `PROPOSED` |

Multi-process note: the tenant services run as separate containers, so an in-process cache
cannot be evicted remotely. The `entitlements_version` compare in step 1 makes cross-process
staleness self-correcting in one request, and the 60 s TTL bounds the worst case. A distributed
cache (Redis) is **not** introduced — that would add infrastructure to solve a problem the
version column already solves.

### 8.3 Failure modes

| Failure | Effect on tenants | Detection |
|---|---|---|
| `platform` service down | **none** for enforcement (data path); platform UI unavailable | health check, platform audit gap alert |
| DB unavailable | all services fail, as today | existing behaviour |
| Expiry job crashes mid-run | partial transitions, each atomic and audited; next run completes the rest (idempotent) | job heartbeat + "due transitions not applied in 24 h" alert |
| Expiry job runs twice concurrently | advisory lock → second exits immediately | lock metric |
| `entitlements_version` not bumped by a writer | stale entitlements until TTL (max 60 s); logged as `entitlement.version_mismatch` when a write completes without a bump | self-check in the writer |
| Unknown `lifecycle_state` value in DB | treated as `suspended` (fail closed) and alarmed | startup validation + daily integrity query |

### 8.4 Performance budget

| Operation added to every request | Cost | Budget |
|---|---|---|
| lifecycle lookup (PK read) | 1 indexed read | ≤ 1 ms p95, inside the existing DB round-trip budget |
| entitlement resolution (cache hit) | dict lookup | ≈ 0 |
| entitlement resolution (cache miss) | 1 joined select | ≤ 5 ms p95 |
| audit denial write | 1 insert, already existing path | unchanged |

No request gains a network hop. The HTTP p95 budget therefore stays inside the current
envelope; if measurement contradicts this, the version-cache design is revisited **before**
any new component is added.

### 8.5 Frontend obligations (contract, not decoration)

| Obligation | Detail |
|---|---|
| Availability is server-declared | the session payload exposes `modules`, `lifecycle_state`, `limits` — the UI renders from that, and still relies on the API for enforcement |
| Read-only affordance | when `lifecycle_state == read_only`, write controls are disabled **and** the page explains why with a machine-code-mapped message |
| No client-side authority | hiding a nav item is never the enforcement (§5.1) |
| i18n | every new string — platform UI and tenant billing/status UI — is added to `frontend/lib/i18n.js` in **both** `en` and `bn` |
| Accessibility | new screens reuse the shared components and pass the same keyboard/focus checks as existing pages |
| Responsive | platform tables follow the existing table/card breakpoint pattern; no new layout system |

---

## 9. Security architecture and threat model

### 9.1 Trust boundaries

| Boundary | Inside | Outside | Crossing rule |
|---|---|---|---|
| TB-1 | Next.js server/BFF | browser | session cookie; no token in `localStorage` (existing pattern preserved) |
| TB-2 | service ↔ service | — | network-internal; tenant services never accept traffic from the platform plane as a tenant |
| TB-3 | `platform` ↔ kernel/DB | — | platform has its own credentials and its own router; it does not import tenant routers |
| TB-4 | tenant staff ↔ tenant data | — | token-derived org + RBAC (existing, strongest existing control) |
| TB-5 | platform operator ↔ tenant metadata | tenant data | metadata only; no routine patient/clinical access (V2.5 §5.1) |

### 9.2 Threat model

| ID | Threat | Mitigation | Residual risk |
|---|---|---|---|
| T-1 | A tenant admin raises its own plan or re-enables a module | subscription tables are platform-plane only; tenant endpoints never expose them; a tenant token on a platform route is `401` (step 5) | none accepted |
| T-2 | A tenant admin changes its lifecycle state to escape `read_only` | `lifecycle_state` removed from tenant-writable fields (fixes R-03); server-side field allowlist on PATCH | none accepted |
| T-3 | Platform operator reads clinical data | the platform API has **no** patient/clinical/queue endpoints; DB access is granted per-service, and the platform service's role has no DML on clinical tables. **Today the opposite is true** — `platform.cross_org` lets a `super_admin` read foreign patients (audit C-9); Phase 2 must remove that reach | insider DB access (ops-level, out of scope) |
| T-4 | Stolen tenant token replayed against the platform plane | wrong-plane rejection (§5.1 step 5); platform and tenant signing contexts differ (separate secret + `scope` claim) | token theft within its own plane — H-3 in the IAM spec |
| T-5 | Token forgery via a publicly known signing key | the production guard must **fail closed**: `AMSDP_ENV` must be set and non-development, `AMSDP_JWT_SECRET` mandatory there with no production default, secret rotation procedure in the IAM spec (BR §42, audit R-10/C-8) | deployment error → startup failure, not silent forgery |
| T-6 | Entitlement bypass after downgrade | `require_module` on every module-gated route + version-bumped cache + a route↔module test matrix (roadmap §5, §9.2) | ≤ 60 s staleness worst case |
| T-7 | Audit trail shows nothing for platform actions | ADR-SAAS-009 (open) chooses tenant-trail writes vs a platform trail; either way the event is persisted | unresolved until the owner rules |
| T-8 | Audit tampering | append-only writer, no update/delete surface, no admin endpoint | DB-superuser tampering (out of scope) |
| T-9 | Suspended tenant keeps broadcasting a public queue | lifecycle gate on public endpoints (§5.3 note 3) | none accepted |
| T-10 | Expiry fires early/late due to local time | all timestamps `timestamptz`, UTC; grace boundaries computed server-side only | clock skew between hosts (bounded by NTP) |
| T-11 | Tenant is denied service by a broken platform deploy | kernel reads data, not the platform service (§8.1) | platform UI outage only |
| T-12 | A support session becomes routine access | support access is time-boxed, reasoned, audited, and visible to the tenant (§9.4) | none accepted |

### 9.3 Platform operator access rules

1. **No impersonation in V1.** A platform operator cannot obtain a tenant token. If a support
   case requires seeing tenant content, the tenant admin grants a scoped, time-limited
   entitlement; the grant is a normal audited tenant action.
2. **Every platform write carries a reason string** (free text, mandatory, min length) stored
   in `subscription_events.reason` and in the audit payload.
3. **Reads are audited too** when they are cross-tenant metadata listings (who looked at the
   subscriber registry matters).
4. **Two roles minimum separation**: `platform_admin` writes commercial state;
   `platform_ops` may read and may not change plans or lifecycle. `platform_viewer` reads only.
   A single operator holding both is a deployment policy question (O-SaaS-7, `OPEN`), not a
   code question.

### 9.4 Transparency: the tenant sees what the platform did

A commercial action taken by the platform affects the tenant's service. The tenant must be able
to see it in its own audit trail (BR §40), which is why §7.2 routes tenant-affecting platform
events into `audit_events` for that tenant:

| Platform action | Tenant-visible audit action | Also in `subscription_events` |
|---|---|---|
| plan assigned/changed | `subscription.plan_changed` | yes |
| module granted/revoked | `subscription.module_changed` | yes |
| grace started / read-only / suspended / restored | `tenant.lifecycle_changed` | yes |
| tenant created / closed | `tenant.provisioned` / `tenant.closed` | yes |
| platform read of tenant metadata | `platform.metadata_viewed` | no |

The actor is recorded as the platform principal (`actor_type='platform'`, `actor_id`), never as
a tenant user. This preserves the audit trail's meaning: an event is always attributable.

### 9.5 Secrets and credentials

- One signing secret per plane, both from the environment; no production default value in code;
  startup fails closed if the secret or `AMSDP_ENV` is missing. **Today the guard fails open**
  (an unset `AMSDP_ENV` selects the dev constant) — audit R-10/C-8.
- No secret, token, or hash is ever written to an audit row, a log line, or this document
  (`.clinerules` §3).
- Rotating the platform secret must not invalidate tenant sessions and vice versa — a direct
  consequence of separate planes, not an extra feature.

---

## 10. Scope boundaries and non-goals

Stated explicitly, because a hybrid SaaS architecture invites scope creep that this project
cannot afford on 4 GB VRAM / 16 GB RAM hardware and a single-developer rhythm.

| Non-goal | Rationale |
|---|---|
| Payment gateway, card processing, invoicing, tax, dunning | V2.5 §21/§30.3: the MVP records commercial *configuration*; money movement is out of scope. Subscriptions are recorded, not charged. |
| Self-service signup and self-service upgrade | Provisioning is an operator action until tenancy lifecycle is proven (roadmap Phase 2) |
| Usage metering beyond seats/doctors/branches | No metered billing exists to consume it |
| Marketplace / third-party modules | Module registry is closed and code-bound |
| Per-tenant theming, custom domains, white-labelling | Not required by any approved interface; large surface for small value |
| Database-per-tenant or sharding | ADR-SAAS-002: one DB, tenant key; B2 dedicated mode is a separate *deployment*, not a runtime feature |
| Multi-region, read replicas, horizontal autoscaling | Firmly deferred; current scale does not need it |
| SSO / SAML / MFA / OIDC federation | Legitimate enterprise requirement, explicitly `DEFERRED` to the IAM spec's roadmap section. This architecture must not *prevent* it (principal model is claim-based) but does not deliver it |
| Break-glass data impersonation | §9.3: deliberately absent |
| Mobile clients, offline mode | Out of scope |
| Implementing any clinical module | This set of documents specifies the *platform*; clinical modules are product work with their own phases |
| Redesigning the queue, appointment, or dashboard flows | Explicitly forbidden: V2.5 §D — Core must not be perturbed by commercial work |

**What this document does not authorize:** no application code, schema, migration, or
configuration change follows from this specification alone. Implementation requires the
roadmap's gates, each with its own approval.

---

## 11. Change control and backward compatibility

### 11.1 The compatibility contract

Every existing behaviour that works today must still work after the SaaS layer lands, or the
change is a regression:

| Must keep working | Why it is at risk |
|---|---|
| Demo login for seeded staff, super_admin, org_admin | a new principal-type claim could reject existing tokens |
| Org-admin dashboard aggregates | a lifecycle gate could block a demo org whose state is wrong |
| Appointment create → queue → display → track flow | public endpoints gaining a lifecycle check could 404 the demo |
| Existing tenant isolation behaviour (`404` on foreign org) | new gates inserted *before* the scope check could leak or mask |
| Audit trail for existing actions | a new action vocabulary could change existing rows |

Mitigation is structural, not hopeful: enforcement is **additive**, existing dependencies keep
their signatures, and the Phase-1 exit gate is a full re-run of the demo flows (roadmap §4).

### 11.2 Tenants without commercial data

| Situation | Behaviour | Why |
|---|---|---|
| Organization has **no** subscription row | sign-in and **Core only**; optional modules denied; alarm raised | Core can never be switched off by commercial configuration (V2.5 §D); a missing row is a data defect, not a customer decision, so it must be loud |
| Organization has a subscription in `active` | full plan + add-ons | normal path |
| Existing demo organizations at migration time | the migration **backfills** an explicit `active` subscription on a `legacy_full` plan | so nothing changes for existing deployments, and no request-time fail-open is needed |

This is the only place a "missing data" case does not hard-deny, and it is bounded: it degrades
to the Core floor (which is what the deployment already is) and it pages an operator. Every
other missing or unreadable commercial input fails closed (§5.2).

### 11.3 Transitional flags (and their removal)

| Flag | Purpose | Removal condition |
|---|---|---|
| `SAAS_ENFORCEMENT_ENABLED` | lets Phase 1 ship the migration + resolver before any gate denies traffic | **must be deleted** at Phase 2 exit; a flag that can disable enforcement in production is a defect, not a feature |
| `AMSDP_DEPLOYMENT_MODE` | shared vs dedicated behaviour of §4.3 | permanent, but scope-limited to the three permitted effects |

Flags may only *delay* enforcement; no flag may ever bypass it once removed, and none is
per-tenant configurable. A per-tenant "enforcement off" switch would be a privilege-escalation
primitive.

---

## 12. Architecture decision register

Every decision that a reviewer might reasonably have made differently is recorded here with its
rejected alternatives. `ACCEPTED` = consistent with an approved document and adopted by this
specification; `PROPOSED` = this specification's recommendation, awaiting owner ratification;
`OPEN` = a genuine owner decision this document cannot make.

| ID | Decision | Rejected alternatives | Status |
|---|---|---|---|
| **ADR-SAAS-001** | "Hybrid SaaS" means one codebase, one database and one deployment shape that can be sold to many organizations, with an optional single-tenant deployment for customers who require it; the commercial plane is configuration on top of the existing tenant plane (§2) | (a) build a separate SaaS control app; (b) stay single-tenant with manual licences; (c) full microservice split with billing | `ACCEPTED` (definition — §2) |
| **ADR-SAAS-002** | One Postgres database, `organization_id` as the only tenant key, one linear Alembic chain | (a) database-per-tenant; (b) schema-per-tenant; (c) a second "commercial" database | `ACCEPTED` (`.clinerules` §3; audit C-1) |
| **ADR-SAAS-003** | Platform identity is a **separate principal domain** (`platform_users`, own token `scope`, own role map), not a tenant-scoped `super_admin` | (a) keep `super_admin` as a platform role inside a tenant; (b) a magic env-var operator account; (c) reuse `staff_users` with a flag | `PROPOSED` (closes audit R-06 and C-9; renames the tenant role, audit C-4) |
| **ADR-SAAS-004** | The platform plane ships as a **new `backend/platform/` service**, not as extra endpoints in `organization` | (a) extend `organization`; (b) a standalone non-Python service; (c) CLI-only administration | `PROPOSED` (§3.3) |
| **ADR-SAAS-005** | Lifecycle lives in a **new** `organizations.lifecycle_state` column with five states; `grace` preserves full operation; `suspended` is a full block; `read_only` is the expiry outcome | (a) reinterpret existing `organizations.status`; (b) a state column on `subscriptions`; (c) derive state from dates at request time | `PROPOSED` (§5.3, §7.4) |
| **ADR-SAAS-006** | Entitlements are resolved **in the kernel from data**, never by an RPC/ licence-server call | (a) call the platform service per request; (b) embed entitlements in the JWT; (c) Redis-backed central resolver | `PROPOSED` (§8.1) — an entitlement in the token cannot be revoked before expiry |
| **ADR-SAAS-007** | Module keys are fixed now (10 keys, §6) and gating applies **only** to optional-module routes; Core is never gated | (a) invent keys per module as built; (b) gate all routes uniformly; (c) plan-level feature strings without a registry | `PROPOSED` (§6) |
| **ADR-SAAS-008** | The platform **records** commercial state; it does not take payments | (a) integrate a gateway now; (b) store card data (never) | `ACCEPTED` (V2.5 §21/§30.3) |
| **ADR-SAAS-009** | Platform-scope audit: either (A) write tenant-affecting actions into `audit_events` with `organization_id` plus a separate `platform_audit_events` for non-tenant actions, or (B) make `audit_events.organization_id` nullable | (a) leave platform actions unlogged; (b) a log file as the record | **`OPEN`** — blocking for Phase 2 (audit C-7) |
| **ADR-SAAS-010** | Enforcement is an **ordered pipeline in the shared kernel** (§5.1); the frontend is never authoritative | (a) per-service checks; (b) middleware-only enforcement without a dependency; (c) frontend gating | `PROPOSED` (§5) |
| **ADR-SAAS-011** | Expiry runs as **one** in-process scheduler with a Postgres advisory lock and compare-and-set transitions (idempotent) | (a) Celery/cron container; (b) per-request lazy expiry evaluation; (c) external scheduler | `PROPOSED` (§4.2) — lazy evaluation would make state unobservable and audit rows unpredictable |
| **ADR-SAAS-012** | Deployment mode via `AMSDP_DEPLOYMENT_MODE` (`shared` / `dedicated`) with exactly three permitted effects | (a) a separate B2 codebase; (b) no B2 support at all; (c) compile-time fork | **`OPEN`** (owner: is B2 in the MVP at all?) |
| **ADR-SAAS-013** | Staff membership: one organization per staff identity (no cross-org membership within one deployment); a "membership" concept is therefore deferred | (a) join table `staff_organizations`; (b) email shared across orgs; (c) cross-org impersonation | **`OPEN`** (owner: is a doctor who works at two clinics in scope?) |

### 12.1 Why ADR-SAAS-013 is open rather than decided

Today `staff_users.organization_id` is `NOT NULL` and the token carries exactly one org; the
tenant isolation model (audit §6, the strongest existing asset) depends on that. Supporting a
staff member in two organizations would mean a principal with a selectable tenant, which is
precisely the shape most multi-tenant breaches take. It is cheaper to keep one-org-per-identity
and provision a second identity than to weaken the invariant — but that is a product decision
about clinician workflows, so it stays `OPEN`.

---

## 13. Traceability to approved requirements

Every claim in this document traces to an `APPROVED` source or to verified evidence in the
audit. Nothing here is invented product intent.

| Approved requirement | Source | Where this set satisfies it | Status |
|---|---|---|---|
| Organizations subscribe to the platform | BR §37 | §2 axis A; subscription spec §3–§4 | `PROPOSED` |
| Super Admin controls entitlement dimensions | BR §38 | plan/limit model §7.3; subscription spec §4, §7 | `PROPOSED` |
| Grace period, then suspended writes, then read-only | BR §39 | lifecycle matrix §5.3; tenant spec §5 | `PROPOSED` |
| No tenant data deletion on non-payment | BR §39 | tenant spec §11 | `PROPOSED` |
| Commercial and access events audited | BR §40 | §9.4; subscription spec §9 | `PROPOSED` |
| Secrets never hardcoded | BR §42 | §9.5; IAM spec §5.2 | `PROPOSED` — already environment-sourced; the remaining defect is the fail-open `AMSDP_ENV` guard (audit R-10, C-8) |
| Ten-module catalogue | V2.5 §C | module registry §6 | `PROPOSED` (keys added) |
| Module dependencies | V2.5 §C.1 | §6.1 rule 3 | `PROPOSED` |
| Core never disabled by a module decision | V2.5 §D | §5.1, §6.1 rule 2, §10, §11.2 | `PROPOSED` |
| No routine cross-tenant operator access | V2.5 §5.1 | §9.3, §9.4 | `PROPOSED` |
| Platform roles and permission separation | V2.5 §19.1–19.3 | IAM spec §7, §9.3 | `PROPOSED` |
| SaaS readiness without payment integration | V2.5 §21 | ADR-SAAS-008, §10 | `ACCEPTED` |
| Module visibility / entitlement / state model | V2.5 §30.1–30.4 | §5, §6, subscription spec §5–§6 | `PROPOSED` |
| Append-only audit; no secret in logs; server-side authorisation; `404` on cross-tenant | `.clinerules` §3 | §7.1, §5.2, §9 | `PROPOSED` |
| Single tenant key, single migration chain | `.clinerules` §3; audit §3 | §7.1 D-1/D-2 | `PROPOSED` |

Two honest notes on status:

- **`PROPOSED` is not a downgrade of intent.** These are specifications awaiting owner
  ratification; the underlying product requirements are already `APPROVED`. What is proposed is
  the *mechanism*, not the requirement.
- **`ACCEPTED` is reserved for decisions the approved documents already force** (ADR-001,
  ADR-002, ADR-008). Nothing in the mechanism is claimed as approved while it is unbuilt — the
  evidence standard (§7 of `.clinerules`) forbids that.

---

## 14. Governance compliance and open items

### 14.1 Documents and rules applied

| Domain (`.clinerules` §4) | Governance applied |
|---|---|
| Multi-tenant data / org isolation | `saas-multitenant-data.md` as adapted (Assessment §3), BR §4–§6, audit §6 |
| Backend API / services | `saas-application-security.md` as adapted, BR Parts II–X |
| Authentication / RBAC | `saas-auth-and-authorisation.md` as adapted, BR §7–§8, `backend/common/permissions.py` |
| Database schema / migrations | `saas-multitenant-data.md` §4–5, `saas-cicd-workflow.md` §3 as adapted, Alembic chain |
| Frontend | `saas-frontend-ux.md` as adapted, shared components, `frontend/lib/i18n.js` |
| Audit / observability | `saas-observability.md` as adapted, `backend/common/audit.py`, `backend/common/denial_audit.py` |
| Deployment / infrastructure | `saas-cicd-workflow.md` as adapted, `docker-compose.yml` |

**Skills:** none installed in this workspace (verified: no `.clinerules/skills/`, `.claude/skills/`,
or repo `skills/` directory). No skill was used or claimed. Governance documents were used in
their place, as `.clinerules` §5 requires.

### 14.2 Deviations declared

1. **Architecture documents, not a milestone report.** This set is `docs/architecture/saas/`,
   per `.clinerules` §11 (subject-matching subfolder); a new `saas/` leaf was added under the
   existing `architecture/` folder rather than creating a parallel top-level folder.
2. **No code, schema or migration was written**, by design. Every normative mechanism is marked
   `PROPOSED` and unbuilt.

### 14.3 Open items — the canonical registry for the whole six-document set

**This table is the single `O-SaaS` registry.** Every sibling document cites these ids and mints no
local ones; if a new question appears, it is added here and cited by id elsewhere. Renumbering is a
defect, not a fix — the ids are referenced from three other documents.

| ID | Question | Owner decision needed | Blocks |
|---|---|---|---|
| O-SaaS-1 | Approve ADR-SAAS-003 (separate platform identity) and the fate of today's tenant-scoped `super_admin`, including R-3 removal of the alias and its `platform.*` grants | Product Owner | Phase 2 |
| O-SaaS-2 | Resolve ADR-SAAS-009 (platform audit shape) — the tenant audit table's `organization_id` is `NOT NULL` | Product Owner + engineering | Phase 2 |
| O-SaaS-3 | Confirm the five-state lifecycle vocabulary and the grace/read-only/suspended interpretations of BR §39 | Product Owner | Phase 1 |
| O-SaaS-4 | Confirm the ten module keys (§6) as the commercial vocabulary | Product Owner | Phase 1 |
| O-SaaS-5 | Approve ADR-SAAS-005 transitional duplicate column (`lifecycle_state` beside `status`) | Engineering owner | Phase 1 migration |
| O-SaaS-6 | Is B2 dedicated deployment in MVP scope (ADR-SAAS-012), and what is the licence/renewal mechanism there? | Product Owner | Phase 3+ |
| O-SaaS-7 | Is one organization per staff identity acceptable (ADR-SAAS-013) — i.e. two accounts for a multi-site clinician? | Product Owner | Phase 2 |
| O-SaaS-8 | Should `platform_admin` and `platform_ops` be separable accounts by policy? | Product Owner | Phase 2 |
| O-SaaS-9 | Migration mapping for legacy `organizations.status='inactive'`: leave as `lifecycle_state='active'`, or map to `closed`/`suspended`? | Product Owner + engineering | Phase 1 migration |
| O-SaaS-10 | In a tenant's own audit view, is a platform operator shown by role only, or by a named identity? | Product Owner | Phase 2 |
| O-SaaS-11 | Are `staff_password_history` reuse checks launch-scope or post-launch? | Product Owner | nothing (`DEFERRED`) |
| O-SaaS-12 | May the operator-assisted reset response return the code to the requesting administrator (V1 assumes yes)? | Product Owner | V1 reset flow |
| O-SaaS-13 | Support-grant acceptance: explicit `org_admin` consent, or policy pre-approval for `grace` tenants? | Product Owner | support-access mechanism |
| O-SaaS-14 | May `platform_ops` suspend a tenant without a second operator (four-eyes)? | Product Owner | suspension authority |
| O-SaaS-15 | MFA for platform operators is `DEFERRED`; accept the resulting risk for MVP launch? | Product Owner | platform launch |
| O-SaaS-16 | Who may close a tenant, and does closure anonymise clinical data or retain it (BR §39 vs legal review)? | Product Owner + legal | Phase 3 |

### 14.4 Self-check against the non-negotiables

| Non-negotiable | Satisfied by |
|---|---|
| No secrets in logs/docs | §9.5, §7.2 (no secret-bearing columns) |
| UI is never the safety boundary | §5.1 rule 4, §8.5 |
| Org/branch from the token, never the body | §5.1 step 6 (unchanged existing mechanism) |
| Cross-tenant fails `404` | §5.2 |
| `organization_id` is the only tenant key | §7.1 D-1 |
| Audit append-only | §7.1 D-4, §9.4 |
| Denials are audited | §5.2 (denial middleware, unchanged) |
| Forward-only idempotent migrations | §7.5 |
| No unverified capability claims | every mechanism labelled `PROPOSED`; §13 notes; §14.1 |

---

## 15. Document control

| Field | Value |
|---|---|
| Written to | `docs/architecture/saas/` (`.clinerules` §11: closest existing subject folder, one new leaf under `architecture/`) |
| Sibling documents | audit (evidence), IAM specification, tenant & organization specification, subscription & entitlement specification, implementation roadmap |
| Evidence base | `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` — every "as built" statement here is sourced there |
| Code, schema, migration, compose, frontend changes | **none** |
| Runtime verification | **none claimed**; this is a specification, not an acceptance report |
| Index registration | `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Revision | V1.0 — 2026-11-17 |
