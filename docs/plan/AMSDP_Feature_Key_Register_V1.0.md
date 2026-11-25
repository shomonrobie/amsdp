# AMSDP — Feature-Key Register V1.0

> **Task ID:** `AMSDP-PO-DECISIONS-2026-11-25`
> **Version:** 1.0 · **Date:** 25 November 2026
> **Status:** **APPROVED SCHEME** — Product Owner decision **PO-12, Option A**, 25 November 2026.
> **Decision record:** `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.11.
> **Why it exists:** three identifier schemes were in force (`ORG-001`… in the MVP catalogue,
> `M1–M9` in Master Feature List V2.5, and the audit's local `F-nn` / `GAP-nn`), with no mapping
> between them, so no requirement could be traced mechanically to a task.

---

## 1. The rule

1. **`F-nn` is the stable feature key.** It is assigned once and never renumbered or reused. A
   feature that is removed keeps its key and is marked retired.
2. The catalogue IDs (`ORG-001`, `QUE-006`, `SYM-001`, …) are **not renamed**. They become one
   column of this register, so an existing document can keep citing them.
3. **Disambiguation:** a bare `F-nn` means a *feature*, per this table. The audit's own keys are
   *finding* identifiers local to `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md`
   and must always be cited as "audit `F-nn`" or "audit `GAP-nn`". They are neither renumbered nor
   reused here.
4. Any future re-keying must publish a mapping table in this register before it is used anywhere.

---

## 2. The register — the 26 features of the approved MVP catalogue

Source of the feature list: `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`
§C–D, 26 features, unchanged in count and identity by this register.

| Key | Catalogue ID | Feature | Business Rules | Milestone | Delivering task | Basis |
|---|---|---|---|---|---|---|
| **F-01** | ORG-001 | Organisation management | §3–§5 | M-1 | MP-02 (done) | IMPLEMENTED / TESTED |
| **F-02** | ORG-002 | Branch management | §3–§5 | M-1 | MP-02 (done) | IMPLEMENTED / TESTED |
| **F-03** | FAC-001 | Facility structure within organisation/branch scope | §3–§5 | M-1 | MP-02 (done) | IMPLEMENTED / TESTED |
| **F-04** | DOC-001 | Doctor management and profile | §14 | M-2 | MP-10, MP-17 | IMPLEMENTED / TESTED |
| **F-05** | DOC-002 | Schedule management | §15 | M-2 | MP-16, MP-18 | IMPLEMENTED / TESTED |
| **F-06** | APT-001 | Appointment booking | §16–§18 | M-3 | MP-05 | IMPLEMENTED / TESTED |
| **F-07** | APT-002 | Appointment check-in | §19–§20 | M-3 | MP-05 | IMPLEMENTED / TESTED |
| **F-08** | APT-003 | Appointment status lifecycle | §21–§23 | M-3 | MP-05 | IMPLEMENTED / TESTED |
| **F-09** | APT-004 | Cancellation and reschedule | §22–§23 | M-3 | MP-13 → MP-15 (**authorised, not started** — PO-04) | PARTIAL |
| **F-10** | PAT-001 | Patient registration and lookup | §10–§11 | M-1 | MP-19 | IMPLEMENTED / TESTED |
| **F-11** | QUE-001 | Queue entry creation | §24–§31 | M-4 | MP-06 | IMPLEMENTED / TESTED |
| **F-12** | QUE-002 | Queue call and recall | §24–§31 | M-4 | MP-06, MP-08 | IMPLEMENTED / TESTED |
| **F-13** | QUE-003 | Queue listing and board | §24–§31 | M-4 | MP-06 | IMPLEMENTED / TESTED |
| **F-14** | QUE-004 | Queue entry scoping | §24–§31 | M-4 | MP-06 | IMPLEMENTED / TESTED |
| **F-15** | QUE-005 | Queue homogeneity | §24–§31 | M-9-A | **unassigned** | **OPEN** — the one surviving P0 (see catalogue §H.1 annotation) |
| **F-16** | QUE-006 | Intelligent queue voice announcements (Bangla/English) | QUE-006 capability decision | M-9-B | MP-08 (done); W3 admin UI **deferred** (PO-05) | IMPLEMENTED / TESTED (audibility unproven) |
| **F-17** | DQDS-001 | Digital queue display system | §33 (PO-13 full scope) | M-9-C | MP-24, MP-35…MP-40 | **BLOCKED** — B-4 |
| **F-18** | PQT-001 | Patient queue tracking | backlog scope | M-9-A | MP-25 | **BLOCKED** — B-4 |
| **F-19** | RBAC-001 | Role-based access control | §8 | M-1 | MP-19 | IMPLEMENTED / TESTED |
| **F-20** | RBAC-002 | Capability delegation | §8 | M-1 | MP-19 | PARTIAL |
| **F-21** | RBAC-003 | Staff administration surface | §8 | M-1 | MP-19 | IMPLEMENTED / TESTED |
| **F-22** | AUD-001 | Audit history | §40 | M-1 | MP-18 | IMPLEMENTED / TESTED |
| **F-23** | DSH-001 | Operational dashboards and reporting | backlog scope | M-7 | MP-07, MP-22 | IMPLEMENTED / TESTED |
| **F-24** | L10N-001 | Bangla/English localization | backlog scope | M-7 | MP-28, MP-29 | IMPLEMENTED / TESTED |
| **F-25** | NOT-001 | Notifications | backlog scope | — | **not scheduled** | DEFERRED (mock provider) |
| **F-26** | SYM-001 | Symptom and onset capture | — (ratified by PO-03, 25 Nov 2026) | M-3 | shipped | IMPLEMENTED / TESTED |

**Reading the "Basis" column.** `IMPLEMENTED` and `TESTED` are `.clinerules` §7 grades evidenced in the
named task's report. **No row is `ACCEPTED`**, and no row is `BROWSER VERIFIED`: no browser run
exists in this programme.

---

## 3. Open item carried by this version

| # | Item | Why it is open | Closing action |
|---|---|---|---|
| **R-1** | The **V2.5 module family** column is not populated | Master Feature List V2.5 is 132 KB and was not read in this window, so naming its families would have meant inventing them. The approved scheme requires that column; an invented value is worse than a declared gap | Populate it when MP-34 next touches documentation, reading V2.5's family taxonomy and adding one column — no key changes |

D-5 compliance: this register is published under **Revision 49** of the Docs Index (decision record §8).

---

## 4. Document control

| Field | Value |
|---|---|
| Authority | PO-12 Option A, 25 November 2026 |
| Effect | Establishes `F-nn` as the stable key and the 26-row mapping; renames nothing in the approved catalogue |
| Does not | change any feature's approval status, priority, estimate or gate; does not renumber the audit |
| Placement | `docs/plan/` — it is planning traceability, ratified for this content by `.clinerules` §11 |

*End of Feature-Key Register V1.0.*
