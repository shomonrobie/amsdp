# AMSDP — Appointment Calendar Search & Filter Diagnosis (V1.0)

> **Task:** `AMSDP-APPT-FILTER-DIAGNOSIS` — explain, with evidence, why typing in the
> appointment calendar's search box and choosing a **Status** or **Branch** does not
> change the appointments shown on screen.
> **Date:** 2026-11-16 · **Mode:** diagnosis only — **no fix, no code change, no data change**.
> **Status:** `DIAGNOSED` (root cause identified and reproduced). Awaiting owner decision
> before any implementation.
>
> **→ Update, 2026-11-16: RESOLVED — see Part I.** The owner's follow-up task
> `AMSDP-CALENDAR-FILTER-01` decided both open questions (D-1 branch-scoped, D-2 the search may
> leave the week) and implemented the correction. Part I maps every finding F-1…F-9 to what was
> built and to the evidence; the implementation record is
> `docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` §12.
> Parts A–H below are the *before* measurement and are preserved unedited.
> **Report location rule:** `.clinerules` §11 — written under `docs/audit/` because it is a
> diagnostic/audit record, not an implementation report. Registered in
> `docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 25). No file was moved or renamed,
> so no migration-manifest entry is due.
> **Evidence grading** follows `.clinerules` §7 (IMPLEMENTED / TESTED / VERIFIED / ACCEPTED).
> Every claim below is labelled; anything not verified is named as unverified.

---

## 0. Executive summary

**Root cause in one sentence.** In **Week** and **Day** view the search box and the
Status/Branch pickers only write into the *list* query state; the grid on screen is
rendered from a **different, independent request** (`GET /api/v1/appointments`) that is
built from the calendar window and the doctor only — so those three controls have no code
path into the grid at all.

Consequences, all measured:

1. Typing a patient name in Week/Day fires **zero** HTTP requests (measured: 0), leaves the
   chip count identical (40 → 40), and yet flips the toolbar into its "filtered" state
   (`Clear filters` appears) — the UI *claims* a filter is active while the grid contradicts it.
2. Switching to **List** with the same typed text fires
   `GET /api/v1/appointments/list?q=Tariqul&status=CANCELLED&branch_id=…&date_from=…`
   — proving the state and the debounce are correct. The defect is not in the search input,
   not in the debounce, not in the state, and not in the API.
3. Switching back to Week **keeps** the filters in state but the grid still shows all 40 chips —
   the filters are silently carried and silently ignored.
4. `GET /api/v1/appointments` (the grid endpoint) does not even accept `q` or `branch_id`.
   It does accept `status` but the page never sends it. So:
   * **Status in Week/Day** = frontend-only wiring gap (backend already supports it);
   * **Name/mobile/token and Branch in Week/Day** = capability gap — the endpoint cannot answer them.
5. **List view works** for all of q / status / branch / doctor — but only inside the
   visible week window, and the toolbar exposes no way to widen it (see F-4).

Two things that are *not* the cause, verified so they can be excluded: the backend search
(returns correct filtered sets: name 2/47, mobile 2/47, token 4/47, `CANCELLED` 4/47,
`COMPLETED` 12/47, `BOOKED` 16/47, nothing-matches 0/47 with HTTP 200), and the browser
(no console errors in any scenario, `consoleErrors: []`).

**Decision needed from the owner** before any fix: which scope rule the calendar should
follow (F-3), and whether a search may look outside the visible week (F-4).

## Part A — Findings

| # | Finding | Where | Severity | Class |
|---|---|---|---|---|
| **F-1** | Week/Day grid never receives the search/status/branch filters; the controls write to list-only state | `frontend/pages/appointments.js:284-296` vs `:325-354` | **High** (the reported symptom) | Frontend state/routing defect |
| **F-2** | The grid endpoint has no `q` and no `branch_id` parameter, and the page never sends `status` even though the endpoint accepts it | `backend/appointment/main.py:477-481` | **High** | Missing capability + unused capability |
| **F-3** | Grid is organisation-scoped (47 rows) while the list is branch-scoped (42 rows for the same receptionist) — same control set, two different result domains | `main.py:481` (no scope filter) vs `main.py:131-141` (token scope) | **High** (trust/consistency) | Cross-cutting scope inconsistency (pre-existing **O-S**) |
| **F-4** | The list is silently clamped to the visible week window, overriding any date the query carries, and no UI control can change that window — so a search can never find a row outside the week on screen | `frontend/lib/calendar/list.js:63-71` + `pages/appointments.js:336-341` | **Medium** | API-integration/design defect |
| **F-5** | No result highlighting anywhere in the app (no `<mark>`, no highlight helper) | repo-wide grep | **Low** (UX expectation) | Missing feature |
| **F-6** | An unknown `status` value returns HTTP 200 with 0 rows instead of 422 — fail-silent where the same endpoint fails loudly on a bad date | `main.py:145-146` vs `:96-105` | **Low** (latent: the UI cannot send one) | Inconsistent validation |
| **F-7** | The grid payload carries no patient/doctor/branch **names** and no mobile, so the calendar resolves them with 30 per-id requests per week load and falls back to `#<id>` when a lookup misses | `main.py:181-205` (`_appt_to_dict`) + patient lookup in `pages/appointments.js` | **Low** | N+1 payload design (pre-existing **O-T**) |
| **F-8** | The frontend suite pins the defect: a test asserts the grid request is `{date_from,date_to}`-only, and the list tests assert list wiring separately — so 146/146 green proves nothing about this behaviour | `frontend/tests/appointments-calendar-integration.test.mjs:40-44`, `:72-90` | **High** (governance/evidence) | Test-assertion gap |
| **F-9** | Bengali-script patient-name search could not be exercised end-to-end: the demo dataset contains **0** non-ASCII patient names (30 patients on page 1, `non-ASCII names: 0`) | demo data | **Info** | Evidence gap (not a defect) |

Detail per finding follows.

### F-1 — The three controls are wired to the list path only (root cause)

`frontend/pages/appointments.js` keeps **one** query object and **two** data sources:

```js
// :284  the grid source — the only thing the calendar renders from
const load = React.useCallback(async () => {
  const params = new URLSearchParams({ date_from: range.from, date_to: range.to });
  if (doctorId) params.set('doctor_id', doctorId);          // <- doctor only
  const data = await apiFetch('/api/v1/appointments?' + params.toString());
  setAppointments(Array.isArray(data) ? data : []);
}, [range.from, range.to, doctorId]);                       // <- no q/status/branch dep
```

```js
// :325  the debounce — the ONLY consumer of the typed text
React.useEffect(() => {
  const timer = setTimeout(() => {
    setQuery((q) => (q.q === searchText ? q : setFilter(q, 'q', searchText)));
  }, 300);
  return () => clearTimeout(timer);
}, [searchText]);
```

```js
// :339  the list source — reads the whole query, but only while the list is on screen
React.useEffect(() => {
  if (!user.id || view !== 'list') return undefined;        // <- the gate
  apiFetch('/api/v1/appointments/list?' + listParams) ...
}, [user.id, view, listParams, listTick]);
```

Status (`:716`) and Branch (`:726`) call `setQuery(q => setFilter(q, 'status'|'branch_id', …))`
— the same list-only state. Therefore, in Week/Day:

* `searchText` → `query.q` (state only; nothing reads `query.q` for the grid),
* `query.status` / `query.branch_id` (state only; the grid request never carries them),
* `appointments` (grid data) is unchanged → `AppointmentCalendar` re-renders identically.

`isFiltered(query)` is read by the toolbar (`:692`) **regardless of view**, which is why the
`Clear filters` button appears in Week/Day even though nothing on screen is filtered. That is
the UI-level proof that the state is set and unused (Part E, scenario C2/G1).

### F-2 — The grid endpoint cannot answer two of the three controls

`backend/appointment/main.py:477-481`:

```python
@app.get("/api/v1/appointments")
def list_appointments(
    patient_id: str = Query(None), doctor_id: str = Query(None),
    date: str = Query(None), status: str = Query(None),
    date_from: str = Query(None), date_to: str = Query(None),
    auth: AuthContext = Depends(get_current_user),
):
```

* `q` — **absent**. Measured: `?q=Tariqul` returns **47** rows (the full set, silently ignored).
* `branch_id` — **absent**. Measured: `?branch_id=Gulshan` returns **47** rows (ignored).
* `status` — **present and correct**. Measured: `?status=CANCELLED` returns **4** rows, all
  `CANCELLED`. The frontend simply never sends it.
* `date_from`/`date_to` — present and validated (422 on a bad date, `main.py:497-500`).

So F-1 and F-2 are two independent gaps that produce the same symptom and need different
remedies per control (Part G).

### F-3 — Two result domains behind one toolbar (pre-existing O-S, now measured per role)

| Principal | `/api/v1/appointments/list` (what the toolbar filters) | `GET /api/v1/appointments` (what Week/Day renders) |
|---|---|---|
| `org_admin` (`demo-br-001`) | 47 rows, no branch filter | 47 rows |
| `receptionist` (`demo-br-001`, 1 branch in `/me/branches`) | **42** rows (Main only) | **47** rows (Main 42 + Gulshan 5; those rows report `branch_id: None`) |

`/appointments/list` enforces branch scope **from the token** and returns **404** for an
out-of-scope branch (`main.py:131-141`; measured `recep_list_other_branch_http: 404`) — correct
`.clinerules` §3 behaviour. The grid applies only
`Appointment.organization_id == auth.organization_id`, so a single-branch receptionist sees
another branch's appointments in the calendar. §3 ("cross-branch access fails closed") makes
this governance-relevant, not cosmetic — but changing what a role can see is an owner decision,
so it is **reported, not changed**. Note also the grid rows carry `branch_id: None` in this
dataset, so a client-side branch filter over grid rows would not work either; branch filtering
there needs the same joins the list uses.

### F-4 — The list is clamped to the visible week

`frontend/lib/calendar/list.js:63-71`:

```js
export function buildListParams(query, window = {}) {
  ...
  const from = str(window && window.from).trim() || q.date_from;
  const to   = str(window && window.to).trim()   || q.date_to;
```

and the page always passes the visible range (`pages/appointments.js:336-341`). The window
therefore **wins over anything the query says**, and the toolbar has no date control at all.
Measured consequences on the live data:

* `q=Tariqul` — 2 org-wide, 2 inside 14–20 Nov (coincidence: both happen to fall in the window).
* `q=Md. Abdul Karim` — **5** org-wide, **4** inside the window; the 5th (13 Nov) is
  unreachable until the user pages back a week.
* Token `T-004-001` — 4 org-wide matches; while viewing 14–20 Nov the table showed 2 rows
  (`T-004-001 Shafiqul Alam … 2026-11-16`), and after one `‹` (7–13 Nov) the *other*
  `T-004-001` appeared (`Md. Abdul Karim … 2026-11-13`). Same query, different answer, purely
  because the anchor moved. (Token numbers are per-doctor-per-day serials, so a token is not a
  unique key — that amplifies the effect.)
* Org-wide, **6 of 47** rows sit outside the current window, i.e. invisible to any search right
  now (`2026-11-13`: Md. Abdul Karim, Jamila Begum, Nusrat Jahan, Shahidul Islam, Rokeya Sultana
  + 1; dataset spans 2026-11-13 … 2026-11-19).

`lib/calendar/list.js:10-13` states the view exists so "one appointment can be found among
thousands … filtering an already-fetched week would only ever search the week on screen, which
is precisely the limitation this view removes" — while `:56-62` and the implementation clamp it
to that same week. The file contradicts itself; the implementation follows the clamp. This is
the second UX complaint ("search doesn't find a known appointment") with a completely different
cause from F-1.

### F-5 — No highlighting

`grep -rn '<mark\|highlight' frontend/` yields exactly one hit and it is unrelated
(`components/SymptomPicker.js:184`, a comment). Neither the calendar chip, the list cell, nor
the shared `SearchInput` marks the matched substring. Recorded as a recommendation only
(Part G.4), scoped to name/mobile/token — never a whole cell.

### F-6 — Unknown status fails silently

`main.py:145-146` filters by `status` with no vocabulary check, so `?status=NOT_A_STATUS` →
HTTP **200**, `total: 0` (measured), while `?date_from=nope` → **422**. Fail-closed for dates,
fail-silent for statuses. Latent only: the picker's options come from the shared
`frontend/lib/status.js` LIFECYCLE map, so the UI cannot emit a bad value; a hand-made request
or a future caller can.

### F-7 — The grid payload has no names (30 extra requests per week load)

`_appt_to_dict` (`main.py:181-205`) returns ids, dates, times, status, token, symptoms, notes —
but no `patient_name`, `doctor_name`, `branch_name`, `patient_mobile`. The list endpoint adds
exactly those four (`main.py:194-199`). Measured on the page: a week load issues **1** grid
request plus **30** `/api/v1/patients/{id}` lookups (`patientLookups: 30`) to label the chips; a
missing doctor record degrades a chip to `#<id>` (pre-existing **O-T**). It also means mobile
could not be shown — or highlighted — on a chip without further lookups.

### F-8 — Why a green test suite certified a broken feature

`frontend/tests/appointments-calendar-integration.test.mjs` is a source-contract suite (regex
over the JSX — the project deliberately has no DOM/component-test dependency). Two of its
assertions *encode* the defect:

```js
// :40-44  "the grid asks for one server-side date window per view"
assert.match(page, /new URLSearchParams\(\{ date_from: range\.from, date_to: range\.to \}\)/);
```

```js
// :72-90  list wiring is asserted separately and never tied to the grid
assert.match(page, /'\/api\/v1\/appointments\/list\?' \+ listParams/);
```

No assertion connects the toolbar state to the grid request, so the suite cannot fail for this
reason. Measured: `npm test` → **146 tests, 146 pass, 0 fail, exit 0**
(`/tmp/amsdp_diag/npmtest.log:152-160`) while the feature is unusable in two of three views.
Per `.clinerules` §7 this is precisely why "TESTED" is not "VERIFIED": the suite never asserted
the behaviour, only the shape of the code that lacked it.

### F-9 — Bengali-name search is unverified (data limitation, not a defect)

`GET /api/v1/patients?limit=100` on the demo dataset returns 30 patients, **0** with a
non-ASCII name. The list endpoint's `q` uses `ILIKE` on UTF-8 (`main.py:152-163`) and its
docstring claims Bangla works, and a Bangla string that cannot exist correctly returns
`total: 0` — but a *successful* Bengali-name match was **not** observed. Status: UNVERIFIED;
closing it needs one seeded Bengali-named patient, which is a data change and out of scope here.

---

## Part B — The search pipeline, step by step

Traced from the DOM element to the rendered row. "Week/Day" and "List" answer: *did this step
actually happen in that view?* (measured, Part E).

| # | Step | Code | Week/Day | List |
|---|---|---|---|---|
| 1 | Keystroke reaches the input | `pages/appointments.js:704` `<SearchInput id='appt-search' value={searchText} onChange={setSearchText}>` | ✅ input value became `Tariqul` | ✅ |
| 2 | 300 ms debounce → `query.q` | `:325-331` `setTimeout(… setFilter(q,'q',searchText) …, 300)` | ✅ state set (proved by step 5) | ✅ |
| 3 | A request is issued because `query` changed | `:339-354`, dep array `[user.id, view, listParams, listTick]` | ❌ **0 requests** | ✅ |
| 4 | Correct endpoint chosen | `:284` grid vs `:345` list | ❌ grid (`/api/v1/appointments`) | ✅ `/api/v1/appointments/list` |
| 5 | Search term placed on the wire | `:286-288` (no `q`) vs `buildListParams` (`list.js:63-69`) | ❌ never sent | ✅ `q=Tariqul` |
| 6 | Encoding | `new URLSearchParams(...)` both paths | n/a (nothing sent) | ✅ percent-encoded; Bangla untested (F-9) |
| 7 | Server filters correctly | `main.py:152-163` | ✅ supported *if* sent — 2/47 by hand | ✅ 2/47 |
| 8 | Response reaches the right state | `setAppointments` vs `parseEnvelope`+`setList` | ✅ (arrives unfiltered) | ✅ |
| 9 | The **calendar** renders the filtered set | `AppointmentCalendar` renders `appointments` | ❌ renders the unfiltered window | n/a (no calendar) |
| 10 | Nothing later overwrites the result | `refresh()` `:302-306` calls `load()` | ⚠️ any booking/status change re-fetches the *unfiltered* window | ⚠️ `setListTick` re-issues the filtered query (correct) |

**The pipeline breaks between steps 2 and 3 in Week/Day, and in step 9 the grid renders a set
that was never filtered.** Steps 1, 2, 6, 7 and 8 are individually correct — which is why the
symptom reads as "the search box is broken" while every individual piece works.

Two structural facts make this a *design* defect rather than a typo:

* **Two sources of truth.** `appointments` (grid) and `list` (paged) are fetched by two effects
  with two different filter sets. Nothing forces them to agree, and the toolbar edits only the
  second.
* **The gate is the view, not the data.** `view !== 'list'` short-circuits the only effect that
  consumes `query`, so whether the filters do anything depends on which tab is open — the
  opposite of what a persistent toolbar implies.

## Part C — Per-filter findings

Measured against the live stack (`:3100` Next proxy → `appointment` service), `org_admin`,
dataset of 47 appointments (2026-11-13 … 2026-11-19; 42 Main Branch + 5 Gulshan Clinic).

| Control | Backend support | List view | Week/Day view | Verdict |
|---|---|---|---|---|
| **Search — patient name** | ✅ `Patient.name ILIKE %term%` (`main.py:156`) | ✅ `Tariqul` → 2 rows, all matching; partial `Tariq` → 2 | ❌ 0 requests, chips unchanged (40) | **Broken in Week/Day (F-1/F-2)** |
| **Search — mobile** | ✅ digits extracted from the term, `%digits%` (`main.py:160-162`) | ✅ `01811220007` → 2; `0181-122-0007` → 2 (same rows); 6-digit prefix `018112` → 47 (all demo mobiles share that prefix — correct prefix semantics, not a bug) | ❌ | **Broken in Week/Day** |
| **Search — token** | ✅ `Appointment.token_number ILIKE %term%` (`:158`) | ✅ `T-004-001` → 4 org-wide; the in-window subset is shown | ❌ | **Broken in Week/Day**, plus window clamp (F-4) |
| **Search — appointment id** | ✅ `Appointment.id ILIKE` (`:157`) | ✅ code path present (not separately exercised) | ❌ | **Broken in Week/Day** |
| **Search — Bangla name** | ✅ same ILIKE, UTF-8 | ⚠️ unverified — no Bengali-script names in the demo data (F-9) | ❌ | **Unverified** |
| **Status** | ✅ grid endpoint **and** list endpoint (`main.py:493`, `:633`) | ✅ `CANCELLED` → 4 (all `CANCELLED`); `COMPLETED` → 12; `BOOKED` → 16 | ❌ status never sent → 40 chips regardless | **Wiring gap only (F-1) — cheapest fix** |
| **Branch** | ✅ list (scope + filter, 404 out-of-scope); ❌ grid (no parameter) | ✅ `branch_id=demo-br-002` → 5 (Gulshan); another branch as receptionist → **404** | ❌ parameter does not exist → 47 rows | **Broken in Week/Day (F-2)** + scope divergence (F-3) |
| **Doctor** | ✅ both endpoints (`main.py:489`, `:631`); the only filter the grid sends | ✅ | ✅ the one toolbar control that does affect the grid (it is in `load()`'s deps) | **Works in both** |
| **Date window** | ✅ both endpoints, 422 on a bad date | ⚠️ implicit and inescapable (F-4) | ✅ inherent to the grid | **Works, but not user-controllable in List** |

Notes that matter when fixing:

* Status vocabulary is aligned end-to-end: `frontend/lib/status.js:19-30` (10 appointment states)
  matches the lifecycle map at `backend/appointment/main.py:107-112`. The data contains 9 of
  them (`AWAITING_CONFIRMATION`, `BOOKED`, `CANCELLED`, `CHECKED_IN`, `COMPLETED`, `CONFIRMED`,
  `IN_CONSULTATION`, `IN_QUEUE`, `NO_SHOW`); `RESCHEDULED` exists in both maps but not in the
  current data, so a `RESCHEDULED` filter would legitimately return 0.
* An unknown status is silently accepted (F-6) — worth closing while the wiring is touched.
* Mobile search extracts digits from the *term*, so a mixed `0181-abc` searches `0181`.

## Part D — Week vs Day vs List: consistency of the same state

State persists across a view switch (one `query` object, no reset on `setView`), but the views
consume different subsets of it. Measured with `q=Tariqul`, `status=CANCELLED`,
`branch=Gulshan Clinic`:

| Transition | Requests fired | Chips / rows | What the user sees |
|---|---|---|---|
| Week, no filters | `GET /appointments?date_from=2026-11-14&date_to=2026-11-20`, `GET /me/branches` ×2 | 40 chips, 406 cells | baseline week |
| Week → type `Tariqul` | **none** | 40 chips | nothing changes; `Clear filters` appears |
| Week → `status=CANCELLED` | **none** | 40 chips | nothing changes |
| Week → `branch=Gulshan Clinic` | **none** | 40 chips | nothing changes |
| Week → **List** | `GET /appointments/list?q=Tariqul&status=CANCELLED&branch_id=demo-br-002&date_from=2026-11-14&date_to=2026-11-20&sort=date&order=desc&page=1&limit=25` | 0 rows (no Gulshan+cancelled row matches) | filters take effect — proving steps 1/2/5 work |
| List → **Week** | `GET /appointments?date_from=2026-11-14&date_to=2026-11-20` | 40 chips | filters silently dropped from the grid, still in state |
| Week → `Clear filters` | **none** | 40 chips | no visible change (there was none to clear) |
| Day, fresh | `GET /appointments?date_from=2026-11-14&date_to=2026-11-20` **and** `GET /appointments?date_from=2026-11-16&date_to=2026-11-16` | 18 chips | **two** grid requests for one day |
| Day → type `Tariqul` | **none** | 18 chips | nothing changes |

Two further observations worth recording:

* Day view issues the week request **and** the day request: `gridView = view === 'list' ? 'week' :
  view` (`:279`) keeps `range` meaningful, but the week-range `load()` still runs on mount, so
  the week payload is fetched and discarded. Harmless, one wasted round trip.
* Filter persistence is *correct* (state survives the switch) — which is what makes the defect
  feel like data being ignored rather than a reset.

---

## Part E — Evidence: how this was measured

**Harness.** Headless **Chrome 156.0.8078.73** (`HeadlessChrome/156.0.0.0`) driven over the
DevTools protocol from `/tmp/amsdp_diag/cdp.mjs` + `browser.mjs` / `browser2.mjs` /
`browser3.mjs`; `Network.enable` records every request/response, `Runtime.evaluate` reads the
live DOM (chip count, `role="gridcell"` count, table row count, `#appt-search` value,
`aria-pressed` on the view buttons, whether `Clear filters` is on screen). The Next.js app is
reached through its own proxy on `:3100`, so the URLs below are exactly what the browser issued.

**Roles.** `org_admin` (3 branches available) and `receptionist` (1 branch — Main). Credentials
were read from `docs/demo/AMSDP_Demo_Credentials_V1.0.md` and are **not** reproduced here
(`.clinerules` §3/§12). Tokens were injected into `sessionStorage` the way the app stores them.

**Runtime identity check** (so the reading is of the code actually running):
`frontend/pages/appointments.js` mtime `2026-11-16 17:31:48 +0600` < `amsdp-frontend-1` created
`17:33:58`; `backend/appointment/main.py` mtime `15:51:47` < `amsdp-appointment-1` created
`17:10:27`. Both containers report `healthy`.

### E.1 Scenario run 1 — Week ↔ List ↔ clear (org_admin)

| Step | Action | Requests that carried `/appointments` | DOM |
|---|---|---|---|
| A0 | week view loaded | `GET /api/v1/appointments?date_from=2026-11-14&date_to=2026-11-20` + `GET /api/v1/me/branches` ×2 | chips **40**, cells 406, `aria-pressed=Week`, 30 patient lookups |
| A1 | typed `Tariqul`, waited 2.5 s (debounce 300 ms) | **none** | chips **40**, cells 406 |
| A2 | `status=CANCELLED` (picker value confirmed) | **none** | chips **40** |
| A3 | branch = `Gulshan Clinic` (`demo-br-002`) | **none** | chips **40** |
| B1 | switched to **List** | `GET /api/v1/appointments/list?q=Tariqul&status=CANCELLED&branch_id=demo-br-002&date_from=2026-11-14&date_to=2026-11-20&sort=date&order=desc&page=1&limit=25` | table rendered, 0 rows for that combination |
| B2 | back to **Week** | `GET /api/v1/appointments?date_from=2026-11-14&date_to=2026-11-20` | chips **40** — filters still in state, still ignored |
| A4 | `Clear search` | **none** | chips **40** |

`consoleErrors: []` for the whole run.

### E.2 Scenario run 2 — Day view, list, token search, previous week, doctor

| Step | Action | Requests | DOM |
|---|---|---|---|
| C1 | **Day** view, 2026-11-16 | `GET /appointments?date_from=2026-11-14&date_to=2026-11-20` **and** `GET /appointments?date_from=2026-11-16&date_to=2026-11-16` | chips **18**, `#appt-search` empty |
| C2 | typed `Tariqul` (2.5 s) | **none** | chips **18**, input value `Tariqul` |
| D1 | **List**, `q=Tariqul` | `GET /appointments/list?q=Tariqul&date_from=2026-11-14&date_to=2026-11-20&sort=date&order=desc&page=1&limit=25` | **2 rows**, first `T-002-001 Tariqul Islam 01811220007 Dr. Kamal Hossain 2026-11-19 09:00` |
| D2 | list, `q=T-004-001` | `…&q=T-004-001&date_from=2026-11-14&date_to=2026-11-20…` | **2 rows**, first `T-004-001 Shafiqul Alam … 2026-11-16` |
| E1 | `‹` previous week (same query) | `GET /appointments?date_from=2026-11-07&date_to=2026-11-13` + `…/list?q=T-004-001&date_from=2026-11-07&date_to=2026-11-13…` | **1 row**: `T-004-001 Md. Abdul Karim … 2026-11-13` — the *other* token holder, revealed only by moving the window (F-4) |
| F1 | doctor = `Dr. Fatima Begum` (`demo-dr-001`) | `GET /appointments?…&doctor_id=demo-dr-001` + `…/list?q=T-004-001&doctor_id=demo-dr-001&date_from=2026-11-07&date_to=2026-11-13…` | 0 rows — the doctor filter **is** applied on both paths |

`errors: []` for the whole run.

### E.3 Scenario run 3 — the "UI says filtered, grid says no" proof

Fresh `org_admin` week session, one probe per step:

| State | chips | `Clear filters` on screen | `#appt-search` | `/appointments` requests caused |
|---|---:|---|---:|---:|
| before | 40 | no | `` | — |
| after typing `Tariqul` | **40** | **yes** | `Tariqul` | **0** |
| after `status=CANCELLED` | **40** | **yes** | `Tariqul` | **0** |

The crispest single piece of evidence: the toolbar's own "filters are active" affordance turns on
(`isFiltered(query)` is true) while the grid re-requests nothing, so the two can only disagree by
construction.

### E.4 API probe matrix (independent of the browser)

`GET` through the same `:3100` origin with a bearer token; totals are `total` from the envelope.

| Probe | Result |
|---|---|
| `/appointments/list` (no filters) | 200 · **47** rows · Main 42 / Gulshan 5 |
| `/appointments/list?q=Tariqul` | 200 · **2** · all match |
| `/appointments/list?q=Tariq` | 200 · **2** |
| `/appointments/list?q=01811220007` | 200 · **2** · all match |
| `/appointments/list?q=0181-122-0007` | 200 · **2** (dashes ignored) |
| `/appointments/list?q=018112` | 200 · **47** (prefix; all demo mobiles share it) |
| `/appointments/list?q=T-002-001` | 200 · **4** (token is not unique) |
| `/appointments/list?q=<no such patient>` | 200 · **0** |
| `/appointments/list?status=CANCELLED` | 200 · **4** · all `CANCELLED` |
| `/appointments/list?status=COMPLETED` | 200 · **12** · all `COMPLETED` |
| `/appointments/list?status=BOOKED` | 200 · **16** · all `BOOKED` |
| `/appointments/list?status=NOT_A_STATUS` | **200 · 0** (F-6 — should be 422) |
| `/appointments/list?branch_id=demo-br-001` (own) | 200 · **42** · all Main |
| `/appointments/list?branch_id=<Uttara>` | 200 · **0** (branch has no appointments) |
| `/appointments/list?status=CANCELLED&branch_id=…` | 200 · **3** (filters combine) |
| `/appointments` (grid, window) | 200 · **47** |
| `/appointments?q=Tariqul` | 200 · **47** — `q` **ignored** (F-2) |
| `/appointments?status=CANCELLED` | 200 · **4** · all `CANCELLED` — works, never used |
| `/appointments?branch_id=demo-br-002` | 200 · **47** — `branch_id` **ignored** (F-2) |
| receptionist `/appointments/list` | 200 · **42** (Main only) |
| receptionist `/appointments` | 200 · **47** · branch distribution `{None: 47}` (F-3) |
| receptionist `/appointments/list?branch_id=<other>` | **404** (correct, §3) |
| both endpoints without a token | **401** (correct) |

Window effect, measured separately: window 14–20 Nov = **41** rows, org-wide = **47**, so **6**
rows (all 2026-11-13) are unreachable from the current anchor. `q=Md. Abdul Karim` → **5**
org-wide, **4** in-window.

### E.5 What was *not* measured (honest gaps)

* Bengali-script name matching (F-9) — no such data exists.
* Keyboard-only operation of the search box (`SearchInput` is a shared component with its own
  contract tests; this diagnosis used programmatic input, which is equivalent for the
  state→request question but is not an accessibility pass).
* The list view's sort/paging interaction with a filter (out of scope of the reported symptom;
  `tests/calendar-list.test.mjs` covers the pure model).
* Any behaviour on a real touch device.

---

## Part F — Root-cause classification

Not one bug: four independent causes behind three user complaints.

| Cause | Symptom the receptionist reports | Class | Evidence | Fixable where |
|---|---|---|---|---|
| **C-1** Toolbar state is not bound to the grid's data path (F-1) | "Typing does nothing" / "Status and Branch do nothing" in Week & Day | Frontend state/routing defect | Part E.1 A1–A3, E.3 | `pages/appointments.js` |
| **C-2** The grid endpoint cannot express `q` or `branch_id` (F-2) | Same symptom, but *not* fixable by wiring alone | Missing backend capability (plus an unused `status` capability) | Part E.4 | `backend/appointment/main.py` |
| **C-3** Two result domains (org vs branch) behind one toolbar (F-3) | "The count changes when I switch view" / a colleague's patient appears | Cross-cutting scope inconsistency (governance) | E.4 roles | Owner decision, then one of the two endpoints |
| **C-4** The list's search is clamped to the visible week (F-4) | "Search doesn't find an appointment I know exists" | API-integration / design contradiction | E.2 D2 vs E1; E.4 window | `lib/calendar/list.js` + toolbar UI |

Secondary causes worth folding into the same change: no highlighting (F-5), silent
invalid-status acceptance (F-6), no names in the grid payload (F-7), and a test suite that
asserts the defective shape (F-8).

**Why this survived review:** the calendar refactor
(`docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md`) delivered
the chart, the paged list and the toolbar in one change; each was tested against its own
contract, and the *contract between them* — "the toolbar filters whatever is on screen" — was
never written down or asserted anywhere (F-8). A green suite plus a screenshot of a working
list is exactly the combination that hides C-1.

---

## Part G — Recommended corrections (proposals only — nothing implemented)

### G.1 Two decisions only the owner can make

| Ref | Question | Options | Why it cannot be assumed |
|---|---|---|---|
| **D-1** (= C-3, F-3) | When a branch-restricted receptionist opens the calendar, should Week/Day show **their branch** (like the list) or **the whole organisation**? | (a) Branch-scoped everywhere — the calendar follows the token branch, matching `/list` and `.clinerules` §3; (b) organisation-wide calendar, with the branch picker hidden/disabled for single-branch users | (a) reduces what some roles see in the calendar today; (b) keeps a §3-relevant divergence. Either way the *toolbar must not mean two things*. |
| **D-2** (= C-4, F-4) | May a search look **outside** the week on screen? | (a) No — keep the window, but show it as a visible, clearable filter chip so it is never silent; (b) Yes — a text search drops/widens the date window and says so | (a) preserves the "calendar context" argument in `list.js:56-62`; (b) honours the argument in `list.js:10-13`. The code currently does (a) *silently*, which is the worst of the two. |

Both are behaviour/scope questions (`.clinerules` §1.2), not engineering preferences, so the
diagnosis stops here.

### G.2 Per-cause minimal correction, once D-1/D-2 are answered

| Cause | Smallest correct change | Blast radius | Risk |
|---|---|---|---|
| **C-1** Status in Week/Day | Send `status` from `load()` and add it to the `useCallback` deps (`pages/appointments.js:284-296`). Backend already supports it (measured). | 1 file | **Very low** — no API change, no schema change |
| **C-1 + C-2** Name/mobile/token + Branch in Week/Day | Add `q` and `branch_id` to `GET /api/v1/appointments` (`main.py:477-481`), reusing the *existing* list predicates verbatim (`:131-141` scope, `:152-163` term) rather than re-implementing them; then send the debounced `q` and `branch_id` from `load()` | 2 files (1 backend, 1 frontend) | **Medium** — touches the endpoint every calendar view depends on; needs backend tests for the new params and an `appointment` image rebuild |
| *Structural guard against this class recurring* | Extract the shared predicate block into one helper used by **both** endpoints, and build the grid request from a pure `gridParams(query, range)` builder in `lib/calendar/` mirroring `buildListParams` — a pure builder is what a node test can assert | 3 files + tests | **Medium** — refactor, but puts both paths on one contract |
| **C-3** Scope divergence | Add the token branch scope to the grid endpoint exactly as the list does (**not** a client-side filter — the grid rows carry `branch_id: None` on this dataset, so a client filter would silently empty the calendar) | 1 file | **Medium-high** — changes what roles see; needs an audit note and owner sign-off |
| **C-4** Window clamp | Either expose `date_from`/`date_to` in the toolbar as real filters, or render the implicit window as a chip with a clear affordance (`list.js:63-71` then needs no logic change, only visibility) | 1-2 files | **Low** for (a); **Medium** for (b) |
| **F-6** Silent bad status | Validate `status` against the lifecycle set and raise 422 (same style as `main.py:96-105`) | 1 file | **Low** — no caller sends an invalid value today |
| **F-7** Names in the grid | Add the four list-style fields to the grid payload so chips stop issuing 30 lookups and can show a mobile | 1-2 files | **Medium** — changes a widely-consumed payload (additive only) |

**Recommended order** (once decided): C-1 status → D-2 window visibility → C-1+C-2 q/branch →
D-1 scope → F-6 → F-7. Step 1 alone makes the most-visible complaint ("Status does nothing")
true in Week/Day with a single-file, zero-API change, and is a safe pilot.

### G.3 Test additions this diagnosis shows are missing

1. **A behavioural assertion, not a shape assertion.** A pure `gridParams(query, range)` builder
   plus a test that `gridParams({ status: 'CANCELLED' }, r)` contains `status=CANCELLED` — the
   exact thing `test.mjs:40-44` currently asserts the absence of.
2. **A cross-view contract test:** the same `query` must produce the same filter semantics on both
   paths — both builders must emit `status`, `branch_id` and `q` when set, and neither may
   silently drop a filter the toolbar can set.
3. **A browser-level acceptance check** of the Part E.3 table: type a name in Week view, assert
   that a `/appointments` request carrying `q=` is issued and that the chip count changes; repeat
   for status and branch. This is what lifts the fix from TESTED to VERIFIED (`.clinerules` §7).
   The scenario scripts under `/tmp/amsdp_diag/` are a working starting point.
4. **Regression guards:** no token → 401 on both endpoints; receptionist + other-branch id → 404
   on both (after D-1).

### G.4 Highlighting (recommendation, recorded — not implemented)

No highlighting exists anywhere (F-5). If it is added:

* Highlight **the matched substring only**, in the fields that can match: **patient name, mobile,
  token**. Never the whole cell or row — a filled cell reads as a selection state, and the list's
  rows already carry actionable buttons.
* Match **the same normalisation the server applies** (digits-only for mobile, case-insensitive
  substring otherwise), otherwise the mark will disagree with the result set.
* The calendar chip shows no mobile today (F-7), so mobile highlighting there needs the payload
  change first — do not fake it with an extra lookup.
* It must stay readable in both languages and must not break `aria-sort` / `role="gridcell"`
  semantics; `<mark>` is the correct element, using the theme's warning tone.

### G.5 What the fix must *not* do

* Do not filter the already-fetched window **client-side** as a shortcut: it would define a
  second, divergent notion of "search" over a subset the server never filtered — the same
  reasoning the `list.js:88-92` docstring uses to reject client-side symptom matching.
* Do not hide or disable the toolbar per view: `.clinerules` §3 (a hidden control is not
  authorisation) and it would not be a fix — the control must mean the same thing in every view.
* Do not widen what a role can see in order to make the two views' counts agree (D-1 is the
  owner's call).
* Do not re-implement the scope/term predicates inside the grid endpoint; share them.

---

## Part H — Repository hygiene, reproduction, compliance

### H.1 Files inspected (read-only)

`frontend/pages/appointments.js`, `frontend/components/AppointmentCalendar.js`,
`frontend/lib/calendar/grid.js`, `frontend/lib/calendar/list.js`,
`frontend/components/ui/SearchInput.js`, `frontend/components/ui/Toolbar.js`,
`frontend/components/shared/BranchSelect.js`, `frontend/lib/auth.js`, `frontend/lib/status.js`,
`frontend/tests/appointments-calendar-integration.test.mjs`, `backend/appointment/main.py`,
`backend/common/models.py` (status enum check), `docs/governance/AMSDP_Docs_Index_V1.0.md`,
`docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md`,
`docs/demo/AMSDP_Demo_Credentials_V1.0.md` (credentials consumed, never quoted).

### H.2 Files modified

**None in the repository by this task.** Diagnosis tooling lives outside the tree, in
`/tmp/amsdp_diag/` (`cdp.mjs`, `browser.mjs`, `browser2.mjs`, `browser3.mjs`, `probe.py`, logs and
JSON captures) and is deliberately not committed — it is throwaway evidence, and
`.clinerules` §11 gives no home for scratch tooling.

`git status --short` at diagnosis time — **72 entries, 0 staged**, `HEAD` =
`133ce83 docs(facility): record post-rebuild runtime verification in the frontend report`. The
entries relevant to this diagnosis, with ownership called out:

```
 M backend/appointment/main.py                  pre-existing (symptom-catalogue / list work), NOT mine
 M frontend/pages/appointments.js              pre-existing (calendar + list refactor), NOT mine
 M docs/governance/AMSDP_Docs_Index_V1.0.md    pre-existing edits + this task's Revision 25
?? backend/appointment/tests/test_appointment_list.py   pre-existing, untracked
?? backend/appointment/symptoms.py, backend/seed/symptom_catalogue.py,
?? backend/alembic/versions/b3d7e91f6a24_add_symptom_catalogue.py, ...   pre-existing, untracked
?? docs/audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md       THIS REPORT (new)
```

The remaining entries (`README.md`, `backend/common/*`, `docker-compose.yml`, `_tools/`,
`docs/chatgpt/`, `docs/deployment/*`, most of `frontend/**`) belong to earlier tasks in this
working tree and were **not** touched here.

No file was added, removed, renamed or restored; nothing was staged, committed or pushed
(`.clinerules` §9 — no destructive git operation was run, `git revert` was not needed). The only
repository writes in this task are this report and the index revision that registers it (§12).

### H.3 How to reproduce in five minutes

```bash
# 1. stack up (frontend on :3100, appointment service healthy)
docker compose ps
# 2. API truth, no browser needed
TOKEN=$(curl -s -X POST localhost:3100/api/v1/staff/login -H 'content-type: application/json' \
  -d '{"username":"org_admin","password":"<demo>"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s "localhost:3100/api/v1/appointments/list?q=Tariqul&limit=100" -H "Authorization: Bearer $TOKEN" | head -c 200
curl -s "localhost:3100/api/v1/appointments?q=Tariqul&date_from=2026-11-14&date_to=2026-11-20" \
  -H "Authorization: Bearer $TOKEN" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))'   # -> 47: q ignored
# 3. browser proof: open /appointments, Week view, type a name, watch the Network tab
#    -> zero /api/v1/appointments requests, chip count unchanged, "Clear filters" appears.
#    Switch to List -> the request appears with q=.
```

### H.4 Verification performed (evidence standard)

| Claim | Grade | Evidence |
|---|---|---|
| The three controls produce no request in Week/Day | **VERIFIED** | CDP network capture ×3 runs, 0 requests; reproducible per H.3 |
| The list view filters correctly | **VERIFIED** | browser requests + API matrix (E.2, E.4) |
| The grid endpoint ignores `q` and `branch_id` | **VERIFIED** | E.4 probes (47 vs 47) |
| The grid endpoint supports `status` | **VERIFIED** | E.4 probe (4 rows, all `CANCELLED`) |
| Scope divergence (org vs branch) | **VERIFIED** | E.4 per-role probes (47 vs 42); matches pre-existing **O-S** |
| Week-window clamp | **VERIFIED** | E.2 D2 vs E1; E.4 window counts |
| No highlighting | **VERIFIED** | repo-wide grep (one unrelated hit) |
| Bad status accepted silently | **VERIFIED** | E.4 probe (200 / 0 rows) |
| Bengali-name search works | **UNVERIFIED** | no Bengali-script data (F-9) |
| Frontend suite is green | **VERIFIED** | `npm test` → 146/146, exit 0 |
| Root cause of the reported symptom | **VERIFIED** | code path + request capture + DOM state agree |

Nothing in this report is ACCEPTED — that is the owner's step.

### H.5 Governance and skill compliance (`.clinerules` §6)

* **Domains identified (§4 routing):** frontend UI/components (calendar, toolbar, search input);
  backend API (the two appointment read endpoints); multi-tenant isolation (branch scope);
  audit/evidence standards; documentation (this report + index).
* **Governance documents read and applied:** `docs/governance/AMSDP_Docs_Index_V1.0.md` (read
  first, per §12), the business-rules baselines it registers (`docs/product/AMSDP_Business_Rules_V1.0.md`
  as the authoritative product rule set), `docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md`
  (the feature's own contract), and the adapted agent-rules named by the §4 rows
  (`saas-frontend-ux.md`, `saas-application-security.md`, `saas-multitenant-data.md`) **as adapted**
  in the governance assessment §3 — in particular the §3 non-negotiables on server-side
  enforcement, failing closed with 404, and never trusting a branch id from the request body,
  all of which this report measured rather than assumed.
* **Skills:** **none installed** in this workspace (§5 — verified: no `.clinerules/skills/`,
  `.claude/skills/` or repo `skills/` directory). No skill was used or claimed; the governance
  documents above were the substitute, exactly as §4 prescribes.
* **§3 non-negotiables honoured:** no secret, token or credential is reproduced here (demo
  credentials were consumed only to authenticate probes); no audit event was written, rewritten or
  deleted; no schema change and no migration; the UI was never treated as a security boundary
  (the 401/404 probes went to the API directly); nothing was claimed that was not run.
* **§9 execution boundaries:** read-mostly work. Commands run: `docker ps` / `docker inspect`
  (state only), `git status` / `git log` (read-only), `npm test` (frontend suite, to establish
  F-8), a headless-Chrome session against the running app, and read-only `GET` probes. **No**
  mutating request, no seed/reset, no rebuild, no restart, no destructive git operation.
* **§11/§12 documentation duties:** this report is under `docs/audit/`; the index was updated in
  the same task (Revision 25, one new row, document count **74 → 75**); no migration occurred, so
  no manifest entry is due; no owner-controlled document was modified.

### H.6 Open items recorded by this task

| Ref | Item | Owner |
|---|---|---|
| **O-Z** | **Calendar filters do not reach Week/Day** (F-1/F-2). Fix deferred pending O-AA/O-AB; until then the toolbar must be read as List-only. | Engineering, after decisions |
| **O-AA** | **D-1 — scope rule for the calendar**: branch-scoped like the list, or organisation-wide. Blocks the correct fix for F-3. | **Product Owner** |
| **O-AB** | **D-2 — may a search leave the visible week?** Blocks the correct fix for F-4. | **Product Owner** |
| **O-AC** | **Test-contract gap** (F-8): a source-contract suite certified the defect. Needs a pure `gridParams` builder plus a browser acceptance check before a fix can be called VERIFIED. | Engineering |
| **O-AD** | Bengali-name search unverified for lack of data (F-9) — needs one seeded Bengali-named patient. | Engineering (data) |

### H.7 Handover

The diagnosis is complete and reproducible. **No implementation was started, by instruction.**
The two decisions above (O-AA, O-AB) are prerequisites for the fix; once answered, the sequence in
G.2 makes Week/Day honour **Status** in a single file with no API change, and then
**name/mobile/token and Branch** with a one-endpoint backend addition that reuses the list's
existing predicates rather than re-implementing them.

---

## Part I — Resolution (added 2026-11-16; Parts A–H unchanged)

**This diagnosis was acted on.** Task `AMSDP-CALENDAR-FILTER-01` implemented the correction;
the record of what was built, and the evidence, is
`docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` **§12**.
Parts A–H above are preserved verbatim — they are the measurement of the *before* state and
their wording is not rewritten, in the same way this repository does not rewrite history.

### I.1 What was decided

| Ref | Question | Answer taken |
|---|---|---|
| **O-AA** | D-1 — calendar scope | **Branch-scoped from the token**, exactly like `/list`. Consequence: D-1(a), not (b). |
| **O-AB** | D-2 — may a search leave the visible week | **Yes**, and the calendar must say so: a count-only date index plus a banner with a route to the nearest other date (D-2(b)). |

### I.2 Status of each finding

| Finding | Correction implemented | Verified by |
|---|---|---|
| **F-1** controls wired to the list only | one query object + one `buildFilterParams` feeding grid, list and match index | browser S02/S10/S12 show the grid request carrying `q`/`status`/`branch_id` (§12.7) |
| **F-2** grid endpoint cannot answer `q`/`branch_id` | both accepted, from the same predicate module; `appointment.read` now required | API probes (§12.6) |
| **F-3** two result domains behind one toolbar | grid scoped from the token; a caller-supplied branch may only narrow | receptionist 37 vs admin 41; out-of-scope `404` |
| **F-4** the list is clamped to the visible week | `GET /appointments/matches` — window-independent, counts only, `near` ordering, cap 120 + `truncated` | probe `q=Rokeya Sultana` → `total:2` across two other dates; banner S02 |
| **F-5** no highlighting | `<mark class="appt-cal-hit">` on the name and the token, via `highlightSegments` (never a `RegExp`, never HTML) | screenshots `S02b`/`S02c`; 8 unit tests |
| **F-6** unknown status silent | **422** naming the lifecycle, on all three reads | probe + backend test |
| **F-7** no names in the grid payload | `patient_name`/`patient_mobile`/`doctor_name`/`branch_name` joined into the payload; mobile gated on `patient.read` | probe payload; closes §11 **O-T** for grid cards |
| **F-8** a green suite certified the defect | the old assertion replaced by its opposite; a pure builder is now testable; a browser acceptance run was added | 167 FE / 108 BE green, plus a 24-step browser run |
| **F-9** Bengali-name search unverified | **not fixed** — it is a data limitation; still **O-AD** | — |

### I.3 Open items from this diagnosis

| Ref | Status |
|---|---|
| **O-Z** | **Closed** — the filters reach Week and Day; the toolbar no longer has to be read as List-only. |
| **O-AA**, **O-AB** | **Closed** — answered in I.1 and recorded in the implementation report. Still worth filing in `docs/decisions/` so a later reader cannot reopen them (implementation report §12.9, **O-AG**). |
| **O-AC** | **Closed** — the test contract now asserts the fixed shape, and a real-Chrome run exists. |
| **O-AD** | **Open** — needs one seeded Bengali-named patient; the search is `ILIKE` on the stored name. |

New items discovered *while implementing* (the 120-date cap, cards-per-cell under a filter, the
decision-register gap) are recorded in the implementation report §12.9 as **O-AG**, **O-AH**,
**O-AI**; **O-N** (no human device pass) remains narrowed, not closed. `O-AE` and `O-AF` were
reserved for anticipated findings that the fix did not need — they are left unallocated rather
than back-filled with invented ones.

### I.4 One defect this diagnosis could not have caught

The browser run of the fix found a sentence defect the counts could not see: the banner read
**“1 more matches on 1 other dates.”** A three-key inflection helper plus EN/BN strings fixed it;
the detail is in the implementation report §12.7.1. It is recorded here because it is a lesson
about *this* diagnosis's own method: measuring requests and counts proves the data path, and
still says nothing about the words a receptionist reads.

