# AMSDP — Product Owner Decisions, 25 November 2026 (V1.0)

> **Task ID:** `AMSDP-PO-DECISIONS-2026-11-25`
> **Version:** 1.0 · **Date:** 25 November 2026
> **Status:** **DECISION RECORD — approved by the Product Owner in writing on 25 November 2026.**
> **Request that produced it:** `docs/implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md` (§5 response sheet).
> **Authority:** `.clinerules` §1 precedence (level 2 — explicit project-owner instructions), §3 non-negotiables, §11 placement, §12 reading.

---

## 1. What is approved, and what is not

The Product Owner approved the **recommended option** for every item below. Nothing outside this
table is approved, and no blank, deferred, conditional or unresolved item may be inferred as
approved by adjacency.

| Item | Approved option | Effect recorded in this file |
|---|---|---|
| **PO-01** | A — publish Phases 4/5/6 | §2.1 — `docs/product/AMSDP_Phase_Model_V1.1.md` |
| **PO-03** | A — ratify symptom/onset capture as approved P1, by annotation | §2.2 |
| **PO-04** | A — overbooking + priority are P1 after the first clean rehearsal | §2.3 |
| **PO-05** | C — defer MP-04 and MP-26 | §2.4 |
| **PO-06** | C — MP-27 stays deferred; Analytics Specification **not approved** | §2.5 |
| **PO-07** | C — subscription formally deferred | §2.6 |
| **PO-08** | B — split: decide D-5, O-2, POD-2, POD-7; appoint POD-11; carry the rest | §2.7 |
| **PO-09** | B — annotation only, never rewriting | §2.8 |
| **PO-10** | A+ — loopback binding **and** key-only SSH, one window | §2.9 — approach approved, **not executed** |
| **PO-11** | A — ratify the implemented doctor ↔ branch contract | §2.10 |
| **PO-12** | A — adopt `F-nn` with a published feature-key register | §2.11 |
| **POD-11** | Reviewer named: **Faria Bushra** | §2.7 |
| **Q-4** | Agent-controlled Business Rules **§33** edits authorised | §3 |
| **O-3** | Path-grouped commits authorised, **no push** | §4 |
| **Q-3** | Repair both test harnesses; **no expected-value change** | §5 |
| **D-3** | Investigate on a freshly migrated database; no fixture edit before reproduction | §6 |
| **B-4** | **UNRESOLVED** — the owner selected "other" | §7 |

**Not approved, and not to be treated as approved:** **B-1** (live reseeding), **B-2 / B-3** (live
verification and midnight observation), **Q-1**, **Q-2**, any live database mutation, and the
deferred band **MP-11 / MP-12 / MP-21 / MP-26 / MP-27**.

---

## 2. The decisions

Each row quotes the response-sheet line that the pack was built to receive, so the record and the
request are auditable against each other.

### 2.1 PO-01 — Phases 4, 5 and 6 published

> `PO-01: Approve Option A — publish Phases 4/5/6 (names from the spec; scopes/exit criteria in §3.1; PO as accepting authority; MP-30 as verification)`

Published as `docs/product/AMSDP_Phase_Model_V1.1.md`. Because Business Rules and MVP Scope are
owner-controlled, the publication is a **standalone** document and neither owner document was
edited. Milestone **M-8** now has a definition; **MP-30** is now defined as verification of the
existing handoff surfaces with **no new clinical feature**.

### 2.2 PO-03 — Symptom and onset capture ratified

> `PO-03: Approve Option A — ratify symptom/onset capture as approved P1, by annotation in MVP §7 + Feature Catalogue`

Applied as dated, additive annotations (§2.8 authority): `docs/product/AMSDP_MVP_SCOPE_V1.0.md` §7
(the clause "Prescriptions, diagnoses, clinical notes, symptoms or treatment") and
`docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` §H. Original text is
preserved and visibly superseded **for symptom/onset capture only**. No code change: SYM-001 was
already implemented and tested.

### 2.3 PO-04 — Priority and overbooking authorised, sequenced

> `PO-04: Approve Option A — overbooking and priority are P1 after the first clean rehearsal (MP-09 → MP-13 → MP-14 → MP-15); subscription deferred`

**Authorised, not started.** The gate is the *first clean rehearsal*, which has not happened; the
order is fixed at MP-09 → MP-13 → MP-14 → MP-15. Moving MP-13 before MP-09 would be a change to
this decision.

### 2.4 PO-05 — MP-04 and MP-26 deferred

> `PO-05: Approve Option C — defer MP-04 and MP-26; re-open W3 on the stated trigger`

The trigger is stated in the decision pack §3.4 and is not restated here, so the two cannot drift
apart. Both tasks stay in the deferred band; neither may be started opportunistically.

### 2.5 PO-06 — Analytics deferred, specification recorded as not approved

> `PO-06: Approve Option C — MP-27 stays deferred; the Analytics Specification is recorded as not approved; V1.1 on resumption`

`docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md`'s 17-criterion Analytics Specification is therefore
**not an approved requirement**, and no acceptance claim may cite it. MP-27 remains deferred and
unestimated (pack §7, **M-1**).

### 2.6 PO-07 — Subscription formally deferred

> `PO-07: Approve Option C — subscription formally deferred pending a billing model; governs PO-04's subscription clause`

MP-21 stays deferred. This row **governs** the subscription clause of PO-04: no agent may read
PO-04 as authorising a subscription surface.

### 2.7 PO-08 — The split; POD-11 reviewer named

> `PO-08: Approve Option B — D-5: adopt "highest previous revision + 1, each annex names its revision"; O-2: no facility-level announcement scope in MVP (platform + organisation only); POD-2: formally closed; POD-7: authorised to remove the unreferenced audio files with the list recorded; POD-11: reviewer is Faria Bushra. Carry D-3, D-7, POD-6, POD-1/3/8/9/10 forward.`

Two measured corrections were required while applying this row. Both are recorded rather than
silently absorbed:

| Item | The pack said | Measured fact (25 Nov 2026) | Applied |
|---|---|---|---|
| **D-5** next index revision | "currently **48**" | The index base already **ends at Revision 48** (`AMSDP_Docs_Index_V1.0.md:1101`); the later annexes are the unnumbered ones | Rule applied as approved: highest recorded + 1 = **49**. The annex that names it is this window's (§8). The stale "48" is a pack defect, not a change to the decision |
| **POD-7** unreferenced audio | "the 15 unreferenced files" | 71 audio files on disk; **70** are declared in `frontend/public/audio/manifest.json`; **one** is not: `bn/phrase/room-suffix.wav`. **Zero** declared paths are missing | The exact list is **one file**, not fifteen. Removal of that one file is authorised and executed (§2.7.3) |

**2.7.1 D-5 (index numbering).** Forward-only rule: *the next revision is the highest previously
recorded revision + 1; each annex names the revision it was issued under; no annex may claim "no
revision advanced" again.* First application: **Revision 49** (§8).

**2.7.2 O-2 (announcement scope).** No facility (branch) level announcement enable/language scope
in the MVP. The approved contract is **platform defaults + organisation overrides**, which is what
`backend/organization/announcement_config.py` implements. A branch scope would be a new schema and a
new admin surface, and is out of scope.

**2.7.3 POD-7 (audio assets).** Verification performed before any deletion, as the brief required:

- Method: every asset path declared anywhere in `frontend/public/audio/manifest.json`
  (`masterFile`, `playbackFile`, `origin.file`) compared against every file on disk.
- Result: `audioFilesOnDisk: 71`, `declaredAssetPathsInManifest: 70`,
  `onDiskNotDeclared: ["bn/phrase/room-suffix.wav"]`, `declaredNotOnDisk: []`.
- The one orphan is a **Bangla** master with no manifest entry and no Bangla consumer — the Bangla
  phrase actually served is `bn/phrase/room-locative.*`. The English `en/phrase/room-suffix.wav`
  *is* declared and is untouched.
- The file was tracked in git before removal, so the deletion is recoverable from history.
- **Removed: exactly one file.** The other 70 remain, among them every `.mp3`, `.wav` and `.m4a`
  the manifest declares. The earlier "15 unreferenced" figure is **not** substantiated by this
  measurement and is withdrawn here.

**2.7.4 POD-11 (reviewer).** **Faria Bushra** is the named human reviewer. Scope of the appointment:

| She confirms | She does not confirm |
|---|---|
| Whether a queue announcement is audible and intelligible in the room it is played in (MP-32's acceptance cell, closing **B-8**) | That the software is correct, installed or deployed |
| Bangla pronunciation, wording and copy quality (**O-4** in the MP-29 report) | That any other limitation in the demo pack is closed |

Her confirmation is `VERIFIED` evidence only when recorded as a dated statement in a report — an
unwritten verbal "sounds fine" does not close MP-32.

**2.7.5 Carried forward explicitly:** **D-3, D-7, POD-6, POD-1/POD-3/POD-8/POD-9/POD-10**. They
remain open known debt and must stop being rediscovered as new findings.

### 2.8 PO-09 — Annotation only

> `PO-09: Approve Option B — annotation only (dated, additive, original text preserved) in the Limitations Report §12, the Feature Catalogue §H.1 and its scope-decision line, plus the D-5 index numbering pass; MP-34 may proceed on that basis.`

Applied to four places, each an **additive, dated block** with the original text left intact:

1. `docs/demo/AMSDP_Limitations_Report_V1.0.md` **§1 "Data Persistence"** — where the three false
   statements actually live (lines 12–15). The pack's "§12" was a line-range shorthand for 12–15,
   not a section number; the section is §1.
2. `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` **§H.1** — the six
   P0 defects, each re-stated as enforced-now or still-owned.
3. The same catalogue's **"features awaiting scope decisions: 0"** line, annotated with the PO-03
   outcome.
4. The **D-5 index numbering pass** (§2.7.1, §8).

**Never authorised by PO-09:** rewriting the original sentences, editing Business Rules, MVP Scope,
the Master Feature Lists or the Blueprint beyond the annotations named, or any change to the
approval status of anything.

### 2.9 PO-10 — PostgreSQL exposure and host administration: approach approved

> `PO-10: Approve Option A+ — bind PostgreSQL to 127.0.0.1 and enable key-only SSH on the deployment host in one window; then run the MP-01 read on the host and return the output.`

The **approach** is approved. It is **not executed**: the brief requires a planned maintenance
window and forbids disrupting live services, and this workstation has no administrative path to the
host. The executable plan — exact steps, rollback, verification and the B-4 read — is
`docs/deployment/AMSDP_PostgreSQL_Exposure_and_Host_Access_Plan_V1.0.md`. **The `:5433` LAN
exposure remains open until that window runs.**

### 2.10 PO-11 — The doctor ↔ branch contract is ratified

> `PO-11: Approve Option A — ratify the implemented doctor/branch contract`

| Rule | Ratified statement |
|---|---|
| Doctor record | **Organisation-scoped.** `organization_id` required, **no `branch_id` column** |
| Branch membership | A separate assignment (`DoctorBranch`), unique on `(doctor_id, branch_id)`, carrying room, fee override, status and `is_primary`, with a partial unique index enforcing **exactly one primary per doctor** |
| Visibility | Organisation-scoped for organisation administrators; branch-filtered for branch-scoped users |
| Out-of-scope access | Fails closed with a **non-disclosing 404** — a doctor in another organisation is indistinguishable from one that does not exist |
| Tenant key | `organization_id`, unchanged. **No second tenant column** is introduced by this ratification |

No code change and no migration: the code already behaves this way (`backend/common/models.py:364–455`,
`backend/doctor/main.py:142–179`, `backend/doctor/profile.py:217–228`). The audit finding closes as a
documentation act. **Explicitly not decided:** whether a doctor may hold two concurrent rooms —
Q-6 (c) reserved that for the room-scoped numbering design, and it stays open.

### 2.11 PO-12 — `F-nn` adopted as the stable feature key

> `PO-12: Approve Option A — adopt F-nn as the stable feature-key scheme, published as a feature-key register mapping key -> BR section -> V2.5 family -> catalogue ID -> MP task`

Published as `docs/plan/AMSDP_Feature_Key_Register_V1.0.md`. The approved catalogue's own IDs
(`ORG-001`, `QUE-006`, `SYM-001`, …) are **not renamed**; they become one column of the register.
Any future re-keying must carry a mapping table.

## 3. Q-4 — authority to edit and commit Business Rules §33

**Owner instruction:** agent-controlled Business Rules §33 edits authorised. **Scope: §33 only.**

What exists in the tree is the PO-13 §33.1 scope-status amendment in **both** copies
(`docs/AMSDP_Business_Rules_V1.1.md`, `docs/product/AMSDP_Business_Rules_V1.0.md`): one header line
plus a `### 33.1` block — `64 insertions, 3 deletions` each, the three deletions being the paragraph
that classified DQDS as a later-phase capability, which §33.1 itself removes.

The diff was inspected before staging: nothing outside §33 and its header amendment is present. The
commit is therefore **in scope** and is made as its own path group. No other owner-controlled
document was edited, staged, reverted or reformatted, and **`.clinerules` was left untouched** — its
two-line local edit is not covered by this authorisation.

---

## 4. O-3 — Path-grouped commits, no push

**Owner instruction:** authorised, without pushing. Commits are grouped by path and reviewed
individually: backend migration → backend code → backend tests → frontend code → frontend tests →
documentation → Business Rules §33. Nothing is pushed; the remote tip is unchanged by this window.

Excluded by instruction or by scope: `.clinerules` (owner edit, not authorised).

---

## 5. Q-3 — Two harness repairs, no expected-value change

**Owner instruction:** preserve the expected dataset hash. Both defects were in the harness:

| File | Defect | Repair | Expected values touched |
|---|---|---|---|
| `frontend/tests/banglanamesense-dataset.test.mjs` | Hashed the **raw** checkout bytes; a CRLF checkout changes the digest although the content is identical | Hash and measure the **LF-canonical** form (comment explains why); the recorded `DATASET_SOURCE.sha256` and `bytes` are unchanged | **None** |
| `frontend/tests/calendar-render.test.mjs` | Dynamic `import()` given raw filesystem paths plus a hand-built `file://` URL; the compiled component then embedded an unescaped Windows path inside generated JS | `pathToFileURL(...).href` for every dynamic import and for the replacements inside the compiled source | **None** (no assertion changed) |

No `.gitattributes` was added and no product code was touched. Results: **9/9** and **9/9** for the
two files; full frontend suite **466 tests, 464 pass, 0 fail, 2 skipped**.

---

## 6. D-3 — Investigation result

Approved as an investigation on a freshly migrated database, with **no fixture change before a
reproduction exists**. Outcome this window: the failure **reproduces, but as an environmental
collection error, not as the original four setup errors.**

- `python -m pytest backend/identity/tests/test_identity.py -q` → `ERROR ... sqlalchemy.exc.OperationalError`, interrupted during collection.
- Cause: `backend/identity/tests/test_identity.py:19–30` performs `SessionFactory()` **database work at module import**, so the whole file — `TestDoctorLink` included — fails collection before a single test registers.
- Environment: **no PostgreSQL listener** on `127.0.0.1:55432` (the verification instance the programme uses) or `127.0.0.1:5432`. A live database is a precondition of the file.
- **No fixture was changed.** The original defect can be neither confirmed nor denied without a
  database, and silencing the module-level coupling would weaken the suite (`.clinerules` §3 and the
  brief's "do not weaken tests to make the suite pass"). D-3 stays **open**; its precondition is
  recorded as **B-4-class access**, not a code question.

---

## 7. B-4 — Unresolved

The owner selected **"other"** and supplied no database credential, so **no live database read,
migration, upgrade, reseed or other mutation was performed in this window** — and none may be
inferred. The read that closes B-4 is written into the PO-10 plan (§2.9) so it can be run in the same
window as the exposure fix. Until then the MP-01 family — MP-24, MP-25 and MP-35…MP-46 — stays
blocked, and no document may claim otherwise.

## 8. D-5 first application — this record is Revision 49 of the index

Under the approved rule, the Docs Index annex that registers this record is **Revision 49** (highest
previously recorded revision 48, + 1). The annexes issued between 21 and 25 November that claimed
"no revision number is advanced" remain in place unnumbered: D-5 is forward-only, and retro-labelling
them would rewrite history rather than fix the rule.

---

## 9. Still requiring a Product Owner decision

| Item | Why it is still open |
|---|---|
| **Q-1** (two patient-service date reads) | Not approved in this window; folds into MP-44 when MP-44 becomes executable |
| **Q-2** ("Waiting" wording: `queue_length` vs `in_queue`) | Not approved in this window; no code changed |
| **B-1** (live reseed), **B-2 / B-3** (live verification, midnight observation) | Explicitly withheld |
| **B-4** (live database access) | Owner selected "other" — §7 |
| **D-3, D-7, POD-6, POD-1/3/8/9/10** | Carried forward by PO-08 |
| **MP-16 / 1–3**, **O-4**, **O-5** | Pack §4.7 — recorded, not blocking |
| **M-1 … M-7** | Pack §7 — the pack's own missing information |
| **PO-06's analytics scope** | Deferred and unestimated |

---

## 10. Governance and skill compliance

| Requirement | Evidence |
|---|---|
| Reading policy (`.clinerules` §12) | Docs Index read first; decision pack, register, roadmap V1.1 (Appendices D/E), the Business Rules §33 diff, MVP Scope §7, the Limitations Report and the Feature Catalogue §H were all opened in this window |
| No skill installed | `.clinerules` §5 — none exists; governance documents were used and no skill usage is claimed |
| Owner-controlled documents | Annotated **only** where PO-03 / PO-09 authorised, additively; §33 committed under Q-4; nothing else touched |
| Evidence standard (§7) | Every claim above is `TESTED` or `IMPLEMENTED`. **Nothing is `ACCEPTED`** except the decisions themselves, signed by the Product Owner in writing |
| Secrets | None quoted. No credential, token or host secret appears in this record |

*End of decision record.*




