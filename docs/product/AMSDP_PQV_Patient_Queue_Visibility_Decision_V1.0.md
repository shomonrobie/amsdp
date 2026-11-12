# AMSDP Product Decision — Patient Queue Visibility & Patient Communication (PQV)

> **Decision ID:** `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
> **Status:** APPROVED (product owner) — design baseline for architecture/scope updates
> **Date:** 8 November 2026
> **Applies to:** AMSDP — Appointment Management System for Doctors & Patients
> **Implementation status:** **NOT IMPLEMENTED.** This document records requirements and
> design direction. DQDS, PQT, WhatsApp and SMS are not yet implemented in the codebase.

## Product-owner approval status (2026-11-08)

| # | Decision | Status |
|---|---|---|
| 1 | Public Product Positioning — "AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences." (primary for public website, hackathon materials, product communications) | **APPROVED** |
| 2 | Two-Stage Patient Notifications (N1 confirmation + N2 pre-visit reminder, default 10 min, 5/10 options; WhatsApp & SMS org-configurable; queue-change-aware scheduling; cooldown/dedup; reminder cancellation; no delivery claim unless provider confirms; booking functional without messaging) | **APPROVED as P0 product scope** |
| 3 | Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** — remains proposed/later-phase; no implementation; future proposal must address BR §§20–21, grace periods, late arrivals, queue-state semantics, emergency/priority handling and audit events |
| 4 | Business Rules reconciliation (DQDS/PQT carve-outs; one-way operational WhatsApp/SMS; two-stage notifications; reminder cancellation/dedup) | **Preparation of a proposed revision authorized** — authoritative Business Rules V1.0 remains unmodified until the proposed revision is separately presented and approved |

## 0. Authority and relationship to other documents

1. This is the authoritative product decision for patient queue visibility (public display and
   personal tracking) and patient communication channels (WhatsApp and SMS).
2. It supersedes or adjusts earlier direction where they conflict with it:
   - Business Rules V1.0 §35 (staff-only communication; SMS later-phase) and §36 (SMS APPROVED
     PHASE 2) — WhatsApp and SMS are here promoted from "later/optional" to **required,
     organization-configurable communication channels**, while actual delivery of each channel
     remains dependent on provider availability (§D.11).
   - Master Feature List V2.0 Draft §14.2 (communication features PENDING) and §23 Phase 3
     (SMS optional extension) — updated per WP2.
   - MVP Scope V1.0 §14 ("automated messaging deferred") — adjusted via the scope addendum
     recorded in the MVP Scope document.
3. **Preserved unchanged:** the six canonical system roles and the existing RBAC permission
   model; the tenant key (`organization_id`); strict tenant and branch isolation; all previously
   approved exclusions (no patient accounts, patient portal, self-service booking, or mandatory
   mobile application).
4. Business Rules V1.0 remains the authoritative behaviour document; where a future Business
   Rules revision reconciles §35/§36 to this decision, this decision takes precedence in the
   interim. Document conflicts are tracked in §9 and in WP2/WP3 outputs.

## A. Four primary personas

The product is designed around four primary personas, all of which remain **staff-mediated**
except the two read-only public surfaces described below:

| Persona | Role in AMSDP | AuthZ model |
|---|---|---|
| 1. **Patient** | Recipient of operational information: sees the public waiting-room display (token only) and can access their own appointment's private tracking page via an unguessable token/link or QR code. No account, no password, no portal. | Token-based read-only |
| 2. **Receptionist** | Registers patients, books/checks-in appointments, manages the queue. | Canonical role `receptionist` (RBAC unchanged) |
| 3. **Doctor** | Views the queue, starts/completes consultations. | Canonical role `doctor` (RBAC unchanged) |
| 4. **Organization Admin** | Runs the facility: dashboard, audit, branch switching, and — new — **channel configuration (WhatsApp/SMS)** for the organization. | Canonical roles `org_admin`/`branch_admin` + new org-scoped settings surface |

The six canonical roles (super_admin, org_admin, branch_admin, receptionist, doctor, assistant)
and the permission matrix are **preserved exactly**. Patient-facing surfaces add new read
capabilities (public display read, tracking read) but no new roles and no changes to the staff
authorization model.

## B. Public Doctor Queue Display (DQDS)

1. **Purpose:** a public, read-only waiting-room display for one or more doctors/rooms.
2. **Data shown:** currently serving token plus relevant queue information — never patient names,
   mobile numbers, DOB, age, or any other PII.
3. **Token-based visibility:** display shows only token numbers and operational state
   (current/next tokens), consistent with Business Rules §33 (FINALIZED DIRECTION).
4. **Read-only:** no public user can change appointments, queues, or settings.
5. **Tenant isolation:** every display data feed is org- and branch-scoped; a display never
   serves another tenant's queue.
6. **Classification:** DQDS is **MVP/P0**, with multi-display configuration part of the same
   capability.

## C. Personal Queue Tracking (PQT)

1. **Purpose:** private, appointment-specific queue tracking for a patient.
2. **No account, no password, no portal, no mandatory mobile application.** The patient uses a
   shared link or printed QR code only.
3. **Tracking token:**
   - Cryptographically unguessable (`secrets.token_urlsafe`-grade entropy).
   - **Store the token hash where practical**; never store the raw token in logs or API responses.
   - One tracking token per eligible appointment; generated when the appointment becomes
     eligible (e.g., confirmed/checked-in), shown in the UI and printed on the queue token/QR.
4. **Tracking page shows only the patient's own appointment:** token, doctor/branch, currently
   serving token, patients ahead, estimated wait/time, and appointment status.
5. **Estimated waiting time is an estimate, never a guarantee** — clearly labelled.
6. **Revocation:** access is revoked when the consultation starts, or when the appointment is
   cancelled or rescheduled. **Expired/revoked tokens are never reactivated.**
7. **No caching** of private tracking responses (no-cache storage headers).
8. **Rate limiting** on the public tracking endpoint (see §F.6).
9. **Classification:** PQT is **MVP/P0** (no external provider dependency).

## D. Patient Notifications — WhatsApp AND SMS

1. **Both** WhatsApp and SMS are required communication channels. Each customer organization's
   admin configures them for their organization.
2. Organization admin can, in the **organization admin panel**:
   - enable or disable WhatsApp (§E for governance boundaries);
   - enable or disable SMS;
   - configure provider/integration settings for each enabled channel, subject to
     platform-supported providers and permissions.
3. **Platform Super Admin governance remains separate** from organization-level configuration
   (see §E).
4. Provider credentials and secrets are stored securely on the backend and **never exposed to
   the frontend** (see §F.4).
5. Configuration is **organization-scoped**; one org's credentials/settings must never be
   accessible to another organization.
6. The system supports patient appointment and queue-related notifications through enabled
   channels (appointment confirmation/reminder, check-in/queue events, etc.).
7. WhatsApp tracking messages include the patient's appointment-specific tracking URL.
8. SMS notifications support an appropriate tracking URL where applicable.
9. **Manual link sharing remains the fallback** when a provider integration is unavailable or
   not configured.
10. The configuration page clearly shows, per channel: **enabled / configured / operational**
    state.
11. **No assumption of existing provider accounts, APIs, sender IDs, template approval, or paid
    services.** Whether delivery actually works depends on provider readiness (§E.5).

## E. Platform Super Admin vs. organization-level governance

| Concern | Platform Super Admin (central) | Organization Admin (customer) |
|---|---|---|
| Channel availability | Defines which channels exist and which providers are supported per platform (and per plan). | Enables/disables channels for the organization within platform allowances. |
| Provider registry | Registers/activates providers in a central registry, sets global defaults, permitted ranges, and (where applicable) template/sender-ID applicability. | Selects from the platform-approved provider list; cannot introduce unapproved providers. |
| Credentials/secrets | Defines custody rules; may hold platform-level defaults. | Enters org-specific API keys/tokens; stored encrypted backend-side, org-scoped. |
| Limits/quota | Sets plan-pinned rate/volume limits. | Views usage/limit state; cannot bypass. |
| Operational status | Central health/readiness of provider integrations. | Per-channel enabled/configured/operational indicator. |

No organization admin can read, modify, or infer another org's settings or secrets.

## F. Security and compliance requirements

1. **PII minimization:** public surfaces (DQDS) carry no PII; tracking surfaces carry only the
   linked patient's appointment data.
2. **Token security:** unguessable tokens; hash-at-rest; narrow read scope; revocation on
   consultation start, cancellation, or reschedule; **no token reuse**; no-cache responses.
3. **Tenant isolation:** all new surfaces are org- and branch-scoped; cross-tenant access fails
   closed (404 non-disclosing).
4. **Secret custody:** provider credentials encrypted at rest on the backend, org-scoped, never
   in frontend bundles, logs, error responses, or in this repository.
5. **Auditability:** configuration changes (channels enabled/disabled, provider settings) and
   relevant notification events (request, delivery status, failure, revocation) are recorded in
   the persistent audit trail.
6. **Rate limiting:** apply rate limits to login, patient creation, **and public tracking
   endpoints** (token-retrieval/query surfaces) to bound abuse (429 with headers).
7. **Delivery honesty:** no silent claim that a message was delivered; record operational
   request/delivery outcomes; appointment creation never blocks on messaging.

## G. Document conflicts discovered and resolved

| Source | Original statement | PQV change | Resolution |
|---|---|---|---|
| Business Rules §35 | SMS is later-phase; communication staff-only | WhatsApp + SMS promoted to required channels; org-admin configurable | §D overrides; §35/§36 reconciled in next BR update |
| Business Rules §36 | SMS APPROVED, PHASE 2 | WhatsApp added; both promoted to required | Same |
| MVP Scope §14 | "Automated messaging … deferred" | Messaging is P0 required; pre-visit intake remains deferred | Scope addendum in MVP Scope V1.0 |
| Master Feature List §14.2 | Communication features PENDING; SMS optional Phase 3 | Updated per WP2 | Feature list updated |
| System Architecture §5.11 | Notification Service — later capability | Elevated to required; provider delivery remains provider-dependent | Architecture §5.11 updated |
| System Architecture §13 | No provider-secret storage defined | Requires encrypted org-scoped secret store | Architecture §13 updated |

## H. Feature classification (captured for WP2/feature list)

| Capability | Classification |
|---|---|
| DQDS (public display) | Approved, **MVP/P0** — no external dependency |
| PQT (personal tracking: link, QR, live position, patients-ahead, ETA with return-before-turn, expiry/revocation, no-cache, rate limiting) | Approved, **MVP/P0** — no external dependency |
| WhatsApp delivery | Approved channel requirement — **provider-dependent** (account/API, template approval, costs may apply) |
| SMS delivery | Approved channel requirement — **provider-dependent** (account/sender ID, costs may apply) |
| Two-Stage Patient Notifications (confirmation + pre-visit reminder) | **APPROVED P0 product scope** (see §J) — **provider-dependent** for actual delivery; not implemented |
| Missed-Turn Recovery & Queue Repositioning | **NOT APPROVED FOR MVP** (see §K) — proposed/later-phase; requires future product decision + Business Rules amendments (§§20–21, grace, late arrival, queue semantics, emergency/priority, audit); not implemented |
| Advanced multi-display management, richer notification matrix, additional channels | Later-phase enhancements |

## I. No-implementation statement

This decision has **not been implemented** and no cloud activity has occurred. It is
documentation-only output of the coordinated documentation tasks (decision ID above).

## J. Two-Stage Patient Notifications & Queue Turn Protection

Product capability (**APPROVED as P0 product scope** on 2026-11-08; see §H and §I for
classification and implementation status).

### J.1 Notification 1 — Appointment Confirmation

- **Trigger:** immediately after a successful appointment booking.
- **Content (where applicable):** patient-facing appointment confirmation; appointment
  date and visiting time; doctor and facility/branch information; queue token or appointment
  reference; personal queue tracking (PQT) link; relevant instructions.

### J.2 Notification 2 — Pre-Visit Reminder ("Queue Turn Protection")

- **Trigger:** a configurable number of minutes before the patient's expected visiting time.
- **Default:** **10 minutes**.
- **Configuration:** organization admin can configure the reminder lead time; **5 and
  10 minutes are the practical options**, subject to platform-configurable permitted limits.
- **Content:** tell the patient their turn is approaching; encourage them to return to or
  remain near the facility; include the tracking link where appropriate; **clarify that
  queue estimates can change**.
- **Queue-change awareness:** reminder scheduling must consider queue changes; avoid
  duplicate or excessive reminders when the estimated visiting time changes repeatedly
  (cooldown/dedup rules to be defined with implementation).

### J.3 Delivery honesty

- **Never claim successful delivery unless the provider confirms it.** Recorded operational
  outcome (requested/delivered/failed/undelivered/unread) is evidence; "sent" is not
  "delivered".
- Undelivered or unread messages **never** trigger automatic queue repositioning or
  no-show marking (see §K.2 rules).

### J.4 Channel configuration (unchanged from §D, extended)

Organization admin can:
- enable/disable **WhatsApp**;
- enable/disable **SMS**;
- configure approved provider settings;
- configure the **reminder lead time**;
- see per-channel **enabled / configured / operational** status.

Provider credentials remain securely stored on the backend and organization-scoped.

### J.5 Acceptance criteria (proposed)

1. Booking a valid appointment emits exactly one Stage-1 confirmation request for each
   enabled channel with configured provider (no duplicates).
2. The reminder fires at the configured lead time (5 or 10 minutes) before the expected
   visiting time **only when the queue state supports it** (no reminder for a completed,
   cancelled, or moved appointment).
3. Repeated estimate changes do not produce repeated reminders within the defined cooldown.
4. Provider outcome (requested/delivered/failed/undelivered) is recorded; the UI and audit
   never show "delivered" unless the provider confirms it.
5. Disabling a channel or removing its provider suppresses requests on that channel without
   affecting booking or the other channel.
6. Organization A cannot read or modify organization B's channel configuration or secrets.

### J.6 Approved behavioural requirements (product-owner, 2026-11-08)

1. **Queue-change awareness:** reminder scheduling must consider queue changes.
2. **Cooldown/deduplication:** implement to prevent excessive or contradictory notifications
   when the expected visiting time changes repeatedly.
3. **Cancellation:** cancel pending reminders when the appointment is cancelled, rescheduled,
   or the consultation has started.
4. **Check-in suppression:** avoid unnecessary return reminders when the patient has already
   checked in.
5. **Delivery honesty:** never claim delivery unless confirmed by the provider.
6. **Non-blocking booking:** appointment booking must remain functional if messaging is
   unavailable or unconfigured.
7. **Scope/status distinction:** this approval is product scope only; implementation status is
   tracked separately (currently **not implemented**).

## K. Missed-Turn Recovery & Queue Repositioning (proposed)

**Product-owner status (2026-11-08): NOT APPROVED FOR MVP.** This capability remains a
**proposal for later-phase consideration**. It is **not** approved scope and **not**
implemented. Existing queue and no-show rules are unchanged.

### K.1 Expected workflow

1. Patient receives the pre-visit reminder (§J.2).
2. The patient's turn approaches.
3. Staff calls the patient according to facility procedure.
4. If the patient is absent, staff may proceed with the next eligible patient.
5. Once another patient enters the doctor's room, staff can **confirm the missed turn** and
   move the absent patient's appointment to the **end of the eligible active queue**.
6. **Preserve** the original appointment, token and complete queue history.
7. Notify the patient of the deferred turn and updated queue information through the enabled
   channel, where available.

### K.2 Hard rules

- **No automatic repositioning** merely because a message was undelivered or unread.
- **No automatic NO_SHOW** marking (no-show remains a staff/operator decision per policy).
- Repositioning is an **authorized, staff-confirmed action**.
- **Preserve the original appointment time**; queue repositioning must not silently change it.
- **Audit trail**: previous position, new position, actor, timestamp and reason.
- Preserve **emergency and priority queue rules**.
- The patient **must not lose their appointment solely because they chose remote waiting**.
- Define interaction with the existing **grace-period and no-show policy** (see §K.4).
- The queue must remain **concurrency-safe** (atomic reorder, consistent with M5 patterns).

### K.3 Conflicts with existing approved queue/appointment rules (identified)

| Existing rule | Conflict / gap | Required product decision / business-rule amendment |
|---|---|---|
| BR Queue statuses (§18–§29 implementation) | No "deferred/repositioned" queue state is defined; repositioning currently happens via manual reorder only. | Approve a named, auditable repositioning action/state (or explicit status-history entry) distinct from a plain manual reorder. |
| BR §20 No-show policy / grace period | Relationship between "missed turn" and NO_SHOW/grace expiry is undefined for the remote-waiting scenario. | Amendment: define that a confirmed missed turn in the recovery flow defers (does not no-show) the patient; NO_SHOW only per the existing no-show policy; grace-period rules explicitly extended or stated. |
| BR §21 Late arrival | Late-arrival handling may place patients at the end or keep slots — must not conflict with staff-confirmed repositioning. | Amendment: state that repositioning follows the approved late-arrival policy and never rewrites the appointment time. |
| BR §28 Priority entries | Repositioning must not reorder priority entries. | Confirmed rule: priority entries are never displaced by "end of queue" repositioning. |
| BR §33 DQDS / PQT | Repositioning updates the displayed/tracked position live. | Requirement: displayed and tracked positions reflect the repositioning immediately; tracking link remains valid (appointment preserved). |
| Audit (BR §40) | "Queue and serial adjustments" audited; repositioning needs the same guarantees (before/after, actor, reason). | No conflict — explicit audit event types for `queue.missed_turn` / `queue.reposition`. |

### K.4 Recommended resolution path

- Record this proposal; do **not** silently override existing queue rules.
- **Future proposal requirements (confirmed 2026-11-08):** any future proposal must address
  Business Rules §§20–21, grace periods, late arrivals, queue-state semantics,
  emergency/priority handling and audit events.
- Product-owner approval then required to: (1) confirm the workflow, (2) amend Business Rules
  §20/§21/grace-period text and define the queue status/history semantics, (3) schedule the
  capability; until then it is explicitly **not MVP** and **not implemented**.

### K.5 Acceptance criteria (proposed)

1. Repositioning is only possible through an explicit staff action (never automatic), with a
   required reason.
2. The absent patient's appointment and original appointment time are unchanged; only the
   queue position moves to the end of the eligible active queue.
3. Position change is atomic and concurrency-safe (no duplicates or lost updates under
   concurrent queue operations).
4. Audit records previous position, new position, actor, timestamp and reason; the queue
   exposes the change to DQDS/PQT immediately.
5. Priority and emergency entries are never displaced.
6. An undelivered/unread reminder never repositions the patient or marks NO_SHOW.
7. When approved, the flow's interaction with grace-period/late-arrival/no-show policy is
   documented and enforced per the amended Business Rules.