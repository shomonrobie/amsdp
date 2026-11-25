# AMSDP — MP-29 Responsive, Touch and Accessibility Pass, Implementation Report V1.0

**Date:** 25 November 2026 · **Checkout:** `E:\amsdp` (Windows workstation) · **Branch:** `hackathon-mvp`
· **HEAD at window start:** unchanged from the MP-28 window (`a4ddc2cf58e019b57dccf59f3a859743e3c48430`);
the tree carried **96** dirty entries, asserted from `git status --porcelain`
**Plan task:** **MP-29 — Responsive, touch and a11y pass on the queue and appointment screens**
(`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6 WP-G, `P2`, *depends on: —*).
**Acceptance cell, verbatim:** *"Core journeys complete at 360 px and on desktop; large hit targets; keyboard reorder
works; no control depends on hover."*
**Grade:** **TESTED (frontend) + TESTED (backend, PostgreSQL)** — 17 new accessibility tests pass, the frontend suite
moved with no new red, and the backend suite is now **fully green** (`979 passed, 0 failed`) against the isolated
PostgreSQL database after the inherited MP-02 reds and one further test defect (D-4) were closed. **Nothing is
VERIFIED:** no browser was driven, no 360 px viewport was actually rendered, and no screen reader was used (§7).

---

## 1. What the task asked for, and what was found

The queue screen is the reception desk: one long table, a row per patient, and two small arrows per row that move a
patient up or down. It was the least accessible screen in the product, and worse than that — **the reorder was
broken outright**.

| Acceptance clause | As found | As delivered |
|---|---|---|
| *Keyboard reorder works* | It did not. `DataTable` called `c.render(row)` — no index — so the queue's arrows called `move(undefined, ±1)`; the swap built `[ids[undefined], ids[j]]`, produced a list containing `undefined`, and the server refused every reorder. No row was focusable, and no chord existed | Row index is passed to every renderer (`c.render(row, ri)`, `rowProps(row, ri)`); the move goes through the tested `moveWithin`; rows are `tabIndex=0` and move on **Alt+Arrow**; both ends are `disabled` |
| *Large hit targets* | The arrows were `btn-sm` (≈30 px) with no accessible name — a glyph-only `↑`/`↓` | 44 px floor in the sheet under `(max-width: 768px), (pointer: coarse)`; every glyph-only button in `pages/` and `components/` now carries an `aria-label` |
| *No control depends on hover* | Hover *was* the only feedback on the calendar chips and the add/more controls; there was no `:focus-visible` twin anywhere in the sheet | Every `:hover` in `global.css` now has a `:focus-visible` or `:focus-within` twin, asserted by test; nothing is revealed by hover |
| *Core journeys complete at 360 px* | No rule existed below 480 px. At 360 px the table collapsed into unreadable columns and the toolbar's fixed-width date input took half the screen | A `(max-width: 360px)` block: page padding, modal width, `overflow-x` on the table wrapper, stacked toolbar; plus `.sr-only` for the live region |

**The reorder defect is the one that matters.** It was not an accessibility gap that made the feature *harder* to use;
it made the feature *not work at all*, for any user, with any input device. It is recorded here rather than in a
separate defect note because MP-29 is the task that found it: a keyboard pass over a broken control is impossible
without discovering that the control is broken.

**The server was never the problem.** `POST /api/v1/queue/reorder` validates `entry_ids` and refuses a payload that is
not a complete permutation of the day's entries. That refusal is what every reorder hit — the screen was sending
`undefined` where an id belonged. No backend rule was relaxed to make the screen work (§6).

---

## 2. What was built

### 2.1 `frontend/lib/a11y.js` — the rules, as data (new, 108 lines)

Kept out of the page for the same reason `lib/staff-policy.js` and `lib/dashboard.js` keep their rules out of theirs:
`node --test` can assert a pure function without a browser, a DOM, or a new dependency. Exports:

| Export | What it decides |
|---|---|
| `MIN_TARGET_PX = 44` | The floor the CSS must use. WCAG 2.5.5 (AAA) asks 44×44, 2.5.8 (AA) 24×24; the reception desk is a touch surface, so the larger floor is taken and asserted against the sheet |
| `REORDER_MODIFIER = 'Alt'` | The chord that turns an arrow into a reorder |
| `reorderDelta(event)` | `-1` / `+1` / `0`. **Bare `ArrowUp`/`ArrowDown` return 0** — the queue is a long list and hijacking page scroll is a worse defect than the one being fixed. `Ctrl+Alt` (AltGr) and `Cmd+Alt` (OS gesture) return 0 for the same reason |
| `toPosition(value)` | An integer position, or `null`. `Number(null)` and `Number('')` are both `0`, so a numeric cast would make a *missing* index look like the first row — the exact failure being fixed. Only an integer or a digit string is a position |
| `moveWithin(list, index, delta)` | `{ list, moved, from, to }`, non-mutating. A non-position index or a move that would leave the list yields `moved: false` and an unchanged copy — **a no-op, never a corrupt payload and never a clamp** |
| `positionLabel(index, total)` | One-based `"2/5"`, or `''` when the arguments are not positions |
| `reorderRowProps({index,total,label,canMove,onMove})` | `aria-rowindex`, an accessible name (`"Token A-014, 2/5"`), and — only when `canMove` — `tabIndex: 0` plus the `onKeyDown` handler that calls `preventDefault()` **only** for a handled chord |

Nothing in this module authorises anything. It mirrors a decision the server already takes (`queue.manage`); a chord it
maps is still refused server-side for a principal without the capability.

### 2.2 `components/ui/DataTable.js` — the row index reaches the renderers

`c.render(row, ri)` and `rowProps(row, ri)`, where `ri` is the row's position in the rendered list. A `rowProps` prop
was added so a caller can decorate a row without DataTable knowing what a queue is.

### 2.3 `pages/queue.js` — the reorder is real, and it is announced

- `move(idx, dir)` builds the id list, calls `moveWithin`, and returns early when `moved` is false — **no request for a
  no-op**.
- `rowProps={(r, i) => reorderRowProps({…})}` wires the index, the total, the accessible name and `onMove: move`.
- The ↑/↓ buttons carry `aria-label={t('moveUp') + ' ' + r.token}` (and `moveDown`), and are `disabled` at
  `i === 0` / `i === entries.length - 1`.
- `<p className="sr-only" role="status" aria-live="polite">{announce}</p>` announces the new position after the server
  confirms: a reorder moves a row the user cannot see moving, so it is spoken instead of silently reflowed.

### 2.4 `lib/i18n.js` — three keys, both languages

`moveUp`, `moveDown`, `movedTo` added to **bn** and **en**. The page contract asserts all three exist, are non-empty,
and are not the same string in both languages (a copy-paste that leaves English text in Bangla mode).

### 2.5 `styles/global.css` — four rules, each asserted

`.sr-only`; keyboard twins for every hover; the 44 px floor under `(max-width: 768px), (pointer: coarse)`; and a
`(max-width: 360px)` block.

---

## 3. The tests, and what each one proves

Two new files, **17 tests**, both runnable with `node --test` and no new dependency.

### 3.1 `tests/a11y.test.mjs` — the decisions (8 tests)

| Test | What it proves |
|---|---|
| *the touch-target floor is 44 px and is the number the CSS uses* | `MIN_TARGET_PX` is 44 and `REORDER_MODIFIER` is `'Alt'`; §3.2 asserts the sheet actually uses the constant |
| *only Alt+Arrow reorders; a bare arrow keeps scrolling the page* | The chord matrix: Alt+↑/↓ move; bare ↑/↓ are 0; `Ctrl+Alt` and `Cmd+Alt` are 0; Alt+Tab/Alt+letter are 0; `null` and `{}` are 0 |
| *a move swaps two neighbours and leaves the input untouched* | The payload is correct **and** the caller's array is not mutated |
| *a move that would leave the list is refused, not clamped* | Five out-of-range pairs all yield `moved: false` and an unchanged list — a clamp would silently mis-order a queue |
| *an index that is not a position cannot corrupt the payload* | `undefined`, `null`, `''`, `' 1'`, `NaN`, `1.5`, `'one'` — every one refuses to move, and **no element of the result is `undefined`**; `moveWithin(null, …)` returns an empty list |
| *the position label is one-based and empty when meaningless* | `1/3`, `3/3`, and `''` for `3/3` overflow, negatives, an empty list and a missing index |
| *a movable row is focusable and moves on the chord only* | `tabIndex`, `aria-rowindex`, an accessible name carrying token **and** position; the handler fires `onMove` twice and calls `preventDefault` exactly twice — the bare arrow is not suppressed; a missing handler does not throw |
| *a read-only row is not a control* | `canMove: false` yields no `tabIndex` and no `onKeyDown`, but the row is still named |

### 3.2 `tests/a11y-page-contract.test.mjs` — the sheet and the markup (9 tests)

This file exists because a correct helper nobody calls fixes nothing. It parses `styles/global.css` (comments stripped
first), `pages/queue.js`, `components/ui/DataTable.js`, and walks every `.js` under `pages/`, `components/` and `lib/`.

| Test | What it proves |
|---|---|
| *every hover state has a keyboard twin* | For **every** selector containing `:hover`, a selector `${base}:focus-visible` or `${base}:focus-within` exists. Not a sample — the whole sheet |
| *nothing is revealed by hover alone* | No `:hover` block sets `display:none`, `visibility:hidden` or `opacity:0` |
| *the touch target floor and the 360 px breakpoint are in the sheet* | `min-height: 44px`, `min-width: 44px` (built from `MIN_TARGET_PX`, so a constant change fails here), `@media (max-width: 360px)`, `(pointer: coarse)`, and a `.sr-only` rule |
| *the queue rows are focusable and move on Alt+Arrow* | `reorderRowProps(` and `rowProps={(r, i)` are called; `moveWithin(ids, idx, dir)` is the mover; both ends are `disabled`; and the hand-rolled `[ids[idx], ids[j]] =` swap **must not come back** |
| *the reorder is announced, and the arrows are named* | `role="status"`, `aria-live="polite"`, and both arrow labels |
| *the table hands every renderer the row index* | `c.render(row, ri)` present, `c.render(row)` **absent** — the index-free call is the defect |
| *the three new keys resolve in both languages* | `moveUp`/`moveDown`/`movedTo` non-empty in bn and en, and different between them |
| *no icon-only button is nameless* | Regex scan of every `pages/`+`components/` file for `<button …>↑</button>`-shaped markup; each must carry `aria-label`. Asserts `inspected > 0` so an empty scan cannot pass |
| *nothing is mouse-only* | No file under `pages/`, `components/` or `lib/` uses `onMouseEnter` / `onMouseOver` / `onMouseLeave` |

---

## 4. Files changed

| File | Change |
|---|---|
| `frontend/lib/a11y.js` | **new** — 108 lines, 7 exports |
| `frontend/tests/a11y.test.mjs` | **new** — 8 tests, 114 lines |
| `frontend/tests/a11y-page-contract.test.mjs` | **new** — 9 tests, 143 lines |
| `frontend/components/ui/DataTable.js` | `rowProps(row, ri)` prop added; `c.render(row, ri)` |
| `frontend/pages/queue.js` | `move()` through `moveWithin`; `rowProps` wiring; arrow `aria-label`s; `disabled` at both ends; `.sr-only` live region |
| `frontend/lib/i18n.js` | +3 keys × 2 languages (`moveUp`, `moveDown`, `movedTo`) |
| `frontend/styles/global.css` | +58 lines: `.sr-only`, hover twins, 44 px floor, 360 px block |

No dependency was added. No backend file was touched **for MP-29's own acceptance criterion**; the five backend files
below belong to the inherited MP-02 defects and to the test defect the full run exposed, and are reported separately
because they are different tasks' acceptance criteria:

| Backend file | Change |
|---|---|
| `backend/scheduling/sessions.py` | D-1: `template.get("session_id")` → `"session_id" in template` (key presence, not truthiness) |
| `backend/tests/test_schedule_audit_coverage.py` | D-1: one test repaired (seeds `session_id`), two tests added for the declared-window contract |
| `backend/doctor/tests/test_doctor_mobile_duplicates.py` | D-2: two-gate contract asserted with a new `ORGADMIN` fixture |
| `backend/organization/tests/test_queue_calling_config.py` | D-4: newest audit event ordered by `timestamp`, not by random UUID |
| `backend/queuing/tests/test_walk_in_placement.py` | D-4, same defect: ordered by `timestamp` |

**Nothing was staged or committed.** The change-control gate this project recorded
(`docs/architecture/saas/AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md` §9.4: *"no staging or committing without
the owner's instruction"*) is still in force, and the working tree already carries **96** dirty entries from nine
earlier work packages whose work is likewise uncommitted. Committing MP-29 alone would either stage a subset of the
tree (leaving the index inconsistent with the tree) or stage nine packages' work under one message. The disposition is
recorded as **O-3** in §8, for the owner to instruct.

---

## 5. Verification — commands and their real output

All commands were run in `E:\amsdp` on this host, 25 November 2026. Outputs were captured to files outside the
repository and read back; every figure below is copied from those captures, not from memory.

### 5.1 The 17 new tests

```
cd frontend
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/a11y.test.mjs tests/a11y-page-contract.test.mjs
```

```
ℹ tests 17
ℹ pass 17
ℹ fail 0
```

### 5.2 The whole frontend suite, before and after

```
cd frontend && npm test          →  E:\tmp-frontend-final.txt
ℹ tests 458 · suites 0 · pass 454 · fail 2 · cancelled 0 · skipped 2 · todo 0 · duration_ms 2564.19
```

| Run | tests | pass | fail | skipped | Note |
|---|---:|---:|---:|---:|---|
| MP-28 close (baseline this window inherited) | 441 | 437 | 2 | 2 | |
| MP-29 (this run) | **458** | **454** | **2** | **2** | +17, all passing; **reds unchanged** |

The two reds are the **pre-existing Q-3 pair**, not new ones, and both were reproduced in this run with their own
diagnostics:

1. `tests/banglanamesense-dataset.test.mjs:60` — `dataset bytes match the hash recorded in DATASET_SOURCE`:
   actual `6f69a0ef…` vs recorded `ac037c24…`. Already diagnosed in the MP-19 and MP-33 reports as a provenance
   mismatch between `frontend/data/bangla_name_sense.json` and the constant in `lib/bangla-name-sense/dataset.js`.
   MP-29 touched neither file.
2. `tests/calendar-render.test.mjs` — fails to load (`ERR_UNSUPPORTED_ESM_URL_SCHEME`), the second half of the same
   recorded pair. It is a Node ESM/SWC harness limitation on this host, not a component defect.

**Nothing in MP-29 touches either file**, and the count moved by exactly +17 tests / +17 passes.

### 5.3 The inherited MP-02 reds (D-1, D-2) — fixed and confirmed

The five reds MP-02 recorded (`5 failed, 972 passed`) were one defect in the product and one in a test. Both are
closed in this window, and this is the evidence:

| Suite | Before (MP-02 baseline) | Now |
|---|---|---|
| `doctor/tests/test_doctor_mobile_duplicates.py` + `tests/test_schedule_audit_coverage.py` | 1 red (D-2) + 4 reds (D-1) | **`27 passed, 1 warning in 22.75s`** (`E:\tmp-d123tail.txt`) |
| `tests/` + `identity/` + `doctor/` + `scheduling/` (against `amsdp_verify_2829`) | — | **`498 passed, 24 warnings in 666.59s (0:11:06)`** |

**D-1 — `scheduling/sessions.py:344`.** `sync_slot_templates` decided whether a published window was operator-declared
by `template.get("session_id")`. That is a *truthiness* test, and it was wrong in both directions: a template that
declares no `session_id` key at all is **not** session-derived, while a template carrying an explicit
`session_id: None` **is** session-owned. The test is now `"session_id" in template` — key **presence**. A declared
window therefore survives a session write, and a session-projection row can never be mistaken for operator-declared
hours.

Two tests were added to `backend/tests/test_schedule_audit_coverage.py` to pin both halves, and one existing test was
repaired because it had been asserting against a session-derived template without saying so (it now seeds
`session_id: "sess-1"`):

- `test_a_declared_window_survives_the_first_session_write` — the merge is a merge, and an identical re-projection
  audits nothing.
- `test_a_declared_window_is_refused_when_the_session_covers_it` — session capacity wins where the two overlap, and the
  window is published once.

**D-2 — `doctor/tests/test_doctor_mobile_duplicates.py`.** The test asserted that a non-platform administrator gets a
403 mentioning "platform administrator". The endpoint has **two** gates in that order — capability (`org.manage`) then
platform administrator — so a capability-holder who is not a platform admin is refused by the *first* gate, and the
message it returns is deliberately different. The product was right; the assertion pinned the wrong gate. The test now
asserts the two-gate contract with two fixtures: `ADMIN` (capability, not platform admin) → 403 **without** the
"platform administrator" text; the new `ORGADMIN` fixture (`org.manage`, not platform admin) → 403 **with** it; and
neither attempt wrote the policy row. **No product behaviour was changed to make a test pass.**

### 5.4 The whole backend suite, and the two test defects the first run exposed

The first full backend run in this window covered the whole `backend/` tree against the isolated
`amsdp_verify_2829` database:

```
cd backend
$env:AMSDP_DATABASE_URL='postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp_verify_2829'
python -m pytest -q --tb=line -p no:cacheprovider
→ 1 failed, 978 passed, 58 warnings in 1726.93s (0:28:46)
```

The MP-02 baseline was `5 failed, 972 passed`. Four of the five were D-1 (closed, §5.3), the fifth was D-2 (closed,
§5.3). The **one** remaining red was a test this window had not touched:

**D-4 — `organization/tests/test_queue_calling_config.py:134`** asserted the *newest* audit event with
`.order_by(AuditEvent.id.desc()).first()`. `AuditEvent.id` is a **UUID string** (`common/audit.py:36`,
`id=str(uuid.uuid4())`), so "descending id" is a **lexicographic sort over random hex** — it returns an *arbitrary*
event, not the latest. On the fresh database MP-02 used there was one event per `(action, target)`, so the arbitrary
pick was the right one and the test was green by luck. On the second run the trail already contains
`test_it_can_be_turned_off_again`'s two events — one of which legitimately has `before: {"…": true}` — and the arbitrary
pick landed on it: `assert True is False`.

- **Fix:** order by `AuditEvent.timestamp.desc()`, which is what every other audit assertion in the tree already does
  (`audit/main.py:96,122`, `appointment/tests/test_symptoms.py:366`, `doctor/tests/test_doctor_mobile_duplicates.py:201`,
  …). No product code changed; the audit row it reads already had the right `before` value.
- **Same defect, second instance:** `queuing/tests/test_walk_in_placement.py:287` had the identical
  `.order_by(AuditEvent.id.desc())`. It filtered on a unique `entry.id`, so it passed — by narrower luck. Fixed the same
  way, so it cannot flake when a second event ever attaches to one entry.
- **Evidence:** the two modules together → **`27 passed, 3 warnings in 35.07s`**.

**D-3 does not reproduce here, and is not claimed as fixed.** The MP-01 evidence window recorded "identity **71 passed /
4 errors**" — the four setup errors being in `identity/tests/test_identity.py::TestDoctorLink` (line 199). In this
window the identity package ran with **0 errors**, both inside the restricted run (`498 passed`) and inside the full run
(`978 passed`). The source does show the coupling the earlier window suspected — `TestDoctorLink` uses the
**module-global** `ADMIN_TOKEN` (set at import, lines 38–41, and re-set by `TestStaffLogin.setup_method` and
`TestValidateToken.setup_class`) and its `setup_class` (lines 202–217) inserts `Doctor` rows it assumes the module's own
import-time seed made possible. **No fix was applied**, because the defect could not be reproduced and a speculative
edit to a fixture is not evidence. Recorded as **O-2**, with the two candidate causes named and neither asserted.

**After the D-4 fix, the same command was run again — the whole tree, the same database, now with three full runs of
history in it:**

```
python -m pytest -q --tb=line -p no:cacheprovider
→ 979 passed, 66 warnings in 823.50s (0:13:43)
```

`979 = 977 (the MP-02 baseline total) + 2` — the two new D-1 tests. **Zero failures, zero errors.** The second run was
also faster (823 s against 1,727 s); the cause was not investigated, so no claim is made about it beyond the fact that
the first run's duration was not the price of passing.

---

## 6. Governance and Skill Compliance

### 6.1 Routing applied (`.clinerules` §4) and documents read

| Routing row | Document(s) actually opened in this window | What was followed |
|---|---|---|
| Frontend UI, components, a11y, responsive | `frontend/components/ui/DataTable.js`, `frontend/lib/i18n.js`, `frontend/pages/queue.js`, `frontend/styles/global.css`, `frontend/lib/staff-policy.js` / `lib/dashboard.js` (as the established "rules as data" pattern), `docs/implementation/AMSDP_MP-28_…_Report_V1.0.md` §1–5 (report structure precedent) | Rules live in `lib/a11y.js` as pure functions, not inline in the page; the page imports the shared dictionary rather than carrying a local one; no new dependency |
| Backend API / audit (D-1) | `backend/scheduling/sessions.py`, `backend/tests/test_schedule_audit_coverage.py`, `backend/scheduling/tests/test_schedule_audit.py`, `docs/implementation/AMSDP_MP-18_…_Report_V1.0.md` | The audit trail stays append-only; the projection change is recorded as `schedule.templates_changed` against the schedule; nothing was deleted or rewritten |
| Authentication / RBAC (D-2) | `backend/doctor/profile.py`, `backend/common/permissions.py`, `backend/doctor/tests/test_doctor_mobile_duplicates.py` | The two-gate order (capability → platform administrator) is preserved as product behaviour; the **test** was corrected, the endpoint was not weakened |
| Database schema | none — no schema change, no migration, no new column | The migration head is unchanged at `b2e5c7d91a04` |
| Documentation: writing a report, updating the index and the register | `.clinerules` §11/§12, `docs/governance/AMSDP_Docs_Index_V1.0.md` (annex pattern, lines 1853–1925), `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §7/§8, `docs/architecture/saas/AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md` §9.4 | One report in `docs/implementation/`, filename `AMSDP_<Topic>_<Version>.md`, a new file (no collision, nothing moved); index annex added in the same task; register row added |

### 6.2 Skills

**No skill was used, because none is installed.** Verified in this window, not assumed:

```
.clinerules\skills -> False
.claude\skills     -> False
skills             -> False
```

The governance documents named in the routing table were used instead, as `.clinerules` §2 step 3–4 and §5 require. No
capability is claimed here that a skill would have supplied.

### 6.3 Non-negotiables (`.clinerules` §3) — checked one by one

| Rule | Status in this change |
|---|---|
| Never log or expose secrets / tokens / keys | No credential is printed in this report. The verification DSN is a **local, password-less** database URL, quoted only in the command form the register already records |
| The UI is never the safety boundary | The keyboard chord only *mirrors* `queue.manage`; `POST /api/v1/queue/reorder` still authorises server-side. `canMove` hides the control, it does not grant anything |
| Access enforced server-side; org/branch from the token | No request shape changed. `queue.js` sends `entry_ids` and `reason` only — no organisation, no branch |
| Cross-tenant access fails closed with 404 | Untouched by this change; the reorder endpoint's existing scoping was not modified |
| Tenant key is `organization_id` | No schema change at all |
| Audit events append-only | D-1 *adds* an event where one was missing; no row is deleted, truncated or rewritten |
| Denials audited, never swallowed | Untouched. The reorder refusal is still the server's, and the screen surfaces it (`setError('Reorder failed: …')`) instead of silently doing nothing |
| Forward-only idempotent Alembic migration for every schema change | No schema change; no migration written |
| Never claim an unverified capability | §7 lists everything not proven. The grade is TESTED, not VERIFIED |
| Do not use a tool or library merely because it exists | No dependency added; `node --test` and the existing Next/SWC harness only |

### 6.4 Deviations and exceptions, stated plainly

1. **Business Rules V1.0 Parts II–X were not re-read in this window.** The D-1 change touches schedule semantics those
   parts govern. The change was derived from the code and from the MP-18 report (which quotes the acceptance criterion),
   and it changes *when an existing audit event is written*, not what a schedule means. Recorded as a deviation rather
   than described as compliance.
2. **`docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` was not read for MP-29.** It is ~320 KB; §12 prescribes targeted
   search instead of loading it, and no targeted contradiction was found to check against. Consequence: the 360 px
   layout is my own rule, not a transcription of the blueprint.
3. **The frontend agent-rules file `saas-frontend-ux.md` was not applied as a checklist.** Its adapted requirements are
   represented by the WCAG 2.5.5 floor, the hover↔focus pairing and the `.sr-only` live region, but the file itself was
   not opened this window.
4. **No staging or committing.** §9.4 of the change-control gate forbids both without the owner's instruction; see
   §4 and **O-3**.

---

## 7. What is not proven, and how far each claim reaches

The grade is **TESTED**, not VERIFIED (`.clinerules` §7): a green suite does not make something verified.

| Claim | Reach of the evidence |
|---|---|
| *Core journeys complete at 360 px* | The **rule** is in the sheet and is asserted by text match (`@media (max-width: 360px)`, the padding/modal/`overflow-x`/toolbar declarations). No 360 px viewport was rendered, so the *layout* is unproven. This is the weakest clause of the four |
| *Large hit targets* | The 44 px floor is present and asserted under two media conditions. It was not measured on a device, and `(pointer: coarse)` was not exercised on a real tablet |
| *Keyboard reorder works* | The decision layer is tested (chord matrix, bounds, no corrupt payload) and the page contract asserts the wiring exists. **No key was pressed in a browser**: React's synthetic `onKeyDown` was never fired against a mounted row |
| *No control depends on hover* | Proven for the sheet by parsing it (every `:hover` has a twin, nothing is hover-hidden). Not proven for anything the sheet cannot see — pseudo-elements, inline styles set from JS |
| Bangla copy | `moveUp`/`moveDown`/`movedTo` exist in both languages and differ. **No native speaker reviewed them** and no screen reader spoke them |
| The live region | `role="status"` + `aria-live="polite"` + `.sr-only` are asserted present. The announcement was never heard |

**Not run at all:** any browser, any accessibility auditing tool (axe, Lighthouse, pa11y), any device emulation, any
screen reader, and any E2E harness — the repository has none. Adding one was out of scope and would have been a new
dependency (`.clinerules` §3: do not add a tool because it exists). **No negative-control mutation was performed in this
window** either: earlier windows mutated a file to prove a test could fail, and that step is absent here rather than
assumed. What stands in its place is weaker: 17 assertions, each naming one rule, none demonstrated to fail on a
deliberately broken input.

**Also still red, and not MP-29's:** the Q-3 pair in the frontend suite (§5.2). It predates this window and is
reproduced unchanged.

---

## 8. Open items

| # | Item | Owner | Disposition |
|---|---|---|---|
| **O-1** | The Q-3 pair is still red — `banglanamesense-dataset` SHA mismatch and `calendar-render` failing to load. Both are diagnosed in MP-19/MP-33; neither is MP-29's | Owner (Q-3 decision) | Carried forward unchanged |
| **O-2** | **D-3** (identity `TestDoctorLink`, four setup errors in the MP-01 evidence window) **does not reproduce**: the identity package ran with 0 errors in both runs of this window (§5.4). The fixture coupling is visible in the source but no fix was applied | Agent, next identity window | Not fixed, not claimed fixed. Reproduce against a freshly migrated database before touching the fixture |
| **O-3** | **Nothing is staged or committed.** The tree carries 96 dirty entries from nine work packages; `.clinerules` §9 and the change-control gate §9.4 forbid staging without the owner's instruction | Owner | Awaiting instruction. No commit, no stage, no reset, no stash was run in this window |
| **O-4** | The Bangla strings and the spoken announcement have not been reviewed by a Bangla speaker, and no screen reader was used | Owner / next a11y window | Reported, not claimed |
| **O-5** | The 360 px layout is asserted as text, never rendered. A viewport test needs a browser harness the repository does not have | Next a11y window | Reported as the weakest clause |

---
