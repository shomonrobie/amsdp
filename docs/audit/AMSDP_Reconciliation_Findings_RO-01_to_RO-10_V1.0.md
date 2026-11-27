# AMSDP — Reconciliation Findings RO-01…RO-10 — Product Owner Authorisation OA-2 Record — V1.0

| | |
|---|---|
| **Document** | `docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` |
| **Purpose** | Preserve, in the repository, the reconciliation findings raised as **RO-01…RO-10** — what was found, the primary evidence for each, what the Product Owner authorised, and what was actually changed |
| **Authority** | Product Owner response to the consolidated decision pack, 2026-11-27: **PO-DEC-01** (Option A) and **OA-2** — *"T-7: preserve the RO-01 through RO-10 reconciliation findings in the appropriate audit document and register the document."* |
| **Written by** | The agent, documentation only, under OA-2 |
| **Status of the items** | **Findings recorded.** Corrections are limited to the ones OA-2 names. Nothing here is VERIFIED or ACCEPTED (`.clinerules` §7) |
| **What this is not** | Not an implementation report, not a re-audit, not an evidence artefact for any test run, and not a decision record — decisions live in `docs/decisions/` |

---

## 1. How this record was produced, and its one honest gap

The ten identifiers were issued in a **read-only reconciliation response on 2026-11-27** that was delivered in
the working conversation and **never written to the repository** — the owner's 2026-11-27 answer records exactly
that: *"the stored RO-01…RO-10 reconciliation report does not exist in the repo (T-7 exists to create it)."*
This document therefore reconstructs each finding from **two primary sources only**:

1. the Product Owner's own restatement of the items in the 2026-11-27 answer, which names **RO-01, RO-03/F-08,
   RO-04, RO-05, RO-07 and RO-08** explicitly, and answers **RO-02** as **PO-DEC-01**; and
2. the file and line evidence in this tree, re-read in this session — every citation below was opened, not
   remembered (`.clinerules` §12).

**The gap, stated rather than papered over.** **RO-06, RO-09 and RO-10** were **not** restated by the owner and
no primary source in this tree identifies them. They are recorded here as **unrecoverable** — the identifier
survives, the finding does not. They are **not** reconstructed by guesswork, and no correction is claimed
against them. If the owner wants them preserved, the original reconciliation text is the only source.

---

## 2. Summary

| ID | Finding, in one line | Verdict | OA-2 authority | Status after this record |
|---|---|---|---|---|
| **RO-01** | The MP-24 "prior test coverage" narrative is **wrong**: the queue-history route *did* have backend tests before 27 November, and the 26 November audit was misquoted | **Confirmed — report premise false** | "correct the MP-24 prior-test-coverage narrative" | **Corrected** (§3.1; report §14; register §16.2 cell) |
| **RO-02** | MD-19 capability field (audit F-02) was a **live** Product Owner decision, and the code arrived before the answer | **Confirmed → answered** | PO-DEC-01 **Option A** | **Closed as a decision**; sequencing preserved (§3.2) |
| **RO-03** | Audit **F-08**: the second scratch database's creation/migration transcript does not exist | **Confirmed — provenance unproven** | "F-08 / RO-03: explicitly record the missing … transcript and do not claim unsupported provenance" | **Corrected** in register §15.1 (§3.3) |
| **RO-04** | MP-33 and MP-34 labels do not match their actual authority and evidence | **Confirmed — stale labels** | "reconcile MP-33 and MP-34 statuses" | **Reconciled** (§3.4; register §13.3 annotation, §17.2) |
| **RO-05** | The "47 items" backlog tally is not a closed set: MP-47 is missing from it | **Confirmed — count wrong** | "correct narrative counts" | **Corrected** → 48 rows (§3.5; register §17.2) |
| **RO-06** | — | **Unrecoverable** | none claimed | **Not restated; not invented** (§3.6) |
| **RO-07** | The Docs Index running count convention was broken by Revision 51, which published no *Counts* line | **Confirmed — convention broken once** | "correct … Docs Index count conventions" | **Convention restated; break recorded** (§3.7; Index Revision 57) |
| **RO-08** | MD-19 does not distinguish **caller** branch from **target** branch on the non-disclosing 404 path | **Confirmed — interpretation, not defect** | "record the MD-19 caller/target branch interpretation" (T-5) + OPC-3 | **Recorded** (§3.8; register §17.3) |
| **RO-09** | — | **Unrecoverable** | none claimed | **Not restated; not invented** (§3.9) |
| **RO-10** | — | **Unrecoverable** | none claimed | **Not restated; not invented** (§3.10) |

---

## 3. The findings

### 3.1 RO-01 — MP-24's prior test coverage (report premise false)

**What was claimed.** `docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md` §6
states that "the audit's MP-24 row (\"IMPLEMENTED, TESTED (frontend)\") proved weaker than it reads", that
"no backend test called `/api/v1/queue/history` at all", and that "the route's own scope rules — the part that
enforces tenancy — were unexercised". Bullet 4 of §0 recasts this as "**MP-24's backend half tested for the
first time**". Register §16.2 repeats it: "The route had **no** backend test".

**What the tree shows.**

- `backend/queuing/tests/test_queue.py` contains **eight** pre-existing tests driving exactly this route, with
  `client.get(...)` call sites at `:1149`, `:1160`, `:1175`, `:1198`, `:1214`, `:1233` and `:1242`, spanning
  `:1141`–`:1250`: `test_c1_receptionist_own_branch_history`,
  `test_c1_receptionist_cannot_another_branch_history` (**404**),
  `test_c1_receptionist_omits_branch_id_limited_to_own` (asserts every returned row's `branch_id`),
  `test_c1_org_admin_authorized_branch_history`, `test_c1_cross_tenant_branch_id` (**404**),
  `test_c1_org_admin_other_org_branch_denied` (**404**), `test_c1_org_admin_nonexistent_branch_denied`
  (**404**) and `test_c3_doctor_no_assignment_denied`.
- **The tenancy rules were the subject of those tests**, including four non-disclosing **404** assertions. The
  claim that they were "unexercised" is contradicted by the file.
- The **26 November** master-roadmap audit
  (`docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md:246`) recorded MP-24 as
  **PARTIALLY IMPLEMENTED** and cited, correctly, *"Queue-history API tests in
  `backend/queuing/tests/test_queue.py`"*. The 27 November report attributes to "the audit" a label
  ("IMPLEMENTED, TESTED (frontend)") that the audit does not carry, so its §6 argues against a misquotation.

**Verdict.** The narrative is wrong on **both** counts: the audit's label is misquoted, and the coverage it
denies exists. MP-24's backend was **partly tested before**; the eight new tests in
`backend/tests/test_queue_history.py` add **different** assertions — every status including `completed`, the
`?status=` filter without re-classification, an invalid date returning **422**, and a foreign doctor id — which
is a real addition, but it is **not** "the first backend test" and it did **not** close an unexercised tenancy
path.

**What this does not change.** MP-24 stays **TESTED**; the new tests stay in the tree and remain valid evidence
for what they actually assert. No test was removed, weakened or re-described in code. Only the *narrative*
changes.

**Correction applied (OA-2 / RO-01).** The register's §16.2 cell is corrected in place with a visible note; the
report's §0, §6 and §8 text is **not rewritten** — report **§14** carries the correction and points here.

### 3.2 RO-02 — the MD-19 capability field was a live decision (F-02)

**What was found.** `backend/queuing/displays.py::_denied()` records
`after.capability = "queue.display.manage"` on both the 403 and the non-disclosing 404 path. That field was
added in the **27 November second window**, i.e. **before** any Product Owner answer existed, while the
implementation report's §4.1 (`:81`, "This was not an open product decision") and §9 recorded that no decision
was required. That reading was an **agent reconciliation**, not an owner decision: MD-19 requires the denial to
be audited with "actor, **capability**, org/branch", so whether the capability is a stored field was always an
owner question (audit **F-02**).

**Verdict.** A Product Owner decision **was** required. It has now been given: **PO-DEC-01 — Option A, persist
the capability field** (2026-11-27). The field stands as implemented; MD-19 is **not** amended; no deviation row
is opened.

**The sequencing is not laundered.** Option A ratifies the **content that resulted**; it does not convert the
earlier write into an authorised act. The sequence — *decision requested, code changed before the answer,
decision then given* — is recorded here, in register §17.1 and in the decision request §11.2(3).

**Recorded in.** `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` **§11** (decision
record); register **§17.1**; report **§13**; Docs Index **Revision 57**. **MP-46 remains TESTED** — the answer is
a decision, not independent evidence, and not an acceptance signature.

### 3.3 RO-03 — the second scratch database's transcript does not exist (F-08)

**What was claimed.** Register §15.1 described `amsdp_verify_1127b` as *"created empty and migrated zero →
head"*.

**What the tree shows.** No retained artefact records that database being created or migrated. The retained
`amsdp_dbs.txt` is timestamped **11:20:38** and predates the database's existence. The **second green run is
real**; its creation and migration transcript is **not**.

**Verdict.** Unsupported provenance. Corrected in place in register §15.1: the row now describes *"a second run
on a separate scratch database"* and states that "created empty and migrated zero → head" is **not claimed**.
The evidence limitation is **retained**, not removed — that is the point of the correction.

### 3.4 RO-04 — MP-33 and MP-34 labels versus actual authority

**MP-34.** Labelled **GATED (PO-09)**. But **PO-09 is CLOSED**, and the deliverable — the annotation set, the
PO-11 note and the PO-12 register — is **applied**. MP-34 is therefore **IMPLEMENTED, awaiting Product Owner
review**, and is **not accepted**. The "GATED" label misstates both the gate (closed) and the remaining work
(acceptance, not a decision).

**MP-33.** Labelled **GATED**, then **BLOCKED** with the reason "CI cannot first go green on work that is not
pushed, and O-3 forbids pushing". That is not a gate and not a defect: it is an **authorisation** blocker.
**OA-1** (commit/push) was requested and was **not granted** on 2026-11-27 — the owner required a CI diagnosis
first. MP-33 is **BLOCKED on OA-1**, and no MP-33 code changed.

**MP-30 (adjacent, authorised under T-3).** Labelled **GATED (undefined)**; **PO-01 is CLOSED**, so MP-30 is
**IMPLEMENTATION-READY as a verification task** and **BLOCKED on live evidence**, not gated on a decision.

**Applied.** Register §13.3 annotates all four lines — and the MP-09/13/14/15 line, which is **SEQUENCED**, not
GATED; §17.2 carries the corrected counts. **No status was promoted**: every re-classification moves an item
**between blockers** against authority that already existed, and nothing moved toward acceptance.

### 3.5 RO-05 — the "47 items" tally is not a closed set

**What was claimed.** Register §16.4 and report §8.5 both give "**Re-derived counts (47 items)**: 28 TESTED,
3 PARTIAL, 5 BLOCKED, 2 GATED, 5 DEFERRED, 4 SEQUENCED" — arithmetic that adds to 47, which is why it survived
review.

**What the tree shows.** The count includes **MP-02b** as its own row (it is a sub-item of MP-02, named in the
plan at `AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md:186` and `:209`) and **omits MP-47 entirely**:
`MP-47` occurs **zero** times in the implementation report, and the register opened MP-47 in **§13** the day
before the tally was taken. The enumerated set is therefore *MP-01…MP-46 plus MP-02b*, not the whole register.

**Verdict.** The tally is arithmetically sound but **not a closed set**: 48 rows, not 47. Combined with RO-04,
the corrected tally is **0 GATED** — register §17.2 enumerates all 48 and shows the class-by-class arithmetic.

### 3.6 RO-06 — unrecoverable

**RO-06 was not restated in the Product Owner's answer and no primary source in this tree identifies it.**
Recording a guess would breach `.clinerules` §3 ("Never claim a capability that is not verified") and §12
("Never describe a document's contents you have not read"). It is therefore **open by absence of source**, not
by disagreement, and no correction is claimed against it.

### 3.7 RO-07 — the Docs Index count convention, broken once

**The convention the index uses.** Every revision closes with a **Counts** line giving the verified on-disk
total of `*.md` files under `docs/`, reconciling with the previous revision's figure, so the chain can be
audited end to end.

**Where it breaks.** Revision 50 closes at **163** (`AMSDP_Docs_Index_V1.0.md:2177`). Revision 51 (`:2191`)
registers one document but publishes **no Counts line**. Revision 52 (`:2280`) then states *"165 (164 before
this revision)"* — a figure its predecessor never published, so the chain appears to jump 163 → 164 with no
stated cause. From Revision 52 onward the chain is internally consistent (165 → 166 → 166 → 169 → 170) and its
closing figure **matches the tree**: `Get-ChildItem docs -Recurse -Filter *.md` returned **170** before this
document was created.

**Verdict.** One break, one cause: a missing Counts line in Revision 51. **Revisions 51 and 52 are not
rewritten** — historical revision text is preserved. The convention is restated, and the break recorded, in
**Revision 57**, whose own figure is verified against the tree rather than carried forward arithmetically.

### 3.8 RO-08 — caller versus target branch on the 404 path

**What was found.** MD-19 requires the denial to be audited with "actor, capability, org/branch". On the
**404** path the target display is, by design, not disclosed; `_denied()` therefore stores the **caller's**
organisation and branch and identifies the target through `target_id`. MD-19 does not distinguish caller from
target branch, so no reading of the specification alone settles which is meant.

**Owner's answer (OPC-3, 2026-11-27):** *AGREE — record caller organisation/branch context and identify the
target through `target_id`, consistent with the current interpretation of MD-19.*

**Verdict.** Not a defect and not an MD-19 amendment: a **documented interpretation**, now owner-confirmed. It
widens no scope and creates no new obligation. Recorded in register **§17.3** and decision request §11.2.

### 3.9 RO-09 — unrecoverable

As §3.6. **No restatement, no primary source, no invented finding.**

### 3.10 RO-10 — unrecoverable

As §3.6. **No restatement, no primary source, no invented finding.**

---

## 4. Corrections applied under OA-2

| # | File | Change | Authority |
|---|---|---|---|
| 1 | `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` | **§11** appended: PO-DEC-01 Option A recorded, with what it settles and what it does not; one status row added to the header table so the answer is visible on arrival. **§1–§10 untouched** | PO-DEC-01 + OA-2 |
| 2 | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | **§17** appended: PO-DEC-01 record, status corrections, corrected 48-row tally, interpretations, outstanding authorisations, CI investigation | PO-DEC-01 + OA-2 |
| 3 | same register | **§13.3** additive *Reconciled* annotation: MP-30, MP-34, MP-33 and MP-09/13/14/15; the table itself not rewritten | T-3, T-4, RO-04 |
| 4 | same register | **F-13, three places:** the §8 change-log row for 2026-11-27, the §15 introduction and the §15.1 table row — "PostgreSQL 17" → **16.4**, each marked with its authority and the original wording | F-13 |
| 5 | same register | **F-08:** §15.1 database row — "created empty and migrated zero → head" replaced by "a second run on a separate scratch database", with the transcript limitation stated | F-08 / RO-03 |
| 6 | same register | **RO-01:** §16.2 MP-24 cell corrected — the route *did* have eight backend tests before this window | RO-01 |
| 7 | `docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md` | **§13** appended: what PO-DEC-01 supersedes in §4.1/§9, and what it does not change. **§0–§12 untouched** | PO-DEC-01 + OA-2 |
| 8 | same report | **§14** appended: the RO-01 correction, pointing at §3.1 here. No finding rewritten | RO-01 |
| 9 | `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` | post-audit annotation: A-1 answered, A-2 executed, F-08/F-13 closed as documentation acts. **Findings untouched** | PO-DEC-01 + OA-2 |
| 10 | `docs/governance/AMSDP_Docs_Index_V1.0.md` | **Revision 57**: this document registered, the decision-request row marked answered and re-sized, the count convention restated, the Revision 51 break recorded | T-7 + RO-07 + §12 |
| 11 | this document | **Created** and registered (T-7) | T-7 |

**Nothing under `backend/`, `frontend/`, `.github/`, `docker-compose.yml` or any migration was touched.** No
test was run, added or edited. No database was contacted. Nothing was staged, committed, pushed, deployed or
reseeded.

## 5. Deliberate non-corrections, and why

1. **`AMSDP_Docs_Index_V1.0.md` Revision 54's "PostgreSQL 17" is left as written.** Revision 55's annex already
   carries the correction and explicitly preserves Revision 54's text; rewriting it would remove the very
   evidence the annex refers to. The register's three operative sentences were corrected instead.
2. **Report §0, §6 and §8 are annotated, not rewritten.** They record what was believed and claimed in that
   window; §14 is the correction of record. Rewriting them would erase the RO-01 finding itself.
3. **Register §7's 25 November gate table (`:307`) is not annotated.** It is superseded by §17.2, and one
   supersession record is easier to audit than scattered notes. It states historical, not current, state.
4. **No MD-19 amendment and no deviation row (RO-08).** The owner confirmed an interpretation; the
   specification is a frozen approved document and OA-2 does not authorise editing it.

---

## 6. Open items this record does not close

1. **RO-06, RO-09, RO-10 — unrecoverable.** Supply the original reconciliation text if they must be preserved.
2. **`AC-21` field enumeration.** The acceptance criterion counts denial rows and does not assert the capability
   field. Adding such an assertion is a test-scope change that **OA-2 does not authorise**.
3. **RO-01's substantive question.** MP-24's coverage now sits in two overlapping files
   (`backend/queuing/tests/test_queue.py` and `backend/tests/test_queue_history.py`). Whether they should be
   consolidated is an engineering decision, not a documentation one, and is **not** taken here.
4. **Owner authorisations remain as answered:** **OA-1, OA-3, OA-4, OA-5, OA-6, OA-7 and OA-8 not granted**;
   **OA-2 granted with limited scope**.

## 7. Evidence index

| Claim | Where it was checked |
|---|---|
| The queue-history route existed and was tested before 27 November | `backend/queuing/tests/test_queue.py:1141`–`:1250`; route at `backend/queuing/main.py:724` |
| The 26 November audit's MP-24 label and its test citation | `docs/implementation/AMSDP_Master_Roadmap_V1.1_Full_Implementation_Audit_V1.0.md:246` |
| The 27 November report's premise | `docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md:27`, `:194`–`:199`, `:312` |
| MP-47 absent from the report | `Select-String … -Pattern 'MP-47'` → **0** matches |
| MP-02b is a sub-item of MP-02 | `AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md:186`, `:209` |
| Docs Index count chain | `AMSDP_Docs_Index_V1.0.md:2022`, `:2057`, `:2104`, `:2148`, `:2177`, `:2280`, `:2352`, `:2439`, `:2492` |
| On-disk document total | `Get-ChildItem docs -Recurse -Filter *.md -File` → **170** before this document |
| The capability field's two paths | `backend/queuing/displays.py::_denied()` |
| The queue-reorder guard behind QUE-005 | `backend/queuing/main.py:651`–`:668` |

## 8. What this document does not claim

- It does **not** re-run, re-verify or re-grade anything. No project status moves because of it.
- It does **not** claim RO-06, RO-09 or RO-10 were investigated — they were not recoverable.
- It does **not** claim the report's or the register's historical text is now accurate; it claims the
  corrections are recorded where a reader will find them.
- It is **not** an acceptance of any work package. Acceptance remains the Product Owner's act alone.

---

<!-- Written 2026-11-27 under Product Owner authorisation OA-2 (task T-7). Read-only evidence review; no code,
     test, database, deployment or configuration was touched. Registered in Docs Index Revision 57. -->


---
