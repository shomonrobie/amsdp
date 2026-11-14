# AMSDP — V2.5 Reconciliation and Decision Register Proposal

> **Document ID:** `AMSDP_V25_Reconciliation_and_Decision_Register_Proposal`
> **Version:** V1.0 **DRAFT — review only**
> **Date:** 2026-11-14
> **Status:** **PROPOSAL. NOTHING HAS BEEN IMPLEMENTED AND NO GOVERNED DOCUMENT HAS BEEN
> CHANGED.** This file is the only artefact this task adds to the repository.
> **Prepared for:** Product Owner review and decision.
> **Governed by:** `.clinerules` §2 (task routing), §3 (non-negotiables), §6 (compliance
> reporting), §7 (evidence standard), §11 (documentation output location).

## 1. Purpose

The AMSDP document set currently states several things about the same subject in mutually
inconsistent terms. Five documents are involved — Business Rules V1.1, MVP Scope V1.1,
Master Feature List V2.5, the PQV product decision, and `.clinerules` itself — plus the
superseded draft `AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` and the owner
decision register. Three decisions taken on 2026-11-13 (D-01 … D-03) are not recorded in
that register, and their effects are not present in the documents they govern.

This document is a **review packet**, not an edit. It contains:

1. the three owner decisions as a record ready to be appended to the decision register;
2. a reconciliation matrix C-01 … C-09 — one row per conflict, with the **exact replacement
   wording** proposed for each affected passage;
3. the complete unified diffs (Appendix A) for every change proposed;
4. near-miss findings that were checked and are **not** conflicts;
5. the open questions that must be answered before any of this is applied.

**What this document is not.** It is not an approval, not an implementation, not a schema
change, not a code change, and not a substitute for the Product Owner's decision. Nothing in
the tree has been modified to produce it. Every proposed edit exists only as text in this
file.

## 2. Basis, method and evidence

### 2.1 Repository state at the time of writing

`git status --short` immediately before this proposal was assembled:

```
 M frontend/styles/global.css
?? _tools/
?? docker-compose.demo.yml
```

Those three entries are **pre-existing, unrelated work** that this task neither created nor
touched (`.clinerules` §9: never tidy someone else's uncommitted work). This task added
only the present file and one index entry (see §9 of this document).

### 2.2 How each proposed replacement was verified

No replacement in this proposal was written from memory or from a paraphrase of a document.
The method was mechanical, and every step is reproducible:

1. The target file was read and the passage located by **exact-string search**.
2. A generator asserted the matched text occurs **exactly once** in the file before
   substituting it. Any zero-match or multi-match aborts the run — so a "verified" quote
   below cannot be a partial or ambiguous match.
3. The replacement was applied to an in-memory copy; the original on disk was never written.
4. A unified diff (3 lines of context, `a/`…`b/` paths, `git apply` compatible) was produced
   from the in-memory copy versus the original.
5. `git apply --check` was run against the real working tree as **non-mutating proof** that
   each patch applies exactly to the bytes currently committed. `--check` writes nothing.

### 2.3 Result

| # | Target file | Patch | Hunks | Bytes | `git apply --check` |
|---|---|---|---|---|---|
| 1 | `docs/AMSDP_Business_Rules_V1.1.md` | `business_rules.patch` | 7 | 5,685 | rc=0 |
| 2 | `docs/AMSDP_MVP_SCOPE_V1.1.md` | `mvp_scope.patch` | 11 | 7,497 | rc=0 |
| 3 | `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` | `v25.patch` | 9 | 6,159 | rc=0 |
| 4 | same file (supplementary) | `v25_addendum.patch` | 3 | 2,933 | rc=0 |
| 5 | `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | `pqv.patch` | 4 | 7,508 | rc=0 |
| 6 | `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md` | `register.patch` | 3 | 8,623 | rc=0 |
| 7 | `.clinerules` | `clinerules.patch` | 3 | 6,074 | rc=0 |
| 8 | `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` | `br_proposal_draft.patch` | 1 | 1,330 | rc=0 |
| — | all eight combined | `all.patch` | 41 | 45,809 | rc=0 |

Hunk counts are `grep -c '^@@'` on each patch file, not the number of conceptual edits:
several edits fall inside one three-line-context window and merge into a single hunk, which is
why patch 7 (`clinerules`) carries four edits in three hunks and patch 1 (`business_rules`)
eight edits in seven hunks.

### 2.4 What this task did not do

- No governed document, schema, migration, endpoint, component or test was modified.
- Nothing was committed, staged, pushed or reverted.
- No test suite was run, because no code changed; no claim of TESTED or VERIFIED status is
  made anywhere in this document for any capability. Every capability named here remains
  **not implemented**.
- No model or provider was called. Section §8 of `.clinerules` (local-model priority) was
  not engaged: this is document reconciliation, not code generation.

## 3. Owner decisions D-01 … D-03

These are the three decisions of 2026-11-13 that the documents do not yet reflect. The full
record text proposed for the decision register is in the `register.patch` diff (Appendix A,
patch 6, "Part II — Decision records D-01 … D-03"). Summary and effect:

| Decision | Subject | Effect on the document set |
|---|---|---|
| **D-01** | Two non-binding informational payment indicators may be stored against an appointment: *is advance payment made?* and *is full payment made?* — Yes/No, staff-entered, and nothing else financial. | Business Rules V1.1 §2.1 (new) and §34 clause 7 (new); MVP Scope V1.1 §5.6 and §7; Master Feature List V2.5 §15.2, §21 item 6, §24. Requires one Alembic migration. |
| **D-02** | Missed-Turn Recovery & Queue Repositioning is **approved MVP/P0** scope — restating the owner approval of 2026-11-09, not demoting it. | Edited: PQV approval table row 3, §H, §K; Master Feature List V2.5 §22 item 4 and the §23 Phase 3 bullet. Left unchanged because already correct: V2.5 §25.9, MVP Scope V1.1 §5.8/§16 item 6/§17, Business Rules V1.1 §27A. |
| **D-03** | BanglaNameSense (Bangla patient-name suggestions) is **Phase 1, advisory only**. | MVP Scope V1.1 §5.6 and §14 (capability + acceptance); Master Feature List V2.5 §23 Phase 1. |

### 3.1 A direction rule that shaped every edit

Where two approved records disagree, this proposal **never resolves the conflict by
demoting an approval**. Precedence inside a disagreement follows `.clinerules` §1: the
latest explicit owner approval and Business Rules V1.1 outrank an earlier decision record,
and both outrank the feature list. Concretely, for Missed-Turn Recovery:

- the PQV decision of **2026-11-08** says *not approved for MVP*;
- the owner approval of **2026-11-09** is recorded in MVP Scope V1.1 §17 and specified in
  §5.8, and Business Rules V1.1 (also 9 November) governs it in §27A;
- Master Feature List V2.5 contradicts **itself**: §22 item 4 and §25.9 say approved MVP,
  §23 Phase 3 says "not part of the MVP".

A later approval supersedes an earlier record, so MTR reconciles **up to approved MVP**. The
alternative — demoting an approved capability to Phase 3 — would be a product decision that
an agent must not take on the owner's behalf. Open item **U-2** asks the owner to confirm
this reading explicitly.

## 4. Reconciliation matrix — C-01 … C-09

| ID | Conflict | Documents | Proposed resolution | Patch (Appendix A) |
|---|---|---|---|---|
| C-01 | Business Rules has no scope-boundary notes: nothing separates "excluded from Core" from "approved optional module", and the PQV capabilities have no cross-reference from §2. | BR V1.1 §2 | New §2.1 with three clarifying notes (payment indicators, optional clinical module, patient queue visibility). | 1 |
| C-02 | DQDS/PQT are **later-phase** in Business Rules §33 and §47, but **Phase 1/P0** in the PQV decision and MVP Scope V1.1 §16 item 1. | BR §33, §47; PQV; MVP §16 | BR §33 and §47 corrected to Phase 1; the superseded draft proposal marked superseded. | 1, 2, 8 |
| C-03 | Business Rules states SMS is later-phase / staff-only (§35 clause 5, §36 "PHASE 2"); the PQV decision makes WhatsApp + SMS required, org-configurable P0 channels. | BR §35, §36; PQV §D | BR §35 clause 5 and §36 reconciled to approved P0, provider-dependent; one-way WhatsApp put under the same clauses as SMS; interactive messaging still excluded. | 1 |
| C-04 | Missed-Turn Recovery is simultaneously "not approved", "approved MVP" and "Phase 3, not MVP". | PQV rows/§H/§K; V2.5 §22, §23, §25.9; MVP §5.8, §16.6, §17 | Reconciled **up** to approved MVP/P0 per the 2026-11-09 approval (D-02); contradictions corrected in place. | 3, 4, 5 |
| C-05 | Governing paths point at files that do not exist or at superseded versions. `.clinerules` §1/§10 cite V1.0 under `docs/product/`; MVP Scope V1.1 §15 cites `docs/product/AMSDP_MVP_SCOPE_V1.1.md` (missing); V2.5 §26.11 cites the same missing path. | `.clinerules`, MVP §15, V2.5 §26.11 | Every governing path corrected to the file that exists; V1.0 copies labelled historical. | 2, 3, 7 |
| C-06 | The PQV decision still treats Business Rules **V1.0** as authoritative and its own reconciliation as merely "authorized"; its conflict table still points at V1.0. | PQV approval table row 4, §0.2, §0.4, §G | PQV updated to Business Rules V1.1 with the reconciling sections named; row 4 marked DELIVERED. | 5 |
| C-07 | V2.5's page-1 change-control rule claims V2.5 governs whenever an older statement conflicts — contradicting `.clinerules` §1, Business Rules authority and V2.5's own §26.11. | V2.5 page 1, §26.11 | V2.5 declared authoritative for **feature inventory only**; behaviour and Phase 1 boundary remain with BR V1.1 and MVP Scope V1.1. | 3, 4, 7 |
| C-08 | The payment prohibition is absolute in all three documents (BR §34 clause 6; MVP §5.6, §7; V2.5 §15.2, §21 item 6, §24) — D-01 permits exactly two Yes/No indicators. | BR §34; MVP §5.6, §7; V2.5 §15.2, §21, §24 | Narrow, identically-worded exception in all three, with every other financial value still forbidden. | 1, 2, 3 |
| C-09 | BanglaNameSense is listed in V2.5 §25.8 but absent from MVP Scope V1.1 and from the V2.5 Phase 1 list — so a listed feature has no release home. | V2.5 §23, §25.8; MVP §5.6, §14 | BanglaNameSense added to Phase 1 in both documents as advisory-only (D-03). | 2, 3 |

Every row above cites a patch in Appendix A. No row is "noted for later": each has exact
replacement wording, verified to apply to the current tree.

## 5. Detail — exact replacement wording

Each subsection states the conflict, the **current wording** (quoted exactly as found), the
**proposed wording**, and where it lands. Quotes are literal; the generator asserted a single
match before substituting, so a quote here cannot be approximate. Long blocks are abbreviated
with `…` only where noted; Appendix A holds the complete text.

**Appendix A is canonical.** Where a table below summarises a proposed replacement in a few
words, the authoritative wording is the `+` line in the corresponding patch — no reader should
apply a summarised cell as if it were final text.


### 5.1 C-01 — Business Rules §2: scope-boundary notes

**Current wording (end of §2):**

> Do not introduce these features as hidden dependencies of appointment workflows.

**Proposed (new §2.1 appended immediately after that line):**

> ### 2.1 Clarifying notes on the exclusions above
>
> 1.  **Payment indicators (owner decision D-01).** Two non-binding informational
>     indicators are permitted against an appointment: *is advance payment made?*
>     (Yes/No) and *is full payment made?* (Yes/No). They are staff-entered flags, not
>     payment data: no payment amount, transaction information, payment method, receipt,
>     gateway/provider information or payment ledger is permitted. See §34 clause 7.
> 2.  **Optional clinical module.** Clinical Management (consultation records, clinical
>     notes, digital prescriptions, prescription support library and encounter history) is
>     **not part of AMSDP Core** and remains excluded from Core, but it is an approved
>     optional product module under Master Feature List V2.5 §C and §29–§43. Its approval
>     never places clinical records inside Core appointment/queue workflows, and it is not
>     part of the current hackathon release.
> 3.  **Patient queue visibility.** DQDS and PQT are not patient accounts, portals,
>     dashboards or self-booking; see §33.

Item 1 is the §2 counterpart of C-08; items 2 and 3 are the §2 counterpart of the module /
PQV distinctions raised by C-02 and C-07. The three notes are deliberately one hunk, because
they are read as one block.

### 5.2 C-02 — DQDS/PQT: later-phase versus Phase 1

**Current wording (Business Rules §33, closing paragraph):**

> DQDS, television integration and multi-display configuration are later-phase capabilities.
> Design the Phase 1 queue/token data model so DQDS can be added without redesigning the
> queue engine.

**Proposed:**

> DQDS and PQT are Phase 1 (MVP) capabilities under product decision
> `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` (see MVP Scope §16, item 1). Multi-screen
> management, television/hardware selection and advanced countdown presentation remain
> later-phase (§47); design the Phase 1 queue/token data model so they can be added without
> redesigning the queue engine.

**Also in Business Rules §47** — the Phase 2 exclusion list currently reads:

> -   Digital Queue Display System, including multi-room/multi-doctor displays.
> -   Estimated waiting-time countdown.
> -   Manual and automatic SMS.

**Proposed:** the three bullets become

> -   Multi-screen DQDS management beyond the Phase 1 read-only display.
> -   Advanced estimated waiting-time countdown presentation beyond the Phase 1 estimate label.
> -   Notification refinements beyond the approved N1/N2 events.

and a closing note is added to §47:

> DQDS, PQT and one-way operational WhatsApp/SMS notifications are Phase 1 (MVP) capabilities
> under product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` (MVP Scope §16). Provider
> integration and paid services remain subject to separate authorization.

In the same patch, §47's opening Phase-1 boundary bullet set gains that statement, and
`docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` is marked **SUPERSEDED**
(patch 8) so the old carve-out proposal is not mistaken for a second live specification.

### 5.3 C-03 — SMS and WhatsApp channels

**Current wording (Business Rules §35 clause 5 and §36 heading):**

> 5.  SMS is a later-phase capability, not a Phase 1 dependency.
>
> ## 36. SMS — APPROVED, PHASE 2

**Proposed:**

> 5.  SMS and one-way operational WhatsApp notifications are approved P0 channels (see §36),
>     but they are provider-dependent and are never a Phase 1 dependency: booking must stay
>     functional when they are unavailable or unconfigured.
>
> ## 36. SMS and one-way operational WhatsApp — APPROVED P0 SCOPE
>
> Provider integration is not yet implemented; see §47 for the Phase 2 refinements.

**And a new clause 9 in §36, after "8. SMS must not delay the core appointment MVP.":**

> 9.  One-way operational WhatsApp notifications follow the same rules as SMS under this
>     section, including the organization-level channel switch, template control, delivery
>     honesty and non-blocking requirements. Interactive two-way messaging and telemedicine
>     remain excluded (§2).

This is the minimum change that makes §35/§36 agree with PQV §D and MVP Scope V1.1 §16 item 2
without inventing channel behaviour that the PQV decision does not specify.

### 5.4 C-04 — Missed-Turn Recovery

Three statements describe the same capability differently. Current wording:

- PQV approval table row 3: *"**NOT APPROVED FOR MVP** — remains proposed/later-phase; no
  implementation; future proposal must address BR §§20–21, grace periods, late arrivals,
  queue-state semantics, emergency/priority handling and audit events"*
- PQV §K opening: *"**Product-owner status (2026-11-08): NOT APPROVED FOR MVP.** This
  capability remains a **proposal for later-phase consideration**…"*
- Master Feature List V2.5 §23 Phase 3: *"- Missed-Turn Recovery, as approved under Business
  Rules V1.1 §27A and product approval; it is not part of the MVP."*
- while V2.5 §22 item 4 says *"Missed-Turn Recovery is approved P0/MVP (§25.7)"* and §25.9
  says the owner *"formally approved the limited Missed-Turn Recovery workflow for MVP"*.

**Proposed resolution direction:** approved **MVP/P0**, per the 2026-11-09 approval (MVP
Scope V1.1 §17, §5.8) and Business Rules V1.1 §27A.

| Document | Current | Proposed |
|---|---|---|
| PQV row 3 | NOT APPROVED FOR MVP | APPROVED — MVP/P0 (owner approval 2026-11-09; restated by D-02) — governed by BR V1.1 §27A, specified in MVP Scope V1.1 §5.8; not implemented |
| PQV §H row | NOT APPROVED FOR MVP … | APPROVED — MVP/P0 … not implemented |
| PQV §K opening | NOT APPROVED … proposal for later-phase | APPROVED — MVP/P0; the 8 Nov classification was superseded on 9 Nov; not implemented; existing rules unchanged until built |
| V2.5 §23 Phase 3 bullet | "as approved … it is not part of the MVP" | "not a Phase 3 candidate … approved MVP/P0 … delivered inside Phase 1" |
| V2.5 §22 item 4 | "approved P0/MVP (§25.7)" | same claim, cross-reference corrected to §25.9 and the governing sources named |
| V2.5 §25.9 | already says approved for MVP | left as is (it is the correct record) |
| BR V1.1 §27A | governs | unchanged |
| MVP Scope V1.1 §5.8, §16 item 6, §17 | already say approved MVP | unchanged; §17 gains a dated note that D-02 restates, and does not demote, the approval |

The MVP Scope document is deliberately **not** edited on MTR, because it is the release-boundary
authority and it already states the approved position. The documents that contradict it are
the ones that change.

One wording note, because it is visible in patch 6: the D-02 decision record's *Lands in* line
names Master Feature List V2.5 §25.9 among the places this decision is **reflected**. No edit is
applied to §25.9 — it already states the approved position and is left byte-identical. "Lands
in" in the register record therefore means "is reflected in", not "is edited"; the edits are
the §22 item 4 cross-reference and the §23 Phase 3 bullet in patches 3 and 4.

### 5.5 C-05 — governing paths

Four path references point at the wrong place. `docs/product/AMSDP_Business_Rules_V1.1.md`
and `docs/product/AMSDP_MVP_SCOPE_V1.1.md` **do not exist**; the real files are
`docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md`.

| Where | Current | Proposed |
|---|---|---|
| `.clinerules` §1 level 2 | `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md` as the approved business rules | BR V1.1 (behaviour/access/workflow), MVP Scope V1.1 (release boundary), V2.5 (feature inventory only, never overriding the first two); V1.0 copies labelled historical |
| `.clinerules` §10 index | "Business Rules (authoritative): …V1.0"; "MVP scope: …V1.0" | four entries: BR V1.1, MVP Scope V1.1, Master Feature List V2.5, and the V1.0 historical baselines |
| MVP Scope V1.1 §15 | `docs/product/AMSDP_Business_Rules_V1.1.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, "Product vision, feature list…" | `docs/AMSDP_Business_Rules_V1.1.md`, `docs/AMSDP_MVP_SCOPE_V1.1.md`, the V2.5 feature list (subordinate, see its §26.11), then product vision/architecture as supporting context |
| V2.5 §26.11 | `docs/product/AMSDP_MVP_SCOPE_V1.1.md` | `docs/AMSDP_MVP_SCOPE_V1.1.md`, plus a sentence that it controls the Phase 1 boundary over the feature list |

The §15 change also renumbers the list from three items to four, so the diff shows the list
being rewritten rather than a single line replaced (Appendix A, patch 2).

`.clinerules` §11 also gains the V2.5 feature list in its owner-controlled list, since V2.5 is
now the active master feature list and is the owner's writing in the same sense as V2.0–V2.3.

### 5.6 C-06 — the PQV decision still cites Business Rules V1.0

**Current wording (PQV §0, item 4):**

> Business Rules V1.0 remains the authoritative behaviour document; where a future Business
> Rules revision reconciles §35/§36 to this decision, this decision takes precedence in the
> interim.

The interim is over: Business Rules V1.1 (2026-11-09) reconciled §35/§36 in §36, §46 and §47.
**Proposed:**

> Business Rules V1.1 is now the authoritative behaviour document and has already reconciled
> §35/§36 to this decision (§36, §46, §47). This decision remains the authoritative source
> for the product scope it records; where the two differ, the divergence is reported rather
> than resolved silently, and the governing document for behaviour is Business Rules V1.1.

Three satellite passages change with it:

| Location | Current (abbreviated) | Proposed (abbreviated) |
|---|---|---|
| Approval table row 4 | "**Preparation of a proposed revision authorized** — authoritative Business Rules V1.0 remains unmodified until…" | "**DELIVERED in Business Rules V1.1** (§2, §33, §35, §36, §46, §47) — the earlier draft proposal is superseded and is not a source of requirements" |
| §0.2 bullet 1 | "Business Rules V1.0 §35 … and §36 (SMS APPROVED PHASE 2) — WhatsApp and SMS are here promoted …" | "Business Rules §35 … and §36 (SMS APPROVED, PHASE 2) — **reconciled in Business Rules V1.1**: WhatsApp and SMS are approved P0, organization-configurable channels (§36)…" |
| §0.2 bullet 3 | "MVP Scope V1.0 §14 … — adjusted via the scope addendum recorded in the MVP Scope document." | "MVP Scope §14 … — **reconciled in MVP Scope V1.1**: §14 and §16, item 2 record one-way operational notifications as Phase 1 scope…" |
| §G conflict table | "Resolution: Scope addendum in MVP Scope V1.0" | "Reconciled in MVP Scope V1.1 §14 and §16, item 2" |

The decision itself is untouched: no scope, channel or persona changes in C-06.

### 5.7 C-07 — V2.5's precedence claim

**Current wording (Master Feature List V2.5, page 1):**

> **Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions
> are historical records only. Where an older statement conflicts with V2.5, V2.5 governs.
> Individual prior product decisions remain in force unless expressly superseded by a later
> decision.

Read literally, this lets the feature list override Business Rules V1.1 and an owner decision
— contradicting `.clinerules` §1 (approved business rules rank above governance documents),
V2.5's own §26.11 ("subordinate to explicit product-owner decisions and authoritative
approved product/business documents"), and §26.11's closing paragraph.

**Proposed:**

> **Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions
> are historical records only. V2.5 governs **the feature inventory and module catalogue**;
> it does **not** govern behaviour, access rules or the Phase 1 release boundary, which are
> controlled by `docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` (see
> §26.11 and `.clinerules` §1). Individual prior product decisions remain in force unless
> expressly superseded by a later decision.

§26.11's closing paragraph changes from *"The Business Rules V1.0 document remains unchanged
by this revision"* (which now names a historical file) to an explicit rule: behaviour →
Business Rules V1.1 controls; Phase 1 boundary → MVP Scope V1.1 controls; and this document
amends neither.

A second-order consequence is fixed in the same patch: §21's "Explicitly Excluded" list is
the source of the "clinical records are excluded" reading, so it now opens with a note that
the exclusions describe **AMSDP Core** and do not erase approved optional modules (§29–§43);
item 8 is annotated accordingly and item 6 points at the D-01 exception.

### 5.8 C-08 — payments

The prohibition is absolute in three documents, and D-01 is a narrow exception to each:

| Document | Current wording | Proposed addition |
|---|---|---|
| BR §34 | clause 6: "Do not store payment amount, recipient number, wallet/bank details, QR code, transaction ID, invoice or financial ledger." | new clause 7 permitting exactly two Yes/No indicators; forbidding amounts, transactions, methods, receipts, providers and ledgers; forbidding aggregation and reconciliation; forbidding any effect on confirmation |
| MVP §5.6 | "Do not implement payment gateway processing, amounts, balances, wallet data, transaction IDs, QR payment, invoices or financial ledgers." + "No payment is processed or represented as collected by AMSDP." | the two indicators as staff-entered flags, explicitly not financial records; plus "any payment indicator recorded or displayed is a staff-entered Yes/No flag, never an amount, balance, receipt or settlement" |
| MVP §7 "Payments and finance" | bare exclusion list | the heading gains "**Excluded**, with one narrow exception…" naming the two indicators and the §5.6 definition |
| V2.5 §15.2 | "AMSDP does not store payment amount… settlement information." / "No payment dashboard or payment gateway is included." | a D-01 paragraph between the two sentences, listing the same forbidden values as BR §34 clause 7 |
| V2.5 §21 item 6 | "Financial transaction records or payment reconciliation." | annotated with the §15.2 exception |
| V2.5 §24 | "Payments remain outside the platform." | "…; the only payment-related values AMSDP stores are the two informational Yes/No indicators of §15.2." |

The wording is deliberately near-identical in all three documents: a differently-shaped
exception in each document is exactly how this kind of conflict is created.

### 5.9 C-09 — BanglaNameSense

**Current state:** V2.5 §25.8 defines the capability; V2.5 §23 Phase 1 does not list it; MVP
Scope V1.1 requires Bangla/Unicode name handling and says nothing about assistance — so a
listed feature has no release boundary.

**Proposed:**

- MVP §5.11, after the Bangla/Unicode name requirement: a bullet requiring Bangla name
  suggestions **while staff type**, naming BanglaNameSense (V2.5 §25.8), stating they are
  local and advisory, never authoritative, and may be ignored.
- MVP §5.11 acceptance criteria: "Bangla name suggestions assist entry without changing,
  overriding or blocking a staff-entered name."
- V2.5 §23 Phase 1: "-   Bangla name suggestions during staff entry (BanglaNameSense,
  §25.8) — advisory only, never authoritative."

No model, network service or provider is introduced by this change; the proposal
deliberately does not prescribe an implementation, which is a separate technical decision.

## Appendix A — unified diffs (verbatim)

Each patch below is exactly the file that was checked with `git apply --check` against this
tree. They are presented in the order they should be applied; `all.patch` is the
concatenation of the eight in this order. Paths are `a/…` / `b/…` relative to the repository
root, standard three lines of context, `git apply` compatible.

Applying none of them is the current state of the tree.

### A.1 — `business_rules.patch` → `docs/AMSDP_Business_Rules_V1.1.md`

```diff
--- a/docs/AMSDP_Business_Rules_V1.1.md
+++ b/docs/AMSDP_Business_Rules_V1.1.md
@@ -122,6 +122,25 @@
 Do not introduce these features as hidden dependencies of appointment
 workflows.
 
+### 2.1 Clarifying notes on the exclusions above
+
+1.  **Payment indicators (owner decision D-01).** Two non-binding
+    informational indicators are permitted against an appointment: *is
+    advance payment made?* (Yes/No) and *is full payment made?*
+    (Yes/No). They are staff-entered flags, not payment data: no payment
+    amount, transaction information, payment method, receipt,
+    gateway/provider information or payment ledger is permitted. See §34
+    clause 7.
+2.  **Optional clinical module.** Clinical Management (consultation
+    records, clinical notes, digital prescriptions, prescription support
+    library and encounter history) is **not part of AMSDP Core** and
+    remains excluded from Core, but it is an approved optional product
+    module under Master Feature List V2.5 §C and §29–§43. Its approval
+    never places clinical records inside Core appointment/queue
+    workflows, and it is not part of the current hackathon release.
+3.  **Patient queue visibility.** DQDS and PQT are not patient accounts,
+    portals, dashboards or self-booking; see §33.
+
 ------------------------------------------------------------------------
 
 # Part II --- Tenancy, organizations and branches
@@ -765,9 +784,12 @@
     queues or settings.
 13. Enforce tenant and branch scope for every display data feed.
 
-DQDS, television integration and multi-display configuration are
-later-phase capabilities. Design the Phase 1 queue/token data model so
-DQDS can be added without redesigning the queue engine.
+DQDS and PQT are Phase 1 (MVP) capabilities under product decision
+`AMSDP-PRODUCT-DECISION-PQV-2026-11-08` (see MVP Scope §16, item 1).
+Multi-screen management, television/hardware selection and advanced
+countdown presentation remain later-phase (§47); design the Phase 1
+queue/token data model so they can be added without redesigning the
+queue engine.
 
 ------------------------------------------------------------------------
 
@@ -785,6 +807,15 @@
     details.
 6.  Do not store payment amount, recipient number, wallet/bank details,
     QR code, transaction ID, invoice or financial ledger.
+7.  **Permitted informational indicators (owner decision D-01).**
+    Notwithstanding clauses 2 and 6, an appointment may carry exactly two
+    non-binding, staff-entered Yes/No indicators: *is advance payment
+    made?* and *is full payment made?*. They are informational flags, not
+    payment data: no payment amount, transaction information, payment
+    method, receipt, gateway/provider information or payment ledger may be
+    stored with them; they must not be summed, reconciled or reported as
+    financial figures; and they must not gate, replace or silently alter
+    the appointment confirmation workflow.
 
 ## 35. Patient communication
 
@@ -793,9 +824,15 @@
 2.  Patients do not need an AMSDP account or portal.
 3.  Copyable appointment details may be provided as a staff convenience.
 4.  Printed queue tokens are supported under Section 32.
-5.  SMS is a later-phase capability, not a Phase 1 dependency.
-
-## 36. SMS --- APPROVED, PHASE 2
+5.  SMS and one-way operational WhatsApp notifications are approved P0
+    channels (see §36), but they are provider-dependent and are never a
+    Phase 1 dependency: booking must stay functional when they are
+    unavailable or unconfigured.
+
+## 36. SMS and one-way operational WhatsApp --- APPROVED P0 SCOPE
+
+Provider integration is not yet implemented; see §47 for the Phase 2
+refinements.
 
 Support both staff-triggered/manual SMS and automatic appointment
 confirmation/reminder SMS.
@@ -814,6 +851,11 @@
 7.  Do not block appointment creation when SMS is disabled or provider
     unavailable.
 8.  SMS must not delay the core appointment MVP.
+9.  One-way operational WhatsApp notifications follow the same rules as
+    SMS under this section, including the organization-level channel
+    switch, template control, delivery honesty and non-blocking
+    requirements. Interactive two-way messaging and telemedicine remain
+    excluded (§2).
 
 ------------------------------------------------------------------------
 
@@ -972,12 +1014,18 @@
 -   Multi-branch operational refinements.
 -   Appointment transfer workflow if not included earlier.
 -   Token print-layout refinements.
--   Digital Queue Display System, including multi-room/multi-doctor
-    displays.
--   Estimated waiting-time countdown.
--   Manual and automatic SMS.
+-   Multi-screen DQDS management beyond the Phase 1 read-only
+    display.
+-   Advanced estimated waiting-time countdown presentation beyond
+    the Phase 1 estimate label.
+-   Notification refinements beyond the approved N1/N2 events.
 -   Duplicate patient merge workflow.
 -   Additional approved appointment-change workflows.
+
+DQDS, PQT and one-way operational WhatsApp/SMS notifications are Phase 1
+(MVP) capabilities under product decision
+`AMSDP-PRODUCT-DECISION-PQV-2026-11-08` (MVP Scope §16). Provider
+integration and paid services remain subject to separate authorization.
 
 ## 48. Phase 3: Optional extensions
 
@@ -1018,7 +1066,9 @@
     configured rules.
 -   Rescheduling preserves the original record and links the new
     appointment.
--   External confirmation does not create a payment record.
+-   External confirmation does not create a payment record; the only
+    permitted payment-related values are the two informational
+    indicators of §34 clause 7.
 
 ## 52. Queue and token
 
```

### A.2 — `mvp_scope.patch` → `docs/AMSDP_MVP_SCOPE_V1.1.md`

```diff
--- a/docs/AMSDP_MVP_SCOPE_V1.1.md
+++ b/docs/AMSDP_MVP_SCOPE_V1.1.md
@@ -180,6 +180,10 @@
 -   Create, search, view and update organization-owned patient records.
 -   Mandatory patient fields: name and mobile number.
 -   Support Bangla and English names and Unicode text.
+-   Provide Bangla name suggestions while staff type a patient name
+    (BanglaNameSense, Master Feature List V2.5 §25.8). Suggestions
+    are local, advisory and never authoritative: staff may ignore
+    them and enter any name.
 -   Permit multiple patient records to share a mobile number within the
     same organization, because family members may share a phone.
 -   Make staff select and verify the correct patient when search results
@@ -207,6 +211,8 @@
     patient records.
 -   Bangla characters are stored, retrieved and displayed without
     corruption.
+-   Bangla name suggestions assist entry without changing, overriding
+    or blocking a staff-entered name.
 -   The system does not silently merge records.
 
 ### 5.4 Doctor and room records
@@ -304,6 +310,13 @@
 -   Do not implement payment gateway processing, amounts, balances,
     wallet data, transaction IDs, QR payment, invoices or financial
     ledgers.
+-   AMSDP may retain only two non-binding informational indicators
+    against an appointment: is advance payment made? (Yes/No) and
+    is full payment made? (Yes/No). They are staff-entered flags,
+    not financial records; no payment amount, transaction
+    information, payment method, receipt, gateway/provider
+    information or payment ledger is permitted (owner decision
+    D-01).
 
 **Acceptance criteria**
 
@@ -313,6 +326,8 @@
 -   A rescheduled appointment is linked to its original appointment.
 -   An appointment cannot be transferred across organizations.
 -   No payment is processed or represented as collected by AMSDP.
+-   Any payment indicator recorded or displayed is a staff-entered
+    Yes/No flag, never an amount, balance, receipt or settlement.
 
 ### 5.7 Walk-in registration
 
@@ -548,6 +563,11 @@
 
 ### Payments and finance
 
+**Excluded**, with one narrow exception: the two non-binding
+informational indicators defined in §5.6 (advance payment made
+Yes/No; full payment made Yes/No). Anything financial beyond those
+two flags is out of scope for Phase 1.
+
 -   bKash, Nagad, Rocket, Bangla QR, card or other payment gateway
     integration.
 -   Advance, partial or full online payment collection.
@@ -558,6 +578,11 @@
 
 ### Clinical and medical records
 
+**Not in AMSDP Core.** These capabilities are excluded from Phase 1
+and from Core, but they are an approved optional module in Master
+Feature List V2.5 (§C, §29–§43) and remain subject to a separate
+activation, release and implementation decision.
+
 -   EMR/EHR.
 -   Prescriptions, diagnoses, clinical notes, symptoms or treatment
     plans.
@@ -568,8 +593,13 @@
 
 ### Intake, communication and integrations
 
+**Exception:** one-way operational WhatsApp/SMS notifications (N1
+confirmation and N2 reminder) are in Phase 1 scope per §16, item 2;
+interactive and two-way messaging remains excluded.
+
 -   Pre-visit questionnaires or asynchronous intake links.
--   Automated SMS, WhatsApp, email or voice reminders.
+-   Two-way or interactive SMS, WhatsApp, email or voice messaging, and
+    automated channel events beyond the approved N1/N2 notifications.
 -   External messaging provider integration.
 -   EHR, hospital information system or third-party PMS integration.
 -   National health identity, e-Health Card or national interoperability
@@ -586,16 +616,21 @@
 
 ### Queue extensions
 
--   Digital queue display/TV system.
--   Multi-screen display configuration.
--   Public-facing queue screens.
--   Advanced queue display countdowns.
+Single-screen DQDS and PQT are Phase 1 scope per §16, item 1. The
+following remain later-phase:
+
+-   Multi-screen/multi-display DQDS configuration.
+-   Advanced queue display countdowns beyond an estimate label.
 -   Token printer integration and printer-specific device management.
-
-**Note:** Basic token generation is in Phase 1. Printed queue tokens and
-digital queue displays are planned for Phase 2. A simple manual
-print/export workaround may be used during testing, but it is not a
-release requirement.
+-   Public-facing queue screens showing patient identity (the Phase 1
+    DQDS is token-only and PII-free).
+
+**Note:** Basic token generation is in Phase 1, and basic token printing
+may be implemented in Phase 1 when a printer is available (Business
+Rules §46). DQDS and PQT are Phase 1 capabilities per §16, item 1;
+advanced multi-display management and printer/device integration remain
+Phase 2. A manual print/export workaround remains acceptable where no
+printer is configured.
 
 ## 8. Later release direction
 
@@ -838,7 +873,9 @@
 -   External payments remain outside AMSDP.
 -   Clinical records and vitals are excluded.
 -   Patient login and self-service booking are excluded.
--   Automated messaging and pre-visit intake are deferred.
+-   Automated one-way WhatsApp/SMS notifications are in scope per §16,
+    item 2 (provider-dependent); pre-visit intake and all other
+    automated messaging remain deferred.
 -   The MVP does not claim national interoperability or integration with
     government health identity systems.
 
@@ -846,12 +883,16 @@
 
 Use these documents together:
 
-1.  `docs/product/AMSDP_Business_Rules_V1.1.md` --- authoritative
-    business behavior and approved decisions.
-2.  `docs/product/AMSDP_MVP_SCOPE_V1.0.md` --- Phase 1 release boundary
-    and acceptance criteria.
-3.  Product vision, feature list, scope and architecture documents ---
-    supporting context, to be reconciled against the two documents above
+1.  `docs/AMSDP_Business_Rules_V1.1.md` --- authoritative business
+    behavior and approved decisions.
+2.  `docs/AMSDP_MVP_SCOPE_V1.1.md` --- Phase 1 release boundary and
+    acceptance criteria (this document; V1.0 is the historical
+    baseline, see §17).
+3.  `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`
+    --- active master feature list; subordinate to items 1-2, see its
+    §26.11.
+4.  Product vision, architecture and positioning documents ---
+    supporting context, to be reconciled against the documents above
     before implementation.
 
 **MVP guiding principle:** Build a small product that genuinely works,
@@ -918,3 +959,17 @@
 V1.0 is retained as the historical baseline. V1.1 is the current
 approved MVP scope. Approval of the requirement does not itself certify
 that the workflow has been implemented or tested.
+
+---
+
+### Amendment record — 2026-11-14 (decisions D-01 and D-03)
+
+- **D-01:** §5.6 and §7 record the two non-binding informational payment indicators
+  (advance payment made — Yes/No; full payment made — Yes/No) as staff-entered flags, with
+  every other financial value still excluded.
+- **D-03:** §5.6 and §14 record Bangla name suggestions during staff entry (BanglaNameSense)
+  as advisory Phase 1 assistance that never overrides a staff-entered name.
+- Missed-Turn Recovery (§5.8, §16 item 6) is **unchanged** by this amendment: it remains
+  approved MVP/P0 scope under the owner approval of 2026-11-09 and Business Rules V1.1 §27A
+  (decision D-02 restates that approval; it does not demote it).
+- V1.0 remains the historical baseline. Nothing added by this amendment is implemented.
```

### A.3 — `v25.patch` → `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`

```diff
--- a/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
+++ b/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
@@ -1844,6 +1844,13 @@
 wallet or bank account, transaction ID, invoice, payment ledger or
 settlement information.
 
+**Owner decision D-01 (2026-11-13):** two non-binding informational
+indicators are permitted against an appointment — *is advance payment
+made?* (Yes/No) and *is full payment made?* (Yes/No). They are
+staff-entered flags, not financial records: no payment amount,
+transaction information, payment method, receipt, gateway/provider
+information or payment ledger is permitted.
+
 No payment dashboard or payment gateway is included.
 
 ## 16. Basic Operational Reports
@@ -1974,16 +1981,28 @@
 Keep the architecture modular so optional features can be added later
 without turning the core application into a full HMS.
 
-## 21. Explicitly Excluded from V2.1 Core
+## 21. Explicitly Excluded from AMSDP Core
+
+> These exclusions describe **AMSDP Core** — the appointment/queue
+> product. They were written in V2.1, when AMSDP Core was the whole
+> catalogue. Since V2.5 the catalogue also contains approved **optional
+> modules** (Clinical Management, AI assistance, Bangla name assistance
+> and further modules in §29–§43). An optional module is excluded from
+> Core and from the Phase 1 MVP, but it is part of the approved
+> catalogue; it becomes buildable only through its own activation and
+> release decision. See §26.11 for precedence.
 
 1.  Patient portal or patient app.
 2.  Patient self-service registration/login.
 3.  Public doctor schedule or doctor marketplace.
 4.  Online appointment booking by patients.
 5.  Payment gateway, bKash/Nagad integration or QR payment management.
-6.  Financial transaction records or payment reconciliation.
+6.  Financial transaction records or payment reconciliation (except the
+    two informational Yes/No indicators of §15.2, owner decision D-01).
 7.  Billing, invoicing, payroll or accounting.
-8.  Prescriptions, diagnoses, clinical notes or EMR.
+8.  Prescriptions, diagnoses, clinical notes or EMR **in AMSDP Core** —
+    see §29–§43: Clinical Management is an approved optional module, not
+    part of Core.
 9.  Vitals and clinical intake.
 10. Insurance and claims.
 11. Doctor HR, employment, attendance or credential management.
@@ -2038,6 +2057,8 @@
 -   User login and permissions.
 -   Lightweight doctor entries.
 -   Patient registration and search.
+-   Bangla name suggestions during staff entry (BanglaNameSense, §25.8)
+    — advisory only, never authoritative.
 -   Appointment creation.
 -   Time-slot, serial and hybrid models.
 -   Doctor schedule configuration.
@@ -2071,8 +2092,10 @@
 - External system integrations.
 - Additional operational reports.
 - Other appointment-related extensions approved by subscribers and AMSDP.
-- Missed-Turn Recovery, as approved under Business Rules V1.1 §27A
-  and product approval; it is not part of the MVP.
+- Missed-Turn Recovery: **not** a Phase 3 candidate. It is approved
+  MVP/P0 scope (owner approval 2026-11-09; Business Rules V1.1 §27A,
+  MVP Scope V1.1 §5.8) and is delivered inside Phase 1, not as an
+  optional extension.
 
 > **Note:** SMS and WhatsApp are **not** Phase 3-optional per PQV Decision
 > `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` — they are required,
@@ -2081,7 +2104,7 @@
 
 ## 24. Product Definition Summary
 
-AMSDP V2.1 is a facility-centric, multi-tenant SaaS platform for
+AMSDP is a facility-centric, multi-tenant SaaS platform for
 lightweight appointment management in Bangladesh.
 
 Its primary subscribers are hospitals, clinics and independent medical
@@ -2090,7 +2113,9 @@
 as lightweight facility-level appointment entries without creating AMSDP
 accounts.
 
-Patients do not need to use AMSDP. Payments remain outside the platform.
+Patients do not need to use AMSDP. Payments remain outside the platform;
+the only payment-related values AMSDP stores are the two informational
+Yes/No indicators of §15.2.
 Each subscribing organization operates an independent data environment,
 with no cross-organization patient, doctor or appointment data sharing.
 
@@ -2098,7 +2123,7 @@
 and easy for receptionists and assistants to use throughout a busy
 working day.
 
-## 25. PQV Decision Addendum (2026-11-08) — Incorporated into V2.1
+## 25. PQV Decision Addendum (2026-11-08) — Incorporated
 
 This addendum records features approved by product decision
 `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
@@ -2686,7 +2711,9 @@
   — authoritative approved PQV decision.
 - `docs/product/AMSDP_Product_Positioning_V1.0.md`
   — approved product positioning and impact-measurement framing.
-- `docs/product/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum.
+- `docs/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum. This
+  document is the Phase 1 release boundary and controls over this
+  feature list.
 - `docs/architecture/AMSDP_System_Architecture_V1.0.md` — architecture,
   security and integration boundaries.
 - `docs/AMSDP_Business_Rules_V1.1.md` — authoritative Business Rules;
@@ -2694,10 +2721,13 @@
 - `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`
   — separate unapproved proposal; not binding requirements.
 
-If this draft conflicts with an explicit approved decision or
-authoritative Business Rules document, the higher-precedence approved
-source controls. The Business Rules V1.0 document remains unchanged by
-this revision. Any amendment requires separate review and approval.
+If this document conflicts with an explicit approved decision, with
+Business Rules V1.1, or with MVP Scope V1.1, the higher-precedence
+approved source controls. Where this document and Business Rules V1.1
+differ on behaviour, Business Rules V1.1 controls; where they differ on
+the Phase 1 release boundary, MVP Scope V1.1 controls. This document
+does not amend Business Rules; any amendment requires separate review
+and approval.
 
 ------------------------------------------------------------------------
 
```

### A.4 — `v25_addendum.patch` → `same file (supplementary patch, apply after A.3)`

```diff
--- a/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
+++ b/docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md
@@ -7,7 +7,7 @@
 **Supersedes:** All prior AMSDP Master Feature List versions, including V1.x, V2.0, V2.1, V2.2, V2.3 and V2.4.  
 **Historical preservation:** The complete V2.3 baseline is retained in Appendix A for traceability. V2.4's previous clinical-module proposal is superseded by this V2.5 specification and is not an independent source of current requirements.  
 **Approval basis:** The Product Owner explicitly approved the revised Section C — Product Family and Module Catalogue — on 11 November 2026. This V2.5 document consolidates that approval with the subsequent product direction for Intelligent Clinical Documentation. Approval of this master list does not itself authorize every module for immediate implementation, paid provider procurement, production deployment, or any Git operation.  
-**Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions are historical records only. Where an older statement conflicts with V2.5, V2.5 governs. Individual prior product decisions remain in force unless expressly superseded by a later decision.
+**Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions are historical records only. V2.5 governs **the feature inventory and module catalogue**; it does **not** govern behaviour, access rules or the Phase 1 release boundary, which are controlled by `docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md` (see §26.11 and `.clinerules` §1). Individual prior product decisions remain in force unless expressly superseded by a later decision.
 
 ---
 
@@ -2003,7 +2003,11 @@
 3. Additional patient-record correction and merge workflows beyond
    warning/select-existing/no-auto-merge.
 4. Detailed policy for exceptional queue recovery and missed turns;
-   Missed-Turn Recovery is approved P0/MVP (§25.7).
+   Missed-Turn Recovery is approved P0/MVP scope (owner approval
+   2026-11-09; see §25.9, MVP Scope V1.1 §5.8 and Business Rules V1.1
+   §27A). The detailed state machine, grace/expiry windows, late-arrival
+   handling, emergency/priority interaction and audit events are settled
+   in §27A.
 5. Provider selection, provider account creation, sender IDs, template
    approvals, credentials, paid plans and message-cost commitments.
 6. Production/cloud deployment and hosting choices beyond the separately
@@ -2058,7 +2062,8 @@
 -   Additional reports.
 -   Multi-branch support, if approved.
 -   Improved appointment change workflows.
--   Printable appointment/serial slips, if approved.
+-   Advanced printing options. Basic token/serial printing is already
+    Phase 1 (Business Rules §35 clause 4 and §32; MVP Scope §5.9).
 
 ### Phase 3 --- Optional extensions
 
```

### A.5 — `pqv.patch` → `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`

```diff
--- a/docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md
+++ b/docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md
@@ -13,29 +13,32 @@
 |---|---|---|
 | 1 | Public Product Positioning — "AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences." (primary for public website, hackathon materials, product communications) | **APPROVED** |
 | 2 | Two-Stage Patient Notifications (N1 confirmation + N2 pre-visit reminder, default 10 min, 5/10 options; WhatsApp & SMS org-configurable; queue-change-aware scheduling; cooldown/dedup; reminder cancellation; no delivery claim unless provider confirms; booking functional without messaging) | **APPROVED as P0 product scope** |
-| 3 | Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** — remains proposed/later-phase; no implementation; future proposal must address BR §§20–21, grace periods, late arrivals, queue-state semantics, emergency/priority handling and audit events |
-| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **Preparation of a proposed revision authorized** — authoritative Business Rules V1.0 remains unmodified until the proposed revision is separately presented and approved |
+| 3 | Missed-Turn Recovery & Queue Repositioning | **APPROVED — MVP/P0 (owner approval 2026-11-09; restated by owner decision D-02, 2026-11-13)** — governed by Business Rules V1.1 §27A and specified in MVP Scope V1.1 §5.8; not implemented |
+| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **DELIVERED in Business Rules V1.1** (§2, §33, §35, §36, §46, §47) — the earlier draft proposal `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md` is superseded and is not a source of requirements |
 
 ## 0. Authority and relationship to other documents
 
 1. This is the authoritative product decision for patient queue visibility (public display and
    personal tracking) and patient communication channels (WhatsApp and SMS).
 2. It supersedes or adjusts earlier direction where they conflict with it:
-   - Business Rules V1.0 §35 (staff-only communication; SMS later-phase) and §36 (SMS APPROVED
-     PHASE 2) — WhatsApp and SMS are here promoted from "later/optional" to **required,
-     organization-configurable communication channels**, while actual delivery of each channel
-     remains dependent on provider availability (§D.11).
+   - Business Rules §35 (staff-only communication; SMS later-phase) and §36 (SMS
+     APPROVED, PHASE 2) — **reconciled in Business Rules V1.1**: WhatsApp and SMS are
+     approved P0, organization-configurable channels (§36), while actual delivery of
+     each channel remains dependent on provider availability (§D.11).
    - Master Feature List V2.0 Draft §14.2 (communication features PENDING) and §23 Phase 3
      (SMS optional extension) — updated per WP2.
-   - MVP Scope V1.0 §14 ("automated messaging deferred") — adjusted via the scope addendum
-     recorded in the MVP Scope document.
+   - MVP Scope §14 ("automated messaging deferred") — **reconciled in MVP Scope
+     V1.1**: §14 and §16, item 2 record one-way operational notifications as Phase 1
+     scope, with pre-visit intake still deferred.
 3. **Preserved unchanged:** the six canonical system roles and the existing RBAC permission
    model; the tenant key (`organization_id`); strict tenant and branch isolation; all previously
    approved exclusions (no patient accounts, patient portal, self-service booking, or mandatory
    mobile application).
-4. Business Rules V1.0 remains the authoritative behaviour document; where a future Business
-   Rules revision reconciles §35/§36 to this decision, this decision takes precedence in the
-   interim. Document conflicts are tracked in §9 and in WP2/WP3 outputs.
+4. Business Rules V1.1 is now the authoritative behaviour document and has already
+   reconciled §35/§36 to this decision (§36, §46, §47). This decision remains the
+   authoritative source for the product scope it records; where the two differ, the
+   divergence is reported rather than resolved silently, and the governing document
+   for behaviour is Business Rules V1.1.
 
 ## A. Four primary personas
 
@@ -148,7 +151,7 @@
 |---|---|---|---|
 | Business Rules §35 | SMS is later-phase; communication staff-only | WhatsApp + SMS promoted to required channels; org-admin configurable | §D overrides; §35/§36 reconciled in next BR update |
 | Business Rules §36 | SMS APPROVED, PHASE 2 | WhatsApp added; both promoted to required | Same |
-| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Scope addendum in MVP Scope V1.0 |
+| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Reconciled in MVP Scope V1.1 §14 and §16, item 2 |
 | Master Feature List §14.2 | Communication features PENDING; SMS optional Phase 3 | Updated per WP2 | Feature list updated |
 | System Architecture §5.11 | Notification Service — later capability | Elevated to required; provider delivery remains provider-dependent | Architecture §5.11 updated |
 | System Architecture §13 | No provider-secret storage defined | Requires encrypted org-scoped secret store | Architecture §13 updated |
@@ -162,7 +165,7 @@
 | WhatsApp delivery | Approved channel requirement — **provider-dependent** (account/API, template approval, costs may apply) |
 | SMS delivery | Approved channel requirement — **provider-dependent** (account/sender ID, costs may apply) |
 | Two-Stage Patient Notifications (confirmation + pre-visit reminder) | **APPROVED P0 product scope** (see §J) — **provider-dependent** for actual delivery; not implemented |
-| Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** (see §K) — proposed/later-phase; requires future product decision + Business Rules amendments (§§20–21, grace, late arrival, queue semantics, emergency/priority, audit); not implemented |
+| Missed-Turn Recovery & Queue Repositioning | **APPROVED — MVP/P0** (owner approval 2026-11-09; restated by owner decision D-02, 2026-11-13; see §K) — governed by Business Rules V1.1 §27A, specified in MVP Scope V1.1 §5.8; not implemented |
 | Advanced multi-display management, richer notification matrix, additional channels | Later-phase enhancements |
 
 ## I. No-implementation statement
@@ -245,9 +248,13 @@
 
 ## K. Missed-Turn Recovery & Queue Repositioning (proposed)
 
-**Product-owner status (2026-11-08): NOT APPROVED FOR MVP.** This capability remains a
-**proposal for later-phase consideration**. It is **not** approved scope and **not**
-implemented. Existing queue and no-show rules are unchanged.
+**Product-owner status: APPROVED — MVP/P0 scope.** The NOT-APPROVED classification
+recorded here on 2026-11-08 was superseded by the product-owner approval of
+9 November 2026 and is restated by owner decision D-02 (2026-11-13). The governing
+detailed rule is Business Rules V1.1 §27A; the MVP workflow is MVP Scope V1.1 §5.8.
+The capability is **not implemented**: the sections below describe the approved
+requirement, not delivered behaviour. Existing queue and no-show rules are unchanged
+until it is built.
 
 ### K.1 Expected workflow
 
```

### A.6 — `register.patch` → `docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`

```diff
--- a/docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md
+++ b/docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md
@@ -1,4 +1,4 @@
-# AMSDP — Owner Decisions Q-1 … Q-6
+# AMSDP — Owner Decisions Q-1 … Q-6 and D-01 … D-03
 
 > **Document ID:** `AMSDP_Owner_Decisions_Q1_Q6`
 > **Version:** V1.0 · **Date:** 2026-11-13
@@ -7,6 +7,8 @@
 > **Status of this document:** decision record only — **what was decided and why**.
 > Implementation status, evidence and open items are deliberately kept out of it and
 > live in `docs/implementation/AMSDP_Owner_Decisions_Implementation_Report_V1.0.md`.
+> **Part II** (D-01 … D-03, 2026-11-13) is appended at the end of this document. The
+> document ID stays `AMSDP_Owner_Decisions_Q1_Q6` as the stable identifier of the record.
 
 ---
 
@@ -185,17 +187,134 @@
 
 ## Cross-cutting conditions
 
-These apply to all six decisions and are not separate approvals:
+These apply to every decision in this document — Q-1 … Q-6 and D-01 … D-03 — and are
+not separate approvals:
 
 - `.clinerules` §3 non-negotiables are untouched: no secret is logged or exposed,
   access stays enforced server-side, cross-tenant access fails closed with 404,
   the tenant key stays `organization_id`, and the audit trail stays append-only.
 - Any schema change would ship as a forward-only idempotent Alembic migration —
-  none of these six decisions requires one.
+  none of Q-1 … Q-6 requires one. D-01 (two payment indicators) **does** require one:
+  two nullable informational columns on the appointment, with no amount, transaction,
+  receipt or ledger structure (see D-01 in Part II).
 - Every claim in the accompanying implementation report must meet the §7 evidence
   standard (IMPLEMENTED / TESTED / VERIFIED / ACCEPTED). A green suite is not
   VERIFIED.
 - No commit made under these decisions may include unrelated work, and nothing is
   pushed without a separate owner instruction.
 
-
+---
+
+# Part II — Decision records D-01 … D-03 (2026-11-13)
+
+Same rules as Part I: this is a record of **what was decided and why**. Implementation
+status, evidence and open items are kept out of it. Recorded because the three decisions
+change authoritative product documents, so the reason must be traceable.
+
+## D-01 — Informational payment indicators on an appointment
+
+**Question.** AMSDP must not become a billing or payment product (Business Rules §2, §34;
+MVP Scope §12). Clinic staff nevertheless need to see, while running the queue, whether a
+patient paid the consultation fee in advance and whether it is settled in full. Is any
+payment-related value permitted?
+
+**Decision.** Two — and only two — non-binding informational indicators may be stored
+against an appointment:
+
+- *Is advance payment made?* — Yes / No
+- *Is full payment made?* — Yes / No
+
+They are staff-entered flags, not payment records. No amount, currency, transaction ID,
+reference number, receipt, payment method, gateway/provider identifier, QR data, wallet or
+bank detail, invoice or ledger entry may be stored, derived, aggregated or reported
+alongside them.
+
+**Boundary of the approval.**
+- In scope: the two Yes/No flags on an appointment, their capture in the appointment UI,
+  and their display in appointment/queue context.
+- Out of scope: payment processing, amounts, balances, reconciliation, receipts, invoices,
+  refunds, settlement reports, gateway or provider integration, and any financial report.
+  None of these is implied by the flags.
+- The flags must not gate, replace or silently alter appointment confirmation, queue
+  admission, or the no-show rules. A patient marked "not paid" is handled exactly as today.
+- Provenance: the flag records what staff asserted, not a verification by AMSDP. No UI text
+  or export may state or imply that AMSDP verified a payment.
+- Schema: ships as a forward-only, idempotent Alembic migration adding two nullable
+  columns. Existing rows stay null, which means *unknown* — not "No".
+- Audit: setting or clearing a flag is an audited state change of the appointment, like any
+  other staff edit, under the append-only audit rules (§3).
+- Lands in: Business Rules V1.1 §2.1 item 1 and §34 clause 7; MVP Scope V1.1 §5.6 and §12;
+  Master Feature List V2.5 §15.2, §21 item 6 and §24.
+
+**Not decided here:** patient visibility. In Phase 1 the flags are staff-facing only.
+
+## D-02 — Missed-Turn Recovery: approved MVP scope, not later-phase
+
+**Question.** Two records disagree about the same approval. The PQV decision (2026-11-08)
+says Missed-Turn Recovery is **not approved for MVP**; Master Feature List V2.5 §23 lists it
+under Phase 3 as "not part of the MVP" while §22 item 4 and §25.9 say it is **approved
+P0/MVP**. Which is true?
+
+**Decision.** Missed-Turn Recovery is **approved MVP/P0 scope**, per the product-owner
+approval of 9 November 2026 recorded in MVP Scope V1.1 §17 and specified in §5.8, governed
+by Business Rules V1.1 §27A. The 8 November "NOT APPROVED" row predates that approval and is
+superseded on this point; the V2.5 Phase 3 listing and its §22/§25.9 wording are corrected
+in place rather than deleted.
+
+**Boundary of the approval.**
+- Scope, not implementation: no MTR code, schema, endpoint, screen or notification exists
+  today. Approval of a requirement never certifies that it is built or tested.
+- Governing rule: Business Rules V1.1 §27A. Its state machine, grace and expiry windows,
+  late-arrival handling, emergency/priority interaction, notification behaviour and audit
+  events govern the build.
+- Behaviour fixed by §27A: staff-confirmed deferral to the end of the same applicable active
+  queue by default; authorized staff or doctors may override to any valid position in that
+  same queue, with a reason and an audit entry. The original appointment, token and full
+  queue history are preserved; no appointment is cancelled or rewritten by a reposition;
+  every reposition is an audited staff action, never silent.
+- No automatic no-show, no messaging-based inference, no automated clinical triage.
+- Access control stays server-side and token-derived; a cross-branch attempt fails closed
+  with 404.
+- Honesty: while unimplemented, no document, demo or report may claim the workflow exists or
+  that a pilot used it.
+- Lands in: PQV approval table row 3, §H and §K; Master Feature List V2.5 §22 item 4,
+  §23 Phase 3 and §25.9.
+
+
+## D-03 — BanglaNameSense is Phase 1 scope, advisory only
+
+**Question.** Master Feature List V2.5 §25.8 lists BanglaNameSense (Bangla patient-name
+assistance) as an approved capability, but MVP Scope V1.1 §5.6 requires Bangla/Unicode name
+entry without defining any assistance mechanism, and V2.5 §23 Phase 1 does not list it. Is
+it Phase 1 or later?
+
+**Decision.** Phase 1, as an **advisory entry aid** for staff typing a patient name. It is
+not a name authority, not a transliteration service and not an identity system.
+
+**Boundary of the approval.**
+- In scope: suggesting Bangla name forms to staff while a patient record is created or
+  edited, and after the suggestion is ignored, everything works exactly as MVP Scope §5.6
+  already requires.
+- Never authoritative: the stored name is exactly what staff entered. A suggestion must
+  never rewrite, correct, transliterate, dedupe or block a staff-entered name, and must
+  never be applied without a staff action.
+- Local and dependency-free: the suggestion mechanism must not require an external service,
+  network call, paid provider or AI model to be available. If it is unavailable, name entry
+  is unaffected.
+- Not a matching engine: no fuzzy patient matching, no merge/dedupe by suggested name and
+  no lookup outside the staff member's own branch — tenant and branch isolation are
+  untouched.
+- Unicode guarantees unchanged: Bangla text is stored, retrieved and displayed without
+  corruption, and the suggestion layer must not normalise or fold stored names.
+- Lands in: MVP Scope V1.1 §5.6 (capability and acceptance), §14 (later-phase boundary),
+  and Master Feature List V2.5 §23 Phase 1.
+
+## Register note — reconstructed wording
+
+D-01 … D-03 are recorded from the approved effects of the 2026-11-13 decisions, because no
+upstream decision artefact existed in the tree when this register was extended. The
+numbering, wording and boundaries above should be confirmed by the Product Owner; the
+discrepancy is tracked as open item **U-1** in
+`docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md`.
+
+
```

### A.7 — `clinerules.patch` → `.clinerules`

```diff
--- a/.clinerules
+++ b/.clinerules
@@ -8,7 +8,7 @@
 ## 1. Precedence — resolve conflicts in this order
 
 1. **System and safety constraints** — verified runtime state, hardware runtime context (4GB VRAM / 16GB RAM), host limits. Within this level, AMSDP's verified ordering applies: verified runtime state → LLM availability routing → hardware runtime context → generic SaaS convention.
-2. **Explicit project-owner instructions and approved AMSDP business rules** — `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`, frozen system design requirements.
+2. **Explicit project-owner instructions and approved AMSDP business rules** — `docs/AMSDP_Business_Rules_V1.1.md` (authoritative for behaviour, access and workflow), `docs/AMSDP_MVP_SCOPE_V1.1.md` (authoritative for the Phase 1 release boundary and acceptance), `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` (authoritative for the feature inventory and module catalogue only — it never overrides the two documents above on behaviour or release scope), frozen system design requirements. V1.0 copies of Business Rules and MVP Scope are historical baselines.
 3. **AMSDP project governance** — this file and `docs/governance/AMSDP_Engineering_Governance_Assessment.md`.
 4. **Applicable engineering rules** — the agent-rules files in `ai_factory/docs/agent-rules/`, applied **only as adapted** in the governance assessment §3. Do not blindly apply CarbonTally-specific requirements.
 5. **Selected specialized skills** — see §5 Skills Registry (none installed today).
@@ -105,8 +105,10 @@
 
 ## 10. Project Governance Document Index
 
-- Business Rules (authoritative): `docs/product/AMSDP_Business_Rules_V1.0.md`
-- MVP scope: `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
+- Business Rules (authoritative, behaviour/access/workflow): `docs/AMSDP_Business_Rules_V1.1.md`
+- MVP scope (authoritative, Phase 1 release boundary): `docs/AMSDP_MVP_SCOPE_V1.1.md`
+- Master feature list (authoritative, feature inventory only): `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`
+- Historical baselines (read-only, never governing): `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
 - Governance assessment (authoritative routing detail): `docs/governance/AMSDP_Engineering_Governance_Assessment.md`
 - Skill routing architecture: `docs/governance/AMSDP_Skill_Routing_Architecture.md`
 - **Documentation navigation index (read first, every task):** `docs/governance/AMSDP_Docs_Index_V1.0.md`
@@ -121,7 +123,7 @@
 - **Never overwrite, never delete.** Check the destination filename before writing; if it already exists, stop and report the collision instead of overwriting. Historical versions are preserved — never delete, consolidate away or "clean up" an earlier version of a document.
 - **Filenames** follow `AMSDP_<Topic>_<Version>.md` (or the exact existing name when a document is migrated). A rename is permitted only when it is recorded in the migration manifest.
 - **Migrations are recorded acts.** Moving or renaming an existing document requires: destination collision check, byte-for-byte content preservation (SHA-256 before/after), and an entry in a manifest under `docs/governance/` giving original path, destination path, date and reason. Content must not be rewritten during a move. Files whose ownership or purpose is uncertain are not migrated — they are reported and left in place.
-- **Owner-controlled documents are read-only.** They may be read and cited, but never modified, moved, renamed or overwritten without explicit Product Owner approval for that specific act: `docs/AMSDP_Master_Feature_List_V2.0_Draft.md`, `docs/AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md`, `docs/AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md`, `docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md`; `docs/AMSDP_Business_Rules_V1.1.md` and `docs/product/AMSDP_Business_Rules_V1.0.md`; `docs/AMSDP_MVP_SCOPE_V1.1.md` and `docs/product/AMSDP_MVP_SCOPE_V1.0.md`; `docs/product/` product decisions and positioning; `docs/architecture/AMSDP_System_Architecture_V1.0.md`; `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md`; the hackathon concept note; `docs/demo/AMSDP_Limitations_Report_V1.0.md` and `docs/demo/AMSDP_Demo_Credentials_V1.0.md`. The same principle extends to any other document the Product Owner subsequently declares authoritative.
+- **Owner-controlled documents are read-only.** They may be read and cited, but never modified, moved, renamed or overwritten without explicit Product Owner approval for that specific act: `docs/AMSDP_Master_Feature_List_V2.0_Draft.md`, `docs/AMSDP_Master_Feature_List_V2.1_Consolidated_Draft.md`, `docs/AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md`, `docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md`; `docs/AMSDP_Business_Rules_V1.1.md` and `docs/product/AMSDP_Business_Rules_V1.0.md`; `docs/AMSDP_MVP_SCOPE_V1.1.md` and `docs/product/AMSDP_MVP_SCOPE_V1.0.md`; `docs/product/` product decisions and positioning; `docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md` (the active master feature list — any future version becomes owner-controlled on the same terms); `docs/architecture/AMSDP_System_Architecture_V1.0.md`; `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md`; the hackathon concept note; `docs/demo/AMSDP_Limitations_Report_V1.0.md` and `docs/demo/AMSDP_Demo_Credentials_V1.0.md`. The same principle extends to any other document the Product Owner subsequently declares authoritative.
 - This section is additional to §1–§10. It relaxes none of them: §1 precedence, §3 non-negotiables, §6 compliance reporting, §7 evidence standard, §9 execution boundaries and the agent-rules library all continue to apply unchanged. Every report must state where it was written and, if it involved a migration, cite the manifest entry.
 
 ## 12. Documentation Reading & Retrieval Policy (consult `docs/` before acting)
```

### A.8 — `br_proposal_draft.patch` → `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`

```diff
--- a/docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md
+++ b/docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md
@@ -21,10 +21,16 @@
    pre-visit reminder) as approved P0 product scope.
 4. Add the required **reminder cancellation and deduplication** behaviour.
 
+> **SUPERSEDED — 2026-11-13.** This draft was superseded by Business Rules V1.1, which
+> incorporates §33 (DQDS/PQT carve-outs), §36 (one-way operational WhatsApp/SMS) and §47
+(two-stage notifications). It is retained as a historical record and is **not** a source
+of requirements. See `docs/audit/AMSDP_V25_Reconciliation_and_Decision_Register_Proposal_V1.0_DRAFT.md`
+> (C-02, C-03).
+
 **Out of scope for this revision:** Missed-Turn Recovery & Queue Repositioning is **not
-approved for MVP** and is intentionally absent here; it will require a separate future
-proposal (addressing BR §§20–21, grace periods, late arrivals, queue-state semantics,
-emergency/priority handling and audit events).
+approved for MVP** by the PQV decision and is intentionally absent here. **Updated
+2026-11-13 (owner decision D-02):** the capability is approved for later-phase
+implementation (Phase 3) under Business Rules V1.1 §27A, still outside Phase 1 MVP scope.
 
 ## 2. Proposed amendment A — DQDS/PQT carve-outs (BR §2)
 
```

## 6. Near-misses — checked, not changed

Recorded because "no conflict found" is a finding, and a reviewer should see what was examined
and deliberately left alone.

| Item examined | Result |
|---|---|
| Six canonical roles (PQV item 3, Business Rules RBAC matrix, MVP Scope §4) | Consistent. No change proposed. |
| Tenant key `organization_id`, org/branch isolation, 404-not-403 rule | Consistent across Business Rules, MVP Scope §9 and `.clinerules` §3. No proposal weakens it. |
| Append-only audit trail (Business Rules Part X, MVP Scope §5.10) | Consistent. Every new state change proposed here (payment flag, MTR reposition, DQDS display) is specified as an audited event. |
| Two-stage notifications: confirmation + pre-visit reminder, default 10 minutes, 5/10 practical options, cancellation/dedup, no delivery claim | Stated identically in PQV §D.6, MVP Scope §16 item 6 and Business Rules §47 in the passages read. No change proposed. |
| "Bangla and Unicode names without corruption" versus BanglaNameSense | Not a contradiction: the MVP requirement is silent on assistance, not hostile to it. Handled as C-09 — a gap, not a conflict. |
| V2.5 §22 item 4 cross-reference to "§25.7" | Cross-reference drift: §25.7 is the notification record, the MTR record is §25.9. Corrected inside the C-04 edit rather than raised separately. |
| MVP Scope §12 (hackathon demonstration acceptance) versus Phase 1 scope | Compatible: §12 demonstrates Phase 1 workflows. No change. |
| MVP Scope §16 item 6's MTR paragraph versus Business Rules §27A | Consistent in substance (same default, same override, same audit requirement). No change: MVP Scope is the release-boundary authority and already states the approved position. |
| `ai_factory/docs/` document policy (`.clinerules` §11) | No violation: this proposal is written under `docs/audit/`; nothing is added to `ai_factory/docs/`. |

### 6.1 Hygiene finding — duplicate-copy risk under `docs/product/`

`docs/product/` holds the V1.0 baselines (`AMSDP_Business_Rules_V1.0.md`,
`AMSDP_MVP_SCOPE_V1.0.md`, the PQV decision, the superseded draft proposal), while the **live**
V1.1 documents sit at the root of `docs/`. Two documents (`MVP Scope V1.1` §15 and
`Master Feature List V2.5` §26.11) cite `docs/product/AMSDP_MVP_SCOPE_V1.1.md` — a path that
does not exist.

The risk is concrete: whoever next "fixes" such a citation is likely to copy the file into
`docs/product/` rather than correct the path, producing two divergent copies of an
authoritative document while the governance index points at one of them. C-05 corrects the
paths; this document recommends that no V1.1 copy is ever created under `docs/product/` and
that the V1.0 files stay where they are, labelled historical.

## 7. Unresolved — owner input required

**U-1 — reconstruction of D-01 … D-03. Blocks patch 6 only.**
No upstream artefact for the 2026-11-13 decisions exists in the tree: no register entry, no
note, nothing recoverable from the documents. The three records in `register.patch` were
reconstructed from their approved effects. The numbering, titles and boundaries need owner
confirmation before that patch is applied; the register text carries that disclosure itself.

**U-2 — direction of the Missed-Turn Recovery reconciliation. Blocks C-04.**
This proposal reconciles MTR **up** to approved MVP/P0, because the 2026-11-09 approval is
later than the 2026-11-08 "NOT APPROVED" row and is recorded in the release-boundary document.
If the owner actually decided on 2026-11-13 to demote MTR to a later phase, C-04 must be
inverted: the PQV rows would stay negative and **MVP Scope V1.1 §5.8, §16 item 6 and §17 would
have to be amended instead**. The patch set does not do that, and no MTR change should be
applied until this is answered.

**U-3 — D-01 migration and reporting surface.** D-01 needs two nullable columns. Not decided
here: the migration revision identifier, whether "unknown" (null) is displayed differently
from "No" in the existing appointment UI, and whether the flags may appear in any export.
"Never an amount, balance, receipt or settlement" only stays true if exports cannot invent one.

**U-4 — who may set the payment flags.** The decision says staff-entered, but not which role
(Facility Staff / Appointment Desk, Doctor, Org Admin). MVP Scope §4.3–§4.4 was not amended.
Needs a role decision before the migration is written.

**U-5 — BanglaNameSense implementation.** The scope decision is advisory-only. How suggestions
are produced (static mapping, local dictionary, model) is a technical decision not taken here;
`.clinerules` §8 local-model routing applies when it is taken.

**U-6 — editing `.clinerules` at all.** Patch 7 adds the V2.5 feature list to the
owner-controlled list and corrects the §1/§10 authoritative paths. Because `.clinerules` is
the governance file itself, this should be applied only on explicit owner instruction, not
folded in silently with the product-document reconciliation.

**U-7 — PQV §K's "§§20–21" reference.** PQV directs a future proposal at "BR §§20–21"; the
current Business Rules V1.1 numbering may no longer place those rules there. Left unedited
rather than guessed at.

## 8. Sequence after approval

Nothing in this sequence is authorised by this document. It is the order that keeps every step
verifiable.

1. Owner answers U-1 (decision wording), U-2 (MTR direction) and U-6 (permission to edit
   `.clinerules`).
2. Apply patches 1–8 in Appendix A order, or `all.patch` as one operation. Re-read each changed
   section afterwards rather than trusting `git apply` alone.
3. Re-run the consistency check: no surviving reference to
   `docs/product/AMSDP_Business_Rules_V1.1.md`, `docs/product/AMSDP_MVP_SCOPE_V1.1.md`, or to
   "Business Rules V1.0" as the authoritative behaviour document.
4. Update the docs index for whatever this DRAFT becomes, mark this DRAFT superseded, and let
   the register carry the decision records (patch 6).
5. Only then, as separate authorised work: D-01 migration + capture UI + audit event (U-3,
   U-4); BanglaNameSense (U-5); Missed-Turn Recovery against §27A. Each is a code change with
   its own tests, and none of them is made true by this document.

## 9. Governance and Skill Compliance

Per `.clinerules` §6.

**Applicable governance.** §2 routing placed this task in the *Documentation* row; no code
domain was engaged. Documents read and applied: `docs/governance/AMSDP_Docs_Index_V1.0.md`
(read first, per §12); `docs/AMSDP_Business_Rules_V1.1.md` and `docs/AMSDP_MVP_SCOPE_V1.1.md`
(the two authoritative documents — read from disk, quoted from disk);
`docs/AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`;
`docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`;
`docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`;
`docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`; `.clinerules`.

**Skills.** None. No `.clinerules/skills/`, no `.claude/skills/`, no repository `skills/`
directory and no Cline skill configuration exists in this workspace. The governance documents
were used instead, as §5 requires; no skill usage is claimed.

**Evidence (§7).** This is a document; the only claims made are about text. IMPLEMENTED:
nothing. TESTED: no tests — no code changed, so no test could be meaningful. VERIFIED: the
patch arithmetic — every replacement matched exactly one occurrence in its file, and
`git apply --check` returned rc=0 for all eight patches and for the combined patch, against
the tree as committed. That verifies the diffs apply; it does **not** verify any product
capability, and none is claimed.

**Non-negotiables.** §3 audit, tenant, 404, secret-handling rules are unchanged by every
proposed edit. The only new state changes proposed (payment flag, reposition) are specified as
audited. No secret or credential appears in this document or in any patch.

**Deviations and limits.**
- No test run and no runtime verification: documentation task; §9 forbids running more than the
  task requires.
- The three decision records are reconstructed (U-1); the register text discloses this.
- Patch 7 edits `.clinerules` itself — disclosed in U-6, not presented as an ordinary fix.
- The MTR direction is an inference from document dates, not from a decision artefact — U-2.

**Output location.** This document is written to `docs/audit/` per `.clinerules` §11 and
registered in `docs/governance/AMSDP_Docs_Index_V1.0.md`. That registration is the **only**
edit this task makes to an existing file: an index row plus a revision line, no content
change, no move, no rename — so no migration-manifest entry is required.
