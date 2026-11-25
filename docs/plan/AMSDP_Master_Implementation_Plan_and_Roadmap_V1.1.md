# AMSDP — Master Implementation Plan and Roadmap

> **Task ID:** `AMSDP-PLAN-MASTER-IMPLEMENTATION-ROADMAP-2026-11-24`
> **Version:** 1.1 · **Date:** 2026-11-24
> **Status:** **PROPOSED — awaiting Product Owner authorisation.** Nothing here is authorised for execution by its own existence; `.clinerules` §1 precedence applies (owner instruction > AMSDP governance > engineering rules).
> **Supersedes:** **V1.0 (same date)** — not withdrawn: V1.0 is preserved as issued. V1.1 changes exactly one scope decision and adds the tasks that implement it; every other task, gate, estimate and sequencing rule is carried forward unchanged, and Appendix C records the change.
> **Derived from:** `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (same task, same date; amended by A-1) and `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md`. Every task traces to a numbered finding (GAP-nn), requirement (MD-nn) or decision (PO-nn).
> **Supersedes (roadmap artefact):** the unpersisted `T-1 … T-12` roadmap delivered in-response on 2026-11-23, which was never written to the repository and never executed. §5.4 records where each T-item went.
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
| **Evidence** | `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (+ Amendment A-1) | Code-level truth for the baseline |
| **Specification** | `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | Requirements MD-01…MD-12 and acceptance AC-01…AC-14 for **MP-35…MP-40**; it does not override any T1 document and records its own conflicts in its §2 |

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
| Runtime | **Corrected 2026-11-24 (Appendix E).** The deployment answers on `192.168.68.108:8110–8117` and `:3100` (all HTTP 200, VERIFIED this date) and the live DB is at head `c4d8e2a91f60` per the 2026-11-23 verified deployment record — not re-queried from this checkout. What is genuinely missing is a **post-migration suite baseline** |
| Queue | check-in → call → start → complete works; **no recall**; priority absent; skip only as "missed turn" |
| Tokens | Atomic daily serial, doctor scope only; no continuous mode; no printed token |
| DQDS / PQT | Implemented and tested; **day-boundary defect**; tracking rate limit is in-process. **Multi-display configuration is absent** — one branch-wide board, no display registry, no per-screen scope, language or administration (GAP-28) |
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
- **A-6** **Multi-display DQDS is Hackathon Version scope**, principally Phase 3, demonstrated and accepted in Phase 6 (owner instruction 2026-11-24; PQV §B.6; specification `AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md`). If **PO-02** rules that BR §33 prevails, **MP-35…MP-40** leave Phase 3 and the hackathon claim narrows to the single branch board.
- **A-7** A display is an unauthenticated public surface reached by URL. No device pairing, provisioning or heartbeat exists, and none is assumed by any task in this plan.

---

## 4. Decision gates — Product Owner

**None of these is a question the agent may answer.** Each blocks the tasks named against it. Full statements appear in audit §11.

| Gate | Decision | Blocks | Assumption used meanwhile |
|---|---|---|---|
| **PO-01** | Publish Phases 4, 5, 6 — names, scope, exit criteria, accepting authority | MP-30, all Phase 4–6 reporting | Phase 4 = tracking hardening; Phase 5 = reporting/localisation; Phase 6 = acceptance |
| **PO-02** | BR §33/§35/§36 vs MVP §16: which prevails for DQDS and SMS | Nothing at code level (both built); affects acceptance wording | **DECIDED 2026-11-24 — RESOLVED for DQDS:** no MVP/later-releases tier governs; BR §33 §33.1 carries the approved scope (Appendix D). The SMS half is unchanged and still open |
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
| **PO-13** | **Full-featured multi-display DQDS as Hackathon Version scope** — displays per branch, independent configuration, targeting by branch/doctor/department/room/queue, configurable BN/EN language, server-side filtering and isolation, refresh on change, TV-scale typography, token plus doctor/room, estimate-labelled waiting time, token-only payloads, facility-controlled public fields, read-only access, admin configuration with audit | **Nothing further — DECIDED 2026-11-24: APPROVED.** Authorises **MP-35…MP-46** as roadmap work (sequencing still applies) | Implementation still begins only after **MP-01** and is subject to the documented dependencies, security requirements and acceptance criteria (Appendix D) |

---

## 5. Roadmap

### 5.1 Shape of the plan

Nine work packages, **40 tasks**, ordered so that nothing is verified before it can be, and nothing approved is built before its owner decision exists.

| WP | Name | Phase | Tasks | Purpose |
|---|---|---|---|---|
| **WP-A** | Release integrity | 3 → 6 precondition | MP-01 … MP-04 | Make the system run and prove the suite; close QUE-006 at runtime |
| **WP-B** | Demo-blocking defect bundle | 3 / 6 | MP-05 … MP-07 | Remove the three defects that break the demo |
| **WP-C** | Queue completeness **and multi-display DQDS** | 3 | MP-08 … MP-12, MP-24; **MP-35 … MP-39** | Recall, priority, policy semantics, token modes, print, history **and multi-display DQDS configuration** |
| **WP-D** | Appointment and scheduling completion | 2 | MP-13 … MP-18 | Overbooking, grace, deadlines, blocked periods, duplicate allowance, schedule audit |
| **WP-E** | Administration surface | 1 | MP-19 … MP-21 | Staff/permission UI, assignment editor, subscription lifecycle |
| **WP-F** | Reporting and dashboard | 5 | MP-22 … MP-23, MP-27 | Operational reports, dashboard completion, analytics |
| **WP-G** | Localisation and usability | 5 | MP-28 … MP-29 | One i18n mechanism; responsive/touch/a11y pass |
| **WP-H** | Tracking and handoff | 4 | MP-25, MP-30 | Tracking hardening; staff handoff (undefined — PO-01) |
| **WP-I** | Acceptance and truth | 6 | MP-31 … MP-34, MP-26; **MP-40** | End-to-end acceptance (incl. the multi-display demonstration), rehearsal, CI truth, documentation truth |

**Nine work packages, 40 tasks.** The five multi-display tasks sit inside **WP-C** as **§6 WP-C.2** because they are Phase 3 queue work and share `queuing/display.py`, `common/models.py` and the queue capability namespace with WP-C's other tasks; the demonstration task sits in **WP-I** because Phase 6 owns acceptance.

### 5.2 Critical path

```
MP-01  Prove runtime + record post-migration suite baseline
       (migration applied 2026-11-23 — Appendix E)
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

**Multi-display path (Hackathon Version scope, PO-13):** MP-06 → MP-35 → MP-36 → **MP-41, MP-42, MP-43, MP-45, MP-46** → MP-37 → MP-38 → MP-39 → **MP-40** (inside MP-31/MP-32), with **MP-44** landing inside MP-06. It is **not** on the critical path to a demonstrable system, so the demo can be rehearsed before it lands — but the Hackathon Version's multi-display claim is not complete until MP-40 has evidence for AC-01…AC-21. The six Phase-3 tasks added by PO-13 plus the demonstration cost ≈ 18.0 engineer-days (Appendix A, Appendix D.3).

### 5.3 Milestones

| Milestone | Definition | Tasks |
|---|---|---|
| **M-1 Runtime proven** | Stack healthy (VERIFIED 2026-11-24), schema at head (2026-11-23 deployment record), and the post-migration suite baseline recorded | MP-01 |
| **M-2 Baseline trusted** | Full suites executed on the migrated DB; every failure named | MP-02 |
| **M-3 Demo-ready** | MVP §12 script passes end to end on the live stack | MP-05, MP-06, MP-07, MP-08, MP-31, MP-32 |
| **M-4 Queue complete** | BR §26–§32 satisfied, including recall, priority and print | MP-09 … MP-12, MP-24 |
| **M-5 Scheduling complete** | BR §15, §19–§20, §22 satisfied | MP-13 … MP-18 |
| **M-6 Administration complete** | All Phase 1 management achievable from the UI | MP-19, MP-20 |
| **M-7 Reporting complete** | BR §43 reports live and reconciled | MP-22, MP-23 |
| **M-8 Phase 4–6 closed** | Only after PO-01 defines the phases | MP-25, MP-30 |
| **M-9 Multi-display DQDS functional** | Two or more displays in one branch, each with its own scope and language, server-side filtered, admin-managed and audited — specification AC-01…AC-11, AC-13, AC-14 evidenced | MP-35 … MP-39 |
| **M-10 Hackathon Version complete** | M-3 satisfied **and** the multi-display demonstration recorded (AC-12, the six-screen load case, stale/reconnect) | MP-31, MP-32, MP-40 |

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
| **MP-01** | **Prove the runtime — never re-apply an applied migration.** On the Ubuntu host: record `alembic current` **first** and confirm it reads `c4d8e2a91f60`; run `alembic upgrade head` only if it does not, and `_tools/pg_backup.sh` before any such upgrade; `_tools/amsdp_rebuild.sh` only if a rebuild is needed; probe the published ports `8110`–`8117` and `3100` from outside and `:8000`/`:3000` from inside | **Reconciled 2026-11-24 (Appendix E):** live DB was migrated to `c4d8e2a91f60` on 2026-11-23; eight services plus the frontend answered HTTP 200 when re-probed; no post-migration suite run is recorded | **P0** | Owner authorisation, host access | `alembic current` output, container list, health JSON, table list | `alembic current` = `c4d8e2a91f60`; `voice_packs`, `queue_announcement_deliveries` and `announcement_platform_config` present in the live schema; every compose service up; each check quoted as output, not asserted | 0.5 | Re-applying an applied revision — mitigated by reading `alembic current` before any upgrade, and taking a backup if it is behind |
| **MP-02** | **Whole-tree suite re-baseline** on the migrated database, plus the Phase-2 cancel/reschedule/no-show regression sweep (**MP-02b**) | Last recorded **790 pass / 1 fail** (DOCUMENTED, pre-migration). The `682 passed / 109 errors` run was also pre-migration; the 109 were fixture setup on `voice_packs`, which now exists — **expected to clear, predicted not proven** | **P0** | MP-01 | Executed logs for backend pytest and frontend `npm test` | Every test executed; every failure named with cause; no pass claimed without output | 1.0 | Long-standing failures surface; that is the purpose |
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

### WP-C.2 — Multi-display DQDS (Phase 3, Hackathon Version)

Added by **V1.1** under owner instruction 2026-11-24. Requirements come from `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` (**MD-01…MD-12**), which also records the current state as evidence. **PO-13 gated the whole subsection and was APPROVED on 2026-11-24** (Appendix D): these tasks are authorised roadmap work and are gated only by sequencing (§8) and MP-01. Requirements MD-13…MD-19 added by PO-13 are delivered in **WP-C.3** (D.3), not here.

| ID | Task | Current state | Pri | Depends on | Deliverables | Acceptance & verification | Est | Risk |
|---|---|---|---|---|---|---|---|---|
| **MP-35** | **Display registry**: `queue_displays` (+ `queue_display_doctors`) model, forward-only idempotent Alembic revision on `c4d8e2a91f60`, branch-unique code, `status`, `language`, `scope_type`, `department_id`, optional footer | **NOT IMPLEMENTED** — no display table exists (spec §3.4) | P1 | MP-01 | Model, migration, seed of two demo displays, unit tests | Two displays persist in one branch independently; a duplicate code is refused; cross-organisation FK is impossible; `alembic upgrade head` runs twice without error; no existing table altered (spec AC-01, AC-14) | 1.5 | A new public-facing table — keep `organization_id` the only tenant key |
| **MP-36** | **Display resolution and server-side scope** in the public route: `?display=<code>` selects a display; doctor scope filtered in SQL; unknown, cross-branch, cross-org and **disabled** displays 404 exactly like an unknown branch; the two-segment route keeps its current behaviour | **NOT IMPLEMENTED** — one branch-wide route, no filtering (`display.py:127-201`) | P1 | MP-35 | Resolver, route query parameter, tests | Scoped payload lists only its doctors; the out-of-scope token appears nowhere in the raw body; 404 identical for unknown and disabled; all 24 existing board tests still pass (spec AC-02, AC-04, AC-05, AC-07) | 2.0 | Client-side filtering would leak the whole branch — assert the raw response |
| **MP-37** | **Department scope and room label**: resolve a department display through `doctor_branches.room_id → facility_rooms.department_id`; publish `room_name` per doctor (nullable) | **NOT IMPLEMENTED** — payload has no room, no department concept | P2 | MP-36 | Resolver join, payload field, page rendering, tests | A department display shows only doctors whose assigned room is in that department; an empty department shows the empty state and never the branch; a doctor without a room renders `—` (spec AC-03, AC-07) | 1.5 | Empty scope must not widen the feed |
| **MP-38** | **Configured language and TV-scale presentation**: return `display.language` and use it below `?lang=`; refresh the language precedence; `clamp()` typography, display name in the header, complete BN/EN labels | **PARTIAL** — device-local preference only (`[branch].js:30,41-53`); card capped at 1180 px (`global.css:92,126`) | P2 | MP-36 | API field, page changes, CSS, screenshots | Two displays show different languages with no device change; clearing storage changes nothing; `?lang=` still overrides; token is the largest element at 1920×1080 and 1366×768 (spec AC-08, AC-11) | 1.5 | Presentation-only change — must not touch the payload allow-list |
| **MP-39** | **Display administration**: `queue.display.manage` capability inside `queue.*`, list/create/patch API scoped from the token, audit events with before/after, one admin page with a copyable display URL | **NOT IMPLEMENTED** — no capability, no route, no page, no audit | P1 | MP-35, MP-36 | Capability entry, routes, page, tests, audit evidence | Receptionist refused server-side; branch admin succeeds; cross-branch and cross-org → 404; one audit row per write with before/after; `DELEGABLE_CAPABILITIES` unchanged; no new role (spec AC-06, AC-13) | 3.0 | An admin surface must not become a second authorisation boundary |

**Explicitly not in these tasks:** heartbeat/health (spec D-01), preview and QR issuance (D-02), next-N tokens (D-05), room on the queue entry and room-scoped numbering (D-08 residue), themes and a show/hide matrix beyond the four policy fields of MD-17 (D-09), device provisioning (D-10), per-display analytics (D-11), platform cross-tenant provisioning (D-12). **Superseded by PO-13 (2026-11-24):** estimated waiting time (was D-04) and room targeting (was part of D-08) are now **in scope** — they are delivered by **MP-41…MP-46 in §6 WP-C.3 and Appendix D**, not by this table.

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
| **MP-40** | **Multi-display demonstration and acceptance**: run two or more displays with different scopes and languages; exercise a call, a cross-scope silence, a disabled display, and a six-screen load from one client IP; capture stale/reconnect behaviour | P1 | MP-35 … MP-39, MP-06, MP-31 | Evidence pack (captures, recordings, load output, two resolutions): specification AC-09 and AC-12 met by artefacts, every other AC marked met or unmet, and **BLOCKED** with the reason if the environment cannot host six clients — never "passed". Six screens may be six simulated pollers, stated as such | 1.0 |

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
8. **A public surface changes once, carefully.** `MP-06` (operational day) and `MP-36` (display resolution) both touch `queuing/display.py`; MP-06 must land first and its regression test must stay green through MP-36–MP-38. Nothing in WP-C.2 may weaken the existing 404/429/cache contract.
9. **Configuration before behaviour, again.** MP-35 (registry) precedes every consumer; MP-39 (admin surface) may ship after MP-36–MP-38 but the demonstration (MP-40) may not claim a configured facility until MP-39 exists.

---

## 9. Risk register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-1 | A **future** migration fails or loses data (the 2026-11-23 migration already succeeded — Appendix E) | Low | High | `alembic current` before any upgrade; `pg_backup.sh` first; rehearse against a disposable restored database — the practice that de-risked the 23 Nov migration; chain is single-headed and **VERIFIED**; restore path documented in the runbook | Engineer |
| R-2 | Restored suite fails in ways no report predicted | Medium | Medium | MP-02 is a **baseline**, not a gate: failures are recorded and triaged, not hidden | Engineer |
| R-3 | Demo features regress while post-demo work proceeds | Medium | High | Freeze non-demo code changes after MP-31 until the demonstration is past | Owner |
| R-4 | A GATED task is started without its decision | Medium | High | §7.1 Definition of Ready; the gate is checked in the report | Engineer |
| R-5 | DQDS fix changes public-endpoint behaviour | Low | Medium | Org resolution must stay scoped and cached; regression test at a fixed instant | Engineer |
| R-6 | Recall duplicates announcement or audit rows | Medium | Medium | Distinct event identity (`qce:` key) plus an idempotency test | Engineer |
| R-7 | Priority is misused as a clinical triage signal | Medium | Medium | Permission-restricted, operational wording only, audit on every use; BR §28 non-clinical | Owner |
| R-8 | Test suite remains untrustworthy; "green" is claimed again | Medium | High | D7 requires quoted output; MP-33 refuses to claim CI without a run | Owner |
| R-9 | Owner documents drift further from the code while work proceeds | High | Medium | MP-34 (gated) plus a documentation check in every milestone review | Owner |
| R-10 | Single engineer on the critical path; no reviewer | Medium | Medium | At minimum, one independent read of every migration and every tenancy-touching change | Owner |
| R-11 | Display scope filtering is implemented client-side, exposing the whole branch on a public URL | Medium | High | Server-side filtering is the acceptance criterion (spec AC-02 asserts the raw body); code review gate on the route | Engineer |
| R-12 | Multi-display requires a durable limiter that the plan has not scheduled | Low | Medium | MP-36 re-keys the in-process bucket per display and proves the six-screen case; the durable limiter stays MP-25 (spec §9.2, §6 D-07) | Engineer |

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
| Multi-display DQDS configuration | **MOVED INTO SCOPE (V1.1)** | Owner instruction 2026-11-24 and PQV §B.6 place multi-display configuration in the Hackathon Version (Phase 3, tasks MP-35…MP-39 **and MP-41…MP-46**; Phase 6 demonstration MP-40). Requirement: specification MD-01…MD-19 |
| Advanced multi-display DQDS management — heartbeat/health, device pairing, QR provisioning, push transport, **per-second countdown**, next-N tokens, themes beyond the four policy fields, per-display analytics | **Deferred** | PO-13 does not require it; none of it is needed to demonstrate multi-display operation (specification D-01…D-12 as amended by Appendix E). **Estimated waiting time is no longer in this row** — PO-13 made it requirement MD-13 / MP-42 |
| Room on the queue entry and room-scoped token numbering | **Deferred** | DQD-002 / GAP-07 (MP-11); an independent queue-model change. The hackathon room *label* is derived from `doctor_branches.room_id` and needs no queue change |
| Automatic no-show status | **Rejected** | BR §20.4 requires staff confirmation; automation would corrupt attendance data |

---

## 11. Traceability — finding to task

| Finding (audit) | Feature keys | Tasks |
|---|---|---|
| GAP-01 ~~live DB behind head~~ / no post-migration runtime evidence (migration half closed 2026-11-24 — Appendix E; evidence half open) | all | MP-01, MP-02 |
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
| GAP-28 multi-display DQDS absent | F-53, F-46 | MP-35, MP-36, MP-37, MP-38, MP-39 → MP-40 (Phase 6); **PO-13 expansion:** MP-41, MP-42, MP-43, MP-44, MP-45, MP-46 → MP-40 extended |

**Coverage check.** Every GAP maps to at least one task; every task in §6 traces back to at least one GAP, specification requirement or decision. No orphan tasks, no unaddressed findings.

**Requirement traceability for WP-C.2.** MD-01→MP-35 · MD-02/MD-03/MD-09→MP-36 · MD-04/MD-05→MP-37 · MD-06/MD-11→MP-38 · MD-08/MD-12→MP-39 · MD-07→asserted by MP-36/MP-37 tests · MD-10→MP-36 (limiter) and MP-40 (evidence). Specification criteria AC-01…AC-14 are attached per task in §6 WP-C.2 and MP-40.

**Requirement traceability for WP-C.3 (PO-13, Appendix D).** MD-13→MP-42 · MD-14→MP-41 · MD-15→MP-43 · MD-16→MP-44 · MD-17→MP-45 · MD-18/MD-19→MP-46 · AC-15…AC-21→MP-40 (extended demonstration).

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
| `.clinerules` §11 — document placement | This plan is written to `docs/plan/` because the Product Owner explicitly requested a plan folder in the authorising instruction (precedence level 2). The interval in which that was a **deviation** ended on **2026-11-24**: the Product Owner ratified `docs/plan/` as an approved location, `.clinerules` §11 now lists `plan/` among the sanctioned subject subfolders, and the decision is recorded in `docs/governance/AMSDP_Docs_Index_V1.0.md`. No file was moved, renamed or migrated, so no manifest entry is required (Appendix D.8). |
| `.clinerules` §1 — owner instruction honoured, phases preserved | V1.1 adds multi-display DQDS to Phase 3 (tasks MP-35…MP-39) and Phase 6 (MP-40) without renaming, renumbering or adding a phase, and without altering any other approved requirement. |
| Index registration | The audit, plan V1.0, the multi-display specification and this V1.1 are registered in an appended annex of `docs/governance/AMSDP_Docs_Index_V1.0.md`, without advancing the revision number because **D-5** (index numbering) remains open. |

---

## Appendix A — Task index

**P0 (demo or verification blocking):** MP-01, MP-02, MP-03, MP-05, MP-06, MP-07, MP-08, MP-31, MP-32
**P1:** MP-04\*, MP-09\*, MP-10, MP-11, MP-13\*, MP-14, MP-16, MP-19, MP-20, MP-23, MP-30\*, MP-35, MP-36, MP-39, MP-40, **MP-41, MP-42, MP-46**
**P2:** MP-12, MP-15, MP-17, MP-18, MP-21\*, MP-22, MP-24, MP-25, MP-28, MP-29, MP-33, MP-34\*, MP-37, MP-38, **MP-43, MP-44, MP-45**
**P3 / deferred:** MP-26, MP-27\*

`*` = gated on an owner decision (§4). **PO-02 and PO-13 were decided on 2026-11-24**, so MP-35…MP-46 are no longer gated on them; the MP-01 sequencing rule (§8) still applies, and MP-06 is a prerequisite for the demonstration tasks. See Appendix D.

**Total estimated effort:** ≈ 73.0 engineer-days (**V1.0: ≈ 55**, **V1.1: ≈ 65.5**), of which **≈ 5.75** constitutes the path to a demonstrable system and **≈ 23.75** the path to a demonstrable system that also demonstrates full multi-display operation (5.75 + 18.0 for MP-35…MP-46).

| Subtotal | Tasks | Engineer-days |
|---|---|---|
| Multi-display Phase 3 | MP-35 (1.5), MP-36 (2.0), MP-37 (1.5), MP-38 (1.5), MP-39 (3.0) | 9.5 |
| Multi-display Phase 6 demonstration | MP-40 | 1.0 |
| **Added by V1.1** | | **10.5** |
| Multi-display Phase 3, PO-13 expansion (WP-C.3) | MP-41 (2.0), MP-42 (2.0), MP-43 (1.0), MP-44 (0.5), MP-45 (1.0), MP-46 (1.0) | 7.5 |
| **Added by V1.1 + Amendment A-1** | | **18.0** |

---

## Appendix B — Command recipes

**MP-01 (Ubuntu host).** The migration in this recipe was **already applied on 2026-11-23** (Appendix E). The first command is therefore a *check*, and any `upgrade` is conditional.

```bash
cd /home/shomonrobie/amsdp
docker compose exec db psql -U amsdp -d amsdp -c "select version_num from alembic_version;"
#   MUST print c4d8e2a91f60. If it does not:
#     _tools/pg_backup.sh                                  # never skip before an upgrade
#     docker compose exec backend alembic upgrade head     # where the console script exists
docker compose exec db psql -U amsdp -d amsdp -c \
  "select to_regclass('voice_packs'), to_regclass('queue_announcement_deliveries'), to_regclass('announcement_platform_config');"
_tools/amsdp_rebuild.sh                                   # only if a rebuild is required
docker compose ps
for p in 8110 8111 8112 8113 8114 8115 8116 8117; do curl -fsS http://192.168.68.108:$p/health; echo; done
curl -fsS -o /dev/null -w '%{http_code}\n' http://192.168.68.108:3100
```

`:8000` and `:3000` are the **container-internal** ports. From outside the host the same services answer on `8110`–`8117` and `3100`; probing `:8000`/`:3000` from a workstation is what produced the earlier false "host unreachable" reading (Appendix E). `alembic` is not on the backend image's `PATH` in this deployment — the `psql` reads are the operative check.

**MP-02 (whole tree, on a throwaway or the migrated database).**

```bash
cd backend && python -m pytest -q          # quote the summary line verbatim
cd frontend && npm test                    # 368 tests expected; quote the summary
```

**MP-03 (announcement proof).** Invoke `call` for one queued entry, then read `queue_announcement_deliveries` and `audit_events` for that appointment; the counts must be exactly one and one.

**MP-40 (multi-display evidence).** Against the running stack, with two displays configured in one branch:

```bash
BASE=http://localhost:8000/api/v1/queue/display/<org>/<branch>
curl -sS -D- "$BASE"                    | head -c 600        # default (branch-wide) board — must be unchanged
curl -sS -D- "$BASE?display=reception"  | head -c 600        # scoped board — only its doctors
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE?display=nope"       # 404, no-store
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE?display=disabled"   # 404 identical to 'nope'
for i in $(seq 1 6); do ( for n in $(seq 1 60); do curl -sS -o /dev/null -w "$i:%{http_code}\n" "$BASE?display=reception"; sleep 10; done ) & done; wait
```

The last line is the six-screen load case (six simulated pollers from one address for ten minutes). Zero `429` lines is the pass condition; any `429` is a failure of **MD-10**, not a flake.

---

## Appendix C — Document control

| Field | Value |
|---|---|
| Version | **1.1** |
| Date | 2026-11-24 |
| Status | **Proposed** — not authorised for execution |
| Author | Implementation agent (read-only assessment) |
| Reviewer | Product Owner |
| Supersedes | **plan V1.0 (same date)** — V1.0 is preserved unchanged; and the unpersisted T-1…T-12 roadmap (2026-11-23) |
| Change rule | amendments create a new version; tasks are never silently re-scoped |
| Companion | `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (Amendments A-1…A-3) and `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` |
| Next action | **PO-13 and PO-02 are decided (2026-11-24): scope approved, plan reconciled (Appendix D).** **Appendix E (same date) reconciles the deployment baseline:** the live DB migration was already applied on 2026-11-23, so **MP-01 is a verification task, not a migration**. Remaining: the Product Owner decides **PO-01, PO-03…PO-12**; nothing starts before **MP-01** is approved, and MP-35…MP-46 follow the §8 sequencing rules |

### C.1 Change history

| Version | Date | Change |
|---|---|---|
| **1.0** | 2026-11-24 | First issue: nine work packages, 34 tasks MP-01…MP-34, the decision gates PO-01…PO-12, milestones M-1…M-8, ≈ 55 engineer-days. Multi-display DQDS recorded as **deferred** (BR §33's later-phase label). |
| **1.1** | 2026-11-24 | **One scope decision changed, by owner instruction.** (1) Multi-display DQDS moved **into** the Hackathon Version: five Phase-3 tasks **MP-35…MP-39** (§6 WP-C.2) and one Phase-6 demonstration task **MP-40**; WP-C renamed to include multi-display; milestone **M-9** (multi-display functional) and **M-10** (Hackathon Version complete) added. (2) Gate **PO-13** added; **PO-02** now explicitly covers multi-display. (3) §3.1 baseline, §3.2 assumptions **A-6/A-7**, §5.2 multi-display path, §8 sequencing rules 8–9, §9 risks **R-11/R-12**, §10 deferral rows, §11 traceability **GAP-28** and requirement traceability, Appendix A totals and Appendix B recipe updated. (4) No other task, gate, estimate, rule or phase was renamed, renumbered or re-prioritised. |
| **1.1 + A-1** | 2026-11-24 | **PO-13 APPROVED, PO-02 RESOLVED, `docs/plan/` ratified — all by the Product Owner.** (1) **WP-C.3** added: MP-41 room-scoped displays, MP-42 estimated waiting time, MP-43 refresh-on-change, MP-44 facility-local operational day, MP-45 facility-controlled public fields, MP-46 read-only enforcement and denial accounting (+7.5 eng-days; total ≈ 73.0). (2) MP-40 extended to AC-15…AC-21; MD-13…MD-19 and AC-15…AC-22 come from the specification's Appendix E. (3) PO-02/PO-13 gate markers removed: both gates are closed. (4) §8 sequencing rules 10–14, §9 risks R-13…R-15, §11 traceability, §12 placement-deviation closure and Appendix A totals updated. (5) The `docs/plan/` deviation is **closed**; nothing was migrated. No task was renumbered or renamed. |
| **1.1 + A-2** | 2026-11-24 | **Deployment baseline corrected — documentation only.** The "live DB two revisions behind head" statement was a true 2026-11-23 measurement that the same-day migration superseded; no in-tree document recorded the application. §3.1 runtime row, §5.2 critical-path label, §5.3 **M-1**, **MP-01** and **MP-02**, §9 **R-1**, §11 **GAP-01** and the Appendix B recipe now reflect the actual baseline: **MP-01 is a verification task and must never re-apply an applied revision**. Appendix E records the evidence and what was and was not freshly verified. **No task added, renamed, re-estimated or re-prioritised; totals unchanged.** |

**What did *not* change.** The six-phase sequence, every V1.0 task except WP-C/WP-I membership, PO-01…PO-12 other than PO-02's scope note, the definitions of ready/done, the evidence vocabulary, and the rule that nothing starts before **MP-01**.

---

## Appendix D — Amendment A-1: PO-13 full-scope reconciliation (24 November 2026)

**This appendix amends §4 (gates), §6 (WP-C.2 scope note), §11 (traceability) and Appendix A (totals). Where it conflicts with those sections, this appendix governs; every other section stands unchanged.**

### D.1 Product Owner decisions absorbed here

| Decision | Date | Effect on this plan |
|---|---|---|
| **PO-13** *Full-featured Multi-display DQDS* — **APPROVED** | 2026-11-24 | Six tasks added as **WP-C.3** (MP-41…MP-46); MP-40 extended to AC-15…AC-21; multi-display management is no longer optional anywhere in the plan |
| **PO-02** *DQDS requirements alignment* — **RESOLVED** | 2026-11-24 | Gate closed. No MVP/Hackathon/Later-Releases tier governs DQDS; BR §33 now carries a §33.1 scope-status block in both copies; this plan may no longer cite "later-phase" as a reason to defer any DQDS capability |
| **MP-06** *Facility-local operational day* — **IMPLEMENTATION COMPLIANCE REQUIRED** | 2026-11-24 | MP-06 stays a P0 prerequisite; **MP-44** is its proof on the display path. `Organization.timezone` already exists (`models.py:38`, default `Asia/Dhaka`), so compliance needs no migration |
| **`docs/plan/` ratified** — **APPROVED** | 2026-11-24 | The recorded §11 placement deviation is **closed**: `plan/` is a sanctioned location; `.clinerules` §11 and the docs index were updated in the same task. **No migration is required** |
| *Change control* | 2026-11-24 | These decisions authorise scope and plan, **not** deployment, production database changes or unrelated work. Nothing starts before **MP-01** |

### D.2 Gate state after this amendment

| Gate | State |
|---|---|
| **PO-02** | **CLOSED — resolved.** No further action |
| **PO-13** | **CLOSED — approved.** MP-35…MP-46 are authorised roadmap work; sequencing still gates them |
| **OP-1** (spec E.9) | *"Queue" targeting has no queue entity* — satisfied as the doctor-set target. Non-blocking; owner may correct |
| **OP-2** (spec E.9) | *Countdown vs labelled estimate* — MD-13 delivers a labelled minute estimate. Non-blocking; additive if the owner requires a countdown |
| PO-01, PO-03…PO-12 | **Unchanged.** Still open, still gating the same tasks |

### D.3 WP-C.3 — PO-13 capability expansion (Phase 3, Hackathon Version)

Requirements MD-13…MD-19 and criteria AC-15…AC-22 are defined in `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` **Appendix E**, which governs where §5/§6 conflict.

| ID | Task | Current state | Pri | Depends on | Deliverables | Acceptance & verification | Est | Risk |
|---|---|---|---|---|---|---|---|---|
| **MP-41** | **Room-scoped displays**: `scope_type='room'` plus `room_id`, resolver via `doctor_branches.room_id → facility_rooms.id`, branch/org validation, empty-state test | **NOT IMPLEMENTED** — `scope_type` has three values in spec §5.1; no room scope, and no display table exists yet | P1 | MP-35, MP-36 | Schema value, CHECK constraint, resolver join, validation, tests | A room display lists only that room's doctors; an unassigned room shows the empty state and never the branch; a cross-branch `room_id` is a `422` (spec AC-15) | 2.0 | An empty room must not widen the feed |
| **MP-42** | **Estimated waiting time** on the board: measured mean from today's completed consultations (≥ 3) else `AMSDP_AVG_SERVICE_MINUTES`, floored at 1, estimate marker in BN/EN, never a guarantee | **NOT IMPLEMENTED on the board** — `display.py` has no estimate; the formula exists only for PQV in `tracking.py:184-185` | P1 | MP-36 | Computation, payload field + `estimate` flag, BN/EN copy, tests | A doctor with ≥ 3 completions shows the measured mean, one with none shows the default; the marker is adjacent to every number; the value is `int ≥ 1` or `null`; no guarantee wording (spec AC-16) | 2.0 | An estimate built on 3 samples reads as authoritative — the marker is mandatory |
| **MP-43** | **Refresh on change**: board version (hash of the projection), weak `ETag`, `304` revalidation, no re-render when unchanged, change visible within one poll interval | **NOT IMPLEMENTED** — a fresh body every 10 s with no validator (`display.py:185-197`) | P2 | MP-36 | Version computation, `ETag`/`If-None-Match`, cache handling, tests | An idle board returns `304` with no body; a token call changes the version and reaches the in-scope display within 10 s; `304`s stay inside the rate-limit bucket (spec AC-17) | 1.0 | A version that varies per request silently defeats caching |
| **MP-44** | **Facility-local operational day** on the display path: "today" from `organizations.timezone`, `date.today()` removed, facility clock rendered | **NOT IMPLEMENTED** — `display.py:138` uses `date.today()`; GAP-03/GAP-25 record the same defect in queue and seed | P2 | MP-06, MP-36 | Shared helper consumed by display (and by queue/dashboard through MP-06), boundary tests | At 20:00 UTC (02:00 Dhaka) the board shows the new Dhaka day; `operational_date` matches; boundary test at 23:59/00:00 Dhaka (spec AC-18) | 0.5 | Fixing the display only would leave dashboards on server-local dates — one helper, three call sites |
| **MP-45** | **Facility-controlled public-display information**: `show_room`, `show_estimated_wait`, `show_waiting_count`, `footer_text`; enforced server-side; admin controls | **NOT IMPLEMENTED** — the payload publishes a fixed field set; `footer_text` exists in the schema design only | P2 | MP-35, MP-39 | Columns (defaults true/""), payload suppression, admin toggles, tests | A field switched off is **absent from the raw response**, not hidden in CSS; the footer renders in the display's language (spec AC-19) | 1.0 | Client-side hiding would make the UI a safety boundary |
| **MP-46** | **Read-only enforcement and denial accounting**: GET-only public routes (`405` + `Allow: GET`), `queue.display.denied`, throttled `queue.display.disabled_requested`, no audit rows for anonymous unknown-code probes | **NOT IMPLEMENTED** — no verb guard, no display audit events | P1 | MP-39 | Route guard, two audit events, throttle, tests | Four verb probes return `405`; no cookie is set; one denial = one row; 100 unknown-code probes add zero audit rows (spec AC-20, AC-21) | 1.0 | An unauthenticated probe must not write unbounded audit rows |

**Explicitly still out after PO-13** (spec E.7): heartbeat/health, preview and QR issuance, next-N tokens, room on the queue entry and room-scoped numbering, themes beyond the four policy fields, device provisioning, per-display analytics, durable multi-process limiter (still GAP-20/MP-25), platform cross-tenant provisioning.

### D.4 Sequencing added to §8

10. **MP-41…MP-46 follow MP-36**, not MP-35: a scope type is meaningless until the resolver exists.
11. **MP-44 lands with MP-06**, in the same change, so queue, dashboard and display share one timezone helper (spec RMD-10).
12. **MP-42, MP-43 and MP-45 share one payload change**; they must be tested together against the raw response, because each can silently widen or suppress a public field.
13. **MP-46 before MP-40**: the demonstration must show a read-only board and a denial audit row, not just a working one.
14. **MP-40 is extended**, not duplicated: AC-15…AC-21 join the existing six-screen run and the cross-scope silence checks.

### D.5 Milestones affected

| Milestone | Change |
|---|---|
| **M-9 — multi-display functional** (§5.3) | Now requires MP-35…MP-39 **and** MP-41…MP-43, MP-45, MP-46; MP-44 must have landed with MP-06 |
| **M-10 — Hackathon Version complete** (§5.3) | Now requires AC-15…AC-22 as well as AC-01…AC-14. No milestone was renamed, renumbered or added |

### D.6 Risks added to §9

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R-13** | A measured estimate (≥ 3 samples) is presented as a consultation time and a patient relies on it | Medium | High | MP-42 makes the estimate marker mandatory and adjacent; a countdown is excluded (spec E.7); wording never claims a time |
| **R-14** | The timezone correction is applied to the display only, leaving the queue and dashboard on server-local dates | Medium | High | MP-44 lands with MP-06, one helper, three call sites; boundary tests in both |
| **R-15** | PO-13's "full-featured" wording is stretched to justify unrequested signage features (themes, preview, analytics) | Medium | Medium | Spec E.7 and D.3's "still out" paragraph enumerate what stays out; new capability needs a new owner decision |

### D.7 What this amendment does **not** change

No task was renumbered, renamed, re-estimated or re-prioritised except by addition. Phase 1 tasks and the MP-01 sequencing rule are untouched; PO-01 and PO-03…PO-12 remain open; the definitions of ready and done, the evidence vocabulary, the delivery rules and the six-phase sequence are unchanged. No code, migration, configuration or deployment is authorised by this appendix.

### D.8 Placement deviation — now closed

§12 previously recorded `docs/plan/` as a **deviation** awaiting ratification. The Product Owner ratified it on **2026-11-24**. `.clinerules` §11 now lists `plan/` among the sanctioned subject subfolders, and `docs/governance/AMSDP_Docs_Index_V1.0.md` records the decision. **No file was moved, renamed or migrated, so no manifest entry is required.**

### D.9 Verification performed for this amendment

| Check | Result |
|---|---|
| Gates closed in the document, not only in the reply | §4/Appendix A and D.2 both state PO-02/PO-13 as decided, and no task row still carries a PO-13 gate marker |
| Totals recomputed | 40 → 46 tasks; ≈ 65.5 → ≈ 73.0 engineer-days (MP-35…MP-46 = 18.0); Appendix A and D.5 agree |
| Traceability closed | MD-13…MD-19 and AC-15…AC-22 each map to a task; GAP-28 now spans MP-35…MP-46 |
| Plan/code agreement | Every "current state" cell cites the line that proves it (`display.py:138`, `:185-197`, `tracking.py:184-185`, `models.py:38`); no cell claims work that exists |
| Tests claimed | **None.** No suite, migration or server was executed |

### D.10 Document control

| Field | Value |
|---|---|
| Amendment | A-1, 24 November 2026 |
| Version | The plan remains **V1.1 with Amendment A-1**; no V1.2 is issued, because V1.1 was not yet in force beyond this working tree and an append-only amendment leaves every earlier statement auditable |
| Trigger | PO-13 (approved), PO-02 (resolved), MP-06 (compliance required), `docs/plan/` ratification |
| Effect | Adds WP-C.3, MP-41…MP-46, sequencing 10–14, risks R-13…R-15, milestone conditions; closes two gates and one placement deviation |

---


---

## Appendix E — Amendment A-2: live deployment baseline correction (24 November 2026)

**This appendix corrects §3.1 (runtime row), §5.2 (critical-path label), §5.3 (M-1), §6 (MP-01, MP-02), §9 (R-1), §11 (GAP-01) and Appendix B (MP-01 recipe). Where it conflicts with those sections, this appendix governs. It changes no scope, no task ID, no gate and no estimate.**

### E.1 What was wrong, and why

The plan inherited "the live DB is two revisions behind head" from two documents that were **correct on 2026-11-23**: runbook §1.4 (`select version_num from alembic_version → a9c4e1f7b2d8`; `to_regclass('voice_packs') → (null)`) and the merge publication report. The migration was then applied **later on 2026-11-23**, rehearsed first against a disposable restored database, with a pre-migration backup. **No in-tree document recorded the application**, so the last written statement stayed "behind" and the plan and the audit copied it forward as a current fact.

A second, independent error reinforced it: the earlier session probed `:8000` and `:3000`, which are **container-internal** ports. From a workstation the same deployment answers on `192.168.68.108:8110–8117` and `:3100`. "Host unreachable" was a probe error, never a deployment fact.

### E.2 The corrected baseline

| Item | Value |
|---|---|
| Repository · branch · HEAD | `shomonrobie/amsdp` · `hackathon-mvp` · `a4ddc2cf58e019b57dccf59f3a859743e3c48430` |
| Previous database revision | `a9c4e1f7b2d8` |
| Live database revision | `c4d8e2a91f60` — single head |
| Migration date · outcome | 23 November 2026 · applied successfully |
| Tables created | `voice_packs` · `queue_announcement_deliveries` · `announcement_platform_config` |
| Rehearsal | Against a disposable restored database, before the live application; pre-migration backup taken |
| Seeded counts preserved in rehearsal | organizations 421 · patients 2963 · doctors 601 · appointments 642 · queue_entries 11 · audit_events 20490 |

Source: the verified deployment record of 2026-11-23. The migration **was not re-run for this amendment** and must not be re-run by MP-01.

### E.3 What was freshly verified on 2026-11-24 — and what was not

| Check | Outcome | Class |
|---|---|---|
| Branch · HEAD | `hackathon-mvp` · `a4ddc2cf58e019b57dccf59f3a859743e3c48430` | **VERIFIED** |
| Revision graph from the tree | 16 revisions, one head `c4d8e2a91f60`; chain `a9c4e1f7b2d8 → a7c3f19d2b64 → c4d8e2a91f60` | **VERIFIED** (`scripts/que-006-w3-voice-config/check_migration_graph.py`) |
| Services `8110`–`8117` on `192.168.68.108` | all HTTP 200, each naming itself (`identity`, `organization`, `patient`, `doctor`, `scheduling`, `appointment`, `queuing`, `audit`) | **VERIFIED** |
| Frontend `:3100` | HTTP 200 | **VERIFIED** |
| Deployed organization-service surface | 33 paths incl. all eleven `/api/v1/voice-packs…` and the platform/org announcement-config routes | **VERIFIED** (`/openapi.json`) |
| Deployed queue-service surface | `/api/v1/queue/display/{org_code}/{branch_code}`, `/api/v1/queue/{entry_id}/announcement`, `/api/v1/queue/announcements/{delivery_id}/outcome` | **VERIFIED** (`/openapi.json`) |
| Database revision · table presence | **not verified** — no `alembic`, `psql` or `docker` binary on the verifying host, and no database credential; no authenticated call was made, because a token needs a `POST` that writes a login-attempt row | **NOT VERIFIED** |

The probes prove the deployment runs the **post-merge code** (the W2/W3 routes exist only in that tree); they do **not** prove the schema revision, because `/health` is a static liveness body. MP-01 exists to close exactly that last gap with a quoted `psql` read.

### E.4 Consequences for the plan

1. **MP-01 is redefined, not removed.** It becomes "prove the runtime, never re-apply an applied migration": read `alembic_version` and the three `to_regclass()` values first, upgrade only if behind. Priority, dependencies and estimate are unchanged.
2. **MP-02 is unchanged in substance and clearer in reason.** It is still P0 and still the gate on every "the suite is green" statement — the reason is no longer "the database is behind" but "no suite run against the migrated database has been recorded". The `109` fixture errors should clear; that is a prediction until the log exists.
3. **MP-03 and everything downstream are unblocked at the environment level**, and remain blocked on MP-02 for any claim about tests.
4. **No re-estimation.** MP-01 stays 0.5 eng-days and the ≈ 73.0 total stands: the same work moves from "migrate then prove" to "prove and only migrate if behind".
5. **The historical numbers stand as history.** `790 pass / 1 fail`, `682 passed / 109 errors` and `109 passed` on a migrated throwaway database are quoted as past results, not as current status.

### E.5 What must not be done

- **Do not run `alembic upgrade head` as the first step of MP-01.** Read `alembic_version` first; an unconditional upgrade treats an applied revision as outstanding.
- **Do not restore or reseed the live database.** The rehearsal already happened against a disposable copy; restoring production is not authorised by any document.
- **Do not treat the `109 errors` as a current defect.** They were fixture setup against the pre-migration schema and are explained, not open.
- **Do not claim a suite result.** No post-migration log exists yet; MP-02 produces it.

### E.6 Open items this appendix does not touch

| Item | State | Why untouched |
|---|---|---|
| PostgreSQL published on `0.0.0.0:5433` | **OPEN — security risk.** TCP `192.168.68.108:5433` confirmed reachable on 2026-11-24 | Owner decision; out of scope for a documentation reconciliation |
| No SSH listener on the host | **OPEN** — TCP `:22` closed, re-confirmed 2026-11-24 | Owner decision |
| **OP-1** queue targeting · **OP-2** countdown wording · **D-5** index numbering · SMS half of **PO-02** | **OPEN** | Unrelated to the deployment baseline |
| B-8 audibility · RBAC-R3 demo assignment | **UNPROVEN** | Need a human in the room / a seeded-data check |

### E.7 Document control

| Field | Value |
|---|---|
| Amendment | A-2, 24 November 2026 |
| Version | The plan remains **V1.1 with Amendments A-1 and A-2**; append-only, so every earlier statement stays auditable |
| Trigger | A verified deployment record contradicting the plan's stated runtime baseline |
| Effect | Corrects the runtime baseline, redefines MP-01 as verification, restates GAP-01, corrects the MP-01 recipe. **No scope, task, gate or estimate changes** |
| Authority | Documentation-only reconciliation under the task brief; no production action, no migration, no code change |

*End of Amendment A-2.*

---

## Appendix F — Amendment A-3: Product Owner decisions of 25 November 2026 applied

### F.1 Trigger

The Product Owner answered the consolidated decision request
(`implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md`) in writing on 25 November 2026. The
decision record is `decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md`; this appendix applies it
to the plan. Like A-1 and A-2 it is **append-only**: no earlier statement in this plan is rewritten,
re-estimated or renumbered.

### F.2 Decision gates (§4 of this plan) — state after the answers

| Gate | State | Where the effect is recorded |
|---|---|---|
| **PO-01** | **CLOSED** | `product/AMSDP_Phase_Model_V1.1.md` publishes Phases 4/5/6 (names, scope, exit criteria, accepting authority) and defines **MP-30** as verification of the existing handoff surfaces |
| **PO-03** | **CLOSED** | Dated annotations in MVP Scope §7 and Feature Catalogue §H; **SYM-001** is approved P1 |
| **PO-04** | **CLOSED** | MP-09 → MP-13 → MP-14 → MP-15 authorised, **sequenced after the first clean rehearsal** |
| **PO-05** | **CLOSED** | MP-04 and MP-26 deferred |
| **PO-06** | **CLOSED** | MP-27 deferred; the Analytics Specification is **not an approved requirement** |
| **PO-07** | **CLOSED** | MP-21 deferred; subscription is not phased in |
| **PO-08** | **CLOSED** | D-5 numbering rule adopted, O-2 decided, POD-2 closed, POD-7 executed, **POD-11 = Faria Bushra** |
| **PO-09** | **CLOSED** | Annotation-only corrections applied to the four named places |
| **PO-10** | **CLOSED as an approach** | `deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md`; **execution still needs a maintenance window** |
| **PO-11** | **CLOSED** | The doctor ↔ branch contract is ratified; the plan's "completeness claims only" caveat is discharged |
| **PO-12** | **CLOSED** | `plan/AMSDP_Feature_Key_Register_V1.0.md` — 26 `F-nn` keys |

**Still open and not touched by this amendment:** **B-1**, **B-2**, **B-3**, **B-4**, **Q-1**, **Q-2**,
and the whole deferred band.

### F.3 Task index (Appendix A) — status changes

| Task | Was | Now | Note |
|---|---|---|---|
| **MP-30** | "TBD until the owner publishes Phase 4" | **Defined**: verification of the existing handoff surfaces; ≈ 1 day as originally estimated | Cannot close before MP-25's acceptance cell is met (**B-4**) |
| **MP-34** | GATED (PO-09) | **IMPLEMENTED, awaiting owner review** | Annotations, PO-11 note and PO-12 register applied. Residual: the register's V2.5 family column (**R-1**) and **QUE-005** |
| **MP-33** | GATED | **BLOCKED** | A first green CI run needs the work pushed; **O-3 forbids pushing** |
| **MP-09, MP-13, MP-14, MP-15** | GATED (PO-04) | **AUTHORISED, NOT STARTED** | Gate is the first clean rehearsal, which has not been held |
| **MP-24, MP-25, MP-35…MP-46** | BLOCKED (B-4) | **BLOCKED** unchanged | ≈ 20.5 engineer-days still waiting on one read |
| **MP-04, MP-21, MP-26, MP-27** | DEFERRED / GATED | **DEFERRED** | PO-05, PO-06, PO-07 |
| **MP-11, MP-12** | DEFERRED (Q-6 c) | **DEFERRED** | Not reopened |

**No estimate in Appendix A changes.** The owner's answers close gates; they do not re-price work.

### F.4 What this amendment does not claim

1. **No task moves to `VERIFIED` or `ACCEPTED`.** The two harness repairs are `TESTED`; the
   documentation acts are `IMPLEMENTED`; nothing was observed in a browser, a live API session or a
   live database in this window.
2. **No live change happened.** No migration was applied to the deployment, no reseed, no service
   restarted, no host configuration altered. The `:5433` exposure described in Appendix E.6 is
   **still open**.
3. **MP-30's definition is narrow on purpose.** Phase 4 does not acquire a clinical feature by
   implication; a future Phase 4 expansion needs a new owner decision.
4. **D-5 is forward-only.** The annexes written between 21 and 25 November that say "no revision
   number is advanced" stay as they are. The rule begins at **Revision 49**.

### F.5 Open items this appendix does not touch

| Item | State |
|---|---|
| **B-4** live database read | **OPEN** — owner selected "other"; the read is specified in the PO-10 plan |
| **Q-1**, **Q-2** | **OPEN** — no code changed |
| **D-3** | **OPEN — investigated**: reproduces only as a module-import collection error with no database present; no fixture changed |
| **D-7**, **POD-6**, **POD-1/3/8/9/10** | Carried forward by PO-08 |
| **O-4**, **O-5**, **MP-16 / 1–3** | Recorded, not blocking |
| **QUE-005** | The one surviving P0 defect; no task currently owns it in this plan — **open gap, deliberately named** |

### F.6 Document control

| Field | Value |
|---|---|
| Amendment | A-3, 25 November 2026 |
| Version | The plan remains **V1.1 with Amendments A-1, A-2 and A-3**; append-only, so every earlier statement stays auditable |
| Trigger | The Product Owner's written answers to the consolidated decision request |
| Effect | Closes the PO-01 and PO-03…PO-12 gates, defines MP-30, re-grades MP-34, records what stays blocked. **No scope, estimate or sequencing change beyond PO-04's fixed order** |
| Authority | `.clinerules` §1 level 2 (explicit owner instruction), §11 (append-only), §6 (compliance reporting) |

*End of Amendment A-3.*

