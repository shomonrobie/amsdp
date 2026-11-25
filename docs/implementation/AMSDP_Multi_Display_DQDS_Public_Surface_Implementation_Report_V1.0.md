# AMSDP — Multi-Display DQDS: public surface implementation report

> **Task ID:** `AMSDP-MULTI-DISPLAY-PUBLIC-SURFACE-2026-11-25`
> **Version:** 1.0 · **Date:** 25 November 2026
> **Branch:** `hackathon-mvp`
> **Plan:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (Amendments A-1 … A-5)
> **Specification:** `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` (MD-01 … MD-19, AC-01 … AC-22)
> **Tasks covered:** MP-35, MP-36, MP-37, MP-41, MP-42, MP-43, MP-44 (display slice), MP-45 (server-side half), MP-46 (read-only half)
> **Tasks **not** covered, deliberately:** MP-38, MP-39, MP-40, and the demo seed of two displays — each named in §10.

---

## 1. What this report claims, and what it does not

This report records the first executed slice of WP-C.2 / WP-C.3: the **public
surface** of multi-display DQDS. Before this change, `queue_displays` existed
nowhere in the tree — no table, no model, no resolver, no scoped payload, no
validator. `queuing/display.py` served exactly one branch-wide board and its
route carried an organisation code, a branch code and nothing else.

What is now **IMPLEMENTED and TESTED**:

| Task | Delivered | Evidence class |
|---|---|---|
| **MP-35** | `queue_displays` + `queue_display_doctors` models and one forward-only, idempotent Alembic revision `d3f5a7b91c24`; branch-unique code; scope/language/status CHECK constraints; membership join table | IMPLEMENTED, TESTED |
| **MP-36** | `?display=<code>` resolution; scope filtered **in SQL**; unknown, cross-branch, cross-org and disabled displays return the *same* 404 as an unknown branch; the two-segment route keeps its historic payload | IMPLEMENTED, TESTED |
| **MP-37** | Department scope through `doctor_branches.room_id → facility_rooms.department_id`; `room_name` per doctor (nullable) | IMPLEMENTED, TESTED |
| **MP-41** | Room scope (`scope_type='room'` + `room_id`), validated by CHECK constraint; empty room is an empty board | IMPLEMENTED, TESTED |
| **MP-42** | Estimated waiting time: measured mean of today's completed consultations when n ≥ 3, else `AMSDP_AVG_SERVICE_MINUTES`, integer ≥ 1, always marked `estimate: true` | IMPLEMENTED, TESTED |
| **MP-43** | `board_version` (hash of the projection only) and weak `ETag`; `If-None-Match` → `304` with no body, cache and rate headers intact | IMPLEMENTED, TESTED |
| **MP-44** | Display path already on `operational_today` since MP-06; this slice publishes `operational_date` and `timezone` so the board states its own day | IMPLEMENTED, TESTED (midnight observation still **BLOCKED — B-3**) |
| **MP-45** | `show_room` / `show_estimated_wait` / `show_waiting_count` / `footer_text` enforced **while the body is built** — a switched-off field is absent from the raw response | IMPLEMENTED, TESTED (admin controls are MP-39) |
| **MP-46** | GET-only public route: `405` + `Allow: GET` + `no-store` for four verbs; one throttled `queue.display.disabled_requested` audit row per display per five minutes; **zero** audit rows for anonymous unknown-code probes | IMPLEMENTED, TESTED (the `queue.display.denied` half belongs to MP-39's write routes and is **not** claimed) |

Nothing here is **VERIFIED** in the `.clinerules` §7 sense for the live
deployment, and nothing is **ACCEPTED**. The verification artefact is a local
PostgreSQL database and a `TestClient`; the owner's deployment was not touched,
not queried and not migrated (§5, §10).


---

## 2. Environment actually used

| Item | Value | How established |
|---|---|---|
| Database | `127.0.0.1:55432/amsdp` — the **local development database** | `engine.url` printed at run time, password masked |
| Credential | none — local trust authentication, passwordless DSN | the DSN resolved from `AMSDP_DB_PORT=55432` with no password set; nothing secret was needed, printed or stored |
| Revision before the change | `b2e5c7d91a04` (`alembic current`) | quoted command output |
| Revision after the change | `d3f5a7b91c24` (head) | quoted command output |
| Owner's deployment (`:5433`, `192.168.68.108`) | **not contacted** | no connection attempt was made in this task |

The local harness does not carry `AMSDP_DATABASE_URL` in every shell, so the
suite was run with `AMSDP_DB_PORT=55432` and the documented passwordless
development DSN. That is a **test-harness note**, not a configuration change:
no file, service or environment was modified to make it work.

**Repository revision head is not what the plan states.** The roadmap and the
specification both say the single migration head is `c4d8e2a91f60`. The tree
holds 18 revisions and the head is **`b2e5c7d91a04`** (`add_schedule_blocks`,
MP-16, which revises `c4d8e2a91f60`). The new revision therefore rests on
`b2e5c7d91a04`, and the plan's head value is corrected by Amendment A-5 rather
than silently contradicted. Verified with Alembic's own graph
(`ScriptDirectory.from_config(...).get_heads()`), not by reading filenames.

---

## 3. The schema change

One revision, `d3f5a7b91c24_add_queue_displays.py`, `down_revision =
'b2e5c7d91a04'`.

**Why one revision creates the whole table.** MP-35, MP-37, MP-41 and MP-45 each
own behaviour, but every bit of that state is a column on a table that did not
exist. Creating the table and then altering it twice immediately would add two
irreversible steps and a window in which a display could not express "this field
is off". The table is therefore created once, complete; the tasks are delivered
by the resolver, the payload and their tests. This is a deliberate interpretation
of §8 rule 3 (one schema change at a time): one new table is one schema change.

**What it creates** — `queue_displays` (org, branch, name, code, language,
scope_type, department_id, room_id, footer_text, three publication flags,
status, created_by, created_at) and `queue_display_doctors` (display_id,
doctor_id, created_at, composite primary key). Constraints: `UNIQUE (branch_id,
code)`; `CHECK` on `scope_type ∈ {branch, doctors, department, room}`,
`language ∈ {bn, en}`, `status ∈ {active, disabled}`; and two
half-configuration guards — `scope_type <> 'department' OR department_id IS NOT
NULL`, `scope_type <> 'room' OR room_id IS NOT NULL`. Three indexes, and no
second index duplicating a primary key's leading column.

**Idempotency and blast radius — measured, not asserted.**

```
upgrade #1  INFO  Running upgrade b2e5c7d91a04 -> d3f5a7b91c24, add_queue_displays
current     d3f5a7b91c24 (head)
upgrade #2  no "Running upgrade" line — a no-op

schema snapshot, before -> after
  tables:            31 -> 33
  added:             ['queue_display_doctors', 'queue_displays']
  removed:           []
  changed existing:  []
```

`changed existing: []` is the AC-14 / specification §5.1-item-5 proof: no
existing table's columns or indexes differ. `queue_entries` in particular gained
no room column — the room label is a read.

**Backup, honestly.** No `pg_dump` binary exists on this workstation and no
database container tooling is available, so a dump was **not** taken. Instead the
pre-migration revision was read first, and a full schema snapshot (31 tables,
columns and indexes) was written to `%TEMP%\amsdp_pre_mp35_schema.json`
(SHA-256 `d22f59ad0b9a1a04b44ad4f5d0c6c14a27ed54fed9492c161b6ca3e280618e2d`)
**before** the upgrade and compared after it. The migration is additive-only —
`CREATE TABLE` and `CREATE INDEX`, nothing else — so the residual risk it carried
was schema drift, which the snapshot rules out. This is a disclosed deviation
from the letter of "take a backup first", with the reason recorded rather than
the rule ignored.


---

## 4. The public contract, before and after

| Aspect | Historic board (no `?display=`) | Configured board (`?display=<code>`) |
|---|---|---|
| Top-level keys | `organization`, `branch`, `doctors`, `updated_at` — **unchanged** | adds `display{code,name,language,scope_type,footer_text}`, `board_version`, `operational_date`, `timezone` |
| Doctor keys | `doctor_name`, `currently_serving`, `patients_waiting` — **unchanged** | those three (subject to the policy flags) plus `room_name`, `estimated_wait_minutes`, `estimate` |
| Scope | whole branch | the display's scope, filtered in SQL |
| Cache | `public, max-age=10` | `public, max-age=10` |
| `ETag` | none | `W/"<board_version>"`, `304` on `If-None-Match` |
| Errors | `404` `{"detail":"not found"}` + `no-store` | identical, including for a disabled display |
| Verbs | `GET` (and framework `HEAD`) | `GET`; `POST/PUT/PATCH/DELETE` → `405` + `Allow: GET` + `no-store` |

The default board is deliberately **not** extended with the new fields. The
existing suite asserts exact key sets on it, and the specification requires that
route to keep behaving exactly as today; adding `board_version` there would have
broken both. All multi-display fields are additive *and* confined to a configured
board, which is also what makes AC-19 ("the field is absent from the raw
response") a precise, testable claim.

**Rate limiting.** The limiter bucket is now `client address | display code`
instead of client address alone. Six screens polling every ten seconds is 36
requests a minute from one address; under the old key the sixth screen would
have been throttled with nobody abusing anything (risk **R-12**). Each configured
display now has its own bucket, an unknown code consumes only its own, and the
per-branch floor the specification describes remains the durable limiter's job
(GAP-20 / MP-25) — stated as a limitation, not glossed over.

**Estimate definition.** Mean of today's completed consultations for that doctor,
measured from `queue_entries.status_history` (`in_consultation` → `completed`),
used only when at least three completed consultations exist; otherwise
`AMSDP_AVG_SERVICE_MINUTES` (default 10). Rounded up, floored at 1, always an
`int`, always accompanied by `estimate: true`. It is never derived from a patient
record and never worded as a guarantee.

---

## 5. Tenancy, privacy and the safety boundary

1. **The tenant key is still `organization_id`.** The new table has exactly one
   organisation column, and the resolver looks a display up by
   `(code, branch_id, organization_id)` where the organisation comes from the
   *branch in the path* — never from the query string.
2. **Cross-tenant and cross-branch are indistinguishable from "does not exist".**
   A display whose code exists in another branch or another organisation returns
   the same 404 body and headers as an unknown branch. Two tests pin this
   (`test_a_display_of_another_branch_is_not_resolvable`,
   `test_a_display_of_another_organisation_is_never_resolvable`).
3. **Filtering is server-side.** The scoped tests assert against `r.text`, not
   the parsed object, so a field that leaked into the raw body would fail even if
   a page chose not to render it.
4. **An empty scope never widens.** `IN (SELECT …)` over an empty membership
   selects nothing; the board returns `{"doctors": []}`. There is no code path in
   which a missing or empty scope falls back to the branch.
5. **No cookie, no session, no PII.** The board publishes doctor name, token
   number, waiting count, room *label* and a facility-owned footer. No patient
   identifier, no mobile number, no appointment id.
6. **Denial accounting is bounded.** A disabled display produces at most one
   `queue.display.disabled_requested` row per five minutes; an unknown code
   produces none, so an unauthenticated caller cannot write unbounded rows into
   an append-only trail (MD-19, AC-21). The audit write is wrapped so that a
   failure cannot turn a public 404 into a 500.

---

## 6. A defect found while writing the tests — and fixed

The first green run of the new suite carried a SQLAlchemy warning:

```
SAWarning: SELECT statement has a cartesian product between FROM element(s)
"doctors" and FROM element "queue_entries"
```

The estimate query selects completed `QueueEntry` rows, but the scope predicate
had been built against `Doctor.id`. Filtering a `queue_entries` query with a
predicate on another table cross-joins the two, **multiplying every sample** by
the number of doctors in scope. With three doctors, a doctor with one completed
consultation would have been treated as having three and the facility default
would have been replaced by a "measurement" that never happened — on a public
screen, with an estimate marker next to it.

The scope predicate now takes the column to compare, and the completed
consultation query filters on `QueueEntry.doctor_id`. A regression test was added
(`test_a_scoped_board_does_not_multiply_its_estimate_samples`): one sample on a
doctor-scoped board must still show the facility default. The warning is gone
(6 → 3 warnings, all pre-existing framework deprecations).

This is recorded because it is exactly the class of defect the evidence rules
exist for: it was found by a *warning* in a run that was already green, not by a
failing assertion, and the assertion that would have caught it did not exist
until after the cause was understood.


---

## 7. Tests executed

### 7.1 The new suite — `backend/tests/test_multidisplay.py`

34 tests, all passing on the local PostgreSQL database:

```
tests/test_multidisplay.py ................ 33 passed  (before the regression test)
tests/test_multidisplay.py + test_dqds.py .. 60 passed, 3 warnings
```

What each group pins:

| Group | Tests | What fails if the behaviour is removed |
|---|---|---|
| MP-35 registry | 8 | two displays persist independently; duplicate branch code is refused by the database; the same code in another branch is allowed; a department/room scope without its target is refused; an unknown scope, language or status is refused |
| MP-36 resolution | 8 | out-of-scope token absent from the raw body; empty scope is empty; unknown display 404 identical to unknown branch; disabled display 404 identical **and** audited once; 100 unknown probes write zero audit rows; other branch / other organisation 404; default board key set unchanged |
| MP-37 / MP-41 | 3 | department scope selects only its department's doctors; room scope selects only its room's doctor; a doctor without a chamber renders `null` |
| MP-42 estimate | 4 | measured mean at n ≥ 3; facility default below that; always `int ≥ 1`; a scoped board does not multiply its samples |
| MP-43 refresh | 3 | unchanged board → `304` with no body and intact headers; a queue change changes `board_version`; the clock alone does not |
| MP-44 facility day | 1 | `operational_date` equals the facility's date, `timezone` is published, yesterday's token is absent |
| MP-45 policy | 2 | a switched-off field is absent from the raw response while the board still serves; the default policy publishes all four |
| MP-46 read-only | 5 | four verbs → `405` + `Allow: GET` + `no-store`; no `Set-Cookie` on a successful board |

### 7.2 Negative controls — three, each restored byte-identically

Each control was applied to `queuing/display.py`, the suite re-run, and the file
restored from the in-memory original; SHA-256 before/after compared.

| Control | Change | Result | Restored |
|---|---|---|---|
| **A** | board query no longer filtered by the display scope | **4 failed**, 30 passed | `True` |
| **B** | `room_name` published regardless of `show_room` | **1 failed**, 33 passed | `True` |
| **C** | `board_version` includes `updated_at` | **2 failed**, 32 passed | `True` |

Final SHA-256 of the restored file: `39accca5cddedcc6…`. A green suite that
cannot be made red is not evidence; these show that the three central claims
(scope is enforced, suppression is enforced, the version is stable) each have a
test that fails without them.


---

### 7.3 Whole-tree suites, executed after the change

```
backend   python -m pytest -q
          1027 passed, 98 warnings in 630.62s (0:10:30)

frontend  npm test -- --watchAll=false
          tests 467 | pass 465 | fail 0 | skipped 2 | duration_ms 4431
```

**Arithmetic, so the baseline cannot be read as a fluke:** the backend tree held
993 passing tests before this change; 34 were added; `993 + 34 = 1027`, and the
failure count is still `0`. The 98 warnings are pre-existing framework and test
hygiene warnings (deprecated `on_event`, `httpx` TestClient, one
`PytestReturnNotNoneWarning` in `tests/test_tracking_tokens.py`); none is
introduced by this change and the cartesian-product warning of §6 is no longer
among them.

The frontend result is unchanged from the immediately preceding baseline (465
passed, 2 skipped), which is the expected outcome of a backend-only change and is
recorded rather than assumed.

---

## 8. Governance and skill compliance

### 8.1 Applicable governance documents, and where they were read

| Domain (`.clinerules` §4 row) | Document / code consulted **in this session** |
|---|---|
| Planning and execution authority | `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` read in full (V1.1 plus Appendices A–G, lines 1–857), including §6 WP-C.2, Appendix D.3, §8 sequencing rules 8–14 |
| Multi-display requirements | `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` §5.1–5.6 (data model, public contract, administrative contract, presentation, language precedence) and Appendix E (§E.3 MD-13…MD-19, §E.4 data-model delta, §E.5 contract deltas, §E.6 AC-15…AC-22) |
| Product rules | `docs/product/AMSDP_Business_Rules_V1.0.md` §33 (items 1–13) and §33.1 (PO-13 scope status), read directly |
| Backend API / public surface | `backend/queuing/display.py` (read in full before editing), `backend/queuing/main.py` router wiring, `backend/common/timeutil.py` |
| Multi-tenant data | `backend/common/models.py` (Organization/Branch/DoctorBranch/FacilityRoom/QueueEntry and the surrounding conventions), `backend/common/permissions.py` (capability matrix and wildcard expansion) |
| Database / migrations | `backend/alembic/versions/b2e5c7d91a04_add_schedule_blocks.py` as the house style (docstring rationale, `has_table` guards, index existence checks), `backend/alembic/env.py`, `backend/alembic.ini`, Alembic's `ScriptDirectory` head query |
| Audit | `backend/common/audit.py` (`record_audit` signature and actor fields), `audit_events` model |
| Frontend UX | Read only to establish what the page consumes (`docs/implementation/AMSDP_Multi_Display_DQDS_Documentation_Update_Report_V1.0.md` §"per-display scope"); **no frontend file was changed** |
| Documentation placement | `.clinerules` §11–§12; `docs/governance/AMSDP_Docs_Index_V1.0.md` revision markers (base Revision 48, annexes 49 and 50) |

**One reading gap, stated plainly:** the full `AMSDP_Docs_Index_V1.0.md` was not
re-read end to end in this session; the Q-1/Q-2 annex (Revision 50) and the
numbering were consulted so that this report's annex could be numbered 51
without retro-labelling anything. Every other document above was opened and read
here, not remembered.

### 8.2 Skills

**No skill is installed in this workspace** (no `.clinerules/skills/`, no
`.claude/skills/`, no repo `skills/`; verified in previous windows and unchanged
since — no skill directory was created in this one). **No skill was used, and
none is claimed.** The governance documents above were the working method.

### 8.3 The ten non-negotiables (`.clinerules` §3), one by one

| # | Requirement | How it is satisfied here |
|---|---|---|
| 1 | Never log or expose secrets | no credential was printed, stored or committed; the database was reached passwordlessly on the local socket; the only masked value printed was a URL with its password redacted |
| 2 | The UI is never the safety boundary | suppression and scoping are applied while the JSON body is built; tests assert on the raw response text |
| 3 | Server-side access, principal-derived scope | the display's organisation comes from the branch in the path and is re-checked against the row; no request body participates |
| 4 | Cross-tenant/branch ⇒ 404, never 403 | the shared `_not_found()` is used for unknown org, unknown branch, unknown display, other branch, other organisation and disabled display |
| 5 | `organization_id` is the only tenant key | the new tables carry exactly one organisation column; no second tenant column was introduced |
| 6 | Audit is append-only and persistent | the only new audit action is an insert; no row is updated or deleted; the test fixture removes its own test rows by `target_id`, never by truncation |
| 7 | Denials are recorded, not swallowed | `queue.display.disabled_requested` is written for a disabled display (throttled); the anonymous unknown-code case is deliberately **not** audited, per MD-19, because writing there would be an amplification path |
| 8 | Forward-only, idempotent migrations, no ad-hoc DDL | one revision, `down_revision` = the actual head, `CREATE` guarded by `has_table`/`get_indexes`, applied twice with the second run a no-op |
| 9 | Never claim an unverified capability | §1 and §10 keep IMPLEMENTED/TESTED apart from VERIFIED/ACCEPTED; MP-38/39/40 are named as not delivered |
| 10 | Do not use a tool or library merely because it exists | no new dependency was added; the work uses SQLAlchemy, Alembic, FastAPI and pytest, all already in use |

### 8.4 Evidence standard (`.clinerules` §7)

| Class | Items |
|---|---|
| **IMPLEMENTED** | the two models, the revision, the resolver, the scope predicate, the estimate, the version/`ETag`, the policy suppression, the verb guard, the disabled-display audit |
| **TESTED** | 34 new tests plus the 26 existing DQDS tests, and the whole-tree run recorded in §7.3 |
| **VERIFIED** | *nothing for the live deployment.* The schema proof (31 → 33 tables, zero existing tables changed) and the `alembic current` read are local-database artefacts, and are labelled as such |
| **ACCEPTED** | nothing |



---

## 9. Disclosures — everything a reviewer would otherwise have to discover

1. **No database dump was taken** (no `pg_dump` on the host). A schema snapshot
   with a recorded SHA-256 replaced it, and the migration is additive-only. §3
   has the detail. If the policy requires a real dump, it must be taken on a host
   that has the client tools.
2. **The migration was applied to the local development database only.** The
   owner's deployment still runs its earlier schema; serving a configured display
   there needs a forward-only upgrade in an authorised maintenance window
   (**B-4**). Nothing was opened, rebound or reconfigured.
3. **MP-35's "seed of two demo displays" is not delivered.** The registry is
   complete and tested, but the seed was deliberately not extended: without MP-39
   an administrator cannot create, edit or disable a display, so seeding rows by
   hand would ship configuration with no way to change it — and the demonstration
   would depend on data nobody can maintain. It belongs with the demo-data step
   once MP-39 exists.
4. **The rate limiter is now keyed per `(client, display)`.** That is a behaviour
   change to a public endpoint, made deliberately for the six-screen case
   (R-12), and covered by the unchanged 429 tests. The per-branch floor described
   in MD-10, and durability across worker processes, remain **MP-25**.
5. **The disabled-display throttle is in-process** (a module dict), like the
   limiter. Two workers could each write one row per five minutes. That is
   bounded and auditable, but it is not the durable dedupe MP-25 will provide.
6. **No frontend file was changed.** The new payload fields (`display`,
   `room_name`, `estimated_wait_minutes`, `footer_text`, `board_version`) are
   served but not yet rendered: configured language and TV typography are MP-38,
   and the administration page is MP-39.
7. **One mojibake character was repaired** in the comment block of
   `queuing/display.py` that this change rewrote (`BR Â§8` → `BR §8`). It is an
   encoding artefact in a comment, not a behaviour change, and it is mentioned
   because it appears in the diff.
8. **A test-fixture namespace collision was found**: ids prefixed `md-doc-*` are
   already owned by another test module (`m5-org`). This module's fixtures were
   renamed to `mdisp-*`. No product code was affected; it is recorded because it
   is the kind of collision that makes a suite pass or fail for the wrong reason.
9. **`queue.*` already grants `queue.display.manage`** to the three administrator
   roles through the existing wildcard, and does **not** grant it to
   `receptionist`, `doctor` or `assistant`. MP-39 therefore needs no new role and
   no `DELEGABLE_CAPABILITIES` change; that claim is **not** used here, because
   MP-39's routes do not exist yet.

---

## 10. Task status after this slice — precise, not optimistic

| Task | Status | Why |
|---|---|---|
| **MP-35** | **IMPLEMENTED, TESTED** (seed outstanding) | models, revision, constraints, idempotency and blast-radius proofs done; §9 item 3 for the seed |
| **MP-36** | **IMPLEMENTED, TESTED** | resolver, SQL scope, identical 404s, unchanged default board |
| **MP-37** | **IMPLEMENTED, TESTED** | department scope + `room_name`; page rendering is MP-38 |
| **MP-41** | **IMPLEMENTED, TESTED** | room scope, CHECK constraint, empty-state test |
| **MP-42** | **IMPLEMENTED, TESTED** (payload half) | computation and marker done; BN/EN copy and the rendered row are MP-38 |
| **MP-43** | **IMPLEMENTED, TESTED** (API half) | `board_version`, weak `ETag`, `304`; the page's no-re-render behaviour is MP-38 |
| **MP-44** | **IMPLEMENTED, TESTED** for the display path | `operational_date` + `timezone` published; the 23:59/00:00 Dhaka observation is **BLOCKED — B-3** |
| **MP-45** | **IMPLEMENTED, TESTED** server-side | suppression proven on the raw body; the **admin controls are MP-39** |
| **MP-46** | **PARTIAL — IMPLEMENTED, TESTED** | GET-only guard, `Allow: GET`, `no-store`, disabled-display audit and its throttle are done; `queue.display.denied` attaches to MP-39's write routes and is **not** claimed |
| **MP-38** | **NOT STARTED** | frontend: configured language above the device setting, `clamp()` typography, display name in the header, BN/EN labels |
| **MP-39** | **NOT STARTED** | admin routes, `queue.display.manage` enforcement, audit of writes, one page with a copyable URL |
| **MP-40** | **BLOCKED** | the demonstration needs MP-38, MP-39, the demo seed and the live stack (**B-4**); AC-01…AC-22 evidence cannot be produced from `TestClient` |
| **B-2 / B-3 / B-4** | **UNCHANGED** | live runtime verification, midnight rollover observation, database access method |
| **MP-33** | **UNCHANGED** | no CI run was observed; `gh` is not installed on this host |

**Milestone effect.** **M-9 (multi-display functional)** is not met: MP-38, MP-39
and MP-35's seed are outstanding. **M-10 (Hackathon Version complete)** is
therefore not met either. What *is* met is the part of M-9 that the public
surface carries — two displays with independent scopes and languages persisted in
one branch, server-side filtering, and the isolation and read-only guarantees —
proven by tests, not by demonstration.

---

## 11. Where this report lives, and what it amends

- **Written to** `docs/implementation/`, per `.clinerules` §11 (`implementation/`
  is the sanctioned subject folder for milestone and implementation reports). No
  new folder was created, nothing was moved, renamed or migrated, so no migration
  manifest entry is required.
- **Roadmap:** Amendment **A-5** (Appendix H of
  `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`) records the
  executed status changes, the corrected migration head, and the B-4
  clarification. It is append-only: no earlier statement is rewritten.
- **Register:** §11 of `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md`
  records the executed package, its verification and its blockers.
- **Index:** `docs/governance/AMSDP_Docs_Index_V1.0.md` **Revision 51** registers
  this report and the B-4 decision brief.
- **Push, verified:** two path-grouped commits — `082e2a0` (backend) and `1f303d1`
  (docs) — went to `origin/hackathon-mvp`; the remote reported
  `0bd8059..1f303d1  hackathon-mvp -> hackathon-mvp`, and after a fetch local
  `HEAD` and `origin/hackathon-mvp` were both
  `1f303d1502819f45a0e27793c1e75f1a7c9c3c29` (`0  0` ahead/behind). No force-push,
  no rewrite, no other branch. A green suite and a pushed commit still do not
  make CI green: **MP-33 is unchanged**, and `gh` is not installed on this host.
- **Next eligible work** is MP-39 (display administration), then MP-38 (configured
  language and TV typography) — MP-40 depends on both plus B-4, and MP-31/MP-32
  depend on the live stack.

