# AMSDP Business Rules — Proposed Revision (DRAFT — FOR APPROVAL)

> **Document type:** proposed amendment (NOT the authoritative Business Rules)
> **Status:** DRAFT — prepared for product-owner review and approval
> **Date:** 8 November 2026
> **Basis:** product-owner authorization (2026-11-08) to **prepare** a revision covering
> DQDS/PQT carve-outs, one-way operational WhatsApp/SMS notifications, two-stage patient
> notifications, and required reminder cancellation/deduplication.
> **Important:** `docs/product/AMSDP_Business_Rules_V1.0.md` is **unchanged** by this
> document. If approved, the amendments below are to be folded into a future Business Rules
> revision by the product owner. This proposal does **not** alter any approved business rule.

## 1. Scope of this proposed revision

1. Clarify that DQDS and PQT are **not** patient accounts, portals, or dashboards (so they
   are not captured by the existing BR §2 exclusions while remaining in approved scope).
2. Clarify that **one-way operational WhatsApp/SMS notifications** are not telemedicine or
   patient-provider messaging (so they are not captured by the BR §2 exclusion of
   "Telemedicine or patient-provider messaging", while interactive messaging remains excluded).
3. Add the **two-stage patient notification** requirement (appointment confirmation +
   pre-visit reminder) as approved P0 product scope.
4. Add the required **reminder cancellation and deduplication** behaviour.

**Out of scope for this revision:** Missed-Turn Recovery & Queue Repositioning is **not
approved for MVP** and is intentionally absent here; it will require a separate future
proposal (addressing BR §§20–21, grace periods, late arrivals, queue-state semantics,
emergency/priority handling and audit events).

## 2. Proposed amendment A — DQDS/PQT carve-outs (BR §2)

**Current text (paraphrased):** "Out of scope for the core product: patient portal, dashboard,
app, login, self-registration or self-booking."

**Proposed addition (after the exclusion list in BR §2, as a clarifying note):**

> Consistent with product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`, the following
> capabilities are **in scope** and are **not** "patient portal, dashboard, app, login,
> self-registration or self-booking" for the purpose of the exclusions above:
> - **Digital Doctor Queue Display (DQDS):** a public, read-only waiting-room display showing
>   token numbers and queue state only, with no patient PII.
> - **Personal Queue Tracking (PQT):** an appointment-specific, private tracking page accessed
>   by a cryptographically unguessable capability token (or printed QR code); it grants no
>   account, no login, no dashboard, and access to no data other than the linked appointment's
>   own queue information.

## 3. Proposed amendment B — one-way operational WhatsApp/SMS notifications (BR §2)

**Current text (paraphrased):** exclusions include "Telemedicine or patient-provider
messaging."

**Proposed addition (clarifying note):**

> One-way **operational notifications** sent by the facility through approved channels
> (currently WhatsApp and SMS) — for example appointment confirmation and pre-visit queue
> reminders — are **in scope** and are **not** "telemedicine" or an interactive
> "patient-provider messaging" portal. Interactive two-way messaging and telemedicine remain
> excluded.

## 4. Proposed amendment C — Two-stage patient notifications (new Business Rules section)

**Proposed new section (Part VIII, after §36 SMS):**

> ### 36A. Two-stage patient notifications --- APPROVED P0 PRODUCT SCOPE
>
> 1. **Notification 1 — Appointment Confirmation:** sent immediately after a successful
>    appointment booking. Content (where applicable): patient-facing appointment
>    confirmation; appointment date and visiting time; doctor and facility/branch
>    information; queue token or appointment reference; personal queue tracking (PQT) link;
>    relevant instructions.
> 2. **Notification 2 — Pre-Visit Reminder ("Queue Turn Protection"):** sent a configurable
>    number of minutes before the patient's expected visiting time.
>    - Default lead time: **10 minutes**. Practical options: **5 and 10 minutes**.
>    - Organization admin can configure the lead time, subject to plan/platform limits.
>    - Message content: the patient's turn is approaching; encourage return to or remaining
>      near the facility; include the tracking link where appropriate; state that queue
>      estimates can change.
> 3. **Channels:** WhatsApp and SMS remain independently configurable organization-level
>    channels, subject to provider availability and configuration. Provider credentials are
>    stored securely on the backend and are organization-scoped; never exposed to frontend
>    users or AI agents.
> 4. **Scheduling rules:** reminder scheduling must consider queue changes; cooldown and
>    de-duplication prevent excessive or contradictory notifications.
> 5. **Cancellation and suppression:** pending reminders are cancelled when the appointment is
>    cancelled or rescheduled, or when the consultation has started; unnecessary return
>    reminders are avoided when the patient has already checked in.
> 6. **Delivery honesty:** never claim successful delivery unless the provider confirms it;
>    record operational request/delivery outcomes.
> 7. **Non-blocking:** appointment booking must remain functional when messaging is
>    unavailable or unconfigured; messaging must not delay the core appointment workflow.
> 8. **Implementation status:** this rule defines approved product scope; implementation is
>    tracked separately and is not implied by this rule.