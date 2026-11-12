# AMSDP — Sequence 3 Completion Report: Missed-Turn Recovery + Notification Outbox

**Sequence:** 3 — BR §27A missed-turn recovery, notification outbox (WhatsApp/SMS), org notification settings
**Work package:** `AMSDP-SEQ-03-WP1-QUEUE-RECOVERY-NOTIFICATION-AUDIT-2026-11-09`
**Date:** 2026-11-09
**Tree:** `/home/shomonrobie/amsdp`, branch `hackathon-mvp`, base commit `eb87cac`
**Status:** **IMPLEMENTED + TESTED** for every work package. Backend behaviour is
**VERIFIED** by live database inspection and passing suites; the two UI screens
are **build-verified only** (no browser run — see §9). Acceptance is a separate
product-owner act and is **not** claimed. No commit, no push, no merge, no
deploy was performed in this sequence.

---

## 1. Scope and objective

Sequence 3 was authorised by `AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md`
(WP1–WP8). It delivered two features and their regression surface:

1. **WP2** — staff-confirmed missed turn on a queue entry (token and appointment
   preserved, entry becomes `skipped`).
2. **WP3** — recovery of a `skipped` entry: default re-entry at the end of the
   same doctor/day queue, optional position override, both audited, both scoped
   to the caller's org + branch.
3. **WP4** — provider-neutral notification boundary (mock adapter only; a real
   provider is a product-owner decision) and a persistent outbox with dedupe,
   cooldown, retry/backoff and a `sent` ≠ `delivered` distinction.
4. **WP5** — lifecycle hooks: booking → confirmation + planned reminder; queue
   change → reminder replan; appointment closed / queue closed → cancellation.
   All hooks are best-effort and can never fail a business operation.
5. **WP6** — org-level notification settings API + staff page (channels off by
   default, server-side provider allow-list, no secret ever returned).
6. **WP7** — focused tests plus regression runs of the earlier suites.
7. **WP8** — this report.

Explicitly out of scope (per the assessment's §6): real WhatsApp/SMS
integration, template approval, cost/metering, patient-facing notification
preferences, retry tuning per provider, deployment changes, commits.

## 2. Governance and skill compliance

Selected per `.clinerules` §4 routing table:

| Domain | Governance documents applied | Skill |
|---|---|---|
| Backend API / service endpoints | `saas-application-security.md` (adapted), Business Rules Parts II–X | none installed |
| Auth / RBAC | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8, `backend/common/permissions.py` | none installed |
| Multi-tenant isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–6, `common/auth.py` scope helpers | none installed |
| DB schema / migrations | `saas-multitenant-data.md` §4–5, `saas-cicd-workflow.md` §3 (adapted), Alembic chain | none installed |
| Queue / workflow transitions | Business Rules **V1.1** §27A + Parts V–VII, M5 Queue Implementation Report | none installed |
| Audit / integrity | `saas-observability.md` (adapted — redaction, denial recording), `common/audit.py`, Part X | none installed |
| Frontend UI | `saas-frontend-ux.md` (adapted), AMSDP UI/UX assessment, `frontend/components/`, `frontend/lib/i18n.js` | none installed |
| LLM / agent tooling | §8 routing policy (not exercised — no model call was made) | none installed |

**Skills: NONE available.** Re-checked in this session: no `.clinerules/skills/`,
no `.claude/skills/`, no repo `skills/` directory. The governance documents
above were used instead; **no skill usage is claimed**.

Non-negotiables actually exercised:

- **Cross-tenant / cross-branch fails closed with 404, never 403** — both new
  queue routes resolve the entry through `_scoped_entry()` and return
  `404 queue entry not found`; asserted by test 7 on both routes.
- **Tenant key is `organization_id`** — the outbox carries
  `organization_id` (FK to `organizations.id`); `branch_id` is a nullable
  location attribute, not a tenant column.
- **Server-side authorisation, never the UI** — `queue.recover` and
  `queue.reposition` are enforced with `require_permission(...)` in
  `queuing/recovery.py`; the page's `can()` mirror is defence in depth only.
- **Denials are recorded, not swallowed** — every applied state change writes an
  append-only audit event (`queue.missed_turn`, `queue.recover`, and one
  `queue.reposition` per shifted row). **Exception:** the pure refusal returns
  on the two new recovery routes (403 / 404 / 422) do not yet write a denial
  record — see §10.3, where it is logged as an open gap rather than claimed as
  done.
- **Secrets never exposed** — the config view returns booleans only
  (`credentials_configured`, `usable`); provider credentials are read from the
  environment in one place and are never logged, echoed or stored.
- **Forward-only, idempotent migration** — `b7c1e4d90a52_add_notifications.py`
  inspects `pg_tables`/`pg_indexes` and no-ops on re-run; chain head verified
  live (see §8.1).
- **No invented evidence** — every number in §8 is copied from a command run in
  this tree during this session.


## 2A. Business Rules §27A — clause-by-clause compliance

Authoritative source: `docs/AMSDP_Business_Rules_V1.1.md` §27A (approved for
MVP, 9 November 2026). `docs/product/AMSDP_Business_Rules_V1.0.md` remains the
historical record and does not contain §27A.

| §27A clause | Satisfied by | Evidence |
|---|---|---|
| 1. Staff-confirmed event only | Both routes are staff-invoked POSTs. No timer, cron, tracking signal or message status can produce `skipped`. | tests 1–3; no caller of `mark_missed_turn` other than the route |
| 2. Default = end of same applicable queue | `_active_queue()` is scoped to `organization_id` + `doctor_id` + `date`; default index is `len(others)` | test 4 |
| 3. Authorized position override, any valid position | `target_position` 1..len(active)+1, reason required | test 6 |
| 4. Permission enforcement in backend | `require_permission("queue.recover")` on both routes; `queue.reposition` checked explicitly for an override → 403 | tests 8, 9; `permissions.py` matrix |
| 5. Appointment and token preservation | Entry id, `token`, `appointment_id`, `patient_id`, `entry_source` untouched; only `status`/`position` change, with `status_history` + `position_history` appended | test 1, 4; response flags `token_preserved`/`appointment_preserved` |
| 6. Audit record incl. old/new position and reason | `queue.missed_turn` (before/after status + position) and `queue.recover` (`mode`, before/after position, reason, `repositioned_others`) | `recovery.py` lines 160–168, 246–256 |
| 7. No automatic no-show | Recovery never writes `no_show`; `no_show` remains a separate staff action | status transitions in `recovery.py` |
| 8. No silent appointment change | Neither route touches appointment date/time/doctor/branch; the hook only re-arms a reminder | `recovery.py` (no `Appointment` import) |
| 9. Human-controlled safety | No urgency, triage or leave-permission logic exists in the feature | none implemented, by design |
| 10. Notification independence | `_notify()` swallows all exceptions; no notification state is read before a state change | test 10 |
| 11. Same-queue boundary | Cross-org and cross-branch entries return 404 (`_scoped_entry`); cross-doctor/cross-date is unreachable because the queue is resolved from the entry's own doctor+date | test 7 |

Known modelling note: the applicable queue in this build is *doctor + date*
(plus branch scope). Room-level queues are not modelled yet, so "same
doctor/room" resolves to "same doctor" today.

## 3. What was delivered (WP → artefact → test)

| WP | Delivered | Files | Tests |
|---|---|---|---|
| WP1 | Audit + plan (requirement classification, reuse decisions, non-goals) | `AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md` | — |
| WP2 | Missed turn: `waiting`/`called` → `skipped`, token + appointment preserved, `status_history` entry, audit `queue.missed_turn` | `backend/queuing/recovery.py` | 1–3 |
| WP3 | Recovery: `skipped` → `waiting`, end-of-queue default, position override (`queue.reposition` + reason), renumbering of the doctor/day queue with `queue.reposition` audit per shifted row | `backend/queuing/recovery.py`, `frontend/pages/queue.js` | 4–10 |
| WP4 | Provider boundary + persistent outbox (dedupe, cooldown, retry/backoff, `sent` vs `delivered`) | `backend/common/notifications/{providers,outbox,config}.py` | 11, 16, 17, 19, 26 |
| WP5 | Lifecycle hooks: booked → confirmation + planned reminder; queue change → replan; appointment cancelled/queue closed → cancel. Best-effort, never fatal. | `backend/common/notifications/hooks.py`, wiring in `appointment/main.py`, `queuing/main.py`, `queuing/recovery.py` | 12–15, 18, 20 |
| WP6 | Org notification settings API + status API + staff page | `backend/organization/notification_config.py`, `frontend/pages/notifications.js` | 21–25 |
| WP7 | Focused tests + regression runs | `backend/tests/test_sequence3.py` | all |
| WP8 | This report | `AMSDP_SEQ_03_COMPLETION_REPORT.md` | — |

Schema: one forward-only migration, `b7c1e4d90a52_add_notifications.py`
(`a1f2b3c4d5e6` → `b7c1e4d90a52`), creating the `notifications` outbox table
with four indexes (`uq_notification_dedup_key`, `idx_notif_org_status`,
`idx_notif_due`, `idx_notif_appointment`) and four FKs
(`organizations`, `branches`, `appointments`, `patients`), using
`pg_tables`/`pg_indexes` guards so a re-run is a no-op.

## 4. API contract added in this sequence

| Method | Path | Permission | Behaviour |
|---|---|---|---|
| POST | `/api/v1/queue/{entry_id}/missed-turn` | `queue.recover` | `waiting`/`called` → `skipped`; 422 if already skipped or not missable; 404 if out of scope. Body `{reason?, actor?}` |
| POST | `/api/v1/queue/{entry_id}/recover` | `queue.recover` | `skipped` → `waiting`; default end of queue; `target_position` requires `queue.reposition` (403 otherwise) and a non-empty reason (422); `target_position` bounded to `1..len(active)+1` (422); 422 if the entry is not `skipped`; 404 if out of scope |
| GET | `/api/v1/orgs/{org_id}/notification-config` | `org.read` | `public_view()` — channels, provider names, `usable`, `credentials_configured`, lead minutes, cooldown, platform capability |
| PUT | `/api/v1/orgs/{org_id}/notification-config` | `org.manage` | Validates lead minutes against `ALLOWED_LEAD_MINUTES` and provider against the platform allow-list ∩ implemented adapters; 422 with explicit messages otherwise |
| GET | `/api/v1/orgs/{org_id}/notification-status` | `org.read` | `channels`, `platform` (`describe_platform()`), `last_24h` + `lifetime` counters per status, `latest_message` with `sent`/`delivered` kept separate |

Both queue routes respond with the queue service's own entry shape (imported
from `queuing/main.py`, single source of truth) plus a `recovery` block stating
`token_preserved` / `appointment_preserved`.

Permission note: the settings page is gated in the UI on `org.manage`, which is
stricter than the server for the read-only `notification-status` route
(`org.read`). The server remains the boundary in both directions.


## 5. Notification design rules as implemented

- **Off by default.** `_channel_config` derives `enabled=False` unless the
  organization's `notification_config` turns the channel on; `status` reports
  `disabled` / `awaiting_setup` / `unavailable` / `configured`.
- **Provider-neutral seam.** Only `mock` has an adapter in this build
  (`_ADAPTERS`). `AMSDP_NOTIFICATION_PROVIDERS` is a platform allow-list;
  declaring a name there does not implement it, and `get_provider()` refuses a
  provider that is undeclared *or* unadapted.
- **`sent` ≠ `delivered`.** The mock adapter returns `delivered=False` because
  no handset was involved; the API and the staff page separate the two, so no
  dashboard can imply delivery that never happened.
- **Dedupe.** `dedup_key(notification_type, appointment_id, channel)` is
  enforced by a unique constraint; `enqueue_or_rearm` re-arms the existing row
  instead of creating a second one, so repeated booking hooks and queue changes
  keep one message and one history.
- **Cooldown.** `COOLDOWN_MINUTES` (default 2) is the minimum gap between two
  messages for the same appointment + channel.
- **Retry/backoff.** `_BACKOFF_SECONDS = (30, 120, 300)` with `attempt_count` /
  `max_attempts`; a row ends in `failed` (not `retry_scheduled`) once attempts
  are exhausted.
- **Transactional safety.** Hooks swallow every exception
  (`logger.warning("notification hook %s failed")`) and open their own session
  via `SessionFactory()`, so no notification fault can fail or roll back a
  booking, a check-in or a recovery. Test 10
  (`test_recovery_survives_notification_failure`) proves this by patching the
  hook to raise.
- **Worker.** `python3 -m common.notifications.worker --interval 30 --limit 50`
  polls `due_rows()` (row-locked), calls `process_due()` and owns the commit.
  `run_once()` is the test-safe entry point.
- **No secrets, no PII in logs.** Recipient numbers and bodies are never logged
  by the adapters; the config view returns booleans only.

## 6. Frontend surfaces

`frontend/pages/queue.js`
- Row actions appear from the permission mirror (`can()`), never from data
  shape: **Missed turn** on `waiting`/`called`, **Recover** on `skipped`.
- Missed turn uses the shared `ConfirmDialog`; recovery uses the shared `Modal`
  with re-entry point (`end_of_queue` default, `position_override` only when
  `queue.reposition` is held), a position select and a reason field that is
  required for an override (client-side courtesy; the server enforces it).
- Success is reported through `SuccessAlert`; failures through `ErrorAlert`
  with the server's `detail`.
- A single `busy` flag disables the action buttons while a request is in
  flight, so a double click cannot submit twice.
- `skipped` rows are labelled *awaiting recovery* so staff can see that this
  patient is waiting to be brought back.

`frontend/pages/notifications.js` (new; nav entry gated by `org.manage`)
- Channel table: enable toggle, provider select limited to the server's
  implemented allow-list, status badge, masked `••••` marker when
  `credentials_configured` is true (the value itself is never rendered).
- Reminder timing select built from `allowed_lead_minutes` (5 / 10), cooldown
  and last update shown read-only.
- Status panel: `mock-only` integration warning, per-status counts for the last
  24 h and lifetime, latest message with `sent`/`delivered` shown separately.
- `PermissionDenied` for non-`org.manage` roles; the API enforces it too.

`frontend/lib/auth.js` now mirrors the backend matrix for `queue.recover` and
`queue.reposition` (receptionist + doctor), and `frontend/lib/i18n.js` gained
the bn/en keys used by both pages. `frontend/components/AppShell.js` gained the
`/notifications` nav entry, gated by `org.manage`.

## 7. Test inventory — `backend/tests/test_sequence3.py`

26 test functions, 29 collected items (one is parametrized ×4).

**Missed turn (WP2)**
1. `test_missed_turn_marks_skipped_and_preserves_identity` — status, token,
   appointment, patient and entry id all survive.
2. `test_missed_turn_is_idempotent_only_once` — second call is 422
   `already recorded`, no second state change.
3. `test_missed_turn_rejects_non_waiting_states` ×4 — `in_consultation`,
   `completed`, `cancelled`, `no_show` → 422.

**Recovery (WP3)**
4. `test_recover_renumbers_queue_and_keeps_token` — default end-of-queue,
   positions contiguous, token preserved.
5. `test_recover_rejects_non_skipped_entry` — 422 when not `skipped`.
6. `test_recover_override_requires_reason_and_repositions` — override without a
   reason is 422; with a reason the position is honoured and the others shift.
7. `test_recovery_cross_branch_and_cross_org_are_404` — both routes, foreign
   org and foreign branch, 404 with no state change (extended in this session).
8. `test_assistant_cannot_recover_or_confirm_missed_turn` — 403 for a role
   without `queue.recover`.
9. `test_doctor_may_confirm_and_recover_within_their_queue` — own queue only.
10. `test_recovery_survives_notification_failure` — a raising hook cannot fail
    the recovery.

**Outbox + hooks (WP4/WP5)**
11. `test_notification_config_defaults_to_everything_disabled`
12. `test_booking_creates_confirmation_and_planned_reminder`
13. `test_no_messages_when_org_has_not_enabled_a_channel`
14. `test_walk_in_booking_creates_no_message`
15. `test_appointment_starting_now_gets_no_reminder` — no reminder in the past.
16. `test_repeated_booking_hook_does_not_duplicate_rows` — dedupe/re-arm.
17. `test_worker_marks_sent_but_never_delivered` — mock is `sent`, not
    `delivered`.
18. `test_cancelling_appointment_cancels_unsettled_messages`
19. `test_provider_failure_retries_then_fails` — backoff, then terminal
    `failed` at `max_attempts`.
20. `test_queue_change_replans_pending_reminder`

**Org settings API (WP6)**
21. `test_org_admin_reads_and_updates_notification_config`
22. `test_notification_config_rejects_unapproved_provider_and_lead` — 422 with
    explicit messages.
23. `test_branch_admin_cannot_read_notification_config` — 403.
24. `test_cross_org_notification_config_is_non_disclosing_404`
25. `test_notification_status_separates_sent_from_delivered`
26. `test_unusable_provider_config_sends_nothing`

The suite runs against the configured Postgres. It creates dedicated fixture
organizations/branches/patients/appointments/entries with unique ids (prefix
`SQ3`/`T-*`), and its `_reset` helper deletes the notification, queue-entry,
tracking-token, appointment and patient rows it created before each test, so
re-runs are repeatable. Earlier suites were run sequentially (never in
parallel) to avoid cross-talk.

## 8. Verification evidence (run in this tree, this session)

### 8.1 Database (live, `docker compose exec -T db psql -U amsdp -d amsdp`)
```
$ ... -c "select column_name, data_type, is_nullable from information_schema.columns
          where table_name='notifications' order by ordinal_position"
      column_name     |        data_type         | is_nullable
----------------------+--------------------------+-------------
 id                   | character varying        | NO
 organization_id      | character varying        | NO
 branch_id            | character varying        | YES
 appointment_id       | character varying        | YES
 queue_entry_id       | character varying        | YES
 patient_id           | character varying        | YES
 notification_type    | character varying        | NO
 channel              | character varying        | NO
 recipient_mobile     | character varying        | NO
 payload              | json                     | YES
 dedup_key            | character varying        | NO
 status               | character varying        | NO
 attempt_count        | integer                  | NO
 max_attempts         | integer                  | NO
 scheduled_at         | timestamp with time zone | NO
 next_attempt_at      | timestamp with time zone | YES
 last_attempt_at      | timestamp with time zone | YES
 sent_at              | timestamp with time zone | YES
 delivered_at         | timestamp with time zone | YES
 provider             | character varying        | YES
 provider_message_id  | character varying        | YES
 error                | character varying        | YES
 cancel_reason        | character varying        | YES
 cancelled_at         | timestamp with time zone | YES
 created_at           | timestamp with time zone | YES
 updated_at           | timestamp with time zone | YES
(26 rows)

$ ... -c "select indexname from pg_indexes where tablename='notifications'"
 notifications_pkey, uq_notification_dedup_key,
 idx_notif_org_status, idx_notif_due, idx_notif_appointment

$ ... -c "select conname, confrelid::regclass from pg_constraint
          where conrelid='notifications'::regclass and contype='f'"
 notifications_organization_id_fkey -> organizations
 notifications_branch_id_fkey       -> branches
 notifications_appointment_id_fkey  -> appointments
 notifications_patient_id_fkey      -> patients

$ ... -c "select version_num from alembic_version"
 b7c1e4d90a52
```
`queue_entry_id` carries no FK constraint (observed above); the FK-protected
links are `organizations`, `branches`, `appointments` and `patients`. `error`
and `cancel_reason` are short strings.

### 8.2 Backend tests
```
$ cd backend && ../.venv/bin/python -m pytest tests/test_sequence3.py -q \
      -p no:cacheprovider
29 passed, 9 warnings in 11.10s
EXIT=0
```
(Three separate runs in this session: `29 passed` each time — no order- or
data-dependence observed.) The only new warning attributable to this sequence is
a `PydanticDeprecatedSince20` on `notification_config.py:89` (`.dict()` where
`model_dump()` is expected); it is cosmetic and recorded as follow-up §10.9.

### 8.3 Regression (earlier sequences + security)
```
$ cd backend && ../.venv/bin/python -m pytest \
    tests/test_security.py tests/test_dqds.py tests/test_dashboard.py \
    tests/test_patient_age.py tests/test_tracking_tokens.py -q
81 passed, 19 warnings in 13.42s
EXIT=0
```
Only pre-existing deprecation warnings (Starlette `on_event`, Pydantic `.dict()`,
short HMAC test key) — none introduced by this sequence.

### 8.4 Frontend
```
$ cd frontend && npm run build
 ✓ Compiled successfully
 Route (pages)                     Size     First Load JS
 ├ ● /notifications                2.23 kB          92.5 kB
 ├ ● /queue                        3.59 kB          93.9 kB
 ...
BUILD_EXIT=0
```
No lint errors, no missing i18n keys, no unresolved imports.

### 8.5 Python syntax
```
$ ../.venv/bin/python -m py_compile queuing/recovery.py \
    organization/notification_config.py common/notifications/*.py
PY_OK
```

## 9. Evidence standard applied (per `.clinerules` §7)

| Capability | IMPLEMENTED | TESTED | VERIFIED | ACCEPTED |
|---|---|---|---|---|
| Missed-turn endpoint + audit | yes | yes (tests 1–3) | yes — 422/404 paths re-read in source; live table read for outbox | no |
| Recovery endpoint (default + override) | yes | yes (tests 4–10) | yes — server-side reason/permission gating read in `recovery.py` | no |
| Outbox schema `b7c1e4d90a52` | yes | yes (implicitly, across tests 11–20) | yes — live `information_schema` / `pg_indexes` / `pg_constraint` / `alembic_version` reads | no |
| Provider boundary (mock only) | yes | yes (tests 17, 19, 26) | yes — `sent` vs `delivered` asserted, not assumed | no |
| Lifecycle hooks non-fatal | yes | yes (tests 10, 12–15, 18, 20) | yes — `try/except` around `_notify` read in `queuing`/`appointment` callers | no |
| Org notification settings API | yes | yes (tests 21–25) | yes — permission and 404 paths asserted | no |
| Queue page missed-turn + recovery UI | yes | build only | **not independently verified** — no browser session was run in this tree | no |
| Notifications settings page | yes | build only | **not independently verified** — same reason | no |
| Regression of earlier sequences | yes | yes — 81 passed | yes — exit 0 recorded | no |

The two UI rows are the honest gap: `npm run build` proves the code compiles and
routes resolve, not that the screens behave. Browser confirmation (or a
Playwright/E2E harness, which this repo does not yet have) is required before
those rows can move to VERIFIED.

## 10. Deviations, limitations and follow-ups

1. **No live WhatsApp/SMS provider (by design).** Only `mock` is implemented;
   no message leaves the building. Selecting `twilio`/`whatsapp_cloud` is
   rejected (422) unless the platform allow-list *and* an adapter exist.
   Real integration, template approval and cost/metering are a product-owner
   decision for a later sequence.
2. **Worker not wired into deployment.** `common.notifications.worker` runs as
   a separate process and is not a service in `docker-compose.yml`, so nothing
   drains the outbox in a running stack unless it is started explicitly
   (`python3 -m common.notifications.worker --interval 30`). Tests exercise
   `run_once()`. Adding it as a compose service belongs to the deployment
   sequence; it was deliberately not added here to avoid changing the runtime
   topology without authorisation.
3. **Refusals are not audited anywhere yet (platform-wide gap).** State changes
   and every repositioned row are audited (`queue.missed_turn`,
   `queue.recover`, `queue.reposition`), but the 403 (missing
   `queue.reposition`), 404 (out of scope) and 422 (invalid transition) returns
   in `queuing/recovery.py` write no audit row. A grep for a denial-audit helper
   in `common/audit.py` and `common/auth.py` finds none (`common/auth.py` raises
   `403 cross-organization/cross-branch access denied` without recording it), so
   this is **not** specific to Sequence 3 — no service in this tree records
   refusals today. It is a deviation from the "denials are recorded" rule and
   is recorded as a known gap: a non-disclosing refusal record keyed to the
   principal would satisfy both the 404 rule and the audit rule, but the audit
   schema's contract for refusals needs a project-owner decision first.
4. **Doctors hold `queue.recover` / `queue.reposition` — new permissions, pending
   product-owner confirmation.** §27A.1 and §27A.3 require an "authorized staff
   member or authorized doctor", and §27A.4 requires an explicit permission for
   confirmation *and* for repositioning, so both were added to
   `receptionist` and to `doctor` in `common/permissions.py` (admin roles inherit
   them through `queue.*`). Doctors keep their scope to their own branch and
   are still denied `queue.manage` (cancel / no-show) and `queue.reorder`. This
   is additive and widens no existing permission, but BR §8's matrix is marked
   FINALIZED, so the assessment flagged it for **product-owner confirmation in
   Sequence 4** — still open.
5. **Client-side position bounds are advisory.** The select is sized from the
   branch-filtered list the UI has; the authoritative bound is the server's
   `1..len(active)+1`. An out-of-range pick returns 422 and the page surfaces
   the server's message rather than guessing.
6. **Cooldown vs. clinical urgency.** The 2-minute cooldown is a spam guard, not
   a clinical rule; a "patient is here now" message can therefore be delayed by
   up to the cooldown window. Acceptable for MVP, flagged for the
   notification-tuning follow-up.
7. **No UI end-to-end run.** As stated in §9: build-verified, not
   browser-verified.
8. **Test isolation is by fixture, not by transaction.** The suite talks to the
   same Postgres as the running stack and cleans up via `_reset`; it must not be
   run concurrently with another suite or against a production database.
9. **Cosmetic deprecation.** `organization/notification_config.py:89` uses
   Pydantic v1's `.dict()`; switch to `model_dump()` in a cleanup pass (no
   behavioural impact, flagged by the suite's warning summary).


## 11. Handoff — files this sequence added or changed

New:
- `backend/common/notifications/__init__.py`, `config.py`, `providers.py`,
  `outbox.py`, `worker.py`, `hooks.py`
- `backend/common/notifications` migration:
  `backend/alembic/versions/b7c1e4d90a52_add_notifications.py`
- `backend/queuing/recovery.py`
- `backend/organization/notification_config.py`
- `backend/tests/test_sequence3.py`
- `frontend/pages/notifications.js`
- `ai_factory/docs/AMSDP_SEQ_03_IMPLEMENTATION_ASSESSMENT.md`,
  `ai_factory/docs/AMSDP_SEQ_03_COMPLETION_REPORT.md`

Modified:
- `backend/common/models.py` (Notification model), `backend/common/permissions.py`
  (`queue.recover`, `queue.reposition`)
- `backend/appointment/main.py`, `backend/queuing/main.py` (hook wiring)
- `frontend/lib/auth.js`, `frontend/lib/i18n.js`,
  `frontend/components/AppShell.js`, `frontend/pages/queue.js`

Git-tracking caveat: `backend/common/`, `backend/alembic/`, `frontend/lib/` and
`frontend/components/` are **untracked in this tree** (they were introduced in
earlier sequences and never committed), so `git status` reports them as whole
directories (`?? backend/common/`, `?? frontend/lib/`, …) rather than as the
individual files edited here. Only `backend/appointment/main.py`,
`backend/queuing/main.py` and `frontend/pages/queue.js` show up as ordinary
`M` entries.

**Git state: nothing was staged or committed.** The working tree already
carried unrelated changes from earlier sequences (`README.md`, service
Dockerfiles, other pages, `docs/`, `var/`). Per `.clinerules` §9, no
`git add -A`, `git reset`, `git clean`, `git stash` or `git checkout .` was run.
Anyone committing this sequence should stage the file list above explicitly and
check each file with `git diff <file>` first, because several of those paths
already had someone else's uncommitted work.

### Reproducing the verification
```bash
cd backend
../.venv/bin/python -m pytest tests/test_sequence3.py -q          # 29 passed
../.venv/bin/python -m pytest tests/test_security.py tests/test_dqds.py \
    tests/test_dashboard.py tests/test_patient_age.py \
    tests/test_tracking_tokens.py -q                              # 81 passed
cd ../frontend && npm run build                                   # exit 0
# outbox drain (not started automatically):
cd ../backend && ../.venv/bin/python -m common.notifications.worker --interval 30
```

## 12. Stop point and recommendation

Sequence 3 is complete as scoped: WP1–WP8 delivered, 29 focused tests and 81
regression tests green, the migration applied and verified in the live database,
the frontend building cleanly with the two new/changed routes.

Recommended before acceptance:
1. **Browser check** of `/queue` (missed turn → recover, including the
   permission-denied variants) and `/notifications` (toggle, provider select,
   read-only credential marker, status counts) to move those two rows in §9
   from build-verified to VERIFIED.
2. **Product-owner decision** on the new `queue.recover` / `queue.reposition`
   grants to `doctor` (§10.4) and on the provider integration path (§10.1).
3. **Sequence 4 candidate work**: add the outbox worker as a compose service,
   audit non-disclosing refusals (§10.3), and decide template/approval handling
   for a real provider.

No further action was taken beyond the work listed above.

