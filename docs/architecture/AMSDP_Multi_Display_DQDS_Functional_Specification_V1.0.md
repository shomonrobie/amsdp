# AMSDP — Multi-display Digital Queue Display System (DQDS) — Functional Specification

> **Task ID:** `AMSDP-MULTI-DISPLAY-DQDS-SPEC-2026-11-24`
> **Version:** 1.0 · **Date:** 2026-11-24
> **Status:** **APPROVED SCOPE (PO-13 / PO-02, 2026-11-24) — a requirements specification, not an authorisation to build or deploy.** Appendix E carries the approved full scope (MD-13…MD-19, AC-15…AC-22) and supersedes the deferrals it names. Implementation still begins only when the Product Owner authorises **MP-01** and then **MP-35…MP-46**; approval of the scope authorises no code, migration or deployment by itself.
> **Feature class:** Hackathon Version — **Phase 3** (Queue Operations, DQDS and QUE-006), with end-to-end demonstration and acceptance under **Phase 6**. The six-phase sequence is unchanged; no phase is renamed, renumbered or added.
> **Owner:** Product Owner.
> **Companions:**
> - `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` — the owner-approved decision that classifies DQDS as MVP/P0 and places multi-display configuration inside the same capability (§B.6).
> - `docs/product/AMSDP_Business_Rules_V1.0.md` §33 (DQDS requirements), §34 (capability ownership), §53 (acceptance).
> - `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` — code-level DQDS findings **DQD-001…DQD-014** (OD-4 is the scope question this document answers for the hackathon).
> - `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` — F-46/F-53, GAP-03, GAP-28 (added by Amendment A-1).
> - `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` — tasks **MP-35…MP-40**.
> - `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` §13 (floor display management screens), §8 point 8 (multiple display support).
> **Scope boundary:** queue display only. This document does **not** authorise clinical modules, patient portals, device provisioning, digital-signage procurement or any change to the queue engine's semantics.

---

## 1. Purpose, and what this document is not

### 1.1 Why it exists

AMSDP already has a working public queue board: one read-only screen per branch, showing every active doctor in that branch. A real facility does not have one screen. It has a reception screen showing the general queue, a department screen showing only that department, a screen outside a particular chamber, and screens on different floors. Business Rules §33.2/§33.3 requires a facility to *"configure each display for relevant branch, rooms, doctors or queues"*, and the owner-approved PQV decision states that multi-display configuration is **part of the same MVP/P0 capability** as the board itself.

No document currently specifies *how many* displays, *what each one shows*, *who configures them*, or *what the hackathon must demonstrate*. Several documents assert the opposite — that multi-display is a later-phase capability. This specification resolves that for the hackathon scope, records what the code actually does today, and separates the minimum demonstrable capability from the enterprise digital-signage programme it must not become.

### 1.2 What it is not

- **Not an implementation report.** Nothing in §5 is built. The current-state section (§3) is evidence; the requirement sections (§5–§8) are specifications.
- **Not a duplicate DQDS specification.** The single-screen board and its acceptance criteria remain `AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` **DQDS-001**. This document extends that capability; it does not restate or revise DQDS-001's own contract (route, cache headers, rate-limit headers, 404 semantics, PII exclusion), which stay exactly as built.
- **Not a change to approved product decisions.** Where this document appears to disagree with an owner-controlled document, §2 records the conflict and the precedence; it does not settle the business question unilaterally.

## 2. Authority chain, scope conflicts and how they resolved

### 2.1 Precedence applied

Per `.clinerules` §1 (verified runtime state → owner instructions → governance → engineering rules) and the owner instruction of 2026-11-24 that places multi-display DQDS in the Hackathon Version under Phase 3:

| Rank | Source | What it says about multi-display |
|---|---|---|
| 1 | **Owner instruction, 2026-11-24** (this task) | Multi-display DQDS is an explicit feature of the Hackathon Version, principally Phase 3, demonstrated and accepted in Phase 6. |
| 2 | **PQV decision V1.0 §B.6** (owner-approved, 2026-11-08) | "DQDS is **MVP/P0**, with multi-display configuration part of the same capability." |
| 3 | **Business Rules §33.2, §33.3, §33.13** | A facility registers multiple displays; each is configured for branch/rooms/doctors/queues; every display feed is org- and branch-scoped. |
| 4 | **Business Rules §34** | *Display configuration* is an administrator capability, listed with staff management and token generation. |
| 5 | **Blueprint §8.8, §13.1–§13.3, §16 row 16** | Multiple displays per facility; authenticated display management with a directory, a configure form and display health. Rated **P0**. |
| 6 | **MVP Scope §16.1** (8-Nov addendum) | DQDS is Phase 1 (MVP), public, read-only, token-based, PII-free, org/branch-scoped. |
| — | **MVP Scope §7** lines 565–567 | Lists "Digital queue display/TV system", "Multi-screen display configuration" and "Public-facing queue screens" as **excluded** — superseded by §16 for DQDS. |
| — | **Business Rules §33** closing paragraph | "DQDS, television integration and multi-display configuration are later-phase capabilities." |
| — | **Master Feature List V2.0–V2.5 §25.4** | "Advanced multi-display DQDS management" is a later-phase enhancement. |

### 2.2 The three conflicts, and the boundary this specification draws

| # | Conflict | Resolution applied here | Remains owner territory |
|---|---|---|---|
| **C-1** | BR §33's closing sentence calls DQDS and multi-display *later-phase*; MVP §16 and PQV §B.6 make them MVP/P0. | MVP §16 is the later dated amendment and prevails (audit **PO-02**). DQDS is Phase 3, and multi-display is inside that capability. | The owner may instead rule that BR §33 prevails; that would reclassify **MP-35…MP-39** as ahead of phase. Recorded as **PO-02**. |
| **C-2** | V2.x §25.4 defers "**advanced** multi-display DQDS management". | The word *advanced* is the boundary: this document specifies a **registry, a scope filter, a per-display language, a presentation mode and an admin surface**. Health telemetry, device pairing, provisioning, push transport, theming and estimation stay deferred (§6) and remain the later-phase item. | Whether the deferral split is drawn at exactly this line — **PO-13**. |
| **C-3** | BR §34 names display configuration an administrator capability, but the nearest existing capability (`queue.manage`) is also held by `receptionist`. | A capability is added **inside the existing `queue.*` namespace** (`queue.display.manage`), which `org_admin` and `branch_admin` already hold through the `queue.*` wildcard (`common/permissions.py:207-218`). No new **role**; `DELEGABLE_CAPABILITIES` unchanged; a receptionist cannot configure a public display. | Whether receptionists should be able to *preview* an unlisted display (this document says no). |

**Nothing else in §3–§56 of the Business Rules is affected.** No rule is amended, waived or reinterpreted by this document.

---

## 3. Current implementation — evidence

Every statement below was read from this checkout (`hackathon-mvp`, HEAD `a4ddc2c`) during this task. Line numbers are to the working tree and will drift; the paths and function names are the stable anchors.

### 3.1 Implemented and tested in code

| Capability | Evidence | Status |
|---|---|---|
| Public branch-wide board endpoint | `backend/queuing/display.py:24` (`APIRouter(prefix="/api/v1/queue/display")`), `:127` (`@router.get("/{org_code}/{branch_code}")`) — **one route**, 201 lines | **IMPLEMENTED — TESTED** |
| Org+branch resolution; non-disclosing 404 for unknown/inactive org, unknown/inactive branch, or a branch of another org | `display.py:98-120` (`_not_found`, `_org_branch_or_404`), `:89-95` (`_active`) | **IMPLEMENTED — TESTED** (`test_dqds_unknown_org_404`, `test_dqds_unknown_branch_404`, `test_dqds_cross_org_404`, `test_dqds_inactive_org_404`, `test_dqds_inactive_branch_404`, `test_dqds_not_found_is_non_disclosing_and_uncacheable`) |
| Doctor-wise aggregation: currently-serving token (in-consultation preferred over called) and waiting count | `display.py:143-183` | **IMPLEMENTED — TESTED** (`test_dqds_serving_prefers_in_consultation`, `test_dqds_skipped_never_shown_as_serving`, `test_dqds_idle_doctor_not_listed`) |
| Token-only allow-list payload (`doctor_name`, `currently_serving`, `patients_waiting`) | `display.py:176-191` | **IMPLEMENTED — TESTED** (`test_dqds_no_pii`, `test_dqds_no_internal_helpers_leak`, `test_dqds_never_returns_tracking_material`) |
| Board data cacheable for 10 s; error responses `no-store` | `display.py:36-38`, `:193-197` | **IMPLEMENTED — TESTED** (`test_dqds_cache_headers`) |
| Rate limiting 30 req/min per client IP, with `X-RateLimit-*` headers and `Retry-After` on refusal | `display.py:30-33`, `:58-78` | **IMPLEMENTED — TESTED** (`test_dqds_rate_limit`, `test_dqds_rate_limit_headers`) |
| Browser board: 10 s polling, 404 state, stale banner, retry, BN/EN labels, per-device language choice | `frontend/pages/queue-display/[org]/[branch].js` (198 lines): `:32` `REFRESH_MS=10000`, `:84-113` fetch loop, `:90` 404 branch, `:101-107` stale flag, `:9-28` BN/EN dictionaries, `:41-53` language precedence | **IMPLEMENTED** — no automated test; **BROWSER UNVERIFIED** in this session |
| TV-scale CSS refinements inside a media query (card 1180 px, token 2.5 rem) | `frontend/styles/global.css:90-133` | **IMPLEMENTED** — **NOT TESTED**, no visual or resolution evidence |
| Test suite for the board | `backend/tests/test_dqds.py` — 465 lines, **24 tests**: active queue, empty queue, unknown org, unknown branch, cross-org, no-PII, rate limit, cache headers, non-active excluded, updates reflected, timezone today-only, other-org isolation, public no-auth, no helper leak, rate-limit headers, non-disclosing 404, inactive org, inactive branch, inactive doctor, cross-org doctor name, idle doctor, serving preference, skipped never serving, never returns tracking material | **TESTED** — recorded as passing; **not executed in this session** (§10.3) |

### 3.2 Partially implemented

| Capability | What exists | What is missing |
|---|---|---|
| **Multiple screens** | Any number of browsers may open the same branch URL. That is *redundancy*, not configuration: every screen shows the identical board. | No per-screen identity, name, scope, language or enable/disable state. Nothing distinguishes "Reception TV" from "Room 301". |
| **Queue scope** | The board is branch-wide: every active doctor of the branch appears (`display.py:143-152`). | No doctor subset, no department or room filter, no query parameter other than `?lang=` (`[branch].js:44`). |
| **Presentation** | Doctor name, now-serving token, waiting count, last-updated time, branch footer, BN/EN toggle. | No display name in the header, no room label (a queue entry has no room — see 3.4), no configured footer text, no per-display layout. |
| **Language** | Device preference chain: `?lang=` → `localStorage['dqds_locale']` → staff session `locale` → `bn` (`[branch].js:30,41-53`). | No facility or per-display language. Two screens in one branch cannot be configured to different languages without touching each device; clearing browser storage changes the board. |
| **Live update** | Polling every 10 s with an in-flight guard; a transient failure keeps the last board and raises the stale banner, and the next success clears it (`[branch].js:84-113`). | The limiter is keyed **per client IP** at 30 req/min. Five screens behind one NAT gateway generate ~30 requests/minute in steady state, so a sixth screen's requests are refused (§9.2, **GAP-28**). No push transport, no per-display liveness signal. |
| **Operation** | A stable, bookmarkable URL per branch. | No display-specific URL, no QR issuance, no pairing, no in-product kiosk guidance. |

### 3.3 Documented but not implemented

| Requirement | Source | Where it would live |
|---|---|---|
| Display directory with name, floor, type, status and per-display actions | Blueprint §13.1 | Frontend page — **absent** (`frontend/pages/` has 16 modules; none for displays) |
| Configure-display form: name, branch, floor, type, show/hide options, language, refresh mode | Blueprint §13.2 | **absent** |
| Display health: online/offline, last updated, last heartbeat, disable | Blueprint §13.3 | **absent** — no heartbeat column anywhere |
| Multiple displays per branch, each configured for rooms/doctors/queues; per-display language | BR §33.2–§33.4 | **absent** |
| Display configuration as an audited administrative act | BR §34, §40 | **absent** — no audit event, no capability |
| Public display management permission row | Blueprint §3052 table | **absent** from `backend/common/permissions.py` |

### 3.4 Not found / requires further verification

| Question | Finding |
|---|---|
| Is there a display table? | **No.** `backend/alembic/versions/` holds 17 revisions on a single head `c4d8e2a91f60`; none creates a display table, and searches for `queue_displays` / `display_screen` / `screen_config` return only the router line. `QueueEntry` (`common/models.py:854-884`) has no display or room column. |
| Is there a device-registration or pairing mechanism? | **No.** No pairing code, no device table, no client certificate, no heartbeat. |
| Is there a push or streaming transport (SSE/WebSocket)? | **No.** A search of `backend/**/*.py` for `text/event-stream`, `EventSourceResponse`, `websocket` returns nothing. The only live-update mechanism is HTTP polling. |
| Can a display be scoped to a room? | **Not through the queue.** `QueueEntry` carries `branch_id` and `doctor_id` only. A doctor's default chamber per branch **is** available (`doctor_branches.room_id`, `models.py:425-456`) and rooms carry `floor_id` and `department_id` (`models.py:134-161`), so a **doctor- or department-scoped display is derivable today**; a **room-scoped queue** needs DQD-002 first. |
| Does the board's day boundary work on a public screen? | **No** — `display.py:138` uses `date.today()` (container/UTC) instead of the facility's operational day (**GAP-03**, plan task **MP-06**). Between 00:00 and 06:00 Asia/Dhaka the board advertises the previous day. |
| Is the board reachable from a display device with no staff login? | **Yes** by design (unauthenticated, public). **No runtime verification** was performed in this session. |
| Is a display's language read from configuration? | **No.** `display.py` returns no language field; `organizations.locale` exists (`models.py:38`) and is unused by the board. |

**Classification summary.** Of the six capability areas in the task brief: **A** multiple display registration — *not implemented*; **B** queue scope/filtering — *not implemented* (branch-wide only); **C** display presentation — *partially implemented* (board exists; no display identity, room, or configured language); **D** live updates — *implemented for one board shape, partially adequate for many displays* (per-IP limiter ceiling, no liveness signal); **E** administration/access control — *not implemented* (no capability, no page, no audit); **F** display operation — *partially implemented* (one stable branch URL; no per-display URL, pairing or registration).

---

## 4. What the Hackathon Version must demonstrate

The hackathon claim is narrow and demonstrable: **one facility runs several screens, each configured for its own audience, each receiving only its own slice of the live queue, with no patient identity on any of them.**

| H# | Hackathon requirement (from the task brief) | Where it lands in §5 |
|---|---|---|
| **H-1** | One facility operates multiple DQDS screens | MD-01, MD-02 |
| **H-2** | Each screen has its own identifiable configuration | MD-01, MD-12 |
| **H-3** | Each screen displays the queue for its configured scope | MD-03, MD-04, MD-05 |
| **H-4** | Queue calls update the relevant screens | MD-10 |
| **H-5** | Bangla and English support where available | MD-06 |
| **H-6** | Public displays expose only appropriate queue information | MD-07 |
| **H-7** | Configuration respects organisation and branch boundaries | MD-09, MD-08 |

## 5. Hackathon scope, baseline — requirements MD-01 … MD-12

These twelve requirements were the whole of the scope when this document was first issued. **PO-13 (2026-11-24) extends them with MD-13…MD-19 in Appendix E**; where the two disagree, Appendix E governs. Anything in neither set is deferred (§6, as amended by E.2). Each requirement is written so that a test or an observation can fail it.

| ID | Requirement | Rationale (source) | Falsifiable check |
|---|---|---|---|
| **MD-01** | A branch can hold **any number of display configurations**, each with a unique code within the branch, a human name, an organisation, a branch, a language, a scope and an active/disabled state. Two displays in one branch are independent records. | BR §33.2; PQV §B.6; Blueprint §13.1 | Create two displays in one branch; both persist, both are listable, changing one leaves the other unchanged |
| **MD-02** | The public board resolves **a specific display** when one is named, and still serves the **branch-wide default** when none is named. The existing route keeps working unchanged. | Backward compatibility with DQDS-001 and `test_dqds.py` (24 tests) | The 24 existing tests stay green; a display-named request returns only that display's scope |
| **MD-03** | A display's scope may be **the whole branch** or an **explicit set of doctors**. Filtering happens **server-side**; the payload of a scoped display never contains an out-of-scope doctor. | BR §33.3; security rule that a public URL must not ship the whole branch for client-side filtering | Scope a display to one of two doctors with active queues; its payload lists exactly one doctor; the other doctor's token is absent from the raw HTTP response |
| **MD-04** | A display's scope may be a **department**, resolved through the doctors assigned to rooms in that department (`doctor_branches.room_id → facility_rooms.department_id`). If the mapping yields no doctors, the display shows the empty state — never the whole branch. | BR §33.3 ("relevant … rooms"); available data model, no new queue column | A department display lists only doctors whose assigned room belongs to that department; an empty department shows the empty state |
| **MD-05** | The board may publish a **room label** per doctor (the doctor's assigned chamber at that branch), and renders `—` where none is set. Room is facility information, never patient data. | BR §33.7, §33.9; Blueprint §13.2 "Show Room Number" | A doctor with an assigned room shows it; a doctor without one shows `—`; the payload still contains no patient field |
| **MD-06** | Each display has a **configured language** (`bn` or `en`) that the board uses when the device expresses no preference; `?lang=` remains an **operator override**; the staff session and `localStorage` stop overriding a configured display. | BR §33.4; DQD-006 | Two displays in one branch show different languages with no device change; clearing browser storage does not change a configured display's language; `?lang=en` still overrides |
| **MD-07** | **Token-only payload, unchanged.** No patient name, mobile number, age, patient id, appointment id, notes or tracking material ever appears in a display response — including in a scoped display and in error bodies. | BR §33.5; PQV §B.2; `.clinerules` §3 | A payload key-set assertion over every display variant; a seeded patient with a distinctive name does not appear in any response body |
| **MD-08** | Displays are managed by an **administrator capability** `queue.display.manage` inside the existing `queue.*` namespace, with **no new role** and **no change to `DELEGABLE_CAPABILITIES`**. Every create/update/disable is **audited** with actor, org, branch and before/after. | BR §34, §40; §2.2 C-3 | A receptionist receives 403; a branch admin succeeds; one audit row per change carrying before/after; the delegable list is byte-identical |
| **MD-09** | Every display operation is scoped to the **principal's organisation and branch** (taken from the token, never the body). Cross-organisation and cross-branch reads or writes return **404**, never 403. A **disabled** display 404s on the public route with the same body and headers as an unknown one. | `.clinerules` §3; BR §33.13; audit F-01/F-02 pattern | Cross-branch update → 404; cross-org display code → 404; disabled display → 404 identical to unknown; no existence oracle |
| **MD-10** | Live update keeps the **existing 10 s polling** and, for multiple screens, the limiter accounts **per display** rather than per client IP alone, so a facility behind one NAT can run several screens without self-inflicted 429s. Connection loss shows the stale banner and the last known board; the next success clears it. | BR §33.5 ("automatically refresh"); measured limiter arithmetic (§9.2) | Six concurrent pollers from one IP for ten minutes produce zero 429s; a killed network shows the stale banner within one poll interval; restoring it clears the banner without a reload |
| **MD-11** | Presentation: the display's **name** appears in the board header, the branch and last-updated time stay, and typography is **TV-scale** (token legible from the far side of a waiting room at 1920×1080). Labels exist in both languages. | BR §33.6; Blueprint §13.2; DQD-004 | Screenshot evidence at 1920×1080 and 1366×768; the token is the largest element; long doctor names wrap without overlapping the token |
| **MD-12** | Operation: each display has a **stable URL** that can be bookmarked on a kiosk browser. **No device pairing, registration or provisioning exists** and none is claimed; the document says so in-product and in the runbook. | Task brief §3.1 F ("do not assume a device-registration mechanism exists"); DQD-003 | The admin screen shows the display's URL and copyable link; documentation states plainly that binding a physical screen = opening that URL in a browser |

### 5.1 Data model (specification only — nothing here exists yet)

A table, not a JSON blob on `organizations.config`. Rationale: a display needs its own identity for auditing, its own enable/disable state, a per-branch uniqueness rule and a foreign key that makes a cross-tenant display *impossible* to store rather than merely unlikely to be written. The organization `config` JSON is untyped, cannot carry a FK, cannot carry a unique constraint, and — as recorded in the tenant specification — is behind a closed key whitelist.

```
queue_displays
  id               String  PK
  organization_id  String  FK organizations.id  NOT NULL      -- the only tenant key
  branch_id        String  FK branches.id        NOT NULL
  code             String(40)  NOT NULL                        -- stable URL token, e.g. "reception", "dept-cardiology"
  name             String(120) NOT NULL                        -- "Reception TV", "Room 301"
  language         String(2)   NOT NULL  default 'bn'          -- 'bn' | 'en'
  scope_type       String(20)  NOT NULL  default 'branch'      -- 'branch' | 'doctors' | 'department'
  department_id    String  FK facility_departments.id  NULL    -- required when scope_type = 'department'
  footer_text      String(160) NULL                            -- optional board footer, org-configured wording
  status           String(20)  NOT NULL  default 'active'      -- 'active' | 'disabled'
  created_by       String  FK staff_users.id  NULL
  created_at       DateTime(timezone=True)
  updated_at       DateTime(timezone=True)
  UNIQUE (branch_id, code)
  INDEX  (organization_id), (branch_id)

queue_display_doctors            -- membership for scope_type = 'doctors'
  display_id  String  FK queue_displays.id  NOT NULL
  doctor_id   String  FK doctors.id         NOT NULL
  PK (display_id, doctor_id)
```

Rules that the schema and the resolver must both enforce:

1. `organization_id` is derived from the branch, not from the requester; the resolver checks `branch.organization_id == display.organization_id` and refuses otherwise.
2. `scope_type = 'doctors'` with an empty membership list is **an empty display**, never "all doctors" — a configuration mistake must not widen a public feed.
3. `scope_type = 'department'` requires `department_id` belonging to the same organisation; otherwise the write is a `422`.
4. Changing `scope_type` clears the now-irrelevant configuration in the same transaction (no orphaned membership rows that could later re-widen the feed).
5. The migration is **forward-only and idempotent**, on the single head `c4d8e2a91f60`, with nullable/defaulted columns so historic data is untouched. No existing table is altered by MD-01; the room label of MD-05 is a *read*, not a column.
6. Deleting a display is **not** offered in the hackathon scope: a display is disabled (`status='disabled'`), which 404s publicly and keeps its audit trail. Deletion would orphan audit rows — the audit trail is append-only (`.clinerules` §3).

### 5.2 Public contract

| Aspect | Specification |
|---|---|
| Route (new) | `GET /api/v1/queue/display/{org_code}/{branch_code}?display={code}` |
| Route (existing, unchanged) | `GET /api/v1/queue/display/{org_code}/{branch_code}` — the branch-wide default; must keep behaving exactly as today, including its 404/429/cache contract |
| Why a query parameter and not a path segment | The Next.js pages router already owns `pages/queue-display/[org]/[branch].js`; a sibling `[branch]/[display].js` would collide with the same route specificity. A query parameter also keeps the CDN cache key distinct per display without relying on `Vary` |
| Payload additions | `display: {code, name, language, scope_type}` and, per doctor, `room_name` (nullable). Everything else stays as built |
| Payload invariant | The allow-list stays hand-built. No ORM row, no aggregation state, no membership list is ever serialised |
| Unknown / disabled display | `404` with the same body and headers as an unknown branch (`no-store`), never `403`, never a different message |
| Unknown org / branch | `404`, non-disclosing, as today |
| Cache | `public, max-age=10` on a successful board; `no-store` on every error |
| Rate limit | Per display and per client, see MD-10 and §9.2 |
| Authentication | None. The display is public by design; a display code is **not** a secret and must not be treated as one (it grants access to the same token-only data as the branch board) |

### 5.3 Administrative contract

| Aspect | Specification |
|---|---|
| Routes | `GET /api/v1/queue/displays` (list, branch-scoped) · `POST /api/v1/queue/displays` · `PATCH /api/v1/queue/displays/{id}` (name, language, scope, membership, footer, status) |
| Capability | `queue.display.manage`, added to the `queue.*` namespace; effective for `org_admin` and `branch_admin` through the existing wildcard, **not** granted to `receptionist`, `doctor` or `assistant` |
| Scope source | The principal's organisation and branch come from the authenticated token (`AuthContext`), never from the request body; a branch-scoped principal cannot read or write another branch |
| Cross-boundary behaviour | Another organisation's display id, or another branch's display id → `404` (non-disclosing), never `403` |
| Audit | One event per write: `queue.display.created`, `queue.display.updated`, `queue.display.disabled` / `.enabled`, with actor, organisation, branch, display code and before/after scope |
| Validation | `422` for: duplicate code in the branch, unknown/other-branch doctor in the membership, missing `department_id` for a department scope, `language` outside `{bn,en}`, `scope_type` outside the three values |
| Frontend | One page listing the principal's branch displays with create/edit/disable and a **copyable display URL**; no dead controls — anything shown must work |
| Not in scope | No pairing screen, no heartbeat, no "preview as" impersonation, no role creation |

### 5.4 Presentation

- The header carries the **display name** (e.g. "রিসেপশন ডিসপ্লে / Reception Display") above the organisation and branch, so a technician standing in front of a screen knows which configuration it is running.
- Per row: doctor name, now-serving token, waiting count, and — when known — the room label. The room is rendered as facility information, never as "patient X to room Y".
- The **token is the largest element** on the screen (`clamp()` typography driven by viewport, minimum ≈ 4 rem at 1920×1080); the layout must not cap the card at a laptop width.
- Both language dictionaries must be complete for every new label; a missing key falls back visibly, never to an empty string.
- The existing states are retained unchanged: loading, empty queue, invalid address, transient error with retry, stale-but-showing. The stale state must state the last update time.
- Privacy is a layout rule, not only a payload rule: no field that could identify a patient is rendered, including in the empty/error states.

### 5.5 Language precedence

| Rank | Source | Applies when |
|---|---|---|
| 1 | `?lang=bn\|en` | An operator deliberately previews a language on one device |
| 2 | **Display configuration** (`queue_displays.language`) | Always, when a display is resolved |
| 3 | Branch organisation locale (`organizations.locale`) | Only for the branch-wide default board with no display configuration |
| 4 | `bn` | Fallback |

`localStorage['dqds_locale']` and the staff session locale **stop taking precedence over a configured display**. They may remain as the *initial suggestion* only when no display is resolved, which keeps the current behaviour of the default board intact. The language toggle in the header remains available but must no longer persist a value that outranks configuration — a display is set up once, centrally, and stays that way after a power cut.

### 5.6 Live update and reliability

| Aspect | Specification |
|---|---|
| Transport | HTTP polling, 10 s interval, unchanged. No SSE/WebSocket is introduced: it would add a stateful connection layer to a stateless public endpoint and is not needed to demonstrate multi-display operation |
| Multi-screen load | A facility with *n* screens issues `6n` requests/minute. The limiter must not refuse the facility's own screens (see §9.2); the bucket is keyed per display code plus client, with a floor that accommodates a branch's configured displays |
| Late join | A screen powered on mid-day renders the current board on its first poll — no warm-up, no history replay |
| Loss of connectivity | The stale banner appears on the first failed poll and the last known board stays on screen; the next success clears it without a reload. A 429 or a 5xx is a *failure*, never an empty queue |
| Reconnect | Polling continues; there is no backoff in the hackathon scope (documented as a limitation, not a defect) |
| Clock | The board shows the facility-local last-updated time; the day boundary follows the facility's operational day (**MP-06**), not the container date |
| Honesty | The board must never claim "live" while showing stale data — that is what the banner is for |

### 5.7 How a physical screen is bound to its configuration

There is no pairing, registration, certificate or provisioning protocol, and this specification does not invent one. The hackathon operating model, to be documented for the operator, is:

1. An administrator creates the display in AMSDP and copies its URL: `https://<host>/queue-display/<org>/<branch>?display=<code>`.
2. The screen device (TV with a browser, mini-PC, or the built-in TV browser) is set to open that URL in full screen / kiosk mode.
3. The device is not authenticated, holds no credential and needs no network configuration beyond reaching the site.
4. Losing the URL is recoverable from the admin page; a device can be re-pointed at any time without touching the database.
5. **Consequence to record honestly:** the system cannot detect whether a screen is switched on, and it cannot revoke a device — disabling the configuration is the only revocation, and that 404s the URL. Health/heartbeat is deferred (§6, D-01).

---

## 6. Deferred beyond the Hackathon (do **not** implement under this specification)

> **Amended by Appendix E (PO-13, 2026-11-24):** **D-04 is withdrawn** (estimated waiting time is now requirement MD-13) and **D-08 is split** (room targeting and the room label are now MD-05/MD-14; only `QueueEntry.room_id` and room-scoped token numbering stay deferred). Read E.2 before acting on any row below.

| ID | Item | Why it is deferred | Decision owner |
|---|---|---|---|
| **D-01** | Display health: last-seen heartbeat, online/offline, server-side last-updated, disable-from-health-screen | Needs a heartbeat endpoint, a liveness budget and a retention policy; nothing in the hackathon's value claim depends on it | Product Owner (post-hackathon) |
| **D-02** | Display preview inside the admin page, and QR-code issuance for a display URL | The URL is copyable and QR printing is a device concern; Blueprint §13.2 asks for Preview, but it is an ergonomics feature | Product Owner |
| **D-03** | Floor and department topology management screens for displays | Requires the facility hierarchy to be curated first; the hackathon derives the department from existing room assignments | PO-04 family |
| **D-04** | ~~Estimated waiting time / countdown per display~~ | **WITHDRAWN by PO-13.** Estimated waiting time is requirement **MD-13**; only a per-second *countdown* remains out (E.7) | Product Owner (decided 2026-11-24) |
| **D-05** | "Next N tokens" list per display | Every token list increases what a public screen shows; needs a privacy review of the *audience*, not only the payload | Owner |
| **D-06** | Push transport (SSE/WebSocket) and differentiated refresh rates | Polling at 10 s is sufficient to demonstrate live multi-display; a stateful transport is an infrastructure programme | Owner |
| **D-07** | Durable, multi-process rate limiting | Already tracked for the tracking endpoint as **GAP-20 / MP-25**; the display shares the limitation | Owner |
| **D-08** | Room on the queue entry (`QueueEntry.room_id`) and room-scoped token numbering | DQD-002 and GAP-07 / MP-11: a queue-model change, not a display change. **Split by PO-13:** room *targeting* and the room *label* are in scope (MD-05, MD-14); the `room_id` column and room-scoped numbering stay deferred | Owner (PO-04) |
| **D-09** | Per-display themes, layouts and the "show/hide" option matrix (Blueprint §13.2 checkboxes) | §5.4 fixes the presentation for the hackathon; a toggle matrix is configuration surface without a proven need | Owner |
| **D-10** | Silent-signage provisioning, device management, remote reload, HDMI/CEC control | Hardware and operations programme; explicitly outside this repository | Owner |
| **D-11** | Per-display analytics (impressions, screen-uptime reporting) | Depends on D-01 and on the unapproved analytics specification (**PO-06**) | Owner |
| **D-12** | Platform-admin cross-organisation display provisioning | `platform.*` capabilities are reserved; nothing in the hackathon needs a platform operator to touch a tenant's screens | Owner |

**Deliberate non-goals, restated:** no new role, no new tenant column, no patient identity on any screen, no enterprise digital-signage features, no device pairing.

---

## 7. Roadmap placement

The six-phase roadmap is unchanged. This feature is **Phase 3** work with **Phase 6** demonstration and acceptance.

| Phase (as established) | This feature's part |
|---|---|
| **Phase 1 — Operational RBAC and Platform Identity Separation** | Nothing new. The capability lands in the existing `queue.*` namespace; no role or identity change |
| **Phase 2 — Appointment and Calendar Reliability** | Nothing new |
| **Phase 3 — Queue Operations, DQDS and QUE-006 Audible Announcements** | **MD-01 … MD-12** — display registry, scope resolution, room label, per-display language, limiter accounting, presentation and admin surface. Tasks **MP-35 … MP-39** |
| **Phase 4 — Patient Tracking and Staff Handoff** | Nothing new (PQT is a separate surface) |
| **Phase 5 — Dashboard, Reporting and Localization** | The i18n unification (**MP-28**) supplies the shared mechanism this feature consumes; no multi-display requirement is added there |
| **Phase 6 — End-to-End Integration, Demo Readiness and Acceptance** | Multi-display is a **demonstration step and an acceptance item**: task **MP-40**, executed inside the MVP §12 end-to-end run (**MP-31**) and the rehearsals (**MP-32**) |

**Task mapping (plan V1.1).**

| Task | Requirement | Phase |
|---|---|---|
| **MP-35** | MD-01 — registry table, model, idempotent migration, unit tests | 3 |
| **MP-36** | MD-02, MD-03, MD-09 — display resolution and server-side doctor scope in the public route, default board untouched | 3 |
| **MP-37** | MD-04, MD-05 — department scope derivation and the room label | 3 |
| **MP-38** | MD-06, MD-11 — configured language and TV-scale presentation | 3 |
| **MP-39** | MD-08, MD-12 — capability, admin API, admin page, audit events, copyable URL | 3 |
| **MP-40** | MD-10 plus the whole set — multi-display end-to-end demonstration, six-screen load and stale/reconnect evidence | 6 |

`MP-06` (operational day, GAP-03) remains a prerequisite: a multi-display demonstration that shows yesterday's queue between midnight and 06:00 Dhaka would fail its own acceptance.

---

## 8. Acceptance criteria

Failable by design. A criterion is met only by an artefact named against it, per `.clinerules` §7 — a green suite alone is **TESTED**, not **VERIFIED**.

| ID | Criterion | Evidence required |
|---|---|---|
| **AC-01** | Two displays exist in one branch with distinct codes, names and languages; each is readable and independently editable | API list response, admin page screenshot |
| **AC-02** | A doctor-scoped display returns only its doctors; the other doctor's token appears nowhere in the raw response | HTTP body captured for both displays |
| **AC-03** | A department-scoped display resolves through room→department assignment and shows only those doctors; an empty department shows the empty state | Two HTTP bodies plus the seed data used |
| **AC-04** | The branch-wide default board is unchanged and the existing 24 board tests are green | `pytest` summary line quoted verbatim |
| **AC-05** | A cross-branch display id and a cross-organisation display code both return `404`; a disabled display returns the same `404` body and headers as an unknown one | Four request/response captures |
| **AC-06** | A receptionist's write attempt is refused server-side; a branch admin's succeeds; the audit trail holds exactly one row per write with before/after | Status codes plus the audit rows |
| **AC-07** | No display response contains patient identity or tracking material, for any scope type | Key-set assertion test, plus a seeded distinctive patient name absent from every body |
| **AC-08** | Two displays configured `bn` and `en` render different languages with no device change; clearing storage changes nothing; `?lang=en` overrides | Two screenshots plus a cleared-storage screenshot |
| **AC-09** | Six concurrent pollers from one client IP run ten minutes with no 429, while an abusive single client is still refused | Load-script output plus the limiter's refusal case |
| **AC-10** | Network loss raises the stale banner with the last update time and the last known board; restoring it clears the banner without a reload | Screenshot sequence or recording |
| **AC-11** | At 1920×1080 the token is the largest element and readable across a waiting room; long doctor names do not overlap it; a 1366×768 layout is also recorded | Screenshots at both resolutions |
| **AC-12** | A queue call made on the staff board appears on the in-scope display and does **not** appear on an out-of-scope display within two poll intervals | Two recordings or timestamped screenshots |
| **AC-13** | No new role exists, `DELEGABLE_CAPABILITIES` is unchanged, and `organization_id` remains the only tenant key | `git diff` of `common/permissions.py` and `common/models.py` |
| **AC-14** | The migration applies cleanly to a database at `c4d8e2a91f60`, is idempotent, and alters no existing table destructively | `alembic upgrade head` log on a scratch database, `alembic current` output |

**Not acceptance criteria:** "the page looks right", "the demo ran once", "tests pass somewhere". Each is either unverifiable or already covered above.

---

## 9. Dependencies, risks and open decisions

### 9.1 Dependencies

| Depends on | Why |
|---|---|
| **MP-06** (operational day, GAP-03) | A display that shows yesterday's queue is wrong regardless of how many screens exist |
| **MP-01 / MP-02** (runtime restored, suite re-baselined) | No demonstration and no "tests are green" claim is possible before them |
| `facility_rooms` / `facility_departments` / `doctor_branches.room_id` data | Department scope and the room label are *derived*; empty data yields an empty display, which is correct but unconvincing in a demo — seed it |
| **MP-28** (i18n unification) | Not a blocker: the board carries its own BN/EN dictionary today. After MP-28 it consumes the shared mechanism; two dictionaries must not be left behind |
| Existing `queue.*` capability namespace and `AuthContext` | MD-08/MD-09 use them unchanged |

### 9.2 Measured constraint that shaped MD-10

`display.py:30-33` sets `_DQDS_RATE_LIMIT = 30` requests per `_DQDS_RATE_WINDOW = 60.0` seconds, keyed by `request.client.host` (`:58-78`). The board polls every 10 s (`[branch].js:32`), i.e. **6 requests/minute per screen**. Therefore:

- 1 screen → 6 req/min, comfortable.
- 4 screens → 24 req/min, still under the ceiling.
- **5 screens → 30 req/min — at the ceiling**, and with any retry or manual reload the limiter refuses with `429` + `Retry-After`.
- 6 screens → 36 req/min → **guaranteed refusals** for part of every minute, and a facility whose screens share one NAT address looks like one abusive client.

This is not hypothetical: it is the arithmetic of the current constants. Six screens behind one public IP would show intermittent 429s on some screens while others worked — the exact failure mode a demonstration must not have. MD-10 therefore requires the bucket to account per display, and MP-36 owns the change with a test reproducing the six-screen case.

### 9.3 Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **RMD-1** | Scope filtering is implemented client-side, shipping the whole branch to a public URL | Medium | High | MD-03 requires server-side filtering; AC-02 asserts the raw response, not the rendered page |
| **RMD-2** | Display configuration drifts into a signage product (themes, assets, device fleet) | Medium | Medium | §6 fixes the deferral list; PO-13 ratifies the boundary |
| **RMD-3** | A department filter silently falls back to "all doctors" when the mapping is empty | Medium | High | MD-04 and data-model rule 2: empty means empty; a test asserts it |
| **RMD-4** | A new role or delegable grant is introduced "to make the admin page work" | Low | High | MD-08 / AC-13: capability inside `queue.*`, delegable list untouched, diff-checked |
| **RMD-5** | The display code is treated as a secret and used as an authorisation token | Medium | High | §5.2: a code is not a secret; exposure is bounded by the token-only payload; disabling is revocation |
| **RMD-6** | Multi-display work is claimed as delivered without a live six-screen run | Medium | High | AC-09/AC-12 need artefacts; MP-40 reports BLOCKED rather than passed if the environment cannot host six clients |

### 9.4 Open decisions — Product Owner only

| Gate | Question | Effect if decided the other way |
|---|---|---|
| **PO-02** | Does MVP §16 + PQV §B.6 prevail over BR §33's "later-phase" sentence for DQDS and multi-display? | **DECIDED 2026-11-24 — RESOLVED in favour of DQDS.** No MVP/Later-Releases tier governs; BR §33 now carries the §33.1 scope status (Appendix E, E.1) |
| **PO-13** | Ratify the split between the hackathon minimum (§5) and "advanced multi-display DQDS management" (§6), and authorise MP-35 as Phase 3 work | **DECIDED 2026-11-24 — APPROVED as full-featured multi-display DQDS.** The split is superseded by Appendix E: MD-13…MD-19 added, D-04 withdrawn. Scope approved; code still unauthorised until MP-01 and MP-35 are authorised |
| **PO-04** (adjacent) | Phase assignment for priority, overbooking and subscription — unchanged by this document | None for displays; recorded for accuracy |
| **OD-4 residue** (gap analysis) | Whether room-scoped *queue numbering* and estimated wait belong in Phase 3 | Affects D-04/D-08 only; the hackathon minimum does not need them |

---

## 10. Governance and skill compliance

### 10.1 Documents read for this specification (`.clinerules` §2 step 3, §12)

`docs/governance/AMSDP_Docs_Index_V1.0.md` first, then: `docs/product/AMSDP_Business_Rules_V1.0.md` §33–§34, §40, §53 and the closing paragraph of §33; `docs/product/AMSDP_MVP_SCOPE_V1.0.md` §7, §16; `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` §A–§C; `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` C.13/E.13 (DQDS-001); `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` (DQD-002/003/004/005/006, OD-4); `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` (F-46, F-53, GAP-03); `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.0.md`; `docs/AMSDP_Complete_ASCII_UI_UX_Blueprint.md` §8.8, §13.1–§13.3, §16 row 16, the permission table row for public display management.

### 10.2 Skills

**No skill is installed** in this workspace (no `.clinerules/skills/`, `.claude/skills/` or repository `skills/`), and no skill use is claimed. The governance documents above and the repository evidence were used instead.

### 10.3 Non-negotiables and evidence standard

| Rule | How it was met |
|---|---|
| `.clinerules` §3 — no secrets, no invented capability | Nothing is built or claimed as built; §3 states the current state with `file:line`; no credential appears |
| `.clinerules` §3 — UI is never the boundary; server-side enforcement | MD-03, MD-09 and RMD-1 require server-side scope and tenancy enforcement; AC-02 inspects the raw response |
| `.clinerules` §3 — 404 not 403 across tenants/branches | MD-09 and AC-05 |
| `.clinerules` §3 — `organization_id` is the only tenant key | §5.1 schema; AC-13 |
| `.clinerules` §3 — audit append-only; denials recorded | MD-08 adds write events; deletion is replaced by disable (§5.1 rule 6) |
| `.clinerules` §3 — forward-only idempotent migration | §5.1 rule 5, AC-14 |
| `.clinerules` §7 — IMPLEMENTED ≠ TESTED ≠ VERIFIED | §3 distinguishes the two tested facts from the untested page; the 24 board tests are recorded as previously reported, **not executed in this session** |
| `.clinerules` §9 — no execution | No suite, container, migration, server or git state change was performed. Read-only commands only (`Get-ChildItem`, `Select-String`, `Get-Content`, `git status`/`log`) |
| `.clinerules` §11 — placement | Written to `docs/architecture/`, a sanctioned subject folder. No existing document was moved, renamed or overwritten |

### 10.4 Boundaries observed for this task

- **No application code was changed.** No file under `backend/`, `frontend/`, `docker-compose.yml`, `_tools/` or `alembic/` was modified.
- **No database, deployment, infrastructure or git history change.** Working tree changes are documentation only (`git status` in §11.2).
- **No approved product-owner decision was altered.** BR, MVP Scope, PQV and the Master Feature List were read, never edited; the conflicts they create are recorded, not re-written.
- **No phase was renamed, renumbered or added.** Multi-display is Phase 3 with Phase 6 acceptance.

---

## 11. Document control

### 11.1 Change history

| Version | Date | Change | Author |
|---|---|---|---|
| **1.0** | 2026-11-24 | First issue. Defines multi-display DQDS for the Hackathon Version: evidence-based current state (§3), hackathon minimum MD-01…MD-12 (§5), deferrals D-01…D-12 (§6), Phase 3/Phase 6 placement (§7), acceptance AC-01…AC-14 (§8), the measured limiter constraint (§9.2), and owner gates PO-02/PO-13 (§9.4) | Implementation agent (read-only assessment) |

**Change rule.** Amendments create a new version with a new row in this table. A task is never silently re-scoped: if implementation discovers that a requirement is wrong, the requirement is amended here and the plan task's acceptance criterion is updated in a new plan version.

### 11.2 Verification performed while writing this document

| Check | Result |
|---|---|
| Repository state | branch `hackathon-mvp`, HEAD `a4ddc2c` (2026-11-23 20:21 +0600); `git status` shows the documentation work of this task only — no modified application file, nothing staged |
| Route count in `backend/queuing/display.py` | 1 (`GET /{org_code}/{branch_code}`); file 201 lines / 8,159 bytes |
| Board tests | `backend/tests/test_dqds.py`, 465 lines, 24 `def test_` functions — **counted, not executed** |
| Board page | `frontend/pages/queue-display/[org]/[branch].js`, 198 lines / 8,508 bytes |
| Display tables | none — 17 Alembic revisions, single head `c4d8e2a91f60`, no display table |
| Push transport | none — no `text/event-stream`, `EventSourceResponse` or `websocket` anywhere in `backend/**/*.py` |
| Capability for displays | none — `common/permissions.py` has no display capability; `DELEGABLE_CAPABILITIES` is three entries, unchanged |

### 11.3 Status and next action

**Status: APPROVED SCOPE — not implemented.** PO-13 and PO-02 are decided (2026-11-24); §5 + Appendix E are the approved requirement set, and BR §33 now states the same scope. This document still authorises no code, migration or deployment: implementation begins when the Product Owner authorises **MP-01** (release integrity) and then **MP-35…MP-46** in `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`. Until then the requirement stands as specified and unbuilt, which is exactly what §3 says.

---

## Appendix E — Amendment A-1: PO-13 full-scope decision (24 November 2026)

**Status of this appendix: APPROVED SCOPE — supersedes the deferrals it names.** Where this appendix conflicts with §5, §6, §8 or §9.4, **this appendix governs**. §1–§4, the data model of §5.1, the contracts of §5.2–§5.5 and §5.7, and everything in MD-01…MD-12 remain in force unchanged.

### E.1 Authority for this amendment

| Decision | Date | Effect here |
|---|---|---|
| **PO-13** — *Full-featured Multi-display DQDS* | 2026-11-24 | **APPROVED.** The full multi-display DQDS is Hackathon delivery scope; multi-display management and configuration are not to be deferred or treated as optional |
| **PO-02** — *DQDS requirements alignment* | 2026-11-24 | **RESOLVED.** No MVP Scope / Hackathon Version / Later Releases tier governs DQDS; BR §33 is updated; no agent may reduce or reinterpret the requirement from outdated scope wording |
| **MP-06** — *Facility-local operational day* | 2026-11-24 | **IMPLEMENTATION COMPLIANCE REQUIRED.** Operational dates and times use the facility's configured timezone (`Asia/Dhaka` default), applied consistently to queue operations, dashboards and DQDS |

Consequential edits made in the same task: BR §33 gained a §33.1 scope-status block in both `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/AMSDP_Business_Rules_V1.1.md` (later-phase paragraph removed); the plan gained WP-C.3 (MP-41…MP-46); the gap audit gained Amendment A-2.

### E.2 What this appendix changes about §6

| §6 row | Was | Now |
|---|---|---|
| **D-04** Estimated waiting time / countdown | Deferred | **WITHDRAWN — in scope.** Requirement **MD-13**. A *countdown* remains out (E.7) |
| **D-08** Room on the queue entry | Deferred | **SPLIT.** Room **targeting** and the room label are **in scope** (**MD-14**); `QueueEntry.room_id` and room-scoped token numbering stay deferred |
| **D-06** Push transport | Deferred | **Unchanged as a transport**, but refresh-on-change is now a requirement: **MD-15** must be met; SSE/WebSocket remains an optional optimisation, not the requirement |
| **D-01, D-02, D-03, D-05, D-07, D-09, D-10, D-11, D-12** | Deferred | **Unchanged.** PO-13 does not require them, and the interpretation rule runs in both directions: an unrequested capability may not be added under cover of "full-featured" |

### E.3 New requirements — MD-13 … MD-19

Each closes a PO-13 bullet that MD-01…MD-12 did not already satisfy, and each is written to be failable.

| ID | Requirement | Rationale | Falsifiable check |
|---|---|---|---|
| **MD-13** | The board publishes, per doctor row, an **estimated waiting time in minutes**, derived from that doctor's **observed mean service time today** when at least 3 consultations have completed, otherwise the facility default (`AMSDP_AVG_SERVICE_MINUTES`, default 10). It renders with a visible estimate marker in both languages (≈ / আনুমানিক), is never zero or negative, and is never presented as a guaranteed consultation time. Where neither measurement nor default applies the field is `null` and the row renders `—`, never a fabricated number. | PO-13 bullet 8; BR §33.8–§33.9 | A doctor with 4 completed consultations shows the measured mean; a doctor with 0 shows the default; the estimate marker is present wherever a number is shown; a payload assertion that the value is an `int ≥ 1` or `null` |
| **MD-14** | A display's scope may be a **room** (`scope_type='room'`), resolved through `doctor_branches.room_id → facility_rooms.id` for the display's branch: the display shows the doctors currently assigned to that room and nobody else. An empty room yields the empty state, never the whole branch. | PO-13 bullet 2 ("room"); derived target documented per BR §33.1 item 2 | Two rooms with different doctors: each room display lists only its own; a room with no assigned doctor shows the empty state |
| **MD-15** | **Refresh on change.** The board response carries a **board version** (content hash of the published projection) in the payload and as a weak `ETag`; an unchanged board revalidates to `304` with no new body. The page reflects a serving-token or waiting-count change for any in-scope doctor within one poll interval (10 s), and does not re-render when the version is unchanged. | PO-13 bullet 5; BR §33.5 | Call a token on the staff board; the in-scope display changes within 10 s; an idle display receives `304` and re-renders nothing; the version changes exactly when the projection changes |

| **MD-16** | **Facility-local operational day and clock.** The board's "today" is the date in `organizations.timezone` (default `Asia/Dhaka`), never the container's local date; `date.today()` is removed from the display path. The last-updated time renders in facility-local time and is labelled with the facility timezone. | MP-06 (PO decision); BR §0 item 8; `models.py:38` already stores the timezone | With the container at `TZ=UTC` at 20:00 UTC (02:00 Dhaka) the board shows the **new** Dhaka day's queue, not the previous day's; boundary test at 23:59/00:00 Dhaka; `last_updated` matches the facility clock |
| **MD-17** | **Facility-controlled public-display information.** Per display the facility decides whether each optional public field is shown: `show_room`, `show_estimated_wait`, `show_waiting_count`, plus a `footer_text` (≤160 chars). Defaults `true`, `true`, `true`, `""`. Toggles are enforced **server-side**: a field switched off is absent from the payload, not merely hidden in CSS. | PO-13 bullet 10; BR §33.11 | Switching `show_estimated_wait` off removes `estimated_wait_minutes` from the raw response while the screen keeps working; the footer renders in the display's language |
| **MD-18** | **Read-only public access, enforced.** No public display route accepts a state-changing verb: `POST`/`PUT`/`PATCH`/`DELETE` on a display URL return `405` with `Allow: GET`, and the board sets no cookie and reads no session. MD-09 holds for every scope type, so no public caller reaches another branch's board by guessing a code. | PO-13 bullet 11; BR §33.12 | Four verb probes returning `405`; no `Set-Cookie` in any board response; a cross-branch code returns the same `404` as an unknown one |
| **MD-19** | **Denials are recorded, not silently swallowed — without creating an oracle or an amplification path.** Authenticated display-management denials are audited (`queue.display.denied`: actor, capability, org/branch). An anonymous request for a **disabled** display raises one `queue.display.disabled_requested` event per display per 5 minutes (throttled, no client IP stored). Unknown-code probes are counted by the limiter only and are **not** audited: an unauthenticated public probe must not be able to write unbounded rows into an append-only audit trail. | `.clinerules` §3 (denials audited) reconciled with BR §33.12 and the append-only rule | One denial of each class produces exactly one audit row (or the documented throttle); 100 anonymous unknown-code probes produce **zero** audit rows and only limiter state |

### E.4 Data-model delta against §5.1

The §5.1 table stands, with these additions. All are on the new table, so the migration remains forward-only, idempotent, on head `c4d8e2a91f60`, and touches no existing table.

| Change | Reason |
|---|---|
| `scope_type` permitted values become `'branch' \| 'doctors' \| 'department' \| 'room'` | MD-14 |
| `room_id  String FK facility_rooms.id NULL` — required when `scope_type='room'`, and validated to belong to the same organisation **and** branch | MD-14 |
| `show_room  Boolean NOT NULL default true` | MD-17 |
| `show_estimated_wait  Boolean NOT NULL default true` | MD-17 |
| `show_waiting_count  Boolean NOT NULL default true` | MD-17 |
| `CHECK (scope_type <> 'room' OR room_id IS NOT NULL)` and `CHECK (scope_type <> 'department' OR department_id IS NOT NULL)` | A half-configured scope is refused by the database, not only by the service |
| `UNIQUE (branch_id, code)` unchanged | MD-01 |

**No `queue` column is added, and none is invented.** AMSDP has no queue-definition entity: `common/models.py` holds `QueueEntry` (per doctor/date), `QueueSequence` and `QueueAnnouncementDelivery`, and nothing else. "Queue" targeting is therefore satisfied by the **doctor-set** target (`scope_type='doctors'`), because a doctor's queue is the only queue the system models. This is recorded as an interpretation, not a reduction, and is the one point a Product Owner may wish to correct (**E.9, OP-1**).

### E.5 Contract deltas

| Aspect | Specification |
|---|---|
| Payload additions | `display: {code, name, language, scope_type, footer_text}` · `board_version` · per doctor row: `room_name` (nullable), `estimated_wait_minutes` (int ≥ 1 or null), `estimate: true` when a value is present · `operational_date` and `timezone` |
| `ETag` | Weak `ETag: W/"<board_version>"` on `200`; `If-None-Match` revalidation returns `304` with the same cache headers and no body. The version is a hash of the published projection only — it must not vary with request time, otherwise every poll re-renders the screen |
| Estimate computation | Mean of today's completed consultations for that doctor when count ≥ 3 (duration = `status_history` `in_consultation` → `completed` timestamps); else `AMSDP_AVG_SERVICE_MINUTES` (10). Rounded up to the minute, floored at 1. Never derived from a patient record |
| Estimate wording | `≈ {n} মিনিট` / `≈ {n} min`, always adjacent to the number; a row showing an estimate must also be readable without it |
| Read-only enforcement | Public router registers `GET` only; a verb probe is a `405` with `Allow: GET`, cache header `no-store` |
| Audit events added | `queue.display.denied`, `queue.display.disabled_requested` (throttled 1 per display per 300 s). Existing `created/updated/disabled/enabled` unchanged |
| Rate-limit key | Unchanged from MD-10 (per display code + client, with a branch floor); MD-15's `304` responses count toward the same bucket, so a facility's screens cannot be starved by a version-check loop |

### E.6 Acceptance criteria — AC-15 … AC-22

Added to §8; the §8 table and AC-01…AC-14 remain in force.

| ID | Criterion | Evidence required |
|---|---|---|
| **AC-15** | A room-scoped display lists only the doctors assigned to that room; a room with no assignment shows the empty state and never the branch | Two HTTP bodies plus the seed assignments used |
| **AC-16** | A doctor with ≥ 3 completed consultations today shows a measured estimate; a doctor with none shows the facility default; every rendered number carries the estimate marker; a payload assertion shows `int ≥ 1` or `null` and never guarantee wording | API bodies for both doctors, page screenshot in BN and EN |
| **AC-17** | An unchanged board revalidates to `304` with no body; a serving-token change on the staff board changes `board_version` and reaches the in-scope display within 10 s; an idle screen does not re-render | Two `curl -i` captures plus a recording of the change |
| **AC-18** | With the container in UTC, a queue built for the Dhaka date is still shown at 02:00 Dhaka, and never the previous day's; `operational_date` equals the Dhaka date | Boundary test output at 23:59/00:00 Dhaka, quoted |
| **AC-19** | Disabling `show_estimated_wait`, `show_room` or `show_waiting_count` removes the field from the **raw** response while the page still renders; a footer renders in the configured language | Raw bodies with the toggles on and off |
| **AC-20** | `POST`/`PUT`/`PATCH`/`DELETE` on a display URL return `405` with `Allow: GET`; no board response sets a cookie | Four verb probes plus response headers |
| **AC-21** | An authenticated cross-branch display write produces one `queue.display.denied` row; a disabled display requested repeatedly produces at most one `queue.display.disabled_requested` row per 5 minutes; 100 unknown-code probes add **no** audit rows | Audit-table counts before and after, quoted |
| **AC-22** | BR §33 contains the §33.1 scope-status block in **both** copies, and **no tracked document states that DQDS is deferred**. A grep for the removed phrasing must return only *historical citations* — §33.1 itself, the audit's original §5.2 row, the specification's §2.2 conflict description, the V2.5 reconciliation drafts and the amendment reports — and never an operative requirement | The two BR files cited by path, plus the grep output with each hit classified as citation or requirement |

### E.7 What is still outside the scope, restated after PO-13

PO-13 adds capability; it does not add a signage product. Still out, and now explicitly out **after** the decision rather than by omission: display health/heartbeat (D-01), preview and QR issuance (D-02), floor/department topology curation (D-03), "next N tokens" (D-05), durable multi-process rate limiting (D-07, tracked as GAP-20/MP-25), room on the queue entry and room-scoped token numbering (D-08 residue), themes and a show/hide matrix beyond the four policy fields of MD-17 (D-09), device provisioning (D-10), per-display analytics (D-11), platform-admin cross-tenant provisioning (D-12).

**Countdown is deliberately excluded.** BR §33.8 permits "estimated waiting-time countdown/reporting time"; PO-13 requires estimated waiting-time *information*, identified as an estimate. A per-second countdown on a public screen manufactures precision the data does not support, so MD-13 delivers a labelled minute estimate. If the Product Owner reads §33.8 as requiring a countdown, that is an additive change to MD-13 and is not covered here.

### E.8 Task mapping (plan §6, WP-C.3)

| Task | Requirements | Phase | Estimate (eng-days) |
|---|---|---|---|
| **MP-41** | MD-14 — room scope: schema value, resolver, validation, empty-state test | 3 | 2.0 |
| **MP-42** | MD-13 — estimated wait: computation, estimate marker, BN/EN copy, payload assertion | 3 | 2.0 |
| **MP-43** | MD-15 — board version, weak `ETag`, `304` revalidation, no-re-render behaviour | 3 | 1.0 |
| **MP-44** | MD-16 — facility timezone on the display path, replacing `date.today()`; boundary test | 3 | 0.5 |
| **MP-45** | MD-17 — four policy fields, server-side suppression, admin controls | 3 | 1.0 |
| **MP-46** | MD-18, MD-19 — GET-only enforcement and the two audit events with their throttle | 3 | 1.0 |
| **MP-40** (extended) | AC-15…AC-21 added to the demonstration and the six-screen run | 6 | unchanged |

**+7.5 engineer-days** on top of the MP-35…MP-40 estimate in the plan, which moves the Hackathon total from ≈ 65.5 to ≈ 73.0 engineer-days.

### E.9 Risks and open points added

| ID | Item | Kind | Handling |
|---|---|---|---|
| **RMD-7** | A measured estimate built on 3 samples looks authoritative and is wrong | Risk, Medium/Medium | The estimate marker is mandatory and adjacent; a countdown is excluded (E.7); the wording never claims a consultation time |
| **RMD-8** | `304` revalidation is defeated by a version that varies per request | Risk, Medium/High | E.5 fixes the version as a hash of the projection only; AC-17 asserts an idle `304` |
| **RMD-9** | Audit amplification through anonymous public probes | Risk, High if mishandled | MD-19 fixes the throttle and the "no audit for unknown codes" rule; AC-21 counts rows before/after |
| **RMD-10** | The timezone fix is done on the display only, leaving dashboards and the queue on server-local dates | Risk, Medium/High | MP-06 stays one implementation with one helper, consumed by queue, dashboard and display; MP-44 is its proof on the board |
| **OP-1** | "Queue" targeting has no queue entity to point at | Owner decision if disagreed | Satisfied as the doctor-set target; a named-queue entity would be a new table and a new migration (E.4) |
| **OP-2** | Whether BR §33.8's "countdown" wording requires a countdown | Owner decision | Excluded with reasons in E.7; additive if required |

### E.10 Verification performed for this amendment

| Check | Result |
|---|---|
| Business Rules edited in both copies | `docs/product/AMSDP_Business_Rules_V1.0.md` and `docs/AMSDP_Business_Rules_V1.1.md` §33.1 identical; the later-phase paragraph is absent from both |
| Timezone support exists | `models.py:38` `Organization.timezone`, default `Asia/Dhaka` — MP-44 needs no migration |
| Estimate inputs exist | `tracking.py:184-185` already computes `patients_ahead × AMSDP_AVG_SERVICE_MINUTES` for PQV; `QueueEntry.status_history` (`models.py:869`) carries the transition timestamps |
| No queue entity to target | `models.py` class inventory — `QueueEntry`, `QueueSequence`, `QueueAnnouncementDelivery` only |
| Code unchanged by this amendment | No file under `backend/`, `frontend/`, `alembic/` modified; MP-41…MP-46 are **NOT IMPLEMENTED** |
| Tests claimed | None. No suite was executed for this amendment |

### E.11 Document control for this amendment

| Field | Value |
|---|---|
| Amendment | A-1, 24 November 2026 |
| Trigger | Product Owner decisions PO-13 (approved), PO-02 (resolved), MP-06 (compliance required) |
| Effect | Adds MD-13…MD-19, AC-15…AC-22, MP-41…MP-46; withdraws D-04, splits D-08; leaves §1–§5.7, MD-01…MD-12 and AC-01…AC-14 untouched |
| Version | The document remains **V1.0 with Amendment A-1**; a V1.1 rewrite is not issued because the amendment is append-only and every superseded statement is named here |

---

*End of document.*
