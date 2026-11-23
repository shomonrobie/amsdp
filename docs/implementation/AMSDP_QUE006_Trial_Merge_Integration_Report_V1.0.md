# AMSDP — QUE-006 Trial Merge and Integration Verification Report V1.0

| Field | Value |
|---|---|
| Document | `docs/implementation/AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md` |
| Task | QUE-006 — controlled trial merge of the Windows-pushed `hackathon-mvp` into the Ubuntu working copy, on a separate trial branch, with no final merge commit, no push, no deployment |
| Ubuntu repository | `/home/shomonrobie/amsdp` |
| Windows target | `2fc007a3f7a96639c3df36341c6081cee4d24a48` (`origin/hackathon-mvp`) |
| Date | 2026-11-22 |
| Location rule applied | `.clinerules` §11 — subject subfolder `docs/implementation/`; destination filename checked before writing (no collision) |
| Evidence rule | Every claim below is tagged **VERIFIED**, **TESTED**, **IMPLEMENTED**, **NOT VERIFIED**, **BLOCKED** or **REQUIRES PRODUCT OWNER DECISION**. A green suite is not acceptance, and static inspection is never reported as execution |
| Outcome in one line | The two histories unify mechanically with **7 textual conflicts**; the trial tree **builds** and passes **332/341** frontend and **738/763** backend tests; the migration graph needed one documented reparent (now proven on a disposable PostgreSQL); the merged feature set is **not** acceptable yet, because the lineages disagree on the *outcome vocabulary* and on **room announcements**, and 34 tests still fail (attribution in §9.3 and §10.1) |

---

## 1. Executive summary

1. **The histories unify safely.** Merge base `37cf3d1`; the Windows side is four commits (`87eceea`, `9812361`, `8cc2024`, `2fc007a`); the Ubuntu side is three (`0554f33`, `cd2f9ec`, plus this task's preservation snapshot `41ac51a`). The committed change sets overlap on **8 files** and produce **7 textual conflicts**; everything else — including all **175 remote files** and every Ubuntu addition — merged without a conflict, and nothing was deleted by the merge.
2. **The real conflict is semantic, not textual.** The Windows lineage (W1/W2/W3) is a *pre-recorded audio* engine with a server-side delivery claim; the Ubuntu lineage (F1–F4) is a set of corrections inside the *browser speech-synthesis* mechanism. Three of the five Ubuntu findings are already satisfied or superseded by the Windows implementation; **F1's honourific is forbidden by an approved product decision**, **F3's per-tab store is superseded for cross-terminal identity but is not integrated**, and **F4's room snapshot survives only as a payload field**.
3. **A real, merge-only defect was found and fixed in the trial tree.** The lineages use different literals for the same six terminal outcomes (`completed` vs `spoken`, `interrupted` vs `cancelled`). Before the fix the delivery classifier recorded a **confirmed playback as `failed`/`status_completed`** — a lost delivery, contradicting the approved rule that only a completed playback counts as delivered. The trial tree now accepts both spellings; the *canonical* spelling stays a Product Owner decision (**D-6**).
4. **The migration graph is broken as pushed, and the fix is proven, not assumed.** `a7c3f19d2b64` declared `Revises: f8a2b3c4d5e6` — an *ancestor* of the current head `a9c4e1f7b2d8` — creating **two heads**. Verified at runtime: `alembic upgrade head` fails with "Multiple head revisions are present". After the reparent to `a9c4e1f7b2d8`, a restored backup in a disposable PostgreSQL 17 container upgraded `f7d2b4c6e8a1 → … → a9c4e1f7b2d8 → a7c3f19d2b64 → c4d8e2a91f60` with **one head**, **three new tables**, and **every row count unchanged** (60 organisations, 85 appointments, 6 queue entries, 4,645 audit events, 596 staff users).
5. **Test evidence.** Frontend: **341 tests, 332 pass, 9 fail, 0 skipped**. Backend (real PostgreSQL, disposable container): **763 tests, 738 pass, 25 fail**. All **25** backend failures reproduce on the **pure remote branch** with no Ubuntu content present, so they are **pre-existing Windows-lineage defects, not merge regressions** (§9.3). The nine frontend failures are the vocabulary collision of item 3 above and are enumerated individually (§10.1).
6. **Not verified and not claimed.** No browser, no audible playback, no two-terminal claim, no permission walk-through, no deployment of the trial tree. The live application and the live database were never touched (§12).
7. **Not ready for acceptance.** The trial merge is a usable base for acceptance review once **D-1…D-7** are answered; it is not deployable now and must not be committed as a merge commit before those decisions.

---

## 2. Starting Git state (Phase A)

Recorded before any Git state change (`/tmp/que006_trial/A1_state.txt`).

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` |
| HEAD | `cd2f9ecdf51b363105214e3ffd504d3adc151ada` — *docs: add AMSDP website content and copywriting proposal* |
| Remote | `origin` = `git@github.com:shomonrobie/amsdp.git` |
| Remote branch SHA at start | tracking ref stale at `37cf3d1`; `git ls-remote origin refs/heads/hackathon-mvp` returned `2fc007a3f7a96639c3df36341c6081cee4d24a48` |
| Local commits ahead | 2 (`0554f33`, `cd2f9ec`) — both only add `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` |
| Working tree | **13 modified + 10 untracked** (23 entries; no stashes, no tags) |
| `.gitignore` delta | one line, `.aider*` (local tooling, unrelated to QUE-006) |

### 2.1 Provenance of every preserved file

The task forbids treating Ubuntu untracked files as F1–F4 work by default, and the Product Owner has stated that some untracked files were created by Windows Cline. Each entry was inspected — header, cited HEAD, timestamp, content — not assumed.

| File (23) | Δ | Observed provenance |
|---|---|---|
| `backend/queuing/main.py` | M +57/−5 | Ubuntu F4 — room snapshot resolver wired into `_entry_to_dict` |
| `backend/appointment/main.py` | M +9/−3 | Ubuntu F4 — location snapshot exposure |
| `backend/queuing/recovery.py` | M +12/−7 | Ubuntu F1–F4 — recovery payload |
| `frontend/lib/announcements/content.js` | M +150/−26 | Ubuntu F1 — approved wording + honourific slot |
| `frontend/lib/announcements/controller.js` | M +80/−19 | Ubuntu F2/F3 — terminal-outcome honesty, per-event store |
| `frontend/lib/announcements/speech-synthesis.js` | M +88/−36 | Ubuntu F2 — six-word terminal vocabulary, `completed` only on `end` |
| `frontend/pages/queue.js` | M +5/−2 | Ubuntu F4 — `room_name` reaches the announcement |
| `frontend/tests/queue-announcement-{content,controller,speech,boundary}.test.mjs` | M | Ubuntu F1–F4 assertions (the boundary file also carries the F4 room assertion) |
| `backend/common/locations.py` | A 67 lines | Ubuntu F4 — `room_payload` / `location_label`, no DB access |
| `backend/tests/test_queue_room_snapshot.py` | A 365 lines | Ubuntu F4 test |
| `frontend/lib/announcements/dedupe.js` | A 273 lines | Ubuntu F3 — bounded per-event store |
| `frontend/tests/queue-announcement-dedupe.test.mjs` | A 183 lines | Ubuntu F3 test |
| `docs/implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md` | A | Ubuntu agent report (self-declares IMPLEMENTED/TESTED, NOT VERIFIED) |
| `docs/implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` | A | Ubuntu agent report, 2026-11-22 |
| `docs/implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md` | A | Ubuntu agent report, 2026-11-22 |
| `docs/implementation/AMSDP_Windows_Commit_Seven_File_Compatibility_Assessment_V1.0.md` | A | Ubuntu agent report, 2026-11-22 |
| `docs/architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md` | A 2,134 lines | **Provenance not provable from Git.** Content declares READ-ONLY design at HEAD `37cf3d1` with a clean tree; it is the plan of record the Ubuntu F1–F4 report cites. Consistent with either lineage, and a candidate under the Product Owner's Windows-Cline statement. Documented, not adjudicated |
| `docs/chatgpt/AMSDP_Project_Handover_2026-11-20.md` | A 530 lines | **Provenance not provable from Git.** A ChatGPT↔Cline handover dated 2026-11-20; its sibling `…2026-11-12.md` is kept in the same folder |
| `.gitignore` | M | Local tooling (`.aider*`) |

**No collision** was found between any untracked path and the remote tree (`git cat-file -e origin/hackathon-mvp:<path>` for all ten), so the snapshot cannot have masked a remote file.

---

## 3. Preservation and backup evidence

All artefacts are **outside** the repository, in `/home/shomonrobie/amsdp_preservation_20261122/`.

| Artefact | Verification |
|---|---|
| `00_branch_and_head.txt` | `wip/que006-ubuntu-preservation` @ `cd2f9ec…` (branch created from the pre-merge HEAD, dirty tree carried over unchanged — `git status` byte-identical before and after) |
| `01_tracked-modifications.patch` (90,278 B) | `git diff` of the 13 modified files; **re-applies cleanly** to a pristine `cd2f9ec` worktree (`git apply --check` → `PATCH-APPLIES-CLEANLY`) |
| `02_file-inventory.txt` | exactly the 23 paths (13 modified + 10 untracked) |
| `03_worktree-files.tar.gz` (240,517 B) | archive of all 23 files; extracted into a scratch directory and **23/23 `sha256sum -c` → OK** |
| `04_sha256-source.txt`, `05_sha256-artifacts.txt` | per-file and per-artefact digests |
| `06_amsdp-local.bundle` (3,297,706 B) | `git bundle verify` → **`okay`**; "The bundle contains these 2 refs" (`hackathon-mvp` = `cd2f9ec`, `wip/que006-ubuntu-preservation` = `41ac51a`); "The bundle records a complete history" |

The WIP branch carries one snapshot commit rather than a dirty tree:

`41ac51a wip(queue): preservation snapshot of the Ubuntu working tree (pre QUE-006 trial merge)` — 23 files, **+6,581 / −154**, working tree clean afterwards. Its message records each file's observed provenance and the external backup path. It is a **preservation** act: no content was altered, nothing was staged that had not been inspected, and it is not pushed.

**The user's own work is preserved:** `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` and both of its commits (`0554f33`, `cd2f9ec`) are ancestors of the trial branch, and the merge does not touch that file (§4.3).

**Gate A: PASSED** — preservation verified before any merge attempt.

---

## 4. Actual Git topology (Phase B)

`git fetch origin` was the only state-changing command; it does not touch the working tree.

```
   37cf3d1..2fc007a  hackathon-mvp -> origin/hackathon-mvp
```

| Fact | Value | How established |
|---|---|---|
| Remote target | `2fc007a3f7a96639c3df36341c6081cee4d24a48` | `git rev-parse origin/hackathon-mvp` = expected SHA → `SHA-MATCH-EXPECTED` |
| Merge base | `37cf3d1e9db76834044afd48fa5729463a26ec47` | `git merge-base HEAD origin/hackathon-mvp` |
| Local-only commits | **3** | `git rev-list --count origin/hackathon-mvp..HEAD` |
| Remote-only commits | **4** | `git rev-list --count HEAD..origin/hackathon-mvp` |
| Website proposal commits preserved | `0554f33`, `cd2f9ec` | `git log --all -- frontend/public/WEBSITE_CONTENT_PROPOSAL.md` |

**Remote-only commits (oldest first):**

| Commit | Subject |
|---|---|
| `87eceea` | feat(queue): QUE-006 W1/W2 pre-recorded playback engine, call control and reliability |
| `9812361` | feat(organization): QUE-006 W3 server-side voice configuration and versioned pack library |
| `8cc2024` | chore(audio): QUE-006 announcement audio assets, standardisation and generation tooling |
| `2fc007a` | docs(queue): QUE-006 workstream reports and documentation index registration |

**Local-only commits:** `0554f33`, `cd2f9ec` (documentation only) and `41ac51a` (this task's preservation snapshot).

### 4.1 Scale of the two sides

| Side | Files touched vs `37cf3d1` | Composition |
|---|---:|---|
| Remote (`2fc007a`) | **175** | 72 audio assets under `frontend/public/audio/`, 45 tooling files under `scripts/`, 58 source/docs files (2 migrations, 6 backend modules, 4 backend tests, 9 frontend modules, 9 frontend test files, 20 QUE-006 reports, index) |
| Local (`41ac51a`) | **23** | 13 modified + 10 untracked; 4 announcement tests, 4 announcement modules, 1 new backend module, 1 new backend test, 8 documents |

### 4.2 Files changed on **both** committed sides

Eight, established by intersecting `git diff --name-only 37cf3d1 origin/hackathon-mvp` with `git diff --name-only 37cf3d1 HEAD` under `LC_ALL=C`:

1. `.gitignore`
2. `backend/queuing/main.py`
3. `docs/governance/AMSDP_Docs_Index_V1.0.md`
4. `frontend/lib/announcements/content.js`
5. `frontend/lib/announcements/controller.js`
6. `frontend/pages/queue.js`
7. `frontend/tests/queue-announcement-content.test.mjs`
8. `frontend/tests/queue-announcement-controller.test.mjs`

Two files the earlier analysis expected to conflict **do not**:

* `frontend/lib/announcements/speech-synthesis.js` — only the Ubuntu side changed it; it merged without conflict (and is precisely where the vocabulary collision lives, §9).
* `frontend/tests/queue-announcements-boundary.test.mjs` — the remote never touched it, so the boundary assertions survive the merge intact and only *run* against W2's page code. That is why C-1 surfaces as a **test result**, not a textual conflict (§9).

**Gate B: PASSED** — no contradiction with the previous analysis, but two corrections to it are recorded above, and the remote change set is far larger (175 files) than the "seven changed files" framing implied.

---

## 5. The trial merge (Phase C)

Branch created from the preserved Ubuntu state, then merged with no commit:

```
git switch -c trial/que006-windows-ubuntu-merge      # from 41ac51a
git merge --no-ff --no-commit origin/hackathon-mvp   # exit 1, conflicts present
```

| Fact | Value |
|---|---|
| Trial branch | `trial/que006-windows-ubuntu-merge` |
| Branch head | `41ac51a` (the preservation snapshot) — **no merge commit exists** |
| `MERGE_HEAD` | `2fc007a3f7a96639c3df36341c6081cee4d24a48` |
| Merge base of the two parents | `37cf3d1` |
| Result | 7 `UU` conflicts; everything else auto-merged |
| Deletions introduced by the merge | none |

**Ancestry as it stands:** `41ac51a` (→ `cd2f9ec` → `0554f33` → `37cf3d1`) with `2fc007a` staged as the second parent in `MERGE_HEAD`. Git would create a merge commit whose parents are exactly `41ac51a` and `2fc007a`; the task forbids creating it, so the **index**, not a commit, holds the result.

### 5.1 Auto-merged without conflict — 168 of 175 remote changes

* **All 162 remote additions**, including `backend/queuing/events.py`, `backend/queuing/announcements.py`, `backend/organization/{voice_pack_policy,voice_packs,announcement_config}.py`, both migrations, 72 audio assets plus `frontend/public/audio/manifest.json`, the 9 new frontend announcement modules, 9 new frontend test files, all 45 `scripts/` files and 20 QUE-006 reports.
* **6 of the 13 files both sides modified** merged cleanly: `.gitignore`, `backend/common/models.py`, `backend/organization/main.py`, `backend/queuing/tests/test_queue.py`, `frontend/components/queue/QueueAnnouncements.js`, `frontend/lib/i18n.js`.
* **All 10 Ubuntu additions and 6 of its 13 modifications** merged cleanly: `backend/common/locations.py`, `backend/tests/test_queue_room_snapshot.py`, `frontend/lib/announcements/dedupe.js`, its test, the four reports, `backend/appointment/main.py`, `backend/queuing/recovery.py`, `frontend/lib/announcements/speech-synthesis.js`, `queue-announcement-speech.test.mjs`, `queue-announcements-boundary.test.mjs`, `.gitignore`.
* `frontend/public/WEBSITE_CONTENT_PROPOSAL.md` — untouched by the merge, as expected.

### 5.2 The complete conflict list — 7 files

| # | File | Conflict shape | Both sides' purpose |
|---|---|---|---|
| 1 | `backend/queuing/main.py` | 2 hunks: `_entry_to_dict` signature; helper block | Ubuntu F4 adds a batched room-snapshot resolver and four room fields; Windows W2 adds a call-event identity derived from `status_history` and three `call_event_*` fields |
| 2 | `docs/governance/AMSDP_Docs_Index_V1.0.md` | 2 hunks: header snapshot paragraph; registration rows | Ubuntu Revisions **36–37** register six local documents; Windows occupies Revisions **36–48** for 20 QUE-006 reports |
| 3 | `frontend/lib/announcements/content.js` | 6 hunks | Ubuntu F1 adds an honourific slot and a wording template; Windows removes doctor identity entirely and adds room/no-room templates |
| 4 | `frontend/lib/announcements/controller.js` | 4 hunks | Ubuntu F2/F3 add the six-word terminal vocabulary and a bounded per-event store; Windows adds the pre-recorded transport, pack capability and the claim/play/report seam |
| 5 | `frontend/pages/queue.js` | 1 hunk | Ubuntu F4 passes `room: entry.room_name` and `doctorName`; Windows removes the doctor name and passes the stale `room: entry.room` |
| 6 | `frontend/tests/queue-announcement-content.test.mjs` | 10 hunks | Assertions for each lineage's wording rules |
| 7 | `frontend/tests/queue-announcement-controller.test.mjs` | 1 hunk | Assertions for each lineage's controller contract |

`.gitignore` was also changed on both sides and auto-merged (Ubuntu's `.aider*` line plus the Windows additions) — no conflict, no content lost.

---

## 6. Resolution summary, per conflict (Phase D)

Rule applied to every conflict: **Windows W2/W3 is the structural baseline** (it is the committed, product-visible architecture), **Ubuntu behaviour is preserved where it is additive and compatible**, and **nothing that contradicts an approved product decision is carried over**. No conflict was resolved by weakening a test.

| # | File | Resolution | Preserved / superseded | Tag |
|---|---|---|---|---|
| 1 | `backend/queuing/main.py` | **Union.** Kept F4's `_rooms_for` / `_room_for_entry` and the four room fields; added W2's `current_call_event` identity plus `call_event_id` / `call_event_at` / `call_count`; both import blocks retained (`room_payload`, `.events`, `.announcements` router) | Both features intact and independent; a trial-merge note in the function says so. 0 markers, `py_compile` OK | **VERIFIED** (compiles, both import sets present) |
| 2 | `docs/governance/AMSDP_Docs_Index_V1.0.md` | **Committed index as base (Revisions 1–48) plus an appended, explicitly unnumbered "Trial-merge annex"** recording the unmerged Ubuntu Revisions 36–37 and the four still-unregistered Ubuntu documents | No entry discarded, no number invented; the 36–37 vs 36–48 collision is stated as open item **D-5** | **IMPLEMENTED**; numbering is **REQUIRES PRODUCT OWNER DECISION (D-5)** |
| 3 | `frontend/lib/announcements/content.js` | **Windows version.** Ubuntu's honourific slot is **not** carried over | Superseded by the approved rule that doctor names and honourifics must never appear. The approved EN/BN wording (including "please proceed to Room …") is present in the Windows templates, so F1's *wording* intent survives and its *honourific* intent is forbidden | **TESTED** (content suite) |
| 4 | `frontend/lib/announcements/controller.js` | **Windows version** (pre-recorded transport, claim/play/report), with the Ubuntu vocabulary kept where it actually lives — `speech-synthesis.js` | F2's "completed only on `end`" survives *by value* through the compatibility aliases (`SPOKEN: 'completed'`), which is why the module composes at all. **F3's per-event store is not integrated**: `dedupe.js` and its test are retained and pass standalone, but the controller still uses a single-slot window. W2's server claim supersedes per-tab dedupe for cross-terminal identity, not for intra-tab retry semantics → **D-3** | **TESTED**; F3 integration **REQUIRES PRODUCT OWNER DECISION (D-3)** |
| 5 | `frontend/pages/queue.js` | **Windows version**, with F4's payload field restored: `room: entry.room_name` instead of the stale `room: entry.room`, and `doctorName` dropped | F4's intent (read the booking snapshot the payload actually carries) preserved; doctor identity removed per the approved rule. **Whether a room is ever spoken is D-4**, and the in-file comment says so at that line | **TESTED** (boundary suite asserts both halves) |
| 6 | `frontend/tests/queue-announcement-content.test.mjs` | **Windows version** | Pins the approved wording of the adopted baseline; Ubuntu's F1 assertions (honourific) are superseded by an approved decision, not deleted — they remain in `wip/que006-ubuntu-preservation` and in the external backup | **TESTED** |
| 7 | `frontend/tests/queue-announcement-controller.test.mjs` | **Windows version** | Pins the adopted controller contract; Ubuntu's F2/F3 assertions remain on the WIP branch, and the F2 vocabulary is still exercised by the merged `queue-announcement-speech.test.mjs` — **19 tests, 19 pass, 0 fail** when run alone | **TESTED** |

### 6.1 Seam repairs applied in the trial tree (beyond textual resolution)

Two edits were needed because each lineage is internally consistent but inconsistent with the other. Both are **additive**, documented in-file, and neither changes a test expectation.

| ID | Edit | Why it is required (not optional) | Effect |
|---|---|---|---|
| **INT-1** | `frontend/lib/announcements/delivery.js` — `classifyAnnouncement` accepts `completed` and `interrupted` as well as `spoken` and `cancelled` | Before the edit, a **confirmed** playback (status `completed`) fell through to `default` and was recorded as `failed`/`status_completed`: a lost delivery record, contradicting the approved rule that only a successful completed playback counts as delivered | "the claim, the clip and the record happen in that order" now passes; no other test changed state (10 failures before, 9 after) |
| **INT-2** | `backend/alembic/versions/a7c3f19d2b64…py` — `down_revision` reparented `f8a2b3c4d5e6 → a9c4e1f7b2d8`, correction documented in the module docstring | Without it the graph has two heads and `alembic upgrade head` **fails** (§11). The DDL is untouched | One head (`c4d8e2a91f60`); the full upgrade proven on a restored backup |

### 6.2 Files retained from each lineage

* **Windows lineage (structural baseline):** the pre-recorded engine (`prerecorded-audio.js`, `segments.js`, `voice-packs.js`, `delivery.js`, `call-announcer.js`, `queue-transitions.js`, `lib/queue/*`), the server side (`events.py`, `announcements.py`, both migrations, `models.py` additions, the three organisation modules), the audio catalogue (72 assets + manifest), the 45 tooling scripts, all 20 QUE-006 reports, and the four conflicted frontend files.
* **Ubuntu lineage:** the F4 room snapshot (`common/locations.py`, `_rooms_for` / `_room_for_entry`, the four payload fields, the boundary test's room assertion), F2's six-word terminal vocabulary and the merged run of `speech-synthesis.js`, the F3 store and its test (retained, not integrated), the four announcement tests the merge did not conflict on, the `appointment/main.py` and `recovery.py` deltas, six documents, and the user's website-proposal commits.

---

## 7. Special issue C-1 — the click path, the boundary test and the delivery claim

The task states the conflict as "the boundary test prohibits API calls from the announcement click path, while W2 introduces server-side delivery claims". Inspecting the merged tree, the conflict is **real but narrower than that framing**, and the correction matters for the decision.

### 7.1 What the merged code actually does (read from the trial tree)

| Path | Trigger | Network writes | Evidence |
|---|---|---|---|
| **Operator click** — `announceEntry(entry)` | the "Announce" button | **none**: it calls `announcements.announce(…, {source: 'operator', userGesture: true})` and nothing else | merged `frontend/pages/queue.js`; the body contains no `apiFetch` and no queue PATCH |
| **Automatic** — `announceOnCall(entry)` | a `waiting → called` transition | **two** POSTs: `POST /api/v1/queue/{id}/announcement` (claim), then `POST /api/v1/queue/announcements/{delivery_id}/outcome` | `call-announcer.js` → `delivery.js` |

So W2 does **not** place a claim on the click path; it places the claim on the *transition* path. The claim inserts a row in `queue_announcement_deliveries` and never modifies `queue_entries`, so "audio never writes queue state" still holds.

### 7.2 Why the boundary test still passes — and what that does and does not prove

`frontend/tests/queue-announcements-boundary.test.mjs` (Ubuntu, unmodified by the merge, **6 tests**) asserts on the *text* of the `announceEntry` body: no `apiFetch`, no `queue/`, plus `source: 'operator'` and `userGesture: true`. All six pass in the trial tree.

That guarantee is **weaker than it looks**: a string search over one function body cannot see an API call reached indirectly (for example via `callAnnouncer.announceCall`). It is true today that the click path makes no call — established by reading the merged `queue.js`, not by the test. The test was neither weakened nor strengthened in this task; strengthening it would be a separate, PO-visible change.

### 7.3 Options and consequences — **REQUIRES PRODUCT OWNER DECISION (D-7)**

| Option | What it means | Consequence |
|---|---|---|
| **A. Keep the merged state** (trial default) | The click path stays API-free; the automatic path claims and records | Boundary test unchanged and passing; cross-terminal duplicate protection intact; a manual repeat produces **no** delivery record |
| **B. Claim on the click path too** | Operator repeats also create/refresh a delivery record | Fuller audit ("who announced this, twice"), but it *does* put a network write on the click path, so the boundary test as written must be revised — a PO-visible change to a governance test, not a trial-merge act |
| **C. Remove the claim from the automatic path** | No server-side ownership, no delivery row | Restores the strictest reading of the boundary but deletes W2's cross-terminal protection and POD-4's delivery record — a capability regression the approved scope does not sanction |

**Trial stance:** option **A** is implemented and tested. Nothing in the boundary test was weakened, and the decision stays open.

### 7.4 Integration defect found while investigating C-1 (reported, not fixed — needs D-4)

`call-announcer.js` passes `room: entry.room`, while `pages/queue.js` (operator path) passes `room: entry.room_name`. The queue payload has never carried `room`; since F4 it carries `room_name`. **INT-3:** therefore an automatic announcement can never speak a room while an operator announcement can, for the same event. Making them consistent either way (both `room_name`, or both room-less) is a product decision about room announcements (**D-4**), so the inconsistency is reported rather than silently patched.

---

## 8. Product decisions still outstanding

Nothing below was decided by this task. Each item names the exact place it bites.

| ID | Decision | Why it cannot be taken here | Current trial state |
|---|---|---|---|
| **D-1** | Confirm the Windows W1/W2/W3 implementation as the structural baseline, with Ubuntu behaviour ported onto it | The task fixes the *technique* ("use W2/W3 as the structural baseline"); authority over the resulting feature set is the Product Owner's | Applied as instructed |
| **D-2** | Close Ubuntu finding **F1** as *withdrawn* (honourific must never be spoken) | The approved rule already forbids doctor names/honourifics, but F1 remains an open finding in the Ubuntu report | Honourific **not** carried over (§6 row 3) |
| **D-3** | **F3**: integrate the bounded per-event store into the W2 controller, or retire `dedupe.js` and its test | Both are defensible: W2's server claim covers cross-terminal identity, but not the intra-tab retry/exhaustion semantics F3 modelled | `dedupe.js` retained and passing standalone; **not** wired into the controller |
| **D-4** | **Room announcements**: speak the appointment snapshot, or defer them | "Room announcements require separate review" — and the code is currently split (operator path reads `room_name`; automatic path reads a field that does not exist: INT-3) | Operator path carries the room; automatic path does not |
| **D-5** | **Index numbering**: reconcile Ubuntu Revisions 36–37 with Windows Revisions 36–48, and confirm 48 is the true head | Renumbering is the index owner's act; inventing numbers is forbidden | Annex appended, no number claimed |
| **D-6** | **Canonical outcome vocabulary**: `completed`/`interrupted`/`unavailable` (F2, plan §8.2) or `spoken`/`cancelled`/`unsupported` (W2/OD-1 contract) | The lineages ship different literals for the same six terminal words; the choice changes the persisted delivery outcomes and nine test expectations | Both accepted at the delivery seam (INT-1); the core keeps F2's vocabulary because the approved rule speaks of a *completed* playback |
| **D-7** | Whether a **manual repeat** must create a delivery record (§7.3) | It trades audit completeness against the boundary test's core promise | Option A: the click path performs no network write |

**Not a decision but a defect to schedule:** `backend/organization/voice_packs.py:504` raises `TypeError: object of type 'int' has no len()` (`len(result['assets'])` where `assets` is a count) on the voice-pack upload path, failing 13 W3 API tests — pre-existing, reproduced on the pure remote branch (§9.3).

---

## 9. Backend test results (Phase F)

**Environment (isolated, never the live database):** disposable `postgres:17` container `que006-trial-pg` bound to `127.0.0.1:55432`; database `amsdp_tests` created empty and migrated with the corrected chain; `AMSDP_DATABASE_URL` pointed at it for the whole run; pytest 9.2.0 / Python 3.14.4 from the repository `.venv`. No command in this task addressed the live database (port 5433) or any live container.

```
.venv/bin/python -m pytest backend -q -p no:cacheprovider
# AMSDP_DATABASE_URL=postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_tests
```

| Metric | Count |
|---|---:|
| Collected / executed | **763** |
| Passed | **738** |
| Failed | **25** |
| Skipped | 0 |
| Not executed | none — the whole suite ran |
| Duration | 1215.60 s (20 min 15 s) |

### 9.1 Where the 25 failures are

| Module | Failures | Character |
|---|---:|---|
| `backend/doctor/tests/test_doctor.py` | 9 | Fixture/state collision: doctor create returns `409 "a doctor with this mobile number already exists"`, and dependent read/update tests then fail with `KeyError: 'id'` |
| `backend/organization/tests/test_voice_packs_api.py` | 13 | **Genuine code defect** in W3: `voice_packs.py:504` `len(result['assets'])` → `TypeError: object of type 'int' has no len()` |
| `backend/queuing/tests/test_queue.py` | 3 | `NameError: name 'after' is not defined` in a W2 test; `qce:…:0` vs `:1` identity expectation; `assert 1 == 0` over `status_history` |

### 9.2 What the merge itself did **not** break

The tests that the merge had to reconcile, all **passing** in the trial tree:

* `backend/tests/test_queue_room_snapshot.py` (Ubuntu F4) — the union of `_entry_to_dict` kept the room snapshot working.
* `backend/queuing/tests/test_queue_events.py` (W2 server event identity) — passes.
* `backend/organization/tests/test_voice_pack_policy.py` (W3 policy layer, 49 tests) — passes.
* Every queue call/claim/outcome test other than the three listed above — passes.

### 9.3 Attribution — merge regressions or pre-existing? **Pre-existing, with evidence**

The same three modules were also run against a **pristine `origin/hackathon-mvp` worktree** (`/tmp/que006_trial/wt-remote`, containing no Ubuntu content whatsoever) on a second empty migrated database:

| Run | Tests | Failed | Passed |
|---|---:|---:|---:|
| Pure remote branch, three modules | 110 | **29** | 81 |
| Trial merge, full suite (same three modules) | 763 total | **25** (9 + 13 + 3) | 738 |

* Every one of the trial's 25 failures appears **in the pure-remote failure set**: the 13 `organization` failures identical, 9 of the 10 `doctor` failures, 3 of the 6 `queuing` failures.
* The pure-remote subset run has *more* failures than the full trial run because a subset seeds less reference data: the difference is test-isolation state, not merge damage.
* Conclusion: **all 25 backend failures are pre-existing Windows-lineage defects or test-isolation defects. None is a merge regression** — but a failing suite is still not evidence of a working feature, so they remain acceptance blockers.

### 9.4 Import and route check of the merged backend (no database contact)

With a deliberately dead DSN (`postgresql+psycopg2://dead@127.0.0.1:59999/none`) so that an accidental connection attempt would fail rather than reach anything:

* `py_compile` of `backend/queuing/main.py`, `backend/common/models.py`, `backend/common/locations.py`, `backend/organization/main.py`, `backend/queuing/events.py`, `backend/queuing/announcements.py` and both migrations → **PYCOMPILE-OK**.
* `import queuing.main` **succeeds**; the app exposes the display, recovery and announcements routers plus its six queue routes.
* The announcements router carries exactly the two endpoints the frontend calls: `/api/v1/queue/{entry_id}/announcement` and `/api/v1/queue/announcements/{delivery_id}/outcome`. (A first probe reported them missing; that was a probe artefact — this FastAPI version wraps included routers in `_IncludedRouter`, which has no `.path`. The router's own route table was then read directly.)

---

## 10. Frontend test results and build (Phase F)

```
cd frontend && npm test      # node --test tests/*.test.mjs, Node v24.21.0
```

| Metric | Count |
|---|---:|
| Tests | **341** |
| Passed | **332** |
| Failed | **9** |
| Skipped / cancelled / todo | 0 / 0 / 0 |
| Duration | 8.07 s |

### 10.1 The nine failures, individually

All nine are `strictEqual` assertions on the *literal* value of a terminal outcome — the D-6 contract collision. None is a logic failure, and none was relaxed or removed.

| File (line) | Test | Expected | Actual |
|---|---|---|---|
| `queue-announcement-controller.test.mjs:65` | an unsupported browser is reported, not thrown | `'unsupported'` | `'unavailable'` |
| `queue-announcement-controller.test.mjs:116` | a blocked browser is not hammered, but a new gesture may recover it | `'spoken'` | `'completed'` |
| `queue-announcement-controller.test.mjs:143` | activating audio is a gesture, and reports what the browser did | `'spoken'` | `'completed'` |
| `queue-announcement-controller.test.mjs:172` | an exploding engine is an error outcome, not an exception | `'error'` | `'failed'` |
| `queue-announcement-w2-integration.test.mjs:61` | W2 prerecorded is the default transport when a player is supplied | `'spoken'` | `'completed'` |
| `queue-announcement-w2-integration.test.mjs:88` | W2 busy and cancelled are passed through unchanged | `'cancelled'` | `'interrupted'` |
| `queue-announcement-w2-integration.test.mjs:97` | W2 a blocked browser is not hammered without a fresh gesture | `'spoken'` | `'completed'` |
| `queue-announcement-w2-integration.test.mjs:158` | W2 capability follows the pack, not the browser voice list | `'spoken'` | `'completed'` |
| `queue-announcement-w2-integration.test.mjs:188` | W2 end to end: spoken is reported only when the final clip ends | `'spoken'` | `'completed'` |

**Reading:** the behaviour each test describes still happens (the browser's refusal is reported, the recovery works, the pack decides capability, only the final clip's `end` yields a success). What differs is the spelling of the word. Two ways out, both one-line, both PO decisions (**D-6**): give the aliases their old values in `speech-synthesis.js` (`SPOKEN: 'spoken'`, `CANCELLED: 'cancelled'`, `UNSUPPORTED: 'unsupported'`, `ERROR: 'error'`), or update these nine expectations to F2's vocabulary. Neither was done here.

### 10.2 Suites that pass, including everything the merge had to reconcile

`queue-announcements-boundary.test.mjs` — **6 tests, 6 pass** (incl. the F4 room assertion and the no-API-on-click assertion) · `queue-announcement-speech.test.mjs` — **19/19** · `queue-announcement-content.test.mjs` (Windows wording), `queue-announcement-prerecorded.test.mjs`, `queue-announcement-segments.test.mjs`, `queue-announcement-voice-packs.test.mjs`, `queue-announcement-delivery.test.mjs`, `queue-announcement-dedupe.test.mjs` (Ubuntu F3 store, standalone), `queue-call-control.test.mjs`, `queue-refresh-safety.test.mjs`, `bangla-*`, and the rest of the 341.

### 10.3 A pre-existing defect in the remote's own test file (reported, not fixed)

`frontend/tests/queue-announcement-delivery.test.mjs` never closes the `test('W2 only a fresh call event may be announced automatically', …)` call — the next `test(...)` at line 179 is nested inside it. Consequence: one failure can fail two tests, which is exactly what happened when INT-1 was trialled too broadly (11 failures instead of 10, then 9 after the correct minimal fix). This is a defect in the committed Windows test file, untouched by the merge; it makes the suite's failure counts less reliable than they look.

### 10.4 Production build

```
cd frontend && npm run build      # next 14, Node v24.21.0
```

**Result: `✓ Compiled successfully`**, with the full route table emitted (static and dynamic routes, first-load JS 97.9 kB shared). No TypeScript or ESLint error, no missing module. The build ran **only** on the trial tree; the live `amsdp-frontend-1` container was not rebuilt (§12).

---

## 11. Migration investigation (Phase E)

### 11.1 The graph as pushed

`backend/alembic/versions` holds **16 revisions**. Reading every `revision` / `down_revision` pair, and then confirming with the Windows lineage's own checker (`scripts/que-006-w3-voice-config/check_migration_graph.py`):

```
16 revisions in backend/alembic/versions
heads: a9c4e1f7b2d8, c4d8e2a91f60
  c4d8e2a91f60 <- a7c3f19d2b64 <- f8a2b3c4d5e6 <- f8a1b2c3d4e5 <- e6c1a9b3d5f8 <- …
  a9c4e1f7b2d8 <- b3d7e91f6a24 <- f7d2b4c6e8a1 <- e6c1a9b3d5f8 <- …
if a7c3f19d2b64 is reparented to a9c4e1f7b2d8, heads: c4d8e2a91f60  <-- single head
```

`a9c4e1f7b2d8` is a **merge revision** (its `down_revision` is a tuple, `('b3d7e91f6a24', …)`), so `f8a2b3c4d5e6` is already one of its ancestors. Declaring `Revises: f8a2b3c4d5e6` on the W2 migration therefore branches off *below* the current head and creates a second head. That is the known issue in the task brief, confirmed independently.

### 11.2 Runtime proof on a disposable PostgreSQL — before the correction

A throwaway `postgres:17` container (name `que006-trial-pg`, `127.0.0.1:55432`, `--rm`, trust auth on loopback, no volume shared with the live stack) received the repository's own backup `backups/amsdp_amsdp_20261116-084923.sql.gz` (pg_dump 16.15):

| Step | Result |
|---|---|
| Restore into `amsdp_trial` | exit **0** |
| `alembic_version` after restore | `f7d2b4c6e8a1` |
| Row counts after restore | 60 organisations · 85 appointments · 6 queue entries · **4,645 audit events** · 596 staff users |
| `alembic heads` | **`a9c4e1f7b2d8 (head)` and `c4d8e2a91f60 (head)`** |
| `alembic upgrade head` | **FAILED**: `Multiple head revisions are present for given argument 'head'` |
| State afterwards | unchanged, still `f7d2b4c6e8a1` — the failure is non-destructive |

### 11.3 After the documented correction

The correction is a single scalar change, recorded in the migration's docstring and **not committed**:

```diff
- down_revision: Union[str, Sequence[str], None] = 'f8a2b3c4d5e6'
+ down_revision: Union[str, Sequence[str], None] = 'a9c4e1f7b2d8'
```

| Check (database `amsdp_trial`, from `f7d2b4c6e8a1`) | Result |
|---|---|
| `alembic heads` | **`c4d8e2a91f60 (head)`** — one head |
| `alembic upgrade head` | exit 0, six steps: `→ f8a1b2c3d4e5 → f8a2b3c4d5e6 → b3d7e91f6a24 → a9c4e1f7b2d8 (merge) → a7c3f19d2b64 → c4d8e2a91f60` |
| Expected tables | **`queue_announcement_deliveries`**, **`voice_packs`**, **`announcement_platform_config`** — all three present |
| Data after migration | 60 · 85 · 6 · **4,645** · 596 — **identical to before**, audit trail intact |

### 11.4 The exact production path (live database is already at `a9c4e1f7b2d8`)

A second restored database (`amsdp_live_path`) was first taken to the live database's position and then upgraded, which is what a real deployment would do:

| Step | Result |
|---|---|
| `alembic upgrade a9c4e1f7b2d8` | `current` reports **`a9c4e1f7b2d8 (mergepoint)`** |
| `alembic upgrade head` | exactly two steps: `a9c4e1f7b2d8 → a7c3f19d2b64` (deliveries) and `a7c3f19d2b64 → c4d8e2a91f60` (voice packs + platform config) |
| `current` | `c4d8e2a91f60 (head)` |
| Re-run `upgrade head` | **no-op** (idempotent, as the migrations claim) |
| Tables | all three present |
| Data | 60 · 85 · 6 · 4,645 · 596 — unchanged |

### 11.5 Status

**VERIFIED** for the correction; **NOT PERFORMED, deliberately** for the live database: no migration of any kind ran against the running PostgreSQL instance, and the trial tree's migration correction is uncommitted. The correction remains a **proposal** requiring the Product Owner's authorisation to become a real change on the branch.

---

## 12. Runtime and browser verification (Phase G) — **NOT VERIFIED**

Nothing was deployed, restarted or rebuilt, and no browser was driven. Every item below is therefore **NOT VERIFIED**, not "passing":

| Check | Status | Reason |
|---|---|---|
| English announcement playback | **NOT VERIFIED** | Requires the trial build served against trial services plus a real audio device |
| Bangla announcement playback | **NOT VERIFIED** | same |
| Room announcement behaviour | **NOT VERIFIED** | impossible to verify as merged: the automatic path cannot carry a room (INT-3) |
| Successful playback completion reporting | **NOT VERIFIED** (unit level only) | `delivery.js` classification is unit-tested; no end-to-end claim/outcome round trip against a server |
| Duplicate event handling | **NOT VERIFIED** (unit level only) | claim/refuse logic unit-tested; no two-terminal observation |
| Missed-turn recovery | **NOT VERIFIED** | untouched by both lineages, but not exercised |
| Queue call permissions | **NOT VERIFIED** | requires a live permission matrix walk |
| Configuration permissions (`super_admin`/`org_admin` only, `branch_admin` none) | **NOT VERIFIED** — 13 of the W3 API tests that encode it are **failing** (§9.1) | the code path raises before it can enforce anything |
| Tenant isolation | **NOT VERIFIED** | as above: the W3 non-disclosing-404 test is among the 13 failures |

**Why no isolated runtime was stood up:** the frontend calls nine live services; a safe trial runtime would need a parallel compose project plus a rebuilt image, i.e. exactly the "modify/rebuild the running application" the task forbids. Audible playback additionally needs a human at a speaker. Claiming any of the above would break the evidence standard, so it is left unclaimed.

**What *is* verified at runtime:** the merged backend imports and registers the two announcement endpoints (§9.4); the frontend production build compiles (§10.4); the migration chain upgrades a restored backup and preserves every row (§11).

---

## 13. Remaining risks and blockers

| ID | Risk / blocker | Severity | Owner |
|---|---|---|---|
| **B-1** | `organization/voice_packs.py:504` `TypeError` — the voice-pack upload path is broken, failing 13 W3 API tests including the permission and tenant-isolation ones | **High** (feature non-functional; "W3 delivered" cannot be claimed) | Engineering fix, then re-run |
| **B-2** | Outcome vocabulary collision (D-6): nine frontend tests fail, and the persisted `outcome` strings depend on the choice | **High** (audit semantics) | Product Owner decision |
| **B-3** | INT-3: the automatic path cannot speak a room while the operator path can | **Medium** (inconsistent patient instruction) | D-4 |
| **B-4** | F3's per-event store is not integrated; `dedupe.js` is dead code in the merged tree | **Medium** (intra-tab retry semantics lost vs the Ubuntu correction) | D-3 |
| **B-5** | Pre-existing test defects: doctor fixture 409 collisions (9 failures), `NameError: name 'after' is not defined` and identity `:0`/`:1` expectations (queuing), unclosed `test()` in `queue-announcement-delivery.test.mjs` | **Medium** (the suite cannot yet be trusted as a gate) | Engineering fix |
| **B-6** | Index numbering unresolved (D-5); the annex is explicitly unnumbered and seven documents stay unregistered | **Medium** (governance) | Product Owner decision |
| **B-7** | The merge state lives in the index only. Nothing is committed, so a `git checkout`/`git merge --abort` would discard the resolution work | **Medium** (work loss) | Mitigated: the resolved tree is exported outside the repository (§14.2) |
| **B-8** | No browser, audio or two-terminal evidence at all | **High** for acceptance | Cannot be closed in this task |

---

## 14. Is the trial merge suitable for a later acceptance review?

### 14.1 Verdict

**Yes as a base; no as a deliverable.**

* **Suitable for acceptance review** because: the histories unify with seven understood conflicts; both lineages' code is present and internally coherent; the frontend builds; the frontend suite is 332/341 with every failure explained by one decision; the backend suite is 738/763 with every failure reproduced on the pure remote branch; and the migration graph is proven on a restored backup, including the exact production path and idempotency.
* **Not suitable for deployment or a merge commit** because: one W3 code defect breaks the configuration feature (B-1); nine frontend and 25 backend tests fail; the outcome vocabulary and room behaviour are undecided; and there is no browser/audio evidence whatsoever.

**Minimum bar before a merge commit:** fix B-1; answer D-6 and D-4; re-run both suites; then run the browser/audio checklist in §12 on a parallel stack.

### 14.2 State left behind (nothing finalised)

| Item | State |
|---|---|
| Branches | `hackathon-mvp` @ `cd2f9ec` (untouched), `wip/que006-ubuntu-preservation` @ `41ac51a` (new, local), `trial/que006-windows-ubuntu-merge` @ `41ac51a` (new, local, **merge in progress**) |
| Merge commit | **none created**; `MERGE_HEAD` = `2fc007a` |
| Merged tree | **176 files** changed against `41ac51a` (**+32,180 / −615**), fully staged in the index: 163 additions and 13 modifications, with no unstaged difference and no conflict marker anywhere in `backend/`, `frontend/`, `docs/` or `scripts/` |
| Push | **none** |
| Deployment | **none** |
| Live database | **untouched**. `amsdp-db-1` (postgres:16-alpine) and all nine `amsdp-*` service containers read **Up 44 hours (healthy)** at the end of the task; no command in this task addressed port 5433. The disposable container that received the backup copy was stopped and removed |
| External backup | `/home/shomonrobie/amsdp_preservation_20261122/` — the original snapshot **plus** `07_trial-merge-resolved.patch` (the resolved trial tree vs `41ac51a`, including this report) and `08_trial-merge-files.tar.gz`, with digests in `05_sha256-artifacts.txt`. The resolution work therefore survives even if the merge state is discarded |
| `origin/hackathon-mvp` | unchanged at `2fc007a` |

---

## 15. Consolidated evidence status

Kept deliberately separate, as the task requires.

| Category | Items |
|---|---|
| **VERIFIED** (independent artefact) | Remote SHA equals the expected target · merge base `37cf3d1` · 3 local / 4 remote commits · 8 files changed on both sides · 7 textual conflicts · `.gitignore` auto-merge · preservation archive 23/23 SHA-256 OK · patch re-applies to a pristine `cd2f9ec` · bundle `okay` with 2 refs · merged backend imports and registers both announcement endpoints · frontend build compiles · migration: two heads before, one head after, three tables, all row counts and the audit trail unchanged, idempotent re-run |
| **IMPLEMENTED** | The trial branch with the merged index (7 conflicts resolved) · the union of `_entry_to_dict` · the index annex · INT-1 and INT-2 |
| **TESTED** | Frontend 341/332 pass/9 fail · backend 763/738 pass/25 fail · pure-remote baseline 110/81 pass/29 fail · migration upgrade ×3 databases · `py_compile` + import of the merged modules |
| **NOT VERIFIED** | Every browser/audio/permission item in §12 · acceptance of any behaviour · whether any announcement is *heard* |
| **BLOCKED** | Nothing in the investigation itself. Blocking *acceptance*: B-1 (W3 defect), B-2/D-6, B-3/D-4, B-8 (no runtime evidence) |
| **REQUIRES PRODUCT OWNER DECISION** | D-1 baseline authority · D-2 close F1 · D-3 F3 store · D-4 room announcements · D-5 index numbering · D-6 outcome vocabulary · D-7 manual-repeat delivery record |

---

## 16. Governance and skill compliance (`.clinerules` §6)

**Applicable governance documents (routing table §4):** `saas-multitenant-data.md` (migrations, §4–5), `saas-cicd-workflow.md` (git safety, honest CI state), `saas-application-security.md` (non-disclosing 404s, tenant isolation expectations), `saas-observability.md` (append-only audit, delivery record), `saas-frontend-ux.md` (announcement surface), and the AMSDP document index (`docs/governance/AMSDP_Docs_Index_V1.0.md`, read before planning). Business rules and the approved product decisions named in the task were treated as binding and are cited at each point where they decided a conflict (§6, §7, §8).

**Skills:** **none installed** in this workspace (`.clinerules` §5). No skill was used or claimed; governance documents were applied directly.

**Non-negotiables honoured:**

* *Server-side scope* — untouched; the merged tree keeps token-derived organisation/branch and W3's three-fold permission checks (though they cannot run, B-1).
* *404 not 403* — no change made; W3's non-disclosing test is among those that currently fail, which is reported as a defect rather than papered over.
* *Audit append-only* — the migration test proves `audit_events` unchanged (4,645 rows before and after); no audit row was deleted or rewritten.
* *Forward-only, idempotent migrations* — the correction changes only the parent pointer; the DDL is untouched and the upgrade is proven idempotent.
* *Never claim an unverified capability* — every browser/audio/permission item is explicitly NOT VERIFIED.
* *No secrets* — no credential, token or key is quoted here; the disposable database used loopback trust auth with no stored secret.
* *No destructive Git* — no `reset --hard`, `clean`, `stash` or `checkout .`; the working tree was preserved before anything else, and the only branch operations were `switch -c` and `fetch`.
* *No push, no merge commit, no deployment* — verified in §14.2.

**Deviations and exceptions (declared, not hidden):**

1. A snapshot commit (`41ac51a`) was created on a **new local branch** to preserve the Ubuntu tree. The task permits a WIP snapshot commit provided every file is inspected and documented, which §2.1 does. It is not pushed.
2. Two seam repairs (INT-1, INT-2) were made beyond textual resolution, because leaving either alone would have shipped a lost delivery record or an unusable migration graph. Both are documented in-file and here.
3. A disposable PostgreSQL container was created for Phase E/F, which the task explicitly allows when a disposable environment is available. It was isolated on `127.0.0.1:55432`, shared nothing with the live stack, and was removed at the end.
4. Documentation was written to `docs/implementation/` per `.clinerules` §11, and the index annex was appended rather than a revision number being invented.

**Report location:** `docs/implementation/AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md` — no collision at write time; no document was moved, renamed or overwritten; no migration manifest entry is required because nothing moved.

---

## 17. Reproducing this trial (for the acceptance review)

```bash
# 1. restoration (already done, kept outside the repo)
ls -la ~/amsdp_preservation_20261122/          # patch, tar.gz, sha256, bundle
git bundle verify ~/amsdp_preservation_20261122/06_amsdp-local.bundle

# 2. the trial merge (do NOT commit)
git switch trial/que006-windows-ubuntu-merge
git merge --no-ff --no-commit origin/hackathon-mvp

# 3. the two suites
cd frontend && npm test && npm run build
cd .. && AMSDP_DATABASE_URL=<disposable-dsn> PYTHONPATH=backend .venv/bin/python -m pytest backend -q

# 4. the migration proof
cd backend && AMSDP_DATABASE_URL=<disposable-dsn> ../.venv/bin/alembic heads   # must print one head
```

**Nothing in this report is accepted.** Acceptance is the Product Owner's act, and §8 lists what must be decided first.












