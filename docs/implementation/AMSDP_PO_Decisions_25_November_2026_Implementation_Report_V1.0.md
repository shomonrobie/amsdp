# AMSDP — Product Owner Decisions Implementation Report (25 November 2026, evening window)

> **Task ID:** `AMSDP-PO-DECISIONS-2026-11-25`
> **Version:** 1.0 · **Date:** 25 November 2026
> **Status:** **IMPLEMENTED / TESTED.** Nothing in this window is `VERIFIED` or `ACCEPTED` except the
> decisions themselves, which the Product Owner took in writing (`.clinerules` §7).
> **Authority:** Product Owner authorisation of 25 November 2026 (PO-01, PO-03…PO-12, POD-11, Q-4,
> O-3) plus Q-3 and D-3 as scoped by the same brief.
> **Decision record:** `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md`

---

## 1. Initial repository state (measured before any change)

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` |
| HEAD | `a4ddc2c` — *docs(queue): record the post-teardown container count in the runbook evidence appendix* |
| Staged | **nothing** |
| Dirty entries | **99** — 48 modified, 51 untracked (the untracked count includes the whole `docs/plan/` folder) |
| Notable untracked | the migration `b2e5c7d91a04_add_schedule_blocks.py`, all `docs/plan/` documents, ~25 implementation reports |
| Uncommitted owner edits | `.clinerules` (2 lines), both Business Rules copies (the PO-13 §33 amendment, 64/3 each) |
| Stray artefact | one file at the repository root whose name is a mangled shell command and whose content is `git log` output — §9.1 |

Nothing was reset, cleaned, stashed or checked out. Every pre-existing modification and untracked file
was preserved and, where O-3 authorised it, committed **unchanged**.

---

## 2. Decisions recorded and documents updated

| Decision | Recorded in | Effect |
|---|---|---|
| **PO-01** | `product/AMSDP_Phase_Model_V1.1.md` (new) + decision record §2.1 | Phases 4/5/6 published with scope, exit criteria and accepting authority; **MP-30** defined as verification |
| **PO-03** | MVP Scope §7 annotation + Feature Catalogue §H annotation | SYM-001 ratified as approved **P1**; no code change |
| **PO-04** | Decision record §2.3, register §7.1 | MP-09 → MP-13 → MP-14 → MP-15 authorised, sequenced after the first clean rehearsal |
| **PO-05 / PO-06 / PO-07** | Decision record §2.4–§2.6, register §7.1 | MP-04, MP-26, MP-27, MP-21 deferred; the Analytics Specification recorded as **not approved** |
| **PO-08** | Decision record §2.7 | D-5 rule adopted, O-2 decided, POD-2 closed, POD-7 executed, **POD-11 = Faria Bushra** |
| **PO-09** | Limitations Report §1, Feature Catalogue §H and §H.1 (annotations) | Four dated, additive corrections; original text preserved |
| **PO-10** | `deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md` (new) | Approach approved and documented; **executed nowhere** |
| **PO-11** | Decision record §2.10 | Doctor ↔ branch contract ratified (no code, no migration) |
| **PO-12** | `plan/AMSDP_Feature_Key_Register_V1.0.md` (new) | 26 `F-nn` keys; catalogue IDs unchanged |
| **Q-4** | Commit `44f4f2f` | The §33 PO-13 amendment committed after verifying the diff is §33-only |
| **O-3** | Commits `355f93a` … `3086742` | 17 path-grouped commits, **nothing pushed** |
| **Roadmap application** | plan V1.1 **Amendment A-3** (Appendix F) | Gates closed, MP-30 defined, MP-34 re-graded, blocked set restated |

---

## 3. Documents created

| File | Why |
|---|---|
| `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` | The authoritative record: what was approved, what was not, and the three measured corrections |
| `docs/product/AMSDP_Phase_Model_V1.1.md` | PO-01's publication act (standalone, so no owner document is edited) |
| `docs/plan/AMSDP_Feature_Key_Register_V1.0.md` | PO-12's register, 26 keys, one declared gap (**R-1**) |
| `docs/deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md` | PO-10's executable plan — order, verification, rollback, B-4 read |
| `docs/implementation/AMSDP_W6_Audio_Asset_Reference_Verification_Report_V1.0.md` | POD-7's required "exact unreferenced file list" |
| `docs/implementation/AMSDP_PO_Decisions_25_November_2026_Implementation_Report_V1.0.md` | This report |
| Docs Index annex **Revision 49** | D-5's first application |

No file was moved, renamed or deleted except the one audio orphan (§5.4), which is recorded in the
verification report and recoverable from git history. **No migration-manifest entry is required.**

## 4. Commits created (path-grouped, not pushed)

| # | Commit | Group |
|---|---|---|
| 1 | `355f93a` chore(audio): remove one undeclared Bangla audio master (POD-7) | audio |
| 2 | `ab158d2` test(frontend): repair the two red harnesses (Q-3) | frontend tests |
| 3 | `0099621` feat(db): add the schedule_blocks migration (MP-16) | migration, alone |
| 4 | `44f4f2f` docs(business-rules): commit the PO-13 section 33 scope amendment (Q-4) | owner docs, §33 only |
| 5 | `55a484b` feat(backend): MP-05 to MP-29 service changes | backend code |
| 6 | `4016c6e` test(backend): MP-05 to MP-29 test coverage | backend tests |
| 7 | `94ac612` feat(frontend): MP-07 to MP-29 interface changes | frontend code |
| 8 | `010f0f3` test(frontend): MP-07 to MP-29 frontend tests | frontend tests |
| 9 | `232d103` docs(audit,architecture): audit, gap analysis and multi-display specification | docs |
| 10 | `c0fc448` docs(implementation): MP-05 to MP-33 reports and the decision pack | docs |
| 11 | `4781540` docs(queue): QUE-006 merge report and runbook corrections | docs |
| 12 | `ea0d326` docs(product,demo): phase model and the PO-03/PO-09 annotations | docs |
| 13 | `cc99116` docs(decisions): the 25 November decision record | docs |
| 14 | `43d6c81` docs(plan): roadmaps, execution register and feature-key register | docs |
| 15 | `19cc270` docs(plan): Amendment A-3 | docs |
| 16 | `808bca5` docs(deployment): PO-10 plan | docs |
| 17 | `3086742` docs(implementation): W6 audio reference verification | docs |
| 18 | *(final)* docs: this report and Docs Index Revision 49 | docs |

**Not committed, deliberately:** `.clinerules` — its two-line edit is the owner's, and Q-4 authorises
Business Rules §33 only. It remains modified in the working tree, untouched.

---

## 5. Work executed and evidence

### 5.1 Q-3 — both harnesses repaired, no expected value changed

| File | Defect found | Repair |
|---|---|---|
| `frontend/tests/banglanamesense-dataset.test.mjs` | Hashed the **raw checkout bytes**. With `core.autocrlf=true` and no `.gitattributes`, a CRLF checkout changes the digest of an identical file | Hashes and measures the **LF-canonical** form; `DATASET_SOURCE.sha256` and `.bytes` untouched |
| `frontend/tests/calendar-render.test.mjs` | Raw filesystem paths passed to `import()`, a hand-built `file://` URL, and — after those were fixed — a Windows path embedded unescaped inside the SWC-compiled source | `pathToFileURL(...).href` everywhere, including the module replacements inside the compiled component; no assertion changed |

Total diff: **25 insertions, 15 deletions across two files.** No `.gitattributes`, no product code.

### 5.2 MP-34's documentation scope — applied

| Target | What was written |
|---|---|
| Limitations Report §1 | The three false claims (in-memory, no PostgreSQL, no migrations) marked superseded, with the measured replacement facts (17 Alembic revisions) and — importantly — a statement of what is **still** limited (audibility unproven, no browser E2E, mock provider, single-engineer review) |
| Feature Catalogue §H | "Awaiting scope decisions: 0" explained: true by PO-03's decision, not by oversight |
| Feature Catalogue §H.1 | All six P0 defects re-checked against the code: **five are enforced now** (`queuing/main.py:191–203`, `:224–232`, `:297–300`, `:422–426`; `scheduling/main.py:185–193`); **QUE-005 stands** |
| MVP Scope §7 | Symptom capture ratified P1; prescriptions, diagnoses, notes and treatment plans stay out of scope |
| PO-11 | Ratified contract recorded in the decision record §2.10 |
| PO-12 | Feature-key register published |

### 5.3 PO-01 — Phase 4/5/6 published, MP-30 defined

`docs/product/AMSDP_Phase_Model_V1.1.md`: three phases with names taken from the multi-display
specification, one scope, one exit criterion and one accepting authority each; MP-30 defined as
verification of four named handoff surfaces with a stated evidence standard; **Phase 4 acquires no
clinical feature.**

### 5.4 POD-7 — verified first, then one file removed

Method: every asset path declared in `frontend/public/audio/manifest.json` compared against every file
on disk. Measured: **71 files, 70 declared, 1 undeclared, 0 declared-but-missing.** The single orphan
(`bn/phrase/room-suffix.wav`, a Bangla master with no manifest entry and no Bangla consumer) was
tracked by git and removed; 70 files remain. **The "15 unreferenced" figure is withdrawn** — it came
from a filename search, which cannot work where playback paths are composed at run time.

### 5.5 D-3 — investigated, not fixed

The identity package cannot run on this workstation: `python -m pytest backend/identity/tests/test_identity.py -q`
ends in `ERROR ... sqlalchemy.exc.OperationalError` **during collection**. Cause: the module performs
`SessionFactory()` database work at import (`test_identity.py:19–30`), so `TestDoctorLink` never
registers. No PostgreSQL listener exists on `127.0.0.1:55432` or `:5432`. **No fixture was changed** —
the original four setup errors can be neither confirmed nor denied without a database, and silencing
the module-level coupling would weaken the suite. D-3 stays **open**; its precondition is now recorded
as **B-4-class access**.

### 5.6 PO-10 — planned, not executed

`docs/deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md` records the approved order
(SSH first, then loopback binding, then verification, then the read), the rollback for each change,
and the rule that the read is read-only and stops if the revision already matches the committed head.
**No step was run.** The `:5433` LAN exposure is still open.

### 5.7 PO-08's four decisions

D-5's rule is in force and this window's annex is **Revision 49**; O-2 (no facility-level announcement
scope) is recorded; POD-2 is formally closed; POD-11 is **Faria Bushra**, with the scope of her
appointment written down (she confirms audibility and Bangla copy quality; she does not confirm that
software is correct or deployed).

---

## 6. Tests run — exact results

| Command | Result |
|---|---|
| `node --test tests/banglanamesense-dataset.test.mjs` | **9 tests, 9 pass, 0 fail** |
| `node --test tests/calendar-render.test.mjs` | **9 tests, 9 pass, 0 fail** (was a load failure) |
| `npm test` (frontend, full suite) | **466 tests, 464 pass, 0 fail, 2 skipped** |
| `python -m pytest backend/identity/tests/test_identity.py -q` | **collection ERROR** — `OperationalError`; no database on this host |
| `python -m pytest backend/tests/test_dashboard.py -q` | **collection ERROR** — same cause |
| Audio manifest comparison (node, read-only) | `71 files on disk / 70 declared / 1 undeclared / 0 missing` |

**The backend suite could not be run in this window** and no figure is claimed for it. The last
recorded green run (`979 passed`, MP-29 window) predates this window and was made against an isolated
verification database that no longer exists on this host. Nothing in this window changed backend
behaviour: the only non-documentary changes are two frontend test files and one deleted binary asset.

**The 2 skipped tests are not new** — they were skipped before this window and remain structurally
skipped; no test was skipped to make the suite green.

---

## 7. Newly unblocked work completed in this window

| Task | Grade now | Basis |
|---|---|---|
| **MP-34** (documentation) | **IMPLEMENTED** | Annotations, PO-11 note, PO-12 register, index revision. Residual: **R-1** (V2.5 family column) and **QUE-005** |
| **Q-3** | **TESTED** | 9/9 + 9/9, full suite green, no expected value changed |
| **POD-7 / W6** | **IMPLEMENTED** | Verified list + one removal |
| **PO-01's publication** | **IMPLEMENTED** | Phase model V1.1; M-8 has a definition |
| **MP-30** | **DEFINED, not started** | Its negative-path checks are executable today; closure still needs MP-25 (B-4) |

## 8. Deferred, blocked and unresolved after this window

| Item | State | What would move it |
|---|---|---|
| **B-4** live database read | **OPEN** | The PO-10 maintenance window, or a credential |
| **MP-24, MP-25, MP-35…MP-46** (≈ 20.5 engineer-days) | **BLOCKED** | B-4 |
| **PO-10 execution** | **PENDING** | A scheduled maintenance window; the plan is written |
| **MP-09, MP-13, MP-14, MP-15** | **AUTHORISED, NOT STARTED** | The first clean rehearsal |
| **MP-33** | **BLOCKED** | A push, which O-3 forbids |
| **MP-04, MP-21, MP-26, MP-27** | **DEFERRED** | New owner decisions |
| **MP-11, MP-12** | **DEFERRED** (Q-6 c) | A room-scoped numbering design |
| **D-3** | **OPEN — investigated** | A database (B-4 class) |
| **Q-1, Q-2** | **OPEN** | Owner decision; no code changed |
| **QUE-005** | **OPEN, unowned** | A task assignment — the only surviving P0 |
| **R-1** | **OPEN** | Populate the register's V2.5 family column at MP-34's next touch |
| **O-4, O-5, D-7, POD-6, POD-1/3/8/9/10** | Carried forward | As PO-08 decided |

---

## 9. Disclosures

### 9.1 A git race, and how it was corrected

Two `git` chains were issued **in parallel** in one tool call; they interleaved and produced a single
commit (`10b9f87`) containing both the MP-16 migration and the Business Rules §33 amendment, with a
message describing only the migration. It was corrected inside the same window with
`git reset --soft HEAD~1` — **un-committing only; working tree and index contents unchanged** — then
re-committed as two path groups: `0099621` and `44f4f2f`. `.clinerules` §9 forbids `reset --hard`,
`clean -fd`, `stash` and `checkout .`; none was used, nothing was lost, and no other commit was
rewritten. Every later commit was issued one chain at a time.

### 9.2 A stray artefact removed

The repository root held a file whose name was a mangled shell command
(`s -ExecutionPolicy RemoteSigned) ; (& …ScriptsActivate.ps1)`) containing 2,192 bytes of `git log`
output — the residue of a broken shell invocation in an earlier window, not project content. It was
**untracked**, matched nothing in any plan or report, and was deleted before committing. It was never
added to git, so nothing recoverable was lost.

### 9.3 Two figures in the decision pack were wrong, and are corrected on the record

| Figure | Pack said | Measured | Corrected in |
|---|---|---|---|
| Next Docs Index revision | 48 | The base index already **ended at 48**; next is **49** | Decision record §2.7, §8 |
| Unreferenced audio files | 15 | **1** | Decision record §2.7.3, W6 report §5 |

Both were fixed by applying the *approved rule*, not by reinterpreting the decision.

### 9.4 What was not done, and why

- **No live database action** (read, migrate, reseed): B-4 unresolved.
- **No push**: O-3 forbids it.
- **No `.clinerules` edit or commit**: outside Q-4's scope, so its two-line owner edit stays in the tree.
- **Only the two named test files and the frontend suite were run**, plus read-only git and node
  commands; the brief requires each task to be tested, and nothing beyond that was executed.
- **Master Feature List V2.5 was not read**, so the feature-key register's V2.5 column is left empty and
  declared as **R-1** rather than filled with invented family names.

---

## 10. Decisions still required from the Product Owner

1. **B-4** — the database access path (or the PO-10 window scheduled), which releases ≈ 20.5
   engineer-days.
2. **Q-1** and **Q-2** — both explicit, both small, both untouched here.
3. **B-1 / B-2 / B-3** — the live re-seed and the live observation acts.
4. **The first clean rehearsal** — the gate PO-04 placed in front of MP-09/13/14/15.
5. **A push decision** — without one, MP-33 cannot produce the first green CI run.
6. **QUE-005** — who owns the one surviving P0 defect.

---

## 11. Governance and skill compliance

| Requirement | Evidence |
|---|---|
| `.clinerules` §2 routing | Domains: backend/API, multi-tenant data, database/migrations, frontend, audit, deployment, documentation. Docs Index read first; governance documents loaded per row. **No skill is installed** (§5), so governance documents were used and no skill usage is claimed |
| §3 non-negotiables | No secret, token or credential written; org/branch scope untouched; tenant key stays `organization_id`; audit rows untouched; **no migration executed**; forward-only migrations only; no capability claimed that was not verified |
| §6 compliance reporting | This section, in every artefact produced |
| §7 evidence standard | `IMPLEMENTED` for documentation acts, `TESTED` for the harness repairs, `DEFINED` for MP-30. **Nothing `VERIFIED`**, nothing `ACCEPTED` except the owner's decisions |
| §9 execution boundaries | No destructive git; one soft un-commit of my own unpushed commit, disclosed; no `reset --hard`, `clean`, `stash` or `checkout .`; no server started; no live service touched |
| §11 placement | Every new document placed in an existing subject folder (`decisions/`, `product/`, `plan/`, `deployment/`, `implementation/`); no new folder invented; no document overwritten; no document deleted except the authorised audio orphan |
| §12 reading policy | Index first, then targeted documents; no large document pasted; the Blueprint and V2.5 were **not** read, and that gap is declared rather than filled |

---

## 12. Final state

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` (unchanged) |
| Commits added | **18**, path-grouped; **nothing pushed** — the remote tip is unchanged |
| Dirty entries at close | **1** — `.clinerules`, the owner's own edit, left untouched by design |
| `.md` files under `docs/` | **155** (measured), all registered in Docs Index **Revision 49** |
| Test status | Frontend **466 / 464 pass / 0 fail / 2 skipped**; backend **not runnable** here, no figure claimed |
| Live environment | **Untouched.** No migration, reseed, restart or host change |
| Exposure (`:5433`) | **Still open** — PO-10's window has not run |

*End of report.*



