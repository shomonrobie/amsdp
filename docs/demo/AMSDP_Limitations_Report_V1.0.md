# AMSDP Limitations Report — V1.0

> **Date:** 2026-11-05  
> **Purpose:** Documents known gaps, constraints, and future improvements for the AMSDP MVP.

---

## 1. Data Persistence

| Limitation | Detail |
|-----------|--------|
| **In-memory storage** | All 8 microservices use in-memory Python dicts. **Data is lost when containers restart.** |
| **No PostgreSQL** | Despite Docker Compose being the deployment target, no PostgreSQL is configured. |
| **No migrations run** | SQL migration files exist but are never executed. |
| **No seed data** | Demo accounts and E2E data must be recreated after each restart (via `pytest` or API calls). |

**Workaround:** `python -m pytest backend/tests/test_e2e.py -v` to re-seed.

> **Annotation — 2026-11-25 (Product Owner decisions PO-09 / PO-13; nothing above is deleted or
> rewritten, and the table stays as the record of what was believed on 2026-11-05).** Three of the
> four statements above are **superseded and must not be repeated in a demonstration or a report**:
>
> - **"In-memory storage" is false of the current tree.** Every service persists through SQLAlchemy to
>   PostgreSQL. No service keeps authoritative state in a Python dictionary.
> - **"No PostgreSQL" is false.** `docker-compose.yml` defines the database, every service resolves its
>   connection from `DATABASE_URL`, and the deployed stack runs against it.
> - **"No migrations run" is false.** Alembic is the only schema mechanism and the chain is applied by
>   the deployment procedure and by CI. **Measured 2026-11-25: 17 revision files** in
>   `backend/alembic/versions/`.
> - **"No seed data"** holds only in the narrow sense that a demo database is seeded once:
>   `backend/seed/seed_demo.py` is the supported path (MP-05).
>
> **What is genuinely limited — stated so this correction does not overstate the product:**
> announcement **audibility has never been confirmed by a human in the room** (the reviewer is now
> named — Faria Bushra, POD-11, 2026-11-25); there is **no browser end-to-end suite**, so no page is
> `BROWSER VERIFIED`; the notification provider is a **mock**, and the SMS half of PO-02 remains
> undecided; and apart from the POD-11 appointment every review in this programme has been
> **single-engineer**.
>
> Evidence: `docs/implementation/AMSDP_PostgreSQL_Verification_and_MP-01_Reconciliation_Report_V1.0.md`,
> `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.8.

---

## 2. Authentication & Authorization

| Limitation | Detail |
|-----------|--------|
| **JWT secret hardcoded** | `_SECRET` in `models.py` is dev-only. Not suitable for production. |
| **No token expiry config** | `_TOKEN_HOURS = 8` hardcoded. |
| **No password policy** | No minimum length, complexity, or rotation. |
| **No brute-force protection** | No rate limiting or account lockout. |
| **No HTTPS** | All traffic plain HTTP.

---

## 3. Frontend Gaps

| Limitation | Detail |
|-----------|--------|
| **Patient registration is staff-only** | The Patients page provides a **Register** dialog to the roles that hold `patient.create` — `receptionist`, `branch_admin`, `org_admin`, `super_admin` — and `POST /api/v1/patients` offers the same capability; `doctor` and `assistant` see search only, because the backend denies them `patient.create`. |
| **No appointment booking UI** | Appointments page lists only; no create. |
| **No schedule creation UI** | Schedules page lists only; no create/edit. |
| **No queue actions UI** | Queue page shows list but no call/arrive/serve buttons. |
| **No doctor/staff/org/branch management UI** | Must use API directly. |
| **Locale not persistent across sessions** | Stored in `sessionStorage`. |
| **No pagination or load-more** | API capped at 20 items. |

---

## 4. Backend Gaps

| Limitation | Detail |
|-----------|--------|
| **No real duplicate detection** | Patient merge uses exact mobile match only. |
| **No appointment conflict detection** | Double-booking not prevented. |
| **No queue timeout handling** | No auto-skip for no-shows. |
| **Notifications are not delivered in the demo** | Only a `mock` provider is configured — real WhatsApp/SMS delivery is blocked pending product-owner approval — and the outbox is drained by a worker that is **not** a docker-compose service (`cd backend && python3 -m common.notifications.worker --once`). **Demo fallback:** staff issue a tracking link with `POST /api/v1/appointments/{id}/tracking-token` (QR image at `/api/v1/track/{token}/qr`) and share `/track/{token}` with the patient manually over SMS/WhatsApp. |
| **No reporting/analytics** | No utilization or volume dashboards. |
| **No WebSocket for real-time queue** | Manual refresh required. |
| **No health check endpoints** | No `/health` or `/ready`. |
## 5. DevOps & Infrastructure

| Limitation | Detail |
|-----------|--------|
| **No CI/CD pipeline** | No GitHub Actions or Jenkins for automated testing/deployment. |
| **No container orchestration** | Docker Compose on single host only. |
| **No secrets management** | JWT secret, DB passwords are hardcoded or in plain text. |
| **No monitoring/alerting** | No Prometheus, Grafana, Sentry. |
| **No backup/restore** | Irrelevant with in-memory storage, but needed for production. |
| **No SSL/TLS** | All traffic plain HTTP. |
| **No rate limiting** | No API gateway or reverse proxy limiting. |

---

## 6. Testing Gaps

| Limitation | Detail |
|-----------|--------|
| **No isolated unit tests per service** | Only one E2E test suite (15 tests). |
| **No frontend tests** | No Jest, Cypress, or Playwright. |
| **No contract tests** | No OpenAPI schema validation. |
| **No performance/load tests** | No k6, Locust, or JMeter. |
| **No security tests** | No SAST, DAST, dependency scanning. |

---

## 7. Compliance & Governance

| Limitation | Detail |
|-----------|--------|
| **Zero Git commits** | All changes outside version control. No audit trail. |
| **Zero autonomous deploys** | Human gate required; MVP runs only on local Docker. |
| **Zero baseline modifications** | AILI Factory untouched; AMSDP is separate application. |
| **Zero real patient data** | All data synthetic. |

---

## Summary: MVP Suitability

| Domain | Verdict |
|--------|---------|
| **Architecture demo** | ✅ Microservice pattern, RBAC, queue lifecycle, audit trail |
| **Feature demonstration** | ⚠️ Core flows work but UIs are basic |
| **Production readiness** | ❌ Not suitable (no persistence, no security hardening) |
| **Code quality** | ⚠️ Functional but lacks tests, error handling, hardening |
| **Governance compliance** | ✅ All session constraints met |

---

*For the defined MVP scope (see `docs/product/AMSDP_MVP_SCOPE_V1.0.md`), this build satisfies the demonstration objectives.*
| **No correlation IDs** | No cross-service request tracing. |