# AMSDP — Remaining Verification Plan — V1.0

| | |
|---|---|
| **Document** | `docs/plan/AMSDP_Remaining_Verification_Plan_V1.0.md` |
| **Purpose** | State, for every package that is implemented or tested but not verified or accepted, exactly what would close it, what already exists, what is missing, and who has to authorise the next move |
| **Written** | 2026-11-27, fourth window (controlled reconciliation phase) |
| **Basis** | Verified tree state at HEAD `71226e8` plus the working tree; register §17.2 (corrected 48-row tally) and §18–§19; `docs/audit/AMSDP_Database_Authorisation_Deviation_27Nov2026_V1.0.md` |
| **Status it does not change** | No package here is promoted. A plan is not evidence. |

**Ordering rule used.** Anything that needs only an already-granted permission and no new equipment comes
first; anything needing a browser, a live runtime, a database or a push comes after it and names the
permission it is waiting on. **The demo and rehearsal sequence is not jumped**: MP-09, MP-13, MP-14 and
MP-15 stay sequenced behind the first clean rehearsal (PO-04).

---

## 1. MP-33 — CI first green run *(highest priority)*

| Field | Content |
|---|---|
| **Acceptance criteria** | The workflow `.github/workflows/ci.yml` runs on the corrected tree and both jobs — *Backend* and *Frontend — build and unit tests* — conclude **success**. A green run of the working tree is the only thing that upgrades MP-33. |
| **Evidence already available** | Root cause recorded and removed at HEAD: `frontend/pages/patients.js` carries the three tokens the test asserts (`BanglaNameSense` import, `label={t('patN')}`, `value={f.name}`), so the recorded cause no longer exists (register §17.6). Last known green run: **#5**, 2026-11-14, `6bfbec4`. Local: frontend 527 tests, backend 1,069 tests. |
| **Evidence missing** | Any CI run of the current tree; the run history for `71226e8` and its predecessors; a frontend test run on **Node 22** (local is Node v24.12.0). |
| **Environment / equipment** | GitHub Actions (`ubuntu-latest`, Node 22). Reading a run needs a GitHub token or the `gh` CLI — **`gh` is not installed on this host** and no token exists in session. |
| **Separate owner permission** | **OA-1** (commit/push). Reading an existing run needs only a token, which is a separate, smaller grant. |
| **Next concrete action** | Grant OA-1 → push the branch → observe the two job conclusions → record the run id and conclusion in a new report. If a token is granted first, read run history without pushing and record what it shows. |

**Why this is first.** It is the only outstanding package whose closure is blocked *purely* on authority, not
on equipment or on product work, and it converts three separate "inferred green" statements into one
observed fact.

---

## 2. MP-04 — voice packs *(backend executed; feature not verified)*

| Field | Content |
|---|---|
| **Acceptance criteria** | Every AC of MP-04 in the master plan demonstrates on a running system: packs listed, audio previewed, selection persisted, the chosen pack audibly used by the queue call, and non-entitled callers refused server-side. |
| **Evidence already available** | `organization/tests/test_voice_packs_api.py` → **25 passed** (27 Nov, `amsdp_verify_1129`); whole-tree 1,069 passed includes that module. |
| **Evidence missing** | Any browser session; any live HTTP call outside the test client; any human confirmation that a selected pack is what the board actually plays. **Backend tests do not exercise audio.** |
| **Environment / equipment** | A running local stack (backend + frontend + PostgreSQL) and a browser with audio. |
| **Separate owner permission** | **OA-8 / B-2** (local-stack and browser risk assessment). Database access, if a fresh database is needed, is **OA-3**. |
| **Next concrete action** | On OA-8: start the stack against an authorised database, walk the four ACs in the browser, capture request/response and a screenshot per AC, and record VERIFIED per AC — or the specific AC that fails. |

**Backend testing ≠ feature verification.** The 25 tests prove the endpoints accept and refuse the right
shapes against a real database. They cannot prove a pack is *heard*, that the operator can find it, or that
the UI sends what the API expects. MP-04 therefore stays **PARTIAL**.

---

## 3. MP-46 / OPC-3 — denial capability and non-disclosing 404

| Field | Content |
|---|---|
| **Acceptance criteria** | MD-19's triple on **both** denial paths: a 403 capability refusal and a cross-tenant 404 each write exactly one `queue.display.denied` row carrying actor, `capability`, and the caller's org/branch; the 404 discloses nothing about the target; the generic `request.denied` row is suppressed so one denial is one row (AC-21, AC-20). |
| **Evidence already available** | Code: `_denied()` records `after["capability"]` on both call sites and takes the caller-supplied `target_id` for the 404. Tests: `tests/test_display_admin.py:192` (403 capability), `:272`–`:281` (404 capability, target id, caller branch, target branch absent). Negative control observed in the prior window for `target_id` (`assert '' == '991ef4bf-…'` before, pass after). Whole-tree 1,069 passed with the change in the tree (retained log, 17:09:20). |
| **Evidence missing** | A **capability-removal** negative control (delete the field, watch both assertions fail, restore). A live request against a running service. An independent reader confirming the 404 body/status/timing are unchanged. |
| **Environment / equipment** | An **authorised** disposable database for the mutation run; a running stack for the live check. |
| **Separate owner permission** | **OA-3** (database access method, credential scope, safety procedure) for the mutation run; **OA-8** for the live check; acceptance is the Product Owner's. |
| **Next concrete action** | On OA-3: remove `"capability": DISPLAY_MANAGE` from `_denied()`, run `pytest tests/test_display_admin.py -k "refused or cross_tenant"` and record **2 failures**, restore the file, confirm the SHA-256 matches, re-run to green. Then on OA-8 do the live 404 and record status, body and headers. |

---

## 4. Multi-display band — MP-38, MP-39, MP-45, MP-37, MP-42, MP-43, MP-24

| Field | Content |
|---|---|
| **Acceptance criteria** | Per package in the master plan; the band's shared criterion is that an administrator can create, scope, edit and switch off a board in the UI, and that the public board renders the configured scope — including the **seeded `cardio` department board**, which is part of the demonstration. |
| **Evidence already available** | Backend: 13 tests in `tests/test_display_admin.py` plus the multidisplay and denial-audit bands (155 passed in the focused band on 1129). Frontend: 527 tests locally, `display-board.test.mjs` 10 pass; MP-38's `ReferenceError` fix carries a 3/3-failing guard against the pre-fix source. |
| **Evidence missing** | Any browser rendering of a non-branch board (the exact case MP-38 broke); any check that the frontend and backend agree on field suppression in a real session. |
| **Environment / equipment** | Running stack + browser. |
| **Separate owner permission** | **OA-8 / B-2**. |
| **Next concrete action** | On OA-8: open the admin page for three boards (branch, doctors, department), switch `show_room` off on one, reload the public board, capture screenshots and the JSON bodies. |

---

## 5. T-10 — collection must not write *(new, this window)*

| Field | Content |
|---|---|
| **Acceptance criteria** | `pytest` collection performs **no** database access: `--collect-only` completes with the full 1,069 collected and no connection attempt, and the six refactored modules still pass when run normally. |
| **Evidence already available** | After the refactor: `1069 tests collected in 1.81s`, **0 errors, zero database contact** (`E:\Temp\amsdp_collect_1129b.txt`); the collected set differs from the retained 1,061 collection by exactly the 8 `tests/test_queue_history.py` ids and by nothing else; `py_compile` clean on all six files. Before the refactor the same command produced 836 collected / 7 errors, then 995 / 3. |
| **Evidence missing** | A normal (non-collect) execution of the six modules against a database — the fixtures are new code and have never run. |
| **Environment / equipment** | An **authorised** disposable database. |
| **Separate owner permission** | **OA-3**. |

---

## 6. Acceptance-only items (no engineering work outstanding)

| Package | What closes it | Permission |
|---|---|---|
| **MP-34** | Product Owner review and signature; residual **R-1** (family column) and **QUE-005** are named in register §17.3 | Owner acceptance |
| **QUE-005** | Live demonstration of the reorder guard + owner sign-off; classified in §17.3 as acceptance, **not** a code defect | OA-8 + owner |
| **MP-30** | Live evidence on a running system (PO-01 closed) | OA-8 |
| **D-3** | Already closed as a defect; the fix is carried by the retained 17:09:20 whole-tree log | none — but re-running needs OA-3 |

---

## 7. Blocked, sequenced and deferred — unchanged by this plan

| Class | Items | What they wait on |
|---|---|---|
| **BLOCKED** | MP-03, MP-31, MP-32, MP-33 (see §1), MP-40 | OA-1 (MP-33); OA-3/OA-4 (the rest) |
| **SEQUENCED** | MP-09, MP-13, MP-14, MP-15 | The first **clean rehearsal** (PO-04). The demo and rehearsal sequence is not bypassed. |
| **DEFERRED** | MP-11, MP-12, MP-21, MP-26, MP-27 | PO-DEC-02…PO-DEC-11 |
| **PROPOSED, deferred by PO-D1** | MP-47 | Owner decision to admit it |
| **Housekeeping** | Drop `amsdp_verify_1129` | A database permission — see the deviation record §6 |

---

## 8. What this plan does not do

- It does not execute anything. No database was opened, no browser started, no push made to write it.
- It does not promote, accept or verify any package, and it does not re-open a settled PO decision.
- It does not claim the outstanding work is small; it states, per package, exactly which permission or
  piece of equipment is the blocker, so that no package is left "waiting on engineering" when it is not.

<!-- Created 2026-11-27, fourth window. Registers the verification queue only; no status is changed. -->


