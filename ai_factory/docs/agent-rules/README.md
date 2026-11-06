---
name: carbontally-agent-rules-router
description: The entry point for CarbonTally agent rules. Maps a task to the one technique file that governs it, states the mandatory pre-implementation protocol, and marks which rules are canonical, draft, or absent. Read this after carbontally-agent-governance.md and before starting any feature work.
---

# CarbonTally Agent Rules — Router

This directory is the **canonical, versioned, reviewable** rule set for agents working on
CarbonTally. Start with [carbontally-agent-governance.md](carbontally-agent-governance.md)
(Tier 1); it outranks everything here.

> **Do not load the legacy global files in `/home/shomonrobie/rules/`.** They are unversioned,
> partly truncated/corrupted, and describe a different application (Next.js, Tailwind, Redis,
> `tenant_id`, a four-tier role model). They are superseded by this directory.

## Mandatory protocol — before you implement

1. **Classify the task** with the table below. If it spans two domains, read both.
2. **Read the governing file** (and any file it cites).
3. **Check for a conflict** with `AGENTS.md` or a ratified decision. If there is one, report it;
   do not resolve it yourself.
4. **Record it**: every implementation report states `Rules consulted: <files>` and
   `Conflicts found: none | <description>`.

## Routing table

| If the task involves… | Read | Status |
|---|---|---|
| Emissions figures, factors, calculation, provenance, reporting output | [emissions-provenance.md](emissions-provenance.md) | **canonical** |
| React UI, components, layouts, tables, forms, accessibility, responsive behaviour | [saas-frontend-ux.md](saas-frontend-ux.md) | **canonical** |
| Tenant data, RLS, schema shape, retention, usage metering | [saas-multitenant-data.md](saas-multitenant-data.md) | **canonical** |
| Authentication, sessions, headers, transport, CSP, secrets, storage access | [saas-application-security.md](saas-application-security.md) | **canonical** |
| LLM provider/model registry, eligibility, activation, credentials | [saas-ai-provider-registry.md](saas-ai-provider-registry.md) | **canonical** |
| Rate limiting, throttling, quotas, upload/OCR surfaces | [saas-api-throttling.md](saas-api-throttling.md) | **canonical** |
| Billing, credits, subscriptions, invoices | — | **absent** — apply governance §10 and the billing decision record |
| Roles, capabilities, consultants, processing entities, invitations | [saas-auth-and-authorisation.md](saas-auth-and-authorisation.md) | **canonical** |
| CI/CD, release gates, Git/rollback | [saas-cicd-workflow.md](saas-cicd-workflow.md) | **canonical** |
| Observability, logging, redaction, alerts | [saas-observability.md](saas-observability.md) | **canonical** |

**"Absent" means: no canonical rule yet.** Do not substitute a generic SaaS rule. Use the
governance file, `AGENTS.md`, and the decision records; if the task is recurrent, propose a
new canonical file rather than reviving a legacy one.

## Why one domain is still absent

The nine legacy files were assessed in
[CT-AI-AGENT-RULES-AUDIT-01-REPORT.md](../dsharness/audit/CT-AI-AGENT-RULES-AUDIT-01-REPORT.md).
Nine domains are now canonical. **Billing / credits / subscriptions remains absent** because
its shape is decided by the Wave 4 and D-1 questions (the credit-draw sequencing and the
`0`-cap semantics). Writing a billing rule before those are answered would produce a confident
wrong rule — the exact defect this library exists to prevent. An honest gap is safer.

## How to add or change a rule

1. It must be **true of this repository** — cite the file:line that proves it.
2. It must not restate `AGENTS.md` at length; link to the section instead.
3. It must declare its tier and defer to the governance file in its first paragraph.
4. It must carry `name` and `description` frontmatter (the description is the routing hook).
5. Regenerate the manifest (`python backend/tools/agent_rules_manifest.py --write`) and run
   the integrity test:
   `python -m pytest backend/tests/unit/docs/test_agent_rules_integrity.py -q`

## Structure

```
docs/agent-rules/
  carbontally-agent-governance.md   Tier 1 — precedence, authorisation, safety, evidence
  README.md                         this router
  emissions-provenance.md           domain rule (the product's actual subject matter)
  saas-multitenant-data.md          schema, RLS, retention, metering
  saas-auth-and-authorisation.md    planes, capabilities, deny-by-default
  saas-application-security.md      authorisation mechanics, sessions, storage
  saas-api-throttling.md            route-dependency limiters, webhook safety
  saas-ai-provider-registry.md      lifecycle, eligibility, credential custody
  saas-frontend-ux.md               CRA/MUI/tokens, a11y, responsive
  saas-observability.md             logging, metrics, redaction
  saas-cicd-workflow.md             gates, migration release, Git safety
  MANIFEST.json                     SHA-256 per file — drift detection
```

Repo-root `.clinerules` is a thin shim that always loads: precedence + this router + the
non-negotiables. It exists so an agent that never opens this directory still hits the rules
that prevent the most damage.
