# AMSDP Skill Routing Architecture

> **Product:** AMSDP — Appointment Management System for Doctors & Patients
> **Document:** Skill Routing Architecture (discovery, selection, onboarding)
> **Version:** 1.0.0 · **Status:** For project-owner review · **Date:** 2026-11-08
> **Companion:** `AMSDP_Engineering_Governance_Assessment.md` (rule applicability + routing map)

## 1. Purpose

Define how AMSDP performs automatic skill discovery and selection for every task, what the pending
"skill slot" is, how it falls back when a skill is unavailable, and how a new skill is onboarded when
the project owner approves one. This document is the depth companion to `.clinerules` §5; the
always-loaded decision table lives in `.clinerules` §4.

## 2. What counts as a "skill" in AMSDP today

A **skill** is an executable, named capability with its own loadable instructions (a SKILL.md or
equivalent) that changes how a task is performed. Verified at integration time:

- **No formal skill packages are installed** in this workspace (searched `skills/`,
  `.clinerules/skills/`, `.claude/skills/`, `~/.cline`, `~/.claude/skills`).
- What **does** exist and plays the skill role today are the AMSDP knowledge artefacts:
  - product specs — `docs/product/AMSDP_Business_Rules_V1.0.md`, `docs/product/AMSDP_MVP_SCOPE_V1.0.md`;
  - architecture — `docs/architecture/AMSDP_System_Architecture_V1.0.md`, AI-factory reports;
  - milestone implementation reports — `docs/security/AMSDP_M2_*`, `docs/implementation/AMSDP_M4/M5/M6_*.md`;
  - governance — the assessment, this document, and the adapted agent-rules.

Until a formal skill package is approved, the skill slot in `.clinerules` §4 resolves to these
artefacts. That is an **honest resolution**: reports must state "no skill installed; used governance
documents", never imply a skill ran.

## 3. Routing flow (automatic per task)

```text
task prompt
   │
   ▼
[1] parse task ──► [2] classify into domain(s)     (.clinerules §4 table)
   │                     │
   │                     ▼
   │              [3] select governing documents per domain
   │                     │
   │                     ▼
   │              [4] discover skills (.clinerules §5)
   │                     │
   │                     ▼
   │        ┌── available? ──────────┐
   │        │ yes                    │ no
   │        ▼                        ▼
   │   read skill instructions   use governance docs
   │        │                        │
   │        ▼                        ▼
   │   [5] conflict check against .clinerules §1/§3 + Business Rules
   │        │
   │        ▼
   │   [6] read required instructions BEFORE code  ──► implement
   │                                                     │
   │                                                     ▼
   │                                              verify (tests + live)
   │                                                     │
   └────────────────────────────────────────────────────▶ report (§9 block)
```

Every step is mandatory; none is optional or discover-by-accident.

## 4. Skill slot registry

| Slot (from `.clinerules` §4) | Installed package | Resolution today |
|---|---|---|
| frontend-ux | none | governance docs (`saas-frontend-ux` adapted + AMSDP UI/UX assessment + `i18n.js`) |
| api-security | none | governance docs (`saas-application-security` adapted) |
| auth-rbac | none | governance docs (`saas-auth-and-authorisation` adapted + `permissions.py`) |
| multitenant-data | none | governance docs (`saas-multitenant-data` adapted) |
| db-migrations | none | governance docs (multitenant-data §4–5 + cicd-workflow §3 adapted) |
| queue-concurrency | none | governance docs (BR Parts V–VII + api-throttling concurrency intent) |
| observability-audit | none | governance docs (`saas-observability` adapted) |
| cicd-deploy | none | governance docs (`saas-cicd-workflow` adapted) |
| llm-routing | none | `.clinerules` §8 LLM policy (local → frontier escalation) |

## 5. Fallback rule (skills unavailable)

1. Report the fact: "No installed skill for <slot>; used the listed governance documents."
2. Use the governing documents selected in `.clinerules` §4.
3. Do not fabricate a skill, borrow a CarbonTally rule verbatim, or silently substitute a different
   skill. A discovered-but-unusable skill is reported, not used.

## 6. Skill onboarding path (requires project-owner approval)

When the project owner approves adding a skill:

1. **Proposal**: name, scope, source, and the slot it fills (from §4).
2. **Location**: a `skills/<name>/SKILL.md` (or the Cline-native skills directory if the harness
   documents it) — never a file Cline cannot load.
3. **Routing hook**: the SKILL.md frontmatter `description` must match a row in the `.clinerules` §4
   table so discovery matches the classification step.
4. **Content rule**: the skill must be true of AMSDP's tree, must not restate `.clinerules` at length,
   must defer to AMSDP Business Rules, and must declare its relationship to the adapted agent-rules.
5. **Registration**: update `.clinerules` §5 registry and this document §4 (slot → package).
6. **Validation**: run a routing trace (like Assessment §8) showing the new skill being selected, and
   require the compliance block to name the installed skill.

## 7. Constraints

- No skill is installed by this deliverable (authorization requires approval).
- The CarbonTally agent-rules directory is **reference material**, not a skill library to import.
- A skill must never override an approved AMSDP business rule; conflicts are escalated, not resolved
  by the skill.