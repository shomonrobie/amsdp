---
name: saas-multitenant-data
description: Tenant data, schema and RLS rules for CarbonTally's shared PostgreSQL (Supabase). Use when adding or changing tables, columns, indexes, RLS policies, retention, usage metering or any query that crosses organisation boundaries. The tenant key is organization_id; the platform has four operating planes, not one.
---

# Multi-Tenant Data — Schema, RLS, Retention, Metering

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).

## 1. When to activate

Any migration, table/column/index change, RLS policy, tenant-scoped query, retention job, or
usage/credit metering work.

## 2. The tenant model — four planes, one key

| Plane | Authoritative relationship |
|---|---|
| Customer | `organization_members` (`role`: owner/admin/member/viewer) |
| Consultant | `consultant_clients` (a relationship, **not** an org role) |
| Processing entity | `processing_entities` + assignment |
| Internal staff | `staff_roles.permissions` (capability flags) |

- The tenant column is **`organization_id`**. Never introduce `tenant_id`.
- Shared reference data (e.g. `emission_factors`) carries no tenant key by design.
- A consultant reaches a client organisation through the relationship; it is revocable without
  cloning the organisation or its data.
- Cross-plane access is denied by default.

## 3. RLS — the primary control

- Enable RLS on every tenant table. A policy that resolves the tenant with
  `current_setting('app.tenant_id')` is **wrong for Supabase** — policies resolve `auth.uid()`
  against `organization_members`.
- A table may deliberately have **no** policy (fail-closed, service-role-only). That is a
  design choice, not an omission — document it.
- Never let a Viewer write. Never widen a policy to make a feature work.
- Every RLS change needs same-tenant ALLOW, cross-tenant DENY, and role-restriction tests.

## 4. Schema shape

- Timestamps: `created_at` / `updated_at` on mutable tables. Soft delete is **domain-specific**
  (documents), not a global column.
- Subscriptions: `customer_subscriptions` with `lifecycle_status` (not a legacy status string)
  and a versioned plan FK; commercial values live in versioned, scoped config.
- **Credits**: the ledger (`billing_credit_ledger`) is append-only and authoritative. The
  balance is **derived** (`SUM(credit_delta)`). Never add a running-balance column.
- Idempotency: unique `(organization_id, external_reference)` style keys; never a client-supplied
  result.
- Usage events and credits are one pipeline: usage is recorded, billing consumes credits. Do
  not create a second ledger.

## 5. Migrations

1. Inspect schema, FKs, indexes and RLS before changing anything.
2. One migration per change, with task/decision IDs, a "what is wrong today" note and a
   post-apply verification block (the repo's existing standard).
3. Forward-only and idempotent; if a change is irreversible, say so explicitly rather than
   pretending a down-migration exists.
4. The chain is **pinned** (count + tip + content fingerprint). Moving the pin is a deliberate
   act in the same change — never a test fix.
5. Production apply is a separate PO-authorised operation.

## 6. Retention (N3 — frozen)

Retention is **configurable per domain** through the admin control plane and enforced
server-side. Do not invent a default duration (no "30–90 days" rule). Retention must never
destroy evidence, audit trail, ledger, provenance history or factor batches.

## 7. Indexing and scale

- Index the tenant key and the common access path (e.g. `(organization_id, created_at)`).
- Composite indexes follow real query shapes, not guesses.
- Do not add indexes speculatively; consult the existing inventory and measured volume.

## 8. Anti-patterns

- **The Second Tenant Column** — `tenant_id` beside `organization_id`.
- **The App-Only Filter** — isolation enforced in Python, not RLS.
- **The Viewable Ledger** — a policy that lets a Viewer read the tenant audit ledger.
- **The Invented Retention** — a hard-coded purge window.
- **The Parallel Ledger** — a second credit table that can drift.

## 9. Self-check

- [ ] New table has RLS and documented policy intent
- [ ] Tenant key is `organization_id`; queries are org-scoped
- [ ] Cross-tenant DENY test exists
- [ ] No commercial literal; no second ledger; no running balance
- [ ] Migration pin and verification updated deliberately
- [ ] Retention, if touched, still configurable and still preserves audit/evidence
