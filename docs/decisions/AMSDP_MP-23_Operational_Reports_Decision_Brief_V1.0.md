# AMSDP — MP-23 Operational Reports: Product Owner Decision Brief V1.0

**Status:** OPEN — awaiting a Product Owner decision · **Written:** 26 November 2026 ·
**Raised by:** the implementation mandate of 26 November 2026 (§4.2) and audit finding **F-6** ·
**Governed by:** `docs/product/AMSDP_Business_Rules_V1.0.md` §43; roadmap §6 WP-F (MP-23, P1, 4.0 days)
**This brief decides nothing.** MP-23 has not been implemented, narrowed or deferred by the agent.

---

## 1. The question

Business Rules **§43** requires operational reports — appointments by day, by doctor and by branch; status
counts; walk-ins; queue activity; utilisation. The requirement is **approved**, it has **no implementation**,
and it has **no recorded deferral**. Roadmap MP-23 is P1 with a 4.0-day estimate and depends on MP-01.

So the question is not *whether* §43 matters. It is: **what, exactly, gets built now, and what is explicitly
deferred in writing?**

---

## 2. Why a decision is needed, and why the agent did not simply build it

- **Two of the five dimensions have no agreed definition.** "Queue activity" could mean transitions, calls or
  consulted minutes; "utilisation" could mean slot occupancy, doctor-hours used or room-hours used. Each
  produces a different number, and choosing one is a product decision with operational consequences — a
  utilisation figure that reads low can be used to justify closing a session.
- **The mandate forbids the agent deciding it** (mandate §4.2): implement, narrow or defer are the Product
  Owner's to choose.
- **M-7 depends on it**, so the decision should be explicit rather than inferred from silence.

---

## 3. What exists today (the starting point for every option)

| Surface | State | Reusable for MP-23? |
|---|---|---|
| Dashboard aggregates (MP-22 work) | Implemented: today's counts, queue length, walk-ins, recent activity | **Yes** — the same `appointments` / `queue_entries` reads answer three of the five dimensions |
| `GET /api/v1/queue/history` | Implemented; doctor + date, every status | **Yes** — a row source for queue activity |
| `appointments` table | day, doctor, branch, status, source, timestamps | **Yes** — no schema change needed |
| `queue_entries` table | token, position, status, `status_history`, `position_history` | **Yes** for counts; a *minutes* metric needs a defined start and end |
| Any reporting screen | **None** | — |
| Any export (CSV/PDF) | **None**, and §43 does not ask for one | out of scope for all three options |

---

## 4. The options

### Option A — implement the complete approved BR §43 scope

**Deliverables.** A reporting surface (new endpoint, or an extension of the dashboard aggregates) plus one
report screen: appointments by day / doctor / branch, status counts, walk-ins, queue activity and utilisation —
each scoped by the principal's organization and branch, with a non-disclosing 404 on a foreign branch.

**Effort.** ≈ 4.0 engineer-days (roadmap estimate) plus tests and a reconciliation run.

**Dependencies.** MP-01 for reconciliation evidence (a fixed day compared against the live tables).
Utilisation needs a Product Owner **definition before** code, or the number will be an invention.

**Effect on M-7.** Satisfies it in one step.

**Risks.** Two metrics whose definitions do not exist yet; a large surface delivered before the demonstration
is ready; and the temptation to define "utilisation" as whatever the query happens to compute.

### Option B — defer MP-23 explicitly to a later phase

**Deliverables.** None. A recorded decision that M-7 is not met for the Hackathon Version.

**Effort.** Zero engineering; one document line.

**Effect on M-7.** Explicitly unmet — honest, and better than an unrecorded gap.

**Risks.** An approved P1 requirement with no delivery and no date; the next audit reports the same finding.

### Option C — implement a defined MVP subset, defer the rest in writing (recommended)

**Deliverables.** One endpoint and one report screen covering the three dimensions that need no new definition
and no schema change:

1. appointments by day, by doctor and by branch;
2. status counts (the BR §8.3 lifecycle statuses);
3. walk-ins versus booked (`entry_source` / `source`).

**Explicitly deferred, in the decision record:** *queue activity* and *utilisation*, until the Product Owner
defines them. Every figure must reconcile for a fixed day against `appointments` and `queue_entries`, be scoped
by organization and branch with 404 on violation, and be readable in Bangla and English.

**Effort.** ≈ 2.0 days plus tests.

**Dependencies.** MP-01 for reconciliation evidence. No schema change, so no migration and no D9 chain risk.

**Effect on M-7.** Partially met — by decision and in writing.

**Risks.** A partial report can be mistaken for the whole §43 obligation. Mitigation: the screen and the
limitations report state which two dimensions are deferred, and why.

---

## 5. Recommendation

**Option C.** It reports only what can be computed truthfully today, keeps M-7's status honest, needs no schema
change, and defers exactly the two dimensions that need a product definition rather than an engineering choice.
Option A should follow once "queue activity" and "utilisation" are defined — at which point the remaining work
is a metric, not a feature.

---

## 6. What can proceed independently of this decision

- Everything else in this session's execution report — MP-24, MP-25, MP-28, MP-33, MP-35, MP-37, MP-38, MP-39,
  MP-42, MP-43, MP-45, MP-46 — is unaffected by MP-23.
- MP-31/MP-32 (acceptance and rehearsal) do not need MP-23: the MVP §12 script does not exercise reports.
- **M-7 stays open** until this decision is taken — that is the only consequence of leaving it undecided.

---

## 7. Document control

| Field | Value |
|---|---|
| Document | `docs/decisions/AMSDP_MP-23_Operational_Reports_Decision_Brief_V1.0.md` |
| Version | V1.0, 26 November 2026 |
| Status | **OPEN** — decision required |
| Evidence base | Roadmap §6 WP-F; Business Rules §43; audit finding F-6; the surfaces named in §3 |
| What it does not do | It does not implement, narrow or defer MP-23, and it does not change the roadmap |
| Registration | `docs/governance/AMSDP_Docs_Index_V1.0.md` Revision 49 |

