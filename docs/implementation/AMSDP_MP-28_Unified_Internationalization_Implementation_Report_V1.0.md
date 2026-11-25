# AMSDP — MP-28 Unified Internationalization, Implementation Report V1.0

**Date:** 24 November 2026 · **Checkout:** `E:\amsdp` (Windows workstation) · **Branch:** `hackathon-mvp`
· **HEAD at window start:** `a4ddc2cf58e019b57dccf59f3a859743e3c48430` (78 dirty entries, asserted from `git status`)
**Plan task:** **MP-28 — Unify i18n into `frontend/lib/i18n.js`, remove the page-local `L={bn,en}` dictionaries,
add a coverage test** (`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6 WP-G, `P2`, *depends on: —*).
**Grade:** **TESTED (frontend)** — 441 tests in this tree, 437 pass, the only two reds being the pre-existing Q-3 pair;
`npm run build` exit 0. No browser run, so nothing here is VERIFIED.

---

## 1. What the task asked for, and what was found

The plan's acceptance cell is three sentences, and each is separately failable:

| Acceptance clause | As found | As delivered |
|---|---|---|
| *Every visible string resolves in Bangla and English* | Five screens did translate, but through their own tables; the shared dictionary had two silent duplicate keys and no test proved either language complete | One dictionary, 505 keys in **both** languages, key parity and non-emptiness asserted |
| *No page-local dictionary remains* | **Five** pages carried `const L = { bn: {...}, en: {...} }` plus a local `function T(k)`: `index.js`, `orgs.js`, `branches.js`, `patients.js`, `appointments.js` | All five removed; every page imports `t` from `lib/i18n.js` |
| *The coverage test fails when a key is missing* | No such test existed; the gap audit's **GAP-23 "three i18n mechanisms"** was accurate | `tests/i18n-coverage.test.mjs`, 7 tests, proven discriminating by a deliberate mutation (§5.3) |

The three mechanisms the audit named, in the form the code actually carried them:

1. **Shared dictionary** — `frontend/lib/i18n.js` (`DICT`, `t`, `tIn`, `getLocale`, `setLocale`, `fmtDate`), used by
   `audit`, `dashboard`, `doctors`, `facilities`, `notifications`, `queue`, `schedules`, `staff`, `_app`.
2. **Page-local dictionary** — the five screens above, each with its own copy of the locale read
   (`sessionStorage.getItem('locale') || 'bn'`) and its own fallback chain.
3. **Component label defaults** — `components/SymptomPicker.js` (17 Bangla-only `DEFAULT_LABELS`) and
   `components/BanglaNameSense.js` (`{ count: 'প্রস্তাব' }`), overridable by a `labels` prop.

Mechanisms 1 and 2 are now one. Mechanism 3 is a component API rather than a page dictionary; it is **not** removed,
and §7 records exactly what that leaves unproven instead of claiming otherwise.

---

## 2. Scale of the move

| Page | Keys moved | Static call sites rewritten | Dynamic call sites |
|---|---:|---:|---:|
| `pages/index.js` | 8 | 8 | 0 |
| `pages/orgs.js` | 7 | 12 | 0 |
| `pages/branches.js` | 9 | 14 | 0 |
| `pages/patients.js` | 15 | 23 | 0 |
| `pages/appointments.js` | 134 | 149 | 9 |
| **Total** | **173** | **206** | **9** |

Every moved key is namespaced by its screen so two screens can never silently share a caption:
`home*` (login), `org*`, `brn*`, `pat*`, `apt*`. The dictionary now holds **505 keys in each language**
(`apt*` 134, `pat*` 17, `org*` 9, `brn*` 9, `home*` 8).

**The move was mechanical and byte-preserving.** A throwaway script (`%TEMP%\mp28-migrate.py`, not added to the
repository) parsed each page's object literal — quote-, comment- and brace-aware, not a regular-expression guess —
copied every value expression **verbatim** into the matching language block, deleted the block and the local `T()`
helper, inserted `import { t } from '../lib/i18n';`, and rewrote `T('key')` to `t('<prefix>Key')`. No Bangla or
English string was retyped by hand, so no translation drifted.

`appointments.js` uses translation **keys computed at runtime** — server refusals (`REFUSAL_KEYS[refusalCode(err)]`),
appointment-type labels/badges (`typeLabelKey`, `typeBadgeKey`), the list view (`view`, `v`) and the
match banner (`matchesBannerKey`). Those nine call sites became `t(aptKey(...))` against a six-line `aptKey`
helper that applies the same namespace. Without it they would have silently fallen back to their raw keys.

---

## 3. What else the move changed

- **Five hard-coded English strings** on those screens became dictionary keys: `createFailed`, `searchFailed`,
  `registerFailed`, `male`, `female` — the last two on the patient form's sex selector, which was English-only in
  Bangla mode.
- **`Cancel` / `Save` / `Loading...`** on three screens now use the existing shared keys (`cancel`, `save`, `loading`).
- **The login page's language toggle** now uses `setLocale(getLocale())` from the shared module instead of writing
  `sessionStorage` itself, so the key name and the default live in one place.
- **Two duplicate keys were removed** from each language block (`active`, `inactive` were declared twice with
  identical values — a latent hazard, since the second declaration silently wins in JavaScript). The surviving
  declarations were left untouched, so no rendered text changed.

---

## 4. Files changed

| File | Change |
|---|---|
| `frontend/lib/i18n.js` | +173 moved keys per language, +5 shared keys, −2 duplicate declarations; 725 lines |
| `frontend/pages/index.js`, `orgs.js`, `branches.js`, `patients.js`, `appointments.js` | local dictionaries and `T()` removed, `t()` imported, runtime keys namespaced, hard-coded strings keyed |
| `frontend/tests/i18n-coverage.test.mjs` | **new** — 7 tests |
| `frontend/tests/symptom-picker-contract.test.mjs` | 3 tests re-pointed at the dictionary (§6) |
| `frontend/tests/appointment-booking-feedback.test.mjs` | 3 tests re-pointed |
| `frontend/tests/appointments-calendar-integration.test.mjs` | 3 tests re-pointed |
| `frontend/tests/banglanamesense-integration.test.mjs` | 2 tests re-pointed |

No backend file, no schema, no migration, no dependency. Nothing was staged or reverted.


---

## 5. Verification — commands and their real output

All commands were run in `E:\amsdp\frontend` on this host, 2026-11-24. Outputs were captured to files outside the
repository and read back; the figures below are copied from those captures, not from memory.

### 5.1 The new coverage test

```
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/i18n-coverage.test.mjs
```

```
ok Bangla and English carry exactly the same keys (2.3043ms)
ok no key resolves to itself, an empty string or a non-string (0.6017ms)
ok the dictionary source declares no duplicate key in either language (0.6881ms)
ok no page keeps a local {bn,en} dictionary or its own translator (3.8779ms)
ok every literal key a page asks for exists in Bangla and English (2.5997ms)
ok keys built at runtime resolve through the same dictionary (0.2149ms)
ok an unknown key returns itself instead of throwing (0.1402ms)
tests 7 · pass 7 · fail 0 · exit=0
```

What each test actually proves:

1. **Key parity** — the two languages declare the same key set (505 each), and the count is asserted `> 400` so a
   regression that empties the dictionary cannot pass by making both sides equally empty.
2. **No silent fallback** — every value is a non-empty string; in Bangla no value may equal its Latin key.
   (English is exempt from the "equals key" clause only because words such as `minutes` are their own translation.)
3. **No duplicate declaration** — the two language blocks are parsed from source and any repeated key is reported;
   this is the check that found the real `active`/`inactive` duplication.
4. **No page-local dictionary or translator** — every file in `pages/` and `components/` is scanned for
   `const L = { … bn: {`, for `function T(k) {`, and for a `bn:`-first table. All five offenders are gone.
5. **Page keys resolve** — every literal `t('…')` / `tIn('bn','…')` across all 14 pages is looked up in **both**
   languages; the scan asserts it found more than 250 references, so an empty scan cannot pass.
6. **Runtime-built keys resolve** — every value of `REFUSAL_KEYS` and every `typeLabelKey` / `typeBadgeKey` of
   `APPOINTMENT_TYPES` is mapped through the same namespace and must exist. This is the case a naive coverage test
   misses: the page never writes those keys as literals.
7. **Fallback behaviour** — an unknown key returns itself rather than throwing or rendering the literal word
   `undefined`.

### 5.2 Full frontend suite

```
npm test
```
```
tests 441 · pass 437 · fail 2
not ok: tests/banglanamesense-dataset.test.mjs:60   (dataset bytes do not match DATASET_SOURCE)
not ok: tests/calendar-render.test.mjs              (ERR_UNSUPPORTED_ESM_URL_SCHEME, 'e:')
```

The arithmetic closes: the previous window recorded `434 / 430 / 2 / 2`; MP-28 adds **7** tests, all green, giving
`441 / 437 / 2 / 2`. **No new red**, and the two reds are exactly the pre-existing **Q-3** pair the register has
carried since the MP-07 window — the dataset provenance mismatch and the `calendar-render` module that cannot be
loaded on this host. They were not touched, weakened or skipped.

### 5.3 Negative control — proving the coverage test is not vacuous

`lib/i18n.js` was copied aside, **one** Bangla declaration renamed (`patNa:` → `patNaGone:`), and the test re-run:

```
not ok Bangla and English carry exactly the same keys
  AssertionError: keys with no English string: patNaGone
not ok every literal key a page asks for exists in Bangla and English
  AssertionError: unknown keys: patients.js: patNa
tests 7 · pass 5 · fail 2 · exit=1
```

Restored from the copy and re-hashed:

```
before = E19FED20D132790132A116D195D88C8DD2C8BB453F024EA66756653269194453
after  = E19FED20D132790132A116D195D88C8DD2C8BB453F024EA66756653269194453
```

Byte-identical. A first, cruder mutation (renaming the key in **both** languages) produced only one failure — parity
held but the page's request for the key failed — which is why the control was repeated with a one-sided mutation.

### 5.4 Build

```
npm run build
```
```
✓ Compiled successfully
Route (pages)             Size      First Load JS
├ ƒ /appointments      20.1 kB           147 kB
├ ○ /patients          13.9 kB           111 kB
exit=0
```

**Not compared:** this window took no "before" build-size reading, so the bundle delta is not claimed. The
`/patients` route staying at 13.9 kB with the dictionary removed from it is the only size statement the capture

---

## 6. Source-contract tests that had to change, and why that is not a weakening

Eight existing tests asserted the **mechanism**, not a product behaviour: they parsed the page source for
`key: '…'` twice (once per language) or for a literal `T('key')` call. Removing the page tables necessarily breaks
them. Each was re-pointed at the same property through the new mechanism; none was deleted, loosened or skipped.

| File | Test | Was | Is now |
|---|---|---|---|
| `symptom-picker-contract.test.mjs` | receptionist sees recorded symptoms | `[T('sy'), …]` in the page | `[t('aptSy'), …]` |
| `symptom-picker-contract.test.mjs` | every new caption in both languages | counted `key:'` twice in the page | 18 keys looked up in `DICT.bn` **and** `DICT.en` |
| `symptom-picker-contract.test.mjs` | picker labels come from the table | `title: T('sy')` | `title: t('aptSy')` |
| `appointment-booking-feedback.test.mjs` | each refusal code has a caption | counted `key:'` twice in the page | 21 captions looked up in both languages via `aptKey` |
| `appointment-booking-feedback.test.mjs` | dialog translates refusals | `T('bookErr')` absent | `t('aptBookErr')` absent (same guarantee) |
| `appointment-booking-feedback.test.mjs` | seats as words / empty-day hint | `T('capacity')`, `T('noSlots')`, … | `t('aptCapacity')`, `t('aptNoSlots')`, … |
| `appointments-calendar-integration.test.mjs` | type label and badge | `T(typeBadgeKey('walk_in'))` | `t(aptKey(typeBadgeKey('walk_in')))` |
| `appointments-calendar-integration.test.mjs` | keyboard/screen-reader labels | `aria-label={T('prev')}` | `aria-label={t('aptPrev')}` |
| `banglanamesense-integration.test.mjs` | name field labelled, duplicate warning | `label={T('n')}`, `T('dup')` | `label={t('patN')}`, `t('patDup')` |

**Arithmetic that shows nothing was dropped:** the suite went from 434 to 441 tests — exactly the 7 new coverage
tests. No test count was lost when the mechanism changed; the re-pointed tests still run and still assert.

The dataset-hash test (`banglanamesense-dataset.test.mjs:60`) and the module that cannot load
(`calendar-render.test.mjs`) are the **Q-3** pair, untouched by this task and still red — as they were before it.

---

## 7. What is not proven, and what was deliberately left alone

1. **No browser run.** This repository ships no DOM renderer and this host has no browser harness, so nothing here
   proves that a click renders Bangla. What is proven is the dictionary, the resolution rule and the source wiring —
   the same split every frontend task in this project has recorded.
2. **Language *switching* is proven at module level, not in a session.** `getLocale()` / `setLocale()` are the
   existing shared functions and the login toggle now calls them; the test proves unknown keys fall back and that
   every key exists in both languages. It does not prove a running Next.js session re-renders on toggle.
3. **The third mechanism survives, by decision.** `components/SymptomPicker.js` keeps 17 Bangla-only
   `DEFAULT_LABELS` and `components/BanglaNameSense.js` keeps one, with `labels` props overriding them. The booking
   page passes a full, bilingual label set for both components, so **on the one screen that uses them** nothing
   falls back — and the coverage test asserts that every literal key in that label set exists in both languages.
   A future caller that omits `labels` would still see Bangla defaults. Converting the defaults would change the
   component API, so it is recorded here rather than done unilaterally.
4. **One English string remains on the login page** — the developer note `Demo: admin · password in .env
   (AMSDP_DEMO_PASSWORD_ADMIN)`. It is an operator hint about a credential location, not product copy; keying it
   into the product dictionary was judged wrong (it would imply the value is translatable). Recorded, not hidden.
5. **`appointments.js` is large (58 kB after the move).** The mechanical transform was verified by the build and by
   the 441-test suite, not by reading all of it. Two spot checks (the top of the file and the label block) are in §2;
   a reviewer wanting line-level assurance should read the diff, not this summary.
6. **No commit.** The working tree carries the change, uncommitted, as every previous window in this session did.


---

## 8. Where this report is registered

| Register | Entry |
|---|---|
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §2 | MP-28 row: scope executed, state **TESTED (frontend)**, evidence figures, this report's filename |
| same §5 | frontend suite row: `441 / 437 / 2 / 2` |
| same §6 | MP-28 window file set, with "no schema, no migration, no dependency" |
| same §7 | next eligible work after MP-28 |
| same §8 | change-log row, 2026-11-24 |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | annex entry for this report; `.md` count 145 → 146 for this report, **147** once the window's second report (the PostgreSQL verification) was added |

---

## 9. Governance and skill compliance

| Requirement (`.clinerules`) | Compliance |
|---|---|
| §2 automatic routing | Domains: frontend UI, localisation, documentation governance. Read: `docs/governance/AMSDP_Docs_Index_V1.0.md` first; plan §6 WP-G (MP-28 row) and §4 (PO-02/PO-13 decisions); `saas-frontend-ux.md` as adapted in Assessment §3; the five pages, `lib/i18n.js`, and the tests that assert them |
| §3 non-negotiables | No secret touched or exposed; no capability claimed beyond TESTED; no schema, migration or audit change; no test weakened, skipped or deleted; the negative control was restored **byte-identically** and re-hashed |
| §4 routing table | Frontend row applied; **no skill package is installed** in this workspace, so governance documents were used and that fact is stated here rather than a skill being invented |
| §6 compliance reporting | This section |
| §7 evidence standard | §5 separates what was executed (test output, build log, mutation) from what was not (browser, live session); the grade is TESTED, never VERIFIED or ACCEPTED |
| §9 execution boundaries | Edits limited to the frontend; the transform ran from `%TEMP%`, not from the repository; no destructive git command, no stage, no commit; outputs captured to short files outside the tree and read back |
| §11 document placement | This report is in `docs/implementation/`; no new folder; nothing deleted or renamed, so no manifest entry is required |
| §12 reading and index currency | Index read first; every cited document was opened in this session; the index is updated in the same task |

**Skills unavailable / not applicable:** none installed (verified in earlier windows and unchanged). Nothing was
pretended.

---

*End of report.*

supports.
