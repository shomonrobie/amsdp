# AMSDP
## Smart Appointment & Queue Management for Bangladeshi Healthcare Facilities

**Primary thematic area:** Appointment (#010)  
**Related thematic area:** Hospital Management Software (#006)  
**Development stage:** Product concept and specification; prototype/MVP to be developed.

### 1. Concept Note

#### The Problem

Patients in Bangladesh often face long and unpredictable waiting times when visiting doctors, clinics and hospitals. Appointment information may be managed through phone calls, paper registers, notebooks or disconnected digital tools.

Receptionists and doctors' assistants must coordinate scheduled appointments, serial numbers, walk-in patients, cancellations and changes—often without a single, reliable view of the day's patient queue.

This creates avoidable administrative workload, scheduling conflicts, confusion and a poor patient experience. It also means patients and their attendants often sit for hours in crowded waiting areas without knowing how much longer they must wait—closely related congestion and comfort problems for facilities and patients alike.

#### The Proposed Solution

AMSDP is a lightweight, mobile-friendly appointment and queue management platform designed for Bangladeshi healthcare facilities.

It gives each subscribing hospital, clinic or independent medical chamber a dedicated digital workspace to manage doctors' schedules, patient registration, appointments and daily queues.

Its core capabilities include:

- **Flexible appointment management:** Supports time-slot, serial-based and hybrid appointment systems.
- **Unified patient queue:** Brings scheduled appointments and walk-in patients into one manageable queue.
- **Configurable walk-in handling:** Facilities can place walk-ins at the end of the queue, use first-come-first-served ordering, reserve walk-in capacity or allow authorized staff to decide placement.
- **Simple daily operations board:** Staff can see the day's appointments and queue at a glance, update patient status and manually reorder the queue.
- **Facility-managed registration:** Receptionists or authorized staff register patients and create appointments, without requiring patients to create AMSDP accounts.
- **Operational accountability:** Important queue and appointment changes can be recorded with the responsible staff member, time and reason.

#### What Makes AMSDP Different?

AMSDP focuses on a specific but important operational problem: coordinating appointments and patient flow in facilities where existing processes may still depend heavily on manual work.

Rather than attempting to become a complete hospital management or electronic medical record system, AMSDP concentrates on making daily appointment operations easier to understand and manage.

It is designed around the realities of Bangladesh, where facilities differ in how they issue serials, allocate appointment times and accommodate walk-in patients. The system therefore supports configurable workflows instead of imposing one universal appointment model.

#### Positioning and Patient-Facing Value

> **AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.**

AMSDP is not merely an appointment and queue management system. Its central patient-facing
value is **reducing unnecessary physical waiting** and helping facilities **manage
waiting-area congestion** through real-time queue visibility and patient communication:

- **For patients:** with a personal tracking link or printed QR code, they need not remain
  inside a crowded waiting area for the whole estimated wait. When appropriate, they can
  wait nearby (e.g., a café or tea stall), monitor their queue remotely, and return before
  their expected turn.
- **For facilities:** better visibility and coordination of appointments, walk-ins and
  queues help manage patient flow and reduce unnecessary waiting-area occupancy.

The approved boundaries are preserved: a **public DQDS** screen for the waiting room
(token-only, no PII) and a **private PQT** page per appointment (capability token, no
account/portal/app); **WhatsApp and SMS** as organization-admin-configurable channels with
manual link-sharing fallback. AMSDP does **not** claim to eliminate waiting or guarantee
consultation times. Full detail: `docs/product/AMSDP_Product_Positioning_V1.0.md`.

**Primary public message**

> "Patients do not need to remain inside a crowded hospital waiting area throughout their
> entire estimated wait. They can monitor their personal queue remotely and return as their
> turn approaches, when appropriate and safe."

#### Patient Notifications and Turn Protection (two-stage)

1. **Appointment confirmation** is offered immediately after a successful booking
   (date, visiting time, doctor and facility/branch, queue token or reference, and the
   patient's personal tracking link).
2. **Pre-visit reminder ("Queue Turn Protection")** is offered a configurable number of
   minutes before the expected visiting time (default **10 minutes**; **5/10 minutes**
   practical options), telling the patient their turn is approaching, encouraging return,
   and noting that queue estimates can change.

WhatsApp and SMS remain organization-admin-configurable channels; reminders are scheduled
with queue changes in mind to avoid duplicates; pending reminders are cancelled on
cancellation, rescheduling or consultation start; no return reminder is sent after
check-in; delivery is only ever claimed when the provider confirms it; booking stays
functional without messaging. **Two-Stage Notifications are APPROVED P0 product scope
(2026-11-08), are not yet implemented, and depend on provider availability.**

#### Missed-Turn Recovery and Queue Repositioning (proposed — NOT APPROVED FOR MVP)

For patients who do not return when their turn is called, staff may, after following
facility procedure and confirming the missed turn, defer the patient to the end of the
eligible active queue — preserving the original appointment, token and queue history, with
the previous/new position, actor, timestamp and reason audited. No automatic repositioning
or NO_SHOW occurs from an undelivered or unread message. This is a **proposed capability
that requires a product decision and Business Rules amendments**; it is not MVP scope and
not implemented.

#### Target Users and Beneficiaries

- Hospitals and clinics.
- Independent doctors' chambers and medical practices.
- Receptionists and appointment operators.
- Doctors and their assigned assistants.
- Patients who benefit from clearer appointment and queue coordination.

#### Expected Impact

AMSDP aims to:

1. Reduce manual effort in appointment registration and daily queue management.
2. Improve visibility into appointment schedules and patient flow.
3. Help facilities manage walk-ins and scheduled patients more consistently.
4. Reduce avoidable scheduling conflicts and duplicate bookings.
5. Give facilities useful operational information for improving their services.
6. Improve the patient experience through more organized appointment handling.
7. Reduce **unnecessary** physical waiting and better manage waiting-area occupancy.

These outcomes are **expected benefits and hypotheses** — they will need to be evaluated
through practical testing and facility pilots. No impact statistics are claimed as verified.
Proposed pilot metrics (e.g., physical waiting-area time, waiting-area occupancy, tracking
adoption, return-before-turn rate, missed turns, appointment-to-consultation time) and the
expected-vs-pilot-target-vs-verified distinction are defined in
`docs/product/AMSDP_Product_Positioning_V1.0.md` §7.

#### Patient Journey and Safety Summary

Booking (staff-mediated) → tracking link + QR issued on eligibility → remote monitoring of the
patient's own position → return-before-turn guidance → tracking revoked when the
consultation starts. Remote waiting is an **option, never an obligation**: facilities can
mark patients as not eligible to leave the waiting area; estimates are recomputed and never
guaranteed; a return buffer is shown; manual link sharing works even without WhatsApp/SMS or
a smartphone. Full journey: `docs/product/AMSDP_Product_Positioning_V1.0.md` §6–§8.

#### Feasibility and Implementation

AMSDP is intended to be a lightweight, mobile-first SaaS platform that can be used by facilities with different sizes and operating practices.

The initial version will focus on facility setup, doctor schedules, patient registration, appointment management, queue operations, staff permissions and basic operational reporting.

Each subscribing facility will have its own isolated workspace and records. The initial product will not attempt to replace clinical records, prescriptions, billing or full hospital management systems.

Future integration with wider digital health infrastructure may be explored, subject to technical requirements, standards and appropriate authorization.

---

### 2. Application-Ready Summary

**Project Title**  
AMSDP — Smart Appointment & Queue Management for Bangladeshi Healthcare Facilities

**Thematic Area**  
Appointment (#010)

**Problem Statement**  
Many healthcare facilities in Bangladesh still coordinate appointments and patient queues through phone calls, paper registers and disconnected tools. Managing scheduled appointments, serial numbers, walk-in patients and last-minute changes creates administrative pressure, scheduling conflicts, unpredictable waiting and a frustrating patient experience.

**Proposed Solution**  
AMSDP is a lightweight, mobile-friendly platform that helps hospitals, clinics and independent medical chambers manage doctor schedules, patient registration, appointments and daily patient queues from one workspace. It supports time-slot, serial-based and hybrid appointment systems, together with configurable walk-in policies and a unified queue management board.

**Innovation / Uniqueness**  
AMSDP is designed around the diverse appointment practices of Bangladeshi healthcare facilities. Instead of forcing every facility into one scheduling method, it supports multiple appointment models and configurable walk-in workflows. Its central feature is a unified operational queue that helps staff coordinate scheduled and walk-in patients through a simple daily interface.

**Target Beneficiaries**  
Healthcare facilities, doctors, receptionists, appointment operators, assistants and patients.

**Expected Outcomes**  
More organized appointment operations, reduced manual coordination, improved queue visibility, fewer avoidable scheduling conflicts and better operational information for healthcare facilities.

**Scalability and Sustainability**  
AMSDP is planned as a subscription-based SaaS platform. Individual chambers, clinics and hospitals can operate separate facility workspaces. Its lightweight design and configurable workflows are intended to support adoption by facilities with different operational capacities.

**Current Development Stage**  
The product concept, scope and core workflows have been defined. The staff-side MVP
(organization/branch, staff, doctor, patient, scheduling, appointment, queue, dashboard and
audit) is implemented and verified locally (milestones M1–M7). The patient-facing
capabilities described in this note — **DQDS, Personal Queue Tracking, and WhatsApp/SMS
notification channels** — are **P0-approved requirements that are not yet implemented**
(see `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`). The next step is to validate workflows with
real facility users and to pilot the patient-facing capabilities.

**Long-Term Vision**  
To make appointment and patient-flow management more organized and accessible across Bangladesh's diverse healthcare facilities, while keeping the platform focused, practical and capable of future integration with the broader digital health ecosystem.