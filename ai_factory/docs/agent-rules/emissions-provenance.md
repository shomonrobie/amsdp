---
name: emissions-provenance
description: Governs emissions factors, matching, calculation, calculation snapshots, evidence and report output — the product's core domain. Use whenever a task touches emission factors or imports, activity/line mapping, validation of emissions data, the calculation engine, calculation snapshots, emissions logs, evidence, or any customer-facing report. Enforces the rule that no emissions number exists without its provenance.
---

# Emissions Provenance — Factors, Calculation, Evidence, Reports

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).

## 1. When to activate

Any work on: `emission_factors`, `customer_factors`, factor imports, matching stages,
`calculation_snapshots`, `emissions_logs`, `evidence_line_items`, the calculation engine,
validation of emissions data, report generation or re-extraction.

## 2. The mandatory chain

```
source document → extraction item → mapped factor → validation
→ calculation snapshot → emissions log → evidence → approval → report version
```

Every link must be durable and addressable. If a change breaks a link, it is a defect even
if the number is right.

## 3. Hard rules

1. **Never produce an emissions number without provenance.** The snapshot must carry
   `factor_id`, `factor_kind` (`emission_factor` | `customer_factor`), `customer_factor_id`
   when applicable, `reporting_year`, `methodology`, `algorithm_version`, `source_item_id`
   and the line link when one exists.
2. **The reporting year is a property of the document/context — never of the wall clock.**
   No exact-year factor ⇒ stop for manual review. Never silently select a factor from another
   reporting year. (PO-1, ratified.)
3. **Customer factors are year-scoped.** A factor approved for one reporting year must not
   apply to another. (PO-3, ratified.) A Customer Owner may self-approve; a Member or Viewer
   may not (AGENTS.md §16).
4. **Factor provenance beats convenience.** Approved customer factor → CarbonTally factor →
   unresolved/manual review. Never silently replace an approved customer factor.
5. **Snapshot immutability.** Never overwrite or delete a calculation snapshot or emissions
   log as a side effect. A correction creates a new record and supersedes the old one.
   Re-extraction must archive rather than destroy prior state (see R-13 — currently open).
6. **Read, do not assert.** A report's methodology, factors and quality must be read from the
   snapshots behind its figures. Never hard-code `direct_multiply`, never accept
   `algorithm_version` from the caller, never take the verification set from the request body.
7. **Scope identity is not optional.** A Scope 2 result needs its method
   (`location_based` | `market_based`); a Scope 3 result needs its category. If either is
   unknown, the line is blocked, not guessed.
8. **Data quality is stated, never implied.** Where quality is unknown, say unknown
   (`unclassified`) — never present it as measured.
9. **Never emit a compliance, certification or assurance claim.** State what was produced and
   on what basis; disclaim assurance explicitly.
10. **Factor history is reference data.** Superseded factor batches are retained indefinitely
    (PO-2); they are not purged, and they must not remain *selectable* once superseded.

## 4. Anti-patterns — name them on sight

- **The Literal Method** — a methodology label typed into a report renderer.
- **The Wall-Clock Year** — `datetime.now().year` as a reporting year.
- **The Helpful Fallback** — "nearest year" / "newest year" selection that nobody approved.
- **The Destructive Save** — replacing `mapped_data.line_items` with a reduced result shape,
  erasing method, confidence and stages.
- **The Demo Report** — copy generated from hard-coded strings instead of persisted figures.
- **The Silent Restatement** — re-extraction that deletes the evidence it replaces.

## 5. Self-check

- [ ] Does every new number carry factor + year + method + source?
- [ ] Did I introduce any cross-year selection or year inference?
- [ ] Can a reviewer answer "why this factor?" from persisted data alone?
- [ ] Does the report read its method, or does it assert one?
- [ ] Did any prior snapshot/log get destroyed instead of superseded?
- [ ] Is any claim about compliance/assurance absent from the output?
