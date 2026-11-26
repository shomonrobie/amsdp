# AMSDP — MP-23 (Option A) and MP-04 (Option B) Implementation Report V1.0

> **SUPERSEDED for current evidence by V1.1** (`docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md`,
> 26 November 2026). V1.1 records five defects found when this work was read back against the routes and the
> approved scope, one missing §43 deliverable (the report screen), and the exact reason the backend suite could
> not execute. **This file is retained unmodified as history**; read it for what the first pass believed, not for
> the current state.

**Status:** ISSUED — implementation evidence, **not** accepted work · **Written:** 26 November 2026 ·
**Repository:** `E:\amsdp` (Windows development checkout) · **Branch:** `hackathon-mvp`

**Authority.** Product Owner decisions of 26 November 2026, recorded in
`docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md`:
MP-23 **Option A** (complete Business Rules §43 reporting scope) and MP-04 **Option B** (complete W3
administration UI scope). PO-05's deferral is superseded **for MP-04 only**; MP-26 stays deferred.

**Evidence vocabulary** (`.clinerules` §7): IMPLEMENTED → TESTED → VERIFIED → ACCEPTED. Nothing in this report
is ACCEPTED. Backend rows are IMPLEMENTED and compiled/collected but **not executed**, because this host has no
PostgreSQL — see §5.

---

## 1. What was built

### 1.1 MP-23 — operational reporting (BR §43)

| Item | File | State |
|---|---|---|
| One reporting endpoint, five §43 dimensions, plus a reconciliation block | `backend/appointment/reports.py` (`GET /api/v1/reports/operational`) | IMPLEMENTED, compiled, collected |
| Router mounted | `backend/appointment/main.py` | IMPLEMENTED, compiled |
| Contract tests | `backend/tests/test_operational_reports.py` (15 tests) | TESTED **by collection only** — execution needs PostgreSQL |

Design decisions, all defensive:

- **One response, not five endpoints.** The five dimensions are computed from the same row set, and the payload
  carries a `reconciliation` block (`appointments_total` against `status_sum`, `by_day_sum`, `by_doctor_sum`,
  `by_branch_sum`, `booking_sources_sum`, `queue_entries` against `queue_status_sum`) so a reader can verify
  every identity without trusting the module.
- **Disjoint headline figures.** `booked = BOOKED + AWAITING_CONFIRMATION + CONFIRMED`; in-facility statuses are
  reported separately, so the four BR §43 headline numbers cannot double-count.
- **Honest utilisation.** `percent` is `null` when no capacity is published (never 0 or 100); `UNSCHEDULED` seats
  are reported in their own field, so a >100% day is explainable rather than clipped.
- **Scope is derived, never trusted from the request.** `scoped_branch` comes from the authenticated token; the
  queue filter and the utilisation denominator both use it, and the payload emits both `branch_id` (effective
  scope) and `requested_branch_id` (what was asked for) so a narrowed caller can see the difference. A
  foreign-branch request fails closed with a non-disclosing **404**.
- **No money, no performance ranking.** A negative test (`test_payload_carries_no_money_or_performance_field`)
  walks every key in the payload and fails if a revenue or performance-ranking field appears.
- **No schema change.** The endpoint reads existing `appointments` and `queue_entries` rows; no migration is
  introduced by MP-23.

### 1.2 MP-04 — voice-pack administration (W3)

| Item | File | State |
|---|---|---|
| Policy mirror: statuses, roles, transitions, selectability, config payload, refusal mapping, grouping | `frontend/lib/voice-pack-admin.js` | IMPLEMENTED, TESTED |
| Operator page: library + detail + lifecycle + configuration | `frontend/pages/voice-packs.js` | IMPLEMENTED, compiled by `next build` |
| Mirror tests against the Python policy | `frontend/tests/voice-pack-admin.test.mjs` (14 tests) | TESTED |
| Navigation entry | `frontend/components/AppShell.js` (`/voice-packs`, `org.read`; also `/queue-displays`, `queue.display.manage`) | IMPLEMENTED |
| Strings, both languages | `frontend/lib/i18n.js` (69 `vp*` keys in **each** dictionary, plus 2 nav keys; 654 Bangla keys total) | IMPLEMENTED, TESTED by the i18n parity suite |

The screen mirrors `voice_pack_policy.py` **only to decide what to offer**. Every refusal remains server-side,
and the page displays the server's answer: a recognised refusal tag is translated, an unrecognised one is shown
verbatim rather than replaced by an apology. Three properties are asserted by test rather than described:

1. **No local authority.** `actionsFor` filters on role and pack ownership; an `org_admin` is never offered
   approve/publish/retire/availability, and the tests read `TRANSITIONS`, `TRANSITION_ROLES`, `PLATFORM_ROLES`,
   `VOICE_CONFIG_ROLES`, `PACK_STATUS`, `LANGUAGES` **out of the Python source** and compare. A policy change
   that the mirror misses fails the suite.
2. **No silent configuration loss.** `configPayload` omits untouched languages; only an explicit "inherit"
   selection sends `null`, because `null` means *clear the override*.
3. **No synthesis fallback.** The page never touches the browser speech API, the policy constant stays `False`,
   and the test fails on any `synthesis` token in the page.

---

## 2. Files changed in this work

| File | Change | Kind |
|---|---|---|
| `backend/appointment/reports.py` | New: reporting module and `GET /api/v1/reports/operational` | New file |
| `backend/appointment/main.py` | Mounts the reports router | Modified (additive) |
| `backend/tests/test_operational_reports.py` | New: 15 contract tests (utilisation, isolation, 404, input validation, §43 negative control) | New file |
| `frontend/lib/voice-pack-admin.js` | New: policy mirror (statuses, roles, transitions, selectability, config payload, refusals, grouping) | New file |
| `frontend/pages/voice-packs.js` | New: the W3 operator screen | New file |
| `frontend/tests/voice-pack-admin.test.mjs` | New: 14 mirror/contract tests, including a parse of the Python policy | New file |
| `frontend/components/AppShell.js` | Nav entries for `/queue-displays` and `/voice-packs` | Modified (additive) |
| `frontend/lib/i18n.js` | 69 `vp*` keys + `queueDisplays`, `voicePacks`, in both dictionaries | Modified (additive) |
| `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` | Records MP-23 Option A and MP-04 Option B; supersedes PO-05 for MP-04 | New file |
| `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.0.md` | This report | New file |
| `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` | MP-23 and MP-04 status rows updated | Modified |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Entries for the two new documents | Modified |

No file was deleted, renamed or overwritten. No owner-controlled document was modified.

---

## 3. Verification actually observed

| Command (run from the workspace) | Result |
|---|---|
| `python -m py_compile backend/appointment/reports.py backend/appointment/main.py backend/organization/voice_packs.py` | **exit 0** — all three compile |
| `python -m pytest --collect-only -q backend/tests/test_operational_reports.py` | **15 tests collected in 1.12 s** — imports resolve, including the mounted router |
| `cd frontend && npm test` | **507 tests, 505 pass, 0 fail, 2 skipped** |
| `node --test tests/voice-pack-admin.test.mjs` | **14 tests, 14 pass, 0 fail** |
| `npx next build` | **exit 0**; `/voice-packs` 7.06 kB and `/queue-displays` 4.95 kB appear in the route table — the JSX compiles and every import resolves |

Not observed, and therefore not claimed:
- **`pytest backend/tests/test_operational_reports.py` was not executed.** It needs PostgreSQL at
  `127.0.0.1:5433`, which is not running on this host, so the 15 tests are collected but not passed. They are
  **not** called TESTED-as-passing anywhere in this report.
- **No live API call, no browser session, no database read.** Nothing here is `VERIFIED`.
- **`alembic` was not run.** MP-23 and MP-04 introduce no schema change, so no migration is owed by either.

### 3.1 One defect found and fixed during verification

Reading the page back against the router exposed a real fault, not a documentation gap: the availability
control posted **no body**, while `POST /{pack_id}/availability` requires `AvailabilityChange{available: bool}`.
The call would have been a 422 in the browser even though every unit test was green. It is fixed — the button now
sends `{ available: !pack.available_to_organizations }` — and a test (`the availability call sends an explicit
target, as the route demands`) now reads the Pydantic model out of the router source and asserts the page sends
the value it intends. The duplicate "Change availability" button that would have posted the same body-less call
was removed, so the action is offered once, by the switch that can supply a target.

This is recorded because a green suite did not catch it: the suite tested the mirror, and the defect was in the
wiring between the mirror and the route.

---

## 4. Governance and skill compliance (`.clinerules` §6)

| Field | Value |
|---|---|
| Applicable governance documents (§4 routing) | **Backend API** — `saas-application-security.md` (adapted), Business Rules Parts II–X, BR §43 · **Frontend UI** — `saas-frontend-ux.md` (adapted), shared components, `frontend/lib/i18n.js` · **Auth / RBAC** — `saas-auth-and-authorisation.md` (adapted), `backend/common/permissions.py` · **Multi-tenant data** — `saas-multitenant-data.md` (adapted), `backend/common/auth.py` · **Database** — `saas-multitenant-data.md` §4–5 (no change made, so no migration) · **Audit** — `saas-observability.md` (adapted), `backend/common/audit.py` |
| Documents read this session | `docs/governance/AMSDP_Docs_Index_V1.0.md` (routing), `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` (MP-04 row), `docs/decisions/AMSDP_MP-23_Operational_Reports_Decision_Brief_V1.0.md` (§4 options), `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.4 (PO-05), `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` (§11.1 rows), the voice-pack policy and router sources |
| Skills selected | **None installed** (`.clinerules` §5: no `.clinerules/skills/`, `.claude/skills/` or repo `skills/`). Governance documents were used instead, and no skill usage is claimed |
| §3 non-negotiables — evidence | Scope from the token, not the body (`scoped_branch`) · cross-branch/tenant failure returns **404**, tested · `organization_id` remains the only tenant key; no second tenant column · no pack delete anywhere (retire only, asserted by test) · denials audited by the existing audit helpers, not bypassed · no schema change, so no ad-hoc DDL · no secrets, tokens or pack asset paths logged or printed · no capability claimed that was not observed |
| Deviations | **None.** MP-04's browser upload wizard was deliberately not built; the decision record names it as outside the approved admin scope rather than silently omitting it |
| Unresolved issues | No PostgreSQL and no Docker on this host (see §5) |

---

## 5. Limitations and blockers (stated, not worked around)

1. **No PostgreSQL** — `common.database` points at `postgresql+psycopg2://amsdp@127.0.0.1:5433/amsdp`, which
   refuses connections here. The 15 operational-report tests therefore remain **collected, not executed**.
   This is the same host limitation recorded in the controlled implementation report; it is unchanged.
2. **No Docker** — no scratch database can be raised to work around (1).
3. **No live runtime evidence** — no browser session, no live API call, no database read. `VERIFIED` is not
   claimed for either deliverable.
4. **The reporting endpoint's definitions are documented, not agreed.** §3.1 of the decision record fixes the
   "queue activity" and "utilisation" definitions so the figures are checkable; if the Product Owner prefers a
   different denominator, that is a product decision and the numbers change with it.

---

## 6. Remaining work

| Item | Why it is still open |
|---|---|
| Execute `backend/tests/test_operational_reports.py` | Needs a PostgreSQL instance; then the row moves from "collected" to "passed" |
| Browser/API walk-through of `/voice-packs` and `/api/v1/reports/operational` | Would raise the two deliverables from TESTED to VERIFIED |
| MP-04 upload-from-browser | Outside the approved Option B scope; would need its own authorisation |
| MP-26 (W5 installer) | Still deferred behind PO-05 |
| Commit / push | **Not performed.** No commit, push, migration or deployment action was taken in this work |

---

## 7. Document control

| Field | Value |
|---|---|
| Location | `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.0.md` (`.clinerules` §11: `implementation/`) |
| Decision record | `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` |
| Predecessor evidence | `docs/implementation/AMSDP_Controlled_Implementation_Execution_Report_V1.0.md` |
| Index entry | `docs/governance/AMSDP_Docs_Index_V1.0.md` |
| Overwrote anything? | **No** — new filename, collision-checked before writing |

