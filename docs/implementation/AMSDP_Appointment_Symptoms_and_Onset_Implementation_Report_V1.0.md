# AMSDP — Appointment Symptoms & Onset — Implementation Report V1.0

> **Task ID:** `AMSDP-SYMPTOM-01-2026-11-16`
> **Date:** 2026-11-16
> **Site:** `/home/shomonrobie/amsdp`
> **Where written:** `docs/implementation/` (`.clinerules` §11), registered in
> `docs/governance/AMSDP_Docs_Index_V1.0.md` Revision 21 in the same task (§12).
> **Status:** IMPLEMENTED + TESTED + BUILD VERIFIED + DOCUMENTED.
> **Not** BROWSER VERIFIED, and **not** ACCEPTED (acceptance is the Product
> Owner's act).
>
> **Evidence vocabulary** (`.clinerules` §7): IMPLEMENTED = code exists and is
> reachable; TESTED = named tests pass in this tree; VERIFIED = a second,
> independent artefact confirms it; ACCEPTED = signed by the Product Owner.
> Nothing below is called VERIFIED unless a second artefact is cited.

---

## 1. What was built

A receptionist-assisted, bilingual **symptom recording** capability inside the
existing appointment booking flow, plus the optional **onset** question:

1. **Symptoms / উপসর্গ** — an optional multi-select, searchable in Bangla and
   English, backed by a database catalogue, with removable chips, comma/Tab
   completion where the typed text is unambiguous, and free-text entry for a
   complaint the catalogue does not contain.
2. **When did the problem start? / কখন থেকে সমস্যা হচ্ছে?** — an optional,
   seven-answer question, plus an optional short note. No date is forced.
3. **A database catalogue** (`symptom_catalog`) of 79 curated, patient-reported
   symptoms in both scripts with synonyms, category, speciality *ranking hints*,
   source and review status.
4. **Appointment integration** (`appointment_symptoms` + two columns on
   `appointments`) that preserves what was recorded at booking time, keeps
   catalogue entries and free text apart, prevents duplicates in the database,
   and survives catalogue edits.
5. **A bilingual, in-memory search** over that catalogue in the browser, built
   on the existing BanglaNameSense normaliser rather than a second engine.

### 1.1 What it is not

Stated in the schema, the API payload and the UI, not only in this report:

* not a diagnosis, not clinical decision support, not triage, not an urgency
  assessment;
* no inference service and no external clinical engine — the only "intelligence"
  is a deterministic string ranking plus a tie-break;
* nothing is ever pre-selected, and neither the patient's age nor sex is passed
  to the picker at all;
* no diagnosis, prescription, clinical encounter or treatment record is created.

---

## 2. Architecture and design decisions

### 2.1 Which service owns the feature

The catalogue and the appointment link live in the **appointment** service
(`backend/appointment/symptoms.py`, mounted as a router beside `dashboard.py`
and `tracking.py`). Reasons:

* the only writer is the booking flow — a receptionist recording a complaint
  against a visit;
* the service already reads across models (`Patient`, `Doctor`, `Schedule`,
  `Organization`) against the single shared PostgreSQL database;
* no new service, no new deployment unit, no new health check, one new proxy
  rule in `next.config.js`.

The catalogue is nevertheless modelled like the facility/speciality catalogues
(org-owned, code + bilingual names + status), so promoting it to the
organization service later is a move, not a rewrite.

### 2.2 Data model — three pieces, each with a reason

| Object | Why it exists |
|---|---|
| `symptom_catalog` | The bilingual catalogue: `code`, `name_en`, `name_bn`, `synonyms_en`, `synonyms_bn`, `category`, `specialty_hints`, `source`, `review_status`, `sort_order`, `status`. Unique on `(organization_id, code)`. |
| `appointment_symptoms` | One row per recorded symptom, with `kind` = `catalogue` \| `free_text`, a **snapshot** of the catalogue names, the free text as typed, a duplicate-suppression key, who recorded it and when. |
| `appointments.symptom_onset_code` / `.symptom_onset_note` | The onset answer belongs to the visit, not to any one symptom — it is recorded even when no symptom was selected. |

Decisions worth recording:

* **A snapshot, not just a join.** `appointment_symptoms.name_en`/`name_bn`
  copy the catalogue wording at booking time, exactly like the chamber snapshot
  on `appointments` (revision `f7d2b4c6e8a1`). Renaming, re-categorising or
  retiring a catalogue entry must not rewrite a visit that already happened.
  `symptom_id` is kept for joins and provenance.
* **Two shapes in one table, enforced by the database.** `ck_appt_symptom_shape`
  refuses a row that claims to be a catalogue entry without an id, or free text
  without text — so a future writer cannot conflate the two.
* **Duplicates are a database fact.** Two *partial* unique indexes make the
  database the last line of defence: `(appointment_id, symptom_id)` where the id
  is not null, and `(appointment_id, text_key)` where the row is free text.
* **Onset is a closed vocabulary, not a date.** `TODAY … UNKNOWN` plus a free
  note. `UNKNOWN` means "asked, could not say" and is deliberately *different*
  from no answer at all (which is stored as no code). A patient at a reception
  desk routinely cannot name a day; forcing one would block the booking or
  invent a fact.
* **No comma-separated string anywhere.** The two lists are separate request
  fields, separate rows, and separate partial unique indexes.
* **Tenant key** is `organization_id` on both new tables, written on every row
  even where it is derivable from the appointment, so a cross-tenant read fails
  closed on this table too.

### 2.3 API shape

* `GET /api/v1/symptoms` returns the whole active catalogue plus the onset
  vocabulary and the `max_symptoms` cap in one response. The form then searches
  in memory — the same design as BanglaNameSense, so a keystroke never costs a
  request and the search behaves identically in both scripts.
* Server-side text search was **deliberately not implemented**. It would mean a
  second implementation of the Bengali normalisation rules (NFC, nukta
  composition, zero-width removal, word-prefix matching), which is the one thing
  this feature must not fork.
* The booking payload gained four optional fields: `symptom_ids`,
  `symptom_texts`, `symptom_onset`, `symptom_onset_note` — on
  `POST /api/v1/appointments` **and** on `POST /api/v1/appointments/walk-in`.
* Every appointment payload now carries `symptoms[]`, `symptom_onset` and
  `symptom_onset_note`.

### 2.4 Reschedule and transfer carry the complaint forward

A reschedule or a transfer moves the visit, not the complaint. The recorded
symptom rows and the onset answer are copied to the new appointment
(`copy_symptoms`), and the original rows stay on the original (now
`RESCHEDULED`) appointment. Dropping them would lose the only record of why the
patient came.

---

## 3. Files changed

### 3.1 Created

| File | Purpose |
|---|---|
| `backend/alembic/versions/b3d7e91f6a24_add_symptom_catalogue.py` | The migration (idempotent, forward-only, guarded). |
| `backend/appointment/symptoms.py` | Catalogue router, onset vocabulary, validation/planning, persistence, copy-forward, batched reads. |
| `backend/seed/symptom_catalogue.py` | The 79-entry curated bilingual catalogue + `demo_symptom_rows()`. |
| `backend/appointment/tests/test_symptoms.py` | 25 integration tests against PostgreSQL. |
| `backend/tests/test_symptom_catalogue.py` | 9 shipped-catalogue data-quality tests. |
| `frontend/lib/symptom-catalogue/matcher.js` | Index + ranking + `resolveCommit` + `textKey`, importing the BanglaNameSense normaliser. |
| `frontend/lib/symptom-catalogue/selection.js` | Pure selection state: add/remove, dedupe, cap, commit-on-comma/Tab, payload. |
| `frontend/components/SymptomPicker.js` | The React shell (`SymptomPicker`, `OnsetField`); owns no effect. |
| `frontend/tests/symptom-catalogue-matcher.test.mjs` | 18 ranking/matching tests. |
| `frontend/tests/symptom-catalogue-selection.test.mjs` | 13 selection-state tests. |
| `frontend/tests/symptom-picker-contract.test.mjs` | 8 source-level contract tests. |
| `docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` | This report. |

### 3.2 Modified

| File | Change |
|---|---|
| `backend/common/models.py` | `SymptomCatalog`, `AppointmentSymptom`, and the two onset columns on `Appointment`. |
| `backend/appointment/main.py` | Router inclusion; four optional fields on both create payloads; `_appt_to_dict(a, symptoms)`; batched symptom load for the calendar; copy-forward on reschedule/transfer; audit metadata. |
| `backend/common/permissions.py` | `symptom.read` (six roles) and `symptom.manage` (three administrative roles). |
| `backend/seed/seed_demo.py` | Seeds the catalogue (upsert by code); adds `appointment_symptoms` and `symptom_catalog` to the `--reset` order. |
| `backend/tests/amsdp_test_support.py` | `ensure_symptom()` helper; `purge_org` now clears the child symptom rows and the org's catalogue. |
| `frontend/pages/appointments.js` | Fetches the catalogue once; renders the two questions in both booking dialogs; posts the four fields; shows symptoms and onset on the appointment. |
| `frontend/next.config.js` | `/api/v1/symptoms` → appointment service. |
| `frontend/lib/auth.js` | Mirrors the two new permissions (the UI's `can()` map). |

Nothing else in the tree was touched by this task. The other files shown as
modified by `git status` belong to earlier, unrelated workstreams (design
system, doctor/facility pages, calendar, deployment) and were left exactly as
they were (§12).

---

## 4. Database migration

`b3d7e91f6a24_add_symptom_catalogue`, down-revision `f7d2b4c6e8a1` (the previous
head). Applied to the development database in this task:

```
INFO  [alembic.runtime.migration] Running upgrade f7d2b4c6e8a1 -> b3d7e91f6a24, add_symptom_catalogue
exit=0
```

It creates two tables and two nullable columns, plus:

* `uq_symptom_org_code` on `(organization_id, code)`;
* `idx_symptom_org`, `idx_symptom_org_status`;
* `idx_appt_symptom_appt`, `idx_appt_symptom_org`;
* `uq_appt_symptom_catalogue` — partial unique, `WHERE symptom_id IS NOT NULL`;
* `uq_appt_symptom_text` — partial unique, `WHERE symptom_id IS NULL AND text_key <> ''`;
* `ck_appt_symptom_shape` — the catalogue/free-text shape check.

Every step is guarded (`has_table` / column and index introspection), so
re-applying is a no-op; `downgrade()` removes only what this revision added.
Backfill: none — the new columns are nullable and an organization with no
catalogue simply records no symptoms, which is the documented behaviour of an
optional field.

The migration was applied from `backend/` with the DSN resolved through
`common.database` (no credential appears in this report, in the migration, or in
`alembic.ini`).


---

## 5. API changes

### 5.1 `GET /api/v1/symptoms` — the catalogue

Permission `symptom.read`. Returns the caller's organization only.

```json
{
  "items": [
    {
      "id": "demo-sym-headache", "code": "headache",
      "name_en": "Headache", "name_bn": "মাথাব্যথা",
      "synonyms_en": ["head pain", "pain in head"],
      "synonyms_bn": ["মাথা ব্যথা", "মাথা ধরা"],
      "category": "neurological", "specialty_hints": ["medicine"],
      "source": "AMSDP curated list (2026-11-16) …",
      "review_status": "curated", "sort_order": 70, "status": "active"
    }
  ],
  "onset_options": [
    { "code": "TODAY", "name_en": "Today", "name_bn": "আজ" },
    { "code": "FEW_DAYS", "name_en": "A few days ago", "name_bn": "কয়েক দিন আগে" }
  ],
  "max_symptoms": 20,
  "review_status_values": ["unreviewed", "curated", "clinically_reviewed"],
  "disclaimer": "Patient-reported symptoms recorded by reception. Not a diagnosis, not triage, and not clinically validated unless review_status says so."
}
```

* Active entries only. `?include_inactive=true` additionally returns retired
  entries and requires `symptom.manage` (403 otherwise, and the denial is
  audited).
* `GET /api/v1/symptoms/onset-options` serves the same seven-option vocabulary
  on its own.

### 5.2 `POST /api/v1/appointments` — new optional fields

```json
{
  "patient_id": "…", "doctor_id": "…",
  "appointment_date": "2026-11-16", "start_time": "21:15",
  "notes": "",
  "symptom_ids": ["demo-sym-headache"],
  "symptom_texts": ["মাথার পেছনে চাপ অনুভব করছি"],
  "symptom_onset": "FEW_DAYS",
  "symptom_onset_note": "প্রায় চার দিন ধরে"
}
```

All four are optional; omitting them (or sending empty lists) is the normal
case. The response now contains:

```json
{
  "symptoms": [
    { "id": "…", "kind": "catalogue", "symptom_id": "demo-sym-headache",
      "name_en": "Headache", "name_bn": "মাথাব্যথা", "text": "",
      "recorded_by": "…", "created_at": "…" },
    { "id": "…", "kind": "free_text", "symptom_id": "",
      "name_en": "", "name_bn": "",
      "text": "মাথার পেছনে চাপ অনুভব করছি", "recorded_by": "…", "created_at": "…" }
  ],
  "symptom_onset": "FEW_DAYS",
  "symptom_onset_note": "প্রায় চার দিন ধরে"
}
```

`POST /api/v1/appointments/walk-in` accepts the same four fields. `GET
/api/v1/appointments` (list), `GET /api/v1/appointments/{id}`, the status
update, the reschedule response and the walk-in response all carry the same
three keys. `symptom_onset` is `""` when the question was not answered;
`"UNKNOWN"` is a different, deliberate answer.

### 5.3 Validation and refusals (all 422)

| Case | Response |
|---|---|
| Symptom id not in this organization (unknown **or** cross-tenant — the same message) | `one or more symptoms are not available in this organization` |
| Retired symptom id | `one or more symptoms are no longer available for booking` |
| More than 20 symptoms | `no more than 20 symptoms can be recorded for one appointment` |
| Description longer than 200 characters | `a symptom description must be 200 characters or fewer` |
| Onset code outside the vocabulary | `unknown onset option` |

A rejected booking creates nothing: validation runs before the appointment row
is made, and the whole request is one transaction.

### 5.4 Audit

`appointment.created` (and `appointment.walk_in_created`) now also record
`symptom_count`, `symptom_ids[]`, `symptom_text_count` and `symptom_onset`.
The patient's free-text words are **not** copied into the audit trail: it is
append-only and permanent, so it holds the minimum needed to evidence what
happened. A test asserts exactly this.


---

## 6. The catalogue — contents, sources, review status

`backend/seed/symptom_catalogue.py`, seeded per organization by
`_seed_symptoms()` (upsert by `code`, so editing the file and re-running the
seed refreshes the wording instead of duplicating it).

| Property | Value |
|---|---|
| Entries | **79** |
| Scripts | Every entry has a non-empty English name and a Bangla name in Bengali script (asserted). |
| Synonyms | Every entry has at least one English **and** one Bangla synonym, so both scripts are always searchable (asserted). |
| Categories | 13: general, neurological, eye, ent, respiratory, cardiovascular, gastrointestinal, urinary, musculoskeletal, skin, mental_health, womens_health, pediatric |
| Speciality hints used | medicine, cardiology, pediatrics, orthopedics, gynecology, ent, dermatology |
| Review status | `curated` on every row — reviewed for wording and for the symptom/diagnosis line by the AMSDP team, **not** clinically validated |
| Source recorded per row | `AMSDP curated list (2026-11-16). Terminology cross-checked against the CARE Hospitals Bengali symptoms page (https://www.carehospitals.com/bn/symptoms) — consulted as a reference only; no page content was imported. Not clinically validated.` |
| `sort_order` | Unique per entry (asserted), so the tie-break is deterministic |

How the list was chosen:

* **Common reception complaints first** — fever, cough, pain (head, chest, back,
  joint, abdominal), gastric upset, weakness, urinary symptoms, skin, sleep and
  mood, gynae and paediatric basics.
* **Symptoms, not conditions.** There is no `diabetes`, `hypertension`,
  `anaemia`, `typhoid`, `asthma`, `tuberculosis`, `cancer`, `stroke`,
  `arthritis`, `migraine`, `pneumonia` or `jaundice` entry, and a test asserts
  none of those words appears in an English name or synonym. Where a patient
  *observes* something ("Yellowish eyes or skin", "Wound not healing") the entry
  is phrased as the observation, not the diagnosis it might suggest.
* **Not a scrape.** The CARE Hospitals Bengali page was read as a terminology
  reference for Bangla wording. It mixes symptoms, diseases, investigations and
  departments; nothing was imported programmatically and the page was not
  treated as a symptom list.
* **Finite on purpose.** 79 entries cover the common desk scenarios without
  pretending to be a terminology database; free-text entry exists for everything
  else, which is why the catalogue does not need to be exhaustive.

Seeded into the demo tenant in this task (`demo-org-001`), verified by a direct
database read:

```
created 79 updated 0 total 79
  fever | Fever | জ্বর | general | ['medicine', 'pediatrics'] | active | curated
  weakness | Weakness | দুর্বলতা | general | ['medicine'] | active | curated
  body_ache | Body ache | শরীর ব্যথা | general | ['medicine'] | active | curated
```

---

## 7. BanglaNameSense integration

The task required reuse of the existing capability, not a second engine.

| Concern | Where it lives | Used by the symptom feature? |
|---|---|---|
| NFC, nukta composition (ড়/ঢ়/য়), zero-width removal, whitespace collapse, Latin case-folding | `frontend/lib/bangla-name-sense/normalize.js` | **Yes — imported directly** (`normalizeBangla`, `normalizeLatin`, `wordsOf`, `matchesWordPrefixesInOrder`) |
| Ordered word-prefix matching | same module | **Yes** |
| Rank constants and the name-specific index | `frontend/lib/bangla-name-sense/matcher.js` | Not imported — a name index collapses on a Bangla name; a catalogue entry needs several aliases and a context tie-break |
| Keyboard state machine | `frontend/lib/bangla-name-sense/controller.js` | Not imported — the symptom picker is a multi-select with chips, a different interaction model |

What was added *around* the reused layer, in
`frontend/lib/symptom-catalogue/matcher.js`:

1. **Multiple aliases per entry** — Bangla name, English name, Bangla synonyms,
   English synonyms are all search keys, so `মাথাব্যথা`, `headache`,
   `মাথা ব্যথা` and `head pain` all find the same entry.
2. **A context tie-break** (§8).
3. `resolveCommit()` — the comma/Tab decision.
4. `textKey()` — duplicate suppression for free text.

`bangla-name-sense/matcher.js` and `controller.js` were **not modified**. The
name autocomplete, its dataset and its tests are unchanged and still green
(§10). A contract test asserts that the symptom matcher imports `normalize.js`
and never imports the name-specific matcher or controller, so the reuse cannot
quietly become a fork.


---

## 8. Suggestion ranking — exactly what it does

```
rank  0  EXACT   some key equals the typed text
      1  PREFIX  some key starts with the typed text
      2  WORD    every typed word prefixes a word of some key, in order
order: rank  →  context tie-break  →  sort_order  →  code
```

* **Text relevance is compared first.** Context can only reorder entries that
  matched *equally well*. A cardiology booking with `কাশি` typed still shows
  `Cough` first; a worse textual match can never be lifted above a better one
  (asserted).
* **Context is one input: the selected doctor's speciality codes.** They come
  from `doctor.specialties[].code`, falling back to a slug of the free-text
  `speciality`. An entry whose `specialty_hints` intersects them sorts above an
  equally ranked entry that does not.
* **Nothing is filtered.** Every entry stays searchable and selectable whatever
  the speciality (asserted: a dermatology-only symptom is still the top result
  for a cardiology booking).
* **Nothing is selected.** `search()` returns candidates. Adding a symptom is an
  explicit act: click, `↓` + `Enter`, comma, or Tab on an unambiguous entry.
* **Age and sex are not used at all.** They are not passed to the picker
  (asserted in the contract test), so a 74-year-old attending a cardiologist gets
  an empty symptom field until the receptionist asks. The rationale for not
  implementing demographic ranking: it has no reception value and its only
  possible effect would be to nudge a receptionist towards a complaint the
  patient has not reported — the exact inference the task forbids.
* **Deterministic.** No locale collation (ICU order differs between Node and the
  browser), no Map iteration order, no randomness: two identical calls produce
  identical arrays (asserted).
* **Empty query browses.** With nothing typed, the most common entries are
  offered, context first — a useful default order, never a selection.

Comma / Tab resolution (`resolveCommit`):

| Typed | Result |
|---|---|
| `মাথাব্যথা` (equals a name or synonym) | that entry is added |
| `মাথা` (prefix of two entries) | nothing happens — the comma is typed, Tab moves on |
| `coughi` (matches exactly one entry) | that entry is added |
| `zzzz` | nothing happens |

Free text is always available through an explicit final row
(“মাথা ব্যথা, জ্বর” → *Add this exactly as described*), so a comma inside a
free-text description still works.

---

## 9. Authorization and tenant isolation

| Control | Where |
|---|---|
| Catalogue read requires `symptom.read` | `require_permission` on both catalogue routes |
| Retired entries require `symptom.manage` | in-endpoint check, 403 otherwise |
| Bookings still require `appointment.create` | unchanged (`require_permission` on both create routes) |
| Org scope | `auth.organization_id` from the JWT — never from the request body |
| Cross-tenant or unknown symptom id | the **same** 422 message (asserted), so the response cannot be used to probe another tenant's catalogue |
| Retired symptom on a new booking | 422, no appointment created |
| Denials | 403/422 pass through `install_denial_audit`; a test asserts a `request.denied` row exists after a refused catalogue read |
| Read paths | `GET /api/v1/appointments` filters on `organization_id` and loads symptoms for exactly those appointment ids |

New permissions (matrix in `backend/common/permissions.py`, mirrored in
`frontend/lib/auth.js`):

| Permission | super_admin | org_admin | branch_admin | receptionist | doctor | assistant |
|---|---|---|---|---|---|---|
| `symptom.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `symptom.manage` | ✅ | ✅ | ✅ | — | — | — |


---

## 10. Tests executed and exact results

### 10.1 New backend tests — `backend/appointment/tests/test_symptoms.py`

Run against PostgreSQL 16 through `TestClient(load_app("appointment"))`, real
JWTs, real rows read back through `SessionFactory`:

```
$ cd backend && python -m pytest appointment/tests/test_symptoms.py -q
25 passed, 3 warnings in 20.88s
```

| Class | What is pinned |
|---|---|
| `TestCatalogue` (6) | unauthenticated read is 401; only this organization's **active** entries are returned (a foreign entry and a retired entry are absent); the payload carries both scripts, synonyms, category, hints, `review_status`, `max_symptoms` and the "not a diagnosis" disclaimer; `include_inactive` is 403 for a receptionist and 200 for an org admin; the onset vocabulary is exactly the seven codes, bilingual; the standalone onset route agrees |
| `TestBooking` (7) | a booking with **no** symptoms is normal (empty lists, no rows); one catalogue symptom is stored with a name snapshot, the recording user and the org; multiple symptoms keep their order and their `kind`; onset can be recorded with **no** symptom; `UNKNOWN` is stored as an answer while "not asked" stores nothing; a repeated id collapses to one row; free text differing only in spacing collapses to one row |
| `TestRejections` (6) | unknown id → 422 and nothing created; **cross-tenant id gives the same 422 detail as an unknown id**; retired id → 422; unknown onset → 422; 21 symptoms → 422; a 201-character description → 422 |
| `TestHistory` (2) | renaming a catalogue entry does not change what an existing appointment recorded (while the catalogue shows the new name); symptoms and onset appear in the calendar list **and** in the detail |
| `TestOtherBookingPaths` (2) | a walk-in records symptoms and onset; a reschedule carries the complaint forward and leaves the original visit's rows intact |
| `TestAudit` (2) | `appointment.created` records counts, ids and the onset code but **not** the patient's free text; a refused `include_inactive` read produces a `request.denied` audit row |

### 10.2 New backend data tests — `backend/tests/test_symptom_catalogue.py`

```
$ cd backend && python -m pytest tests/test_symptom_catalogue.py -q
9 passed in 1.33s
```

Pins the shipped catalogue: size band (40–120), unique URL-safe codes,
bilingual names with Bengali script, at least one synonym per script with no
duplicates, **no diagnosis words in English names/synonyms**, known categories
and speciality hints, unique `sort_order`, provenance and review status present,
`demo_symptom_rows()` shape, and the onset vocabulary contract.


### 10.3 Full backend suite

```
$ cd backend && python -m pytest -q
9 failed, 389 passed, 175 warnings in 326.42s
```

The **9 failures are pre-existing and unrelated** to this feature: they are all
in `backend/doctor/tests/test_doctor.py` and all say
`409 a doctor with this mobile number already exists` (or cascade from it).
Mechanism, established by inspection and a database read:

* that module's fixture calls `purge_org(ORG)`, which deliberately **keeps**
  doctor rows (they are reference rows the audit trail points at);
* `_create()` defaults to `mobile="01711111111"`, so the module's first test
  creates a doctor that a later test cannot create again;
* the leftover rows carry `created_at 2026-11-16 07:22` — i.e. that module's own
  earlier test in the same run.

`backend/doctor/tests/test_doctor.py` is unmodified in the working tree (last
commit `1448612`, 2026-11-12) and the failing module loads only `doctor.main`,
so this task cannot have caused it. It is recorded as open item **O-2**; fixing
test isolation for the doctor module is out of this task's scope.

The appointment service's own suite (which this task does touch) is green:

```
$ cd backend && python -m pytest appointment/tests -q
50 passed            (25 pre-existing + 25 new)
```

### 10.4 New frontend tests

```
$ cd frontend && npm test
ℹ tests 135
ℹ pass 135
ℹ fail 0
```

39 of those 135 are new (96 before this task):

| File | Tests | What is pinned |
|---|---|---|
| `tests/symptom-catalogue-matcher.test.mjs` | 18 | retired entries excluded (and included on request); Bangla name, English name, Bangla synonym and English synonym each find the same entry; partial terms in both scripts; a single word matching inside a multi-word name; case/whitespace/zero-width insensitivity; **nukta composition** (evidence the BanglaNameSense normaliser is reused); unknown query vs. empty-query browse; `maxSuggestions`; selected entries excluded; **context reorders only equal matches** and removes nothing; **context cannot promote a worse match**; a symptom outside the doctor's speciality stays findable; determinism; `resolveCommit` (exact / ambiguous / only-match / none / empty); a malformed catalogue does not throw |
| `tests/symptom-catalogue-selection.test.mjs` | 13 | empty selection and payload; ordering preserved; duplicate catalogue entry refused; free-text whitespace collapsed; duplicate free text refused (spacing variants); empty and over-long descriptions refused; the 20-item cap for both kinds; chip removal by kind; comma/Tab adds only an unambiguous entry; re-adding an already-selected entry is a no-op; chips keep the catalogue/free-text distinction and stable keys; payload keeps the two lists apart |
| `tests/symptom-picker-contract.test.mjs` | 8 | the picker owns **no effect** (the focus-loss defect class); the matcher imports `normalize.js` and never the name matcher/controller; no symptom name is hard-coded in the page or the picker (the catalogue comes from the API); the booking payload carries the four fields and both dialogs start empty; **the page passes no age/sex/patient data to the picker**; the detail view shows symptoms and onset; every new caption exists in Bangla and English; the labels are wired from the page's bilingual table |

What these frontend tests do **not** prove: that typing works in a browser.
There is no DOM harness in this suite (the jsdom attempt is recorded as
abandoned for memory reasons in the design-system report, §9), so the component
is covered by pure-module behaviour plus source-level structure, and the
behavioural claim rests on that — not on an unperformed browser run (§12).

### 10.5 Pre-existing suites re-run

The BanglaNameSense suites (dataset, matcher, controller, integration) and the
appointment-calendar, dialog-focus, facility/doctor and i18n suites are part of
the same `npm test` run above and are all green, so the reuse did not disturb
the capability it reuses.

---

## 11. Build results

```
$ cd frontend && npm run build
...
├ ƒ /appointments                         16.7 kB         133 kB
...
exit=0
```

Route table renders, `/appointments` bundles the picker (16.7 kB route bundle,
133 kB first load). No new dependency was added: React, the existing Tailwind
layer and the shipped normaliser are all that the new code uses.

---

## 12. Browser verification — not performed

**No browser run was performed for this feature.** Nothing in this report claims
BROWSER VERIFIED. The `/appointments` UI was exercised only through the two pure
modules, the source-level contract test and the compiler.

Two consequences worth stating plainly:

1. The running demo containers still contain the **previous** images. The
   feature becomes visible in the demo only after rebuilding `amsdp-appointment`
   (new router, new code) and `amsdp-frontend` (new `next.config.js` rewrite) —
   `docker compose build appointment frontend && docker compose up -d
   appointment frontend`. The database is already migrated and the catalogue is
   already seeded (§6), so no data step is outstanding.
2. A subsequent browser pass should confirm: typing a Bangla word into the
   symptom box keeps the caret (the dialog focus fix), chips appear and can be
   removed, comma completes an unambiguous entry, and the appointment detail
   shows what was recorded. Those are the checks a reviewer should run, and they
   are listed as open item **O-1**.


---

## 13. Documentation updated

| Document | What changed |
|---|---|
| `docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md` | **New** — this report (feature purpose and scope, receptionist workflow, catalogue and sources, search behaviour, ranking, API and database changes, authorization, tests, limitations). |
| `docs/implementation/AMSDP_M4_Appointment_Implementation_Report.md` | New §10: the symptom/onset extension — the two new tables, the two columns, the two endpoints and the four optional booking fields, with its status and its limits. |
| `docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md` | New §13: reuse by the appointment symptom field — which layer is shared, which is not, and the test that pins the difference. |
| `docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` | New §10: the booking dialog now carries the two optional questions, and what that does **not** change about the calendar contract. |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Revision 21: the new report registered under `implementation/` with its real size (`41,972` bytes, from `wc -c`), and a maintenance correction — the tree holds **72** files against 69 registered rows. Rows 69 → 70 for the subject trees; the two `docs/chatgpt/` planning files that the index's `chatgpt/` section described as "one unregistered document" are now listed there (neither moved nor adopted) and the snapshot line states the 70/2 split. No document was moved, renamed or deleted, so no manifest entry is due. |

Deliberately **not** touched:

* `docs/product/AMSDP_Business_Rules_V1.0.md`, `AMSDP_MVP_SCOPE_V1.0.md`,
  `docs/architecture/AMSDP_System_Architecture_V1.0.md` and the other
  owner-controlled documents (`.clinerules` §11) — read, not modified. The
  feature adds an optional data capture inside an approved booking flow; it does
  not change an approved business rule, so no owner document was edited and no
  product decision was silently re-written.
* `docs/chatgpt/AMSDP_Configurable_Multi-Sector_Architecture_Implementation_Plan.md`
  (the post-hackathon roadmap) — the feature has no architectural implication
  for a multi-sector configuration, so the roadmap was left alone as instructed.
  It was **read only**; the only change anywhere near it is the index row that
  now records it exists (§13), which is required by `.clinerules` §12.
* `docs/demo/AMSDP_Limitations_Report_V1.0.md` — owner-controlled (R). The
  limitations of this feature are recorded here (§14) and can be folded in by
  the owner.

---

## 14. Known limitations and deferred work

| Id | Item | Status |
|---|---|---|
| O-1 | **No browser run.** The picker has not been exercised in a real browser; see §12 for exactly what that leaves unproven and what a reviewer should check. | Deferred (needs a browser session) |
| O-2 | **`backend/doctor/tests/test_doctor.py` cannot pass twice against one database** (duplicate mobile 409). Pre-existing, unrelated, demonstrated in §10.3. | Reported, not fixed (out of scope) |
| O-3 | **The running demo images are older than this change.** The catalogue is seeded and the schema migrated, but the appointment and frontend containers must be rebuilt before the feature is visible. | Deployment step, not a defect |
| O-4 | **No editing after booking.** Symptoms and onset are recorded at booking; there is no endpoint to add or correct them later (a `PATCH .../symptoms` would be a small follow-on, with its own audit action). | Deferred |
| O-5 | **No catalogue administration UI, and no catalogue write endpoints.** The catalogue is seeded (and can be edited in the database or by extending `symptom_catalogue.py`). `symptom.manage` exists so a future admin screen has a capability to gate on. | Deferred |
| O-6 | **Age and sex are not used for ranking at all** — deliberately, with the reasoning in §8. If the Product Owner wants them, that is a product decision, not an implementation detail. | Open decision for the owner |
| O-7 | **79 entries, `review_status = curated`.** The wording has not been signed off by a clinician; the UI and the API both say so. A clinical review pass would move the value to `clinically_reviewed` without a schema change. | Deferred (needs a clinician) |
| O-8 | **`text_key` dedupe is casefold + whitespace only** (no nukta composition) on the server. It is a duplicate-suppression key, not a search key; the search normaliser remains single-sourced in the frontend. Two descriptions differing only in nukta form would create two rows. | Accepted, documented |
| O-9 | **Free text is not searchable and not coded.** It is stored verbatim as the patient reported it; mapping it later to a catalogue entry is a clinical-coding feature, explicitly out of scope. | Out of scope |
| O-10 | **`GET /api/v1/symptoms` has no `q` parameter.** Search is client-side by design (§2.3); a server-side search would fork the Bengali normaliser. | Accepted, documented |

Also unchanged and out of scope by the task: patient self-service, patient
login, diagnosis, AI recommendations, triage, prescriptions, Clinical Management
expansion, external clinical systems, calendar redesign.


---

## 15. Governance and skill compliance (`.clinerules` §6)

**Domains identified by §4 routing:** backend API/service endpoints; multi-tenant
data and migrations; authentication/RBAC; frontend UI/components; bilingual
localisation; documentation.

**Documents read before coding** (§12): the docs index
(`docs/governance/AMSDP_Docs_Index_V1.0.md`), the M4 appointment report, the
appointment-calendar report, the BanglaNameSense report, the facility/doctor
frontend report and the design-system report, plus the code they point at
(`frontend/pages/appointments.js`, `frontend/lib/bangla-name-sense/*`,
`backend/appointment/main.py`, `backend/common/{models,permissions,auth}.py`,
`backend/alembic/env.py`, the latest migration, `backend/seed/seed_demo.py`,
`backend/tests/amsdp_test_support.py`, `frontend/lib/auth.js`,
`frontend/next.config.js`, `frontend/tailwind.config.js`,
`frontend/styles/global.css`).

**Skills:** none installed in this workspace (§5). The governance documents
above were used instead, as §4 prescribes, and no skill is claimed.

**Non-negotiables (§3) and how they were met:**

| Rule | Evidence |
|---|---|
| No secret in code, log, report or commit | The migration resolves its DSN from the environment; no credential appears in any new file or in this report |
| Server-side enforcement, tenant from the token | `auth.organization_id` in every query; no `organization_id` accepted from the body |
| Cross-tenant access fails closed and non-disclosing | A foreign symptom id returns exactly the same 422 as an unknown one (test) |
| `organization_id` is the only tenant key | Both new tables carry it; no second tenant column |
| Audit trail append-only | No update/delete path; symptom metadata added to the existing `appointment.created` event; a denial test asserts `request.denied` |
| Denials recorded, never swallowed | `install_denial_audit` covers the new 403/422s (test) |
| Forward-only, idempotent migration | `b3d7e91f6a24`, guarded, applied once, no data rewrite |
| Never claim an unverified capability | §12 says plainly that no browser run happened; the pre-existing failures in §10.3 are reported rather than hidden |
| No destructive git or database action | Nothing committed, staged, reset or cleaned; the only database write this task performed was the additive catalogue seed (§6) |

---

## 16. Git status — nothing committed, nothing pushed

`git status --porcelain` for this task's files (all **uncommitted**):

```
 M backend/appointment/main.py
 M backend/common/models.py
 M backend/common/permissions.py
 M backend/seed/seed_demo.py
 M backend/tests/amsdp_test_support.py
 M frontend/lib/auth.js
 M frontend/next.config.js
 M frontend/pages/appointments.js
 M docs/governance/AMSDP_Docs_Index_V1.0.md
 M docs/implementation/AMSDP_M4_Appointment_Implementation_Report.md
 M docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md
 M docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md
?? backend/alembic/versions/b3d7e91f6a24_add_symptom_catalogue.py
?? backend/appointment/symptoms.py
?? backend/appointment/tests/test_symptoms.py
?? backend/seed/symptom_catalogue.py
?? backend/tests/test_symptom_catalogue.py
?? frontend/lib/symptom-catalogue/
?? frontend/components/SymptomPicker.js
?? frontend/tests/symptom-catalogue-matcher.test.mjs
?? frontend/tests/symptom-catalogue-selection.test.mjs
?? frontend/tests/symptom-picker-contract.test.mjs
?? docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md
```

Confirmed:

* **nothing was staged** (`git diff --cached` is empty);
* **nothing was committed and nothing was pushed**;
* no `git add -A`, no `reset`, no `clean`, no `stash`, no `checkout`;
* the other modified/untracked paths in the tree (design system, doctor and
  facility pages, calendar, deployment files, earlier reports) belong to
  earlier workstreams and were **not** touched by this task — the four
  documents this task edited are listed above with their specific sections in
  §13.

---

## 17. Evidence register

| Claim | Artefact |
|---|---|
| Migration applied | `alembic upgrade head` output: `f7d2b4c6e8a1 -> b3d7e91f6a24`, exit 0 (§4) |
| 25 symptom integration tests pass | `pytest appointment/tests/test_symptoms.py -q` → `25 passed` |
| 9 catalogue data tests pass | `pytest tests/test_symptom_catalogue.py -q` → `9 passed` |
| Appointment suite unchanged plus new | `pytest appointment/tests -q` → `50 passed` |
| Full backend suite | `pytest -q` → `389 passed, 9 failed` — the 9 are the pre-existing doctor-module defect (§10.3) |
| 135 frontend tests pass | `npm test` → `tests 135 / pass 135 / fail 0` |
| Final re-run after the last documentation edit | `pytest appointment/tests/test_symptoms.py tests/test_symptom_catalogue.py -q` → `34 passed`, exit 0; `npm test` → `fail 0`, `exit=0` (no code file changed after these runs — only documentation) |
| Build | `npm run build` → exit 0, `/appointments` 16.7 kB (§11) |
| Catalogue seeded in the demo tenant | direct read: `created 79 updated 0 total 79`, sample rows printed (§6) |
| The demo containers still need rebuilding | `docker exec amsdp-appointment-1 ls /app/appointment/symptoms.py` → `No such file or directory` (the container carries the previous image) (§12) |

**Status summary:** IMPLEMENTED ✅ · TESTED ✅ · BUILD VERIFIED ✅ ·
DOCUMENTED ✅ · BROWSER VERIFIED ✗ (not attempted, stated) · ACCEPTED ✗ (owner's
act) · BLOCKED — none.


---

## 18. Phase 1 — demo runtime rebuild and browser verification (2026-11-16, later the same day)

This section is an **append-only addition**. Sections 1–17 above are left exactly as
written earlier the same day: §12 ("Browser verification — not performed") and the
status line in §17 are the honest record of *that* moment. **Both are now
superseded by this section**, and open items **O-1** and **O-3** are closed. Nothing
above was rewritten, and no other document was moved, renamed or deleted.

Task executed: rebuild the images, recreate only the affected containers, and prove
the symptom field and the onset question actually work in the running instance —
not only in the test suite.

### 18.1 Working tree preserved (first step, before any build)

| Check | Result |
|---|---|
| `git status --porcelain` captured before starting | 67 entries (26 modified, 41 untracked) — the symptom work plus earlier workstreams (design system, calendar, deployment, earlier reports) |
| Same command after every step of this phase | **byte-for-byte identical** to the baseline snapshot |
| `git diff --cached` | empty |
| `git log -1` | `133ce83` (unchanged) |

No `git add`, `reset`, `clean`, `stash`, `checkout` or `revert` was run. No file in
the repository working tree was modified by this phase; the scripts that drove it
live in `/tmp` (`p1_api1.sh`, `p1_book.py`, `p1_read.py`, `p1_search.mjs`,
`p1_browser.cjs`, `p1_hydration.cjs`, `p1_detail.cjs`). The only repository edits
this section adds are this §18 and the index revision, both documentation.

### 18.2 Database state — nothing reset, nothing removed

| Check | Command | Result |
|---|---|---|
| Migration applied | `select version_num from alembic_version` in `amsdp-db-1` | `b3d7e91f6a24` ✅ |
| Catalogue live | `select count(*) from symptom_catalog` | **79** |
| Tenant scope | `group by organization_id` | `demo-org-001|79` — no other tenant has rows |
| Audit trail intact | `select count(*) from audit_events` | **5 320** rows; 2 115 of them `appointment.*` — no row deleted, truncated or rewritten in this phase |

No `alembic downgrade`, no `drop`, no `delete`, no `truncate`, no `seed_demo.py
--reset`. The only writes this phase made to the database are the appointments
created on purpose by the booking tests (§18.6, §18.9) and their audit events.

### 18.3 Image rebuild and container scope

```
docker compose -p amsdp build appointment frontend
  appointment  Built          (symptom router + plan_symptoms/validate_onset)
  frontend     Built          (next build exit 0, new /api/v1/symptoms rewrite)
docker compose -p amsdp up -d --no-deps --force-recreate appointment frontend
  Container amsdp-appointment-1  Recreated / Started
  Container amsdp-frontend-1     Recreated / Started
```

**Deliberately only those two services.** The other seven images were left running:
the two new tables are used only by the appointment service, `symptom.read` /
`symptom.manage` are enforced only there (`common/permissions.check` is evaluated
in the calling service), and no other service maps the new models — so rebuilding
identity/patient/doctor/scheduling/queuing/audit would have restarted six healthy
containers for no behavioural gain. This is a scope decision, stated here so a
reviewer can disagree with it explicitly rather than discover it.

Before → after evidence (the stale-image claim from §12, now closed):

| Probe | Before | After |
|---|---|---|
| `docker exec amsdp-appointment-1 ls /app` | no `symptoms.py` | `main.py`, **`symptoms.py`** |
| `docker exec amsdp-frontend-1 ls /app/components` | no `SymptomPicker.js` | **`SymptomPicker.js`** |
| `docker ps` | both `Up 7 hours` (old images) | both `Up … (healthy)` on the new images |

### 18.4 Health and endpoint verification

| Probe | Result |
|---|---|
| `GET http://localhost:8115/health` / `/health/ready` | `200` / `200` |
| `GET http://localhost:3100/` | `200` |
| `docker ps` health of `amsdp-appointment-1`, `amsdp-frontend-1` | `(healthy)` for both; the other seven services still `(healthy)` |

All endpoint checks below went through **`http://localhost:3100`** — the frontend
proxy — because that is the path the browser actually takes; a direct
`8115` call would not have exercised the `next.config.js` rewrite this feature
added.

| Check | Result |
|---|---|
| `GET /api/v1/symptoms` without a token | **401** |
| `GET /api/v1/symptoms/onset-options` without a token | **401** |
| `GET /api/v1/symptoms` as `receptionist` | **200** — `items: 79`, `max_symptoms: 20` |
| Bilingual completeness | `name_bn` on **79/79**, `name_en` on **79/79** |
| Categories | 13 distinct |
| Review status | every row `curated` (no row claims clinical validation) |
| `onset_options` in the catalogue response | 7 — `TODAY, YESTERDAY, FEW_DAYS, FEW_WEEKS, OVER_MONTH, LONG_STANDING, UNKNOWN` |
| `GET /api/v1/symptoms/onset-options` as `receptionist` | **200**, same 7 codes with `name_bn` + `name_en` |
| `?include_inactive=1` as `receptionist` | **403** (read-only role) |
| `?include_inactive=1` as `org_admin` | **200** |


### 18.5 Appointment creation — the six booking cases, one per symptom/onset combination (API, through the proxy)

Real bookings on the demo doctor's clinic day (`demo-dr-001`, Monday
`2026-11-16`, session 19:00–23:30), one per case, each with a different patient.
Every request carried the full payload the booking dialog sends
(`symptom_ids`, `symptom_texts`, `symptom_onset`, `symptom_onset_note`).

| Case | Request | HTTP | Response `symptoms` | `symptom_onset` | Note |
|---|---|---|---|---|---|
| **S1 no symptoms** | both lists empty, onset `null` | **201** | `[]` | `''` (not asked) | the booking completes with nothing recorded |
| **S2 one symptom** | `['demo-sym-fever']` + `FEW_DAYS` + note | **201** | 1 — Fever / জ্বর | `FEW_DAYS` | note stored verbatim: `প্রায় চার দিন ধরে, সকালে বেশি` |
| **S3 multiple** | fever + cough + headache | **201** | 3 — জ্বর, কাশি, মাথাব্যথা | `TODAY` | order preserved |
| **S4 manually entered** | `symptom_texts: ['বুক জ্বালাপোড়া, খাওয়ার পর বেশি']` | **201** | 1 `kind=free_text` | `''` | no catalogue id involved |
| **S5 onset only** | no symptom, `YESTERDAY` | **201** | `[]` | `YESTERDAY` | the onset answer is a property of the visit, not of a symptom |
| **S6 mixed** | `['demo-sym-headache']` + free text + `FEW_WEEKS` + note | **201** | 2 — 1 catalogue + 1 `free_text` | `FEW_WEEKS` | both `kind`s survive independently |

Response shape (free text keeps its own field, never merged into the catalogue row):

```json
[{"id":"d743…","kind":"free_text","symptom_id":"","name_en":"","name_bn":"",
  "text":"বুক জ্বালাপোড়া, খাওয়ার পর বেশি","recorded_by":"0bc1ae3e…","created_at":"…"}]
[{"id":"024d…","kind":"catalogue","symptom_id":"demo-sym-headache","name_en":"Headache",
  "name_bn":"মাথাব্যথা","text":"","recorded_by":"0bc1ae3e…","created_at":"…"}]
```

**Negative cases (validation happens before any row is written):**

| Case | Request | Result |
|---|---|---|
| **N1 unknown symptom id** | `symptom_ids: ['no-such-symptom']` | **422** `one or more symptoms are not available in this organization` — the same non-disclosing message an id from another tenant produces (that path is covered by the integration tests) |
| **N2 invalid onset code** | `symptom_onset: 'LAST_TUESDAY'` | **422** `unknown onset option` — the vocabulary is closed |

Neither negative case created an appointment row.

**Read-back through the API** (`GET /api/v1/appointments?date=2026-11-16`, and
`GET /api/v1/appointments/{id}`) returned all six with their symptom lists and
onset answers intact — e.g. `T-DEMO-D-003 20:00 → জ্বর, কাশি, মাথাব্যথা, onset TODAY`.
Note the response model reports "not asked" as the empty string: `''` and `UNKNOWN`
are different answers and stay different.

### 18.6 Database and audit evidence for those bookings

`appointment_symptoms` (joined to `appointments`), after the API bookings:

```
19:30|catalogue|জ্বর|
20:00|catalogue|জ্বর|
20:00|catalogue|কাশি|
20:00|catalogue|মাথাব্যথা|
20:30|free_text||বুক জ্বালাপোড়া, খাওয়ার পর বেশি
21:30|catalogue|মাথাব্যথা|
21:30|free_text||ঘাড়ও ব্যথা করে
```

* `kind` is stored explicitly; `text_reported` is only set for `free_text`;
  `name_bn`/`name_en` are the **booking-time snapshot** (5 rows carry a snapshot in
  this run), `recorded_by` is populated on every row, and all 7 rows are
  `organization_id = demo-org-001`.
* `appointments.symptom_onset_code` / `symptom_onset_note`: `NULL` for S1 and S4
  (not asked), `FEW_DAYS` / `TODAY` / `YESTERDAY` / `FEW_WEEKS` for the rest.

Audit `after` payload for one of them (S6):

```json
{"patient_id":"35db59b0…","doctor_id":"demo-dr-001","appointment_date":"2026-11-16",
 "start_time":"21:30","status":"BOOKED","booking_source":"reception",
 "session_id":"03003671…","room_id":"demo-rm-br1-201",
 "location":"First Floor / Cardiology / Chamber 201",
 "symptom_count":2,"symptom_ids":["demo-sym-headache"],
 "symptom_text_count":1,"symptom_onset":"FEW_WEEKS"}
```

The audit entry records **counts, ids and the onset code — never the patient's own
words**; the free-text description stays in the clinical record, not in the audit
trail. That is the intended split and it is what the shipped tests assert.

### 18.7 Bangla and English search, against the live catalogue

The shipped `lib/symptom-catalogue/matcher.js` was executed against the **79 entries
the API actually returned** (not fixtures) — one request, searched in memory:

| Query | Kind | Result |
|---|---|---|
| `fever` | English exact | `fever` (rank EXACT) |
| `fev` | English prefix | `fever` (PREFIX) |
| `chest pain` | English phrase | `chest_pain` (EXACT) |
| `জ্বর` | Bangla exact | `fever` (EXACT) |
| `মাথা` | Bangla partial | `headache`, `dizziness`, `hair_loss` |
| `গা গরম` | Bangla **synonym** | `fever` (EXACT) |
| `পেট ব্যথা` | Bangla phrase | `abdominal_pain` (EXACT) |
| `jor`, `matha betha` | **Romanised / Banglish** | **no match** — see O-11 |
| `zzzqqq` | nonsense | no match → the "as described" row is offered |

`fever` and `জ্বর` resolve to the **same** catalogue id, and `resolveCommit('জ্বর')`
and `resolveCommit('জ্বর জ্বর ভাব')` both complete unambiguously, while
`resolveCommit('মাথা')` correctly declines (three equally good entries).

Both scripts were then confirmed in the real UI (§18.8): the Bangla query rendered
the option `জ্বর`, the English query rendered `কাশি / Cough` — the list shows the
entry in the receptionist's language first and the other script second.

### 18.8 Browser verification — real Chrome, real key events, real focus (O-1 closed)

Tooling actually used: the Playwright **1.63.0** driver already present on this host
(`~/.npm/_npx/e41f203b7505f1fb/node_modules/playwright`) driving the **installed
Google Chrome** (`channel: 'chrome'`, headless). No dependency was added to the
project and no package was installed: the driver and the browser both pre-existed.
The cached Playwright browser build (`chromium-1243`) is not what 1.63 expects
(`chromium-1234` is cached), which is why the system Chrome was used — stated so a
reproducing reviewer is not surprised.

The run signed in through the real login form as `receptionist`, navigated to
`/appointments`, opened the booking dialog and drove the symptom field **entirely
with the keyboard**.

**34 of 35 checks passed.** The checks that passed:

| Area | Evidence from the run |
|---|---|
| Dialog opens with an **empty** picker | 0 chips, the "কোনো উপসর্গ দেওয়া হয়নি" caption visible, `aria-expanded="false"` — nothing is pre-selected |
| **Focus retention while typing Bangla** | `document.activeElement.id` sampled after every keystroke of `জ্বর` → `book-symptoms-input → book-symptoms-input → book-symptoms-input → book-symptoms-input` |
| Bangla search | the listbox appeared with `জ্বর` as the first option |
| Keyboard selection | `ArrowDown` set `aria-activedescendant="book-symptoms-option-0"`; `Enter` created 1 chip |
| Focus after choosing | the caret returned to `book-symptoms-input` and the query was cleared |
| English search | `cough` → `কাশি / Cough` in the list; `ArrowDown`+`Enter` added a 2nd chip; focus retained |
| **Manual entry** | typing `ঘাড় শক্ত হয়ে আছে` offered `“ঘাড় শক্ত হয়ে আছে” / নিজের ভাষায় লিখে যোগ করুন`; `ArrowDown`+`Enter` created a 3rd chip labelled `নিজের ভাষায়`; focus retained |
| Chip removal | the `×` button (`aria-label="সরান: …"`) removed one chip and **focus returned to the search box** |
| Onset | the note input is disabled until an answer is chosen; `ArrowDown`+`Enter` chose `YESTERDAY`; the note then accepted `প্রায় চার দিন ধরে, সকালে বেশি` |
| Whole booking | patient picked through the real patient search (`Karim` → `Md. Abdul Karim`), doctor `demo-dr-001`, date `2026-11-16`, slot `22:00 0/8` clicked from the calendar-derived slot buttons |
| What the browser actually sent | `POST /api/v1/appointments` → **201**; server received `[catalogue:কাশি, free_text:ঘাড় শক্ত হয়ে আছে]`, the free text **verbatim**, `symptom_onset` `YESTERDAY` and the note |
| Confirmation | notice `বুকিং সম্পন্ন হয়েছে — টোকেন: T-DEMO-D-007`; the token survives a full page reload |
| Walk-in dialog | carries the same two questions — combobox `walk-symptoms-input`, onset `walk-onset` — so the second booking path is wired, not just the first |


**The one failing check was the console-hygiene assertion, and it is not this
feature.** The run captured React hydration errors (`Minified React error #418` and
`#423`). A separate baseline run over six pages shows they are app-wide and
pre-existing:

| Page | page errors | hydration-class (#418/#423/#421/#425) |
|---|---|---|
| `/dashboard` | 6 | 6 |
| `/patients` | 2 | 2 |
| `/doctors` | 4 | 2 |
| `/schedules` | 2 | 2 |
| `/appointments` | 2 | 2 |
| `/queue` | 3 | 3 |

`/appointments` — the page this feature changed — sits **at the same baseline as
`/patients`**. The defect class was already known and partly fixed in the frontend
usability task (`components/AppShell.js` now reads `sessionStorage` after mount,
which removed one of them); the remainder is that task's open item, carried here as
**O-12**. Claiming "browser verified, zero console errors" would have been false;
claiming the symptom field causes it would also have been false.

Screenshots from the run were kept **out of the repository** deliberately — ten PNGs
in `/tmp/p1_shots/`: `01-dialog-open`, `02-bangla-search`, `03-one-chip`,
`04-two-chips`, `05-three-chips`, `06-onset`, `07-ready-to-save`, `08-booked`,
`09-after-reload`, `10-detail-dialog`. The machine-readable result is
`/tmp/p1_browser_result.json` (per-check name, pass/fail and observed detail).

### 18.9 The read path a doctor uses — 7/7

The value of recording a symptom is that somebody reads it back. The booking just
made from the browser (`T-DEMO-D-007`) was opened from its calendar chip:

* the chip exists on the calendar: `22:00 · Md. Abdul Karim · T-DEMO-D-007 · BOOKED`
  (41 chips rendered);
* the **detail dialog** shows the **উপসর্গ** row with `কাশি` **and** the patient's
  own words `ঘাড় শক্ত হয়ে আছে`;
* the **কখন থেকে** row shows `গতকাল` with the note `প্রায় চার দিন ধরে, সকালে বেশি`.

That closes the loop UI → API → database → API → UI in one continuous run: **7/7**.

### 18.10 Test data left in the demo database (and who else is writing)

Nothing was deleted (the audit trail is append-only and the brief forbids a reset),
so this phase left **seven** appointments on `2026-11-16`:

* six created by the API matrix, identifiable by `notes = 'phase1 verification S1…S6'`
  (`19:00, 19:30, 20:00, 20:30, 21:00, 21:30`);
* one created through the browser UI at `22:00` (`T-DEMO-D-007`, no notes).

All seven are ordinary `BOOKED` appointments with normal audit events. The owner can
cancel them from the UI if the demo should look clean — not done here, because a
cancellation writes its own audit events and that is the owner's call.

**Observation, not caused by this task:** another session was booking in the same
demo database while this run was in progress (appointments at `11:30` and `15:45`,
actor `dc7e1fc2…`, on `demo-dr-002` and `demo-dr-009`). Two consequences:

* the per-day inventory for `2026-11-16` contains other people's data as well —
  every query in this section is filtered by this run's own markers, so no number
  reported here is inflated by their rows;
* token numbers were observed to **collide across doctors** on the same date
  (`T-DEMO-D-002` is both `demo-dr-001` at 19:30 and `demo-dr-002` at 11:30 — the
  token encodes the doctor's numeric suffix plus the serial, so it is unique per
  doctor, not per day). `_serial_token` is **untouched by this feature** (`git diff`
  shows no hunk near it); recorded as **O-13** for the owner, out of scope here.

### 18.11 Open items — status after this phase

| Item | Status after this phase |
|---|---|
| **O-1** No browser run | **CLOSED** — 34/35 checks in real Chrome plus 7/7 on the read path (§18.8, §18.9); the single failure is the pre-existing hydration noise now tracked as O-12 |
| **O-2** doctor-module test isolation | **Open, unchanged** — not re-run in this phase (no code changed); still the pre-existing `backend/doctor/tests/test_doctor.py` defect |
| **O-3** Demo containers carry the previous images | **CLOSED** — images rebuilt, containers recreated, new code verified inside both (§18.3) |
| **O-4** No editing after booking | Open, unchanged |
| **O-5** No catalogue administration UI / write endpoints | Open, unchanged |
| **O-6** Age and sex not used for ranking | Open decision for the owner, unchanged |
| **O-7** `review_status = curated`, no clinical sign-off | Open, unchanged — the live API confirms all 79 rows still say `curated` |
| **O-8** `text_key` dedupe is casefold + whitespace only | Accepted, unchanged |
| **O-9** Free text is not searchable and not coded | Accepted, unchanged |
| **O-10** No server-side `q` parameter | Accepted, unchanged |
| **O-11** *(new)* **Romanised/Banglish queries do not match** — `jor` and `matha betha` return nothing, so the receptionist sees only the "as described" row and the patient's words are recorded as free text. Not a regression (the normaliser is shared with BanglaNameSense and no transliteration layer was claimed in §7); recorded because a reviewer who types `jor` will notice within seconds | Documented; a transliteration alias layer would be a separate feature |
| **O-12** *(new)* **Page-level React hydration errors** (#418/#423) on every page, including `/dashboard` and `/patients` — pre-existing, inherited from the frontend usability task, not caused by the symptom field (§18.8) | Owner / next frontend task |
| **O-13** *(new)* **Token numbers collide across doctors on the same date** — `_serial_token` is per doctor, not per day (`T-DEMO-D-002` exists for two different doctors on `2026-11-16`) | Out of scope, pre-existing |
| **O-14** *(new)* **Seven verification appointments remain in the demo DB** on `2026-11-16` (§18.10) — not deleted, because a reset is forbidden and audit is append-only | Owner's call to cancel in the UI |
| **O-15** *(new)* **Only `appointment` and `frontend` were rebuilt.** The other seven images still carry the pre-change copy of `common/`; harmless today because no other service checks `symptom.*` or maps the new tables, but the images are not uniform | State to be aware of before the next full rebuild |

### 18.12 Governance and skill compliance for this phase (`.clinerules` §6)

* **Documents read in this phase:** `docs/governance/AMSDP_Docs_Index_V1.0.md`
  (§11/§12 obligations, the Revision 21 row and the maintenance rules),
  `docs/demo/AMSDP_Demo_Credentials_V1.0.md` (to sign in — **no credential from it
  is quoted anywhere in this report or in any log**), `docker-compose.yml` and
  `docker-compose.demo.yml` (to choose the right project, database and port range),
  this report, and the implementation files the phase exercised
  (`backend/appointment/main.py`, `backend/common/permissions.py`,
  `frontend/components/SymptomPicker.js`, `frontend/pages/appointments.js`,
  `frontend/components/AppointmentCalendar.js`, `frontend/lib/auth.js`,
  `frontend/lib/symptom-catalogue/*`).
* **Skills:** none installed (§5 Skills Registry: NONE) — the governance documents
  listed in §4 were the governing material, as §4 requires, and no skill was claimed
  to have been used.
* **§3 non-negotiables honoured in this phase:** no secret, token or credential was
  printed (JWT material was written to `0600` files and referenced by file only);
  tenant scope was read from the token, never from a request body; the negative case
  exercised (unknown symptom id) returns the same non-disclosing 422 that a foreign
  id produces; no audit row was deleted, rewritten or truncated; the migration was
  **verified applied**, not re-applied; nothing destructive was run against Git.
* **§9 execution boundaries:** builds, container recreation, HTTP calls and a real
  browser were run **because the task explicitly asked for them**; the test suites
  were not re-run (no code changed); terminal output was redirected to small files
  instead of dumping large logs; no `/tmp` driver script was added to the repository.
* **§11 documentation placement:** this verification is recorded **in the existing
  implementation report** rather than as a new document — the pattern the facility
  task used (`133ce83`, "record post-rebuild runtime verification in the frontend
  report"). No folder was created, no file moved, no manifest entry is due.

### 18.13 Evidence register for this phase

| Claim | Artefact |
|---|---|
| Migration applied, no reset | `select version_num from alembic_version` → `b3d7e91f6a24`; `symptom_catalog` → 79; `audit_events` → 5 320 |
| Images rebuilt | `docker compose … build appointment frontend` → `appointment Built`, `frontend Built` |
| Only two containers recreated | `up -d --no-deps --force-recreate appointment frontend` → `Recreated` / `Started` for exactly those two |
| New code inside the containers | `ls /app` in `amsdp-appointment-1` → `symptoms.py`; `ls /app/components` in `amsdp-frontend-1` → `SymptomPicker.js` |
| Healthy after rebuild | `/health` 200, `/health/ready` 200, frontend `/` 200, both `(healthy)` |
| Catalogue served bilingually | `GET /api/v1/symptoms` → 79 items, 79 `name_bn`, 79 `name_en`, 13 categories, 7 onset codes |
| Authorization | unauthenticated 401; `include_inactive` 403 receptionist / 200 org_admin |
| Six booking cases | S1–S6 → six 201s with the expected `symptoms` / `symptom_onset` (§18.5) |
| Validation | unknown id → 422; invalid onset → 422; no partial rows written |
| Records written correctly | `appointment_symptoms` 7 rows for the API matrix with `kind`, snapshot names and `recorded_by`; onset columns set / `NULL` as expected (§18.6) |
| Audit carries no free text | `audit_events.after` → counts + ids + onset code only |
| Bangla and English search | matcher run against the live 79 entries: `জ্বর`→`fever`, `fever`→`fever`, synonym `গা গরম`→`fever`, `পেট ব্যথা`→`abdominal_pain`, `zzzqqq`→none (§18.7) |
| Keyboard + focus in a real browser | 34/35 checks, focus trail captured per keystroke; `/tmp/p1_browser_result.json`; 10 screenshots (§18.8) |
| Read path | detail dialog 7/7 (§18.9) |
| Nothing staged, committed or pushed | `git status --porcelain` identical to the pre-phase snapshot; `git diff --cached` empty; `git log -1` = `133ce83` |

**Status summary for §18 (phase 1):** IMPLEMENTED ✅ · TESTED ✅ (the unchanged suite
results of §10) · BUILD VERIFIED ✅ · **RUNTIME VERIFIED ✅** (running stack, rebuilt
images, live database) · **BROWSER VERIFIED ✅** with one stated caveat — the
console-hygiene check fails on app-wide, pre-existing hydration errors (O-12), while
every symptom and onset check passes · DOCUMENTED ✅ (this section and index
Revision 22) · ACCEPTED ✗ (the owner's act) · BLOCKED — none.

