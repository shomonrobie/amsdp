# AMSDP Business Rules V1.1

**Product:** Appointment Management System for Doctors & Patients
(AMSDP)\
**Market:** Bangladesh\
**Version:** 1.1\
**Baseline:** 4 November 2026; amendment approved 9 November 2026\
**Status:** Approved business-rule baseline for implementation (V1.0 retained; V1.1 amendment adds limited missed-turn recovery)\
**Amendment:** PO-13 / PO-02, 24 November 2026 — §33 scope status: full multi-display DQDS required for Hackathon delivery\
**Authority:** This document consolidates
`AMSDP_Master_Feature_List_V2.0_Draft.md`, subsequent approved product decisions, and the V1.1 amendment dated 9 November 2026 and the product-owner
decisions confirmed during the AMSDP project discussion.

------------------------------------------------------------------------

## 0. Instructions to AI agents and developers

This is the authoritative business-rule baseline for AMSDP
implementation.

1.  Read this document before designing, coding, reviewing or testing an
    AMSDP feature.
2.  Implement finalized rules as written. Do not reinterpret or weaken
    them.
3.  Do not add excluded HMS, EMR, clinical, financial, patient-portal,
    marketplace, telemedicine, pharmacy, laboratory or HR features.
4.  Where this document says **configurable**, implement the stated
    options and their permitted scope. Do not hard-code one facility's
    preference globally.
5.  Where a value is unspecified, use the safe default stated here. If
    no safe default exists, use the restrictive behavior and document
    the technical assumption. Do not block routine implementation with
    questions already answered here.
6.  Enforce tenant, branch, role and record authorization in backend
    services and database access paths. UI hiding is not security.
7.  Preserve historical records. Never silently overwrite appointment,
    queue, token, patient-merge, subscription or audit history.
8.  Use the facility's configured time zone for operational dates and
    times. Store timestamps consistently (UTC recommended) and render
    them locally.
9.  Never expose patient personal information on public queue displays
    by default.
10. Choose the simplest technical implementation that preserves these
    business rules. Record implementation assumptions and decisions.

### Requirement labels

-   **FINALIZED:** Explicitly approved. Must be implemented.
-   **APPROVED DEFAULT:** Product owner accepted the recommendation; use
    as default.
-   **CONFIGURABLE:** Facility/platform may choose among the stated
    options.
-   **PHASED:** Approved in principle but assigned to a later release.
-   **OUT OF SCOPE:** Do not implement unless separately approved.

### Conflict precedence

Apply this order if sources conflict:

1.  Explicit product-owner decisions in this document.
2.  Finalized decisions in the V2.0 master feature list.
3.  Approved defaults and safe rules in this document.
4.  Other proposed/draft descriptions in the master list.
5.  Developer or AI-agent assumptions.

Do not treat a proposed feature as finalized merely because it appears
in an earlier draft.

------------------------------------------------------------------------

# Part I --- Product identity and scope

## 1. Product definition

AMSDP is a lightweight, facility-centric, multi-tenant appointment
management SaaS for hospitals, clinics, diagnostic centres and
independent medical practices in Bangladesh.

It helps authorized facility staff manage:

-   Organizations, branches and appointment locations.
-   Lightweight doctor appointment profiles.
-   Patient registration for appointment purposes.
-   Doctor schedules and appointment capacity.
-   Time-slot, serial-based and hybrid appointments.
-   Walk-in registration and placement.
-   Attendance and appointment status.
-   A unified, manually manageable queue.
-   Token generation and printing.
-   Digital queue displays.
-   Basic operational reports.
-   Facility users, permissions, configuration and audit history.

Patients do not need AMSDP accounts. Patients ordinarily contact
facilities by phone or in person; authorized facility staff operate
AMSDP.

## 2. Product positioning and exclusions

AMSDP is an appointment management system, not a complete HMS, PMS, EMR
or EHR. It must remain lightweight and work alongside a facility's
existing software or independently.

Out of scope for the core product:

-   Patient portal, dashboard, app, login, self-registration or
    self-booking.
-   Public doctor directory, marketplace or public doctor schedules.
-   Payment gateway or payment processing.
-   bKash/Nagad wallet management, QR payment management or transaction
    reconciliation.
-   Payment amounts, recipient details, transaction IDs, financial
    ledgers, invoices, billing, payroll or accounting.
-   Prescriptions, diagnoses, clinical notes, treatment records,
    clinical history, vitals or clinical intake.
-   Insurance and claims.
-   Doctor employment, HR, payroll, attendance or credential management.
-   Pharmacy, inventory, laboratory or diagnostic operations.
-   Telemedicine or patient-provider messaging.
-   Central doctor identity matching.
-   Cross-organization patient, doctor, appointment or schedule sharing.

Do not introduce these features as hidden dependencies of appointment
workflows.

------------------------------------------------------------------------

# Part II --- Tenancy, organizations and branches

## 3. Organization and tenant model

1.  Each subscribing organization is one tenant and owns its own AMSDP
    workspace.
2.  A hospital, clinic or diagnostic-centre organization subscribes for
    its organizational workspace.
3.  An independent doctor's personal chamber/practice may subscribe as
    its own organization.
4.  Doctors do not need individual subscriptions to be listed in a
    subscribed facility.
5.  The organization is the primary tenant-isolation boundary. A branch
    is not a separate tenant by default.
6.  Subscription plans may impose organization-level limits, including
    branch, user or doctor-entry limits.

## 4. Strict tenant isolation --- FINALIZED

1.  Every tenant-owned record must be associated with its
    organization/tenant.
2.  Every authenticated request must be scoped to the user's authorized
    organization and permitted branch/doctor context.
3.  No tenant may access another tenant's patients, appointments,
    doctors, schedules, staff, assistants, queues, tokens, reports or
    configuration.
4.  A doctor entered in two organizations is represented by two separate
    facility-local doctor records.
5.  Do not create a central doctor identity or automatically match
    doctors across organizations.
6.  Do not automatically transfer data when a doctor changes facilities.
7.  Super Admin functions must not create routine cross-tenant access to
    patient or appointment content.
8.  Tenant isolation must be enforced server-side and, where practical,
    reinforced by database constraints/policies.

## 5. Multi-branch organizations --- FINALIZED

One organization may operate multiple physical branches under one
organizational workspace/subscription, subject to plan limits.

Suggested hierarchy:

``` text
Organization / Tenant
├── Branch A
│   ├── Departments (optional)
│   ├── Consultation rooms (optional)
│   ├── Doctors and staff assignments
│   └── Schedules, appointments and queues
└── Branch B
    ├── Departments (optional)
    ├── Consultation rooms (optional)
    ├── Doctors and staff assignments
    └── Schedules, appointments and queues
```

Rules:

-   A single-location chamber must operate without configuring
    departments or rooms.
-   Branches have their own operating details, doctors, schedules,
    rooms, queues and appointment operations.
-   Authorized central organization administrators may manage multiple
    branches.
-   Branch staff are restricted to assigned branches and other
    explicitly granted scopes.
-   Branches remain within the same tenant.
-   Cross-branch transfer follows Section 17.
-   Do not force every organization to reproduce its full organizational
    structure.

## 6. Shared patient records across branches --- FINALIZED

1.  Patient records are shared at organization level, not isolated
    independently per branch.
2.  Authorized users at different branches of the same organization may
    access the shared patient directory according to permissions.
3.  Branch-level permissions may restrict which patient records a user
    can view or operate on.
4.  Each appointment retains its originating/servicing branch
    association.
5.  Patient history identifies the branch associated with each
    appointment.
6.  Shared records do not permit access by another organization.
7.  A patient visiting another branch should not need duplicate
    registration solely because the branch differs, provided the user
    can access the existing record.

------------------------------------------------------------------------

# Part III --- Roles, permissions and records

## 7. Roles

### 7.1 Super Admin

Platform-level functions:

-   Create, activate, suspend and manage subscriber organizations.
-   Manage plans, limits, expiry and feature availability.
-   Define available appointment models, policy options, defaults and
    platform limits.
-   Define available permission options and role templates.
-   Configure doctor mobile-number uniqueness policy.
-   View tenant-level usage and system health.
-   Manage platform support and platform audit metadata.

Super Admin is not a routine appointment operator and must not have
routine cross-tenant patient-content access.

### 7.2 Facility Admin

May manage organization and branch settings, doctors, schedules, staff,
roles, patient records, appointments, queues, tokens, displays, reports
and facility policies, subject to subscription and permission limits.

### 7.3 Receptionist / Appointment Operator

May be permitted to search/register patients, create/reschedule/cancel
appointments, register walk-ins, check patients in, update attendance,
view assigned schedules, manage queue positions and generate/print
tokens.

### 7.4 Doctor

Doctor login is optional. Where enabled, a doctor may view their own
appointments/queue and schedule, see appointment changes and update
limited appointment statuses if permitted. No clinical workspace is
included.

### 7.5 Assistant

An assistant may manage appointments, patient registration, walk-ins,
check-in and queue operations for assigned doctor(s), subject to
permissions. Assignment is facility-local. Platform policy may allow one
or multiple doctors per assistant; the default may be one assigned
assistant per doctor, but this is not a universal hard-coded
restriction.

## 8. Permission model

1.  Super Admin defines available permission options and limits.
2.  Facility Admin assigns available permissions to roles/users and may
    delegate selected configuration rights.
3.  Users may perform only actions allowed by platform policy and their
    facility assignment.
4.  Enforce permissions server-side on every protected operation.
5.  Enforce branch and doctor assignment scopes in addition to role
    permissions.
6.  Audit important permission, role and assignment changes.
7.  Facility configuration cannot override tenant isolation or mandatory
    security.

Permissions should cover: viewing schedules/appointments; creating,
editing, cancelling and rescheduling appointments; patient
registration/editing; walk-ins; check-in/attendance; queue movement;
priority assignment/removal; schedule management; policy configuration;
staff management; token generation/printing; display configuration; and
reports.

## 9. Doctor appointment profiles

1.  A facility may create a doctor entry without the doctor's
    participation or account.
2.  Mandatory: doctor name and mobile number.
3.  Generate a facility-local unique Doctor ID.
4.  Optional: specialty, department, branch/location, room, schedule,
    appointment model and internal operational note.
5.  These are appointment profiles, not employment/credential profiles.
6.  Default doctor mobile-number uniqueness is within an organization.
7.  Super Admin may allow duplicate doctor mobile numbers within an
    organization.
8.  The same mobile number may exist in different organizations.

## 10. Patient records

1.  Patients do not need AMSDP accounts.
2.  Authorized staff create and manage patient records.
3.  Mandatory: patient name and mobile number.
4.  Optional fields must be limited to appointment-operation needs.
5.  Multiple patient records may share one mobile number within an
    organization, supporting family/shared-phone use.
6.  Search may return multiple records; staff must select the correct
    person before booking.
7.  Each patient record has its own appointment history.
8.  Records are shared across branches of the same organization subject
    to permissions.
9.  Records are never shared across organizations.
10. A shared phone number is not proof that two records represent the
    same person.

## 11. Duplicate patient handling

1.  Warn staff about likely duplicates where a reliable matching rule
    exists.
2.  Matching name or mobile number alone must never trigger automatic
    merging.
3.  Initial release: duplicate warnings and authorized record
    correction.
4.  Actual merge workflow is a later-phase capability.
5.  When enabled, an authorized user requests a merge and an authorized
    Facility Admin/approver approves it.
6.  Merging is restricted to the same organization.
7.  Preserve appointment history and references to source and retained
    records.
8.  Audit requester, approver, timestamp, reason and before/after
    references.
9.  Do not erase historical appointment or audit references during a
    merge.

------------------------------------------------------------------------

# Part IV --- Facility configuration and scheduling

## 12. Facility setup

Minimum: organization/facility name, facility type, contact information,
time zone, operating days and default appointment settings.

Optional: branches/locations, departments, consultation rooms and
facility-specific working hours.

A single-location chamber must not be forced to configure a multi-level
structure.

## 13. Configuration governance

1.  Super Admin defines available options, defaults, limits and
    permission boundaries.
2.  The organization configures its policies within those boundaries.
3.  Facility Admin may delegate configuration rights.
4.  Only permitted users may change settings.
5.  Security and tenant-isolation rules cannot be overridden.
6.  Important configuration changes are audit logged.
7.  New settings apply prospectively. Do not silently rewrite historical
    appointments or tokens.

## 14. Appointment models --- FINALIZED

AMSDP supports exactly three core models:

1.  **Time-slot:** appointment assigned to a defined time slot.
2.  **Serial-based:** appointment assigned a serial/token in the day's
    queue.
3.  **Hybrid:** combines time windows and serial/queue order.

The model may be configured by facility and, where supported, doctor or
consultation location.

Appointment model, external-confirmation requirement, walk-in policy,
queue policy and token-numbering policy are separate configuration
concepts.

## 15. Doctor schedules and availability

Schedules are internal to authorized facility users. Patients do not
browse schedules through AMSDP.

Schedule configuration should support:

-   Working days and start/end times.
-   Breaks and unavailable periods.
-   Appointment duration for time-slot models.
-   Serial capacity for serial models.
-   Hybrid rules.
-   Blocked dates and periods.
-   Facility defaults with permitted doctor/branch overrides.

Validate availability and capacity when an appointment is saved, not
only when the form is opened.

------------------------------------------------------------------------

# Part V --- Appointment lifecycle and capacity

## 16. Appointment creation

An appointment may include patient, doctor, organization, branch,
optional department/room, date, appointment model, slot and/or
serial/token, booking source, optional operational note and
external-confirmation state where applicable.

Booking source may be phone, in-person, receptionist, doctor assistant,
walk-in or another facility-approved source.

## 17. Appointment transfer

1.  Transfer is a configurable, permission-controlled capability.
2.  Transfers are allowed only between doctors, branches and locations
    within the same organization.
3.  Cross-organization transfers are prohibited.
4.  Destination must be active and have permitted availability/capacity
    unless authorized overbooking applies.
5.  Record original and new doctor, branch, location, date, slot/serial.
6.  Preserve original appointment history.
7.  Require an authorized user and record a reason.
8.  Never silently change an appointment.
9.  If transfer is disabled, use cancel-and-create.

## 18. Appointment statuses

Use these core statuses:

  -----------------------------------------------------------------------
  Status                              Meaning
  ----------------------------------- -----------------------------------
  `BOOKED`                            Appointment created.

  `AWAITING_CONFIRMATION`             Facility requires external
                                      confirmation before confirmation.

  `CONFIRMED`                         Appointment confirmed.

  `CHECKED_IN`                        Staff recorded patient arrival.

  `IN_QUEUE`                          Patient is waiting in the active
                                      queue.

  `IN_CONSULTATION`                   Consultation has started;
                                      operational status only.

  `COMPLETED`                         Appointment process completed.

  `CANCELLED`                         Appointment cancelled.

  `NO_SHOW`                           Staff confirmed patient did not
                                      attend.

  `RESCHEDULED`                       Original appointment superseded by
                                      a new appointment.
  -----------------------------------------------------------------------

### 18.1 Default transitions

``` text
BOOKED
 ├── CONFIRMED
 ├── AWAITING_CONFIRMATION
 ├── CANCELLED
 └── RESCHEDULED

AWAITING_CONFIRMATION
 ├── CONFIRMED
 ├── CANCELLED
 └── RESCHEDULED

CONFIRMED
 ├── CHECKED_IN
 ├── CANCELLED
 ├── RESCHEDULED
 └── NO_SHOW (after grace period and staff confirmation)

CHECKED_IN
 ├── IN_QUEUE
 ├── IN_CONSULTATION (if facility workflow permits)
 ├── CANCELLED (authorized exception with reason)
 └── RESCHEDULED (authorized exception with reason)

IN_QUEUE
 ├── IN_CONSULTATION
 ├── CANCELLED (authorized exception with reason)
 └── RESCHEDULED (authorized exception with reason)

IN_CONSULTATION
 └── COMPLETED
```

Rules:

-   `COMPLETED`, `CANCELLED`, `NO_SHOW` and `RESCHEDULED` are terminal
    for that appointment record.
-   Correcting a terminal status requires a specifically authorized
    correction with reason and audit entry.
-   Rescheduling creates a new appointment linked to the original. Never
    overwrite the original date/time/doctor/token history.
-   `AWAITING_CONFIRMATION` is used only when external confirmation is
    enabled.
-   Queue position, appointment status, appointment time and token
    number are separate concepts.
-   A patient may be checked in and queued through staff workflow; no
    patient portal action is required.

## 19. Cancellation policy

1.  Cancellation policy is configurable within platform limits.
2.  Support configurable deadlines/restrictions and exceptional
    cancellation permissions.
3.  Routine cancellation requires cancellation permission.
4.  Late/exceptional cancellation may require higher permission
    according to facility configuration.
5.  Capture a cancellation reason. Suggested reasons: patient requested,
    doctor unavailable, facility closed, duplicate booking, other.
6.  Preserve the cancelled appointment and history.
7.  Cancellation does not erase token or queue audit history.
8.  If no facility deadline is configured, an authorized staff member
    may cancel at any time, with reason and audit entry.

## 20. No-show policy

1.  Facility configures a no-show grace period.
2.  After scheduled time plus grace period, system may flag **potential
    no-show**.
3.  System must not automatically assert that the patient physically
    failed to attend.
4.  Authorized staff confirms `NO_SHOW`.
5.  Staff may correct the flag if patient arrived or was present.
6.  Record actor, timestamp and reason.
7.  No-show does not delete appointment or queue history.

## 21. Late arrival

1.  Grace period is facility-configurable.
2.  System indicates lateness according to the configured rule.
3.  Late arrival does not automatically cancel or mark no-show.
4.  Authorized staff decides whether to retain position, move patient in
    queue or reschedule.
5.  Queue changes/rescheduling follow permissions and audit rules.
6.  If no grace period is configured, use zero minutes for the late
    indicator, but do not automatically cancel or mark no-show.

## 22. Overbooking

1.  Overbooking is configurable and **disabled by default**.
2.  Facility Admin configures permitted limits within Super Admin
    limits.
3.  Limits may be scoped by doctor, schedule, date, branch/location or
    appointment model where applicable.
4.  Only authorized users may exceed normal capacity.
5.  Every overbooking action requires a reason and audit record.
6.  Distinguish normal capacity from additional overbooking capacity.
7.  Overbooking cannot bypass tenant isolation or create invalid
    slot/serial assignment.
8.  If disabled or limit reached, reject booking with a clear
    explanation.

## 23. Capacity and double-booking protection

1.  Super Admin defines platform limits.
2.  Facility Admin configures operational capacity within those limits.
3.  Capacity may vary by doctor, schedule, date, branch/location and
    appointment model.
4.  Time-slot models enforce slot capacity.
5.  Serial models enforce configured serial capacity.
6.  Hybrid models enforce configured time-window and serial/queue
    constraints.
7.  Validate capacity atomically at save time to prevent concurrent
    overbooking.
8.  Use transactions, constraints or equivalent concurrency-safe
    mechanisms; frontend-only validation is insufficient.
9.  Do not assume one universal daily capacity.

------------------------------------------------------------------------

# Part VI --- Walk-ins, queue and daily board

## 24. Walk-in registration --- FINALIZED

1.  Authorized staff may register walk-ins in the facility workspace.
2.  Minimum patient details: name and mobile number.
3.  Search for an existing organization-level patient record before
    creating a new one.
4.  Walk-in is an entry source, not a fourth appointment model.
5.  Walk-ins join the unified queue under the configured policy.

## 25. Walk-in placement policies --- FINALIZED

Facility may choose among:

1.  **End of queue:** walk-in joins after existing applicable bookings.
2.  **First-come, first-served:** order follows configured
    arrival/registration rule.
3.  **Reserved capacity:** reserve a configurable number or percentage
    of capacity for walk-ins.
4.  **Staff-controlled placement:** authorized staff selects queue
    position.

Super Admin defines available options/limits. Facility Admin selects
policy. Only authorized users may change it. Changes are audit logged
and apply prospectively; they must not silently reorder an active queue
or alter existing appointments.

## 26. Unified queue --- FINALIZED

The queue may contain advance bookings, phone/reception/assistant
bookings, walk-ins, rescheduled appointments and authorized priority
entries.

Queue scope is configured for the relevant organization, branch, doctor,
room, date and queue/serial configuration. Do not combine unrelated
doctors' queues unless the facility explicitly configures a shared
queue.

## 27. Manual queue management --- FINALIZED

Authorized staff may move patients up/down, change queue position,
adjust serial order where supported, mark absent/temporarily
unavailable, skip a patient and reinsert a skipped patient where
permitted.

Rules:

1.  Permission-check every change.
2.  Record previous/new position and status, actor, timestamp and reason
    where required.
3.  Preserve original appointment and token history.
4.  Reordering must not silently change appointment date or time slot.
5.  Time-slot changes use a separate appointment-change action that
    shows the new slot before saving.
6.  Queue position, appointment status, appointment time and token are
    separate concepts.
7.  Do not automate clinical triage or infer clinical urgency.

## 28. Priority entries

1.  Super Admin defines available priority permissions/limits.
2.  Facility Admin assigns priority permissions.
3.  Authorized staff may assign/remove priority.
4.  Assignment/removal is audit logged.
5.  AMSDP does not assess or triage clinical urgency.
6.  Priority affects queue ordering only according to facility policy
    and authorized action.

## 29. One-page daily appointment board

The daily board is the main workspace for receptionists and assistants.
Subject to permissions, it should provide:

-   Date, branch/location and doctor selectors.
-   Patient search.
-   Add appointment and add walk-in actions.
-   Appointment/queue list.
-   Patient name/mobile for authorized staff.
-   Slot time and/or serial/token.
-   Appointment status.
-   Check-in and attendance controls.
-   Queue position.
-   Quick reschedule/cancel actions.
-   Token generation/printing when enabled.

### Touch and drag behavior

-   Desktop: mouse and keyboard-accessible queue movement.
-   Mobile/tablet: press-and-hold drag-and-drop where practical.
-   Visible drag handles and drop-position feedback.
-   Move-up/move-down alternatives.
-   Permission check before save.
-   Confirmation or undo for consequential changes as appropriate.
-   Audit actor and timestamp.
-   Dragging changes queue order only; it must not silently change
    appointment date/time.

------------------------------------------------------------------------

# Part VII --- Tokens and digital queue displays

## 30. Token generation

1.  Token generation is part of the core appointment/queue engine.
2.  Token identifies a queue entry within its configured numbering
    scope.
3.  Token is distinct from internal appointment ID and patient ID.
4.  Generation must be concurrency-safe; simultaneous registrations must
    not receive duplicate tokens within the same scope.
5.  Preserve token history after queue reorder, cancellation,
    rescheduling or sequence reset.
6.  Queue position changes must not silently regenerate historical
    tokens.

## 31. Token numbering --- FINALIZED

Facility configures numbering independently for each doctor or
consultation room.

Supported modes:

-   **Daily serial:** starts from `001` for each operating day.
-   **Continuous serial:** continues increasing without daily reset.
-   **Default:** daily serial.

Rules:

1.  Numbering scope may be doctor or room, as configured.
2.  Different doctors/rooms may have independent sequences.
3.  Token must be unique within its configured scope and applicable
    date/sequence.
4.  Resetting daily sequence does not erase history.
5.  Queue reorder does not regenerate token numbers automatically.
6.  Printed token and digital display show the same assigned token.
7.  A voided/cancelled token remains in history and is not reused by
    default.

## 32. Printed queue tokens --- FINALIZED

AMSDP supports printing a queue token. This is not a full appointment
slip.

A token should contain only operational information:

-   Facility/branch name.
-   Doctor name.
-   Room name/number, if applicable.
-   Queue token/serial number.
-   Appointment/queue date.
-   Estimated reporting time, if available and clearly labelled as an
    estimate.

Do not print patient mobile number, clinical details, payment
information or unnecessary personal data by default.

Use a simple browser-compatible print layout initially. Printer model,
paper size and device integration are technical choices to document.

## 33. Digital Queue Display System (DQDS) --- FINALIZED DIRECTION

DQDS is an approved optional capability for facilities using a
television or large display. It is not mandatory for every subscriber.

Requirements:

1.  Display current queue/token information for multiple doctors and
    rooms on one screen.
2.  Support multiple displays per branch.
3.  Configure each display for relevant branch, rooms, doctors or
    queues.
4.  Display language configurable as Bangla or English.
5.  Automatically refresh when authorized queue information changes.
6.  Use large readable typography suitable for television/waiting areas.
7.  Display current token/serial and relevant doctor/room information.
8.  Support estimated waiting-time countdown/reporting time where
    sufficient data exists.
9.  Label countdown/reporting time as an estimate, never a guaranteed
    consultation time.
10. Do not display patient names, mobile numbers or other personal
    information by default.
11. Show only information explicitly enabled for public display by the
    facility.
12. Display is read-only; public users cannot change appointments,
    queues or settings.
13. Enforce tenant and branch scope for every display data feed.

### 33.1 Scope status --- PRODUCT OWNER DECISION PO-13 (24 November 2026)

The full capability in items 1--13 above is **required for Hackathon
delivery**. It is not optional, not deferred and not a later-phase
capability. The paragraph that previously classified DQDS, television
integration and multi-display configuration as later-phase capabilities
is removed by this decision and must not be reinstated or cited.

Two different questions must not be confused: **delivery** of the
capability is mandatory; **adoption** by a given subscriber remains
optional (the sentence above about facilities not being obliged to run a
screen is unchanged). A facility may choose not to operate a display; no
implementation may choose not to build one.

Required for Hackathon delivery, explicitly (numbered independently of
items 1--13 above):

1.  Multiple independently configured displays per branch, with no fixed
    cap; each display is a separate record with its own name, code,
    configuration, language and enabled/disabled state.
2.  Display targeting by branch, doctor, department, room or queue, as
    applicable. Where a target cannot be expressed against the existing
    data model, the closest derived target is used and the derivation is
    documented --- never a silent fall-back to the whole branch.
3.  Configurable Bangla and English display language, held on the display
    itself so that a screen keeps its language across a power cycle.
4.  Server-side filtering and strict organization and branch isolation on
    every display feed.
5.  Automatic refresh when authorized queue information changes.
6.  Large, readable typography suitable for television and waiting-area
    displays.
7.  Current token/serial with the relevant doctor and room information.
8.  Estimated waiting-time information where sufficient data exists,
    clearly identified as an estimate and never as a guaranteed
    consultation time.
9.  Token-only public payloads by default: no patient names, mobile
    numbers or other personally identifiable information.
10. Facility-controlled public-display information: the facility decides
    what its own screens show.
11. Read-only public access. No public user can change appointments,
    queues, displays or settings through a display.
12. Administrator configuration of displays, with audit logging of every
    configuration change.

**Interpretation rule.** No implementation agent may use earlier
later-phase wording, an MVP-scope ranking, a roadmap position or any
other document to reduce, defer or independently reinterpret this
scope. A reduction requires a new product-owner decision recorded in
this section.

**No separate scope tiers.** There is no MVP Scope, Hackathon Version or
Later Releases distinction governing this requirement (product-owner
decision PO-02, 24 November 2026). Section 33 governs.

**Boundaries that still apply.** Implementation remains subject to the
documented dependencies, the security requirements (tenant and branch
scope enforced server-side from the authenticated principal; unknown,
cross-tenant, cross-branch or disabled display targets return 404, never
403; audit events append-only; no patient identity on a public screen)
and the acceptance criteria in the DQDS functional specification.
Approval of this scope does not by itself authorise production
deployment, unrelated implementation work or a change to any other
approved rule.

------------------------------------------------------------------------

# Part VIII --- External confirmation, communication and SMS

## 34. External advance-payment confirmation

1.  Advance payment is arranged and handled outside AMSDP.
2.  AMSDP does not process, receive, reconcile or store payment details.
3.  If facility requires external confirmation before appointment
    confirmation, it may enable `AWAITING_CONFIRMATION`.
4.  Authorized staff checks the external arrangement outside AMSDP and
    changes appointment to `CONFIRMED`.
5.  Store only appointment confirmation state and operational audit
    details.
6.  Do not store payment amount, recipient number, wallet/bank details,
    QR code, transaction ID, invoice or financial ledger.

## 35. Patient communication

1.  Facility staff communicates appointment information through existing
    channels.
2.  Patients do not need an AMSDP account or portal.
3.  Copyable appointment details may be provided as a staff convenience.
4.  Printed queue tokens are supported under Section 32.
5.  SMS is a later-phase capability, not a Phase 1 dependency.

## 36. SMS --- APPROVED, PHASE 2

Support both staff-triggered/manual SMS and automatic appointment
confirmation/reminder SMS.

Rules:

1.  SMS is optional and configurable per organization/facility.
2.  Use an external SMS provider.
3.  Provide facility-configurable templates within platform limits.
4.  Support facility-level enable/disable and message-event
    configuration.
5.  Record operational request/delivery status as needed; do not create
    a patient messaging portal.
6.  Store provider credentials securely; never expose them to frontend
    users or AI agents.
7.  Do not block appointment creation when SMS is disabled or provider
    unavailable.
8.  SMS must not delay the core appointment MVP.

------------------------------------------------------------------------

# Part IX --- Subscription lifecycle

## 37. Subscription model --- FINALIZED

Hospitals, clinics and diagnostic-centre organizations subscribe for
their organizational workspace. An independent chamber/practice may
subscribe as its own facility. Doctors do not need individual
subscriptions to be listed in an organization. Each tenant's data
remains isolated.

## 38. Subscription controls

Super Admin may configure plans, user limits, doctor-entry limits,
branch/location limits, feature availability, start/expiry, grace
period, suspension and reactivation.

## 39. Expiry and suspension --- APPROVED DEFAULT

Use this default lifecycle unless plan configuration specifies a
stricter permitted policy:

1.  Notify authorized facility administrators before expiry where
    notification capability exists.
2.  At expiry, enter grace-period state.
3.  During grace period, normal operation continues unless plan
    explicitly states otherwise.
4.  After grace period, suspend write operations that create or change
    operational data.
5.  Preserve read-only access for authorized users to view existing
    records and retrieve permitted exports.
6.  Do not delete tenant data merely because subscription expires.
7.  On renewal, restore permitted operations without creating a new
    tenant or losing history.
8.  Permanent deletion/retention periods follow a separately configured
    legal/product retention policy. Until one exists, retain data
    securely and do not automatically purge it.
9.  Audit subscription state changes and administrative actions.

------------------------------------------------------------------------

# Part X --- Audit, privacy and security

## 40. Audit history --- FINALIZED DIRECTION

Audit important actions, including:

-   Appointment creation and changes.
-   Cancellation, rescheduling and transfers.
-   Queue and serial adjustments.
-   Priority assignment/removal.
-   Patient record changes and merges.
-   Permission, role, configuration and staff-assignment changes.
-   Token generation, voiding and sequence configuration.
-   Digital display configuration.
-   Subscription activation, expiry, suspension and reactivation.

Audit record should identify tenant, relevant branch/context, actor,
action, timestamp, target record, before/after values where appropriate
and reason where required.

Protect audit records against ordinary user modification/deletion. Never
expose audit history across tenants.

## 41. Data minimization --- FINALIZED DIRECTION

1.  Collect and store only information needed for appointment
    operations.
2.  Do not collect unnecessary clinical, financial or identity
    information.
3.  Do not expose patient personal data on public displays.
4.  Restrict patient data to authorized users and permitted branches.
5.  Phone-number equality is not proof of identity.
6.  Apply secure authentication, authorization, transport protection,
    secret management, backups and recovery.

## 42. Security requirements

Provide secure facility-user authentication, server-side role/scope
authorization, strict tenant isolation, protection against unauthorized
record access, secure password/session handling, safe error handling,
secret management, backups/recovery and audit logging.

Never embed credentials or production secrets in source code, prompts,
agent context or frontend bundles.

------------------------------------------------------------------------

# Part XI --- Reports, localization and usability

## 43. Basic operational reports

Permitted reports include appointments by day, doctor or branch;
booked/completed/cancelled/no-show counts; walk-in counts; queue
activity; booking-source counts; and schedule utilization where
meaningful for the appointment model.

Do not add revenue, billing, payment-settlement or clinical-performance
analytics.

## 44. Bangladesh-focused usability

Support Bangla and English interfaces, Bangla/English patient-name
input, correct Unicode handling and Bangla/English digital display
configuration.

Support phone-based requests, in-person registration,
assistant/reception bookings, walk-ins, serial, time-slot and hybrid
practices, and external advance-payment arrangements without payment
processing.

## 45. Device and connectivity

The staff experience should be mobile-first, responsive on
tablet/desktop, touch friendly, fast on ordinary mobile connections,
lightweight, clear about save/error/connection states and usable without
high-end devices or constant heavy background activity.

------------------------------------------------------------------------

# Part XII --- Release phasing

## 46. Phase 1: Essential appointment operations

Prioritize:

-   Subscriber/organization workspace and basic subscription state.
-   User login and permission enforcement.
-   Organization and basic branch data model.
-   Lightweight doctor entries.
-   Organization-level patient registration and search.
-   Patient records shared across branches subject to permissions.
-   Appointment creation.
-   Time-slot, serial and hybrid models.
-   Doctor schedule configuration.
-   Daily appointment board.
-   Check-in and attendance.
-   Queue and serial management.
-   Walk-in registration and all four walk-in policies.
-   Manual queue adjustment with audit history.
-   Basic priority permissions.
-   Token generation and configurable numbering data model.
-   Strict tenant isolation.
-   Audit history and data minimization.

Basic token printing may be implemented in Phase 1 if needed for
operational validation; the token engine must exist independently of
printer hardware.

## 47. Phase 2: Operational refinement

-   Advanced queue policies and full drag-and-drop interaction.
-   Additional reports.
-   Multi-branch operational refinements.
-   Appointment transfer workflow if not included earlier.
-   Token print-layout refinements.
-   Digital Queue Display System, including multi-room/multi-doctor
    displays.
-   Estimated waiting-time countdown.
-   Manual and automatic SMS.
-   Duplicate patient merge workflow.
-   Additional approved appointment-change workflows.

## 48. Phase 3: Optional extensions

External integrations and other appointment-related extensions only
after core operations are validated and separately approved. Do not add
excluded HMS/EMR/financial/clinical functionality without separate
product approval.

------------------------------------------------------------------------

# Part XIII --- Acceptance criteria

## 49. Tenant and branch isolation

-   Organization A cannot retrieve Organization B data by changing IDs,
    URLs, API parameters or request bodies.
-   Branch-restricted user cannot access an unassigned branch unless
    explicitly granted.
-   Authorized users can access shared organization-level patient
    records across branches.
-   Appointment records retain branch association.

## 50. Patient handling

-   Patient name and mobile are required.
-   Multiple records may share a mobile number within one organization.
-   Staff selects the correct patient record.
-   No automatic merge based only on matching name/mobile.
-   No patient account is required.

## 51. Appointment and capacity

-   All three appointment models work.
-   Capacity is validated at save time.
-   Concurrent bookings cannot exceed capacity except through authorized
    overbooking.
-   Cancellation, no-show, late arrival and rescheduling follow
    configured rules.
-   Rescheduling preserves the original record and links the new
    appointment.
-   External confirmation does not create a payment record.

## 52. Queue and token

-   All four walk-in policies work.
-   Queue can contain applicable bookings and walk-ins.
-   Authorized staff can reorder queue.
-   Queue reorder does not silently change appointment date/time.
-   Queue changes are auditable.
-   Token numbering supports daily and continuous modes.
-   Numbering is configurable per doctor or room.
-   Daily reset does not erase history.
-   Token generation is safe under concurrent registrations.
-   Public display does not expose patient personal data.

## 53. Printing and digital display

-   Printed token matches the assigned queue token.
-   Display language is configurable as Bangla or English.
-   Display can show multiple doctors/rooms.
-   Display updates when queue information changes.
-   Countdown is labelled as an estimate.
-   Display is read-only and tenant/branch scoped.

## 54. Permissions and audit

-   Every sensitive operation is authorized server-side.
-   Important changes record actor, time and relevant before/after
    values.
-   Ordinary users cannot edit/delete audit history.
-   Configuration changes do not silently rewrite historical records.

------------------------------------------------------------------------

# Part XIV --- AI-agent operating contract

## 55. Mandatory instructions for every AI agent

Every agent must:

1.  Read this document before implementing any feature.
2.  Read relevant product, architecture, database and API
    specifications.
3.  Treat this document as the business-rule authority.
4.  Implement only its assigned task and dependencies.
5.  Avoid out-of-scope features.
6.  Never weaken tenant isolation or server-side authorization.
7.  Never invent clinical triage, patient self-service or
    payment-processing behavior.
8.  Add tests for relevant business rules, permissions, tenant
    boundaries and failure cases.
9.  Preserve auditability and historical data.
10. Document technical assumptions and implementation decisions.
11. Report a genuine requirements contradiction rather than silently
    choosing a conflicting interpretation.
12. Do not ask routine product questions answered by this document. Use
    stated defaults/configuration rules.

## 56. Configurable decisions --- do not hard-code globally

Implement configuration and safe defaults for:

-   Cancellation deadline/restrictions and exceptional cancellation
    permissions.
-   No-show grace period.
-   Late-arrival grace period.
-   Overbooking enablement and limits.
-   Capacity by doctor/schedule/date/location/model within platform
    limits.
-   Appointment transfer permissions.
-   Branch, department and room usage.
-   Walk-in placement policy.
-   Appointment model.
-   Doctor mobile-number duplicate policy.
-   Token numbering mode and scope.
-   Facility and display language.
-   SMS event/template settings when implemented.
-   Subscription plans, limits, expiry and grace period.

## 57. Final product rule

AMSDP must remain a lightweight, facility-centric appointment and queue
management platform for Bangladesh.

It must make appointment operations easier for receptionists,
assistants, doctors and facility administrators without requiring
patients to use AMSDP, replacing a facility's full HMS, or expanding
into clinical, financial or unrelated hospital operations.

**When in doubt: protect patient privacy, preserve tenant isolation and
history, prefer staff-controlled operational decisions, and keep the
product focused on appointments and queues.**

------------------------------------------------------------------------

## 27A. Missed-turn recovery and queue repositioning — APPROVED FOR MVP (9 November 2026)

This section supplements §27 (Manual queue management), §28 (Priority
entries), and the existing no-show and late-arrival rules. It does not
replace or weaken those rules.

1. **Staff-confirmed event only.** A missed turn is handled only after an
   authorized staff member or authorized doctor confirms that the patient
   was unavailable when called. The system must not infer a missed turn
   from elapsed time, tracking-page activity, message delivery/read status,
   or lack of patient response.
2. **Default recovery action.** Once confirmed, the default is to defer
   the patient to the end of the same applicable active queue. The
   applicable queue is the same doctor/room and operational queue context
   from which the patient was called; the action must not silently move
   the patient to another doctor, branch, date, or appointment slot.
3. **Authorized position override.** An authorized staff member or
   authorized doctor may instead move the patient to any valid position
   in that same applicable queue. This includes a human-directed
   emergency or priority adjustment. AMSDP does not assess urgency,
   make clinical triage decisions, or automatically grant priority.
4. **Permission enforcement.** The actor must have explicit permission
   for missed-turn confirmation and queue repositioning. Any override
   must also satisfy the actor's queue-movement/priority permissions.
   Enforce permissions in backend services, not only in the interface.
5. **Appointment and token preservation.** Recovery does not cancel,
   recreate, or reschedule the appointment. Preserve the original
   appointment identity, appointment date/time, token/serial identity,
   and complete prior queue history. Queue position is changed separately
   from appointment time and token identity.
6. **Audit record.** Record the missed-turn confirmation and resulting
   queue movement, including previous and new position/status, actor,
   timestamp, action type (default end-of-queue or override), and reason.
   An override requires a reason. Record the old and new position even
   when the patient is placed at the default end position.
7. **No automatic no-show.** Missed-turn recovery does not itself set
   `NO_SHOW`. The existing staff-confirmed no-show policy and configured
   grace-period rules remain in force. No-show must never be inferred
   solely from a missed call, elapsed grace period, message status, or
   tracking activity.
8. **No silent appointment change.** Do not change the appointment date,
   start time, doctor, branch, or room as part of queue recovery. Any
   appointment change must use its separate authorized workflow.
9. **Human-controlled safety.** AMSDP must not decide whether a patient
   can safely leave the facility or whether a case is urgent. Remote
   waiting remains optional. A patient instructed to remain, or requiring
   urgent assessment, must follow facility staff/clinical instructions.
10. **Notification independence.** A messaging provider outage, failed
    delivery, or unconfigured channel must not block staff from recording
    the missed turn or repositioning the queue.
11. **Same-queue boundary.** "End of queue" and "any valid position"
    refer only to a position permitted by the active queue's configuration
    and policy. Cross-branch, cross-doctor, cross-date, and cross-appointment
    movement is not part of this recovery action.

**Acceptance criteria**

- An authorized staff member or doctor can confirm a missed turn.
- Confirmation defaults to the end of the same applicable active queue.
- An authorized actor can override the default and select any valid
  position in that same queue, with a recorded reason.
- Appointment, appointment time, token identity, and historical queue
  events remain preserved.
- Previous/new position, actor, timestamp, action type, and reason are
  auditable.
- No automatic `NO_SHOW` or clinical triage decision is made.
- Recovery remains available when notifications are unavailable.

**Version control:** This section is the approved V1.1 amendment. The
V1.0 baseline is retained as the historical record and must not be
silently overwritten.

