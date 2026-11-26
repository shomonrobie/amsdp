# AMSDP — MP-23 (Option A) and MP-04 (Option B) Implementation Report V1.1

**Status:** ISSUED — verification evidence, **not** accepted work · **Written:** 26 November 2026
**Repository:** `E:\amsdp` (Windows development checkout) · **Branch:** `hackathon-mvp`
**Tree under test:** `HEAD = fd4d3656738dfef0885cfc86307903305aa2f08d` (in sync with `origin/hackathon-mvp`) **plus the uncommitted working-tree changes in §4** — nothing was committed, so this SHA names the base, not the exact bytes tested.
**Supersedes:** `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.0.md` (retained unchanged as history; §0 says exactly what changed).

**Authority.** Product Owner decisions of 26 November 2026, recorded in
`docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md`: MP-23 **Option A** (complete Business
Rules §43 reporting scope) and MP-04 **Option B** (complete W3 administration UI scope). PO-05's deferral is
superseded **for MP-04 only**; MP-26 stays deferred.

**Amended 26 November 2026 — PO-D1 decided (Option C).** The Product Owner has ruled that browser-based
voice-pack upload is a **separate work package (MP-47)** and is *not* part of MP-04. This report's conclusions are
unchanged; the open question it carried in §2.1 and §9.3 is now closed. The amendment is additive — see **§12** —
and nothing earlier in this document was rewritten: §2.1 and §9.3 each carry a pointer to §12 so a reader arriving
at either cannot mistake the question for open. Authority: `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md`
§7; proposal: `docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md`.

---

## 0. What this pass changed, and why V1.0 was not enough

V1.0 reported what had been written. Reading that work back against the routes, the approved scope and the
decision brief produced **five defects and one missing deliverable**. All six are closed below; each is listed
with the artefact that now prevents a recurrence.

| # | Finding | Severity | Closed by |
|---|---|---|---|
| D-1 | **MP-23's report screen did not exist.** The PO chose Option A, whose stated deliverable (decision brief §4) is *"a reporting surface … **plus one report screen**"*. Only the endpoint had been built | Scope gap | `frontend/pages/reports.js`, `frontend/lib/operational-report.js`, 12 tests, 69 `rep*` keys plus the `reports` nav key in both dictionaries, sidebar entry, `/api/v1/reports` rewrite |
| D-2 | **`can('org.read')` was false for `org_admin`** in the client mirror while the server grants it. The voice-pack page therefore showed "permission denied" to the one role that may configure a facility's voice, and the sidebar entry was hidden from it | Functional, role-blocking | `frontend/lib/auth.js` now mirrors `permissions.py` entry for entry; `tests/permissions-mirror.test.mjs` parses the Python matrix and fails on any drift |
| D-3 | **`REFUSAL_KEYS` mapped eight machine tags the policy never emits** (`pack_missing_metadata`, `pack_not_validated`, …), so the refusal translator never fired and silently degraded to raw English detail | Correctness of error handling | Keys are now phrases that exist in `voice_pack_policy.py` / `voice_packs.py` / `announcement_config.py`; the test fails if a phrase disappears from the server source |
| D-4 | **`isManageable` refused `super_admin` on a tenant's pack**, so no screen could approve or publish an organisation's `pending_review` version — `super_admin` is the only role allowed to approve, and the tenancy branch was unreachable | Functional dead end | Mirror now matches `policy.require_pack_access` exactly; asserted against the policy source |
| D-5 | **The organisation configuration reported "inherited" incorrectly** — the page read `view.organization.inherited`, which the organisation route never sends. The hint could never appear | Cosmetic-informational | Derived from the override block (`hasOrgOverride`); asserted |
| D-6 | **Rollback (assignment §3.3) was unreachable from the UI.** `POST /orgs/{id}/announcement-config/rollback` existed and nothing called it, so restoring an earlier published version still required `curl` — precisely what MP-04's acceptance forbids | Scope gap | Restore controls per language in the configuration panel; `rollbackBody`; test asserts the route, the body shape and the wiring |

V1.0's own defect (the body-less availability POST) stays recorded in §8.2 and remains fixed and asserted.

---

## 1. Status at a glance

Statuses are separate on purpose (`.clinerules` §7): a green frontend suite does not make a page
`BROWSER VERIFIED`, and a collected pytest file is not `TESTED`.

| Work package | IMPLEMENTED | TESTED | BUILD VERIFIED | BROWSER VERIFIED | ACCEPTED |
|---|---|---|---|---|---|
| **MP-04** (voice-pack administration, Option B) | **Yes** — library, preview, six lifecycle steps, availability, org configuration, platform defaults, rollback | **Frontend only** — `tests/voice-pack-admin.test.mjs` **17 pass**, `tests/permissions-mirror.test.mjs` **4 pass**; the Python API suite (`organization/tests/test_voice_packs_api.py`, incl. `TestUploadContract`) is **NOT EXECUTED** on this host | **Yes** — `next build` exit 0, `/voice-packs` 7.91 kB | **No** — no database, so no session, no data | **No** |
| **MP-23** (operational reports, Option A) | **Yes** — endpoint + the report screen the option requires | **Frontend: yes** (`tests/operational-report.test.mjs` **12 pass**). **Backend: NOT EXECUTED** — 16 collected, fixture setup fails with `psycopg2.OperationalError … port 5433 … Connection refused` | **Yes** — `next build` exit 0, `/reports` 6.8 kB | **No** | **No** |

Nothing in this report is `ACCEPTED`. `VERIFIED` is not claimed for either work package, because verification
requires a second independent artefact (a browser run, a live API call or a database read) and this host
provides none — see §7.

---

## 2. MP-04 — requirement-by-requirement coverage

The approved requirement is the roadmap row (MP-04, `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`
line 211, quoted verbatim): *"**W3 voice-pack admin surface** (preview / publish / retire) … Deliverables: Page,
tests, report … Acceptance & verification: An operator configures and publishes a pack without curl; every
`voice_pack_policy.py` refusal still enforced server-side"*, plus the PO decision's expansion in
`AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §3.2.

| # | Requirement | Where it lives | Server side that still decides | Test / evidence | Status |
|---|---|---|---|---|---|
| M4-0 | The screen is reachable and readable by the roles the policy allows | `components/AppShell.js` (`/voice-packs`, `org.read`); page gate `mayReadLibrary(user) && can('org.read')` | `GET /api/v1/voice-packs` requires `org.read` | `permissions-mirror.test.mjs` (4 pass) proves the client mirror equals `permissions.py` for all six roles; `voice-pack-admin.test.mjs` asserts the page asks for `org.read` | IMPLEMENTED, TESTED |
| M4-1 | Library: both languages, every status, grouped by lifecycle bucket | `LibraryPanel` + `groupPacks`/`BUCKETS`/`BUCKET_KEYS` | `GET /api/v1/voice-packs?language=&status=` filters **and scopes** | "the library is grouped by lifecycle bucket, newest version first"; "status, role and bucket vocabulary matches the policy exactly" | IMPLEMENTED, TESTED |
| M4-2 | Filtering by language and status, plus "all" | `FILTER_STATUSES`, `PACK_LANGUAGES`, two `Select`s that drive the query | Route filters; a filter the caller may not use returns nothing rather than leaking | `FILTER_STATUSES === [''].concat(STATUSES)`; `PACK_LANGUAGES === policy.LANGUAGES` | IMPLEMENTED, TESTED |
| M4-3 | Audition / preview, showing the server's `problems` and its `selectable` answer | `PackDetail` ← `GET /{id}/preview` | `policy.validate_manifest` + `policy.check_selectable` | "the page is wired to the existing routes and decides nothing locally" asserts `/preview`; the page renders `problems`, `selectable` and the descriptor | IMPLEMENTED, TESTED (contract) |
| M4-4 | Validate (technical, machine step) | `ACTIONS.validate` → `POST /{id}/validate` | `policy.transition('validate')` re-validates the *stored* manifest and files | transition table parsed from `TRANSITIONS`; route existence asserted for every action | IMPLEMENTED, TESTED |
| M4-5 | Submit for human review | `ACTIONS.submit` → `POST /{id}/submit` | Refuses unless `validation_status == 'pass'` (`validation_required`) | same table test; refusal phrase `must pass technical validation` mapped | IMPLEMENTED, TESTED |
| M4-6 | Approve, with the reviewer's note | `ACTIONS.approve` (`note: vpReviewNote`) → `POST /{id}/approve` | `TRANSITION_ROLES['approve'] = PLATFORM_ROLES`; reviewer identity from the token; `human_review_required` if unnamed | roles parsed from `TRANSITION_ROLES`; a note field is asserted present for approve and reject | IMPLEMENTED, TESTED |
| M4-7 | Reject, with a reason | `ACTIONS.reject` (`note: vpRejectNote`) | as above | as above | IMPLEMENTED, TESTED |
| M4-8 | Publish | `ACTIONS.publish` → `POST /{id}/publish` | requires passing validation **and** a recorded named approval | roles/sources parsed; `must be approved by a named reviewer` mapped | IMPLEMENTED, TESTED |
| M4-9 | Retire (never delete) | `ACTIONS.retire` → `POST /{id}/retire` | keeps the row; `retired_at` recorded | "the audit trail is never offered for deletion" asserts no `delete` token in the page and the `voice_pack.availability_changed` audit action | IMPLEMENTED, TESTED |

| M4-10 | Release / withhold a published platform pack | `PackDetail` availability switch → `POST /{id}/availability` with `{available: <target>}` | `AvailabilityChange{available: bool}`; 409 for an organisation pack; 409 when releasing an unpublished pack | "the availability call sends an explicit target, as the route demands" reads the Pydantic model out of the router and asserts the sent value | IMPLEMENTED, TESTED |
| M4-11 | Organisation configuration: language + independent per-language pack | `ConfigPanel` → `GET`/`PUT /api/v1/orgs/{id}/announcement-config` | `_selection_problems` + `policy.check_selectable`; `org.manage`; a foreign org is 404 | "a configuration change omits untouched languages and clears only on inherit"; the mirror test asserts both config routes exist and the read is wired | IMPLEMENTED, TESTED |
| M4-12 | Platform defaults (`super_admin`) | scope tabs + `GET`/`PUT /api/v1/platform/announcement-config` | `platform.admin`; a default must be a published, **released platform** pack | same test; label keys asserted in both languages | IMPLEMENTED, TESTED |
| M4-13 | The configuration **in force**, resolved by the server | `ConfigPanel` prints `resolved.language`, `resolved.voice_packs`, `resolved.sources` and the warnings list | `policy.resolve_config` (org → platform → none) | the page reads `view.resolved`; the test asserts it does not recompute precedence | IMPLEMENTED, TESTED |
| M4-14 | Roll back to a previous approved version | restore controls per language → `POST /api/v1/orgs/{id}/announcement-config/rollback` with `{language}` | `policy.rollback_target` chooses the highest published version that is not the current one | "rollback is offered, and names only the language" asserts the route, the `RollbackRequest` shape and `rollbackBody(lang)` | IMPLEMENTED, TESTED |
| M4-15 | Every refusal stays server-side and is shown verbatim | `failure()` + `refusalKey` / `REFUSAL_KEYS` | 403/404/409/422 from `PolicyError` and the routes | "a refusal is translated only when the phrase exists in the policy" — every phrase is verified present in the server source | IMPLEMENTED, TESTED |
| M4-16 | No synthesis fallback | the page never imports or calls the speech API | `ALLOW_SYNTHESIS_FALLBACK = False` (a constant, not a flag) | the test fails on any `synthesis` token in the page and on the constant changing | IMPLEMENTED, TESTED |
| M4-17 | Every write is audited | none of it client-side | `_audit` per transition; `record_audit` / `record_platform_audit` per configuration write | asserted by the existing Python suite, **not executed here** | IMPLEMENTED, NOT TESTED |
| M4-18 | Upload a new pack from the browser | **not built** | `POST /api/v1/voice-packs` exists and is covered by `organization/tests/test_voice_packs_api.py::TestUploadContract` | see §2.1 | **EXCLUDED — §2.1** |

### 2.1 The upload wizard: why the exclusion is kept, and what would overturn it

The mandate required this to be *checked*, not inherited, so it is decided from the approved text:

- **The roadmap row names the surface and does not name upload.** MP-04 is *"W3 voice-pack admin surface
  (preview / publish / retire)"* with deliverables *"Page, tests, report"*. Creating a version is the W3 **API**
  (audit finding F-50, already implemented and covered by `test_voice_packs_api.py`); the admin **surface** is
  preview/publish/retire plus configuration.
- **The decision record states the exclusion explicitly** (§2.2): *"Not authorised by this decision: uploading a
  new pack from the browser (the upload route exists; a file picker was not part of the approved admin scope)"*.
- **The acceptance criterion is met without it**: "an operator configures and publishes a pack without curl" —
  publication, review, retirement, availability and configuration are all reachable from the page.

**Residual ambiguity, recorded rather than decided.** "Publishes a pack without curl" *presupposes a pack exists*.
If the Product Owner intends an operator to author a version end to end in a browser (file picker → base64 →
`POST /api/v1/voice-packs`), that is **additional scope**, not a defect in this one. It is raised as **PO-D1** in
§9.3 with the alternatives; the agent has not invented the decision.

> **Resolved 26 November 2026 — PO-D1 decided: Option C.** Browser upload becomes the separate work package
> **MP-47** (`docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md`) and is **not** added to
> MP-04. The exclusion in this section is therefore not a deviation any more: it is the approved scope, confirmed by
> the Product Owner in `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §7. **Nothing above is
> withdrawn** — see §12 for the full amendment.


---

## 3. MP-23 — Business Rules §43 coverage

BR §43 is short, so it is reproduced here and each clause is matched to an artefact
(`docs/product/AMSDP_Business_Rules_V1.0.md` lines 970–978):

> *"Permitted reports include appointments by day, doctor or branch; booked/completed/cancelled/no-show counts;
> walk-in counts; queue activity; booking-source counts; and schedule utilization where meaningful for the
> appointment model. Do not add revenue, billing, payment-settlement or clinical-performance analytics."*

The approved deliverable (decision brief §4, Option A — the option taken) is *"a reporting surface … **plus one
report screen**"*, scoped *"by the principal's organization and branch, with a non-disclosing 404 on a foreign
branch"*. Roadmap acceptance: *"Report totals reconcile against `appointments`/`queue_entries` for a fixed day;
org and branch scoping enforced with 404 on violation."*

| §43 requirement | Backend | Frontend | Data source and calculation | Org / branch enforcement | Automated test | Status |
|---|---|---|---|---|---|---|
| Appointments by day | `appointments.by_day` | "By day" table | `GROUP BY appointment_date` over the scoped rows | org from token; branch from token scope | `test_every_dimension_sums_to_the_appointment_total`, `test_a_period_reports_by_day_in_order` | IMPLEMENTED, NOT EXECUTED |
| … by doctor | `appointments.by_doctor` | "By doctor" table | `GROUP BY doctor_id`; a `doctor_id` outside the tenant is 404 | doctor ownership checked against `auth.organization_id` | `test_unknown_doctor_in_the_tenant_is_a_404`, `test_another_tenants_rows_never_enter_the_report` | IMPLEMENTED, NOT EXECUTED |
| … by branch | `appointments.by_branch` | "By branch" table | `GROUP BY branch_id` | a foreign branch is a non-disclosing **404** via `require_branch_access` | `test_foreign_branch_is_a_non_disclosing_404`, `test_branch_scoped_principal_is_narrowed_to_its_own_branch` | IMPLEMENTED, NOT EXECUTED |
| Booked / completed / cancelled / no-show counts | `br43` (four figures) + full `status_counts` | headline row + status table | `booked = BOOKED + AWAITING_CONFIRMATION + CONFIRMED`; in-facility statuses reported separately as `present` | same scoped row set | `test_br43_headline_counts_are_disjoint_and_present_balance`; the screen's `HEADLINE_ORDER` is parsed from `reports.HEADLINE` | IMPLEMENTED, NOT EXECUTED (backend) / TESTED (frontend contract) |
| Walk-in counts | `walk_ins` | "Walk-ins" figure | `booking_source == 'walk_in'`, the convention `/dashboard/today` already uses | same | `test_walk_ins_and_booking_sources_are_counted_once` | IMPLEMENTED, NOT EXECUTED |
| Queue activity | `queue_activity` (entries, by_status, by_source, calls, transitions, avg wait, avg service) | queue block | `queue_entries` + `status_history`; averages from recorded transitions, `max(delta, 0)` | queue query filtered by the same scoped branch/doctor | `test_queue_activity_reconciles_and_counts_calls` | IMPLEMENTED, NOT EXECUTED |
| Booking-source counts | `booking_sources` | source tables (appointments and queue) | `GROUP BY booking_source` / `entry_source` | same | the walk-in test asserts the exact map | IMPLEMENTED, NOT EXECUTED |
| Schedule utilisation **where meaningful** | `utilisation` (capacity, claimed, unscheduled, percent, per doctor) | utilisation block + per-doctor table | active `schedule_sessions` → published seats; `slot_allocations` → claimed; `UNSCHEDULED` counted separately; `percent = null` when capacity is 0 | utilisation filters by the same branch/doctor scope | `test_utilisation_compares_claimed_seats_with_published_capacity`, `test_utilisation_is_null_rather_than_zero_when_nothing_is_published` | IMPLEMENTED, NOT EXECUTED |
| **No** revenue / billing / settlement / clinical-performance analytics | no such field exists | the page prints none, asserted by regex | — | — | `test_payload_carries_no_money_or_performance_field` walks every payload key; the frontend asserts the page and lib carry no money vocabulary | IMPLEMENTED, NOT EXECUTED (backend) / TESTED (frontend) |
| Reconciliation for a fixed day (roadmap) | `reconciliation` block | "Reconciliation" panel that **recomputes** the identities from the payload | seven identities, listed in the `reports.py` module docstring | — | backend: four reconciliation tests; frontend: "reconciliation is computed from the payload, not assumed" | IMPLEMENTED, NOT EXECUTED (backend) / TESTED (frontend) |
| One report screen (Option A deliverable) | — | `frontend/pages/reports.js` — day or period, branch, doctor; all five dimensions | reads only the endpoint | branch list from `/orgs/{id}/branches`; the server still decides scope | `operational-report.test.mjs` (12 pass): route, query, ceiling, formatting, reconciliation, labels, no money | IMPLEMENTED, TESTED, BUILD VERIFIED |
| Bangla and English | — | `rep*` keys in **both** dictionaries | — | — | `i18n-coverage.test.mjs` plus the per-label assertions in `operational-report.test.mjs` | IMPLEMENTED, TESTED |
| Empty dataset is an answer | `_buckets` keeps every lifecycle key at 0 | "Nothing happened in this period" plus zero figures | — | — | `test_an_empty_day_reports_zeroes_and_no_utilisation_figure` (**new in this pass**) | IMPLEMENTED, NOT EXECUTED |
| Date-boundary behaviour | strict `YYYY-MM-DD` round-trip, `from <= to`, ≤ 366 days | the screen blocks inverted and over-long ranges before calling | — | — | `test_unpadded_or_impossible_dates_are_refused`, `test_inverted_and_overlong_periods_are_refused`; frontend `periodTooLong` parity test | IMPLEMENTED, NOT EXECUTED (backend) / TESTED (frontend) |


**Definitions published rather than assumed.** §43 leaves "queue activity" and "utilisation" open, so both are
defined in the module docstring *and* in the decision record §3.1, and the payload carries the raw components
(`calls`, `transitions`, both averages, `unscheduled`) so a reader can disagree with the definition and still
recompute. `percent: null` prints as "—", never as 0%.

---

## 4. Files changed

### 4.1 This verification pass (26 November 2026, second pass)

| File | Change | Kind |
|---|---|---|
| `frontend/pages/reports.js` | **New**: the BR §43 report screen (D-1) | New |
| `frontend/lib/operational-report.js` | **New**: query building, period ceiling, null-safe percentage, reconciliation re-check, label maps, scope reading | New |
| `frontend/tests/operational-report.test.mjs` | **New**: 12 tests, three of them parsing `reports.py` | New |
| `frontend/tests/permissions-mirror.test.mjs` | **New**: 4 tests comparing `ROLE_PERMISSIONS` with `PERMISSIONS` parsed out of `backend/common/permissions.py` | New |
| `frontend/lib/auth.js` | `PERMISSIONS` mirror rewritten to match the server matrix exactly (**D-2**); `hasPermission(user, perm)` extracted as a pure function; `can(perm, user)` delegates | Modified |
| `frontend/lib/voice-pack-admin.js` | `isManageable` now mirrors `require_pack_access` (**D-4**); `REFUSAL_KEYS` replaced with phrases that exist in the server (**D-3**); `hasOrgOverride`, `rollbackBody`, `ROLLBACK_LANGUAGES` added (**D-5**, **D-6**) | Modified |
| `frontend/pages/voice-packs.js` | Restore-version controls wired to the rollback route (**D-6**); `inherited` derived from the override block (**D-5**) | Modified |
| `frontend/lib/i18n.js` | 10 `vp*` keys (rollback, refusal labels) + 69 `rep*` keys and the `reports` nav key, in both dictionaries (Bangla block now 735 keys) | Modified (additive) |
| `frontend/next.config.js` | `/api/v1/reports/:path*` → appointment service — found missing by the existing `next-config-rewrites` scan, which derives prefixes from the page source | Modified (additive) |
| `frontend/components/AppShell.js` | Sidebar entry `/reports` (`appointment.read`) | Modified (additive) |
| `frontend/tests/voice-pack-admin.test.mjs` | 14 → **17** tests: corrected the `super_admin` expectation (**D-4**), refusal phrases verified against the server source (**D-3**), configuration-view and rollback tests added | Modified |
| `backend/tests/test_operational_reports.py` | 15 → **16** tests: an empty-day test (zeros, unsuppressed status keys, `percent: null`, zero reconciliation) | Modified (additive) |

### 4.2 First pass (reported in V1.0, unchanged)

| File | Change |
|---|---|
| `backend/appointment/reports.py` | New: the reporting module and `GET /api/v1/reports/operational` |
| `backend/appointment/main.py` | Mounts the reports router |
| `frontend/lib/voice-pack-admin.js` | New: the policy mirror |
| `frontend/pages/voice-packs.js` | New: the W3 operator screen |
| `frontend/tests/voice-pack-admin.test.mjs` | New: the mirror/contract suite |
| `frontend/components/AppShell.js` | Nav entries for `/queue-displays` and `/voice-packs` |
| `frontend/lib/i18n.js` | The `vp*` keys |
| `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` | New: records MP-23 Option A and MP-04 Option B |
| `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.0.md` | New: the V1.0 report (retained) |

No file was deleted, renamed or overwritten. No owner-controlled document was modified. No migration, seed,
deployment or commit accompanied this work.


---

## 5. Test evidence — commands and actual outcomes

Run from `E:\amsdp` (or `frontend/`, as stated). Every line is an observed result from this pass; nothing is
restated from V1.0.

| # | Command | Observed outcome |
|---|---|---|
| 1 | `cd frontend && npm test` | **tests 526 · pass 524 · fail 0 · skipped 2** (the two skips are pre-existing). V1.0 recorded 507/505/0/2; the +19 are 3 voice-pack, 4 permissions-mirror and 12 operational-report tests |
| 2 | `node --test tests/voice-pack-admin.test.mjs` | **17 tests, 17 pass, 0 fail** |
| 3 | `node --test tests/permissions-mirror.test.mjs` | **4 tests, 4 pass, 0 fail** |
| 4 | `node --test tests/operational-report.test.mjs` | **12 tests, 12 pass, 0 fail** |
| 5 | `npx next build` | **exit 0**, "Compiled successfully"; `/reports 6.8 kB`, `/voice-packs 7.91 kB` in the route table |
| 6 | `python -m py_compile backend/appointment/reports.py backend/appointment/main.py backend/tests/test_operational_reports.py` | **exit 0** |
| 7 | `python -m pytest tests/test_operational_reports.py --collect-only -q` | **16 tests collected in 1.17 s** — imports resolve, including the mounted router |
| 8 | `python -m pytest tests/test_operational_reports.py -x -q` | **FAILED at fixture setup — 1 error, 0 tests executed.** Verbatim: `psycopg2.OperationalError: connection to server at "127.0.0.1", port 5433 failed: Connection refused (0x0000274D/10061) Is the server running on that host and accepting TCP/IP connections?`, then `!!! stopping after 1 failure`, `1 warning, 1 error in 3.96s` |
| 9 | Translation-coverage audit (one-off `node` script, `$env:TEMP`, not committed): every i18n key the two screens can render — `t('…')` literals, `labelKey`/`note`/`reason` map values, and every `vp*`/`rep*` string in `voice-pack-admin.js` / `operational-report.js`, i.e. including the keys chosen at runtime from `STATUS_LABELS`, `QUEUE_STATE_LABELS`, `HEADLINE_KEYS` and `DIMENSIONS` | **148 distinct keys referenced, 0 missing in Bangla, 0 missing in English** (`bn` 735 keys, `en` 739). This closes the gap a literal-only scan leaves: a runtime-selected key could otherwise render as its own name |
| 10 | `node -e` probe of `lib/auth.js` against the parsed matrix: `org_admin`/`org.read` **true**, `org_admin`/`platform.admin` **false**, `branch_admin`/`org.read` **false**, `super_admin`/`queue.display.manage` **true**, `receptionist`/`appointment.check_in` **true**, `doctor`/`appointment.modify` **false**, `assistant`/`queue.consult` **false** | all eight agree with `backend/common/permissions.py`; the D-2 fix is exercised outside the test suite as well |

### 5.1 Why row 8 is a blocker and not a defect

Row 8 is the honest classification of the mandate's item 5. The environment was checked before concluding:

| Probe | Result |
|---|---|
| `Get-Service` filtered on `postgres` / `docker` | **no such service** |
| `Get-NetTCPConnection` on 5432, 5433, 3000, 3100, 8000, 8110, 8111 | **all closed** |
| `docker --version` | **not installed** ("The term 'docker' is not recognized…") |
| `backend/common/database.py` DSN | `AMSDP_DATABASE_URL` or `postgresql+psycopg2://amsdp@127.0.0.1:5433/amsdp` |

No safe test database therefore exists on this host, and the mandate forbids reaching for a production or
deployment database, changing authentication, or raising a service that is not installed. The 16 backend tests
are therefore **NOT EXECUTED** — not "passing", not "verified", and not counted anywhere in §1.

### 5.2 What the frontend suites establish, and what they do not

They establish contract facts that would otherwise be assumptions: the mirror equals the parsed Python policy
(transitions, roles, statuses, languages, selectability) and the parsed server permission matrix; every refusal
phrase the screen translates exists in the server source; the report screen's ceiling, headline set and label
coverage come from `reports.py`; the query cannot express what the route refuses.

They do **not** establish that a browser renders the pages, that an `org_admin` can complete a publish, or that
the report figures match a database. Only §7 could establish that, and §7 did not happen.


---

## 6. Build evidence

`npx next build` compiles every page, including the new `/reports`, with **exit 0**, and emits both routes in its
table (`/reports 6.8 kB`, `/voice-packs 7.91 kB`, 122–123 kB first load). That is **BUILD VERIFIED** and no more:
a successful build proves the JSX parses and the imports resolve; it does not prove a control works, and in this
work package a green build coexisted with five defects (§0).

---

## 7. Browser verification — not performed, and why

**Status: not performed.** No browser session, no live API call, no database read. Nothing here is `VERIFIED`.

The reason is environmental and specific, not a matter of effort:

1. **No database.** Every surface under test authenticates through a login that needs the PostgreSQL instance of
   §5.1. Without it there is no session token, so `/voice-packs` and `/reports` would render the
   `PermissionDenied` branch — a screenshot of that proves nothing about the surfaces.
2. **No running stack.** No backend service is listening on 8000/801x and no frontend is serving on 3000/3100,
   so there is not even a stale deployment to click through; and `docker` is not installed, so the compose stack
   cannot be raised here.
3. **No seeded data.** Even with a UI, MP-23's acceptance is *reconciliation against the tables*; without rows
   there is nothing to reconcile, and fabricating rows in a scratch database is not the same test.

What would close it (and what the acceptance review needs): a PostgreSQL instance at a **non-production** DSN,
`alembic upgrade head` on it, the demo seed, then — for MP-04 — sign in as `org_admin` to see the library, preview
a pack, submit it, sign in as `super_admin` to approve/release/publish it and roll a facility's configuration
back; for MP-23, open `/reports` for a fixed day, screenshot the five sections, and compare `br43`,
`status_counts` and `queue_activity` against `SELECT` counts for that date. That is the mandate's "second
independent artefact", and it requires the deployment the B-4/B-2 items already record as outstanding.

---

## 8. Security and negative-path evidence

### 8.1 Server-side authority (`.clinerules` §3)

| Property | Where it is enforced | Evidence |
|---|---|---|
| Tenant from the token, never the body | `reports.py` (`auth.organization_id`), `voice_packs.py` (`_scope_of`), `announcement_config.py` (`_scoped_org`) | parsed and asserted by the frontend mirror tests; the backend assertions are in the collected-but-unexecuted suite |
| Cross-branch / cross-tenant fails closed with **404** | `require_branch_access`, `_visible_or_404`, `_scoped_org`, `_pack_or_404` | `test_foreign_branch_is_a_non_disclosing_404`, `test_unknown_doctor_in_the_tenant_is_a_404`, `test_another_tenants_rows_never_enter_the_report` (collected) |
| Platform-only steps are platform-only | `TRANSITION_ROLES` → `PLATFORM_ROLES`; `require_permission("platform.admin")` | the page is *stricter or equal* to the policy for every action, asserted; an `org_admin` is never offered approve/publish/retire/availability |
| The UI is not the boundary | the page renders `actionsFor` and the server answers anyway | "the page is wired to the existing routes and decides nothing locally" |
| Denials are recorded | `_audit`, `record_audit`, `record_platform_audit` in the routers | referenced; not executed here |
| No secrets in the payload, the page or this report | no credential, token or DSN password is printed anywhere | the DSN is quoted **without** its password (it is environment-supplied) |

### 8.2 The availability defect (V1.0's D-fix) and its regression guard

The page once posted no body to `POST /{pack_id}/availability`, which requires `AvailabilityChange{available:
bool}` — a 422 in the browser behind a fully green suite. It now sends the intended target, and the test reads the
Pydantic model out of `voice_packs.py` and asserts both the model and the sent value, so re-breaking it fails.

### 8.3 Negative paths now covered on the frontend side

- `can()`/`hasPermission` against the parsed server matrix for six roles and twelve probe capabilities, including
  a `nothing.at.all` capability that must never be granted.
- Refusal mapping: an unrecognised detail returns `''` so the page shows the server's text verbatim; a recognised
  phrase must exist in the server source.
- Query construction: a day and a period are never sent together; empty filters are omitted; the period ceiling
  is the backend's constant.
- `percentText(null)` is "—"; `percentText(0)` is "0%" — a real zero is not suppressed.
- Reconciliation: a doctored `by_branch_sum`, an inconsistent total, a mismatched queue sum and a missing
  `reconciliation` block are all reported as failures rather than printed as success.
- Page hygiene: no raw `fetch` (the token would be lost), no `speechSynthesis` in either page, no `delete`
  control on a voice pack, no money vocabulary in the report screen or its lib.


---

## 9. Remaining gaps, blockers and required decisions

### 9.1 Implementation gaps (none inside the approved scope)

Every requirement in §2 and §3 is implemented. The one deliberate exclusion is MP-04's browser upload (§2.1).
Two *enhancements* are not implemented and are **not** claimed: audio playback inside the admin screen (the
preview returns the server's descriptor, `problems` and `selectable`; actual auditioning of the audio is served by
the authenticated asset route the queue page already uses) and CSV/PDF export, which §43 does not ask for and the
decision record explicitly does not authorise.

### 9.2 Blockers, unchanged from V1.0 and still open

| Ref | Blocker | Consequence for these work packages |
|---|---|---|
| B-4 | Deployment database access unresolved | no reconciliation run for MP-23 |
| B-2 | Live runtime verification outstanding | no `VERIFIED` status; §7 cannot be performed |
| — | No PostgreSQL, no Docker on this host | the 16 backend tests stay **NOT EXECUTED** |
| — | No browser session | MP-04 and MP-23 stay **BUILD VERIFIED**, not **BROWSER VERIFIED** |

Also unchanged: B-1 (no destructive live reseed), B-3 (midnight rollover), B-8 (hardware audio) are untouched by
this work; MP-11/12, MP-21, MP-26 and MP-27 remain deferred; MP-09 → MP-13 → MP-14 → MP-15 remain gated on the
first clean rehearsal; the R-3 change freeze was respected (no commit, push, migration or deployment).

### 9.3 Product Owner decisions still required

**PO-D1 — is browser upload part of MP-04?** (raised in §2.1; not decided by the agent.)

| Option | Meaning | Consequence |
|---|---|---|
| **A** (current state) | Upload stays out; an operator administers, reviews and publishes packs created through the W3 API | MP-04 is complete as implemented; no further work |
| **B** | Add a create-version form (metadata + file picker → base64 → `POST /api/v1/voice-packs`) to the same page | a new, small surface; the upload route and its tests already exist, so this is UI + tests only |
| **C** | Move it to its own work package with its own estimate | MP-04 closes now; the upload UI is planned and priced separately |

Recommendation: **A or C**. The approved text neither names nor needs upload, the route is already tested, and
adding a file-upload surface to an operator screen is a security-adjacent change (size ceilings, container
sniffing, path traversal are all already enforced server-side) that deserves its own authorisation rather than a
rider on this one.

**No other decision is required by this work.** The §3.1 definitions (queue activity, utilisation) were recorded
with the decisions themselves and the implementation publishes them in the payload, so a reader can recompute.

> **Decided 26 November 2026 — PO-D1: Option C.** The table above is retained as the record of what was asked.
> The Product Owner selected **C**: browser upload is its own work package, **MP-47**, with its own scope, estimate
> and acceptance (`docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md`). Consequences for this
> report: MP-04 is **not** widened, the upload exclusion stops being a declared deviation (§2.1), and MP-04 is to be
> assessed against its existing approved requirements with no upload-related defect. See §12.


---

## 10. Governance and skill compliance (`.clinerules` §6)

| Field | Value |
|---|---|
| Domains routed (§4) | **Frontend UI** — `saas-frontend-ux.md` (adapted), shared `components/ui/*`, `frontend/lib/i18n.js` · **Backend API** — `saas-application-security.md` (adapted), Business Rules Parts II–X, BR §43 · **Auth / RBAC** — `saas-auth-and-authorisation.md` (adapted), `backend/common/permissions.py`, `voice_pack_policy.py` · **Multi-tenant data** — `saas-multitenant-data.md` (adapted), `common/auth.py` scope checks · **Database** — reviewed; **no schema change**, so no migration owed · **Audit** — `saas-observability.md` (adapted), `common/audit.py` |
| Documents read this session | `docs/governance/AMSDP_Docs_Index_V1.0.md`; `docs/product/AMSDP_Business_Rules_V1.0.md` §43; `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (MP-04 row 211, MP-23 row 270); `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md`; `docs/decisions/AMSDP_MP-23_Operational_Reports_Decision_Brief_V1.0.md` §4; `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.4; `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (F-50, GAP-15, GAP-18); the implementation report V1.0; the voice-pack policy, router, configuration module and `permissions.py` sources |
| Skills selected | **None installed** (`.clinerules` §5 — no `.clinerules/skills/`, `.claude/skills/` or repo `skills/`). Governance documents were used instead; **no skill usage is claimed** |
| §3 non-negotiables — evidence | tenant from the token, never the body · cross-tenant/branch fails closed with **404**, tested · `organization_id` remains the only tenant key · no pack deletion anywhere (retire only, asserted) · denials audited by the existing helpers · no schema change, so no ad-hoc DDL · no secrets printed · no capability claimed that was not observed |
| §7 evidence standard | IMPLEMENTED / TESTED / BUILD VERIFIED are used precisely; NOT EXECUTED is stated where a suite could not run; **VERIFIED and ACCEPTED are not claimed** |
| Deviations | **One, declared**: MP-04's browser-upload surface is not built (§2.1), and the reason is quoted from the approved scope rather than asserted. V1.1 (rather than an in-place rewrite of V1.0) was chosen to honour §11's "never overwrite; preserve historical versions". **Update 26 November 2026:** the declared deviation is **closed** by PO-D1 Option C — the exclusion is now the Product Owner's confirmed scope, not a deviation (§12) |
| Unresolved issues | No PostgreSQL and no Docker on this host; no browser verification; PO-D1. **Update 26 November 2026:** PO-D1 is **decided** (§12); the environment blockers are unchanged |

---

## 11. Document control

| Field | Value |
|---|---|
| Location | `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` (`.clinerules` §11: `implementation/`) |
| Predecessor | `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.0.md` — **retained unmodified**; a one-line supersession note was added at its top, nothing else |
| Decision records | `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` (decisions + implementation cross-reference) |
| Register | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` (MP-04 / MP-23 rows) |
| Index entry | `docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 51) |
| Collision check | the filename did not exist before this write (`git status` shows it as untracked, added only by this pass) |
| Overwrote anything? | **No** |


---

## 12. Amendment A-1 — PO-D1 decided: Option C (26 November 2026)

### 12.1 What changed

| Field | Value |
|---|---|
| Decision | **PO-D1 — Option C**: browser-based voice-pack upload is a **separate work package**, not MP-04 |
| Taken | 26 November 2026, Product Owner written instruction |
| Recorded in | `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §7 (additive; §1–§6 untouched) |
| New work package | **MP-47** — `docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md` (status **PROPOSED**) |
| Register | `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` — MP-47 row added; MP-04 row annotated |
| Rationale (owner) | "Preserve the approved MP-04 scope and manage the additional upload capability independently." |

### 12.2 Effect on this report's conclusions

- **§2.1 exclusion — confirmed, not changed.** The upload surface was excluded because the approved MP-04 text
  names preview, administration, publishing and retirement only. The Product Owner has now confirmed that reading.
  The exclusion is therefore removed from the *deviation* column (§10) and is simply the scope.
- **§9.3 PO-D1 — closed.** The question is answered; the alternatives table is retained as the record of what was
  asked. The agent's recommendation (A or C) was **not** the decision; the owner's choice of C is.
- **MP-04 status — unchanged.** IMPLEMENTED · frontend TESTED · BUILD VERIFIED · not browser-verified · not accepted.
  PO-D1 removes a scope question; it does **not** supply any missing evidence. The blockers in §7 (no PostgreSQL, no
  live stack, no browser run) still stand, and nothing here is promoted to VERIFIED or ACCEPTED.
- **MP-23 status — unchanged** for the same reason.
- **No MP-04 requirement is added, removed or reinterpreted** by this amendment, and no MP-04 code, test or i18n key
  was touched for it.

### 12.3 Effect on the tree

**Documentation only.** No source file, schema, migration, seed, container or configuration was modified for PO-D1.
The turn's verification re-ran the existing suites unchanged (§12.4), because a documentation amendment must not be
reported as new implementation evidence.

### 12.4 Verification performed with this amendment

| Check | Command | Result |
|---|---|---|
| Frontend suite | `cd frontend; npm test` | **526 tests / 524 pass / 0 fail / 2 skipped** — identical to the V1.1 figures, i.e. the amendment changed no behaviour |
| Backend collection | `python -m pytest --collect-only` | **16 tests collected** (not executed — no database, §9.2) |
| Backend syntax | `python -m py_compile` on the two edited Python modules | exit 0 (unchanged this turn) |
| Untouched sources | `git status --porcelain` | no source file added or modified in this turn; only `docs/` files changed |

### 12.5 Amendments are additive by policy

`.clinerules` §11 forbids overwriting a historical record. This amendment therefore **appends** §12 and adds
pointers in §2.1, §9.3 and §10 — it does not rewrite the V1.1 findings, the V1.0 predecessor, the decision record's
earlier sections, or the register's existing rows. Where a status field had to reflect the new fact, the original
text is retained and the update is appended to it.

