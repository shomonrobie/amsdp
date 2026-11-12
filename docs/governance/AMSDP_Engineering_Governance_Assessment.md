# AMSDP Engineering Governance Assessment

> **Product:** AMSDP — Appointment Management System for Doctors & Patients
> **Document:** Engineering Governance Assessment (routing & skill-selection integration)
> **Version:** 1.0.0 · **Status:** For project-owner review · **Date:** 2026-11-08
> **Authorized by:** Project-owner authorization — "Persistent Engineering Governance and Automatic Skill Routing"
> **Source rules reviewed:** `ai_factory/docs/agent-rules/` (CarbonTally agent rules, 12 files incl. MANIFEST.json)

## 1. Purpose and Scope

This assessment determines which rules in the CarbonTally agent-rules directory are applicable to
AMSDP, how each is adapted (or rejected), and how every future task will automatically trigger
governance selection, skill discovery, implementation, verification, and compliance reporting.

Scope:
- Read the complete agent-rules documents (see §2).
- Determine applicability to AMSDP; preserve AMSDP's approved business rules and architecture.
- Provide the authoritative routing detail referenced by the persistent router (`.clinerules` §4).
- Demonstrate the automatic routing mechanism on three hypothetical tasks (§8).

Out of scope: implementation of the hypothetical tasks; changes to AMSDP application source code,
database, Docker configuration, AILI, or the CarbonTally agent-rules files. Nothing committed or
pushed.

## 2. Source Rules Reviewed

All files in `ai_factory/docs/agent-rules/` were read completely (hashes recorded in the directory's
own `MANIFEST.json`):

| File | Subject | AMSDP verdict |
|---|---|---|
| `README.md` | Router + mandatory protocol + routing-table pattern | **Adopt as pattern** (AMSDP-adapted) |
| `carbontally-agent-governance.md` | Tier-1 governance: precedence, inspection, authorization, evidence | **Adopt, AMSDP-adapted** |
| `saas-application-security.md` | Authz mechanics, sessions, storage, transport | **Adopt, AMSDP-adapted** |
| `saas-auth-and-authorisation.md` | Identity, roles, capabilities, deny-by-default | **Adopt, AMSDP-adapted** |
| `saas-multitenant-data.md` | Tenant data, schema, RLS, migrations, retention | **Adopt, AMSDP-adapted** |
| `saas-frontend-ux.md` | UI/UX, a11y, responsive, states | **Adopt, AMSDP-adapted** |
| `saas-cicd-workflow.md` | CI/CD, migration release, git safety | **Adopt, scope-limited** |
| `saas-observability.md` | Logging, redaction, audit, denial recording | **Adopt, AMSDP-adapted** |
| `saas-api-throttling.md` | Rate limiting / quotas | **Reference guide (inactive surface)** |
| `emissions-provenance.md` | CarbonTally emissions domain | **N/A — CarbonTally product domain** |
| `saas-ai-provider-registry.md` | CarbonTally AI provider registry | **N/A — CarbonTally-specific** |
| `MANIFEST.json` | CarbonTally rule hashes | **N/A — not regenerated** |

**Governing principle:** these files describe CarbonTally (its tech stack, its ratified decisions, its
product domain). AMSDP applies their *general engineering rules* only where they do not contradict
AMSDP's approved Business Rules (`docs/product/AMSDP_Business_Rules_V1.0.md`), MVP scope, frozen
architecture, and verified runtime state. CarbonTally-specific requirements (Supabase/RLS mechanics,
CRA/MUI tokens, the four-plane role model, emissions/credit/registry domains) are **not** imported.

## 3. Applicability Assessment (rule-by-rule)

### 3.1 carbontally-agent-governance.md — Tier-1 governance (ADOPT, adapted)

The process rules transfer directly and form the spine of AMSDP governance:

| CarbonTally rule | AMSDP adaptation / evidence |
|---|---|
| Inspect before you change (read code, migrations, tests, decision records first) | Adopted. AMSDP keeps decision records in `docs/product/`, `docs/architecture/`, `docs/implementation/AMSDP_M*_Implementation_Report.md`. |
| Protect uncommitted work; never destructive git; check `git diff <file>` before staging | Adopted. `.clinerules` §9 banned destructive git; extended with `git revert` and pre-stage diff check. High relevance: `hackathon-mvp` carries large uncommitted milestone work. |
| Authorization boundaries ("PO DECISION REQUIRED" → record BLOCKED, state options, stop) | Adopted as AMSDP yield/ask behaviour. Raw schema changes, RBAC matrix changes, port/infra changes, and demo-data policy require project-owner authorization. |
| DB & migration safety: migration per change, forward-only, idempotent, separate authorized production apply | Adopted, mapped to AMSDP's Alembic chain (`backend/alembic/versions/`). AMSDP does **not** use CarbonTally's migration-pin tooling; the equivalent discipline is forward-only idempotent migrations, never applied ad-hoc to a running stack. |
| Testing: ALLOW and DENY cases; regression fails-before; never delete a test to pass | Adopted. Existing practice: `test_security.py`, `test_dashboard.py`, identity/queue unit tests, 20-way concurrent enqueue test. |
| Evidence labels IMPLEMENTED / TESTED / VERIFIED / ACCEPTED | Adopted verbatim as `.clinerules` §7. |
| Report what changed including what you did not | Adopted; M6 §10 "Constraints Honoured" already follows this. |
| Stop conditions | Adopted; mapped to Yield Protocol and authorization checks. |
| Non-negotiables list | Adapted: only rules true of AMSDP were kept and extended (see §4). |

### 3.2 saas-application-security.md — authz mechanics (ADOPT, adapted)

| CarbonTally control | AMSDP adaptation |
|---|---|
| Control order: primary isolation → server-side authorization → framework validation → UI presentation only | Adapted. AMSDP has **no RLS**: isolation is application-level via `backend/common/auth.py` scope checks and org/branch filtering (BR §4 strict tenant isolation, FINALIZED). AMSDP order: **server-side authorization per route → Pydantic validation / parameterised SQL → UI presentation only.** |
| The tenant comes from the principal, never the body | Adopted — AMSDP already implements (JWT-derived `organization_id`). |
| Cross-tenant → 404, not 403 | Adopted — AMSDP already implements. |
| No secrets / tokens in logs or responses | Adopted — `.clinerules` non-negotiable + M2 hardening. |
| ALLOW **and** DENY tests ship with any security change | Adopted — existing security test suite. |
| N/A: RLS policies, signed URLs, service-role, Supabase session/CSP, password hashing | Not applicable — no such surfaces in AMSDP. Do **not** invent them. |

### 3.3 saas-auth-and-authorisation.md — identity, roles, capabilities (ADOPT, adapted)

| CarbonTally principle | AMSDP adaptation |
|---|---|
| Capabilities over implied tiers; never broaden a role for convenience | Adopted with AMSDP's own matrix. Authoritative model: BR §7–8 (Super Admin, Facility Admin, Receptionist, Doctor, Assistant, View/Run) enforced by `backend/common/permissions.py`. Never infer one capability from another (receptionist is explicitly NOT granted `queue.consult`). |
| Deny by default; authorize every sensitive route server-side | Adopted — M2 work. |
| Tenant from the principal; cross-tenant non-disclosing refusal | Adopted. |
| A denied action is recorded, not swallowed | Adopted — `backend/common/audit.py` writes persistent audit events. |
| The hidden button is not authorization | Adopted — `.clinerules` non-negotiable. |
| N/A: CarbonTally four planes and seven-value staff vocabulary | Not applicable — AMSDP's 6-role model + permission matrix governs instead. |
### 3.4 saas-multitenant-data.md — schema, migrations, data integrity (ADOPT, adapted)

| CarbonTally rule | AMSDP adaptation |
|---|---|
| Consistent tenant key; never a second tenant column | Adopted — AMSDP uses `organization_id` (+ `branch_id` where scoped); no `tenant_id`. |
| Index the tenant key and common access paths `(organization_id, created_at)` | Adopted as guidance — mirror `backend/common/models.py` indexes; composite indexes follow real query shapes, never speculative. |
| Migrations: one change each, forward-only, idempotent; irreversible changes stated | Adopted — Alembic chain discipline. |
| Append-only audit preserved; retention never destroys evidence | Adopted — `audit_events` + audit helper; no purge. |
| N/A: RLS policies, subscriptions/credits/ledger, retention-admin control plane | Not applicable (no credit ledger; BR Part IX documents the subscription *model*). |

### 3.5 saas-frontend-ux.md — UI/UX, a11y, responsive (ADOPT, adapted)

| CarbonTally rule | AMSDP adaptation |
|---|---|
| Never introduce a second design system | Adopted, restated for AMSDP: one global stylesheet (`frontend/styles/global.css`) + shared components (`AppShell`, `DataTable`, `Modal`, `ConfirmDialog`, `StatusBadge`, `Alert`) + `lib/i18n.js` registry. No per-page one-off visual language. |
| Operational screens answer: where am I / what needs attention / what can I do / what happened / what next / how do I go back | Adopted — UI/UX blueprint assessment (2026-10) is the AMSDP authority. |
| Business state over implementation detail (no raw UUIDs, no status codes as prose) | Adopted. |
| Loading / empty / error / denied states, all four, truthful | Adopted. |
| Tables: pagination/sort/filter as scale demands | Adopted. |
| Accessibility bar WCAG 2.2 AA; real table semantics; keyboard-reachable controls | Adopted as the bar. |
| Responsive across a defined viewport set | Adapted: AMSDP tests the viewports it actually serves (desktop-first hackathon demo); the eight-viewport list is target guidance, not yet build-verified. |
| N/A: CRA/MUI/tokens; D19/D21 frozen decisions | Not applicable — AMSDP is Next.js Pages Router + plain CSS. |
### 3.6 saas-cicd-workflow.md — CI/CD, git safety (ADOPT, scope-limited)

- Adopted: git safety (revert not reset; no force-push; no history rewriting), never claim a CI gate that
  does not exist, secrets absent from diffs, and "if a workflow is added it must be able to fail".
- AMSDP verified state: **no GitHub workflows exist** in this repo; AMSDP's verification pipeline is the
  local Docker build + pytest + live e2e workflow performed in milestone reports. Do not describe a
  pipeline that does not exist.
- N/A surface: CarbonTally workflow files, migration-drift tooling, 90-day evidence artefacts.

### 3.7 saas-observability.md — logging, redaction, audit (ADOPT, adapted)

- Adopted: hard redaction list (passwords, JWTs, DB credentials, tokens — never in logs); an error body
  carries a code + safe message, never a stack trace; a denial is a first-class recorded signal; domain
  tables rather than a generic catch-all `logs` table; no claimed vendor pipeline (AMSDP has no
  APM/alerting pipeline).
- AMSDP mapping: `backend/common/audit.py` + `audit_events` (authoritative "who did what" record), org/branch
  stamping, actor from the JWT principal.
- N/A surface: CarbonTally log inventory and middleware specifics.

### 3.8 saas-api-throttling.md — rate limits (REFERENCE GUIDE, inactive surface)

AMSDP currently has **no rate limiter implemented**; these rules are not applicable today. Recorded as
design intent so a future limiter is not built wrong:

- a limiter is a **route dependency**, never a global middleware;
- state lives in the **database**, never an in-process counter (or worker count multiplies the allowance);
- refusal is **429 with headers**, never 500;
- the bucket key comes from the principal, never the body/query;
- health checks and provider callbacks are exempt.

### 3.9 emissions-provenance.md — N/A (CarbonTally product domain)

The emissions subject matter does not exist in AMSDP. The transferable *principle* — "no produced
figure without its provenance" — is already covered by AMSDP's audit rules (dashboard figures read live
PostgreSQL aggregates; audit events carry actor/action/org/branch). No rule is imported.

### 3.10 saas-ai-provider-registry.md — N/A (CarbonTally-specific)

AMSDP has no AI provider/model registry. AMSDP's own LLM availability routing already exists and is
authoritative: `.clinerules` §8 (local `qwen2.5-coder:1.5b` priority → Frontier escalation on complex
tasks) plus hardware constraints (4GB VRAM / 16GB RAM). Do **not** overlay CarbonTally's registry
lifecycle rules on this.

### 3.11 README.md — router pattern (ADOPT as pattern)

The router pattern is adopted: a thin always-loaded `.clinerules` carrying precedence + routing table +
non-negotiables, with detail living in deeper documents. The CarbonTally routing content itself is
replaced by the AMSDP Governance Map (§4).

## 4. AMSDP Governance Map (authoritative routing detail)

The map below is the expanded form of `.clinerules` §4. Every future task classifies into one or more
row(s); the listed documents become the mandated reads before implementation.

| Domain | Triggers | AMSDP governance to apply | AMSDP-native reference |
|---|---|---|---|
| Frontend UI | components, pages, forms, tables, dialogs, states, a11y, responsive, i18n | saas-frontend-ux (adapted §3.5); no second design system | `frontend/components/`, `frontend/styles/global.css`, `frontend/lib/i18n.js`, UI/UX assessment |
| Backend API | any endpoint read/write, validation, service logic | saas-application-security (adapted §3.2) | BR Parts II–X, `backend/common/`, M2/M4/M5 reports |
| Auth & RBAC | login, sessions, roles, permissions, scope checks | saas-auth-and-authorisation (adapted §3.3); capabilities, deny-by-default | BR §7–8, `backend/common/permissions.py`, `backend/common/auth.py` |
| Multi-tenant isolation | org/branch scoping, cross-tenant behaviour | saas-multitenant-data (adapted §3.4); tenant from principal, 404-on-cross | BR §4–6 |
| Database & migrations | schema, Alembic, indexes, seed data | saas-multitenant-data §4–5; forward-only idempotent migrations | `backend/alembic/`, `backend/common/models.py`, `backend/seed/seed_demo.py` |
| Dashboard & analytics | aggregate endpoints, metric correctness | saas-frontend-ux + saas-observability (adapted) | `backend/appointment/dashboard.py`, `frontend/pages/dashboard.js` |
| Queue & scheduling | tokens, transitions, concurrency, capacity | saas-api-throttling (concurrency intent §3.8); BR Parts V–VII | M5 report, `backend/queuing/`, `backend/scheduling/` |
| Audit & integrity | audit writes, denials, evidence trail | saas-observability (adapted §3.7); append-only | `backend/common/audit.py`, BR Part X |
| Docker & deploy | compose, ports, images, rollout | saas-cicd-workflow (adapted §3.6); honest CI/verify state | `docker-compose.yml`, service Dockerfiles, M6 constraints |
| LLM / agent tooling | agent execution, model routing, AILI | `.clinerules` §8 LLM policy | `ai_factory/docs/` architecture reports |
| Product policy | business rules, scope, role behaviour | AMSDP Business Rules (level-2 precedence) | `docs/product/` |

Conflict handling: when a domain maps to multiple rows and they disagree, the `.clinerules` §1
precedence applies; if the conflict affects business behaviour, security, or scope, stop and request
clarification. Never silently override approved AMSDP business rules.

## 5. Skills Inventory (discovered at integration time)

Discovery performed 2026-11-08 against the working tree and home-level config:

| Location | Exists? | What it holds |
|---|---|---|
| `skills/`, `.clinerules/skills/`, `.claude/skills/` (repo) | **No** | — |
| `~/.cline/*`, `~/.claude/skills` | **No skill packages** | VS Code Cline data only; no installable skills |
| `AGENTS.md` | **No** | the repo uses `.clinerules` as its constitution |
| `ai_factory/docs/` | Yes | milestone reports; **treated as knowledge base / skill material**, not executable skills |
| `docs/product/`, `docs/architecture/` | Yes | product + architecture specs (governance level-2 sources) |

**Conclusion:** no formal skill package is available to select. Per the authorization, no skills were
installed. Until a skill package is approved and present, every registered skill slot resolves to the
AMSDP governance documents in §4 — and the compliance report must state that no skill was used, rather
than claiming one. The onboarding path for future skills is defined in `AMSDP_Skill_Routing_Architecture.md`.
## 6. Precedence (integrated)

The task authorization's precedence (§5 of the authorization) is combined with AMSDP's pre-existing
precedence without losing any built-in element:

1. **System and safety constraints** — verified runtime state, hardware (4GB VRAM / 16GB RAM), host.
   Inside this level, AMSDP's verified ordering: runtime state → LLM availability routing → hardware →
   generic SaaS convention.
2. **Explicit project-owner instructions and approved AMSDP business rules** — Business Rules, MVP
   scope, frozen system design requirements.
3. **AMSDP project governance** — `.clinerules` + this assessment.
4. **Applicable engineering rules** — agent-rules files, only as adapted in §3.
5. **Selected specialized skills** — none installed; resolves to governance docs until an approved
   skill package exists.
6. **General agent defaults** — fallback SaaS convention and agent behaviour.

A rule file that contradicts levels 1–3 is **wrong for AMSDP and must be reported**, not applied
(this mirrors the CarbonTally Tier-1 rule while preserving AMSDP's own business rules).

## 7. Persistent Instruction Integration (what changed and why)

**Chosen mechanism:** the repo-root `.clinerules` file — the only instruction file guaranteed to load
for every task in this workspace. It was extended (not replaced) from 24 to 110 lines with a
self-contained routing core so future tasks trigger governance/skill selection without any extra step:

| What | Where | Result |
|---|---|---|
| Precedence hierarchy | `.clinerules` §1 | Ambiguity resolved automatically |
| Mandatory 10-step task workflow | `.clinerules` §2 | Every task routes, reads, implements, verifies, reports |
| Non-negotiables | `.clinerules` §3 | Hard rules always loaded |
| Domain → governance → skill routing table | `.clinerules` §4 | Automatic selection per task domain |
| Skills registry | `.clinerules` §5 | Honest availability + fallback rule |
| Compliance reporting requirement | `.clinerules` §6 + §9 below | Every future report carries the block |
| Evidence standard | `.clinerules` §7 | IMPLEMENTED/TESTED/VERIFIED/ACCEPTED |
| Detail documents | `.clinerules` §10 index | Depth without bloating the shim |

No other persistent instruction mechanism exists in this workspace (no `AGENTS.md`, no Cline skill
configuration found); creating a new one would have been redundant. The existing content of
`.clinerules` (LLM routing, execution boundaries, hardware safety) is preserved verbatim as §8–§9.
## 8. Validation — Routing Demonstration (three hypothetical tasks)

The routing mechanism is exercised below with three hypothetical tasks. Each trace follows
`.clinerules` §2 exactly (parse → classify → select rules → discover skills → conflict check →
implement → verify → report). **These tasks are demonstrations only and were NOT implemented.**

### Demo 1 — Build a reusable frontend component ("add an empty-state panel component")

| Step | Result of automatic routing |
|---|---|
| 1. Parse | Frontend UI / components |
| 2. Classify | Row "Frontend UI" in `.clinerules` §4 |
| 3. Select rules | `saas-frontend-ux.md` as adapted (§3.5): no second design system; four truthful states; business context; a11y |
| 4. Skill discovery | No installed skill → per §5, fall back to governance docs and **state it** |
| 5. Conflict check | Component must reuse `frontend/components/` + `global.css` + `lib/i18n.js`; no new framework (aligns with `.clinerules` §3) |
| 6. Risks | Component consistency, empty-state copy via i18n registry |
| 7–8. Implement | Build against shared components; single-file component + import in target page |
| 9. Verify | `npm run build` (if authorized) or manual page check; confirm render + a11y keyboard path |
| 10. Report | Compliance block: applied saas-frontend-ux (adapted) + AMSDP UI/UX assessment; **skill availability: none, used docs** |

### Demo 2 — Implement a secure multi-tenant backend endpoint ("list branch appointments scoped to the caller")

| Step | Result of automatic routing |
|---|---|
| 1. Parse | Backend API + multi-tenant isolation + auth/RBAC |
| 2. Classify | Rows "Backend API", "Multi-tenant isolation", "Auth & RBAC" |
| 3. Select rules | `saas-application-security.md` (adapted §3.2), `saas-auth-and-authorisation.md` (adapted §3.3), `saas-multitenant-data.md` (adapted §3.4) |
| 4. Skill discovery | None installed → governance docs; must add security ALLOW + DENY tests |
| 5. Conflict check | BR §4 strict tenant isolation + BR §7 role model govern the scope; endpoint returns 404 on cross-org, never 403; tenant from JWT not body |
| 6. Risks | Leaking existence of other orgs; missing permission for one role |
| 7–8. Implement | Route in `backend/appointment/main.py` + permission via `backend/common/permissions.py` + org/branch filter from `backend/common/auth.py` principal |
| 9. Verify | Unit + live e2e: same-org ALLOW, cross-org 404, role DENY (401/403), audit event on denial |
| 10. Report | Compliance block: applied security + auth + multitenant rules (adapted); tests passed named; skill availability: none |

### Demo 3 — Add a PostgreSQL schema migration ("add a recall-table column for patient reminders")

| Step | Result of automatic routing |
|---|---|
| 1. Parse | Database / schema change |
| 2. Classify | Row "Database & migrations" |
| 3. Select rules | `saas-multitenant-data.md` §4–5 (adapted), `saas-cicd-workflow.md` §3 (adapted) |
| 4. Skill discovery | None installed → governance docs |
| 5. Conflict check | Migration must be forward-only + idempotent Alembic revision; new column org/branch-aware or documented as shared reference; no ad-hoc ALTER; existing uncommitted work untouched |
| 6. Risks | Breaking the running stack (migrations never applied to a live demo without authorization); index shape |
| 7–8. Implement | New revision under `backend/alembic/versions/` + `common/models.py` model update |
| 9. Verify | `alembic upgrade head` on a disposable test DB (authorized); introspection of resulting column; seed/rollback sanity |
| 10. Report | Compliance block: applied multitenant-data + cicd rules (adapted); migration verified in isolated DB; skill availability: none |

All three demonstrations resolve an **empty skill slot** to governance documents and record that fact
explicitly — satisfying the "do not pretend a skill was used" requirement.

## 9. Compliance Reporting Template (mandated by `.clinerules` §6)

Every future AMSDP implementation report must include exactly this block:

```markdown
## Governance and Skill Compliance
- **Applicable governance documents (routed):** <from .clinerules §4 table; e.g.
  saas-application-security (adapted), Business Rules §8>
- **Selected skills:** <skill name, version, location> — or: none installed; resolved to
  the listed governance documents.
- **Evidence their instructions were followed:** <1–3 concrete lines: e.g. ALLOW+DENY tests,
  tenant-from-principal, append-only audit write, no second design system>
- **Tests and verification performed:** <named suites + results; live checks>
- **Deviations or exceptions:** <none | list>
- **Skills unavailable or not applicable:** <list; never silently assumed present>
```

## 10. Constraints Honoured (this integration)

- No AMSDP application source code modified.
- No database or Docker configuration changed.
- AILI untouched.
- No skills or external tools installed; installation flagged for project-owner approval.
- Nothing committed or pushed (`git status` re-checked; only the governance deliverables were added).
- All pre-existing uncommitted milestone work preserved.
- CarbonTally agent-rules files left byte-for-byte intact; no manifest regeneration.

## 11. Governance and Skill Compliance (this document)

- **Applicable governance documents (routed):** `carbontally-agent-governance.md` (Tier-1 process:
  inspect-first, evidence labels, report-what-you-did-not-do), `saas-cicd-workflow.md` (git safety,
  honest capability claims), `README.md` (router pattern), all others assessed in §3; AMSDP Business
  Rules preserved as the level-2 authority. Never applied a CarbonTally rule that contradicts AMSDP
  (per `.clinerules` §1).
- **Selected skills:** none — no skill package exists in this workspace (verified; see §5). Resolved
  to governance documents, as required.
- **Evidence instructions were followed:** this document applies the evidence standard
  (IMPLEMENTED/TESTED/VERIFIED are respected — routing traces are demonstrations, marked NOT
  implemented); non-negotiables (no secrets logged, no app source touched) hold; uncommitted work
  protected (no git operations beyond read-only status).
- **Tests and verification performed:** directory-level verification of skill absence; `git status`
  read-only confirmation that only the three governance deliverables changed (verifiable). No test
  suites were run — none were affected by documentation/routing changes.
- **Deviations or exceptions:** none material. Scope note: API throttling rules (§3.8) are recorded as
  design intent because AMSDP has no limiter to govern yet.
- **Skills unavailable or not applicable:** all skill slots (frontend, security, data, queue, dashboard,
  audit, infra, LLM) — no installed packages exist to select; emissions-provenance and
  ai-provider-registry are not applicable to AMSDP's product domain.