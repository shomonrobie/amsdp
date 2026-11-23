# AMSDP — QUE-006 Trial Merge: Acceptance-Readiness Verification Report — V1.0

> **Date:** 2026-11-23
> **Branch:** `trial/que006-windows-ubuntu-merge` — HEAD `41ac51a`, **merge not committed** (`.git/MERGE_HEAD` present)
> **Scope:** evidence-based acceptance-readiness verification of the trial merge, with targeted repairs only
> **Writes made to the repository:** working tree only — no commit, no push, no deploy, no live-database migration, no live-stack restart
> **Written to:** `docs/implementation/` (§11 placement rule: implementation verification record)

---

## 1. Verdict

**NOT READY for Product Owner acceptance.**

The merge is technically stronger than its own reports claim in one respect — a **fatal,
suite-invisible startup defect was found by running the built containers and is now
repaired and regression-tested** — and weaker in another: the announcement lifecycle
**cannot yet be called VERIFIED end-to-end in a browser**, and two doctor-contract
questions remain open by decision.

| # | Gate | Result | Evidence class |
|---|---|---|---|
| G1 | Fresh database → `alembic upgrade head` → services start | **PASS** | VERIFIED (live PG 16.15, Scenario A) |
| G2 | Restored **live** dump → `alembic upgrade head` | **PASS**, `DATA_PRESERVED=YES`, idempotent re-run | VERIFIED (Scenario B) |
| G3 | Every container starts and answers `/health` | **PASS after repair** (was **FAIL** on unmodified HEAD) | VERIFIED (9/9 services HTTP 200) |
| G4 | Backend test suite | **769 pass / 2 fail** (2 pre-existing contract questions) | TESTED |
| G5 | Frontend suite + build | **355/355 pass, build exit 0** | TESTED |
| G6 | Queue **call** permission matrix server-side | **PASS** (401 / 403 / 403 / 200) | VERIFIED (live HTTP) |
| G7 | Cross-branch isolation, non-disclosing | **PASS** (own 200, foreign **404** "not found") | VERIFIED (live HTTP) |
| G8 | Duplicate-announcement suppression, two terminals | **PASS** (exactly one delivery per call event) | VERIFIED (browser + DB row count) |
| G9 | Audio-unavailable terminal does not block the queue | **PASS** (`failed` outcome, queue stays `called`) | VERIFIED (browser) |
| G10 | Announcement plays to completion and reports `completed` | **NOT VERIFIED** — one browser run reported `interrupted`; a second reported nothing | OPEN |
| G11 | W3 voice-pack API reachable through the browser origin | **FAIL** — Next.js returns its own 404 (no rewrite) | VERIFIED defect (INT-4) |

Two findings are decision items, not regressions (see §6), so they do not by themselves
block acceptance. **G10 and G11 do.** A facility cannot be told "the announcement is
verified" when no run has produced a `completed` delivery, and an API surface that is
unreachable from the application's own origin is not integrated.

---

## 2. Environment and method

Nothing in this verification touched the live `amsdp` compose project, its volumes, its
database or its `.env` values.

| Component | Detail |
|---|---|
| Database engine | PostgreSQL **16.15** (throwaway containers), three independent scenarios |
| Scenario A | Empty volume → `alembic upgrade head` from zero |
| Scenario B | Restored **read-only dump of the live database** → `alembic upgrade head`; row-count comparison before/after; second run to prove idempotency |
| Runtime | Isolated compose project `q6arv` (ports 58010–58020), built from the trial head, database restored from the same dump |
| Browser harness | Playwright (`playwright-core` + `chromium-1234`), **two independent browser contexts** = two terminals, plus a third with `/audio/**` aborted |
| Test execution | Repository venv (Python 3.14), `pytest`, isolated PG DSN; development defaults so the baseline is comparable |

**Environment artefact worth recording.** With `AMSDP_ENV=test`, ~15 tracking tests fail
because the JWT/pepper test defaults are not the development ones. That is a harness
property, not a product defect; the reported suite result uses development defaults.

**Operational-date artefact worth recording.** On 2026-11-23 the services' operational
day was **2026-11-22** (facility-local day, BR §8), so `GET /api/v1/queue` must be called
with `doctor_id` **and** `date=2026-11-22`. A tester who uses the host's calendar date gets
`422`/empty output and can mistake correct behaviour for a defect.

---

## 3. The defect that mattered: the organisation service was dead on arrival

### 3.1 What the built image actually did

`organization/Dockerfile` builds `organization/` into `/app` and runs `uvicorn main:app`,
so `main.py` is a **top-level** module there. On the unmodified trial head the container
exited during import:

```
File "/app/main.py", line 59, in <module>
    from voice_packs import router as voice_packs_router
File "/app/voice_packs.py", line 42, in <module>
    from . import voice_pack_policy as policy
ImportError: attempted relative import with no known parent package
```

Consequence: **no organisation route existed at runtime** — branches, facilities,
notification settings, appointment configuration, the whole W3 voice-pack registry and the
announcement configuration. `GET /health` answered `000` (connection refused). Every unit
test still passed, because the harness imports `organization.main` **as a package**, where
`from . import …` resolves. This is the defect class that acceptance testing exists to
catch: invisible to the suite, fatal in production, and it silently removed the feature
this merge was built to deliver.

### 3.2 The repair

Both modules now accept either spelling, exactly as `main.py` has always done for its own
router imports (`try: from .x import … / except ImportError: from x import …`). Behaviour,
routes, payloads and permissions are unchanged — only the import spelling differs between
the package layout (tests) and the flat layout (the image).

- `backend/organization/voice_packs.py` — guarded `voice_pack_policy` import
- `backend/organization/announcement_config.py` — guarded `voice_pack_policy` and
  `voice_packs` imports

No other line in either module was touched.

### 3.3 Proof, positive and negative

| Evidence | Result |
|---|---|
| Container after repair | `Application startup complete`; `/health` **200**; the rebuilt `q6arv-organization-1` stayed up for the whole session |
| OpenAPI of the flat import | `/api/v1/voice-packs` + 13 sub-routes + 3 announcement-config routes present (32 paths total) |
| New regression test on the repaired tree | **1 passed** |
| Same test logic against **pre-repair bytes from the index** | **Fails** with `ImportError: attempted relative import with no known parent package` at `voice_packs.py:42` |

The negative control is the important one: it proves the new test detects the real defect
rather than merely passing on a healthy tree.

`backend/organization/tests/test_container_layout_import.py` reproduces the image layout in
a subprocess (so the two layouts cannot shadow each other's SQLAlchemy models) and asserts
mounting through `app.openapi()["paths"]`. That last detail is deliberate: FastAPI 0.162
keeps an included router as an opaque `_IncludedRouter` entry in `app.routes`, so walking
`route.path` silently misses every mounted router — a trap this test originally fell into
and now documents.


---

## 4. Test-suite results as run

| Suite | Command target | Result |
|---|---|---|
| Whole backend | `pytest backend` (development defaults, isolated PG) | **3 failed, 768 passed**, 58 warnings, 1108.06 s |
| Doctor module + new test (re-run after fixing the new test) | `pytest backend/doctor/tests/test_doctor.py backend/organization/tests/test_container_layout_import.py` | **2 failed, 13 passed** |
| New regression test alone | `pytest backend/organization/tests/test_container_layout_import.py` | **1 passed** |
| Frontend | `npm test` | **355/355 passed** |
| Frontend build | `npm run build` | **exit 0** |
| Queue module (after the isolation fixes) | `pytest backend/queuing` | **78/78 passed** |

**Reconciling the full-suite number.** Of the three failures in the full run, **one was the
new regression test's own bug** — it collected route paths from `app.routes`, where FastAPI
0.162 stores included routers as `_IncludedRouter` objects without `.path`, so it saw 12 of
32 paths and asserted against a truncated list. The test was corrected (§3.3) and verified
passing in isolation and as part of the doctor module re-run. The suite was **not** re-run
in full afterwards, so the current-tree figure (**2 failed / 769 passed**) is a derivation
from the executed runs, not a single executed run — stated that way deliberately.

**Test-isolation defects repaired during this verification** (not product defects, but they
were masking signal): doctor mobile-number collisions between tests, queue tests asserting a
`status_history`/`call_event_id` shape the merge had changed, and an appointment test using
a hard-coded `TZ-42` token that collided with the merge's token format. All are working-tree
edits to test files only.

---

## 5. Runtime evidence (isolated stack `q6arv`)

All eight backend services answered `/health` with **200**: identity 58010, organization
58011, patient 58012, doctor 58013, scheduling 58014, appointment 58015, queuing 58016,
audit 58017; the frontend root answered **200** on 58020 (Next has no `/health` route — its
404 there is expected, not a defect).

### 5.1 Permission and isolation matrix (live HTTP, server-side)

| Check | Actor | Result |
|---|---|---|
| `PATCH /api/v1/queue/{id}` `action=call` | no token | **401** |
| same | `doctor` | **403** `insufficient permissions` |
| same | `assistant` | **403** `insufficient permissions` |
| same | `receptionist` | **200** |
| `GET /api/v1/queue` with own branch | `receptionist` | **200** |
| same, `branch_id` of another branch | `receptionist` | **404** `{"detail":"not found"}` |
| `GET /api/v1/orgs/{id}/announcement-config` | `org_admin` | **200** (resolved precedence + warnings) |
| Claim one call event twice | `receptionist` | **201** `claimed:true` → **200** `claimed:false, reason=duplicate_event` |

The doctor row is a *design* consequence, not a regression: `call` requires `queue.manage`,
which the role matrix grants to the front desk and above, not to doctors (**DEV-1** in the
POD-12 report). The 403 is correct enforcement; whether a doctor *should* be able to call is
a product question, and the UI's role gate must agree with the server's.

### 5.2 Two terminals, one call (browser)

Two independent Playwright contexts opened `/queue`, selected the same doctor, enabled audio,
and one walk-in entry was enqueued through the real API and then called once.

| Observation | Result |
|---|---|
| Claim requests captured | 1 delivery created for the call event |
| Losing terminal | rendered **"অন্য টার্মিনালে ঘোষণা হয়েছে"** ("announced on another terminal") |
| Winning terminal | fetched catalogue clips (`en/phrase/room-suffix.mp3`, `bn/phrase/token-number.mp3`) and posted an outcome |
| Outcome reported | `failed`, reason **`interrupted`** |
| Queue state after | `status = called`, `call_event_id = qce:<entry>:1` |
| Database | **exactly one** `queue_announcement_deliveries` row per call event |
| Audit trail | `queue.announcement.requested` ×3, `queue.announcement.failed` ×2 — append-only, never rewritten |

Duplicate suppression is therefore **real and persisted**, not merely a client-side guard.

### 5.3 A terminal that cannot play audio (browser)

Third context with `**/audio/**` aborted. The call was still delivered to the queue, the
terminal reported `failed` / reason **`unsupported_language`** (no catalogue ⇒ refuse to
speak), and the entry stayed `called`. **Audio never blocks the queue** — the required
degradation.

### 5.4 What was *not* verified, and why (G10)

- In the two-terminal run the claiming terminal reported **`interrupted`**, not `completed`.
  **No run in this verification produced a `completed` delivery.**
- In a single-terminal run the announcement **did not fire at all**: the page's first queue
  snapshot arrived after the `call`, so the announcer never observed a `waiting → called`
  transition to announce. One clip was fetched when audio was enabled (a preload), no claim
  was made, no outcome was posted.
- A headless browser cannot prove that sound was **audible**. Even with a clean network
  trace, "the room heard it" needs a person or a recorded audio device.

Honest status of the announcement lifecycle: **claim ✓, duplicate suppression ✓,
audio-failure degradation ✓, playback-to-completion ✗, audibility ✗.**

Open question raised by the second bullet: does the accepted design require a terminal that
*starts up or refreshes* while an entry is already `called` to announce it (catch-up), or is
"only announce transitions this terminal observed, otherwise the operator presses
*ঘোষণা করুন*" the intended rule? The code behaves like the latter. If catch-up is expected,
it is missing; if not, it should be written down.

### 5.5 New integration defect found (G11 / INT-4)

`frontend/next.config.js` rewrites `/api/v1/staff`, `/orgs`, `/branches`, `/floors`,
`/departments`, `/rooms`, `/specialties`, `/me`, `/patients`, `/doctors`, `/schedules`,
`/sessions`, `/appointments`, `/symptoms`, `/dashboard`, `/queue`, `/track` and `/audit` —
but **not** `/api/v1/voice-packs` and **not** `/api/v1/platform/**`. Through the browser
origin both return Next.js's own HTML 404 page:

```
GET /api/v1/voice-packs                     → 404 (Next 404 page)   [service would answer 200/403]
GET /api/v1/platform/announcement-config    → 404 (Next 404 page)   [service would answer 200/403]
GET /api/v1/orgs/{id}/announcement-config   → 200 (covered by the /orgs rule)
```

The service itself is correct — its routes exist in its OpenAPI and answer when called
directly. But any admin UI, reviewer or demo using the application's own origin cannot reach
the voice-pack registry or the platform defaults. The shipped queue UI does not call them
yet, which is why no test caught it.

---

## 6. Decision items carried forward

| ID | Item | Status |
|---|---|---|
| D-1 | **Doctor contract, branch from another organisation** — `POST /api/v1/doctors` with a foreign `branch_ids` entry returns **422 "branch not found in this organization"**, while `test_branch_assignment_is_limited_to_the_owning_org` expects **201 with the foreign id dropped** | Open — behaviour is fail-closed and tenant-safe; only test and code disagree. Decide: change the test, or change the endpoint to drop-and-201 |
| D-2 | **Doctor contract, retired assignments in the response** — `PATCH /api/v1/doctors/{id}` with `branch_ids: []` returns `['legacy-doc-br']`, i.e. a retired/legacy assignment is still serialised | Open — either the response should list only active assignments, or the test's expectation is wrong |
| B-8 | Announcement playback to completion / audibility (G10) | Open — needs a real speaker or a recorded output device |
| INT-4 | Missing Next rewrites for `/api/v1/voice-packs`, `/api/v1/platform/**` (G11) | Open — one-line config fix, plus a test that asserts every service prefix in the UI is proxied |
| B-10, D-3, D-5, D-7, O-2 | Carried forward from the trial report unchanged | Open as previously recorded |
| — | Appointment search: substring versus id semantics | Open as previously recorded |

D-1 and D-2 are **pre-existing latent contract questions surfaced by the merge**, not merge
regressions: both are tenant-safe (nothing leaks, nothing crosses tenants), so this
verification deliberately did **not** change product behaviour to make a test green.

---

## 7. Governance and skill compliance (§6 of `.clinerules`)

| Requirement | How it was met |
|---|---|
| §2.3 read the docs index first | `docs/governance/AMSDP_Docs_Index_V1.0.md` was read before planning; the QUE-006 report set it maps (`W1`…`W6`, `W2_RELIABILITY`, `W3_VOICE_CONFIGURATION_IMPLEMENTATION_AND_VERIFICATION`, `POD-12`, `D4_D6`, `B1_INT3`) was loaded for the announcement/queue/W3 domains |
| §4 routing | Domains: backend API, auth/RBAC, multi-tenant isolation, DB migrations, deployment/Docker, frontend UX. Governance documents applied: `saas-application-security.md`, `saas-auth-and-authorisation.md`, `saas-multitenant-data.md`, `saas-cicd-workflow.md` (as adapted in the governance assessment §3) |
| §5 skills | **No skill package is installed in this workspace** (verified: no `.clinerules/skills/`, `.claude/skills/` or repo `skills/`). No skill was used or claimed; governance documents filled that slot |
| §3 non-negotiables | Server-side enforcement verified live (§5.1); cross-branch read fails closed with a non-disclosing **404**; audit trail read but never modified; schema produced only by Alembic; no secret, token or password is quoted in this report |
| §7 evidence standard | Each gate is labelled VERIFIED / TESTED / OPEN explicitly; `interrupted` is reported as `interrupted`; no `completed` delivery is claimed; the 769/2 figure is labelled a derivation |
| §9 execution boundaries | No destructive Git operation; no staging, commit, push; live stack, live DB and live `.env` untouched; all runtime work in throwaway containers |
| §11 output location | This report is in `docs/implementation/`; the index registration is in `docs/governance/AMSDP_Docs_Index_V1.0.md`; no file was moved or deleted |

---

## 8. Files changed in the working tree (all uncommitted)

| File | Change |
|---|---|
| `backend/organization/voice_packs.py` | Import guard (runtime fix) |
| `backend/organization/announcement_config.py` | Import guard (runtime fix) |
| `backend/organization/tests/test_container_layout_import.py` | **New** regression test (image layout + OpenAPI mounting) |
| `backend/doctor/tests/test_doctor.py` | Test-isolation fix (mobile-number collision) |
| `backend/queuing/tests/test_queue.py` | Test-isolation fix (`status_history` / `call_event_id` assertions) |
| `backend/appointment/tests/test_appointment_calendar_filters.py` | Test-isolation fix (`TZ-42` token) |
| `docs/implementation/AMSDP_QUE006_Acceptance_Readiness_Verification_Report_V1.0.md` | **New** — this report |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Registration of this report (§12 index obligation) |

Nothing else was modified. The staged merge content (W3 modules, migrations, models, the
two earlier QUE-006 reports) was left exactly as the merge staged it.

**Rollback** is `git checkout -- <file>` for any single file, or `git restore` of the working
tree; the merge itself remains uncommitted and untouched.

---

## 9. Cleanup and safety confirmation

| Item | State |
|---|---|
| `q6arv` compose project (10 containers, network, volume) | **removed** (`down -v`) |
| Scenario containers `q6a-pg16`, `q6b-pg16` and their volumes `q6a_pgdata`, `q6b_pgdata` | **removed** |
| Throwaway images built for `q6arv` | **removed** |
| Live `amsdp` stack | **still running, 10 containers, untouched** at the time of teardown |
| Live database | never migrated; the dump used was a **read-only** copy |
| Git | no commit, no push, no stash, no reset; `.git/MERGE_HEAD` still present — the merge remains in progress for the owner to conclude |

---

## 10. What the Product Owner must decide before acceptance

1. **G10 / B-8** — accept the announcement lifecycle as *UNVERIFIED for playback*, or fund the
   one thing that closes it: a run on a real speaker PC (or a recorded output device) that
   produces a `completed` delivery, ideally with the operator-clicked **ঘোষণা করুন** path as
   well as the automatic one.
2. **Catch-up rule** (§5.4) — is a terminal that arrives after the call expected to announce
   it, or is silence the intended behaviour?
3. **D-1 / D-2** — doctor contract: change the tests or change the endpoints. Both are safe
   today; leaving them red is a permanent 2-failure baseline that will hide the next real
   regression.
4. **INT-4** — add the two missing Next rewrites (and a test that pins the proxy surface).
5. **DEV-1** — confirm that a doctor must not be able to call the queue; the UI's role gate
   must then match the server's 403 rather than offering the control.

**Verdict unchanged: NOT READY.** The merge is one runtime fix and two small integration
fixes away from a defensible acceptance, and one real-device run away from being able to say
that the announcement the whole of QUE-006 exists to produce has been heard.


were masking signal): doctor mobile-number collisions between tests, queue tests asserting a
`status_history`/`call_event_id` shape the merge had changed, and an appointment test using
a hard-coded `TZ-42` token that collided with the merge's token format. All are working-tree
edits to test files only.

