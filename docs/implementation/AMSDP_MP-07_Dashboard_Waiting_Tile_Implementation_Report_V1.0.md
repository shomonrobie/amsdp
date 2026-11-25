# AMSDP — MP-07 Implementation Report: the dashboard Waiting tile

**Task:** MP-07 (`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6, WP-B)
**Priority:** P0 · **Depends on:** — · **Related:** GAP-04
**Date:** 2026-11-24 · **Checkout:** `E:\amsdp` · **Branch:** working tree, uncommitted
**Evidence status reached: TESTED** (frontend suite executed here; live browser confirmation on the deployed
frontend is **not** available from this host and is not claimed)

---

## 1. Requirement

The plan's row:

> **MP-07** — `frontend/pages/dashboard.js:27` binds Waiting to `today.checked_in`, the same field as the
> adjacent Checked-in tile. P0. Deliverables: bind to `today.in_queue`; a test that the six tiles carry six
> distinct figures. Acceptance: *no two tiles show the same figure; the Waiting count changes when a patient is
> queued but not called.*

### 1.1 The defect as found

`frontend/pages/dashboard.js` built the six "today" cards from the `/api/v1/dashboard/today` payload:

```js
{ label: t('booked'),     value: today.scheduled  || 0 },   // line 25
{ label: t('checkedIn'),  value: today.checked_in || 0 },   // line 26
{ label: t('waiting'),    value: today.checked_in || 0 },   // line 27  ← defect
{ label: t('completedT'), value: today.completed  || 0 },   // line 28
{ label: t('cancelledT'), value: today.cancelled  || 0 },   // line 29
{ label: t('noShow'),     value: today.no_show    || 0 },   // line 30
```

Two of the six cards were bound to one field, so "Checked in" and "Waiting" always displayed the *same*
number. The clinic director's board therefore under-reported nothing and over-reported nothing — it simply had
one fewer figure than it appeared to have: a patient moved from "checked in" to "waiting" changed neither card,
and a queue of nine read as if nobody were waiting once the check-in tally was consumed elsewhere. A card that
duplicates its neighbour is worse than a missing card, because it looks authoritative.

The API was already correct and supplied the right field: `backend/appointment/dashboard.py` maps appointment
status `IN_QUEUE` → `counts["in_queue"]` and returns it as `"in_queue"` (line 64). Only the binding was wrong.

---

## 2. Change

One line in `frontend/pages/dashboard.js`:

```diff
-    { label: t('waiting'), value: today.checked_in || 0 },
+    { label: t('waiting'), value: today.in_queue || 0 },
```

Nothing else in the page was touched — no layout, no i18n key, no payload field. The `waiting` label and its

---

## 3. Tests

### 3.1 New test file

`frontend/tests/dashboard-tiles.test.mjs` (new; picked up automatically by `npm test`, which runs
`node --test` over `tests/`):

1. **`the dashboard declares its six today tiles`** — the page must declare exactly six
   `{ label: t('…'), value: today.<field> || 0 }` entries, in the order
   `booked, checkedIn, waiting, completedT, cancelledT, noShow`. A removed, added or reordered card fails.
2. **`the Waiting tile counts the queue, not the check-in tally`** — the Waiting tile's bound field must be
   `in_queue`, and the failure message names the field actually found (`MP-07: Waiting must read
   today.in_queue, found today.checked_in`), so a regression is self-diagnosing.
3. **`no two tiles display the same figure`** — the six bound field names must be six *distinct* names. This is
   the assertion that survives a future re-shuffle: any duplicate binding anywhere in the tile list fails, not
   only the one that was wrong here.

**Why source-contract and not a DOM render.** This project ships no DOM test renderer — the same constraint and
the same pattern already used by `frontend/tests/queue-call-control.test.mjs` and `calendar-render.test.mjs`
(regex/parse over the page source). The file states that limitation in its header. It is a genuine contract test
of the binding, and it is **not** a rendering test; §5 records the difference.

### 3.2 Executed results — the suite

```text
$ cd frontend && npm test
ℹ tests 363        ℹ pass 359      ℹ fail 2      ℹ skipped 2
✔ the dashboard declares its six today tiles (2.2921ms)
✔ the Waiting tile counts the queue, not the check-in tally (0.4538ms)
✔ no two tiles display the same figure (0.2312ms)
```

(The per-test lines are quoted from `runs/frontend-suite-2026-11-24-post-fix.log`; the console prints
`✔`/`✖` glyphs that the Windows code page renders as `Γ£ö`/`Γ£û`, so the tick marks here are transliterated, the
numbers are not.)

The two failures are **pre-existing and unrelated** — identical, by file and line, to the run captured at
`runs/frontend-baseline-2026-11-24.log` **before** any change in this task:

| Failing file | Baseline (pre-change) | Post-change |
|---|---|---|
| `tests/banglanamesense-dataset.test.mjs:60` (dataset hash `ac037c…` expected, `6f69a0…` produced) | fail | fail |
| `tests/calendar-render.test.mjs:1` (whole-file failure) | fail | fail |

Baseline was **`tests 360 / pass 356 / fail 2 / skipped 2`**; post-change is
**`tests 363 / pass 359 / fail 2 / skipped 2`** — three tests added, three passes added, the same two reds and the
same two skips (356 + 3 = 359, 360 + 3 = 363). The arithmetic closes, so no test was removed or silently
swallowed. The two failures are reported, not fixed here (D1: implement the named requirement) and are recorded
as an untriaged baseline red in the execution register.

### 3.3 Mutation check — the tests are not vacuous

The defect was reinstated in `dashboard.js` (`value: today.checked_in || 0` on the Waiting line) and the file
run on its own:

```text
$ node --test tests/dashboard-tiles.test.mjs
ℹ tests 3   ℹ pass 1   ℹ fail 2
✔ the dashboard declares its six today tiles
✖ the Waiting tile counts the queue, not the check-in tally
✖ no two tiles display the same figure
   AssertionError: duplicate tile binding: scheduled, checked_in, checked_in, completed, cancelled, no_show
   5 !== 6
```

Log: `runs/evidence-mp07-mutation.log`. The file was then restored from a byte-identical copy
(SHA-256 `EF40892FC7216741270CD8D5778C861E3A0CB1E54DAC26816AF46C2F8D688B0D`, unchanged), and the full suite
re-run green for those three tests.

Bangla string already existed, so no translation work was implied.

**Byte integrity.** The file is JSX/UTF-8 carrying Bengali strings; the edit was applied to the one line and the
file was verified by hash before/after the mutation check in §3.3 (`EF40892F…8B0D` both times), so no
re-encoding or line-ending churn was introduced.

---

## 4. Verification evidence

| Criterion | Status | Evidence |
|---|---|---|
| Waiting tile bound to `today.in_queue` | **IMPLEMENTED** | `frontend/pages/dashboard.js:27`; the payload field exists (`appointment/dashboard.py:64`) |
| Six tiles, six distinct figures | **TESTED** | `dashboard-tiles.test.mjs` — 3/3 pass in `npm test` |
| Tests fail when the defect returns | **TESTED** | mutation run, `runs/evidence-mp07-mutation.log` (2 failed) |
| No regression in the frontend suite | **TESTED** | 363 tests, 359 pass, 2 pre-existing failures (same two files at baseline) |
| A queued-but-not-called patient moves the Waiting number | **NOT OBSERVED live** | needs the deployed app with a real check-in; the binding + distinct-field proofs stand in its place. The API field is derived from appointment status `IN_QUEUE`, which is set by the check-in/enqueue flow |
| Rendered in a browser | **NOT AVAILABLE** | no DOM renderer in this repo, no browser automation on this host |

---

## 5. Known limitations and remaining gaps

1. **`in_queue` vs `queue_length` — a semantic question for the owner.** The dashboard endpoint returns *both*:
   `in_queue` (appointments whose status is `IN_QUEUE`) and `queue_length` (live `queue_entries` rows with status
   waiting/called/in_consultation/skipped, `dashboard.py:14,49–55`). The plan prescribes `in_queue`, and that is
   what was implemented. They are not the same number: a **walk-in** enqueued without an appointment row raises
   `queue_length` but not `in_queue`. If the owner wants "Waiting" to mean "patients physically in the room's
   queue" (matching the DQDS `patients_waiting`), the field becomes `queue_length` — a one-line change plus the
   same test. Recorded as an open decision, not silently chosen.
2. **Source-contract, not rendering.** The test proves the binding and the tile set; it cannot prove the card
   renders, localises, or looks right on a phone. That stays with the UI review on the deployed frontend
   (MP-31/MP-40 territory).
3. **Two pre-existing frontend failures** (`banglanamesense-dataset`, `calendar-render`) remain red at baseline
   and after this change; they are outside MP-07's scope, are not caused by it, and are flagged in the register
   as untriaged.
4. **No tile for `confirmed` / `in_consultation` / `walk_ins`.** The endpoint returns them; the page shows six
   cards. That is a product-layout decision, not a defect, and is left untouched.
5. **`npm test` was not part of any CI gate in this workspace** — it was executed manually here. No CI claim is
   made.

---

## 6. Governance and Skill Compliance

| Item | Detail |
|---|---|
| Governing documents read | `.clinerules` §1–§12; the plan §6 WP-B (MP-07 row), §7, §8, Appendix D (D.1, D.6, D.9); `frontend/pages/dashboard.js`; `frontend/tests/queue-call-control.test.mjs` and `calendar-render.test.mjs` (to reuse the established test pattern); `backend/appointment/dashboard.py` (to confirm the payload field, not to change it); `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Skills | **None installed** (`.clinerules` §5 verified). Governance documents used instead; no skill use claimed |
| D1 code scope | One binding line + one new test file. No API change, no i18n change, no layout change |
| D2 server-side enforcement | Not applicable — this is a display binding; no authorisation logic touched, and the payload was already branch/org scoped server-side (`require_branch_access`) |
| D3 tenancy | Untouched: the frontend receives only its own organisation's aggregates from an endpoint that derives the organisation from the token |
| D4 audit | Untouched — a read-only dashboard; no audit event is produced by a GET |
| D5 migration | None — no schema change |
| D6 tests | Positive (field is `in_queue`), structural (six tiles), and duplicate-detecting (distinctness), plus a mutation run |
| D7 execution | `npm test` and `node --test` executed here; output quoted from `runs/` logs |
| D8 runtime | **NOT AVAILABLE** — no browser/deployed-frontend access from this host; stated plainly |
| D9 report | This file, under `docs/implementation/`, with this section |
| Non-negotiables | No secret, token or credential read or written; no cross-tenant path added; nothing muted or hidden in the UI (a duplicate card was *removed from existence*, not hidden) |

**Report placement.** `docs/implementation/` per `.clinerules` §11. No move or rename, so no migration-manifest
entry. The docs index is updated in the same task (§12). Evidence logs live under `runs/` alongside the other
run artefacts of this session and are cited, not duplicated into `docs/`.

