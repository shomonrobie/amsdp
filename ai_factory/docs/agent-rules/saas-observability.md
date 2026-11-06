---
name: saas-observability
description: Observability and logging rules for CarbonTally. Use when adding logging, metrics, an alert, a health check, or a diagnostic surface, and when deciding what must never be written to a log. CarbonTally uses stdlib plain-text logging plus in-house metrics and an immutable audit trail — not a structured-JSON pipeline, and not a SaaS log vendor.
---

# Observability — Logging, Metrics, Alerts, Redaction

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).

## 1. When to activate

Any log line, metric, alert, health endpoint, error envelope, or diagnostic/admin surface.

## 2. What actually exists (state it, do not upgrade it in prose)

- **Plain-text stdlib logging**, not structured JSON. Do not claim otherwise in a rule or a
  report; if structured logging is wanted, that is a change with a migration-free but real cost.
- **Request context** middleware (request id) and in-house API metrics that record route
  **templates**, never raw URLs (raw URLs can carry ids and query data).
- **`audit_trail`** is the append-only audit ledger, with an immutability trigger and an
  organisation stamp. It is the authoritative record for "who did what".
- **Domain log tables** exist where the domain needs them: document activity, processing logs,
  billing payment records, webhook events, idempotency keys, calculation snapshots.
- **Billing failure *data*** exists (`billing_webhook_events`, `billing_idempotency_keys`).
  An alerting **sink** is not implemented — say so rather than implying alerts fire.

## 3. Redaction — the hard rule

**Never log:** passwords, API keys, JWTs, refresh tokens, signed URLs, database credentials,
provider credentials, full payment data, or raw document contents.

- Mask a credential-shaped value (`...` + last 4) at the boundary; do not rely on review.
- A signed URL is a credential: log the object path, never the signature.
- An error body returned to a user carries a code and a safe message — never an exception
  string, a PostgREST message or a stack trace.

## 4. What a useful record contains

For an operational failure: `request_id`, route template, organisation id (when known), the
actor (when known), the stage (`extract`/`map`/`validate`/`calculate`/`report`), the outcome or
reason code, and a retry count. Not: the payload, the secret, or the signed URL.

## 5. Health and monitoring

- `/health` exists; a deeper readiness check may depend on configuration.
- Do not claim external synthetic monitoring, uptime checks or a vendor APM. If none exists,
  say none exists — an unmonitored system described as monitored is worse than an honest gap.
- A denial is a first-class signal: count it, do not swallow it silently.

## 6. Anti-patterns

- **The Secret Log** — the credential, token or signed URL in a line.
- **The Silent Denial** — an authorisation refusal with no record.
- **The Generic `logs` Table** — a catch-all table nobody queries; use the domain table.
- **The Claimed Pipeline** — describing structured logging or alerting that is not deployed.
- **The Raw URL Metric** — unbounded cardinality and leaked identifiers.

## 7. Self-check

- [ ] Does any new log line contain a secret, token, signed URL or personal data?
- [ ] Is a denial recorded and counted rather than swallowed?
- [ ] Did I claim a capability (structured logs, alerting, APM) that is not there?
- [ ] Does the error surfaced to the user avoid technical internals?
- [ ] Is the metric keyed on a route template?
- [ ] Is the event routed to its domain table rather than a generic one?
