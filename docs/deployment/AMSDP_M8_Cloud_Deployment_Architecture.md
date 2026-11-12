# AMSDP M8 Cloud Deployment Architecture

> **Milestone ID:** AMSDP-M8-PCL-2026-11-08 · **Phase:** M8-A (assessment & planning only)
> **Status:** FOR PRODUCT-OWNER APPROVAL — no cloud resources created, no credentials entered,
> no charges incurred, no public deployment published.
> **Date:** 2026-11-08

## 1. Purpose and scope

Assess how the existing AMSDP (8 FastAPI services + Next.js frontend + PostgreSQL, currently
running as a local Docker Compose stack) can be made securely publicly accessible for hackathon
judges, and produce a recommended deployment architecture, cost/availability assessment, and an
approval-gated execution plan.

**Authorization boundary honoured:** this document only evaluates. Creating cloud resources,
entering credentials, or publishing any public deployment requires explicit product-owner
approval after this assessment.

## 2. Verified inventory of the current implementation

Facts verified against the working tree and the running local stack (M8-A baseline):

| Component | Verified behaviour relevant to deployment |
|---|---|
| Frontend (Next.js 14 Pages Router) | Talks to services **only through server-side rewrites** (`next.config.js` → `http://identity:8000/…` etc.); the browser uses relative `/api/v1/*` paths only — no absolute URLs, no DB access. |
| Backend (8 FastAPI services: identity, organization, patient, doctor, scheduling, appointment, queuing, audit) | Each binds a fixed port (`uvicorn --port 8000..8007`); **no service-to-service HTTP calls** exist — services read the shared PostgreSQL schema directly via `backend/common/` (SQLAlchemy `SessionFactory`, `common/models.py`). |
| Database (PostgreSQL 16, Docker) | Single shared schema; org/branch isolation enforced application-side (`common/auth.py`). |
| Secrets (env vars) | `AMSDP_DATABASE_URL`, `AMSDP_JWT_SECRET`; `common/auth.py` already **fails fast** in non-development environments when the JWT secret is missing. |
| CORS | **Not configured** — the browser never calls a backend directly today (superscripted by Next rewrites). |
| Health endpoints | **None** — services expose no `/health` (verified 404). |
| Persistence | PostgreSQL only; no local-filesystem writes (legacy in-memory `audit` service is unused; real audit lives in `audit_events`). |
| Migrations / seed | Alembic chain `5f3fce6757cf → ccf34da72c1b → c7d3601e2486 → 9d8a1f2b3c4d → 3c8e5d0a9b2f`; `seed/seed_demo.py` idempotent, self-refreshing, synthetic data only. |
| Auth/RBAC | JWT (HS256) + `common/permissions.py`; tenant from token; cross-org/branch fail closed; 6 roles. |
| Rate limiting | **Not implemented** (design guidance only; see §10). |

**Conclusion:** the local stack cannot be deployed to the cloud unchanged. Every component needs
an environment adaptation (URLs, secrets, ports, health/cold-start behaviour), but **no code
architecture change is required** — service boundaries and API contracts are cloud-ready.

## 3. Compatibility review

### 3.1 Supabase × SQLAlchemy × Alembic

| Concern | Assessment |
|---|---|
| Driver | `postgresql+psycopg2://` works against the direct connection host (`db.<ref>.supabase.co:5432/postgres`). |
| SSL | Required by Supabase → add `?sslmode=require`; `pool_pre_ping=True` already set in `common/database.py`. |
| Alembic | Plain DDL — fully supported; run against the cloud URL from the release host, never the browser. |
| Atomic UPSERT (queue tokens) | PostgreSQL `ON CONFLICT` — supported; the concurrency design carries over unchanged. |
| Transactions | Standard PG — audit rows still commit atomically with operations. |
| Connection pooling | Free tier allows ~60 direct connections. Current defaults (`pool_size=5, max_overflow=10`) × 8 services risk exceeding that → **reduce to `pool_size=2, max_overflow=2` + `pool_recycle`**, env-configurable. Supabase pooler (port 6543, transaction mode) is a compatible alternative (the app holds no session-level PG state); decide after a live connection-count probe. |
| Inactivity pause | Free projects pause after 7 days without API activity; must be restored manually. The demo keep-alive must prevent this. |
| Backups | Free tier daily backups, 7-day retention — adequate for a demo. |

### 3.2 Render free tier

| Concern | Assessment |
|---|---|
| Instance hours | **Shared pool ≈750 hours/month across ALL free services in the workspace.** Eight 24/7 services need ~7× the pool → **impractical on free tier** (see §5). |
| Cold starts | Free web services sleep after ~15 min idle and take ~50–60 s to wake; eight services waking independently is a poor judge experience. |
| Resources | 0.1 vCPU / 512 MB RAM per instance — fine for one uvicorn; tight for several. |
| Custom domains | Not on free tier — platform URLs used (acceptable). |
| Port binding | Render injects `$PORT`; all Dockerfile `CMD`s hard-code 8000–8007 → must become `$PORT`-aware. |

### 3.3 Vercel Hobby

- Free tier is appropriate for a **non-commercial hackathon demo**; platform URLs accepted.
- Next.js rewrites work on Hobby (serverless proxy) → the app keeps relative `/api/v1/*` calls,
  never exposing backend URLs to the browser, and the browser never holds database credentials.
- Hobby bandwidth (~100 GB/mo) is ample; build minutes are limited but fine; first-request
  function cold start is normal.

### 3.4 Compatibility conclusion

**Compatible with adjustments.** Required cloud adapters (all M8-D items, no business-rule or
API-contract changes): `$PORT`-aware Docker CMDs, `/health` endpoints, production rewrite URLs,
CORS allowlist, tightened SQLAlchemy pool settings, SSL in the DB URL, and a strong
`AMSDP_JWT_SECRET` (already enforced).

## 4. Recommended architecture

```text
  Public (judges / reviewers / demo users)
            │  HTTPS
            ▼
  ┌───────────────────────────────┐
  │  Vercel (Hobby) — Next.js     │  landing page (/, public) + app (/login, /dashboard, …)
  │  Landing + Application         │  server-side rewrites /api/v1/* → backend origin
  └───────────────┬───────────────┘
                  │ HTTPS (server-side, no browser→backend, no DB credentials in frontend)
                  ▼
  ┌───────────────────────────────┐
  │  Backend origin (single entry) │  8 FastAPI services, unchanged boundaries & ports
  │  (see §5: Option B recommended)│  identity · organization · patient · doctor ·
  │                                │  scheduling · appointment · queuing · audit
  └───────────────┬───────────────┘
                  │ SSL (sslmode=require), low pool sizes
                  ▼
  ┌───────────────────────────────┐
  │  Supabase (Free) — PostgreSQL │  dedicated project, synthetic demo data only
  │  migrations via Alembic       │
  └───────────────────────────────┘
```

Design principles honoured:
- **Landing and application remain separate concerns** (distinct pages/routes; the landing page
  is public, the app requires login; the demo button navigates to `/login`).
- **The backend is the only component with database credentials.** The frontend never receives
  `AMSDP_DATABASE_URL` or the Supabase password.
- **All API traffic stays same-origin** through Vercel rewrites (no CORS dependency); CORS is
  still configured on the backend as defence-in-depth for any direct calls.
- **Synthetic data only** in the cloud; the local dev/demo databases remain untouched.

## 5. Backend hosting decision (Render)

### 5.1 Why eight individual free Render services are impractical

The product owner's architecture table lists Render for the FastAPI backend. Running the eight
services as **eight separate Render Free web services** is technically possible but fails three
acceptance tests at once:

1. **Shared free-hours pool (~750 h/month for all free services at the workspace level).**
   Eight services running around the clock consume ~5,840 instance-hours/month — ~7.8× the
   free allowance → Render would keep most instances spun down.
2. **Independent cold starts.** Each sleeping service takes ~50–60 s to wake; the first judge
   click would stall repeatedly across services.
3. **Operational sprawl.** Eight deployments, eight wake/discovery cycles, and eight failure
   surfaces for a two-hour demo window.

This is therefore presented as **not recommended**.

### 5.2 Option B (recommended — requires product-owner approval)

**One backend host running the existing Docker Compose service topology.** The 8 services remain
8 separate processes with the same internal ports, the same `backend/common/` boundaries and the
same `/api/v1/*` contracts — nothing is consolidated or removed. A minimal reverse proxy
(nginx/caddy) in front of the 8 services maps the single public HTTPS entry to each internal
service by path, mirroring today's `next.config.js` rewrites.

- Suggested implementations:
  - **Render Starter web service** (1 Dockerfile that starts nginx + 8 uvicorns; ~0.5–1 GB RAM,
    $7–13/month), **or**
  - **A small Linux VPS** ($4–8/month) running `docker compose up` essentially as locally.
- Because this changes the hosting shape (single host vs 8 services) and may use a provider
  other than Render, it is presented for approval per the milestone instructions
  ("Do not substitute another hosting provider … without approval", "Do not consolidate
  services or change architecture without approval"). Note: no service or endpoint is removed;
  only the hosting topology changes.

### 5.3 Option A (conforming, fallback)

If the product owner prefers to keep per-service Render deployments, the least-bad shape is
**paid Render services** for the busiest ones (identity, appointment, queuing) with the rest on
free — but this still hits the shared-hours and cold-start problems and is cost-inefficient
(~$21–56/month). **Not recommended.**

## 6. Supabase configuration requirements

| Item | Requirement |
|---|---|
| Project | One dedicated Free project for the online demo (never the local dev DB). |
| Credentials | Set `AMSDP_DATABASE_URL` as an env var on the **backend host only**. Never place it in frontend code, files, reports, or screenshots. |
| URL form | `postgresql+psycopg2://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require` (direct: `db.<ref>.supabase.co:5432`). Preferred: **pooler** (transaction mode) to stay under connection limits; verify with a live connection-count probe. |
| Pool settings | Backend override: `AMSDP_DB_POOL_SIZE=2`, `AMSDP_DB_MAX_OVERFLOW=2`, `AMSDP_DB_POOL_RECYCLE=1800` (to be implemented in `common/database.py`, defaulting to current values locally). |
| Migrations | Run `alembic upgrade head` from the release host with `AMSDP_DATABASE_URL=<cloud>` — never the browser; preserve the forward-only chain. |
| Seeding | `seed/seed_demo.py` against the cloud DB (synthetic only), idempotent + self-refreshing; demo reset = truncate the demo tenant tables **in the cloud DB only**, then re-seed. |
| Isolation | Re-verify org/branch isolation + concurrent queue-token uniqueness on the cloud DB before release (M8-G). |
| Keep-alive | Scheduled heartbeat to a health endpoint keeps the project awake and outside the 7-day pause. |
| RLS | Not used by the app (isolation is application-level per Business Rules §4); leave disabled to preserve behaviour; restrict DB access to the backend host where possible. |

## 7. Vercel project configuration

| Item | Requirement |
|---|---|
| Project | One Next.js project (`frontend/`), framework preset Next.js. |
| Build | `npm run build` (already green); production `NODE_ENV` at build time. |
| Env vars | **None secret:** no DB URL, no JWT secret. Non-secret knobs only (e.g., `NEXT_PUBLIC_APP_URL` if ever needed). |
| Rewrites | `next.config.js` rewrites target the production backend origin (Option B URL) instead of `identity:8000/…`. No localhost in production builds. |
| HTTPS | Automatic on Vercel. |
| Demo URL | *Explore Live Demo* links to `/login` on the same deployment. |
| Degradation | Landing page is static content → stays fully usable if the backend is briefly unavailable (with a clear note under the demo button). |
| Eligibility | Hobby fits a non-commercial hackathon demo; platform URL; re-verify Terms at deploy time. |

## 8. Free-tier limitations and likely failure points

| Limitation | Impact | Mitigation |
|---|---|---|
| Render free shared hours ~750 h/mo across all free services | 8 services cannot run 24/7 | Option B single host (~24/7) or accept sleeping (not recommended) |
| Render cold start ~50–60 s | Slow first API calls | Keep-alive pings + warm-up; warn judges the first load can take ~1 min |
| Supabase 7-day inactivity pause | Project offline if unused | Scheduled heartbeat + documented manual *Restore* |
| Supabase connection limits ~60 direct | Pool exhaustion under bursts | Pooler + low pool sizes (configurable) |
| Vercel Hobby bandwidth/build limits | Unlikely for a demo | Monitor; static landing stays light |
| No custom domains on free tiers | Platform URLs only | Accepted |
| Missing `/health` endpoints | Render checks + runbook probes fail | Add `/health` in M8-D (small, contract-safe) |
| No rate limiting | Public brute-force/login abuse | Implement a route-level limiter pre-launch (M8-G; §10) |
## 9. Required product-owner / user actions (before deployment)

1. **Approve Option B hosting topology** (§5.2) — the single deployment decision that unlocks
   everything.
2. Create the **Supabase** Free project (product owner's account) and provide the connection
   string to be set only as a backend env var.
3. Create the **Vercel** project and import the repo (or `vercel` CLI) — no secrets needed.
4. Create the **Render / VPS** backend host per Option B.
5. Provide a strong **`AMSDP_JWT_SECRET`** (`openssl rand -hex 32`) set only as a backend env var.
6. Authorize running **Alembic + demo seed** against the cloud DB (release host).
7. Authorize the **public demo credentials** (unchanged from M7 seed; passwords live only in
   `seed_demo.py` and are never published in the UI).

## 10. Security posture for public launch (M8-G inputs)

- HTTPS end-to-end (Vercel + backend origin). Auth/RBAC unchanged (6 roles; JWT from backend
  env). Org/branch isolation remain application-level (verified locally; must be re-verified on
  the cloud DB from an external browser).
- **Rate limiting is not implemented** — the only identified security gap for public exposure.
  Recommended minimal control before launch: a DB-backed route-dependency limiter on
  `/api/v1/staff/login` and patient create (429 + headers; per `saas-api-throttling.md` guidance).
  This is an M8-G pre-launch item requiring approval to implement.
- CORS: allowlist to the Vercel origin only (defence-in-depth; the main path is same-origin
  rewrites).
- Secrets: JWT + DB URL exist only on the backend host; no secrets in logs (existing redaction
  rules), reports, screenshots, or the frontend bundle.
- Synthetic data only; no real patient records ever uploaded; synthetic-data disclaimer on the
  landing page.

## 11. Estimated operating cost

| Item | Cost |
|---|---|
| Vercel Hobby | $0/month |
| Supabase Free | $0/month |
| Backend (Option B) — Render Starter | ~$7–13/month |
| Backend (Option B) — small VPS (1 GB / 1 vCPU) | ~$4–8/month |
| **Total (recommended)** | **≈ $4–13/month (platforms $0 + one host)** |
| vs. 8 paid Render services | $56–104/month (rejected) |

## 12. Deployment execution plan (approval-gated)

1. **Gate 0 — Approval.** Product owner approves Option B topology, accounts setup, cloud
   migration/seed authorization, and the rate-limiter item.
2. **M8-D implementation.** `$PORT`-aware Docker CMDs, `/health` endpoints, env-configurable pool
   settings in `common/database.py`, production rewrite URLs in `next.config.js`, CORS allowlist,
   prod-env validation for `AMSDP_DATABASE_URL` (fail fast if unset in non-dev).
3. **M8-B landing page.** Public `/` landing (branding, problem/solution, capabilities,
   screenshots, demo button, synthetic-data disclaimer, Bangla/English, responsive), login moved
   to `/login`.
4. **M8-C cloud DB.** Create Supabase project; run Alembic + seed; connection-probe check; verify
   concurrency/isolation on the cloud DB.
5. **M8-E Vercel.** Deploy frontend; verify the landing page is independent of the backend; verify
   rewrites to the backend origin; HTTPS check.
6. **M8-F online demo dataset.** Use the M7 seed strategy against the cloud DB; verify 6 roles,
   branch switching, audit; document the demo reset procedure.
7. **M8-G external testing.** Full persona workflows + security matrix from an external
   browser/network; verify persistence in the cloud DB; rate limiter verified.
8. **M8-H documentation.** `AMSDP_M8_Deployment_Runbook.md` + `AMSDP_M8_Public_Launch_Readiness_Report.md`
   (created during deployment; architecture doc = this file).
9. **Cutover.** Public demo live; local dev/demo stacks untouched.

## 13. Open items for the product owner

1. Approve Option B (§5.2) — a single host inside Render or a small VPS.
2. Approve the pre-launch rate-limiter implementation (§10).
3. Approve cloud migration + seed execution and the public demo credentials set.
4. Confirm Vercel/Supabase/Render accounts and ownership (user actions in §9).

---

## Governance and Skill Compliance

- **Routed governance:** `saas-cicd-workflow.md` (honest capability claims, no invented CI state),
  `saas-application-security.md` (tenant-from-principal, deny closed, secrets), `saas-observability.md`
  (no claims without verification), `saas-api-throttling.md` (limiter design guidance), all as
  adapted in `AMSDP_Engineering_Governance_Assessment.md` §3; Business Rules; `.clinerules`.
- **Selected skills:** none installed (reported, not claimed).
- **Evidence:** deployment compatibility claims are explicitly marked assessed-vs-to-verify; no
  cloud resource was created and no live deployment is claimed.
## 14. PQV revision of this assessment (2026-11-08)

Revised after product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
(DQDS, PQT, WhatsApp + SMS). The architecture in §4 remains unchanged in
shape; the items below add the PQV requirements and their deployment
implications. **Unless stated, everything here is assessment only — no
implementation, provider registration, credential entry, or cloud
activity has occurred.**

### 14.1 DQDS and PQT — API and deployment implications

| Item | Implication |
|---|---|
| DQDS feed endpoint(s) | Public, read-only, token-number-only queue feed scoped by org+branch; must be served HTTPS; PII-free payload; cache allowed (public data) but short TTL; tenant/branch key from the display's configured scope, deny-closed. |
| DQDS target | A waiting-room TV/web page. Served from the same Vercel site (route) or a static client polling the feed — no extra backend services required. |
| PQT endpoint(s) | Public unauthenticated route keyed by capability token (`/track/{token}`); token unguessable and hashed at rest; returns only the linked appointment's data; **no-cache headers mandatory**; rate-limited; revoked on consult-start/cancel/reschedule; tokens never reactivated. |
| PQT token storage | New table, forward-only migration, hash-at-rest, revocation flag + expiry. |
| Estimated wait | Derived client-side or by a light backend calc from queue state; labelled estimate; must never be a guarantee. |

**Deployment impact on §4 architecture:** two new public routes (DQDS feed,
PQT) behind the same frontend origin and backend host; no new services;
new low-complexity endpoints + migration in the queue/appointment boundary.

### 14.2 WhatsApp and SMS integration architecture

- A **notification boundary** (service/outbox) consumes domain events
  (appointment confirmed/reminder, check-in, queue events) and issues
  outbound provider calls; provider-specific adapters live behind it, not
  in Appointment/Queue services.
- Provider calls are **asynchronous, retry-bounded, non-blocking** for
  appointment creation; results recorded append-only (request, delivery
  outcome, failure) in the audit trail. **No silent delivery claims.**
- **Provider account, API, sender ID, template approval, and paid-service
  dependencies are NOT assumed to exist** anywhere in the stack or this
  plan. Each channel's "operational" state is derived from actual provider
  readiness, not from configuration defaults.

### 14.3 Organization-level provider configuration and platform governance

- Organisation settings: enable/disable WhatsApp and SMS; provider
  selection from a **platform-approved registry**; per-channel
  enabled/configured/operational indicator.
- **Platform Super Admin (central):** provider registry, plan-pinned
  limits/defaults, global sender-ID/template applicability, central health.
- **Tenant isolation:** org-scoped settings & secrets; one org can never
  read another's configuration or credentials (fail closed).

### 14.4 Secure secret storage

Provider API keys/tokens stored **encrypted at rest, backend-side,
org-scoped**; only masked/unmasked-on-write API. Never exposed to the
frontend, logs, error responses, screenshots, or this repository. The
backend host env vars carry bootstrap secrets; runtime secrets stay in the
database (encrypted) or a platform secret store approved at deploy time.

### 14.5 Notification delivery, retries, failures, and audit

- Delivery pipeline: enqueue → attempt → outcome record. Bounded retries
  with backoff for transient provider failures; dead-letter + manual
  resend path for repeated failures (operational, not automatic infinite
  retry).
- **Auditability:** append-only events for channel configuration changes,
  notification requests, delivery outcomes, failures, and PQT token
  issue/revocation.
- **Never block the core workflow:** appointment creation and queue
  operations complete whether or not a channel is configured.

### 14.6 Rate limiting and security

- Rate-limit targets (per `saas-api-throttling.md` guidance): `/staff/login`,
  patient creation, **and public PQT tracking and DQDS feed endpoints**.
  Database-backed route dependencies returning **429 with
  Retry-After/X-RateLimit headers**, never 500; tokens never cached on
  shared/CDN layers; privacy layering is backend-enforced.

### 14.7 Tenant and branch isolation (unchanged but reinforced)

All PQV surfaces are org- and branch-scoped server-side; token/display
scope comes from the server, never from the request body; cross-tenant
reads fail closed (404 non-disclosing). Patients remain org-scoped
records; appointment branch association preserved.

### 14.8 Cloud-platform notes (revised)

- **DB connection limits & pooler:** pool-size cap required (2/2 + recycle)
  per service. **Supabase pooler-port inconsistency (flagged):** the pooler
  address historically used port **6543**; recent Supabase guidance uses
  ports **5432/5433** depending on region and Supavisor version. This
  assessment does not pin a port — the correct direct-vs-pooled connection
  string must be verified against the actual Supabase project at deploy
  time. The M7 Document referenced 6543; treat it as to-verify.
- **Supabase Free backup assumptions:** daily backups with a retention
  window are assumed; retention terms should be re-verified at deploy
  time, and our `_tools/pg_backup.sh` (against the cloud URL) remains the
  local safety net.
- **Startup / health / recovery of the eight services:** each service
  needs `/health` (mandated in M8-D), `$PORT`-aware binding, and an
  explicit startup order/keep-alive. Free-tier cold starts (~50–60 s)
  remain the biggest availability risk for a live judge demo.
- **Public demo security & synthetic data:** only synthetic demo records
  in the cloud; demo disclaimer required on the landing page; demo
  credentials are not published in the UI; rate limiting per §14.6.

### 14.9 Revised feature-to-architecture traceability

| PQV feature | Architecture touchpoint | External dependency |
|---|---|---|
| DQDS (MVP) | public feed endpoint + display route | none |
| PQT (MVP) | tracking endpoint + token table + QR on print | none |
| WhatsApp/SMS notifications | notification boundary/outbox + provider adapters | **provider accounts/APIs/templates/sender IDs; costs where applicable** |
| Org channel config | org settings API + encrypted secret store | provider registry existence |
| Tracking-URL messages | templates + short URL handling | providers + HTTPS domain |

### 14.10 Decisions still requiring product-owner approval

1. Approve Option B hosting topology (§5.2).
2. Approve implementing the pre-launch **rate limiter** (§10/§14.6).
3. Approve cloud migration + seed execution and public demo credentials.
4. Select which external providers are platform-approved for WhatsApp/SMS
   and whether any provider account work is authorized (cost-bearing).
5. Confirm Supabase/Vercel/Render accounts and ownership.

### 14.11 Features that require external provider accounts or incur cost

- **WhatsApp delivery** (provider account/API; template approval; per-message
  costs may apply).
- **SMS delivery** (provider account/sender ID; per-message costs).
- **Provider-registry availability** (platform-level provider agreements).
- **Hypothetical paid hosting seats** if Option B is hosted on paid
  infrastructures (Render Starter or VPS). Platform free tiers remain $0.

### 14.12 Recommendation

**The §4 architecture (Vercel + single-host backend + Supabase) remains
suitable for the hackathon demo**, including the added PQV surfaces: DQDS
and PQT add only two low-complexity public routes to the existing host;
WhatsApp/SMS are required but provider-gated, with manual link sharing as
the operational fallback, so the demo does not depend on any external
provider actually delivering messages.

Deployment remains **approval-gated**: Option B hosting, the rate limiter,
cloud migration/seeding, and provider-selection decisions (§14.10) must be
approved before any cloud resource is created or credential entered.

### 14.13 Two-stage notifications and missed-turn recovery — deployment notes

- **Two-Stage Patient Notifications** (appointment confirmation + configurable pre-visit
  reminder, default 10 min, 5/10 options) are **APPROVED P0 product scope but not yet
  implemented**; they do **not** add new backend services to the §4 topology: the
  notification boundary/outbox and a lightweight reminder scheduler run on the existing
  single host (or as an additional worker process there). Delivery is **provider-gated**;
  the demo must not depend on real message delivery.
- Reminder scheduling must be **queue-state aware**, **cooldown/dedup** protected, and
  support cancellation (cancel/reschedule/consultation-started) and check-in suppression;
  the scheduler needs the same platform secrets policy as the backend and writes delivery
  outcomes to the audit trail.
- **Missed-Turn Recovery & Queue Repositioning** is **NOT APPROVED FOR MVP** (2026-11-08)
  and **not in any deployment plan**; a future proposal must address Business Rules §§20–21,
  grace/late-arrival policy, queue-state semantics, emergency/priority handling and audit
  events before it can be considered.
- **Business Rules reconciliation:** a proposed revision draft
  (`docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`) covers DQDS/PQT
  carve-outs, one-way operational WhatsApp/SMS notifications, two-stage notifications and
  reminder cancellation/deduplication; the authoritative Business Rules document remains
  unchanged until the recommended revision is separately approved.
- None of these capabilities are implemented; nothing here claims otherwise.

---

## Governance and Skill Compliance (M8, incl. WP additions)

- **Routed governance:** same adapted rules as the original M8-A plus
  `saas-multitenant-data.md` (org-scoped secrets, tenant isolation),
  `saas-auth-and-authorisation.md` (capability tokens ≠ account model),
  `saas-observability.md` (honest delivery reporting), and
  `saas-cicd-workflow.md` (no invented CI/implementation claims), all as adapted in
  the governance assessment.
- **Selected skills:** none installed (reported; not claimed).
- **Evidence:** all PQV/M8 items, two-stage notifications and missed-turn recovery are
  documentation and assessment only as **approved/proposed and not implemented**; no
  verification claims are made for them. No implementation, provider registration,
  credential entry, cloud activity, deployment, or Git change occurred.