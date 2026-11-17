# AMSDP — Hybrid SaaS Architecture Specification V1.0

> **Document ID:** `AMSDP_Hybrid_SaaS_Architecture_Specification`
> **Version:** V1.0 · **Revision 3 (post-commit O-SaaS-15 correction) — 2026-11-17** · **Branch:** `hackathon-mvp` @ `597d9b1`
> **Status:** **SPECIFICATION — DECISION-RECONCILED, NOT IMPLEMENTED.** On 2026-11-17 the Product
> Owner decided all sixteen `O-SaaS` items and four architectural directions (A1–A4). Those
> rulings are recorded as `OWNER-APPROVED` in §1.5, §12 and §14.3 and applied throughout this
> document. Every *mechanism* that implements them remains `SPECIFIED` — written, engineering-owned,
> not built — unless a section says otherwise. **Nothing here is `IMPLEMENTED`, `TESTED` or
> `VERIFIED`**, and nothing in this document authorises code.
> **Revision 3 note (2026-11-17, post-commit):** one record corrected — O-SaaS-15 is a
> **production-launch requirement** with a temporary, documented, restricted hackathon exception
> (§1.5, §9.3 rule 7, §14.3), not an indefinite deferral. No mechanism, evidence grade or other
> ruling changed; operator MFA is `NOT IMPLEMENTED`.
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
4. **Owner direction**: *Hybrid SaaS only*, **plus the owner decision packet of 2026-11-17** —
   `O-SaaS-1…O-SaaS-16` and directions A1–A4, recorded in §1.5 and §14.3 and applied throughout
   this document.
5. Everything else in this document: `SPECIFIED` (the earlier label `PROPOSED` is retained as its
   exact synonym) — a written mechanism, engineering-owned, not owner-decided, not built.

### 1.3 Status labels used (and enforced)

Two axes, deliberately never mixed. A document may say "owner-approved, not implemented" and that
is a complete, honest statement; it may not say "approved" and imply "works".

**Decision axis — who decided it**

| Label | Meaning | May an agent implement it? |
|---|---|---|
| `OWNER-APPROVED` | The Product Owner decided it on 2026-11-17 (§1.5) or it is traceable to a Business Rules / V2.5 statement quoted in §13 | Yes, once scheduled and once the mechanism is implemented and tested |
| `SPECIFIED` | This document's design; engineering-owned; **not** owner-decided. `PROPOSED` in this set means exactly this | **No** — requires the owner to accept the ADR |
| `OPEN` | A decision the owner must make; both options are described | **No** |
| `DEFERRED` | Explicitly out of scope for V1 | No |
| `FORBIDDEN` | Contradicts a rule or a non-negotiable | Never |
| `SUPERSEDED` | Replaced by a later decision; kept verbatim for traceability, never reused as current guidance | No — follow the replacement |

**Evidence axis — what actually exists in this tree** (`.clinerules` §7)

| Label | Meaning |
|---|---|
| `NOT IMPLEMENTED` | no code exists |
| `IMPLEMENTED` | code exists and is reachable |
| `TESTED` | the named tests pass in this tree |
| `VERIFIED` | a second, independent artefact confirms it (browser run, live API call, DB read) |

`APPROVED` (used in §6, §13 and the audit) is retained only as the **traceability** label for
"quoted from an owner-approved document". No ADR in this revision carries a bare `ACCEPTED` label;
where an older document does, read `OWNER-APPROVED`.

### 1.4 What this document deliberately does **not** do

- It does not decide pricing, packaging, taxes, trial/refund policy or AI allowances — V2.5
  §30.3 lists those as **not fixed**, so they appear here only as unfixed configuration hooks.
  They are not `OPEN` decisions: nothing in this architecture blocks on them.
- It does not authorise a database-per-service refactor; it records the contradiction (audit
  C-1) and proposes the V1 position as an ADR.
- It does not change tenant key semantics: `organization_id` remains the single tenant key
  (`.clinerules` §3). Multi-organization *membership* (§8 of the IAM spec) gives one human several
  identities-in-tenants; every dataset still carries exactly one `organization_id`.

### 1.5 The owner decisions of 2026-11-17 (record, not re-litigation)

The Product Owner resolved every open item in this set and gave four architectural directions. This
table is the **decision record**; §14.3 is the same list in registry form with the original questions
preserved, and §12 carries the ADR-level consequences. Nothing below is an inference: where a
mechanism was not decided, it is left `SPECIFIED` and appears as an engineering question in §14.3.1.

| ID | Owner decision (2026-11-17) | Applied in |
|---|---|---|
| **O-SaaS-1** | Separate platform identity is approved. `super_admin` is migrated **safely**: existing aliases and permissions are **not removed before the replacement is tested**. | §12 ADR-003; IAM §7.4; roadmap §5 |
| **O-SaaS-2** | Two stores: **platform-only events → `platform_audit_events`**; **tenant-affecting events → the tenant's `audit_events` with a non-null `organization_id`**. `organization_id` is **not** made nullable. | §7.2, §7.3, §9.4; IAM §10.2; subscription §9.3 |
| **O-SaaS-3** | Five lifecycle states approved: `active`, `grace`, `read_only`, `suspended`, `closed`. `grace` is normal operation. Automatic expiry action is **capped at `read_only`** — never auto-suspend, never auto-delete. | §5.3, §7.4; tenant §5 |
| **O-SaaS-4** | The **ten module keys** are the approved commercial vocabulary; **Core is always available** and is never gated or sold. | §6; subscription §4.1, §11.3 |
| **O-SaaS-5** | `lifecycle_state` is **authoritative**. The legacy `organizations.status` remains **transitional** and may be retired later through a controlled migration. | §7.4; tenant §3.3, §12.1 |
| **O-SaaS-6** | **Dedicated SaaS is a long-term direction, not an MVP requirement.** Commercial arrangements are institution-shaped (contract, donor-funded, annual/institutional licence), not assumed monthly. | §2 Axis B, §4.3; subscription §4.4 |
| **O-SaaS-7** | **Multi-membership replaces one-organization-per-staff-identity.** One human identity may hold memberships in several organizations, with per-organization roles, permissions and branch scope. ADR-SAAS-013 is superseded by ADR-SAAS-014. | §12; IAM §8.1, §3; tenant §3.4 |
| **O-SaaS-8** | `platform_admin` and `platform_ops` are **separate responsibilities**. Holding more than one platform role requires an explicit, audited policy — never a default. | §9.3; IAM §7.3 |
| **O-SaaS-9** | Legacy `organizations.status='inactive'` is **never auto-mapped**. It is preserved; only a validated, reviewed backfill to `active` is permitted. | §11.2; tenant §3.3, §12.1 |
| **O-SaaS-10** | A tenant's audit view shows the **named operator identity together with the platform role**, and no unnecessary personal information. | §9.4; IAM §7.3; tenant §10.1 |
| **O-SaaS-11** | `staff_password_history` reuse checks are **deferred** to post-launch. | IAM §4.6 |
| **O-SaaS-12** | The operator-assisted reset **may** return the code to the requesting administrator, under the constraints in IAM §6.2 (hashed at rest, single-use, short-lived, audited, never a new password chosen by the operator). | IAM §6.2 |
| **O-SaaS-13** | Support access requires **explicit `org_admin` consent for every grant**. There is **no pre-approval** for `grace` tenants. | §9.3; IAM §7.3 |
| **O-SaaS-14** | **Suspension requires second-person (four-eyes) approval**, the same as closure. | §9.3; tenant §5.2, §11.3; IAM §7.3 |
| **O-SaaS-15** | **Platform operator MFA is required before production launch.** A temporary exception, explicitly documented as a security risk and restricted to a limited authorised operator group, may be used for the hackathon MVP only; it does not satisfy the production requirement, and MFA is not deferred to a post-launch enhancement. | §9.3 rule 7; IAM §13.2; roadmap §9.6 |
| **O-SaaS-16** | Closure requires **platform administrator approval plus a second approver**. Data is **retained by default**; anonymisation or deletion only with legal approval. | §9.3; tenant §11 |
| **A1** | **Microservices remain the approved target architecture.** It is not redefined as a modular monolith. Transitional compromises are permitted only when explicitly documented as transitional. | §3.4 |
| **A2** | Three customer deployment patterns: **Shared Multi-Tenant SaaS**, **Dedicated SaaS**, **Institution-Controlled / Approved Deployment**. "Estate" is an **operator capability**, not a fourth pattern. Dedicated is long-term (§O-SaaS-6). | §2 Axis B, §4.3 |
| **A3** | **Healthcare organization profiles** (private, government, NGO, community, outreach) are configuration, independent of deployment pattern; a profile is a preset, never a hard restriction. | §2.2 |
| **A4** | The **Platform Service is authoritative** for lifecycle and entitlement. Tenant services enforce **locally** from a controlled, versioned distribution. No synchronous platform RPC on the request path and no direct shared business-data access. Isolation, RBAC and entitlement stay **separate** controls. | §3.5, §8.1 |


---

## 2. Definition — what "Hybrid SaaS" means for AMSDP

The phrase is ambiguous and an architecture cannot be built on an ambiguity. This section
pins it down. The direction *"Hybrid SaaS"*, the **three customer deployment patterns** and the state
vocabulary are `OWNER-APPROVED` (ADR-SAAS-001, ADR-SAAS-005, ADR-SAAS-012; A2, O-SaaS-3, O-SaaS-6).
The mechanisms that implement them remain `SPECIFIED` and unbuilt.

"Hybrid" applies along **three independent axes**. A deployment picks one value per axis, and
the same codebase serves every combination.

### Axis A — Commercial plane separation (always on)

A **platform/control plane** exists alongside the existing **tenant/operations plane**. The
platform plane governs *who may operate, and what they are entitled to*; the tenant plane runs
clinical operations. V2.5 §5.1 already approves a Super Admin dashboard for platform
governance and simultaneously forbids it from creating **routine cross-tenant access to
patient or appointment content**. That single sentence defines the boundary of this axis:

> The platform plane may see *tenant metadata* and *aggregate usage*. It may not browse
> patient records, appointments or clinical content as a normal operating mode.

### Axis B — Customer deployment pattern (three patterns, decided)

`OWNER-APPROVED` 2026-11-17 (A2, O-SaaS-6; ADR-SAAS-012). A deployment selects exactly one pattern.

| Pattern | Shape | Who it is for | In the MVP? |
|---|---|---|---|
| **P1 Shared Multi-Tenant SaaS** | one stack, many organizations, one database, `organization_id` isolation (today's model) | clinics, chambers, small/mid-size hospitals; a network that joins the platform as one tenant | **yes — the only MVP pattern** |
| **P2 Dedicated SaaS** | one stack per customer (institutional, government or private-cloud hosted), same images, same migrations, one organization | institutions that cannot share infrastructure | **no — long-term direction** |
| **P3 Institution-Controlled / Approved Deployment** | the institution's own approved environment (on-premise or its mandated hosting), same images, same migrations, same approval path | government bodies and institutions with a hosting mandate | **no — long-term direction** |

Two consequences the ruling makes explicit:

1. **"Estate" is not a fourth pattern.** Operating P1 and P2/P3 at the same time is an **operator
   capability** — a property of how the platform is run, not a shape a customer buys. It adds no
   code path, no `AMSDP_DEPLOYMENT_MODE` value and no tenant column.
2. **Dedicated is a direction, not a prerequisite** (O-SaaS-6). Nothing in Phases 0–4 may depend on
   P2/P3. When one lands it stays a *deployment* variation — configuration plus a restricted
   platform plane — never a code fork; A1 keeps the service boundaries identical in every pattern.

P1 is what the tree implements today. P2/P3 are recorded so the shared design does not preclude
them, not as work items.

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

### 2.2 Healthcare organization profiles (A3 — `OWNER-APPROVED`, configuration only)

Healthcare customers differ in *governance culture*, not only in size. The owner's direction is that
this difference is expressed as a **profile**: a preset of defaults a tenant starts from.

| Profile | Typical customer | What the preset tends to set | What it must **never** do |
|---|---|---|---|
| `private` | private clinic, chamber, diagnostic centre, small hospital | default branch naming, standard plan hints, self-service onboarding tone | change authorisation, bypass a limit, hide audit rows |
| `government` | government hospital, directorate, ministry-run facility | institutional billing metadata, longer retention review references, formal notice wording | create a second tenant type, grant cross-tenant reach |
| `ngo` | NGO / donor-funded network | donor-orientation reporting defaults, network-branch hierarchy | make a branch a tenant (V2.5 §6.1) |
| `community` | community clinic, outreach programme | minimal-configuration defaults, offline-tolerant wording | weaken isolation because the site is small |
| `outreach` | mobile / camp-based service | session-oriented branch defaults, neutral public-display text | create a per-camp tenant |

Rules that keep the profile from becoming a hidden tenancy model:

1. **A profile is configuration, never a column that decides isolation.** It is stored as a
   whitelisted key in `organizations.config` (tenant spec §8.1) — mechanism `SPECIFIED`. There is no
   `organization_type` tenant discriminator, and D-1 still holds: `organization_id` is the only
   tenant key.
2. **A profile is a preset, not a restriction.** Any tenant may use any feature its plan entitles
   regardless of profile; a profile may change defaults, wording and which optional settings are
   surfaced first — nothing else (A3).
3. **Independent of deployment pattern.** All three patterns (Axis B) can host any profile; profile
   × pattern is a matrix with no forbidden cell.
4. **No profile may touch Core, RBAC, lifecycle or audit.** A profile that changed any of those
   would be a business rule, not configuration, and would require an owner decision.
5. **Changing a profile is audited** (`tenant.profile_updated`, key name only — tenant spec §10.1).

A **network** (government directorate, NGO umbrella, outreach programme) is a **single responsible
tenant with branches**, never a tenant-of-tenants; a genuinely separate legal institution is a
separate tenant (O-SaaS-7 and the tenant spec §3.4 govern the human side of that split).

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
| `backend/common/auth.py` | existing, **extended** | kernel | principal resolution; add principal-type/`scope` check | `SPECIFIED` (additive) |
| `backend/common/permissions.py` | existing, **extended** | kernel | tenant RBAC map; add a **separate** platform permission map | `SPECIFIED` |
| `backend/common/lifecycle.py` | **new** | kernel | resolve tenant lifecycle state; `require_operational` / `require_write_access` dependencies | `SPECIFIED` |
| `backend/common/entitlements.py` | **new** | kernel | resolve effective modules + limits for an org, cached by version; `require_module(key)` | `SPECIFIED` |
| `backend/common/audit.py` | existing | kernel | append-only writer; extend action vocabulary (`subscription.*`, `tenant.*`, `platform.*`) | `OWNER-APPROVED` (BR §40) |
| `backend/common/denial_audit.py` | existing | kernel | unchanged; will automatically record lifecycle/entitlement denials (403) | `OWNER-APPROVED` (`.clinerules` §3) |
| `backend/platform/` | **new service** | platform | subscriber registry, plan catalogue, subscriptions, entitlement administration, tenant usage | `SPECIFIED` |
| `backend/identity/` | existing, **extended** | tenant | refresh/revoke/reset endpoints; environment-sourced secret | `SPECIFIED` |
| `backend/organization/` | existing, **restricted** | tenant | remove tenant self-service `status` write (R-03); keep profile/branch/hierarchy | `SPECIFIED` |
| `frontend/pages/platform/*` | **new** | platform | tenant list, plan editor, subscription assignment, usage | `SPECIFIED` |
| `frontend/pages/settings/*` | **new/extended** | tenant | "my plan", module visibility for org admins | `SPECIFIED` |
| `modules` / `plans` / `subscriptions` tables | **new** | platform (data) | §7.3 | `SPECIFIED` |
| Alembic chain | existing | data | **one** chain, head `f7d2b4c6e8a1` → new revisions appended | `SPECIFIED` |

### 3.3 Why a separate `backend/platform/` service rather than endpoints inside `organization`

| Criterion | Inside `organization` | Separate `platform` service |
|---|---|---|
| Token acceptance | mixed with tenant tokens in one app | own dependency: platform tokens only |
| Blast radius if misconfigured | tenant org API exposed | isolated |
| Audit surface | interleaved with tenant org events | one service, one action namespace |
| Deployment under the dedicated pattern (P2) | indistinguishable from tenant code | can be restricted per deployment |
| Extra cost | none | one more container (Compose already runs nine) |

`SPECIFIED` choice: separate service, published through the frontend rewrite layer like every
other service. No new third-party dependency is introduced.

### 3.4 Microservices remain the target architecture (A1 — `OWNER-APPROVED`)

The owner's direction is that **microservices stay the target architecture**. This document is
therefore not allowed to relabel the current shape as the destination, and no reader may conclude
that the platform has been redefined as a modular monolith.

Four compromises in this specification are **transitional, explicitly and only transitional**:

| Compromise | Why it is transitional | What must remain true meanwhile | Revisit when |
|---|---|---|---|
| One Postgres database for every service (ADR-SAAS-002) | the tree already works this way, and a database-per-service split is not an MVP-scale change | `organization_id` stays the only tenant key; no service reads another service's business tables at request time beyond the existing shared-model usage | a service needs an independent release or scaling profile |
| The shared `common/` kernel imported by all services | one enforcement point is a *safety* property; duplicating it in eight services would drift | the kernel stays small and boundary-respecting; it may read control data, never own business rules | a service moves to its own deployment and needs the gate over the network |
| The platform service writes into the same database as tenant services | no message bus exists (audit AR-3) | the platform never writes tenant business data (D-5); the write path is transactional and audited | a broker exists, or P2/P3 requires isolation |
| Next.js rewrites as the browser entry point | not a gateway, and the specification deliberately does not add one | authorization never depends on the rewrite layer | a gateway is justified by a measured need |

Rules:

1. **A transitional compromise may not be cited as the target**, in a report, a review or a slide.
   Each row above is a documented exception, not a design principle.
2. **No new coupling is introduced in the name of "it is one database anyway".** The compromise
   licenses what already exists, not further sharing.
3. **A1 does not authorise a refactor.** It fixes the direction so that incremental work does not
   foreclose it; the roadmap's phases remain the only implementation plan.

### 3.5 Lifecycle and entitlement ownership (A4 — `OWNER-APPROVED`)

| Ownership question | Owner ruling (2026-11-17) | Consequence in this document |
|---|---|---|
| Who is authoritative for lifecycle state and entitlements? | the **Platform Service** | it is the only writer of `lifecycle_state`, subscriptions and module grants (§7.4, tenant spec §3.3 T-3) |
| How do tenant services know? | **controlled, versioned distribution**, enforced **locally** | the kernel resolves from data stamped by `entitlements_version` (§8.1–§8.2); no per-request call to the platform |
| May a request wait on the platform? | **no synchronous platform RPC on the request path** | the platform may be down without denying tenant traffic (§8.3) |
| May the platform read tenant business data directly? | **no direct shared business-data access** | D-5; support access only through the consented, time-boxed grant (§9.3) |
| Are isolation, RBAC and entitlement one control? | **no — three separate controls** | §3.1 observation 3, §5.1 steps 6/8/9, audit K-1 |

One distinction makes A4 usable in practice, and it is a distinction of *data class*, not of table
ownership:

- **Commercial control data** — `plans`, `plan_modules`, `plan_limits`, `subscriptions`,
  `subscription_modules`, `modules`, and `organizations.lifecycle_state`. The platform owns the
  writes; every service may read it to enforce. This is the "controlled, versioned distribution".
- **Tenant business data** — patients, doctors, schedules, appointments, queue, clinical content,
  documents. The platform has **no** read path at all, granted or otherwise, except through the
  consented support grant, which is itself a tenant-plane authorisation.

Calling the kernel read "shared business-data access" would be a category error: the kernel reads
*commercial control data* about the tenant, never the tenant's clinical content. Conversely, the
platform's convenience of being in the same database is **not** permission to query across that line.

A4 additionally settles an ownership trap: because lifecycle is authoritative at the platform, a
tenant service must **never** compute a lifecycle answer from dates, plan rows or a token. It reads
the state (§8.2 "lifecycle is never cached"), which is exactly how the four-eyes suspension of
O-SaaS-14 becomes visible on the next request rather than after a cache expiry.

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
| API gateway | not introduced; Next.js rewrites remain the single browser entry | `SPECIFIED` (no change) |
| Service discovery | Compose DNS, unchanged | `SPECIFIED` (no change) |
| Message bus | not introduced; lifecycle transitions are transactional DB writes + audit rows | `SPECIFIED` |
| Expiry scheduler | **one** in-process scheduler inside the `platform` service guarded by a Postgres advisory lock, so replicas cannot double-fire | `SPECIFIED` (bounded by O-SaaS-3) |
| Notification delivery | reuse the existing `notifications` outbox; its worker is not deployed today (audit AR-3), so deploying it becomes a **Phase-4 prerequisite** for expiry warnings, not a SaaS blocker | `SPECIFIED` |
| Read replicas / sharding | not introduced | `DEFERRED` |

> The expiry job is the only time-driven behaviour in the whole SaaS layer. It is specified as
> **idempotent**: running it twice must produce the same state and exactly **one** audit row.
> It only acts when the stored state still matches its expected predecessor (compare-and-set),
> which is also the concurrency control for a platform admin suspending a tenant at the same
> moment.

### 4.3 Deployment patterns in practice

`OWNER-APPROVED` (A2, O-SaaS-6). Only **P1** ships in the MVP; **P2** and **P3** are recorded so
that P1 does not preclude them.

| Aspect | P1 Shared (MVP) | P2 Dedicated (long-term) | P3 Institution-controlled (long-term) |
|---|---|---|---|
| `AMSDP_DEPLOYMENT_MODE` | `shared` | `dedicated` | `institution` |
| Organizations per database | many | exactly one (enforced at provisioning) | exactly one (enforced at provisioning) |
| Platform plane | full tenant registry | restricted: single tenant, no cross-tenant surface | restricted, operated inside the institution's approved environment |
| Subscription source | platform-recorded subscription | institutional contract recorded on the platform; the local licence record mirrors it | as P2 |
| Commercial shape | plan / add-on configuration | contract, donor-funded or annual institutional licence (O-SaaS-6) — **not** monthly-assumed | as P2 |
| Data residency | operator's database | customer's infrastructure | institution's mandated hosting |
| Upgrade | one release, all tenants | customer-scheduled window, same migrations | customer-scheduled window, same migrations |
| Audit retention | operator policy | customer policy, same append-only rules | institution policy, same append-only rules |

The `AMSDP_DEPLOYMENT_MODE` values are `SPECIFIED` mechanism. Their only permitted effects are:
(a) refusing to create a second organization, (b) hiding multi-tenant platform screens, (c) refusing
cross-tenant admin actions. The value must **never** change authorisation logic — the same isolation
rules apply in every pattern, because a bug masked in P2 becomes a breach in P1.

Two boundaries keep P2/P3 from becoming forks:

1. **Same images, same migrations, same audit rules.** A pattern is configuration, not a branch.
2. **P2/P3 add no tenant column and no second identity plane.** Their single organization is a
   provisioning constraint, not a new tenancy model.

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
6  membership/scope   token org must still be a live, active membership of this identity;
                      path org must equal token org, else 404
7  lifecycle gate     state must permit this HTTP method (§5.3)
8  RBAC               require_permission(...) / platform permission, using the role held
                      in *this* membership (never a global role)
9  entitlement gate   require_module(key) for module-gated routes only
10 handler            performs the operation
11 audit              append event (success) — failure paths audited by denial middleware
```

Rules that make the order non-negotiable:

- **Step 6 is a membership check, not a "does this user belong to some organization" check**
  (O-SaaS-7). The token's organization must be one the identity holds a **live, active membership**
  in, and the *role* applied at step 8 is the role held **in that membership** — never a global role
  and never a role borrowed from another membership. A revoked or suspended membership must fail on
  the next request, not at the next token refresh, which is why the membership is re-read here in the
  same way the principal row is re-read at step 4.
- **Switching organization is an explicit, authorized act.** The active organization travels with the
  token; a switch must re-authorise the target organization and then issue a fresh token. A request
  may never name its own tenant in a header or a body (`.clinerules` §3). The transport choice is
  engineering question `EQ-2` (§14.3.1) — the requirement is only that no unverified tenant value is
  ever trusted.
- **Steps 6 before 7 before 9.** A lifecycle or entitlement check that runs before the membership
  and tenant-scope checks can leak existence information about another tenant; it must run *after*
  the caller's membership in the named tenant is verified.
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

Four notes:

1. **`grace` is not a penalty state.** BR §39 item 3 says operation continues during grace. A
   design that degrades service during grace would violate the approved default.
2. **`suspended` is full block, `read_only` is the expiry path.** BR §39 item 5 preserves read-only
   after grace; explicit suspension (BR §38) is a governance action for abuse/legal cases and
   is therefore stronger. `OWNER-APPROVED` 2026-11-17 as O-SaaS-3, with one addition that is now a
   control rather than an interpretation: **the automatic expiry action is capped at `read_only`** —
   the scheduler may never auto-suspend and may never delete. Suspension and closure are always
   human decisions, and each requires a second approver (O-SaaS-14, O-SaaS-16; §9.3).
3. **Public, unauthenticated endpoints are gated too.** `/api/v1/queue/display` and
   `/api/v1/track/{token}` resolve a tenant; they must consult the same lifecycle resolver, or
   a suspended tenant keeps broadcasting a live queue. Tracking returns 404 when the owning
   tenant is not `active`/`grace`/`read_only` (non-disclosing), the display returns a neutral
   message and no patient-identifying content.
4. **A state is a platform fact, never a tenant inference** (A4). The matrix binds because
   `lifecycle_state` is authoritative; a service that derives a state from `ends_at` or from a token
   is wrong even when it happens to agree. **`closed` is not a delete** — closure stops access and
   retains data by default; anonymisation or deletion requires legal approval (O-SaaS-16).

---

## 6. Module registry (capability model)

V2.5 §C is an `APPROVED` catalogue of 10 modules, and on 2026-11-17 the owner approved the **ten
machine keys below as the commercial vocabulary** (O-SaaS-4). The key set is therefore
`OWNER-APPROVED`; the last column is the evidence axis and stays honest — six of the ten have no
code in this tree.

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
2. **`core` cannot be disabled, sold or gated.** V2.5 §D: no optional module may disable or corrupt
   the Core workflows. Therefore `require_module("core")` is a no-op by construction and is never
   written; `core` is never a plan line item, never an add-on and never a limit (O-SaaS-4). Core is
   available to every tenant in every state that permits the method at all (§5.3).
3. **Dependencies are declarative, not implied.** Enabling `prescriptions` without
   `clinical_records` is a configuration **error**, rejected at write time with a validation
   message — never silently satisfied at request time.
4. **A module key is not a permission.** Purchasing `clinical_records` does not let a
   receptionist read notes (V2.5 §30.1/§30.2). Module entitlement and RBAC compose.
5. **Absent modules are neither "disabled by a flag" nor sellable.** A module with no code in this
   tree may not appear in an active plan and no route may reference `require_module` for it; it
   becomes sellable only in the phase that implements it (roadmap §5). Approving the vocabulary
   (O-SaaS-4) approved the **names**, not the features — six of the ten remain `ABSENT`
   (`NOT IMPLEMENTED`) and no document in this set may imply otherwise.

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
| `staff_users` (human identity), `login_attempts`, `organization_memberships` | tenant (identity) | — | `staff_users` is the **person**, not the tenant membership; `organization_memberships` carries the per-organization role, permissions and branch scope (O-SaaS-7 — shape `SPECIFIED`, `EQ-1`/`EQ-3`). The platform plane never authenticates a staff user |
| patients / doctors / schedules / appointments / queue / symptoms / tracking | tenant services | yes | platform plane: **no access** (D-5) |
| `audit_events` | tenant (audit service) | yes, per tenant | `OWNER-APPROVED` two-store rule (O-SaaS-2): every tenant-affecting event — including a platform operator's action on that tenant — is written **into the tenant's trail** with a **non-null `organization_id`**, so the tenant can see its own history without reading a platform table. `organization_id` is never made nullable (§9.4) |
| `modules`, `plans`, `plan_modules`, `plan_limits` | platform | read-only via kernel | global reference data, no tenant column |
| `subscriptions`, `subscription_modules`, `subscription_events` | platform | read via kernel | `organization_id NOT NULL` (D-6) |
| `platform_users` | platform | never | no org column: platform identity is not a tenant |
| `platform_audit_events` | platform | never | `OWNER-APPROVED` (O-SaaS-2; ADR-SAAS-009 resolved **to option A**). Platform-only events live here; a tenant-affecting event additionally lands in the tenant's trail, so no tenant ever depends on a platform table to read its own history |

Note on the identity rows: moving the human identity off the tenant column (multi-membership,
O-SaaS-7) is the one place where D-6 has to be re-examined rather than applied. D-6 continues to bind
every table that remains tenant-scoped — `organization_memberships` included — while the global
identity row stops being tenant-scoped by definition. Which physical shape achieves that is
engineering question `EQ-1` (§14.3.1); the owner decided the **model**, not the migration.

### 7.3 New tables (shape `OWNER-APPROVED`, columns `SPECIFIED`)

Column detail belongs to the subscription, tenant and IAM documents; this table fixes **shape and
ownership** so they cannot diverge.

| Table | Tenant column | Purpose | Key constraints |
|---|---|---|---|
| `modules` | — (global) | the 10 module keys of §6 | `key` PK; `dependencies` text[]/JSON; `status` |
| `plans` | — (global) | sellable configuration of modules + limits | `code` UNIQUE; `version` int; `status` ∈ draft/active/retired |
| `plan_modules` | — | which modules a plan includes | PK `(plan_id, module_key)` |
| `plan_limits` | — | `users` / `doctors` / `branches` / future keys | PK `(plan_id, limit_key)`; `limit_value` NULL = unlimited |
| `subscriptions` | **`organization_id` NOT NULL** | one tenant's commercial state | partial-UNIQUE on `organization_id` where state is current; `plan_id`; `starts_at`, `ends_at`, `grace_ends_at`; `lifecycle_state` mirror is **not** stored here (§7.4) |
| `subscription_modules` | `organization_id` NOT NULL | purchased add-ons beyond the plan | PK `(subscription_id, module_key)`; `source` ∈ plan/addon; `state` per V2.5 §30.4; `branch_scope` JSON NULL = all branches |
| `subscription_events` | `organization_id` NOT NULL | append-only commercial history | `event_type`, `from_state`, `to_state`, `actor_type`, `actor_id`, `reason` |
| `platform_users` | **none** | platform identities, structurally separate from staff identity | `username` UNIQUE; `role` ∈ platform_admin/platform_ops/platform_viewer. The roles are **separate responsibilities** (O-SaaS-8): no account holds two by default, and a deliberate multi-role grant is an explicit, audited policy decision — never a convenience |
| `platform_audit_events` | **none** | platform-only events (no tenant) | O-SaaS-2: append-only, no `organization_id`; a tenant-affecting action is **also** written to that tenant's `audit_events` with a non-null `organization_id` |
| `organization_memberships` | `organization_id` NOT NULL | one identity's membership in one tenant, carrying that tenant's role and branch scope | UNIQUE `(staff_user_id, organization_id)`; `role`, `branch_scope`, `status`; columns `SPECIFIED` (`EQ-1`, `EQ-3`). Not a second tenant key — the join that makes one human usable in several tenants (O-SaaS-7) |

### 7.4 Changes to `organizations`

| Change | Detail | Status |
|---|---|---|
| **New `lifecycle_state` column** | `String(20)`, NOT NULL, server default `'active'`; values `active`/`grace`/`read_only`/`suspended`/`closed`; index for the expiry job. **Authoritative** (O-SaaS-5) and written only by the platform plane (A4, T-3) | **`OWNER-APPROVED`** (O-SaaS-3, O-SaaS-5; ADR-SAAS-005) — column shape `SPECIFIED` |
| `status` | retained as **transitional**: no longer authoritative, the tenant PATCH stops accepting it (R-03), and retirement is a later controlled migration rather than part of this phase (O-SaaS-5) | **`OWNER-APPROVED`** (transitional), retirement `DEFERRED` |
| `entitlements_version` | `Integer`, NOT NULL, default `1`; incremented on any change to plan, modules or lifecycle-relevant limits; the cache key | `SPECIFIED` |
| commercial metadata | `billing_contact_name`, `billing_contact_email`, `billing_contact_phone`, `contract_reference`, `reseller_code` — all nullable, all platform-writable only | `OWNER-APPROVED` as **non-enforcement configuration** (O-SaaS-6): they describe an institution-shaped arrangement, they never gate a request, and no monthly billing cycle is assumed. Columns `SPECIFIED` |
| organization profile | `config.profile` ∈ `private`/`government`/`ngo`/`community`/`outreach` (A3, §2.2) — a whitelisted config key, not a column and not a tenant discriminator | `OWNER-APPROVED` as configuration; key name `SPECIFIED` |

Why a **new** column rather than reinterpreting `organizations.status`: existing rows may hold
values written under the old, unenforced semantics. Reinterpreting them silently would either
lock tenants out (if unknown → `suspended`) or fail open (if unknown → `active`). A new column
with an explicit, audited backfill is the only option that is both safe and reviewable. The
cost is one transitional duplicate field, retired in a later revision. This trade-off is
recorded in ADR-SAAS-005 so the owner can reject it with full information.

**The owner has since accepted it** (O-SaaS-3, O-SaaS-5) and added a constraint this section implies
but did not state: the backfill is `active` **only** for rows whose existing value is known and
validated. A legacy `status='inactive'` is **never auto-mapped** (O-SaaS-9) — it is preserved as-is
and reaches `lifecycle_state` only through a reviewed list (tenant spec §12.1). Guessing would turn
an unknown into a governance action nobody approved.

### 7.5 Migration policy

1. One revision per concern, named `add_<topic>`, `down_revision = <current head>`.
2. Each revision must be re-runnable on a database that already contains the change (guard on
   `inspector`/`IF NOT EXISTS`), per `.clinerules` §3.
3. Data backfill (every organization whose existing status is known and validated →
   `lifecycle_state='active'`, `entitlements_version=1`) is in the same revision as the column.
   Legacy `status='inactive'` rows are **not** auto-mapped (O-SaaS-9): they are left untouched and
   listed for review.
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
# backend/common/entitlements.py  — SPECIFIED shape
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

A4 (`OWNER-APPROVED`) turns that shape from a preference into a **requirement**: the platform is
authoritative for lifecycle and entitlement, tenant services enforce **locally** from a controlled,
versioned distribution, and there is **no synchronous platform RPC on the request path**.
`entitlements_version` is that distribution's version stamp. Two drifts A4 rules out that this sketch
could otherwise invite:

1. a fallback like "if the platform is unreachable, allow" — resolution is local, so there is
   nothing to fall back *to*; a local resolution failure is `503` (§5.2), never `allow`;
2. a "refresh from the platform on cache miss" call — the miss is answered from the database, and
   the version bump belongs to the writer, inside its own transaction.

### 8.2 Cache contract

| Aspect | Rule | Status |
|---|---|---|
| What is cached | the resolved `Entitlement` object only | `SPECIFIED` |
| Key | `(organization_id, entitlements_version)` | `SPECIFIED` |
| Invalidation | **version bump** on any plan/add-on/lifecycle change, inside the writing transaction; the writer also evicts the key in its own process | `SPECIFIED` |
| TTL | 60 s safety net (bounds staleness if an eviction is lost across processes) | `SPECIFIED` |
| Size bound | LRU, 5 000 organizations per worker, then TTL-managed | `SPECIFIED` |
| Lifecycle state | **never cached.** It is one primary-key read and must react immediately to a suspension | `SPECIFIED` |
| Failure | resolution exception → `503`, never "allow" (§5.2) | `SPECIFIED` |

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
| T-7 | Audit trail shows nothing for platform actions | **Decided** (O-SaaS-2): platform-only events go to `platform_audit_events`, and every tenant-affecting action is written to that tenant's `audit_events` with a **non-null `organization_id`**, so the tenant's own trail is complete without reading a platform table | cross-store consistency of the second write (`EQ-4`); no longer a coverage risk |
| T-8 | Audit tampering | append-only writer, no update/delete surface, no admin endpoint | DB-superuser tampering (out of scope) |
| T-9 | Suspended tenant keeps broadcasting a public queue | lifecycle gate on public endpoints (§5.3 note 3) | none accepted |
| T-10 | Expiry fires early/late due to local time | all timestamps `timestamptz`, UTC; grace boundaries computed server-side only | clock skew between hosts (bounded by NTP) |
| T-11 | Tenant is denied service by a broken platform deploy | kernel reads data, not the platform service (§8.1) | platform UI outage only |
| T-12 | A support session becomes routine access | support access requires **explicit `org_admin` consent for every grant** — no pre-approval and no standing consent, including for `grace` tenants (O-SaaS-13) — and is time-boxed, reasoned, audited and visible to the tenant (§9.4) | none accepted |
| T-13 | One operator suspends or closes a tenant, maliciously or by mistake | the two states that remove a tenant's access outright each require **a second approver** (O-SaaS-14, O-SaaS-16), a mandatory reason, an audit row and a tenant-visible event (§9.4); the automatic expiry path cannot reach either state (O-SaaS-3) | collusion between the two approvers (out of scope, as T-8) |

### 9.3 Platform operator access rules

1. **No impersonation in V1.** A platform operator cannot obtain a tenant token. If a support
   case requires seeing tenant content, the tenant admin grants a scoped, time-limited
   entitlement; the grant is a normal audited tenant action. **O-SaaS-13 makes the consent
   explicit and per-grant**: there is no pre-approval, no standing consent and no special case for
   a `grace` tenant — a support grant that an `org_admin` did not request or approve for that
   specific window does not exist.
2. **Every platform write carries a reason string** (free text, mandatory, min length) stored
   in `subscription_events.reason` and in the audit payload. The reason is **written for the tenant
   to read** (§9.4): internal-only context belongs outside the audit trail.
3. **Reads are audited too** when they are cross-tenant metadata listings (who looked at the
   subscriber registry matters).
4. **Separate responsibilities, decided** (O-SaaS-8). `platform_admin` writes commercial state;
   `platform_ops` may read and may not change plans or lifecycle; `platform_viewer` reads only.
   Holding more than one role is **not** a deployment convenience: it is an explicit policy
   decision that must be recorded and audited, and the default posture is one role per account.
5. **Suspension and closure are four-eyes actions** (O-SaaS-14, O-SaaS-16). Neither may be executed
   by a single operator, including the one who requested it: a second, independently authenticated
   platform operator approves, **both** identities are recorded, and the tenant sees one decided
   event naming both. A rejected or withdrawn approval is audited as a denial — never dropped
   (`.clinerules` §3).
6. **No single-operator override is specified.** An emergency path that lets one operator bypass
   rule 5 would remove the control precisely in the case it exists for; if such a path is ever
   required it needs an owner decision and is tracked as `EQ-7` (§14.3.1).
7. **Operator MFA is a production precondition, not a deferral** (O-SaaS-15). Password-only platform
   authentication is permitted **only** inside a temporary, explicitly documented hackathon
   exception, restricted to a limited and named authorised operator group. MFA must be enforced for
   every platform operator account **before production platform access is granted**; the exception
   does not travel into production, does not satisfy the requirement, and is retired at that gate.
   No mechanism, provider or enrolment flow is selected here — see IAM §13.2 for the three contexts
   (hackathon / production launch / post-launch) and roadmap §9.6 for the gate. Operator MFA is
   `NOT IMPLEMENTED`.

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
| suspend/close approval requested, granted or rejected | `tenant.lifecycle_approval_decided` | yes |
| platform read of tenant metadata | `platform.metadata_viewed` | no |

The actor is recorded as the platform principal (`actor_type='platform'`, `actor_id`), never as
a tenant user, so an event is always attributable to the plane that caused it.

**O-SaaS-10 decides what the tenant is shown.** The tenant-facing view of a platform action names
the **operator identity together with that operator's platform role** — enough to hold a named human
accountable and no more:

| Shown to the tenant | Deliberately not shown |
|---|---|
| operator display name or username, platform role, the action, its timestamp, its reason, and for a suspension or closure the **approving** operator as well | operator email address or phone number, session identifiers, IP address, internal notes, other tenants' data |

Naming the operator is a transparency requirement, not a personal-data licence: the platform stores
the minimum needed for attribution, and no field from the "not shown" column may be added to the
tenant projection without a new owner decision.

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
| Database-per-tenant or sharding | ADR-SAAS-002: one DB, tenant key. The dedicated pattern (P2) is a separate *deployment*, not a runtime feature |
| Multi-region, read replicas, horizontal autoscaling | Firmly deferred; current scale does not need it |
| SSO / SAML / OIDC federation (enterprise identity federation, tenant and platform) | Legitimate enterprise requirement, explicitly `DEFERRED` to the IAM spec's roadmap section. This architecture must not *prevent* it (principal model is claim-based) but does not deliver it. **Operator MFA is not part of this non-goal:** O-SaaS-15 makes a second factor a precondition of production platform access (§9.3 rule 7; IAM §13.2; roadmap §9.6) — only the *enterprise federation* of identities is deferred |
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
rejected alternatives. **`OWNER-APPROVED`** = the Product Owner decided it, here or in the
2026-11-17 packet (§1.5). **`SPECIFIED`** = this specification's mechanism, engineering-owned, not
built. **`OPEN`** = a genuine owner decision this document cannot make. **`SUPERSEDED`** = replaced,
kept verbatim for traceability.

On 2026-11-17 the owner closed **every** `OPEN` item in this register. Any status below still
reading `OPEN` is a defect in this revision, not a live question.

| ID | Decision | Rejected alternatives | Status |
|---|---|---|---|
| **ADR-SAAS-001** | "Hybrid SaaS" means one codebase, one database and one deployment shape that can be sold to many organizations, with an optional single-tenant deployment for customers who require it; the commercial plane is configuration on top of the existing tenant plane (§2) | (a) build a separate SaaS control app; (b) stay single-tenant with manual licences; (c) full microservice split with billing | **`OWNER-APPROVED`** (owner direction: *Hybrid SaaS only*; traceability label `ACCEPTED`) — §2 |
| **ADR-SAAS-002** | One Postgres database, `organization_id` as the only tenant key, one linear Alembic chain | (a) database-per-tenant; (b) schema-per-tenant; (c) a second "commercial" database | **`OWNER-APPROVED`** for the tenancy rule and the single chain (`.clinerules` §3; audit C-1). The **one-database topology is `TRANSITIONAL`** under A1 (§3.4) — it is not the target architecture |
| **ADR-SAAS-003** | Platform identity is a **separate principal domain** (`platform_users`, own token `scope`, own role map), not a tenant-scoped `super_admin` | (a) keep `super_admin` as a platform role inside a tenant; (b) a magic env-var operator account; (c) reuse `staff_users` with a flag | **`OWNER-APPROVED`** (O-SaaS-1; closes audit R-06, C-9). Two constraints travel with the approval: the legacy `super_admin` **alias and its `platform.*` grants are not removed until the replacement is tested**, and the tenant role is renamed by controlled migration (audit C-4), never dropped |
| **ADR-SAAS-004** | The platform plane ships as a **new `backend/platform/` service**, not as extra endpoints in `organization` | (a) extend `organization`; (b) a standalone non-Python service; (c) CLI-only administration | `SPECIFIED` (§3.3) |
| **ADR-SAAS-005** | Lifecycle lives in a **new** `organizations.lifecycle_state` column with five states; `grace` preserves full operation; `suspended` is a full block; `read_only` is the expiry outcome | (a) reinterpret existing `organizations.status`; (b) a state column on `subscriptions`; (c) derive state from dates at request time | **`OWNER-APPROVED`** (O-SaaS-3, O-SaaS-5) — states, semantics and the "expiry caps at `read_only`" rule decided; column shape `SPECIFIED` (§5.3, §7.4) |
| **ADR-SAAS-006** | Entitlements are resolved **in the kernel from data**, never by an RPC/ licence-server call | (a) call the platform service per request; (b) embed entitlements in the JWT; (c) Redis-backed central resolver | **`OWNER-APPROVED` as principle (A4)** — platform authoritative, local enforcement from a versioned distribution; the kernel mechanism and version stamp are `SPECIFIED` (§8.1) |
| **ADR-SAAS-007** | Module keys are fixed now (10 keys, §6) and gating applies **only** to optional-module routes; Core is never gated | (a) invent keys per module as built; (b) gate all routes uniformly; (c) plan-level feature strings without a registry | **`OWNER-APPROVED` keys (O-SaaS-4)**; gating mechanism `SPECIFIED` (§6) |
| **ADR-SAAS-008** | The platform **records** commercial state; it does not take payments | (a) integrate a gateway now; (b) store card data (never) | **`OWNER-APPROVED`** (V2.5 §21/§30.3; traceability label `ACCEPTED`) |
| **ADR-SAAS-009** | Platform-scope audit: either (A) write tenant-affecting actions into `audit_events` with `organization_id` plus a separate `platform_audit_events` for non-tenant actions, or (B) make `audit_events.organization_id` nullable | (a) leave platform actions unlogged; (b) a log file as the record | **`OWNER-APPROVED` — option (A)** (O-SaaS-2; closes audit C-7). `organization_id` stays `NOT NULL` |
| **ADR-SAAS-010** | Enforcement is an **ordered pipeline in the shared kernel** (§5.1); the frontend is never authoritative | (a) per-service checks; (b) middleware-only enforcement without a dependency; (c) frontend gating | `SPECIFIED` (§5) |
| **ADR-SAAS-011** | Expiry runs as **one** in-process scheduler with a Postgres advisory lock and compare-and-set transitions (idempotent) | (a) Celery/cron container; (b) per-request lazy expiry evaluation; (c) external scheduler | `SPECIFIED` mechanism (§4.2); the owner-approved **constraint on it** is O-SaaS-3 — the job may never move a tenant beyond `read_only` |
| **ADR-SAAS-012** | Deployment pattern via `AMSDP_DEPLOYMENT_MODE` with exactly three permitted effects | (a) a separate codebase per pattern; (b) no dedicated support at all; (c) compile-time fork | **`OWNER-APPROVED`** (A2, O-SaaS-6) — three customer patterns; `dedicated` and institution-controlled are **long-term, not MVP** |
| **ADR-SAAS-013** | Staff membership: one organization per staff identity (no cross-org membership within one deployment); a "membership" concept is therefore deferred | (a) join table `staff_organizations`; (b) email shared across orgs; (c) cross-org impersonation | **`SUPERSEDED`** by ADR-SAAS-014 (O-SaaS-7, 2026-11-17). Kept verbatim for traceability; not current guidance |
| **ADR-SAAS-014** | **Multi-membership replaces one-organization-per-identity.** One human identity holds memberships in one or more organizations; each membership carries its own role, permissions and branch scope. The token names exactly **one active organization**, and switching is an explicit re-authorisation followed by a fresh token | (a) keep one organization per identity (former ADR-013); (b) trust an organization header or body from the client; (c) cross-org impersonation; (d) a tenant-selector cookie with no authorization | **`OWNER-APPROVED`** (O-SaaS-7) — model decided; physical shape `SPECIFIED` (`EQ-1`, `EQ-2`, `EQ-3`) |

### 12.1 Why ADR-SAAS-013 was open, how O-SaaS-7 settled it, and what stays true

The original reasoning is preserved verbatim, because it is still why the replacement model is
specified so conservatively:

> Today `staff_users.organization_id` is `NOT NULL` and the token carries exactly one org; the
> tenant isolation model (audit §6, the strongest existing asset) depends on that. Supporting a
> staff member in two organizations would mean a principal with a selectable tenant, which is
> precisely the shape most multi-tenant breaches take. It is cheaper to keep one-org-per-identity
> and provision a second identity than to weaken the invariant — but that is a product decision
> about clinician workflows, so it stays `OPEN`.

**O-SaaS-7 (2026-11-17) decided the product question**: a clinician working at two institutions must
not need two accounts. ADR-SAAS-014 replaces ADR-SAAS-013, and the security concern above is
answered by design rather than dismissed:

| The concern | How the replacement answers it |
|---|---|
| "a principal with a selectable tenant" | selection is **authorized, not free**: a switch re-checks the target membership and mints a new token; no request may name its own tenant (`.clinerules` §3) |
| "isolation depends on one org per identity" | it never did — isolation depends on `organization_id` having a verified source. The source becomes "the membership the token names, re-verified per request" (§5.1 step 6) |
| "cheaper to provision a second identity" | still permitted: one membership per identity remains a legal configuration, and a single-tenant deployment (P2/P3) always looks like it |
| "audit must stay attributable" | every row still carries exactly one `organization_id`; the actor is the human identity and the membership determines the role used (§9.4) |

Two invariants O-SaaS-7 does **not** change, and that no later revision may soften:
`organization_id` remains the only tenant key (D-1), and a cross-tenant read still fails `404`
(§5.2). The **audit's original finding** — that today's code assumes one organization per staff
identity — stays true of the code until the migration lands, and the audit document still says so.

### 12.2 The three directions recorded as ADRs

| ID | Decision | Rejected alternatives | Status |
|---|---|---|---|
| **ADR-SAAS-015** | **Healthcare organization profiles** (`private`, `government`, `ngo`, `community`, `outreach`) are presets in whitelisted tenant configuration — never a discriminator that changes isolation, authorisation or entitlement | (a) an `organization_type` column driving behaviour; (b) a separate product edition per sector; (c) per-profile permission sets | **`OWNER-APPROVED`** (A3); key name `SPECIFIED` (§2.2) |
| **ADR-SAAS-016** | The **Platform Service is authoritative** for lifecycle and entitlement; tenant services enforce **locally** from a controlled, versioned distribution; **no** synchronous platform RPC on the request path; **no** direct platform access to tenant business data; isolation, RBAC and entitlement stay three separate controls | (a) per-request licence check; (b) entitlements in the token; (c) the platform querying tenant business tables for reporting | **`OWNER-APPROVED`** (A4) — §3.5, §8.1 |
| **ADR-SAAS-017** | **Microservices remain the target architecture.** The single database, the shared kernel, the platform sharing that database and the Next.js rewrites are **transitional compromises**, documented as such, never the destination | (a) declare the current shape the target ("modular monolith"); (b) full service split now; (c) add a gateway now | **`OWNER-APPROVED`** (A1) as direction; each compromise `SPECIFIED` as transitional (§3.4) |

---

## 13. Traceability to approved requirements

Every claim in this document traces to an `APPROVED` source or to verified evidence in the
audit. Nothing here is invented product intent.

| Approved requirement | Source | Where this set satisfies it | Status |
|---|---|---|---|
| Organizations subscribe to the platform | BR §37 | §2 axis A; subscription spec §3–§4 | `OWNER-APPROVED` (O-SaaS-3/6); mechanism `SPECIFIED` |
| Super Admin controls entitlement dimensions | BR §38 | plan/limit model §7.3; subscription spec §4, §7 | `OWNER-APPROVED` (O-SaaS-4, O-SaaS-8); mechanism `SPECIFIED` |
| Grace period, then suspended writes, then read-only | BR §39 | lifecycle matrix §5.3; tenant spec §5 | `OWNER-APPROVED` (O-SaaS-3), with the added cap: expiry never goes beyond `read_only` |
| No tenant data deletion on non-payment | BR §39 | tenant spec §11; §5.3 note 4 | `OWNER-APPROVED` (O-SaaS-16: retained by default); mechanism `SPECIFIED` |
| Commercial and access events audited | BR §40 | §9.4; subscription spec §9 | `OWNER-APPROVED` (O-SaaS-2, O-SaaS-10); mechanism `SPECIFIED` |
| Secrets never hardcoded | BR §42 | §9.5; IAM spec §5.2 | requirement `APPROVED`; **`IMPLEMENTED`** but **not `VERIFIED`** — the `AMSDP_ENV` guard currently fails open (audit R-10, C-8) |
| Ten-module catalogue | V2.5 §C | module registry §6 | keys `OWNER-APPROVED` (O-SaaS-4); 6 of 10 `NOT IMPLEMENTED` |
| Module dependencies | V2.5 §C.1 | §6.1 rule 3 | `OWNER-APPROVED` as a rule; enforcement `SPECIFIED` |
| Core never disabled by a module decision | V2.5 §D | §5.1, §6.1 rule 2, §10, §11.2 | `OWNER-APPROVED` (O-SaaS-4); mechanism `SPECIFIED` |
| No routine cross-tenant operator access | V2.5 §5.1 | §9.3, §9.4 | `OWNER-APPROVED` (O-SaaS-13); mechanism `SPECIFIED` |
| Platform roles and permission separation | V2.5 §19.1–19.3 | IAM spec §7, §9.3 | `OWNER-APPROVED` (O-SaaS-8, O-SaaS-14); mechanism `SPECIFIED` |
| SaaS readiness without payment integration | V2.5 §21 | ADR-SAAS-008, §10 | `OWNER-APPROVED` (V2.5 §21; traceability label `ACCEPTED`) |
| Module visibility / entitlement / state model | V2.5 §30.1–30.4 | §5, §6, subscription spec §5–§6 | `OWNER-APPROVED` (O-SaaS-3/4/5); mechanism `SPECIFIED` |
| Append-only audit; no secret in logs; server-side authorisation; `404` on cross-tenant | `.clinerules` §3 | §7.1, §5.2, §9 | `OWNER-APPROVED` as invariants (governance); evidence: **`IMPLEMENTED`** for existing paths, new SaaS paths `NOT IMPLEMENTED` |
| Single tenant key, single migration chain | `.clinerules` §3; audit §3 | §7.1 D-1/D-2 | `OWNER-APPROVED` for D-1 and the chain; topology `TRANSITIONAL` (A1, §3.4) |
| Multi-membership identity model | **O-SaaS-7** (owner, 2026-11-17) | ADR-SAAS-014; §7.2; IAM spec §8 | `OWNER-APPROVED`; mechanism `SPECIFIED`, `EQ-1…3` |
| Three customer deployment patterns; dedicated is long-term | **A2**, O-SaaS-6 | §2 axis B, §4.3 | `OWNER-APPROVED`; P2/P3 `NOT IMPLEMENTED` |
| Healthcare organization profiles | **A3** | §2.2, ADR-SAAS-015 | `OWNER-APPROVED` as configuration; key `SPECIFIED` |
| Platform authoritative, local enforcement | **A4** | §3.5, §8.1, ADR-SAAS-016 | `OWNER-APPROVED`; mechanism `SPECIFIED` |
| Microservices remain the target | **A1** | §3.4, ADR-SAAS-017 | `OWNER-APPROVED` as direction; compromises documented as transitional |

Three honest notes on status:

- **`OWNER-APPROVED` is not an implementation claim.** It says who decided the *requirement or the
  model*; it never says the *mechanism* exists. Every mechanism here is `SPECIFIED` and unbuilt, and
  the evidence axis — `NOT IMPLEMENTED` / `IMPLEMENTED` / `TESTED` / `VERIFIED` — is where the truth
  about code lives (`.clinerules` §7).
- **`SPECIFIED` is not a downgrade of intent.** The product requirements are `APPROVED` and the
  model questions are now `OWNER-APPROVED`; what remains specified is the *mechanism*.
- **`ACCEPTED` is reserved for decisions the approved documents already force** (ADR-001,
  ADR-002's tenancy rule, ADR-008). Nothing in the mechanism is claimed as approved-and-working
  while it is unbuilt — the evidence standard (`.clinerules` §7) forbids that.

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
2. **No code, schema or migration was written**, by design. Every normative mechanism is
   `SPECIFIED` and unbuilt. Revision 2 records the owner's decisions as `OWNER-APPROVED`; recording
   a decision is not implementing it, and no claim in this document moves to `IMPLEMENTED`,
   `TESTED` or `VERIFIED` on the strength of a decision.

### 14.3 Open items — the canonical registry for the whole six-document set

**This table is the single `O-SaaS` registry.** Every sibling document cites these ids and mints no
local ones; if a new question appears, it is added here and cited by id elsewhere. Renumbering is a
defect, not a fix — the ids are referenced from three other documents.

**All sixteen items were decided by the Product Owner on 2026-11-17.** The `Question` column is
preserved **verbatim** as the record of what was asked; the `Ruling` column records the answer. Where
a ruling leaves an *implementation* choice open, that choice is an engineering question in §14.3.1 —
it never reopens the owner's decision. The four directions A1–A4 are recorded in §1.5 and as
ADR-SAAS-002/014–017.

| ID | Question (as asked, verbatim) | Ruling (2026-11-17) | Follow-through |
|---|---|---|---|
| O-SaaS-1 | Approve ADR-SAAS-003 (separate platform identity) and the fate of today's tenant-scoped `super_admin`, including R-3 removal of the alias and its `platform.*` grants | **Approved.** Separate platform identity. The legacy alias and its `platform.*` grants are kept until the replacement is tested, then removed; the tenant role is renamed by controlled migration, never dropped | ADR-SAAS-003; IAM §7.4 |
| O-SaaS-2 | Resolve ADR-SAAS-009 (platform audit shape) — the tenant audit table's `organization_id` is `NOT NULL` | **Option A.** Platform-only events → `platform_audit_events`; tenant-affecting events → the tenant's `audit_events` with a real `organization_id`. The column is **not** made nullable | ADR-SAAS-009; §7.2, §7.3, §9.4 |
| O-SaaS-3 | Confirm the five-state lifecycle vocabulary and the grace/read-only/suspended interpretations of BR §39 | **Confirmed**, plus one addition: automatic expiry is capped at `read_only` — the job never auto-suspends and never deletes | ADR-SAAS-005; §5.3 |
| O-SaaS-4 | Confirm the ten module keys (§6) as the commercial vocabulary | **Confirmed.** Core is always available and is never sold, gated or disabled; a module absent from the catalogue is not sellable | ADR-SAAS-007; §6, §10 |
| O-SaaS-5 | Approve ADR-SAAS-005 transitional duplicate column (`lifecycle_state` beside `status`) | **Approved.** `lifecycle_state` is authoritative, `status` is transitional, and its retirement is deferred with a stated precondition | ADR-SAAS-005; §7.4 |
| O-SaaS-6 | Is B2 dedicated deployment in MVP scope (ADR-SAAS-012), and what is the licence/renewal mechanism there? | **Not in MVP.** Dedicated SaaS and institution-controlled deployment are long-term directions. Commercial arrangements in this market are institution-shaped, not monthly-subscription-shaped, so the licence/renewal mechanism stays `SPECIFIED` and is not designed now | ADR-SAAS-012; §2, §4.3, `EQ-6` |
| O-SaaS-7 | Is one organization per staff identity acceptable (ADR-SAAS-013) — i.e. two accounts for a multi-site clinician? | **Rejected — multi-membership adopted.** One identity, several memberships, one active organization per token, switching is an explicit re-authorisation. ADR-SAAS-013 is superseded | ADR-SAAS-014; §7.2; IAM §8; `EQ-1…3` |
| O-SaaS-8 | Should `platform_admin` and `platform_ops` be separable accounts by policy? | **Yes.** Separation of responsibility is the default; an operator holding both is an explicit, individually approved and audited exception | ADR-SAAS-003; §9.3 |
| O-SaaS-9 | Migration mapping for legacy `organizations.status='inactive'`: leave as `lifecycle_state='active'`, or map to `closed`/`suspended`? | **Preserve, never auto-map.** No legacy `inactive` row is mapped automatically; only a validated, reviewed backfill to `active` is permitted | §7.4; tenant spec §12.1 |
| O-SaaS-10 | In a tenant's own audit view, is a platform operator shown by role only, or by a named identity? | **Named operator identity plus platform role.** No personal data beyond what the tenant needs to identify the actor | §9.4 |
| O-SaaS-11 | Are `staff_password_history` reuse checks launch-scope or post-launch? | **Post-launch.** Recorded as `DEFERRED` with the risk accepted | IAM §4.6, §13.1 |
| O-SaaS-12 | May the operator-assisted reset response return the code to the requesting administrator (V1 assumes yes)? | **Yes**, under the stated constraints: authenticated operator, audited request, one-time code, no logging of the code | IAM §6.2 |
| O-SaaS-13 | Support-grant acceptance: explicit `org_admin` consent, or policy pre-approval for `grace` tenants? | **Explicit `org_admin` consent for every grant.** No policy pre-approval, including for `grace` tenants — `grace` is normal operation, so it grants no extra operator power | §9.3; IAM §7.3 |
| O-SaaS-14 | May `platform_ops` suspend a tenant without a second operator (four-eyes)? | **No.** Suspension requires a second approver, exactly like closure — the two irreversible, customer-visible actions share the control | §9.3; tenant spec §5.2 |
| O-SaaS-15 | *(verbatim question, 2026-11-17 — superseded by the ruling in the next column)* MFA for platform operators is `DEFERRED`; accept the resulting risk for MVP launch? | **Required before production launch — not deferred.** MFA must be enforced for every platform operator account before production access; the hackathon MVP may use a **temporary exception**, explicitly documented as a security risk and restricted to a limited authorised operator group. The exception does not satisfy the production requirement, and MFA is not a post-launch enhancement | §9.3 rule 7; IAM §13.2; roadmap §9.6 |
| O-SaaS-16 | Who may close a tenant, and does closure anonymise clinical data or retain it (BR §39 vs legal review)? | **Platform administrator approval plus a second approver.** Data is **retained by default**; anonymisation or deletion happens only on legal approval, as a separate, audited act. `closed` ≠ deleted | §9.3; tenant spec §11 |

### 14.3.1 Engineering questions (mechanism only — not owner decisions)

These are the choices the owner's rulings deliberately left to engineering. **None of them may be
answered by weakening a ruling above, and none of them blocks Phase 1 except where stated.** They are
tracked here so the sibling documents cite one id space rather than inventing local ones.

| ID | Question | Constraint it must satisfy (non-negotiable) | Answering role | Blocks |
|---|---|---|---|---|
| `EQ-1` | Physical shape of multi-membership: how `staff_users.organization_id` is retired — new `organization_memberships` join, backfill of one membership per existing identity, and the point at which the identity row stops carrying a tenant column | no data loss; forward-only idempotent migration; `organization_id` stays the only tenant key (D-1); every existing login keeps working throughout; the audit trail is never rewritten | Engineering owner (with owner sign-off on the cutover migration only) | Phase 2 migration |
| `EQ-2` | Transport of the active organization: claim in the token plus a dedicated switch endpoint and token re-issue, versus a short-lived per-request exchange | a request may never name its own tenant; a revoked membership fails on the next request, not the next refresh; no tenant value is ever read from a header or body | Engineering owner | Phase 2 |
| `EQ-3` | Membership lifecycle detail: invitation/acceptance, revocation and suspension semantics, and how a per-membership `role` + `branch_scope` produces effective permissions when one identity holds several memberships | least privilege per tenant; the role applied is the one held in the named membership, never a union across memberships; every membership change is audited in the affected tenant's trail | Engineering owner | Phase 2 |
| `EQ-4` | Cross-store consistency of the second audit write: a tenant-affecting platform action must reach both `platform_audit_events` and the tenant's `audit_events` — one transaction while they share a database, an outbox with retry once A1 separates them | no tenant-affecting action may exist without a tenant-side row; neither write may be rewritten or back-filled silently; a failed second write is an alert, not a dropped event | Engineering owner | Phase 2 (single-database form); A1 split |
| `EQ-5` | Entitlement distribution mechanics: the version stamp, how a tenant learns of a new `entitlements_version`, the permitted staleness bound, and what a tenant does when its distribution is older than the bound | enforcement stays local with no synchronous platform RPC (A4); stale data fails closed on **optional-module** routes only and can never switch off Core; every rejected request is audited | Engineering owner | Phase 2 |
| `EQ-6` | Licence and renewal mechanism for dedicated / institution-controlled deployment — deliberately **not designed** in this revision | it may not leak into P1 behaviour, and it may not turn the platform into a request-path dependency (A4) | Engineering owner, after the owner scopes P2/P3 | post-MVP (P2/P3) |
| `EQ-7` | Whether a documented single-operator emergency override for suspension/closure should exist at all | it would weaken the four-eyes control exactly where it matters; if ever required it needs **an owner decision**, not an engineering one, and must be time-boxed, reasoned and audited with both identities recorded | **Product Owner** (this one is not engineering) | nothing today |
| `EQ-8` | Retirement precondition for the transitional `organizations.status` column (O-SaaS-5 approved the duplicate; the removal needs a trigger) | `lifecycle_state` must be authoritative and read by every path first; no compatibility read may survive removal; the removal ships only after the transitional read path has been `TESTED` and `VERIFIED` | Engineering owner | Phase 2+ |

`EQ-5` and `EQ-4` are the only two that can silently become security defects if left unanswered past
Phase 2, because both decide what happens when the platform and the tenant disagree. Neither may be
resolved by "check with the platform" — that is the design A4 forbids.

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
| No unverified capability claims | every mechanism labelled `SPECIFIED`; decisions labelled `OWNER-APPROVED` and kept on a separate axis from evidence; §13 notes; §14.1 |
| Owner decisions recorded, not invented | §1.5 (O-SaaS-1…16, A1–A4) and §12 (ADRs), with `SUPERSEDED` records kept verbatim rather than deleted |
| One tenant key, still | §7.1 D-1, §7.2 note on D-6, §12.2 — `organization_memberships` is a join, not a second tenant column |
| Production preconditions are not presented as optional | §9.3 rule 7 — O-SaaS-15 separates a documented hackathon exception from the mandatory production MFA requirement; IAM §13.2 and roadmap §9.6 carry the same three contexts |

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
| Superseded records retained | ADR-SAAS-013 and the original §14.3 question wording — kept verbatim, never deleted (`.clinerules` §11) |

### 15.1 Revision history

| Revision | Date | Change | Authority |
|---|---|---|---|
| V1.0 | 2026-11-17 | Initial six-document set; mechanisms `PROPOSED`, four `OPEN` owner decisions | Engineering |
| **Revision 2** | 2026-11-17 | Reconciled against the owner-approved SaaS decision packet: §1.5 decision record added; two-axis status introduced (decisions `OWNER-APPROVED`/`SPECIFIED`/`OPEN`/`DEFERRED`/`SUPERSEDED` vs evidence `NOT IMPLEMENTED`/`IMPLEMENTED`/`TESTED`/`VERIFIED`); A1 microservices target and transitional compromises (§3.4, ADR-017); A2 three deployment patterns (§2, §4.3, ADR-012); A3 healthcare profiles (§2.2, ADR-015); A4 platform authority (§3.5, ADR-016); O-SaaS-2 audit split; O-SaaS-3 lifecycle cap at `read_only`; O-SaaS-4 Core never sold or gated; O-SaaS-7 multi-membership (ADR-014 supersedes ADR-013); O-SaaS-8/13/14/16 four-eyes and consent; O-SaaS-9 no legacy auto-mapping; §14.3 registry closed with rulings; §14.3.1 engineering questions opened | Product Owner (decisions) + Engineering (mechanisms) |
| **Revision 3** | 2026-11-17 | Post-commit correction of one record: **O-SaaS-15 restated** — platform operator MFA is a **production-launch requirement** with a temporary, explicitly documented, restricted hackathon exception, not a deferral and not a post-launch enhancement. §1.5 row rewritten; **new §9.3 rule 7**; §14.3 ruling rewritten with the original question marked verbatim; §14.4 self-check row added; §11 non-goal row narrowed to enterprise SSO/federation so it no longer implies MFA is optional. No mechanism, evidence grade, other ruling or `A1–A4` direction changed; operator MFA is `NOT IMPLEMENTED` | Product Owner decision O-SaaS-15, restated without reinterpretation |

### 15.2 What Revision 2 did **not** do

- It wrote no code, schema, migration or test, and claims no new evidence. Every evidence label in
  §13 stands exactly where V1.0 left it.
- It did not reopen a decided question. Where Revision 2 disagreed with an earlier mechanism, the
  mechanism changed and the *decision* stayed the owner's — the reason is recorded next to it.
- It did not edit the five sibling documents' substance from here; each carries its own Revision 2
  note and cites §1.5 / §12 / §14.3 by id rather than restating them (one registry, one ADR set).
- It did not touch `docs/product/`, `docs/architecture/AMSDP_System_Architecture_V1.0.md`,
  `.clinerules`, or any owner-controlled document (`.clinerules` §11).

### 15.3 What Revision 3 did **not** do

- It did not implement, schedule or design MFA: no provider, protocol or enrolment flow was chosen,
  and no second-factor capability is claimed to exist.
- It did not change O-SaaS-15's substance, any other `O-SaaS` ruling, any `A1–A4` direction, or any
  `EQ` question (`EQ-4`, `EQ-5` and `EQ-7` remain open).
- It did not advance an evidence grade: operator MFA is `NOT IMPLEMENTED` and the platform identity
  domain is still absent from the tree, exactly as the audit recorded it.
- It did not touch application code, schema, migrations, deployment files, the frontend or any test.
- It did not amend the other five documents' substance; each carries its own Revision 3 note and
  cites §1.5 / §9.3 / §14.3 rather than restating them.
| Revision | V1.0 — 2026-11-17 |
