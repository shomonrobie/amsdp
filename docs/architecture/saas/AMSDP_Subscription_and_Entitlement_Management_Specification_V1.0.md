# AMSDP — Subscription and Entitlement Management Specification V1.0

> **Document ID:** `AMSDP_Subscription_and_Entitlement_Management_Specification`
> **Version:** V1.0 · **Date:** 2026-11-17 · **Branch:** `hackathon-mvp` @ `133ce83`
> **Status:** **SPECIFICATION — PROPOSED, NOT APPROVED.** Nothing here is authorised for
> implementation. Table shapes are fixed by the architecture specification §7.3; this document may
> only add column detail and behaviour, never a new entity.
> **Evidence base:** `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` §6 (no commercial layer exists).
> **Companion documents:** architecture specification (§6 module registry, §7 data, §8 caching),
> tenant & organization specification (lifecycle, limits counting), IAM specification
> (authorisation chain), implementation roadmap (phases, gates).
> **No code, schema, migration, compose or frontend file was changed to produce it.**

Status labels are the architecture specification's set: `APPROVED`, `PROPOSED`, `OPEN`, `DEFERRED`,
`FORBIDDEN`. This document adds no label and softens none.

---

## 1. Purpose, scope and authority

### 1.1 What this document specifies

How a tenant's **commercial state** is stored, resolved, enforced and audited: plans and their
versions, the ten module keys, purchased add-ons, numeric limits, the `Entitlement` object the
request path consults, the cache version contract, and the rules that keep a downgrade from
becoming data loss.

### 1.2 What it does not specify

| Out of scope | Where it lives |
|---|---|
| Lifecycle states and their transition authority | tenant & organization specification §5 |
| Principal, token and permission semantics | IAM specification §3–§9 |
| Enforcement *order* inside a request pipeline | architecture specification §5.1 |
| Pricing, invoices, payments, tax, refunds | excluded (ADR-SAAS-008); V2.5 §30.3 leaves them unfixed |
| Counting rules for `max_users` and friends | tenant & organization specification §9 (cited, not duplicated) |

### 1.3 Authority order

`.clinerules` §3 → `AMSDP_Business_Rules_V1.1.md` §37–§40 → `AMSDP_Master_Feature_List_V2.5`
§C/§C.1/§D, §19.1–§19.3, §30.1–§30.4 → architecture specification §6–§8 → this document
(`PROPOSED`).

---

## 2. Baseline: what exists today

| Aspect | Today | Evidence |
|---|---|---|
| Subscription, plan, entitlement, licence code | **none** — no table, no column, no route | audit §6 (`grep` for `subscription\|entitlement\|billing` returns nothing) |
| Module gating | **none** — every implemented endpoint is reachable by any authenticated, authorised principal | audit §6 |
| Commercial vocabulary | **none** in code | audit §6 |
| Tenant of record | `organizations` | audit §3 |
| Precedent for a global (non-tenant) table | `symptom_catalog.organization_id` nullable | audit §10 |
| Enforcement point available | the shared kernel's dependency chain, already used for tenancy and RBAC | `backend/common/auth.py`, `backend/common/permissions.py` |

The commercial layer is therefore **greenfield** — which is the good case, because it can be built
straight rather than migrated into. The risk it carries is different: with no existing behaviour to
constrain it, an under-specified design would invent behaviour the owner never approved. Hence the
`PROPOSED` labels and the explicit refusal to invent pricing.

---

## 3. Vocabulary (fixed once, used everywhere)

| Term | Meaning | Never means |
|---|---|---|
| **Module key** | one of the ten stable keys in architecture §6 (`core`, `pqv`, …) | a permission, a route prefix, a UI tab |
| **Plan** | a named, versioned bundle of module keys and limit values | a subscription |
| **Plan version** | an immutable snapshot of a plan's contents | an edit of a live plan |
| **Subscription** | one row binding an organization to one plan version for a period | a payment, an invoice |
| **Entitlement** | the resolved set of modules + limits for one organization at one version | a stored table |
| **Add-on** | a module granted to one tenant beyond its plan, with provenance | an override without a reason |
| **Limit** | a numeric ceiling (`users`, `doctors`, `branches`, `appointments_per_month`) | a soft warning threshold |
| **`entitlements_version`** | monotonic integer on `organizations` used as the cache key | a timestamp |
| **Grace** | the post-expiry period in which operation continues (BR §39 item 3) | a free tier |

Two naming rules that prevent most future confusion:

1. An **entitlement is never stored**. It is a computed view; a table called `entitlements` would be
   a second source of truth that drifts from `plan_modules` on the first missed write.
2. A **plan is never edited in place**. Plans are versioned; an edit produces a new version, so a
   tenant's terms cannot change because someone fixed a typo in the catalogue.

---

## 4. Persistence

### 4.1 Tables (shape fixed by architecture specification §7.3; detail here)

| Table | Columns (beyond `id`, `created_at`, `updated_at`) | Notes |
|---|---|---|
| `modules` | `key` PK, `name`, `dependencies` (JSON array of keys), `status` ∈ `available`/`absent` | 10 rows, seeded by migration, asserted equal by test to the code constant |
| `plans` | `code` UNIQUE per version, `version` int, `name`, `description`, `status` ∈ `draft`/`active`/`retired`, `effective_from`, `supersedes_id` | a "plan" the operator recognises is one `code` across several rows |
| `plan_modules` | PK `(plan_id, module_key)`, `included` bool | `included=false` is never written; absence means excluded |
| `plan_limits` | PK `(plan_id, limit_key)`, `limit_value` int NULL | NULL = unlimited; never `0` (tenant spec §9.3) |
| `subscriptions` | `organization_id` NOT NULL, `plan_id`, `starts_at`, `ends_at`, `grace_ends_at`, `state` ∈ `current`/`superseded`/`cancelled`, `external_reference` NULL | partial UNIQUE on `organization_id WHERE state='current'` |
| `subscription_modules` | PK `(subscription_id, module_key)`, `source` ∈ `plan`/`addon`/`override_deny`, `state` ∈ `enabled`/`disabled`, `branch_scope` JSON NULL, `expires_at` NULL, `reason` | add-ons and emergency denials only; plan inclusions come from `plan_modules` |
| `subscription_events` | `organization_id`, `event_type`, `from_state`, `to_state`, `actor_type` ∈ `operator`/`scheduler`/`system`, `actor_id` NULL, `reason`, `payload` JSON | append-only |

### 4.2 Why `branch_scope` lives on `subscription_modules` and nowhere else

V2.5 §30.4 permits a module to be scoped to specific branches. Expressing that on the subscription
row instead would make a plan-level scope indistinguishable from a tenant-wide one, and the
resolver would have to guess. One nullable JSON array — `["<branch_id>", …]`, NULL meaning all
branches — is enough, validates cheaply, and reads in one row.

`branch_scope` is **not** an authorisation boundary. A module scoped away from a branch returns the
module-missing response (§6.3); it never affects tenant isolation, which is decided earlier
(architecture §5.1 step 6).

### 4.3 Constraints the database must enforce (not just the service)

| Constraint | Why in SQL |
|---|---|
| `plan_limits.limit_value IS NULL OR limit_value > 0` | a `0` limit means "feature off" and would silently break Core |
| FK `subscriptions.plan_id → plans.id` | an orphan subscription resolves to nothing, i.e. fails closed at runtime for a data bug |
| FK `subscription_modules.subscription_id → subscriptions.id` ON DELETE RESTRICT | add-ons must never outlive their subscription silently |
| partial UNIQUE current subscription | two current subscriptions produce two answers to one question |
| CHECK on `modules.key` against the ten keys | a typo in a seed must fail at migration, not at request time |

### 4.4 `organizations` additions this document depends on

| Column | Type | Rule |
|---|---|---|
| `entitlements_version` | `Integer NOT NULL DEFAULT 1` | bumped in the same transaction as any commercial write (§8.1) |
| `lifecycle_state` | owned by the tenant specification §3.3 | read here, never written here |
| billing metadata (`billing_contact_*`, `contract_reference`, `reseller_code`) | nullable text | `OPEN`; not required for enforcement, so not required for this specification to hold |

### 4.5 What is deliberately absent

| Not built | Reason |
|---|---|
| `entitlements` table | derived data; §3 |
| `invoices`, `payments`, `credit_notes` | ADR-SAAS-008 excludes billing |
| `usage_counters` | T-7/§9.2 of the tenant specification: counters drift, counts do not |
| `coupons`, `trials` as a separate entity | a trial is a `subscriptions` row with `ends_at`; a coupon is pricing, hence excluded |
| per-branch subscriptions | a plan attaches to an organization only (audit §5.3) |

---

## 5. Resolution

### 5.1 The algorithm (mirrors architecture specification §8.1 exactly)

```
effective_modules(org, branch?) =
       { m ∈ plan_modules(plan_of(current_subscription(org))) }        -- plan inclusions
  ∪    { m ∈ subscription_modules(org) : source='addon', state='enabled' }  -- purchased
  ∖    { m ∈ subscription_modules(org) : source='override_deny', state='enabled' }  -- emergency stop
       restricted to branch_scope (NULL = all branches), and to rows whose expires_at is null or future

effective_limits(org) =
       plan_limits(plan_of(current_subscription(org)))
  ⊕    addon/provisioning overrides recorded as subscription_events (deltas only, never absolute)
```

### 5.2 Precedence rules, stated so they cannot be argued later

| # | Rule | Reason |
|---|---|---|
| R-1 | a plan inclusion cannot be removed by an add-on row | "removal" is a deny row with a reason and an expiry, not an absence |
| R-2 | a deny row always wins over an inclusion | an emergency stop that can be overridden by the plan is not a stop |
| R-3 | dependency violations are **write-time errors**, never request-time surprises | architecture §6.1 invariant 3 |
| R-4 | a module key that is `status='absent'` in `modules` cannot be granted | you cannot sell a module the code does not implement (architecture §6.1 invariant 5) |
| R-5 | `core` is always present | architecture §6.1 invariant 2; V2.5 §D |
| R-6 | an organization with no current subscription resolves to **no commercial modules** and is treated as `read_only`-equivalent for module-gated routes — never "all modules" | the free-access failure mode the audit warns about (audit R-08) |
| R-7 | limits are read from the plan in force at the moment of the check, never from a copy on the subscription | one truth |

R-6 is the single most important line in this document. It is what stops a missing row (a failed
provisioning, a deleted subscription, a migration bug) from becoming a free enterprise tenant. The
platform treats "no subscription" as an **integrity alarm**, not as a permissive default.

### 5.3 The resolved object

```python
# backend/common/entitlements.py — PROPOSED shape (contract, not implementation)
@dataclass(frozen=True)
class Entitlement:
    organization_id: UUID
    version: int              # organizations.entitlements_version at resolve time
    modules: frozenset[str]   # includes 'core' always
    limits: Mapping[str, int | None]
    branch_scope: Mapping[str, tuple[UUID, ...] | None]  # module -> branches or None (all)
```

Frozen, so a request handler cannot accidentally mutate a cached object and leak the mutation into
another request in the same worker.

### 5.4 Where resolution is *not* allowed

| Prohibited | Why |
|---|---|
| calling the `platform` service from the request path | architecture §8.1: entitlements are data, not an RPC; a platform outage must not deny tenant service |
| resolving entitlements in the JWT or a claim | staleness measured in hours, and a token is not a commercial source |
| resolving in the frontend | `.clinerules` §3: the UI is never the safety boundary |
| caching a negative result differently from a positive one | a "no modules" cached for 60 s is correct; cached forever is an outage |

---

## 6. Enforcement

### 6.1 The single gate

```python
require_module("clinical_records")   # PROPOSED
```

Behaviour, in order:

| Step | Check | Failure |
|---|---|---|
| 1 | is the module key in the registry and `status='available'`? | `500` at startup/test time, never at request time — a missing key is a programming error |
| 2 | is the key `core`? | return immediately (no-op by construction, never written in code) |
| 3 | is the module in `effective_modules(org)` for this branch? | `403 MODULE_NOT_ENTITLED` |
| 4 | log and audit one denial row | — |

### 6.2 Placement in the pipeline

Module enforcement is step 9 of architecture specification §5.1 — **after** lifecycle (step 7) and
**after** RBAC (step 8). Consequence, deliberately chosen:

| If both fail | Response | Why |
|---|---|---|
| not entitled **and** lacking permission | `403` on permission first | the caller's authority is checked before the tenant's commercial state; this keeps RBAC messages stable and prevents the commercial layer from becoming an oracle about roles |
| not entitled, authorised | `403 MODULE_NOT_ENTITLED` with the module key | actionable: the tenant can buy it |

### 6.3 Status codes and their justification

| Situation | Code | Body | Why not the alternative |
|---|---|---|---|
| module not in the entitlement | `403` | `{code: "MODULE_NOT_ENTITLED", module: "<key>"}` | `404` would hide a purchasable capability and make support impossible |
| module `absent` in the codebase | never reachable at runtime | — | no route may gate on an unbuilt module (architecture §6.1) |
| tenant in `read_only` **and** not entitled | `403 TENANT_READ_ONLY` | lifecycle body | lifecycle precedes the commercial check; the earlier, more fundamental block is reported |
| cross-tenant path with any of the above | `404` | empty | tenant scope is decided at step 6, before this gate (`.clinerules` §3) |
| entitlements unresolvable (DB error) | `503` | empty + `X-Entitlement-State: unknown` | fail closed, never "allow" |

### 6.4 What is never gated by a module

`/health`, `/api/v1/auth/*`, `/api/v1/platform/*`, audit writes, and any Core workflow path
(V2.5 §D: no optional module may disable Core). A gated login or a gated audit write would be a
self-inflicted outage or, worse, an unaudited one.

---

## 7. Numeric limits

### 7.1 What this section owns, and what it cites

| Owned here | Cited from the tenant specification §9 (not duplicated) |
|---|---|
| where limit values come from (`plan_limits`) | how a limit is counted (`COUNT(*)` over an org-scoped predicate) |
| when a limit is checked (create/reactivate only) | over-limit behaviour after a downgrade |
| the response shape (`403 LIMIT_REACHED`) | counting a monthly window in the tenant's timezone |

This split exists so a limit is defined once. The tenant specification answers "how many are there";
this document answers "what is the ceiling and who may change it".

### 7.2 Limit keys

| Limit key | Scope | Notes |
|---|---|---|
| `users` | organization | counts active staff identities |
| `doctors` | organization | protects the doctor-entry dimension of BR §38 |
| `branches` | organization | limits locations, not tenants |
| `appointments_per_month` | organization, calendar month | a growth limit, never a lockout (§7.5) |

New limit keys are added by migration to `plans`/`plan_limits` with a matching entry in the code
constant; a key present in one and absent from the other is a test failure (architecture §6.1
invariant 1 applied to limits).

### 7.3 Which operation is checked

| Operation | Checked? | Reason |
|---|---|---|
| create a staff user / doctor / branch | yes | the only moment a ceiling is crossed |
| reactivate a deactivated user or retired branch | yes | reactivation consumes a slot |
| create an appointment | yes (`appointments_per_month`) | the only creation path |
| update, cancel, complete | **no** | a clinic must always be able to cancel; refusing an update would corrupt the workflow, not protect revenue |
| read anything | no | reads never grow usage |
| restore/import | yes, as creation | an import is creation in bulk; a bypass here would make the limit decorative |

### 7.4 Who may change a limit

| Actor | Allowed |
|---|---|
| tenant (`org_admin`) | **nothing** — limit changes are commercial acts (T-3) |
| platform `platform.subscription.manage` | change plan, add-on, override |
| scheduler | **nothing** — expiry changes lifecycle, never limits |
| support grant holder | **nothing** — a support grant is not a commercial authority (IAM §7.3) |

### 7.5 The asymmetry rule

A limit may block **growth**; it may never block **operation**. Concretely: a tenant at its branch
limit can still manage existing branches; a tenant over `appointments_per_month` can still cancel,
rebook and complete appointments. This is the numeric expression of V2.5 §D's prohibition on an
optional module disabling Core, and it is the rule most likely to be violated by a well-meaning
`if over_limit: return 403` placed too early in a handler.

---

## 8. Version bump and caching contract

### 8.1 The bump rule

`organizations.entitlements_version` is incremented **in the same transaction** as any write that
can change the resolved entitlement:

| Write | Bumps? |
|---|---|
| subscription created, renewed, plan changed, cancelled | yes |
| `subscription_modules` add-on or deny row inserted, expired, removed | yes |
| `plan_modules` / `plan_limits` edited on a plan **in force for at least one tenant** | yes — for every tenant on that plan |
| a new plan version published | no (it affects only future subscriptions) |
| `lifecycle_state` change | no — lifecycle is never cached (architecture §8.2) |
| `organizations.config` change | no — not commercial (§4.5) |

The "plan edited while in force" row is the one that gets forgotten. It is also why plans are
versioned (§3): editing a live plan's contents would require touching every tenant that uses it,
which is both a write amplification and a support incident. The intended path is: publish a new
version, migrate tenants deliberately.

### 8.2 The cache contract (mirrors architecture specification §8.2)

| Aspect | Rule |
|---|---|
| key | `(organization_id, entitlements_version)` |
| value | the frozen `Entitlement` object only |
| TTL | 60 s safety net, bounding staleness if an eviction is lost across processes |
| bound | LRU, 5 000 organizations per worker |
| lifecycle state | never cached — a suspension must take effect on the next request |
| invalidation | version compare on every request; a mismatch is a miss, not an error |
| failure | resolution exception → `503`, never "allow" |

### 8.3 Why a version integer and not a distributed cache

The tenant services are separate containers, so an in-process cache cannot be evicted remotely.
Comparing `entitlements_version` on every request makes cross-process staleness self-correcting in
one request, at the cost of one indexed integer read already performed for the lifecycle check. A
Redis dependency would add a network hop to every request to solve a problem a column solves —
and the hardware envelope (4 GB VRAM / 16 GB RAM) has no appetite for another service.

### 8.4 The self-check that catches a missed bump

When a writer commits a commercial change it must verify, before returning, that the version it
wrote is the version the resolver now reads. A mismatch logs `entitlement.version_mismatch` at
WARN with the organization id. This is a bounded, cheap assertion placed at the only place where the
mistake can originate — rather than a periodic reconciler over every tenant.

---

## 9. Events and audit

### 9.1 Event vocabulary

| Event | Written to | Required fields |
|---|---|---|
| `subscription.created` | `subscription_events` + audit | plan code+version, period, actor |
| `subscription.renewed` | both | new period, actor |
| `subscription.plan_changed` | both | from plan, to plan, reason |
| `subscription.cancelled` | both | reason, effective date |
| `subscription.expiring` | `subscription_events` only | days remaining (a notification trigger, not a governance act) |
| `subscription.expired` | both | lifecycle transition caused |
| `subscription.module_granted` / `module_revoked` | both | module key, source, expiry, reason |
| `entitlement.denied` | audit (denial path) | org, module key or limit key, principal |
| `entitlement.version_mismatch` | log at WARN | org id, expected vs observed version |

### 9.2 Two stores, one truth

`subscription_events` is the **commercial** history (narrow, typed, easy to render in a platform
screen). `audit_events` is the **governance** record (append-only, retention-scoped, queried during
incidents). Both are written in the same transaction as the change; neither replaces the other. A
commercial change that appears only in `subscription_events` is ungoverned, and one that appears
only in `audit_events` is unrenderable.

### 9.3 The platform-audit caveat

`audit_events.organization_id` is `NOT NULL` today (audit C-7), so a purely platform-scope action has
nowhere to be written. Subscription events for a specific tenant carry that tenant's id and are
therefore **writable today**; a plan-catalogue edit belongs to no tenant and is **not** writable
until ADR-SAAS-009 / O-SaaS-2 is decided. This document does not invent a table for it — it records
the gap and, in the meantime, requires plan-catalogue edits to be made only by an operator and
logged to the platform service's structured log.

### 9.4 What is never in an audit row

Passwords, tokens, support-grant secrets, and full tenant configuration values. Key **names** are
recorded for configuration changes; values are not (§4.5 of the tenant specification).

---

## 10. Failure modes and integrity alarms

| Failure | Effect | Detection |
|---|---|---|
| organization has no current subscription | resolves to no commercial modules (R-6); module-gated routes `403` | integrity query on startup + daily: organizations without a current subscription |
| subscription points at a `draft` or `retired` plan | treated as invalid → no modules, alarm | FK cannot prevent it; resolver validates plan status |
| `subscription_modules` reference a `retired` module key | module not granted; alarm | daily integrity query |
| `entitlements_version` never bumped | stale entitlement for ≤ 60 s | writer self-check (§8.4) |
| plan edited in place while in force | tenants' limits change without an offer | prevented by versioning (§3); if it happens, audit gap and alarm |
| resolver raises | `503` on module-gated routes; Core routes unaffected | error log + `X-Entitlement-State: unknown` |
| two current subscriptions exist | impossible via the partial UNIQUE; if the constraint was dropped, resolver takes the newest by `starts_at` **and alarms** | integrity query |

The first row is the one that decides whether this feature is safe in production. A tenant with no
subscription must see "not entitled", never "everything" — that is R-6, restated as an operational
alarm rather than a code path.

---

## 11. Change control

### 11.1 Upgrades

| Step | Rule |
|---|---|
| preview | the platform shows the target plan's modules and limits against current usage before applying |
| apply | one transaction: new subscription row + old row `state='superseded'` + version bump + event |
| effect | immediate; the resolver sees the new plan on the next request |
| proration | **out of scope** (billing excluded, ADR-SAAS-008) |

### 11.2 Downgrades

| Step | Rule |
|---|---|
| block if dependency-invalid | removing `clinical_records` while `prescriptions` is granted is rejected at write time (R-3) |
| warn on over-limit | the platform shows which limits would be exceeded |
| apply | same transaction as an upgrade; **nothing is deleted**, ever |
| effect | over-limit data stays readable; new creations refused until under the limit (tenant spec §9.3) |
| audit | `subscription.plan_changed` with `reason` mandatory for a downgrade |

A downgrade without a reason is refused. The reason is the only artefact that explains, six months
later, why a tenant saw a paywall.

### 11.3 Retiring a plan

| Rule | Detail |
|---|---|
| `status='retired'` | no new subscription may reference it |
| existing subscriptions | **continue unchanged** — a retirement is not a downgrade |
| forced migration | a separate, audited, per-tenant action, never a side effect of retirement |
| deletion | never; a retired plan is history referenced by live subscriptions |

### 11.4 Versioning the module key set

Adding a module key is a migration + code change + test in one pull request. Renaming a key is
**forbidden** (plans and audit rows reference it); a renamed module is a new key with a
`supersedes` note. Removing a key is forbidden while any subscription references it.

---

## 12. Migration and compatibility

### 12.1 Revision order (five revisions, each forward-only and idempotent)

| # | Revision | Content |
|---|---|---|
| 1 | `add_saas_module_registry` | `modules` table, CHECK on the ten keys, seed of ten rows |
| 2 | `add_saas_plans` | `plans`, `plan_modules`, `plan_limits`; no plan rows seeded (a plan is a commercial decision, not a migration) |
| 3 | `add_saas_subscriptions` | `subscriptions`, `subscription_modules`, `subscription_events`; partial UNIQUE current subscription |
| 4 | `add_org_entitlements_version` | `organizations.entitlements_version` NOT NULL DEFAULT 1, backfill implicit |
| 5 | `add_saas_indexes` | the indexes named in §12.2 |

Splitting the schema from the plan data is deliberate: a migration that invents a `starter` plan
would encode pricing in a revision, which no reviewer could approve and no owner has decided.

### 12.2 Indexes that the resolution query requires

| Index | Query it serves |
|---|---|
| `subscriptions (organization_id) WHERE state='current'` | unique current subscription lookup |
| `subscription_modules (subscription_id, module_key)` | the joined resolution select |
| `plan_modules (plan_id)` | plan inclusion select |
| `plans (code, version)` | "which version is in force" |
| `organizations (entitlements_version)` | not needed for lookup; included only if the integrity query uses it |

### 12.3 Compatibility

| Concern | Behaviour |
|---|---|
| code paths before the gate exists | unchanged; `require_module` is introduced route by route, and a route without it behaves exactly as today |
| a tenant with no subscription at rollout | R-6 applies **only** to routes that call `require_module`; because no route calls it at first, rollout cannot lock anyone out |
| the compatibility flag | `SAAS_ENFORCEMENT_ENABLED` (default **off**) makes `require_module` a pass-through; the flag is removed in roadmap Phase 2, not carried forever |
| rollback | flip the flag off; the tables stay, containing data that is correct but unread |

The flag is the one piece of transitional machinery this design accepts, and only because it lets
the schema land before the behaviour. Its removal is a roadmap gate, not an intention.

### 12.4 What breaks on purpose

| Breaking change | Why it must break |
|---|---|
| a route gated on a module the tenant lacks now returns `403 MODULE_NOT_ENTITLED` | that is the entire product change |
| plan contents become immutable once in force | editing in place is the failure mode §8.1 describes |

---

## 13. Tests that must accompany the change

| Test | Asserts |
|---|---|
| `test_registry_matches_code_constant` | `modules` rows == the ten keys in code |
| `test_core_always_entitled` | `effective_modules` contains `core` for every organisation, including one with no subscription |
| `test_no_subscription_grants_nothing` | R-6: an organization without a current subscription resolves to `{core}` only, and gated routes `403` |
| `test_addon_grants_module` | an add-on row makes a gated route `200` |
| `test_deny_wins_over_plan` | `override_deny` removes a plan-included module (R-2) |
| `test_branch_scope_limits_module` | a module scoped to branch A is `403` on branch B, `200` on branch A |
| `test_expired_addon_stops` | `expires_at` in the past → module gone without a write |
| `test_version_bump_invalidates_cache` | plan change → the next request sees the new entitlement |
| `test_missing_version_bump_logs` | a write without a bump logs `entitlement.version_mismatch` |
| `test_limit_blocks_growth_not_operation` | at `appointments_per_month`, create → `403`, cancel → `200` |
| `test_downgrade_deletes_nothing` | row counts identical before and after a downgrade |
| `test_entitlement_error_is_503` | resolver exception → `503`, never `200` |
| `test_cross_tenant_still_404` | a foreign org on a module-gated route → `404`, not `403 MODULE_NOT_ENTITLED` |
| `test_flag_off_is_passthrough` | with `SAAS_ENFORCEMENT_ENABLED=off`, every module gate is a no-op |

The first four and `test_cross_tenant_still_404` are the non-negotiable group: they encode R-5, R-2,
R-6 and `.clinerules` §3 respectively.

---

## 14. Open items

Ids are the canonical registry (architecture specification §14.3); this document mints none.

| ID | Item | Blocks |
|---|---|---|
| O-SaaS-4 | Confirm the ten module keys as the commercial vocabulary — the plan catalogue cannot be authored until the key set is fixed | plan authoring (Phase 1) |
| O-SaaS-2 | Platform-scope audit shape (ADR-SAAS-009): plan-catalogue edits have no tenant and therefore no `audit_events` row | §9.3; platform launch |
| O-SaaS-6 | If B2 dedicated deployment is in scope, how is a licence recorded for a stack that has one organization? Every mechanism here assumes platform-written subscription rows | Phase 3+ |

### 14.1 Residual risks accepted by this specification

1. **60-second staleness window** for entitlement changes. Accepted because it is bounded, because a
   lifecycle change (the safety-critical case) is never cached, and because the alternative is a
   distributed cache on a 16 GB host.
2. **`SAAS_ENFORCEMENT_ENABLED` exists at all.** Any flag is a bypass; this one is accepted only
   with a roadmap gate that removes it, and a test that asserts it defaults to off.
3. **No self-service purchase.** The platform writes subscriptions; tenants cannot. That is a
   deliberate V1 restriction — there is no payment path, so a self-service purchase would be a
   self-service free upgrade.

---

## 15. Governance and skill compliance

| Requirement | Compliance |
|---|---|
| `.clinerules` §2 automatic routing | domain rows applied: backend API, multi-tenant data, database/migrations, audit, documentation |
| `.clinerules` §3 non-negotiables | `organization_id` remains the only tenant key (§4.1); enforcement server-side only (§6.1, §5.4); cross-tenant `404` precedes every gate (§6.3); audit append-only (§9.2); no secrets in events or logs (§9.4); forward-only idempotent migrations (§12.1); no capability claimed that is unbuilt (every label `PROPOSED`) |
| `.clinerules` §4 domain table | read and applied: `saas-application-security.md` (adapted), `saas-multitenant-data.md` §4–5, BR §37–§40, V2.5 §C/§D/§30, architecture specification §6–§8 |
| `.clinerules` §5 skills | **no skills installed** — none used, none claimed |
| `.clinerules` §7 evidence standard | §2 is graded from the audit; no runtime claim is made |
| `.clinerules` §9 boundaries | no code, schema, migration, compose or frontend file changed; no service started, no suite run |
| `.clinerules` §11 output location | `docs/architecture/saas/` (§16) |
| `.clinerules` §12 reading policy | index, audit and architecture specification read before writing; siblings cited by section, not paraphrased |

### 15.1 Self-check

- Can a missing row grant everything? No — R-6, and `test_no_subscription_grants_nothing`.
- Can the platform service outage deny tenant requests? No — §5.4 forbids the request-path call.
- Can a tenant grant itself a module? No — `platform.*` only (§7.4); TENANT plane has no write route.
- Does a downgrade lose data? No — §11.2, `test_downgrade_deletes_nothing`.
- Is enforcement dependent on the frontend? No — §5.4, §6.1.
- Is a limit able to break Core? No — §7.5, R-5.
- Are module keys invented at implementation time? No — architecture §6.2, §11.4.

---

## 16. Document control

| Field | Value |
|---|---|
| Written to | `docs/architecture/saas/` (`.clinerules` §11: new leaf under the existing `architecture/` subject folder) |
| Evidence base | `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` §6, §13 |
| Shape authority | architecture specification §7.3 (tables), §8.1–§8.2 (resolution, cache), §5.1 (pipeline steps) |
| Siblings | architecture specification, tenant & organization specification, IAM specification, implementation roadmap |
| Open items | O-SaaS-2, O-SaaS-4, O-SaaS-6 |
| Code, schema, migration, compose, frontend changes | **none** |
| Runtime verification | **none claimed** |
| Index registration | `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Revision | V1.0 — 2026-11-17 |
