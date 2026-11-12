# AMSDP — Master Feature List V2.3 (Consolidated Draft)

## Facility-Centric, Lightweight Appointment Management SaaS

**Working baseline:** 9 November 2026 (V2.2 amendment)\
**Supersedes for working use:** V2.1 Consolidated Draft and V2.0 Draft (both retained as historical baselines)\
**Market focus:** Bangladesh\
**Document status:** Consolidated Draft for Product Owner Review — NOT APPROVED AS A WHOLE; approved decisions are individually marked

------------------------------------------------------------------------

# Part I --- Product Vision, Scope and Core Architectural Principles

## 1. Product Vision

AMSDP is a lightweight, facility-centric appointment management platform
for Bangladeshi hospitals, clinics and independent medical practices.

Its purpose is to help authorized facility staff manage doctor
appointment schedules, patient registration for appointment purposes,
appointment booking and changes, serial and queue operations, walk-in
patients, appointment status and basic operational visibility.

AMSDP is operated by the facility's administrators, receptionists,
appointment operators and assigned assistants. Patients communicate with
the facility through its existing channels, such as telephone calls and
in-person visits. Patients do not need to access or create accounts on
AMSDP.

**Product promise:** make daily appointment operations simple, fast,
flexible and reliable without requiring a facility to replace its
existing hospital or clinic management software.

> **Positioning (2026-11-08):** AMSDP's central patient-facing value is
> reducing **unnecessary physical waiting** and better managing
> waiting-area occupancy through real-time queue visibility and patient
> communication — "**Less Waiting. Less Crowding. Better Healthcare
> Experiences.**" See `docs/product/AMSDP_Product_Positioning_V1.0.md`
> and decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`.

## 2. Product Positioning

AMSDP is an **Appointment Management System**, not a complete Hospital
Management System (HMS), Electronic Medical Record (EMR), Electronic
Health Record (EHR), Practice Management System (PMS), billing platform
or doctor-management system.

It should work as a focused appointment tool alongside a facility's
existing software---or independently where the facility does not have
another system.

### Primary subscribers

1.  Hospitals.
2.  Clinics.
3.  Independent medical practices, including a doctor's personal
    chamber.
4.  Other appointment-based healthcare facilities, if enabled by AMSDP.

A personal chamber is treated as an independent facility/practice for
subscription, appointment operations and data isolation.

Doctors, assistants, receptionists and facility administrators are users
of the relevant facility workspace. A doctor is not required to
subscribe personally or create an AMSDP account for a hospital to create
an appointment profile for that doctor.

## 3. Product Scope

### 3.1 In scope

-   Facility subscription and independent facility workspaces.
-   Lightweight doctor entries for appointment scheduling.
-   Facility-managed patient registration.
-   Appointment creation, rescheduling and cancellation workflows.
-   Time-slot, serial-based and hybrid appointment models.
-   Doctor availability and appointment capacity configuration.
-   Walk-in registration and placement.
-   Unified queue management with configurable priority.
-   Touch-friendly daily appointment board.
-   Staff roles and appointment-specific permissions.
-   Appointment status tracking.
-   Basic operational reports.
-   Tenant isolation, security and audit history.
-   Bangla and English interface support.
-   Mobile-friendly, low-bandwidth staff experience.

### 3.2 Out of scope for the core product

The following are deliberately excluded from the initial AMSDP scope:

-   Patient portal, patient dashboard or patient login.
-   Patient-facing doctor directory or appointment marketplace.
-   Patient self-booking through AMSDP.
-   Public display of doctors' daily schedules or availability calendars. **Approved exception:** DQDS is a token-only, read-only public queue display; it is not a public doctor schedule and must not expose patient PII.
-   Online payment gateway or payment processing.
-   bKash/Nagad account management, QR-code management or transaction
    reconciliation.
-   Financial ledger, invoicing, billing, payroll or revenue settlement.
-   Prescription writing or clinical consultation documentation.
-   Full electronic medical records or patient clinical history
    management.
-   Vitals collection and clinical intake forms.
-   Insurance administration and claims.
-   Hospital HR, attendance or employment management.
-   Pharmacy, inventory, laboratory or diagnostic operations.
-   Telemedicine, patient-provider messaging or two-way patient communication. Approved one-way operational appointment/queue notifications over WhatsApp and SMS are a narrow exception and do not create a patient messaging portal.
-   Central doctor directory or cross-organization doctor matching.
-   Cross-organization patient or appointment data sharing.

These may be considered separately in the future only if they directly
support the product strategy and are explicitly approved.

## 4. Core Architectural Principles

### 4.1 Facility-first subscription model --- FINALIZED

-   Hospitals and clinics subscribe as organizations.
-   An independent doctor's personal chamber can subscribe as an
    independent practice/facility.
-   Doctors are appointment-related users or entries within a facility
    workspace; they do not need individual subscriptions to work at a
    subscribed hospital.
-   A doctor who operates an independent chamber may subscribe through
    that independent practice.
-   Each subscriber controls its own appointment operations and
    workspace.

### 4.2 Strict organizational data isolation --- FINALIZED

Every subscribing organization operates an independent logical AMSDP
environment.

-   No cross-organization patient record access.
-   No cross-organization appointment or schedule access.
-   No cross-organization assistant or staff access.
-   No cross-organization doctor-record discovery.
-   No automatic data transfer when a doctor changes facilities.
-   No central doctor identity or automatic matching between
    organizations.
-   A doctor entered by Hospital A and a doctor with the same name
    entered by Hospital B are separate records.
-   A doctor's personal chamber and a hospital where the doctor works
    maintain separate patient records, appointments and operational
    permissions.

The software and infrastructure may be centrally operated by AMSDP, but
tenant-level authorization and data isolation must prevent one
subscriber from accessing another subscriber's data.

### 4.3 Lightweight doctor entries --- FINALIZED

A facility can create a doctor entry without the doctor's participation.

Mandatory fields: - Doctor name. - Doctor mobile number.

The system generates an internal unique Doctor ID for that facility's
record.

Additional appointment-related information---such as specialty,
department, chamber, room, schedule or notes---may be added when needed.
AMSDP does not manage employment, payroll, credentials or the doctor's
wider professional administration.

Doctor mobile-number uniqueness is an AMSDP Super Admin policy: -
Default: unique within an organization. - Super Admin may allow
duplicates within an organization. - The same number may exist in
different organizations because their data is isolated.

### 4.4 Facility-owned patient records --- FINALIZED

-   Patients do not need AMSDP accounts.
-   Authorized facility staff create and manage patient records.
-   Minimum mandatory registration fields are patient name and mobile
    number.
-   Multiple patient records may be associated with one mobile number
    within the same facility, supporting family members who use a shared
    contact number.
-   Searching that number displays the associated patient records that
    the staff member is authorized to access.
-   Staff confirms which person is being booked before creating the
    appointment.
-   Each patient record and appointment history remains separate.
-   A shared mobile number does not grant access to another facility's
    records.

### 4.5 Appointment-first, not clinical-management-first --- FINALIZED

AMSDP stores only the information needed to operate appointments. It
does not become the system of record for clinical notes, prescriptions,
diagnoses, investigations or treatment.

### 4.6 Provider-managed booking --- FINALIZED

The normal booking journey is:

1.  Patient calls or visits the hospital, clinic or practice.
2.  Receptionist, assistant or authorized staff member searches for or
    registers the patient.
3.  Staff checks the internal schedule.
4.  Staff decides whether and when to book the appointment under the
    facility's rules.
5.  Staff communicates the appointment information to the patient
    outside AMSDP.
6.  Staff updates the appointment and queue in AMSDP.

Patients do not need to browse schedules, book online or interact with
the AMSDP platform.

### 4.7 External payment, minimal appointment flag --- FINALIZED

Any advance payment is arranged and handled outside AMSDP through the
facility's chosen method.

AMSDP does not process or manage payments and does not store payment
amounts, wallet details, QR codes, transaction IDs, invoices or
financial ledgers.

If a facility requires advance payment before confirming a booking,
AMSDP may record only the appointment-level outcome needed for
scheduling, such as: - Awaiting external confirmation. - Appointment
confirmed.

An authorized staff member updates the appointment after confirming the
external arrangement. This is an appointment state, not a
payment-management module.

### 4.8 Configurable policies with centrally defined limits --- FINALIZED

-   AMSDP Super Admin defines which configuration options are available,
    system defaults, limits and permission boundaries.
-   The subscriber configures its facility's appointment policies.
-   The subscriber may delegate configuration rights to authorized
    users.
-   Users can change settings only when they have the relevant
    permission.
-   Mandatory platform security and tenant-isolation rules cannot be
    overridden.
-   Important configuration changes should be audit logged.

### 4.9 Flexible appointment models --- FINALIZED

AMSDP supports three appointment models, selectable by facility and,
where appropriate, by doctor or consultation location:

1.  Time-slot based.
2.  Serial-based.
3.  Hybrid.

Appointment model, payment-related confirmation requirement and queue
policy are separate configuration concepts. Payment processing itself is
out of scope.

### 4.10 Estimated reporting time only --- FINALIZED

AMSDP supports estimated reporting time. It does not impose a guaranteed
consultation time or guaranteed time window. Facilities communicate
expected reporting time to patients outside AMSDP.

### 4.11 Lightweight and mobile-friendly --- APPROVED PRODUCT PRINCIPLE

-   Staff workflows should work well on desktop, tablet and mobile.
-   Large touch targets and simple actions.
-   Fast loading and minimal screen transitions.
-   Bangla and English UI support.
-   Unicode Bangla input support.
-   Low-bandwidth performance.
-   Clear save, error and connection states.
-   Avoid unnecessary animations, large assets and complex dashboards.

------------------------------------------------------------------------

# Part II --- Lightweight Master Feature List

## 5. Interfaces and User Roles

### 5.1 AMSDP Super Admin Dashboard --- APPROVED ROLE / PLATFORM GOVERNANCE

Platform-level functions only: - Create, activate, suspend and manage
subscriber accounts. - Manage subscription plans, limits and expiry. -
Configure available appointment models and policy options. - Set default
values and configurable limits. - Configure permission templates and
role options. - Configure doctor mobile-number uniqueness policy. - View
tenant-level usage and system health. - Manage platform support and
audit metadata.

Super Admin functions must not create routine cross-tenant access to
patient or appointment content.

### 5.2 Facility Dashboard --- APPROVED WORKSPACE; FEATURE DETAILS SUBJECT TO PERMISSIONS

The primary subscriber workspace: - Facility profile and basic
settings. - Manage branches or locations if enabled. - Create and manage
doctor appointment entries. - Configure doctor schedules. - Manage staff
accounts and role permissions. - Manage patient records. - Manage
appointments and queues. - View daily operational summaries. - Configure
walk-in and queue policies.

### 5.3 Receptionist / Appointment Operator --- APPROVED ROLE

-   Search patient records.
-   Register new patients.
-   Create, reschedule and cancel appointments according to permission.
-   Register walk-ins.
-   Check patients in.
-   Update appointment attendance status.
-   View the relevant doctor schedule.
-   Manage queue position if authorized.

### 5.4 Doctor --- APPROVED OPTIONAL LOGIN ROLE

A doctor account is not mandatory for a facility to use AMSDP.

Where a facility chooses to provide doctor access, the doctor may be
allowed to: - View their own appointment list and queue. - View relevant
schedule information. - See appointment changes. - Update limited
appointment statuses if permitted.

No clinical record, prescription or full doctor-management workspace is
included.

### 5.5 Assistant --- APPROVED ROLE

-   Manage appointments for assigned doctor(s).
-   Register patients and walk-ins.
-   Check patients in.
-   Update queue status and position.
-   Reschedule or cancel appointments when permitted.
-   View only the doctor/facility data assigned to the assistant.

Assistant-to-doctor assignment limits and role permissions should be
configurable within Super Admin policy boundaries.

## 6. Facility and Doctor Setup

### 6.1 Facility setup --- APPROVED CORE; OPTIONAL HIERARCHY

Minimum facility setup:
- Organization/facility identity and contact information.
- Operating days and hours.
- Default appointment settings.

Branches are supported within an organization and are not separate
tenants. Department, floor and room hierarchy is optional. A single-
branch, single-chamber clinic must work without configuring departments,
floors or rooms. Patient records are shared across branches within the
organization; each appointment retains its assigned branch.

### 6.2 Doctor appointment entry --- APPROVED

Mandatory: - Doctor name. - Doctor mobile number.

System-generated: - Facility-local Doctor ID.

Optional appointment-related fields: - Specialty. - Department. -
Branch/location. - Consultation room. - Schedule. - Appointment model. -
Internal operational note.

No central doctor directory, central identity matching or employment
profile.

## 7. Patient Registration and Search

### 7.1 Quick patient registration --- FINALIZED

Mandatory: - Patient name. - Mobile number.

Optional fields may be added only when useful to appointment operations.

### 7.2 Patient search --- APPROVED

Search by: - Mobile number. - Patient name. - Internal patient ID, if
available.

Search results should be fast and easy to distinguish, especially when
names are repeated.

### 7.3 Shared mobile numbers and family records --- FINALIZED

-   One mobile number may be associated with multiple patient records
    within the same facility.
-   Search by that number displays the associated records permitted to
    the staff member.
-   Staff selects the actual patient before booking.
-   Each patient has a separate facility-local record and appointment
    history.

### 7.4 Duplicate handling --- APPROVED

- Warn staff when a likely duplicate patient record exists.
- Allow authorized staff to select an existing record.
- Do not automatically merge records based only on matching name or
  mobile number.
- Patient records are organization-scoped and shared across branches
  within that organization; appointments retain their branch.
- Patient name and mobile number are mandatory. Age may be recorded;
  date of birth is optional. If DOB is present, DOB-derived age is
  authoritative; a separately reported age remains distinguishable.
  Do not infer DOB when it is not supplied.
- Any future merge capability requires explicit authorization and an
  audit record; it is not an MVP requirement.

## 8. Appointment Management Engine

### 8.1 Appointment creation --- APPROVED

Staff can create an appointment by selecting: - Patient. - Doctor. -
Facility location/branch, if applicable. - Appointment date. -
Appointment model and available slot/serial. - Booking source, such as
phone, in-person, assistant or reception. - Optional operational note.

### 8.2 Appointment models --- FINALIZED

Support all three: 1. **Time-slot based:** Appointment is assigned to a
defined time slot. 2. **Serial-based:** Appointment is assigned a
serial/token in the day's queue. 3. **Hybrid:** Facility combines time
windows and serial/queue order.

The facility configures which model applies. Different doctors or
locations may use different models where supported by the facility's
configuration.

### 8.3 Appointment status --- APPROVED

The canonical lifecycle statuses are:

1. `BOOKED`
2. `AWAITING_CONFIRMATION`
3. `CONFIRMED`
4. `CHECKED_IN`
5. `IN_QUEUE`
6. `IN_CONSULTATION`
7. `COMPLETED`
8. `CANCELLED`
9. `NO_SHOW`
10. `RESCHEDULED`

The status names are canonical system states. UI labels may be localized.
A status transition must be valid for the current state and actor's
permission. Rescheduling preserves the original appointment history and
creates a linked replacement appointment; it must not silently overwrite
the original record. `NO_SHOW` is staff-confirmed under the configured
grace-period policy; it is never inferred solely from a missed or
undelivered notification. Consultation start/completion permissions are
limited to doctors and appropriately authorized administrators; a
receptionist cannot start or complete a consultation.

### 8.4 Appointment changes --- APPROVED

Authorized staff can, within branch and role permissions:
- Change appointment date or time slot through an explicit reschedule workflow.
- Change queue position independently of the appointment date/time.
- Transfer an appointment to another permitted doctor or branch within
  the same organization, preserving history.
- Cancel or reschedule with the required reason.
- Add an internal operational note where supported.

A queue reorder must never silently change the appointment date or
scheduled time. Rescheduling retains the original appointment and creates
a linked new appointment. Cross-organization transfer is prohibited.
Every consequential change records actor, timestamp, reason where
required, and relevant before/after values.

### 8.5 Double-booking protection --- APPROVED

Booking and capacity validation must be atomic at save time so
concurrent staff actions cannot exceed configured capacity. Overbooking
is configurable but disabled by default. Capacity limits are configured
at the appropriate facility/branch/doctor or schedule level supported
by the product; reserved walk-in capacity defaults to zero. The system
must distinguish slot capacity, serial capacity and queue position.

### 8.6 Booking source --- APPROVED

Record how the appointment was received: - Phone call. - In-person. -
Doctor assistant. - Reception. - Walk-in. - Other facility-approved
source.

This is operational metadata, not a patient-facing channel.

## 9. Scheduling and Availability

### 9.1 Doctor schedule --- APPROVED

-   Configure working days.
-   Configure start and end times.
-   Configure breaks and unavailable periods.
-   Configure appointment duration for time-slot models.
-   Configure serial capacity for serial-based models.
-   Configure hybrid rules.
-   Block dates or periods when appointments should not be accepted.

### 9.2 Facility-level defaults --- APPROVED

-   Default working hours.
-   Default appointment model.
-   Default walk-in policy.
-   Default queue policy.
-   Default appointment statuses.
-   Default staff permissions.

A facility may override defaults where Super Admin policy allows.

### 9.3 Availability visibility --- FINALIZED

Schedules are internal to authorized facility users. Patients do not
browse or see the facility's daily doctor schedule through AMSDP.

## 10. Walk-In Management

### 10.1 Walk-in registration --- FINALIZED

Minimum mandatory details: - Patient name. - Mobile number.

Authorized staff registers the patient in the facility's workspace.

### 10.2 Walk-in queue placement --- FINALIZED

Support four configurable policies: 1. **End of queue:** Walk-in
patients join after existing bookings. 2. **First-come, first-served:**
Queue order follows the facility's configured arrival/registration rule.
3. **Reserved capacity:** Facility reserves a configurable number or
percentage of appointments/serial capacity for walk-ins. 4.
**Staff-controlled placement:** Authorized staff manually determines the
walk-in's queue position.

### 10.3 Walk-in configuration --- FINALIZED

-   AMSDP Super Admin defines available options and defaults.
-   Subscriber configures its preferred policy.
-   Authorized users may change the policy if granted permission.
-   Configuration changes are audit logged.

## 11. Queue and Serial Management

### 11.1 Unified queue --- FINALIZED

The facility can manage a unified queue containing applicable
appointment sources, including advance bookings, phone bookings,
assistant/reception bookings, walk-ins, rescheduled appointments and
authorized priority entries.

The exact queue behavior is configurable within platform rules.

### 11.2 Manual queue changes --- FINALIZED

Authorized staff may:
- Move a patient up or down and change queue position.
- Adjust serial order where permitted.
- Mark a patient absent or temporarily unavailable using the approved
  staff workflow.
- Skip a patient and continue to the next patient where permitted.

Queue position is distinct from appointment time. No-show remains
staff-confirmed under a configurable grace period. The system must not
automatically mark a patient NO_SHOW or reposition them based on unread,
undelivered or unacknowledged messages. Missed-Turn Recovery is approved P0/MVP: staff-confirmed recovery defaults to the end of the same applicable active queue; authorized staff or doctors may override to any valid position in that queue with reason and audit (see §25.7 and Business Rules V1.1 §27A).

### 11.3 Queue audit history --- FINALIZED

For each manual adjustment, record: - Previous position/status. - New
position/status. - User who made the change. - Date and time. - Reason,
where required by the action.

Original appointment and serial history must remain traceable.

### 11.4 Emergency and priority permissions --- FINALIZED

-   AMSDP Super Admin defines available permission options.
-   Each facility decides which staff roles can assign or remove
    priority status.
-   Priority assignment and removal are logged.
-   The system does not independently triage patients or decide clinical
    urgency.

## 12. One-Page Daily Appointment Board

### 12.1 Purpose --- APPROVED PRODUCT DIRECTION

The daily appointment board should be the main working screen for
receptionists and assistants. Staff should be able to perform most daily
appointment tasks without navigating through multiple modules.

### 12.2 Suggested screen content

A single-page view containing: - Selected date. - Facility
branch/location, if applicable. - Doctor selector. - Search patient. -
Add appointment / add walk-in action. - Current appointment and queue
list. - Patient name and mobile number. - Slot time or serial number. -
Appointment status. - Check-in and attendance controls. - Queue
position. - Quick reschedule/cancel actions, subject to permission.

### 12.3 One-finger drag-and-drop queue control --- OPTIONAL UX ENHANCEMENT (NOT A RELEASE GATE)

On touch devices, authorized staff can: 1. Press and hold a patient's
appointment card. 2. Drag it up or down. 3. Drop it at the desired queue
position. 4. The system updates the queue/serial order. 5. The change is
saved and added to the audit history.

Design requirements: - Large, touch-friendly appointment cards. -
Visible drag handle so staff can distinguish dragging from opening a
record. - Clear indication of the intended drop position. - Confirmation
or undo for consequential changes, as appropriate. - Permission checks
before saving. - Record who moved the patient and when. - Preserve the
original booking and queue history.

**Important behavior distinction:** dragging a patient up or down the
list changes queue order/serial position. It must not silently change
the appointment date or time slot. If staff need to change the actual
time slot, the interface should provide a clear target slot and show the
new time before saving.

### 12.4 Desktop and mobile behavior --- APPROVED UX REQUIREMENTS

-   Desktop: mouse drag-and-drop and keyboard-accessible controls.
-   Mobile/tablet: touch-and-hold drag-and-drop.
-   Alternative move-up/move-down buttons for users who cannot or do not
    want to drag.
-   Responsive layout for narrow screens.

## 13. Staff Roles and Permissions

### 13.1 Permission-controlled actions --- APPROVED

Permissions should be defined for: - View schedules. - Create
appointments. - Edit appointments. - Cancel appointments. - Register
walk-ins. - Check patients in. - Change queue position. - Assign/remove
priority. - Manage doctor schedules. - Configure facility appointment
policies. - Manage staff access.

### 13.2 Central policy model --- FINALIZED

-   Super Admin defines available permission options and limits.
-   Facility subscriber assigns permissions to roles/users.
-   Subscriber may delegate selected configuration permissions.
-   No user may exceed the permissions granted by the platform and
    facility.

### 13.3 Assistant assignment --- APPROVED

- Support assigning assistants to doctors within an organization.
- An assistant may be scoped to one or more doctors according to
  platform policy and organization authorization.
- Assistant access remains limited to assigned doctor and permitted
  branch/facility operations.
- This is an appointment-operations assignment, not HR or workforce
  management.

This assignment model should be kept lightweight and should not become a
full HR or workforce-management module.

## 14. Appointment Communication

### 14.1 Core approach --- FINALIZED

Patients do not need an AMSDP account, password, portal or mandatory app.
Staff-mediated booking remains the normal workflow. For PQT, a patient
may optionally open an appointment-specific unguessable tracking URL or
QR code without creating an account. One-way operational WhatsApp/SMS
notifications are permitted under §25; this is not patient-provider
messaging.

### 14.2 Communication features --- APPROVED P0 SCOPE; PROVIDER INTEGRATION NOT YET IMPLEMENTED

Both WhatsApp and SMS are supported as independently configurable
organization-level channels. N1 appointment confirmation is triggered
after successful booking. N2 pre-visit reminder defaults to 10 minutes
before expected visit; organization configuration supports approved
5- or 10-minute options. Queue changes must be considered; cooldown and
deduplication apply. Pending reminders are cancelled on cancellation,
reschedule, consultation start or check-in. Booking must remain usable
when messaging is unavailable or unconfigured. Delivery is reported only
when the provider confirms it. Manual link sharing is the fallback.
Provider accounts, sender IDs, template approvals, credentials and
message costs are not assumed to exist. See §25.

## 15. External Advance-Payment Confirmation

### 15.1 Out-of-platform payment --- FINALIZED

Any advance payment is arranged directly between the patient and the
facility outside AMSDP.

### 15.2 Minimal appointment handling --- FINALIZED

If the facility requires advance payment before confirming an
appointment, AMSDP may hold the appointment in an awaiting-confirmation
state. Authorized staff confirms the appointment after checking the
external arrangement.

AMSDP does not store payment amount, payment recipient number, QR code,
wallet or bank account, transaction ID, invoice, payment ledger or
settlement information.

No payment dashboard or payment gateway is included.

## 16. Basic Operational Reports

### 16.1 Proposed reports

Keep reporting limited to appointment operations: - Appointments by
day. - Appointments by doctor. - Appointments by branch/location, if
applicable. - Booked, completed, cancelled and no-show counts. - Walk-in
counts. - Queue activity. - Appointment source counts. - Schedule
utilization, where meaningful for the selected appointment model.

No revenue, billing, payment settlement or clinical-performance
analytics.

## 17. Security, Privacy and Audit

### 17.1 Tenant isolation --- FINALIZED

Every staff data request must be scoped to the authenticated organization
and the user's permitted branch/context. Branches are not tenants.
Patient records are organization-scoped and may be accessed across
branches by appropriately authorized staff; appointments remain
branch-scoped. Public DQDS/PQT endpoints are unauthenticated exceptions
with narrowly scoped, validated identifiers/capability tokens and
strictly minimized responses. No cross-organization data access is
permitted.

### 17.2 Role-based access --- APPROVED

Users can access only the functions and records required for their
assigned appointment role.

### 17.3 Audit history --- FINALIZED DIRECTION

Record important actions, including: - Appointment creation and
changes. - Cancellation and rescheduling. - Queue and serial
adjustments. - Priority assignment/removal. - Patient record changes. -
Permission and configuration changes. - Staff access changes.

Audit records should identify the user, action, timestamp and relevant
before/after values where appropriate.

### 17.4 Data minimization --- FINALIZED DIRECTION

Collect and store only the information needed for appointment
operations. Avoid collecting clinical, financial or identity information
that the appointment workflow does not require.

## 18. Bangladesh-Focused Usability and Localization

### 18.1 Language --- APPROVED

-   Bangla interface.
-   English interface.
-   Bangla and English patient-name input.
-   Correct Unicode handling.

### 18.2 Device and connectivity --- APPROVED

-   Mobile-first staff experience.
-   Tablet and desktop support.
-   Fast loading on ordinary mobile connections.
-   Lightweight pages and assets.
-   Clear network and save-state feedback.
-   Avoid requiring high-end devices or constant heavy background
    activity.

### 18.3 Local operating practices --- FINALIZED DIRECTION

The system should accommodate phone-based appointment requests,
in-person registration, assistant-managed booking, receptionist-managed
booking, walk-in patients, serial-based practices, time-slot practices,
hybrid appointment practices and external advance-payment arrangements
without integrating payment processing.

## 19. Subscription and Tenant Lifecycle

### 19.1 Subscription model --- FINALIZED

-   A hospital or clinic subscribes for its own organizational
    workspace.
-   An independent personal chamber/practice can subscribe as its own
    facility.
-   A doctor does not need a separate subscription to be listed in a
    subscribed hospital.
-   Each subscriber's data remains isolated.

### 19.2 Subscription controls --- APPROVED PLATFORM CAPABILITY; PLAN DETAILS CONFIGURABLE

Super Admin may configure: - Subscription plans. - User limits. -
Doctor-entry limits. - Branch/location limits, if applicable. - Feature
availability. - Subscription start and expiry. - Suspension and
reactivation.

### 19.3 Expiration behavior --- APPROVED HIGH-LEVEL POLICY; OPERATIONAL DETAILS PENDING

After subscription expiry, apply a grace period as configured by platform
policy, then restrict the tenant to read-only access. Retain tenant data
rather than deleting it automatically. Exact grace-period duration,
export workflow, reactivation workflow and retention schedule remain
platform-policy decisions and are not specified here.

## 20. Technical and Non-Functional Requirements

### 20.1 Core requirements --- APPROVED NON-FUNCTIONAL REQUIREMENTS

-   Secure authentication for facility users.
-   Role-based authorization.
-   Strict tenant isolation.
-   Reliable appointment writes and updates.
-   Protection against double booking.
-   Audit logging.
-   Responsive web application.
-   Bangla Unicode support.
-   Low-bandwidth performance.
-   Backups and recovery.
-   Clear error handling.
-   Maintainable configuration and policy engine.

### 20.2 Architecture guidance --- APPROVED ARCHITECTURAL PRINCIPLE

Use a centralized AMSDP application and appointment engine with strict
logical tenant separation. Separate physical deployments for every
facility are not assumed to be necessary; the essential requirement is
that no subscriber can access another subscriber's data.

Keep the architecture modular so optional features can be added later
without turning the core application into a full HMS.

## 21. Explicitly Excluded from V2.1 Core

1.  Patient portal or patient app.
2.  Patient self-service registration/login.
3.  Public doctor schedule or doctor marketplace.
4.  Online appointment booking by patients.
5.  Payment gateway, bKash/Nagad integration or QR payment management.
6.  Financial transaction records or payment reconciliation.
7.  Billing, invoicing, payroll or accounting.
8.  Prescriptions, diagnoses, clinical notes or EMR.
9.  Vitals and clinical intake.
10. Insurance and claims.
11. Doctor HR, employment, attendance or credential management.
12. Pharmacy, laboratory, inventory or hospital operations.
13. Cross-organization patient or doctor data sharing.
14. Central doctor identity matching.
15. Patient messaging portal or telemedicine.

## 22. Decisions Still Pending / Not Yet Authorized

The following items are not fully specified or are not authorized as
MVP requirements. Their presence here does not authorize implementation.

1. Appointment slip / printable serial-token requirements and format.
2. Exact subscription grace-period duration, export workflow,
   reactivation workflow and retention schedule.
3. Additional patient-record correction and merge workflows beyond
   warning/select-existing/no-auto-merge.
4. Detailed policy for exceptional queue recovery and missed turns;
   Missed-Turn Recovery is approved P0/MVP (§25.7).
5. Provider selection, provider account creation, sender IDs, template
   approvals, credentials, paid plans and message-cost commitments.
6. Production/cloud deployment and hosting choices beyond the separately
   approved planning baseline; no deployment is authorized by this
   feature list.
7. Any expansion into patient accounts, self-booking, payment, clinical
   records or two-way messaging; each requires separate product approval.

Resolved decisions are not pending: cancellation requires a reason;
no-show is staff-confirmed after a configurable grace period; late
arrival is an indicator rather than automatic cancellation; overbooking
is configurable and disabled by default; reserved walk-in capacity
defaults to zero; transfers are within the same organization only;
branches are not tenants; the canonical lifecycle is in §8.3; and
WhatsApp plus SMS operational notifications are approved P0 scope.

## 23. Release Priorities and Phase Boundaries

Release priority describes approved product scope, not proof of
implementation. Implementation status is separately recorded in §26.

### P0 / MVP --- Essential appointment operations and PQV

The P0 scope includes the essential appointment operations listed below,
plus the approved PQV and two-stage notification capabilities in §25.
Provider-dependent message delivery remains conditional on provider
availability and configuration.

### Phase 1 --- Essential appointment operations

-   Subscriber and facility workspace.
-   User login and permissions.
-   Lightweight doctor entries.
-   Patient registration and search.
-   Appointment creation.
-   Time-slot, serial and hybrid models.
-   Doctor schedule configuration.
-   Daily appointment board.
-   Check-in and attendance.
-   Queue and serial management.
-   Walk-in registration and placement.
-   Manual queue adjustment with audit history.
-   Strict tenant isolation.

### Phase 2 --- Operational refinement

-   Production-grade rate limiting and operational hardening where
    needed beyond the current development implementation.
-   Advanced queue policies.
-   Priority permission configuration.
-   Drag-and-drop queue management.
-   Additional reports.
-   Multi-branch support, if approved.
-   Improved appointment change workflows.
-   Printable appointment/serial slips, if approved.

### Phase 3 --- Optional extensions

Only after the core system is adopted and validated, and only with
separate approval:
- Additional external provider integrations and channels beyond
  WhatsApp/SMS.
- Advanced multi-display DQDS management.
- Richer notification event matrix beyond approved N1/N2.
- External system integrations.
- Additional operational reports.
- Other appointment-related extensions approved by subscribers and AMSDP.
- Missed-Turn Recovery, as approved under Business Rules V1.1 §27A
  and product approval; it is not part of the MVP.

> **Note:** SMS and WhatsApp are **not** Phase 3-optional per PQV Decision
> `AMSDP-PRODUCT-DECISION-PQV-2026-11-08` — they are required,
> organization-configurable channels (delivery still depends on provider
> availability). See §25.

## 24. Product Definition Summary

AMSDP V2.1 is a facility-centric, multi-tenant SaaS platform for
lightweight appointment management in Bangladesh.

Its primary subscribers are hospitals, clinics and independent medical
practices. Facility staff manage patient registration, doctor schedules,
appointment bookings, walk-ins, serials and queues. Doctors may be added
as lightweight facility-level appointment entries without creating AMSDP
accounts.

Patients do not need to use AMSDP. Payments remain outside the platform.
Each subscribing organization operates an independent data environment,
with no cross-organization patient, doctor or appointment data sharing.

The product should remain focused, fast, mobile-friendly, configurable
and easy for receptionists and assistants to use throughout a busy
working day.

## 25. PQV Decision Addendum (2026-11-08) — Incorporated into V2.1

This addendum records features approved by product decision
`AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
(`docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`).
It is authoritative for the items below; the rest of this document remains
a draft to be reconciled by the product owner.

### 25.1 MVP/P0 (no external provider dependency)

- **Digital Doctor Queue Display (DQDS)** — public, read-only waiting-room
  display; token-based visibility only; no patient PII; org/branch-scoped
  feeds.
- **Personal Queue Tracking (PQT)** — appointment-specific private tracking
  page via cryptographically unguessable tracking token (hash-at-rest) and
  printed QR code; shows only the patient's own appointment: token,
  doctor/branch, currently-serving token, patients ahead, estimated wait
  time (labelled estimate), status.
- Secure tracking links and printed QR codes.
- Tracking-token expiry and revocation (on consultation start,
  cancellation, reschedule); revoked tokens never reactivated.
- No-cache responses for private tracking pages.
- Rate limiting for public tracking endpoints (plus login and patient
  creation).
- Live queue position / patients-ahead and return-before-turn guidance.
- Privacy and tenant-isolation requirements for all public/patient
  surfaces.

### 25.2 Capabilities requiring external provider accounts or paid services

- **WhatsApp delivery** — requires a platform-supported WhatsApp Business
  Provider/API account; template approval; provider costs where applicable.
- **SMS delivery** — requires a platform-supported SMS provider (sender ID,
  credits/costs where applicable).
- Consent/opt-in and delivery-tracking are provider-dependent; AMSDP
  records operational request/delivery outcomes but never silently claims
  delivery.

### 25.3 Organization-admin configuration (both channels)

Organization admin enables/disables WhatsApp and SMS, and configures
provider settings (subject to platform-supported providers); per-channel
**enabled / configured / operational** indication; secrets stored securely
on the backend and never exposed to the frontend; configuration is
organization-scoped with strict tenant isolation. Platform Super Admin
governance remains central (provider registry, plan limits, defaults).

### 25.4 Later-phase enhancements

Advanced multi-display DQDS management; richer notification event matrix;
additional channels (e.g., email) if ever approved.

### 25.5 Preserved exclusions

PQV does **not** change the following exclusions: patient accounts,
patient self-service registration/login/open booking, mandatory patient
mobile application, patient messaging portal, telemedicine, payment
gateways, EMR/EHR/clinical records. PQT uses a capability token — it is
**not** a patient portal or account.

### 25.6 Two-Stage Patient Notifications (2026-11-08 added)

- **Notification 1 — Appointment Confirmation:** immediately after a
  successful booking; content includes confirmation, date/visiting time,
  doctor and facility/branch, queue token or reference, PQT tracking
  link, and relevant instructions.
- **Notification 2 — Pre-Visit Reminder ("Queue Turn Protection"):**
  configurable lead time before expected visiting time; default **10
  minutes**; practical options **5 and 10 minutes**; tells the patient the
  turn is approaching, encourages return, includes the tracking link, and
  states estimates can change. Scheduler must consider queue changes and
  avoid duplicate/excessive reminders.
- **Delivery honesty:** never claim delivery unless the provider confirms;
  undelivered/unread messages never trigger automatic repositioning or
  no-show.
- **Classification:** **APPROVED P0 product scope** (product-owner, 2026-11-08);
  **provider-dependent** for actual delivery; **not implemented**. Approved behaviour:
  queue-change-aware scheduling, cooldown/deduplication, reminder cancellation on
  cancel/reschedule/consultation-started, no return reminder after check-in, no delivery
  claim unless provider confirms, booking functional without messaging.

### 25.7 Missed-Turn Recovery & Queue Repositioning (approved 2026-11-09)

- **Classification: APPROVED P0 / MVP product scope** (product-owner,
  2026-11-09). The capability is a required MVP workflow.
- An authorized staff member or authorized doctor must explicitly
  confirm that the patient was unavailable when called. No automatic
  missed-turn detection is permitted.
- **Default:** defer the patient to the end of the same applicable active
  queue from which the patient was called.
- **Authorized override:** staff or doctor with the required permissions
  may move the patient to any valid position in that same queue. This
  supports human-directed emergency/priority adjustments; AMSDP does not
  clinically triage or determine urgency. An override requires a reason.
- Preserve the original appointment, appointment date/time, token/serial
  identity and complete queue history. Do not cancel, recreate or
  reschedule the appointment as part of queue recovery.
- Audit the missed-turn confirmation and queue movement: previous/new
  position and status, actor, timestamp, action type (default or
  override), and reason.
- Do not automatically set `NO_SHOW`; existing grace-period and
  staff-confirmed no-show rules remain unchanged.
- Do not infer missed turns from message delivery/read status, tracking
  page activity, elapsed time or lack of response.
- Do not change doctor, branch, room, appointment date or appointment
  time through this action. Movement is limited to valid positions in
  the same applicable queue.
- Messaging failure/unavailability must not block recovery.
- Remote waiting remains optional; facility/clinical instructions to
  remain present take precedence.
- **Implementation state:** approved requirement; implementation and
  acceptance evidence must be tracked separately. Approval does not
  imply that the feature is already implemented.

## 25.8 BanglaNameSense — Bangla Patient Name Assistance

### Feature ID: AMSDP-FEATURE-BANGLANAMESENSE-MVP-2026-11-10
**Priority:** P0 — MVP
**Status:** Approved for MVP inclusion; implementation pending verification
**Category:** Patient Registration / Usability / Bangladesh Localization

### 25.8.1 Purpose

BanglaNameSense is a local, Bangla-first patient-name suggestion and autocomplete capability intended to make patient registration faster, easier and more accessible for Bangla-speaking users.

It is also a Bangladesh-focused product differentiator for AMSDP.

The feature assists staff when entering patient names. It does not replace manual name entry or become an authoritative source of patient identity.

### 25.8.2 Initial MVP Scope

The initial integration is limited to the existing patient registration name-entry field.

The feature shall:

- Provide Bangla name suggestions as the user types.

- Display the Bangla name (bn) as the primary suggestion.

- Support Bangla prefix matching.

- Support multi-word name matching.

- Support optional English alias (en) matching.

- Rank suggestions deterministically.

- Suppress duplicate suggestions in the displayed results.

- Allow keyboard, mouse and touch interaction.

- Support Bangla and English input where applicable.

- Remain responsive and usable on mobile and desktop.

- Allow users to select a suggestion or enter a name manually.

- Never require a suggested name to be selected.

### 25.8.3 Dataset

Initial source:

bangla_name_sense.json

Initial dataset structure:

- Root object contains total_count and names.
- Each name record contains:

    * en: English name or alias.

    * bn: Bangla name.

    * gender: dataset metadata.

Initial dataset contains 718 records, including 701 distinct Bangla-name strings.

Dataset rules:

1. Preserve the original source dataset.

2. Validate the dataset structure and required fields before integration.

3. Deduplicate suggestions at runtime or display time without silently modifying the original source.

4. Use bn as the primary display value.

5. Use en as an optional search alias.

6. Do not use gender to filter, rank, display or infer patient information.

7. Do not treat the dataset as comprehensive or authoritative.

8. Preserve dataset source, version and update information in project documentation.

9. Confirm dataset provenance and redistribution rights before public redistribution.

### 25.8.4 Technical and Architectural Rules

- Implement as a local frontend capability using the existing Next.js 14 Pages Router and JavaScript stack.
- Use a reusable matching utility and reusable React autocomplete component.
- Keep suggestions local; do not make backend or external AI requests for each keystroke.
- Do not introduce a new backend service, database table or migration for this feature.
- Do not introduce a patient account, portal or additional registration workflow.
- Do not automatically create or modify patient records from suggestions.
- Do not search or expose private patient records through this feature.
- Preserve existing patient registration APIs, validation, authorization, duplicate-patient warning and persistence behavior.
- Manual entry must remain available for names absent from the dataset.

### 25.8.5 Acceptance Criteria

The feature is acceptable when:

- The dataset loads and passes structural validation.
- Bangla prefix matching works correctly.
- Multi-word matching works correctly.
- English alias matching works where applicable.
- Duplicate suggestions are not displayed repeatedly.
- Empty and unmatched searches behave gracefully.
- Users can navigate suggestions using the keyboard.
- Users can select suggestions using pointer or touch.
- Users can enter names not present in the dataset.
- Selecting a suggestion populates the existing patient name field correctly.
- Existing patient registration, validation, duplicate-warning and persistence workflows remain functional.
- Relevant automated tests and regression tests pass.

### 25.8.6 Future Extension

After successful MVP acceptance, the dataset and reusable component may be considered for other appropriate name-entry workflows, such as doctor or staff registration.

Such extensions must not be assumed to be included in the initial MVP implementation. They require separate prioritization and approval.

### 25.8.7 Scope Exclusions

The initial feature does not include:

- Automatic patient identity verification.
- Gender-based filtering or inference.

### AI-generated name suggestions.

External API calls or third-party autocomplete services.

Automatic transliteration that silently changes the user's entered name.

Automatic patient record creation.

Patient-record search or matching against private records.

A separate name-management backend or administrative module.

Version History / Change Record — V2.23

Version: V2.23
Date: 2026-11-10
Change: Added BanglaNameSense as a P0 core MVP feature.

Summary:

- Introduced Bangla-first patient-name autocomplete and suggestion assistance.

- Added the initial 718-record BanglaNameSense dataset as the starting source.

- Defined local frontend implementation, matching behavior, accessibility and manual-entry requirements.

- Limited initial integration to patient registration.

- Added dataset integrity, privacy, licensing and acceptance requirements.

**Implementation status:** Approved for MVP inclusion; implementation and acceptance verification pending.

**Governance note:** This addition records the approved BanglaNameSense feature. It does not mean the entire Master Feature List V2.23, or any other previously unapproved feature, is approved as a whole.

## 25.9 Approval record — Missed-Turn Recovery (9 November 2026)

The product owner formally approved the limited Missed-Turn Recovery
workflow for MVP. This supersedes the V2.1 draft's proposed/not-approved
classification. The governing detailed rule is Business Rules V1.1 §27A;
the MVP scope is reflected in MVP Scope V1.1 §5.8 and its amendment
record. V1.0 business rules and scope documents remain preserved as
historical baselines.


------------------------------------------------------------------------

# 26. Approval, Implementation and Evidence Register

## 26.1 How to read this document

This document is a consolidated working draft. It is **not an approval
of every feature in the catalogue** and does not authorize implementation,
deployment, provider registration, paid expenditure, commit, push or
merge.

Every feature must be read on two separate axes:

**Product approval**
- **APPROVED:** Product owner has approved the requirement or policy.
- **PROPOSED:** A candidate capability or design direction; not a
  requirement until explicitly approved.
- **DEFERRED:** Intentionally placed in a later phase; not an MVP
  requirement.
- **EXCLUDED:** Outside current product scope unless separately approved.
- **PENDING DECISION:** Requires a further product/business decision.

**Implementation state**
- **COMPLETED (reported):** Project records report implementation;
  this is not a substitute for a fresh acceptance run.
- **PARTIAL / HARDENING REQUIRED:** Some implementation exists, with
  known gaps or acceptance conditions.
- **PENDING:** No completion evidence recorded in the project context.
- **BLOCKED / DEPENDENCY:** Requires a provider, infrastructure,
  credential, policy or other dependency.
- **NOT AUTHORIZED:** Implementation or deployment has not been
  authorized. This is distinct from whether the product capability is
  approved.

Do not infer implementation from approval, or approval from code that
happens to exist.

## 26.2 Canonical personas and roles

The four primary product personas are:
1. Patient (no AMSDP account required).
2. Receptionist / appointment operator.
3. Doctor.
4. Organization administrator.

The six canonical staff/platform roles are:
- `super_admin`
- `org_admin`
- `branch_admin`
- `receptionist`
- `doctor`
- `assistant`

Role names are canonical. Permission assignment is governed by
platform-defined permission boundaries and organization-level grants.
A doctor's login is optional. Assistants are assigned within an
organization and may be limited to one or more doctors according to
policy.

## 26.3 Organization, branch and patient-data boundaries

- The organization is the tenant/security boundary.
- Branches are organizational locations, not separate tenants.
- No cross-organization patient, appointment, doctor or staff data access.
- Patient records are organization-scoped and may be shared across
  branches within the organization, subject to authorization.
- Each appointment retains its branch/location.
- Doctor records are facility/organization-local; there is no central
  doctor identity or cross-organization matching.
- The same doctor mobile number may exist in different organizations.
- Patient name and mobile number are mandatory. A mobile number may be
  shared by multiple patient records within one organization.
- Duplicate detection warns; it does not automatically merge.
- A single-chamber clinic must not be forced to configure department,
  floor or room hierarchy.

## 26.4 Appointment, capacity and queue rules

- Supported appointment models: time-slot, serial and hybrid.
- Walk-in is a booking source, not a fourth appointment model.
- Walk-in placement policies: end of queue, first-come-first-served,
  reserved capacity, and staff-controlled placement.
- Reserved walk-in capacity defaults to zero.
- Overbooking is configurable but disabled by default; capacity
  validation must be atomic.
- Queue order/position is distinct from appointment date/time.
- Reordering the queue must not silently change the appointment time.
- Manual queue changes preserve original history and record old/new
  position or status, actor, timestamp and reason where required.
- Transfers are permitted only within the same organization.
- Reschedule preserves the original appointment and creates a linked
  replacement appointment.
- Cancellation reason is required.
- No-show is staff-confirmed after a configurable grace period.
- Late arrival is an indicator; it does not automatically cancel or
  reposition the appointment.
- Emergency/priority handling is staff-authorized and audited; AMSDP
  does not clinically triage patients.
- Doctors and appropriately authorized administrators may start and
  complete consultations. Receptionists may not.
- Missed-Turn Recovery is approved P0/MVP; see §25.7.

## 26.5 Patient Queue Visibility (PQV) — approved P0

PQV consists of two separate surfaces:

**Digital Doctor Queue Display (DQDS)**
- Public, read-only waiting-room display.
- Token-only queue visibility; no patient name, mobile, DOB, age or
  other patient-identifying information.
- Organization/branch-scoped data.
- Public display is not a public doctor schedule or availability
  calendar.
- Public response must expose only the minimum approved queue fields.

**Personal Queue Tracking (PQT)**
- Private, appointment-specific, account-free tracking through an
  unguessable capability URL and QR code.
- No patient account, password, portal, self-booking or mandatory app.
- Shows the patient's own token/appointment status, doctor/branch,
  currently serving token, patients ahead and estimated wait.
- Estimates are not guarantees; queue conditions may change.
- Return-before-turn guidance must include an appropriate buffer and
  clear instructions.
- Remote waiting is optional. Patients who need urgent care or have
  been instructed to remain at the facility must not be encouraged to
  leave.
- Token is generated with cryptographically secure randomness, stored
  as a keyed hash, and revoked on consultation start, cancellation or
  reschedule. Revoked tokens are never reactivated.
- Private PQT and QR responses require no-store/no-cache handling.
- Public endpoints require rate limiting and must not expose PII.
- Unknown, invalid and revoked tracking tokens should not reveal which
  condition occurred.

## 26.6 Two-stage operational notifications — approved P0 scope

**N1 — Appointment confirmation**
- Triggered immediately after successful booking.
- Includes appointment date/visiting time, doctor, facility/branch,
  queue token/reference, PQT link and relevant instructions.

**N2 — Pre-visit reminder / queue-turn protection**
- Default lead time: 10 minutes before expected visit.
- Organization configuration supports approved 5- or 10-minute
  settings.
- Queue-change-aware scheduling, cooldown and deduplication apply.
- Pending reminder is cancelled on appointment cancellation,
  reschedule, consultation start or check-in.
- Do not send a redundant return reminder after check-in.

**Channel and delivery rules**
- WhatsApp and SMS are both supported and independently configurable
  at organization level.
- Booking remains functional if messaging is disabled, unconfigured or
  unavailable.
- Delivery is claimed only after provider confirmation.
- Manual sharing of tracking links is the fallback.
- Provider accounts, sender IDs, template approvals, credentials,
  costs and production provider selection are not assumed or approved
  by this feature list.
- These are one-way operational notifications, not patient-provider
  messaging or a portal.

## 26.7 Current milestone / implementation status (as reported)

This register records the latest project status available when this
draft was prepared (9 November 2026). It is not a fresh code audit.

| Area | Product approval | Reported implementation state | Notes / acceptance caveat |
|---|---|---|---|
| M1–M7 core appointment platform | Approved scope | Reported complete; M7 conditional GO | Prior project reports describe backup/restore, localization, branch switching, audit and regression checks. Do not infer every open non-blocking item is closed. |
| Patient age / optional DOB (M7-B8) | Approved | Reported complete | Migration `3c8e5d0a9b2f_add_patient_age.py`; DOB-derived age authoritative when DOB exists; no DOB inferred. |
| M8 cloud deployment | Architecture assessment only | Readiness/architecture assessment complete; execution not authorized | Vercel + Supabase + Render architecture considered; no cloud resources or deployment are claimed. |
| M9-A PQV readiness | Approved planning baseline | Assessment/gate 1 reported complete | Planning only; not implementation authorization. |
| M9-B PQT | Approved P0 | Development implementation reported present; acceptance hardening remains | Token issue/QR/tracking/revocation and 14 PQT tests reported. Earlier acceptance review identified missing no-store headers and raw token in access-log paths; later hardening report must be checked before calling those closed. |
| M9-C DQDS | Approved P0 | Pending implementation / not authorized in current record | Readiness plan exists; no implementation approval is implied. |
| M9-D notifications | Approved P0 product scope | Pending implementation; provider-dependent | No provider account, credentials, sender ID, paid service or delivery capability assumed. |
| Production-grade rate limiting | Security requirement | Partial / hardening required | Current M9-B in-process limiter is not a durable multi-process production limiter; DB-backed/token-bucket hardening was deferred to later M9 work. |
| Cloud deployment | Separate approval required | Not authorized | No deployment, migration, seed of cloud DB, or public release. |
| WhatsApp/SMS provider integration | Approved product scope, provider selection pending | Not implemented / dependency blocked | Development/mock adapter may be used only within an authorized implementation task. |

### M9-B known acceptance caveats to verify

The available PQT acceptance review reported:
- Raw tracking tokens appeared in web-server access-log request paths.
  Production logging must redact token path segments and avoid leaking
  tokens in exception/application logs.
- Private PQT response and QR response required explicit
  `Cache-Control: no-store, private, no-cache, must-revalidate` and
  appropriate `Pragma: no-cache`.
- The rate limiter was in-process and resets on restart; this is not a
  durable multi-worker production solution.
- The broad test run reported 91 passing tests but also two test
  collection errors in unrelated scheduling and E2E suites. Do not
  describe the entire repository suite as green.
- A previous queue suite count discrepancy (20 previously reported vs
  14 in the later run) requires explanation; do not silently assume
  tests were intentionally removed.
- These issues must be checked against the latest hardening report
  before PQT is declared fully accepted. Do not fix unrelated test
  collection failures under a PQT-only task.

## 26.8 Milestone mapping and change control

Milestone references below are traceability aids, not blanket
implementation authorization:
- M1–M7: core appointment-management foundation and reported delivery.
- M7-B8: patient age / optional DOB.
- M8: cloud deployment planning and, only after separate approval,
  execution.
- M9-A: PQV implementation-readiness assessment.
- M9-B: PQT implementation.
- M9-C: DQDS implementation.
- M9-D onward: notifications and remaining PQV operational hardening
  according to the approved milestone plan.

Any milestone task must have a unique task ID, a bounded scope,
acceptance criteria and explicit authorization. No future milestone is
authorized by this document alone. No commit, push, merge or deployment
is authorized unless separately approved.

## 26.9 Minimum acceptance criteria by feature family

**Appointment and tenant foundation**
- Every staff API operation enforces organization and branch scope.
- Cross-organization access attempts fail without disclosing records.
- Patient records can be shared across branches within the same
  organization where role permissions allow.
- Appointment branch remains explicit.
- Concurrent booking cannot exceed configured capacity.
- Lifecycle transitions enforce actor permissions and preserve audit
  history.

**Queue management**
- Queue reordering does not alter appointment date/time.
- Before/after queue position and status, actor, timestamp and required
  reason are auditable.
- No-show is staff-confirmed under grace-period policy.
- No notification delivery/read state triggers automatic NO_SHOW or
  queue repositioning.

**DQDS**
- Public read-only endpoint and display are branch/org scoped.
- Unknown organization/branch and mismatched branch relationships are
  handled safely.
- No patient PII appears in API payload, UI, logs or cached content.
- Public feed uses the approved short cache policy and rate limit.
- Display supports empty and active queues and updates without staff
  interaction by the viewer.

**PQT**
- Only the appointment-specific token holder can view that appointment.
- Raw token is never stored; token is high entropy and hash-at-rest.
- Token revokes on consultation start, cancellation and reschedule.
- Revoked tokens never reactivate; invalid/revoked responses are
  indistinguishable.
- Response contains no patient PII.
- Private tracking and QR responses are no-store/no-cache.
- Token values are redacted from access, application and exception logs.
- Queue position is re-evaluated on every request/poll.
- Rate limiting is effective across all production workers/instances.

**N1/N2 notifications**
- Both channels can be independently enabled/configured per
  organization.
- Booking succeeds even when notifications fail or are disabled.
- N1 is queued after successful booking.
- N2 scheduling reacts to queue changes and uses cooldown/deduplication.
- Pending reminders are cancelled on the specified lifecycle events.
- Delivery status is represented honestly and only confirmed by the
  provider.
- Secrets never reach the frontend and are isolated by organization.

## 26.10 Security, privacy and clinical-safety guardrails

- Organization tenant boundary is mandatory; branch is a scope within
  the organization.
- Public DQDS never exposes patient PII.
- PQT is a bearer capability; possession of the unguessable URL grants
  access only to one appointment's minimal tracking data. Treat it as
  sensitive.
- Tracking tokens must not be placed in analytics, referrers, logs or
  third-party resources.
- Private responses must not be stored by browsers or shared caches.
- Notification content must be operational and minimal; do not include
  clinical information.
- Queue estimates are estimates, not promises or guarantees.
- Patients requiring urgent assessment or instructed to stay must not
  be directed to wait remotely.
- AMSDP does not clinically triage or determine urgency.
- No automated no-show or missed-turn repositioning based on message
  delivery, reading or acknowledgement.

## 26.11 Document precedence and source references

This consolidated feature list is subordinate to explicit product-owner
decisions and authoritative approved product/business documents.

Relevant sources:
- `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`
  — authoritative approved PQV decision.
- `docs/product/AMSDP_Product_Positioning_V1.0.md`
  — approved product positioning and impact-measurement framing.
- `docs/product/AMSDP_MVP_SCOPE_V1.1.md` — MVP scope and PQV addendum.
- `docs/architecture/AMSDP_System_Architecture_V1.0.md` — architecture,
  security and integration boundaries.
- `docs/AMSDP_Business_Rules_V1.1.md` — authoritative Business Rules;
  do not silently amend it through this feature list.
- `docs/product/AMSDP_Business_Rules_Revision_Proposal_V1.0_DRAFT.md`
  — separate unapproved proposal; not binding requirements.

If this draft conflicts with an explicit approved decision or
authoritative Business Rules document, the higher-precedence approved
source controls. The Business Rules V1.0 document remains unchanged by
this revision. Any amendment requires separate review and approval.

------------------------------------------------------------------------

# 27. Product Impact Measurement — No Unverified Claims

The product promise is:

**AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.**

The intended outcome is to reduce unnecessary time spent physically
waiting in the facility and improve visibility into patient flow. This
does not mean zero waiting or guaranteed consultation times.

Track separately:
1. Physical waiting-area time.
2. Waiting-area occupancy.
3. PQT tracking adoption.
4. Return-before-turn rate.
5. Missed turns / delayed returns.
6. Appointment-to-consultation time.

Do not claim measured reductions, pilot success, occupancy improvements
or numerical targets until supported by facility pilot data. Physical
waiting-area time and occupancy require suitable measurement or
instrumentation. Appointment-to-consultation time is not the same as
physical waiting-area time.

------------------------------------------------------------------------

# 28. Revision History

| Version | Date | Status | Summary |
|---|---|---|---|
| V2.0 | 4 November 2026 baseline | Historical draft | Initial facility-centric master feature list. |
| V2.1 | 9 November 2026 | Consolidated draft for review; not approved as a whole | Reconciles approved business/product decisions, incorporates PQV/PQT/DQDS and N1/N2 scope, distinguishes approval from implementation, updates release priorities and adds acceptance/security guardrails. |
