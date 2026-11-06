---
name: saas-api-throttling
description: Rate limiting and quota rules for CarbonTally. Use when adding or changing a limiter, a quota, an upload/OCR/enqueue surface, an abuse control, or a webhook route. The limiter is a database-backed token bucket applied as a route dependency — never a global middleware, never Redis, and never in front of provider callbacks.
---

# API Throttling — Route Dependencies, DB Buckets, Webhook Safety

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).

## 1. When to activate

Any change to a limiter, a limit value, a quota, a burst/refusal path, an upload/OCR/enqueue
route, or anything under `/webhooks/`.

## 2. The ratified shape (do not redesign it)

1. **A route dependency, not middleware.** `backend/middleware/tenant_rate_limit.py` and
   `ip_rate_limit.py` run per route. `RateLimitMiddleware` is **unregistered and must stay
   unregistered** (D-004).
2. **The state is the database.** Token buckets live in `billing_rate_limit_buckets` and
   `billing_ip_rate_limit_buckets` (one table per limiter, D-014). There is **no Redis** and no
   in-process counter — a second worker must not double the allowance.
3. **Limits are scoped config.** `rate_limits` resolves customer → plan-pinned → global. Never
   hard-code a limit.
4. **The tenant key comes from the authenticated principal.** Never from the request body or
   query — otherwise a caller can spend another tenant's tokens.
5. **Headers on every response** that a limiter touches, including refusals:
   `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (absolute epoch seconds).
6. **Refusal is 429 with headers, never 500.** A refusal raised outside FastAPI's exception
   boundary becomes a 500 and loses the headers; that is a defect, not a detail.

## 3. Webhooks are never rate-limited

Provider callbacks (`/webhooks/*`) must be exempt from any global interceptor, and no limiter
may refuse one. A non-2xx response makes the provider retry — a limiter in front of a webhook
causes a retry storm rather than protection. If a global middleware is ever introduced, it must
check the path **before** counting.

## 4. What a limiter must not do

- count 4xx client errors as usage;
- apply a paid-tier limit to an unauthenticated surface with the same bucket;
- refuse a health check or a provider callback;
- return a bare 429 with no `Retry-After`/reset signal;
- store state in module globals.

## 5. Anti-patterns

- **The Global Middleware** — convenient, intercepts webhooks, and 500s on refusal.
- **The In-Memory Counter** — multiplies the allowance per worker.
- **The Body Tenant** — spending someone else's quota.
- **The Silent Drop** — refusing without telling the caller when they may retry.

## 6. Self-check

- [ ] Is the limiter a route dependency on the specific surface?
- [ ] Is the bucket state in the database, keyed by the principal's organisation?
- [ ] Are all three headers present on 200 **and** 429?
- [ ] Is every `/webhooks/*` route provably outside the limiter?
- [ ] Are the limits read from scoped config, not literals?
- [ ] Does the refusal path return 429 (never 500)?
