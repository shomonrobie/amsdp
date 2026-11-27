# OA-1 — Final Commit Manifest (for approval)

**Document id:** AMSDP-OA1-MANIFEST-FINAL · **Version:** 1.0 · **Date:** 27 November 2026
**Supersedes (sequence only):** `docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md` §7 — that document is
retained unchanged; its measurements, exclusions and risk register stand.
**Status:** **PROPOSED — nothing staged, nothing committed, nothing pushed.**

**Owner decisions this document implements**

| Decision | Effect on this manifest |
|---|---|
| "Proceed with commit preparation only" | Staging/commit commands are presented, **not executed**. `git diff --cached` is empty at the time of writing |
| "Use the proposed four-commit structure, subject to final inspection" | Sequence **B** is the strict four-commit arrangement; sequence **A** is the five-commit arrangement the correction split forces. The owner chooses (§5, §6) |
| The five corrections, named | §3 maps each to file, hunk and diff lines; they are separated from T-10 in both sequences |
| "Exclude `.clinerules` entirely" | Excluded from every commit; it is the only path left dirty at the end |
| "Commit and push are separate permissions. No push is authorised" | No `push` appears in any command block below |

---

## 1. Measured state at the time of writing

| Property | Value | How measured |
|---|---|---|
| `HEAD` | `71226e8` *docs: verify the pull by ancestry, not by a hardcoded tip* | `git log -1` |
| Staged | **0 files, 0 lines** | `git diff --cached --name-only`, `git diff --cached` |
| Working paths | **29** — 15 tracked-modified + 14 untracked files | `git status --porcelain -uall` |
| `git status --porcelain` lines | **27** | `docs/testing/` is wholly untracked, so it collapses 3 files into 1 line |
| Source diff (`backend/`, `frontend/` — 12 paths) | **+316 / −69** | `git diff --numstat -- backend frontend` |
| Docs diff (2 registers, additions only) | **+1,265 / −0** | `git diff --numstat -- docs` — grows while this sitting writes |
| `.clinerules` | **+2 / −1** — excluded from every commit | `git diff --numstat -- .clinerules` |
| Tests collected | **1,071**, 0 errors | `pytest --collect-only -q` |
| Backend modules compiling | all 12 touched modules | `python -m py_compile` (this window) |

*(Source totals above exclude `.clinerules` and `docs/`. `.clinerules` is unchanged from the start of this
sitting: `+2/−1`, identical to the figure measured before any edit here.)*


---

## 2. Untracked files, by destination commit

| File | Commit |
|---|---|
| `backend/tests/test_collection_purity.py` | A‑4 / B‑3 (T‑10 guard) |
| `backend/tests/test_queue_history.py` | A‑4 / B‑3 (MP‑24 tests that arrived with the T‑10 work) |
| `docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` | A‑5 / B‑4 |
| `docs/audit/AMSDP_Database_Authorisation_Deviation_27Nov2026_V1.0.md` | A‑5 / B‑4 |
| `docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` | A‑5 / B‑4 |
| `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` | A‑5 / B‑4 |
| `docs/implementation/AMSDP_D3_Fixture_and_MP-46_OPC3_Target_Id_Implementation_Report_V1.0.md` | A‑5 / B‑4 |
| `docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md` | A‑5 / B‑4 |
| `docs/plan/AMSDP_OA1_Commit_Manifest_Proposal_V1.0.md` | A‑5 / B‑4 |
| `docs/plan/AMSDP_OA1_Commit_Manifest_Final_V1.0.md` (this file) | A‑5 / B‑4 |
| `docs/plan/AMSDP_Remaining_Verification_Plan_V1.0.md` | A‑5 / B‑4 |
| `docs/testing/AMSDP_Backend_Execution_Evidence_27Nov2026_V1.0.md` | A‑5 / B‑4 |
| `docs/testing/AMSDP_OA8_B2_Local_Stack_Verification_Plan_V1.0.md` | A‑5 / B‑4 |
| `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md` | A‑5 / B‑4 |

---

## 3. The five corrections, mapped exactly

`git diff -U3` grouping (the grouping a patch carries). `Hn` is the 1-based hunk index for that file.

| # | Correction | File | Hunk(s) | Diff |
|---|---|---|---|---|
| **1** | Fixture-owned patient deletion — `purge_org` removes patients, so the report patient is re-created after the purge instead of assumed to survive it | `backend/tests/test_operational_reports.py` | H1 | +5/−0 |
| **2** | Required queue-entry fields — `_queue_entry` supplies NOT NULL `token` and `patient_id` | `backend/tests/test_operational_reports.py` | H2, H3 | +4/−0 |
| **3** | Public-board facility-code handling — the board is addressed by org/branch **code**; tests now call `ORG_CODE`/`BR_CODE` | `backend/tests/test_display_admin.py` | H2, H6, H10 | +10/−4 |
| **4** | Non-vacuous MP‑45 visibility assertion — seeds one called + one waiting patient and asserts `D-001` is in the body, so "field absent" cannot pass against an empty board | `backend/tests/test_display_admin.py` | H1, H3, H4, H8, H9 | +40/−2 |
| **5** | Durable rate-limit fixture isolation — clears `tracking_rate_buckets` per test (MP‑25 moved the budget out of `_RATE`) and drops the three `_RATE.clear()` calls that stopped being a reset | `backend/tests/test_tracking_tokens.py` | H1, H2, H5, H6, H7 | +37/−7 |

**Not corrections — product fix (MP‑46 / OPC‑3):** `backend/tests/test_display_admin.py` H5 (+6) and H7 (+13),
which assert the MD‑19 triple (actor, capability, org/branch) on both denial paths and `target_id` on the
non-disclosing 404.

**Not corrections — T‑10:** `backend/tests/test_tracking_tokens.py` H3 (+8/−1) and H4 (+15/−2), which move
`_ensure()` and `TOKEN = _token()` into fixtures.

Arithmetic check: display_admin 50/6 (corrections) + 19/0 (product) = **69/6** = its full diff;
tracking_tokens 37/7 + 23/3 = **60/10** = its full diff. Nothing is left unassigned.

## 4. Why file-level `git add` cannot do this — and what does

`backend/tests/test_display_admin.py` and `backend/tests/test_tracking_tokens.py` each carry two unrelated
deliverables. `git add <file>` stages the whole file, so one deliverable would ride inside the other's commit —
exactly what the owner's instruction forbids for corrections vs T‑10.

**Mechanism:** `E:\Temp\amsdp_hunkstage.py` — read-only with respect to the repository (it runs `git diff`,
writes a patch file, nothing else).

```
python E:\Temp\amsdp_hunkstage.py --file <path> --list
python E:\Temp\amsdp_hunkstage.py --file <path> --hunks 5,7 --out <patch>
git apply --cached --check <patch>   # verify, writes nothing
git apply --cached <patch>           # stage exactly those hunks
```

**Validation performed this window — against a throwaway index (`GIT_INDEX_FILE=E:\Temp\idx_probe`), so the
repository index was never written:**

| Id | Check | Result |
|---|---|---|
| **V‑1** | `p1_display_feature.patch` (H5,H7) staged into a temp index | applicable; **19/0**, 2 hunks |
| **V‑2** | `p2_display_corrections.patch` (H1–H4, H6, H8–H10) | applicable; **50/6**, 8 hunks |
| **V‑3** | p2 then p1 in the proposed order | p1 still applicable after p2; union = **69/6, 10 hunks** = full file diff |
| **V‑4** | p3 (tracking H1,H2,H5,H6,H7) then p4 (H3,H4) | p4 applicable after p3; union = **60/10, 7 hunks** = full file diff |
| **V‑5** | real index after all probes | `git diff --cached --name-only` empty; `E:\Temp\idx_probe*` deleted |

Patches live in `E:\Temp` and are **derived artefacts**: valid only while those two files' diffs are unchanged.
If anything is edited before approval is exercised, re-read `--list` and regenerate — a stale patch fails
`--check` rather than applying to the wrong place.

---

## 5. Sequence A (recommended) — five commits, each independently reviewable

Order is deliberate: **corrections → product → frontend → T‑10 → docs**. Corrections first because the product
commit's stronger assertions only become reachable once the tests call the public route with the right handle;
T‑10 after corrections because `test_tracking_tokens.py` H1 (`import pytest`) belongs to the correction; docs
last because they describe everything above.

### A‑1 `test: five pre-existing corrections that blocked the queued work`

```
git add backend/tests/test_operational_reports.py
git apply --cached --check E:\Temp\p2_display_corrections.patch
git apply --cached E:\Temp\p2_display_corrections.patch
git apply --cached --check E:\Temp\p3_tracking_correction5.patch
git apply --cached E:\Temp\p3_tracking_correction5.patch
git diff --cached --numstat      # expect exactly: 9 0 ; 50 6 ; 37 7
git commit -F E:\Temp\msg_a1.txt
```

### A‑2 `feat(queuing): record capability and target id on both display denial paths`

```
git add backend/queuing/displays.py
git apply --cached --check E:\Temp\p1_display_feature.patch
git apply --cached E:\Temp\p1_display_feature.patch
git diff --cached --numstat      # expect exactly: 21 3 ; 19 0
git commit -F E:\Temp\msg_a2.txt
```

### A‑3 `fix(frontend): pass the board's translator into the scope label`

```
git add "frontend/pages/queue-display/[org]/[branch].js" frontend/tests/display-board.test.mjs
git diff --cached --numstat      # expect exactly: 6 3 ; 22 0
git commit -F E:\Temp\msg_a3.txt
```

### A‑4 `test: stop pytest collection from writing to the database (T‑10)`

By this point `test_tracking_tokens.py` holds only its T‑10 hunks, so a plain `git add` is exact.

```
git add backend/tests/test_tracking_tokens.py backend/identity/tests/test_identity.py `
        backend/queuing/tests/test_queue.py backend/tests/test_dashboard.py `
        backend/tests/test_dqds.py backend/tests/test_patient_age.py `
        backend/tests/test_security.py backend/tests/test_queue_history.py `
        backend/tests/test_collection_purity.py
git diff --cached --numstat      # expect 9 paths: 23/3, 59/39, 8/1, 9/1, 10/1, 29/4, 14/1, new, new
git commit -F E:\Temp\msg_a4.txt
```

### A‑5 `docs: OA-1 manifest, T‑10 and OA‑8/B‑2 plans, reconciliation and deviation records`

```
git add docs
git diff --cached --numstat      # expect 2 modified registers + 14 new documents
git commit -F E:\Temp\msg_a5.txt
```

`git add docs` is exactly the two registers plus the 14 untracked documents — no source path is under `docs/`.

### Residual tree after each step

| After | Paths still dirty | Expected `git status --porcelain` lines |
|---|---|---|
| A‑1 | 26 (12 modified + 14 untracked) | 24 |
| A‑2 | 24 (10 + 14) | 22 |
| A‑3 | 22 (8 + 14) | 20 |
| A‑4 | 15 (3 modified + 12 untracked) | 13 |
| A‑5 | **1** (`.clinerules`) | 1 |

---

## 6. Sequence B — the strict four-commit arrangement

Identical patches, merged boundaries: **B‑1 corrections** = A‑1 verbatim; **B‑2 products** = A‑2 + A‑3 with both
`git add` groups and both patches in one commit; **B‑3 T‑10** = A‑4 verbatim; **B‑4 docs** = A‑5 verbatim.

The only cost of B is that the backend denial fix and the frontend translator fix share one commit.
**Recommendation: A** — each correction is then reviewable as one act, and the two product fixes stay separable
in `git log`.

---

## 7. Verification per commit (to run at execution time, not now)

| Check | A‑1 | A‑2 | A‑3 | A‑4 | A‑5 |
|---|---|---|---|---|---|
| `git diff --cached --numstat` matches the stated figures | required | required | required | required | required |
| `git show --stat HEAD` lists only the expected paths | required | required | required | required | required |
| `.clinerules` absent from `git show --name-only HEAD` | required | required | required | required | required |
| `git diff HEAD -- <path>` empty for every committed path | required | required | required | required | required |
| Residual `git status --porcelain` line count matches §5 | required | required | required | required | required |

**Test evidence available for each commit.** Honest position: the retained whole-tree log is the **17:09** run
(`1,069 passed`, 548.80 s, 0 errors). It predates the new guard, and **no retained log isolates the five
corrections or the MP‑46 assertions as their own run**. These commits therefore rest on that log plus inspection,
not on per-commit execution. Run A of the T‑10 execution plan is what upgrades them to tested-by-run; the commit
sequence does not wait for it, and no commit message claims otherwise.

---

## 8. Exclusions (restated because they are load-bearing)

| Excluded | Why |
|---|---|
| `.clinerules` (+2/−1) | Owner change (2026‑11‑24 `docs/plan/` ratification). Never staged, committed or edited |
| `.env`, `.env.*` | Secrets. Never staged, never quoted |
| `__pycache__/`, `.pytest_cache/`, `*.pyc` | Build artefacts, already ignored |
| `ai_factory/` | Separate subsystem; out of tree by owner decision O‑1 |
| `E:\Temp\*` | Logs, patches, guard scripts, message files — evidence, not source |
| Every database | No commit command in this manifest touches one |

---

## 9. Risks and limits

1. **No per-commit test run** (§7). Run A is the remedy.
2. **The patches are derived artefacts** tied to two files' current diffs. If either changes, re-read `--list`
   and regenerate; a stale patch fails `--check` rather than applying elsewhere.
3. **A failed `git apply --cached` leaves the index partly staged.** Every block runs `--check` first; recovery is
   `git restore --staged <the paths just added>` — an index-only operation that cannot touch the working tree
   (`.clinerules` §9 forbids `checkout`/`stash`/`reset --hard`; `restore --staged` is named here explicitly so the
   recovery path is a decision, not an improvisation).
4. **A‑1 lands before the product fix**, so `displays.py`'s change is committed on the strength of the 17:09 log,
   not a fresh run.
5. **The docs commit is self-referential** — this manifest is committed by A‑5 while describing A‑5, so its cited
   byte size is measured at write time.
6. **"OA‑1" alone is ambiguous.** This manifest authorises commit preparation only; a push needs a separate,
   named grant.

---

## 10. What approval would and would not cover

**Would cover:** running the command blocks exactly as written, in order, creating local commits on the current
branch — nothing else.

**Would not cover:** `git push`, rebase, amend, squash, staging any excluded path, any database access, any
container, any browser work, or editing any product file.

---

## 11. Approval block

| Item | Owner answer |
|---|---|
| Sequence A (5 commits) or B (4 commits) | _pending_ |
| Commit preparation approved | _pending_ |
| Hunk-split patches approved as the mechanism for the two mixed files | _pending_ |
| Push approved | **No** — separate permission, not requested here |

---

## 12. Exact commit messages

The block below is the only place these messages exist; running it writes the five files the command blocks
consume, so message text and command cannot drift apart. Messages are ASCII-only and written with
`-Encoding ascii` so no BOM reaches the commit message.

```powershell
$m1 = @'
test: five pre-existing corrections that blocked the queued work

Five tests were written before MP-25 moved the tracking budget into the
database and before the public board became code-addressed. Each could not
have passed as written. None of them changes product behaviour.

1. tests/test_operational_reports.py - the clean fixture purges patients
   together with the organisation, so the report patient is now re-created
   after the purge instead of being assumed to survive it.
2. tests/test_operational_reports.py - _queue_entry supplies the NOT NULL
   token and patient_id, so the fixture builds a row the schema permits.
3. tests/test_display_admin.py - the public display is addressed by
   organisation and branch code, not by id; the tests now call it with
   ORG_CODE/BR_CODE derived the same way the deployment's URL is.
4. tests/test_display_admin.py - the MP-45 field-visibility test seeds one
   called and one waiting patient and asserts the doctor's token is in the
   body, so "the switched-off field is absent" is asserted against a board
   that has a row, not against an empty one.
5. tests/test_tracking_tokens.py - the durable budget in
   tracking_rate_buckets is cleared per test instead of the in-process _RATE
   dict, so the limit is charged exactly as it used to be and later
   assertions no longer meet 429.

Kept separate from the T-10 collection-purity refactor that follows.

No retained log isolates these five as their own run: they rest on the 17:09
whole-tree log and on inspection, and T-10 Run A covers them.
'@
Set-Content -LiteralPath 'E:\Temp\msg_a1.txt' -Value $m1 -Encoding ascii
```

```powershell
$m2 = @'
feat(queuing): record capability and target id on both display denial paths

MD-19 requires a display-management denial to carry the actor, the capability
and the org/branch. The capability was missing from the audit row on both
_denied call sites (finding F-02, audit 27 Nov 2026).

- The refusals now write capability alongside actor_id and branch_id.
- The cross-tenant refusal keeps its non-disclosing 404 and records the
  caller's org/branch with the governing capability, identifying the target
  through target_id only (OPC-3, recorded interpretation 27 Nov 2026). The
  target's own branch is never written: that is the fact the 404 exists to
  withhold.

Status codes, response bodies and the one-row-per-denial property are
unchanged.

Verified: whole-tree run 17:09 (1,069 passed, 0 errors), which includes
tests/test_display_admin.py. The capability negative control needs a database
and is Run B of the T-10 execution plan.
'@
Set-Content -LiteralPath 'E:\Temp\msg_a2.txt' -Value $m2 -Encoding ascii

$m3 = @'
fix(frontend): pass the board's translator into the scope label

The scope label on /queue-display/[org]/[branch] was rendered with a
translator that was not in scope, so it did not resolve on the department
board (MP-38). The page now hands the board its translator and the label
resolves in both languages.

The regression test holds the component contract: a board without a
translator must not crash, and a supplied translator must reach the label.
'@
Set-Content -LiteralPath 'E:\Temp\msg_a3.txt' -Value $m3 -Encoding ascii
```

```powershell
$m4 = @'
test: stop pytest collection from writing to the database (T-10)

Seven test modules seeded rows at import time, so pytest's collection phase
connected to and wrote to whatever AMSDP_DATABASE_URL named. That made
collection a schema-mutating operation, hid the failure behind collection
succeeding anyway, and is what masked D-3: a module that wrote at import also
created rows another module's test needed, so the missing fixture never
showed.

- identity/tests/test_identity.py, queuing/tests/test_queue.py,
  tests/test_dashboard.py, tests/test_dqds.py, tests/test_patient_age.py,
  tests/test_security.py and tests/test_tracking_tokens.py move module-scope
  seeding into module-scoped autouse fixtures. Test bodies are unchanged.
- tests/test_queue_history.py carries the MP-24 queue-history coverage that
  arrived with this work and was never committed.
- tests/test_collection_purity.py is the new guard: it points pytest at an
  unreachable DSN (127.0.0.1 port 1) and requires collection to succeed
  anyway, with a second assertion that the sentinel really is unreachable.
  It fails when import-time I/O is reintroduced, which is the property worth
  having.

Suite: 1,069 -> 1,071 collected.

Verified: the guard passes (2 passed); it fails as designed against a
throwaway module that writes at import, and passes again once that module is
removed; whole-tree collection is 1,071 with 0 errors and no connection
attempt. The seven refactored modules have not been executed: that is Run A
of the T-10 execution plan and needs an authorised database.
'@
Set-Content -LiteralPath 'E:\Temp\msg_a4.txt' -Value $m4 -Encoding ascii

$m5 = @'
docs: OA-1 manifest, T-10 and OA-8/B-2 plans, reconciliation and deviation

Fifth window: the OA-1 commit manifest (proposal and final), the T-10
disposable-database execution plan, the OA-8/B-2 local-stack verification
plan, reconciliation findings RO-01..RO-10, the backend execution audit and
evidence, the database authorisation deviation record, the MP-46 capability
decision request, and the MP-46/MP-38 and D-3 implementation reports.

The execution register gains sections 20 and 21; the documentation index gains
Revision 61. No status is promoted: MP-04 stays PARTIAL, MP-46 and the
display band stay TESTED, T-10 stays IMPLEMENTED with collection-level
coverage only, D-3 stays CLOSED as a defect.
'@
Set-Content -LiteralPath 'E:\Temp\msg_a5.txt' -Value $m5 -Encoding ascii
```

**Sequence B's merged message** (only if four commits are chosen): subject
`fix: MP-46/OPC-3 denial fields and the MP-38 board translator`; body = the A‑2 and A‑3 bodies under `Backend:`
and `Frontend:` headings, with one shared `Verified:` paragraph.

---

## 13. Nothing was executed

In producing this document: **no `git add`, no `git apply --cached` against the real index, no `git commit`, no
`git push`, no `git restore`, no `git checkout`, no `git stash`.** The only writes were to `E:\Temp` (patch files
and a throwaway index, deleted) and to `docs/` (this document, three addenda, one index revision).

<!-- Written 2026-11-27, fifth window (continued). Read-only with respect to git history. -->





