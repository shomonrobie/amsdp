# AMSDP — PO-13 Multi-display DQDS Reconciliation Report

> **Task:** reconcile the requirements, the implementation plan and the current code against Product Owner decisions **PO-13**, **PO-02**, **MP-06** and the `docs/plan/` ratification (all dated 24 November 2026).
> **Version:** 1.0 · **Date:** 2026-11-24 · **Status:** documentation complete; **no implementation authorised or performed**
> **Scope:** documentation and planning only. No file under `backend/`, `frontend/`, `alembic/`, `docker-compose.yml` or `ai_factory/` was created, modified or executed.

---

## 1. What the Product Owner decided, and what this report answers

| Decision | Content | Disposition in this task |
|---|---|---|
| **PO-13** | Full-featured multi-display DQDS **in** the Hackathon delivery scope: multiple independently configured displays per branch, independent names and configuration, targeting by branch/doctor/department/room/queue, configurable Bangla and English, server-side filtering with strict org/branch isolation, automatic refresh on change, TV-scale typography, current token with doctor/room information, estimated waiting time (labelled, never guaranteed), token-only payloads, facility-controlled public information, read-only public access, administrator configuration with audit logging. **Not to be deferred or treated as optional** | **Applied.** Requirement set extended by **MD-13…MD-19**, criteria **AC-15…AC-22**, tasks **MP-41…MP-46**; BR §33 rewritten; audit §15 added |
| **PO-02** | No MVP Scope / Hackathon Version / Later Releases tier governs DQDS. BR §33's later-phase wording must be removed. No agent may use outdated scope wording to reduce or reinterpret the requirement | **Applied.** Both BR copies now carry a §33.1 scope-status block; the later-phase paragraph is **gone**; the plan's PO-02 gate is closed |
| **MP-06** | Queue operational dates and times use the relevant facility's configured timezone (`Asia/Dhaka` default), consistently across queue operations, dashboards and DQDS; tested around the facility-local date boundary | **Applied to the plan and the specification** (task **MP-44**, requirement **MD-16**). Recorded as *compliance with BR §0 item 8*, which already required it. **Not implemented** |
| **`docs/plan/`** | Ratify `docs/plan/` as an approved location for implementation plans and roadmaps; update `.clinerules`/governance; document the decision in the index | **Applied.** `.clinerules` §11 updated and the index annex records it; the earlier "placement deviation" is **closed**; nothing migrated, so no manifest entry |
| Change control | Approval does not authorise production deployment, database changes or unrelated implementation | **Honoured.** No deployment, no migration, no schema change, no unrelated work |

The four required follow-ups were: (1) reconcile BR §33 against PO-13, (2) update BR §33, (3) reconcile the plan and roadmap so every approved capability, dependency, work package and acceptance criterion appears, (4) identify implementation gaps or conflicts between requirements, plan and code, and (5) report the files, the changes and anything unresolved. Sections 3–7 answer them in order.

---

## 2. The one measurement that decided several requirements

Nothing below is inferred from a document; the constraint was measured in this tree:

- `backend/queuing/display.py:30-33` — `_DQDS_RATE_LIMIT = 30` requests per `_DQDS_RATE_WINDOW = 60.0` seconds, keyed by `request.client.host` (`:58-78`).
- `frontend/pages/queue-display/[org]/[branch].js:32` — the board polls every **10 s**, i.e. **6 requests/minute per screen**.
- Therefore: 4 screens = 24 req/min (fit); **5 screens = 30 req/min (exactly at the ceiling)**; 6 screens = 36 req/min (guaranteed `429`s for part of every minute), and every screen behind one public NAT address looks like one abusive client.

That arithmetic is why **MP-36** must re-key the limiter per display, and why "we support multiple displays" could not be claimed without changing it. It also sits behind **MD-15/MP-43**: polling decides *when* a screen looks, so "refresh when information changes" needs a change signal, not only a timer.

---

## 3. Files changed, and exactly what changed

| File | Kind | Change |
|---|---|---|
| `docs/product/AMSDP_Business_Rules_V1.0.md` | **Owner-controlled — edit explicitly instructed by PO-02** | §33's closing paragraph ("DQDS, television integration and multi-display configuration are later-phase capabilities…") **removed** and replaced by **§33.1 Scope status — PRODUCT OWNER DECISION PO-13**: the twelve required capabilities, the delivery-vs-adoption distinction, the interpretation rule ("no agent may reduce, defer or reinterpret"), the "no separate scope tiers" statement from PO-02, and the boundaries that still apply (server-side tenant scope, 404-not-403, append-only audit, no patient identity). Items 1–13 of §33 and every other section are untouched. Header gained one line: `**Amendment:** PO-13 / PO-02, 24 November 2026 — §33 scope status`. **42,812 → 47,353 bytes** |
| `docs/AMSDP_Business_Rules_V1.1.md` | Same authorised edit, same wording | The identical §33.1 block — **verified byte-identical, 3,433 characters** — so **no stale DQDS wording survives in either copy**, the failure mode PO-02 warned about. **47,338 → 51,954 bytes** |
| `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | Working requirement document — **Appendix E (Amendment A-1)** added, append-only | Approved-scope status; **D-04 withdrawn** (estimated wait is now MD-13), **D-08 split** (room targeting in, `QueueEntry.room_id` out); **MD-13…MD-19**; **AC-15…AC-22**; data-model delta (`scope_type='room'`, `room_id`, three policy booleans, CHECK constraints); contract deltas (`board_version`, weak `ETag`/`304`, estimate rule and wording, GET-only, two audit events); frame changes to the §5 title, §6 banner, D-04/D-08 rows, §9.4 gate states and §11.3 status. **50,246 → 69,052 bytes** |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | Working plan — **Appendix D (Amendment A-1)** added, append-only, plus in-place corrections | **WP-C.3** = **MP-41** room-scoped displays, **MP-42** estimated waiting time, **MP-43** refresh-on-change, **MP-44** facility-local operational day, **MP-45** facility-controlled public fields, **MP-46** read-only enforcement and denial accounting (**+7.5 eng-days**; 40 → 46 tasks; ≈ 65.5 → **≈ 73.0**); MP-40 extended to AC-15…AC-21; PO-02/PO-13 gate markers removed; sequencing rules 10–14; risks R-13…R-15; milestone conditions for M-9/M-10; §5.2 path, §10 deferral rows, §11 traceability, §12 placement row, Appendix A totals and Appendix C history corrected. **49,357 → 62,905 bytes** |
| `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | Working audit — **§15 (Amendment A-2)** appended | Decisions recorded; **all thirteen BR §33 items reconciled item-by-item** against the code with line evidence; **GAP-29…GAP-34** added; **GAP-28** restated as a delivery gap over MD-01…MD-19; unresolved items listed. **80,953 → 92,572 bytes** |
| `.clinerules` | Governance | §11: `plan/` added to the sanctioned subfolder list, with a sub-bullet recording the ratification, the closure of the deviation, and that no migration or manifest entry is needed |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Index | New annex section recording the four decisions, the file sizes above, which owner-controlled documents were **not** touched and why, and the D-5 position |
| `docs/implementation/AMSDP_PO13_Multi_Display_DQDS_Reconciliation_Report_V1.0.md` | New | This report |

**Not touched, deliberately:** `product/AMSDP_MVP_SCOPE_V1.0.md` / `V1.1`, `product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`, the master feature lists V2.0–V2.5, `architecture/AMSDP_System_Architecture_V1.0.md`, the ASCII UI/UX Blueprint, the demo documents, and the earlier multi-display report (V1.0). **MVP §16 needs no edit:** its §16.1 already places DQDS in Phase 1, and PO-02 removed the tier distinction rather than moving DQDS down. Its §16.5 "documented requirements only — not yet implemented" remains true.

---

## 4. Business Rules §33 — what it said, what it says now

**Before (the only offending text, identical in both copies, §33 lines 768–770):**

> DQDS, television integration and multi-display configuration are later-phase capabilities. Design the Phase 1 queue/token data model so DQDS can be added without redesigning the queue engine.

**That sentence was the whole conflict.** §33's numbered list already required multiple displays per branch (§33.2), per-display configuration (§33.3), configurable Bangla/English (§33.4), automatic refresh (§33.5), large typography (§33.6), token plus doctor/room (§33.7), estimated waiting time labelled as an estimate (§33.8–§33.9), no PII (§33.10), facility-controlled public information (§33.11), read-only access (§33.12) and tenant/branch scope (§33.13). The closing paragraph contradicted its own list — and, read out of context, let an agent defer the work.

**After:** the paragraph is gone, replaced by **§33.1 Scope status — PRODUCT OWNER DECISION PO-13 (24 November 2026)**, which states that the full capability is required for Hackathon delivery, restates the twelve required capabilities in the owner's own terms, forbids reduction ("No implementation agent may use earlier later-phase wording, an MVP-scope ranking, a roadmap position or any other document to reduce, defer or independently reinterpret this scope"), records PO-02's "no separate scope tiers", and keeps the security boundaries intact (server-side tenant/branch scope, 404-never-403, append-only audit, no patient identity on a public screen).

**Why both copies were edited.** `product/AMSDP_Business_Rules_V1.0.md` is the authoritative baseline (`.clinerules` §10) and `AMSDP_Business_Rules_V1.1.md` is its live counterpart. Editing one and leaving the other would have recreated exactly the inconsistency PO-02 forbids, because an agent reading the untouched copy would find the deferral wording intact. PO-02's instruction ("Business Rules §33 must be updated") was applied to both, with identical text.

**Every §33 item now maps to a requirement and a task** — §15.2 of the audit carries the table (implemented / partial / absent, with line-level evidence). The short version: 4 items implemented, 6 partial, 3 previously deferred and now required; **nothing in §33 is deferred any more**.

---

## 5. The plan and roadmap, reconciled against PO-13

| PO-13 capability | Requirement | Task | Phase |
|---|---|---|---|
| Multiple independently configured displays per branch, names, independent configuration | MD-01, MD-19 | **MP-35**, **MP-39** | 3 |
| Targeting by branch / doctor | MD-03, MD-09 | **MP-36** | 3 |
| Targeting by department | MD-04 | **MP-37** | 3 |
| **Targeting by room** | **MD-14** | **MP-41** | 3 |
| **Targeting by queue** | MD-15→ doctor-set interpretation, **OP-1** | **MP-41** scope values / MP-36 | 3 |
| Configurable Bangla and English on the display | MD-06 | **MP-38** | 3 |
| Server-side filtering, strict org/branch isolation | MD-03, MD-07, MD-09 | MP-36, MP-41, MP-46 | 3 |
| **Automatic refresh when information changes** | **MD-15** | **MP-43** (plus MP-36 for the limiter) | 3 |
| TV-scale typography | MD-11 | MP-38 | 3 |
| Current token plus doctor/room | MD-05, MD-11 | MP-37 | 3 |
| **Estimated waiting time, labelled, never guaranteed** | **MD-13** | **MP-42** | 3 |
| Token-only payloads, no PII | MD-07 | asserted in MP-36/41/42/45 tests | 3 |
| **Facility-controlled public information** | **MD-17** | **MP-45** | 3 |
| **Read-only public access, enforced** | **MD-18** | **MP-46** | 3 |
| Administrator configuration and audit logging | MD-08, **MD-19** | MP-39, MP-46 | 3 |
| **Facility-local operational day (MP-06)** | **MD-16** | **MP-44** (lands inside MP-06) | 3 |
| End-to-end demonstration of all of it | AC-01…AC-21 | **MP-40** (extended) | 6 |

**Totals after the amendment:** 46 tasks, **≈ 73.0 engineer-days** (V1.1 was ≈ 65.5; V1.0 ≈ 55). The multi-display block is 18.0 engineer-days (MP-35…MP-39 = 9.5, MP-40 = 1.0, MP-41…MP-46 = 7.5). Gates **PO-02** and **PO-13** are closed; every other gate is untouched; nothing starts before **MP-01**.

---

## 6. Implementation gaps and conflicts the reconciliation exposed

Six new gaps were added to the audit register (GAP-29…GAP-34). Each is a difference between an approved requirement and the code as it stands today, and each has one owning task.

| ID | Gap against the approved scope | Evidence in this tree | Task |
|---|---|---|---|
| GAP-28 | The multi-display capability as a whole — registry, resolution, scope, configuration — does not exist | no display table (17 revisions, head `c4d8e2a91f60`); one branch-wide route (`display.py:127`) | MP-35…MP-46 |
| **GAP-29** | **No estimated waiting time on the public board** | payload keys at `display.py:176-183`; the estimate formula exists only for PQV (`tracking.py:184-185`) | **MP-42** |
| **GAP-30** | **No room-scoped display, and no room in any display concept** | `facility_rooms` (`models.py:134`) and `doctor_branches.room_id` (`:425`) exist but `display.py` never reads them | **MP-41** |
| **GAP-31** | **No change signal or cache validator** — "refresh" is a timer, not change detection | `display.py:185-197`: fresh `200` every 10 s, no `ETag`, no version | **MP-43** |
| **GAP-32** | **The board's operational date is the container's local date** — wrong day between 00:00 and 06:00 Dhaka on a UTC container | `display.py:138` `date.today()`; `organizations.timezone` (`models.py:38`) never read | **MP-44** (with GAP-03, GAP-25) |
| **GAP-33** | **The facility cannot control what its screen publishes** | `display.py:174-183` publishes a fixed field set unconditionally | **MP-45** |
| **GAP-34** | **Read-only access and denial accounting are unproven** | `display.py:127` is GET-only by construction; no `queue.display.*` audit event exists anywhere | **MP-46** |

**Two conflicts were resolved by the decisions rather than by code:**

1. *BR §33 vs MVP §16 / PQV §B.6* — PO-02 removed the tier question; PO-13 fixed the scope. The audit's §5.2 reading of BR §33 as "later-phase" is corrected in §15.1. No document now says DQDS is deferred.
2. *"Later-phase" vs the roadmap* — the plan's V1.1 deferral row that carried ETA/countdown is amended (§10) so that ETA is no longer in a deferred row; only a per-second countdown remains out.

**One design conflict inside the requirements themselves** deserves recording: `.clinerules` §3 says denials are recorded, and BR §33.12 makes the board public and unauthenticated. Auditing every anonymous 404 would let any internet client write unbounded rows into an append-only audit trail — a denial-of-service against the audit record itself. **MD-19** reconciles them: authenticated denials audited; **disabled**-display requests logged once per display per 5 minutes with no client IP; unknown-code probes counted by the limiter and **not** audited. That is a deliberate, documented deviation from "record every denial", and it is listed in the specification's risk table (RMD-9) and in AC-21.

---

## 7. What remains unresolved

| Item | Who | Why it is not closed here |
|---|---|---|
| **OP-1** — PO-13 says targeting "by … queue", but AMSDP models no queue entity (`QueueEntry`, `QueueSequence` only) | Product Owner | Satisfied as the **doctor-set** target, documented as an interpretation. A named-queue entity would be a new table and a migration; inventing one unasked would exceed the brief |
| **OP-2** — BR §33.8 says "countdown"; PO-13 says "estimated waiting-time information" | Product Owner | MD-13 delivers a labelled minute estimate; a per-second countdown on a public screen manufactures precision the data does not support. Additive if the owner requires it |
| **MP-06** implementation | Engineering | Recorded as required compliance (BR §0 item 8). Not implemented; `display.py:138`, the queue path and the seed all still use server-local dates |
| **D-5** — index revision numbering and document recount | Product Owner | No version number was claimed by any document in this pass; the tree now holds **132** `.md` files under `docs/`; the annex does not advance the revision |
| **SMS half of PO-02** (BR §35/§36 vs MVP §16) | Product Owner | Only the DQDS half was decided |
| **GAP-20 / MP-25** — display and tracking limiters are in-process | Already on the roadmap | PO-13 does not authorise a durable limiter; the six-screen case is handled by re-keying, not by new infrastructure |
| Frontend board has **no component test** | Engineering | Folded into MP-38/MP-40 rather than creating a new task |
| Stray `<!-- ANCHOR -->` markers in four documents written elsewhere | Product Owner | Cosmetic; two apparent hits in this task's own files are quoted examples inside prose, verified |

**Nothing in this list blocks the plan.** It blocks only *claims*: none of it may be reported as done.

---

## 8. What was not done (and must not be reported as done)

- **No application code changed.** `git status --short` shows documentation only: `M .clinerules`, `M docs/AMSDP_Business_Rules_V1.1.md`, `M docs/product/AMSDP_Business_Rules_V1.0.md`, `M docs/governance/AMSDP_Docs_Index_V1.0.md`, `M docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` (the previous session's Appendix D), and untracked `docs/architecture/…Functional_Specification_V1.0.md`, `docs/audit/…Gap_Audit_V1.0.md`, `docs/plan/`, and the implementation reports. **No file under `backend/`, `frontend/`, `alembic/`, `docker-compose.yml` or `ai_factory/` is modified.**
- **No test suite was run**, no migration applied, no container started, no server contacted. Every task added by PO-13 is **NOT IMPLEMENTED**.
- **No commit, no staging** — the working tree is left exactly as found, plus documentation edits.
- **No scope reduction and no scope invention.** Nothing approved was deferred; nothing unapproved was added. The two places where the requirement could not be met literally (no queue entity; a per-second countdown) are recorded as interpretations **OP-1/OP-2** rather than silently resolved.

---

## 9. Governance and skill compliance (`.clinerules` §6)

| Requirement | How it was met |
|---|---|
| §1 — precedence | Explicit owner decisions (level 2) governed; verified code state (level 1) was measured before writing; no approved rule was silently overridden. The one conflict the code created (audit every denial vs an unauthenticated public endpoint) was **reported**, not quietly resolved — see §6 |
| §2 — automatic routing | Domains: requirements documentation, backend API, auth/RBAC, multi-tenant data, migrations, queue/workflow, audit, documentation governance. Each row's governance documents were read from the index before writing |
| §2 step 3 / §12 — read the index first | `docs/governance/AMSDP_Docs_Index_V1.0.md` read first, then the routed documents (BR §33 and §0, MVP §16, the DQDS specification, the plan, the audit, the QUE-006 gap analysis) |
| §3 — non-negotiables | No secret quoted (the demo credentials file was not opened); `organization_id` kept as the only tenant key in every schema statement; 404-never-403 stated as required behaviour in each tenancy criterion; audit trail described as append-only; no capability invented |
| §3 — "the UI is never the safety boundary" | MD-17 requires server-side suppression of disabled public fields; MP-45's risk cell and AC-19 assert the **raw response**, not the rendered page |
| §4 — domain routing | No skill row applied beyond governance documents, because none is installed |
| **§5 — skills** | **None installed.** Verified: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`. **No skill use is claimed anywhere in this task** |
| §6 — compliance reporting | This section |
| §7 — evidence standard | IMPLEMENTED / TESTED / VERIFIED / ACCEPTED kept distinct. "Implemented" is used only where a route or model is reachable; nothing in this task is TESTED or VERIFIED. The 24 board tests are **counted, not re-executed** |
| §9 — execution boundaries | No server, suite, migration or container executed; no destructive git command; outputs kept short |
| §10 — owner documents | BR §33 was edited **only** because PO-02 instructed it; every other owner-controlled document was read-only |
| §11 — document placement | This report is in `docs/implementation/`; each amendment sits in the document it belongs to. **The `docs/plan/` deviation is closed by owner ratification in this task**, `.clinerules` §11 updated, no migration performed, so no manifest entry. Nothing was overwritten, moved, renamed or deleted; amendments are append-only except the in-place corrections listed in §3 |

**Skills unavailable or not applicable:** all of them (none installed). **No CI gate, browser run, live API call or database read is claimed** for any DQDS capability in this report.

---

## 10. Validation actually performed (with results, not assurances)

| Check | Command / method | Result |
|---|---|---|
| BR §33 now carries the scope status in **both** copies | `Select-String` for `### 33.1 Scope status` in `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/AMSDP_Business_Rules_V1.1.md` | **2 hits** — both files |
| The two §33.1 blocks are the same text | block extracted from both files and compared case-sensitively | **identical, 3,433 characters** — no divergence between the authoritative copy and its V1.1 counterpart |
| No document still *states* DQDS is deferred | `Select-String -Path 'docs/**/*.md' -Pattern 'later-phase capabilities\|DQDS, television integration'` | **14 hits**, every one a **historical citation**, none operative: the two `§33.1` blocks (the decision that removed the sentence), the specification's §2.2 conflict description, the audit's original §5.2 row, eight lines in the V2.5 reconciliation drafts (untouched, they quote the conflict), and two lines in this report (§3, §4). **AC-22** in the specification now defines the check exactly this way |
| Requirement IDs exist and cross-reference | `MD-13…MD-19`, `AC-15…AC-22`, `MP-41…MP-46` searched in spec / plan / audit | MD-13…19: 33 / 9 / 17 hits · AC-15…22: 14 / 14 / 2 · MP-41…46: 13 / 33 / 16 — every ID appears in the specification and in the plan |
| Plan totals agree with the specification | Appendix A of the plan vs §E.8 of the specification | MP-41…MP-46 = **7.5** days in both; block total **18.0**; overall **≈ 73.0**; 46 tasks |
| Markdown tables intact | every line starting with `|` also ends with `|` in the four amended documents | **0 unclosed rows** in all four |
| Encoding | byte-level check on all eight touched files | **no BOM**, no `U+FFFD` replacement character, UTF-8 preserved (Bangla text in the specification renders as valid characters) |
| Changes are documentation-only | `git status --short` | **`M`**: `.clinerules`, both Business Rules files, the docs index, the QUE-006 gap analysis (previous session's amendment) · **`??`**: specification, gap audit, `docs/plan/`, three implementation reports. **No** `backend/`, `frontend/`, `alembic/` or infrastructure file |
| Tests | — | **None executed.** No claim of TESTED or VERIFIED is made for any capability in this task |

**What this validation does not prove.** It proves the documents are internally consistent, cross-referenced, well-formed and honestly scoped. It proves nothing about the product: no screen shows an estimate, no room display exists, no `304` is served, no facility-local date is used, and no display audit event is written. Those are MP-41…MP-46.

---

## 11. Document control

| Field | Value |
|---|---|
| Report | `docs/implementation/AMSDP_PO13_Multi_Display_DQDS_Reconciliation_Report_V1.0.md` |
| Version / date | 1.0 · 2026-11-24 |
| Author | Implementation agent (documentation only) |
| Reviewer | Product Owner |
| Supersedes | Nothing. It complements `AMSDP_Multi_Display_DQDS_Documentation_Update_Report_V1.0.md`, which recorded the earlier proposal stage; that report is preserved unchanged |
| Companion documents | `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` (Appendix E) · `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (Appendix D) · `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (§15) · `docs/product/AMSDP_Business_Rules_V1.0.md` (§33.1) |
| Index registration | Recorded in the annex of `docs/governance/AMSDP_Docs_Index_V1.0.md`; revision number deliberately not advanced (**D-5** open) |
| Next action | **Product Owner:** nothing further is required to unblock the plan — PO-13 and PO-02 are applied. **Engineering:** MP-01, then MP-06 with MP-44, then MP-35 → MP-36 → MP-41/42/43/45/46 → MP-37 → MP-38 → MP-39 → MP-40. **Owner, optional:** confirm **OP-1**/**OP-2**, settle **D-5** |

---

*End of document.*