---
name: carbontally-agent-governance
description: Tier-1 governance for every AI agent working on CarbonTally. Load this before any other rule and before reading or changing code. Establishes the precedence order, the inspection protocol, authorisation boundaries, database and migration safety, test requirements, and the evidence standard. It outranks every technique skill in this directory and every generic SaaS convention.
---

# CarbonTally Agent Governance (Tier 1)

**Load order: this file first, always.** Every file in this directory defers to it.

## 1. Precedence — resolve conflicts in this order

When two sources disagree, the higher one wins:

1. **Current verified runtime, database and test state** — what actually happens
2. **Ratified Product Owner decisions** — including `AGENTS.md` §16, D-001…D-029, D1–D17, I-R*, M-*
3. **Frozen architecture decisions** — D1–D21, N1 (messaging), N3 (retention)
4. **`AGENTS.md`** — the repository constitution
5. **These rule files** (Tier 2)
6. **Generic SaaS convention**

A rule in this directory that contradicts 1–4 is **wrong and must be reported**, not applied.
Never resolve a conflict silently. Never change a ratified decision to make a rule fit.

## 2. Inspect before you change

Before writing code, read: the current implementation, the migrations that created the
schema, the tests that pin the behaviour, and the decision record for the area. A remembered
fact is a hypothesis until re-verified against the tree (this platform has already shipped
three "final" audits that contradicted each other).

## 3. Protect uncommitted work

The tree is frequently dirty — other agents' tested-but-uncommitted work lives in it.

- **Never** `git reset --hard`, `git clean -fd`, `git stash`, `git checkout .`, or switch
  branches "to tidy up".
- Never amend or rebase shared history; never force-push.
- Keep your own commits path-scoped, and **check whether a file you are editing already
  carries someone else's uncommitted change** (`git diff <file>`) before staging it.
- If a file's diff contains work that is not yours, say so in your report.

## 4. Authorisation — what you may and may not decide

You may decide: implementation, naming, file layout, test strategy, and the smallest correct
change.

**PO DECISION REQUIRED** (stop and ask; do not infer):
- who may approve/create/manage users or roles
- retention durations
- communication and messaging boundaries
- consultant and processing-entity capabilities
- billing rules, credit semantics, pricing
- workflow transitions and approval authority
- imposing any compatibility break or blocking behaviour on customers
- changing or retracting a ratified decision

When a decision is missing: record **BLOCKED — PO DECISION REQUIRED**, state the options and
their consequences, and stop. Never choose policy to avoid waiting.

## 5. Database and migration safety

1. Inspect the schema, existing migrations, foreign keys, RLS and indexes first.
2. Every schema change has a migration; no ad-hoc production modification.
3. The migration chain is **pinned** (`EXPECTED_MIGRATION_COUNT`, an advancing tip and a
   content fingerprint). Adding or editing a migration moves the pin — do that deliberately,
   in the same change, and never to make a test pass.
4. Production migration is a **separate PO-authorised operation**. CI never applies it.
5. Never disable RLS, never broaden a policy, never grant service-role access as a shortcut.
   Provider-owned policy changes (e.g. `storage.objects`) are **operator steps**, not
   migrations — and must be recorded as applied per environment.

## 6. Testing — test the behaviour, both directions

- A workflow change needs a workflow test, not only a unit test.
- A security change needs **ALLOW and DENY** cases. An unexpected ALLOW is a serious finding.
- A data change needs a test over real-shaped rows (including NULLs), not only the happy path.
- A fix needs a **regression test that fails before it** — otherwise you cannot show it fixed.
- Do not weaken or delete a test to make a change pass. If a test encodes the defect, change
  it deliberately and say why in the report.

## 7. Evidence — never promote on one artefact

| Label | Means exactly |
|---|---|
| IMPLEMENTED | code exists and is reachable |
| TESTED | named tests pass in this tree |
| VERIFIED | a **second, independent** artefact confirms it (real document, browser run, DB read) |
| ACCEPTED | the Product Owner has signed it |

A green suite does **not** make something VERIFIED. A migration in the chain does **not**
prove the schema is applied. Documentation does **not** prove implementation.

## 8. Report what you changed — including what you did not

Every implementation report states: task and scope; files changed; database/migration/API
changes (or "none"); tests run and their real result; runtime verification (or why none);
security verification; git state; remaining limitations; and **what you deliberately did not
do and why**.

## 9. Stop conditions

Stop and report instead of proceeding when: a PO decision is missing; a change would break a
ratified decision; you cannot verify the affected behaviour; the change would require touching
another agent's uncommitted work; or the "fix" would be more harmful than the defect.

## 10. Non-negotiables (repeat them every time they are relevant)

- The tenant key is `organization_id`. Never introduce `tenant_id`.
- The credit balance is **derived** (`SUM(credit_delta)`); the ledger is append-only. Never add
  a running-balance or `credits_balance` column.
- `RateLimitMiddleware` is **unregistered** and must not be registered. The limiter is a route
  dependency; `/webhooks/*` is never intercepted; a refusal is **429 with headers**, never 500.
- Commercial values live in scoped config (customer → plan → global). No pricing literal in
  Python or SQL.
- The UI is never the security boundary. Hidden or disabled controls are not authorisation.
- Never log or expose secrets, tokens, signed URLs or database credentials.
- Never emit a compliance, certification or assurance claim from CarbonTally.
- Never produce an emissions number without its provenance (see `emissions-provenance.md`).
