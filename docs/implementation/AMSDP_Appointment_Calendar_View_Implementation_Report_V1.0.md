# AMSDP — Appointment Booking Refactored to a Calendar View (V1.0)

> **Task (owner instruction, 2026-11-15):** *"refactor বুকিং to calendar view like standard
> booking system."* The screenshot supplied with the request shows the old surface: a
> `বুকিং` button that opened a dialog with patient / doctor / date / **free-text time**
> fields, plus a flat table with every appointment of the organization.
> **Status:** IMPLEMENTED · TESTED · VERIFIED against the live stack — with one honest
> gap: no browser session was used, so the *pixels* are unverified (§9, **O-N**). The
> markup the component emits is verified by a server-render test (§7.4).
> **Report location:** `docs/implementation/` — the `.clinerules` §11 subject folder for
> "what was built, and how was it tested".
>
> **Later additions (append-only; earlier sections keep their original wording):** §11 — the
> list view, paging and the toolbar's filters (2026-11-16); **§12 — those filters now reach
> Week and Day as well, with a cross-date match index (2026-11-16, task
> `AMSDP-CALENDAR-FILTER-01`, closing the browser gap of §11.9 **O-N** — narrowed — and
> resolving **O-S** and **O-T**).**

---

## 1. What was built

The appointment surface is now **calendar-first**:

| Before | After |
|---|---|
| `বুকিং` opened a 5-field dialog; **time was typed by hand** | Week/day **grid**; an empty cell is a `+` that books that doctor, date and time |
| No schedule awareness — any time on any date could be entered | Cells are drawn from the doctor's published `slot_templates`; each slot shows `booked/capacity` and refuses a full slot |
| One flat table, `slice(0,50)` | **সপ্তাহ / দিন / তালিকা** views; the table is preserved as the list view with no page-level cap |
| Patient chosen from the first 100 patients in a `<select>` | Patient **type-ahead** on `GET /api/v1/patients?q=` (name or mobile) |
| Cancelling a booking required the row's inline buttons only | Clicking a chip opens the appointment, with the same state-machine actions and cancel-with-reason |

Everything the receptionist could do before still works: create booking, walk-in,
confirm, check-in, move to queue, complete, cancel with a mandatory reason.

## 2. Screens and behaviour

**Toolbar** — `‹` `আজ` `›`, the range label (`১৪ – ২০ নভেম্বর ২০২৬` in Bangla numerals),
a doctor filter, the `সপ্তাহ | দিন | তালিকা` switch, `বুকিং` and `ওয়াক-ইন`.

**Week grid** — 7 columns starting **শনিবার** (the working week in Bangladesh), a sticky
time gutter, a sticky day header carrying that day's appointment count, today marked with
`aria-current="date"`. Each cell shows the appointments in it as chips
(`status colour · patient name · token`), a `+` when it is bookable, `পূর্ণ` when full,
`শিডিউল নেই` when the doctor publishes no clinic that weekday, `শেষ` for a past date.
The grid scrolls inside a 68 vh box instead of pushing the page down — the real week has
37 rows (§7.3).

**Day view** — same grid, one wide column; clicking any day header switches to it.

**List view** — the previous table (Token, Patient, Doctor, Date, Time, Status, Actions).

**Booking dialog** — patient search, doctor, date, then a **slot picker** where each button
reads `09:15 2/4` and a full slot is disabled. When the doctor has no schedule that day the
dialog says so and offers a free time field, so the old workflow is never blocked.
Saving POSTs the same payload as before (`booking_source: 'reception'`) and reports the
issued token.

**Appointment dialog** — patient, doctor, date, time, token, status, source, notes, plus the
actions the status machine allows; cancelling reuses the shared `ConfirmDialog` with a
required reason.

## 3. Design decisions, and the traps they avoid

1. **The grid must never hide a booking.** A naive slot grid silently drops any appointment
   whose `start_time` is not on a slot boundary — and the demo data contains `02:45` and
   `21:30`. The row axis is therefore the **union of slot starts and appointment times**
   (`gridTimes`). Proven by the live probe in §7.3: *no appointment time is missing from
   the axis: true*.
2. **Two week indexes, named apart.** `Schedule.slot_templates[].day_of_week` is
   **0 = Monday** (`backend/seed/seed_demo.py:101` — "Mon-Fri clinic", `day_of_week: 0` on
   every doctor). The display week starts Saturday. `pythonWeekday()` and `jsDay()` are
   separate exported functions so no future edit can quietly mix them.
3. **Capacity mirrors the server.** A cell's capacity comes from the template covering that
   time and falls back to `1`, exactly what `create_appointment` does when no template
   matches (`max_patients`, `max_capacity = 1`). Cancelled / no-show rows still display but
   do not consume capacity (`ACTIVE_STATUSES`). The browser is not the authority: the POST
   is still validated server-side.
4. **Combined "all doctors" mode is honest.** With no doctor filter the grid is a union of
   every doctor's hours, so the per-cell `booked/capacity` caption is suppressed and the `+`
   picks a doctor with capacity in that slot (`preferredDoctor`); when nobody has capacity
   it opens the doctor who *does* publish the slot, so the dialog shows it as full instead
   of offering a time nobody works.
5. **Pure model, thin component, tested page contract.** The arithmetic lives in
   `frontend/lib/calendar/grid.js` with no React, DOM or `fetch`, so `node --test` exercises
   the same code the browser runs — the split `lib/bangla-name-sense/*` already established.
   `AppointmentCalendar.js` only renders. The page's contract is pinned by a source test.
6. **Additive backend change only.** One new optional filter; no schema change, no
   migration, no change to any existing query semantics or permission.
7. **No new dependencies, no global CSS edit.** `frontend/package.json` is untouched. The
   calendar's styles are inline, like the rest of the pages, deliberately leaving
   `frontend/styles/global.css` alone — it carries unrelated uncommitted work (**O-M**).

---

## 4. Backend change — one optional, backwards-compatible filter

`backend/appointment/main.py`, `list_appointments` only:

```python
date_from: str = Query(None), date_to: str = Query(None),
...
if date_from:
    try: window_start = datetime.strptime(date_from, "%Y-%m-%d").date()
    except ValueError: raise HTTPException(422, "invalid date_from, use YYYY-MM-DD")
    q = q.filter(Appointment.appointment_date >= window_start)
if date_to:
    try: window_end = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError: raise HTTPException(422, "invalid date_to, use YYYY-MM-DD")
    q = q.filter(Appointment.appointment_date <= window_end)
```

* **Inclusive** `[date_from, date_to]`; either bound may be omitted.
* **Fail-closed on a typo.** A malformed bound answers `422` instead of being ignored — an
  ignored bound silently widens the result to "every appointment in the organization",
  which for a calendar is the wrong failure direction. (The pre-existing single `date`
  filter keeps its historical ignore-on-parse behaviour; it was not touched.)
* **Tenant scoping unchanged.** The `organization_id == auth.organization_id` filter is
  still applied first; there is no new path to another tenant's rows. The new test
  `test_window_never_crosses_the_tenant_boundary` proves it with two organizations.
* **Why it was needed:** the calendar asks once per visible range. Without it the page would
  have to fan out to seven single-date requests per week — seven round trips, seven chances
  to render a half-loaded week.
* No migration: no column, index or constraint changed.

## 5. Files

| File | Lines | State | What it is |
|---|---:|---|---|
| `frontend/lib/calendar/grid.js` | 378 | **new** | Pure model: date maths, week/day ranges, template expansion, capacity, bucketing, grid axis, cell state, Bangla/English labels |
| `frontend/components/AppointmentCalendar.js` | 166 | **new** | Presentational grid: sticky header + time gutter, chips as buttons, `+` cells, 68 vh scroll box |
| `frontend/pages/appointments.js` | 638 | **rewritten** | Toolbar, week/day/list, booking dialog with slot picker and patient type-ahead, appointment dialog, walk-in, cancel-with-reason |
| `frontend/tests/calendar-grid.test.mjs` | 227 | **new** | 15 unit tests over the pure model |
| `frontend/tests/appointments-calendar-integration.test.mjs` | 90 | **new** | 8 contract/regression tests over the page and component sources |
| `frontend/tests/calendar-render.test.mjs` | 188 | **new** | 6 tests that server-render the real component and assert on the emitted HTML (§7.4) |
| `backend/appointment/main.py` | +11 | modified | `date_from` / `date_to` on `GET /api/v1/appointments` |
| `backend/appointment/tests/test_appointment.py` | +65 | modified | `TestAppointmentCalendarWindow` — 6 tests |

Nothing else was modified. `frontend/styles/global.css`, `frontend/package.json`,
`docker-compose.yml`, the alembic chain and `docs/product/` are untouched by this task.

## 6. Tests — what was run, and what came back

| Suite | Command | Result |
|---|---|---|
| Frontend unit + contract (`node --test`) | `cd frontend && npm test` | **72 passed, 0 failed** — 43 pre-existing + 15 model tests (`calendar-grid`) + 8 contract tests (`appointments-calendar-integration`) + 6 render tests (`calendar-render`) |
| Frontend production build | `cd frontend && npm run build` | **exit 0**; `ƒ /appointments 9.87 kB` (was 5.1 kB), no type/lint error |
| Backend appointment suite | `cd backend && set -a; . ../.env; set +a; ../.venv/bin/python -m pytest appointment/tests -q` | **25 passed, 0 failed** (19 previous + 6 new) |
| Container build | `docker compose -p amsdp up -d --build appointment frontend` | `appointment Built`, `frontend Built`, both recreated and healthy |

The new model tests cover: timezone-safe `YYYY-MM-DD` round-trips, month/year/leap
arithmetic, Saturday week start, `0 = Monday` weekday mapping, 15-minute slot expansion,
inactive schedules, overlapping templates, capacity fallback to 1, half-open intervals,
defensive time parsing, bucketing (including time-less serial rows and malformed rows),
off-grid rows, the 09:00–17:00 fallback ladder, every cell state (open / full / closed /
past), range navigation, and Bangla/English labels.

The new contract tests assert the things a refactor of this size can silently break: the
page still uses the shared component and the tested model, it requests one server window,
the booking payload is unchanged, walk-in / check-in / status / cancel-with-reason are all
still wired, the list view keeps its columns, the grid stays keyboard reachable
(`role="grid"`, `role="gridcell"`, `aria-current`, labelled `+` buttons), and off-grid
appointments still get a row.

The six render tests (§7.4) are the only ones that see markup, and they exist because
`node --test` has no DOM: everything above reasons about source text or about the model,
not about what React actually emits. They add **no dependency** — the JSX compiler
(`next/dist/build/swc`) and the renderer (`react-dom/server`) are already installed.

---

## 7. Verification against the live stack

All figures below come from the running dev stack (`docker compose -p amsdp`, frontend on
`http://localhost:3100`) after the image rebuild, authenticated as the demo
`receptionist` through the frontend proxy. No credential is reproduced here.

### 7.1 The range filter behaves as specified

| Probe | Result |
|---|---|
| `GET /api/v1/appointments?date_from=2026-11-14&date_to=2026-11-20` | `200`, **9 rows**, dates `2026-11-15` (8) and `2026-11-16` (1); **0 rows outside the window** |
| `GET /api/v1/appointments?date=2026-11-15` (pre-existing filter) | `200`, **8 rows** — unchanged behaviour, consistent with the window above |
| `GET …date_from=16-11-2026` | **`422`** `invalid date_from, use YYYY-MM-DD` |
| `GET …date_to=tomorrow` | **`422`** |
| `GET …&date_from=…&date_to=…&doctor_id=demo-dr-001` | `200`, 2 of the 9 rows, all belonging to that doctor |
| `GET /api/v1/schedules` / `GET /api/v1/doctors` | `200`, 5 schedules / 5 doctors |
| `GET /appointments`, `/schedules`, `/queue` | `200`, `200`, `200` |

### 7.2 The rebuilt image is what is running

`docker inspect` shows `amsdp-frontend-1` started after the last source edit; the served
client chunk `/app/.next/static/chunks/pages/appointments-*.js` contains both
`appt-cal-wrap` (the new component) and `68vh` (the new scroll box).

### 7.3 What the calendar computes for the real week

`/tmp/render_probe.mjs` (a throw-away probe, not committed) imported the **shipped**
`lib/calendar/grid.js` and fed it the live API responses:

```
today               : 2026-11-15 (pythonWeekday 6)
visible week        : 2026-11-14 .. 2026-11-20 | ১৪ – ২০ নভেম্বর ২০২৬
appointments in week: 9 | active: 6
schedules           : 5
grid rows           : 37 (09:00 → 21:30)
col/days with clinic: 11-14:0 11-15:0 11-16:20 11-17:16 11-18:0 11-19:16 11-20:0

TIME  11-14    11-15    11-16    11-17    11-18    11-19    11-20
09:00 ·        T-001-003+        +        ·        +        ·
09:15 ·        T-002-004+        +        ·        +        ·
...
15:15 ·        T-DEMO-D-+        +        ·        +        ·
...
21:30 ·        ·        T-DEMO-D-+        ·        +        ·

no appointment time is missing from the axis: true
```

Read this carefully, because it is the honest picture of the demo data:

* the week really has **37 rows** (five doctors × 15-minute slots spanning 09:00–18:00,
  plus the off-grid `21:30` booking) — exactly why the grid got its own 68 vh scroll box
  with a pinned header;
* only **Monday (11-16), Tuesday (11-17) and Thursday (11-19)** publish clinic hours,
  because the seeded `day_of_week` values are 0–3 (Mon–Thu);
* appointments on days *without* a published schedule (`11-15`, Sunday) are still rendered
  as chips, and the `21:30` booking still gets a row. Nothing is hidden by the schedule.

### 7.4 The component actually emits a calendar (server-rendered markup)

§7.3 proves the model; it says nothing about the JSX. To close that gap without a browser
and without a new dependency, `frontend/tests/calendar-render.test.mjs` compiles
`components/AppointmentCalendar.js` with the SWC binary that ships inside Next
(`next/dist/build/swc`, already a direct dependency) and renders it with
`react-dom/server`, then asserts on the resulting HTML string. Real component, real props,
real markup — run by the ordinary `npm test`.

| What the emitted HTML was checked for | Result |
|---|---|
| wrapper `.appt-cal-wrap` carrying the `68vh` scroll box | present |
| `role="grid"` with the Bangla `aria-label` | present |
| day headers / gridcells form a full rectangle (7 days × N rows) | 7 headers, `rows × 7` cells |
| `aria-current="date"` marks today | exactly once |
| one chip per appointment, cancellations struck through, token + patient on the chip | 4 of 4, none hidden |
| row axis from real props | `02:45, 09:00, 09:15, 09:30, 09:45, 21:30` — the two off-grid bookings included, sorted |
| `+` offered on the published slots of an open day | `09:00, 09:15, 09:30, 09:45` + `21:30` |
| `+` suppressed where the slot is full | `02:45` holds a booking and no template covers it → capacity 1 → full, no `+` |
| `+` suppressed on a spent day | 0 buttons when `today` is later in the week |
| `booked/capacity` caption on a multi-patient slot | `2/4` present |
| `শিডিউল নেই` on weekdays with no published hours, `সময় শেষ` on past open cells | both present, and absent when they should be |
| day view | one column, `rows` cells, today still marked |

Reaching these assertions took four corrections, and every one was to the *test*, not the
component: the Bangla day-number pattern guessed the wrong week (`২৩`+ instead of `১৪`–`২০`);
the first `+` count was 0 because that fixture had already made the day **past**; the chip
pattern assumed `title` immediately follows `type` (React emits `style` between them); and on
an open day the count is 5, not 4 — the `02:45` row is **full** at capacity 1 while the
empty `21:30` row is offered. Recorded because a test that has never failed has not been
shown to check anything, and because each correction was the model teaching the test what
the correct behaviour actually is.

The probe of this section is a committed test; the throw-away `/tmp` scripts of §7.3 are not.

## 8. Governance and skill compliance

Per `.clinerules` §2 and §6.

| Domain (`.clinerules` §4) | Applied | Evidence |
|---|---|---|
| Frontend UI / components / pages / a11y / responsive | `saas-frontend-ux.md` (as adapted, Assessment §3), `docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md`, `frontend/lib/i18n.js`, `frontend/components/` | shared `Modal`, `ConfirmDialog`, `RequireLogin` and existing global CSS classes reused; chips/toolbar/slot picker are real `<button>`s with labels; grid is `role="grid"` with `aria-current` — asserted on emitted markup in §7.4, not just in source; Bangla-first labels, Bangla numerals for dates; the week starts Saturday |
| Backend API | `saas-application-security.md` (adapted), Business Rules Part II | one additive read filter; no new endpoint; the `422` idiom follows `/schedules/{id}/available-slots` |
| Multi-tenant data | `saas-multitenant-data.md` (adapted), Business Rules §4–§6 | organization scope is still the first filter; a new test proves a second organization's window is invisible |
| Auth / RBAC | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–§8 | no permission changed; booking buttons stay gated to `super_admin / org_admin / branch_admin / receptionist`; every write still passes the service's own `require_permission` |
| Documentation | §11, §12, `AMSDP_Docs_Index_V1.0.md` | this report; index Revision 18 |

**Skills:** `.clinerules` §5 — **no skill packages are installed** in this workspace
(no `.clinerules/skills/`, no repo `skills/`, no Cline skill configuration). No skill was
used and none is claimed; the governance documents were used instead and are cited above.

**Non-negotiables checked:** no secret is logged or printed (the demo password is expanded
from `.env` and never echoed; session tokens live in `umask 077` temp files deleted on
exit); access control is still enforced server-side and the UI is not treated as the
boundary; no audit row is written, altered or deleted by this change; there is no schema
change, so no migration is owed.

## 9. Limitations and open items

**O-N — no browser session was used.** The page is client-rendered (every page here returns
an empty shell from `getServerSideProps` and hydrates from `sessionStorage`), so `curl`
cannot show the rendered grid. What *is* verified: the production build compiles the page;
the served bundle contains the new component; the live API returns exactly the data the
model consumes; the model produces the grid in §7.3; and the component's **emitted markup**
is asserted in §7.4 (real component, real props, server-rendered — structure, labels,
cells, chips, `+` behaviour). What is **not** verified: pixel layout, chip overflow on a
narrow screen, and the click paths themselves. Treat visual acceptance as pending a human
look; it is the only part of this feature that no automated check covers.

**O-R — an empty out-of-hours row offers a `+`.** On a day that publishes clinic hours, a
row that exists only because some appointment sits outside those hours (e.g. the demo's
`21:30`) is still clickable for a new booking, at the API's fallback capacity of 1. That
matches the backend — which accepts such a booking — and the dialog already supports an
out-of-hours time by hand when a day publishes nothing. Whether the grid should suppress
`+` on rows outside the published window is a business decision, so the current behaviour
is pinned by a test and left for the owner rather than changed silently.

**O-O — the seeded schedules do not cover the whole week.** Three of seven days show
`শিডিউল নেই` because `day_of_week` 0–3 is all the demo data has. The grid is right; the demo
data is thin. Changing the seed would change demo data, which this task did not own.

**O-P — the demo data contains bookings outside clinic hours** (`21:30`, `02:45`, odd-minute
times). They display correctly but make the week look untidy. Data, not code.

**O-Q — appointment reads are still organization-scoped, not branch-scoped.** `GET
/api/v1/appointments` filters by organization only (unchanged), so the calendar shows the
whole organization's bookings while the doctor list honours the active branch. Making reads
branch-aware is a business-rule decision the owner has not asked for, so it was not taken
here.

**O-M (carried)** — `frontend/styles/global.css` still carries unrelated uncommitted work;
this task deliberately did not touch it. It is inside the rebuilt image either way.

Nothing was committed, staged or pushed. No document was moved, renamed or deleted.

---

## 10. Later addition — optional symptoms and onset in the booking dialog

A later task (AMSDP-SYMPTOM-01, 2026-11-16) added two **optional** controls to
the booking and walk-in dialogs on this page: a bilingual symptom picker with
removable chips and free text, and a seven-answer onset question. See
`docs/implementation/AMSDP_Appointment_Symptoms_and_Onset_Implementation_Report_V1.0.md`.

What it does not change, and therefore what this report's contract still holds:

* the slot picker, the capacity display, the patient search, the doctor/date
  bindings and the `POST /api/v1/appointments` fields it documents are untouched;
  the request gains four optional keys and nothing else;
* the calendar grid, its SSR contract tests and the `date_from`/`date_to` window
  are unchanged;
* the dialog still renders through `components/ui/Modal` → the Radix `Dialog`,
  and the new picker owns no effect, so the focus-loss fix documented in
  `AMSDP_Frontend_Usability_Shared_Design_System_and_Demo_Readiness_V1.0.md`
  remains in force (`frontend/tests/dialog-focus.test.mjs` still passes).



---

## 11. Later addition — appointment cards, a shared toolbar and a paged list view (2026-11-16)

A later task, `AMSDP-APPT-LIST-UX` (2026-11-16), refactored the appointment surface's
*interface*: what a card says, what the toolbar offers, and a `তালিকা` view that searches
and pages **on the server** instead of slicing a week that is already in memory. The
constraint was explicit and is what makes this section short: **no scheduling, lifecycle
or queue rule changed.** `POST /api/v1/appointments`, the status transitions, check-in,
cancel-with-reason, walk-in, the slot picker, capacity and the symptoms/onset fields are
byte-for-byte the request paths documented in §1–§10. The only backend change is one new
read-only route.

### 11.1 What changed, in the order a receptionist meets it

| Surface | Before | After |
|---|---|---|
| Page opening | an ad-hoc row of `<select>`/`<button>` elements | `PageHeader` (title, one-line purpose, live meta) + `Toolbar`/`Filter`/`SearchInput`/`Select`/`BranchSelect` from `components/ui/` |
| A grid card | name, then a doctor/time fragment; status carried by colour only | patient first, token at the right, `time · doctor` on one line, the status **in words** as well as colour, then the chamber snapshot |
| A crowded cell | the fourth card overflowed the cell silently | `chipLayout()` keeps three and renders `আরও N` — a control that opens the day view when the grid can, a plain count when it cannot |
| List view | the whole week's rows, sorted client-side, no search, no paging | `GET /api/v1/appointments/list`: search, filter, whitelisted sort, 25/50/100 pages, an honest total and a windowed pager |
| Status vocabulary | page-local `STATUSES`/`ACTION_LABEL` maps, English only, duplicating `lib/status` | one source: `statusLabel()` for the filter options, the badges and the action buttons |
| Actions on a row | `CHECKED_IN` appeared twice for a confirmed appointment | check-in is offered where the transition list does not already contain it |
| Detail dialog | no chamber; the raw enum as the status | `StatusBadge` plus a `কক্ষ` row with `location_label` |

### 11.2 The card, and why it looks like that

`Chip` in `components/AppointmentCalendar.js` is a `<button>` — opening an appointment has
to be reachable by keyboard — laid out as four one-line rows so a long Bangla name cannot
push the status out of the cell:

```
● Tariqul Islam              T-002-001     ← name (flex, ellipsised) + token
10:00 · Dr. Nasrin Akter                   ← time · doctor
কিউতে                                      ← status, in words, in the status colour
First Floor / Cardiology / Chamber 101     ← the booking-time chamber snapshot
```

The tooltip keeps the machine status (`… · IN_QUEUE`) so the card's *visible* text can be
localised without losing the value a test or a support call needs. `aria-label` reads in
the same order as the card.

Overflow is decided by the pure model, not by CSS: `chipLayout(items, { max })` returns
`{ shown, hidden, overflow }` and `moreLabel(template, hidden)` renders a translated
`আরও 1` (falling back to `+1` when no template is supplied). The week view caps a cell at
three cards, the day view passes `Infinity` because the column has the room. Clicking
`আরও N` opens that day; without an `onDayClick` handler the same text renders as a
non-interactive summary rather than a button that does nothing.

### 11.3 The toolbar

`SearchInput` (debounced 300 ms before it becomes a request, so the caret never jumps),
a doctor `Select`, a status `Select` whose options are the lifecycle in `lib/status`'s
own words, and a `BranchSelect` that appears only when `GET /api/v1/me/branches` returns
more than one branch — a one-branch user is offered no choice they do not have. The
branch picker is a *filter*, never an authorisation decision: the API scopes by token and
an out-of-scope id answers `404`, which §11.6 confirms live.

`ফিল্টার মুছুন` appears only when something is actually filtered (`isFiltered(query)`),
and it clears the search box, the doctor selection and every query field together — one
handler, because the doctor filter is state shared by the grid and the list.

### 11.4 The list view, and the endpoint behind it

**`GET /api/v1/appointments/list`** (new, read-only; `backend/appointment/main.py`):

| Part | Behaviour |
|---|---|
| `q` | patient name, appointment id, token number, and the patient's mobile with punctuation stripped — so `017-0000` and `0170000` agree. LIKE metacharacters are escaped (`%`, `_`, `\`), so `q=%` matches nothing instead of everything |
| `doctor_id`, `status`, `branch_id`, `date_from`, `date_to` | equality/range filters, `date_*` inclusive, `422` on a malformed bound |
| `sort`, `order` | whitelist `date, patient, doctor, branch, status`; an unknown key answers `422` naming the valid set, never a silent fallback. Date sorts newest-first with time ascending inside a day; the other columns get a stable date/time tie-break |
| `page`, `limit` | `page ≥ 1`; the UI sends only 25/50/100, the API itself clamps at 100 |
| envelope | `{items, total, page, limit, pages}` — `total` counts the *filtered set*, before the page is sliced |
| scope | branch derived from the token, never from the query string; an out-of-scope `branch_id` answers `404 not found`; no token → `401`; `patient.read` gates `patient_mobile` in the payload |
| route order | declared **before** `GET /api/v1/appointments/{appointment_id}`, so `list` is never swallowed as an id |

**`frontend/lib/calendar/list.js`** (new, pure — no React, no fetch) owns the client half:

| Export | Job |
|---|---|
| `emptyQuery()` | the list's opening state: page 1, 25 rows, `date desc` |
| `normaliseQuery()` | coerces an arbitrary object into something the API accepts; drops unknown keys, refuses an unsupported sort or page size *here* rather than shipping it and taking a 422 |
| `setFilter()`, `clearFilters()`, `setPage()`, `setLimit()`, `toggleSort()`, `ariaSort()` | one state transition each; every filter change and every page-size change returns to page 1 |
| `buildListParams(query, window)` | the request: blank filters omitted, the calendar's visible window carried over, sort/order/page/limit always explicit |
| `parseEnvelope()` | reads the envelope defensively; a bare array (the old unpaged shape) still renders instead of blanking the table |
| `pageWindow(page, pages, span)` | a sliding window of at most five page numbers plus two truncation flags, so the pager never runs off either end |

The list keeps the calendar's visible date window on purpose: switching views must not
silently change *which days* are being looked at. The window is stated in the header
(`১৪ – ২০ নভেম্বর ২০২৬`) and the empty state tells the receptionist to try another date or
filter. Sorting is stated, not implied: `aria-sort` sits on the `<th>`, the ▲/▼ beside the
label is `aria-hidden`, and the header's `aria-label` says what pressing it will do.

### 11.5 Tests — what was run, and what came back

| Suite | Command | Result |
|---|---|---|
| Frontend unit + contract | `cd frontend && npm test` | **146 passed, 0 failed** — includes the 8 new `calendar-list` tests, 2 new render tests and 1 new contract test |
| Frontend production build | `cd frontend && npm run build` | **exit 0**, lint/type check clean; `ƒ /appointments 18.5 kB` |
| Backend appointment suite | `cd backend && set -a; . ../.env; set +a; python -m pytest appointment/tests -q` | **76 passed, 0 failed** — 26 of them in the new `test_appointment_list.py` |
| Container rebuild | `docker compose build appointment frontend && docker compose up -d appointment frontend` | both `Built`, both recreated, both `healthy` |
| Real browser | `node /tmp/c1_browser.mjs` (headless Chrome over DevTools) | **22 / 22 checks passed** — §11.7 |

`test_appointment_list.py` (backend) covers: the envelope's `total`/`pages` against a
filtered set, page 2 of a known set, next/previous boundaries, name substring search in
**Bangla** and in Latin, mobile search with and without separators, token search, `%`/`_`
escaping, every filter, every whitelisted sort, the 422s (sort, order, date, limit) and
authorisation — including that a denial is written to the audit trail, polled rather than
assumed.

`calendar-list.test.mjs` (frontend) is the mirror image on the client side: the opening
state, coercion of a bad sort/order/limit/page, the exact request object (including that
blank filters are *absent* rather than empty), envelope reading (envelope, bare array,
garbage, page-past-the-end), the sliding page window at both ends, sort toggling,
filter/clear/paging interplay, and that an unsupported page size is refused.

The two new render tests (§7.4's machinery, no new dependency) assert the card's anatomy
and the overflow: a card whose accessible name reads `patient · 09:00 · doctor · নিশ্চিত`,
a `>09:00 · ডা. রহমান<` line, `>নিশ্চিত<` as visible text, the chamber line, and a tooltip
that still ends `· CONFIRMED`; then five bookings in one slot render **three** cards plus
`>আরও 2<`, the summary is a `<span>` without a day handler and a `<button
class="appt-cal-more">` with one, the day view shows all five, and a missing translation
template degrades to `>+2<`.

### 11.6 Verification against the live stack

All figures are from the rebuilt stack (appointment service on `localhost:8115`,
frontend on `localhost:3100`), authenticated as the demo `receptionist`. No credential or
token appears in this report.

| Probe | Result |
|---|---|
| `list?date_from=2026-11-01&date_to=2026-11-30&limit=5` | `200` — `total=42`, `page=1`, `pages=9`, 5 items |
| `…&limit=100` | `200` — `total=42`, `pages=1`, 42 items (the cap holds) |
| `…&limit=25&page=2` | `200` — `page=2`, `pages=2`, **17** items (25 of 42 on page 1) |
| `…&sort=patient&order=asc` | `200` — first row **Abdul Mannan** (A→Z, not date order) |
| `…&sort=status&order=desc` | `200` — first row **NO_SHOW** |
| `…&status=CONFIRMED` | `200` — `total=5`, all five `CONFIRMED` |
| `…&sort=surname` | **`422`** `invalid sort, use one of ['branch', 'date', 'doctor', 'patient', 'status']` |
| `…&order=sideways` | **`422`** `invalid order, use asc or desc` |
| `…&date_from=16-11-2026` | **`422`** `invalid date_from, use YYYY-MM-DD` |
| `…&limit=500` | **`422`** `Input should be less than or equal to 100` |
| `…&branch_id=does-not-exist` (receptionist) | **`404`** `not found` — non-disclosing |
| no `Authorization` header | **`401`** |

Search, against the live data (`q=` → total):

| Query | Total | First row |
|---|---|---|
| `Tariqul Islam` (full name) | 2 | Tariqul Islam |
| `tari` (lower-case substring) | 2 | Tariqul Islam |
| `Islam` (surname only) | 7 | Tariqul Islam |
| `01811220007` (full mobile) | 2 | Tariqul Islam |
| `0181-1220-007` (same mobile, dashed) | 2 | Tariqul Islam |
| `T-002-001` (token) | 4 | Tariqul Islam |
| `%` / `_` (LIKE metacharacters) | 0 / 0 | — |
| `zzzznot-a-patient` | 0 | — |

Two notes, both honest: a six-digit mobile prefix (`018112`) matches **all 42** rows
because the seed's numbers run sequentially (`01811220001`–`01811220030`) — correct
behaviour, thin data. And Bangla substring search is proven by the backend test rather
than by this probe, because the seeded patients have transliterated names.

**One real inconsistency, found by this verification.** For the same window the *grid*
endpoint returns **41** rows across **two** branches (`demo-br-001`, `demo-br-002`) while
the *list* endpoint returns **37** rows, all `demo-br-001`. The grid's
`GET /api/v1/appointments` is organization-scoped (the pre-existing **O-Q**); the new
route is branch-scoped from the token, as `.clinerules` §3 requires — the list is the
*more* correct of the two. Because two different totals in one header invite a false
comparison, the header now prints the grid count only while the calendar is on screen and
lets the pager state the list's own total. Making the grid branch-aware is a business-rule
decision, left to the owner (**O-S**).

### 11.7 The browser run — what a person would actually see

A throw-away CDP script (headless Chrome, no Puppeteer, no new dependency) signed in
through the login form as the demo receptionist and drove the shipped page. Screenshots:
`/tmp/amsdp_shots/10-appointments-week.png`, `11-appointments-list.png`,
`12-appointments-search.png`, `13-appointments-sorted.png`.

| Check | Observed |
|---|---|
| page header, Bangla title | `অ্যাপয়েন্টমেন্ট` |
| one-line purpose | `ফাঁকা স্লটে ক্লিক করে বুক করুন, কার্ডে ক্লিক করে কাজ করুন` |
| shared toolbar wired | `role="toolbar"`, `#appt-search`, `#appt-doctor`, `#appt-status` all present |
| view toggle | `সপ্তাহ, দিন, তালিকা` |
| cards on the real week | **40** |
| card anatomy | `["Shafiqul Alam T-004-001", "09:00 · …", "কিউতে", "Ground Floor / General Medicine / Chamber 101"]` |
| tooltip keeps the enum | `09:00 · Shafiqul Alam · T-004-001 · IN_QUEUE` |
| overflow in a real cell | `আরও 1` rendered as `.appt-cal-more` |
| list view loads | rows appear after the view switch |
| columns and sorting | `টোকেন | রোগী | ডাক্তার | তারিখ▼ | সময় | অবস্থা | কর্ম`; `aria-sort` = `[null, none, none, descending, null, none, null]` |
| a row | `["T-002-001", "Tariqul Islam 01811220007", "Dr. Kamal Hossain", "2026-11-19", "09:00", "বুক হয়েছে", "নিশ্চিতবাতিলচেক-ইন"]` |
| status is a word | `বুক হয়েছে`, never `BOOKED` |
| the total | `দেখানো হচ্ছে 1–25 · মোট 37` |
| page sizes | `25, 50, 100` |
| server-side search | typing `Tariqul` → 25 rows became **2**, `মোট 2`, every row matching |
| sort really sorted | `রোগী▲ → ascending`, names in order |
| clear-filters | offered once a filter is active; clears back to the 25-row baseline |

The pixels were read as well as the DOM: the week view shows the four-row cards with the
chamber line, the list view shows the dark header with `তারিখ ▼`, the Bangla status pills
and `চেক-ইন` appearing **once** on a confirmed row (twice was the pre-refactor behaviour).

### 11.8 Governance and skill compliance

Per `.clinerules` §2, §6 and §11.

| Item | This task |
|---|---|
| Documents read before coding | `docs/governance/AMSDP_Docs_Index_V1.0.md`; this report; `docs/product/AMSDP_Business_Rules_V1.0.md` (statuses/roles/scoping, §7–8); `docs/implementation/AMSDP_M4_Appointment_Implementation_Report.md`; the frontend UX rules as adapted in `AMSDP_Engineering_Governance_Assessment.md` §3 |
| Skills installed / used | **none installed** (`.clinerules` §5) — governance documents used instead, as that section requires |
| Server-side authorisation, not UI hiding | branch scope from the token in the new route; out-of-scope id → `404`, no token → `401` (§11.6); the branch picker is a filter, not a grant |
| Tenant key | `organization_id` throughout; no second tenant column introduced |
| Audit | no write path added; the new route is read-only; the denial path it *can* trigger (403/404 on scope) is the shared dependency, and the backend test polls the audit trail for the denial it produces |
| Migrations | none — no schema change |
| Evidence standard (§7) | IMPLEMENTED (route + model + UI), TESTED (146 frontend / 76 backend), VERIFIED (live API probes §11.6, rebuilt containers, real browser §11.7) |
| Output location (§11) | this section is appended to the existing report under `docs/implementation/`; no new document, no move, no rename, so no manifest entry is due; the index records the new size and a revision entry |
| Git | nothing staged, nothing committed, nothing pushed; `frontend/styles/global.css` gained two additive `.appt-cal-more` rules (the file already carried unrelated uncommitted work — **O-M**) |

### 11.9 Limitations and open items

**O-S (new) — the grid is organization-scoped, the list is branch-scoped.** Measured, not
suspected: 41 rows across two branches versus 37 for one (§11.6). The new route follows
`.clinerules` §3; the old endpoint is unchanged because making it branch-aware changes who
sees what, which is an owner decision.

**→ Resolved by §12 (decision D-1).** The owner's follow-up task fixed the behaviour (the
calendar follows the token's branch), and the measured result is 37 rows for the receptionist
and `404` for an out-of-scope branch (§12.6, §12.7 B01).

**O-T (new) — the card's doctor label can fall back to `#<id>`.** The card resolves the
doctor from `GET /api/v1/doctors`, and the demo data contains appointments for
`demo-dr-006…010` which that list does not return, so those cards read `#demo-d…`. The list
view is unaffected: the new endpoint joins the doctor name into the payload. No rule was
invented to paper over missing demo data.

**→ Resolved for grid cards by §12 (F-7).** The grid payload now carries `doctor_name` from the
same join the list uses, and the card prefers it
(`doctorName={(a) => a.doctor_name || doctorName(a.doctor_id)}`), so the lookup that produced
`#demo-d…` is now only a fallback for a row whose doctor genuinely does not exist.

**O-U (new) — Latin digits in the pager.** Page numbers and `1–25` stay Latin while dates
and day numbers are localized. Deliberate: `YYYY-MM-DD` and `HH:MM` are API values (the
schedules page and the database speak them), and the pager sits beside them.

**O-V (new) — two cosmetics inherited from the shared layer, not fixed here.**
(a) Tailwind's `preflight` is disabled by design (`tailwind.config.js`), so a `<button>`
without an explicit border shows the user agent's; it is visible on `/doctors` too, i.e. it
predates this task, and the new bare buttons (`SortTh`, the patient-name link) reset it
explicitly. (b) `SearchInput` is `type="search"` *and* renders its own clear button, so
Chrome paints its native ✕ beside the custom one — the same on `/patients` and `/doctors`.
Both are one-line fixes in shared components; touching them would change pages this task
did not own.

**O-N (still open) — no human has clicked through this on a device.** This section adds a
real-Chrome pass (§11.7), which narrows but does not close O-N: touch targets on a tablet
and the Bangla line-breaking of long chamber names still want a person's eyes.

No product decision was taken here. Nothing was moved, renamed or deleted.


## 12. Later addition — the search box, the Status filter and the Branch picker now reach Week and Day (2026-11-16)

A later task, `AMSDP-CALENDAR-FILTER-01` (2026-11-16), implements the correction that
`docs/audit/AMSDP_Appointment_Calendar_Filter_Diagnosis_V1.0.md` proposed and deliberately did
not perform. The diagnosis found (F-1…F-9) that in **Week** and **Day** view the toolbar's
search box and its Status/Branch pickers wrote only into the paged list's query state, while
the grid was rendered from a separate `GET /api/v1/appointments` request built from the
calendar window and the doctor alone — so typing a patient's name fired **no** request at all
and the grid contradicted the very filter chip the UI displayed.

The constraint is the same one §11 carried: **no scheduling, lifecycle, capacity, token or
queue rule changed.** `POST /api/v1/appointments`, the status transitions, check-in,
cancel-with-reason, walk-in, the slot picker and the symptoms/onset fields are the request
paths documented in §1–§10. What changed is *which rows a read returns* — the predicates now
exist once, and every read applies them in the same order.

Two behaviour questions framed the work, and the task fixed them as the diagnosis asked:

* **D-1 (scope, previously O-AA)** — the calendar follows **the branch its token carries**,
  exactly as `/list` already did. Verified: the demo receptionist's grid now states **37**
  rows (its own branch) where the organization's total is **41**, and asking for another
  branch answers `404` (12.6) — the pre-fix behaviour was measured by the diagnosis as the
  receptionist receiving the organization-wide set (47 vs 42 for the same day, F-3).
* **D-2 (search reach, previously O-AB)** — a search **does** look beyond the week on screen,
  and the calendar says so instead of pretending: a count-only date index plus a banner with
  a one-click route to the nearest other date.

### 12.1 What changed, in the order a receptionist meets it

| Surface | Before (measured in the diagnosis) | After (measured in 12.7) |
|---|---|---|
| Typing a patient's name in Week | **0** requests; chips stayed at 40 | `GET /appointments?q=Rokeya+Sultana&date_from=…&date_to=…` — the header reads `Matched this week 1`, one card on screen |
| Status in Week/Day | the picker wrote list-only state | `GET /appointments?status=CANCELLED&date_from=…` → 3 cards, and the same filter reaches the list and the match index |
| Branch picker | ignored by the grid | `GET /appointments?branch_id=demo-br-002&…` → 4 cards; an out-of-scope branch is `404`, never an empty grid |
| A match that exists on another date | silently absent ("search doesn't find it") | banner `1 more match on 1 other date`, a `Go to nearest date — Friday, 13 November 2026` button that moves the calendar, and `See all in the list` |
| The matched part of a name | nothing was marked | `<mark class="appt-cal-hit">Rokeya Sultana</mark>` on the card's name, and on the token when the token matched |
| An unknown `status` | `200` with 0 rows (F-6) | `422` naming the lifecycle values |
| Chip names | 30 `GET /patients/{id}` lookups per week load (F-7) | names arrive with the appointment; a lookup happens only for a row that has none |
| The grid route's authorisation | *any* authenticated principal | `appointment.read`, like the list (a role without it could read the day's schedule before) |


### 12.2 The one predicate module — `backend/appointment/appt_filters.py`

The structural half of the fix. Three read routes answer *the same question* — “which
appointments match what the receptionist typed?” — for three presentations, so the predicates
live once, in one module, and are applied in one order: **tenant → branch scope → filters →
search**. The order is what makes a query-string `branch_id` able to *narrow* a scope but never
*widen* it.

| Export | Job |
|---|---|
| `parse_day(value, field)` | a `date`, or **422** — a malformed bound must never turn “this week” into “everything” |
| `validate_status(status, statuses)` | blank → `None`; a value outside the lifecycle → **422** naming the valid set (F-6) |
| `like_pattern(term)` | escapes `\`, `%`, `_` before the `ILIKE`, so `q=%` matches nothing instead of everything |
| `search_conditions(term)` / `apply_search(query, term)` | patient name, patient mobile (non-digits stripped, so `0181-1220-007` and `01811220007` agree), appointment id, token number |
| `apply_filters(query, *, q, doctor_id, status, date_from, date_to, statuses)` | the toolbar's filter half, one implementation for all three routes |
| `apply_branch_scope(query, auth, branch_id)` | the token's branch, before anything the caller sent; an out-of-scope id → **404** (`require_branch_access`, `.clinerules` §3) |
| `appointment_rows(session, auth)` | the tenant-scoped join shape every read starts from |
| `search_rows(session, auth)` | `appointment_rows` plus the patient join the search needs |
| `row_context(row, can_see_mobile)` | `patient_name`, `patient_mobile`, `doctor_name`, `branch_name` — the mobile gated on `patient.read`, not on `appointment.read` |
| `match_index(session, auth, …, near, limit)` | the counts-only date index (12.3) |

`SEARCH_MAX_LENGTH = 120` bounds the `LIKE` pattern (a longer string is a paste accident,
not a name); `MATCH_DATE_LIMIT = 120` bounds the date list.

### 12.3 `GET /api/v1/appointments/matches` — the missing half of the answer

A Week grid cannot hold a match three months away, and *showing nothing and saying nothing*
was the defect (F-4). The new read-only route answers **where** the matches are, with counts
only — the browser learns that a date has matches, never who is on it. Navigating there
fetches that week through the ordinary, authorised grid route.

| Part | Behaviour |
|---|---|
| filters | `q`, `branch_id`, `doctor_id`, `status`, `date_from`, `date_to` — the same helpers, the same validation |
| `near` | the anchor day (the calendar's own date). The date list is ordered by **distance from it**, so a truncated list keeps the dates one click away rather than the oldest in the database. Malformed → `422` |
| envelope | `{total, dates: [{date, count}], truncated}` — `total` is the exact count of the filtered set; `dates` is capped at 120 with `truncated: true` |
| scope | tenant from the token, branch from the token, out-of-scope `branch_id` → **404**, no token → **401** |
| payload safety | no patient name, no mobile, no record — counts and dates only |

Measured (`q=Rokeya Sultana`, `near=2026-11-16`):
`{"total":2,"dates":[{"date":"2026-11-13","count":1},{"date":"2026-11-19","count":1}],"truncated":false}`
— which is exactly the banner the receptionist then reads, because the week on screen
(14–20 Nov) holds one of the two and owns neither.

### 12.4 The client half — three pure modules, one builder

| Module | Export | Job |
|---|---|---|
| `lib/calendar/list.js` | **`buildFilterParams(query, window)`** (new) | the filter half of every read — `q`, `doctor_id`, `status`, `branch_id`, blank values omitted, window carried; `buildListParams` is now exactly this **plus** sort/paging, so there is no second copy to drift |
| `lib/calendar/matches.js` (new) | `MATCHES_PATH`, `MATCH_FILTER_FIELDS` | the endpoint and the four filters it accepts — deliberately **no** date window |
| | `buildMatchParams(query, near)` | the request, built from the same query object the grid and the list use |
| | `parseMatchIndex(data)` | defensive read; an unknown shape degrades to “nothing known”, never to a crash or an invented number |
| | `matchSummary(index, window)` | `inWindow` / `outOfRange` / `otherDates` / `otherDateCount` / `truncated`; when the server truncated, `outOfRange` comes from the exact `total`, so a number printed beside “more” never understates the truth |
| | **`matchesBannerKey(summary)`** | which sentence fits these counts (12.7, the bug the browser found) |
| | `nearestMatchDate(summary, anchor)` | the other date to jump to — nearest, ties breaking to the earlier day, so the same banner always lands on the same date |
| `lib/calendar/highlight.js` (new) | `highlightSegments(text, term)` | `text` as `[{text, match}]` segments that reassemble into the original string exactly once |
| | `hasHighlight(text, term)` | whether to mark at all — marking happens on evidence |

`components/AppointmentCalendar.js` gained a `Highlighted` renderer and a `highlightTerm`
prop, applied to the **name** and the **token** only — never the whole card. The term is never
compiled into a `RegExp` (a stray `*` or `(` would throw) and never into HTML (React escapes
the segments, so a name containing `<script>` stays text). Case folding matches the server's
`ILIKE`, and `%`/`_` are literal here exactly as the escaped `LIKE` treats them.

`pages/appointments.js` gained the wiring: one memoised `gridParams` from
`buildFilterParams`, one `matches` effect keyed on the same filters, the memoised summary, the
banner (with `Go to nearest date` / `See all in the list`), the header's `Matched this week N`
/ `Matched this day N`, joined patient/doctor/branch names on the card, and the bilingual
strings for all of it.

### 12.5 Tests — what was run, and what came back

| Suite | Command | Result |
|---|---|---|
| Frontend unit + contract | `cd frontend && npm test` (`node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/*.test.mjs`) | **167 passed, 0 failed**, exit 0 (`/tmp/fe_final.txt`; the same suite is `/tmp/fe_t2.txt`) — 146 at §11 plus 21, of which the new `calendar-matches` (9 tests) and `calendar-highlight` (8) are 17, and `calendar-list` (grown to 9) with the extended integration contract make up the rest |
| Backend | `cd backend && set -a; . ../.env; set +a; python -m pytest appointment/tests -q` | **108 passed, 0 failed** in 206 s (`/tmp/t_all_tail.txt`) — 76 at §11, plus 32 in the new `appointment/tests/test_appointment_calendar_filters.py` |
| Frontend production build | `cd frontend && npm run build` | **exit 0** (container rebuilt and healthy on `:3100`, `/tmp/febuild.txt`) |

What the new tests pin down, rather than merely describe:

* **The contract gap the diagnosis found (F-8, O-AC).** The old suite *asserted* the defective
  request shape. It now asserts the opposite in the same place: the grid request is
  `buildFilterParams(query, { from: range.from, to: range.to })`, every shared control writes
  into that one query object, and the *absence* of the old window-only request is a regression
  guard. A pure builder is something a node test can hold to account; a JSX string is not.
* **One builder, three reads.** `buildListParams` must equal `buildFilterParams` plus
  sort/paging — a diff between them fails the suite, so the grid and the list cannot drift
  apart again.
* **The scope rule is the server's, not the client's.** Backend tests call the routes with a
  receptionist token and with an admin token and assert 37 vs 41 rows, the `404` for an
  out-of-scope `branch_id`, the `401` without a token, and that a denied branch is *recorded*
  in the audit trail (the shared `require_branch_access` dependency writes the denial).
* **`422`, not an empty table**, for an unknown `status` or a malformed `date_from`/`near`.
* **The index is counts-only.** A test asserts the payload carries no patient name and no
  mobile, so “where are my matches” can never quietly become “download the history”.
* **Truncation honesty.** More dates than the cap → `truncated: true` and an exact `total`
  that does not shrink to the listed dates.
* **Highlight safety.** `%`, `_`, a leading `*`, `(` and a name containing `<script>` are all
  plain text; the segments always reassemble into the original string; an empty term marks
  nothing.
* **The assertion the browser wrote.** `matchesBannerKey` is tested across all six reachable
  combinations, including the one the browser run caught (12.7).

### 12.6 Live API verification (read-only, the running stack)

Probes against the running services (`:8115` appointment service, token from
`POST /api/v1/staff/login` on `:3100`; script `/tmp/appt-verify/probe.mjs`, log
`/tmp/appt-verify/probe.log`). No write path was exercised.

| Probe | Answer |
|---|---|
| `GET /appointments/matches?q=Rokeya Sultana&near=2026-11-16` | **200** `{"total":2,"dates":[{"date":"2026-11-13","count":1},{"date":"2026-11-19","count":1}],"truncated":false}` |
| `GET /appointments/matches?q=Rokeya Sultana&status=CANCELLED&near=…` | **200** `total:1`, one date — the index respects the other filters |
| `GET /appointments?status=CANCELLED&date_from=2026-11-14&date_to=2026-11-20` | **200**, 3 rows; the first row carries `patient_name`, `doctor_name`, `branch_name`, `patient_mobile` |
| `GET /appointments?status=NOPE&…` | **422** `invalid status, use one of AWAITING_CONFIRMATION, BOOKED, …` |
| `GET /appointments?q=%&…` | **200** `[]` — the metacharacter is literal |
| `GET /appointments?…` with no token | **401** `authentication required` |
| `GET /appointments?…` as the receptionist | **200**, **37** rows (own branch only) |
| `GET /appointments?branch_id=demo-br-002&…` as the receptionist | **404** `not found` — non-disclosing, exactly as `.clinerules` §3 requires |
| `GET /appointments/matches?q=Nargis Parvin&near=2026-11-16` as the receptionist | **200** `total:1`, date `2026-11-16` — the index is scoped too |
| `GET /appointments/matches?near=nope` | **422** `invalid near, use YYYY-MM-DD` |

The grid payload now returns
`patient_name, patient_mobile, doctor_name, branch_name` alongside the existing fields, which is
what removes the 30-lookup-per-week behaviour recorded as F-7.

### 12.7 The browser run — what a person would actually see (24 recorded steps, two roles)

A CDP script (`/tmp/appt-verify/run.mjs`, headless Chrome, no Puppeteer, no new dependency)
signs in through the real login form, drives the shipped page and records per step: the
committed controls, the header count, the cards rendered, the `<mark>` elements, the banner
text, and **every** `/api/v1/` request the step made (`/tmp/appt-verify/run4.log`,
`/tmp/appt-verify/results.json`). Two hazards were designed out: a reused tab keeps the
previous user's token (so `sessionStorage.clear()` runs before each handshake), and a stale
token would answer as the wrong role (so each session asserts the handshake's role).

The header count is the number the page states (`Matched this week N`), so it is meaningful in
Week/Day and not in List — the List's own figure is read from its `Total N` status line.
That distinction is deliberate: printing one number for two different totals is how §11.6's
inconsistency became visible in the first place.

| # | Step | Header | Cards | Marks | Requests the step actually made |
|---|---|---|---|---|---|
| S01 | Week, default | 41 | 40 | 0 | none (first paint already loaded) |
| S02 | Week, search `Rokeya Sultana` | 1 | 1 | 1 | `appointments?q=Rokeya+Sultana&date_from=2026-11-14&date_to=2026-11-20` · `matches?q=…&near=2026-11-16` |
| S02b | hit mark scrolled into view | 1 | 1 | 1 | — (screenshot `S02c-hit-mark-centred.png`: the mark on “Rokeya Sul…” in Thu 19, 10:00, beside `T-006-001`) |
| S03 | press `Go to nearest date` | 1 | 1 | 1 | `appointments?q=…&date_from=2026-11-07&date_to=2026-11-13` · `matches?…&near=2026-11-13` |
| S04 | `Clear filters` | 6 | 4 | 0 | `appointments?date_from=2026-11-07&date_to=2026-11-13` |
| S05 | `Today` | 41 | 40 | 0 | `appointments?date_from=2026-11-14&date_to=2026-11-20` |
| S06 | Week at 480 px, search a mobile | 2 | 2 | 0 | `appointments?q=01811220004&…` · `matches?…` (layout holds: toolbar wraps, banner wraps) |
| S07 | clear search | 41 | 40 | 0 | `appointments?date_from=…&date_to=…` |
| S08 | Week, search `T-001-001` | 2 | 2 | 2 | `appointments?q=T-001-001&…` · `matches?…` — the token is marked on both cards |
| S09 | clear search | 41 | 40 | 0 | `appointments?…` |
| S10 | Week, status `CANCELLED` | 3 | 3 | 0 | `appointments?status=CANCELLED&…` · `matches?status=CANCELLED&near=…` — **the picker now reaches the grid** |
| S11 | `Clear filters` | 41 | 40 | 0 | `appointments?…` |
| S12 | Week, branch `demo-br-002` | 4 | 4 | 0 | `appointments?branch_id=demo-br-002&…` · `matches?branch_id=…` |
| S13 | `Clear filters` | 41 | 40 | 0 | `appointments?…` |
| S14 | switch to Day | 18 | 18 | 0 | `appointments?date_from=2026-11-16&date_to=2026-11-16` |
| S15 | Day, search `Nusrat Jahan` | 1 | 1 | 1 | `appointments?q=Nusrat+Jahan&date_from=2026-11-16&date_to=2026-11-16` · `matches?q=…&near=2026-11-16` → banner `2 more matches on 2 other dates` |
| S16 | switch to List | — (total **2**) | — | — | `appointments?q=Nusrat+Jahan&date_from=2026-11-14&date_to=2026-11-20` · `appointments/list?q=…&sort=date&order=desc&page=1&limit=25` — **the filters survive the view change** |
| S17 | List, add status `BOOKED` | — (total **2**) | — | — | both reads carry `q` **and** `status` |
| S18 | back to Week | 2 | 2 | 2 | `matches?q=Nusrat+Jahan&status=BOOKED&near=2026-11-16` only — the grid rows for that exact filter set were already loaded, so nothing was refetched; the filters are still applied |
| S19 | `Clear filters` | 41 | 40 | 0 | `appointments?…` (the last reads of the clearing transition) |
| S20 | switch locale, then search again | 1 | 1 | 1 | `appointments?q=Rokeya+Sultana&…` · `matches?…` → banner in Bangla: `এই তারিখগুলোর বাইরে আরও 1টি মিল আছে — 1টি তারিখে` |

Receptionist session (branch-scoped token), same page, same controls. This session recorded
**four** steps: its own default-week baseline (37 rows, identical to B01 below — recorded twice
because the baseline is asserted before anything is typed), then B01–B03. Across both sessions
`results.json` therefore holds **24** step records.

| # | Step | Header | Cards | Marks | What it proves |
|---|---|---|---|---|---|
| B01 | restricted Week, default | 37 | 37 | 0 | the grid is now **branch-scoped from the token** — 37, the number the List has always shown, not the organization's 41 (D-1) |
| B02 | restricted Week, search `Nargis Parvin` | 1 | 1 | 1 | search works inside the restricted scope; `matches?q=Nargis+Parvin&near=…` → `total:1` on `2026-11-16`, so no banner appears — because there is genuinely nothing outside the window, not because the index was skipped |
| B03 | restricted List | — (total **1**) | — | — | `appointments/list?q=Nargis+Parvin&…&page=1&limit=25` → total 1: the list and the calendar now agree |

**`consoleErrors: []` and `failedResponses: []` in both sessions** — checked explicitly, since
the diagnosis established that a silent console is *not* evidence of a working filter, and the
reverse must hold too: a green run with errors in the console would not be evidence either.

Screenshots (`/tmp/appt-verify/shots/`): `S02-week-name-banner.png`, `S02b-week-hit-mark.png`,
`S02c-hit-mark-centred.png` (the mark centred after scrolling it into view),
`S03-nearest-date.png`, `S15-day-search.png`, `S16-list-search.png`, `S18-week-retained.png`,
`S20-banner-other-locale.png`, `B02-restricted-search.png`.
### 12.7.1 The bug only the browser found — “1 more matches on 1 other dates”

The first two runs passed every count-based check and were wrong in the one place a machine
does not read: the sentence. On the default demo week the banner rendered
**“1 more matches on 1 other dates”**. The template was
`'{n} more matches on {d} other dates'` — English inflects the noun after *both* numbers, so
one template cannot be right for every count, and one/one is the *common* case (one patient,
one other day).

Fix, in three parts:

1. `matchesBannerKey(summary)` in `lib/calendar/matches.js` chooses among three keys. Only
   three are needed: `otherDateCount` can never exceed `outOfRange` (each named date
   contributes at least one match), so “one match on several dates” is unreachable.
2. `otherDatesOne` (`1 more match on 1 other date`), `otherDatesOneDate`
   (`{n} more matches on 1 other date`) and `otherDates` are added in **both** languages. The
   Bangla text is intentionally identical across the three keys — Bangla does not inflect its
   counters — but the keys exist so `T()` never falls back to a bare key.
3. The banner renders `T(matchesBannerKey(matchesSummary))`. The `d <= 1` comparison is written
   that way rather than `d === 1` on purpose: a truncated index that named no dates still
   produces a real sentence instead of a dangling placeholder.

Re-verified in the browser afterwards: S02 reads `1 more match on 1 other date`, S10 reads the
same (a status filter, no search), S15 reads `2 more matches on 2 other dates`, and S20 reads
the Bangla sentence. `calendar-matches.test.mjs` now covers all six reachable combinations, so
the sentence is a tested artefact rather than something a person happened to notice.


### 12.8 Governance and skill compliance

| Requirement | Where it was applied | Evidence |
|---|---|---|
| `.clinerules` §2 step 3 / §12 — read the docs index first | `docs/governance/AMSDP_Docs_Index_V1.0.md` read before planning; the diagnosis read in full | this section cites both; the diagnosis's F-1…F-9 are the task list |
| §3 — tenant key is `organization_id`, no second tenant column | every read starts at `appointment_rows`, which filters `organization_id` from the token | no schema change; `appt_filters.py` uses the existing column only |
| §3 — scope from the token, never the request body | `apply_branch_scope` applies the token's branch **before** the caller's `branch_id` | 12.6: receptionist 37 rows; out-of-scope `404` |
| §3 — cross-tenant / cross-branch fails closed with **404**, denials audited | shared `require_branch_access` dependency (unchanged) | backend tests assert the 404 **and** the recorded denial |
| §3 — the UI is never the safety boundary | the browser is told nothing about other branches; every narrowing is re-applied server-side | a hand-crafted `branch_id` in the URL answers 404 |
| §3 — never expose data beyond authorisation | the match index is counts-only; mobile is gated on `patient.read` | backend test asserts no name/mobile in the index payload |
| §3 — audit events append-only | no write path touched, so no new audit event was needed; nothing suppresses an existing one | `POST` handlers unchanged |
| §3 — every schema change is a migration | **no schema change**, so no migration | Alembic chain untouched; `git status` shows no revision file |
| §4 Frontend row (`saas-frontend-ux.md`, `frontend/lib/i18n.js`, shared components) | `Highlighted` reuses the page's own `<mark class="appt-cal-hit">` styling; every new string added in EN **and** BN in the page's existing labels block | 12.7 S20; no hard-coded English in the banner |
| §4 Backend / multi-tenant rows (`saas-application-security.md`, `saas-multitenant-data.md`) | one predicate module; validation as 422; non-disclosing 404 | 12.5, 12.6 |
| §4 Queue / scheduling row | **not applicable by design** — capacity, tokens, transitions untouched | §1–§10 cover them; this change is read-only |
| §6 compliance reporting | this subsection | — |
| §7 evidence standard | IMPLEMENTED (code reachable) · TESTED (167 FE, 108 BE) · VERIFIED (live API, real-Chrome run, DB-visible row counts) · **not ACCEPTED** (the owner has not signed it) | 12.5–12.7 |
| §9 execution boundaries | tests and the browser run were part of this task; commands limited to the project's own scripts; no destructive git | no `reset`/`clean`/`stash` |
| §5 skills registry | **none installed** (as `.clinerules` §5 states). No skill was used or claimed; the governance documents above carried it | — |
| §11 documentation placement | diagnosis in `docs/audit/`, this report in `docs/implementation/`, index updated in the same task | no new folder; nothing moved, renamed or deleted |


### 12.9 What is still not done — honestly

* **O-AD (carried from §11) — Bangla patient names.** The demo data is Latin-script, so
  searching `রোকেয়া` finds nothing. The search is `ILIKE` on the stored name; Bangla-script or
  transliterated search remains open product work, not a defect of this change.
* **O-AG (new) — D-1/D-2 are implemented but not yet in the decision register.** The two
  behaviours were fixed as described in the §12 preamble and are recorded here, in the
  diagnosis's resolution section and in code comments. They are not yet filed in
  `docs/decisions/`; the owner may wish to record them there so a later reader does not reopen
  them.
* **O-AH (new) — the 120-date cap.** A search spanning more than 120 other dates is counted
  exactly (`total`) but only the 120 dates nearest the anchor are navigable
  (`truncated: true`). The banner says so and offers the list, which has no such cap. That is
  intended degradation, not silent degradation — but it is a limit.
* **O-AI (new; pre-existing and now more visible) — cards per cell.** A week cell draws at most
  three cards and then `আরও N`, so under a filter the header can state a number larger than the
  cards visible in one cell (S01: 41 stated, 40 chips, because one cell holds a fourth). This is
  the §11.2 behaviour surfacing under filtering, not a new defect — and a filtered cell is
  exactly where a receptionist will notice it next.
* **O-N (carried) — no human has clicked through this on a device.** The Chrome run narrows it;
  tablet touch targets and Bangla line-breaking inside a filtered banner still want a person's
  eyes.
* **A measurement caveat, stated rather than hidden.** The run's `shown` figure is read from
  the header text; in List view that text is a paging phrase, not a count, so the list's true
  total is taken from its `Total N` status line (`listTotal` in `results.json`) and never from
  `shown`.

No product rule was changed, no schema was altered, and no document was moved, renamed or
deleted. This section was written to
`docs/implementation/AMSDP_Appointment_Calendar_View_Implementation_Report_V1.0.md` per
`.clinerules` §11.


