# AMSDP — Master Implementation Plan and Roadmap

> **Task ID:** `AMSDP-PLAN-MASTER-IMPLEMENTATION-ROADMAP-2026-11-24`
> **Version:** 1.0 · **Date:** 2026-11-24
> **Status:** **PROPOSED — awaiting Product Owner authorisation.** Nothing here is authorised for execution by its own existence; `.clinerules` §1 precedence applies (owner instruction > AMSDP governance > engineering rules).
> **Derived from:** `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (same task, same date). Every task traces to a numbered finding (GAP-nn) or decision (PO-nn) in that audit.
> **Supersedes:** the unpersisted `T-1 … T-12` roadmap delivered in-response on 2026-11-23, which was never written to the repository and never executed. §5.4 records where each T-item went.
> **Scope:** the `hackathon-mvp` branch to demonstrable readiness, then the approved product beyond it, in dependency order. The clinical module families (`V2.5` Parts III–VI) are **out of scope** and are not authorised by this plan.
> **Owner:** Product Owner.

---

## 1. Purpose and how to use this plan

This is the single implementation plan for AMSDP. It exists because the audit established that **no comprehensive plan had ever been persisted**: what existed was one programme plan (`QUE-006_MASTER_IMPLEMENTATION_PLAN.md`), one state report, two phase-level gap analyses and a backlog — none of which reconciles the nine requirement documents against the code.

**How to use it.**

1. Read §5 for the roadmap, then §6 for the work package containing your task.
2. Do not start a task whose dependencies (§6 "Depends on") are unmet.
3. Do not start a task marked **GATED**: it needs a recorded owner decision from §4.
4. A task closes only when its **Acceptance & verification** cell is satisfied by an artefact, never by a claim. `.clinerules` §7 governs: IMPLEMENTED ≠ TESTED ≠ VERIFIED ≠ ACCEPTED.
5. Report completion into `docs/implementation/` with a Governance and Skill Compliance section (`.clinerules` §6).
6. When reality diverges from this plan, **amend this plan** (new version) rather than deviate silently.

**Estimate convention.** `Est` is engineer-days for one competent engineer including tests and the report — an estimate, not a measurement and not a commitment. No calendar dates are assigned: sequence is meaningful, duration is not.

---

## 2. Authority, inputs and precedence

### 2.1 Inputs

| Tier | Document | How this plan uses it |
|---|---|---|
| **T1 — binding** | `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/AMSDP_Business_Rules_V1.1.md` | Rule-level acceptance for every backend task |
| **T1 — binding** | `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, `docs/AMSDP_MVP_SCOPE_V1.1.md` | Release boundary; §12 is the demo acceptance script; §16 overrides §7 where the addendum says so |
| **T2 — approved catalogue** | `docs/AMSDP_Master_Feature_List_V2.5_…_Intelligent_Clinical_Documentation.md` | Module/family classification; §F hackathon boundary; §G status vocabulary |
| **T3 — design source** | `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` | Screens, mandatory UI rules; the analytics specification is unapproved (PO-06) |
| **T4 — historical** | `…V2.0_Draft`, `…V2.1/V2.2/V2.3_Consolidated_Draft`, `…V2.4_Modular_Healthcare_Platform_Edition` | Rationale and decision trail only; V2.4 clinical content is superseded by V2.5 |
| **Evidence** | `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | Code-level truth for the baseline |

### 2.2 Precedence inside this plan

1. Verified runtime state.
2. Owner decisions recorded in `docs/decisions/` and in §4 below.
3. Binding product documents (T1).
4. AMSDP governance (`.clinerules`, governance assessment).
5. This plan.

Where this plan contradicts a T1 document, **the T1 document wins** and this plan carries a defect.

### 2.3 Constraints carried in from the codebase — do not re-litigate

- `organization_id` is the only tenant key. No second tenant column, ever.
- Cross-tenant and cross-branch denial returns **404**, never 403.
- The principal's org and branch derive from the authenticated token, never from a request body.
- Audit is append-only; denials are recorded, never swallowed.
- Every schema change is a forward-only, idempotent Alembic migration on the single head `c4d8e2a91f60`.
- The UI is never a security boundary; every gate is re-checked server-side.
- No secret, token or credential appears in code, fixture, log, report or commit message.

---

## 3. Baseline and planning assumptions

### 3.1 Verified baseline

| Area | State |
|---|---|
| Phases 0–3 | Implemented and committed; Phase 3 **not ACCEPTED** — never exercised on hardware |
| Runtime | Not verifiable from this checkout; live DB two revisions behind head |
| Queue | check-in → call → start → complete works; **no recall**; priority absent; skip only as "missed turn" |
| Tokens | Atomic daily serial, doctor scope only; no continuous mode; no printed token |
| DQDS / PQT | Implemented and tested; **day-boundary defect**; tracking rate limit is in-process |
| QUE-006 | W1/W2/W4/W7 implemented; W3 API-only (no UI); W5 agent-only; audibility unproven |
| Notifications | Two-stage lifecycle implemented against a **mock** provider; worker not a compose service |
| Audit | Implemented incl. denial audit; schedule-edit audit unverified |
| Admin surfaces | Staff, orgs and branches pages are list+create only; capability grants and assignments are API-only |
| Reports / analytics / subscription | Absent |
| Clinical modules (V2.5) | Absent — and out of scope |

### 3.2 Planning assumptions — correct these and the plan changes

- **A-1** The Ubuntu host remains the runtime target; Windows remains the development workstation.
- **A-2** Ordering is dependency-driven; no external deadline is fixed by this plan.
- **A-3** `AMSDP_Business_Rules_V1.1.md` stands as written until the owner decides **PO-02**. Tasks that would depend on the contested clauses are unaffected because DQDS and SMS are already built.
- **A-4** MVP Scope §12 is the acceptance script for the hackathon release.
- **A-5** Clinical families stay out until a separately authorised programme.

---

## 4. Decision gates — Product Owner

**None of these is a question the agent may answer.** Each blocks the tasks named against it. Full statements appear in audit §11.

| Gate | Decision | Blocks | Assumption used meanwhile |
|---|---|---|---|
| **PO-01** | Publish Phases 4, 5, 6 — names, scope, exit criteria, accepting authority | MP-30, all Phase 4–6 reporting | Phase 4 = tracking hardening; Phase 5 = reporting/localisation; Phase 6 = acceptance |
| **PO-02** | BR §33/§35/§36 vs MVP §16: which prevails for DQDS and SMS | Nothing at code level (both built); affects acceptance wording | MVP §16 prevails as the later amendment |
| **PO-03** | Ratify or reclassify appointment symptoms/onset capture | Documentation only | Feature stands as implemented |
| **PO-04** | Assign a phase to overbooking (§22), priority (§28), subscription (§37–§39) — or defer | MP-09, MP-13, MP-21 | Overbooking and priority post-demo P1; subscription deferred |
| **PO-05** | Authorise W3 admin UI and W5 server API | **MP-04**, MP-26 | Neither is built until authorised |
| **PO-06** | Classify the Blueprint Analytics Specification (7 open decisions) | MP-27 | Deferred entirely |
| **PO-07** | Confirm subscription lifecycle phase | MP-21 scope | Deferred |
| **PO-08** | Batch D-3, D-5, D-7, O-2, POD-2, POD-6, POD-7, POD-1/3/8/9/10/11 | MP-04 language flags, asset cleanup | None assumed; items stay open |
| **PO-09** | Authorise correction of stale owner-controlled documents | MP-34 | No owner document is touched |
| **PO-10** | Infrastructure: bind PostgreSQL to `127.0.0.1`; decide SSH transport | Not on the critical path | Recorded as an open security item |
| **PO-11** | D-1/D-2 doctor-branch contract | Completeness claims only | Current fail-closed behaviour retained |
| **PO-12** | Approve a feature-key scheme (`F-nn`) for traceability | §11 maintenance | Local keys used, mapped to source sections |

---

## 5. Roadmap

### 5.1 Shape of the plan

Nine work packages, **34 tasks**, ordered so that nothing is verified before it can be, and nothing approved is built before its owner decision exists.

| WP | Name | Phase | Tasks | Purpose |
|---|---|---|---|---|
| **WP-A** | Release integrity | 3 → 6 precondition | MP-01 … MP-04 | Make the system run and prove the suite; close QUE-006 at runtime |
| **WP-B** | Demo-blocking defect bundle | 3 / 6 | MP-05 … MP-07 | Remove the three defects that break the demo |
| **WP-C** | Queue completeness | 3 | MP-08 … MP-12, MP-24 | Recall, priority, policy semantics, token modes, print, history |
| **WP-D** | Appointment and scheduling completion | 2 | MP-13 … MP-18 | Overbooking, grace, deadlines, blocked periods, duplicate allowance, schedule audit |
| **WP-E** | Administration surface | 1 | MP-19 … MP-21 | Staff/permission UI, assignment editor, subscription lifecycle |
| **WP-F** | Reporting and dashboard | 5 | MP-22 … MP-23, MP-27 | Operational reports, dashboard completion, analytics |
| **WP-G** | Localisation and usability | 5 | MP-28 … MP-29 | One i18n mechanism; responsive/touch/a11y pass |
| **WP-H** | Tracking and handoff | 4 | MP-25, MP-30 | Tracking hardening; staff handoff (undefined — PO-01) |
| **WP-I** | Acceptance and truth | 6 | MP-31 … MP-34, MP-26 | End-to-end acceptance, rehearsal, CI truth, documentation truth |

### 5.2 Critical path

```
MP-01  Restore runtime + migrate live DB to c4d8e2a91f60
  │
  ├── MP-02  Whole-tree suite re-baseline
  │     ├── MP-03  QUE-006 runtime closure  (only if voice is demoed)
  │     └── MP-08  Recall action ─────────────┐
  │                                           │
  ├── MP-05  Seed doctor assignment ───────┐  │
  ├── MP-06  DQDS operational day ─────────┤  │
  └── MP-07  Dashboard Waiting tile ───────┤  │
                                           ▼  ▼
                              MP-31  End-to-end acceptance (MVP §12)
                                           │
                              MP-32  Demo rehearsal ×2
                                           │
                                       DEMO READY
```

**Minimum viable demo path:** MP-01 → MP-02 → MP-05 → MP-06 → MP-07 → MP-31 → MP-32 (≈ 5.75 engineer-days, dominated by MP-02). MP-03 is required only if the voice feature is demonstrated; MP-08 only if the script calls a patient twice.

### 5.3 Milestones

| Milestone | Definition | Tasks |
|---|---|---|
| **M-1 Runtime restored** | Stack healthy, schema at head, evidence recorded | MP-01 |
| **M-2 Baseline trusted** | Full suites executed on the migrated DB; every failure named | MP-02 |
| **M-3 Demo-ready** | MVP §12 script passes end to end on the live stack | MP-05, MP-06, MP-07, MP-08, MP-31, MP-32 |
| **M-4 Queue complete** | BR §26–§32 satisfied, including recall, priority and print | MP-09 … MP-12, MP-24 |
| **M-5 Scheduling complete** | BR §15, §19–§20, §22 satisfied | MP-13 … MP-18 |
| **M-6 Administration complete** | All Phase 1 management achievable from the UI | MP-19, MP-20 |
| **M-7 Reporting complete** | BR §43 reports live and reconciled | MP-22, MP-23 |
| **M-8 Phase 4–6 closed** | Only after PO-01 defines the phases | MP-25, MP-30 |

### 5.4 Disposition of the prior roadmap (T-1 … T-12)

| Prior | Disposition |
|---|---|
| T-1 Runtime restoration | → **MP-01** (unchanged, still first) |
| T-2 Three-file repair bundle | → **MP-05 + MP-06 + MP-07** |
| T-3 Full-suite re-baseline | → **MP-02** |
| T-4 Cancel/reschedule/no-show regression | → **MP-02b** |
| T-5 G10 delivery closure | → **MP-03** |
| T-6 Audibility closure (B-8) | → **MP-32** (human, at rehearsal) |
| T-7 W3 voice-pack admin UI | → **MP-04** (GATED, PO-05) |
| T-8 W5 distribution API | → **MP-26** (deferred) |
| T-9 Priority entries | → **MP-09** |
| T-10 Recall action | → **MP-08** |
| T-11 Printed token | → **MP-12** |
| T-12 Documentation truth-up | → **MP-34** (GATED, PO-09) |

**Nothing in the prior roadmap is discarded**, but ten of the twelve were re-scoped and four were re-prioritised after the code was actually read.

---

## 6. Work packages and tasks

**Legend.** `Pri`: P0 = blocks the demonstration or blocks all verification; P1 = approved MVP obligation; P2 = approved but not demo-blocking; P3 = deferred. `GATED` = needs the named owner decision before work starts. Every acceptance cell is written so that it can be failed.

### WP-A — Release integrity

| ID | Task | Current state | Pri | Depends on | Deliverables | Acceptance & verification | Est | Risk |
|---|---|---|---|---|---|---|---|---|
| **MP-01** | **Restore the runtime.** On the Ubuntu host: `_tools/pg_backup.sh` → `alembic upgrade head` → `_tools/amsdp_rebuild.sh`; probe `:8000`/`:3000`; record `alembic current` | Live DB `a9c4e1f7b2d8`, head `c4d8e2a91f60`; no stack verifiable | **P0** | Owner authorisation, host access | Backup artefact, migration log, container list, health JSON | `GET :8000/health` and `:3000` both 200; `alembic current` = `c4d8e2a91f60`; `voice_packs` and `queue_announcement_deliveries` exist in the live schema; all compose services up | 0.5 | Migration failure (chain is single-headed, VERIFIED); DB outage (mitigated by backup) |
| **MP-02** | **Whole-tree suite re-baseline** on the migrated database, plus the Phase-2 cancel/reschedule/no-show regression sweep (**MP-02b**) | Last recorded 790 pass / 1 fail (DOCUMENTED) | **P0** | MP-01 | Executed logs for backend pytest and frontend `npm test` | Every test executed; every failure named with cause; no pass claimed without output | 1.0 | Long-standing failures surface; that is the purpose |
| **MP-03** | **QUE-006 runtime closure**: announce from the staff board against the live stack | IMPLEMENTED, never exercised on hardware | **P0** | MP-01, MP-02 | Evidence record: request, delivery row, audit row, browser log | One `call` produces exactly one `queue_announcement_deliveries` row and one audit event; audio audible on the target device | 1.0 | No audio device (B-8) → record BLOCKED, never "passed" |
| **MP-04** | **W3 voice-pack admin surface** (preview / publish / retire) | API-only | P1 **GATED (PO-05)** | MP-01 | Page, tests, report | An operator configures and publishes a pack without curl; every `voice_pack_policy.py` refusal still enforced server-side | 3.0 | New UI must not weaken the policy layer |

### WP-B — Demo-blocking defect bundle

| ID | Task | Current state | Pri | Depends on | Deliverables | Acceptance & verification | Est | Risk |
|---|---|---|---|---|---|---|---|---|
| **MP-05** | Seed a `staff_doctor_assignments` row for the demo doctor (and assistant); replace `date.today()` with `operational_today` at `seed/seed_demo.py:699,744` | **VERIFIED missing / VERIFIED wrong** | **P0** | MP-01 | Seed change, re-seed, assertion | Doctor login → own queue **200**; another doctor's queue **404**; seeded "today" data matches the facility day at 01:00 Dhaka | 0.5 | Over-granting — assign exactly one doctor, no capability widening |
| **MP-06** | `queuing/display.py:138` → `operational_today(session, org)` | **VERIFIED defect** | **P0** | — | One-line fix, regression test | New test pins a 01:00-Dhaka instant and asserts today's tokens appear; existing `test_dqds.py` stays green | 0.5 | Org resolution added to a public endpoint — must remain org-scoped |
| **MP-07** | Dashboard "Waiting" tile → `today.in_queue` | **VERIFIED defect** | **P0** | — | One-line fix | A queued-but-not-called patient makes the two tiles differ | 0.25 | None |

### WP-C — Queue completeness

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-08** | **Recall** transition (`called → called`), distinct event, UI control, announcement-safe | **P0** | MP-02 | Two calls for one entry produce two delivery rows with distinct `qce:` keys; both audited; position unchanged | 1.5 |
| **MP-09** | **Priority** assign/remove: permission, field, endpoint, audit before/after, queue badge | P1 **GATED (PO-04)** | MP-02 | BR §28 satisfied; ordering changes only through an authorised, audited action; no clinical wording in the UI | 2.0 |
| **MP-10** | Walk-in **policy configuration** persisted per facility (incl. a real `reserved_capacity` pool); retire the per-request parameter | P1 | MP-02 | BR §25/§52: four *distinct* behaviours proven by tests; a policy change never reorders an active queue; the change is audited | 3.0 |
| **MP-11** | Token numbering **modes** (daily / continuous) and **scope** (doctor / room) | P1 | MP-10 | BR §31/§52: both modes; reset preserves history; concurrency test at fixed day boundary | 2.0 |
| **MP-12** | **Printed token** layout (browser print, no PII) | P2 | MP-11 | BR §32/§53: printed token equals assigned token; no mobile number on the artefact | 1.0 |
| **MP-24** | **Queue history** screen consuming `/queue/history` | P2 | MP-01 | Branch-scoped; cross-branch returns 404; history survives completion | 1.0 |

### WP-D — Appointment and scheduling completion

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-13** | **Overbooking**: configuration (disabled by default), per-doctor/schedule/date limits, mandatory reason, audit | P1 **GATED (PO-04)** | MP-02 | BR §22: disabled ⇒ explicit 422; enabled ⇒ constrained by the configured limit; every override audited with reason and actor | 3.0 |
| **MP-14** | **No-show and late-arrival grace** configuration plus a *potential* flag (never an automatic `NO_SHOW`) | P1 | MP-13 (shared config surface) | BR §20/§21: status changes only on staff confirmation, audited; grace thresholds configurable per facility | 2.0 |
| **MP-15** | **Cancellation deadline** and restriction policy | P2 | MP-14 | BR §19: permitted/forbidden paths behave as configured; a reason is captured in every path | 1.5 |
| **MP-16** | **Blocked periods** — confirm absence, then implement | P1 | — | BR §15: a blocked period cannot be booked unless an authorised exception is used; `available-slots` degrades without error | 2.0 |
| **MP-17** | Doctor mobile **duplicate allowance** (platform-level policy) | P2 | — | BR §9.7: default unique per organisation; the allowance permits duplicates within one organisation only, never across tenants | 1.0 |
| **MP-18** | **Schedule-edit audit** — verify, implement if absent | P2 | MP-02 | Any schedule write produces an audit row with before/after; no silent schedule mutation remains | 1.0 |

### WP-E — Administration surface (Phase 1 completeness)

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-19** | **Staff and permission management UI**: edit, deactivate, role, branch scope, capability grants limited to `DELEGABLE_CAPABILITIES` | P1 | MP-02 | The UI cannot grant beyond the delegable set; self-escalation still 403; last-admin protection intact; every change audited | 3.0 |
| **MP-20** | **Doctor-assignment editor** (multi-doctor for assistants) | P1 | MP-19 | Changes audited as `staff.doctor_assignment_changed`; revocation takes effect on the next request; cross-org assignment returns 404 | 1.5 |
| **MP-21** | **Subscription lifecycle**: model, controls, expiry → read-only, renewal | P2 **GATED (PO-07)** | PO-07 | BR §39: grace → read-only without data loss; renewal restores write access; every transition audited | 5.0 |

### WP-F — Reporting and dashboard (Phase 5)

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-22** | **Dashboard completion**: branch/date selectors, today's queue panel, quick actions, recent activity | P2 | MP-07 | Blueprint §2 parity; every figure filtered by the principal's authorised org and branch; a branch user cannot select another branch | 2.0 |
| **MP-23** | **Operational reports** per BR §43: appointments by day/doctor/branch, status counts, walk-ins, queue activity, utilisation | P1 | MP-01 | Report totals reconcile against `appointments`/`queue_entries` for a fixed day; org and branch scoping enforced with 404 on violation | 4.0 |
| **MP-27** | **Analytics suite** per the Blueprint specification | P3 **GATED (PO-06)** | PO-06 | Not defined until the seven open product decisions are taken | — |

### WP-G — Localisation and usability (Phase 5)

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-28** | **Unify i18n** into `frontend/lib/i18n.js`, remove the page-local `L={bn,en}` dictionaries, add a coverage test | P2 | — | Every visible string resolves in Bangla and English; no page-local dictionary remains; the coverage test fails when a key is missing | 2.0 |
| **MP-29** | **Responsive, touch and a11y pass** on the queue and appointment screens | P2 | — | Core journeys complete at 360 px and on desktop; large hit targets; keyboard reorder works; no control depends on hover | 2.0 |

### WP-H — Phase 4 (tracking and staff handoff)

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-25** | **Tracking hardening**: database-backed rate limit, ETA always labelled "estimated", QR print flow | P2 | MP-01 | The limit survives multiple workers; an expired or revoked token never reactivates; the ETA string carries its estimation label | 1.5 |
| **MP-30** | **Staff handoff** — definition and implementation | P1 **GATED (PO-01)** | PO-01 | Undefined until the owner publishes Phase 4; this plan deliberately does not invent it | TBD |

### WP-I — Acceptance and truth (Phase 6)

| ID | Task | Pri | Depends on | Acceptance & verification | Est |
|---|---|---|---|---|---|
| **MP-31** | **End-to-end acceptance run** of the MVP §11 gate and the §12 demonstration script, with evidence captured | **P0** | MP-01, MP-02, MP-05, MP-06, MP-07 | Every §12 step executed against the live stack with an artefact; every §11 checkbox evidenced or explicitly listed as unmet | 2.0 |
| **MP-32** | **Demo rehearsal**, twice, with the real personas, timed | **P0** | MP-31 | Two clean consecutive runs; every hesitation and failure recorded; audibility confirmed by a human (closes B-8) | 1.0 |
| **MP-33** | **CI first green run**, or an explicit statement that it cannot be executed in this environment | P2 | MP-02 | A green run URL/log, or a recorded BLOCKED with the reason — never a claim | 0.5 |
| **MP-34** | **Documentation truth-up**: `AMSDP_Limitations_Report_V1.0.md:12` (still "in-memory storage"), Feature Catalogue §H.1, and this plan's index registration | P2 **GATED (PO-09)** | Owner approval | No document claims a capability the code does not enforce; this plan and the audit appear in `AMSDP_Docs_Index_V1.0.md` | 1.0 |
| **MP-26** | **W5 server-side distribution API** | P3 (deferred) | MP-04 | Deferred until the voice programme resumes | 4.0 |

---

## 7. Delivery rules — definition of ready, definition of done, evidence gates

These apply to every task in §6. A task that cannot satisfy them is not complete, whatever its code looks like.

### 7.1 Definition of Ready

- The task's **Depends on** column is satisfied, evidenced, not assumed.
- Any **GATED** decision is recorded in `docs/decisions/` or in this plan's §4 as decided.
- The requirement reference (BR section, MVP section, Blueprint section) has been read in this session, not remembered.
- The affected tests are identified before coding starts.

### 7.2 Definition of Done

| Gate | Requirement |
|---|---|
| **D1 — Code** | Implements the named requirement only; no unrelated refactor; follows existing module layout and naming. |
| **D2 — Server-side enforcement** | Any new action is authorised server-side with the existing permission helpers; the UI gate is never the boundary. |
| **D3 — Tenancy** | Every query is scoped by `organization_id` (and branch where applicable); cross-tenant and cross-branch access returns 404. |
| **D4 — Audit** | Every state change that BR §40 names produces an audit row with actor, org, branch, before/after and reason where applicable. |
| **D5 — Migration** | If schema changed: one forward-only, idempotent Alembic revision on head `c4d8e2a91f60`; upgrade verified on a scratch database; no data loss. |
| **D6 — Tests** | Unit or integration tests added for the rule, including the negative path (denial, limit, conflict). |
| **D7 — Execution** | The new tests **and** the surrounding suite were **executed**, and the output is quoted in the report. Unexecuted tests are not a pass. |
| **D8 — Runtime evidence** | For UI or end-to-end work: a browser or API artefact from the running stack. Where the environment makes this impossible, the task reports BLOCKED and names the missing capability. |
| **D9 — Report** | An implementation report under `docs/implementation/` with the Governance and Skill Compliance section required by `.clinerules` §6. |

### 7.3 Evidence vocabulary for reports

`IMPLEMENTED` (code exists and is reachable) → `TESTED` (named tests pass in this tree) → `VERIFIED` (a second independent artefact confirms it: browser run, live call, database read) → `ACCEPTED` (owner has signed it). **A green suite does not make something VERIFIED; documentation does not prove implementation.**

---

## 8. Sequencing rules

1. **Nothing is verified before it can be.** MP-01 precedes every claim; MP-02 precedes every "the suite is green" statement.
2. **Demo paths before completeness.** WP-B before WP-C/D/E/F, even though WP-C contains more approved obligations.
3. **One schema change at a time.** MP-09, MP-10, MP-11, MP-13 and MP-21 each require their own revision; they must not be bundled into one migration.
4. **Configuration before behaviour.** Where a rule is "configurable" (BR §56), the configuration surface is built before the behaviour that consumes it (MP-10 before MP-11; MP-13 before MP-14).
5. **Gated work waits.** MP-04, MP-09, MP-13, MP-21, MP-27 and MP-30 do not start until the named decision exists.
6. **No parallel edits to a shared file without coordination.** `queuing/main.py`, `appointment/main.py` and `common/models.py` are the collision hotspots (MP-08/MP-09/MP-10; MP-13/MP-14/MP-15/MP-16; MP-09/MP-13/MP-21).
7. **Branch discipline.** One branch per work package, merged only after D1–D9; no force-push, no history rewrite.

---

## 9. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-1 | Live database migration fails or loses data | Low | High | `pg_backup.sh` first; chain is single-headed and verified; restore path documented in the runbook | Engineer |
| R-2 | Restored suite fails in ways no report predicted | Medium | Medium | MP-02 is a **baseline**, not a gate: failures are recorded and triaged, not hidden | Engineer |
| R-3 | Demo features regress while post-demo work proceeds | Medium | High | Freeze non-demo code changes after MP-31 until the demonstration is past | Owner |
| R-4 | A GATED task is started without its decision | Medium | High | §7.1 Definition of Ready; the gate is checked in the report | Engineer |
| R-5 | DQDS fix changes public-endpoint behaviour | Low | Medium | Org resolution must stay scoped and cached; regression test at a fixed instant | Engineer |
| R-6 | Recall duplicates announcement or audit rows | Medium | Medium | Distinct event identity (`qce:` key) plus an idempotency test | Engineer |
| R-7 | Priority is misused as a clinical triage signal | Medium | Medium | Permission-restricted, operational wording only, audit on every use; BR §28 non-clinical | Owner |
| R-8 | Test suite remains untrustworthy; "green" is claimed again | Medium | High | D7 requires quoted output; MP-33 refuses to claim CI without a run | Owner |
| R-9 | Owner documents drift further from the code while work proceeds | High | Medium | MP-34 (gated) plus a documentation check in every milestone review | Owner |
| R-10 | Single engineer on the critical path; no reviewer | Medium | Medium | At minimum, one independent read of every migration and every tenancy-touching change | Owner |

---

## 10. Deferred and rejected work

| Item | Decision | Reason |
|---|---|---|
| Analytics suite (MP-27) | **Deferred** | Unapproved source with seven open product decisions (C-6) |
| W5 server-side distribution API (MP-26) | **Deferred** | No consumer until the voice programme resumes; gated on PO-05 |
| W6 asset cleanup (15 unreferenced files) | **Deferred** | Awaiting POD-7; deletion is reversible only from history |
| Clinical modules F-62 … F-66 | **Out of scope** | V2.5 §F excludes them from the hackathon release; separate authorised programme needed |
| Patient portal, self-booking, payments, EMR, SMS provider integration | **Rejected for this plan** | MVP Scope §7 excludes them; provider cost and credentials need explicit authorisation |
| Priority as clinical triage | **Rejected outright** | BR §28 defines priority as operational only; presenting it as triage would misrepresent the product |
| Multi-display DQDS configuration | **Deferred** | BR §33 labels it later-phase and MVP §16 does not add it |
| Automatic no-show status | **Rejected** | BR §20.4 requires staff confirmation; automation would corrupt attendance data |

---

## 11. Traceability — finding to task

| Finding (audit) | Feature keys | Tasks |
|---|---|---|
| GAP-01 live DB behind head / no runtime | all | MP-01, MP-02 |
| GAP-02 missing doctor assignment | F-07, F-28 | MP-05 |
| GAP-03 DQDS day boundary | F-46 | MP-06 |
| GAP-04 dashboard Waiting tile | F-57 | MP-07 |
| GAP-05 no recall / no neutral skip | F-38, F-39 | MP-08 |
| GAP-06 walk-in policy semantics | F-35 | MP-10 |
| GAP-07 token numbering modes | F-43 | MP-11 |
| GAP-08 no priority | F-40 | MP-09 |
| GAP-09 no overbooking | F-31 | MP-13 |
| GAP-10 no grace configuration | F-29 | MP-14 |
| GAP-11 no cancellation deadline | F-30 | MP-15 |
| GAP-12 blocked periods unverified | F-20 | MP-16 |
| GAP-13 doctor mobile duplicate allowance | F-17 | MP-17 |
| GAP-14 no printed token | F-44 | MP-12 |
| GAP-15 no operational reports | F-56 | MP-23 |
| GAP-16 queue history API unused | F-45 | MP-24 |
| GAP-17 thin administration UI | F-09, F-06 | MP-19, MP-20 |
| GAP-18 no voice-pack admin UI | F-50 | MP-04 |
| GAP-19 W5 server API absent | F-51 | MP-26 |
| GAP-20 in-process tracking rate limit | F-47 | MP-25 |
| GAP-21 no subscription lifecycle | F-10 | MP-21 |
| GAP-22 analytics unimplemented/unapproved | F-58 | MP-27 |
| GAP-23 three i18n mechanisms | F-59 | MP-28 |
| GAP-24 CI never proven green | F-61 | MP-33 |
| GAP-25 seed uses `date.today()` | F-07 | MP-05 |
| GAP-26 stale owner documents | — | MP-34 |
| GAP-27 Phases 4–6 undefined | — | MP-30 (gated) |

**Coverage check.** Every GAP maps to at least one task; every task in §6 traces back to at least one GAP or decision. No orphan tasks, no unaddressed findings.

---

## 12. Governance and skill compliance

| Requirement | How it was met |
|---|---|
| `.clinerules` §2 — automatic routing | Domains identified: backend API, auth/RBAC, multi-tenant data, migrations, queue/workflow, audit, deployment, documentation, frontend UX. Each routed row's governance documents were read. |
| `.clinerules` §2 step 3 / §12 — read the index before acting | `docs/governance/AMSDP_Docs_Index_V1.0.md` read first; the nine source documents loaded from it. |
| `.clinerules` §5 — skills | **None installed** (no `.clinerules/skills/`, `.claude/skills/`, repo `skills/`). No skill use is claimed; governance documents were used instead. |
| `.clinerules` §3 — non-negotiables | No secret quoted; `organization_id` retained as the only tenant key; 404-not-403 recorded as required behaviour in every tenancy gate; nothing written outside `docs/`. |
| `.clinerules` §6 — compliance reporting | This section. |
| `.clinerules` §7 — evidence standard | IMPLEMENTED / TESTED / VERIFIED / ACCEPTED kept distinct in every table; §12 of the audit names everything unverified. |
| `.clinerules` §9 — execution boundaries | No suite, migration, container or destructive git command was executed. |
| `.clinerules` §11 — document placement | This plan is written to `docs/plan/` **because the Product Owner explicitly requested a plan folder** in the authorising instruction (precedence level 2). `docs/plan/` did not exist; the closest sanctioned folder would have been `docs/implementation/`. **This is a recorded deviation**, flagged for governance ratification: either add `plan/` to §11's sanctioned list, or migrate this file to `docs/implementation/` with a migration-manifest entry. No existing document was moved, renamed or overwritten. |
| Index registration | Both new documents are registered in an appended annex of `docs/governance/AMSDP_Docs_Index_V1.0.md`, without advancing the revision number because **D-5** (index numbering) remains open. |

---

## Appendix A — Task index

**P0 (demo or verification blocking):** MP-01, MP-02, MP-03, MP-05, MP-06, MP-07, MP-08, MP-31, MP-32
**P1:** MP-04\*, MP-09\*, MP-10, MP-11, MP-13\*, MP-14, MP-16, MP-19, MP-20, MP-23, MP-30\*
**P2:** MP-12, MP-15, MP-17, MP-18, MP-21\*, MP-22, MP-24, MP-25, MP-28, MP-29, MP-33, MP-34\*
**P3 / deferred:** MP-26, MP-27\*

`*` = gated on an owner decision (§4).

**Total estimated effort:** ≈ 55 engineer-days, of which **≈ 5.75** constitutes the path to a demonstrable system.

---

## Appendix B — Command recipes

**MP-01 (Ubuntu host).**

```bash
cd /home/shomonrobie/amsdp
_tools/pg_backup.sh                      # never skip: this is the only rollback
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
_tools/amsdp_rebuild.sh
curl -fsS http://localhost:8000/health
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:3000
docker compose ps
```

**MP-02 (whole tree, on a throwaway or the migrated database).**

```bash
cd backend && python -m pytest -q          # quote the summary line verbatim
cd frontend && npm test                    # 368 tests expected; quote the summary
```

**MP-03 (announcement proof).** Invoke `call` for one queued entry, then read `queue_announcement_deliveries` and `audit_events` for that appointment; the counts must be exactly one and one.

---

## Appendix C — Document control

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-11-24 |
| Status | **Proposed** — not authorised for execution |
| Author | Implementation agent (read-only assessment) |
| Reviewer | Product Owner |
| Supersedes | the unpersisted T-1…T-12 roadmap (2026-11-23) |
| Change rule | amendments create a new version; tasks are never silently re-scoped |
| Companion | `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` |
| Next action | Product Owner decides **PO-01 … PO-12**; no task is authorised to start before **MP-01** is approved |
