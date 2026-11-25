# AMSDP — Multi-display DQDS Documentation Update — Task Report

> **Task ID:** `AMSDP-MULTI-DISPLAY-DQDS-SPEC-2026-11-24`
> **Version:** 1.0 · **Date:** 2026-11-24
> **Type:** Requirements / gap-assessment / documentation update — **no application code, schema, deployment or infrastructure was changed**
> **Branch:** `hackathon-mvp` at HEAD `a4ddc2c` (2026-11-23 20:21 +0600)
> **Owner:** Product Owner
> **Outcome:** Multi-display DQDS is now explicitly part of the Hackathon Version (Phase 3), specified in detail, classified against repository evidence, and carried into the master plan as tasks **MP-35…MP-40**. **It is not implemented**, and nothing in this task claims it is.
> **Later status (added 2026-11-24, not a rewrite):** the gates this report left open are now decided — **PO-13 APPROVED**, **PO-02 RESOLVED**, **MP-06 compliance required**, **`docs/plan/` ratified**. The scope was extended by **MD-13…MD-19 / AC-15…AC-22 / MP-41…MP-46** and the plan now totals **≈ 73.0** engineer-days. Read this report as the record of the proposal stage; the current state is in `AMSDP_PO13_Multi_Display_DQDS_Reconciliation_Report_V1.0.md`. Everything this report says about the code remains true.

---

## 1. Existing implementation — what actually exists

| Area | Evidence | Classification |
|---|---|---|
| Public board endpoint — one route, org+branch scoped, non-disclosing 404, 30 req/min per client IP, `public, max-age=10`, token-only payload | `backend/queuing/display.py` — 201 lines; router at `:24`; route at `:127`; limiter `:30-33,58-78`; allow-list `:176-191` | **Implemented — tested** (`backend/tests/test_dqds.py`, 465 lines, 24 tests) |
| Board page — 10 s poll, 404 state, stale banner + last known board, retry, BN/EN labels, per-device language | `frontend/pages/queue-display/[org]/[branch].js` — 198 lines; `:32` interval, `:84-113` loop, `:41-53` language chain | **Implemented** — no automated test; **browser-unverified in this session** |
| TV-size CSS | `frontend/styles/global.css:90-133` (card 1180 px, token 2.5 rem in a media query) | **Implemented — not tested** (no visual/resolution evidence) |
| Multiple screens | Any number of browsers can open the *same* branch URL — redundancy, not configuration | **Partially implemented** (not multi-display in any meaningful sense) |
| Per-display scope (doctors / department / room) | No display entity, no query parameter except `?lang=` (`[branch].js:44`) | **Not implemented** |
| Per-display language | Language is device-local (`localStorage`, staff session) | **Partially implemented** — wrong owner |
| Display registry / admin surface / audit | No `queue_displays` table in 17 Alembic revisions (head `c4d8e2a91f60`); no display capability in `common/permissions.py`; no admin page among 16 frontend modules | **Not implemented** |
| Room information on the board | `QueueEntry` (`common/models.py:854-884`) has no room; a doctor's chamber *is* available via `doctor_branches.room_id` (`:425-456`), rooms carry `floor_id`/`department_id` (`:134-161`) | **Not implemented** (derivable today for a *label*, not for a room-scoped queue) |
| Device registration / pairing / heartbeat | None anywhere | **Not found** — and none is claimed |
| Live-update transport | HTTP polling only; no `text/event-stream`, `EventSourceResponse` or `websocket` in `backend/**/*.py` | **Implemented as polling** |
| Operational day on the board | `display.py:138` uses `date.today()` instead of the facility's operational day | **Verified defect** (audit GAP-03, plan MP-06) |

**The one multi-display-specific defect found by measurement.** The limiter allows 30 requests/minute per client IP; a screen polls 6 times/minute. Four screens fit; **five sit exactly on the ceiling**; six are refused for part of every minute — so a facility behind one NAT would see intermittent 429s on some screens. This is the arithmetic of `display.py:30-33` against `[branch].js:32`, not a hypothesis.

## 2. Gaps

| Gap | Severity | Where recorded |
|---|---|---|
| Multi-display DQDS absent (registry, scope, per-display language, administration, limiter accounting) | **S2** | Audit **GAP-28** (§14.4) |
| Per-IP limiter cannot serve a multi-screen facility | folded into GAP-28 | Spec §9.2, plan MP-36 |
| Language belongs to the device, not the display | DQD-006 | Gap analysis Appendix D.2 → MP-38 |
| No display administration, no audit of display configuration | DQD-009, BR §34 | → MP-39 |
| Room on the queue entry (room-scoped queue) | DQD-002 | **Stays deferred** |
| Estimated wait / countdown, next-N tokens, display health, push transport, device provisioning | DQD-005, DQD-008, DQD-003 ext. | **Stay deferred** (spec §6, D-01…D-12) |

## 3. Hackathon scope now included

One facility runs several screens; each screen has its own **name, queue scope (whole branch, chosen doctors, or a department) and language**; every screen receives only its own slice of the live queue, server-side; no patient identity appears on any of them; configuration is an audited administrator act inside the facility's own organisation and branch.

Requirements **MD-01…MD-12** and acceptance criteria **AC-01…AC-14** are in the specification. Explicitly **out** of the hackathon scope: display health/heartbeat, device pairing, QR provisioning, push transport, ETA/countdown, next-N tokens, room on the queue entry, themes, per-display analytics. No new role, no new tenant column, no enterprise digital-signage features.

## 4. Documents changed

| Document | Change | Original content preserved |
|---|---|---|
| `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | **Created** (new) | n/a |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | **Created** as an amendment of V1.0: WP-C.2 (MP-35…MP-39), MP-40, gate PO-13, milestones M-9/M-10, assumptions A-6/A-7, risks R-11/R-12, sequencing rules 8–9, GAP-28 traceability, Appendix A/B/C updates | V1.0 kept untouched in the same folder |
| `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | **Appended §14 Amendment A-1**: F-53 reclassified (status unchanged), GAP-28 added (register now 28 gaps: S1 5 · S2 14 · S3 6 · S4 3), four evidence transcriptions corrected, PO-13 added, documents reconciled | Yes — append-only; no finding withdrawn, no severity lowered |
| `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` | **Appended Appendix D Amendment A-1**: OD-4 answered for the hackathon; effect mapped onto DQD-001…DQD-014 | Yes — append-only |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | **Registration appended** for the new specification, plan V1.1 and this report; amendment byte-sizes and the 130-file count recorded; revision number **not** advanced (**D-5** open) | Yes — append-only |
| `docs/implementation/AMSDP_Multi_Display_DQDS_Documentation_Update_Report_V1.0.md` | **Created** (this report) | n/a |

**Inspected and deliberately not modified:** `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/AMSDP_Business_Rules_V1.1.md` §33/§34/§53, `AMSDP_MVP_SCOPE_V1.0.md`/`V1.1` §7/§16, `AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` §B, `AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` C.13/E.13 (DQDS-001), `AMSDP_Complete_ASCII_UI_UX_Blueprint.md` §8.8/§13/§16, the master feature lists V2.0–V2.5 §25.4, `AMSDP_M7_Hackathon_Readiness_Report.md`, `AMSDP_MVP_Hackathon_Readiness_Assessment.md`, `AMSDP_Hackathon_Demo_Runbook.md`.

Why not modified:
- The product documents are **owner-controlled** (`.clinerules` §11) — read and cited, never edited. Their DQDS wording still says what it says; the conflict is recorded, not rewritten.
- The two readiness reports are **historical point-in-time audits** with no DQDS rows; amending them would fabricate a re-assessment that did not happen.
- The demo runbook gains a multi-display step only when the feature exists — MP-40, not now.

## 5. Why a new specification was necessary

No DQDS requirements document existed. The two candidates could not be cleanly extended: the Feature Catalogue's **DQDS-001** is an owner-controlled acceptance entry for the *single* board, and the Phase 3 **gap analysis** is a findings document (DQD-001…DQD-014) whose purpose is to record what is wrong. Extending either would have rewritten an approved acceptance row or a frozen audit. The specification instead **extends DQDS-001 by reference** (it does not restate its route, cache, rate-limit or 404 contract) and cites the gap analysis for evidence, so no requirement is duplicated and none conflicts.

## 6. Roadmap placement — confirmed

- **Phase 3 — Queue Operations, DQDS and QUE-006 Audible Announcements**: MP-35 (registry + migration), MP-36 (display resolution + server-side scope), MP-37 (department scope + room label), MP-38 (configured language + TV-scale presentation), MP-39 (capability, admin API/page, audit).
- **Phase 6 — End-to-End Integration, Demo Readiness and Acceptance**: MP-40 (multi-display demonstration inside the MVP §12 run and the rehearsals).
- **No phase was added, renamed, renumbered or reordered.** Phases 1, 2, 4 and 5 gain nothing.

## 7. Outstanding work (implementation and testing — not started)

| # | Work | Task | Blocked by |
|---|---|---|---|
| 1 | Display registry table, model, forward-only idempotent migration, tests | MP-35 | **PO-13** |
| 2 | Display resolution + server-side doctor scope in the public route, default board untouched, per-display limiter accounting | MP-36 | MP-35 |
| 3 | Department scope derivation + room label | MP-37 | MP-36 |
| 4 | Per-display language + TV-scale presentation + screenshots | MP-38 | MP-36 |
| 5 | `queue.display.manage`, admin API + page, audit events, copyable URL | MP-39 | MP-35, MP-36 |
| 6 | Six-screen load case, cross-scope silence, disabled display, stale/reconnect evidence | MP-40 | MP-35…MP-39, MP-06, MP-31 |
| 7 | Frontend tests for the board (currently none) | within MP-38/MP-40 | — |
| 8 | Operational-day fix on the same route | MP-06 | MP-01 |
| 9 | Seeded demo data: two displays, two doctors with different rooms, one department | within MP-35 | — |

## 8. Validation performed

| Check | Result |
|---|---|
| Application code unchanged | `git status` shows only documentation: `M` on the gap analysis and the docs index; new untracked specification, plan folder and this report. No file under `backend/`, `frontend/`, `_tools/`, `docker-compose.yml` or `alembic/` touched; nothing staged, no commit |
| Routes/limits cited | 1 route in `display.py`, 201 lines; limiter constants read at `:30-33`; polling interval read at `[branch].js:32` |
| Tests cited | `test_dqds.py` counted (465 lines, 24 test functions) — **not executed**; no pass is claimed |
| Display table absent | 17 Alembic revisions, single head `c4d8e2a91f60`, no display table |
| Push transport absent | No `text/event-stream`/`EventSourceResponse`/`websocket` in `backend/**/*.py` |
| Placeholder hygiene | 0 `<!-- ANCHOR -->` markers in every file written or edited by this task |
| Encoding | UTF-8 without BOM in all six files; `§`, `…`, `—`, `≈`, `→` render correctly in `read_files` |
| Markdown tables | Column-consistent in all five files (one intentional `\|` escape inside a table cell) |
| Cross-references | GAP-28 → MP-35…MP-40 resolves in three documents; MD-01…MD-12 → tasks resolves in plan §11; AC-01…AC-14 attached per task |
| Contradiction sweep | Plan V1.1 contains no remaining "deferred" row for multi-display; the only V1.0 wording left is inside the change-history row that describes V1.0 |
| Phase integrity | Phase names and order unchanged in the plan, the specification and the gap analysis amendment |

## 9. Governance and skill compliance (`.clinerules` §6)

| Requirement | How it was met |
|---|---|
| §2 — automatic routing | Domains identified: documentation, frontend UX, backend API, multi-tenant data, auth/RBAC, migrations, queue/workflow, audit. Each routed row's governance documents were read. |
| §2 step 3 / §12 — read the index first | `docs/governance/AMSDP_Docs_Index_V1.0.md` read before acting; the source documents were loaded from it and from §4 routing. |
| §5 — skills | **None installed** (no `.clinerules/skills/`, `.claude/skills/`, repo `skills/`). No skill use is claimed; governance documents were used instead. |
| §3 — non-negotiables | No secret or credential quoted. `organization_id` kept as the only tenant key. 404-not-403 written into MD-09/AC-05. Audit stays append-only: displays are disabled, not deleted. Every schema change specified as forward-only idempotent on the existing head. No capability claimed that does not exist — GAP-28 states the opposite. |
| §7 — evidence standard | IMPLEMENTED / TESTED / VERIFIED kept distinct: the board is implemented, its 24 tests are *recorded* as passing but were not run here, and the page is browser-unverified. Multi-display is NOT IMPLEMENTED everywhere it appears. |
| §9 — execution boundaries | No suite, server, container, migration or destructive git command was run. Read-only inspection only; write scope limited to `docs/`. |
| §11 — placement | Specification → `docs/architecture/` (sanctioned subject folder). Report → `docs/implementation/`. Plan → `docs/plan/`, the **recorded deviation** (owner-named folder; §11's list lacks it) now covering two files and flagged for ratification or migration with a manifest entry. Audit amendments appended to the existing audit files rather than creating parallel records. No document was moved, renamed, deleted or overwritten; V1.0 of the plan is preserved as issued. |
| §12 — index currency | Registration appended in the same task; revision number deliberately not advanced because **D-5** is open, consistent with the annexes already in the index. |

## 10. Document control

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-11-24 |
| Status | Task complete — documentation only |
| Author | Implementation agent |
| Reviewer | Product Owner |
| Companions | `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md`; `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`; audit §14 A-1; gap analysis Appendix D |
| Next action | Product Owner decides **PO-13** (and **PO-02**), then authorises **MP-01** and **MP-35** |

---

*End of document.*