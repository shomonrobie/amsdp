# AMSDP MVP Scope V1.1

**Product:** Appointment Management System for Doctors & Patients
(AMSDP)\
**Document type:** Product scope and release boundary\
**Version:** 1.1\
**Status:** Approved MVP scope baseline (V1.1 amendment approved 9 November 2026)\
**Prepared:** 4 November 2026\
**Primary market:** Bangladesh\
**Related authority:** `docs/product/AMSDP_Business_Rules_V1.1.md`

------------------------------------------------------------------------

## 1. Purpose

This document defines the first real, usable release of AMSDP. The
objective is to build a small but complete appointment and
queue-management product that a healthcare facility could use in
day-to-day operations---not a mock-up or a hackathon-only demonstration.

The hackathon demonstration will use the same application, backend,
database, permissions and workflows intended for real use. Demonstration
data may be prepared in advance, but the workflow itself must be
genuine.

This scope is subordinate to the approved **AMSDP Business Rules V1.0**.
If a detail in this document conflicts with that rules document, the
business rules document takes precedence unless a new decision is
explicitly approved and recorded.

## 2. Product outcome

At the end of Phase 1, one healthcare organization must be able to
configure its facility operations and use AMSDP to:

1.  Maintain its own patient records.
2.  Maintain its own doctors and their schedules.
3.  Register appointments through authorized staff.
4.  register walk-in patients.
5.  Operate one unified daily queue for scheduled and walk-in patients.
6.  Track each appointment through its operational lifecycle.
7.  Review an auditable history of important appointment and queue
    actions.

The release must support multiple organizations in the same application
while enforcing strict tenant isolation.

## 3. Product principles and constraints

-   **Facility-first:** Healthcare organizations subscribe to and
    operate the service. An independent chamber can be its own
    organization.
-   **Staff-mediated workflow:** Facility staff create and manage
    appointments. Patient accounts, patient self-booking and a patient
    portal are not part of the MVP.
-   **Tenant isolation:** Organization boundaries are security
    boundaries. Users must never access another organization's patients,
    doctors, appointments, schedules or operational data.
-   **Operationally complete:** The MVP prioritizes a complete
    booking-to-queue workflow over a broad collection of partially
    implemented modules.
-   **Bangladesh-ready:** Support Bangla and English text, Unicode,
    mobile-first use and low-bandwidth operating conditions.
-   **Human-controlled decisions:** The system supports staff decisions;
    it does not perform clinical triage or make clinical judgments.
-   **Auditable operations:** Important changes record the actor,
    timestamp and relevant before/after values; reasons are recorded
    where required by the business rules.
-   **No unsupported claims:** Do not claim measured reductions in
    waiting time, improved clinical outcomes, interoperability,
    integrations or pilot results unless these are independently
    verified.

## 4. Users and roles in the MVP

### 4.1 Platform Super Admin

Platform-level operator who can:

-   Create, activate, suspend and administer organizations.
-   Set platform-wide limits, defaults and permitted configuration
    ranges.
-   Manage platform-level roles and permissions.
-   Configure whether duplicate doctor mobile numbers are permitted
    within an organization.
-   Access platform administration functions without bypassing tenant
    security controls or silently changing tenant-owned operational
    records.

### 4.2 Organization / Facility Admin

Organization-level administrator who can:

-   Manage organization settings and permitted branches.
-   Create and manage facility staff accounts and role assignments.
-   Configure branches, doctors, rooms and schedules within platform
    limits.
-   Configure operational policies where the business rules permit.
-   Review organization-level operational records and audit history.

### 4.3 Facility Staff / Appointment Desk

Authorized staff who can:

-   Search for and register patients.
-   View permitted doctor schedules and availability.
-   Create, update, cancel and transfer appointments according to
    permissions.
-   Register walk-in patients.
-   Check patients in and operate the daily queue.
-   Record appointment confirmation state where applicable.
-   View the information required for their assigned work.

### 4.4 Doctor

A doctor may be represented as a facility-local operational record. A
doctor does not need an individual AMSDP account or subscription merely
to be listed in a facility.

If doctor login access is enabled in the MVP, it must be
permission-scoped to the relevant organization and branch. Doctor
self-service features are not a dependency for the core workflow.

## 5. MVP functional scope

### 5.1 Organization and branch foundation

**Required**

-   Create and manage organizations (tenants).
-   Support one or more branches under an organization.
-   Keep organization as the tenant boundary; a branch is not a separate
    tenant by default.
-   Assign users to an organization and permitted branch scope.
-   Support a single-branch organization without requiring unnecessary
    department or room hierarchy.
-   Allow an organization to share patient records across its branches
    according to permissions.
-   Keep appointments associated with the branch where they are booked.

**Acceptance criteria**

-   A user from Organization A cannot retrieve or modify Organization B
    data through the UI, API or direct identifier manipulation.
-   Branch-scoped staff cannot operate outside their assigned branch
    permissions.
-   An authorized organization-level user can work across permitted
    branches.
-   A single-chamber organization can configure and use the system
    without creating multiple branches or departments.

### 5.2 Authentication and authorization

**Required**

-   Secure staff authentication.
-   Server-side authorization for every protected operation.
-   Role- and scope-based permissions for platform, organization and
    branch operations.
-   Secure password handling and session management.
-   Account activation and deactivation.
-   Enforced tenant and branch scope on API requests and database access
    paths.
-   Audit important administrative and permission changes.

**Acceptance criteria**

-   Hiding a button in the frontend is never the only authorization
    control.
-   Unauthorized requests are rejected by the backend.
-   Changing an organization, branch, patient, doctor or appointment
    identifier in a request cannot expose another tenant's data.
-   Deactivated users cannot continue to perform authenticated
    operations.

### 5.3 Patient records

**Required**

-   Create, search, view and update organization-owned patient records.
-   Mandatory patient fields: name and mobile number.
-   Support Bangla and English names and Unicode text.
-   Permit multiple patient records to share a mobile number within the
    same organization, because family members may share a phone.
-   Make staff select and verify the correct patient when search results
    contain similar names or shared mobile numbers.
-   Share patient records across branches of the same organization
    according to permissions.
-   Keep patient data isolated from all other organizations.
-   Warn staff about possible duplicate records and provide a safe
    correction workflow.

**Duplicate handling**

-   Do not automatically merge patients based only on name or mobile
    number.
-   Phase 1 supports duplicate warnings and correction through an
    authorized process.
-   A formal merge workflow may be delivered in a later phase. Any
    future merge must preserve appointment history and audit records.

**Acceptance criteria**

-   A patient can be found by supported search fields without exposing
    records from another organization.
-   Two family members can share one mobile number and remain distinct
    patient records.
-   Bangla characters are stored, retrieved and displayed without
    corruption.
-   The system does not silently merge records.

### 5.4 Doctor and room records

**Required**

-   Create and manage facility-local doctor records.
-   Mandatory doctor fields: name and mobile number.
-   Assign a facility-local unique Doctor ID.
-   Associate doctors with the relevant organization and branch.
-   Support optional room association.
-   Enforce the approved organization-level mobile-number uniqueness
    policy, including the Super Admin-controlled duplicate allowance.
-   Do not create a global doctor identity or automatically match the
    same doctor across organizations.

**Acceptance criteria**

-   A doctor record is unique within its defined organization context.
-   The same mobile number may exist in different organizations.
-   A doctor listed by one organization is not automatically visible or
    transferable to another organization.

### 5.5 Schedule and capacity configuration

**Required**

-   Configure doctor availability by branch and operating date/time.
-   Support the approved appointment models:
    -   Time-slot.
    -   Serial-based.
    -   Hybrid.
-   Configure capacity at the appropriate doctor, schedule, date and
    model level, within platform limits.
-   Support schedule blocking for unavailable periods.
-   Validate appointment capacity on the server at booking time.
-   Prevent concurrent requests from exceeding configured capacity or
    creating prohibited double bookings.
-   Keep queue order separate from the originally booked appointment
    date/time.

**Acceptance criteria**

-   Staff can see whether a doctor has bookable capacity for the
    selected schedule.
-   Two concurrent booking attempts cannot both consume the same
    exclusive capacity.
-   Blocked periods cannot be booked unless an explicitly authorized
    exception is supported by the approved rules.
-   Changing queue position does not silently change appointment date or
    time.

### 5.6 Appointment booking and management

**Required**

-   Staff can create an appointment for an existing patient or register
    a new patient during the workflow.

-   Staff can select branch, doctor, schedule/date and the relevant slot
    or serial arrangement.

-   Support time-slot, serial-based and hybrid appointment models.

-   Record booking source, including staff-mediated booking and walk-in.

-   Support the approved appointment lifecycle:

    `BOOKED` → `AWAITING_CONFIRMATION` / `CONFIRMED` → `CHECKED_IN` →
    `IN_QUEUE` → `IN_CONSULTATION` → `COMPLETED`

    Other terminal or linked states include `CANCELLED`, `NO_SHOW` and
    `RESCHEDULED`, subject to the business rules.

-   Support appointment cancellation with configured permission/deadline
    rules and reason capture.

-   Support rescheduling while preserving the original appointment
    history and linking the replacement appointment.

-   Support same-organization appointment transfer when permitted and
    when destination availability rules are satisfied.

-   Support configurable overbooking permissions and limits; disabled by
    default.

-   Record appointment-level confirmation state only where applicable.

**Payment boundary**

-   External payment collection is outside the MVP.
-   AMSDP may record only the appointment-level state
    `AWAITING_CONFIRMATION` → `CONFIRMED` when the facility uses that
    workflow.
-   Do not implement payment gateway processing, amounts, balances,
    wallet data, transaction IDs, QR payment, invoices or financial
    ledgers.

**Acceptance criteria**

-   An authorized staff member can book an appointment end to end.
-   Booking validation is enforced by the backend.
-   Cancellation and rescheduling preserve history.
-   A rescheduled appointment is linked to its original appointment.
-   An appointment cannot be transferred across organizations.
-   No payment is processed or represented as collected by AMSDP.

### 5.7 Walk-in registration

**Required**

-   Staff can register a walk-in patient against a doctor/branch
    operating queue.
-   Walk-in is an entry source, not a separate appointment model.
-   Apply one of the configured walk-in policies:
    -   End of queue.
    -   First-come-first-served.
    -   Reserved capacity.
    -   Staff-controlled placement.
-   Record the staff member and time of registration.
-   Apply normal queue and audit rules to walk-in entries.

**Acceptance criteria**

-   A walk-in can join the same daily queue as scheduled appointments.
-   The configured walk-in policy is applied consistently.
-   Staff-controlled placement is permission-limited and auditable.

### 5.8 Unified queue management

**Required**

-   Provide a one-page daily operational board for the selected branch
    and doctor/room context.
-   Display scheduled and walk-in patients in a unified queue.
-   Support check-in and movement through queue statuses.
-   Support authorized manual reordering.
-   Provide press-and-hold drag-and-drop where practical, plus
    accessible move-up/move-down alternatives.
-   Support marking a patient absent, temporarily unavailable or
    skipped, with staff-controlled handling.
-   Support priority assignment and removal by authorized staff;
    priority is operational only and is not clinical triage.
-   Keep token/serial identity stable when queue position changes.
-   Record queue changes, including previous and new position/status,
    actor and timestamp; capture a reason where required.
-   Never automatically mark a patient as a no-show solely because a
    grace period elapsed.
-   Use a configurable grace period to flag a potential no-show for
    staff review.
-   Apply configurable late-arrival grace periods as indicators only;
    staff decide whether to retain, move or reschedule the patient.

-   Support staff-confirmed missed-turn recovery: by default, defer the
    unavailable patient to the end of the same applicable active queue.
-   Allow an authorized staff member or doctor to override the default
    and move the patient to any valid position in that same queue,
    subject to permissions; an override requires a reason.
-   Preserve the original appointment, appointment date/time, token
    identity and complete queue history. Do not cancel/recreate or
    reschedule the appointment as part of recovery.
-   Audit the confirmation and movement, including previous/new
    position/status, actor, timestamp, action type and reason.
-   Do not automatically mark `NO_SHOW`, infer a missed turn from
    messaging/tracking activity, or make clinical triage decisions.
-   Messaging availability must not block queue recovery.

**Acceptance criteria**

-   Scheduled and walk-in entries appear in one queue.
-   Authorized staff can move a patient and the updated order is
    reflected consistently.
-   Queue changes are auditable.
-   Queue reordering does not change the appointment's booked date/time
    or regenerate its token.
-   A potential no-show requires staff confirmation.
-   An authorized staff member or doctor can confirm a missed turn and
    the default action places the patient at the end of the same
    applicable active queue.
-   An authorized override can place the patient at any valid position
    in that same queue and requires a reason.
-   Appointment identity, booked date/time, token identity and queue
    history are preserved; the recovery action does not cancel or
    reschedule the appointment.
-   The missed-turn action is auditable and does not automatically set
    `NO_SHOW`.
-   The system does not make clinical priority decisions.

### 5.9 Queue token / serial engine

**Required**

-   Generate a queue token/serial for queue operation.
-   Support configurable numbering by doctor or room.
-   Support:
    -   Daily serial numbering, default starting at `001` for each
        operating day.
    -   Continuous serial numbering.
-   Allow different doctors/rooms to maintain independent sequences
    where configured.
-   Keep token values stable after queue reordering.
-   Do not reuse voided or cancelled token numbers by default.
-   Reset numbering without deleting historical records.

**Acceptance criteria**

-   The same queue entry has one stable token across the staff board and
    any later print/display capability.
-   Token sequences do not collide within their configured scope.
-   Historical tokens remain traceable after a daily reset.

### 5.10 Audit history

**Required**

-   Record important patient, doctor, schedule, appointment, queue, role
    and configuration actions.
-   Record actor and timestamp.
-   Record previous/new values for changes where relevant.
-   Record reasons for cancellation, exceptional placement, overbooking
    and other actions where required by the business rules.
-   Make audit history available to appropriately authorized users.
-   Prevent ordinary users from silently editing or deleting audit
    events.

**Acceptance criteria**

-   An authorized reviewer can reconstruct the important history of an
    appointment and its queue changes.
-   Audit entries identify who performed an action and when.
-   Tenant and branch permissions apply to audit history as they do to
    operational records.

### 5.11 Language, accessibility and operational usability

**Required**

-   Bangla and English user interface support for MVP-critical
    workflows.
-   Unicode-safe patient and doctor names and other text.
-   Responsive layouts for mobile, tablet and desktop.
-   Touch-friendly controls for front-desk queue operation.
-   Clear validation and error messages.
-   Avoid unnecessarily heavy assets and workflows that impair
    low-bandwidth use.
-   Show estimated reporting time only where configured; never promise
    an exact consultation time.

**Acceptance criteria**

-   Core workflows can be completed on a modern mobile browser and
    desktop browser.
-   Bangla text can be entered, saved, searched where supported and
    displayed correctly.
-   Staff can operate the queue without relying solely on drag-and-drop
    gestures.

## 6. MVP end-to-end workflows

The MVP is not complete unless these workflows work together against the
real backend and database.

### Workflow A: Organization setup

1.  Super Admin creates an organization.
2.  Super Admin or authorized administrator creates its first branch.
3.  Organization Admin creates staff accounts and assigns roles/scopes.
4.  Organization Admin creates doctor and optional room records.
5.  Organization Admin configures doctor schedules, appointment model
    and capacity.

### Workflow B: Scheduled appointment

1.  Staff selects the appropriate branch and doctor.
2.  Staff searches for a patient.
3.  If no suitable record exists, staff registers the patient.
4.  Staff checks available capacity and selects a slot/serial
    arrangement.
5.  Staff creates the appointment.
6.  The system validates permissions, tenant scope and capacity, then
    persists the booking.
7.  Staff communicates the appointment details to the patient outside
    AMSDP.
8.  On arrival, staff checks the patient in and moves the entry into the
    queue.

### Workflow C: Walk-in appointment

1.  Staff selects the branch and doctor/room queue.
2.  Staff finds or registers the patient.
3.  Staff registers the walk-in.
4.  The system applies the configured walk-in placement policy.
5.  The walk-in appears in the same queue as scheduled appointments.
6.  Staff manages the patient through the normal queue lifecycle.

### Workflow D: Queue operation

1.  Staff opens the daily queue board.
2.  Staff sees scheduled and walk-in entries together.
3.  Staff calls or advances the next patient using the facility's
    operational process.
4.  Staff marks the patient as in consultation and later completed, or
    uses an appropriate exception status.
5.  Staff may skip, move or reprioritize an entry if authorized.
6.  The system records the change history.
7.  Token identity remains stable regardless of queue position changes.

### Workflow E: Cancellation and rescheduling

1.  Authorized staff selects an appointment.
2.  Staff selects the permitted action and reason.
3.  The system validates permission and policy.
4.  The original appointment and its history remain traceable.
5.  A rescheduled booking is created and linked to the original record.
6.  Queue and token history are not silently rewritten.

### Workflow F: Tenant-isolation verification

1.  Create at least two test organizations.
2.  Create separate users, patients, doctors, schedules and appointments
    in each.
3.  Attempt cross-organization access through normal navigation and
    direct API requests.
4.  Verify that all unauthorized access is rejected and no data is
    disclosed or modified.

## 7. Explicitly out of scope for Phase 1

The following are not MVP requirements, even if they appeared in early
brainstorming or the initial concept draft.

### Patient-facing access

-   Patient accounts and patient login.
-   Patient portal or patient dashboard.
-   Patient self-booking or public appointment marketplace.
-   Public doctor schedules or cross-facility doctor discovery.
-   Patient self-service cancellation or rescheduling.

### Payments and finance

-   bKash, Nagad, Rocket, Bangla QR, card or other payment gateway
    integration.
-   Advance, partial or full online payment collection.
-   Wallet PIN/OTP handling or payment credential capture.
-   Invoices, receipts for financial settlement, balances, cash desk or
    financial ledger.
-   Subscription billing automation and payment reconciliation.

### Clinical and medical records

-   EMR/EHR.
-   Prescriptions, diagnoses, clinical notes, symptoms or treatment
    plans.
-   Vitals intake such as blood pressure, weight or temperature.
-   Clinical decision support or AI triage.
-   Medical document uploads or clinical file management.
-   Insurance data, NID/OCR capture or clinical identity verification.

### Intake, communication and integrations

-   Pre-visit questionnaires or asynchronous intake links.
-   Automated SMS, WhatsApp, email or voice reminders.
-   External messaging provider integration.
-   EHR, hospital information system or third-party PMS integration.
-   National health identity, e-Health Card or national interoperability
    integration.
-   Telemedicine or video consultation.

### Additional facility operations

-   Pharmacy, inventory, laboratory, radiology or bed management.
-   HR, payroll, staff attendance or workforce scheduling.
-   Billing and claims management.
-   Advanced analytics, predictive reporting or AI agents making
    operational decisions.

### Queue extensions

-   Digital queue display/TV system.
-   Multi-screen display configuration.
-   Public-facing queue screens.
-   Advanced queue display countdowns.
-   Token printer integration and printer-specific device management.

**Note:** Basic token generation is in Phase 1. Printed queue tokens and
digital queue displays are planned for Phase 2. A simple manual
print/export workaround may be used during testing, but it is not a
release requirement.

## 8. Later release direction

This section is a planning guide, not a commitment to dates or delivery.

### Phase 2 --- Operational extensions

Candidate capabilities, subject to prioritization:

-   Printed queue token support and thermal printer compatibility.
-   Digital Queue Display System (DQDS), read-only and
    privacy-preserving by default.
-   Staff-triggered and automated SMS confirmations/reminders through an
    external provider.
-   More complete branch-level operational reporting.
-   Patient duplicate merge workflow with authorization and history
    preservation.
-   Additional operational conveniences based on facility feedback.
-   Subscription lifecycle automation, including grace period and
    restricted/read-only states, according to the approved business
    rules.

### Phase 3 --- Broader ecosystem capabilities

Candidate capabilities requiring separate product, security, legal and
integration review:

-   Patient-facing portal or self-service features.
-   External payment integrations.
-   Advanced analytics and carefully bounded AI assistance.
-   Third-party systems integration.
-   Broader clinical or facility-management modules, only if separately
    approved and appropriately governed.

No Phase 2 or Phase 3 feature should be added to Phase 1 merely because
it is technically interesting or easy to prototype. Any scope change
must include its user value, dependencies, security implications and
impact on the MVP delivery.

## 9. Non-functional requirements

These are release requirements, not optional future enhancements.

### Security and privacy

-   Enforce tenant isolation in backend authorization and data access.
-   Use secure authentication, password hashing and session handling.
-   Validate all input on the server.
-   Apply least-privilege access by role and branch scope.
-   Protect secrets and environment configuration; never commit
    credentials.
-   Avoid exposing patient information in URLs, public screens, logs or
    error messages.
-   Use HTTPS in deployed environments.
-   Maintain auditability for sensitive operational changes.
-   Backups and restore procedures must be documented before real
    production use.

### Data integrity

-   Use database constraints and transactions for critical operations.
-   Prevent race conditions and over-capacity booking.
-   Preserve appointment and audit history.
-   Use stable identifiers and explicit relationships.
-   Use migrations for schema changes; do not rely on manual production
    database edits.

### Reliability and usability

-   Provide clear errors and recoverable workflows.
-   Keep the core front-desk workflow responsive on mobile and desktop.
-   Design for intermittent or low-bandwidth connectivity, but do not
    claim full offline operation unless it is implemented and tested.
-   Do not silently discard staff input after a recoverable error.
-   Keep operational screens focused on the work staff perform most
    often.

### Maintainability

-   Separate frontend, backend, persistence and business logic concerns.
-   Keep business rules explicit and testable.
-   Maintain automated tests for critical workflows and authorization
    boundaries.
-   Document setup, configuration, migrations, testing and deployment.
-   Require human review of architecture, database migrations,
    security-sensitive code and production deployment.

## 10. Recommended implementation sequence

The sequence below is a delivery recommendation. It does not prescribe a
final technology choice.

1.  **Requirements baseline:** MVP scope, business rules, user roles,
    permissions and acceptance criteria.
2.  **Architecture:** application boundaries, deployment model,
    tenant-isolation strategy and key data flows.
3.  **Data model:** organization, branch, users/roles, patients,
    doctors, rooms, schedules, appointments, queue entries, tokens and
    audit events.
4.  **Backend foundation:** configuration, database migrations,
    authentication, authorization, tenant-scoped data access and API
    conventions.
5.  **Organization setup:** organizations, branches, staff and
    permissions.
6.  **Master data:** patients, doctors, rooms and schedules.
7.  **Appointment workflow:** availability, booking, cancellation,
    transfer and rescheduling.
8.  **Queue engine:** walk-ins, unified queue, token generation,
    reordering and status transitions.
9.  **Frontend workflow:** responsive staff-facing screens for the
    complete end-to-end process.
10. **Quality and security:** automated tests, tenant-isolation tests,
    concurrency tests, usability review and security review.
11. **Deployment readiness:** environment configuration, HTTPS,
    backup/restore, monitoring, error logging and operator
    documentation.
12. **Pilot readiness:** controlled facility test using realistic
    workflows, staff feedback and documented issues.
13. **Hackathon demonstration:** demonstrate the same working product
    using a prepared demo organization and sample data.

Do not begin broad parallel AI-agent implementation before architecture,
data boundaries and core acceptance criteria are reviewed. AI agents may
assist with implementation, but humans must review security, migrations,
data access and release decisions.

## 11. MVP acceptance and release gate

The MVP may be called **functionally complete** only when all mandatory
criteria below pass.

### Product workflow

-   [ ] An organization can be created and configured.
-   [ ] A branch, staff roles, doctor, room (if used) and schedule can
    be configured.
-   [ ] Staff can register and search patients.
-   [ ] Staff can book an appointment using the configured appointment
    model.
-   [ ] Staff can register a walk-in.
-   [ ] Scheduled and walk-in entries appear in one daily queue.
-   [ ] The queue supports permitted status changes and reordering.
-   [ ] Queue tokens are generated according to configured numbering
    rules.
-   [ ] Cancellation and rescheduling preserve history.
-   [ ] Important actions appear in audit history.

### Security and data integrity

-   [ ] Authentication and server-side authorization are enforced.
-   [ ] Tenant-isolation tests pass for read and write operations.
-   [ ] Branch scope is enforced.
-   [ ] Critical booking/capacity operations are transactionally safe.
-   [ ] Bangla/Unicode data is stored and displayed correctly.
-   [ ] Secrets are not committed to the repository.
-   [ ] Database migrations can create and update the schema
    reproducibly.
-   [ ] Backup and restore procedure is documented and tested before
    production use.

### Quality and operations

-   [ ] Critical backend and frontend workflows have automated tests.
-   [ ] The main staff workflow works on mobile and desktop browsers.
-   [ ] Errors are understandable and do not leak sensitive information.
-   [ ] A fresh developer can follow the setup documentation to run the
    application.
-   [ ] Deployment configuration and operational responsibilities are
    documented.
-   [ ] Known limitations and unresolved risks are recorded.

### Real-use readiness

Passing the functional checklist does not automatically mean the system
is ready for unrestricted production use. Before a real facility uses it
with real patient data, the team must complete a separate
production-readiness review covering security, privacy, legal
obligations, backups, access control, incident response, hosting and
support.

## 12. Hackathon demonstration acceptance

The hackathon demo should demonstrate the real application, not a
slide-only simulation.

A focused demonstration should show:

1.  An organization and branch already configured.
2.  A facility staff member signing in.
3.  Patient search and registration.
4.  Doctor schedule and appointment capacity.
5.  A scheduled appointment being created.
6.  A walk-in being registered.
7.  Both entries appearing in the unified queue.
8.  A patient being checked in and moved through the queue.
9.  A queue reorder or skip action.
10. The resulting audit history.
11. A brief demonstration that a second organization cannot access the
    first organization's records.

Use realistic but fictional demonstration data. Do not display real
patient information in public demonstrations.

The team must not claim measured reductions in waiting time, improved
health outcomes, national interoperability or successful facility
deployment unless supported by verifiable evidence.

## 13. Scope change control

A feature may enter Phase 1 only if:

1.  It is necessary for a complete and safe core appointment/queue
    workflow, or is required by an approved business rule.
2.  Its user value and acceptance criteria are clear.
3.  Its effect on tenant isolation, privacy, security and data integrity
    is reviewed.
4.  Its implementation does not put the core MVP delivery at
    unreasonable risk.
5.  The change is recorded in the relevant product or architecture
    decision document.

If a feature is not essential to the core workflow, default it to a
later phase.

## 14. Relationship to the initial concept draft

The initial concept draft explored a broader product, including
patient-facing intake, payment integrations, financial settlement,
clinical vitals, identity/insurance capture, consent workflows and
messaging.

Those ideas remain possible future research topics, but they are **not
approved Phase 1 scope**. The MVP scope follows the later approved
product boundaries and Business Rules V1.0, especially the decisions to
keep AMSDP facility-centric, staff-mediated and focused on appointment
and queue operations.

In particular:

-   External payments remain outside AMSDP.
-   Clinical records and vitals are excluded.
-   Patient login and self-service booking are excluded.
-   Automated messaging and pre-visit intake are deferred.
-   The MVP does not claim national interoperability or integration with
    government health identity systems.

## 15. Governing documents

Use these documents together:

1.  `docs/product/AMSDP_Business_Rules_V1.1.md` --- authoritative
    business behavior and approved decisions.
2.  `docs/product/AMSDP_MVP_SCOPE_V1.0.md` --- Phase 1 release boundary
    and acceptance criteria.
3.  Product vision, feature list, scope and architecture documents ---
    supporting context, to be reconciled against the two documents above
    before implementation.

**MVP guiding principle:** Build a small product that genuinely works,
not a large product that mostly exists on paper.

## 16. PQV Scope Addendum (8 November 2026)

Per product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`
(`docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`), and
recorded under the scope-change process in §13:

1. **Public Doctor Queue Display (DQDS)** and **Personal Queue Tracking
   (PQT)** are **Phase 1 (MVP) capabilities**, not later-phase options.
   - PQT requires a cryptographically unguessable tracking token
     (hash-at-rest), appointment-specific tracking page and QR code,
     revocation on consultation start / cancellation / reschedule
     (tokens never reactivated), no-cache responses, and rate limiting of
     public tracking endpoints.
   - DQDS is public, read-only, token-based, PII-free, and strictly
     org/branch-scoped.
2. **Patient notifications via WhatsApp AND SMS** are required,
   organization-configurable channels. Delivery depends on external
   provider availability; AMSDP must not block appointment creation on
   messaging; manual link sharing is the fallback.
3. The six canonical roles and the existing RBAC matrix are **unchanged**.
4. The following remain **excluded**: patient accounts, patient portal,
   patient self-service booking, mandatory mobile application, payments,
   EMR/EHR/clinical records.
5. Features in this addendum are **documented requirements only** — not yet
   implemented. This addendum adjusts MVP Scope §14's "automated messaging
   … deferred" statement for the channel requirement only; pre-visit
   intake and other deferred items remain deferred.
6. **Two-Stage Patient Notifications** are **APPROVED P0 product scope**
   (product-owner, 2026-11-08): appointment confirmation immediately after
   booking + configurable pre-visit reminder (default 10 minutes; 5/10
   minutes practical options); queue-change-aware scheduling;
   cooldown/deduplication; pending reminders cancelled on cancel,
   reschedule or consultation start; no return reminder after check-in; no
   delivery claim unless provider confirms; booking functional without
   messaging. **Provider-dependent for delivery; not implemented.**
   **Missed-Turn Recovery & Queue Repositioning is APPROVED P0/MVP scope**
   (product-owner, 2026-11-09; governed by Business Rules V1.1 §27A).
   Default staff-confirmed action defers the patient to the end of the
   same applicable active queue. Authorized staff or doctors may override
   to any valid position in that same queue, with reason and audit.
   Appointment/time/token/history are preserved; no automatic `NO_SHOW`,
   messaging-based inference, or automated clinical triage. This is a
   required product workflow and is not yet a claim of implementation.


------------------------------------------------------------------------

## 17. V1.1 amendment record — 9 November 2026

The product owner approved limited Missed-Turn Recovery & Queue
Repositioning for the MVP. This amendment adds the explicit workflow to
§5.8 and the PQV/product-scope addendum above. The approved default is
staff-confirmed deferral to the end of the same applicable active queue;
authorized staff or doctors may override to any valid position in that
same queue, with reason and audit. Existing no-show, appointment,
token-preservation, permission, and human-controlled safety rules remain
in force.

V1.0 is retained as the historical baseline. V1.1 is the current
approved MVP scope. Approval of the requirement does not itself certify
that the workflow has been implemented or tested.
