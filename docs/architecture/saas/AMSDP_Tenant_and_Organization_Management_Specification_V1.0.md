# AMSDP — Tenant and Organization Management Specification V1.0

> **Document ID:** `AMSDP_Tenant_and_Organization_Management_Specification`
> **Version:** V1.0 · **Revision 2 (owner decision reconciliation) — 2026-11-17** · **Branch:** `hackathon-mvp` @ `409a929`
> **Status:** **SPECIFICATION — DECISION-RECONCILED, NOT IMPLEMENTED.** The sixteen `O-SaaS` items and
> directions A1–A4 were decided by the Product Owner on 2026-11-17 (architecture specification §1.5,
> §14.3). This document applies those rulings: the model decisions are `OWNER-APPROVED`, every
> mechanism here remains `SPECIFIED` and unbuilt, and nothing here authorises implementation.
> **Evidence base:** `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` §5 (tenant as built).
> **Companion documents:** architecture specification (states, pipeline, ADRs), IAM specification
> (principals, membership), subscription & entitlement specification (plans, quotas), implementation
> roadmap.
> **No code, schema, migration, compose or frontend file was changed to produce it.**
> **Evidence base:** `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` §5 (tenant as built).
> **Companion documents:** architecture specification (states, pipeline, ADRs), IAM specification
> (principals, membership), subscription & entitlement specification (plans, quotas), implementation
> roadmap.
> **No code, schema, migration, compose or frontend file was changed to produce it.**

---

## 1. Purpose and scope

### 1.1 What this document specifies

The tenant's whole life as a commercial object: what an organization **is** in the SaaS model, how
one is **created**, what **state** it is in, what each state **permits**, how its **configuration
and limits** are expressed, and how one is **closed** without destroying the audit trail.

### 1.2 What it deliberately does not specify

| Out of scope | Where it lives |
|---|---|
| Plan definitions, entitlements, quota arithmetic | subscription & entitlement specification |
| Who a principal is, tokens, revocation | IAM specification |
| Enforcement order inside a request | architecture specification §5 |
| Billing, invoicing, payment gateways | excluded by product documents (ADR-SAAS-008) |

### 1.3 Authority order

`.clinerules` §3 → `AMSDP_Business_Rules_V1.1.md` §37–§40 → `AMSDP_Master_Feature_List_V2.5`
§5.1, §19.1–§19.3, §21 → owner decisions Q-1…Q-6 → **owner decision packet 2026-11-17** (`O-SaaS-1…16`,
A1–A4 — architecture specification §1.5, §12, §14.3) → this document (mechanisms `SPECIFIED`).

The two-axis status vocabulary of architecture specification §1.3 governs here: a decision axis
(`OWNER-APPROVED` / `SPECIFIED` / `OPEN` / `DEFERRED` / `SUPERSEDED`) and an evidence axis
(`NOT IMPLEMENTED` / `IMPLEMENTED` / `TESTED` / `VERIFIED`). `PROPOSED` is retained as the exact
synonym of `SPECIFIED`.

---

## 2. Tenant as built (baseline)

| Aspect | Today | Evidence |
|---|---|---|
| Tenant key | `organizations.id`; every tenant table carries `organization_id` | audit §3 |
| Hierarchy | `organization → branch → floor / department / room`, optional at every level, per-branch unique codes | audit §5.3 |
| Status field | `organizations.status`, default `active`, values `active`/`inactive` in practice | `common/models.py` |
| Enforcement of that status | **none** — nothing reads it on the request path | audit §5.2, finding G-2 |
| Who can change it | the tenant itself: `org.manage` is held by `org_admin`, and `PATCH /api/v1/orgs/{org_id}` accepts `status` | audit R-03 (privilege inversion) |
| Audit of that change | broken: `before` is built from the already-mutated row, so both sides are identical | audit R-04 |
| Provisioning | `POST /api/v1/orgs`; no signup, invitation, trial, domain claim or seed step beyond the demo seeder | audit R-05 |
| Global reference data precedent | `symptom_catalog.organization_id` nullable | audit §10 |

Two consequences follow, and they shape everything below:

1. **A lifecycle column already exists but is inert and tenant-writable.** The specification cannot
   simply reuse `status`; it must add an enforced state and remove the tenant's ability to write it
   (§3.3, §5).
2. **Provisioning is one endpoint, not a process.** `POST /api/v1/orgs` produces a tenant with no
   administrator and no plan, which is why provisioning becomes an ordered, audited operation
   (§4) rather than "the POST returned 201".

## 3. Tenant model (target)

### 3.1 Vocabulary, fixed once

| Term | Meaning | Never means |
|---|---|---|
| **Organization** | the tenant; the subscription holder; the tenant key | a branch, a department, a doctor |
| **Branch** | a physical or logical site inside a tenant | a billing unit |
| **Site** | synonym for branch in product language | a new table |
| **Lifecycle state** | the enforced operational state of the organization | the subscription's own status, which is a separate row |
| **Plan** | the catalogue entry that defines limits and modules | the tenant's own subscription |
| **Subscription** | one row binding an organization to a plan for a period | a payment |

A plan attaches to an **organization**, never to a branch (audit §5.3). No exception is designed.

### 3.2 Invariants

| # | Invariant | Consequence if violated |
|---|---|---|
| T-1 | `organization_id` is the only tenant key; no second tenant column is introduced | isolation becomes ambiguous; `.clinerules` §3 forbids it |
| T-2 | A tenant's state is derived from its row, never from a token claim or `config` | a suspended tenant keeps working until tokens expire |
| T-3 | Only the platform plane may write `lifecycle_state` and subscription fields | a tenant lifting its own suspension (today's R-03) |
| T-4 | Closing a tenant never deletes rows, ever | BR §39 and the append-only audit trail |
| T-5 | Every state transition is audited with actor, reason, before/after | BR §40 |
| T-6 | A branch is always inside exactly one organization; cross-org branch assignment is impossible | tenant leakage through `branch_id` |
| T-7 | Limits are counted from data, not stored as mutable counters | drift and invisible over-provisioning |
| T-8 | A tenant can read its own state and entitlements and cannot read another's | transparency + non-disclosure |

### 3.3 The `lifecycle_state` column (ADR-SAAS-005)

New column on `organizations`: `text NOT NULL DEFAULT 'active'`, constrained to the five states in
§5.1. The legacy `status` column is **retained unchanged** so nothing that reads it breaks, and:

| Rule | Detail |
|---|---|
| Single writer | `backend/platform/` only; the tenant service's `PATCH` loses the ability to set either field |
| Derivation | `status` is kept consistent by the platform writer (`active` ⇔ `lifecycle_state in (active, grace, read_only)`); it is a **mirror**, never the authority |
| Reader | one function, `common/lifecycle.resolve(org_id)`, used by every endpoint, the public display endpoint and tracking |
| Caching | per request, memoised in the request scope; no cross-request cache without the version-bump rule (subscription specification §8) |
| Backfill | the migration sets `lifecycle_state='active'` for every existing row; mapping legacy `inactive` → `closed` requires owner approval (**O-SaaS-9**) |

That last row is a deliberate restraint: reinterpreting an existing value would silently shut off
whatever tenants currently have `status='inactive'` — a data change disguised as a migration.

### 3.4 Hierarchy rules

1. Organization → branch → floor / department / room, all optional below the organization.
2. Branch codes are unique **per organization**, and facility codes unique **per branch** — the
   existing model, unchanged.
3. Retiring a branch is `status='inactive'`, never a delete; historical appointments and queue
   entries keep pointing at it.
4. A branch's plan-relevant limits come from its organization. A branch has no plan.

## 4. Provisioning

### 4.1 Why provisioning must be an operation, not a POST

Today `POST /api/v1/orgs` creates a row and stops. A tenant created that way cannot log in (no
administrator), has no plan (no entitlement resolution), and produces no audit of "who onboarded
whom". Provisioning therefore becomes one platform-plane operation that either completes every step
or leaves nothing half-built.

### 4.2 Steps (one transaction, then one audit)

| # | Step | Failure behaviour |
|---|---|---|
| 1 | verify the platform operator holds `platform.tenant.manage` | `403` |
| 2 | validate the payload (§4.3) | `422`, no writes |
| 3 | create the `organizations` row with `lifecycle_state='active'` | rollback |
| 4 | create the first `org_admin` staff row (or an invitation token once e-mail exists) | rollback |
| 5 | create the `subscriptions` row (plan, period, grace policy) | rollback |
| 6 | materialise the entitlement projection from the plan | rollback |
| 7 | seed nothing else — no branches, no patients, no demo data | n/a |
| 8 | audit `tenant.provisioned` with the operator, plan and tenant id | audit failure **fails the operation** |

Step 8 is inside the success criterion on purpose: a tenant that exists with no record of who
created it is precisely the state the audit rules forbid.

### 4.3 Payload and validation

| Field | Required | Rule |
|---|---|---|
| `name` | yes | 2–120 characters, trimmed |
| `slug` | yes | `^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$`, globally unique |
| `timezone` | yes | IANA name; validated, not free text |
| `plan_key` | yes | must exist in `plans` and be `active` |
| `admin_username` | yes | unique within the org, not equal to the slug |
| `admin_password` | yes | supplied by the operator, policy-checked (IAM §4.6), never written to audit |
| `trial_days` | no | integer 0–60; `0` means no trial |
| `contact_email`, `contact_phone` | no | format-validated; stored on the organization, consumed by the notification worker later |

### 4.4 Idempotency

Provisioning requires an `Idempotency-Key` header. Replaying the key returns the original result
instead of creating a second tenant — without it, a double-clicked form creates two tenants with
the same clinic name and two subscriptions.

### 4.5 What provisioning must never do

| # | Prohibition | Reason |
|---|---|---|
| PV-1 | create a tenant with no administrator | an unreachable tenant is a support ticket by construction |
| PV-2 | create a tenant with no subscription | entitlement resolution would have to invent a default, which is how free access appears |
| PV-3 | copy data from another tenant (template tenants) | one template mistake becomes a cross-tenant data copy |
| PV-4 | return credentials to anyone but the provisioning operator | password material must never enter a log or a third party's inbox |
| PV-5 | touch the demo seed or a demo override database | the demo database is a presentation artefact, not a provisioning target |

### 4.6 Onboarding after provisioning (tenant-led)

| Step | Actor | Notes |
|---|---|---|
| first login | the created `org_admin` | must change the password on first use (flagged column, not a policy hope) |
| create branches | `org_admin` | subject to the plan's branch limit (§9) |
| invite staff | `org_admin` | subject to the user limit; no self-service signup exists or is designed |
| configure symptoms / facilities | `org_admin`, `branch_admin` | existing org configuration, unchanged |

There is **no self-service signup** in V1 and none is designed here: a clinic cannot create its own
tenant. That is a product decision (audit R-05 recommends operator-led onboarding), and inventing
a public signup flow would add abuse handling, e-mail verification and domain claiming — none of
which exist.

---

## 5. Lifecycle states

### 5.1 The five states (ADR-SAAS-005)

| State | Meaning | Entered by |
|---|---|---|
| `active` | normal operation | provisioning; renewal; reactivation |
| `grace` | subscription expired, operation **continues** (BR §39 item 3) | expiry scheduler |
| `read_only` | grace elapsed; reads and permitted exports continue, writes refused (BR §39 item 5) | expiry scheduler |
| `suspended` | governance action for abuse, legal or non-payment escalation (BR §38) | platform operator |
| `closed` | tenant terminated; nothing reachable, nothing deleted | platform operator, after retention review |

`grace` is **not** a penalty state, and a design that degrades service during it would contradict
the approved business rule. `suspended` is stronger than `read_only` because it is a deliberate
governance act, not an expiry consequence.

> **Revision 2 note.** ADR-SAAS-005 (the five-state model reproduced above) is **`OWNER-APPROVED`**
> — it was ratified as part of the 2026-11-17 packet, together with `O-SaaS-14` (suspension needs a
> second operator) and `O-SaaS-16` (closure needs a second approver and retains data by default).
> The state set is unchanged by those rulings; only the **actor requirement** tightens (§5.2).

### 5.2 Transition table

| From → To | Trigger | Actor | Reversible |
|---|---|---|---|
| — → `active` | provisioning | `platform.tenant.manage` | n/a |
| `active` → `grace` | period end reached, grace policy > 0 | scheduler | yes, by renewal |
| `active` → `read_only` | period end reached, grace policy = 0 | scheduler | yes, by renewal |
| `grace` → `read_only` | grace elapsed | scheduler | yes, by renewal |
| `read_only` → `active` | renewal recorded | `platform.subscription.manage` | yes |
| `active`/`grace`/`read_only` → `suspended` | governance decision, reason required, **second operator approval required (O-SaaS-14)** | `platform.tenant.manage` + approver | yes |
| `suspended` → `active` | decision reversed | `platform.tenant.manage` | yes |
| any → `closed` | termination request, retention review done, **second approver signed (O-SaaS-16)**; data retained by default | `platform.tenant.manage` + approver | **no** |
| `closed` → anything | — | — | **forbidden**; a returning customer gets a new tenant |

Two rules make this table safe to implement:

1. **Every transition is compare-and-set** on the current state. The scheduler and an operator
   acting at the same moment cannot both win, so no "suspended then silently reactivated by an
   expiry job" sequence is possible.
2. **Two of these transitions are two-person acts** (O-SaaS-14, O-SaaS-16). The approval is a
   recorded row — a distinct principal, a timestamp and a reason — not a checkbox on the same
   screen. A single operator holding both `platform_admin` and `platform_ops` cannot self-approve;
   the approver must be a different account (IAM §7.3).
### 5.3 State × operation matrix (authoritative; identical in every document)

| State | Sign in | Read (GET/HEAD) | Write (POST/PATCH/PUT/DELETE) | Export | Public display / tracking |
|---|---|---|---|---|---|
| `active` | yes | yes | yes | yes | yes |
| `grace` | yes | yes | **yes** (BR §39 item 3: normal operation continues) | yes | yes |
| `read_only` | yes | yes | **403 `TENANT_READ_ONLY`** | yes (BR §39 item 5 "permitted exports") | yes |
| `suspended` | yes (so support can act) | **403 `TENANT_SUSPENDED`** | 403 `TENANT_SUSPENDED` | platform-only | neutral "temporarily unavailable" |
| `closed` | 403 `TENANT_CLOSED` | 403 `TENANT_CLOSED` | 403 `TENANT_CLOSED` | platform-only | 404 / neutral |

This table is reproduced verbatim from architecture specification §5.3 because it must not drift
between documents: **one** table, two citations.

Three consequences that are easy to get wrong:

1. **Sign-in survives `suspended`.** If sign-in is blocked, the tenant cannot read the reason, and
   support cannot use any tenant-plane tooling. Only `closed` blocks sign-in.
2. **Public endpoints are gated too.** `/api/v1/queue/display` and `/api/v1/track/{token}` resolve
   a tenant and must consult the same resolver: tracking returns `404` when the owning tenant is
   not `active`/`grace`/`read_only`; the display returns a neutral message with no patient content.
   A suspended tenant that keeps broadcasting a live queue is a real, user-visible leak.
3. **`read_only` still exports.** BR §39 item 5 preserves data access; blocking exports would make the
   state punitive and push tenants toward churn instead of renewal.

### 5.4 Expiry: notice first, then degrade

| Point in time | Action | Channel | Status |
|---|---|---|---|
| 14 days before period end | `subscription.expiry_reminder` | notification worker (**not deployed** — Phase 4 prerequisite) | `SPECIFIED`, blocked |
| 3 days before | second reminder | same | `SPECIFIED`, blocked |
| at period end, grace > 0 | `active` → `grace`, audit | scheduler | `SPECIFIED` |
| at period end, grace = 0 | `active` → `read_only` | scheduler | `SPECIFIED` |
| grace elapsed | `grace` → `read_only` | scheduler | `SPECIFIED` |
| 30 days in `read_only` | **nothing automatic** — suspension is a human decision (BR §38) requiring a second operator (O-SaaS-14) | — | `SPECIFIED` |

The last row matters: BR §39 requires notice and read-only preservation; it does not authorise an
automatic suspension or deletion. An expiry job that eventually suspends on its own would exceed
its authority. The job's maximum legitimate action is `read_only`.

**The scheduler cannot deliver notices today** because no notification transport is deployed
(audit AR-3). The roadmap therefore places the first *enforcement* of expiry behind the
notification worker, not merely behind code: a tenant silently dropped into `read_only` with no
warning violates the business rule as written.

### 5.5 The scheduler

| Property | Requirement |
|---|---|
| Placement | one in-process loop inside the `platform` service (ADR-SAAS-011) |
| Mutual exclusion | Postgres advisory lock; if the lock is held, this replica skips the tick |
| Cadence | every 15 minutes; the tick is cheap (one indexed query for due subscriptions) |
| Idempotency | compare-and-set on state; a second run produces no state change and no audit row |
| Failure | tick errors are logged with the subscription id, never with the tenant's content; the next tick retries |
| Observability | one structured log line per tick: `due`, `changed`, `skipped` counts |
| Time source | database `now()`, never application clock, so replicas cannot disagree |

The database clock choice is not pedantry: two containers with drifting clocks can otherwise
compute different "grace has elapsed" answers for the same tenant.

---

## 6. Enforcement in the request path

### 6.1 Where the state is applied

Exactly one place: architecture specification §5.1 step 7, between the tenant scope check (step 6)
and the permission check (step 8). `common/lifecycle.resolve()` returns the state; a small
`require_lifecycle_permits(request)` dependency applies §5.3.

| Property | Requirement |
|---|---|
| Placement in the pipeline | **after** tenant scope, **before** RBAC and entitlement |
| Reason | a lifecycle check before scope turns the platform into an existence oracle (§9.2 of the IAM specification) |
| Coverage | every authenticated router, plus the public display/tracking endpoints through the same resolver |
| Exempt list | a short, explicit allowlist: `/health`, `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/me`, `/api/v1/platform/*` |
| Exempt-list rule | the list is defined **in code and asserted by a test**; a new router is gated by default, never exempt by omission |

### 6.2 Failure semantics

Identical to architecture specification §5.2; the lifecycle rows are:

| Situation | Response | Audited as |
|---|---|---|
| lifecycle forbids the method | `403` + machine code `TENANT_READ_ONLY` / `TENANT_SUSPENDED` / `TENANT_CLOSED` | denial row + the originating lifecycle event, written by the platform plane |
| lifecycle cannot be determined (row missing / resolver error) | `503` — **never** allow the request | denial row + error log, `X-Entitlement-State: unknown` |

---

## 7. What a tenant sees and feels

### 7.1 Transparency requirements

| Surface | Content | Rule |
|---|---|---|
| Global banner | current state, plan name, period end, grace remaining | must be visible on every page while state ≠ `active` |
| Settings → Subscription | plan, limits, usage, period, renewal contact | read-only from the tenant side (no self-service upgrade in V1) |
| Blocked write | inline message naming the machine code and the period end | never a generic "error" |
| Export | available in `read_only`, disabled in `suspended` | reflects §5.3 exactly |
| Audit | the tenant can read its own subscription/lifecycle events | actor is shown as the platform operator's **role**, not a personal identity, unless the policy owner decides otherwise (O-SaaS-10) |

### 7.2 Why the banner is a specification requirement

BR §39 item 1 requires notice before expiry, and a tenant that discovers a block by hitting it will
telephone support. The banner is the cheapest compliance mechanism available and needs no new
infrastructure. It is **not** an enforcement mechanism — hiding it changes nothing about §5.3.

### 7.3 Frontend obligations

| Obligation | Detail |
|---|---|
| render from `/api/v1/auth/me` | state, modules and capabilities come from the server (IAM §9.3) |
| no client-side state logic | the frontend never decides that a write "should" be allowed |
| show server codes verbatim | `TENANT_READ_ONLY` and friends are the shared vocabulary between UI, support and logs |
| disable, but do not hide, in `read_only` | hiding implies the capability is gone; disabling with a renewal hint is accurate |
| no cached state beyond one page load | a stale "active" banner after suspension is a support call; it must refresh on navigation |

---

## 8. Tenant configuration and overrides

### 8.1 `organizations.config` is a controlled extension point

The column already exists (audit §10) and is the right place for tenant-scoped settings that are
not commercial (those are subscription fields, never `config`).

| Rule | Detail |
|---|---|
| Allowed keys | a **closed** whitelist defined in one module (`common/org_config.py`): `locale_default`, `queue_display_footer`, `appointment_walk_in_policy`, `symptom_catalog_mode`, `notification_channel`, `timezone_display` |
| Unknown key on write | `422 ORG_CONFIG_UNKNOWN_KEY` — fail closed; a silently ignored setting is an invisible no-op support will chase for days |
| Unknown key on read | ignored with one warning log line, so a legacy row cannot break the app |
| Type validation | every key has a declared type and range, validated in the same module |
| Commercial keys | `plan`, `modules`, `limits`, `lifecycle_state` are **forbidden** in `config` — they live on the subscription, and duplicating them creates two truths |
| Size | 16 KB serialised; beyond that it is configuration debt, not configuration |

### 8.2 Feature overrides

| Mechanism | Allowed? | Why |
|---|---|---|
| per-tenant module grant on top of the plan | yes, via a `subscription_overrides` row | a pilot or goodwill grant must be visible, dated, audited and revocable in one place |
| per-tenant module *removal* below the plan | no | removes value the tenant pays for, and hides revenue problems |
| negative override (block a module) | only for security incidents, platform-only, with reason and expiry | an emergency stop is legitimate; a silent one is not |
| override stored in `organizations.config` | **never** | §8.1 forbids commercial keys; an override in JSON is invisible to the subscription screens |

### 8.3 Every override is audited

---

## 9. Limits and usage accounting

### 9.1 Declared limits (BR §38)

| Limit | Counted from | Enforced at |
|---|---|---|
| `max_users` | `staff_users` with `status='active'` for the org | staff creation / reactivation |
| `max_doctors` | `doctors` rows for the org that are not retired | doctor creation / reactivation |
| `max_branches` | `branches` with `status='active'` for the org | branch creation / reactivation |
| `max_appointments_per_month` | `appointments` created in the current calendar month (org timezone) | appointment creation |
| module availability | entitlement projection | module-gated routes only |

### 9.2 Counting rules (T-7: count, never cache a counter)

1. Every limit is answered by a `COUNT(*)` over an indexed, org-scoped predicate at enforcement
   time. There is no stored `users_count` column to drift.
2. The count is **not** cached, because limits are consulted only on create/reactivate — a few
   hundred operations a month, not a hot path.
3. Monthly appointment counts use the organization's timezone, not UTC, or a Dhaka tenant's month
   boundary would be wrong by six hours.
4. A retired branch or deactivated user frees a slot; the count reflects reality, not history.
5. Usage **reporting** (platform screens through `platform.usage.read`) uses the same queries, so
   the number the operator sees and the number enforced cannot diverge.

### 9.3 Exceeding a limit

| Situation | Behaviour |
|---|---|
| at limit, creating another | `403 LIMIT_REACHED` with `{limit, current, max}` in the body |
| downgrade leaves the tenant over a limit | **nothing is deleted**; existing records stay; **new** creations are refused until the count fits. Reads and updates of existing records continue |
| over `max_appointments_per_month` | appointments may still be **cancelled and modified**; only *creation* is refused — a clinic must never be unable to cancel |
| limit is `null` | unlimited (enterprise); never `0`, which would mean "feature off" and is expressed by module entitlement instead |

The downgrade rule is the one that matters commercially: deleting a tenant's data to satisfy a new
plan would be both a data-loss incident and a breach of BR §39's preservation principle. Over-limit
tenants degrade into "no new growth", never into loss.

### 9.4 What is never a limit

Storage bytes, request rate (that is throttling, not a plan), audit rows, and anything else that
would silently break the Core workflow. V2.5 §D forbids an optional module from disabling Core, and
the same reasoning applies to limits: a limit may constrain *growth*, never *operation*.

---

## 10. Audit requirements

### 10.1 Tenant-plane and platform-plane events

| Event | Plane | Required fields |
|---|---|---|
| `tenant.provisioned` | platform | operator id, tenant id, plan key, timestamp |
| `tenant.lifecycle_changed` | platform / scheduler | from, to, actor (or `scheduler`), reason, timestamp |
| `tenant.suspended` / `tenant.reactivated` | platform | as above; suspension requires a free-text reason |
| `tenant.closed` | platform | retention review reference, operator id |
| `tenant.override_granted` / `tenant.override_revoked` | platform | module key, reason, actor, expiry |
| `tenant.config_updated` | tenant | actor, changed key **names** only — never values, which may contain free text |
| `tenant.branch_created` / `tenant.branch_retired` | tenant | actor, branch id, name |
| `tenant.profile_updated` | tenant | actor, changed key names |

### 10.2 Rules

1. Append-only; no update or delete path exists in code for `audit_logs` (`.clinerules` §3).
2. A lifecycle change and its audit row commit in the **same transaction**; if the audit insert
   fails the transition does not happen.
3. Denials caused by lifecycle (§6.2) are audited with the tenant id and the machine code.
4. Reasons are stored but **never echoed into logs** at INFO level beyond the first 200 characters,
   and never contain credentials or patient data — the writer truncates and the reviewer notices.
5. The tenant sees its own rows only; the platform sees all rows; neither sees secrets.
6. **`before` is captured before the mutation, never after** — the existing `org.update` handler
   builds both sides from the already-mutated row, so the audit row records a change from X to X
   (audit R-04). The fix is one line at the correct place, and it is a precondition for this
   document's claim that lifecycle and configuration changes are auditable at all.
7. **Event-plane routing (O-SaaS-2).** A *tenant-affecting* event goes to the tenant's `audit_events`
   with a **non-null `organization_id`**, even when a platform operator caused it. A *platform-only*
   event (operator sign-in, operator screens, internal review) goes to `platform_audit_events`. There
   is no nullable `organization_id` anywhere, so "which tenant did this touch" is never inferred.
8. **Operator identity is disclosed to the tenant (O-SaaS-10).** The tenant-facing view of an
   operator-caused row names the operator's identity **and** their platform role; platform-only rows
   are not hidden from the tenant when they affected it, and never expose another tenant's data.

---

## 11. Closure and offboarding

### 11.1 What `closed` means

| Aspect | Decision |
|---|---|
| data rows | **retained**, untouched, unreachable through the API |
| access | every tenant-plane request returns `403 TENANT_CLOSED`, including login |
| audit | retained, queryable by the platform, never deleted |
| public tracking | `404` |
| reversal | **not possible**; a returning customer is provisioned as a new tenant with a new id |
| deletion | a **separate, owner-approved** data-retention process (BR §39 + legal review), never a side effect of closing |

### 11.2 Why closure is irreversible

Reversing a closure would resurrect tokens, links and tracking URLs that the outside world may
already treat as dead — a security regression dressed as convenience. Irreversibility also forces
the operator to confirm the decision, which is the point.

### 11.3 Closure preconditions

| # | Precondition | Reason |
|---|---|---|
| 1 | tenant is `suspended` first | closure always follows a deliberate suspension, never a scheduler path |
| 2 | an export has been offered or declined in writing | BR §39 access guarantee |
| 3 | a retention review reference is recorded | legal and finance reconciliation |
| 4 | the reason is recorded in the audit row | an unexplained closure cannot be defended later |
| 5 | **a second approver, distinct from the requesting operator, has signed (O-SaaS-16)** | closure is irreversible (§11.2); one account must not be able to end a tenant alone |

**O-SaaS-16 in words.** The owner decided that a tenant ends through **two** operators and that its
data is **retained by default**; deletion is never a consequence of closure and remains a separate,
explicitly authorised retention process (§11.1). The approved ruling does not extend to reusing a
closed tenant's id — §11.2 stands.

### 11.4 Offboarding checklist (operational)

1. record the request and its authority;
2. produce the tenant data export and hand it over, or record a documented refusal;
3. suspend, then close — two audited transitions, not one;
4. confirm no active staff sessions matter (they are refused at the lifecycle gate, not revoked);
5. leave rows, audit and files intact;
6. file the retention review reference in the closure audit row.

No step in this list deletes anything, and that is the point.

---

## 12. Migration and compatibility

### 12.1 The migration (one revision, forward-only, idempotent)

| # | Operation | Reversible by |
|---|---|---|
| 1 | `ALTER TABLE organizations ADD COLUMN lifecycle_state text NOT NULL DEFAULT 'active'` | a later forward migration dropping the column (production never runs `down`) |
| 2 | `CREATE INDEX ix_organizations_lifecycle_state ON organizations (lifecycle_state)` | a later forward migration |
| 3 | `CHECK (lifecycle_state IN ('active','grace','read_only','suspended','closed'))` | a later forward migration |
| 4 | backfill: every existing row is already `'active'` through the default — no `UPDATE` needed | n/a |
| 5 | no change to `status`, no change to any other table | n/a |

Written with `IF NOT EXISTS` guards against a single head, per `.clinerules` §3 and the existing
linear Alembic chain (audit §10).

### 12.2 Compatibility window

| Concern | Behaviour during the window |
|---|---|
| code that reads `status` | unchanged; `status` keeps its current values and semantics |
| code that reads `lifecycle_state` | only the new resolver, deployed **before** enforcement is switched on |
| the tenant `PATCH /orgs/{id}` | still accepts `status` until the platform plane owns it; then the field is rejected (`422`), never silently ignored |
| demo seed | untouched; it keeps working because the default is `active` |
| rollback | switch enforcement off and leave the column in place — an unused column is harmless, a dropped one is a data-loss rehearsal |

### 12.3 Ordering (cannot be reordered)

1. migration → 2. resolver + tests (enforcement **off**) → 3. platform-plane lifecycle endpoints →
4. enforcement **on** for `read_only`/`suspended`/`closed` → 5. scheduler (only once the
notification worker exists, §5.4).

Step 4 before step 3 would expose states no operator can set; step 5 before the notification worker
would degrade tenants without the notice BR §39 item 1 requires.

---

## 13. Tests that must accompany the change

| Test | Asserts |
|---|---|
| `test_lifecycle_default_is_active` | every pre-existing organization resolves to `active` after migration |
| `test_read_only_blocks_writes_allows_reads` | `POST` → `403 TENANT_READ_ONLY`; `GET` → `200`; export → `200` |
| `test_grace_allows_writes` | a `grace` tenant can create an appointment (BR §39 item 3) |
| `test_suspended_allows_login_blocks_data` | login `200`, `GET /api/v1/patients` → `403 TENANT_SUSPENDED` |
| `test_closed_blocks_login` | `403 TENANT_CLOSED`, no token issued |
| `test_lifecycle_after_scope_check` | a cross-org request still returns `404`, never `403 TENANT_*` (no existence oracle) |
| `test_public_tracking_gated` | tracking token of a `suspended` tenant → `404`; display shows no patient content |
| `test_transition_is_compare_and_set` | two concurrent transitions: one wins, one is a no-op, exactly one audit row |
| `test_no_op_transition_writes_no_audit` | a repeated scheduler tick adds nothing |
| `test_tenant_cannot_write_own_lifecycle` | `org_admin` `PATCH` carrying `lifecycle_state` → `422`/`403`, row unchanged |
| `test_limit_reached_body` | `403 LIMIT_REACHED` carries `{limit, current, max}` |
| `test_over_limit_downgrade_keeps_data` | downgrade → existing records readable, new creation refused, nothing deleted |
| `test_lifecycle_exempt_list_is_closed` | router inventory vs allowlist: any unlisted router is gated |

The first four are the ones a reviewer should refuse to merge without: they encode BR §39 itself.

---

## 14. Governance and skill compliance

| Requirement | Compliance |
|---|---|
| `.clinerules` §2 automatic routing | domain rows applied: multi-tenant data, database/migrations, backend API, audit, documentation |
| `.clinerules` §3 non-negotiables | `organization_id` stays the only tenant key (T-1); enforcement is server-side only (§6); cross-tenant `404` preserved (§6.1); audit append-only (§10.2); no secrets in audit or logs (§4.3, §10.2); forward-only idempotent migration (§12.1) |
| `.clinerules` §4 domain table | read and applied: `saas-multitenant-data.md` (adapted, §4–5), `saas-cicd-workflow.md` §3 (adapted migration discipline), BR §38–§40, `backend/common/models.py`, `backend/alembic/versions/` |
| `.clinerules` §5 skills | **no skills installed** in this workspace — none used, none claimed; governance documents used in their place |
| `.clinerules` §7 evidence standard | every "today" statement is sourced from the audit; every mechanism is `SPECIFIED`; nothing is claimed `VERIFIED` |
| `.clinerules` §9 boundaries | no code, schema, migration, compose or frontend file changed; no server started, no test suite run |
| `.clinerules` §11 output location | `docs/architecture/saas/`, the subject-matching subfolder (§15) |
| `.clinerules` §12 reading policy | index and audit read before writing; architecture specification §14.3 used as the single decision registry |
| Revision 2 reconciliation | O-SaaS-1/2/5/9/10/14/16 applied; ADR-SAAS-005/012 `OWNER-APPROVED`; `PROPOSED` → `SPECIFIED`; two-person suspension and closure added (§5.2, §11.3); no evidence label advanced by any decision |

### 14.1 Self-check

- Does anything here let a tenant change its own commercial state? No — T-3, §8.1.
- Does anything here delete data? No — T-4, §11.1; O-SaaS-16 confirms retention by default.
- Does any lifecycle check run before tenant scope? No — §6.1.
- Is any state trusted from a token? No — T-2.
- Is a counter stored that can drift from reality? No — §9.2.
- Is a notification claimed that does not exist? No — §5.4 marks it blocked and the roadmap gates it.
- Is the §5.3 matrix written here independently of the architecture specification? No — cited, not
  re-derived, so the two cannot disagree.
- Can one operator suspend or close a tenant alone? No — §5.2 rule 2, §11.3 item 5 (O-SaaS-14/16).

---

## 15. Document control

| Field | Value |
|---|---|
| Written to | `docs/architecture/saas/` (`.clinerules` §11: new leaf under the existing `architecture/` subject folder) |
| Evidence base | `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` — all "as built" claims trace there |
| Siblings | architecture specification (planes, ADRs, §5.3 matrix), IAM specification (principals, authorisation chain), subscription specification (plans, entitlements), roadmap (phases, gates) |
| Decisions applied | O-SaaS-3, O-SaaS-5, O-SaaS-9, O-SaaS-10, O-SaaS-14, O-SaaS-16 — ids and verbatim rulings owned by architecture specification §14.3 |
| Code, schema, migration, compose, frontend changes | **none** |
| Runtime verification | **none claimed** — a specification, not an acceptance report |
| Index registration | `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Revision | V1.0 — 2026-11-17; **Revision 2** — 2026-11-17 (owner decision reconciliation) |

### 15.1 Revision history

| Revision | Date | Change | Authority |
|---|---|---|---|
| V1.0 | 2026-11-17 | Initial tenant & organization specification; five lifecycle states and closure left gated on owner questions | specification-only draft |
| **Revision 2** | 2026-11-17 | Owner decisions `O-SaaS-1…16` and A1–A4 applied: ADR-SAAS-005 ratified; two-person suspension (§5.2 rule 2, O-SaaS-14) and two-approver closure (§11.3 item 5, O-SaaS-16); audit plane routing and operator disclosure (§10.2 rules 7–8, O-SaaS-2/10); header, §1.3 and all mechanism labels moved to the two-axis vocabulary | Product Owner, 2026-11-17 |

### 15.2 What Revision 2 did not do

- It did not create the `lifecycle_state` column, the resolver, the scheduler, the platform screens,
  the two-approver workflow or the notification transport. Every mechanism stays `SPECIFIED` with
  evidence `NOT IMPLEMENTED`.
- It did not change the §5.3 state × operation matrix — that matrix is reproduced from architecture
  specification §5.3 and must not drift between documents.
- It did not touch any code, migration, compose file, frontend file or test.
