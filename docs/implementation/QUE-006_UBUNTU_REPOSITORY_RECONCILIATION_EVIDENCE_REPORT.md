# QUE-006 — Ubuntu Repository Reconciliation Evidence Report

**Document ID:** `QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT`
**Version:** 1.0
**Date:** 2026-11-22
**Author:** Cline (agent), read-only inspection task
**Location:** `/home/shomonrobie/amsdp/docs/implementation/` (per `.clinerules` §11 — subject folder `implementation/`, no new folder created)
**Subject host:** Ubuntu workstation `/home/shomonrobie/amsdp`
**Comparison target:** a separately built Windows "*W2*" announcement-reliability implementation (not present on this host)
**Nature of document:** evidence record. It states what was **observed** on this host and nothing more.

---

## 0. Label legend and honesty statement

| Label | Meaning in this document |
|---|---|
| **VERIFIED** | A second, independent artefact confirms it. Here: a live read-only PostgreSQL query, or an executed shell command whose output is quoted. |
| **IMPLEMENTED** | The code exists in this tree and is reachable from a registered route, export, or import path. Reached by reading the file, not by running it. |
| **PARTIALLY VERIFIED** | The artefact exists and is reachable, but a required confirmation (the test run, the runtime call) was not performed in this session. |
| **NOT VERIFIED** | No artefact on this host confirms it. Not the same as "false" — it means *unproven here*. |
| **NOT PRESENT** | The file, symbol, table, or column does not exist on this host. Established by filesystem sweep, source sweep, and (where applicable) catalog query. |
| **BLOCKED** | The check could not be performed on this host for a stated reason. |

**Honesty statement.** This inspection was **strictly read-only**. No source file, migration, database row, container, or Git history entry was created, modified, or deleted by the inspection, and **no test suite was executed**. Consequently:

- No claim in this document is **ACCEPTED** (owner sign-off) — nothing was submitted for acceptance.
- No claim in this document is **VERIFIED** on the strength of a green test suite; the only VERIFIED labels below rest on live command output.
- Test *counts* are read from the tree by `grep`; **passing** is not asserted here, only presence.
- Where a prior QUE-006 implementation report claims a run (e.g. "73/73 announcement tests"), this document repeats that claim **as a prior claim**, attributed, and does not adopt it.

---

## 1. Scope and method

### 1.1 Question this report answers

The W2 announcement-reliability implementation was built on a separate Windows checkout. This report records, from evidence gathered on this Ubuntu host only:

1. What QUE-006 room-support work exists **here** (backend contract, frontend announcement layer, tests, schema, live data).
2. What W2 work exists **here** — which, as §5.2 and §9.2 show, is **nothing**.
3. Which parts of the present implementation any future merge of W2 must **preserve** (§11).
4. Which questions could **not** be answered here, and why (§12).

### 1.2 Method

Two probe families, both non-mutating:

- **Repository probes** — `git rev-parse`, `git log`, `git status --short -uall`, `git diff --stat`, `git diff`, `sed`/`grep`/`find` reads of source, migrations, tests, and docs.
- **Runtime probes** — `docker compose ps` (state only) and read-only `SELECT` queries piped into the running `db` container: `information_schema` catalog reads and `to_regclass(...)` existence checks. No `INSERT`/`UPDATE`/`DELETE`, no DDL, no `alembic` command, no container start/stop/restart, no test run.

Raw artefacts were staged under `/tmp/que006_inspect/` (repository-external scratch, not an AMSDP document location): `status_final.txt`, `phaseA2.txt`, `phaseB2.txt`, `phaseB3.txt`, `heads.txt`, `routes.txt`, `anchors.txt`, `containers.txt`, `db_ver3.txt`, `dbtables2.txt`, `db_queue.txt`, `db_room.txt`, `w2sweep.txt`, `alembic_run.txt`, `tests.txt`, `tests2.txt`, `queue_test_names.txt`, `misc4.txt`–`misc9.txt`, plus per-file diffs `backend.diff`, `content.diff`, `controller.diff`, `speech.diff`.

### 1.3 What this report is *not*

- It is **not** a test report: no suite ran.
- It is **not** a compatibility verdict: W2 is absent here, so "W2 is compatible with this tree" **cannot be claimed** (§11.1).
- It is **not** a claim about the Windows host. Nothing here describes a machine that was not the one inspected.

## 2. Repository identity — VERIFIED

| Item | Observed value | How |
|---|---|---|
| Working directory | `/home/shomonrobie/amsdp` | `pwd` |
| Branch | `hackathon-mvp` | `git rev-parse --abbrev-ref HEAD` |
| HEAD commit | `cd2f9ecdf51b363105214e3ffd504d3adc151ada` | `git rev-parse HEAD` |
| Upstream | `origin/hackathon-mvp` | `git rev-parse --abbrev-ref --symbolic-full-name @{u}` |
| Last commit | `cd2f9ec` · 2026-11-20 15:03:30 +0600 · `shomonrobie` · *"docs: add AMSDP website content and copywriting proposal"* | `git log -1 --date=iso` |
| Tags at HEAD | none printed | `git tag --points-at HEAD` |

**Interpretation.** The tree is a `hackathon-mvp` working copy whose newest commit is dated 2026-11-20, carrying uncommitted work (§3). Nothing about the Windows W2 checkout can be inferred from this identity block.

---

## 3. Working-tree inventory and diffstat — VERIFIED

`git status --short -uall` returned **exactly 20 entries: 13 modified, 7 untracked.** This is the pre-existing state of the checkout. **None of it was produced by this inspection**, and the inspection changed none of it (§12.2 records the post-inspection re-check).

### 3.1 Modified (tracked)

```
 M .gitignore
 M backend/appointment/main.py
 M backend/queuing/main.py
 M backend/queuing/recovery.py
 M docs/governance/AMSDP_Docs_Index_V1.0.md
 M frontend/lib/announcements/content.js
 M frontend/lib/announcements/controller.js
 M frontend/lib/announcements/speech-synthesis.js
 M frontend/pages/queue.js
 M frontend/tests/queue-announcement-content.test.mjs
 M frontend/tests/queue-announcement-controller.test.mjs
 M frontend/tests/queue-announcement-speech.test.mjs
 M frontend/tests/queue-announcements-boundary.test.mjs
```

### 3.2 Untracked

```
?? backend/common/locations.py
?? backend/tests/test_queue_room_snapshot.py
?? docs/architecture/AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_Plan_V1.0.md
?? docs/chatgpt/AMSDP_Project_Handover_2026-11-20.md
?? docs/implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md
?? frontend/lib/announcements/dedupe.js
?? frontend/tests/queue-announcement-dedupe.test.mjs
```

### 3.3 Diffstat

```
 .gitignore                                         |   1 +
 backend/appointment/main.py                        |  12 +-
 backend/queuing/main.py                            |  62 +++++++-
 backend/queuing/recovery.py                        |  19 ++-
 docs/governance/AMSDP_Docs_Index_V1.0.md           |  34 +-
 frontend/lib/announcements/content.js              | 176 ++++++++++++++++---
 frontend/lib/announcements/controller.js           |  99 ++++++++---
 frontend/lib/announcements/speech-synthesis.js     | 124 ++++++++-----
 frontend/pages/queue.js                            |   7 +-
 frontend/tests/queue-announcement-content.test.mjs | 128 ++++++++++++---
 frontend/tests/queue-announcement-controller.test.mjs | 170 ++++++++++++++---
 frontend/tests/queue-announcement-speech.test.mjs  |  36 ++++-
 frontend/tests/queue-announcements-boundary.test.mjs |  12 ++
 13 files changed, 726 insertions(+), 154 deletions(-)
```

### 3.4 What the uncommitted work is

The set is coherent and self-labelled: it is the **QUE-006 F1–F4 announcement correction plus the F4 room-support work** — the room resolver module (`backend/common/locations.py`, new), the queue serializer and wiring changes (`backend/queuing/main.py`, `recovery.py`, `appointment/main.py`), the frontend announcement layer (`content.js`, `controller.js`, `speech-synthesis.js`, and the new `dedupe.js`), the queue page wiring (`pages/queue.js`), the room-snapshot test (new), the dedupe test (new), and the two new QUE-006 documents plus their index registration.

The only `docs/governance/` change is the index registration of those two documents (Revision 34/36 text). The only `.gitignore` change is one added line, `.aider*`. That line is unrelated to QUE-006 — noted so it is not later mistaken for part of the announcement work.

**Consequence for reconciliation:** room-support work on this host is **uncommitted**. It exists as working-tree changes on top of `cd2f9ec`, not as a commit. Any cherry-pick, diff, or merge strategy aimed at W2 must be taken against the *working tree*, not against `HEAD`.

---

## 4. Alembic migration graph and head state — VERIFIED

### 4.1 Inventory

`backend/alembic/versions/*.py` contains **14 revision files**. The chain was reconstructed by parsing each file's `revision` and `down_revision` (a local script; no `alembic` command was run, so nothing touched the database):

| Revision | File | down_revision |
|---|---|---|
| `5f3fce6757cf` | `5f3fce6757cf_initial_schema.py` | *(root)* |
| `ccf34da72c1b` | `ccf34da72c1b_add_queue_sequences.py` | `5f3fce6757cf` |
| `c7d3601e2486` | `c7d3601e2486_add_audit_branch.py` | `ccf34da72c1b` |
| `9d8a1f2b3c4d` | `9d8a1f2b3c4d_add_staff_doctor_link.py` | `c7d3601e2486` |
| `3c8e5d0a9b2f` | `3c8e5d0a9b2f_add_patient_age.py` | `9d8a1f2b3c4d` |
| `a1f2b3c4d5e6` | `a1f2b3c4d5e6_add_tracking_tokens.py` | `3c8e5d0a9b2f` |
| `b7c1e4d90a52` | `b7c1e4d90a52_add_notifications.py` | `a1f2b3c4d5e6` |
| `d4b2c8e1f7a3` | `d4b2c8e1f7a3_add_login_attempts.py` | `b7c1e4d90a52` |
| `e6c1a9b3d5f8` | `e6c1a9b3d5f8_drop_redundant_tracking_token_index.py` | `d4b2c8e1f7a3` |
| `f7d2b4c6e8a1` | `f7d2b4c6e8a1_add_facility_hierarchy_doctor_profile.py` | `e6c1a9b3d5f8` |
| `f8a1b2c3d4e5` | `f8a1b2c3d4e5_add_staff_doctor_assignments.py` | `e6c1a9b3d5f8` |
| `f8a2b3c4d5e6` | `f8a2b3c4d5e6_add_platform_audit_events.py` | `f8a1b2c3d4e5` |
| `b3d7e91f6a24` | `b3d7e91f6a24_add_symptom_catalogue.py` | `f7d2b4c6e8a1` |
| `a9c4e1f7b2d8` | `a9c4e1f7b2d8_appointment_types_and_capacity_integrity.py` | `b3d7e91f6a24`, `f8a2b3c4d5e6` *(merge)* |

### 4.2 Head analysis

- **Heads: exactly one — `a9c4e1f7b2d8`.** (Computed as `revisions − all down_revisions`.)
- **No dangling parent:** every `down_revision` named is a revision present locally.
- **One fan-out, one merge:** `e6c1a9b3d5f8` forks into the facility-profile branch (`f7d2b4c6e8a1`) and the staff-assignments branch (`f8a1b2c3d4e5`); `a9c4e1f7b2d8` merges both with the multi-parent `down_revision = ('b3d7e91f6a24', 'f8a2b3c4d5e6')`. The graph is linear at the head, so a W2 migration would have exactly one place to attach (`a9c4e1f7b2d8`) — no second head to reconcile **today**.

### 4.3 Announcement-related migration content

`grep -rIn -i 'announce|call_event|delivery' backend/alembic/versions/*.py` returns **no matches**. No migration creates an announcement, call-event, or delivery table, and no migration adds a `call_event_id` column.

### 4.4 Legacy, non-Alembic SQL (observation, not a finding)

`backend/queuing/migrations/001_create_queue_entries.sql` exists (766 bytes) with `CREATE TABLE IF NOT EXISTS queue_entries (...)`. It declares `queue_entry_id TEXT PRIMARY KEY` and no ORM column (`id`, `position_history`) — i.e. it is a **pre-Alembic bootstrap** and does not match the current ORM. A repository-wide grep finds it referenced only by itself and by `runs/RUN-*.json` AI-Factory logs; it is **not** referenced by `docker-compose.yml`, any Dockerfile, or any entrypoint (there are no entrypoint files). The live schema matches the ORM, not this file (§5.3), so it appears superseded. **`.clinerules` §3** requires every schema change to ship as a forward-only idempotent Alembic migration; this file is not part of that mechanism and should not be extended.

### 4.5 How migrations reach the database (relevant to any W2 claim about "the migration ran")

No Dockerfile, `docker-compose.yml`, or entrypoint runs `alembic upgrade` (grep returned nothing, and no entrypoint files exist). The deployment documents instead instruct running it from the host, e.g. `docs/deployment/AMSDP_Platform_Restart_and_Redeploy_Runbook_V1.0.md:199` — `python -m alembic upgrade head`. **Consequence:** "the container started" proves nothing about schema state; only the live `alembic_version` read (§5.1) does.

## 5. Live database state — VERIFIED (read-only)

All queries below were `SELECT`-only, piped as a file into the running `db` container, authenticating with the container's own `POSTGRES_USER`/`POSTGRES_DB` environment (no credential appears in this document; `.clinerules` §3 and §12). Exit status `0` on every query.

### 5.1 Applied revision

```
SELECT version_num FROM alembic_version;
→ a9c4e1f7b2d8
```

**Finding: the live database is exactly at the single local head** (`a9c4e1f7b2d8`, §4.2). Code and schema are in step; there is no pending local migration and no un-applied revision. This is the first item on this host carrying the label **VERIFIED** rather than "implemented".

### 5.2 Announcement / event tables — NOT PRESENT (proven, not assumed)

```
SELECT to_regclass('public.alembic_version'),
       to_regclass('public.queue_entries'),
       to_regclass('public.queue_announcement_deliveries'),
       to_regclass('public.queue_call_events');
→ alembic_version | queue_entries | (null) | (null)

SELECT table_name FROM information_schema.tables
 WHERE table_schema='public' AND table_name LIKE '%queue%' ORDER BY 1;
→ queue_entries
→ queue_sequences
```

**Findings.** The `public` schema contains exactly **two** queue-related tables: `queue_entries` and `queue_sequences`. `queue_announcement_deliveries` and `queue_call_events` **do not exist** (`to_regclass` returned NULL for both). No announcement-delivery, call-event, or event-outbox storage of any name exists on this host.

### 5.3 `queue_entries` — the 17 columns that actually exist

```
id varchar · organization_id varchar · branch_id varchar · doctor_id varchar ·
date date · position int · token varchar · patient_id varchar · appointment_id varchar ·
entry_source varchar · status varchar · status_history json · position_history json ·
notes text · added_by varchar · created_at timestamptz
```

**Findings.**
- The table matches the ORM (`backend/common/models.py::QueueEntry`) and the Alembic chain — **not** the legacy SQL bootstrap (§4.4).
- There is **no** `call_event_id`, no announcement counter, no "last announced at", and no delivery state on the row. Announcement identity and delivery reliability **cannot** be reconstructed from this table today.
- `status_history` and `position_history` are `json` (arrays written by the service; §7).

### 5.4 Room columns that exist (the F4 dependency)

```
SELECT table_name||'.'||column_name FROM information_schema.columns
 WHERE table_schema='public' AND (column_name LIKE '%room%' OR column_name='location_label');
→ appointments.room_id varchar
→ appointments.room_name varchar
→ doctor_branches.room_id varchar
→ facility_rooms.room_type varchar
→ schedule_sessions.room_id varchar
```

**Findings.**
- The booking snapshot the room contract reads — `appointments.room_id` and `appointments.room_name` — **exists** in the live database. F4's premise is real, not aspirational.
- **`location_label` is not a column.** It is derived at read time by `common/locations.location_label()` from `floor_name / department_name / room_name` (§7.1). Any W2 change that assumes a stored `location_label` column would be wrong.
- Three competing room sources exist in the schema (`appointments`, `doctor_branches`, `schedule_sessions`) — which is precisely why the F4 contract pins the announcement to the **booking snapshot** and forbids the doctor's current chamber (§7.1).

### 5.5 Container state (context, not a QUE-006 claim)

`docker compose ps` — all eleven services `running`, `Up 38 hours (healthy)`: `appointment`, `audit`, `db`, `doctor`, `frontend`, `identity`, `organization`, `patient`, `queuing`, `scheduling`. Health here means the containers answer their probes; it says nothing about announcement behaviour, and no announcement was exercised.

## 6. Backend queue route inventory and router registration pattern — IMPLEMENTED

### 6.1 Routes served by the `queuing` service

| Method + path | Source | Line | Notes |
|---|---|---|---|
| `GET /api/v1/queue` | `backend/queuing/main.py` | 168 | Page listing; resolves rooms once per page (§7.2) |
| `POST /api/v1/queue/check-in` | `backend/queuing/main.py` | 219 | 201; creates an entry from an appointment |
| `POST /api/v1/queue/enqueue` | `backend/queuing/main.py` | 345 | 201; walk-in / staff placement |
| `PATCH /api/v1/queue/{entry_id}` | `backend/queuing/main.py` | 446 | The single transition endpoint (status machine) |
| `POST /api/v1/queue/reorder` | `backend/queuing/main.py` | 525 | Position changes, token preserved |
| `GET /api/v1/queue/history` | `backend/queuing/main.py` | 598 | Branch-scoped history |
| `POST /api/v1/queue/{entry_id}/missed-turn` | `backend/queuing/recovery.py` | 148 | Router prefix `/api/v1/queue` (line 36) |
| `POST /api/v1/queue/{entry_id}/recover` | `backend/queuing/recovery.py` | 197 | Router prefix `/api/v1/queue` |
| `GET /api/v1/queue/display/{org_code}/{branch_code}` | `backend/queuing/display.py` | 127 | Public read-only TV board; prefix `/api/v1/queue/display` (line 24) |

**There is no announcement route** — no `POST .../announcements`, no `.../announce`, no delivery-claim or acknowledgement endpoint anywhere in the service.

### 6.2 The registration pattern a future announcement router must follow

`backend/queuing/main.py:28–43` registers the two existing sub-routers with a dual-import shim, because the service is importable both as a package (`backend.queuing.main`) and as a flat module inside the container:

```python
try:
    from .display import router as display_router
except ImportError:
    from display import router as display_router
app.include_router(display_router)

# Sequence 3 — missed-turn recovery (BR §27A). Kept in its own module so the
# recovery contract stays readable and independently testable.
try:
    from .recovery import router as recovery_router
except ImportError:
    from recovery import router as recovery_router
app.include_router(recovery_router)
```

Any W2 announcement module (`queuing/announcements.py`, if that is its name) must be added in **exactly this shape**: own module, own `APIRouter` with a `/api/v1/queue`-derived prefix, and the same `try: from .x import ... except ImportError: from x import ...` include. A plain `from .announcements import ...` breaks the flat-import deployment path; a plain `from announcements import ...` breaks package imports and the test suite.

Also installed at startup, and not to be bypassed by a new router: `install_token_redaction`, `install_health`, and `install_denial_audit(app, "queuing")` (line 29 — *"Q-2: every 403/404/422 answered by this service is written to the audit trail"*). A new announcement endpoint inherits denial auditing only if it is registered on this same `app`; a separately constructed `FastAPI()` instance would drop it and violate §3 ("denials are recorded, never silently swallowed").

### 6.3 Authorisation shape every queue endpoint already uses

`main.py` imports `AuthContext, get_current_user, require_permission, branch_accessible` from `common.auth` and `permission_check` from `common.permissions` (lines 16–17). Scope is derived from the token, never the body — `branch_accessible` is the gate, org/branch come from `auth`. A W2 endpoint that accepts an `organization_id` or `branch_id` from the request body would violate §3 of `.clinerules`; the same is true of any announcement endpoint that trusts a client-supplied `doctor_id` without the scope check the existing routes perform.

## 7. The queue room-support contract as implemented here — IMPLEMENTED

### 7.1 The resolver: `backend/common/locations.py` (untracked, new)

| Line | Symbol | What it fixes in place |
|---|---|---|
| 21 | `ROOM_SOURCE_APPOINTMENT = "appointment_snapshot"` | The only source currently produced |
| 23 | `ROOM_SOURCE_WALK_IN = "walk_in_capture"` | Reserved; *"Nothing writes it yet"* |
| 27 | `NO_ROOM = {"room_id": "", "room_name": "", "label": "", "source": ""}` | The empty answer; must never be read as "Room 0" or as a fallback to the doctor's current chamber |
| 30 | `location_label(snapshot)` | Joins `floor_name / department_name / room_name` with `" / "`, omitting missing parts; `None` → `""` |
| 47 | `room_payload(snapshot, source=ROOM_SOURCE_APPOINTMENT)` | Returns `{room_id, room_name, label, source}`; `source` collapses to `""` when `room_name` is empty |

The decisive rule is at line 66: `"source": source if room_name else ""`. A snapshot with a floor and a department but **no room name** is therefore *not* announceable, and the caller degrades to the approved room-less sentence instead of inventing a room. The docstring is explicit that the announcement uses `room_name` only — a floor or a department alone names nothing the patient can walk into.

### 7.2 The serializer: `backend/queuing/main.py:83–140`

```python
def _entry_to_dict(e, room=None):          # line 83
    ...
    "room_id": room.get("room_id") or "",          # 107
    "room_name": room.get("room_name") or "",      # 108
    "location_label": room.get("label") or "",     # 109
    "room_source": room.get("source") or "",       # 110
```

- `room` is **passed in**, never looked up inside the serializer (line 86–90): a page of entries costs one query, and no code path can read the doctor's *current* chamber by accident.
- The four fields are additive and backward compatible: an entry with no room keeps four empty strings rather than raising (lines 92–95, 107–110). This is what keeps every pre-existing caller working.
- Note the naming asymmetry that must be preserved: the payload *source* key is `label`, the queue *serializer* key is `location_label`; the payload key is `room_id`/`room_name`/`source`, the serializer key is `room_source`.

Two resolution paths, deliberately different in cost:

| Function | Line | Used for | Query cost |
|---|---|---|---|
| `_rooms_for(session, entries)` | 114 | A page of entries (`GET /api/v1/queue`) | **One** `appointments` query for the whole page, re-asserting `organization_id IN (...)` (lines 125–128) |
| `_room_for_entry(session, entry)` | 132 | A single-entry action response | One query, filtered by `id` **and** `organization_id` (lines 136–139) |

The batch path's tenant filter is not decorative: `Appointment.organization_id.in_({e.organization_id for e in entries})` keeps a cross-org appointment id from ever resolving a room across tenants (§3).

`room_payload` is imported once, at `main.py:19`. Both `check-in` (line 319: `result = _entry_to_dict(entry, room_payload(appt))`) and the single-entry action response use it; the page path uses `_rooms_for`.

### 7.3 What the queue already persists for a call — the only place W2 could hang identity today

- **Creation seeds history.** `check-in` (line 286) and `enqueue` (line 397) both write `status_history=[{"from": "", "to": "waiting", "actor": auth.user_id, "at": _now_iso()}]`.
- **Every transition appends.** `queue_action` (line 446) does `sh = list(entry.status_history or [])` (473), appends, then `entry.status_history = sh` (477). The `called` transition therefore leaves a timestamped record of *when* the call happened and *who* made it.
- **Audit is written for queue actions.** `record_audit(session, service="queuing", org_id=auth.organization_id, ...)` at lines 305, 312, 401, 493, 569. `remove`/`reorder`/recovery paths write their own events.
- **Recovery serialises the same room.** `recovery.py:69 _entry_payload(session, entry)` is the single payload builder used by both `missed-turn` (line 180) and `recover` (line 268), so recovery answers and list answers agree about the room.

**Consequence for W2.** A call *event* identity can, in principle, be derived from `status_history` (append-only array of `{from,to,actor,at}`) — but nothing gives it a stable id, nothing records whether the call was *announced*, and nothing records delivery. W2's `call_event_id` / `current_call_event` have **no host structure** here (§5.3, §8).

## 8. Room-support test inventory — PARTIALLY VERIFIED (present and readable; not executed)

### 8.1 `backend/tests/test_queue_room_snapshot.py` (untracked, new) — 15 test functions

Its module docstring declares it the **test of record** for the contract, in three parts: pure helpers (`common/locations.py`), the serializer (`queuing/main._entry_to_dict`), and end-to-end over PostgreSQL through the real `GET /api/v1/queue` with a real staff JWT.

| Line | Test |
|---|---|
| 171 | `test_location_label_names_the_chamber_snapshot` |
| 176 | `test_location_label_omits_parts_the_clinic_does_not_model` |
| 183 | `test_location_label_of_no_snapshot_is_empty` |
| 188 | `test_no_room_is_the_empty_answer_and_clears_every_field` |
| 194 | `test_room_payload_without_a_room_name_is_not_announceable` |
| 208 | `test_room_payload_names_the_booking_snapshot_as_its_source` |
| 222 | `test_entry_dict_without_a_room_keeps_four_empty_room_fields` |
| 241 | `test_entry_dict_carries_the_resolved_room` |
| 261 | `test_queue_page_announces_the_snapshotted_chamber` |
| 273 | `test_walk_in_entry_announces_without_a_room` |
| 289 | `test_enqueue_endpoint_reports_no_room_for_a_walk_in` |
| 302 | `test_each_entry_on_one_page_keeps_its_own_room` |
| 318 | `test_a_page_of_entries_costs_one_appointments_query` |
| 332 | `test_recovery_payload_reports_the_same_room` |
| 352 | `test_queue_page_never_leaks_another_branch` |

Two of these are the ones a W2 merge is most likely to break: **line 318** pins the one-query-per-page guarantee (a per-entry room lookup added by a reliability feature would fail it), and **line 352** pins branch isolation of the page (any new join-based room resolution must keep the tenant filter).

The file uses `fastapi.testclient.TestClient`, `amsdp_test_support` fixtures, `common.database.SessionFactory`/`engine`, and clears rows with `purge_org`; it runs against the throwaway development database, so it is destructive to dev rows by design (it reuses reference rows because the append-only audit trail points at them).

### 8.2 The rest of the backend queue suite (tracked, unmodified)

- `backend/queuing/tests/test_queue.py` — **58** test functions, **clean** in `git status` (unchanged by the QUE-006 work). It covers transitions (`test_lifecycle`, `test_invalid_transition`), branch/org isolation (P0-1…P0-5), RBAC (R1/R3/C1–C3), recovery authorisation, token uniqueness, position history, persistence across reopen, and audit (`test_queue_ops_write_audit_events`, line 284, which asserts a `queue.enqueue` audit row with `organization_id == "m5-org"` and `actor_role == "receptionist"`).
- **It contains no room, announcement, or delivery assertions.** `grep 'def test_' | grep -i 'room|call|history|announce'` matched only the three `history` authorisation tests (lines 886, 897, 925). Room support is therefore proven only by the new file, and announcement behaviour is proven only on the frontend (§9).
- `backend/tests/` holds 12 further `test_*.py` files (`test_dashboard`, `test_denial_audit`, `test_dqds`, `test_e2e`, `test_facility_doctor`, `test_patient_age`, `test_platform_admin`, `test_queue_room_snapshot`, `test_security`, `test_sequence3`, `test_sequence4`, `test_symptom_catalogue`, `test_tracking_tokens`) plus `amsdp_test_support.py`.

### 8.3 Prior claims, quoted not adopted

The index row for `implementation/AMSDP_QUE-006_F1_F4_Announcement_Corrections_Implementation_Report_V1.0.md` claims **"73/73 announcement tests, 253/253 frontend suite, 15/15 room-snapshot tests, 464 backend suite — and no browser/device playback run, so nothing is VERIFIED and nothing is ACCEPTED"**. Those numbers are consistent with the tree (73 announcement test cases, 15 room-snapshot tests — §9.3), but **no suite was run in this inspection**, so they are **NOT VERIFIED** here.

**No browser or device playback exists on this host, and none was performed.** Per the never-claim rule (`.clinerules` §3; gate A-13 of the QUE-006 plan), no audio may be described as produced.

## 9. Frontend announcement layer and the W2 presence audit — IMPLEMENTED / NOT PRESENT

### 9.1 What the frontend announcement layer is, here

```
frontend/lib/announcements/content.js           (modified)  sentence composition, honorific, numeric-only room speech
frontend/lib/announcements/controller.js        (modified)  facility switch, dedupe, overlap, activation, outcome
frontend/lib/announcements/dedupe.js            (new)       bounded per-event store, TTL / backoff / maxKeys
frontend/lib/announcements/speech-synthesis.js  (modified)  browser adapter, voice selection, "silence is not success"
frontend/components/queue/QueueAnnouncements.js (unchanged) panel; renders controller state only
frontend/pages/queue.js                         (modified)  one announcer per page, announce button for `called`
```

The controller's own header (lines 16–18) states the boundary of what was built:

> *Deliberately NOT here (separate requirements, see the implementation report): server-side queue events, facility configuration storage (OD-2), server-side announcement audit, and cross-client ordering.*

That sentence is the hinge of the whole reconciliation: **the four things the controller names as "not here" are exactly the class of thing an announcement-*reliability* implementation provides** — and none of them exists on this host: no table or column for it (§5.2, §5.3), no route for it (§6.1), no artefact for it (§9.2).

The controller's public surface is `{announce, activate, cancel, getState, subscribe, dispose}` plus a `logger` option (line 47: `(entry) => void|object`, invoked as `logger.info('queue.announcement', line)`). **There is no delivery-reporting callback, no `onDelivered`, no `report` hook** — the only outbound channel for the outcome of an attempt is a log line. A suppressed delivery is *"reported, never spoken and never silently swallowed"* (line 241) — but it is reported **to the console**, not to a server.

### 9.2 The W2 items — NOT PRESENT, individually proven

| W2 item | Expected location | This host | Evidence |
|---|---|---|---|
| `queuing/events.py` | queuing service module | **NOT PRESENT** | `ls backend/queuing/` = `Dockerfile`, `__init__.py`, `display.py`, `main.py`, `migrations`, `recovery.py`, `requirements.txt`, `tests` |
| `queuing/announcements.py` | queuing service module | **NOT PRESENT** | same listing; no `announcements.py` under `backend/queuing/` |
| `QueueAnnouncementDelivery` model | `backend/common/models.py` | **NOT PRESENT** | repo-wide symbol grep: **zero** project matches (only third-party `.venv313`) |
| `queue_announcement_deliveries` table | Alembic migration + live DB | **NOT PRESENT** | no migration matches `announce`/`delivery` (§4.3); `to_regclass` → NULL (§5.2) |
| `call_event_id` column | `queue_entries` or an event table | **NOT PRESENT** | `queue_entries` has 17 columns, none named `call_event_id` (§5.3); symbol grep: zero project matches |
| `current_call_event` | ORM property / payload field | **NOT PRESENT** | symbol grep: zero project matches |
| `call-announcer.js` | component | **NOT PRESENT** | filesystem sweep `*call-announcer*`: no hit |
| `queue-refresh.js` | lib | **NOT PRESENT** | filesystem sweep `*queue-refresh*`: no hit; `pages/queue.js` imports no refresh module |
| `queue-announcement-w2-integration.test.mjs` | test | **NOT PRESENT** | `frontend/tests/` holds 21 files; none matches `w2` |

**Method note.** Filesystem sweep patterns: `*call-announcer*`, `*queue-refresh*`, `*w2*`, `queuing/events.py`, `announcements.py`, run over the repository excluding `node_modules` and `.git`. The only `*w2*` hits were `.venv/lib/python3.14/site-packages/PIL/ImageDraw2.py` and its `.pyc` — a false positive on the substring `w2`. The symbol sweep (`QueueAnnouncementDelivery`, `queue_announcement_deliveries`, `call_event_id`, `current_call_event`, `call_event`) over `*.py`/`*.js`/`*.mjs`/`*.sql` returned **third-party hits only** (`crewai`, `grpc`, and a `crewai` platform-catalogue slug containing `call_event`) — **zero hits in AMSDP project code**.

**Verdict: W2 is NOT PRESENT on this host on all nine probes**, confirmed twice — once by filesystem/source sweep, once by live database catalog. W2 exists only in the Windows checkout.

### 9.3 Frontend announcement test inventory — PARTIALLY VERIFIED

| File | Test cases |
|---|---|
| `frontend/tests/queue-announcement-content.test.mjs` | 14 |
| `frontend/tests/queue-announcement-controller.test.mjs` | 21 |
| `frontend/tests/queue-announcement-dedupe.test.mjs` | 13 |
| `frontend/tests/queue-announcement-speech.test.mjs` | 19 |
| `frontend/tests/queue-announcements-boundary.test.mjs` | 6 |
| **Total announcement tests** | **73** |

Present, readable, **not executed** (`.clinerules` §9 — no test run without an explicit request; this task mandated read-only).

The six boundary tests are the ones that constrain a W2 merge most tightly, because they are *source-level* assertions about the page:

| Line | Test | Why it matters for W2 |
|---|---|---|
| 31 | *the queue page and the announcement panel compile as JSX* | A W2 rewrite of either file must still compile |
| 46 | *every caption the announcement boundary asks for is bilingual* | Bengali/English parity is pinned |
| 60 | *the queue page owns one announcer and renders the panel* | One controller per page — a W2 second poller must not mint a second announcer |
| 68 | *announcing is not a queue action* | **Direct conflict source** — see §11.1 |
| 80 | *the page announces the room the payload carries* | Pins `room: entry.room_name` and forbids the stale `entry.room` |
| 92 | *the panel defers browser state until after mount* | The panel never touches `speechSynthesis` directly |

## 10. Evidence ledger — every claim and the artefact behind it

| # | Claim | Label | Artefact |
|---|---|---|---|
| 1 | Branch `hackathon-mvp`, HEAD `cd2f9ec`, upstream `origin/hackathon-mvp` | **VERIFIED** | `git rev-parse`, `git log -1` output |
| 2 | 20 working-tree entries (13 M / 7 ??), 726 insertions / 154 deletions | **VERIFIED** | `git status --short -uall`, `git diff --stat` |
| 3 | 14 Alembic revisions, exactly one head `a9c4e1f7b2d8`, no dangling parent | **VERIFIED** | parsed graph (§4.1/§4.2) |
| 4 | No migration mentions announcement / call event / delivery | **VERIFIED** | grep over `backend/alembic/versions/*.py` → no matches |
| 5 | Live DB at `a9c4e1f7b2d8` (= local head) | **VERIFIED** | `SELECT version_num FROM alembic_version` |
| 6 | `queue_announcement_deliveries`, `queue_call_events` absent from the DB | **VERIFIED** | `to_regclass(...)` → NULL for both |
| 7 | `queue_entries` = 17 columns; no `call_event_id` | **VERIFIED** | `information_schema.columns` dump |
| 8 | `appointments.room_id` / `room_name` exist; `location_label` is not a column | **VERIFIED** | `information_schema.columns` dump |
| 9 | All 11 containers running/healthy | **VERIFIED** | `docker compose ps` |
| 10 | Queue service exposes 9 routes, none of them an announcement route | **IMPLEMENTED** | route decorators in `main.py`, `recovery.py`, `display.py` |
| 11 | Room contract: `room_payload`, `_rooms_for`, `_room_for_entry`, `_entry_to_dict` | **IMPLEMENTED** | source read at cited lines |
| 12 | `status_history` append + `queue.*` audit on transitions | **IMPLEMENTED** | `main.py` 286/397/473–477/493; `test_queue.py:284` |
| 13 | Frontend announcement layer + 73 test cases + 6 boundary assertions | **PARTIALLY VERIFIED** | files read; case counts by grep; **not executed** |
| 14 | 15 room-snapshot tests | **PARTIALLY VERIFIED** | test names by grep; **not executed** |
| 15 | W2's nine artefacts (files, model, table, columns, tests) | **NOT PRESENT** | filesystem sweep + symbol sweep + catalog query |
| 16 | Prior claims 73/73, 253/253, 15/15, 464 | **NOT VERIFIED** | quoted from the docs index row; no run in this session |
| 17 | Any produced/audible announcement | **NOT VERIFIED** | no browser/device playback performed here |
| 18 | W2 ↔ this tree compatibility | **BLOCKED** | W2 source is not on this host (§11.1) |

**Tally: 9 VERIFIED, 3 IMPLEMENTED, 2 PARTIALLY VERIFIED, 1 NOT PRESENT verdict (covering nine probes), 1 NOT VERIFIED prior-claim row, 1 BLOCKED.** No item is ACCEPTED.

## 11. Reconciliation: conflicts, and what a W2 merge must preserve

### 11.1 The reconciliation cannot be called "compatible" — and this is why

A compatibility statement requires both sides to be observable. On this host, **one side does not exist**: nine W2 artefacts are absent (§9.2), the two W2 tables are NULL in `to_regclass` (§5.2), and no W2 symbol appears in AMSDP project code. Therefore:

- **"W2 is compatible with the Ubuntu tree" — BLOCKED.** Not refuted; *unperformable*. Nothing was compared, so nothing can be cleared.
- **"The Ubuntu tree does not implement W2" — NOT PRESENT, proven.** That is the only defensible direction of the statement.
- Any future sentence of the form "the Windows work merges cleanly" must be accompanied by the two artefacts this report could not obtain: the W2 file list *with content*, and a run of both suites over the merged tree.

### 11.2 Anticipated conflicts, ranked by likelihood of breaking this tree

| # | Conflict | Where it bites | Why |
|---|---|---|---|
| **C-1** | W2 reports deliveries **from inside the announce action** | `frontend/tests/queue-announcements-boundary.test.mjs:68–78` asserts the `announceEntry` body contains **no `apiFetch`** and **no `queue/`** call — *"announcing must not call the API"* | This is deliberate: audio never writes queue state, so a browser that fails to speak cannot corrupt the queue. A W2 delivery claim POSTed from `announceEntry` **fails this test by construction**. It is a design decision, not a merge — either the claim moves to a separate reporting path (and the boundary test is amended with the owner's reasoning), or W2 does not report from the click path. **Highest-risk conflict; escalate, never silently resolve.** |
| **C-2** | W2 adds a server-side **event feed** with its own router | `backend/queuing/main.py:28–43` dual-import registration (§6.2) | A module registered with a single import style breaks either package imports or the flat container import |
| **C-3** | W2 adds `call_event_id` / `current_call_event` **to the queue payload** | `_entry_to_dict` (83–111), asserted field-by-field by `test_entry_dict_without_a_room_keeps_four_empty_room_fields` | New payload fields must be additive and defaulted for old rows; a required field breaks walk-ins and every existing caller |
| **C-4** | W2 resolves the room **per entry**, or from `schedule_sessions` | `test_a_page_of_entries_costs_one_appointments_query` (318), `test_each_entry_on_one_page_keeps_its_own_room` (302) | One query per page is a pinned guarantee; `schedule_sessions` is the doctor's *current* chamber, which F4 forbids as an announcement source |
| **C-5** | W2's room resolution joins across tenants | `_rooms_for`'s `organization_id.in_(...)` filter (125–128); `test_queue_page_never_leaks_another_branch` (352) | A new join that drops the org filter is a tenancy defect (`.clinerules` §3) |
| **C-6** | W2 mints its **own refresh loop / second announcer** | boundary test line 60 (*the queue page owns one announcer*); `dedupe.js` per-event store | Two announcers ⇒ two voices, or one consuming the other's key space; dedupe memory is per-controller |
| **C-7** | W2 stores announcement state **client-side only** and calls it "reliable" | `.clinerules` §3 (append-only, persistent audit); `controller.js:16–18` (OD-3 named as not built) | An announcement that leaves no server record cannot be audited; "reliable" would then be a claim without evidence |
| **C-8** | W2 renames or reorders the announcement **outcome vocabulary** | `content.js` / `speech-synthesis.js` / `controller.js` (six terminal outcomes; only `end` proves delivery) | The "silence is not success" rule depends on that vocabulary; renaming a state silently changes what the UI reports |
| **C-9** | W2 turns the **facility switch** into a server-side setting | `controller.js:16–18` (OD-2 explicitly not built) | Today the switch is client-local; a server setting needs a table, a route, RBAC, and an audit event — none of which exist (§5.2) |

### 11.3 Preservation contract — the exact surfaces a W2 merge must not degrade

Each entry is a named symbol or an asserted behaviour, so a reviewer can check it mechanically.

**Backend**

| Must preserve | Location | Contract |
|---|---|---|
| `room_payload(snapshot, source=...)` | `common/locations.py:47` | Returns `room_id`, `room_name`, `label`, `source`; `source` is `""` when there is no room name |
| `location_label(snapshot)` | `common/locations.py:30` | `floor / department / room` joined by `" / "`, missing parts omitted |
| `NO_ROOM`, `ROOM_SOURCE_APPOINTMENT`, `ROOM_SOURCE_WALK_IN` | `common/locations.py:21,23,27` | The empty answer and the two source constants |
| `_entry_to_dict(e, room=None)` | `queuing/main.py:83` | Four additive room fields, empty-string defaults, **no** per-row lookup inside |
| `_rooms_for(session, entries)` | `queuing/main.py:114` | One org-filtered `appointments` query per page |
| `_room_for_entry(session, entry)` | `queuing/main.py:132` | One query, filtered by `id` **and** `organization_id` |
| `status_history` creation on check-in / enqueue | `queuing/main.py:286,397` | `[{from:"",to:"waiting",actor,at}]` |
| `status_history` append on every transition | `queuing/main.py:473–477` | Append-only array; the `called` transition is timestamped here |
| `queue.{action}` audit on every action | `queuing/main.py:305,312,401,493,569` | Append-only audit row per queue operation |
| Denial auditing wiring | `queuing/main.py:29` (`install_denial_audit(app,"queuing")`) | Every 403/404/422 is audited; a new router must share this `app` |
| Dual-import router registration | `queuing/main.py:28–43` | `try: from .x import ... except ImportError: from x import ...` |
| `recovery._entry_payload` | `queuing/recovery.py:69` | Single payload builder for both recovery endpoints; must report the same room |
| Forward-only, idempotent migration discipline | `.clinerules` §3; chain §4 | Any W2 table/column arrives as a new revision whose `down_revision` is `a9c4e1f7b2d8` |

**Frontend**

| Must preserve | Location | Contract |
|---|---|---|
| One announcer per page | `pages/queue.js` (`useQueueAnnouncements`); boundary test 60 | A single controller instance owns the page |
| `room: entry.room_name` in the announce payload | `pages/queue.js` (`announceEntry`); boundary test 80 | Room comes from the appointment snapshot, never `entry.room` |
| `source: 'operator'` + `userGesture: true` for a manual repeat | `pages/queue.js`; boundary test 68 | A click is operator intent and may recover blocked audio |
| **No API write from the announce click path** | `pages/queue.js`; boundary test 68 | See **C-1** — the conflict to escalate |
| Bilingual captions | boundary test 46 | Every boundary caption exists in Bengali and English |
| Controller surface `{announce, activate, cancel, getState, subscribe, dispose, logger}` | `lib/announcements/controller.js:334–343` | New capability must not rename these |
| Outcome vocabulary — only `end` proves delivery | `lib/announcements/speech-synthesis.js`, `controller.js` | Any W2 reliability metric must be defined in these terms |
| Dedupe store semantics (TTL / backoff / `maxKeys`; `busy` / `unavailable` release) | `lib/announcements/dedupe.js` | Per-event memory with a bounded key space |
| Panel never touches `speechSynthesis` directly | `components/queue/QueueAnnouncements.js`; boundary test 92 | All engine access stays behind the adapter |

## 12. Governance and skill compliance, limitations, and open items

### 12.1 Governance compliance — `.clinerules` §6 report

| Requirement | How this task complied |
|---|---|
| §2 routing (read the index first, load the domain documents) | `docs/governance/AMSDP_Docs_Index_V1.0.md` was read first; it routed to the QUE-006 plan, the OD-1 report, the F1–F4 report, the Business Rules, and the deployment runbook, which were then read and cited |
| §4 domain rows applied | *Multi-tenant data* (org filter in `_rooms_for`, branch-isolation test), *database schema/migrations* (Alembic chain, live revision), *backend API* (route inventory, registration pattern), *frontend UI* (announcement layer, boundary tests), *audit/data integrity* (`status_history`, `queue.*` audit, denial audit), *Docker/deployment* (container state, how migrations are applied) |
| §5 skills | **No skill package is installed in this workspace** (verified: no `.clinerules/skills/`, no repo `skills/`). Governance documents were used instead, as the registry requires. **No skill was used and none is claimed.** |
| §3 non-negotiables | No secret entered this report (DB access used the container's own env vars; nothing quoted). No source, migration, DB row, or Git history was mutated. No capability was claimed that was not observed (§0, §10). Denial-audit and tenant-filter behaviour was read and reported, not altered |
| §7 evidence standard | Every row of §10 carries a label; VERIFIED is used only where a live command output exists |
| §9 execution boundaries | No server started, no suite run, no destructive Git command — only `git status` / `git diff` / `git log` / `git rev-parse` |
| §11 output location | Written to `docs/implementation/` — the subject folder for an implementation reconciliation record; no new folder created; **destination collision checked before writing: no file of this name existed** (the folder held three other QUE-006 documents, none matching) |
| §12 reading discipline | Documents were located by pattern and cited by the path actually opened in this session; no remembered path was relied on |

### 12.2 Read-only guarantee — post-inspection re-check

`git status --short -uall` was re-run after all probes and compared line-by-line against the pre-inspection capture (`status_final.txt`, SHA-256 `f19acb4535fa52be07a48818145d0fb3c95ddd26e84ad7cc55888e1e0cea8976`). The difference is **one added line only**:

```
?? docs/implementation/QUE-006_UBUNTU_REPOSITORY_RECONCILIATION_EVIDENCE_REPORT.md
```

Everything else is byte-identical — the same 13 modified files, the same 7 pre-existing untracked files, and `git diff --stat` still reporting 13 files / 726 insertions / 154 deletions. **The creation of this report is the only attributable change made by this task.**

### 12.3 Limitations of this report

1. **No test execution.** Every test statement is presence-level. A green suite is not claimed — and would not by itself have made anything VERIFIED (§7 evidence standard).
2. **No browser or device playback.** Nothing here proves an announcement is audible; gate A-13 remains open.
3. **W2 unobservable.** Compatibility is BLOCKED, not satisfied (§11.1).
4. **Database on this host only.** The live reads describe the `db` container on this Ubuntu machine. The Windows host's database was not inspected and may differ.
5. **Migration *execution path* not exercised.** How the DB reached `a9c4e1f7b2d8` was not replayed; only the resulting state was read.
6. **Docs index not updated (§12 obligation deferred, deliberately).** `.clinerules` §12 requires an index entry for a newly created document in the same task. It was **not** applied here because (a) this task's mandate was strictly read-only outside the report itself, and (b) `docs/governance/AMSDP_Docs_Index_V1.0.md` already carries uncommitted in-flight edits from the QUE-006 work (§3.1) — editing it would interleave this report's registration with someone else's uncommitted changes. **Owner action requested:** register this file as the next index revision when the QUE-006 working tree is committed.

### 12.4 Open items

| ID | Item | Owner |
|---|---|---|
| **O-R1** | W2 source is absent here; supply the W2 file list (or the checkout) before any compatibility claim | Project owner |
| **O-R2** | **C-1**: does a delivery claim belong inside the announce click path? The boundary test forbids it today | Project owner |
| **O-R3** | Register this report in `docs/governance/AMSDP_Docs_Index_V1.0.md` (§12.3 limitation 6) | Project owner / next doc revision |
| **O-R4** | `backend/queuing/migrations/001_create_queue_entries.sql` is a pre-Alembic artefact contradicting the live schema (§4.4). Retire it or annotate it as historical | Project owner |
| **O-R5** | No container or entrypoint applies migrations; schema correctness depends on someone running `alembic upgrade head` by hand (§4.5) | Platform |
| **O-R6** | Nothing on this host records *whether* a call was announced — no table, no column, no route, no frontend reporter. The W2 problem statement is real here and unmet | Project owner |

---

**End of report.** No claim in this document is ACCEPTED, and none may be cited as verified behaviour of a running announcement feature: the only VERIFIED items are repository identity, working-tree state, migration-graph shape, live schema/catalog state, and container state.

