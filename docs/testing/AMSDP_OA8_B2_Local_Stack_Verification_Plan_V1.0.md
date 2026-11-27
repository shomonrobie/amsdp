# AMSDP — OA-8 / B-2 Local-Stack Verification Plan — V1.0

| | |
|---|---|
| **Document** | `docs/testing/AMSDP_OA8_B2_Local_Stack_Verification_Plan_V1.0.md` |
| **Purpose** | Request the local-stack and browser session needed to move MP-04, MP-46/OPC-3 and the multi-display band from *tested* to *verified*, with the services, accounts, steps, evidence and risks named in advance |
| **Written** | 2026-11-27, fifth window (controlled verification preparation) |
| **Status** | **PLAN ONLY.** No container was started, no stack was addressed, no browser was opened, no O-1 / Ubuntu proxy was contacted |
| **Permission requested** | **OA-8 / B-2** — local-stack start plus browser session. Database access for the stack arrives with the stack's own volume; it is **not** the disposable-database grant in `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md` and does not authorise either |

> **The boundary that makes this a request rather than a step.** Everything below touches a *running system*:
> containers with `restart: unless-stopped`, a persistent PostgreSQL volume, and a browser holding real JWTs.
> Four windows of evidence were produced without any of that. This plan is the point where that stops being
> possible, so it is written to be approved or refused item by item.

---

## 1. What this session would verify

| Package | Currently | What only a browser can show |
|---|---|---|
| **MP-04** voice packs | PARTIAL — 25 backend tests pass, no UI or audio evidence | that an operator can find, preview and select a pack, and that the board *plays* the selected one |
| **MP-46 / OPC-3** | TESTED — capability + target id asserted in-process | that a cross-tenant `PATCH` from a real session returns the same non-disclosing 404 to the browser, and that the denial row is readable **without** a database console |
| **Multi-display band** (MP-38, MP-39, MP-45, MP-37, MP-42, MP-43, MP-24) | TESTED — 13 admin tests + the focused 155-test band + frontend source guards | that a non-branch board **renders** (the exact case MP-38 crashed on), that scoping round-trips through the UI, and that history survives completion on screen |

## 2. Services required, with the ports this repository actually declares

All from `docker-compose.yml` (host port → container port):

| Service | Host port | Role in this session |
|---|---:|---|
| `db` (postgres:16-alpine) | **5433** | the stack's database — the **developer** database `amsdp`, or `amsdp_demo` under the demo overlay |
| `identity` | 8110 | login, JWT issuance |
| `organization` | 8111 | orgs, branches, floors/departments/rooms, **voice packs**, `/me` |
| `patient` | 8112 | patients (seeded) |
| `doctor` | 8113 | doctors (seeded) |
| `scheduling` | 8114 | sessions |
| `appointment` | 8115 | appointments, dashboard, reports, tracking |
| `queuing` | 8116 | **queue, displays, denial audit** — the centre of this plan |
| `audit` | 8117 | audit search |
| `frontend` (Next 14) | **3100 → 3000** | the only public entry point; proxies every `/api/v1/*` prefix |

**The browser never talks to a backend origin directly** (`frontend/next.config.js` rewrites), so every request
this plan inspects appears under `http://localhost:3100/api/v1/…` — one origin, one DevTools Network tab.

**Browser:** a desktop Chromium-family browser (Edge or Chrome) on this Windows host, DevTools open.
No automation framework is installed and none is proposed.

## 3. Which stack — and why the demo overlay

| Option | Command | Trade-off |
|---|---|---|
| **Demo overlay (recommended)** | `docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml up -d --build` | Same code and migrations, **separate** database `amsdp_demo` on volume `amsdp_demo_pg_data`. Seeded by `backend/seed/seed_demo.py`, which is what creates the **`cardio` department board** the MP-38 crash needs and the demo accounts MP-04 needs. Mutating it is what it exists for; `seed_demo.py` resets it |
| Development stack | `docker compose -p amsdp up -d --build` | Writes to the developer database `amsdp` — the one every guarantee so far has kept untouched. Only acceptable if the owner says the dev database is expendable |

**Port collision is real, not theoretical:** the demo overlay keeps the **same host ports** as the dev project
(its header says so), so **exactly one may run at a time**. The session therefore starts by recording which
project is currently up and stopping it only with the owner's agreement.

```powershell
docker compose ls                       # which project is running right now
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

**Schema + seed for the demo database** (from the overlay's own header, `docker-compose.demo.yml:15`–`23`):

```powershell
cd e:\amsdp\backend
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp:<POSTGRES_PASSWORD from .env>@127.0.0.1:5433/amsdp_demo"
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe seed/seed_demo.py
```

The password is read from the gitignored `.env` at the moment of use and is **never** written into a command
log, a document or a reply (`.clinerules` §3). If `.env` is absent, the session stops rather than guessing.

---

## 4. Accounts and data — referenced, never quoted

| Need | Source | Handling |
|---|---|---|
| Staff accounts, roles and passwords | `docs/demo/AMSDP_Demo_Credentials_V1.0.md` (owner-controlled, read-and-cite only) | read in the session, typed into the login form, **never** copied into a report, log, screenshot title or commit message |
| Minimum roles exercised | platform admin, organisation admin, **branch admin**, receptionist, doctor | each step below names the role it needs |
| Seeded data | `backend/seed/seed_demo.py` | organisations, branches, doctors, patients, clinic sessions, queue displays **including the department-scoped `cardio` board** |
| Data this session creates | one pack selection change, one display edit (scope or `show_room`), queue entries behind a display, one cross-tenant PATCH attempt | all inside `amsdp_demo`; reset by reseeding |

**Screenshots must not capture a session token.** The DevTools panels used below (Network → response body,
Application → storage) are captured with the `Authorization` header redacted or with the request filtered to
exclude `login`.

## 5. Evidence standard for this session

The repository's rule is that a screenshot alone is *implemented-and-seen*, not VERIFIED (`.clinerules` §7).
Each step therefore captures **three** things, and a step is only recorded VERIFIED when all three exist:

1. **Screenshot** — the rendered screen, named `<package>-<step>-<yyyymmdd-hhmm>.png`, saved to
   `E:\Temp\amsdp_b2_1127\`;
2. **Network capture** — the request URL, status, and response body (HAR export or a redacted copy of the
   Response tab), named to match the screenshot;
3. **A sentence of what was expected vs what was seen**, written at the time — not reconstructed later.

Anything short of that is recorded as PARTIAL with the missing element named.

## 6. MP-04 — voice packs (browser)

Roles: organisation admin (and, for the refusal step, a role without the entitlement).

| # | Step | Expected observation |
|---|---|---|
| 1 | `http://localhost:3100/voice-packs` as organisation admin | packs listed from `GET /api/v1/voice-packs`; language/status filters narrow the list without a re-login |
| 2 | Select a pack → preview | `GET /api/v1/voice-packs/{id}/preview` returns the audition payload and the panel renders it; the request is a **read** (no status change afterwards) |
| 3 | Choose a language, listen to the preview with the speakers audible | the announcement is *heard*, in the selected language — this step cannot be evidenced by a screenshot alone; it needs the captured audio asset request **and** a human confirmation line |
| 4 | Publish / retire / change availability on a pack | `POST /api/v1/voice-packs/{id}/{action}`; the list refreshes and the status visibly changes; a second browser tab shows the change (persistence) |
| 5 | Log in as a role without the entitlement and repeat step 4 | refused **server-side** — the button being hidden is not the evidence; the Network tab must show the request being made and refused (403/404), or the step is recorded as "UI-hidden, server behaviour not probed" |
| 6 | Trigger a queue call with the selected pack, on a board using announcements | the board plays the **selected** pack's voice — if announcements are silent in the demo seed, record that as a **data gap**, not a pass |

**Acceptance:** steps 1–4 verified with three-part evidence = MP-04's UI half is VERIFIED. Step 5 upgrades
"non-entitled refused server-side" from test-only. Step 6 is the only step that can never be automated, and
MP-04 stays PARTIAL until it is done by a human at the machine.

## 7. MP-46 / OPC-3 — denial capability and the non-disclosing 404, through a browser

Roles: **branch admin of branch A** (the probe) plus a second organisation's display id (the target).

| # | Step | Expected observation |
|---|---|---|
| 1 | As branch admin A, open `http://localhost:3100/queue-displays` | the screen lists branch A's boards only |
| 2 | Using DevTools → Console on the same origin, send a `PATCH /api/v1/queue/displays/<id belonging to the other organisation>` with the session's own token | **404**, body `{"detail":"not found"}`-shaped and **non-disclosing** — no `code`, no org, no branch of the target. Headers carry the domain-denial marker, not an error stack |
| 3 | Compare with a `PATCH` to a display id that does not exist at all | identical status **and** identical body — the two responses must be indistinguishable |
| 4 | Read the denial row **without SQL**: `GET /api/v1/audit/...` filtered to the actions just produced, in the Network tab | one `queue.display.denied` row per refusal carrying actor, `capability: queue.display.manage` (or its constant value), `target_id` = the id that was asked for, and the **caller's** org/branch — with the target's branch absent |
| 5 | Open `/audit` in the UI and search the same actor | either the row renders with those fields (**screen-level verification**) or the screen omits `after` — in which case that omission is recorded as a UI gap and step 4's API response stands as the evidence |

**What this closes.** Step 4 is the first *independent* reader of the audit row: every previous statement
about `capability` and `target_id` came from the test that asserts them. It also demonstrates the point of the
whole design — the denial is investigable **without** database access, which is why this session needs no new
database grant.

**What it does not close.** The capability-removal negative control still requires deleting a source line and
running tests; that is `docs/testing/AMSDP_T10_Disposable_Database_Execution_Plan_V1.0.md` §6, not this plan.


---

## 8. The multi-display band (MP-38, MP-36, MP-39, MP-45, MP-37, MP-42, MP-43, MP-24)

The band shares one acceptance: **an administrator can create, scope, edit and switch off a board in the UI,
and the public board renders the configured scope — including the seeded `cardio` department board.**

| # | Step | Expected observation |
|---|---|---|
| 1 | `/queue-displays` as branch admin | boards for the caller's branch listed; `GET /api/v1/queue/displays?branch_id=…` |
| 2 | Edit the **department-scoped `cardio`** board (rename, or toggle `show_room`) | `PATCH /api/v1/queue/displays/{id}` → 200, list reflects it. **This is the MP-38 case**: before the translation fix, rendering this board threw `ReferenceError: tr is not defined` and blanked the page |
| 3 | Open `http://localhost:3100/queue-display/<org>/<branch>?display=cardio` | the board **renders**, header shows the branch, and the scope line is **labelled in the board's language** (`dispScopeDepartment` rendered — not a raw key, not a crash). Console free of `ReferenceError` |
| 4 | Same board in the other language | the label switches with the rest of the board — this is the half that was broken |
| 5 | Open the branch-scoped board (`?display=<branch code>`) | the scope line is **absent** — that branch of the conditional was always fine and must not regress |
| 6 | `?display=<unknown code>` | a defined, non-crashing state; record it, because "no board configured" and "a crash" must not look alike |
| 7 | Toggle `show_room` off on one board, reload the public board | the room is suppressed on the board **and** the JSON from `GET /api/v1/queue/display/<org>/<branch>?display=…` no longer carries it — frontend and backend agree in a real session, not only in unit tests |
| 8 | Receptionist: complete a queue entry, then open `/queue-history` | the **completed** entry is present (history outlives the terminal state — MP-24's point) |
| 9 | Same session, request history for another branch through the page | non-disclosing 404, indistinguishable from "no such branch" — observed in the browser, not only in `tests/test_queue_history.py` |

**Per-package ACs (MP-39, MP-45, MP-37, MP-42, MP-43).** These are not restated here: their acceptance
criteria are read from the master plan (`docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`) at
the start of the session and walked in the same visit, under the same three-part evidence rule (§5). This plan
deliberately does not paraphrase them, because a paraphrase in a test plan becomes the thing that gets tested.

## 9. Display and accessibility matrix

| Configuration | Why |
|---|---|
| 1920 × 1080, 100 % | the demonstration's own resolution; the token must dominate by construction |
| 1366 × 768, 100 % | the smallest common clinic screen — overflow and clipping surface here |
| 1920 × 1080 at 200 % browser zoom | stands in for a 4K board read from a distance; must not reflow into unreadable columns |
| Both languages, both resolutions | Bangla labels are longer; truncation is a real failure mode |

## 10. Cleanup

```powershell
# 1  reset the demo data this session changed (pack selection, display edits, queue traffic)
cd e:\amsdp\backend
$env:AMSDP_DATABASE_URL = "postgresql+psycopg2://amsdp:<POSTGRES_PASSWORD>@127.0.0.1:5433/amsdp_demo"
..\.venv\Scripts\python.exe seed/seed_demo.py

# 2  stop the demo project, keeping its volume (never -v: that volume is the demo's data)
cd e:\amsdp
docker compose -p amsdp_demo -f docker-compose.yml -f docker-compose.demo.yml down

# 3  resume the development stack only if the owner wants it running again
docker compose -p amsdp up -d
```

| Artefact | Disposition |
|---|---|
| Screenshots + HAR files in `E:\Temp\amsdp_b2_1127\` | retained until the resulting report is accepted; cited by name from the report |
| Demo database `amsdp_demo` on `amsdp_demo_pg_data` | **not dropped** — it is the demonstration's data. Reseeded instead |
| Developer database `amsdp` / volume `amsdp_pg_data` | **never touched**; no command in this plan names it as a target |
| Browser storage (localStorage tokens) | cleared by logging out; recorded as done |


---

## 11. Live-system risks, and what each one means

| Risk | Consequence | Handling |
|---|---|---|
| **Shared host ports** (3100, 8110–8117, 5433) | the demo project cannot start while the dev project runs; a partial start leaves services unhealthy | record `docker compose ls` first; stop exactly one project with the owner's agreement; verify every health probe green before step 1 |
| `restart: unless-stopped` on every service | a container that crashes comes straight back, so a "stopped" stack can look alive | confirm with `docker ps` after `down`, not from the exit code alone |
| Seeding rewrites `amsdp_demo` | any demo data someone else relies on is replaced | the demo overlay exists for this; announce the session before starting it |
| The board shows **today's** queue | seeded rows from another day render an empty board, which reads like a bug | seed for today, or record "empty board — data date, not a defect" as a data gap; never change code to make it look populated |
| Audio device | a muted or absent device turns a real pass into a recorded failure | confirm the output device before §6 step 3; if silent, record the gap and leave MP-04 PARTIAL |
| Tokens in the browser | a screenshot can leak a live JWT | redact `Authorization`; never paste a token into a report or document (`.clinerules` §3) |
| Environment drift | the stack runs committed code **plus** the uncommitted MP-46/MP-38 changes | intentional — those changes are what is being verified — but the report must say so: the session verifies the **working tree**, not `71226e8` |

## 12. What approval would cover — and what it would still not

**Authorised acts, if OA-8 / B-2 is granted as written:**

1. start the **demo** compose project (`-p amsdp_demo` with the demo overlay), after stopping the dev project
   if it is running;
2. run `alembic upgrade head` and `seed_demo.py` against **`amsdp_demo`** on host port **5433**;
3. open a browser on this host against `http://localhost:3100`, log in as the seeded accounts, reading
   `docs/demo/AMSDP_Demo_Credentials_V1.0.md` in order to do so;
4. create, edit and retire **demo** displays and voice-pack selections inside `amsdp_demo`;
5. create and complete **demo** queue entries so the board and history have data;
6. capture screenshots and HAR files into `E:\Temp\amsdp_b2_1127\`;
7. reseed `amsdp_demo` and stop the demo project at the end.

**Still forbidden under this approval:**

- any access to the **developer** database `amsdp` or its volume;
- any access to `amsdp_verify_1129` or to the T-10 disposable databases;
- `docker compose down -v`, volume deletion, or any database drop;
- deployment of any kind, and any contact with O-1 / the Ubuntu host;
- staging, committing, pushing or destructive Git operations (OA-1 remains separate);
- editing `.clinerules`, the owner-controlled documents, or any migration.

## 13. What this plan does not claim

It does not verify anything: MP-04 remains **PARTIAL**, MP-46 remains **TESTED**, the display band remains
**TESTED**. It does not assert that the seeded `cardio` board still exists in the current demo data — §8 step 2
confirms or creates it. It has not started a stack, opened a browser or contacted any host: this window's
infrastructure access is **zero**.

<!-- Plan only. Written 2026-11-27, fifth window; no stack started, no browser, no O-1 contact. -->

---

## 14. Owner decision recorded — 27 November 2026 (fifth window)

- The **demo-overlay approach is accepted as the preferred proposed approach**; §2's recommendation stands.
- **Execution is not authorised.** No container is started, no browser is opened, no image is pulled.
- The developer database `amsdp` must not be used for this verification, and **Ubuntu and O‑1 must not be
  accessed** under this permission.
- The Docker commands, ports, environment variables, database target, seed/reset procedure, accounts and cleanup
  in §3–§11 are submitted for final review unchanged; approval of the plan is not approval to execute it.

<!-- §14 appended 2026-11-27. §1–§13 preserved exactly as written. -->


