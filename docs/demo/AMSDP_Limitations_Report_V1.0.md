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
| **No patient registration form** | Patients page only supports search. |
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
| **No notification system** | No SMS/email integration. |
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