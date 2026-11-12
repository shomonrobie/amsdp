# AMSDP M9 Implementation Readiness Assessment

> **Task ID:** AMSDP-M9-A-PQV-IMPLEMENTATION-READINESS-2026-11-08
> **Milestone:** M9 — Patient Queue Visibility & Patient Experience
> **Status:** GATE 1 COMPLETE — Design finalized; awaiting product-owner authorization for
> M9-B implementation.
> **Date:** 9 November 2026
> **Strategic positioning:** AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.

## 1. Executive summary

M9 implements the patient-facing PQV capabilities (PQT, DQDS, Two-Stage Notifications, and
organization-admin channel configuration) on top of the existing M1–M7 staff-side MVP. The
implementation is assessed as **feasible with low architecture risk** — no new services, no
consolidation, and no changes to the 8-service topology or core appointment/queue lifecycle.
All patient-facing surfaces use read-only or capability-token access, with zero new storage of
PII. Missed-Turn Recovery is excluded per product-owner decision.

**Estimated implementation effort:** 4–6 batches across 8–12 working files.
**Database:** ~3 new migrations (tracking_tokens, org_secrets, notification_outbox).

## 2. Implementation baseline — existing M1–M7 reuse

| Existing component | How it serves M9 | Gaps |
|---|---|---|
| Appointment/queue lifecycle & statuses | Tracking-eligibility triggers; status_history carries timestamps. | No tracking-token on appointments. |
| QueueEntry model | PQT shows position, patients-ahead, serving token. | Need currently-serving indicator per doctor. |
| common/audit.py + audit_events | Notification/config audit reuses record_audit. | None. |
| Organization.config JSON | Non-secret notification settings. | Secrets need encrypted storage (org_secrets). |
| common/auth.py | Org-admin config uses same RBAC; PQT/DQDS are token-gated. | None. |
| Frontend components (AppShell, DataTable, Modal, i18n, auth.js) | Org config uses Modal; PQT/DQDS standalone pages. | New routes outside AppShell; ~20 new i18n keys. |

## 3. Database and migration requirements

### 3.1 New tables

**`tracking_tokens`** — one row per eligible appointment, PQT token hash + state.
Columns: id (UUID PK), appointment_id (FK→appointments.id UNIQUE), token_hash (String(64) not
null UNIQUE = hex SHA-256(token_bytes + pepper_bytes) — the pepper is a backend env var
`AMSDP_TRACKING_PEPPER`, never stored in the DB), token_prefix (String(8) not null = first 8
base64 chars of raw token, for display & staff reference only), status (String(20) not null =
active/revoked/expired), eligible_at (timestamp), revoked_at (timestamp null), created_at
(timestamp). Unique index on token_hash enables O(1) lookup without iteration. No salt column
needed: the raw token has 256 bits of entropy; the application pepper provides
defence-in-depth. Cross-appointment collision is computationally infeasible.

**`org_secrets`** — encrypted provider credentials per org per channel.
Columns: id (UUID PK), organization_id (FK→organizations.id), channel (String(20) =
whatsapp/sms), encrypted_value (Text, AES-256-GCM), config_json (JSON, non-secret metadata),
updated_by (String), updated_at (Timestamp).

**`notification_outbox`** — queued notification requests.
Columns: id (UUID PK), organization_id (FK), appointment_id (FK), channel (String(20)),
stage (String(1) = 1/2), status (String(20) = pending/sent/failed/cancelled),
scheduled_at (Timestamp null for stage-1), sent_at (Timestamp null), provider_response (JSON),
delivery_confirmed (Bool, →true only on provider confirm), created_at, cancelled_at.

### 3.2 Migrations (forward-only, idempotent)
Existing: `5f3fce6757cf → ccf34da72c1b → c7d3601e2486 → 9d8a1f2b3c4d → 3c8e5d0a9b2f`
New: 1. `add_tracking_tokens` 2. `add_org_secrets` 3. `add_notification_outbox`

## 4. Backend API change matrix

| Endpoint | Method | Service | Auth | Notes |
|---|---|---|---|---|
| `/api/v1/dqds/{org_id}/{branch_id}` | GET | queuing | Public | DQDS feed, token-only no PII; rate-limited |
| `/api/v1/track/{token}` | GET | appointment | Public (token-gated) | PQT data; no-cache; rate-limited |
| `/api/v1/appointments/{id}/tracking-token` | POST | appointment | require_permission("appointment.modify") | Generate + issue tracking |
| `/api/v1/orgs/{id}/notification-config` | GET/PATCH | organization | require_permission("org.manage") | Non-secret config |
| `/api/v1/orgs/{id}/notification-secrets` | GET/PUT | organization | require_permission("org.manage") | Encrypted masked-write |
| `/api/v1/orgs/{id}/notification-status` | GET | organization | require_permission("org.manage") | enabled/configured/operational |

## 5. Frontend page and component changes

| Route | Auth | Description |
|---|---|---|
| `/queue-display/{org}/{branch}` | Public | DQDS — large token text, auto-refresh, no AppShell |
| `/track/{token}` | Public (token) | PQT — single appointment card, no AppShell |
| `/orgs/{id}/notifications` | requirePermission | Channel toggles, provider selects, reminder lead, status |
| Existing print slip | — | Add QR code + short tracking link to token-print layout |

## 6. Queue and appointment lifecycle integration

- **Tracking token generation:** appointment → CONFIRMED (or CHECKED_IN) triggers token
  generation (insert tracking_tokens, status=active). Auto-revoke on IN_CONSULTATION
  (consultation start), cancellation, or reschedule.
- **DQDS current-token:** QueueEntry.status == "in_consultation" identifies currently serving
  token per doctor; DQDS endpoint aggregates per doctor/branch.
- **N1 trigger:** appointment created + CONFIRMED → notification_outbox stage=1 immediate.
- **N2 scheduling:** expected time from start_time + position-based estimate; outbox
  scheduled_at = expected_time - lead_minutes.
- **N2 cancellation:** status change away from CONFIRMED/CHECKED_IN/IN_QUEUE cancels pending
  N2. Check-in also suppresses pending N2 reminders.
- **Cooldown:** queue reorder re-evaluates pending N2 scheduled_at with a cooldown window
  (e.g., 30 s) to avoid fire/cancel thrashing.

## 7. Security and authorization requirements

| Surface | Auth model | Hard rules |
|---|---|---|
| DQDS feed | Public (no HTTP auth) | Org/branch scope in URL, deny-closed (404 on unknown); token-only, no PII; rate-limited (~10 req/s); cache short TTL. |
| PQT tracking | Capability-token only | Path = raw token; server hashes with stored salt → lookup; no-cache; rate-limited (~1 req/s per token); revoked → 404 (indistinguishable from unknown). |
| Token storage | Hash + salt at rest | Raw token never stored, logged, or exposed in API (only short prefix for display). |
| Org secrets | Encrypted at rest | AES-256-GCM with backend key; GET returns masked; cross-org 404; never in frontend or logs. |
| Channels/RBAC | org.manage | Standard RBAC; org-scoped. |
| Outbox / audit | org.manage or staff | Filtered by org; delivery_confirmed set only on provider confirm. |


## 8. Testing strategy

| Suite | Type | Scope | New tests |
|---|---|---|---|
| `tests/test_tracking_tokens.py` | Automated (TestClient) | Token gen/validate/revoke lifecycle, hash-at-rest, no-raw-token exposure, 404 on revoked | ~12 |
| `tests/test_dqds.py` | Automated (TestClient) | Feed scope, token-only no PII, rate limiting (simulate), cross-org 404 | ~6 |
| `tests/test_notifications.py` | Automated (TestClient) | Config CRUD, secrets encrypted/masked, N1 trigger on booking, N2 scheduling + cancellation, outbox status transitions, outbox state persistence | ~15 |
| Existing suite regression | Automated | 77 existing must pass | 77 |
| M9-G rehearsal | Manual / live | Full PQT/DQDS/notification demo workflow | As M9-G |

## 9. Incremental implementation dependencies

| Batch | Depends on |
|---|---|
| M9-B: Tracking tokens → PQT page migration + model + API + token endpoint + page | B1 (tok table+API) → B2 (FE page) |
| M9-C: DQDS feed + display page | queue serving model + org/branch scope |
| M9-D: Notification engine | org_secrets migration + config APIs + outbox table + scheduler + stub adapters |
| M9-E: Org-admin config UI | config APIs (M9-D) |
| M9-F: i18n + security + regression | all earlier |
| M9-G: Integrated acceptance | all complete |

## 10. Recommended implementation order

1. **M9-B1**: Tracking token migration + model + `POST /appts/{id}/tracking-token` + `GET
   /track/{token}` + auto-revoke in appointment status transitions. Tests.
2. **M9-B2**: Frontend `/track/{token}` page.
3. **M9-C1**: DQDS feed endpoint in queuing service.
4. **M9-C2**: Frontend DQDS display page.
5. **M9-D1**: `org_secrets` migration + notification config/secrets/status APIs. Tests.
6. **M9-D2**: `notification_outbox` migration + `OutboxService` + N1/N2 lifecycle hooks +
   scheduler loop + provider stub (log-only). Tests.
7. **M9-D3**: Org-admin notification settings frontend.
8. **M9-F**: Bangla/English sweep + rate-limiting middleware + full regression (77+ tests).
9. **M9-G**: End-to-end manual rehearsal + acceptance.

## 11. Explicit authorization gates

| Gate | Condition | Who triggers |
|---|---|---|
| **Gate 1 (M9 start)** | PO approves this assessment report + confirms PQT security model. | PO review |
| **Gate 2 (M9-D1 start)** | PO selects WhatsApp + SMS providers (or approves stub-first). | PO decision |
| **Gate 3 (M9-D2 start)** | PO approves encryption mechanism + outbox architecture. | PO decision |
| **Gate 4 (M9-F start)** | All earlier batches building. | CI |
| **Gate 5 (M9-G accept)** | PO witnesses integrated rehearsal. | Rehearsal |
| **Gate 6 (launch)** | PO separately authorizes cloud deployment (M8). | M8-O |


## 12. Acceptance criteria (summary, extended from PQV §J.5/§K.5)

### PQT
- Eligible (confirmed/checked-in) appointments generate an unguessable tracking token.
- `GET /track/{token}` returns only the linked appointment's queue data.
- Token revoked on IN_CONSULTATION, cancellation, reschedule; revoked → 404 (indistinguishable).
- Token hash stored; raw token never logged or returned.
- No-cache headers present; rate-limited.

### DQDS
- Feed returns tokens + counts; zero patient PII.
- Unknown org/branch returns 404.
- Rate-limited (429 + headers).

### Notifications
- Booking creates exactly one stage-1 outbox row per enabled configured channel.
- N2 scheduled_at = expected_time − lead_minutes.
- Cancel/reschedule/consultation-start sets pending N2 → cancelled.
- Check-in suppresses pending N2.
- Delivery outbox statuses correctly track pending→sent→failed→cancelled.
- `delivery_confirmed` only true when provider confirms.
- Booking succeeds with messaging disabled.

## 13. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Token collision (SHA-256) | Very low | None | Accept |
| Queue ETA inaccurate | Medium | Misleading PQT | Label "estimate, not guarantee" |
| Outbox scheduler backlog | Low | Reminder delays | Keep-alive + manual fallback |
| Secrets leaked in logs | Low | Very high | Existing redaction rules + review |
| Rate limiter not implemented | High (not started) | Public endpoint unprotected | Implement in M9-F before any public access |
| Supabase connection burst | Low | Notifications delayed | Test sustained load; adjust pool_size |

## 14. Conclusion

M9 is **feasible and well-scoped** on the M1–M7 base. Three new tables, ~7 new endpoints,
and ~3 new test suites following existing patterns — no new services, no containers, no
architectural transformation. The notification engine is the largest new sub-system but is
bounded by the outbox + scheduler pattern and gated by provider availability. The
patient-facing promise — a patient who can wait at a nearby tea stall and return on time — is
within one milestone of becoming real.

**Gates 1–3 require product-owner action and are listed in §11.**

---

## Governance and Skill Compliance (M9-A)

- **Routed governance:** `.clinerules` §2/§4 rows — Database/migrations · Backend API ·
  Multi-tenant isolation · Auth/RBAC · Dashboard · Queue/scheduling · Audit · Frontend UX · LLM
  routing applied. Governing documents: `saas-multitenant-data.md` (3 forward-only migrations),
  `saas-application-security.md` (token, secret, rate-limit, deny-closed), `saas-auth-and-
  authorisation.md` (no new roles; capability tokens ≠ accounts), `saas-observability.md`
  (delivery honesty, audit trail), `saas-frontend-ux.md` (standalone PQT/DQDS pages, i18n,
  responsive), `saas-api-throttling.md` (rate limit design guidance), as adapted in the
  governance assessment. Business Rules (PQV/approved BR revision) preserved.
- **Selected skills:** none installed (reported; not claimed).
- **Evidence:** assessment only. No source code, schema, DB, Docker, migrations, tests, cloud
  resources, credentials, or deployments were created or modified. Existing M1–M7
  functionality, local environments, databases, ports, and unrelated changes preserved.

## 15. Gate 1 — Finalized Design Details

### 15.1 PQT Security Model (finalized)

| Aspect | Decision |
|---|---|
| Token generation | `secrets.token_urlsafe(32)` → 43-char URL-safe base64 (256 bits entropy) |
| Hash storage | `sha256(token_bytes + pepper_bytes).hexdigest()` → 64-char hex (UNIQUE index) |
| Application pepper | Env var `AMSDP_TRACKING_PEPPER` — 32+ random bytes, NOT in DB; defence-in-depth |
| Token prefix | `token[:8]` — first 8 chars of base64 token, displayed on printed/UI reference |
| Lookup path | GET /track/{raw_token} → server hashes incoming token with pepper → query token_hash UNIQUE index → return row if active → 404 if revoked/unknown |
| Revocation | Update status=revoked, set revoked_at=now(). Induces 404 on future lookups |
| Indistinguishable errors | Revoked, expired, and never-issued tokens all return 404 with identical JSON body |
| No-token-exposure rules | Raw token never logged; only token_prefix may appear in logs/audit; API never returns the raw token or hash |
| Rate limiting | GET /track/{token}: 10 req/min per IP, 1 req/s burst; DB-backed token bucket |
| Appointment/org scope | FK appointment_id → one appointment; response enforces org/branch server-side |

### 15.2 Organization Secrets (finalized)

| Aspect | Decision |
|---|---|
| Encryption | AES-256-GCM with backend env var `AMSDP_SECRETS_ENCRYPTION_KEY` (32 bytes, 64 hex chars). Never stored in DB or frontend. |
| API | PUT accepts new raw value, encrypts, stores. GET returns masked (`"****"` + last 4 chars). |
| Isolation | Queries always scoped by organization_id; cross-org 404. |
| Rotation | Key rotation script (offline) re-encrypts org_secrets.encrypted_value row by row. |
| Updated_by | Set from the authenticated auth context (actor_id). |

### 15.3 DQDS Privacy (finalized)

| Aspect | Decision |
|---|---|
| Exposed fields | Token number, doctor name/room, currently-serving flag, waiting count per doctor |
| Excluded fields | Patient name, mobile, DOB, age, sex, address, all IDs, status history, actor info |
| URL scope | GET /dqds/{org_id}/{branch_id} — path-parameter scoped; unknown → 404 |
| Cache | Allow 10s Cache-Control (public); DQDS targets waiting-room TV/displays |
| Rate limiting | 30 req/min per IP |

### 15.4 Notification Scheduling (finalized)

| Aspect | Decision |
|---|---|
| N1 trigger | Immediately after appt create+CONFIRMED (or from BOOKED per org config). Outbox scheduled_at=now(). |
| N2 expected time | max(start_time, now() + 2min) — lead_minutes. Baseline estimate = start_time + 15min. |
| N2 scheduling | Outbox scheduled_at = expected_time — lead_minutes. Worker polls pending rows every 2 s. |
| Cooldown/dedup | 30-second debounce timer per doctor-branch after queue reorder. On expiry, pending N2 rows re-scheduled. |
| Cancellation rules | Appointment cancelled → outbox cancelled (all pending). Rescheduled → cancel old, schedule new. Consultation start → cancel N2. Checked-in → cancel N2. Completed → no action. |
| Delivery retries | Up to 2 retries exponential backoff (5 s, 25 s); 3rd failure → status=failed. |
| Provider confirmation | Only on provider ack → delivery_confirmed=true. Never inferred. |
| Non-blocking | Outbox insert failure does not prevent booking success (fire-and-log). |

### 15.5 Updated authorization gates

| Gate | Status |
|---|---|
| **Gate 1** (← YOU ARE HERE) | COMPLETED — assessment accepted, design finalized. Awaiting PO authorization for M9-B. |
| Gate 2 | PO selects WhatsApp/SMS providers (or confirms stub-first). |
| Gate 3 | PO approves encryption mechanism + outbox architecture. |
| Gate 4 | CI pass on all earlier batches. |
| Gate 5 | PO witnesses integrated rehearsal. |

## 16. M9-B Implementation Complete

**Status:** IMPLEMENTED — November 9, 2026

### 16.1 Backend
- **Migration:** `a1f2b3c4d5e6_add_tracking_tokens` applied to dev DB (forward-only, idempotent).
- **Model:** `TrackingToken` in `backend/common/models.py`.
- **Shared helpers:** `backend/common/tracking_tokens.py` — `token_hash()`, `generate_raw_token()`, `revoke_for_appointment()` (used by appointment + queuing services).
- **Endpoints** (all in `backend/appointment/tracking.py`):
  - `POST /api/v1/appointments/{id}/tracking-token` — issue (staff, `appointment.modify`)
  - `POST /api/v1/appointments/{id}/tracking-token/revoke` — revoke (staff)
  - `GET /api/v1/track/{token}` — public PQT data (rate-limited)
  - `GET /api/v1/track/{token}/qr` — QR code image (rate-limited)
- **Lifecycle hooks** (transactionally consistent, same DB session):
  - Appointment status change to `IN_CONSULTATION`/`CANCELLED`/`RESCHEDULED` → revoke (`appointment/main.py`)
  - Reschedule endpoint → revoke original (`appointment/main.py`)
  - Transfer endpoint → revoke original (`appointment/main.py`)
  - Queue `start_consultation` action → revoke linked appointment token (`queuing/main.py`)

### 16.2 Frontend
- **Page:** `frontend/pages/track/[token].js` — mobile-first, bilingual (BN/EN), 15s auto-refresh, low-bandwidth.
- **Styles:** PQT card/layout in `frontend/styles/global.css`.
- **Rewrite:** `frontend/next.config.js` — `/track/:path*` → appointment service.

### 16.3 Security implementation
- **Token:** `secrets.token_urlsafe(32)` = 256-bit entropy, returned exactly once.
- **Storage:** `hmac_sha256(raw + pepper).hexdigest()` with UNIQUE index (O(1) lookup).
- **Pepper:** env `AMSDP_TRACKING_PEPPER`; never stored in DB (verified by test).
- **Rate limit:** 10 req/min/IP sliding window on public endpoints.
- **Indistinguishable 404:** revoked/unknown/short tokens all return `{"detail":"not found"}`.
- **No raw-token leakage:** only the 8-char prefix ever appears in responses/audit.

### 16.4 Tests — 14 new, all passing
Token issuance/duplicate/hash-storage, active/unknown/short tracking lookups, manual + auto revocation (consultation start, cancel, reschedule), cross-org isolation, rate limiting (429), pepper non-persistence, raw-token absence in audit.

### 16.5 Regression
Existing backend tests: **54 passed, 0 failed** (one pre-existing collection error in `tests/test_e2e.py` — an unrelated `main` module attribute collision predating M9-B; run with `--ignore=tests/test_e2e.py`).

### 16.6 Files created
- `backend/alembic/versions/a1f2b3c4d5e6_add_tracking_tokens.py`
- `backend/appointment/tracking.py`
- `backend/common/tracking_tokens.py`
- `frontend/pages/track/[token].js`
- `backend/tests/test_tracking_tokens.py`

### 16.7 Files modified
- `backend/common/models.py`, `backend/appointment/main.py`, `backend/queuing/main.py`
- `backend/appointment/requirements.txt` (qrcode, Pillow)
- `frontend/next.config.js`, `frontend/styles/global.css`
- This assessment document

### 16.8 Known limitations / risks
1. Rate limiter is in-process (resets on restart); DB-backed bucket deferred to M9-F.
2. `qrcode` + `Pillow` dependencies added to the appointment service only.
3. Estimated wait time = patients-ahead × `AMSDP_AVG_SERVICE_MINUTES` (default 10), re-calculable per deployment.
4. Production must set `AMSDP_TRACKING_PEPPER`; outside `development` env the service refuses unsigned tokens.
5. M9-C (DQDS), M9-D/E (notifications, org config), WhatsApp/SMS integration are explicitly out of scope here.

### 16.9 Next action
Awaiting product-owner acceptance of M9-B before M9-C (DQDS) implementation may begin.

---

## 17. M9-B acceptance hardening — two open checks closed with live evidence

The two mandatory hardening checks left open at the end of M9-B were executed
against real uvicorn servers (not just TestClient) on 2026-11-09.

### 17.1 No-cache headers on token-bearing responses — VERIFIED

Live server: `uvicorn appointment.main:app --port 8124`, real seeded token.

| Request | Status | `cache-control` | `pragma` |
|---|---|---|---|
| `GET /api/v1/track/<raw token>/qr` | 200 | `no-store, private, no-cache, must-revalidate` | `no-cache` |
| `GET /api/v1/track/<raw token>` | 200 | `no-store, private, no-cache, must-revalidate` | `no-cache` |
| `GET /api/v1/track/<unknown 40-char>` | 404 | `no-store, private, no-cache, must-revalidate` | `no-cache` |

**Gap found and fixed during verification:** the success paths already carried
`_NO_CACHE_HEADERS`, but *error* responses (404/429) on token paths did not —
an intermediary could have cached a 404 for a token URL. Fixed by adding an
HTTP middleware in `backend/appointment/main.py` (`_no_cache_token_paths`) that
stamps the no-store headers onto every response whose path starts with
`/api/v1/track/` or `/track/`. The third row above is the post-fix evidence.

### 17.2 Access-log redaction of raw tokens — VERIFIED

Live server access log, after hitting `/api/v1/track/<raw token>` and
`/api/v1/track/<raw token>/qr`:

```
INFO:     127.0.0.1:57728 - "GET /api/v1/track/REDACTED/qr HTTP/1.1" 200 OK
INFO:     127.0.0.1:57736 - "GET /api/v1/track/REDACTED HTTP/1.1" 200 OK
INFO:     127.0.0.1:57744 - "GET /api/v1/track/REDACTED HTTP/1.1" 404 Not Found
```

A `grep -F` for the exact raw token against the log file returned nothing
(`NOT PRESENT (redacted)`). The `TokenRedactionFilter` installed by the startup
hook is therefore effective on real uvicorn access logs, not only in tests.


---

## 18. M9-C — Digital Queue Display System (DQDS) implementation report

Status: **IMPLEMENTED + TESTED + VERIFIED** in this tree. Acceptance is a
separate product-owner act and is not claimed here.

### 18.1 What was built

| Piece | Location |
|---|---|
| Public DQDS endpoint (APIRouter) | `backend/queuing/display.py` |
| Router mount + startup security hook | `backend/queuing/main.py` |
| Public display page (BN/EN) | `frontend/pages/queue-display/[org]/[branch].js` |
| Display-board styles | `frontend/styles/global.css` (`dqds-*`) |
| Automated tests (14) | `backend/tests/test_dqds.py` |

No new service, container, table, or migration was required — DQDS reads the
existing `queue_entries`, `doctors`, `branches`, and `organizations` tables.

### 18.2 Endpoint contract

`GET /api/v1/queue/display/{org_code}/{branch_code}` — public, read-only.

Identifier resolution uses the **real supported identifiers**: `organizations.code`
(globally `UNIQUE`) and `branches.code` (unique per org via `uq_branch_org_code`).
This was confirmed in `backend/common/models.py` before writing the endpoint.

Response schema is an explicit allow-list, hand-built (ORM objects are never
serialised):

```json
{
  "organization": {"name": "...", "code": "..."},
  "branch":       {"name": "...", "code": "..."},
  "doctors": [
    {"doctor_name": "...", "currently_serving": "L-001", "patients_waiting": 3}
  ],
  "updated_at": "2026-11-09T04:43:01+00:00"
}
```

Aggregation rules:

- Query is scoped to **both** `organization_id` and `branch_id`, plus today's date.
- Active set = `waiting`, `called`, `in_consultation`, `skipped`.
  `completed`, `cancelled`, `no_show` are terminal and never counted.
- `patients_waiting` = `waiting` + `called` + `skipped`.
- `currently_serving` prefers an `in_consultation` entry, else the
  lowest-position `called` entry, else `null`.
- Internal aggregation keys are stripped before serialisation.

### 18.3 Controls (deliberately different from PQT)

| Control | DQDS | PQT |
|---|---|---|
| Auth | none (public board) | capability token in path |
| Rate limit | **30 req/min/IP**, own state (`_DQDS_RATE`) | 10 req/min/IP |
| Cache | `public, max-age=10` | `no-store, private, no-cache, must-revalidate` |
| Frontend refresh | 10 s poll | 15 s poll |

### 18.4 Privacy / tenancy

- Zero patient PII: no name, mobile, DOB, age, sex, address, national ID,
  `patient_id`, `appointment_id`, tracking URL or token hash.
- Unknown org **or** a branch that belongs to a different org → **404**
  `{"detail":"not found"}` (fails closed, non-disclosing — never 403).


### 18.5 Tests — `backend/tests/test_dqds.py`

At M9-C: 14 tests, all passing. After the Sequence 2 hardening pass: **24**
tests, all passing (the 10 additions are catalogued in
`AMSDP_SEQ_02_COMPLETION_REPORT.md` §7).

| # | Test | Covers |
|---|---|---|
| 1 | `test_dqds_active_queue` | doctor-wise serving token + waiting counts |
| 2 | `test_dqds_empty_queue` | empty branch returns valid empty display |
| 3 | `test_dqds_unknown_org_404` | unknown org → 404 |
| 4 | `test_dqds_unknown_branch_404` | unknown branch → 404 |
| 5 | `test_dqds_cross_org_404` | branch of another org → 404 |
| 6 | `test_dqds_no_pii` | recursive key scan + seeded patient values absent + exact schema |
| 7 | `test_dqds_rate_limit` | 429 inside 35 requests, ≤30 succeed |
| 8 | `test_dqds_cache_headers` | `public, max-age=10`, and **not** `no-store` |
| 9 | `test_dqds_non_active_excluded` | completed/cancelled/no_show excluded; skipped counts |
| 10 | `test_dqds_updates_reflected` | status change visible on next request |
| 11 | `test_dqds_timezone_today_only` | other-date rows excluded |
| 12 | `test_dqds_other_org_isolation` | other org's queue never bleeds across |
| 13 | `test_dqds_public_no_auth_required` | no Authorization header needed |
| 14 | `test_dqds_no_internal_helpers_leak` | internal aggregation helpers never serialised |

Result at M9-C: `14 passed` (`python3 -m pytest tests/test_dqds.py -q`).
After the Sequence 2 pass: `24 passed` (repeated runs, proving the extended
fixtures do not leak between runs) — see §18.12.

### 18.6 Regression

`python3 -m pytest tests/ queuing/tests/ identity/tests/ --ignore=tests/test_e2e.py -q`
→ **108 passed**. That is 94 pre-M9-C + 14 new DQDS. The pre-existing
`tests/test_e2e.py` collection error is unrelated and predates M9 (run with
`--ignore`). The `appointment/main.py` middleware added in §17.1 was in place
for this run.

Re-run after the Sequence 2 hardening pass: **118 passed** (same command) —
108 + the 10 new DQDS tests. See §18.12.

### 18.7 Live verification (VERIFIED, not just green tests)

Live `uvicorn queuing.main:app --port 8125` against the real Postgres with a
seeded branch (1 `in_consultation`, 1 `called`, 1 `waiting`, 1 `skipped`,
1 `completed`, 1 `cancelled`):

```
HTTP/1.1 200 OK
cache-control: public, max-age=10
content-type: application/json

{"organization":{"name":"Live Hospital","code":"LIVE-ORG"},
 "branch":{"name":"Live Branch","code":"LIVE-BR"},
 "doctors":[{"doctor_name":"Dr. Live","currently_serving":"L-001",
             "patients_waiting":3}],
 "updated_at":"2026-11-09T04:43:01.894203+00:00"}
```

`currently_serving` = `L-001` (the `in_consultation` entry) and
`patients_waiting` = 3 (`called` + `waiting` + `skipped`), with `completed`
and `cancelled` correctly excluded. Live 404s confirmed for unknown org,
unknown branch, and cross-org branch. All live fixture rows were removed
afterwards; both servers were stopped.

### 18.8 Frontend

`npm run build` in `frontend/` → exit 0, `EXIT=0`, page compiled. The display
page polls `/api/v1/queue/display/{org}/{branch}` every 10 s, which is routed
by the **existing** `/api/v1/queue/:path*` rewrite — no `next.config.js`
change was needed. UI is bilingual (BN/EN), TV/monitor-friendly, and renders
loading / empty / 404 / error states. (After the Sequence 2 pass the language
precedence is `?lang=` → `localStorage['dqds_locale']` →
`sessionStorage.locale` → `bn`; route and language are resolved post-mount to
avoid hydration drift. Rebuilt: `npx --no-install next build` → EXIT=0.)

### 18.9 Governance and skill compliance

- **Applicable governance (§4 routing):** Backend API endpoints → adapted
  `saas-application-security.md` + Business Rules Parts II–X; multi-tenant data
  → adapted `saas-multitenant-data.md` §4–5 + `backend/common/auth.py` scope
  checks; frontend → adapted `saas-frontend-ux.md` + shared styles /
  `sessionStorage.locale` convention; queue/scheduling → Business Rules
  Parts V–VII.
- **Skills:** none installed in this workspace; the §5 registry state is
  unchanged. Governance documents were used instead, as §4 requires.
- **Non-negotiables honoured:** no secrets or tokens logged; access enforced
  server-side (org/branch derived from the resolved path identifiers and
  compared against the DB, never trusted from a request body); cross-tenant
  access fails closed with 404 (never 403); single tenant key
  `organization_id`; no schema change, therefore no migration; verification
  claims in this section are backed by the command output quoted above.
- **Deviation:** none in scope. The one in-flight fix (§17.1 404 cache
  headers) was required to close a pre-existing M9-B hardening item, not to
  satisfy a new M9-C requirement.

### 18.10 Known limitations

1. Rate limiting is in-process per worker (same known limitation as PQT);
   a durable shared limiter remains deferred to M9-F.
2. ~~`updated_at` is server clock time; the display shows the client render
   time, not the server's.~~ **Fixed in Sequence 2** — the board renders the
   server's `updated_at` via `Intl.DateTimeFormat`.
3. Doctors with no active entries today are not listed (no roster source is
   consumed); a future revision may join `doctor_branches` to show idle
   doctors with `null` serving. Now asserted explicitly by
   `test_dqds_idle_doctor_not_listed`.
4. ~~The display trusts that a `QueueEntry`'s `doctor_id` belongs to the same
   org.~~ **Fixed in Sequence 2** — the doctor join is constrained to
   `Doctor.organization_id == org.id` (plus the org's active doctor roster), so
   a mis-joined row publishes nothing (`test_dqds_cross_org_doctor_name_never_leaks`).
5. Suspended/expired organizations and disabled branches now return the same
   non-disclosing 404 as an unknown code; `NULL` status is treated as active so
   pre-suspension rows keep serving (Sequence 2).

### 18.11 Next action

M9-C awaits product-owner acceptance. M9-D (notifications) remains gated by
Gate 2 (provider selection) and is out of scope here.

| Gate 6 | PO separately authorizes cloud deployment (M8). |

---

### 18.12 Sequence 2 audit addendum — DQDS hardening (2026-11-09)

Full detail: `AMSDP_SEQ_02_COMPLETION_REPORT.md`. This addendum records only
what changed **after** §18.1–18.11 were written, so the earlier section stays
readable as the M9-C record.

**Audited gaps found and closed**

| Gap | Before | After |
|---|---|---|
| Suspended/expired org, disabled branch | served a board | same non-disclosing `404 {"detail":"not found"}` as an unknown code (`NULL` status = active, deliberately) |
| Cross-tenant `doctor_id` on a queue row | could publish another tenant's doctor name | join constrained to `Doctor.organization_id == org.id` + active roster → publishes nothing |
| Deactivated doctor | still advertised | excluded |
| Rate-limit signalling | bare 429 | `X-RateLimit-Limit/Remaining/Reset` on every limited response, `Retry-After` on 429 |
| Limiter memory | unbounded per-IP buckets | stale buckets pruned every 512 requests |
| `currently_serving` | `in_consultation` only | `in_consultation`, else the lowest-position `called` |
| Error caching | cacheable | `no-store` on 404 and 429 (board keeps `public, max-age=10`) |
| Display page | route/lang resolved during render; no not-found state, no `?lang=`, no stale-on-error recovery | post-mount resolution (no hydration drift), `?lang=` → `dqds_locale` → `sessionStorage.locale` → `bn`, explicit phase machine, stale-while-error with automatic recovery, `aria-live`, `Intl` timestamps |
| Test coverage | 14 tests | 24 tests (limiter headers, inactive org/branch/doctor, cross-org name leak, `called` precedence, skipped-never-serving, PQT-material absence, non-disclosing 404) |

Unchanged by design (re-verified, not re-decided): `skipped` still counts in
`patients_waiting`; `completed`/`cancelled`/`no_show` stay invisible; only the
serving token is published; no schema change, therefore no migration.

**Evidence re-run in this tree**

| Check | Command | Result |
|---|---|---|
| DQDS suite | `python3 -m pytest tests/test_dqds.py -q` | 24 passed (repeated runs) |
| Regression | `python3 -m pytest tests/ queuing/tests/ identity/tests/ --ignore=tests/test_e2e.py -q` | 118 passed |
| Frontend build | `npx --no-install next build` | EXIT=0, `/queue-display/[org]/[branch]` static, 2.31 kB |
| Live 200 | `curl -i .../live-seq2-org/live-seq2-br` | serving `L-001`, `patients_waiting` 3, `public, max-age=10`, `x-ratelimit-limit: 30` |
| Live 404 | unknown org | `404`, `cache-control: no-store`, `{"detail":"not found"}` |
| Live suspend/restore | org status flipped | 404 while suspended, 200 after restore |
| Live 429 | limiter exhausted | `retry-after` present, `x-ratelimit-remaining: 0`, `no-store` |

Live fixtures (queue entries, patient, doctor, branch, organization) were
deleted and the server was stopped afterwards. No commit, push, merge, or
deploy was performed; acceptance is still a product-owner act.
