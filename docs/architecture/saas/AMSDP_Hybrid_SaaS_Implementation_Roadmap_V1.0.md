# AMSDP Hybrid SaaS — Implementation Roadmap V1.0

| Field | Value |
|---|---|
| Document | Implementation roadmap for the Hybrid SaaS architecture set |
| Status | **Revision 3** — `SPECIFIED` plan, **not** an acceptance record. Nothing in this document is implemented today. The sixteen `O-SaaS` decisions and directions A1–A4 were made by the Product Owner on 2026-11-17 (architecture specification §1.5, §14.3); this revision sequences the work they authorise. **Revision 3 (post-commit, 2026-11-17)** corrects two records only: operator MFA is a **production-launch gate** with a documented hackathon-only exception (§9.6), not a Phase 5+ deferral; and the P3 row in §8 now states A3's five approved profiles instead of the stale "internal/dedicated" wording. No phase, dependency or gate was added elsewhere |
| Date | 2026-11-17 |
| Location | `docs/architecture/saas/` |
| Siblings | `AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` (shape authority), `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` (evidence base), `AMSDP_Identity_and_Access_Management_Specification_V1.0.md`, `AMSDP_Tenant_and_Organization_Management_Specification_V1.0.md`, `AMSDP_Subscription_and_Entitlement_Management_Specification_V1.0.md` |
| Decision registry | Architecture specification §14.3 (`O-SaaS-1…16`, all decided) and §14.3.1 (`EQ-1…8`, engineering questions) — this document mints no ids |

## 1. Purpose and scope

### 1.1 What this document is

The ordering, gates, dependencies and abort criteria for turning the five SaaS specifications into
working software. It answers three questions the specifications deliberately leave open:

1. **In what order** can the pieces be built without breaking a working demo?
2. **What must be true** before a phase is allowed to finish?
3. **What do we do** if a phase turns out wrong?

### 1.2 What it is not

- Not a schedule and not an estimate. No dates are promised; the phases are dependency-ordered, not
  calendar-ordered.
- Not a re-statement of the specifications. Where a phase implements something, it **cites the
  section** rather than paraphrasing it. If a phase and a specification disagree, the specification
  wins and this document has a defect.
- Not an evidence claim. `.clinerules` §7 grading applies: nothing here is `TESTED` or `VERIFIED`.

**Citation convention (applies to every table below).** `architecture §x` means
`AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` §x — never
`docs/architecture/AMSDP_System_Architecture_V1.0.md`, which owns its own numbering. `audit §x`
means `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md`. A bare `§x` is this document's own section.
`BR §x` is `AMSDP_Business_Rules_V1.1.md`; `V2.5 §x` is the Master Feature List V2.5.

### 1.3 The one-sentence strategy

> Make the data model and the resolver correct **before** anything can deny a request, then turn
> denial on in one controlled step, then operate it.

That is the whole roadmap; every gate below exists to protect it.

---

## 2. The phase model

### 2.1 Phases at a glance

| Phase | Name | Product behaviour change | Can it break the demo? | Exit gate |
|---|---|---|---|---|
| 0 | Verify and freeze | none | no | runtime verification of the stated baseline (§3.3) |
| 1 | Foundation, enforcement off | none (flag off) | no | demo flow re-run green + the O-SaaS-3/4/5/9 rulings applied to the migration (§4.1) |
| 2 | Enforcement on | module/lifecycle/RBAC denials become real; multi-membership lands | **yes** | the demo-flow re-run passes **with** enforcement on; flag deleted; membership switch verified (§5.6) |
| 3 | Platform operations | a tenant can be sold, changed and closed | no (adds surface) | platform actions fully audited, four-eyes proved (§6.5) |
| 4 | Notifications and recovery | expiry notices, self-service reset | low | notification worker exists and is deployed (§7.5) |
| 5+ | Deferred | P2/P3 deployment, introspection | — | owner decision per item (§8). Operator MFA is **not** here: it is the production-launch gate (§9.6) |

### 2.2 Why this order and not another

| Tempting order | Why it is wrong |
|---|---|
| Build the platform UI first (visible progress) | The UI would write tables that do not exist, against resolution rules not yet frozen, and would have to be rewritten. UI is Phase 3. |
| Turn enforcement on with the schema | A single mis-seeded plan locks out every tenant including the demo, with no way to see why. Foundation ships dark first. |
| Add `lifecycle_state` and the module gate in one change | Two independent failure modes in one deploy: a wrong lifecycle default denies everything; a wrong module default denies some things. Separate phases keep the blast radius attributable. |
| Defer audit to Phase 4 | BR §40 and `.clinerules` §3 make audit a launch blocker, not a nicety. Audit ships **with** the action that needs it. |
| Keep `SAAS_ENFORCEMENT_ENABLED` for safety | A flag that can disable enforcement in production is an escalation primitive (architecture §11.3). It exists only for Phase 1, and Phase 2 deletes it. |

### 2.3 Phase invariant

A phase may **add** behaviour; it may never **remove** a working one, except where the specification
says the removal *is* the product change (e.g. a tenant writing its own lifecycle state — audit
R-03). Every such intentional removal is listed by finding id in §13.

### 2.4 Definition of done (applies to every phase)

A phase is done only when all seven hold; a partially-done phase is not "mostly done", it is open:

1. The cited specification sections are implemented as written, or a deviation is recorded in the
   phase report with the owner's decision.
2. The named tests exist and pass in this tree (`TESTED`).
3. At least one independent artefact confirms it — live API call, DB read, or browser run
   (`VERIFIED`), per `.clinerules` §7.
4. Schema changes are forward-only, idempotent, and in the single Alembic chain.
5. Audit rows are written for every event the specification lists.
6. No secret, token or credential appears in code, log, report or commit.
7. The phase report exists under `docs/implementation/` with a Governance and Skill Compliance
   section (`.clinerules` §6).

---

## 3. Phase 0 — Verify and freeze

**Goal:** replace every "as built" claim in the audit with a checked observation, so Phase 1 is not
built on a document's memory of the code.

**Product change:** none. This phase may only add evidence and tests.

### 3.1 Work items

| # | Item | Output |
|---|---|---|
| 0.1 | Re-run the existing backend and frontend test suites and record the exact pass/fail counts | baseline test record |
| 0.2 | Start the stack from `docker-compose.demo.yml` and walk the demo flow (login → appointment → queue → display → track) | demo-flow transcript |
| 0.3 | Read the audit findings graded `IMPLEMENTED` against live code (`R-03`, `R-04`, `R-10`, `R-16`) and confirm each is still true | verification table |
| 0.4 | Confirm the Alembic head is single and linear (`alembic heads` returns one revision) | head revision id |
| 0.5 | Confirm `organizations.status` has no reader on the request path (grep, not memory) | grep evidence |
| 0.6 | Confirm the JWT secret code path: env-sourced, fallback reachable when `AMSDP_ENV` is unset | file:line evidence |

### 3.2 What must not happen in Phase 0

No schema change, no new endpoint, no dependency upgrade, no flag introduced. If a work item
requires a code change to be observable, the observation is deferred to Phase 1 and noted.

### 3.3 Exit gate — Phase 0

- [ ] Suite counts recorded (a number, not "passing")
- [ ] Demo flow walked end-to-end and transcribed
- [ ] Each `IMPLEMENTED` audit finding re-confirmed or corrected in the audit document
- [ ] One Alembic head confirmed
- [ ] Any audit statement found wrong is **corrected in the audit**, not silently worked around
- [ ] Phase report written to `docs/implementation/`

**Abort:** if the demo flow does not complete on a clean stack, stop. Phase 1 must not begin on a
broken baseline, because a later regression could not then be attributed to the SaaS layer.

---

## 4. Phase 1 — Foundation, enforcement off

**Goal:** land the schema, the resolver and the counting functions **behind a flag that denies
nothing**, with the vocabulary decisions frozen first.

**Product change:** none visible. `SAAS_ENFORCEMENT_ENABLED` defaults **off** (architecture §11.3).

### 4.1 Decisions this phase depends on — **all now decided**

| ID | Ruling (architecture §14.3) | Why it had to precede the migration |
|---|---|---|
| O-SaaS-3 | Five-state lifecycle vocabulary confirmed; automatic expiry capped at `read_only` | the CHECK constraint and the matrix encode it; changing it later is a migration plus a behaviour change |
| O-SaaS-4 | The ten module keys confirmed as the commercial vocabulary; Core never sold or gated | the registry row set is seeded by migration |
| O-SaaS-5 | `lifecycle_state` authoritative, transitional duplicate `status` approved | the migration shape depends on it; retirement precondition is `EQ-8` |
| O-SaaS-9 | Legacy `status='inactive'` is **preserved, never auto-mapped**; only a validated reviewed backfill to `active` | the backfill lives in the same migration |

These were open when this roadmap was first written; they are now `OWNER-APPROVED`, so Phase 1 is
**unblocked on decisions** and blocked only on engineering. The migration still may not contradict a
ruling: O-SaaS-9 in particular forbids the convenient `inactive → closed` shortcut.

### 4.2 Work items

| # | Item | Cites |
|---|---|---|
| 1.1 | Migration: `modules` registry + seed | subscription spec §12.1 rev 1 |
| 1.2 | Migration: `plans`, `plan_modules`, `plan_limits` | subscription spec §12.1 rev 2 |
| 1.3 | Migration: `subscriptions`, `subscription_modules`, `subscription_events` | subscription spec §12.1 rev 3 |
| 1.4 | Migration: `organizations.lifecycle_state` (default `active`) + legacy backfill | tenant spec §12.1 |
| 1.5 | Migration: `organizations.entitlements_version` (default 1) | subscription spec §12.1 rev 4 |
| 1.6 | Migration: the resolution indexes | subscription spec §12.2 |
| 1.7 | Backfill an explicit `active` subscription on a `legacy_full` plan for existing organizations | architecture §11.2 |
| 1.8 | `Entitlement` dataclass + resolver (pure function, no writes) | subscription spec §5.1–§5.3 |
| 1.9 | Counting functions (count, never cache) | tenant spec §9.2 |
| 1.10 | `require_module` wired but pass-through while the flag is off | subscription spec §6.1, §12.3 |
| 1.11 | `config` key whitelist validation | tenant spec §8.1 |
| 1.12 | The Phase 1 test group | subscription spec §13; tenant spec §13 |

### 4.3 Sequencing inside the phase

Schema (1.1–1.7) may merge before logic (1.8–1.11) but never the reverse: the resolver must not be
released against a schema missing a column it reads. The flag is what makes this safe — with it off
the resolver computes a value that is not enforced, so a wrong seed produces a wrong *value* rather
than a denied request.

### 4.4 What Phase 1 must prove with tests

The five non-negotiable tests (subscription spec §13) exist from day one, even with the flag off:
`test_core_always_entitled`, `test_no_subscription_grants_nothing`, `test_registry_matches_code_constant`,
`test_cross_tenant_still_404`, `test_flag_off_is_passthrough`. A foundation without these is a
foundation nobody can trust later.

### 4.5 What Phase 1 must not do

- Turn the flag on (§5 owns that).
- Gate a route the demo depends on.
- Add the `platform.*` principal domain (§5 owns that — it is a decision, not a migration).
- Write a plan row with a price. Pricing is out of scope (ADR-SAAS-008).

### 4.6 Exit gate — Phase 1

- [ ] All Phase-1 migrations applied forward **and** re-runnable on a clean database
- [ ] Every organization resolves to a non-null `Entitlement` with `core` present
- [ ] Demo flow re-run with the flag **off** — green, identical to the Phase 0 transcript
- [ ] The five non-negotiable tests pass
- [ ] `test_no_subscription_grants_nothing` passes against an organization deliberately left without
      a subscription
- [ ] Integrity query reports zero organizations without a current subscription
- [ ] Phase report written to `docs/implementation/`

**Rollback:** nothing is dropped (migrations are forward-only). Leave the flag off; the tables stay,
correct but unread. A schema mistake is corrected by a new forward revision, never by editing an
applied one.

---

## 5. Phase 2 — Enforcement on

**Goal:** make the denials real, delete the flag, and retire the tenant-scoped `super_admin` alias.

**Product change:** **yes** — the only phase that can break a working demo.

### 5.1 Decisions this phase depends on — **all now decided**

| ID | Ruling (architecture §14.3) | Consequence for this phase |
|---|---|---|
| O-SaaS-1 | Separate platform identity approved; legacy `super_admin` alias and its `platform.*` grants kept until the replacement is tested, then removed | 2.8 becomes a staged rename, not a drop |
| O-SaaS-2 | **Option A** audit split — `platform_audit_events` for platform-only events; tenant `audit_events` with a real `organization_id` for tenant-affecting events; never nullable | 2.5 must ship the table; 3.10 uses it |
| O-SaaS-7 | **Multi-membership adopted**; ADR-SAAS-013 superseded by ADR-SAAS-014 | `staff_users` **is** touched in this phase (2.12–2.14), not deferred |
| O-SaaS-8 | `platform_admin` and `platform_ops` separable; holding both is an audited, individually approved exception | shapes the role map before it is written |
| O-SaaS-10 | Named operator identity plus platform role in the tenant's audit view | shapes audit rendering in the same change |

The two-person controls are decided too (O-SaaS-14 suspension, O-SaaS-16 closure) but they become
relevant in Phase 3, where the buttons first exist — §6.1.

### 5.2 Work items

| # | Item | Cites |
|---|---|---|
| 2.1 | Lifecycle enforcement in the pipeline — **after** scope, before RBAC | tenant spec §6.1 |
| 2.2 | The tenant can no longer write its own lifecycle state (audit R-03) | tenant spec §3.3 |
| 2.3 | `before` captured before mutation in the organization update audit (audit R-04) | tenant spec §10.2 rule 6 |
| 2.4 | Module gate becomes real; flag default flipped on | subscription spec §6.2 |
| 2.5 | `platform_users`, platform token scope, role map | IAM spec §7.2–§7.3 |
| 2.6 | JWT guard fails closed on unset `AMSDP_ENV` (audit R-10 / C-8) | IAM spec §5.2 |
| 2.7 | Server-side token revocation + logout | IAM spec §4.3, §4.5 |
| 2.8 | `super_admin` → `org_super_admin`; `platform.*` grants removed from the tenant role | IAM spec §7.4 |
| 2.9 | `cross_org` retirement per the platform capability split | IAM spec §7.3, §9.3 |
| 2.10 | **Delete `SAAS_ENFORCEMENT_ENABLED`** and its pass-through branch | architecture §11.3 |
| 2.11 | Frontend: lifecycle banner, `403` rendering, capability discovery | tenant spec §7.3; IAM spec §9.3 |
| 2.12 | Membership migration: `organization_memberships` join + backfill of exactly one membership per existing identity (**`EQ-1`**) | IAM spec §8.1, §8.1.1 |
| 2.13 | Active-organization transport: token claim + dedicated switch endpoint with re-issue, live membership re-check on every request (**`EQ-2`**) | IAM spec §8.1; architecture §7.2 |
| 2.14 | Per-membership `role` + `branch_scope` → effective permissions; invitation/acceptance/revocation/suspension (**`EQ-3`**) | IAM spec §8.1.1 |
| 2.15 | `platform_audit_events` table + the tenant-side second write for tenant-affecting platform actions (**`EQ-4`**) | architecture §7.3; subscription spec §9.3 |

### 5.2.1 Why multi-membership sits in Phase 2 and not Phase 5+

It sat in "deferred" while ADR-SAAS-013 (one organization per identity) was the assumption. O-SaaS-7
rejected that assumption, and `EQ-1` explicitly **blocks the Phase 2 migration**: retiring
`staff_users.organization_id` into a join table cannot sensibly happen after enforcement is already
reading the column. So the shape lands with the enforcement work, and the switch path is part of the
Phase 2 gate.

`organization_id` remains the only tenant key (D-1). `organization_memberships` is a join that answers
"who may act in which tenant", never a second tenant column and never a second tenant key. Every
cross-tenant read still fails `404`; switching is an explicit re-authorisation that re-issues the
token, never a header or body value.

### 5.3 The order inside Phase 2 matters

2.6 and 2.7 must precede 2.8/2.9, and 2.8/2.9 must precede 2.10:

- Making the guard fail closed **before** renaming roles means the rename is evaluated under strict
  token validation, not loose.
- Removing `platform.*` from the tenant role **before** deleting the flag means the operator plane is
  already the only way to perform a platform action when the flag disappears. Delete the flag first
  and there is a window in which nobody can suspend a tenant at all.

### 5.4 What Phase 2 must not do

- Suspend a tenant automatically. The scheduler's maximum legitimate action is `read_only`
  (tenant spec §5.5); automatic suspension is forbidden by BR §39 as specified here.
- Gate login. A `closed` tenant is refused at authentication with a specific message; a `suspended`
  tenant can still sign in and read (tenant spec §5.3 matrix).
- Introduce a per-tenant "enforcement off" switch. That is a privilege-escalation primitive
  (architecture §11.3).
- Delete data to satisfy a limit or a downgrade (subscription spec §11.2).

### 5.5 The gate that actually protects the demo

Not a unit test: **the full demo-flow re-run with enforcement on**, executed against the seeded demo
tenant, plus a second run against a deliberately `read_only` tenant to prove the banner and the
denial path. The first run proves nothing broke; the second proves the feature exists.

### 5.6 Exit gate — Phase 2

- [ ] Demo flow re-run **with enforcement on** — green
- [ ] Demo tenant's commercial data present and correct (`active` subscription, `legacy_full` plan)
- [ ] `SAAS_ENFORCEMENT_ENABLED` does not appear anywhere in the tree (grep, not memory)
- [ ] A tenant token cannot perform a platform action; a platform token cannot read clinical content
- [ ] Cross-tenant request on a module-gated route still returns `404`, never `403`
- [ ] Revoked token rejected on the next request (live call, `VERIFIED`)
- [ ] An identity holding two memberships switches explicitly; the token re-issues; a request naming
      the other tenant in a header or body is ignored, not honoured
- [ ] Removing a membership takes effect on the **next request**, not the next refresh
- [ ] A membership revoked in tenant A cannot be used to reach tenant A from tenant B's token (`404`)
- [ ] `read_only` tenant: writes `403`, reads `200`, banner shown
- [ ] Phase report written to `docs/implementation/`

**Abort/rollback:** 2.10 (flag deletion) is the last step, so an abort leaves the flag available
*only* if nothing after 2.9 was merged. If a regression appears after the flag is gone, the rollback
is `git revert` of the specific offending change (§9.4), not re-adding the flag — re-adding it would
restore the escalation primitive the phase exists to remove.

---

## 6. Phase 3 — Platform operations

**Goal:** a tenant can be sold, changed, supported and closed by an operator through the product,
not through SQL.

**Product change:** additive — new platform surface, no tenant-plane behaviour removed.

### 6.1 Decisions this phase depends on — **all now decided**

| ID | Ruling (architecture §14.3) | Consequence for this phase |
|---|---|---|
| O-SaaS-13 | **Explicit `org_admin` consent for every support grant**; no policy pre-approval, including for `grace` tenants | 3.6 has one acceptance path and no shortcut |
| O-SaaS-14 | Suspension requires a **second approver**, exactly like closure | 3.7 and the suspend action are two-person actions; both buttons are gated by the same control |
| O-SaaS-16 | Closure needs **platform administrator approval plus a second approver**; clinical data is **retained by default**; anonymisation only on legal approval, as a separate audited act; `closed` ≠ deleted | 3.7 exports and retains; it never anonymises |
| O-SaaS-15 | **Platform operator MFA is required before production launch.** The hackathon MVP may run under a temporary exception that is documented as a security risk and restricted to a limited authorised operator group; the exception does **not** satisfy the production requirement and MFA is **not** deferred | the operator plane exists without a second factor **only** for the demo, inside the documented exception (§9.6); no production platform access before the gate is met |
| O-SaaS-12 | The operator-assisted reset response may return the code to the requesting administrator, under constraints | K-9 becomes a constraint to implement, not an open question |

### 6.2 Work items

| # | Item | Cites |
|---|---|---|
| 3.1 | `backend/platform/` service with the platform route set | architecture §3.2–§3.3 |
| 3.2 | Plan catalogue authoring: `draft` version → publish → retire | subscription spec §3, §11.3 |
| 3.3 | Subscription lifecycle endpoints: create, renew, change plan, cancel | subscription spec §11.1–§11.2 |
| 3.4 | Add-on and override rows (`subscription_modules`) with `branch_scope` | subscription spec §4.1–§4.2 |
| 3.5 | Tenant list + detail + usage display (counts, not cached counters) | tenant spec §9.2 |
| 3.6 | Support grant: request → tenant consent → time-boxed capability | IAM spec §7.3; architecture §9.3 |
| 3.7 | Tenant closure flow (irreversible, export-first) | tenant spec §11 |
| 3.8 | Platform UI: `/platform` pages — tenant list, plan picker, lifecycle actions | audit R-17 |
| 3.9 | Commercial metadata fields on `organizations` (nullable, platform-writable only) | architecture §7.4 |
| 3.10 | Platform-scope audit per the **settled** option A split: `platform_audit_events` + the tenant-side row | subscription spec §9.3; `EQ-4` |
| 3.11 | Two-person workflow primitive: request → second approver → execution, both identities audited (**O-SaaS-14/16**) | tenant spec §5.2, §11.3; architecture §9.3 |
| 3.12 | Suspension and closure buttons wired through 3.11 — no single-operator path in the code at all | tenant spec §5.2 rule 2 |

3.11 precedes 3.7: a closure flow built before the four-eyes primitive exists would need the primitive
retrofitted into the most dangerous code path in the product.

The one-permission escape hatch is deliberately absent. `EQ-7` records that any single-operator
emergency override would weaken exactly the control O-SaaS-14/O-SaaS-16 exist to create, and that it
would be an **owner** decision, never an engineering one. Nothing in Phase 3 may add one.

### 6.3 Ordering inside Phase 3

3.2 before 3.3 (a subscription needs a plan to point at), and 3.10 **with** 3.7 — a closure that is
irreversible and unaudited is the worst possible combination, so the audit path must exist before the
button does. 3.8 (UI) comes last: every endpoint must be callable and verified by direct API call
before a page is drawn over it.

### 6.4 What Phase 3 must not do

- Take a payment, store a card, or compute a price (ADR-SAAS-008).
- Give a tenant any subscription write route. The platform writes; the tenant reads
  (subscription spec §7.4).
- Let a support grant modify commercial state — a support grant is a time-boxed clinical-key
  capability, not an entitlement editor (IAM spec §7.3).
- Anonymise, or delete, clinical data on closure. O-SaaS-16 settled this: data is **retained by
  default** and `closed` ≠ deleted; anonymisation happens only on legal approval, as a separate audited
  act — never as part of the closure flow.
- Suspend or close a tenant on one operator's say-so. O-SaaS-14/O-SaaS-16 require a second approver;
  a flow that can complete with one identity is a defect, not a convenience.

### 6.5 Exit gate — Phase 3

- [ ] A full sale simulated by API: create plan version → create tenant → create subscription →
      verify the tenant resolves the expected modules and limits
- [ ] An upgrade and a downgrade performed and verified against the resolver, with `reason` recorded
- [ ] A downgrade over a limit verified to block growth only, never to delete data
- [ ] A support grant exercised, time box expired, capability gone on the next request
- [ ] A closure performed on a scratch tenant, verified irreversible, audited and export-first, with
      the clinical data **still present** (O-SaaS-16 retain-by-default)
- [ ] Suspension attempted by one `platform_ops` identity: refused; completed only after a second
      approver, with both identities in the audit trail
- [ ] Every platform action appears in `platform_audit_events`; every tenant-affecting action also
      appears in that tenant's `audit_events` with a real `organization_id` (`EQ-4`)
- [ ] A `grace` tenant receives no shortcut: its support grant still needed explicit `org_admin` consent
- [ ] Phase report written to `docs/implementation/`

**Abort/rollback:** platform endpoints are additive, so an abort disables routes and leaves tenant
behaviour untouched. Data written by an aborted phase (a plan, a subscription) is corrected by
superseding rows, never by deletion.

---

## 7. Phase 4 — Notifications and recovery

**Goal:** the two features the specifications deliberately gate on a component that does not exist
yet — expiry notices and self-service recovery.

**Product change:** additive, but it activates behaviour that is otherwise dark.

### 7.1 The prerequisite, stated plainly

Both items below need a **notification worker** (outbound mail or an equivalent delivery channel).
That worker is **not deployed today**. Until it is:

- expiry proceeds **without notice**, which is a commercial unfairness, not a technical bug;
- self-service password reset cannot exist, and operator-assisted reset stands in (IAM spec §6.2).

Neither is faked. The specifications say so; this roadmap gates them here rather than letting a
banner be described as a notice.

### 7.2 Work items

| # | Item | Cites |
|---|---|---|
| 4.1 | Notification worker: queue consumer, retry, dead-letter, redaction | §7.4 (no specification exists yet) |
| 4.2 | `subscription.expiring` trigger at the notice window (default 7 / 3 / 1 days) | tenant spec §5.4 |
| 4.3 | Expiry scheduler activated on the worker deployment, not before | tenant spec §5.5 |
| 4.4 | Self-service password reset (token delivery through the worker) | IAM spec §6.3 |
| 4.5 | Notification templates, Bangla + English, following existing i18n conventions | `.clinerules` §4 frontend row |

### 7.3 Why the scheduler is gated here

The scheduler's maximum action is `read_only` (tenant spec §5.5), so the action itself is safe. What
is not safe is running it **before** notices can be sent: a tenant dropped to `read_only` with no
warning is exactly the support incident tenant spec §5.4 exists to prevent. Notice first, then
degrade — so the worker precedes the scheduler.

### 7.4 The gap this phase exposes

There is no notification subsystem specification in the document set. This roadmap states that
plainly rather than inventing one (`.clinerules` §3: never claim a capability that is not verified).
Item 4.1 therefore needs its own short specification **before** implementation, written under
`docs/architecture/` and registered in the index. Until then Phase 4 is blocked, not merely
sequenced later.

### 7.5 Exit gate — Phase 4

- [ ] Worker deployed and delivering to a test channel, with retry and dead-letter proven
- [ ] A tenant moved toward expiry receives a notice **before** any degradation
- [ ] Scheduler proved idempotent: two concurrent runs produce one transition and one audit row
- [ ] Self-service reset completed end-to-end and the old password invalidated immediately
- [ ] No credential, reset token or tenant PII in worker logs
- [ ] Phase report written to `docs/implementation/`

**Abort/rollback:** disable the scheduler first (the only actor that changes state without a human),
then the worker. Re-enabling is a deliberate act with an audit row, not a restart side effect.

---

## 8. Phase 5+ — Deferred, and why

| Item | Canonical id | Why deferred |
|---|---|---|
| `staff_password_history` reuse checks | O-SaaS-11 | Post-launch decision; defence in depth with no launch blocker, risk accepted |
| P2 dedicated deployment and its licence/renewal mechanics | O-SaaS-6 | **Not in MVP.** Long-term direction; `EQ-6` owns it and it may not leak into P1 behaviour |
| P3 institution-controlled deployment | O-SaaS-6; A2 | Same ruling; additionally requires the per-tenant profile configuration that A3 defines (architecture §2.2: `private`, `government`, `ngo`, `community`, `outreach` — presets, never a deployment pattern) to mature |
| Microservice split (A1) | ADR-SAAS-002 | Target, not MVP; transitional compromises stay until then. It is what turns `EQ-4`'s single transaction into an outbox |
| Payment integration | ADR-SAAS-008 (`OWNER-APPROVED` out of scope) | V2.5 §21 |
| Per-tenant custom domains | — | Not required by any approved document |

Multi-membership is **no longer** on this list: O-SaaS-7 adopted it and it moved into Phase 2 (§5.2.1).

**MFA for platform operators is no longer on this list either.** O-SaaS-15 makes it a precondition of
production platform access, not a post-launch hardening item, so it is gated in §9.6 and carries no
Phase 5+ entry. A requirement that **blocks** a launch does not belong in a list of items that block
nothing.

A deferred item is **not** a half-built item: nothing in Phases 0–4 depends on these, and none of them
leaves a stub in the code. If a deferred item later becomes required, it enters as a new phase with its
own gate, not as an increment to a finished one.

---

## 9. Cross-cutting gates

These apply to every phase; a phase report that omits one is incomplete.

### 9.1 Migration gate

| Rule | Source |
|---|---|
| one linear Alembic chain; no second chain, ever | `.clinerules` §3; architecture §7.5 |
| forward-only and idempotent; a mistake is fixed by a new revision | `.clinerules` §3 |
| `organization_id` on every new tenant table; no second tenant column | architecture §7.1 D-1 |
| a migration that seeds **decisions** (plans, prices, limits) is rejected | subscription spec §12.1 |

### 9.2 Test gate

| Rule | Source |
|---|---|
| new behaviour ships with its named tests from the specification | subscription spec §13; tenant spec §13; IAM spec §12.3 |
| a passing suite alone is not `VERIFIED` | `.clinerules` §7 |
| the five non-negotiable entitlement tests never regress | roadmap §4.4 |

### 9.3 Audit gate

Every state-changing action introduced by a phase writes an audit row in the **same transaction**, and
a denial is audited rather than swallowed. An action that cannot be audited yet (platform-scope, until
ADR-SAAS-009 resolves) is not shipped — it is deferred to the phase where the audit path exists.

### 9.4 Change-control gate

| Rule | Detail |
|---|---|
| no destructive git operations | `.clinerules` §9: never `reset --hard`, `clean -fd`, `stash`, `checkout .` |
| rollback by revert | `git revert` of the specific offending commit |
| a file already dirty before the task is never staged with unrelated work | check `git diff <file>` first |
| no staging or committing without the owner's instruction | the set was committed only when the owner instructed it (`597d9b1`, 2026-11-17, branch `hackathon-mvp`, pushed to `origin/hackathon-mvp`); later documentation amendments follow the same rule — see the reconciliation report §M |

### 9.5 Documentation gate

| Rule | Detail |
|---|---|
| a new or moved document is registered in `docs/governance/AMSDP_Docs_Index_V1.0.md` in the same task | `.clinerules` §12 |
| a move or rename has a manifest entry with before/after SHA-256 | `.clinerules` §11 |
| the phase report goes to `docs/implementation/`, not the repository root and not `ai_factory/docs/` | `.clinerules` §11 |

### 9.6 Production launch gate — platform operator MFA (O-SaaS-15)

O-SaaS-15 is a **launch requirement with a time-boxed exception**. It is the only gate in this
document not attached to a phase, because it protects a transition no phase performs: from
*demonstration* to *production platform access*. It is **not** a Phase 5+ item and it is not deferred.

| Context | What is allowed | What is required |
|---|---|---|
| **Hackathon MVP** | platform authentication with a password only, **inside a documented exception** | the exception is recorded as a security risk; access under it is restricted to a **limited, authorised operator group** (named accounts, no shared credentials); nothing else in §9.3 is relaxed |
| **Production launch** | nothing — the exception does not travel | **MFA enforced for every platform operator account before production access is granted** |
| **Post-launch** | — | MFA is **already in place**. It is not a backlog item and not an optional enhancement |

**Prerequisite, stated without inventing a mechanism.** A second factor needs a channel to deliver
the factor itself. No provider, protocol or enrolment flow is selected anywhere in this set, and none
is implemented, tested or verified. The Phase 4 notification worker (§7) is the only delivery path
this roadmap identifies, which makes it a **candidate** prerequisite, not a chosen design; selecting a
mechanism is engineering work with its own change record, not an owner decision, and it does not
reopen O-SaaS-15.

**Gate — production platform launch is blocked until every item is true:**

- [ ] A second factor is required at platform login for **every** platform operator account, enforced
      server-side — not by hiding or disabling a form field
- [ ] A platform login attempt without the second factor is **refused and audited** as a denial
- [ ] The hackathon exception is **retired**: no account, environment or leftover flag keeps it usable
- [ ] The authorised operator group is documented, and every change to its membership is audited
- [ ] The evidence is a live attempt recorded against the running build (`VERIFIED`); the gate cannot
      be satisfied by text in this document

**Evidence status: `NOT IMPLEMENTED`.** No second-factor capability exists in the tree today — the
platform identity domain itself is absent (audit §4.5). This subsection states a requirement and a
gate; it claims no implementation, and no phase exit gate above may be read as satisfying it.

---

## 10. Dependency map

Read as "X cannot start until Y has landed". Only cross-phase and cross-document dependencies are
shown; intra-phase ordering is in each phase's own subsection.

```
Phase 0 (verification)
   └─> Phase 1 schema ──> Phase 1 resolver ──> Phase 2 gates
                                                  ├─> Phase 2 platform identity (O-SaaS-1)
                                                  └─> Phase 3 platform operations
                                                          ├─> Phase 3 closure (O-SaaS-16)
                                                          └─> Phase 3 support grant (O-SaaS-13)
Phase 4 notification worker ──> Phase 4 notices ──> Phase 4 scheduler activation
                             └─> Phase 4 self-service reset
```

| Dependency | Why it is hard |
|---|---|
| resolver → gates | a gate without a resolver has nothing to enforce |
| `entitlements_version` → cache | the bump is meaningless without the compare |
| lifecycle column → lifecycle enforcement | the state must exist before it can be read |
| platform identity (Phase 2) → platform operations (Phase 3) | the operator plane needs a principal that is not a tenant user |
| plan catalogue (Phase 3) → subscription creation | no plan, no subscription (R-6 would deny everything) |
| notification worker (Phase 4) → scheduler activation | notice before degradation (§7.3) |
| ADR-SAAS-009 (Phase 2) → platform-scope audit (Phase 3) | the audit store must exist before platform actions need it |

Two dependencies are commonly reversed by accident and are called out because of it:

1. **Plan authoring before platform identity.** Tempting because authoring plans is the "product"
   work; but without the operator principal, plan authoring has no authorized actor and would be
   done by SQL — the exact bypass the set forbids.
2. **Scheduler before the worker.** Tempting because the scheduler is small; but a degrade without
   notice is the failure mode the lifecycle is designed around.

---

## 11. Risk register

| # | Risk | Phase | Mitigation | Residual |
|---|---|---|---|---|
| K-1 | Enforcement lands before the seeded plans are correct, locking out the demo | 2 | Phase 1 ships dark; backfill verified before the flag flips | low |
| K-2 | `entitlements_version` forgotten on a write → stale entitlement | 1–3 | writer self-check (subscription spec §8.4) + test | low |
| K-3 | Role rename leaves a token or a test asserting `super_admin` | 2 | staged rename (IAM spec §7.4) with both names accepted for one release | medium |
| K-4 | Platform scope accidentally reachable from a tenant token | 2 | separate principal domain + `test_cross_tenant_still_404` | low |
| K-5 | Lifecycle gate placed before the scope check → `404` masked as `403`, or a leak | 2 | pipeline order is a test, not a convention (architecture §5.1) | low |
| K-6 | New platform tables create a second migration story | 1 | all tables in the single chain (audit C-6) | low |
| K-7 | Scheduler double-transitions on restart | 4 | advisory lock + compare-and-set + idempotency test | low |
| K-8 | Expiry degrades a tenant before any notice can be sent | 4 | scheduler gated behind the worker (§7.3) | **accepted until Phase 4** |
| K-9 | Operator-assisted reset leaks a code (O-SaaS-12 allows returning it, under constraints) | 2 | authenticated operator + audited request + one-time code + no code in any log (IAM spec §6.2) | medium |
| K-10 | Scope creep into billing during Phase 3 | 3 | ADR-SAAS-008 states the boundary; any price field is a review reject | low |
| K-11 | The six documents drift from the code as phases land | all | each phase report re-checks its cited sections; the index is updated in the same task | medium |

K-8 is the one residual this roadmap cannot close: until Phase 4, a tenant can be degraded without a
notice. The specifications accept that explicitly (tenant spec §5.4) rather than pretending a banner
is a notice.

---

## 12. Abort criteria

A phase is stopped, not pushed through, when any of these is true. "Stop" means: report, do not merge
further, do not delete anything.

| Trigger | Action |
|---|---|
| The demo flow fails and the cause is not identified within the phase | stop; revert the offending change |
| A cross-tenant request returns anything other than `404` | stop immediately — this is a §3 non-negotiable breach |
| An audit row is missing for a shipped state change | stop; the change is not shippable without it |
| A secret appears in a log, report or commit | stop; rotate, remove, record the incident |
| A migration requires editing an applied revision | stop; write a new forward revision instead |
| A "temporary" per-tenant enforcement bypass is proposed | reject — architecture §11.3 |
| Two consecutive phase exit gates are unmet for the same reason | stop and re-plan; the design assumption is probably wrong |

Abort is not failure. A phase that stops with a written cause is worth more than a phase that ships a
bypass to a green dashboard — `.clinerules` §7 exists precisely to make that distinction visible.

---

## 13. Traceability — audit finding to phase

Every finding from the audit is placed, so nothing is orphaned and nothing appears in a phase
without a reason.

| Finding | Phase | Work item |
|---|---|---|
| R-01 no commercial persistence | 1 | 1.1–1.3 |
| R-02 no enforcement point | 2 | 2.4 |
| R-03 tenant writes own status | 2 | 2.2 |
| R-04 audit `before`/`after` identical | 2 | 2.3 |
| R-05 no provisioning | 3 | 3.1, 3.3 |
| R-06 no platform identity domain | 2 | 2.5 |
| R-07 no revocation/refresh/logout | 2 | 2.7 |
| R-08 no password reset/policy | 2 (policy), 4 (self-service) | IAM spec §4.6, §6 |
| R-09 no membership model | 2 | 2.12–2.14 (`EQ-1…3`) |
| R-10 fail-open `AMSDP_ENV` guard | 2 | 2.6 |
| R-11 no counting | 1 | 1.9 |
| R-12 modules only as prose | 1 | 1.1 |
| R-13 no platform-scope audit | 2 (table + dual write), 3 (use) | 2.15, 3.10 |
| R-14 no read-only mode | 2 | 2.1 |
| R-15 no commercial metadata | 3 | 3.9 |
| R-16 unvalidated `config` | 1 | 1.11 |
| R-17 no platform UI | 3 | 3.8 |
| R-18 no closure semantics | 3 | 3.7 |

| Comparable finding | Phase | Note |
|---|---|---|
| C-1 database-per-service divergence | — | constraint recorded, not a defect to fix (ADR-SAAS-002) |
| C-2 platform console absent | 3 | 3.1, 3.8 |
| C-3 lifecycle unread | 2 | 2.1 |
| C-4 `super_admin` naming | 2 | 2.8 |
| C-5 single-tier product | 1–3 | the whole set |
| C-6 shared schema coupling | all | release coordination, §9.1 |
| C-7 platform audit shape | 2 | O-SaaS-2 option A settled; table in 2.15, consumed in 3.10 |
| C-8 secret fallback | 2 | 2.6 |
| C-9 unbounded operator reach | 2 | 2.9 |

---

## 14. Governance and skill compliance

| Requirement | Compliance |
|---|---|
| `.clinerules` §2 automatic routing | domains applied: documentation (this document's own subject), plus the domains its phases touch — backend API, auth/RBAC, multi-tenant data, database/migrations, frontend, audit, deployment, LLM/agent tooling (none used) |
| `.clinerules` §3 non-negotiables | no secrets (§7.5 gate, §9.4); server-side authorisation only (§5.4); `404` on cross-tenant preserved as an abort trigger (§12) and re-asserted for membership switching (§5.6); single tenant key and single migration chain (§9.1); audit append-only (§9.3); forward-only migrations (§9.1); no capability claimed unbuilt (whole document is `SPECIFIED`; §7.4 names the missing notification specification instead of inventing one) |
| `.clinerules` §4 domain table | governance documents read and applied: `saas-cicd-workflow.md` (adapted — git safety, honest CI state), `saas-multitenant-data.md` §4–5, `saas-application-security.md` (adapted), `saas-observability.md` (adapted), BR §37–§42, V2.5 §C/§D/§19/§21/§30 |
| `.clinerules` §5 skills | **no skills installed** — verified absent (`.clinerules/skills/`, `.claude/skills/`, repo `skills/`); none used, none claimed |
| `.clinerules` §6 compliance reporting | this section; each future phase report repeats it |
| `.clinerules` §7 evidence standard | every gate is a future act; nothing in this document is graded `TESTED`, `VERIFIED` or `ACCEPTED` |
| `.clinerules` §9 execution boundaries | no code executed, no service started, no suite run, no git state changed |
| `.clinerules` §11 output location | written to `docs/architecture/saas/` (§15) |
| `.clinerules` §12 reading policy | the index, the audit and all four sibling specifications read before sequencing; siblings cited by section, never paraphrased |

### 14.1 Self-check

- Does any phase require an undecided question to be guessed? No — §4.1, §5.1, §6.1 list the rulings the
  phase depends on, and all sixteen are decided. The eight `EQ` questions are named where a phase needs
  their answer and gate that phase, so nothing is guessed either.
- Can a phase ship a temporary bypass? No — §12 rejects it, and the one accepted flag is deleted in
  Phase 2 by an explicit gate.
- Is there a phase whose exit cannot be observed? No — every gate is a command, a live call or a
  document.
- Does the roadmap claim the notification worker exists? No — §7.1 states it does not, and §7.4 names
  the specification gap.
- Can the demo break silently? No — Phase 2's exit gate is the demo re-run itself, and §3.3 refuses to
  start Phase 1 on a broken baseline.
- Can a tenant be suspended or closed by one operator? No — O-SaaS-14/16 are sequenced as 3.11 before
  3.12, and §6.5 refuses the phase if a single identity can complete either action.
- Can a production platform launch happen without a second factor? No — §9.6 is a **gate**, not a
  phase: MFA blocks production platform access, and the hackathon exception is documented, restricted
  to a named operator group, and retired at that gate. Nothing in Phases 0–5+ satisfies or replaces it.
- Is anything in this document already implemented? No.

---

## 15. Document control

| Field | Value |
|---|---|
| Written to | `docs/architecture/saas/` (`.clinerules` §11: existing `architecture/` subject folder, one leaf) |
| Shape authority | `AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` §3–§11 |
| Evidence base | `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` R-01…R-18, C-1…C-9 |
| Cross-referenced by | architecture specification §11.1 (Phase-1 exit gate = §4); the audit §14.2 (question table with the 2026-11-17 rulings, R-17) |
| Decisions applied | O-SaaS-1…16 and A1–A4 (architecture specification §14.3 / §1.5); `EQ-1…8` named where a phase depends on them |
| Code, schema, migration, compose, frontend changes | **none** |
| Runtime verification | **none claimed** |
| Index registration | `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Revision | V1.0 — 2026-11-17; **Revision 2** — 2026-11-17 (owner decision reconciliation); **Revision 3** — 2026-11-17 (post-commit O-SaaS-15 correction) |

### 15.1 Revision history

| Revision | Date | Change | Authority |
|---|---|---|---|
| V1.0 | 2026-11-17 | Initial roadmap: six phases, gates, abort criteria, risk register, traceability; five decision gates left open | specification-only draft |
| **Revision 2** | 2026-11-17 | Owner decisions applied: §4.1/§5.1/§6.1 converted from "decisions required" to "decisions applied"; **multi-membership moved from Phase 5+ into Phase 2** (2.12–2.14, `EQ-1…3`, §5.2.1); platform audit table 2.15 with `EQ-4`; two-person suspension/closure primitive 3.11 → 3.12 (O-SaaS-14/16); closure retains data (O-SaaS-16); support grants need consent for `grace` tenants too (O-SaaS-13); deferred list re-labelled (MFA, password history, P2/P3 + `EQ-6`, A1, payment); `PROPOSED` → `SPECIFIED`; revision history added | Product Owner, 2026-11-17 |
| **Revision 3** | 2026-11-17 | Post-commit corrections to two records. **O-SaaS-15 restated** — operator MFA is a **production-launch requirement** with a temporary, documented, restricted hackathon exception, not a Phase 5+ deferral or a post-launch hardening item. Phase table row 5+ no longer lists MFA; §6.1 row rewritten; §8 deferred list entry removed and explained; **new §9.6 production launch gate** (three contexts, candidate prerequisite, five gate checks, evidence `NOT IMPLEMENTED`); §14.1 gained the gate self-check; §8's P3 row replaced the stale "internal/dedicated" A3 wording with the five approved profiles; §9.4 change-control row records the owner-instructed commit `597d9b1`. No phase, dependency or other gate changed; nothing labelled `IMPLEMENTED`, `TESTED` or `VERIFIED` | Product Owner decision O-SaaS-15 and direction A3, restated without reinterpretation |

### 15.2 What Revision 2 did not do

- It did not build anything, run anything or start any service; no gate in this document is satisfied.
- It did not renumber phases — Phase 2 grew, the ordering argument survives, and the demo-breaking
  phase remains Phase 2.
- It did not answer an `EQ` question; it placed each one where its answer is needed.

### 15.3 What Revision 3 did not do

- It did not add, remove or renumber a phase; §9.6 is a cross-cutting gate, exactly like §9.1–§9.5.
- It did not implement MFA, choose a provider or protocol, or schedule the work. Every gate box in
  §9.6 is unsatisfied, and the capability is `NOT IMPLEMENTED`.
- It did not change O-SaaS-15's substance, any other `O-SaaS` ruling, any `A1–A4` direction, or any
  `EQ` question (`EQ-4`, `EQ-5` and `EQ-7` are still open).
- It did not touch application code, schema, migrations, deployment files, tests or any phase report.
