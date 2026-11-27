# AMSDP — OA-1 Commit Manifest — Proposal — V1.0

| | |
|---|---|
| **Document** | `docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md` |
| **Purpose** | State exactly which working-tree paths would be committed, in what groups, in what order, with what messages — so OA-1 can be granted or refused against a specific act rather than a description of one |
| **Written** | 2026-11-27, fifth window (controlled verification preparation) |
| **Status** | **PROPOSAL. Nothing is staged, committed or pushed.** `HEAD` is `71226e8`; `git diff --cached` is empty; 0 paths staged (verified this window) |
| **Companions** | `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md`; `docs/testing/AMSDP_OA8_B2_Local_Stack_Verification_Plan_V1.0.md` |

> **The manifest is the request.** Granting OA-1 against this document means authorising these specific
> `git add` calls and these specific commit messages — not "committing whatever is in the tree".

---

## 1. What exists right now, measured

| Fact | Value | How it was measured |
|---|---|---|
| `HEAD` | `71226e8` *docs: verify the pull by ancestry, not by a hardcoded tip* | `git log -1 --format=…` |
| Branch | `hackathon-mvp`, tracking `origin/hackathon-mvp` | `git log --oneline -12` |
| Staged paths | **0** | `git diff --cached --stat` → empty |
| Working paths at window start | **24** — 15 tracked-modified, 9 untracked | `git status --porcelain` |
| Working paths now | **28** — 15 tracked-modified, 13 untracked | `git status --porcelain` (**26 lines**: the wholly-untracked `docs/testing/` directory collapses its 3 files into one line) |
| Backend suite | **1,071 collected** — 1,069 before this window, +2 collection-purity guards | `pytest --collect-only -q` → `1071 tests collected in 1.80s` |

**Note on the count.** The Product Owner asked for a manifest of **24** paths. The tree held 24 at the start
of this window; this window's §4 safe work added one source file (`test_collection_purity.py`), and this
window's documentation adds three more (this manifest, the T-10 execution plan, the local-stack plan). The
manifest therefore covers **28 paths by the end of the window**, of which the 24 the instruction named are
unchanged. Nothing was removed or consolidated to reach any number.

---

## 2. The tracked modifications (15)

| # | Path | +/− | What the hunk actually does |
|---|---|---:|---|
| 1 | `.clinerules` | +2/−1 | **Owner change.** Adds `plan/` to the authoritative docs tree and records the 2026-11-24 ratification of `docs/plan/`. Not authored in these windows |
| 2 | `backend/queuing/displays.py` | +21/−3 | **MP-46 / OPC-3 product change.** `_denied()` gains a `target_id` parameter and a `capability` field on both denial branches |
| 3 | `backend/tests/test_display_admin.py` | +69/−6 | MP-46 assertions: capability on the 403 path (`:192`), capability + `target_id` + caller branch on the 404 path (`:272`–`:281`) |
| 4 | `backend/identity/tests/test_identity.py` | +59/−39 | **Two deliverables in one file**: the D-3 fixture (third window) and the T-10 conversion of its import-time seeding (fourth window) |
| 5 | `backend/tests/test_security.py` | +14/−1 | T-10: `_ensure_orgs_and_branches()` moved from import time into a module-scoped `autouse` fixture. Its import-time run created `other-org-999` before any test — the mechanism that masked D-3 |
| 6 | `backend/tests/test_dashboard.py` | +9/−1 | T-10: `_ensure()` moved into the same fixture shape |
| 7 | `backend/tests/test_dqds.py` | +10/−1 | T-10: `_ensure()` moved into the same fixture shape (`import pytest` added) |
| 8 | `backend/tests/test_patient_age.py` | +29/−4 | T-10: import-time seeding and token minting moved into fixtures |
| 9 | `backend/tests/test_tracking_tokens.py` | +60/−10 | T-10: three import-time token mints and their seeding moved into fixtures |
| 10 | `backend/queuing/tests/test_queue.py` | +8/−1 | T-10: `_ensure_org()` moved into the same fixture shape |
| 11 | `backend/tests/test_operational_reports.py` | +9/−0 | **Earlier correction, not T-10.** `purge_org` deletes patients, so the patient is re-created after the purge; `QueueEntry` rows now carry the NOT NULL `token` and `patient_id` the schema requires |
| 12 | `frontend/pages/queue-display/[org]/[branch].js` | +6/−3 | **MP-38 product fix.** `scopeLabel(display,T)` referenced a module-scope `tr` that does not exist — a `ReferenceError` the moment a non-branch board rendered; the translator is now a parameter |
| 13 | `frontend/tests/display-board.test.mjs` | +22/−0 | MP-38 regression guard for that `ReferenceError`, plus a translated-key check per scope type |
| 14 | `docs/governance/AMSDP_Docs_Index_V1.0.md` | +317/−0 | Documentation register: Revisions 58, 59 and 60 — additive blocks only |
| 15 | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | +736/−0 | Documentation register: §18 (third window) and §19 (fourth window) — additive sections only |

## 3. The untracked documents and tests (13 by the end of this window)

| # | Path | Bytes | Deliverable |
|---|---|---:|---|
| 16 | `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` | 49,655 | Second-window execution audit |
| 17 | `docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` | 21,311 | Second-window reconciliation findings |
| 18 | `docs/audit/AMSDP_Database_Authorisation_Deviation_27Nov2026_V1.0.md` | 12,135 | Fourth window: the deviation record |
| 19 | `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` | 18,173 | MP-46 / OPC-3 decision request |
| 20 | `docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md` | 36,035 | MP-46 / MP-38 implementation report |
| 21 | `docs/implementation/AMSDP_D3_Fixture_and_MP-46_OPC3_Target_Id_Implementation_Report_V1.0.md` | 23,580 | D-3 / OPC-3 report, carrying §11 |
| 22 | `docs/plan/AMSDP_Remaining_Verification_Plan_V1.0.md` | 10,384 | Fourth window: per-package verification plan |
| 23 | `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` | 21,344 | Second/third-window execution evidence |
---

## 4. The six groupings the instruction asked for

| Requested grouping | Paths | Note |
|---|---|---|
| **Application and test changes** | `#2` `displays.py`, `#12` `[branch].js`, with their tests `#3`, `#13` | The only two product-code changes in the tree. Everything else is test or documentation |
| **Documentation and audit changes** | `#14`, `#15`, `#16`–`#23`, `#26`–`#28` | Additive only: no existing document was rewritten, and no earlier version was deleted |
| **Pre-existing owner changes** | `#1` `.clinerules` (+2/−1) | The `docs/plan/` ratification of 2026-11-24. **Excluded from every proposed commit** — it is the owner's change, not an agent's, and §5 explains why |
| **"The five earlier test corrections"** | **The tree does not contain a set of five.** See §4.1 | Reported rather than invented |
| **D-3 / MP-04 / MP-46 / OPC-3** | D-3 → part of `#4`; MP-46/OPC-3 → `#2`, `#3`; **MP-04 → no working-tree change at all** | MP-04's 25 tests live in `organization/tests/test_voice_packs_api.py`, which is **already committed** — nothing about MP-04 is uncommitted |
| **T-10 fixture changes** | part of `#4`, plus `#5`–`#10`, and the new guard `#25` | Behaviour-preserving on the test side only; no product code and no schema |

### 4.1 The "five earlier test corrections" — what the diffs actually contain

Read hunk by hunk (`git diff -U0`), the test-side changes decompose as:

| Class | Paths | Count |
|---|---|---|
| Import-time write removed, nothing else (pure T-10) | `test_security.py`, `test_dashboard.py`, `test_dqds.py`, `test_patient_age.py`, `test_tracking_tokens.py`, `queuing/tests/test_queue.py` | **6** |
| D-3 fixture **and** T-10 in the same file | `identity/tests/test_identity.py` | 1 |
| Genuinely earlier correction, unrelated to T-10 or D-3 | `tests/test_operational_reports.py` — `purge_org` deletes patients, so the patient is re-created after the purge, and `QueueEntry` rows are given the NOT NULL `token`/`patient_id` | **1** |
| New test modules not previously tracked | `test_queue_history.py` (MP-24), `test_collection_purity.py` (T-10 guard) | 2 |

**The closest true statement** is: *six* test modules were corrected for one defect (T-10), *one* for a
different one (`test_operational_reports.py`), and *one* carries two deliverables. If the instruction's
"five" refers to a specific set, it does not correspond to a boundary visible in the diff, so it is listed
here as an **open item** rather than forced into a shape the tree does not have. It does not block the
manifest: every test path is included in exactly one proposed commit (§5).

| 24 | `backend/tests/test_queue_history.py` | 7,448 | **MP-24 route-level tests** — the history route asserted where it is enforced, not by a source scan |
| 25 | `backend/tests/test_collection_purity.py` | 5,167 | **T-10 guard**, new this window (executed: 2 passed; proven to fail against a reintroduced import-time write — §6) |
| 26 | `docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md` | 22,426 | **This manifest** |
| 27 | `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md` | 22,933 | T-10 execution authorisation request |
| 28 | `docs/testing/AMSDP_OA8_B2_Local_Stack_Verification_Plan_V1.0.md` | 18,745 | Browser verification plan |


---

## 5. Recommended commit sequence — four commits

**Why four and not two.** The instruction asks for separate code/test and documentation commits; that is the
backbone (C1–C3 carry code and tests, C4 carries documentation). Within the code side, the two product
changes are unrelated defects in different layers (a backend denial-audit contract; a frontend
`ReferenceError`), and each already carries its own regression test, so splitting them gives two commits that
are individually reviewable and individually revertable. **Two commits would also be defensible**; one commit
would not — it would put a product-code change and 13 documents in the same review.

| Commit | Subject | Paths | Depends on |
|---|---|---|---|
| **C1** | `feat(display): record capability and target id on both denial paths` | `backend/queuing/displays.py`, `backend/tests/test_display_admin.py` | — |
| **C2** | `fix(dqds): pass the board's translator into the scope label` | `frontend/pages/queue-display/[org]/[branch].js`, `frontend/tests/display-board.test.mjs` | — |
| **C3** | `test: stop pytest collection from writing to the database` | `backend/tests/test_security.py`, `test_dashboard.py`, `test_dqds.py`, `test_patient_age.py`, `test_tracking_tokens.py`, `test_operational_reports.py`, `backend/queuing/tests/test_queue.py`, `backend/identity/tests/test_identity.py`, `backend/tests/test_queue_history.py` (new), `backend/tests/test_collection_purity.py` (new) | independent of C1/C2 |
| **C4** | `docs: MP-46/OPC-3 and MP-38 reports, the D-3 follow-through, the T-10 finding and the deviation record` | the 2 tracked registers + all 13 untracked documents | **C1, C2, C3** — it describes code those commits contain |

**Why C4 must be last.** Every document in C4 cites the state of the files above it by name, difference and
test count. Committing the documents first would put a description of uncommitted code into history — exactly
the class of claim the audit records spent four windows separating. C1–C3 in any order is safe.

**Why `.clinerules` is in none of them.** It is a **Product Owner** change (the `docs/plan/` ratification)
sitting in a shared working tree. Committing it under an agent's OA-1 would attribute the owner's governance
edit to an agent commit. Recommendation: the owner includes it in their own commit, or explicitly authorises
its inclusion in C4. **It is preserved untouched either way** (verified: last modified 2026-11-24 09:55:25,
before this window).

### 5.1 Exact commands — to be run only after OA-1 is granted

```powershell
# C1
git add backend/queuing/displays.py backend/tests/test_display_admin.py
git commit  # message in §6.1

# C2
git add "frontend/pages/queue-display/[org]/[branch].js" frontend/tests/display-board.test.mjs
git commit  # message in §6.2

# C3
git add backend/tests/test_security.py backend/tests/test_dashboard.py backend/tests/test_dqds.py `
        backend/tests/test_patient_age.py backend/tests/test_tracking_tokens.py `
        backend/tests/test_operational_reports.py backend/queuing/tests/test_queue.py `
        backend/identity/tests/test_identity.py backend/tests/test_queue_history.py `
        backend/tests/test_collection_purity.py
git commit  # message in §6.3

# C4
git add docs/governance/AMSDP_Docs_Index_V1.0.md docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md `
        docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md `
        docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md `
        docs/audit/AMSDP_Database_Authorisation_Deviation_27Nov2026_V1.0.md `
        docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md `
        docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md `
        docs/implementation/AMSDP_D3_Fixture_and_MP-46_OPC3_Target_Id_Implementation_Report_V1.0.md `
        docs/plan/AMSDP_Remaining_Verification_Plan_V1.0.md `
        docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md `
        docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md `
        docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md `
        docs/testing/AMSDP_OA8_B2_Local_Stack_Verification_Plan_V1.0.md
git commit  # message in §6.4
```

**Guard rail before each commit:** `git diff --cached --name-only` must list **exactly** the paths of that
commit and nothing else — in particular never `.clinerules`, `.env*`, `*.log`, `__pycache__/` or
`.pytest_cache/`. If a path appears that is not on the list, stop and report; do not `git add -A`, and do not
`git reset --hard` or `git checkout --` to tidy up (`.clinerules` §9).


---

## 6. Proposed commit messages

Style matches the existing history (`feat:`, `fix(scope):`, `docs:`, conventional subject, imperative mood,
body explaining *why* — see `516e46b`, `082e2a0`, `31fcb45`).

### 6.1 C1

```
feat(display): record capability and target id on both denial paths

A display refusal wrote a queue.display.denied row that could not answer the
two questions an auditor asks: which permission was missing, and which display
was targeted.  MD-19 requires all three (actor, capability, caller org/branch).

_denied() now takes a target_id and writes a capability field on both branches:
the 403 capability refusal and the cross-tenant 404.  The 404 path passes the
target the caller named, plus the resolved row's id when the row exists, so the
audit row is populated whether or not the target resolved -- and the response
stays the same non-disclosing 404 either way.

Tests: test_display_admin.py asserts the capability on the 403 path (line 192)
and capability + target id + caller branch, with the target branch absent, on
the 404 path (272-281).
```

### 6.2 C2

```
fix(dqds): pass the board's translator into the scope label

scopeLabel() lives at module scope, so it has no access to the component's tr.
An earlier version referenced tr anyway and its call site passed an undefined T,
so the board threw a ReferenceError the moment a non-branch display rendered --
including the seeded cardio department board used in the demonstration.

The helper now declares its translator as a parameter and the call site passes
tr.  display-board.test.mjs asserts both, and that every scope type renders a
translated key.
```

### 6.3 C3

```
test: stop pytest collection from writing to the database

Seven modules created reference rows or minted tokens at import time, so
collection -- a read-only command -- wrote to whatever AMSDP_DATABASE_URL
pointed at.  The side effect also made the suite order-dependent: test_security
seeded other-org-999 before any test ran, which is why the D-3 cross-tenant
defect passed in every whole-tree run and failed when its module ran alone.

Every import-time seed and token mint is now a module-scoped autouse fixture.
No test body changed; no product code or schema changed.

Adds test_collection_purity.py as the guard: it points the suite at an
unreachable sentinel DSN and requires collection to succeed anyway, with a
separate assertion that the sentinel really is unreachable.  Verified by
reintroducing an import-time write -- the guard fails with the OperationalError.

Also: test_operational_reports.py recreates its patient after purge_org (which
deletes patients) and gives QueueEntry rows the NOT NULL token/patient_id;
test_queue_history.py asserts the MP-24 history route at the route itself.
```

### 6.4 C4

```
docs: MP-46/OPC-3 and MP-38 reports, D-3 follow-through, T-10 and the deviation

Registers, in one place, what the last four windows established and what they
did not:

* implementation and evidence records for MP-46/OPC-3, MP-38 and MP-24;
* the D-3 fixture follow-through and the T-10 finding that collection was
  writing to the database;
* a scope-deviation record for creating and migrating amsdp_verify_1129 in a
  window authorised for implementation only -- recorded, not normalised;
* per-package plans for the remaining verification, the disposable-database
  execution of T-10, and the local-stack checks for MP-04, MP-46 and the
  display band.

Docs Index Revision 60 and register sections 18-19 are additive; no earlier
document or version was rewritten, moved or deleted.
```


---

## 7. Deliberately excluded

| Path / class | Why |
|---|---|
| `.clinerules` | Owner change (2026-11-24 ratification of `docs/plan/`). Preserved untouched; committed only if the owner says so, in their own commit or explicitly in C4 |
| `.env`, `.env.local` | Gitignored, and §3 of `.clinerules` forbids exposing credentials. Verified absent from `git status` |
| `__pycache__/`, `.pytest_cache/` | Build artefacts. Collection runs in this window used `-p no:cacheprovider`, so no new cache was written |
| `E:\Temp\*.txt` logs | Outside the repository by design; cited by path and hash from the audit records, never committed |
| `docs/demo/AMSDP_Demo_Credentials_V1.0.md` | Owner-controlled and already tracked; may be read, never quoted (§12) |
| Anything under `ai_factory/` | Out-of-tree by owner decision O-1; not touched |

## 8. Verification available per commit, without a database or a browser

| Commit | Command | Expected | Already observed? |
|---|---|---|---|
| C1 | *(none executable in this window)* | — | **No.** `displays.py` is product code whose tests need a database; the last execution is the retained 17:09:20 whole-tree log (`1069 passed`) with the change in the tree. C1 is committed on **that** evidence, not on a fresh run — the T-10 plan is what closes the gap |
| C2 | `cd frontend; npm test` | the `display-board.test.mjs` MP-38 guard passes together with the rest of the local frontend suite | **Yes** at the last recorded run (frontend suite green, MP-38 guard 3/3 against the pre-fix source); not re-run this window |
| C3 | `cd backend; python -m pytest tests/test_collection_purity.py -q` and `python -m pytest --collect-only -q` | `2 passed`; `1071 tests collected`, 0 errors, no connection attempt | **Yes — executed this window** (§9, evidence E-1) |
| C4 | `git diff --cached --name-only` before committing | exactly the 15 documentation paths | n/a (proposal) |

## 9. Evidence this window produced for the manifest

| Id | What was run | Result |
|---|---|---|
| **E-1** | `python -m pytest tests/test_collection_purity.py -q -p no:cacheprovider` | **2 passed in 7.63 s**, then **2 passed in 6.62 s** after the negative control was removed |
| **E-2** | *Negative control:* a throwaway module with a module-level `SessionFactory().execute(text("select 1"))` added under `backend/tests/` | guard **failed** as designed: `sqlalchemy.exc.OperationalError … connection to server at "127.0.0.1", port 1 failed: Connection refused`, `1 failed, 1 passed`; the probe (sentinel-unreachable) still passed, so the two assertions are independent |
| **E-3** | throwaway module deleted; `Test-Path` → `False`; guard re-run | green again; **no residual file** |
| **E-4** | `pytest --collect-only -q` | **1071 tests collected in 1.80 s** with no database configured |

## 10. Risks, and what approval would actually cover

| Risk | Handling |
|---|---|
| C1 commits product code whose tests cannot be executed in this window | Stated, not hidden. The retained whole-tree log is the evidence; the T-10 execution plan closes it. C1 can also be deferred until after the database run, if the owner prefers C2/C3/C4 first |
| The two registers mix several windows in one file | One docs commit (C4). Splitting them with `git add -p` would create intermediate commits whose documents describe each other inconsistently — worse than a single additive docs commit |
| Byte counts inside the documents drift with every edit | Documents state sizes as measured at write time and the index says its own size is not asserted as exact. No document is load-bearing on a byte count |
| A wrong `git add` picks up the owner's `.clinerules` | Guard rail in §5.1: inspect `git diff --cached --name-only` before every commit; never `git add -A` |
| Push is a separate act from commit | **MP-33 needs a push.** Approval should say which: (a) commit only, (b) commit + push to `origin/hackathon-mvp`. This manifest requests **(a) or (b) explicitly named by the owner** — a bare "OA-1" is ambiguous and will be treated as (a) |

**What this manifest does not claim.** It does not claim the tree is green — the backend suite has not been
executed since the T-10 refactor. It does not claim C1's behaviour is verified. It does not ask for a push. It
does not touch `.clinerules`, any database, any container or any O-1 infrastructure.

<!-- Proposal only. Written 2026-11-27, fifth window; nothing staged, committed or pushed. -->

---

## 11. Addendum — 27 November 2026 (fifth window): owner response

**The five corrections are named by the owner, and §4.1's open item closes:**

1. `test_operational_reports.py` — fixture-owned patient deletion.
2. `test_operational_reports.py` — required queue-entry fields.
3. `test_display_admin.py` — public-board facility-code handling.
4. `test_display_admin.py` — non-vacuous MP‑45 visibility assertion.
5. `test_tracking_tokens.py` — durable rate-limit fixture isolation.

The naming confirms §4.1's finding rather than contradicting it: the set is not a diff boundary, because #3 and
#4 share a file with the MP‑46 assertions and #5 shares a file with the T‑10 refactor. Separating corrections from
product fix and from T‑10 therefore needs **hunk-level staging**; `docs/plan/AMSDP_OA1_Commit_Manifest_Final_V1.0.md`
carries the validated mechanism (V‑1…V‑5) and **supersedes §7's sequence**. Its §3 is the authoritative mapping.

Other owner answers, recorded here because they bind this document too: `.clinerules` stays excluded from every
commit; **commit preparation only** — no staging, no commit; **no push is authorised**; the T‑10 and OA‑8/B‑2
plans are submitted for review, not execution.

<!-- Addendum appended 2026-11-27. §1–§10 preserved exactly as written. -->


