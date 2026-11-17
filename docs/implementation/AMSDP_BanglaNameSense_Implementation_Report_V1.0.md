# AMSDP — BanglaNameSense MVP Implementation Report

> **Task ID:** `AMSDP-FEATURE-BANGLANAMESENSE-MVP-2026-11-10`
> **Date:** 2026-11-10
> **Site:** `/home/shomonrobie/amsdp`
> **Status:** implementation complete and tested (IMPLEMENTED + TESTED). Not
> ACCEPTED — acceptance is the Product Owner's act.
> **Where written:** `docs/implementation/` (`.clinerules` §11). The task text
> proposed `ai_factory/docs/AMSDP_BanglaNameSense_Implementation_Report.md`; that
> location is prohibited by `.clinerules` §11 ("`ai_factory/docs/` accepts no new
> AMSDP reports"), and the same task text also required following §11. The
> conflict and the rule applied are recorded in §12.
> **Companion report (separate task, same session):**
> `docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md`
>
> **Evidence vocabulary** (`.clinerules` §7): IMPLEMENTED = code exists and is
> reachable; TESTED = named tests pass in this tree; VERIFIED = a second,
> independent artefact confirms it; ACCEPTED = signed by the Product Owner. No
> claim below uses ACCEPTED.

---

## 1. What was built

A Bangla-first name autocomplete capability in the existing Next.js 14
Pages Router / plain JavaScript frontend, wired into the patient registration
name field, with a reusable matching engine, a reusable component, automated
dataset validation and tests.

Nothing was added on the backend: no service, no table, no migration, no API
change, no new dependency, no TypeScript, no App Router, no Tailwind, no
shadcn/ui, no AI service, no external API call.

### 1.1 Files created

| File | Purpose |
|---|---|
| `frontend/data/bangla_name_sense.json` | Byte-identical copy of the source dataset (80,517 bytes, SHA-256 `ac037c24…e51e`) |
| `frontend/data/README.md` | Dataset provenance, version, counts, hash, licence status, rules, refresh procedure |
| `frontend/lib/bangla-name-sense/normalize.js` | Unicode-aware normalization + word matching helpers (pure) |
| `frontend/lib/bangla-name-sense/matcher.js` | Index building, matching, deterministic ranking, duplicate suppression (pure) |
| `frontend/lib/bangla-name-sense/controller.js` | Keyboard/pointer/touch interaction state machine (pure) |
| `frontend/lib/bangla-name-sense/validate-dataset.js` | Structural dataset validation (shared by tests and the CLI) |
| `frontend/lib/bangla-name-sense/dataset.js` | Dataset metadata + index construction; degrades to "no suggestions" on a broken dataset |
| `frontend/components/BanglaNameSense.js` | Reusable React autocomplete component |
| `frontend/scripts/validate-bangla-name-sense.mjs` | Validation CLI (`npm run validate:dataset`) |
| `frontend/tests/banglanamesense-dataset.test.mjs` | 9 dataset tests |
| `frontend/tests/banglanamesense-matcher.test.mjs` | 14 matching/ranking tests |
| `frontend/tests/banglanamesense-controller.test.mjs` | 12 interaction tests |
| `frontend/tests/banglanamesense-integration.test.mjs` | 8 integration/regression-contract tests |

### 1.2 Files modified

| File | Change |
|---|---|
| `frontend/pages/patients.js` | The patient-name `<input>` replaced by `<BanglaNameSense>`; one dictionary key added per locale (`sg` = "Name suggestions" / "নাম প্রস্তাব"). Nothing else in the page changed. |
| `frontend/styles/global.css` | One `.bns-*` block appended (list panel, options, alias text, visually-hidden status, `@media (max-width:480px)` layout). |
| `frontend/package.json` | Two scripts added: `test` (`node --test`, built-in runner — no dependency) and `validate:dataset`. No dependency added or removed. |

---

## 2. Governance and skill compliance

| Requirement | How it was met |
|---|---|
| §2 task routing (read the index first) | `docs/governance/AMSDP_Docs_Index_V1.0.md` read at the start, then `docs/AMSDP_Business_Rules_V1.1.md`, `docs/AMSDP_MVP_SCOPE_V1.1.md`, `docs/AMSDP_Master_Feature_List_V2.3_Consolidated_Draft.md` §25.8 (read-only), `frontend/lib/i18n.js`, `frontend/pages/patients.js`, `backend/patient/main.py`, `frontend/styles/global.css`, `docker-compose.yml`, `docs/demo/AMSDP_Hackathon_Demo_Runbook.md` |
| §3 non-negotiables | No secret touched or logged. No schema change. No new tenant column. No audit change. No authorization change: the page keeps its role gate, the API keeps its server-side checks (unauthenticated `GET /api/v1/patients` still returns **401** — verified live, §8.4) |
| §4 routing rows applied | *Frontend UI / components*; *Backend API* (read-only inspection); *Multi-tenant data* (no change); *LLM / AI tooling* — explicitly **not** used: the brief forbids an AI service |
| §5 skills | **No skill package is installed** in this workspace (`.clinerules` §5). No skill was used or claimed. Governance documents were used instead, as §5 requires |
| §7 evidence standard | Every claim below names the command or artefact that produced it |
| §9 execution boundaries | The task explicitly required running tests, so suites were run; no servers were started by hand, and no git state was changed (nothing staged, committed or pushed) |

---

## 3. Dataset integration

### 3.1 Source, copy and preservation

| Item | Value |
|---|---|
| Source (untouched) | `~/bangla_name_sense/bangla_name_sense.json` |
| Integrated copy | `frontend/data/bangla_name_sense.json` |
| Copy method | `cp -p` (permissions and mtime preserved) |
| Identity check | `cmp` reports no difference; `sha256sum` of both files = `ac037c24ebaf0208324351352bd62cedf2de16fbfde6a7d02966c55b8879e51e` |
| Size | 80,517 bytes |
| Local dataset version | `1.0.0-2026-11-10` (recorded in `frontend/data/README.md` and `lib/bangla-name-sense/dataset.js`) |

The original file was not edited, moved or converted. Later source refreshes are
validated, never silently rewritten.

### 3.2 Validation results (`npm run validate:dataset`)

```
BanglaNameSense dataset validation — frontend/data/bangla_name_sense.json
  records .............. 718
  distinct Bangla names  701
  duplicate records .... 17 (suppressed at display time)
  with English alias ... 718
  gender metadata ...... present, never used for matching or display
  search index ......... 701 entries
  reference version .... 1.0.0-2026-11-10
  result ............... VALID

warnings:
  - 17 duplicate Bangla name record(s) — suppressed at display time, source preserved
```

Checker rules (all enforced, `validate-dataset.js`): root must be an object with
a `names` array; `total_count` must equal the array length; every record needs a
non-empty `bn` containing Bengali-script code points and a non-empty `en`; a
record or the root object carrying patient/application fields (`mobile`, `phone`,
`address`, `date_of_birth`, `nid`, `patient_id`, `organization_id`, …) is an
**error**.

### 3.3 Field policy actually implemented

| Field | Use |
|---|---|
| `bn` | Primary display value, exactly as stored — never rewritten |
| `en` | Optional search alias; also shown as small secondary text next to the Bangla name |
| `gender` | **Not read at all.** No filter, no ranking influence, no display, no inference. Asserted by tests (`results never expose gender…`, `gender metadata is never used…`) |

Duplicate handling: records are keyed by the normalized `bn`. The first record's
display form wins; later records for the same name contribute only their `en`
aliases. 718 records → 701 unique suggestions. The source array is never mutated.

---

## 4. Matching engine

`frontend/lib/bangla-name-sense/{normalize,matcher}.js` — pure functions, no
React, no DOM, no I/O, no network.

### 4.1 Normalization (search keys only)

1. Unicode **NFC**.
2. Remove zero-width characters (U+200B/200C/200D/2060/FEFF) that IMEs insert
   accidentally.
3. Apply the Bengali canonical compositions that NFC deliberately excludes:
   `ড+়→ড়`, `ঢ+়→ঢ়`, `য+়→য়`. Without this, two keyboards produce two different
   spellings of the same name.
4. Collapse internal whitespace and trim.
5. Lowercase (Latin only; Bangla is caseless).

A suggested name is always displayed from the raw `bn` string, so normalization
can never alter what the receptionist sees.

### 4.2 Matching and ranking (deterministic)

| Rank | Rule |
|---:|---|
| 0 | **exact** — typed text equals the whole Bangla name |
| 1 | **prefix** — the Bangla name starts with the typed text |
| 2 | **word** — every typed word prefixes a word of the name, in order (`রফি খা` → `রফিক খান`) |
| 3 | **alias** — typed text prefixes the `en` alias, or its words, case-insensitively (`ROF RAH` → `রফিক রহমান`) |

Tie-breaks, in order: rank → number of code points (shorter = more precise) →
plain ordinal comparison of the Bangla string. **Ordinal, not ICU collation**, so
the order is identical in Node and in every browser build. Verified by a test
that rebuilds the index from a reversed copy of the dataset and asserts
byte-identical result order.

Order-sensitivity is deliberate: `খান রফিক` returns nothing (documented in §9).

### 4.3 Performance and locality

- The dataset is bundled at build time (`import`ed JSON) and the index is built
  once per page load: 701 entries, linear scan per keystroke.
- 200 consecutive searches measured at **44 ms total** in the test suite
  (`local search is fast enough for per-keystroke use`).
- No request is issued while typing: asserted in tests (`doesNotMatch fetch(`,
  `XMLHttpRequest`, `/api/` in the component and both engine modules) and
  confirmed in the build output — the dataset string is inside the page chunk.
- Configurable `maxSuggestions` (default 8) and `minQueryLength` (default 1).

| §11 output location | This report and its companion live under `docs/`; the index was updated in the same task (§12 below) |
| §12 reading policy | Documents were located through the index and cited by the path actually opened |

---

## 5. Reusable component API

`frontend/components/BanglaNameSense.js` — plain JavaScript function component,
default export.

| Prop | Type | Default | Meaning |
|---|---|---|---|
| `id` | string | `'bns-input'` | input id; also the base of the option ids used by `aria-activedescendant` |
| `name` | string | — | forwarded to the input |
| `value` | string | `''` | controlled value |
| `onChange` | `(text) => void` | no-op | receives **only** what the user typed, or the exact `bn` of a picked suggestion |
| `label` | string | — | visible `<label>`; `*` is appended when `required` |
| `required` | bool | `false` | renders the asterisk and `aria-required`; form validation stays with the caller |
| `placeholder`, `disabled`, `autoFocus`, `className` | | | forwarded / applied |
| `maxSuggestions` | int | `8` | suggestion cap |
| `minQueryLength` | int | `1` | minimum characters before searching |
| `labels` | `{count}` | Bangla default | wording of the visually-hidden live region |
| `index` | object | shipped index | injectable index (tests, other datasets) |

Interaction contract (`controller.js`, unit-tested):

- Typing never selects, replaces or reorders anything the user typed.
- `ArrowDown` / `ArrowUp` open the list and move the highlight with wrap-around.
- `Enter` selects **only** a highlighted suggestion; with nothing highlighted the
  keystroke is untouched, so the form submits the typed name as-is.
- `Escape` closes the list and keeps the text; `Tab` closes without selecting.
- Pointer (`mousedown`, `click`) and touch (`touchstart`) select the tapped row;
  `preventDefault` on `mousedown`/`touchstart` keeps focus in the input and a
  400 ms guard prevents touch+click double-firing.
- IME composition (`isComposing`) is ignored so Bangla input methods are not
  hijacked.

Accessibility: `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`,
`aria-controls`, `aria-activedescendant`, `aria-required`, `role="listbox"` with
`role="option"` + `aria-selected`, and a `role="status" aria-live="polite"`
region announcing the suggestion count. Options are ≥44 px tall (touch target)
and stack vertically below 480 px.

---

## 6. Integration location

`frontend/pages/patients.js`, patient registration modal, name field:

```jsx
<div className='form-group'>
  <BanglaNameSense
    id='patient-name' name='name' label={T('n')} required
    value={f.name} onChange={v=>setF({...f,name:v})}
    labels={{count:T('sg')}} />
</div>
```

Behaviour preserved deliberately — the page still owns everything that matters:

| Preserved | Evidence |
|---|---|
| Mandatory patient name (no client or server bypass) | component renders the `*` and `aria-required`; `backend/patient/main.py` still rejects a blank name with 422; 16 backend patient tests pass |
| `{...f}` payload and `date_of_birth` / `age` pruning | unchanged lines in `patients.js` (contract test) |
| `POST /api/v1/patients` | unchanged (contract test asserts exactly one `method:'POST'` in the page) |
| Duplicate-patient warning (`duplicates`) | unchanged `setDupes(d.duplicates||[])` + `T('dup')` banner |
| Search by name/mobile | unchanged `GET /api/v1/patients?q=` |
| Role gate on the Register button and `if(!u.id)return null` | unchanged |
| Tenant isolation / authorization | untouched; live check: unauthenticated `GET /api/v1/patients` → **401** |
| No patient record created from a suggestion | suggestions only call the page's `onChange`; only the Save button posts |
| No search of private patient records | the engine reads only the static dataset (no fetch at all) |

Doctor and staff registration were **not** touched (explicitly out of scope).

---

## 7. Tests and results

Run from `frontend/`:

```
$ npm test
ℹ tests 43
ℹ pass 43
ℹ fail 0
```

| File | Tests | Covers (brief's required list) |
|---|---:|---|
| `banglanamesense-dataset.test.mjs` | 9 | JSON dataset validation, counts, hash/byte identity, no patient fields, malformed-dataset rejection, graceful degradation |
| `banglanamesense-matcher.test.mjs` | 14 | Bangla prefix, Unicode normalization, multi-word, English alias + case-insensitivity, duplicate suppression, empty/unmatched input, `maxSuggestions`, `minQueryLength`, determinism, no gender leakage, per-keystroke speed |
| `banglanamesense-controller.test.mjs` | 12 | keyboard navigation (Up/Down/Enter/Escape/Tab), **manual entry without selection**, pointer/touch selection, out-of-range guard, editing after selection |
| `banglanamesense-integration.test.mjs` | 8 | page↔component contract, mandatory-field contract, preserved registration behaviour, a11y attributes, keyboard/mouse/touch wiring, locality (no fetch/AI), no gender use, "never rewrites the input" |

Regression checks:

| Check | Result |
|---|---|
| `frontend`: `npm run build` (real Next pipeline) | `✓ Compiled successfully`; `/patients` 12 kB; dataset string found in `.next/static/chunks/pages/patients-*.js`; `bns-option`, `bns-list`, `combobox`, `aria-activedescendant`, `listbox` present in the chunk; `.bns-list` in the CSS bundle |
| `backend`: `.venv/bin/python -m pytest backend/patient -q` | **16 passed** (1 unrelated Starlette deprecation warning) |
| No existing test removed, weakened or rewritten | `git status` shows only the files listed in §1.2; no test file was modified |


---

## 8. Acceptance criteria checklist (Master Feature List §25.8.5)

| # | Criterion | Status | Evidence |
|---:|---|---|---|
| 1 | The dataset loads and passes structural validation | **TESTED** | `validate:dataset` → VALID; 4 dataset tests |
| 2 | Bangla prefix matching works correctly | **TESTED** | `Bangla prefix matching returns the expected names`; `রফিক` → rank-1 prefix matches only |
| 3 | Multi-word matching works correctly | **TESTED** | `multi-word matching works when words are abbreviated` (`রফি খা` → `রফিক খান`, rank `word`) |
| 4 | English alias matching works where applicable | **TESTED** | `English alias matching works and is case-insensitive` (`rof`, `ROF`, `rof rah`) |
| 5 | Duplicate suggestions are not displayed repeatedly | **TESTED** | 718 → 701; `duplicate Bangla names are suppressed…`; `every displayed suggestion is unique` |
| 6 | Empty and unmatched searches behave gracefully | **TESTED** | `empty and unmatched queries return nothing and do not throw` (`''`, `'   '`, `null`, `undefined`, `zzzzzz`, `12345`, `!!!`) |
| 7 | Users can navigate suggestions using the keyboard | **TESTED** | 12 controller tests incl. `ArrowDown / ArrowUp move the highlight with wrap-around`, `Enter selects…`, `Escape closes…` |
| 8 | Users can select suggestions using pointer or touch | **TESTED** | `pointer and touch selection pick the row that was tapped`; component wires `onMouseDown`, `onTouchStart`, `onClick` (contract test) |
| 9 | Users can enter names not present in the dataset | **TESTED** | `a name absent from the dataset can be typed and submitted`; `no suggestion is selected until the user asks for one` |
| 10 | Selecting a suggestion populates the existing patient name field correctly | **TESTED** | component `onChange(suggestion.bn)` → page `setF({...f,name:v})`; contract test asserts the wiring; selection tests assert the exact `bn` |
| 11 | Existing patient registration, validation, duplicate-warning and persistence workflows remain functional | **TESTED** | `existing patient registration behaviour is preserved verbatim`; 16 backend patient tests pass; live 401 check proves auth is unchanged. Persistence itself was **not** exercised against the live database on purpose — creating a real patient record is out of scope for a code change, and the backend suite covers it against the test database |
| 12 | Relevant automated tests and regression tests pass | **TESTED** | 43/43 frontend, 16/16 backend patient, `npm run build` green |
| — | Component usability on mobile and a11y (§25.8.2, README acceptance) | **IMPLEMENTED, partially TESTED** | responsive CSS + a11y attributes asserted in the contract test; no DOM/browser automation exists in this project (see §10) |

---

## 9. Description of the implemented UI

No screenshot tooling exists in this environment, so the interface is described
precisely instead of illustrated.

**Patient registration modal (`/patients` → Register):**

1. The first field is still **Name / নাম**, now with a leading asterisk and a
   normal single-line input (`combobox`).
2. On focus, if text is already present, the suggestion panel appears directly
   under the input, overlapping the following fields (absolute, `z-index:60`,
   `max-height:220px`, scrollable). The name field is the topmost field of the
   modal, so the panel is never clipped by the modal's own scroll area.
3. Each row is at least 44 px tall: the **Bangla name in 1.05rem semibold dark
   text** (primary), with the English alias in small grey text on the right.
4. The highlighted row is tinted (`#eef4f8`); hovering tints it as well.
5. Below 480 px the rows stack (Bangla name above the alias) so long names do
   not squeeze the alias.
6. Nothing is pre-selected when the panel opens: the user must press
   `ArrowDown`/`ArrowUp` (or tap a row) before `Enter` can apply anything.
7. Pressing `Enter` with nothing highlighted does nothing to the field — the
   form's own behaviour is untouched, so a name absent from the dataset is
   submitted exactly as typed.
8. Closing the panel (`Escape`, `Tab`, blur, or selecting) leaves the typed text
   intact.


---

## 10. Known limitations

1. **No DOM/browser automation.** The project has no component-test dependency
   (no Jest, no Testing Library, no Playwright) and adding one was not approved,
   so interactive behaviour is verified through the pure state machine that the
   component actually calls, plus a source-contract test for the markup and event
   wiring, plus a real `next build`. A human click-through in a browser is still
   recommended before ACCEPTED.
2. **No per-keystroke network-silence instrumentation** beyond static analysis
   and bundle inspection: no request is made because there is no fetch call at
   all and the dataset is bundled.
3. **Word-order sensitivity.** `খান রফিক` does not match `রফিক খান`; only
   in-order word prefixes match. Deliberate (predictability over recall).
4. **No substring / middle-of-word matching.** `ফিক` does not match `রফিক`.
   Prefix and word-prefix matching only.
5. **No transliteration.** Latin input matches only the supplied `en` aliases; a
   Latin spelling not present in the dataset returns nothing. No silent
   transliteration (explicit scope exclusion).
6. **Dataset coverage** is 701 names — a starting collection, not an
   authoritative directory. Real receptionist coverage may be low.
7. **Licence unconfirmed.** Provenance and redistribution rights of the dataset
   are not documented; it must not be published until they are (recorded in
   `frontend/data/README.md`).
8. **Bundle size.** The dataset adds ~80 KB of JSON to the `/patients` chunk
   (page 12 kB, first-load JS ~101 kB). Acceptable for a local per-page
   capability; a lazy chunk is the next optimisation if it grows.
9. **Doctor and staff registration are not integrated** (explicitly deferred by
   the brief and by §25.8.6).

---

## 11. Confirmation that existing patient registration is intact

1. `frontend/pages/patients.js` changed in exactly three places: one import, one
   dictionary key per locale, and the name field's markup. Payload construction,
   POST call, duplicate handling, search, role gate and login guard are
   byte-identical (asserted by `existing patient registration behaviour is
   preserved verbatim`).
   **Caveat on the file's diff (recorded deliberately).** This file already
   carried **pre-existing uncommitted work** when this task started — the
   working tree version is an owner-side rewrite of the page (AppShell, the
   `RequireLogin` wrapper, the age-from-DOB column, the registration modal), and
   the committed `HEAD` version is still the older plain-HTML page. Its
   `git diff` against `HEAD` is therefore 49 added / 62 removed lines, of which
   only the three locations above are this task's. The claim in point 1 is about
   *what this task edited*, not about the size of that diff. Consequence for
   committing: per `.clinerules` §9, staging `frontend/pages/patients.js`
   stages someone else's uncommitted work too — commit it deliberately.
2. `backend/patient/main.py` was **not** modified: `name` and `mobile` are still
   required (422 otherwise) and duplicate detection is unchanged.
3. `backend/patient` tests: 16 passed.
4. Live stack: `GET /api/v1/patients` without a token returns **401**, i.e.
   authorization was not weakened by this change.
5. No database migration, no schema change, no new endpoint, no new dependency.

---

## 12. Deviations, conflicts and open items

| ID | Item | Resolution |
|---|---|---|
| D-1 | The brief asked for `ai_factory/docs/AMSDP_BanglaNameSense_Implementation_Report.md`, which `.clinerules` §11 forbids ("no new AMSDP reports" there), while the same brief required following §11 and §12 | Written to `docs/implementation/` per §11/§12. **Open item O-8 for the Product Owner:** if a copy under `ai_factory/docs/` is wanted anyway, that is an explicit owner decision overriding §11 and can be added on request (one mirrored file, no content change) |
| D-2 | The ops task asked to "append" its results to this report, but both tasks must stay "separately identifiable" with their own acceptance checklists | Implemented as a **separate** report `docs/implementation/AMSDP_One_Command_Restart_Implementation_Report_V1.0.md`, cross-linked from both, so this report stays free of ops content |
| D-3 | `.clinerules` §9 limits terminal execution | The brief explicitly required running tests and verifying startup, so suites and the stack restart were executed; results are quoted verbatim above |
| D-4 | `npm test` uses Node's built-in test runner | No dependency added. The `MODULE_TYPELESS_PACKAGE_JSON` warning is suppressed by one targeted flag rather than by adding `"type": "module"`, which would have forced `next.config.js` → `next.config.mjs` |
| D-5 | README append changed one byte-level detail (see ops report §8) | Appending to `README.md` (which had no trailing newline) adds one; the owner's text is untouched |
| O-7 | `docs/governance/AMSDP_Engineering_Governance_Assessment.md:193` needs a reworded cell | Still open from the previous session; untouched, awaiting the owner |
| O-8 | Report location (D-1) | Awaiting owner decision |

Nothing was staged, committed, pushed, merged or deployed. Unrelated uncommitted
work in the tree was preserved; no `git reset`, `stash`, `checkout` or `clean`
was run.

---

## 13. Later reuse — appointment symptom search (AMSDP-SYMPTOM-01, 2026-11-16)

A later task reused this capability for a different dataset: searching a
bilingual *symptom* catalogue in the appointment booking form. The reuse is
recorded here so this report stays an accurate index of who depends on what.
Full account:
`docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md`.

| Layer | Reused? | Why |
|---|---|---|
| `lib/bangla-name-sense/normalize.js` | **Yes, imported directly** | NFC, the three nukta compositions, zero-width removal, whitespace collapse, Latin case-folding and `matchesWordPrefixesInOrder` are the language sense. `frontend/lib/symptom-catalogue/matcher.js` imports them and re-implements none of them. |
| `lib/bangla-name-sense/matcher.js` | No | Its index collapses on one Bangla name with one English alias; a catalogue entry needs several aliases plus a context tie-break. |
| `lib/bangla-name-sense/controller.js` | No | Different interaction: a multi-select with chips, not a single text field. |
| `data/bangla_name_sense.json` | No | The symptom catalogue is database-backed, not bundled. |

**Nothing in this module, its dataset or its component was modified.** The
dataset hash test, the matcher tests, the controller tests and the integration
tests are unchanged and still pass (they are part of the 135-test frontend run
recorded in the symptom report §10.4). A contract test in the symptom feature
asserts that its matcher imports `normalize.js` and never imports this module's
`matcher.js` or `controller.js`, so the reuse cannot silently become a fork.


| Approved business rules | Master Feature List §25.8 governs the feature and was followed clause by clause (§3–§8). No approved rule was modified or reinterpreted. Note: the brief listed `AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md`; that version contains **no** BanglaNameSense section (`grep -n BanglaNameSense` → no match), so the approved requirement text used is §25.8 of **V2.3**, which is the version that records the approval (`Change: Added BanglaNameSense as a P0 core MVP feature`, 2026-11-10). Both files were read-only |
