# AMSDP — Facility, Doctor Profile and Chamber Assignment (Frontend) — Implementation Report V1.0

**Task:** AMSDP-FACILITY-DOCTOR-01 (frontend half)
**Date:** 2026-11-15
**Written to:** `docs/implementation/AMSDP_Facility_Doctor_Frontend_Implementation_Report_V1.0.md` (§11: subject subfolder `implementation/`, reused, no new folder)
**Backend half:** already implemented in this tree; `backend/tests` was reported green at 216 passed before this frontend phase began. **The backend suite was not re-run while writing this report** — see §6.

---

## 1. Scope and status

The redesign replaces one free-text speciality field and a bare doctor list with three
working screens over the facility/session API that already exists:

| Screen | Route | Purpose |
|---|---|---|
| Doctor Management | `/doctors` | Directory + profile: canonical mobile, structured specialities, per-branch chamber, BMDC verification, photograph |
| Schedules | `/schedules` | Clinic sessions: weekday + window + chamber, with pre-submit conflict warnings |
| Facilities | `/facilities` | Floor → department → room tree, room usage, speciality catalogue |

Status of each: **IMPLEMENTED** (code exists and is reachable), **TESTED** (§5 names
the passing tests), **COMPILED** (`next build` emits the routes) and, after the
2026-11-15 stack rebuild, **runtime-verified at the HTTP level** (§5.4): the built
image serves all three pages, the API answers the exact calls the screens make, and
the proxy forwards the by-id routes. What is still **not VERIFIED** is the visual
result — no browser click-through has been performed (§7).

---

## 2. What was created or changed

| File | Change |
|---|---|
| `frontend/lib/phone.js` | New. Browser mirror of `backend/common/phone.py` (`normalizeMobile`, `isValidMobile`, `formatMobile`, `validateMobile`, `InvalidMobileNumber`). |
| `frontend/lib/facility.js` | New. Weekdays (0 = Monday), BMDC states/transitions, room types, `minutesOf`/`isHhmm`/`overlaps`, `windowConflicts`, `chamberText`/`roomChamberText`, `activeOnly`, `groupRoomsByFloor`, `roomOptions`, `roomUsage`, `facilityCounts`, `initials`, `assignmentText`, `bmdcLabel`/`bmdcBadgeClass`/`bmdcTransitions`, `specialityName`. |
| `frontend/lib/i18n.js` | Added the facility/doctor/session key block to **both** `bn` and `en` (parity asserted by a test). |
| `frontend/lib/auth.js` | `can()` grants `facility.read` to every role and `facility.manage` to `org_admin`/`branch_admin`, mirroring `backend/common/permissions.py`. |
| `frontend/components/AppShell.js` | `/facilities` navigation entry; navigation visibility now filtered by a real `visible(user, item)` built on `can()` instead of the old placeholder. |
| `frontend/next.config.js` | Rewrites for `/api/v1/branches/:branchId/sessions` (ordered **before** the generic branches rule), `/api/v1/sessions/:path*` to scheduling, and `/api/v1/floors|departments|rooms|specialties/:path*` to organization — the by-id routes every edit and retirement calls. |
| `frontend/pages/doctors.js` | Rewritten (was a 47-line form over a free-text speciality). |
| `frontend/pages/schedules.js` | Rewritten (was a legacy schedule list with no chamber). |
| `frontend/pages/facilities.js` | New. |
| `frontend/styles/global.css` | Additive only: `.badge`/`.badge-active`/`.badge-inactive`/`.badge-warn`, `.muted`, `.stack`, `.grid-2`, `.checkbox-row`, `.avatar`, `.tree-group`, `.tree-title`, `.toolbar`, `.summary`. No existing selector changed. |
| `frontend/tests/facility-doctor.test.mjs` | New test file, 22 tests (§5). |

---

## 3. Behaviour worth knowing

1. **The mobile number is normalised before it is sent.** `+880 1711-111111`,
   `1711111111` and `01711111111` all become `01711111111`; `010…`/`012…` (PSTN)
   are refused in the browser exactly as the API refuses them, so one person
   cannot become two records under two spellings.
2. **A chamber belongs to the assignment, not the doctor.** Re-assigning a branch
   reactivates the original `doctor_branches` row, so the chamber is reconciled
   per branch after the profile is saved (`PATCH /doctors/{id}/branches/{aid}`,
   `room_id: ''` clears it — the API's way of telling *clear* from *unchanged*).
3. **Verification is its own axis.** The verify dialog offers only
   `bmdcTransitions(current)`; `verified` can be revoked to `rejected` and is
   never silently reset to `unverified`.
4. **Sessions are the bookable thing, and they live inside a schedule.** Adding a
   session resolves the doctor's schedule for the branch first and creates one
   (empty) only when none exists; the doctor picker offers only doctors with an
   *active* assignment to the branch, because the API answers 422 otherwise.
5. **Conflicts are warned about, never decided, client-side.**
   `windowConflicts` reproduces the two 409s (same doctor overlapping, same
   chamber occupied) with the same half-open comparison (`start < end`), ignoring
   retired rows and the row itself. The server re-checks and stays authoritative.
6. **Nothing is deleted.** Retiring a floor, department, room, speciality or
   session is a `DELETE` that sets `status="inactive"`, so a booked appointment
   keeps naming the location it was booked into. Retired records are hidden by
   default, can be revealed, and can be restored with `PATCH {status:'active'}`
   — otherwise a mistaken retirement would be unrecoverable from the UI.
7. **A room with no floor is shown, not dropped** — `groupRoomsByFloor` puts it
   under an "unassigned" heading, because that is a state the operator must see.
8. **Permission in the UI is convenience only.** Buttons are hidden when `can()`
   says no, but every request is authorised again by the service.

---

## 4. API surface used (no backend edits in this phase)

```
GET    /api/v1/doctors?q&branch_id&specialty_id&status
POST   /api/v1/doctors                            PATCH /api/v1/doctors/{id}
GET    /api/v1/doctors/{id}/photo                 POST/DELETE .../photo
POST   /api/v1/doctors/{id}/verification
PATCH  /api/v1/doctors/{id}/branches/{aid}
GET    /api/v1/orgs/{org}/specialties[?include_inactive=true]
POST   /api/v1/orgs/{org}/specialties             PATCH/DELETE /api/v1/specialties/{id}
GET    /api/v1/branches/{id}/facility[?include_inactive=true]
POST   /api/v1/branches/{id}/floors|departments|rooms
PATCH  /api/v1/floors/{id} | /departments/{id} | /rooms/{id}      (+ DELETE)
GET    /api/v1/branches/{id}/sessions
GET    /api/v1/schedules?doctor_id&branch_id
POST   /api/v1/schedules                          POST /api/v1/schedules/{id}/sessions
PATCH  /api/v1/sessions/{id}                      DELETE /api/v1/sessions/{id}
```

---

## 5. Tests and verification performed (real results)

### 5.1 Frontend suite — `cd frontend && npm test`

```
ℹ tests 93
ℹ pass 93
ℹ fail 0
ℹ skipped 0
```

`tests/facility-doctor.test.mjs` adds 22 of those. The tests that matter most for
this task, and what they pin down:

| Test | What would break without it |
|---|---|
| `mobile numbers normalise to the stored national form` | A second spelling of one doctor's number becomes a second doctor |
| `the browser refuses exactly what the API refuses` | The form accepts `010…`, the API answers 422 at submit |
| `validateMobile reports the caller's own message` | A Bangla screen shows English error text |
| `windows parse as HH:MM and compare as half-open ranges` | Touching windows (09–10, 10–11) warn as a conflict |
| `windowConflicts reproduces both 409s, and only for active rows` | The form warns on a retired session, or misses a chamber clash |
| `a chamber reads the way it is spoken, and skips what it does not have` | A room with no floor renders as `undefined · রুম ১` |
| `rooms group under their floor, and unassigned rooms stay visible` | A mis-filed room disappears from the facility tree |
| `chamber options are labelled and filtered for a picker` | A retired room is offered for booking; two "রুম ১" are indistinguishable |
| `session usage counts active sessions only` | The usage column counts retired sessions |
| `BMDC states and their permitted transitions mirror the server` | The dialog offers a transition the API answers 422 for |
| `every key exists in both languages` / `every key the redesigned pages ask for is in the dictionary` | A missing key silently renders the raw key name |
| `doctors, schedules and facilities compile as JSX` | A broken chunk reaches `next build` |
| `every API resource the pages call is proxied by next.config.js` | A correct API call 404s because the frontend proxy never forwards it |

The JSX test compiles each page with the SWC build that ships inside Next
(`next/dist/build/swc`), the same technique `tests/calendar-render.test.mjs`
already uses — no dependency was added. It caught one real defect during this
task: a duplicated `<div className="card mt-2">` in `pages/facilities.js`.

The proxy test caught a second, functional one: `PATCH`/`DELETE
/api/v1/floors|departments|rooms|specialties/{id}` were **not** in the rewrite
table, so editing or retiring any facility record would have 404'd in the browser
while the API itself was perfectly correct. The rewrites were added and the test
was proved to have teeth (removing the `/floors` pattern makes it fail).

### 5.2 Production build — `cd frontend && npm run build` → exit 0

```
✓ Compiled successfully
✓ Generating static pages (8/8)
├ ƒ /doctors      6.26 kB
├ ƒ /facilities   5.32 kB
├ ƒ /schedules    4.46 kB
```

All three routes are emitted as dynamic (server-rendered) pages.

### 5.3 Database schema — live container, not just the migration file

```
docker exec amsdp-db-1 psql -U amsdp -d amsdp -tAc "select version_num from alembic_version"
  → f7d2b4c6e8a1
information_schema.tables  → facility_departments, facility_floors, facility_rooms,
                             doctor_branches, schedule_sessions
information_schema.columns (doctors)     → bmdc_verification_status, bmdc_verified_at
information_schema.columns (appointments) → floor_id, floor_name, department_id,
                             department_name, room_id, room_name
```

`alembic heads` → `f7d2b4c6e8a1 (head)`: the chain is linear and this is the only
head, so no `upgrade head` was needed and none was run (the database was already
there).

### 5.4 Runtime verification after the 2026-11-15 stack rebuild

A restart alone would not have shown these screens: the compose stack uses **baked
images with no bind mounts** (`frontend/Dockerfile` is `COPY . .` + `RUN npm run
build` + `CMD npm start`), so the running containers still held 16-hour-old frontend
code and 5-day-old backend images. Measured before the rebuild:

```
docker exec amsdp-frontend-1 ls /app/pages        → no facilities.js
grep -c api/v1/floors /app/.next/routes-manifest.json → 0
docker exec amsdp-organization-1 ls /app/facility.py  → missing
curl localhost:8111/api/v1/branches/x/facility    → 404
```

Rebuilt with `docker compose up -d --build frontend organization doctor scheduling
appointment` (identity came along as a dependency). After the rebuild:

| Probe | Result |
|---|---|
| `docker ps` (amsdp-*) | frontend, organization, doctor, scheduling, appointment, identity all `Up (healthy)` |
| `docker exec amsdp-organization-1 ls /app/facility.py` | present |
| `docker exec amsdp-doctor-1 ls /app/profile.py` | present |
| `docker exec amsdp-scheduling-1 ls /app/sessions.py` | present |
| `ls /app/pages` in the frontend | 17 pages, `facilities.js` included |
| `grep -c api/v1/floors routes-manifest.json` | 1 (rewrite baked into the build) |
| `grep -c api/v1/sessions routes-manifest.json` | 1 |
| `GET :8111/api/v1/branches/x/facility` | **401** (route exists; 404 before) |
| `DELETE :8111/api/v1/floors/x` | **401** |
| `PATCH :8111/api/v1/specialties/x` | **401** |
| `GET :8113/api/v1/doctors/x/branches` | **401** |
| `DELETE :8114/api/v1/sessions/x` | **401** |
| `GET :3100/facilities`, `/doctors`, `/schedules` | **200**, 200, 200 |

Authenticated smoke test (org_admin, read-only, status codes and counts only):

```
POST :8110/api/v1/staff/login            → 200
GET  :8111/api/v1/orgs                   → 200  items=1
GET  :8111/api/v1/orgs/{id}/branches     → 200  items=4
GET  :8111/api/v1/branches/{id}/facility → 200  floors=0 depts=0 rooms=0
GET  :8111/api/v1/orgs/{id}/specialties  → 200  items=0
GET  :8113/api/v1/doctors?branch_id=…    → 200  items=4
GET  :8114/api/v1/branches/{id}/sessions → 200  items=0
GET  :8113/api/v1/orgs/{id}/registration-policy → 200 {"bmdc_required":false,…}
```

Doctor records returned by the rebuilt service carry the new profile fields
(`bmdc_verification_status`, `bmdc_verified_at`, `registration_number`,
`specialties`, `specialty_ids`, `branches`, `primary_branch_id`, `mobile`,
`has_photo`), which is direct evidence that `doctor/profile.py` is the code serving
requests, not the pre-rebuild `main.py`.

Proxy proof that separates "proxied and the service said no" from "never proxied" —
same 404 status, different body:

```
DELETE :3100/api/v1/floors/<missing>   → application/json  {"detail":"not found"}   ← reached the service
DELETE :3100/api/v1/sessions/<missing> → application/json  {"detail":"not found"}   ← reached the service
DELETE :3100/api/v1/nosuchresource/x   → text/html         <!DOCTYPE html>…          ← Next's own 404 page
```

Database totals after the rebuild (`floors=37 depts=25 rooms=29 specialties=14
doctor_branches=8 schedule_sessions=0`): the hierarchy has been written to before,
but those rows belong to other organisations created by the backend test suite. The
demo organisation that `org_admin` logs into is **empty**, so `/facilities` opens on
its empty state and `/schedules` has no session to list until floors, rooms,
specialities and a chamber session are created. That is expected for a new feature,
not a defect — but it is why the screens look blank on first visit.

---

## 6. Governance and Skill Compliance (§6)

**Applicable governance documents, by §4 routing row:**

| Domain | Documents applied | Where their instruction shows up |
|---|---|---|
| Frontend UI, components, pages, forms, tables, dialogs, a11y | `saas-frontend-ux.md` (as adapted, Assessment §3), `docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md`, shared components in `frontend/components/`, `frontend/lib/i18n.js` | Shared `Modal`/`ConfirmDialog`/`Alert`/`AppShell` reused rather than re-implemented; every string via `t()` in both languages; `aria-label`s on filter controls; no new dependency |
| Backend API / service endpoints | `saas-application-security.md` (adapted), Business Rules Parts II–X | The UI calls only documented endpoints, sends no ids it does not own, and surfaces the API's own 403/404/409/422 text instead of substituting its own |
| Authentication, RBAC, permissions | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `backend/common/permissions.py` | `can('facility.read'/'facility.manage'/'doctor.create'/'schedule.manage')` mirrors the server's permission map; buttons hidden, never trusted |
| Multi-tenant data, org/branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–6, `backend/common/auth.py` | Every read is branch-scoped by the token; the pages never send `organization_id` as an authorisation claim (only as a route parameter the server re-checks) |
| Database schema, migrations | `saas-multitenant-data.md` §4–5, Alembic chain, `backend/common/models.py` | No migration written or edited; head `f7d2b4c6e8a1` confirmed applied in the live database |
| Queue / scheduling / workflow transitions | Business Rules Parts V–VII, `saas-api-throttling.md` (adapted) | Session windows and conflicts follow the service's half-open rule; the client warns, the server decides |
| Audit / data integrity / reporting | `saas-observability.md` (adapted, redaction + denial recording) | Nothing added to or removed from the audit trail; retirement is a status change so history keeps resolving |

**Selected skills:** **none installed** (`.clinerules` §5 verified: no
`.clinerules/skills/`, no `.claude/skills/`, no repository `skills/`, no Cline
skill configuration). No skill was claimed or pretended to be used; the governance
documents above plus the repository's own conventions carried the task.

**Additional governance obligations observed:**

- §3 non-negotiables: no secret logged or exposed (the photo payload and the
  `.env` values never entered a report, log or commit message); access enforced
  server-side; tenant key stays `organization_id`; audit appended, never rewritten.
- §9 execution boundaries: no destructive git command was run; the files edited
  here were checked before being written (`pages/doctors.js` and
  `pages/schedules.js` were read in full first, then replaced deliberately).
- §11/§12: this report was written to `docs/implementation/`, an existing
  subfolder; `docs/governance/AMSDP_Docs_Index_V1.0.md` was updated in the same
  task. No document was moved, renamed or deleted, so no manifest entry is due.
- §7 evidence standard: §5.4 states exactly what the runtime probes do and do not
  establish — that the built image serves the screens and the API answers the calls
  the screens make, **not** that anything renders correctly to a human.

---

## 7. Deviations, limitations and open items

1. **Not browser-verified.** The evidence is a green suite, a successful
   production build, a schema read against the live database, and — after the
   2026-11-15 rebuild — HTTP-level runtime checks (§5.4: pages 200, API 200 with a
   real token, proxy forwarding proved by body type). No human or independent
   artefact confirmed a *rendered* click-through, so by §7 of `.clinerules` the
   visual result is still **not VERIFIED** and nothing here is ACCEPTED.
2. **Backend suite not re-run in this phase.** No backend file was edited, so the
   216-passed result is inherited, not re-established here. Anyone re-verifying
   should run `cd backend && python -m pytest` and treat the number as the
   acceptance input.
3. **Room list fan-out.** `/doctors` loads the facility tree once per branch to
   name a chamber (`floor · department · room`). With two or three branches that
   is two or three requests; with many branches a per-branch room endpoint that
   also returns floor/department names would be the cheaper contract. Not changed
   here, because it is a backend contract decision.
4. **Speciality management lives on `/facilities`.** There is no other screen
   that can create the catalogue the doctor form needs, so the catalogue was
   placed beside the branch tree rather than inventing a fourth page.
5. **Session creation still creates an (empty) schedule when none exists.**
   The API nests sessions inside a schedule, so the first session for a
   doctor+branch also creates a childless schedule row. Harmless (a schedule with
   no sessions books nothing), but it is a modelling artefact worth folding into
   the sessions API eventually.
6. **No pagination on any of the three screens.** Fine at demo scale; a doctor
   directory of hundreds would need it, together with a server-side photo
   thumbnail.
7. **A floor's `level` cannot be cleared from the UI.** `FacilityUpdate.level` is
   `Optional[int]` and the handler applies it only when it is not `None`
   (`facility.py`, `update_floor`), so blanking the field is read as "unchanged".
   The form therefore cannot unset a level once set; correcting it to another
   number works. Fixing it needs a sentinel on the request model, i.e. a backend
   contract decision.
8. **The demo organisation has no facility data yet.** After the rebuild, the
   branch `org_admin` sees (`demo-br-001`) returns `floors=0 depts=0 rooms=0` and
   the org's speciality catalogue is empty, so `/facilities` opens blank and
   `/schedules` cannot offer a chamber. The 37 floors / 29 rooms / 14 specialities
   in the database belong to organisations created by the backend test suite. To
   demo this feature, create a floor, a department, a room and the specialities on
   `/facilities` first — or seed them — before adding a chamber to a session.
