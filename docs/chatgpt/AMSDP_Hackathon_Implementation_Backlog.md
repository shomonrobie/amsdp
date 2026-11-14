AMSDP Hackathon Implementation Backlog

Repository: shomonrobie/amsdp
Branch: hackathon-mvp
Inspected commit: c5fc6463c9226406928f8f05042487c7a1084bf9
Target event: Bangladesh E-Health Hackathon & Symposium, 3–5 December 2026
Purpose: Turn the existing AMSDP application into a reliable, professional, demonstrable outpatient operations MVP.

1. Delivery objective

Deliver one coherent, working demonstration using the existing AMSDP application:

A professional public-facing website.

Secure staff login and administrator-controlled account provisioning.

A usable clinic operations application.

A live receptionist-to-doctor outpatient workflow.

A large-screen Digital Queue Display System (DQDS).

A private Personal Queue Tracking (PQT) page accessible by patient-specific link.

A reproducible demonstration environment and reliable rehearsal procedure.

The demonstration must use genuine application workflows, backend services, database persistence and authorization. Prepared demonstration data is acceptable; simulated workflow results are not.

2. Architecture and scope to preserve

Existing architecture

Retain:

Next.js 14 Pages Router, React 18 and JavaScript.

Existing eight FastAPI backend service processes.

Shared PostgreSQL database and SQLAlchemy models.

Existing Alembic migration chain.

JWT staff authentication and server-side permissions.

Existing Next.js API rewrites.

Docker Compose deployment.

Existing shared frontend components and Bangla/English localization.

Existing DQDS, PQT, BanglaNameSense and missed-turn recovery implementations.

Do not introduce a new frontend framework, backend framework, database, authentication system, tenant model or independent patient application.

Product boundaries

AMSDP is a staff-operated outpatient appointment and queue-management platform.

The hackathon MVP must not introduce:

Patient accounts, patient login or patient self-registration.

Patient portal or patient self-booking.

Public doctor directory or public schedules.

EMR, diagnosis, prescription or clinical documentation.

Payment processing or financial transaction records.

Pharmacy, laboratory, inventory or full hospital-management features.

DQDS must remain public and token-only. It must never display patient names, mobile numbers or other patient-identifying information.

PQT must remain private, appointment-specific and account-free.

BanglaNameSense is advisory assistance for Bangla name entry. It is not an AI clinical capability.

Missed-turn recovery is already approved for the MVP. Do not remove or defer it.

SMS/WhatsApp provider delivery is not to be represented as operational until independently verified. Manual tracking-link and QR sharing is an acceptable demonstration fallback.

3. Prioritized implementation backlog

P0 — Release and demonstration blockers

H0. Establish and preserve the working baseline

Priority: P0
Type: Repository and environment safety

Inspect before changing anything:

Local branch, HEAD and remote branch.

Working-tree status.

Tracked modifications and untracked files.

Current database and Docker Compose project state.

Existing local demo scripts and environment files.

Known local work that must be preserved:

frontend/styles/global.css

_tools/

docker-compose.demo.yml

The remote Git tree does not contain docker-compose.demo.yml or the _tools/ scripts referenced by the demo runbook. They may exist in the local working tree.

Acceptance criteria

Existing modifications and untracked files are inventoried.

No unrelated changes are overwritten.

No git reset, git clean, destructive Docker volume operation, branch switch, commit or push occurs without authorization.

Existing demo scripts are inspected before any replacement is considered.

H1. Repair branch-level authorization across queue operations

Priority: P0 — security blocker
Files:

backend/queuing/main.py

backend/queuing/recovery.py

backend/scheduling/main.py

backend/common/auth.py

backend/tests/test_security.py

Relevant queue tests

Confirmed code-review findings

GET /api/v1/queue accepts a branch_id query parameter. When supplied, it filters by that branch without first enforcing the caller's branch authorization.

_scoped_entry_or_404() checks organization ownership but does not check branch ownership.

Queue actions using that helper can therefore lack the branch-scope protection already present in the recovery module.

Queue reorder filters by organization but does not ensure all entries belong to the caller's authorized branch and the same applicable queue.

Queue enqueue and check-in accept branch identifiers in request bodies. These must not be trusted as authorization evidence.

Schedule creation uses auth.organization_id, correctly deriving the tenant from authentication, but accepts branch_id without an equivalent branch-access validation.

Required work

Apply server-side branch authorization consistently to queue reads and mutations.

Derive branch scope from the authenticated user.

Permit organization administrators to operate across their authorized organization's branches.

Ensure branch-scoped users cannot read or modify another branch's entries.

Validate schedule branch and doctor ownership before creating or modifying schedules.

Ensure reorder operations cannot combine unrelated queues.

Preserve the existing non-disclosing 404 behavior for cross-scope records.

Keep authorization enforcement in the backend, not just the frontend.

Acceptance criteria

A branch administrator cannot retrieve another branch's queue by changing a query parameter.

A branch administrator cannot call, cancel, recover, reposition or reorder another branch's queue entries.

A branch administrator cannot create a schedule for another branch.

An organization administrator can operate across permitted branches.

Cross-organization access remains denied.

Every relevant denial is audited.

Automated tests cover each attempted cross-branch access path.

Do not weaken existing permission checks to make the UI work.

H2. Repair the PQT frontend API integration

Priority: P0
Files:

frontend/next.config.js

frontend/pages/track/[token].js

backend/appointment/tracking.py

Confirmed defect

The tracking page requests:

/api/v1/track/{token}

The Next.js configuration currently rewrites:

/track/:path*

to the appointment service, but does not provide the matching /api/v1/track/:path* rewrite.

Consequently, the tracking page's API request does not reach the intended backend endpoint.

Required work

Add the correct API rewrite to the appointment service.

Preserve the existing public browser route /track/[token].

Verify token lookup and response handling.

Verify revoked and unknown tokens return indistinguishable not-found responses.

Verify no-cache headers.

Verify the QR endpoint and tracking URL base.

Confirm the page works on a real browser, not only through static inspection.

Acceptance criteria

/track/{token} loads the actual Next.js tracking page.

/api/v1/track/{token} reaches the appointment service.

A valid token displays the correct appointment and queue information.

A revoked or invalid token does not disclose appointment information.

The page works on a mobile browser.

H3. Complete schedule creation and appointment booking

Priority: P0
Files:

frontend/pages/schedules.js

frontend/pages/appointments.js

backend/scheduling/main.py

backend/appointment/main.py

backend/tests/

Confirmed schedule-creation defect

ScheduleCreate requires:

doctor_id

organization_id

branch_id

The frontend form currently submits only the doctor, slot templates and appointment model. It omits the two other required fields.

The backend derives organization ownership from the authenticated user, which must remain authoritative. The branch must also be validated against the user's authorized scope.

Confirmed booking-workflow gap

The appointments page permits staff to enter a date and time manually. It does not guide the user through the existing schedule availability endpoint.

The scheduling backend already provides:

GET /api/v1/schedules/{schedule_id}/available-slots

Required work

Make schedule creation work with the authenticated organization and selected authorized branch.

Validate doctor and branch ownership on the backend.

Display available slots for the selected doctor, schedule and date.

Allow staff to select an available slot rather than relying on arbitrary time entry.

Connect the selected branch to appointment creation.

Ensure appointment creation assigns the correct branch for organization-level users as well as branch-scoped users.

Preserve the existing server-side capacity enforcement.

Verify schedule effective dates, working days, slot templates and unavailable periods are respected.

Test concurrent booking attempts against the same capacity.

Important additional verification

The booking code performs an active-appointment count before inserting a booking. The approved MVP scope requires concurrent requests not to exceed configured capacity. Verify that the current transaction strategy actually guarantees that requirement under concurrent requests. If it does not, introduce the smallest safe database-level or transactional protection.

Acceptance criteria

An authorized administrator can create a schedule.

A schedule appears in the schedule list.

Staff can retrieve available slots for the selected date.

Staff can book an appointment into an available slot.

A full slot cannot be overbooked.

Concurrent requests cannot exceed configured capacity.

A booking is associated with the correct organization and branch.

Unauthorized branch or doctor identifiers are rejected.

Appointment history and audit events remain intact.

H4. Add the staff-to-patient PQT handoff

Priority: P0
Files:

frontend/pages/appointments.js

frontend/next.config.js

backend/appointment/tracking.py

frontend/pages/track/[token].js

The backend already implements tracking-token issuance, revocation, public tracking data and QR generation.

The appointments page does not yet expose a complete staff-facing tracking workflow.

Required work

Add an authorized staff action to issue a tracking link.

Display the generated link once.

Provide copy-link functionality.

Display or retrieve the QR code.

Provide a permitted revoke action.

Explain when an existing active token cannot be re-exposed.

Allow staff to share the link manually with the patient.

Never expose the stored token hash or other internal tracking data.

Acceptance criteria

A receptionist can:

Open an appointment.

Issue its tracking link.

Copy the link or display its QR code.

Open the link on a separate smartphone.

See the correct appointment-specific tracking information.

Revoke the token when permitted.

No patient account or login is introduced.

H5. Verify and complete the end-to-end outpatient workflow

Priority: P0
Files:

frontend/pages/patients.js

frontend/pages/doctors.js

frontend/pages/schedules.js

frontend/pages/appointments.js

frontend/pages/queue.js

backend/appointment/main.py

backend/queuing/main.py

backend/queuing/recovery.py

Existing functionality includes patient registration, appointments, walk-ins, queue check-in, queue actions, consultation transitions, missed-turn recording and recovery.

Do not rewrite these systems without evidence of a defect.

Required work

Verify this exact workflow:

Receptionist logs in.

Receptionist registers a patient.

Receptionist selects a doctor and branch.

Receptionist creates an appointment.

Receptionist checks the patient in.

Patient receives a queue token.

Queue entry appears in the doctor's queue.

DQDS displays the token.

Patient opens the private PQT link.

Doctor calls the patient.

Doctor starts consultation.

Doctor completes consultation.

Queue and appointment statuses update.

Audit records the important actions.

Also verify walk-in registration and missed-turn recovery.

Acceptance criteria

Every transition follows the approved lifecycle.

The original appointment and token history are preserved.

Missed-turn recovery preserves the appointment identity and token.

Unauthorized roles cannot perform consultation or administrative actions.

Repeated actions cannot create duplicate queue entries.

Database state survives service/container restart.

H6. Complete DQDS presentation and reliability

Priority: P0/P1
Files:

frontend/pages/queue-display/[org]/[branch].js

backend/queuing/display.py

backend/tests/test_dqds.py

frontend/styles/global.css

DQDS already has a public endpoint, polling, Bangla/English labels, error handling and a token-only response.

Required work

Improve the large-screen experience:

Large, readable token numbers.

Clear currently-serving section.

Waiting count.

Doctor-wise grouping.

Organization and branch identity.

Last-updated timestamp.

High contrast and readable typography at TV distance.

Clear empty-queue state.

Visible stale-data/connection-loss state.

Automatic recovery after connectivity returns.

Responsive layout for common TV resolutions.

Additional date verification

The DQDS implementation uses date.today(). Other operational code uses the facility-local operational_today() helper. Verify date behavior at the Bangladesh timezone boundary and use the facility's configured operational date consistently.

Acceptance criteria

A public DQDS URL works without staff login.

Only the intended active organization and branch are displayed.

Patient names, mobile numbers and IDs never appear.

The display refreshes automatically.

Temporary connection failure does not silently present stale information as live.

The board displays the correct facility-local operational date.

H7. Make the demo environment reproducible

Priority: P0
Files and local resources:

docker-compose.yml

docker-compose.demo.yml — currently absent from the remote branch

_tools/init_demo_env.sh — currently absent from the remote branch

_tools/pg_backup.sh — currently absent from the remote branch

_tools/pg_restore_test.sh — currently absent from the remote branch

backend/seed/seed_demo.py

docs/demo/AMSDP_Hackathon_Demo_Runbook.md

.env.example

The runbook describes an isolated demo database and dedicated scripts. Those supporting files are not currently present in the remote Git tree.

Required work

Inspect the existing local scripts before changing them.

Confirm the demo database is isolated from development data.

Confirm seed operations are idempotent.

Confirm demo accounts use environment-provided credentials.

Confirm migrations apply from a clean database.

Confirm backup and restore procedures work against an isolated database.

Confirm the demo stack starts from documented instructions.

Confirm all services become healthy.

Confirm data survives restart.

Ensure the demo can be recreated without depending on undocumented local state.

Do not overwrite or recreate existing local scripts blindly.

Acceptance criteria

A fresh, controlled demo setup can be initialized from the approved instructions without destroying development data or exposing credentials.

P1 — Presentation, usability and onboarding

H8. Run a formal end-to-end rehearsal

Priority: P1, but mandatory before the event.

Test personas:

Receptionist

Doctor

Organization Admin

Assistant

Patient using PQT without an account

Test:

Login and logout.

Patient registration and BanglaNameSense.

Schedule creation.

Appointment booking and capacity enforcement.

Walk-in registration.

Check-in.

Queue operations.

DQDS.

PQT.

Consultation start and completion.

Missed-turn recovery.

Tracking-token revocation.

Cross-tenant and cross-branch denial.

Unauthenticated access.

Persistence after restart.

Use the existing tests first. Add tests for demonstrated gaps.

Test evidence warning

The repository contains backend tests and frontend tests, but the latest documented CI history includes an initial failed runner execution. Previous local test counts must not be represented as a current green CI run.

The older backend/tests/test_e2e.py is documented as stale. Do not use it as proof of a working live demonstration.

H9. Build the public-facing AMSDP website

Priority: P1
Files:

frontend/pages/index.js

New public pages under frontend/pages/

Existing shared styles and components

The current home page is the staff login screen. There is no separate public marketing website.

Required routes

/ — public AMSDP website.

/login — staff login.

/dashboard — authenticated staff application.

/track/[token] — private patient tracking.

/queue-display/[org]/[branch] — public queue display.

Website sections

Hero and product identity.

The outpatient waiting and queue-management problem.

AMSDP overview.

Appointment and clinic operations.

DQDS preview.

PQT patient experience.

Privacy and security principles.

Pilot/clinic interest invitation.

Contact information.

Staff login access.

Use the approved positioning:

AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.

Do not claim measured waiting-time reductions, clinical outcomes, government adoption or successful pilots without evidence.

H10. Add a controlled clinic onboarding interest form

Priority: P1
Type: Public-facing lead capture

The form may collect:

Facility name.

Facility type.

Contact person's name.

Email or phone.

Location.

Number of branches.

Brief expression of interest.

Important boundary

Submitting the form must not automatically create:

An organization/tenant.

A staff account.

A subscription.

An operational clinic workspace.

The request must be reviewed and approved through a controlled onboarding process.

Do not introduce a CRM or third-party service without approval.

H11. Improve staff login and account provisioning

Priority: P1
Files:

frontend/pages/index.js

frontend/pages/staff.js

frontend/components/AppShell.js

backend/identity/routes.py

The existing application has staff login, JWT authentication, role-based permissions and administrator-controlled staff creation.

Required work

Give the login screen a professional, consistent design.

Move login to /login.

Preserve authentication and redirect behavior.

Improve error messages and loading states.

Improve mobile usability.

Make staff identity and facility context clear.

Improve account provisioning and staff status management.

Make branch assignment clear.

Provide authorized account activation/deactivation controls where supported by existing APIs.

Ensure role assignment remains restricted to authorized administrators.

No public staff signup and no patient signup.

H12. Correct dashboard semantics and improve consistency

Priority: P1
Files:

frontend/pages/dashboard.js

backend/appointment/dashboard.py

Shared UI components

Relevant localization files

Confirmed dashboard issue

The frontend maps the waiting card to today.checked_in. The backend separately returns in_queue and queue_length.

The correct metric must be selected according to the intended meaning of the card. Do not simply substitute a number without defining what it represents.

Required work

Correct the waiting metric.

Verify all dashboard labels against backend definitions.

Add only metrics supported by real backend data.

Improve loading, empty and error states.

Improve consistency across patient, doctor, schedule, appointment, queue, staff, branch and audit screens.

Reuse existing AppShell, DataTable, Modal, ConfirmDialog, StatusBadge and alert components.

Preserve Bangla/English behavior.

4. Explicitly deferred work

Do not allow these items to displace the hackathon-critical backlog:

Real SMS/WhatsApp provider integration.

Advanced analytics and reporting.

FHIR integration and government identity integrations.

National deployment infrastructure.

EMR and clinical documentation.

Digital prescriptions.

Payments.

Patient self-service.

Telemedicine.

Pharmacy and laboratory management.

These may be discussed as future roadmap capabilities, not presented as completed MVP features.

5. Recommended implementation sequence

The implementation should proceed in small, reviewable batches.

Order

Work item

Exit condition

1

H0 — Baseline preservation

Existing local work inventoried and protected

2

H1 — Branch authorization

Cross-branch tests pass

3

H2 — PQT routing

Tracking page and API work in browser

4

H3 — Schedule and booking

Staff can create a schedule and book available capacity

5

H4 — PQT handoff

Staff can issue and share a tracking link

6

H5 — Outpatient workflow

Complete receptionist-to-doctor workflow succeeds

7

H6 — DQDS

TV display works reliably and exposes no PII

8

H7 — Demo environment

Demo can be initialized and restored reproducibly

9

H8 — Rehearsal

All mandatory scenarios pass

10

H9–H12 — Presentation and usability

Website and staff application are ready for judges

After each batch:

Inspect the relevant approved documents.

Inspect existing implementation.

Identify the smallest safe change.

Document affected files, APIs, models and permissions.

Implement only that batch.

Run relevant tests.

Verify actual behavior where possible.

Report exact results and remaining blockers.

Stop for review before moving to the next batch.

6. Repository governance and unresolved documentation issue

The current repository contains an authority-reference inconsistency:

.clinerules still references older V1.0 business-rule and MVP-scope paths.

Approved V1.1 business rules and scope documents are present at the repository's docs/ level.

The V1.1 scope document itself still contains a reference to Business Rules V1.0.

The approved Master Feature List V2.5 is present and active.

Use the approved product decisions and V1.1 business rules for implementation requirements, but do not silently rewrite owner-controlled documents or .clinerules as part of this backlog. Resolve the authority-reference corrections through the appropriate owner approval process.

The V2.5 reconciliation proposal is a proposal, not authorization to apply its patches.

7. Evidence and reporting requirements

Every work item must use the repository's evidence vocabulary:

IMPLEMENTED: Code exists and is reachable.

TESTED: Named tests pass in the current tree.

VERIFIED: Independent runtime, browser, API or database evidence confirms behavior.

ACCEPTED: Product owner has approved the result.

DEFERRED: Deliberately postponed.

BLOCKED: Cannot proceed without a decision or dependency.

ABSENT: Capability does not exist.

OUT OF SCOPE: Explicitly excluded.

Do not claim a feature is verified merely because a component or endpoint exists.

Do not claim that the live demo environment, patient tracking page, provider messaging or government integration works until its behavior has been independently tested.

Every implementation report must include:

Work item ID.

Root cause or objective.

Files changed.

API/model/permission impact.

Tests executed and exact results.

Runtime/browser verification, if performed.

Remaining issues.

Governance and scope compliance.

8. Final hackathon acceptance gate

AMSDP is ready for the hackathon demonstration only when:

Staff can log in.

Staff accounts are administrator-provisioned.

Patient registration works.

BanglaNameSense works as advisory name-entry assistance.

Doctors and schedules can be configured.

Appointment booking uses real availability and capacity enforcement.

Walk-in registration works.

Queue check-in and management work.

Missed-turn recovery works.

DQDS works on a large display.

DQDS exposes no patient-identifying information.

Staff can issue and share a PQT link.

PQT works on a separate smartphone.

Consultation start and completion work.

Audit history is retained.

Branch and tenant access restrictions pass.

Demo data persists after restart.

The demo environment can be initialized reproducibly.

The public website is present.

The complete demonstration has been rehearsed.

Release principle: A smaller, fully working and independently demonstrated outpatient workflow is more valuable than a larger collection of unfinished features.
