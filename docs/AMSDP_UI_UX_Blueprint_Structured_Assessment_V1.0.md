# AMSDP Complete ASCII UI/UX Blueprint — Structured Review Assessment

**Assessment ID:** AMSDP-UIUX-REVIEW-001  
**Assessment date:** 6 November 2026  
**Source reviewed:** `AMSDP_Complete_ASCII_UI_UX_Blueprint.md` (5,252 lines; approximately 320 KB)  
**Primary baseline:** `AMSDP_MVP_SCOPE_V1.0.md`  
**Cross-check references:** `AMSDP_Business_Rules_V1.0.md`, `AMSDP_System_Architecture_V1.0.md`  
**Review type:** Product-scope, UI coverage, workflow, role, consistency, and implementation-readiness assessment  
**Disposition:** **Substantive design coverage is strong; the blueprint is not yet a clean, implementation-authoritative MVP specification.**

---

## 1. Executive assessment

The blueprint is a substantial and useful design collection. It covers the main AMSDP staff-facing workflows and goes well beyond the original core screens. It includes:

- the application shell, dashboard, organization and branch management;
- staff and role management;
- doctor and patient directories and profiles;
- schedules, appointments, queue operations, and lifecycle;
- organization settings, subscription state, audit logs, landing page and login;
- floor/room management, doctor-room assignment, walk-ins, rescheduling, cancellation, attendance, session management, queue history, capacity, and schedule conflicts;
- Platform Admin and organization onboarding;
- dedicated Doctor and Assistant workspaces;
- analytics at platform, organization, branch, doctor, and assistant levels; and
- analytics configuration, data quality, retention, export, and permission screens.

The core appointment-and-queue journey is represented well enough to guide detailed design and implementation planning. The blueprint also reflects important product principles such as branch-scoped work, tenant boundaries, role-based navigation, privacy-preserving public queue displays, and auditability.

However, **the blueprint combines several different levels of product commitment in one long document**. Core MVP screens, Phase 2 capabilities, Phase 3 ideas, recommendations, proposed data-model additions, and detailed analytics are presented alongside one another. Some screens are explicitly marked P0 even though the governing MVP scope places the associated capability outside Phase 1. Other screens imply account or operational capabilities that the MVP does not require.

The most important correction is therefore not to remove design work. It is to establish a clear authority and release label for every screen, workflow, data concept, and permission.

### Overall assessment

| Dimension | Assessment | Notes |
|---|---|---|
| Core workflow coverage | Strong | Patient, doctor, schedule, appointment, walk-in, queue, cancellation and rescheduling are represented. |
| Role/workspace coverage | Good, needs normalization | Platform Admin, Organization Admin, Branch Admin, Receptionist, Doctor and Assistant are addressed, but the governing MVP document groups some roles differently. |
| Facility operations | Strong but partly expanded | Floors, rooms, sessions, room assignment and displays need a deliberate MVP boundary. |
| Platform administration | Good design coverage | Needs explicit separation of platform control-plane actions from tenant-owned operational data. |
| Organization onboarding | Good | Several onboarding steps are optional or Phase 2; do not make all steps mandatory. |
| Analytics | Extensive proposal | Must not be interpreted as Phase 1 commitment. |
| Security and privacy | Good principles | Requires screen-by-screen permission and data-exposure acceptance criteria. |
| Consistency with approved scope | Mixed | Identifiable conflicts exist, especially DQDS, analytics, duplicate merge and subscription lifecycle. |
| Developer/agent readiness | Not yet ready as a single implementation source | Needs screen IDs, authority labels, dependency mapping, API/action mapping, and a decision register. |

**Recommendation:** retain the original file unchanged as the design source. Create a controlled, indexed implementation blueprint after product-owner decisions are recorded. Do not ask an agent to silently rewrite or reinterpret the existing designs.

---

## 2. Documents and authority used for this assessment

This review treats the documents as follows:

1. **`AMSDP_MVP_SCOPE_V1.0.md`** — governing Phase 1 product boundary and MVP acceptance baseline.
2. **`AMSDP_Business_Rules_V1.0.md`** — approved operational rules, lifecycle, roles, permissions, queue, tenancy, subscription and release phasing.
3. **`AMSDP_System_Architecture_V1.0.md`** — architecture boundaries, service ownership, security and implementation constraints.
4. **`AMSDP_Complete_ASCII_UI_UX_Blueprint.md`** — the UI/UX design source being assessed.

The blueprint itself contains proposals and recommendations. A wireframe, priority label, or recommendation inside it does not by itself amend the MVP scope or business rules.

Where the sources differ, this assessment flags the difference rather than silently resolving it. Product-owner approval is required for scope changes.

---

## 3. Blueprint structure and coverage inventory

The source contains several design waves. The following inventory identifies the major sections and their coverage.

| Blueprint section | Approx. source lines | Coverage | Review |
|---|---:|---|---|
| Application structure and dashboard | 1–63 | App shell, role-filtered sidebar, branch context, daily metrics, recent activity | Core MVP foundation; dashboard figures must be backed by real operational records. |
| Organization and branch entities | 64–127 | Organization directory/create, branch list/details | Core platform/tenant setup; enforce platform vs tenant authority. |
| Staff and role entities | 128–170 | Staff list/create and role assignment | Core; normalize role names and scope. |
| Doctor entity | 171–224 | Doctor directory, registration, profile and search | Core; doctor is a facility-local record, not necessarily a login account. |
| Patient entity | 225–292 | Patient list, registration, duplicate warning, profile | Core; do not imply unique mobile number or automatic merge. |
| Doctor schedule entity | 293–346 | Schedule management and calendar concepts | Core; capacity and concurrency rules must be server-enforced. |
| Appointment entity | 347–441 | Appointment creation, list, details and management | Core; lifecycle and payment boundaries must be explicit. |
| Queue entity and lifecycle | 442–528 | Queue board/details and state lifecycle | Core; queue position must remain separate from booked appointment time. |
| Organization settings/configuration | 529–561 | Tenant settings | Core where limited to approved configurable settings. |
| Subscription entity | 562–594 | Subscription view/state | Subscription metadata is relevant; automation/billing must remain out of scope. |
| Audit log entity | 595–627 | Audit log view | Core audit visibility; not a substitute for immutable backend audit records. |
| Landing page and login | 628–673 | Public landing and staff login | Staff login is core; marketing landing page is not a core operational dependency. |
| Public DQDS | 674–695 | Public queue display | Phase 2 under the MVP scope. |
| Entity/screen inventory and role navigation | 696–752 | Screen and navigation summaries | Useful, but needs canonical IDs and release labels. |
| Floor-wide/chamber display concepts | 753–918 | TV/LED floor display, individual chamber display, staff control panel, room/session concepts | Public display is Phase 2; internal room/doctor assignment requires product-model alignment. |
| Additional operational screen recommendations | 919–1083 | Walk-in, doctor room changes, session close, operations overview, checklists | Several are necessary operational detail; label individual screens by scope. |
| Expanded facility operations screens | 1084–1887 | Floor, room, assignments, room availability, walk-in, policies, reschedule, cancellation, no-show, availability, sessions, queue history, display management, branch switching, permissions, duplicate review, capacity, conflict handling, search, expiry state | Mixed: core, optional, and later-phase screens are currently grouped together. |
| Platform Admin and workspace architecture | 1888–2065 | Platform Admin, Organization Admin, Branch Admin, role workspaces | Good control-plane/workspace separation concept; authority boundaries need specification. |
| Platform Admin UI | 2066–2349 | Platform dashboard, organization management, onboarding requests, plans, subscriptions, users, global config, monitoring, audit | Useful SaaS control-plane proposal; billing automation and advanced monitoring are not implied MVP deliverables. |
| Organization onboarding | 2350–2593 | Registration, review, profile, first branch, floors/rooms, first admin, staff/doctors, schedules/queues, activation | Good guided setup; floors/rooms should be conditional, not mandatory for simple facilities. |
| Doctor Workspace | 2594–2812 | Doctor dashboard, appointments, queue, schedule, room/session and patient views | Useful optional workspace; doctor login is not a dependency for MVP operations. |
| Assistant Workspace | 2813–3036 | Assigned doctor, room overview, queue, appointments and permitted walk-in operations | Useful; must enforce assigned-doctor/branch permissions and avoid implying unrestricted patient access. |
| Role access/navigation and MVP priority | 3037–3157 | Role access matrix, navigation and priorities | Needs reconciliation with the authoritative role/permission model. |
| Analytics overview and role dashboards | 3158–3538 | Platform, organization, branch, doctor, assistant analytics; metric and data-model needs | Proposed/advanced scope; do not treat as core MVP. |
| Analytics Specification V1.0 | 3539–4512 | Metric dictionary, events, permissions, filters, wireframes, exports, data model, retention, accuracy and acceptance criteria | Detailed proposal; its status is explicitly proposed. |
| Analytics configuration | 4513–4725 | Configurable analytics decisions, inheritance, settings model | Proposed administrative capability; requires governance and approval. |
| Analytics configuration UI | 4726–5252 | Analytics configuration screens, data quality, UI states and screen inventory | Extensive proposal; phase and implementation boundary required. |

### Coverage conclusion

The document is not merely a set of wireframes. It is a combined UI blueprint, product expansion proposal, analytics specification, and preliminary data-model discussion. That is useful for exploration but creates risk if agents treat the entire file as a single approved implementation instruction.

---

## 4. Alignment with the approved MVP

### 4.1 Clearly aligned with Phase 1

The following areas are consistent with the MVP scope and should form the core implementation blueprint:

- Staff login and authenticated application shell.
- Organization and branch setup.
- Staff accounts, role assignment and branch scope.
- Patient registration, search, profile and duplicate warning.
- Facility-local doctor records and optional room association.
- Doctor schedules, appointment models and capacity.
- Staff-mediated appointment creation and management.
- Walk-in registration using the approved walk-in placement policies.
- Unified queue, token/serial generation, manual queue management and status transitions.
- Cancellation with reason and configured policy.
- Rescheduling with original/replacement linkage and preserved history.
- Appointment transfer within the same organization where permitted.
- Operational audit history.
- Bangla/English, Unicode, responsive and low-bandwidth usability.
- Tenant and branch context indicators and server-enforced permissions.
- Basic operational dashboard information derived from authorized records.

### 4.2 Phase 2 or later — do not label as Phase 1 without approval

| Capability/screen | Governing scope position | Blueprint risk |
|---|---|---|
| Public Digital Queue Display System (DQDS) | Explicitly out of Phase 1; planned for Phase 2 | The blueprint calls DQDS a major UI area and gives it detailed screens. Keep it as a separately labelled Phase 2 package. |
| Multi-screen floor/chamber display management | Phase 2 queue extension | The display management screens are marked P0 in the additional screen inventory. This conflicts with the MVP scope. |
| Printed token slip / printer integration | Printed queue tokens and device support are Phase 2; basic token generation is Phase 1 | Walk-in confirmation/token slip must distinguish on-screen token confirmation from printer/device integration. |
| Patient duplicate merge | Phase 1 supports warnings and authorized correction; formal merge is later | Duplicate resolution/merge screen is marked P1, but its exact operation must be explicitly deferred. |
| Advanced analytics | Advanced analytics and predictive reporting are out of Phase 1 | The analytics section is extensive and includes a P0 analytics phase; that label must not override MVP scope. |
| Analytics event warehouse, aggregates and exports | Not a core Phase 1 acceptance requirement | Detailed event architecture, aggregation, exports and retention need separate release planning. |
| Automated subscription lifecycle/grace/read-only automation | Phase 2 direction in MVP scope | The read-only expiry screen is marked P0 in the UI inventory. It may be useful to design now, but automatic enforcement is not an MVP assumption. |
| SMS and external notifications | Phase 2 | Do not add notification settings or provider workflows to Phase 1 unless separately approved. |
| Doctor self-service workspace | Doctor login is optional and not a core workflow dependency | Build only if it does not delay staff-mediated appointment and queue workflows. |
| Expanded room utilization and availability analytics | Advanced reporting proposal | Do not treat as operational MVP requirement. |

**Required correction:** replace the generic P0/P1 labels with release labels tied to the governing scope: `MVP-P1`, `PHASE-2`, `PHASE-3`, `PROPOSED`, or `DECISION-REQUIRED`. Avoid using `P0` without defining whether it means release-critical or design priority.

### 4.3 Proposed additions that need a product decision

These concepts may be valuable, but should not be promoted to approved scope solely because the blueprint contains wireframes:

1. **Floor as a first-class entity.** The MVP requires organizations, branches, doctors, rooms and schedules. A floor hierarchy is not necessary for every facility and must be optional.
2. **Doctor-room assignment/session model.** The MVP supports optional room association. A time-bounded assignment/session relationship, room reassignment history, and concurrent assignment constraints need explicit approval.
3. **Room availability board.** Useful operational enhancement, but the exact meaning of availability (room occupancy, doctor availability, or session status) needs definition.
4. **Doctor session controls.** Opening, pausing, resuming and closing a session may be needed for queue operations; define minimum MVP state transitions before implementing expanded session management.
5. **Today's Operations Overview and operational alerts.** Define which alerts are deterministic core workflow conditions versus analytics-derived or predictive signals.
6. **Detailed platform monitoring.** Platform health and service monitoring may belong to internal operations rather than tenant-facing product scope.
7. **Analytics configuration hierarchy.** Platform > Organization > Branch is a proposal; it must not create permission escalation or override business-rule constraints.
8. **Role-specific analytics access.** The seven configurable analytics decisions are explicitly proposed and require approval.
9. **Bulk import, notification centre, or other ancillary items** if added in later revisions: classify separately and do not infer approval from a UI sketch.

---

## 5. Specific inconsistencies and corrections required

### 5.1 DQDS and floor display priority conflict

The blueprint's additional screen inventory marks **Floor display management P0** and includes public display connection status. The MVP scope explicitly excludes digital queue displays and multi-screen public queue screens from Phase 1, placing them in Phase 2.

**Correction:** mark all public floor/chamber display screens, display configuration and display health as `PHASE-2`. The authenticated staff queue board remains Phase 1.

### 5.2 Analytics phase conflict

The Analytics Specification labels itself **“Proposed — requires product-owner approval”** and contains seven open product decisions. Later, the blueprint proposes an analytics P0 implementation phase and extensive configuration screens. The MVP scope excludes advanced analytics from Phase 1 and describes broader analytics as Phase 3 direction, with more complete branch operational reporting as a Phase 2 candidate.

**Correction:**
- Treat the analytics specification and all its configuration screens as `PROPOSED`.
- Do not use its internal P0/P1/P2 labels as approved AMSDP release commitments.
- If basic operational counts are needed for the MVP dashboard, define them separately as simple operational views—not as implementation of the full analytics subsystem.
- Require approval of each metric, event source, access rule, retention rule, and export behavior before analytics implementation.

### 5.3 Doctor login and workspace dependency

The MVP scope states that a doctor can be represented as a facility-local operational record and does not need an AMSDP account. If doctor login is enabled, it must be scoped to the relevant organization and branch; self-service is not a core workflow dependency.

**Correction:** retain the Doctor Workspace as an optional interface design. The Phase 1 workflow must remain operable by authorized staff even if no doctor account exists. Do not require doctor login for appointment completion or queue progression unless the product owner explicitly changes the rule.

### 5.4 Assistant workspace permissions

The blueprint includes assistant queue and walk-in operations. The assistant's actual scope must be limited to the assigned doctor/room/session and permitted branch context. The UI must not imply that an assistant can search all organization patients or manage unrelated doctors.

**Correction:** define an explicit assistant permission matrix for each action: view patient identifiers, search patient, register patient, create walk-in, call next, skip, reorder, mark consultation started/completed, and view history. Each must be permission-gated server-side.

### 5.5 Patient duplicate handling

The patient screens include duplicate warning and duplicate resolution. The MVP allows duplicate warnings and safe correction, but does not permit automatic merge; formal merge is a later-phase capability.

**Correction:** Phase 1 duplicate UI should support warning, comparison and authorized correction without destructive merge. Keep merge UI and merge APIs as Phase 2 or later, with audit and appointment-history preservation.

### 5.6 Subscription expiry/read-only state

The blueprint shows an expired subscription read-only screen and marks it P0. The MVP scope places subscription lifecycle automation and grace/read-only enforcement in Phase 2 direction.

**Correction:** the Phase 1 subscription UI may show plan/status metadata if needed, but do not imply automated billing, payment reconciliation, grace-period automation, or expiry-based write suspension as an MVP acceptance requirement unless separately approved. Subscription billing automation is explicitly out of scope.

### 5.7 Onboarding wizard over-specification

The onboarding flow includes floors, rooms, staff, doctors, schedules and queues. The MVP scope explicitly supports a simple single-branch organization and a single-chamber facility without unnecessary hierarchy.

**Correction:** make floors and room setup conditional. The minimum path must allow a small clinic or single-doctor practice to become operational with only the required organization, branch, staff, doctor, schedule and queue configuration. Do not force a floor hierarchy.

### 5.8 Role naming and model normalization

The blueprint uses six roles: Super Admin, Organization Admin, Branch Admin, Receptionist, Doctor and Assistant. The MVP scope's role section uses broader groupings (Platform Super Admin, Organization/Facility Admin, Facility Staff/Appointment Desk, Doctor), while Business Rules V1.0 defines the six-role model.

**Correction:** use the six canonical role identifiers from the business rules and treat the MVP scope's groupings as explanatory role families. UI labels may be localized, but role IDs must remain consistent. Every role must also have an organization and/or branch scope definition.

### 5.9 Organization versus branch authority

Some screens place organization, branch, subscription, staff and configuration actions together. This can blur the tenant boundary.

**Correction:** distinguish:
- **Platform control plane:** create/suspend organizations, define platform limits/defaults, manage plans and platform users.
- **Organization workspace:** manage tenant-owned settings, branches, staff and permitted configuration.
- **Branch operations:** operate only within assigned branch scope.
- **Public display:** read-only, narrowly scoped queue output with no patient identity.

Platform Admin must not become an unrestricted route to tenant patient data or operational records.

### 5.10 Payment wording and UI controls

The MVP permits appointment-level confirmation state such as `AWAITING_CONFIRMATION` and `CONFIRMED` where a facility uses an external payment/confirmation process. It prohibits payment processing, amounts, balances, transaction IDs, wallets, invoices and financial ledgers.

**Correction:** any appointment confirmation UI must not use language or controls that imply AMSDP collected or reconciled money. Do not add payment amount, gateway, transaction, receipt or financial status fields.

### 5.11 Patient identity and privacy on dashboards/displays

The blueprint's internal dashboard examples show patient names in queue tables. This may be acceptable only inside authenticated, permission-scoped staff interfaces. Public display rules explicitly prohibit patient names.

**Correction:** create distinct presentation contracts:
- authenticated staff queue: show only patient data required for that user's work;
- doctor/assistant workspace: show only assigned operational records;
- public display: token/serial and room/doctor status only; no patient name, mobile or other identifying data;
- platform analytics: no patient-level identifiers.

### 5.12 Appointment and queue lifecycle

The blueprint includes lifecycle screens and queue controls. The governing rules require queue position to remain separate from booked appointment time, and queue reordering to preserve previous/new position, actor, timestamp and reason. Rescheduling must preserve the original and link a replacement.

**Correction:** every relevant dialog and detail screen should show:
- appointment status separately from queue status/position;
- original appointment time and any rescheduled replacement;
- explicit actor/reason where required;
- no silent appointment-time mutation from queue reorder;
- confirmation before irreversible or consequential actions.

---

## 6. Role-by-role UI coverage assessment

| Role | Blueprint coverage | Required MVP boundary / gap |
|---|---|---|
| `super_admin` | Platform dashboard, organization directory/details, onboarding review, plans, subscriptions, platform users, global config, monitoring, audit | Define exact tenant-data visibility. Platform configuration must set allowed limits/defaults; it must not silently alter tenant-owned records. |
| `org_admin` | Organization workspace, branches, staff, doctors, patients, settings, analytics proposal | Define cross-branch permissions and organization-level patient access. Analytics is not MVP by default. |
| `branch_admin` | Branch dashboard, daily operations, staff/doctor/schedule/queue controls, permission concepts | Ensure all queries and actions are branch-scoped unless explicitly authorized across branches. |
| `receptionist` | Patient search/registration, appointments, walk-ins, queue operations | This is the core operational persona. Need a single efficient end-to-end workflow and explicit action permissions. |
| `doctor` | Dedicated dashboard, appointment and queue views, schedule, patient views, room/session controls | Login is optional. Doctor record must work without a user account. Restrict to own authorized records and avoid clinical-record features. |
| `assistant` | Assigned doctor, room overview, queue and appointment operations | Assignment-scoped access; define exactly which queue and patient actions are permitted. |

### Cross-role gaps to resolve

- Provide an explicit role/action matrix, not just role navigation.
- Define whether one user may hold multiple roles and how effective permissions combine.
- Define branch switching behavior and ensure the server revalidates scope on every request.
- Define who can create/deactivate staff, change roles, and grant cross-branch access.
- Define whether doctor and assistant accounts are optional and what happens to their assignments when accounts are disabled.
- Ensure `super_admin` platform operations and tenant operations remain distinct.

---

## 7. Workflow completeness assessment

### 7.1 Organization setup

**Covered:** organization creation, branch setup, first admin, staff/doctors, schedules and activation.

**Needs refinement:**
- Minimum onboarding must support a single-branch, single-room or no-room configuration.
- Floors and rooms must be optional where not needed.
- Subscription assignment must not imply payment collection.
- Define invite/credential creation, first-login password setup, account recovery and account deactivation.
- Define rollback/recovery for partially completed onboarding.

### 7.2 Patient registration and selection

**Covered:** patient directory, create, profile, duplicate warning and appointment search.

**Needs refinement:**
- Shared mobile numbers are valid within an organization.
- Patient name and mobile are mandatory; do not require email or national ID.
- Search results must distinguish patients with similar names/shared mobile.
- Do not auto-merge.
- Avoid exposing patient search to public or platform-level contexts.

### 7.3 Doctor and schedule setup

**Covered:** doctor registration, profile, schedule list/calendar, availability and room association.

**Needs refinement:**
- Doctor records are organization-local; no global identity.
- Doctor mobile uniqueness follows the platform-controlled organization policy.
- Room association is optional.
- Define schedule date/timezone, capacity, blocked periods and concurrent booking behavior.
- Prevent a room/doctor double-booking only where the approved model requires it.

### 7.4 Appointment creation and management

**Covered:** appointment list, create, details, reschedule, cancellation and search.

**Needs refinement:**
- Keep time-slot, serial-based and hybrid as the only appointment models.
- Walk-in remains a source, not a fourth appointment model.
- Preserve original appointment and link replacement on reschedule.
- Transfer only within the same organization and preserve history.
- Cancellation reason and policy must be visible and enforced.
- Do not silently change booked time due to queue movement.
- No payment processing or financial ledger.

### 7.5 Walk-in and queue

**Covered:** walk-in registration, placement policy, token, queue board, queue history, session controls.

**Needs refinement:**
- All four approved walk-in policies should be configurable and enforced.
- Queue position is distinct from appointment time.
- Manual reorder must capture old/new position, actor, timestamp and reason.
- Late arrival is an indicator; staff decides handling.
- No-show requires staff confirmation after configured grace period; do not automatically infer no-show.
- Estimated waiting time is not a guarantee.
- Queue token numbering must follow the approved reset/uniqueness rules.
- Public queue display is later phase.

### 7.6 Cancellation, rescheduling and no-show

**Covered:** dedicated screens and history.

**Needs refinement:**
- Cancellation reason required where specified.
- Reschedule must create a linked replacement; preserve old record.
- No-show grace period configurable; staff confirms.
- Late-arrival indicator must not automatically reorder or cancel.
- Ensure status transition validation is enforced by backend, not merely by UI.

### 7.7 Audit and exception handling

**Covered:** audit log, queue history, schedule conflict and capacity screens.

**Needs refinement:**
- Audit records must be generated by the backend and not editable from the UI.
- Provide before/after values, actor, timestamp, reason and entity reference where applicable.
- Show failed/denied actions where the audit design requires them.
- Provide explicit conflict-resolution outcomes; never silently overbook or reassign.
- Include stale data, network failure, concurrent update and permission-denied states.

---

## 8. Missing or under-specified UI areas

The source contains broad screen coverage, but several important operational and security details are either absent, only implied, or not consistently specified. These should be added to the blueprint index and then designed only where necessary.

### 8.1 Priority missing screens/states

| Gap | Why it matters | Suggested priority |
|---|---|---|
| Account activation, deactivation and access recovery | Staff lifecycle and secure access are MVP requirements. | MVP |
| First-login/password reset and session-expired states | Completes the authentication experience. | MVP |
| Unauthorized/forbidden and tenant-scope error states | Makes server-side authorization understandable without leaking data. | MVP |
| Empty states for patients, doctors, schedules, appointments and queue | Required for first-use and low-volume facilities. | MVP |
| Form validation and server error states | Prevents ambiguous failure during core operations. | MVP |
| Concurrent booking/capacity conflict state | Critical because capacity must be transactionally protected. | MVP |
| Duplicate patient warning with shared-mobile handling | Avoids accidental selection or merge. | MVP |
| Appointment transfer within organization | Required by business rules; not as prominent as create/reschedule/cancel. | MVP |
| Queue transition confirmation and invalid-transition feedback | Lifecycle must be enforced consistently. | MVP |
| Manual no-show confirmation and grace-period display | Prevents automatic or premature no-show classification. | MVP |
| Late-arrival indicator and staff decision state | Required behavior is not equivalent to automatic queue movement. | MVP |
| Overbooking exception flow | Configurable, disabled by default; needs explicit authorization and audit. | MVP if enabled |
| Branch access and staff role assignment review | Prevents accidental privilege expansion. | MVP |
| Network interruption / retry / stale data | Low-bandwidth and unreliable connectivity are important operating conditions. | MVP |
| Audit detail view with before/after/reason | Required for operational accountability. | MVP |
| Data retention/deletion request handling | Privacy and operational policy need an approved user-facing/admin process. | Decision required |
| Subscription grace/read-only state details | Relevant later; must match approved subscription lifecycle. | Phase 2 |
| Public display stale/offline state | Needed when DQDS is implemented. | Phase 2 |
| Print fallback and printer failure state | Only if printed token support is implemented. | Phase 2 |

### 8.2 Missing design contracts (not necessarily new screens)

- Common table behavior: sorting, pagination, search debounce, filters, column visibility and mobile adaptation.
- Common form behavior: required fields, inline validation, server errors, unsaved changes, duplicate submission prevention.
- Date/time display: facility timezone, Bangla/English formatting, 12/24-hour preference and daylight/timezone assumptions.
- Accessibility: keyboard navigation, contrast, focus indicators, readable token sizes and touch targets.
- Localization: translated labels, mixed Bangla/English names, numerals and fallback behavior.
- Data freshness: timestamp and refresh behavior for live queue boards.
- Confirmation behavior for destructive/high-impact operations.
- Loading, empty, partial, error, forbidden and stale-data states across all modules.
- Audit/event traceability from a record detail page.
- Mobile responsive behavior for receptionist/assistant workflows.

---

## 9. Analytics assessment

The analytics material is unusually detailed for a UI blueprint. It includes metric definitions, event catalogue, role access, filters, export controls, data model, retention, reconciliation, quality states and configuration inheritance.

This is valuable discovery work, but its status must remain **proposed** until approved.

### 9.1 What is strong

- Metrics have documented definitions and formulas.
- Reporting periods, timezone and filters are considered.
- Tenant and branch isolation are explicit.
- Patient identifiers are excluded from platform analytics.
- Event idempotency, unique IDs and versioning are specified.
- Reschedules and transfers are treated as historical relationships.
- Missing timestamps and zero denominators are handled explicitly.
- Queue wait time is defined from queue entry to consultation start.
- Export permissions and audit are included.
- Analytics configuration changes have a proposed inheritance and history model.

### 9.2 Risks and unresolved decisions

1. **Phase mismatch:** the MVP scope excludes advanced analytics from Phase 1. The analytics document's internal MVP/P0 terminology must not override that.
2. **Metric definitions need product approval:** counts and denominators can affect business decisions. They must be versioned and approved.
3. **Event sourcing scope:** the proposed event catalogue and aggregate pipeline add significant engineering work beyond basic appointment operations.
4. **Retention:** the seven configurable decisions include event/aggregate retention, but retention periods and legal/privacy constraints are not finalized.
5. **Platform visibility:** aggregate-only versus detailed non-patient usage needs a firm platform privacy boundary.
6. **Receptionist analytics:** summary/full branch analytics options need least-privilege review.
7. **Doctor historical activity:** own historical patient appointment activity requires a clear retention and access policy.
8. **Room utilization:** scheduled availability and actual session time are different metrics and should remain separately named.
9. **Queue snapshots:** event-driven versus periodic sampling must not produce misleading queue-length or wait-time claims.
10. **Exports:** CSV/PDF/Excel support has implementation, data leakage and audit implications; do not assume all formats are MVP.
11. **Metric configuration:** allowing tenant-level metric changes can harm comparability. Platform-owned definitions and versioning should be protected.
12. **Analytics data access:** drill-down must never bypass the user's source-record permissions.

### 9.3 Recommendation

Keep the analytics specification in a separate document or a clearly separated appendix. For the MVP, implement only the minimum operational counts required for the core dashboard and daily queue operations. Do not build a general analytics event warehouse, advanced reports, export engine or analytics configuration module until the release scope and decisions are approved.

---

## 10. Data model and architecture implications

The blueprint introduces or implies entities beyond the core MVP model. The architecture and data model should be reconciled before implementation.

| Concept | MVP baseline | Blueprint implication | Assessment |
|---|---|---|---|
| Organization | Required tenant boundary | Organization management/onboarding | Aligned. |
| Branch | Required, within organization | Branch switching and branch dashboards | Aligned; enforce scoped access. |
| User / role assignment | Required | Six-role workspaces and permission matrix | Aligned; canonical identifiers and scope needed. |
| Patient | Organization-owned; shared across branches by permission | Duplicate review and patient analytics | Core record aligned; merge later. |
| Doctor | Facility-local record; no global identity | Doctor login/workspace and analytics | Record aligned; account optional. |
| Room | Optional room association | Room directory, availability, floor display | Room record is supported; expanded occupancy model needs decision. |
| Floor | Not required for every facility | Floor directory and hierarchy | Optional proposal; must not be mandatory. |
| Schedule/capacity | Required | Availability board, conflict management | Aligned; define authoritative constraints. |
| Appointment | Required | List/create/detail/reschedule/cancel/search | Aligned; preserve lifecycle/history. |
| Queue entry/token | Required | Queue board, history, public display | Core queue aligned; public display later. |
| Doctor session | Not clearly a mandatory first-class MVP entity | Session open/pause/resume/close and room assignments | Needs architecture/product decision. |
| Doctor-room assignment | Optional room association in MVP | Time-bound assignment and history | Define whether a simple association suffices for MVP. |
| Public display/device | Explicitly later phase | Display registry, health and configuration | Phase 2. |
| Analytics events/aggregates | Not core MVP | Detailed event pipeline and aggregate tables | Proposed/later phase. |
| Analytics configuration/history | Not core MVP | Platform/org/branch config hierarchy | Proposed; separate governance. |
| Subscription plan/status | Subscription model exists | Platform plan/subscription administration | Basic metadata can be scoped; billing automation excluded. |

**Architecture gate:** before coding floor/session/analytics functionality, update the system architecture and data model with approved entity ownership, lifecycle, API contracts, audit behavior and service boundaries. Do not infer that a UI sketch authorizes a new service or database table.

---

## 11. UI/UX quality and operational recommendations

### 11.1 Establish one reusable design system

Define shared components and behaviors for:

- application shell, role-aware navigation and branch context;
- tables, filters, pagination and responsive layouts;
- forms, validation and confirmation dialogs;
- status badges and lifecycle timelines;
- patient/doctor selectors;
- queue position and token display;
- audit history;
- permission-denied, loading, empty, stale and error states;
- Bangla/English switching and date/time/number formatting.

### 11.2 Prioritize the receptionist end-to-end journey

The MVP should be demonstrable without navigating through many unrelated admin pages:

1. Sign in as authorized facility staff.
2. Select or confirm active branch.
3. Search for an existing patient or register a new one.
4. Select doctor and available schedule/capacity.
5. Create a scheduled appointment or register a walk-in.
6. See both in the same daily queue.
7. Check in and move the entry through valid queue states.
8. Reorder or skip only where permitted, with reason/audit.
9. Complete, cancel, reschedule or confirm no-show according to policy.
10. Inspect the resulting audit history.

The daily queue should be the primary operational surface. The design should reduce context switching and avoid requiring the receptionist to navigate through analytics, room utilization or platform administration to complete routine work.

### 11.3 Separate operational and public interfaces

- Staff queue board: authenticated, permission-scoped and operational.
- Public display: separate read-only surface, Phase 2, token/room/status only.
- Platform admin: separate control plane.
- Organization and branch workspaces: tenant-owned operations.
- Doctor and Assistant workspaces: optional, narrowly scoped operational surfaces.

### 11.4 Design for Bangladesh operating conditions

Retain the blueprint's Bangla/English and low-bandwidth intent. Explicitly test:
- long Bangla names and mixed-script search;
- shared family mobile numbers;
- small-screen use at reception;
- touch-first queue controls;
- intermittent network and reconnect;
- clear local date/time and token numbering;
- readable public token display without patient identity.

---

## 12. Recommended release classification

The following is a recommended classification based on the governing MVP scope, not a unilateral scope change.

### MVP / Phase 1

- Staff login and application shell.
- Platform organization creation and basic administration.
- Organization and branch setup.
- Staff accounts, role assignment and branch scope.
- Patient create/search/view/update and duplicate warning.
- Doctor create/search/view/update; optional room association.
- Schedule and capacity configuration.
- Appointment create/list/detail/update.
- Walk-in registration and approved placement policy.
- Unified queue, token generation, queue movement and lifecycle.
- Cancellation, rescheduling and same-organization transfer.
- No-show and late-arrival handling consistent with business rules.
- Audit history and queue movement history.
- Basic operational dashboard and daily queue view.
- Core error, empty, loading, validation, permission and concurrency states.
- Bangla/English, Unicode, responsive and low-bandwidth support.

### Phase 2 candidates

- Digital Queue Display System, floor/chamber displays and display management.
- Printed token support and printer-specific integrations.
- SMS/notification integrations.
- Formal patient duplicate merge.
- Subscription grace/read-only lifecycle automation.
- More complete branch-level operational reporting.
- Additional room/session operational refinements where validated by facilities.

### Phase 3 / separate approval

- Patient-facing portal/self-service.
- External payment integrations and financial features.
- Advanced analytics, predictive reporting and AI assistance.
- Third-party integrations and broader ecosystem capabilities.
- Clinical or broader facility modules.

### Proposed / decision required

- Floor as mandatory or optional entity.
- Detailed doctor-room assignment/session model.
- Doctor login and the precise Doctor Workspace feature set.
- Assistant permissions and assignment model.
- Analytics specification, metrics, event pipeline, retention and export.
- Analytics configuration inheritance and override permissions.
- Platform monitoring/support tooling exposed in product UI.
- Any new operational alerting beyond deterministic MVP rules.

---

## 13. Prioritized remediation plan

### R0 — Resolve before AILI implementation uses the blueprint

1. Add an authority/status banner: MVP approved, Phase 2, Phase 3, proposed, or decision required.
2. Correct DQDS and floor/chamber display screens from P0 to Phase 2.
3. Reclassify the analytics specification and all analytics screens as proposed/later phase.
4. Correct duplicate merge to Phase 2; retain Phase 1 warning/correction only.
5. Clarify subscription metadata versus subscription billing/automation.
6. Make floors and room hierarchy optional in onboarding.
7. State explicitly that doctor login is optional and not required for core operations.
8. Establish canonical six role IDs and an action-level permission matrix.
9. Define the Phase 1 minimum appointment/queue lifecycle screens and states.
10. Confirm whether floor/session/doctor-room assignment is part of the MVP data model.

### R1 — Complete the MVP interaction specification

1. Add missing authentication/account lifecycle states.
2. Add appointment transfer and concurrency conflict screens/states.
3. Specify no-show grace-period and staff-confirmation interactions.
4. Specify late-arrival handling without automatic queue mutation.
5. Add queue transition validation, confirmation and audit details.
6. Add network, stale-data, retry, empty and permission-denied states.
7. Define common table/form behavior and localization rules.
8. Add a screen-to-action/API mapping for each MVP screen.
9. Add responsive variants for reception and queue operation.

### R2 — Prepare later-phase modules separately

1. Move public display screens into a Phase 2 package.
2. Move advanced analytics and analytics configuration into a separate proposal.
3. Define subscription lifecycle automation as a separate Phase 2 package.
4. Move duplicate merge into a Phase 2 package.
5. Keep optional Doctor/Assistant workspace enhancements behind explicit release decisions.

---

## 14. Recommended blueprint organization

Do not compress or discard the original. Preserve it as the full design archive and create a structured, agent-consumable set of documents.

Suggested structure:

```text
docs/product/ui-ux/
├── README.md
├── AMSDP_UI_UX_Blueprint_Index_V1.0.md
├── AMSDP_UI_UX_MVP_Screens_V1.0.md
├── AMSDP_UI_UX_Phase2_Screens_V1.0.md
├── AMSDP_UI_UX_Phase3_and_Proposals_V1.0.md
├── AMSDP_UI_UX_Role_Permission_Matrix_V1.0.md
├── AMSDP_UI_UX_Workflow_Catalogue_V1.0.md
├── AMSDP_UI_UX_Screen_Action_API_Map_V1.0.md
├── AMSDP_Analytics_Specification_PROPOSED_V1.0.md
├── decisions/
│   └── AMSDP_UI_UX_Product_Decision_Register.md
└── archive/
    └── AMSDP_Complete_ASCII_UI_UX_Blueprint.md
```

Each screen entry should contain:

- stable screen ID;
- screen name and purpose;
- release classification;
- approval status;
- primary actor and permitted roles;
- organization/branch scope;
- entry point and exit/next actions;
- required fields and validation;
- actions and state transitions;
- API/action dependencies;
- empty/loading/error/forbidden/stale states;
- audit requirements;
- data sensitivity and public/private designation;
- acceptance criteria;
- dependencies and unresolved decisions.

### Suggested stable ID convention

- `AUTH-###` — authentication/account
- `PLAT-###` — platform administration
- `ORG-###` — organization and onboarding
- `BR-###` — branch/facility
- `STAFF-###` — staff and permissions
- `PAT-###` — patients
- `DOC-###` — doctors
- `SCH-###` — schedules/capacity
- `APT-###` — appointments
- `Q-###` — queue/tokens
- `AUD-###` — audit
- `ROOM-###` — rooms/floors/sessions
- `DQDS-###` — public queue display
- `SUB-###` — subscription
- `AN-###` — analytics

The current analytics inventory already uses `AN-001` through `AN-021`; preserve those IDs if retained.

---

## 15. Product-owner decision register

The following decisions should be recorded before implementation. They are not assumed to be approved by this assessment.

| ID | Decision | Current source position | Recommended action |
|---|---|---|---|
| D-01 | Are floors mandatory or optional? | MVP does not require a floor hierarchy for every facility. | Keep optional; allow branch → room without floor. |
| D-02 | Is doctor-room assignment a simple optional association or a time-bound session assignment? | MVP supports optional room association; blueprint proposes richer assignment/session concepts. | Approve the minimum Phase 1 model; defer advanced session lifecycle if not essential. |
| D-03 | Are public floor/chamber displays Phase 1? | MVP explicitly places DQDS in Phase 2. | Keep Phase 2. |
| D-04 | Is doctor login required? | No; optional and not a core workflow dependency. | Keep optional. |
| D-05 | What can an assistant do? | Assignment-scoped assistant role exists; screen actions need detail. | Approve action-level permissions. |
| D-06 | Is analytics part of Phase 1? | Advanced analytics excluded; full analytics spec is proposed. | Keep advanced analytics out of Phase 1; define only basic dashboard counts if needed. |
| D-07 | Are analytics configuration choices tenant-configurable? | Proposed platform/org/branch inheritance. | Approve only after privacy, metric governance and override rules are specified. |
| D-08 | Is formal patient merge Phase 1? | MVP supports warnings/correction; formal merge later. | Keep merge Phase 2. |
| D-09 | Is subscription expiry read-only enforcement Phase 1? | Subscription lifecycle automation is Phase 2 direction. | Keep automation Phase 2; basic status visibility may be separately scoped. |
| D-10 | Is a marketing landing page required for MVP? | Not a core operational acceptance criterion. | Defer unless required for hackathon presentation. |
| D-11 | Are platform monitoring/support screens part of customer-facing product? | Blueprint proposes them; architecture includes observability. | Separate internal operator tooling from tenant UI. |
| D-12 | Which basic dashboard metrics are required for MVP? | MVP requires daily operational workflow, not advanced analytics. | Approve a minimal set tied directly to operational records. |

---

## 16. Acceptance checklist for the revised blueprint

The blueprint should be considered implementation-ready only when the following are true:

### Authority and scope
- [ ] Every screen has a stable ID.
- [ ] Every screen has an explicit release classification.
- [ ] Every screen has an approval status.
- [ ] Phase 2/3/proposed screens cannot be mistaken for MVP requirements.
- [ ] Conflicts with MVP Scope, Business Rules and Architecture are resolved or recorded.

### Roles and security
- [ ] Six canonical roles are used consistently.
- [ ] Every action has an authorized role and organization/branch scope.
- [ ] Doctor login is explicitly optional.
- [ ] Assistant access is assignment-scoped.
- [ ] Platform control-plane access is distinct from tenant operations.
- [ ] Public screens expose no patient-identifying information.

### Workflow and data integrity
- [ ] Patient shared-mobile behavior is explicit.
- [ ] Duplicate warning is separated from formal merge.
- [ ] Appointment model choices are limited to time-slot, serial-based and hybrid.
- [ ] Walk-in is a source, not a fourth appointment model.
- [ ] Queue position is separate from booked appointment time.
- [ ] Reschedule preserves and links records.
- [ ] Transfer is same-organization only.
- [ ] No-show requires staff confirmation after the configured grace period.
- [ ] Late arrival does not automatically change queue order.
- [ ] Capacity and concurrency errors are designed.
- [ ] Audit requirements are visible in the relevant workflows.

### UI quality
- [ ] Empty, loading, validation, error, forbidden, stale and offline states are specified.
- [ ] Bangla/English and Unicode behavior is specified.
- [ ] Responsive mobile and desktop behavior is specified.
- [ ] Low-bandwidth/reconnect behavior is specified.
- [ ] Common form/table patterns are defined.

### Engineering handoff
- [ ] Each MVP screen maps to backend actions/API contracts.
- [ ] Each screen maps to required data entities.
- [ ] Dependencies and service ownership are identified.
- [ ] Acceptance criteria are testable.
- [ ] Open decisions are recorded and assigned to the product owner.

---

## 17. Final conclusion

The UI/UX blueprint is a strong design foundation and contains enough material to support a complete AMSDP interface plan. Its main weakness is **scope and authority ambiguity**, not lack of screens.

The next step should be to create a structured index and split the design into approved MVP, later-phase, and proposed sections while preserving the original source. Before AILI uses it for implementation, the team should resolve the P0 conflicts around DQDS, analytics, duplicate merge and subscription lifecycle; clarify the optional floor/session model; and finalize role/action permissions.

**Final disposition:**

- **Accept as a comprehensive design source/archive:** Yes.
- **Accept as the single authoritative Phase 1 implementation specification:** Not yet.
- **Ready for controlled MVP UI planning after R0 corrections:** Yes.
- **Ready for agents to implement every screen in the file:** No.
- **Original file should be rewritten or shortened:** No. Preserve it and create an indexed, release-classified implementation set.

The governing principle is: **the UI blueprint describes possible and intended experiences; the approved MVP scope and business rules determine what AMSDP is authorized to build in Phase 1.**
