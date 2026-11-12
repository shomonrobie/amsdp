# AMSDP Product Positioning

> **Product:** AMSDP — Appointment Management System for Doctors & Patients
> **Document:** Product positioning, messaging, patient journey and impact framework
> **Version:** 1.0 · **Status:** FOR PRODUCT-OWNER REVIEW · **Date:** 2026-11-08
> **Related decisions:** `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
> (`docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`)
> **Implementation status:** **NOT IMPLEMENTED.** Positioning and journey described here are
> documentation only; DQDS, PQT and notification channels are not yet implemented.

## 1. Positioning statement

> **AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.**

AMSDP is not merely an appointment and queue management system. Its central patient-facing
value is **reducing unnecessary physical waiting** and helping healthcare facilities
**manage waiting-area congestion** through real-time queue visibility and patient
communication.

The tagline carries one strategic point with two complementary benefits:

| Phrase | Whose benefit | What it means |
|---|---|---|
| **Less Waiting** | Patient | With queue visibility, the patient does not need to remain inside a crowded waiting area for the whole estimated wait. Where appropriate, they wait nearby (e.g., a café or tea stall), monitor their queue remotely, and return before their expected turn. |
| **Less Crowding** | Facility | Better visibility and coordination of appointments, walk-ins and queues help the facility manage patient flow and reduce unnecessary waiting-area occupancy. |
| **Better Healthcare Experiences** | Both | Lower stress, less congestion, and more trust in the process for patients, staff, doctors, and attendants. |

## 2. Promise and boundary

**The central promise:** improved queue visibility; reduced **unnecessary** physical waiting;
better management of waiting-area occupancy.

**Boundaries (never claimed):**
- AMSDP does **not** eliminate waiting.
- AMSDP does **not** guarantee consultation times.
- AMSDP does **not** necessarily reduce total clinical waiting time.
- Any estimate shown (DQDS, PQT, tracking page) is an **estimate, never a guarantee**
  (consistent with Business Rules §33 direction).

## 3. Two complementary benefits

### 3.1 For patients: wait comfortably, return on time

1. The patient books or registers through facility staff (no patient account; no mandatory
   mobile app).
2. When the appointment becomes eligible, staff give the patient a **tracking link and/or
   printed QR code** (personal queue tracking, PQT).
3. The patient can leave the crowded waiting area, wait at a nearby comfortable location,
   and watch their live position remotely.
4. The tracking page shows: their token, doctor/branch, currently serving token, patients
   ahead, and an estimated wait with **return-before-turn** guidance.
5. The patient returns shortly before their turn — less time sitting in the waiting area.

### 3.2 For facilities: less congestion, better flow

1. Staff see the unified queue and manage appointments/walk-ins from one board.
2. Public DQDS screens show the current token to keep the waiting area informed.
3. Reduced unnecessary occupancy means more comfortable, safer waiting areas and calmer
   operations.
4. Operational data (appointment-to-consultation time, no-shows/missed turns, queue state)
   supports facility decisions — measured honestly, never invented.

## 4. Bangladesh patient and attendant experience

- Waiting areas in many Bangladeshi facilities are crowded, with patients **often accompanied
  by family attendants** who also occupy the area.
- Nearby cafés and tea stalls are a familiar part of the local environment — a natural remote
  waiting option when it is safe and appropriate.
- AMSDP is **mobile-first and low-bandwidth**: tracking works through a shared link or QR code
  on ordinary smartphones, with Bangla and English support.
- The product respects that some patients cannot (or should not) leave the facility: safety
  rules in §8 always take priority over convenience.
- The benefit story is told in Bangla and English in facility-facing and hackathon-facing
  materials.

## 5. Architecture anchors preserved

| Anchor | Requirement (from PQV decision) |
|---|---|
| Public DQDS vs private PQT | DQDS: read-only waiting-room display, token-based only, no PII. PQT: appointment-specific private tracking via unguessable capability token (hash-at-rest), no account/portal/app. The two surfaces remain distinct; PQT never exposes another patient's data. |
| Channels | WhatsApp **and** SMS are required, **organization-admin-configurable** channels; delivery depends on provider availability; manual link sharing is the fallback. |
| Roles & tenants | The six canonical roles and RBAC are unchanged; all surfaces are org/branch-scoped; tenant key remains `organization_id`. |
| Exclusions | No patient accounts, patient portal, self-service booking, mandatory app, payments, EMR/EHR, telemedicine. |

## 6. Patient journey (booking → tracking → return-before-turn)

```text
1. Registration / booking (staff-mediated)
      │  2. Eligibility (e.g., confirmed / checked-in)
      ▼
3. Tracking link + QR issued (staff gives link or prints token/QR)
      │  4. Remote monitoring (patient waits nearby; watches live position)
      ▼
5. Return-before-turn guidance (patients ahead, estimated wait, buffer)
      │  6. Consultation starts → tracking revoked automatically
      ▼
7. Appointment completed / follow-up handled (/ no-show recorded if applicable)
```

Step detail:

1. **Booking:** authorized staff register the patient and book the appointment
   (time-slot, serial, or hybrid) as today; no patient account exists.
2. **Eligibility:** when the appointment is confirmed or checked in, a personal tracking
   token is issued for that appointment only.
3. **Link + QR delivery:** staff hand the patient a short link and/or printed token with a
   QR code (unavailable channels → manual link sharing remains the fallback).
4. **Remote monitoring:** the patient views their own queue status on any phone — token,
   doctor/branch, currently-serving token, patients ahead, estimated wait.
5. **Return-before-turn:** the page prompts the patient to return a defined buffer before
   their turn; estimated wait is recalculated as the queue changes and is never a guarantee.
6. **Revocation:** when the consultation starts (or appointment is cancelled/rescheduled),
   tracking access is revoked; tokens are never reactivated.
7. **Closure:** completed/consultation done; no-shows and missed turns are recorded; audit
   keeps the notification and tracking event trail.

## 7. Measurable impact indicators

Definitions and measurement source. **None of these figures have been verified yet — no
verified-result numbers exist.**

| # | Indicator | Definition | Measurement source | Status |
|---|---|---|---|---|
| 1 | **Physical waiting-area time** | Time a patient physically spends in the waiting area (not total appointment duration). | Estimated from queue state transitions (check-in → consultation start) where feasible; not yet instrumented | Expected benefit; not verified |
| 2 | **Waiting-area occupancy** | Concurrent patients/attendants physically present (average & peak). | Requires a facility-defined occupancy model (queue-state based estimate or facility-provided counts); **evidence gap** — no occupancy sensing exists | Expected benefit; not verified |
| 3 | **Tracking adoption** | Share of eligible appointments whose tracking link/QR was issued and accessed at least once. | PQT access events (audit); to be instrumented | Expected benefit; not verified |
| 4 | **Return-before-turn rate** | Share of tracked consultations where the patient returned before their turn (no missed turn caused by tracking). | Comparison of tracking access vs consultation start; definition needs pilot agreement | Expected benefit; not verified |
| 5 | **Missed turns** | Eligible appointments skipped/lost due to patient return timing (and no-shows separately). | Queue/appointment status data + audit | Expected benefit; not verified |
| 6 | **Appointment-to-consultation time** | Check-in (or scheduled start) to consultation start. | Queue/appointment timestamps (already partly available) | Expected benefit; partially measurable |

### Distinguishing claims

- **Expected benefits:** directional, hypothesis-level (this document and the concept note).
- **Proposed pilot targets:** concrete targets must be agreed **with pilot facilities** before
  any number is published; none are set here and none are verified.
- **Verified results:** **none exist yet.** No statistic in any AMSDP document claims measured
  reductions in waiting time, occupancy, or related outcomes (Business Rules §"No unsupported
  claims" is preserved).

## 8. Safety safeguards and equity

Remote waiting is an option, **never an obligation**. The product and facilities must protect
patients for whom leaving the waiting area is inappropriate:

| Safeguard | Design requirement |
|---|---|
| Patients who should not leave | Facilities can mark a patient/appointment as **not eligible for remote waiting** (e.g., fragile, unwell, pregnant, pre-procedure, minor without guardian consent). Tracking may still exist, but the suggested action is "please remain in the waiting area". |
| Changing queue estimates | Estimated wait is **recomputed on every relevant queue change**; the tracking page always shows the latest estimate and a "recently changed" signal where practical. Estimates are never guarantees. |
| Return buffer | A **return buffer** (facility-configurable, e.g., "please be back within X minutes") is shown so patients can reach the clinic in time; queue call-out (DQDS/audio where available) remains in use. |
| Emergencies | If a consultation cannot proceed (doctor unavailable, emergency, facility closure), the appointment is handled per the existing status/lifecycle rules; tracking is revoked or updated accordingly; no automatic rebooking assumptions. |
| Assistance required | Patients needing help (elderly, disabled, illiterate, unaccompanied) are supported by **attendants and staff**; AMSDP does not require self-service and never substitutes for staff judgment. |
| Minors | Minor patients are always accompanied; guidance defers to guardian and facility policy. |
| Privacy | Remote monitoring shows only the patient's own appointment; no PII on public DQDS; tokens are unguessable and revoked. |
| Fallback | If WhatsApp/SMS delivery is unavailable, **manual link sharing** (verbal, printed, other channel) still gives the patient access; not having a smartphone never excludes a patient. |

## 9. Inconsistencies with existing authoritative documents and recommended resolutions

Found during this positioning work; **no approved business rule was silently changed.**

| # | Document & statement | Inconsistency / risk | Recommended resolution |
|---|---|---|---|
| 1 | Business Rules §2 excludes "Patient portal, dashboard, app, login…"; §1 lists "Digital queue displays" | DQDS is a *public read-only display* and PQT is a *capability-token page* — neither is a portal/account, but wording may be read ambiguously. | Add explicit carve-outs for DQDS (public read-only display) and PQT (appointment capability token, not a portal/account/login) in the next Business Rules revision. PQV §C/§25.5 record this intent. |
| 2 | Business Rules §2 excludes "Telemedicine or patient-provider messaging" | WhatsApp/SMS are one-way operational notifications (appointment/queue), not a messaging portal. | Explicit caveat in the next BR revision that one-way operational notifications on enabled channels are in scope while interactive messaging/telemedicine stays excluded (PQV §D). |
| 3 | Business Rules "No unsupported claims" / MVP Scope "Do not claim measured reductions… unless verified" | This positioning document must not be read as a measured claim. | Keep the expected-vs-pilot-target-vs-verified distinction (§7); publish no numbers until pilot agreement. **Adopted here.** |
| 4 | Master Feature List §1 "Patients do not need to access or create accounts" | Consistent with PQT (no account). Pointer added to this positioning document. | No resolution needed. |
| 5 | MVP Scope §14 "automated messaging deferred" | Already adjusted by PQV scope addendum (MVP Scope §16). | Already resolved; positioning stays consistent with the addendum. |
| 6 | Impact indicator "appointment-to-consultation time" wording | Operational metric definition only. | Keep as pilot-verifiable metric definition; no performance claim. |

## 10. Status and evidence

- **Status:** positioning package is FOR PRODUCT-OWNER REVIEW.
- **No implementation, source-code, schema, deployment, cloud, or Git changes** were made by
  this task beyond documentation; DQDS, PQT, WhatsApp and SMS remain **not implemented**.
- **Evidence gap:** occupancy measurement and pilot targets require facility agreement and
  instrumentation (§7). No verified impact statistics exist anywhere.

## 11. Public messaging and roadmap framing

### 11.1 Primary public message (website, concept note, pitch)

> **"Patients do not need to remain inside a crowded hospital waiting area throughout their
> entire estimated wait. They can monitor their personal queue remotely and return as their
> turn approaches, when appropriate and safe."**

The public-facing AMSDP website and hackathon materials must **lead with this patient and
facility value proposition** — not present AMSDP as merely an appointment-booking or
queue-management application. Accuracy rules (§2, §7) apply: no elimination of waiting, no
guaranteed consultation times, no unverified congestion-reduction claims.

### 11.2 Directional capabilities to cite (classified, honest)

| Capability | How to cite publicly | Classification |
|---|---|---|
| DQDS (public waiting-room display) | "Token-only waiting-room visibility for facilities" | Approved, MVP/P0; not yet implemented |
| PQT (personal tracking link/QR, return-before-turn) | "Patients can track their own queue and return before their turn" | Approved, MVP/P0; not yet implemented |
| Two-Stage Notifications (confirmation + pre-visit reminder, WhatsApp & SMS) | "Appointment confirmation and a pre-visit 'return to the clinic' reminder via WhatsApp and SMS (subject to provider availability)" | **APPROVED P0 product scope**; provider-dependent; **not implemented** |
| Missed-Turn Recovery (defer-to-end repositioning after staff confirmation) | Directional future capability — present as a planned facility flow; do not present as live | **NOT APPROVED FOR MVP**; proposed/later-phase; not implemented |

Public materials must never imply live WhatsApp/SMS delivery, delivered reminders, or
missed-turn recovery unless the capabilities are implemented and verified in application
code and tests.