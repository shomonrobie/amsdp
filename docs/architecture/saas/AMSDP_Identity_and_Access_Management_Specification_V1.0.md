# AMSDP — Identity and Access Management Specification V1.0

> **Document ID:** `AMSDP_Identity_and_Access_Management_Specification`
> **Version:** V1.0 · **Revision 2 (owner decision reconciliation) — 2026-11-17** · **Branch:** `hackathon-mvp` @ `409a929`
> **Status:** **SPECIFICATION — DECISION-RECONCILED, NOT IMPLEMENTED.** The sixteen `O-SaaS` items and
> the four directions A1–A4 were decided by the Product Owner on 2026-11-17 (architecture
> specification §1.5). This document applies those rulings. Model decisions are `OWNER-APPROVED`;
> every mechanism here remains `SPECIFIED` and unbuilt. Nothing here authorises implementation.
> **Evidence base:** `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` §4 (identity as built) — every
> "today" statement below is sourced there, not re-derived.
> **Companion documents:** architecture specification (planes, pipeline, ADRs), tenant &
> organization specification, subscription & entitlement specification, implementation roadmap.
> **No code, schema, migration, compose or frontend file was changed to produce it.**

---

## 1. Purpose and scope

### 1.1 What this document specifies

Who a principal is, how it proves that, how long the proof lasts, how it is withdrawn, and how
authority is decided — for **two distinct principal domains**:

1. **Tenant principals** — clinic staff, today's only kind (`staff_users`).
2. **Platform principals** — the operator who administers tenants, plans and subscriptions.
   These do not exist today as a domain; only a capability does (audit §4.5).

### 1.2 Authority order

| Rank | Source |
|---|---|
| 1 | `.clinerules` §3 non-negotiables (server-side enforcement, no secrets, audited denials, `404` on cross-tenant) |
| 2 | `AMSDP_Business_Rules_V1.1.md` §7–§8 (roles, permissions), §39 (suspension must take effect), §40 (audit), §42 (security, secrets, session handling) |
| 3 | `AMSDP_Master_Feature_List_V2.5` §5.1 (platform governance scope), §19.1–§19.3 (role/permission model) |
| 4 | Owner decision **Q-1** (`docs/decisions/AMSDP_Owner_Decisions_Q1_Q6_V1.0.md`): enumerated platform capabilities, no wildcard |
| 5 | Owner decision packet **2026-11-17** — `O-SaaS-1…16` and A1–A4 (architecture specification §1.5, §12, §14.3) |
| 6 | This document: mechanisms `SPECIFIED` |

### 1.3 Status labels

The two-axis vocabulary of architecture specification §1.3 governs here unchanged: the **decision
axis** (`OWNER-APPROVED` / `SPECIFIED` / `OPEN` / `DEFERRED` / `FORBIDDEN` / `SUPERSEDED`) and the
**evidence axis** (`NOT IMPLEMENTED` / `IMPLEMENTED` / `TESTED` / `VERIFIED`). `PROPOSED` is retained
as the exact synonym of `SPECIFIED`. An agent may implement an `OWNER-APPROVED` item once it is
scheduled *and* its mechanism is written and tested; a decision never implies working code.

### 1.4 The three failures this document exists to prevent

| Failure | Why it is fatal here | Where addressed |
|---|---|---|
| **A credential outlives the authority behind it** | suspending a tenant or offboarding a user must take effect on the **next request**, not after a 12-hour token expires (BR §39) | §4.3 revocation, §4.5 session model |
| **A tenant role becomes a platform role** | one rename turns every clinic administrator into a platform administrator (audit K-3) | §7 platform identity, §7.4 rename plan |
| **A platform role becomes clinical access** | `platform.cross_org` today reaches patient data (audit C-9), against V2.5 §5.1 | §7.3 capability split |

---

## 2. Identity as built (baseline)

### 2.1 The principal

| Property | Today | Evidence |
|---|---|---|
| Table | `staff_users` | `common/models.py` |
| Shape | one row = one login = one organization = at most one branch | `organization_id` NOT NULL, `branch_id` NULLABLE |
| Roles | `super_admin`, `org_admin`, `branch_admin`, `receptionist`, `doctor`, `assistant` | `common/permissions.py` |
| Status | `active` / other; non-active rejected at login and on every request | `identity/main.py:207`, `common/auth.py:142` |
| Membership | none — cross-organization membership is impossible | audit §4.1 |
| Password | bcrypt hash, no policy, no reset path | `identity/main.py:205` |

> **Revision 2 note.** Lines 63–67 describe the tree **as built** and are kept verbatim as baseline
> evidence. The approved target is **multi-membership** (O-SaaS-7, ADR-SAAS-014): `staff_users`
> becomes the global identity and `organization_memberships` carries the per-tenant role. Read §8.1
> for the target; nothing in this table is yet `IMPLEMENTED` differently.

### 2.2 The token

| Property | Today |
|---|---|
| Algorithm | HS256, one symmetric secret for all services |
| Claims | `sub`, `org`, `branch`, `role`, `exp` |
| TTL | 12 h fixed, no refresh |
| Revocation | none (no JTI, no session row, no `token_version`) |
| Logout | client discards the token only |
| Reset | absent |
| Throttle | DB-backed per (IP, username), success clears, **no lockout by design** |
| Secret guard | `AMSDP_JWT_SECRET` required outside `development`; **`AMSDP_ENV` unset ⇒ dev constant** (audit R-10) |

### 2.3 What is already good and must not regress

1. **The principal is re-read on every request.** `get_current_user` queries `staff_users` and
   rejects a non-active account, so a deactivated user is locked out immediately even though the
   token is still cryptographically valid. The revocation gap is therefore narrower than it
   looks: it applies to **role changes, password changes and tenant suspension**, not to account
   disablement.
2. **Denials are audited** (`common/denial_audit.py`, 403/404/422 → `audit_events`).
3. **No wildcard.** Q-1 replaced `"*"` with an enumerated matrix; an unknown permission is denied
   to every role, `super_admin` included (`tests/test_platform_admin.py`).
4. **Throttling is stateful and shared** (`login_attempts`), so it works identically on every
   replica — the correct pattern for anything added later.

---

## 3. Principal model

### 3.1 Principal types

| Type | Authenticates | Tenant key | Domain | Status |
|---|---|---|---|---|
| `tenant_staff` | password → tenant token | the membership the token names (today `staff_users.organization_id`, NOT NULL) | today, unchanged in shape | `OWNER-APPROVED` (existing behaviour); membership shape `SPECIFIED` (§8.1) |
| `platform_operator` | password → short-lived platform token | **none** — no organization, no branch | new `platform_users` | `OWNER-APPROVED` model (O-SaaS-1, ADR-SAAS-003); table `SPECIFIED` |
| `patient` | opaque tracking token, no login | resolved by the token pepper | public endpoint path only | `OWNER-APPROVED`; explicitly **not** a principal — it never receives an `AuthContext` |

The important line: a principal is something that can *hold authority*. A patient tracking token
carries a reference, not authority, and must never be accepted by `require_permission`.
This document does not change the tracking-token scheme (`common/tracking_tokens.py`).

### 3.2 Target claim set

| Claim | Present today | Target | Why |
|---|---|---|---|
| `sub` | yes | yes | principal id (`staff_users.id` or `platform_users.id`) |
| `org` | yes | yes (tenant only) | the tenant key; derived from the principal row, never from input |
| `branch` | yes | yes (tenant only) | nullable branch scope |
| `role` | yes | yes | role **name**; authority is still resolved from the server-side matrix, never from the claim alone |
| `scope` | **no** | `tenant` \| `platform` | rejects a tenant token at the platform plane and vice versa — the plane boundary that does not exist today (audit T-4) |
| `ver` | **no** | integer, mirrors `staff_users.token_version` | revokes every outstanding token of a principal with one UPDATE |
| `jti` | **no** | opaque id | names a session for revocation and audit |
| `iat`, `exp` | `exp` only | both | observability of session age |
| `org_status` | **no** | **never** | a claim must never carry lifecycle state — it would be stale the moment a tenant is suspended |

### 3.3 Invariants

| # | Invariant | Enforcement |
|---|---|---|
| P-1 | Every authenticated request re-reads the principal row; a token alone is never sufficient | existing `get_current_user`, kept |
| P-2 | `org`/`branch` always come from the verified token, never from a request body or query | existing `AuthContext` |
| P-3 | Authority is `permissions.check(permission, role)` **and** status **and** scope **and** tenant match. No single check is sufficient | §9 |
| P-4 | A platform principal has no `org`, and a tenant principal can never acquire `scope=platform` | token minting per plane (§7.2) |
| P-5 | No role string implies cross-tenant reach; only an enumerated capability does | Q-1, `common/permissions.py:30-35` |
| P-6 | Lifecycle and entitlement state are resolved **per request from data**, never embedded in a token | architecture spec §5.2, ADR-SAAS-006 |
| P-7 | A password change, role change, status change or explicit logout invalidates outstanding tokens at the next request | `ver` + `jti` (§4.5) |
| P-8 | No credential, secret or token value is ever logged, returned in an error, or written to `audit_events` | `.clinerules` §3 |

### 3.4 The `AuthContext` contract (additive only)

`AuthContext` gains three fields and keeps every existing one, so no router signature changes:

```text
principal_id : str          # was user_id
scope        : "tenant" | "platform"
role         : str
organization_id : Optional[str]   # None only for scope="platform"
branch_id    : Optional[str]
can_cross_org : bool        # preserved; now true only for a platform principal
```

---

## 4. Authentication, sessions and revocation

### 4.1 Login (tenant)

Unchanged in shape: `POST /api/v1/auth/login` → bcrypt verify → re-read row → status check →
token. Additions, all server-side:

| # | Addition | Status |
|---|---|---|
| A-1 | reject login when the **organization** is not `active` (today only the user's status is checked) — audit R-03 / G-2 | `SPECIFIED` |
| A-2 | the throttle records a counter even when the username does not exist, so response time and audit volume do not reveal account existence | `SPECIFIED` |
| A-3 | a failed login is written to `audit_events` as `identity.login_failed` **without** the attempted password or a token | `SPECIFIED` |

No account lockout is introduced: it remains an owner-approved non-control (audit §11, item 4).

### 4.2 Token lifetime

| Token | Today | Target | Rationale |
|---|---|---|---|
| tenant access | 12 h, no refresh | **60 min** | short enough that a leaked token decays; long enough that a clinic shift does not re-login |
| tenant refresh | none | **12 h absolute**, single-use, rotated per use | keeps the old 12 h ceiling as an *absolute* session bound rather than a per-token one |
| platform access | — | **30 min**, **no refresh** | platform actions are rare; re-authentication is cheap and materially safer |
| clock skew | — | 30 s leeway | avoids spurious 401s across containers |

The `scope` claim, not a second secret, is the primary plane discriminator. Two secrets alone
would silently produce `401` instead of `404`, a worse failure mode (§9.2).

### 4.3 Revocation — the mechanism that makes BR §39 real

Revocation must not add a token-store lookup to the hot path. It reuses the row read that
**already happens** on every request:

1. `staff_users.token_version` (integer, default 1).
2. A token carries `ver`; `get_current_user` compares it to the row. A mismatch is `401` with
   reason `token_revoked`, audited as `identity.token_revoked`.
3. Bumping `token_version` is the single revocation primitive. It fires on: password change,
   role change, branch reassignment, deactivation, "log out everywhere", and **tenant
   suspension** (bulk bump across the organization).
4. `staff_sessions` (new table) stores refresh-token hashes and `jti`s; it is authoritative for
   refresh and logout-by-session, not for access tokens.

Hot-path cost stays one indexed `SELECT` by primary key — identical to today.

### 4.4 Refresh and reuse detection

| Rule | Behaviour |
|---|---|
| single use | presenting a refresh token rotates it; the old hash is marked consumed |
| reuse | presenting a consumed refresh token revokes the **entire family** (every session of that principal) and audits `identity.refresh_reuse_detected` |
| absolute bound | a session cannot be extended past 12 h from first login, even if continuously refreshed |
| storage | `sha256(pepper || token)`, never the token itself |

### 4.5 Logout

`POST /api/v1/auth/logout` marks the `jti` consumed and, when `all=true` (re-authenticating with
the current password), bumps `token_version`. Client-side token discard stays supported but is no
longer the only mechanism — today it is the only one.

### 4.6 Password policy (BR §42)

| Rule | Value | Status |
|---|---|---|
| minimum length | 12 characters | `SPECIFIED` |
| composition rules | none (length beats symbols, and complexity rules push users to reuse) | `SPECIFIED` |
| rejected | the password equal to the username, the organization slug, or one of a bundled small list of common passwords | `SPECIFIED` |
| hashing | bcrypt, cost unchanged from today | `OWNER-APPROVED` (existing, BR §42) |
| reuse | last 3 hashes retained in `staff_password_history`, compared on change | `DEFERRED` (nice-to-have, not launch-blocking) |
| transport | password only ever in the request body over TLS; never in a URL, log line or audit row | `OWNER-APPROVED` (BR §42) |

---

## 5. Secrets and key management

### 5.1 Where each secret lives

| Secret | Source | Consumers | Status |
|---|---|---|---|
| `AMSDP_JWT_SECRET` (tenant plane) | environment / deployment secret store | identity mints; all services verify | `OWNER-APPROVED` (exists) |
| `AMSDP_JWT_SECRET_PLATFORM` (platform plane) | environment / deployment secret store | platform service only | `SPECIFIED` |
| `AMSDP_TRACKING_PEPPER` | environment; already fail-closed outside development | public tracking endpoints | `OWNER-APPROVED` (exists) |
| `AMSDP_SESSION_PEPPER` | environment | refresh-token hashing | `SPECIFIED` |
| `POSTGRES_PASSWORD` | `.env`, never a compose literal | database + every service DSN | `OWNER-APPROVED` (deployment convention) |

### 5.2 The fail-closed rule (fixes audit R-10 / C-8)

Today's guard is:

```text
secret missing → AMSDP_ENV defaults to "development" → dev constant, no error
```

Correct behaviour:

| Condition | Behaviour |
|---|---|
| `AMSDP_ENV` unset | **startup failure**: the environment is not declared, so it cannot be assumed to be development |
| `AMSDP_ENV=development` and no secret | dev constant, but a **single WARNING line at startup** naming the fallback |
| `AMSDP_ENV` set to anything else and no secret | startup failure, unchanged |
| `AMSDP_ALLOW_DEV_SECRET=1` | explicit opt-in for CI sandboxes that legitimately test the fallback; never set in a deployment manifest |

`common/auth.py` and `identity/models.py` both hold a copy of this guard. They must be collapsed
into **one** helper (`common/secrets.py`) so the rule cannot drift between the minting and
verifying sides — today it is duplicated, which is how one copy can be fixed and the other
forgotten.

### 5.3 Rotation

| Step | Tenant plane | Platform plane |
|---|---|---|
| 1 | deploy `AMSDP_JWT_SECRET_PREVIOUS` = current value, new `AMSDP_JWT_SECRET` | same shape, `..._PLATFORM_PREVIOUS` |
| 2 | verifiers accept both, **mint with the new key only** | same |
| 3 | wait one access-token lifetime (60 min; 30 min platform) plus skew | same |
| 4 | remove `_PREVIOUS` | same |

Dual-key acceptance exists only during the rotation window and is removed within one TTL. A
rotation is an audited platform action (`platform.secret_rotated`, no key material in the row).

### 5.4 Absolute prohibitions

1. No secret in source, a compose literal, a Dockerfile, a test fixture or a JWT payload.
2. No secret or token in any log line, exception message, HTTP error body or `audit_events` row.
3. No secret echoed by a `/health` endpoint — health reports liveness, not configuration.
4. No "temporary" operator password in documentation; owner-run provisioning generates it
   (§7.5).

---

## 6. Password reset and account recovery

### 6.1 What exists

Nothing. There is no reset endpoint, no token table, no email path. A locked-out user today has
only a database edit, which is unaudited and therefore unacceptable as a documented procedure.

### 6.2 V1 — operator-assisted reset (no mailer dependency)

The platform has **no deployed mail transport** (notifications are a later milestone; the
architecture spec §4 lists the notification worker as a Phase 4 prerequisite). A reset flow that
assumes e-mail would be documentation for a capability that cannot run.

| Step | Actor | Behaviour |
|---|---|---|
| 1 | `org_admin` (own org) or `platform_admin` (any org) | `POST /api/v1/{orgs/{id}/staff/{staff_id}/reset-password}` → server generates a 24-character single-use code, stores only `sha256`, expires in **30 min** |
| 2 | operator | delivers the code to the user **out of band** (phone/in person); the API returns it exactly once, in the response to the authenticated administrator |
| 3 | user | `POST /api/v1/auth/reset-password` with `{username, code, new_password}` → policy check → bcrypt → `token_version` bump |
| 4 | audit | `identity.password_reset_requested`, `identity.password_reset_completed`, actor + target, never the code |

Guard rails: a reset code is invalidated by a second request; five failed attempts consume it; a
`platform_admin` reset additionally requires the tenant's `lifecycle_state` to be reachable for
support and is audited into the tenant's trail (ADR-SAAS-009 pending). A tenant administrator can
never reset a platform operator's credential — the domains have no shared table.

### 6.3 V2 — self-service (deferred, gated)

`DEFERRED` until the notification worker exists and the project owner approves an e-mail provider
(the roadmap treats this as a Phase 4 item, not a launch blocker). When it lands it reuses the
same code table, the same policy function and the same audit actions; only the delivery channel
and an enumeration-neutral response (`202` regardless of whether the username exists) change.

### 6.4 Recovery invariants

| # | Invariant |
|---|---|
| PR-1 | A reset never reveals whether a username exists to an unauthenticated caller |
| PR-2 | A reset code is single-use, short-lived, stored hashed, and never logged |
| PR-3 | A completed reset bumps `token_version`, so every existing session dies at the next request |
| PR-4 | No human "looks up" or types a password hash; support staff can only trigger a reset |

---

## 7. Platform identity domain

### 7.1 Why a separate domain, not a role flag

A flag on `staff_users` would mean every platform operator is also **some tenant's employee**: it
inherits that tenant's data as a normal user, cannot be offboarded without touching a tenant's
staff list, and cannot be counted as a distinct population in an audit. Three properties are
required that a flag cannot give:

| Requirement | Why a flag fails |
|---|---|
| The operator has no tenant | `staff_users.organization_id` is NOT NULL |
| Platform tokens are rejected by tenant endpoints and vice versa | a claim the tenant table has no concept of |
| A tenant administrator cannot create, list, or reset a platform operator | one shared table means one shared admin surface |

### 7.2 The `platform_users` table (ADR-SAAS-003)

| Column | Type | Notes |
|---|---|---|
| `id` | text PK | `plt_` prefix |
| `username` | text unique | globally unique, not per-tenant |
| `password_hash` | text | bcrypt, same cost |
| `role` | text | `platform_admin` \| `platform_ops` \| `platform_support` |
| `status` | text | `active` \| `disabled` |
| `token_version` | integer | default 1; same revocation primitive |
| `created_at`, `updated_at` | timestamptz | |
| `last_login_at` | timestamptz | nullable |

Deliberately **absent**: `organization_id`, `branch_id`. The absent column is the security
property. A partial unique index is not needed; username uniqueness alone is correct because the
table is global.

Login: `POST /api/v1/platform/auth/login` → throttle (reusing `login_attempts`, keyed with a
`platform:` prefix so the two planes cannot exhaust each other's budget) → bcrypt → mint a token
with `scope=platform`, `role`, `ver`, `jti`, 30-minute expiry, **no** `org`/`branch`. There is no
refresh; the operator re-authenticates.

Verification: `get_platform_principal` accepts only `scope=platform` **and** verifies with
`AMSDP_JWT_SECRET_PLATFORM`. A tenant token presented to a platform endpoint — or a platform token
presented to a tenant endpoint — is **`401` with machine code `WRONG_PLANE`**, matching the
architecture specification §5.1 step 5 and §5.2. It is not a `403`: the caller is not
under-privileged, the credential is simply for the other plane, and treating it as a permission
failure would invite a future reviewer to "fix" it by widening the matrix. The rejection is
written to the log stream (no verified tenant exists yet, so no `audit_events` row is possible —
audit §11, item 2; ADR-SAAS-009).

### 7.3 Role map and the capability split (fixes audit C-9)

`platform.cross_org` is **retired** and replaced by capabilities that name what they reach:

| Capability | `platform_admin` | `platform_ops` | `platform_support` | Reaches |
|---|---|---|---|---|
| `platform.tenant.read` | yes | yes | yes | tenant **metadata**: name, status, plan, counts, timestamps |
| `platform.tenant.manage` | yes | yes | no | create, suspend, reactivate, change plan |
| `platform.plan.manage` | yes | no | no | plan definitions and limits |
| `platform.subscription.manage` | yes | yes | no | per-tenant subscription rows |
| `platform.usage.read` | yes | yes | yes | usage counters, never clinical content |
| `platform.audit.read` | yes | yes | no | audit trail reads |
| `platform.operator.manage` | yes | no | no | create/disable operators, rotate their credentials |
| `platform.support.grant` | no | no | no | **nobody** — see below |

Clinical content is not reachable through any platform capability. It is reachable only through a
**support grant** (`platform_support_grants`), which is:

1. requested by a `platform_support` operator for one organization, one module, one purpose text;
2. valid **max 60 minutes**, auto-expiring, single-organization, single-operator;
3. accepted by the tenant's `org_admin` (or pre-approved by policy for `lifecycle_state=grace`);
4. while active, every response carries a `X-AMSDP-Support-Access` header and the tenant sees a
   banner;
5. fully audited in the **tenant's** trail at grant, use and expiry.

That is the mechanism `.clinerules` and V2.5 §5.1 require, and it is the only path from the
platform plane to patient data.

### 7.4 Renaming `super_admin` (audit C-4) — staged, reversible

The tenant role `super_admin` is today the only holder of `platform.admin` /
`platform.cross_org`. Once §7.2 exists, keeping that name guarantees a permanent misreading, so
it is renamed in three stages:

| Stage | Change | Compatibility | Reversible |
|---|---|---|---|
| R-1 | add `org_super_admin` to `PERMISSIONS` as a **copy** of today's `super_admin` entry, minus the two `platform.*` capabilities | existing tokens and rows untouched | yes — delete the entry |
| R-2 | mint `org_super_admin` for new users; migrate `staff_users.role` in a forward-only migration; `super_admin` remains accepted as an alias in `check()` for one release | old tokens keep working; `super_admin` no longer holds platform capabilities | yes — re-add the capability list |
| R-3 | remove the `super_admin` alias and the `platform.*` grants from the tenant matrix entirely | requires no live token older than one access TTL; gate on a clean token-age check | **no** — a one-way door, hence last |

**O-SaaS-1 decided this on 2026-11-17**: separate platform identity is approved, and removing the
alias and its `platform.*` grants is approved **subject to safety** — R-1 and R-2 land first, and R-3
only once the replacement is `TESTED` and `VERIFIED` and no live token is older than one access TTL.
Until then `super_admin` retains its present capabilities exactly as they are: no privilege is
withdrawn by documentation, and no agent may run R-3 on the strength of an approval alone.

### 7.5 Bootstrapping the first operator

No seed inserts a platform operator, and none may: the demo seed is a tenant-plane artefact.
Provisioning is an owner-run command:

```text
python -m backend.platform.admin create-operator --username <name> --role platform_admin
```

It reads the password from stdin (never an argument, so it never reaches shell history), prints the
operator id once, and audits `platform.operator_created`. It refuses to run if
`AMSDP_ENV=development` and the database already contains an operator (idempotence guard) — the
first operator is a production act.

### 7.6 What the platform plane must never do

| # | Prohibition | Reason |
|---|---|---|
| PP-1 | create, read or reset a **tenant** staff credential | two admin surfaces must stay disjoint; tenant onboarding is tenant-led |
| PP-2 | read patient, appointment, queue or clinical content without a support grant | V2.5 §5.1, audit C-9 |
| PP-3 | be granted by a tenant administrator | a tenant cannot manufacture platform authority |
| PP-4 | authenticate with a tenant token, or accept one on any platform endpoint | plane confusion is the highest-severity escalation path (H-3) |
| PP-5 | exist in the demo seed or any fixture used by tenant tests | a fixture operator becomes a production default |

---

## 8. Membership and staff lifecycle

### 8.1 Model: multi-membership (ADR-SAAS-014, `OWNER-APPROVED`)

**Revision 2 change.** V1.0 specified one organization per identity and recorded the join-table
option as `OPEN` (ADR-SAAS-013). **O-SaaS-7 rejected that**: a clinician working at two institutions
must not need two accounts. ADR-SAAS-013 is `SUPERSEDED` by ADR-SAAS-014; the model is now:

- one human identity (`staff_users`) is **global** — it is the person, and it no longer carries the
  tenant as its identity;
- `organization_memberships` carries, per organization, the `role`, `permissions`/`branch_scope` and
  membership status;
- an access token names **exactly one** active organization and one membership; the role applied at
  authorisation is the role **held in that membership**, never a union across memberships;
- switching organization is an explicit, authorised act that mints a fresh token (architecture
  spec §5.1); no request may name its own tenant.

| Question | Ruling / owner |
|---|---|
| Which model | **multi-membership** — `OWNER-APPROVED` (O-SaaS-7) |
| Physical shape, backfill and cutover of `staff_users.organization_id` | `EQ-1` (architecture spec §14.3.1) — engineering, forward-only, no data loss |
| How the active organization travels | `EQ-2` — engineering; the constraint is that a revoked membership fails on the **next request** |
| Membership lifecycle and effective permissions | `EQ-3` — engineering; least privilege per tenant, no cross-membership union |

What does **not** change: `organization_id` remains the only tenant key, every tenant table still
carries exactly one `organization_id`, and a cross-tenant read still fails `404`. A
single-organization deployment (P2/P3) is simply the case where every identity holds one membership.

### 8.1.1 Why the superseded model was replaced, not deleted

The V1.0 concern — a principal with a *selectable* tenant is the shape most multi-tenant breaches
take — remains valid. It is answered by making the selection an **authorised** act (§4.3 revocation,
architecture spec §5.1 step 6) rather than a client-supplied value, not by pretending the concern
went away. The superseded reasoning is preserved verbatim in architecture specification §12.1.

### 8.2 Tenant-managed staff lifecycle

| Action | Actor | Effect | Guard |
|---|---|---|---|
| create | `org_admin` / `branch_admin` (own branch) | row + bcrypt hash + `token_version=1` | org from token; branch must belong to that org; role must not be `super_admin` |
| change role | `org_admin` | new role, `token_version` bumped | cannot grant a role above one's own; cannot change own role (self-escalation) |
| reassign branch | `org_admin` | `branch_id` change, version bumped | target branch must be in the same org |
| deactivate | `org_admin` | `status=inactive`, version bumped | cannot deactivate the last active `org_admin` of an org |
| read | `staff.read` | own org only | never returns a hash |

Both a role change and a deactivation take effect on the **next request** — that is the practical
value of §4.3, and the reason the revoke test in the roadmap is non-negotiable.

### 8.3 What the tenant plane must never do

| # | Prohibition |
|---|---|
| TP-1 | create, read, reset or enumerate a platform operator |
| TP-2 | hold a platform capability through any tenant role, tenant `config` or request body |

---

## 9. Authorisation composition

### 9.1 The single decision function

Every protected endpoint resolves authority through one chain. It is deliberately **additive** to
today's `require_org_access`: the tenant gate cannot be skipped, and no new factor can *grant*
access that the tenant gate would refuse.

| # | Factor | Source | Failure |
|---|---|---|---|
| 1 | token valid and unexpired | signature + `exp` | `401` |
| 2 | plane matches the route | `scope` claim | `401 WRONG_PLANE` |
| 3 | principal exists and is active | principal row (re-read) | `401` |
| 4 | token version current | `ver` vs `token_version` | `401 TOKEN_REVOKED` |
| 5 | tenant/branch scope | token vs path, `platform.cross_org` retired (§7.3) | `404` |
| 6 | lifecycle permits the method | `organizations.lifecycle_state` | `403 TENANT_*` |
| 7 | role holds the permission | `permissions.check` | `403` |
| 8 | module entitled (module-gated routes only) | entitlement resolver | `403 MODULE_NOT_ENTITLED` |
| 9 | resource belongs to the tenant | query is org-scoped | `404` |

Factors 5–8 mirror architecture specification §5.1 steps 6–9 and are **not** re-ordered here; that
document is authoritative on order. Factor 9 is not a pipeline step at all — it is the query-level
guarantee inside the handler (step 10): every read and write filters on the token's organization, so a
correctly-scoped path with a foreign id still yields `404`.

Factors 1–4 correspond to architecture steps 2–5 (signature/expiry, principal type, principal
resolve, plane match): they are split here because step 2 of that document is two checks
(signature then `exp`) and because revocation is a factor that document delegates to this one. Their
internal order is immaterial for security — every outcome in the block is `401`, so no ordering inside
it can leak whether a tenant or a resource exists.

### 9.2 Why the order is a security property, not a style preference

- **Scope before lifecycle before entitlement.** A lifecycle or entitlement check that runs before
  the tenant check turns the platform into an existence oracle: `403 TENANT_SUSPENDED` for a real
  tenant versus `404` for a nonexistent one reveals which organizations exist.
- **Revocation before permission.** A revoked token must not be able to reach the permission
  matrix at all, so a stale role cannot be evaluated.
- **No factor is sufficient alone.** A valid token with a correct role in a suspended tenant is
  denied; a suspended tenant with a platform `platform_admin` is not reachable except through the
  metadata surface, which lifecycle still gates.
- **The endpoint is the boundary.** Hiding a control in the frontend changes nothing (V2.5 §30.1);
  the frontend consumes a capabilities payload that *reflects* the server's decision and never
  makes one.

### 9.3 Capability discovery for the frontend

`GET /api/v1/auth/me` (tenant) and `GET /api/v1/platform/auth/me` (platform) return:

| Field | Content |
|---|---|
| `principal` | id, username, role, org, branch |
| `capabilities` | the effective permission strings for this role |
| `modules` | entitled module keys for the tenant |
| `lifecycle_state` | current state (so the UI can render the correct banner) |
| `support_access` | active support grant id + expiry, if any |

The frontend must render navigation from `modules` ∪ `capabilities` and must still show the server's
`403`/`404` verbatim when a cached capability is stale. A cached capability is a hint, never a
grant.

---

## 10. Audit and evidence for identity events

### 10.1 Event vocabulary (additive to `common/audit.py`)

| Action | Actor | Target |
|---|---|---|
| `identity.login_succeeded` / `identity.login_failed` | username | principal |
| `identity.logout` / `identity.token_revoked` | principal | principal |
| `identity.password_changed` / `identity.password_reset_requested` / `identity.password_reset_completed` | actor | principal |
| `identity.refresh_reuse_detected` | principal | principal |
| `identity.role_changed` | org admin | principal + `before`/`after` role |
| `platform.operator_created` / `platform.operator_disabled` | platform admin | operator |
| `platform.login_succeeded` / `platform.login_failed` | username | operator |
| `platform.support_grant_requested` / `_accepted` / `_used` / `_expired` | operator + tenant acceptor | grant + org |

### 10.2 Rules

1. **Never** log a password, hash, token, reset code, secret or `jti` value.
2. Identity events for a tenant principal are written to that tenant's trail; the tenant owns its
   access history.
3. Platform-operator events have no tenant, which is exactly the gap in `audit_events`
   (`organization_id` NOT NULL, audit C-7). Until ADR-SAAS-009 is ruled on, those events are
   written to the structured log **and** to the tenant trail when a tenant is the target; the
   platform-plane trail is an open item, not an assumption.
4. A denial is never swallowed: `403`/`404`/`422` continue to be recorded by
   `common/denial_audit.py`, unchanged.

---

## 11. Threat model (identity-specific)

Architecture specification §9 covers the platform-wide model (T-1…T-12); this table covers the
identity mechanisms this document introduces. `H-n` ids are the ones referenced there.

| # | Threat | Control | Residual |
|---|---|---|---|
| H-1 | Stolen tenant token replayed for its remaining lifetime | 60 min access TTL, `ver` revocation, revocation on password/role/status change | ≤ 60 min of stolen-token value; unavoidable without per-request token introspection |
| H-2 | Offboarded employee keeps working until the token expires | `token_version` bump on deactivation; principal row re-read each request | none on the next request |
| H-3 | Tenant token used to reach the platform plane | `scope` claim + separate secret + `401 WRONG_PLANE` | none, given both checks; a single missing check is a total breach, hence the test is mandatory |
| H-4 | A tenant administrator manufactures a platform operator | separate table, separate service, separate route namespace, `platform.operator.manage` only | none by construction; tenant has no write path |
| H-5 | Privilege escalation by editing one's own row | role change requires `org_admin`, cannot grant above one's own role, cannot change self | a compromised `org_admin` is still an `org_admin` |
| H-6 | Platform operator reads clinical content silently | no clinical capability (§7.3); support grant requires tenant acceptance, 60 min, visible banner, audited | a rogue `platform_support` can still read **the tenant that accepted** — which is the point of consent |
| H-7 | Refresh-token theft and silent prolongation | single-use rotation + family revocation + 12 h absolute bound | attacker and victim race; first reuse revokes both, visible as a logout |
| H-8 | Password guessing | bcrypt cost, DB-backed throttle, no user enumeration (§4.1 A-2) | no lockout (approved), so slow guessing is bounded only by throttling |
| H-9 | Reset-code interception | 30 min TTL, single use, hashed at rest, delivered out of band by an authenticated admin | operator channel is out of the system's control; documented, not pretended |
| H-10 | Signing key exfiltration via source or logs | fail-closed guard (§5.2), rotation with dual keys (§5.3), no key in any log/audit/response | key custody belongs to the deployment target (roadmap Phase 3 gate) |
| H-11 | JWT forgery via the dev constant deployed by mistake | `AMSDP_ENV` must be declared (§5.2); startup fails otherwise; CI asserts the guard | one misconfigured host that sets `AMSDP_ENV=development` alongside a public secret |
| H-12 | Identity event tampering to hide an intrusion | append-only audit by convention; Phase 1 adds the DB-level constraint | **open weakness** today — recorded, not glossed |

### 11.1 What this document does **not** defend against

Insider database access, a compromised container image, TLS termination compromise and
supply-chain attacks are deployment concerns. They are named here so that no reader concludes the
identity layer is a complete security boundary.

---

## 12. Migration, compatibility and rollback

### 12.1 Shape of the change

All of it is additive, and every step is forward-only (`.clinerules` §3):

| Change | Type | Reversible without data loss |
|---|---|---|
| `staff_users.token_version`, `session_epoch` | new columns, default 1 | yes |
| `staff_sessions` | new table | yes (drop if unused) |
| `staff_password_history` | new table (`DEFERRED`) | yes |
| `password_reset_codes` | new table | yes |
| `platform_users` | new table | yes |
| `platform_support_grants` | new table | yes |
| `org_super_admin` role | matrix entry + data backfill (R-2) | yes until R-3 |
| `scope`/`ver`/`jti` claims | token format | **yes, with care**: tokens minted before the change carry no `scope`; verifiers treat a missing `scope` as `tenant` for one access TTL only |

### 12.2 Rolling-deploy compatibility

1. Deploy verifiers first (they accept tokens with and without `scope`/`ver`), then the minter.
2. `ver` defaults to 1, and a missing `ver` is treated as 1 — so no session is invalidated by the
   deployment itself.
3. Once every service runs the new verifier, the compatibility shim is removed in a later release;
   the removal is a code change, not a migration, and is gated on the TTL having elapsed.
4. `platform_users` and its routes ship dark: deployed but unreachable until the roadmap's Phase 2
   flag is enabled by the owner.

### 12.3 Tests that must accompany the change (roadmap gates)

| Test | Asserts |
|---|---|
| `test_revocation_next_request` | bump `token_version` → the same token is `401` on the very next call |
| `test_wrong_plane_rejected` | tenant token on a platform route → `401 WRONG_PLANE`; platform token on a tenant route → `401` |
| `test_tenant_cannot_manage_platform_operator` | `org_admin` on every platform route → `404`/`401`, never `200` |
| `test_super_admin_alias_window` | during R-2, `super_admin` tokens still authenticate but hold no `platform.*` |
| `test_secret_guard_fails_closed` | `AMSDP_ENV` unset + no secret → `RuntimeError` at import |

---

## 13. Owner decisions applied (registry: architecture spec §14.3)

Ids are the **canonical registry** in the architecture specification §14.3; this document mints no
local ids (an earlier draft did, and that duplication caused the renumber). **All of these were
decided by the Product Owner on 2026-11-17**; each row now records what this document must do about
the ruling, not a question.

| ID | Ruling applied here | Effect on this document |
|---|---|---|
| O-SaaS-1 | Separate platform identity approved; `super_admin` alias/grants removed only after the replacement is tested | §7.2–§7.4 proceed; R-3 is last and conditional |
| O-SaaS-2 | Platform-only events → `platform_audit_events`; tenant-affecting → tenant `audit_events` with non-null `organization_id` | §10.2; no nullable column anywhere |
| O-SaaS-7 | Multi-membership replaces one-org-per-identity (ADR-SAAS-014) | §8.1 rewritten; shape `EQ-1…3` |
| O-SaaS-8 | `platform_admin` and `platform_ops` are separate responsibilities | §7.3 (one role per account by default) |
| O-SaaS-10 | Tenant audit view shows named operator identity **and** platform role | §10.1 event fields |
| O-SaaS-11 | `staff_password_history` reuse checks deferred to post-launch | §4.6 stays `DEFERRED` |
| O-SaaS-12 | The operator-assisted reset **may** return the code under the stated constraints | §6.2 as written |
| O-SaaS-13 | Explicit `org_admin` consent for every support grant; no `grace` pre-approval | §7.3 |
| O-SaaS-14 | Suspension requires second-person approval | §7.3; tenant spec §5.2 |
| O-SaaS-15 | MFA deferred for MVP with risk recorded and accepted | §13.1 item 1 |
| O-SaaS-16 | Closure needs platform admin + second approver; data retained by default | §7.3; tenant spec §11 |

### 13.1 Residual risks accepted by this specification

1. **No MFA.** A stolen platform password grants 30 minutes of platform authority. **Accepted for the
   MVP by O-SaaS-15** because the platform operator population is tiny and known; MFA remains the
   first post-launch hardening item, and the acceptance is recorded rather than assumed.
2. **No e-mail channel.** Reset is operator-assisted (O-SaaS-12). The trade-off is documented
   rather than hidden behind a flow that cannot run.
3. **One access token per plane, no central introspection.** Revocation is bounded by the access
   TTL, not instantaneous. A per-request introspection service is `DEFERRED` (it would add a
   network hop to every request, which the hardware envelope cannot absorb).
4. **Multi-membership adds an authorisation surface** that one-org-per-identity did not have. The
   owner accepted the trade for clinician usability (O-SaaS-7). Mitigation is structural: the active
   organization comes from the token, is re-verified against a live membership on every request
   (§8.1), and a switch is its own authorised, audited act — never a client-supplied value.

---

## 14. Governance and skill compliance

| Requirement | Compliance |
|---|---|
| `.clinerules` §2 automatic routing | domain rows applied: authentication/RBAC (§4), multi-tenant data (§8), audit (§10), documentation (§11/§12) |
| `.clinerules` §3 non-negotiables | server-side enforcement (§9), token-derived tenancy preserved (§3.3 P-2), `404` on cross-tenant (§9.1), no secrets in logs (§10.2), append-only audit (§10.2) |
| `.clinerules` §4 domain table | auth row: `saas-auth-and-authorisation.md` (adapted), BR §7–§8, `common/permissions.py`, M2 report — read and applied |
| `.clinerules` §5 skills | **no skills installed** — none used, none claimed |
| `.clinerules` §7 evidence standard | every "today" claim traces to the audit, which is the evidence artefact; nothing here is labelled VERIFIED |
| `.clinerules` §9 boundaries | no code, migration, compose, frontend or test file changed; no server started, no suite run |
| `.clinerules` §11 output location | written to `docs/architecture/saas/` — one new leaf under the existing `architecture/` subject folder (rule applied; see §15) |
| `.clinerules` §12 reading policy | audit read before writing; index consulted; citations are paths opened in this session |
| Revision 2 reconciliation | O-SaaS-1/2/7/8/10/11/12/13/14/15/16 and A1–A4 applied; ADR-SAAS-013 `SUPERSEDED` by 014; `EQ-1…3` cited for the membership shape; no evidence label advanced by any decision |

### 14.1 Self-check

- Does anything here weaken tenant isolation? No — §9.1 is strictly additive to `require_org_access`,
  and multi-membership keeps the active organization token-derived with a live-membership re-check.
- Does anything here grant a new privilege to an existing role? No — `super_admin` loses nothing
  until R-3, which O-SaaS-1 makes conditional on the replacement being `TESTED` and `VERIFIED`.
- Is any claim marked VERIFIED without a second artefact? No.
- Does any mechanism depend on an absent capability (mailer, MFA, introspection)? Yes, three times,
  and each is labelled: MFA deferred by O-SaaS-15, reset operator-assisted by O-SaaS-12,
  introspection `DEFERRED` in §13.1.

---

## 15. Document control

| Field | Value |
|---|---|
| Written to | `docs/architecture/saas/AMSDP_Identity_and_Access_Management_Specification_V1.0.md` |
| Sibling documents | architecture specification, current-state audit, tenant & organization specification, subscription & entitlement specification, implementation roadmap |
| Code/schema/deployment changes | **none** |
| Runtime verification | **none claimed** |
| Index registration | `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Revision | V1.0 — 2026-11-17; **Revision 2** — 2026-11-17 (owner decision reconciliation) |

### 15.1 Revision history

| Revision | Date | Change | Authority |
|---|---|---|---|
| V1.0 | 2026-11-17 | Initial identity/access specification; ADR-SAAS-013 left `OPEN` | specification-only draft |
| **Revision 2** | 2026-11-17 | Owner decisions `O-SaaS-1…16` and A1–A4 applied. §8.1 rewritten to multi-membership (ADR-SAAS-014, supersedes 013) with `EQ-1…3` for the physical shape; §7.4 R-3 made conditional on tested replacement; §2.1 annotated as as-built baseline; §1.2/§1.3 moved to the two-axis vocabulary; §13 converted from open items to applied rulings; §13.1 gained the multi-membership risk and the O-SaaS-15 acceptance; `PROPOSED`/bare `APPROVED` labels normalised | Product Owner, 2026-11-17 |

### 15.2 What Revision 2 did not do

- It did not build multi-membership, `platform_users`, refresh tokens, revocation or the reset
  flow. Every mechanism remains `SPECIFIED` with evidence `NOT IMPLEMENTED`.
- It did not decide the membership table's physical shape, backfill or token mechanics — those are
  `EQ-1`, `EQ-2`, `EQ-3` (architecture spec §14.3.1) and remain engineering questions.
- It did not touch `common/auth.py`, `common/permissions.py`, `identity/main.py`, any migration,
  `docker-compose.yml`, the frontend or any test.
