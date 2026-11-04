# AMSDP --- Master Feature List V2.0

## Facility-Centric, Lightweight Appointment Management SaaS

**Working baseline:** 4 November 2026\
**Market focus:** Bangladesh\
**Document status:** Draft for review

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
-   Public display of doctors' daily schedules.
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
-   Telemedicine or patient-provider messaging.
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

### 4.11 Lightweight and mobile-friendly --- PROPOSED

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

### 5.1 AMSDP Super Admin Dashboard --- PROPOSED

Platform-level functions only: - Create, activate, suspend and manage
subscriber accounts. - Manage subscription plans, limits and expiry. -
Configure available appointment models and policy options. - Set default
values and configurable limits. - Configure permission templates and
role options. - Configure doctor mobile-number uniqueness policy. - View
tenant-level usage and system health. - Manage platform support and
audit metadata.

Super Admin functions must not create routine cross-tenant access to
patient or appointment content.

### 5.2 Facility Dashboard --- PROPOSED

The primary subscriber workspace: - Facility profile and basic
settings. - Manage branches or locations if enabled. - Create and manage
doctor appointment entries. - Configure doctor schedules. - Manage staff
accounts and role permissions. - Manage patient records. - Manage
appointments and queues. - View daily operational summaries. - Configure
walk-in and queue policies.

### 5.3 Receptionist / Appointment Operator --- PROPOSED

-   Search patient records.
-   Register new patients.
-   Create, reschedule and cancel appointments according to permission.
-   Register walk-ins.
-   Check patients in.
-   Update appointment attendance status.
-   View the relevant doctor schedule.
-   Manage queue position if authorized.

### 5.4 Doctor --- PROPOSED

A doctor account is not mandatory for a facility to use AMSDP.

Where a facility chooses to provide doctor access, the doctor may be
allowed to: - View their own appointment list and queue. - View relevant
schedule information. - See appointment changes. - Update limited
appointment statuses if permitted.

No clinical record, prescription or full doctor-management workspace is
included.

### 5.5 Assistant --- PROPOSED

-   Manage appointments for assigned doctor(s).
-   Register patients and walk-ins.
-   Check patients in.
-   Update queue status and position.
-   Reschedule or cancel appointments when permitted.
-   View only the doctor/facility data assigned to the assistant.

Assistant-to-doctor assignment limits and role permissions should be
configurable within Super Admin policy boundaries.

## 6. Facility and Doctor Setup

### 6.1 Facility setup --- PROPOSED

Minimum facility setup: - Facility name. - Facility type. - Contact
information. - Time zone and operating days. - Default appointment
settings.

Optional configuration: - Branch/location. - Department. - Consultation
room or chamber. - Facility-specific working hours.

Do not require a hospital to reproduce its complete organizational
structure.

### 6.2 Doctor appointment entry --- FINALIZED / PROPOSED DETAILS

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

### 7.2 Patient search --- PROPOSED

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

### 7.4 Duplicate handling --- PROPOSED

-   Warn staff when a likely duplicate patient record exists.
-   Allow authorized staff to select an existing record.
-   Do not automatically merge records based only on matching name or
    mobile number.
-   Any merge capability should require explicit authorization and an
    audit record.

## 8. Appointment Management Engine

### 8.1 Appointment creation --- PROPOSED

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

### 8.3 Appointment status --- PROPOSED

A simple status set: - Booked. - Awaiting external confirmation, if the
facility requires it. - Confirmed. - Checked in / Present. - In queue. -
In consultation (optional operational status). - Completed. -
Cancelled. - No-show. - Rescheduled.

The final list and transition rules require review.

### 8.4 Appointment changes --- PROPOSED

Authorized staff can: - Change appointment date or slot. - Change
serial/queue position. - Move appointment to another permitted doctor or
location. - Cancel or reschedule. - Add an internal reason/note.

Changes must preserve appointment history and record who made the
change.

### 8.5 Double-booking protection --- PROPOSED

Prevent two staff members from booking the same unavailable time slot or
serial capacity at the same time. The system should validate
availability at the moment the booking is saved.

### 8.6 Booking source --- PROPOSED

Record how the appointment was received: - Phone call. - In-person. -
Doctor assistant. - Reception. - Walk-in. - Other facility-approved
source.

This is operational metadata, not a patient-facing channel.

## 9. Scheduling and Availability

### 9.1 Doctor schedule --- PROPOSED

-   Configure working days.
-   Configure start and end times.
-   Configure breaks and unavailable periods.
-   Configure appointment duration for time-slot models.
-   Configure serial capacity for serial-based models.
-   Configure hybrid rules.
-   Block dates or periods when appointments should not be accepted.

### 9.2 Facility-level defaults --- PROPOSED

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

Authorized staff may: - Move a patient up or down. - Change queue
position. - Adjust serial number. - Mark a patient absent. - Mark a
patient temporarily unavailable. - Skip a patient and continue to the
next patient.

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

### 12.1 Purpose --- PROPOSED

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

### 12.3 One-finger drag-and-drop queue control --- PROPOSED

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

### 12.4 Desktop and mobile behavior --- PROPOSED

-   Desktop: mouse drag-and-drop and keyboard-accessible controls.
-   Mobile/tablet: touch-and-hold drag-and-drop.
-   Alternative move-up/move-down buttons for users who cannot or do not
    want to drag.
-   Responsive layout for narrow screens.

## 13. Staff Roles and Permissions

### 13.1 Permission-controlled actions --- PROPOSED

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

### 13.3 Assistant assignment --- PREVIOUSLY AGREED DIRECTION

-   Support assigning assistants to doctors within a facility.
-   Default may be one assigned assistant per doctor per facility.
-   Super Admin may configure whether an assistant can manage one doctor
    or multiple doctors.
-   Assistant access remains limited to assigned doctor/facility
    operations.

This assignment model should be kept lightweight and should not become a
full HR or workforce-management module.

## 14. Appointment Communication

### 14.1 Core approach --- FINALIZED

Patients receive appointment information directly from the hospital,
clinic, receptionist, doctor assistant or other facility staff. AMSDP
does not provide a patient portal or require patient interaction with
the platform.

### 14.2 Communication features --- PENDING

Possible future operational support: - Copyable appointment details for
staff to communicate by phone or message. - Printable appointment slip
or serial token. - Optional staff-triggered SMS reminder integration.

These are not assumed to be part of the first release. They require
separate approval and should not introduce a patient-facing AMSDP
account or portal.

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

Every data request must be scoped to the authenticated subscriber and
the user's permitted facility context.

### 17.2 Role-based access --- PROPOSED

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

### 18.1 Language --- PROPOSED

-   Bangla interface.
-   English interface.
-   Bangla and English patient-name input.
-   Correct Unicode handling.

### 18.2 Device and connectivity --- PROPOSED

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

### 19.2 Subscription controls --- PROPOSED

Super Admin may configure: - Subscription plans. - User limits. -
Doctor-entry limits. - Branch/location limits, if applicable. - Feature
availability. - Subscription start and expiry. - Suspension and
reactivation.

### 19.3 Expiration behavior --- PENDING

The system must define what happens to existing appointments, read-only
access, new booking ability, data export, reactivation and data
retention after termination. No final expiration behavior is assumed in
this draft.

## 20. Technical and Non-Functional Requirements

### 20.1 Core requirements --- PROPOSED

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

### 20.2 Architecture guidance --- PROPOSED

Use a centralized AMSDP application and appointment engine with strict
logical tenant separation. Separate physical deployments for every
facility are not assumed to be necessary; the essential requirement is
that no subscriber can access another subscriber's data.

Keep the architecture modular so optional features can be added later
without turning the core application into a full HMS.

## 21. Explicitly Excluded from V2.0 Core

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

## 22. Decisions Still Pending

1.  Appointment cancellation rules and cancellation reasons.
2.  No-show definition and handling.
3.  Late arrival and grace-period rules.
4.  Whether overbooking is allowed and under what permissions.
5.  Maximum appointment capacity and booking limits.
6.  Whether appointments can be transferred between doctors or
    locations.
7.  Branch and multi-location configuration details.
8.  Whether appointment slips or printable serial tokens are required.
9.  Whether staff-triggered SMS reminders are required.
10. Subscription expiry, suspension, export and retention behavior.
11. Data correction and duplicate patient-record merge permissions.
12. Exact appointment status transitions.

## 23. Release Priorities

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

-   Advanced queue policies.
-   Priority permission configuration.
-   Drag-and-drop queue management.
-   Additional reports.
-   Multi-branch support, if approved.
-   Improved appointment change workflows.
-   Printable appointment/serial slips, if approved.

### Phase 3 --- Optional extensions

Only after the core system is adopted and validated: - Staff-triggered
SMS reminders. - External system integrations. - Additional operational
reports. - Other appointment-related extensions approved by subscribers
and AMSDP.

## 24. Product Definition Summary

AMSDP V2.0 is a facility-centric, multi-tenant SaaS platform for
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
