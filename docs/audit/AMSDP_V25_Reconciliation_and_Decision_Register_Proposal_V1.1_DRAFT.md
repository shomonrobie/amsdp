# AMSDP — V2.5 Reconciliation and Decision Register Proposal

> **Document ID:** `AMSDP_V25_Reconciliation_and_Decision_Register_Proposal`
> **Version:** V1.1 **DRAFT — review only**
> **Date:** 2026-11-14
> **Status:** **PROPOSAL. NOTHING HAS BEEN IMPLEMENTED AND NO GOVERNED DOCUMENT HAS BEEN
> CHANGED.** V1.1 supersedes V1.0 as the working review copy; V1.0 is retained unmodified at
> `docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md`.
> **Prepared for:** Product Owner review and decision.
> **Governed by:** `.clinerules` §2 (task routing), §3 (non-negotiables), §6 (compliance
> reporting), §7 (evidence standard), §11 (documentation output location), §12 (reading
> policy).

## 1. Purpose

The AMSDP document set states several things about the same subject in mutually inconsistent
terms. Six records are involved — Business Rules V1.1, MVP Scope V1.1, Master Feature List
V2.5, the PQV product decision, the owner decision register and `.clinerules` itself. Three
decisions taken on 2026-11-13 (D-01 … D-03) are not yet recorded in the register, and their
effects are not yet present in the documents they govern.

This document is a **review packet**, not an edit. It contains:

1. the three owner decisions as a corrected record ready to be appended to the decision
   register (§3, Appendix A patch 6);
2. a reconciliation matrix C-01 … C-09 — one row per conflict, with the exact replacement
   wording for each affected passage (§4, §5);
3. the complete unified diffs for every proposed change (Appendix A);
4. near-miss findings that were examined and are **not** conflicts (§6);
5. the open questions that must be answered before any of this is applied (§7).

**Why V1.1 exists.** V1.0 misdescribed all three owner decisions: it turned D-01 into a
storage-and-migration mandate, attributed the 9 November Missed-Turn Recovery approval to D-02,
and attributed BanglaNameSense to D-03. §3.0 lists each misdescription against the corrected
reading. V1.1 also withdraws one incorrect V1.0 finding (a non-existent V2.5 cross-reference
drift) and drops one patch (§2.4).

**What this document is not.** It is not an approval, not an implementation, not a schema
change, not a migration, not a code change, and not a substitute for the Product Owner's
decision. Nothing in the tree was modified to produce it. Every proposed edit exists only as
text in this file.

## 2. Basis, method and evidence

### 2.1 Repository state at the time of writing

Branch `hackathon-mvp`, HEAD `c5fc646`. `git status --short` at the start of this task:

```
 M frontend/styles/global.css
?? _tools/
?? docker-compose.demo.yml
```

All three entries **predate this task and are unrelated work**; file modification times are
2026-11-10 21:15, 2026-11-10 21:27 and 2026-11-11 13:24, against a 2026-11-14 run. This task
neither created nor touched them (`.clinerules` §9: never tidy someone else's uncommitted
work). During the session `docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md` also appeared
as untracked, preceded by a transient `.swp` file, from a concurrent editing session; this task
did not create, read or touch it either.

The only repository writes this task makes are the present file and one index row (§9). After
them, `git status --short` reads:

```
 M docs/governance/AMSDP_Docs_Index_V1.0.md
 M frontend/styles/global.css
?? _tools/
?? docker-compose.demo.yml
?? docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.1_DRAFT.md
?? docs/chatgpt/AMSDP_Hackathon_Implementation_Backlog.md
```

Nothing is staged or committed.

### 2.2 How each proposed replacement was verified

No replacement was written from memory or from a paraphrase. The method is mechanical and
reproducible:

1. The target file was read from disk and the passage located by **exact-string search**.
2. A generator asserted that the matched text occurs **exactly once** in the file before
   substituting it. A zero-match or multi-match aborts the whole run, so no quote below can be
   a partial or an ambiguous match. All 35 replacements (§2.3) passed that assertion.
3. The replacement was applied to an in-memory copy; the original on disk was never written.
4. A unified diff (3 lines of context, `a/`…`b/` paths, `git apply` compatible) was produced
   from the in-memory copy against the original.
5. `git apply --check` was run against the live working tree as **non-mutating proof** that
   each patch applies to the bytes currently committed. `--check` writes nothing.

The exactly-once guard earned its keep during authoring: it rejected two hand-transcribed
targets (an ASCII arrow where the source has `→`, and a lost four-space continuation indent)
before any diff was recorded. Both were corrected against the file and the run repeated.

### 2.3 Result

| # | Target file | Patch | Edits | Hunks | Bytes | `git apply --check` |
|---|---|---|---|---|---|---|
| 1 | `docs/AMSDP_Business_Rules_V1.1.md` | `business_rules.patch` | 6 | 5 | 5,329 | rc=0 |
| 2 | `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` | `v25.patch` | 3 | 3 | 3,159 | rc=0 |
| 3 | `docs/AMSDP_MVP_SCOPE_V1.1.md` | `mvp_scope.patch` | 14 | 13 | 9,019 | rc=0 |
| 4 | `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | `pqv.patch` | 9 | 6 | 9,494 | rc=0 |
| 5 | `.clinerules` | `clinerules.patch` | 2 | 2 | 2,377 | rc=0 |
| 6 | `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md` | `register.patch` | 1 | 1 | 4,701 | rc=0 |
| — | all six combined | `all.patch` | 35 | 30 | 34,079 | rc=0 |

Hunk counts are `grep -c '^@@'` on each patch file, not the number of conceptual edits: edits
inside one three-line-context window merge into a single hunk, which is why patch 1 carries six
edits in five hunks and patch 4 carries nine edits in six hunks.

### 2.4 What changed between V1.0 and V1.1

| V1.0 item | V1.1 status | Reason |
|---|---|---|
| `br_proposal_draft.patch` — marking `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` SUPERSEDED | **Dropped** | It rewrites a historical draft no approved document depends on; `.clinerules` §11 forbids rewriting historical documents, and retiring a document is an owner decision, not a reconciliation. Raised as U-5. |
| D-01 patch content (storage model, nullability, “application-level capture”, “one Alembic migration”) | **Removed from every patch** | Not what D-01 decides. D-01 permits two answers and settles nothing about storage (§3.1). No migration appears anywhere in Appendix A. |
| `.clinerules` §11 edit adding V2.5 to the owner-controlled list | **Removed** | D-02 covers §1 and §10 only (§3.2). §11 is untouched. |
| Finding: “V2.5 §22 item 4 cross-reference drift — §25.7 is the notification record” | **Withdrawn as incorrect** | §25.7 is “Missed-Turn Recovery & Queue Repositioning (approved 2026-11-09)”; §25.9 is the approval record. The cross-references are correct. The real defect in V2.5 is the §23 Phase 3 bullet, which is corrected (C-04). |
| V1.0 arithmetic: 8 patches, 41 hunks, 45,809 bytes | **Superseded** | Those figures describe the V1.0 patch set (V1.0 §2.3 line 78). V1.1 is 6 patches, 35 edits, 30 hunks, 34,079 bytes. |

### 2.5 What this task did not do

- No governed document, code file, schema, migration, endpoint, component or test was modified.
- Nothing was staged, committed, pushed or reverted.
- No test suite was run, because no code changed. No capability is newly TESTED or VERIFIED by
  this document. The status statements in §3.5 are readings of files present on disk plus the
  named reports, and each carries its own evidence label.
- No model or provider was called. `.clinerules` §8 (local-model priority) was not engaged:
  this is document reconciliation, not code generation.
- `frontend/styles/global.css`, `_tools/` and `docker-compose.demo.yml` were not touched.

## 3. Owner decisions D-01 … D-03 (corrected)

These are the three owner decisions of 2026-11-13 that the documents do not yet reflect. The
full record text proposed for the decision register is in `register.patch` (Appendix A,
patch 6, “Part II — Decision records D-01 … D-03”).

### 3.0 What V1.0 got wrong, and the corrected reading

| Ref | V1.0 said | Corrected reading (this version) |
|---|---|---|
| **D-01** | “Two non-binding informational payment indicators may be **stored against an appointment** … staff-entered … **Requires one Alembic migration**”, plus new payment clauses in Business Rules, MVP Scope and V2.5 §15.2/§21/§24 | D-01 permits **two informational Yes/No answers** — is advance payment made, is full payment made — and settles **nothing** about storage, nullability, placement, permissions, reporting or migration. It is a data-display/permission-boundary decision, not a schema decision. No migration, column, endpoint or component is proposed anywhere in this document. |
| **D-02** | “Missed-Turn Recovery & Queue Repositioning is **approved MVP/P0** … restating the owner approval of 2026-11-09” | D-02 is the **`.clinerules` authority-reference correction**: the precedence section (§1) and governance index (§10) must cite Business Rules V1.1 and MVP Scope V1.1. The Missed-Turn Recovery approval is a separate, earlier owner decision (2026-11-09) and is restated in §3.4, not attributed to D-02. |
| **D-03** | “BanglaNameSense … is **Phase 1, advisory only**” | D-03 authorises **preparation of this reconciliation material only** — review text, no application. BanglaNameSense's Phase 1 advisory status is a separate recorded position (§3.4, R-2) and appears in this packet only as a consequence (C-09). |

### 3.1 D-01 — two informational payment indicators

**Decision.** AMSDP may record two informational Yes/No indicators: *is advance payment made?*
and *is full payment made?* Nothing else financial is recorded — no amount, balance, receipt,
settlement, wallet, transaction reference, QR payment record, invoice or ledger entry.

**Nature.** Advisory information only. The indicators create no financial obligation,
entitlement or reconciliation state, and nothing in the product may use them to decide
eligibility, priority, scheduling or access.

**Explicitly not decided by D-01.** The storage model (table, columns, nullability), whether a
value attaches to an appointment or to another record, any migration, interface placement,
which role may set them, audit detail beyond existing patterns, and any reporting or export
treatment. D-01 does not authorise implementation either: it permits the two answers and
nothing more.

**What this packet therefore proposes.** Only the *permission boundary*: Business Rules §34
clause 7 (new) records that the two answers are permitted and everything else financial is still
forbidden; MVP Scope §5.6 states the same and says explicitly that storage, nullability,
permissions, interface placement and reporting are unsettled. Nothing in Appendix A creates a
column, table, migration, endpoint or component.

**Evidence of current state.** `grep -rn payment backend --include=*.py` returns **no matches**:
no payment handling exists in the backend. The capability is **ABSENT**, and this packet claims
no implementation.

### 3.2 D-02 — `.clinerules` authority references

**Decision.** The authority references in `.clinerules` **§1 (precedence)** and **§10
(governance document index)** must cite the current approved documents —
`docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` — and identify the
`docs/product/` V1.0 files as retained historical baselines.

**Scope limit.** Only §1 and §10. `.clinerules` §11 (documentation output location) and every
other section are unchanged. This is a reference correction, not a change to precedence, to the
non-negotiables or to the evidence standard.

**Why it needs the owner.** `.clinerules` is the agent governance file. Patch 5 changes an
agent's own instructions, so it should be applied by the Product Owner or on explicit
instruction — see U-6.

### 3.3 D-03 — authorisation to prepare this material

**Decision.** Preparation of review material that identifies and corrects cross-document
inconsistencies across Business Rules V1.1, MVP Scope V1.1, Master Feature List V2.5, the PQV
decision, the decision register and `.clinerules` is authorised — as reviewed, proposed text
only.

**Not authorised.** Applying any proposed edit to a governed document or to `.clinerules`; any
code, schema, migration, endpoint, component or test change; any product-scope change or new
requirement; any claim that a proposed capability is implemented. Each proposed edit needs
separate owner approval, and `.clinerules` §11 keeps every owner-controlled document read-only
until that approval is given.

### 3.4 Related decisions restated (not newly approved)

| Ref | Decision | Already recorded in |
|---|---|---|
| R-1 | Missed-Turn Recovery & Queue Repositioning is approved MVP/P0 scope (9 November 2026), superseding the 8 November 2026 not-approved status | `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 6, §17; `docs/AMSDP_Business_Rules_V1.1.md` §27A; PQV decision §K.0 (after the proposed correction) |
| R-2 | BanglaNameSense Bangla patient-name suggestions are Phase 1 scope, advisory only | Master Feature List V2.5 §25.8 and Part II item 15; `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` |
| R-3 | DQDS and PQT are Phase 1 (MVP) capabilities | PQV decision §H; `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 1 |
| R-4 | Two-stage notifications (confirmation plus pre-visit reminder) are approved P0 scope, WhatsApp and SMS, provider-dependent delivery | PQV decision §J; `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 6 |

These four rows restate decisions that already exist elsewhere. They create no new approval and
no new requirement; they are listed so the register shows no false gap where those capabilities
are concerned.

### 3.5 Capability status in the tree (evidence-checked)

Recorded because three of these capabilities are described inconsistently *because* their
implementation status differs. Labels follow `.clinerules` §7. Nothing below is VERIFIED and
nothing is ACCEPTED; no test suite was run for this document.

| Capability | In the tree? | Evidence read this session | Label |
|---|---|---|---|
| Missed-Turn Recovery & Queue Repositioning | Yes | `backend/queuing/recovery.py` (12,143 bytes, 2026-11-09 21:35); tests `backend/tests/test_sequence3.py`, `backend/tests/test_sequence4.py` | IMPLEMENTED |
| DQDS | Yes | `backend/queuing/display.py` (7,958 bytes); `APIRouter(prefix="/api/v1/queue/display", tags=["dqds"])`, rate-limited read-only endpoint | IMPLEMENTED |
| PQT | Yes | `backend/appointment/tracking.py` (9,337 bytes); `tags=["pqt"]`, tracking-token issue/revoke and `/track/{token}` | IMPLEMENTED |
| WhatsApp / SMS notifications | Partly | `backend/common/notifications/{__init__,config,hooks,outbox,providers,worker}.py`; `MockNotificationProvider` with `name = "mock"`, `declared_providers()` defaulting to `mock`, and `integration_status: "mock-only"` when no real provider is implemented | IMPLEMENTED (outbox + mock providers); real provider delivery **ABSENT** |
| BanglaNameSense | Yes, frontend only | `frontend/lib/bangla-name-sense/{normalize,matcher,controller,dataset,validate-dataset}.js`, `frontend/components/BanglaNameSense.js`, `frontend/data/bangla_name_sense.json`, four test files under `frontend/tests/`; report `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` (2026-11-10) | IMPLEMENTED; TESTED per that report (not re-run here); no server-side Bangla logic — `grep -rni bangla backend --include=*.py` returns no matches |
| Payment indicators (D-01) | No | `grep -rn payment backend --include=*.py` returns no matches | ABSENT, and DEFERRED pending an approved design (U-3) |

Two consequences for the proposals below. First, no patch may be justified by “make the text match
the code”, because the code is not ACCEPTED and, for payments, does not exist. Second, the
proposals stay at the level of *approved scope and constraints*; they never certify delivery.

## 4. Reconciliation matrix — C-01 … C-09

| ID | Conflict | Where | Proposed correction | Patches |
|---|---|---|---|---|
| **C-01** | Business Rules §2 lists a large excluded set with no boundary notes, so an approved capability (payment indicators, queue visibility, notifications, missed-turn recovery) looks excluded by adjacency. | BR §2 | New §2.1 “Approved scope clarifications”: four numbered notes pointing at the clause that governs each approved capability, plus a closing paragraph listing what the clarifications do **not** admit. | 1 |
| **C-02** | DQDS is **later-phase** in Business Rules §33 and §47, but **Phase 1 (MVP)** in the PQV decision and MVP Scope §16 item 1; MVP Scope §7 and §8 still exclude DQDS and public queue screens outright. | BR §33, §47; MVP §7, §8 | BR §33 corrected to Phase 1/PQT included, with display refinements left later-phase; §47 bullet replaced; MVP §7 queue extensions and §8 Phase 2 bullets re-scoped to “beyond the approved capability”; §8 note corrected. V2.5 §23 already keeps only *advanced* multi-display in Phase 3 — consistent, unchanged. | 1, 3 |
| **C-03** | Business Rules §35 clause 5 calls SMS “a later-phase capability” and §36 is headed “SMS — APPROVED, PHASE 2”; MVP §7 lists “Automated SMS, WhatsApp … reminders” and “External messaging provider integration” as exclusions and says “Automated messaging … deferred”. All four contradict the PQV decision (§D, P0) and MVP §16 item 6. | BR §35, §36, §47; MVP §7, §14 | BR §35 clauses 5–7 rewritten (approved Phase 1/P0, provider-dependent, one-way and staff-mediated, booking independent of messaging); §36 heading and rules reconciled; §47 bullet replaced; MVP §7 exclusions narrowed to what is genuinely out of scope; the §14 “deferred” bullet narrowed to messaging outside the approved requirement. | 1, 3 |
| **C-04** | Missed-Turn Recovery is described as “not approved” (PQV row 3, §H, §K) and “not part of the MVP” (V2.5 §23 Phase 3) while Business Rules §27A, MVP §5.8/§16/§17 and V2.5 §22/§25.7/§25.9 record the 9 November 2026 MVP/P0 approval. | PQV row 3, §H, §K; V2.5 §23 | Reconcile **up** to the approved status, never demote it: PQV row 3 and §H marked superseded and approved; §K gains a status history (K.0) that keeps the 8 November entry as history; V2.5 §23 Phase 3 bullet re-scoped to *refinements*, with the workflow named as MVP/P0. | 4, 2 |
| **C-05** | Governing paths point at files that do not exist. `docs/product/` contains no V1.1 file, yet `.clinerules` §1/§10 cite V1.0 as authoritative, MVP §10 and §15 cite `docs/product/AMSDP_Business_Rules_V1.1.md`, and V2.5 §26.11 cites `docs/product/AMSDP_MVP_SCOPE_V1.1.md`. | `.clinerules` §1, §10; MVP §10, §15; V2.5 §26.11 | Every governing path corrected to the file that exists; V1.0 copies named as retained historical baselines; V2.5's change-control rule states it does not override the other two. | 5, 3, 2 |
| **C-06** | The PQV decision still treats Business Rules **V1.0** as authoritative, says its own reconciliation is merely “authorized”, and its conflict table still points at V1.0; MVP §14 still says the scope “follows … Business Rules V1.0”. | PQV header, approval rows 4, §0.2, §0.4, §G; MVP §14 | PQV updated to Business Rules V1.1 with the reconciling sections named, row 4 marked DELIVERED, conflict table rewritten, implementation-status banner corrected; MVP §14 sentence corrected to V1.1. | 4, 3 |
| **C-07** | V2.5's page-1 change-control rule claims V2.5 governs whenever an older statement conflicts — contradicting `.clinerules` §1, Business Rules authority and V2.5's own §26.11. | V2.5 line 10 | V2.5 declared authoritative for **feature inventory and module catalogue only**; behaviour stays with BR V1.1 and the Phase 1 boundary with MVP Scope V1.1. | 2 |
| **C-08** | The payment prohibition reads as absolute — BR §34, MVP §5.6, MVP §7 “Payments and finance” — while D-01 permits exactly two Yes/No answers. | BR §34; MVP §5.6, §7 | BR §34 clause 7 (new): the two answers permitted, every other financial value still forbidden, storage/permissions/reporting explicitly unsettled. MVP §5.6 states the same and §7 opens with the one-line D-01 exception. | 1, 3 |
| **C-09** | BanglaNameSense is a listed P0 feature (V2.5 §25.8, Part II item 15, “Added … as a P0 core MVP feature”) and is implemented in the frontend, but MVP Scope V1.1 never mentions it, so an approved, shipped-adjacent capability has no release home. | MVP §5.3, §18 | MVP §5.3 gains an advisory-only capability bullet and an acceptance bullet (“no population, replacement or submission without explicit staff selection”); §18 records the amendment. V2.5 needs no change. | 3 |

## 5. Detail — exact replacement wording

Quotes below are read from disk; each was matched exactly once before substitution (§2.2). The
complete, verbatim diffs are Appendix A.

### 5.1 C-01 — Business Rules §2: approved-scope clarifications (patch 1)

**Current** — §2 ends with the exclusion list and one closing sentence:

> Do not introduce these features as hidden dependencies of appointment workflows.

**Proposed** — keep that sentence and append §2.1 with four numbered notes: (1) payment
indicators, two Yes/No answers only, see §34 clause 7; (2) patient queue visibility — DQDS and
PQT approved Phase 1 under `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`, see §33; (3) WhatsApp and
SMS — approved Phase 1 (P0), organization-configurable, see §35 and §36; (4) missed-turn
recovery — approved MVP scope 2026-11-09, see §27A. A closing paragraph states that the
clarifications do **not** admit interactive messaging, a patient portal, patient accounts,
clinical records or payment processing.

One hunk deliberately: the four notes and the closing sentence are the boundary statement, and
splitting them would let one note be applied without the limit that constrains it.

### 5.2 C-02 — DQDS/PQT: later-phase versus Phase 1 (patch 1, patch 3)

**Business Rules §33, current:**

> DQDS, television integration and multi-display configuration are later-phase capabilities.
> Design the Phase 1 queue/token data model so DQDS can be added without redesigning the queue
> engine.

**Proposed:** DQDS *and PQT* are approved **Phase 1 (MVP)** capabilities under
`AMSDP-PRODUCT-DECISION-PQV-2026-11-08` (MVP Scope §16 item 1); multi-display management
beyond that requirement, additional display topologies and richer countdown/reporting stay
later-phase; the Phase 1 data model must support both without redesign.

**MVP Scope §7, current** — a `### Queue extensions` section that excludes “Digital queue
display/TV system”, “Multi-screen display configuration”, “Public-facing queue screens” and
“Advanced queue display countdowns”. **Proposed:** the section opens by recording that DQDS and
PQT are *in* Phase 1, and the bullets are re-scoped to extensions beyond the approved
capability.

**MVP Scope §7 note, current:** “Basic token generation is in Phase 1. Printed queue tokens and
digital queue displays are planned for Phase 2…” **Proposed:** basic token generation *and* the
approved DQDS/PQT capability are Phase 1; printed token hardware and thermal-printer support
remain later-phase; the manual print/export workaround stays non-binding.

**MVP Scope §8 Phase 2 candidates, current** — includes “Digital Queue Display System (DQDS),
read-only and privacy-preserving by default.” **Proposed:** that bullet and the SMS bullet are
replaced by “refinements beyond the approved Phase 1 capability / beyond the approved two-stage
requirement”, so Phase 2 no longer re-announces a Phase 1 capability.

**Master Feature List V2.5 §23** already keeps only “Advanced multi-display DQDS management” in
Phase 3 — consistent with the corrected Business Rules. No V2.5 change for C-02.

### 5.3 C-03 — SMS and WhatsApp channels (patch 1, patch 3)

**Business Rules §35 clause 5, current:**

> 5.  SMS is a later-phase capability, not a Phase 1 dependency.

**Proposed:** clause 5 becomes three clauses — 5: WhatsApp and SMS are approved Phase 1 (P0)
channels, configurable per organization, with delivery dependent on the external provider and
a ban on claiming unconfirmed delivery; 6: communication is operational, staff-mediated and
one-way in Phase 1, with interactive messaging, chat, a patient portal and clinical content
excluded; 7: booking must stay fully functional when messaging is disabled, unconfigured or
unavailable. Clause 7 preserves the intent of the old clause — messaging is never a hard
dependency — without demoting it from approved scope.

**Business Rules §36, current:** heading `## 36. SMS --- APPROVED, PHASE 2`, with rules 1–2
(“SMS is optional and configurable…”, “Use an external SMS provider.”). **Proposed:**
`## 36. SMS and WhatsApp --- APPROVED, PHASE 1 (P0), PROVIDER-DEPENDENT`, covering the same
capability over both channels, with per-channel enablement and one provider per channel; the
approved two-stage requirement is cross-referenced to MVP Scope §16 item 6.

**Business Rules §47, current** (Phase 2 list): “Digital Queue Display System…”, “Estimated
waiting-time countdown.”, “Manual and automatic SMS.” **Proposed:** two bullets — queue-display
refinements beyond the approved DQDS/PQT capability, and notification channels/matrices beyond
the approved WhatsApp/SMS requirement.

**MVP Scope §7, current:** excludes “Automated SMS, WhatsApp, email or voice reminders”,
“External messaging provider integration” and “Interactive messaging or a patient-initiated
conversation channel”, and §14 says “Automated messaging and pre-visit intake are deferred.”
**Proposed:** §7 excludes only what is genuinely out of scope (other channels, multi-step
campaigns, provider integration for any channel other than the approved WhatsApp/SMS channels,
interactive messaging); §14 narrows “automated messaging” to *outside* the approved two-stage
requirement.

### 5.4 C-04 — Missed-Turn Recovery (patch 4, patch 2)

Three PQV passages and one V2.5 bullet still describe the capability as unapproved. The correct
status is the 9 November 2026 approval (R-1), and the reconciliation never demotes an approval.

| Location | Current | Proposed |
|---|---|---|
| PQV approval table, row 3 | “**NOT APPROVED FOR MVP** — remains proposed/later-phase; no implementation; future proposal must address BR §§20–21…“ | “**NOT APPROVED FOR MVP (2026-11-08) — SUPERSEDED 2026-11-09: APPROVED as MVP/P0 scope.**”, with MVP Scope §16 item 6/§17, Business Rules §27A and §K.0 named |
| PQV §H table row | “…requires future product decision + Business Rules amendments…; not implemented” | Approved MVP/P0 (2026-11-09); governed by §27A; implemented in `backend/queuing/recovery.py` with tests in `test_sequence3.py` / `test_sequence4.py` — IMPLEMENTED, not ACCEPTED |
| PQV §K opening | “**Product-owner status (2026-11-08): NOT APPROVED FOR MVP.** … remains a **proposal for later-phase consideration**” | §K retitled, with a new **K.0 status history** (08 Nov noted, 09 Nov approved with the §27A constraints listed, 14 Nov implementation note) and a line stating that K.1–K.5 remain the design intent and that §27A governs where they differ |
| V2.5 §23 Phase 3 | “- Missed-Turn Recovery, as approved under Business Rules V1.1 §27A and product approval; it is not part of the MVP.” | Refinements beyond the approved workflow, with the workflow itself named as MVP/P0 scope |

Business Rules §27A, MVP Scope §5.8 / §16 item 6 / §17, and V2.5 §22 item 4 / §25.7 / §25.9
already state the approved position and are **not** edited. The 8 November 2026 refusal is kept
in the PQV document as history rather than deleted (`.clinerules` §3: history is not rewritten).

### 5.5 C-05 — governing paths (patch 5, patch 3, patch 2)

`docs/product/` holds `AMSDP_Business_Rules_V1.0.md`, `AMSDP_MVP_SCOPE_V1.0.md`, the PQV
decision and the superseded revision draft. It holds **no** V1.1 file, yet five passages cite
one.

| Where | Current | Proposed |
|---|---|---|
| `.clinerules` §1 level 2 | `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md` as the approved business rules | BR V1.1 and MVP Scope V1.1 as the current approved versions, with the `docs/product/` V1.0 files named as retained historical baselines |
| `.clinerules` §10 index | “Business Rules (authoritative): …V1.0”; “MVP scope: …V1.0” | BR V1.1 (+ V1.0 retained at the `docs/product/` path), MVP Scope V1.1 (+ V1.0 retained), and a third entry for V2.5 marked *feature inventory only, does not override* |
| MVP Scope §10 header | “**Related authority:** `docs/product/AMSDP_Business_Rules_V1.1.md`” | `docs/AMSDP_Business_Rules_V1.1.md` (authoritative business behaviour and approved decisions) |
| MVP Scope §15 | `docs/product/AMSDP_Business_Rules_V1.1.md`; `docs/product/AMSDP_MVP_SCOPE_V1.0.md` as the release boundary | `docs/AMSDP_Business_Rules_V1.1.md` and this document, with both V1.0 files named as retained historical baselines. The list is rewritten, so the diff shows a replacement rather than a one-line edit |
| V2.5 §26.11 | `docs/product/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum | `docs/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum, **and it controls the Phase 1 release boundary over this feature list** |

Historical drafts V2.2, V2.3 and V2.4 carry the same stale path. They are owner-controlled and
historical, so they are **not** edited; the index identifies V2.5 as the active list (§11).

### 5.6 C-06 — the PQV decision still cites Business Rules V1.0 (patch 4, patch 3)

| Location | Current (abbreviated) | Proposed (abbreviated) |
|---|---|---|
| PQV implementation-status banner | “**NOT IMPLEMENTED.** … DQDS, PQT, WhatsApp and SMS are not yet implemented in the codebase.” | Revised 2026-11-14: requirements approved and no longer documentation-only; DQDS/PQT/outbox with `mock` providers exist in the tree with named tests; real provider delivery absent; IMPLEMENTED, not ACCEPTED |
| PQV approval row 4 | “**Preparation of a proposed revision authorized** — authoritative Business Rules V1.0 remains unmodified…” | “**DELIVERED — Business Rules V1.1 (9 November 2026)**” with §33, §35/§36 and §27A named |
| PQV §0.2 bullet | “MVP Scope V1.0 §14 … — adjusted via the scope addendum recorded in the MVP Scope document.” | Adjusted by the addendum in MVP Scope V1.1 §16; §7 now excludes only messaging outside this decision |
| PQV §0 item 4 | “Business Rules V1.0 remains the authoritative behaviour document… this decision takes precedence in the interim.” | Business Rules **V1.1** is authoritative and has reconciled §33/§35/§36 and added §27A; where the two still differ the later approved text governs and the difference is a defect to report, not a precedence to exercise |
| PQV §G table, three rows | “Resolution: §D overrides…”, “Scope addendum in MVP Scope V1.0” | Reconciled in Business Rules V1.1 §35, §36, and in MVP Scope V1.1 §16 with §7 corrected |
| MVP Scope §14 | “…follows the later approved product boundaries and Business Rules V1.0…” | “…Business Rules V1.1…” |

No scope, channel or persona changes in C-06; only which document is named as authoritative.

### 5.7 C-07 — V2.5's precedence claim (patch 2)

**Current (V2.5, page 1):**

> **Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions are
> historical records only. Where an older statement conflicts with V2.5, V2.5 governs…

**Proposed:** V2.5 is the sole active Master Feature List and authoritative for **feature
inventory and module catalogue only**; it does not override Business Rules V1.1 (behaviour) or
MVP Scope V1.1 (Phase 1 release boundary), and on any difference those govern. The rest of the
rule — older versions are history, prior decisions stand unless superseded — is unchanged.

### 5.8 C-08 — payments (patch 1, patch 3)

**Business Rules §34, current** ends its prohibition list at clause 6 (“Do not store payment
amount, recipient number, wallet/bank details, QR code, transaction ID, invoice or financial
ledger.”). **Proposed:** a new clause 7 recording the two permitted indicators, stating that no
financial value accompanies them, that they may not drive eligibility/priority/scheduling/access,
and that storage design, nullability, permissions, placement and reporting require separate
approval before implementation.

**MVP Scope §5.6, current** allows only the appointment state `AWAITING_CONFIRMATION` →
`CONFIRMED`. **Proposed:** two additional bullets for the two indicators and one bullet stating
that their storage model, nullability, permissions, placement and reporting are unsettled; and
an added acceptance bullet: “The two informational indicators record an answer only; no
financial value is calculated, stored or displayed.”

**MVP Scope §7 “Payments and finance”, current** opens straight into the exclusion list.
**Proposed:** a two-sentence opening — except for the two informational indicators approved by
D-01 (§5.6), which are not payment collection and relax nothing below — then the unchanged list.

**Known residual, deliberately not edited.** MVP Scope §16 item 4 (the 8 November 2026 addendum)
still lists “payments” among the items that “remain excluded”. The proposed §5.6/§7 wording is
compatible with it — the two indicators are answers, not payment processing — but a reader could
still read item 4 as prohibiting them. Amending the addendum is **not** proposed here because the
addendum is the record of a dated decision; if the owner wants it clarified, that is a further,
separately authorised edit. Flagged so the gap is not mistaken for an oversight.

### 5.9 C-09 — BanglaNameSense (patch 3)

**Current:** MVP Scope V1.1 does not mention BanglaNameSense at all, while V2.5 §25.8, V2.5
Part II item 15 (“BanglaNameSense patient-name assistance, preserving manual entry and existing
patient-registration safeguards”) and V2.5 §25.8's change note (“Added BanglaNameSense as a P0
core MVP feature”) all do. The capability is implemented in the frontend (§3.5).

**Proposed:** MVP §5.3 gains one capability bullet — BanglaNameSense *may* offer Bangla
patient-name suggestions while staff type, advisory only, manual entry always possible, a
suggestion never auto-selects or submits, duplicate warning and verification unchanged — and
one acceptance bullet — suggestions never populate, replace or submit a record without explicit
staff selection. MVP §18 records the amendment and its non-certification.

The wording is deliberately “may offer”: the release boundary records an approved *option*, not
a requirement, because the implementation is frontend-only and not ACCEPTED, and because the
capability must remain degradable when the dataset is unavailable.

## 6. Near-misses — checked, not changed

Recorded because “no conflict found” is a finding, and a reviewer should see what was examined
and deliberately left alone.

| Item examined | Result |
|---|---|
| Six canonical roles (PQV item 3, Business Rules RBAC matrix, MVP Scope §4) | Consistent. No change proposed. |
| Tenant key `organization_id`, org/branch isolation, 404-not-403 rule | Consistent across Business Rules §4, MVP Scope §9 (non-functional requirements) and `.clinerules` §3. No proposal weakens it. |
| Append-only audit trail (Business Rules Part X, MVP Scope §5.10 “Audit history”) | Consistent. The only new state change proposed (a payment indicator) inherits existing audit rules; U-4 asks whether it needs its own event. |
| Two-stage notifications: confirmation + pre-visit reminder, organization-configurable channels, provider-dependent delivery, manual fallback | Stated consistently in PQV §D items 1, 6, 9 and 11, MVP Scope §16 item 6 and the corrected Business Rules §35/§36. No change proposed. |
| “Bangla and Unicode names without corruption” versus BanglaNameSense | Not a contradiction: the requirement is silent on assistance, not hostile to it. Handled as C-09 — a gap, not a conflict. |
| V2.5 §22 item 4 / §25.7 cross-references to Missed-Turn Recovery | **Correct, not drift.** §25.7 is “Missed-Turn Recovery & Queue Repositioning (approved 2026-11-09)” and §25.9 is the approval record. V1.0 asserted drift here; that finding is withdrawn (§2.4). |
| V2.5 §23 note: “SMS and WhatsApp are **not** Phase 3-optional … they are required, organization-configurable channels” | Already agrees with the PQV decision and with the corrected Business Rules. No change. |
| MVP Scope §16 item 6 (MTR + two-stage notifications paragraph) versus Business Rules §27A | Consistent in substance (same default deferral, same override-with-reason, same audit requirement). No change: MVP Scope is the release-boundary authority and already states the approved position. |
| MVP Scope §12 (hackathon demonstration acceptance) versus Phase 1 scope | Compatible: §12 demonstrates Phase 1 workflows. No change. |
| `.clinerules` §11 output-location policy | No violation: this proposal is written under `docs/audit/`; nothing is added to `ai_factory/docs/`, `/tmp`, or the repository root. |
| Historical drafts V2.2, V2.3, V2.4 | Owner-controlled (§11). They carry the same stale `docs/product/…V1.1.md` citation as V2.5; not edited, because history is not rewritten and V2.5 is the active list. |

### 6.1 Hygiene finding — duplicate-copy risk under `docs/product/`

`docs/product/` holds the V1.0 baselines while the **live** V1.1 documents sit at the root of
`docs/`. Because two live documents cite `docs/product/…V1.1.md` paths that do not exist
(C-05), the next person to “fix” the citation is likely to copy the file into `docs/product/`
rather than correct the path — producing two divergent copies of an authoritative document while
the governance index points at one of them.

C-05 corrects the paths. This document recommends that no V1.1 copy is ever created under
`docs/product/` and that the V1.0 files stay where they are, labelled historical.

## 7. Unresolved — owner input required

**U-1 — decision wording (CLOSED).** V1.0's reconstruction of D-01 … D-03 was wrong on all
three counts (§3.0). The owner supplied the corrected reading in review, and patch 6 carries it.
Remaining action: append Part II to the register once approved — no further judgement needed.

**U-2 — Missed-Turn Recovery direction (CLOSED).** Approved MVP/P0 on 9 November 2026, later
than the 8 November refusal. Patch 4 reconciles up and keeps the refusal as history. There is no
pending inversion.

**U-3 — D-01 storage, permission and interface design (OPEN; blocks any D-01 code work, not
this packet).** Nothing here proposes a design, and none may be inferred. Open questions: does
the answer attach to an appointment, a visit, or nothing at all; nullable or defaulted; which
roles may set it (front desk, doctor, both); where it is shown (booking detail, queue view,
both); is it editable after the visit starts; and what happens to the answers when an
appointment is rescheduled.

**U-4 — D-01 audit granularity (OPEN).** Does setting or clearing an indicator emit an audit
event, does clearing require a reason, and is the event per indicator or per change? Suggested
default, consistent with existing appointment-state auditing: one event per change, no reason
required. Not assumed anywhere in Appendix A.

**U-5 — status of the superseded revision draft (OPEN).**
`docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` is history that still reads
like a live specification. V1.1 proposes no edit to it (patch dropped, §2.4). Options: (a) leave
it untouched — this packet's §6.1 records the risk; (b) the owner adds a SUPERSEDED line; (c)
record its status in the docs index only. Option (b) is a one-line owner edit and is the
clearest; it is not taken here because it would rewrite a historical document.

**U-6 — permission to apply patch 5 (`.clinerules`) (OPEN).** Patch 5 changes the agent
governance file's precedence references and index. Under `.clinerules` §11 that is an owner act.
Apply it yourself, or instruct an agent to apply it in a single stated operation.

**U-7 — C-09 wording and placement (OPEN).** Confirm the advisory “may offer” wording in MVP
§5.3, and confirm that the BanglaNameSense dataset stays frontend-supplied
(`frontend/data/bangla_name_sense.json`) rather than being served by the backend. If the owner
prefers the release boundary to stay silent on the capability, drop the two §5.3 edits from
patch 3 and keep only the §18 amendment record.

**Not an item, but not hidden either.** §5.8 records one residual this packet does not close: MVP
Scope §16 item 4 (the dated 8 November addendum) still names “payments” among the excluded items.
Clarifying it is a separate owner edit on a dated decision record, not a reconciliation.

## 8. Recommended application sequence (if the owner approves)

1. Answer U-3 … U-7. **U-3 and U-4 block only D-01 code work**; the text in Appendix A is
   written to stand regardless of how they are answered, because it commits to no storage design.
2. Apply patches 1–4 and 6 from Appendix A (or `all.patch`), in the order listed, from the
   repository root, after `git apply --check` returns rc=0 for each.
3. Apply patch 5 (`.clinerules`) separately, by the owner or on explicit instruction (U-6).
4. Re-read every changed section in place; confirm no section was changed twice and no hunk
   landed in the wrong place. `git diff --stat` should show six files.
5. Re-run the path audit: no live document may cite `docs/product/AMSDP_Business_Rules_V1.1.md`
   or `docs/product/AMSDP_MVP_SCOPE_V1.1.md`; no live document may present Business Rules V1.0
   as the current authority (historical mentions in changelogs and history sections are expected
   and correct).
6. Update `docs/governance/AMSDP_Docs_Index_V1.0.md`, then issue this proposal as V1.2 (or a
   final V2.0) and mark V1.1 SUPERSEDED. V1.0 and V1.1 are not deleted.
7. Code work is a **separate** task with its own tests and evidence: the D-01 design (U-3/U-4),
   real WhatsApp/SMS provider delivery, and any backend BanglaNameSense work if U-7 asks for it.
   None of that is authorised by this packet.

## 9. Governance and skill compliance

Per `.clinerules` §6.

| Requirement | How it was met |
|---|---|
| §2 task routing | Domains identified: documentation (primary), plus multi-tenant/audit and backend-interface rows touched by the *subject matter*. Index read first; product, architecture and governance documents loaded via its routing. |
| §2.4 / §5 skills | Skill discovery performed: **no installed skill packages** exist in this workspace (`.clinerules` §5, verified: no `.clinerules/skills/`, `.claude/skills/` or repo `skills/`). No skill was used and none is claimed. Governance documents served as the routing material. |
| §3 non-negotiables | No secret read, quoted or written. No governed document modified. The proposals strengthen, and never weaken, server-side authorization, the 404-not-403 rule, the `organization_id` tenant key, append-only audit and migration discipline. No audit or history text is deleted: the 8 November refusal stays in the PQV document. |
| §7 evidence standard | Every capability statement carries a label; nothing is called VERIFIED or ACCEPTED; nothing is called TESTED except BanglaNameSense, whose TESTED status is attributed to the implementation report and explicitly not re-run here. |
| §8 LLM routing | Not engaged; this is document reconciliation, not code generation. No model or provider was called. |
| §9 execution boundaries | No server started, no test suite run, no destructive git command. The dirty files were inspected, left untouched, and are reported in §2.1. |
| §11 output location | Written to `docs/audit/` — the existing subject folder for audit and reconciliation material. No new folder. `ai_factory/docs/`, `/tmp`, and the repository root hold nothing attributable to this task. No file overwritten; V1.0 preserved unmodified at its own path. |
| §12 reading policy | Index read before planning. Documents cited by the path opened in this session. Large documents were searched, not pasted. |

**Files written by this task:** this document, plus one row in
`docs/governance/AMSDP_Docs_Index_V1.0.md` (§11/§12 oblige the index update).

**Not compliance, stated plainly:** no test suite was run, so this document cannot and does not
claim any test result of its own. Its verification is `git apply --check` (rc=0 for all six
patches against HEAD `c5fc646`) and exact-string matching during generation, both reproducible
from §2.2.

## Appendix A — full unified diffs

Generated from the committed bytes of each file with three lines of context. Paths carry `a/`
and `b/` prefixes and apply with `git apply -p1` from the repository root. No diff creates,
deletes, renames or changes the mode of a file; every diff is content only.

| Patch | File | Edits | Hunks | Bytes | `git apply --check` |
|---|---|---|---|---|---|
| A.1 `business_rules.patch` | `docs/AMSDP_Business_Rules_V1.1.md` | 6 | 5 | 5,329 | rc=0 |
| A.2 `v25.patch` | `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` | 3 | 3 | 3,159 | rc=0 |
| A.3 `mvp_scope.patch` | `docs/AMSDP_MVP_SCOPE_V1.1.md` | 14 | 13 | 9,019 | rc=0 |
| A.4 `pqv.patch` | `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | 9 | 6 | 9,494 | rc=0 |
| A.5 `clinerules.patch` | `.clinerules` | 2 | 2 | 2,377 | rc=0 |
| A.6 `register.patch` | `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md` | 1 | 1 | 4,701 | rc=0 |
| A.7 `all.patch` | all six, combined | 35 | 30 | 34,079 | rc=0 |

A.6's single hunk is a single append — Part II — not a one-edit change; the count refers to the
number of matched passages, and an append has no anchor passage to match.

### A.1 — `business_rules.patch` → `docs/AMSDP_Business_Rules_V1.1.md`

```diff
--- a/docs/AMSDP_Business_Rules_V1.1.md
+++ b/docs/AMSDP_Business_Rules_V1.1.md
@@ -122,6 +122,27 @@
 Do not introduce these features as hidden dependencies of appointment
 workflows.
 
+### 2.1 Approved scope clarifications
+
+Four approved capabilities sit at the edge of the list above. Each is
+governed by the section named, and none of them may be introduced as an
+undeclared dependency of an appointment flow:
+
+1.  **Payment indicators** --- two informational Yes/No answers only
+    (product decision D-01, 2026-11-13); see §34 clause 7. No payment
+    amount, gateway, wallet, transaction reference, receipt or ledger is
+    permitted.
+2.  **Patient queue visibility** --- DQDS and PQT are approved Phase 1
+    capabilities under product decision
+    `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`; see §33.
+3.  **WhatsApp and SMS notifications** --- approved Phase 1 (P0),
+    organization-configurable channels; see §35 and §36.
+4.  **Missed-turn recovery and queue repositioning** --- approved MVP
+    scope on 2026-11-09; see §27A.
+
+These clarifications do not admit interactive messaging, a patient
+portal, patient accounts, clinical records or payment processing.
+
 ------------------------------------------------------------------------
 
 # Part II --- Tenancy, organizations and branches
@@ -765,9 +786,14 @@
     queues or settings.
 13. Enforce tenant and branch scope for every display data feed.
 
-DQDS, television integration and multi-display configuration are
-later-phase capabilities. Design the Phase 1 queue/token data model so
-DQDS can be added without redesigning the queue engine.
+DQDS is an approved **Phase 1 (MVP)** capability, not a later-phase
+option, under product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
+(recorded in MVP Scope V1.1 §16 item 1). Personal Queue Tracking (PQT) is
+part of the same approved Phase 1 decision. Multi-display management
+beyond the approved Phase 1 requirement, additional display topologies
+and richer countdown/reporting refinements remain later-phase. The Phase 1
+queue/token data model must support DQDS and PQT without redesigning the
+queue engine.
 
 ------------------------------------------------------------------------
 
@@ -785,6 +811,14 @@
     details.
 6.  Do not store payment amount, recipient number, wallet/bank details,
     QR code, transaction ID, invoice or financial ledger.
+7.  **Two informational indicators (decision D-01, 2026-11-13).** The
+    facility may record a Yes/No answer to "advance payment made" and to
+    "full payment made". These are advisory answers only: no amount,
+    balance, receipt, settlement, wallet or transaction reference is
+    stored alongside them, and nothing in the product may use them to
+    decide eligibility, priority, scheduling or access. Storage design,
+    nullability, permissions, placement and reporting are not settled by
+    this clause and require separate approval before implementation.
 
 ## 35. Patient communication
 
@@ -793,17 +827,28 @@
 2.  Patients do not need an AMSDP account or portal.
 3.  Copyable appointment details may be provided as a staff convenience.
 4.  Printed queue tokens are supported under Section 32.
-5.  SMS is a later-phase capability, not a Phase 1 dependency.
-
-## 36. SMS --- APPROVED, PHASE 2
+5.  WhatsApp and SMS are approved Phase 1 (P0) communication
+    channels, configurable per organization. Actual delivery depends on
+    external provider availability and must never be claimed unless the
+    provider confirms it.
+6.  Communication is operational, staff-mediated and one-way in
+    Phase 1. Interactive patient messaging, chat, a patient portal and
+    clinical content are not permitted.
+7.  Appointment booking must remain fully functional when messaging is
+    disabled, unconfigured or unavailable.
+
+## 36. SMS and WhatsApp --- APPROVED, PHASE 1 (P0), PROVIDER-DEPENDENT
 
 Support both staff-triggered/manual SMS and automatic appointment
-confirmation/reminder SMS.
+confirmation/reminder SMS, and the same capability over WhatsApp. The
+approved two-stage requirement (confirmation plus configurable pre-visit
+reminder) is recorded in MVP Scope V1.1 §16 item 6.
 
 Rules:
 
-1.  SMS is optional and configurable per organization/facility.
-2.  Use an external SMS provider.
+1.  Each channel is configurable per organization/facility and may be
+    disabled independently.
+2.  Use an external provider for each channel.
 3.  Provide facility-configurable templates within platform limits.
 4.  Support facility-level enable/disable and message-event
     configuration.
@@ -972,10 +1017,11 @@
 -   Multi-branch operational refinements.
 -   Appointment transfer workflow if not included earlier.
 -   Token print-layout refinements.
--   Digital Queue Display System, including multi-room/multi-doctor
-    displays.
--   Estimated waiting-time countdown.
--   Manual and automatic SMS.
+-   Queue display refinements beyond the approved Phase 1 DQDS/PQT
+    capability, including additional display topologies and richer
+    countdown/reporting options.
+-   Additional notification channels and richer notification matrices
+    beyond the approved WhatsApp/SMS requirement.
 -   Duplicate patient merge workflow.
 -   Additional approved appointment-change workflows.
 
```

### A.2 — `v25.patch` → `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`

```diff
--- a/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
+++ b/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
@@ -7,7 +7,7 @@
 **Supersedes:** All prior AMSDP Master Feature List versions, including V1.x, V2.0, V2.1, V2.2, V2.3 and V2.4.  
 **Historical preservation:** The complete V2.3 baseline is retained in Appendix A for traceability. V2.4's previous clinical-module proposal is superseded by this V2.5 specification and is not an independent source of current requirements.  
 **Approval basis:** The Product Owner explicitly approved the revised Section C — Product Family and Module Catalogue — on 11 November 2026. This V2.5 document consolidates that approval with the subsequent product direction for Intelligent Clinical Documentation. Approval of this master list does not itself authorize every module for immediate implementation, paid provider procurement, production deployment, or any Git operation.  
-**Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions are historical records only. Where an older statement conflicts with V2.5, V2.5 governs. Individual prior product decisions remain in force unless expressly superseded by a later decision.
+**Core change-control rule:** V2.5 is the sole active Master Feature List and is authoritative for **feature inventory and module catalogue only**. Older Master Feature List versions are historical records only. Where an older Master Feature List statement conflicts with V2.5, V2.5 governs — but V2.5 does not override the authoritative behaviour document (`docs/AMSDP_Business_Rules_V1.1.md`) or the Phase 1 release boundary (`docs/AMSDP_MVP_SCOPE_V1.1.md`); on any point where this feature list differs from either, those documents govern. Individual prior product decisions remain in force unless expressly superseded by a later decision.
 
 ---
 
@@ -2071,8 +2071,9 @@
 - External system integrations.
 - Additional operational reports.
 - Other appointment-related extensions approved by subscribers and AMSDP.
-- Missed-Turn Recovery, as approved under Business Rules V1.1 §27A
-  and product approval; it is not part of the MVP.
+- Missed-Turn Recovery refinements beyond the approved workflow; the
+  approved Missed-Turn Recovery workflow itself is MVP/P0 scope (see §22
+  item 4, §25.7, §25.9 and Business Rules V1.1 §27A).
 
 > **Note:** SMS and WhatsApp are **not** Phase 3-optional per PQV Decision
 > `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` — they are required,
@@ -2686,7 +2687,8 @@
   — authoritative approved PQV decision.
 - `docs/product/AMSDP_Product_Positioning_V1.0.md`
   — approved product positioning and impact-measurement framing.
-- `docs/product/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum.
+- `docs/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum; it
+  controls the Phase 1 release boundary over this feature list.
 - `docs/architecture/AMSDP_System_Architecture_V1.0.md` — architecture,
   security and integration boundaries.
 - `docs/AMSDP_Business_Rules_V1.1.md` — authoritative Business Rules;
```

### A.3 — `mvp_scope.patch` → `docs/AMSDP_MVP_SCOPE_V1.1.md`

```diff
--- a/docs/AMSDP_MVP_SCOPE_V1.1.md
+++ b/docs/AMSDP_MVP_SCOPE_V1.1.md
@@ -7,7 +7,8 @@
 **Status:** Approved MVP scope baseline (V1.1 amendment approved 9 November 2026)\
 **Prepared:** 4 November 2026\
 **Primary market:** Bangladesh\
-**Related authority:** `docs/product/AMSDP_Business_Rules_V1.1.md`
+**Related authority:** `docs/AMSDP_Business_Rules_V1.1.md` (authoritative
+business behaviour and approved decisions)
 
 ------------------------------------------------------------------------
 
@@ -180,6 +181,10 @@
 -   Create, search, view and update organization-owned patient records.
 -   Mandatory patient fields: name and mobile number.
 -   Support Bangla and English names and Unicode text.
+-   BanglaNameSense may offer Bangla patient-name suggestions while staff
+    type, as an advisory aid only: manual entry always remains possible, a
+    suggestion never auto-selects or submits, and the existing duplicate
+    warning and staff verification safeguards are unchanged.
 -   Permit multiple patient records to share a mobile number within the
     same organization, because family members may share a phone.
 -   Make staff select and verify the correct patient when search results
@@ -207,6 +212,8 @@
     patient records.
 -   Bangla characters are stored, retrieved and displayed without
     corruption.
+-   Name suggestions never populate, replace or submit a record without an
+    explicit staff selection.
 -   The system does not silently merge records.
 
 ### 5.4 Doctor and room records
@@ -301,6 +308,15 @@
 -   AMSDP may record only the appointment-level state
     `AWAITING_CONFIRMATION` → `CONFIRMED` when the facility uses that
     workflow.
+-   Two informational Yes/No indicators may be recorded: advance payment
+    made, and full payment made (decision D-01, 2026-11-13). They carry no
+    amount, balance, receipt, settlement, wallet data, transaction
+    reference or ledger entry, and nothing in the product may use them to
+    determine eligibility, priority, scheduling or access.
+-   The storage model, nullability, permissions, UI placement and
+    reporting treatment of those indicators are not settled by this
+    scope; they require a separate approved design (see the amendment
+    record in §18).
 -   Do not implement payment gateway processing, amounts, balances,
     wallet data, transaction IDs, QR payment, invoices or financial
     ledgers.
@@ -313,6 +329,8 @@
 -   A rescheduled appointment is linked to its original appointment.
 -   An appointment cannot be transferred across organizations.
 -   No payment is processed or represented as collected by AMSDP.
+-   The two informational indicators record an answer only; no financial
+    value is calculated, stored or displayed.
 
 ### 5.7 Walk-in registration
 
@@ -548,6 +566,10 @@
 
 ### Payments and finance
 
+Except for the two informational Yes/No payment indicators approved by
+decision D-01 (§5.6). The indicators are not payment collection and do not
+relax any exclusion below.
+
 -   bKash, Nagad, Rocket, Bangla QR, card or other payment gateway
     integration.
 -   Advance, partial or full online payment collection.
@@ -569,8 +591,13 @@
 ### Intake, communication and integrations
 
 -   Pre-visit questionnaires or asynchronous intake links.
--   Automated SMS, WhatsApp, email or voice reminders.
--   External messaging provider integration.
+-   Automated reminders beyond the approved two-stage WhatsApp/SMS
+    notification requirement (§16): email, voice, robocall and multi-step
+    campaign messaging.
+-   Messaging provider integration for any channel other than the
+    organization-configurable WhatsApp/SMS channels required by §16.
+-   Interactive messaging, chat or any patient-initiated conversation
+    channel.
 -   EHR, hospital information system or third-party PMS integration.
 -   National health identity, e-Health Card or national interoperability
     integration.
@@ -586,16 +613,20 @@
 
 ### Queue extensions
 
--   Digital queue display/TV system.
--   Multi-screen display configuration.
--   Public-facing queue screens.
--   Advanced queue display countdowns.
+DQDS and PQT are **in** Phase 1 (§16 item 1). The exclusions below are the
+extensions beyond that approved capability:
+
+-   Additional display topologies and advanced multi-display management
+    beyond the approved DQDS capability.
+-   Display countdown and reporting options richer than the approved
+    estimate-only presentation.
 -   Token printer integration and printer-specific device management.
 
-**Note:** Basic token generation is in Phase 1. Printed queue tokens and
-digital queue displays are planned for Phase 2. A simple manual
-print/export workaround may be used during testing, but it is not a
-release requirement.
+**Note:** Basic token generation and the approved DQDS/PQT capability are
+in Phase 1 (§16 item 1). Printed queue-token hardware support and thermal
+printer integration remain later-phase. A simple manual print/export
+workaround may be used during testing, but it is not a release
+requirement.
 
 ## 8. Later release direction
 
@@ -606,10 +637,11 @@
 Candidate capabilities, subject to prioritization:
 
 -   Printed queue token support and thermal printer compatibility.
--   Digital Queue Display System (DQDS), read-only and
-    privacy-preserving by default.
--   Staff-triggered and automated SMS confirmations/reminders through an
-    external provider.
+-   Queue display refinements beyond the approved Phase 1 DQDS/PQT
+    capability.
+-   Notification refinements beyond the approved two-stage WhatsApp/SMS
+    requirement, such as additional channels and richer event
+    configuration.
 -   More complete branch-level operational reporting.
 -   Patient duplicate merge workflow with authorization and history
     preservation.
@@ -829,7 +861,7 @@
 
 Those ideas remain possible future research topics, but they are **not
 approved Phase 1 scope**. The MVP scope follows the later approved
-product boundaries and Business Rules V1.0, especially the decisions to
+product boundaries and Business Rules V1.1, especially the decisions to
 keep AMSDP facility-centric, staff-mediated and focused on appointment
 and queue operations.
 
@@ -838,7 +870,8 @@
 -   External payments remain outside AMSDP.
 -   Clinical records and vitals are excluded.
 -   Patient login and self-service booking are excluded.
--   Automated messaging and pre-visit intake are deferred.
+-   Automated messaging outside the approved two-stage WhatsApp/SMS
+    notification requirement (§16) and pre-visit intake are deferred.
 -   The MVP does not claim national interoperability or integration with
     government health identity systems.
 
@@ -846,10 +879,12 @@
 
 Use these documents together:
 
-1.  `docs/product/AMSDP_Business_Rules_V1.1.md` --- authoritative
-    business behavior and approved decisions.
-2.  `docs/product/AMSDP_MVP_SCOPE_V1.0.md` --- Phase 1 release boundary
-    and acceptance criteria.
+1.  `docs/AMSDP_Business_Rules_V1.1.md` --- authoritative business
+    behavior and approved decisions. `docs/product/AMSDP_Business_Rules_V1.0.md`
+    is the retained historical baseline.
+2.  This document, `docs/AMSDP_MVP_SCOPE_V1.1.md` --- Phase 1 release
+    boundary and acceptance criteria. `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
+    is the retained historical baseline.
 3.  Product vision, feature list, scope and architecture documents ---
     supporting context, to be reconciled against the two documents above
     before implementation.
@@ -918,3 +953,27 @@
 V1.0 is retained as the historical baseline. V1.1 is the current
 approved MVP scope. Approval of the requirement does not itself certify
 that the workflow has been implemented or tested.
+
+## 18. Amendment record --- 14 November 2026
+
+Recorded without changing the approved Phase 1 workflow set:
+
+1.  **D-01 (2026-11-13): two informational payment indicators.** Recorded
+    in §5.6 as informational answers only, with §7 clarified so that the
+    indicators are not read as payment collection. No storage design,
+    permission, interface or migration is authorised by this record, and
+    no capability is claimed as implemented.
+2.  **BanglaNameSense --- approved Phase 1, advisory only.** Recorded in
+    §5.3. Implementation evidence is separate and is not re-certified
+    here: `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md`
+    (2026-11-10) reports the capability as IMPLEMENTED and TESTED, not
+    ACCEPTED.
+3.  **Missed-turn recovery** remains as recorded in §5.8, §16 item 6 and
+    §17 (approved 9 November 2026). This amendment does not change its
+    status.
+4.  **Governing paths and document references** in §14 and §15 corrected;
+    DQDS/PQT and notification exclusions in §7 and §8 restored to the
+    approved Phase 1 position recorded in §16.
+
+V1.0 remains the historical baseline and no approved requirement is
+removed by this amendment.
```

### A.4 — `pqv.patch` → `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`

```diff
--- a/docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md
+++ b/docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md
@@ -4,8 +4,12 @@
 > **Status:** APPROVED (product owner) — design baseline for architecture/scope updates
 > **Date:** 8 November 2026
 > **Applies to:** AMSDP — Appointment Management System for Doctors & Patients
-> **Implementation status:** **NOT IMPLEMENTED.** This document records requirements and
-> design direction. DQDS, PQT, WhatsApp and SMS are not yet implemented in the codebase.
+> **Implementation status (revised 2026-11-14):** the requirements in this document are
+> approved and are no longer documentation-only. DQDS, PQT and the notification outbox with
+> `mock` providers exist in the tree (`backend/queuing/display.py`,
+> `backend/appointment/tracking.py`, `backend/common/notifications/`) with named tests.
+> Real WhatsApp/SMS provider delivery is still absent. In-tree capability is IMPLEMENTED;
+> nothing here is ACCEPTED, and this note is not a VERIFIED claim.
 
 ## Product-owner approval status (2026-11-08)
 
@@ -13,8 +17,8 @@
 |---|---|---|
 | 1 | Public Product Positioning — "AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences." (primary for public website, hackathon materials, product communications) | **APPROVED** |
 | 2 | Two-Stage Patient Notifications (N1 confirmation + N2 pre-visit reminder, default 10 min, 5/10 options; WhatsApp & SMS org-configurable; queue-change-aware scheduling; cooldown/dedup; reminder cancellation; no delivery claim unless provider confirms; booking functional without messaging) | **APPROVED as P0 product scope** |
-| 3 | Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** — remains proposed/later-phase; no implementation; future proposal must address BR §§20–21, grace periods, late arrivals, queue-state semantics, emergency/priority handling and audit events |
-| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **Preparation of a proposed revision authorized** — authoritative Business Rules V1.0 remains unmodified until the proposed revision is separately presented and approved |
+| 3 | Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP (2026-11-08) — SUPERSEDED 2026-11-09: APPROVED as MVP/P0 scope.** Recorded in MVP Scope V1.1 §16 item 6 and §17; governed by Business Rules V1.1 §27A; see §K.0 |
+| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **DELIVERED — Business Rules V1.1 (9 November 2026)** reconciles §33 (DQDS Phase 1), §35/§36 (WhatsApp + SMS, Phase 1/P0) and adds §27A (missed-turn recovery). V1.1 is the authoritative behaviour document |
 
 ## 0. Authority and relationship to other documents
 
@@ -27,15 +31,18 @@
      remains dependent on provider availability (§D.11).
    - Master Feature List V2.0 Draft §14.2 (communication features PENDING) and §23 Phase 3
      (SMS optional extension) — updated per WP2.
-   - MVP Scope V1.0 §14 ("automated messaging deferred") — adjusted via the scope addendum
-     recorded in the MVP Scope document.
+   - MVP Scope V1.0 §14 ("automated messaging deferred") — adjusted by the scope addendum
+     in MVP Scope V1.1 §16; MVP Scope V1.1 §7 now excludes only messaging that falls outside
+     this decision.
 3. **Preserved unchanged:** the six canonical system roles and the existing RBAC permission
    model; the tenant key (`organization_id`); strict tenant and branch isolation; all previously
    approved exclusions (no patient accounts, patient portal, self-service booking, or mandatory
    mobile application).
-4. Business Rules V1.0 remains the authoritative behaviour document; where a future Business
-   Rules revision reconciles §35/§36 to this decision, this decision takes precedence in the
-   interim. Document conflicts are tracked in §9 and in WP2/WP3 outputs.
+4. Business Rules **V1.1** (9 November 2026) is the authoritative behaviour document; it has
+   reconciled §33, §35 and §36 to this decision and added §27A for missed-turn recovery.
+   Where this decision and Business Rules V1.1 still differ, the later approved text governs
+   and the difference is a defect to be reported, not a precedence to be exercised. Document
+   conflicts are tracked in §G and in WP2/WP3 outputs.
 
 ## A. Four primary personas
 
@@ -146,9 +153,9 @@
 
 | Source | Original statement | PQV change | Resolution |
 |---|---|---|---|
-| Business Rules §35 | SMS is later-phase; communication staff-only | WhatsApp + SMS promoted to required channels; org-admin configurable | §D overrides; §35/§36 reconciled in next BR update |
-| Business Rules §36 | SMS APPROVED, PHASE 2 | WhatsApp added; both promoted to required | Same |
-| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Scope addendum in MVP Scope V1.0 |
+| Business Rules §35 | SMS is later-phase; communication staff-only | WhatsApp + SMS promoted to required channels; org-admin configurable | Reconciled in **Business Rules V1.1 §35** |
+| Business Rules §36 | SMS APPROVED, PHASE 2 | WhatsApp added; both promoted to required | Reconciled in **Business Rules V1.1 §36** (Phase 1/P0) |
+| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Scope addendum recorded in **MVP Scope V1.1 §16**; §7 corrected |
 | Master Feature List §14.2 | Communication features PENDING; SMS optional Phase 3 | Updated per WP2 | Feature list updated |
 | System Architecture §5.11 | Notification Service — later capability | Elevated to required; provider delivery remains provider-dependent | Architecture §5.11 updated |
 | System Architecture §13 | No provider-secret storage defined | Requires encrypted org-scoped secret store | Architecture §13 updated |
@@ -162,13 +169,16 @@
 | WhatsApp delivery | Approved channel requirement — **provider-dependent** (account/API, template approval, costs may apply) |
 | SMS delivery | Approved channel requirement — **provider-dependent** (account/sender ID, costs may apply) |
 | Two-Stage Patient Notifications (confirmation + pre-visit reminder) | **APPROVED P0 product scope** (see §J) — **provider-dependent** for actual delivery; not implemented |
-| Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** (see §K) — proposed/later-phase; requires future product decision + Business Rules amendments (§§20–21, grace, late arrival, queue semantics, emergency/priority, audit); not implemented |
+| Missed-Turn Recovery & Queue Repositioning | **APPROVED MVP/P0 (2026-11-09)**, superseding the 2026-11-08 status (see §K.0); governed by Business Rules V1.1 §27A; implemented in `backend/queuing/recovery.py` with tests in `backend/tests/test_sequence3.py` and `backend/tests/test_sequence4.py` (IMPLEMENTED in the tree; not ACCEPTED) |
 | Advanced multi-display management, richer notification matrix, additional channels | Later-phase enhancements |
 
 ## I. No-implementation statement
 
-This decision has **not been implemented** and no cloud activity has occurred. It is
-documentation-only output of the coordinated documentation tasks (decision ID above).
+**Revised 2026-11-14.** This decision is no longer documentation-only: DQDS, PQT and the
+notification outbox with `mock` providers exist in the tree, and missed-turn recovery is
+implemented under Business Rules V1.1 §27A. Still absent: real WhatsApp/SMS provider
+delivery. No cloud activity occurred as part of the original decision task, and no capability
+here is ACCEPTED or claimed as VERIFIED by this note.
 
 ## J. Two-Stage Patient Notifications & Queue Turn Protection
 
@@ -243,11 +253,23 @@
 7. **Scope/status distinction:** this approval is product scope only; implementation status is
    tracked separately (currently **not implemented**).
 
-## K. Missed-Turn Recovery & Queue Repositioning (proposed)
-
-**Product-owner status (2026-11-08): NOT APPROVED FOR MVP.** This capability remains a
-**proposal for later-phase consideration**. It is **not** approved scope and **not**
-implemented. Existing queue and no-show rules are unchanged.
+## K. Missed-Turn Recovery & Queue Repositioning
+
+### K.0 Status history
+
+- **2026-11-08:** recorded as a proposal and NOT APPROVED FOR MVP. That status is retained in
+  the approval table above as history and is not deleted.
+- **2026-11-09:** **APPROVED as MVP/P0 scope** by the product owner; recorded in MVP Scope V1.1
+  §16 item 6 and §17; specified in Business Rules V1.1 §27A (staff-confirmed event, default
+  deferral to the end of the same applicable active queue, authorized override with reason,
+  appointment/token/history preservation, audit, no automatic `NO_SHOW`, no inference from
+  messaging or tracking activity, no clinical triage).
+- **2026-11-14:** implementation exists in `backend/queuing/recovery.py`, with tests in
+  `backend/tests/test_sequence3.py` and `backend/tests/test_sequence4.py`. IMPLEMENTED in the
+  tree; not ACCEPTED; this note is not a VERIFIED claim.
+
+K.1–K.5 below are retained as the original proposal text and remain the design intent; where
+they differ from Business Rules V1.1 §27A, §27A governs.
 
 ### K.1 Expected workflow
 
```

### A.5 — `clinerules.patch` → `.clinerules`

```diff
--- a/.clinerules
+++ b/.clinerules
@@ -8,7 +8,7 @@
 ## 1. Precedence — resolve conflicts in this order
 
 1. **System and safety constraints** — verified runtime state, hardware runtime context (4GB VRAM / 16GB RAM), host limits. Within this level, AMSDP's verified ordering applies: verified runtime state → LLM availability routing → hardware runtime context → generic SaaS convention.
-2. **Explicit project-owner instructions and approved AMSDP business rules** — `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, frozen system design requirements.
+2. **Explicit project-owner instructions and approved AMSDP business rules** — `docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` (the current approved versions), the retained historical baselines `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, and frozen system design requirements.
 3. **AMSDP project governance** — this file and `docs/governance/AMSDP_Engineering_Governance_Assessment.md`.
 4. **Applicable engineering rules** — the agent-rules files in `ai_factory/docs/agent-rules/`, applied **only as adapted** in the governance assessment §3. Do not blindly apply CarbonTally-specific requirements.
 5. **Selected specialized skills** — see §5 Skills Registry (none installed today).
@@ -105,8 +105,9 @@
 
 ## 10. Project Governance Document Index
 
-- Business Rules (authoritative): `docs/product/AMSDP_Business_Rules_V1.0.md`
-- MVP scope: `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
+- Business Rules (authoritative): `docs/AMSDP_Business_Rules_V1.1.md` (V1.0 retained at `docs/product/AMSDP_Business_Rules_V1.0.md` as the historical baseline)
+- MVP scope (Phase 1 release boundary): `docs/AMSDP_MVP_SCOPE_V1.1.md` (V1.0 retained at `docs/product/AMSDP_MVP_SCOPE_V1.0.md`)
+- Master Feature List (active): `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` — feature inventory only; it does not override Business Rules V1.1 or MVP Scope V1.1
 - Governance assessment (authoritative routing detail): `docs/governance/AMSDP_Engineering_Governance_Assessment.md`
 - Skill routing architecture: `docs/governance/AMSDP_Skill_Routing_Architecture.md`
 - **Documentation navigation index (read first, every task):** `docs/governance/AMSDP_Docs_Index_V1.0.md`
```

### A.6 — `register.patch` → `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`

```diff
--- a/docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md
+++ b/docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md
@@ -198,4 +198,72 @@
 - No commit made under these decisions may include unrelated work, and nothing is
   pushed without a separate owner instruction.
 
-
+---
+
+# Part II — Decision records D-01 … D-03 (13 November 2026)
+
+> **Provenance.** These three records were taken by the Product Owner on 2026-11-13 and were
+> first reconstructed from their effects in
+> `docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md`
+> (2026-11-14, open item U-1). The wording below is the corrected reading supplied in review
+> of that proposal. Proposal V1.0 overstated D-01 (storage, nullability and migration),
+> attributed the 9 November missed-turn approval to D-02, and attributed BanglaNameSense to
+> D-03. Those three misdescriptions are removed here.
+
+## D-01 — Two informational payment indicators
+
+**Decision.** AMSDP may record **two informational Yes/No indicators**: *is advance payment
+made?* and *is full payment made?* Nothing else financial is recorded — no amount, balance,
+receipt, settlement, wallet, transaction reference, QR payment record, invoice or ledger
+entry.
+
+**Nature.** Advisory information only. The indicators create no financial obligation,
+entitlement or reconciliation state, and nothing in the product may use them to decide
+eligibility, priority, scheduling or access.
+
+**Explicitly not decided by D-01.** The storage model (table, columns, nullability), whether
+a value attaches to an appointment or to another record, any migration, interface placement,
+which role may set them, audit detail beyond existing patterns, and any reporting or export
+treatment. D-01 does not authorise implementation either; it permits the two answers and
+nothing more.
+
+**Does not change.** Business Rules V1.1 §2 and §34 remain in force for every other
+financial prohibition; MVP Scope V1.1 §7 remains in force for payment collection; no payment
+is processed, represented as collected or reconciled by AMSDP.
+
+## D-02 — `.clinerules` authority references
+
+**Decision.** The authority references in `.clinerules` **§1 (precedence)** and **§10
+(governance document index)** must cite the current approved documents —
+`docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` — and identify the
+`docs/product/` V1.0 files as retained historical baselines.
+
+**Scope limit.** Only §1 and §10. `.clinerules` §11 (documentation output location) and every
+other section are unchanged. This is a reference correction, not a change to precedence, the
+non-negotiables or the evidence standard.
+
+## D-03 — Preparation of the C-01 … C-09 reconciliation review material
+
+**Decision.** Preparation of review material that identifies and corrects cross-document
+inconsistencies across Business Rules V1.1, MVP Scope V1.1, Master Feature List V2.5, the PQV
+decision, this register and `.clinerules` is authorised — as reviewed, proposed text only.
+
+**Not authorised.** Applying any proposed edit to a governed document or to `.clinerules`;
+any code, schema, migration, endpoint, component or test change; any product-scope change or
+new requirement; any claim that a proposed capability is implemented. Each proposed edit
+needs separate owner approval, and `.clinerules` §11 keeps every owner-controlled document
+read-only until that approval is given.
+
+## Related decisions restated (not newly approved)
+
+| Ref | Decision | Already recorded in |
+|---|---|---|
+| R-1 | Missed-Turn Recovery & Queue Repositioning is approved MVP/P0 scope (9 November 2026), superseding the 8 November 2026 not-approved status | `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 6, §17; `docs/AMSDP_Business_Rules_V1.1.md` §27A; PQV decision §K.0 (after the proposed correction) |
+| R-2 | BanglaNameSense Bangla patient-name suggestions are Phase 1 scope, advisory only | Master Feature List V2.5 Part II item 15 (retained V2.3 §25.8); `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` — IMPLEMENTED and TESTED, not ACCEPTED |
+| R-3 | DQDS and PQT are Phase 1 (MVP) capabilities | PQV decision §H; `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 1 |
+| R-4 | Two-stage notifications (confirmation plus pre-visit reminder) are approved P0 scope, WhatsApp and SMS, provider-dependent delivery | PQV decision §J; `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 6 |
+
+These four rows restate decisions that already exist elsewhere. They create no new approval
+and no new requirement; they are listed so the register shows no false gap where those
+capabilities are concerned.
+
```

### A.7 — `all.patch` → all six files, combined

Concatenation of A.1–A.6 in order; byte-identical in content to the six separate patches.

```diff
--- a/docs/AMSDP_Business_Rules_V1.1.md
+++ b/docs/AMSDP_Business_Rules_V1.1.md
@@ -122,6 +122,27 @@
 Do not introduce these features as hidden dependencies of appointment
 workflows.
 
+### 2.1 Approved scope clarifications
+
+Four approved capabilities sit at the edge of the list above. Each is
+governed by the section named, and none of them may be introduced as an
+undeclared dependency of an appointment flow:
+
+1.  **Payment indicators** --- two informational Yes/No answers only
+    (product decision D-01, 2026-11-13); see §34 clause 7. No payment
+    amount, gateway, wallet, transaction reference, receipt or ledger is
+    permitted.
+2.  **Patient queue visibility** --- DQDS and PQT are approved Phase 1
+    capabilities under product decision
+    `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`; see §33.
+3.  **WhatsApp and SMS notifications** --- approved Phase 1 (P0),
+    organization-configurable channels; see §35 and §36.
+4.  **Missed-turn recovery and queue repositioning** --- approved MVP
+    scope on 2026-11-09; see §27A.
+
+These clarifications do not admit interactive messaging, a patient
+portal, patient accounts, clinical records or payment processing.
+
 ------------------------------------------------------------------------
 
 # Part II --- Tenancy, organizations and branches
@@ -765,9 +786,14 @@
     queues or settings.
 13. Enforce tenant and branch scope for every display data feed.
 
-DQDS, television integration and multi-display configuration are
-later-phase capabilities. Design the Phase 1 queue/token data model so
-DQDS can be added without redesigning the queue engine.
+DQDS is an approved **Phase 1 (MVP)** capability, not a later-phase
+option, under product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
+(recorded in MVP Scope V1.1 §16 item 1). Personal Queue Tracking (PQT) is
+part of the same approved Phase 1 decision. Multi-display management
+beyond the approved Phase 1 requirement, additional display topologies
+and richer countdown/reporting refinements remain later-phase. The Phase 1
+queue/token data model must support DQDS and PQT without redesigning the
+queue engine.
 
 ------------------------------------------------------------------------
 
@@ -785,6 +811,14 @@
     details.
 6.  Do not store payment amount, recipient number, wallet/bank details,
     QR code, transaction ID, invoice or financial ledger.
+7.  **Two informational indicators (decision D-01, 2026-11-13).** The
+    facility may record a Yes/No answer to "advance payment made" and to
+    "full payment made". These are advisory answers only: no amount,
+    balance, receipt, settlement, wallet or transaction reference is
+    stored alongside them, and nothing in the product may use them to
+    decide eligibility, priority, scheduling or access. Storage design,
+    nullability, permissions, placement and reporting are not settled by
+    this clause and require separate approval before implementation.
 
 ## 35. Patient communication
 
@@ -793,17 +827,28 @@
 2.  Patients do not need an AMSDP account or portal.
 3.  Copyable appointment details may be provided as a staff convenience.
 4.  Printed queue tokens are supported under Section 32.
-5.  SMS is a later-phase capability, not a Phase 1 dependency.
-
-## 36. SMS --- APPROVED, PHASE 2
+5.  WhatsApp and SMS are approved Phase 1 (P0) communication
+    channels, configurable per organization. Actual delivery depends on
+    external provider availability and must never be claimed unless the
+    provider confirms it.
+6.  Communication is operational, staff-mediated and one-way in
+    Phase 1. Interactive patient messaging, chat, a patient portal and
+    clinical content are not permitted.
+7.  Appointment booking must remain fully functional when messaging is
+    disabled, unconfigured or unavailable.
+
+## 36. SMS and WhatsApp --- APPROVED, PHASE 1 (P0), PROVIDER-DEPENDENT
 
 Support both staff-triggered/manual SMS and automatic appointment
-confirmation/reminder SMS.
+confirmation/reminder SMS, and the same capability over WhatsApp. The
+approved two-stage requirement (confirmation plus configurable pre-visit
+reminder) is recorded in MVP Scope V1.1 §16 item 6.
 
 Rules:
 
-1.  SMS is optional and configurable per organization/facility.
-2.  Use an external SMS provider.
+1.  Each channel is configurable per organization/facility and may be
+    disabled independently.
+2.  Use an external provider for each channel.
 3.  Provide facility-configurable templates within platform limits.
 4.  Support facility-level enable/disable and message-event
     configuration.
@@ -972,10 +1017,11 @@
 -   Multi-branch operational refinements.
 -   Appointment transfer workflow if not included earlier.
 -   Token print-layout refinements.
--   Digital Queue Display System, including multi-room/multi-doctor
-    displays.
--   Estimated waiting-time countdown.
--   Manual and automatic SMS.
+-   Queue display refinements beyond the approved Phase 1 DQDS/PQT
+    capability, including additional display topologies and richer
+    countdown/reporting options.
+-   Additional notification channels and richer notification matrices
+    beyond the approved WhatsApp/SMS requirement.
 -   Duplicate patient merge workflow.
 -   Additional approved appointment-change workflows.
 
--- a/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
+++ b/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
@@ -7,7 +7,7 @@
 **Supersedes:** All prior AMSDP Master Feature List versions, including V1.x, V2.0, V2.1, V2.2, V2.3 and V2.4.  
 **Historical preservation:** The complete V2.3 baseline is retained in Appendix A for traceability. V2.4's previous clinical-module proposal is superseded by this V2.5 specification and is not an independent source of current requirements.  
 **Approval basis:** The Product Owner explicitly approved the revised Section C — Product Family and Module Catalogue — on 11 November 2026. This V2.5 document consolidates that approval with the subsequent product direction for Intelligent Clinical Documentation. Approval of this master list does not itself authorize every module for immediate implementation, paid provider procurement, production deployment, or any Git operation.  
-**Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions are historical records only. Where an older statement conflicts with V2.5, V2.5 governs. Individual prior product decisions remain in force unless expressly superseded by a later decision.
+**Core change-control rule:** V2.5 is the sole active Master Feature List and is authoritative for **feature inventory and module catalogue only**. Older Master Feature List versions are historical records only. Where an older Master Feature List statement conflicts with V2.5, V2.5 governs — but V2.5 does not override the authoritative behaviour document (`docs/AMSDP_Business_Rules_V1.1.md`) or the Phase 1 release boundary (`docs/AMSDP_MVP_SCOPE_V1.1.md`); on any point where this feature list differs from either, those documents govern. Individual prior product decisions remain in force unless expressly superseded by a later decision.
 
 ---
 
@@ -2071,8 +2071,9 @@
 - External system integrations.
 - Additional operational reports.
 - Other appointment-related extensions approved by subscribers and AMSDP.
-- Missed-Turn Recovery, as approved under Business Rules V1.1 §27A
-  and product approval; it is not part of the MVP.
+- Missed-Turn Recovery refinements beyond the approved workflow; the
+  approved Missed-Turn Recovery workflow itself is MVP/P0 scope (see §22
+  item 4, §25.7, §25.9 and Business Rules V1.1 §27A).
 
 > **Note:** SMS and WhatsApp are **not** Phase 3-optional per PQV Decision
 > `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` — they are required,
@@ -2686,7 +2687,8 @@
   — authoritative approved PQV decision.
 - `docs/product/AMSDP_Product_Positioning_V1.0.md`
   — approved product positioning and impact-measurement framing.
-- `docs/product/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum.
+- `docs/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum; it
+  controls the Phase 1 release boundary over this feature list.
 - `docs/architecture/AMSDP_System_Architecture_V1.0.md` — architecture,
   security and integration boundaries.
 - `docs/AMSDP_Business_Rules_V1.1.md` — authoritative Business Rules;
--- a/docs/AMSDP_MVP_SCOPE_V1.1.md
+++ b/docs/AMSDP_MVP_SCOPE_V1.1.md
@@ -7,7 +7,8 @@
 **Status:** Approved MVP scope baseline (V1.1 amendment approved 9 November 2026)\
 **Prepared:** 4 November 2026\
 **Primary market:** Bangladesh\
-**Related authority:** `docs/product/AMSDP_Business_Rules_V1.1.md`
+**Related authority:** `docs/AMSDP_Business_Rules_V1.1.md` (authoritative
+business behaviour and approved decisions)
 
 ------------------------------------------------------------------------
 
@@ -180,6 +181,10 @@
 -   Create, search, view and update organization-owned patient records.
 -   Mandatory patient fields: name and mobile number.
 -   Support Bangla and English names and Unicode text.
+-   BanglaNameSense may offer Bangla patient-name suggestions while staff
+    type, as an advisory aid only: manual entry always remains possible, a
+    suggestion never auto-selects or submits, and the existing duplicate
+    warning and staff verification safeguards are unchanged.
 -   Permit multiple patient records to share a mobile number within the
     same organization, because family members may share a phone.
 -   Make staff select and verify the correct patient when search results
@@ -207,6 +212,8 @@
     patient records.
 -   Bangla characters are stored, retrieved and displayed without
     corruption.
+-   Name suggestions never populate, replace or submit a record without an
+    explicit staff selection.
 -   The system does not silently merge records.
 
 ### 5.4 Doctor and room records
@@ -301,6 +308,15 @@
 -   AMSDP may record only the appointment-level state
     `AWAITING_CONFIRMATION` → `CONFIRMED` when the facility uses that
     workflow.
+-   Two informational Yes/No indicators may be recorded: advance payment
+    made, and full payment made (decision D-01, 2026-11-13). They carry no
+    amount, balance, receipt, settlement, wallet data, transaction
+    reference or ledger entry, and nothing in the product may use them to
+    determine eligibility, priority, scheduling or access.
+-   The storage model, nullability, permissions, UI placement and
+    reporting treatment of those indicators are not settled by this
+    scope; they require a separate approved design (see the amendment
+    record in §18).
 -   Do not implement payment gateway processing, amounts, balances,
     wallet data, transaction IDs, QR payment, invoices or financial
     ledgers.
@@ -313,6 +329,8 @@
 -   A rescheduled appointment is linked to its original appointment.
 -   An appointment cannot be transferred across organizations.
 -   No payment is processed or represented as collected by AMSDP.
+-   The two informational indicators record an answer only; no financial
+    value is calculated, stored or displayed.
 
 ### 5.7 Walk-in registration
 
@@ -548,6 +566,10 @@
 
 ### Payments and finance
 
+Except for the two informational Yes/No payment indicators approved by
+decision D-01 (§5.6). The indicators are not payment collection and do not
+relax any exclusion below.
+
 -   bKash, Nagad, Rocket, Bangla QR, card or other payment gateway
     integration.
 -   Advance, partial or full online payment collection.
@@ -569,8 +591,13 @@
 ### Intake, communication and integrations
 
 -   Pre-visit questionnaires or asynchronous intake links.
--   Automated SMS, WhatsApp, email or voice reminders.
--   External messaging provider integration.
+-   Automated reminders beyond the approved two-stage WhatsApp/SMS
+    notification requirement (§16): email, voice, robocall and multi-step
+    campaign messaging.
+-   Messaging provider integration for any channel other than the
+    organization-configurable WhatsApp/SMS channels required by §16.
+-   Interactive messaging, chat or any patient-initiated conversation
+    channel.
 -   EHR, hospital information system or third-party PMS integration.
 -   National health identity, e-Health Card or national interoperability
     integration.
@@ -586,16 +613,20 @@
 
 ### Queue extensions
 
--   Digital queue display/TV system.
--   Multi-screen display configuration.
--   Public-facing queue screens.
--   Advanced queue display countdowns.
+DQDS and PQT are **in** Phase 1 (§16 item 1). The exclusions below are the
+extensions beyond that approved capability:
+
+-   Additional display topologies and advanced multi-display management
+    beyond the approved DQDS capability.
+-   Display countdown and reporting options richer than the approved
+    estimate-only presentation.
 -   Token printer integration and printer-specific device management.
 
-**Note:** Basic token generation is in Phase 1. Printed queue tokens and
-digital queue displays are planned for Phase 2. A simple manual
-print/export workaround may be used during testing, but it is not a
-release requirement.
+**Note:** Basic token generation and the approved DQDS/PQT capability are
+in Phase 1 (§16 item 1). Printed queue-token hardware support and thermal
+printer integration remain later-phase. A simple manual print/export
+workaround may be used during testing, but it is not a release
+requirement.
 
 ## 8. Later release direction
 
@@ -606,10 +637,11 @@
 Candidate capabilities, subject to prioritization:
 
 -   Printed queue token support and thermal printer compatibility.
--   Digital Queue Display System (DQDS), read-only and
-    privacy-preserving by default.
--   Staff-triggered and automated SMS confirmations/reminders through an
-    external provider.
+-   Queue display refinements beyond the approved Phase 1 DQDS/PQT
+    capability.
+-   Notification refinements beyond the approved two-stage WhatsApp/SMS
+    requirement, such as additional channels and richer event
+    configuration.
 -   More complete branch-level operational reporting.
 -   Patient duplicate merge workflow with authorization and history
     preservation.
@@ -829,7 +861,7 @@
 
 Those ideas remain possible future research topics, but they are **not
 approved Phase 1 scope**. The MVP scope follows the later approved
-product boundaries and Business Rules V1.0, especially the decisions to
+product boundaries and Business Rules V1.1, especially the decisions to
 keep AMSDP facility-centric, staff-mediated and focused on appointment
 and queue operations.
 
@@ -838,7 +870,8 @@
 -   External payments remain outside AMSDP.
 -   Clinical records and vitals are excluded.
 -   Patient login and self-service booking are excluded.
--   Automated messaging and pre-visit intake are deferred.
+-   Automated messaging outside the approved two-stage WhatsApp/SMS
+    notification requirement (§16) and pre-visit intake are deferred.
 -   The MVP does not claim national interoperability or integration with
     government health identity systems.
 
@@ -846,10 +879,12 @@
 
 Use these documents together:
 
-1.  `docs/product/AMSDP_Business_Rules_V1.1.md` --- authoritative
-    business behavior and approved decisions.
-2.  `docs/product/AMSDP_MVP_SCOPE_V1.0.md` --- Phase 1 release boundary
-    and acceptance criteria.
+1.  `docs/AMSDP_Business_Rules_V1.1.md` --- authoritative business
+    behavior and approved decisions. `docs/product/AMSDP_Business_Rules_V1.0.md`
+    is the retained historical baseline.
+2.  This document, `docs/AMSDP_MVP_SCOPE_V1.1.md` --- Phase 1 release
+    boundary and acceptance criteria. `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
+    is the retained historical baseline.
 3.  Product vision, feature list, scope and architecture documents ---
     supporting context, to be reconciled against the two documents above
     before implementation.
@@ -918,3 +953,27 @@
 V1.0 is retained as the historical baseline. V1.1 is the current
 approved MVP scope. Approval of the requirement does not itself certify
 that the workflow has been implemented or tested.
+
+## 18. Amendment record --- 14 November 2026
+
+Recorded without changing the approved Phase 1 workflow set:
+
+1.  **D-01 (2026-11-13): two informational payment indicators.** Recorded
+    in §5.6 as informational answers only, with §7 clarified so that the
+    indicators are not read as payment collection. No storage design,
+    permission, interface or migration is authorised by this record, and
+    no capability is claimed as implemented.
+2.  **BanglaNameSense --- approved Phase 1, advisory only.** Recorded in
+    §5.3. Implementation evidence is separate and is not re-certified
+    here: `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md`
+    (2026-11-10) reports the capability as IMPLEMENTED and TESTED, not
+    ACCEPTED.
+3.  **Missed-turn recovery** remains as recorded in §5.8, §16 item 6 and
+    §17 (approved 9 November 2026). This amendment does not change its
+    status.
+4.  **Governing paths and document references** in §14 and §15 corrected;
+    DQDS/PQT and notification exclusions in §7 and §8 restored to the
+    approved Phase 1 position recorded in §16.
+
+V1.0 remains the historical baseline and no approved requirement is
+removed by this amendment.
--- a/docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md
+++ b/docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md
@@ -4,8 +4,12 @@
 > **Status:** APPROVED (product owner) — design baseline for architecture/scope updates
 > **Date:** 8 November 2026
 > **Applies to:** AMSDP — Appointment Management System for Doctors & Patients
-> **Implementation status:** **NOT IMPLEMENTED.** This document records requirements and
-> design direction. DQDS, PQT, WhatsApp and SMS are not yet implemented in the codebase.
+> **Implementation status (revised 2026-11-14):** the requirements in this document are
+> approved and are no longer documentation-only. DQDS, PQT and the notification outbox with
+> `mock` providers exist in the tree (`backend/queuing/display.py`,
+> `backend/appointment/tracking.py`, `backend/common/notifications/`) with named tests.
+> Real WhatsApp/SMS provider delivery is still absent. In-tree capability is IMPLEMENTED;
+> nothing here is ACCEPTED, and this note is not a VERIFIED claim.
 
 ## Product-owner approval status (2026-11-08)
 
@@ -13,8 +17,8 @@
 |---|---|---|
 | 1 | Public Product Positioning — "AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences." (primary for public website, hackathon materials, product communications) | **APPROVED** |
 | 2 | Two-Stage Patient Notifications (N1 confirmation + N2 pre-visit reminder, default 10 min, 5/10 options; WhatsApp & SMS org-configurable; queue-change-aware scheduling; cooldown/dedup; reminder cancellation; no delivery claim unless provider confirms; booking functional without messaging) | **APPROVED as P0 product scope** |
-| 3 | Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** — remains proposed/later-phase; no implementation; future proposal must address BR §§20–21, grace periods, late arrivals, queue-state semantics, emergency/priority handling and audit events |
-| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **Preparation of a proposed revision authorized** — authoritative Business Rules V1.0 remains unmodified until the proposed revision is separately presented and approved |
+| 3 | Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP (2026-11-08) — SUPERSEDED 2026-11-09: APPROVED as MVP/P0 scope.** Recorded in MVP Scope V1.1 §16 item 6 and §17; governed by Business Rules V1.1 §27A; see §K.0 |
+| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **DELIVERED — Business Rules V1.1 (9 November 2026)** reconciles §33 (DQDS Phase 1), §35/§36 (WhatsApp + SMS, Phase 1/P0) and adds §27A (missed-turn recovery). V1.1 is the authoritative behaviour document |
 
 ## 0. Authority and relationship to other documents
 
@@ -27,15 +31,18 @@
      remains dependent on provider availability (§D.11).
    - Master Feature List V2.0 Draft §14.2 (communication features PENDING) and §23 Phase 3
      (SMS optional extension) — updated per WP2.
-   - MVP Scope V1.0 §14 ("automated messaging deferred") — adjusted via the scope addendum
-     recorded in the MVP Scope document.
+   - MVP Scope V1.0 §14 ("automated messaging deferred") — adjusted by the scope addendum
+     in MVP Scope V1.1 §16; MVP Scope V1.1 §7 now excludes only messaging that falls outside
+     this decision.
 3. **Preserved unchanged:** the six canonical system roles and the existing RBAC permission
    model; the tenant key (`organization_id`); strict tenant and branch isolation; all previously
    approved exclusions (no patient accounts, patient portal, self-service booking, or mandatory
    mobile application).
-4. Business Rules V1.0 remains the authoritative behaviour document; where a future Business
-   Rules revision reconciles §35/§36 to this decision, this decision takes precedence in the
-   interim. Document conflicts are tracked in §9 and in WP2/WP3 outputs.
+4. Business Rules **V1.1** (9 November 2026) is the authoritative behaviour document; it has
+   reconciled §33, §35 and §36 to this decision and added §27A for missed-turn recovery.
+   Where this decision and Business Rules V1.1 still differ, the later approved text governs
+   and the difference is a defect to be reported, not a precedence to be exercised. Document
+   conflicts are tracked in §G and in WP2/WP3 outputs.
 
 ## A. Four primary personas
 
@@ -146,9 +153,9 @@
 
 | Source | Original statement | PQV change | Resolution |
 |---|---|---|---|
-| Business Rules §35 | SMS is later-phase; communication staff-only | WhatsApp + SMS promoted to required channels; org-admin configurable | §D overrides; §35/§36 reconciled in next BR update |
-| Business Rules §36 | SMS APPROVED, PHASE 2 | WhatsApp added; both promoted to required | Same |
-| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Scope addendum in MVP Scope V1.0 |
+| Business Rules §35 | SMS is later-phase; communication staff-only | WhatsApp + SMS promoted to required channels; org-admin configurable | Reconciled in **Business Rules V1.1 §35** |
+| Business Rules §36 | SMS APPROVED, PHASE 2 | WhatsApp added; both promoted to required | Reconciled in **Business Rules V1.1 §36** (Phase 1/P0) |
+| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Scope addendum recorded in **MVP Scope V1.1 §16**; §7 corrected |
 | Master Feature List §14.2 | Communication features PENDING; SMS optional Phase 3 | Updated per WP2 | Feature list updated |
 | System Architecture §5.11 | Notification Service — later capability | Elevated to required; provider delivery remains provider-dependent | Architecture §5.11 updated |
 | System Architecture §13 | No provider-secret storage defined | Requires encrypted org-scoped secret store | Architecture §13 updated |
@@ -162,13 +169,16 @@
 | WhatsApp delivery | Approved channel requirement — **provider-dependent** (account/API, template approval, costs may apply) |
 | SMS delivery | Approved channel requirement — **provider-dependent** (account/sender ID, costs may apply) |
 | Two-Stage Patient Notifications (confirmation + pre-visit reminder) | **APPROVED P0 product scope** (see §J) — **provider-dependent** for actual delivery; not implemented |
-| Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** (see §K) — proposed/later-phase; requires future product decision + Business Rules amendments (§§20–21, grace, late arrival, queue semantics, emergency/priority, audit); not implemented |
+| Missed-Turn Recovery & Queue Repositioning | **APPROVED MVP/P0 (2026-11-09)**, superseding the 2026-11-08 status (see §K.0); governed by Business Rules V1.1 §27A; implemented in `backend/queuing/recovery.py` with tests in `backend/tests/test_sequence3.py` and `backend/tests/test_sequence4.py` (IMPLEMENTED in the tree; not ACCEPTED) |
 | Advanced multi-display management, richer notification matrix, additional channels | Later-phase enhancements |
 
 ## I. No-implementation statement
 
-This decision has **not been implemented** and no cloud activity has occurred. It is
-documentation-only output of the coordinated documentation tasks (decision ID above).
+**Revised 2026-11-14.** This decision is no longer documentation-only: DQDS, PQT and the
+notification outbox with `mock` providers exist in the tree, and missed-turn recovery is
+implemented under Business Rules V1.1 §27A. Still absent: real WhatsApp/SMS provider
+delivery. No cloud activity occurred as part of the original decision task, and no capability
+here is ACCEPTED or claimed as VERIFIED by this note.
 
 ## J. Two-Stage Patient Notifications & Queue Turn Protection
 
@@ -243,11 +253,23 @@
 7. **Scope/status distinction:** this approval is product scope only; implementation status is
    tracked separately (currently **not implemented**).
 
-## K. Missed-Turn Recovery & Queue Repositioning (proposed)
-
-**Product-owner status (2026-11-08): NOT APPROVED FOR MVP.** This capability remains a
-**proposal for later-phase consideration**. It is **not** approved scope and **not**
-implemented. Existing queue and no-show rules are unchanged.
+## K. Missed-Turn Recovery & Queue Repositioning
+
+### K.0 Status history
+
+- **2026-11-08:** recorded as a proposal and NOT APPROVED FOR MVP. That status is retained in
+  the approval table above as history and is not deleted.
+- **2026-11-09:** **APPROVED as MVP/P0 scope** by the product owner; recorded in MVP Scope V1.1
+  §16 item 6 and §17; specified in Business Rules V1.1 §27A (staff-confirmed event, default
+  deferral to the end of the same applicable active queue, authorized override with reason,
+  appointment/token/history preservation, audit, no automatic `NO_SHOW`, no inference from
+  messaging or tracking activity, no clinical triage).
+- **2026-11-14:** implementation exists in `backend/queuing/recovery.py`, with tests in
+  `backend/tests/test_sequence3.py` and `backend/tests/test_sequence4.py`. IMPLEMENTED in the
+  tree; not ACCEPTED; this note is not a VERIFIED claim.
+
+K.1–K.5 below are retained as the original proposal text and remain the design intent; where
+they differ from Business Rules V1.1 §27A, §27A governs.
 
 ### K.1 Expected workflow
 
--- a/.clinerules
+++ b/.clinerules
@@ -8,7 +8,7 @@
 ## 1. Precedence — resolve conflicts in this order
 
 1. **System and safety constraints** — verified runtime state, hardware runtime context (4GB VRAM / 16GB RAM), host limits. Within this level, AMSDP's verified ordering applies: verified runtime state → LLM availability routing → hardware runtime context → generic SaaS convention.
-2. **Explicit project-owner instructions and approved AMSDP business rules** — `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, frozen system design requirements.
+2. **Explicit project-owner instructions and approved AMSDP business rules** — `docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` (the current approved versions), the retained historical baselines `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, and frozen system design requirements.
 3. **AMSDP project governance** — this file and `docs/governance/AMSDP_Engineering_Governance_Assessment.md`.
 4. **Applicable engineering rules** — the agent-rules files in `ai_factory/docs/agent-rules/`, applied **only as adapted** in the governance assessment §3. Do not blindly apply CarbonTally-specific requirements.
 5. **Selected specialized skills** — see §5 Skills Registry (none installed today).
@@ -105,8 +105,9 @@
 
 ## 10. Project Governance Document Index
 
-- Business Rules (authoritative): `docs/product/AMSDP_Business_Rules_V1.0.md`
-- MVP scope: `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
+- Business Rules (authoritative): `docs/AMSDP_Business_Rules_V1.1.md` (V1.0 retained at `docs/product/AMSDP_Business_Rules_V1.0.md` as the historical baseline)
+- MVP scope (Phase 1 release boundary): `docs/AMSDP_MVP_SCOPE_V1.1.md` (V1.0 retained at `docs/product/AMSDP_MVP_SCOPE_V1.0.md`)
+- Master Feature List (active): `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` — feature inventory only; it does not override Business Rules V1.1 or MVP Scope V1.1
 - Governance assessment (authoritative routing detail): `docs/governance/AMSDP_Engineering_Governance_Assessment.md`
 - Skill routing architecture: `docs/governance/AMSDP_Skill_Routing_Architecture.md`
 - **Documentation navigation index (read first, every task):** `docs/governance/AMSDP_Docs_Index_V1.0.md`
--- a/docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md
+++ b/docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md
@@ -198,4 +198,72 @@
 - No commit made under these decisions may include unrelated work, and nothing is
   pushed without a separate owner instruction.
 
-
+---
+
+# Part II — Decision records D-01 … D-03 (13 November 2026)
+
+> **Provenance.** These three records were taken by the Product Owner on 2026-11-13 and were
+> first reconstructed from their effects in
+> `docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md`
+> (2026-11-14, open item U-1). The wording below is the corrected reading supplied in review
+> of that proposal. Proposal V1.0 overstated D-01 (storage, nullability and migration),
+> attributed the 9 November missed-turn approval to D-02, and attributed BanglaNameSense to
+> D-03. Those three misdescriptions are removed here.
+
+## D-01 — Two informational payment indicators
+
+**Decision.** AMSDP may record **two informational Yes/No indicators**: *is advance payment
+made?* and *is full payment made?* Nothing else financial is recorded — no amount, balance,
+receipt, settlement, wallet, transaction reference, QR payment record, invoice or ledger
+entry.
+
+**Nature.** Advisory information only. The indicators create no financial obligation,
+entitlement or reconciliation state, and nothing in the product may use them to decide
+eligibility, priority, scheduling or access.
+
+**Explicitly not decided by D-01.** The storage model (table, columns, nullability), whether
+a value attaches to an appointment or to another record, any migration, interface placement,
+which role may set them, audit detail beyond existing patterns, and any reporting or export
+treatment. D-01 does not authorise implementation either; it permits the two answers and
+nothing more.
+
+**Does not change.** Business Rules V1.1 §2 and §34 remain in force for every other
+financial prohibition; MVP Scope V1.1 §7 remains in force for payment collection; no payment
+is processed, represented as collected or reconciled by AMSDP.
+
+## D-02 — `.clinerules` authority references
+
+**Decision.** The authority references in `.clinerules` **§1 (precedence)** and **§10
+(governance document index)** must cite the current approved documents —
+`docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` — and identify the
+`docs/product/` V1.0 files as retained historical baselines.
+
+**Scope limit.** Only §1 and §10. `.clinerules` §11 (documentation output location) and every
+other section are unchanged. This is a reference correction, not a change to precedence, the
+non-negotiables or the evidence standard.
+
+## D-03 — Preparation of the C-01 … C-09 reconciliation review material
+
+**Decision.** Preparation of review material that identifies and corrects cross-document
+inconsistencies across Business Rules V1.1, MVP Scope V1.1, Master Feature List V2.5, the PQV
+decision, this register and `.clinerules` is authorised — as reviewed, proposed text only.
+
+**Not authorised.** Applying any proposed edit to a governed document or to `.clinerules`;
+any code, schema, migration, endpoint, component or test change; any product-scope change or
+new requirement; any claim that a proposed capability is implemented. Each proposed edit
+needs separate owner approval, and `.clinerules` §11 keeps every owner-controlled document
+read-only until that approval is given.
+
+## Related decisions restated (not newly approved)
+
+| Ref | Decision | Already recorded in |
+|---|---|---|
+| R-1 | Missed-Turn Recovery & Queue Repositioning is approved MVP/P0 scope (9 November 2026), superseding the 8 November 2026 not-approved status | `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 6, §17; `docs/AMSDP_Business_Rules_V1.1.md` §27A; PQV decision §K.0 (after the proposed correction) |
+| R-2 | BanglaNameSense Bangla patient-name suggestions are Phase 1 scope, advisory only | Master Feature List V2.5 Part II item 15 (retained V2.3 §25.8); `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` — IMPLEMENTED and TESTED, not ACCEPTED |
+| R-3 | DQDS and PQT are Phase 1 (MVP) capabilities | PQV decision §H; `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 1 |
+| R-4 | Two-stage notifications (confirmation plus pre-visit reminder) are approved P0 scope, WhatsApp and SMS, provider-dependent delivery | PQV decision §J; `docs/AMSDP_MVP_SCOPE_V1.1.md` §16 item 6 |
+
+These four rows restate decisions that already exist elsewhere. They create no new approval
+and no new requirement; they are listed so the register shows no false gap where those
+capabilities are concerned.
+
```
