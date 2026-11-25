# AMSDP — Phase Model V1.1 (Phases 4, 5 and 6 published)

> **Task ID:** `AMSDP-PO-DECISIONS-2026-11-25`
> **Version:** 1.1 · **Date:** 25 November 2026
> **Status:** **APPROVED** — Product Owner decision **PO-01, Option A**, 25 November 2026.
> **Decision record:** `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md`
> **Supersedes nothing.** V1.0 of the phase model does not exist; Phases 1–3 remain as defined in
> Business Rules §46–§48 and Master Feature List V2.5 §2035–2063 and are untouched by this document.

---

## 1. Why this document exists

AMSDP is reported against a six-phase programme. Phases 1, 2 and 3 are defined in approved
documents; Phases 4, 5 and 6 existed **only as names**, taken from
`docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md:288–295`. No exit
criterion and no accepting authority existed for any of them, so milestone **M-8** ("Phase 4–6
closed") could not be reported honestly and MP-30 had no definition that this programme was
willing to invent.

PO-01 (25 November 2026) closed that gap. This document is the publication act. It is written as a
**standalone** document on purpose: Business Rules and MVP Scope are owner-controlled
(`.clinerules` §11), and PO-01 authorises a publication, not an edit to them.

---

## 2. The three phases

Names are the ones already used in the multi-display specification — nothing is renamed or
renumbered.

| Phase | Scope (tasks) | Exit criterion | Accepting authority |
|---|---|---|---|
| **4 — Patient Tracking and Staff Handoff** | **MP-25** (durable tracking rate limit; ETA explicitly labelled *estimated*; QR print flow) and **MP-30** (verification of the handoff surfaces that already exist) | MP-25's acceptance cell is met, **and** MP-30's verification record names each handoff surface with the audit event that proves it. **M-8** closes | Product Owner |
| **5 — Dashboard, Reporting and Localization** | **MP-22, MP-23, MP-28, MP-29**. **MP-27 analytics excluded** (PO-06, 25 Nov 2026) | Report totals reconcile against `appointments` / `queue_entries` for one fixed day; every visible string resolves in both languages. **M-7** closes | Product Owner |
| **6 — End-to-End Integration, Demo Readiness and Acceptance** | **MP-31, MP-32, MP-33, MP-34, MP-40** | The MVP Scope §12 script is executed end to end with artefacts; two clean rehearsals are recorded; no document claims a capability the code does not enforce. **M-10** closes | Product Owner, after the rehearsal and the documentation audit |

**Two consequences that follow from the table and are not negotiable by an implementation agent:**

1. **Phase 4 contains no new clinical feature.** MP-30 is verification. A report that describes
   Phase 4 as delivering new clinical capability contradicts this decision.
2. **Phase 6 cannot close on a green test suite.** Its third exit clause is a documentation-audit
   result, which is why it depends on MP-34.

---

## 3. MP-30 — definition (what the task now is)

**Definition:** verify the staff-handoff surfaces that the code already ships, and record the
evidence. No new handoff feature is built under MP-30.

| Handoff surface | What must be verified | Where the claim must be provable |
|---|---|---|
| Doctor call / recall on the queue | A call and a recall from an authorised role succeed; an unauthorised role is denied **and the denial is audited** | Queue API + audit rows for one entry |
| Assistant → doctor assignment | The assigned assistant's view and the doctor's view agree on the same entry | `backend/common/permissions.py`, queue read paths |
| Tracking link sharing | A tracking link resolves for its own scope and fails closed (non-disclosing 404) outside it | tracking endpoint + a cross-scope request |
| Branch/tenant scope | Every surface above derives org/branch from the token, never from the request body | code read + one negative request |

**Evidence standard.** `.clinerules` §7 applies unchanged: a passing test is `TESTED`. MP-30 is
`VERIFIED` only when a second, independent artefact confirms each row — a live API session, a
browser run or a database read. **As of 25 November 2026 no row has been verified**, because no
database was reachable from this workstation (see the implementation report of the same date).

**Gate:** MP-25 is blocked by **B-4** (no live database access). MP-30 can be *started* by
verifying the surfaces that need no live database, but it cannot close until MP-25's acceptance
cell is met or the owner restates Phase 4's exit criterion.

---

## 4. Status of each phase today

| Phase | State | Honest one-line reason |
|---|---|---|
| 4 | **OPEN — partially executable** | MP-30's code read and negative-path checks are executable; MP-25 is blocked by B-4 |
| 5 | **OPEN — implemented, not verified** | MP-22/28/29 report TESTED; the day-reconciliation check needs a live database |
| 6 | **OPEN** | Depends on MP-31/32/33/34/40; MP-33 needs a pushed branch (O-3 explicitly forbids pushing), MP-32 needs a reviewer (now named — Faria Bushra) and a reproducible environment |

No phase is claimed as started, complete or accepted.

---

## 5. Document control

| Field | Value |
|---|---|
| Authority | Product Owner decision PO-01 (Option A), 25 November 2026 |
| Basis | `docs/implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md` §3.1 |
| Effect | Publishes names, scopes, exit criteria and accepting authority for Phases 4–6; defines MP-30 as verification |
| Does not | edit Business Rules or MVP Scope; authorise clinical V2.5 Parts III–VI; change any task estimate or gate other than MP-30's definition |
| Placement | `docs/product/` per `.clinerules` §11 (a scope publication, not an implementation report) |

*End of Phase Model V1.1.*
