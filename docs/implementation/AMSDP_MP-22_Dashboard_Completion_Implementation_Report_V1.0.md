# AMSDP — MP-22 Dashboard Completion Implementation Report V1.0

**Work package:** MP-22 — *dashboard completion: branch/date selectors, today's queue panel, quick actions, recent
activity*, **P2** (estimate 2.0), depends on MP-07 (satisfied).
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`).
**Authoritative scope:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` row MP-22, acceptance —
*"Blueprint §2 parity; every figure filtered by the principal's authorised org and branch; a branch user cannot
select another branch."*
**Where written:** `docs/implementation/` (`.clinerules` §11). New file; nothing was moved, renamed or deleted, so no
migration-manifest entry is required.

---

## 1. What existed before this window

The dashboard was six figures and nothing else: `pages/dashboard.js` (53 lines) read `GET /api/v1/dashboard/today`
once, on mount, for the branch in session storage, and rendered the six tiles MP-07 had just fixed. There was no
date selector, no branch selector, no queue panel, no quick action and no activity list — and no way to ask the
figures a question about any day except the facility's today.

The **server** already had more than the screen used: `/api/v1/dashboard/today` (counts, `queue_length`,
`per_doctor`, `walk_ins`), `/api/v1/dashboard/period` (rates, average wait) and `/api/v1/dashboard/audit` (the audit
trail, filterable by branch and bounded by `limit`). So MP-22 is mostly a **screen** task — with one genuine server
gap: `/today` could not be asked about a specific day at all.

---

## 2. What was built

### 2.1 `backend/appointment/dashboard.py` — `date` on `/today` (+1 parameter, +4 lines of response)

| Change | Why |
|---|---|
| `date: str = Query(None)` on `GET /api/v1/dashboard/today` | A date selector that only filters in the browser would be a lie: the figures for a past day do not exist client-side. The day is now a server question |
| `datetime.strptime(date, "%Y-%m-%d")`, else **422** | An unparseable date is refused, never silently replaced by today. The neighbouring `/period` endpoint already behaves this way |
| default stays `operational_today(...)` | BR §8: the facility's day, not the server's UTC date. The selector changes which day is asked about, never the calendar the day is expressed in |
| `"facility_today"` added to the response | The screen can say "showing 2026-11-20 (facility today: 2026-11-24)" instead of leaving the operator to guess |

Branch scoping is unchanged and untouched: `require_branch_access(branch_id)` still answers a **non-disclosing 404**
for a branch the caller does not hold, which is what makes "a branch user cannot select another branch" true even
if the request is hand-written.

### 2.2 `frontend/lib/dashboard.js` (127 lines, new) — the screen's decisions, testable without a browser

| Export | Purpose |
|---|---|
| `BRANCH_WIDE_ROLES`, `mayChooseAnyBranch(user)` | `org_admin` / `super_admin` reach the whole organization; everyone else is branch-scoped |
| `selectableBranches(branches, user)` | Active branches only; a branch-scoped user is offered **their own branch only**, and an empty list — never "all" — when that branch is not in the roster |
| `quickActionsFor(user)` | Four shortcuts for front-desk/administrative roles; a doctor or assistant gets the queue and booking ones |
| `dashboardQuery({branchId, date})`, `activityQuery({branchId, limit})` | The two query strings, URL-encoded, omitting what was not chosen |
| `ACTIVITY_LABELS`, `activityRow`, `activityRows` | A known action becomes an i18n key; an unknown one is shown **as itself** rather than dropped |
| `perDoctorRows(today, names)` | The queue panel's per-doctor breakdown, ordered by volume, named from the roster with the id as fallback |

The module states in its own header that **none of it is an authorization boundary** — the figures come from an
endpoint that derives the tenant and the branch from the token, so filtering the selector is a courtesy that avoids
offering a choice the server will refuse.

### 2.3 `frontend/pages/dashboard.js` (155 lines) — the screen

- **Branch selector** — populated from `GET /api/v1/orgs/{id}/branches` and filtered through `selectableBranches`;
  "All branches" is offered only to a role that may use it.
- **Date selector** — `<input type="date">`, sent as `date=`; a "Today" control clears it back to the facility day,
  and the header states which day is on screen and what the facility's today is.
- **Six tiles** — unchanged from MP-07, including the literal `{ label: t('…'), value: today.<field> || 0 }` shape
  that `dashboard-tiles.test.mjs` asserts, so the MP-07 guard keeps its meaning.
- **Today's queue panel** — `queue_length`, `walk_ins`, and the per-doctor breakdown.
- **Quick actions** — the links from `quickActionsFor(user)`, rendered through `next/link`.
- **Recent activity** — the last eight audited events for the selected branch, labelled through `ACTIVITY_LABELS`.

Thirteen i18n keys were added in **both** `bn` and `en`: `today`, `showingDay`, `facilityToday`, `queueToday`,
`waitingNow`, `walkIns`, `noBookings`, `quickActions`, `recentActivity`, `noActivity`, `newAppointment`,
`rescheduledT`, `staffT`. The page test proves every `t('…')` key it uses resolves in both languages (§4.1).

---

## 3. Decisions taken, and why

| # | Decision | Why |
|---|---|---|
| D1 | The date selector asks the **server**, rather than filtering a client-side copy | Past-day figures are not in the payload and a client cannot compute them; a browser-side filter would have shown today's numbers under a past date |
| D2 | An unparseable `date` is a **422**, not a fallback to today | A dashboard that silently answers a different question than the one asked is exactly the class of defect MP-22 is meant to remove |
| D3 | The response also carries `facility_today` | It is the only way the screen can disclose *which* calendar the day belongs to, and it costs one field |
| D4 | Branch filtering lives in `lib/dashboard.js`, not inline in JSX | The page has no DOM test renderer; a pure module is the only place this project can assert "a branch user is offered one branch" |
| D5 | A branch-scoped user with no matching branch gets an **empty** selector | The alternative fallback — "show them all" — is the failure mode that hands a front-desk user the tenant's whole tree |
| D6 | Quick actions are role-shaped navigation, not authority | Every target enforces its own permission; the rule here only avoids offering a doctor the registration screen first |
| D7 | An unknown audit action renders as its own slug | Hiding activity the dashboard does not have words for would make the panel quietly incomplete as new events are added |
| D8 | The six tiles keep MP-07's literal shape | `dashboard-tiles.test.mjs` reads the page source; rewriting the tiles into a helper would have silently retired a guard that exists because of a real defect |
| D9 | No new dependency, no server-side data for the page | Consistent with the rest of the tree: `node --test` plus source-contract assertions, and the page stays prerenderable |

---

## 4. Verification — what was actually run, and what it showed

Every number is a run in this tree on 24 November 2026, Windows, `E:\amsdp`.

### 4.1 The dashboard's own modules — **28 tests, no browser, no database**

```
cd frontend
node --test tests/dashboard-page.test.mjs tests/dashboard-policy.test.mjs tests/dashboard-tiles.test.mjs
tests 28 · pass 28 · fail 0
```

| Module | Tests | What it pins |
|---|---:|---|
| `tests/dashboard-policy.test.mjs` | **15** (new) | Which branches a selector may list (org-wide roles vs branch-scoped, inactive excluded, missing branch → empty), the four quick actions per role, both query builders (encoding and omission), known/unknown audit labels, malformed payloads, the per-doctor ordering and its id fallback |
| `tests/dashboard-page.test.mjs` | **10** (new) | No `getServerSideProps`; the branch selector is fed by `selectableBranches`; the date selector is a real `type="date"` sent through `dashboardQuery`; the page calls `/dashboard/today` and `/dashboard/audit`; the facility day comes from the response and **no `toISOString()`** date is computed in the browser; `perDoctorRows` feeds the queue panel; quick actions are not hard-coded links; unknown activity renders as itself; **every `t('…')` key resolves in both `bn` and `en`** |
| `tests/dashboard-tiles.test.mjs` | **3** (pre-existing) | MP-07's three tile guards, still green after the rewrite — the six tiles survive verbatim |

### 4.2 The frontend suite

| Run | Tests | Pass | Fail | Skipped |
|---|---:|---:|---:|---:|
| After MP-19/MP-20 | 409 | 405 | 2 | 2 |
| **After MP-22** | **434** | **430** | **2** | **2** |

434 = 430 + 2 + 2 ✓, and 409 + 25 = 434 with 405 + 25 = 430: the delta is exactly the two new dashboard modules, all
passing. The two reds are the pre-existing Q-3 pair — the BanglaNameSense dataset-hash assertion (observed again:
`6f69a0ef…7779` vs the recorded `ac037c24…e51e`) and `calendar-render.test.mjs` failing to load. No new red.

### 4.3 Negative control — the selector-widening defect is caught

`selectableBranches` was mutated so that every caller receives every active branch (the exact defect D5 exists for),
and the policy module was re-run: it **failed**, with the reported assertion
`a branch user whose branch is not in the roster gets an empty list, not all of it` — expected `[]`, received both
active branches. `frontend/lib/dashboard.js` was restored from a byte copy, SHA-256
`9C20CF10C08DF22BFF70594F8BF3D74B1426DA6009F169A403DEE4F2D75FF335` **before and after**, and the three modules
re-ran **28/28**.

### 4.4 Build

```
cd frontend && npm run build
✓ Compiled successfully
● /dashboard   6.6 kB   99.8 kB First Load JS
exit 0
```

**Disclosed defect, fixed before the green run:** the first build *failed* (`exit 1`,
`Error: Failed to collect page data for /dashboard`, cause `ReferenceError: user is not defined`) because one line of
my own edit — `const actions = quickActionsFor(user);` — ended up after the component's closing brace, at module
scope. It was moved inside the component and the build then compiled with `/dashboard` **prerendered** (`●`) rather
than dynamic. The failing run is recorded here because a build that only ever succeeds is not evidence of anything.

### 4.5 One endpoint-level caveat — no server run happened

The `date` parameter and `facility_today` are proven by **inspection, `py_compile` and the page contract**, not by a
live request: six new tests were written in `backend/tests/test_dashboard.py` (`test_an_explicit_date_selects_that_day`,
`test_the_facility_day_is_reported_alongside_the_selection`, and four parametrised
`test_an_unparseable_date_is_refused_not_guessed` cases), but that module connects at import
(`TestClient(app)` + `operational_today()`), so **collection stops** on this host:

```
python -m pytest backend/tests/test_dashboard.py -q --collect-only
ERROR … sqlalchemy.exc.OperationalError: (psycopg2…
Interrupted: 1 error during collection
```

They are recorded as **written and not run**, exactly like MP-17's and MP-18's database tests.

### 4.6 What is **not** verified here

| Claim | Status |
|---|---|
| Blueprint §2 parity | **NOT ASSESSED against the blueprint text here** — the row's acceptance names it; the elements it names (branch selector, date selector, today's queue panel, quick actions, recent activity) exist and are tested, but a line-by-line reading of §2 was not performed in this window (§7, O-2) |
| Every figure filtered by the principal's org and branch | **TESTED (server contract, unchanged)**: `/today` scopes by `auth.organization_id` and refuses a foreign `branch_id` with a non-disclosing 404 |
| A branch user cannot select another branch | **TESTED (client rule)**: `selectableBranches` returns only their own branch, and an empty list when it is absent. The server refusal is the pre-existing `require_branch_access` path |
| The date parameter and `facility_today`, end to end | **NOT VERIFIED HERE** — six tests written, collection blocked by the missing database (§4.5) |
| The screen renders correctly in a browser | **NOT VERIFIED HERE** — no browser harness in this repository (O-3) |

Nothing here promotes MP-22 to VERIFIED: the client rules and the screen's contract are TESTED; the endpoint change
is not.

---

## 5. Files touched

| File | Lines | Change |
|---|---:|---|
| `backend/appointment/dashboard.py` | 179 | `date` query parameter (validated, 422 on garbage), `facility_today` in the response, docstring stating the facility-day rule |
| `backend/tests/test_dashboard.py` | 222 | Six new MP-22 cases (explicit day, facility day reported, four unparseable inputs) — **written, not run** (§4.5) |
| `frontend/lib/dashboard.js` | 127 | **New** — branch/role rules, query builders, activity mapping, per-doctor rows |
| `frontend/pages/dashboard.js` | 155 | Rewritten: selectors, six tiles (verbatim), queue panel, quick actions, recent activity |
| `frontend/lib/i18n.js` | 368 | 13 keys added in `bn` and in `en` |
| `frontend/tests/dashboard-policy.test.mjs` | 113 | **New** — 15 rule tests |
| `frontend/tests/dashboard-page.test.mjs` | 90 | **New** — 10 source-contract tests |

No schema change, no migration, no new dependency. One file was mutated once for the negative control and restored
from a byte copy — SHA-256 `9C20CF10…F335` before and after (§4.3).

---

## 6. Governance and Skill Compliance (`.clinerules` §6)

### 6.1 Documents read and applied

| Domain routed (§4) | Document applied | How it shaped this work |
|---|---|---|
| Frontend UI / components / pages | `saas-frontend-ux.md` (as adapted in the governance assessment §3), the shared components in `frontend/components/ui/`, `frontend/lib/i18n.js` | The screen reuses `AppShell`, `RequireLogin`, `LoadingState`, `EmptyState`, `ErrorAlert`; every control has a label or `aria-label`; both languages were kept in step and asserted by test |
| Dashboard / analytics / metrics | `saas-frontend-ux.md` + `saas-observability.md` (adapted), `backend/appointment/dashboard.py`, Business Rules §8 | The dashboard asks the facility-day question the rest of the system asks (BR §8), and its activity panel reads the append-only audit trail rather than inventing a second source of truth |
| Authentication / RBAC / permissions | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–§8, `frontend/lib/auth.js`, `backend/common/auth.py` | `mayChooseAnyBranch` mirrors the server's reach; the selector filters client-side while the server still refuses a forged `branch_id` with a 404 |
| Multi-tenant data / org-branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–§6 | Every request keeps the tenant from the token; nothing new reads a body-supplied organization |
| Documentation placement | `.clinerules` §11–§12, `docs/governance/AMSDP_Docs_Index_V1.0.md` | This report is in `docs/implementation/`; the index annex and the register were updated in the same window (§8) |

### 6.2 Skills

**No skill package is installed in this workspace** (`.clinerules` §5). No skill was claimed or simulated.

### 6.3 Non-negotiables (`§3`) — point by point

| Rule | Status here |
|---|---|
| Never log or expose secrets | No token or credential is read, stored or printed by the screen; the activity panel shows ids and roles, no patient data |
| The UI is never the fallback safety boundary | Stated in `lib/dashboard.js` and in the page: the selector is a courtesy, the server's 404 is the rule |
| Access enforced server-side, principal from the token | Unchanged: `/today` and `/audit` take the org from the token; a foreign branch is a non-disclosing 404 |
| Cross-tenant / cross-branch fails closed with **404** | Unchanged and relied upon, not re-implemented |
| `organization_id` is the only tenant key | Unchanged |
| Audit append-only; denials recorded | The activity panel **reads** the trail; it writes nothing and offers no delete |
| Forward-only idempotent migrations for schema change | No schema change: the selector is a query parameter, not a column |
| Never claim unverified capability | §4.5/§4.6 state that the endpoint change was not executed and that blueprint parity was not read line by line; nothing is VERIFIED |
| Do not use a tool/library merely because it was discovered | No dependency added; `node --test` and `npm run build` are the repository's own gates |

### 6.4 Deviations and exceptions

1. **Blueprint §2 was not read line by line.** The elements the plan names were implemented and tested; a
   clause-by-clause comparison against `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` §2 was not performed in this
   window (O-2). Claiming "parity" without that reading would be inventing evidence.
2. **No browser run.** No Playwright/DOM harness exists here, so the screen's contract is asserted against source,
   not against a rendered page (O-3).
3. **No server run.** Six endpoint tests are written and blocked by the missing database (§4.5).
4. **One self-inflicted build failure** is disclosed rather than hidden (§4.4).

---

## 7. Open items, and what should happen next

| # | Item | Effect | Suggested handling |
|---|---|---|---|
| **O-1** | Six endpoint tests in `backend/tests/test_dashboard.py` are **unrun** (§4.5) | The `date` parameter, the 422 on garbage and `facility_today` are unproven end to end | On a host with PostgreSQL: `python -m pytest backend/tests/test_dashboard.py -q`; if green, amend §4.6 and the register row |
| **O-2** | **Blueprint §2 was not read line by line** (§6.4.1) | "Blueprint §2 parity" is asserted in the register *by element*, not by clause | Read §2 against the screen before MP-22 is called complete; any clause it names and this screen does not have becomes either a follow-up or an explicit deviation |
| **O-3** | No browser harness | The screen's behaviour in a real browser (focus, labels, layout at 1280/1024/768) is unproven | The Playwright package already suggested for MP-19's O-2 would cover the dashboard journeys in the same run |
| **O-4** | The `wait` tile uses `in_queue` (MP-07) while `queue_length` is now displayed separately in the queue panel | Two numbers that answer different questions sit on one screen — by design, since MP-07 fixed the tile to a specific field and Q-2 in the register still asks which is the contract | Owner decision on Q-2 would settle the vocabulary; nothing here pre-empts it |
| **O-5** | Q-3's two pre-existing frontend reds are untouched | The suite is not green | Owner decision on the dataset hash; `pathToFileURL` for `calendar-render.test.mjs` |

**Next eligible work package.** **MP-25** (tracking hardening: database-backed rate limit, ETA always labelled
"estimated", QR print flow) is next in the register's non-gated list, and it depends on MP-01 — so MP-28 (unify i18n)
and MP-29 (responsive/touch/a11y) are checked first for an unmet dependency in the next window. The gated rows
(MP-04, MP-09, MP-13, MP-21, MP-27, MP-30, MP-34) stay behind their owner decisions; MP-24 / MP-35…MP-40 stay behind
MP-01/B-2.

---

## 8. Where this report is registered

- **Docs Index:** `docs/governance/AMSDP_Docs_Index_V1.0.md` — annex *"MP-22 dashboard completion report
  (2026-11-24)"* added with the file's byte size and line count, and the tree count updated **144 → 145**
  (measured).
- **Execution register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` — an **MP-22** row in §2 with the
  evidence quoted from §4 here, the §5 suite table extended `409/405/2/2 → 434/430/2/2`, §6 listing the files
  touched, and §7's next-task line advanced.
- **Nothing was moved, renamed or deleted**, so no migration-manifest entry was created and no version number was
  advanced.
