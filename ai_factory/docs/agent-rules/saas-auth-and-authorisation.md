---
name: saas-auth-and-authorisation
description: Identity, role and authorisation rules for CarbonTally. Use when adding or changing an endpoint guard, a role, a capability, a consultant grant, a processing-entity assignment, an invitation, or any access decision. CarbonTally has four operating planes and capability-based staff permissions — not one four-tier role hierarchy.
---

# Auth & Authorisation — Four Planes, Capabilities, Deny-by-Default

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).
This file owns **who may do what**. Enforcement mechanics live in
[saas-application-security.md](saas-application-security.md); tenant RLS lives in
[saas-multitenant-data.md](saas-multitenant-data.md).

## 1. The four planes and their authoritative relationship

| Plane | Authority comes from | Not from |
|---|---|---|
| Customer | `organization_members.role` (`owner`/`admin`/`member`/`viewer`) | a staff role |
| Consultant | `consultant_clients` (a relationship) | `organization_members` |
| Processing entity | `processing_entities` + work assignment | org membership |
| Internal staff | `staff_roles.permissions` (capability flags) | "being an admin" |

Cross-plane access is **denied by default**. A consultant reaching a client organisation does
so through the relationship and loses access when it ends — the organisation and its data are
never cloned.

## 2. Capabilities, not tiers

Staff permissions are **explicit flags** (`can_manage_billing`, `can_manage_staff`,
`can_manage_compliance`, `can_process`, `can_review`, `can_view_all`, `can_qc`, …) on a
seven-value staff vocabulary (`admin`, `system_admin`, `operator`, `reviewer`, `qc_specialist`,
`pe_manager`, `compliance_admin`).

- **Do not infer one capability from another.**
- **Do not broaden a role** (or add `admin`) to make a workflow convenient.
- `system_admin` is a permission **superset**, not a tier; `pe_manager` deliberately carries
  several capabilities at once. A rule that forbids roles spanning functions is wrong here.
- `can_manage_compliance` is distinct from `can_manage_billing` and `can_manage_staff`.

## 3. Customer roles

- `owner`: full organisation authority. **May self-approve a customer factor** (ratified; do
  not reintroduce a blanket "no self-approval" rule).
- `admin`: organisation administration, except where a decision reserves it to the owner.
- `member`: operates data; cannot perform owner/admin actions.
- `viewer`: **read-only** — no writes anywhere, including storage.

## 4. Processing entities

- PE users see work **assigned to their entity**, and nothing else.
- PE A must not reach PE B's work; PE must not reach restricted customer documents.
- PE users never gain internal CarbonTally administrative capability.
- PE work authority is entity- and batch-scoped, not organisation-role-scoped.

## 5. Internal staff

- Operators, reviewers and QC are capability-scoped; none of them gains user/role management
  merely by processing work.
- `require_admin()` alone is **not** purpose-bound document access. M-20 (explicit,
  purpose-bound, audited staff access) is ratified and currently unimplemented — treat
  `require_admin()`-only document access as a known gap, not as the intended design.

## 6. Invitations

Invitations are a persisted record, and their acceptance path is a real workflow. **Do not
invent a state machine** (the legacy rule attempted this and was truncated mid-sentence). If
invitation states are needed, read the existing table and the acceptance route, and state the
states that exist.

## 7. Enforcement rules

1. Authorise server-side on **every** sensitive route; the UI is never the boundary.
2. Resolve the tenant from the principal, then authorise the specific action.
3. Cross-tenant access returns **404**, not 403, when existence itself is sensitive.
4. A denied action is recorded (a counted signal), not silently ignored.
5. Never gate on a route being hidden or a button being disabled.

## 8. Minimum negative-test matrix

Customer A→B · Client A→B · Consultant A→B · Consultant A→B's client · PE A→B ·
PE→restricted customer document · Viewer→write · Member→admin operation ·
Staff→Staff-Admin operation · Staff-Admin→System-Admin-only · Customer→internal ·
PE→internal.

**Every unexpected ALLOW is a serious finding.**

## 9. Anti-patterns

- **The Four-Tier Doctrine** — "every role must fit one tier; never span tiers".
- **The Admin Shortcut** — `admin` as a universal permission.
- **The Org Role Consultant** — modelling consultant access as membership.
- **The Membership PE** — modelling PE access as organisation membership.
- **The Hidden Button** — UI-only enforcement.

## 10. Self-check

- [ ] Which plane is this actor in, and what is the authoritative relationship?
- [ ] Is the capability explicit, or did I infer one from another?
- [ ] Did I broaden a role instead of adding a capability?
- [ ] Does cross-plane access fail closed with a non-disclosing response?
- [ ] Are the ALLOW and DENY cases both tested?
