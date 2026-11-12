# AMSDP System Architecture V1.0

**Product:** Appointment Management System for Doctors & Patients
(AMSDP)\
**Document type:** Target system architecture and technical decision
baseline\
**Version:** 1.0 --- revised to adopt microservices from inception\
**Status:** Proposed architecture baseline reflecting the product
owner's selected direction\
**Prepared:** 4 November 2026\
**Primary market:** Bangladesh

**Governing product documents** -
`docs/product/AMSDP_Business_Rules_V1.0.md` -
`docs/product/AMSDP_MVP_SCOPE_V1.0.md`

------------------------------------------------------------------------

## 1. Purpose and authority

This document defines the target architecture for AMSDP and the
technical boundaries that implementation agents must follow.

The selected architecture is **microservices from the beginning**. AMSDP
will be composed of independently deployable business services, each
with a defined responsibility, API contract, data ownership and test
boundary.

The architecture is intended to: - Translate approved product rules and
MVP scope into implementable services. - Enable CrewAI development
agents to work on separate services in parallel against agreed
contracts. - Enforce strict organization/tenant isolation and
branch-level permissions. - Establish independent service and data
ownership. - Define synchronous API and asynchronous event
communication. - Address distributed transactions, failures,
observability and deployment from the start. - Allow services to evolve
and scale independently.

The approved Business Rules V1.0 and MVP Scope V1.0 remain authoritative
for product behavior and release scope. This architecture must not
silently add features excluded from Phase 1.

Where a technical proposal in this document has not yet been approved
through an architecture decision record (ADR), it must be treated as a
proposal for review rather than an already implemented fact.

## 2. Architecture goals

The architecture must support:

1.  A real, usable Phase 1 appointment and queue-management product.
2.  Multiple healthcare organizations operating in one platform with
    strict tenant isolation.
3.  Multiple branches within an organization, with branch-scoped
    permissions and organization-wide patient records where authorized.
4.  Independently developed, tested, deployed and versioned services.
5.  Clear service ownership, API contracts and data ownership.
6.  Reliable booking, capacity, appointment lifecycle, queue and token
    operations across service boundaries.
7.  Bangla/English Unicode support and responsive front-desk workflows.
8.  A manageable initial microservices deployment with explicit
    operational safeguards.
9.  Parallel service development coordinated by the CrewAI AI Factory.
10. Future independent scaling and evolution without uncontrolled
    coupling.

## 3. Architecture style: microservices from inception

### 3.1 Selected approach

**AMSDP will use a microservices architecture from the beginning.**

Each service: - Owns a bounded business capability. - Has its own code
and deployment unit. - Exposes a documented API contract. - Owns its
data and persistence operations. - Can be built, tested, versioned and
deployed independently. - Does not allow other services to read or write
its private database tables directly. - Publishes or consumes events
through defined event contracts where asynchronous integration is
appropriate.

Services may initially run on a single host or a small number of hosts
using Docker Compose or another reviewed deployment mechanism.
Independent deployment boundaries do not require a large Kubernetes
cluster on day one.

### 3.2 Why this direction

The product owner has selected microservices in conjunction with a
development strategy using CrewAI multi-agent capabilities. This enables
development agents to be assigned bounded service responsibilities and
work in parallel, provided that service contracts and shared standards
are established first.

Microservices do not automatically make parallel AI development safe.
Without contract governance, agents can create incompatible APIs,
duplicate data models, inconsistent authorization and fragile
distributed workflows. The AI Factory must therefore manage service
contracts, dependency order, integration tests and human approval.

### 3.3 Microservices are not one agent per service

A service is a runtime and data-ownership boundary. An AI agent is a
development role. These concepts should not be forced into a one-to-one
mapping.

One agent may work on multiple small related services; several agents
may collaborate on one service; and a reviewer agent may review multiple
services. CrewAI task assignments must follow dependencies and ownership
rules.

### 3.4 Initial deployment philosophy

Use independently deployable containers and service configurations, but
keep the infrastructure footprint proportionate to the MVP.

Do not introduce Kubernetes, a service mesh, complex distributed tracing
infrastructure or multiple physical database servers solely for
appearance. Evaluate those technologies when operational requirements
justify them.

## 4. High-level system architecture

``` text
┌───────────────────────────────────────────────────────────────┐
│                         USERS / STAFF                         │
│ Super Admin | Organization Admin | Branch Staff | Other roles │
└───────────────────────────────┬───────────────────────────────┘
                                │ HTTPS
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                      WEB FRONTEND                             │
│                Next.js + TypeScript (proposed)                │
│       Staff workspace | Platform administration              │
└───────────────────────────────┬───────────────────────────────┘
                                │ HTTPS / JSON
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                  API GATEWAY / EDGE ROUTER                    │
│ TLS termination | routing | rate limits | request IDs         │
│ Authentication integration | coarse-grained request controls │
└───────────┬──────────┬──────────┬───────────┬──────────────────┘
            │          │          │           │
            ▼          ▼          ▼           ▼
       Identity     Patient    Doctor     Scheduling
       Service      Service    Service     Service
            │          │          │           │
            ▼          ▼          ▼           ▼
       Identity DB  Patient DB Doctor DB  Scheduling DB

            ┌──────────────┬──────────────┬──────────────┐
            ▼              ▼              ▼              ▼
       Organization   Appointment       Queue          Audit
        Service        Service         Service        Service
            │              │              │              │
            ▼              ▼              ▼              ▼
       Organization    Appointment     Queue DB        Audit DB
          DB              DB

            ┌─────────────────────────────────────────────┐
            │        ASYNCHRONOUS EVENT INFRASTRUCTURE    │
            │ Broker / event transport (technology TBD)  │
            │ Outbox, retries, dead-letter handling      │
            └─────────────────────────────────────────────┘

       Each service owns its database and persistence access.
       Services communicate through APIs and versioned events.
```

This is a logical architecture. The exact gateway, event broker, service
discovery and deployment technologies require explicit decisions.

## 5. Service catalogue and ownership

The following is the proposed Phase 1 service decomposition. It is
deliberately based on business capabilities rather than arbitrary
technical layers.

### 5.1 Identity & Access Service

**Responsibilities** - Staff user identity and credentials. -
Authentication and session/token lifecycle. - Roles and permission
assignments. - Organization and branch membership/scope. - Account
activation and deactivation. - Authentication-related security events.

**Owns** - User identity records. - Credential records. -
Role/permission definitions and assignments. - User membership and scope
records, or authoritative references to organization/branch membership
as decided in the detailed design.

**Does not own** - Patient, doctor, schedule, appointment or queue
data. - Organization business configuration.

**Security requirements** - Authentication establishes identity;
downstream services must enforce authorization for the requested action
and tenant scope. - The service must not become a shortcut that allows
other services to trust arbitrary client-supplied organization IDs.

### 5.2 Organization Service

**Responsibilities** - Organization/tenant lifecycle. - Organization
profile and settings. - Organization status and permitted operational
defaults. - Organization-level configuration within platform limits. -
Organization-level subscription state where required by approved product
rules.

**Owns** - Organization records. - Organization settings and
organization-owned configuration.

**Rules** - Organization is the tenant boundary. - A branch is not a
separate tenant by default. - Organization-wide patient sharing across
branches is permitted subject to authorization.

### 5.3 Branch & Facility Structure Service

**Responsibilities** - Branch records within an organization. - Optional
room and facility structure. - Branch operational settings and
activation. - Branch-scoped configuration.

**Owns** - Branch and room records.

**Rules** - A single-chamber organization must not be forced to
configure unnecessary hierarchy. - Branch staff access must be scoped
according to approved permissions. - Organization membership and branch
scope must be validated through trusted service context/contracts.

### 5.4 Patient Service

**Responsibilities** - Patient registration, search and update. -
Organization-owned patient records. - Duplicate warnings and authorized
correction workflow. - Patient lookup APIs for authorized services.

**Owns** - Patient records and patient-specific identifiers.

**Rules** - Patient records belong to an organization. - Patient records
may be shared across branches of the same organization according to
permissions. - Multiple patients may share a mobile number within one
organization. - Do not automatically merge patients based only on name
or mobile number. - No cross-organization patient matching or
transfer. - Other services store patient identifiers and only the
minimum necessary denormalized display data, if explicitly justified;
Patient Service remains authoritative.

### 5.5 Doctor Service

**Responsibilities** - Facility-local doctor records. - Doctor contact
details and local identifiers. - Doctor-to-branch association. -
Optional room assignment or association.

**Owns** - Doctor records and organization-local doctor identifiers.

**Rules** - Doctor records are organization/facility-local. - Mandatory
fields are name and mobile number. - Doctor ID is unique within its
defined organization context. - Mobile-number uniqueness follows the
approved organization policy, including the platform-controlled
duplicate allowance. - No global doctor identity or automatic
cross-organization matching. - Other services use the Doctor Service
contract to validate doctor references.

### 5.6 Scheduling Service

**Responsibilities** - Doctor availability and schedule
templates/instances. - Operating dates and time ranges. - Time-slot,
serial-based and hybrid appointment model configuration. - Capacity and
blocked periods. - Availability queries and capacity
reservation/validation.

**Owns** - Schedule, availability, capacity and blocked-period records.

**Rules** - Capacity may be configured at the applicable doctor,
schedule, date and appointment-model level within platform limits. -
Scheduling is authoritative for availability and capacity. - Other
services must not query its private database. - Capacity reservation
must be safe under concurrent requests. - Queue reordering must not
mutate booked appointment date/time.

### 5.7 Appointment Service

**Responsibilities** - Appointment creation and retrieval. - Booking
source and appointment lifecycle. - Cancellation and reason capture. -
Rescheduling with a link to the original appointment. -
Same-organization transfer subject to permissions and destination
availability. - Appointment-level confirmation state where used. -
Coordination with Patient, Doctor, Scheduling and Queue services through
their contracts.

**Owns** - Appointment records and appointment lifecycle history.

**Rules** - Staff-mediated booking is the Phase 1 workflow. - Patient
self-booking is excluded. - External payment processing is excluded. -
Appointment statuses follow Business Rules V1.0. - Queue position is
separate from appointment status. - Booking must coordinate safely with
Scheduling and Queue services; it cannot assume a single cross-service
database transaction.

### 5.8 Queue Management Service

**Responsibilities** - Daily operational queues. - Scheduled and walk-in
queue entries. - Walk-in placement policies. - Token/serial generation
and sequence rules. - Queue status transitions and manual ordering. -
Skip, absent, temporarily unavailable and priority operations. - Queue
action history.

**Owns** - Queue entries, queue positions, token sequences and
queue-action records.

**Rules** - Walk-in is an entry source, not a fourth appointment
model. - Scheduled and walk-in patients appear in a unified queue. -
Queue position and appointment date/time are separate. - Token identity
remains stable when position changes. - No-show is staff-confirmed;
elapsed time may flag a potential no-show but cannot automatically
establish it. - Priority is operational and staff-assigned; the system
does not perform clinical triage. - Privileged queue changes are
auditable. - Queue Service is authoritative for token allocation and
queue ordering.

### 5.9 Audit Service

**Responsibilities** - Receive, store and retrieve business audit
events. - Record actor, timestamp, action and relevant before/after
values. - Record reasons where required by business rules. - Enforce
authorized access to audit history.

**Owns** - Audit event records and audit query capabilities.

**Rules** - Ordinary users cannot silently edit or delete audit
events. - Other services publish audit-relevant events through a defined
contract. - Critical audit requirements must not be lost if the Audit
Service is temporarily unavailable. Use transactional outbox or another
reliable delivery pattern for events that must be retained. - Audit
access follows organization and branch permissions. - Avoid unnecessary
patient data in event payloads.

### 5.10 Platform Administration capability

Platform administration may initially be implemented as a separately
deployable service or as a clearly isolated API capability within
Organization/Identity services. The final ownership split must be
recorded in an ADR.

It is responsible for: - Super Admin operations. - Platform-wide limits
and defaults. - Permitted configuration ranges. - Organization
administration controls.

It must invoke other services through their contracts and must not
bypass their business rules or directly modify their databases.

### 5.11 Notification Service --- required capability (PQV 2026-11-08)

Patient notifications via **WhatsApp and SMS** are required,
organization-configurable channels (product decision
`AMSDP-PRODUCT-DECISION-PQV-2026-11-08`). Actual provider delivery is
provider-dependent; appointment creation must never block on messaging;
manual link sharing is the fallback.

Design direction:

- Keep provider-specific logic out of Appointment and Queue services (a
  notification boundary/outbox consuming domain events or explicit
  requests).
- Organization-scoped channel configuration: enable/disable WhatsApp and
  SMS, select from platform-approved providers, per-channel
  enabled/configured/operational state, org-scoped templates within
  platform limits.
- **Secure provider credentials:** encrypted at rest on the backend,
  org-scoped, never in frontend bundles, logs, error responses, or source
  control.
- WhatsApp tracking messages include the appointment-specific PQT tracking
  URL; SMS supports the tracking URL where applicable.
- Track request/delivery outcomes (append-only audit); never silently
  claim delivery.
- Platform Super Admin remains the owner of the provider registry, plan
  limits and defaults; organization admins configure within those bounds
  and never see another organization's settings or secrets.

### 5.11.1 Two-stage notifications and reminder scheduling (2026-11-08)

- **Stage 1 — Appointment Confirmation:** emitted by Appointment Service
  immediately after a successful booking (via notification boundary/outbox).
- **Stage 2 — Pre-Visit Reminder ("Queue Turn Protection"):** a scheduler
  fires a configurable number of minutes (default **10**; options **5/10**)
  before the patient's expected visiting time. It must:
  - recompute against the **current queue state** (respect repo reorder,
    walk-ins and repositioning that shift the estimated turn),
  - apply **cooldown/dedup** so repeated estimate changes do not stack
    multiple reminders, and
  - state in the message that estimates can change.
- **Delivery honesty:** outcome recorded (requested/delivered/failed/
  undelivered); "sent" never becomes "delivered"; no automatic queue
  action from delivery state.
- **Missed-turn repositioning** (proposed, **NOT APPROVED FOR MVP**,
  2026-11-08): queue-side, staff-confirmed, audit-recorded, concurrency-safe
  reorder to end of eligible queue; interacts with no-show/grace policy per
  a future Business Rules amendment — see PQV decision §K. No repositioning
  is implemented or auto-triggered.

## 6. Service communication

### 6.1 Synchronous communication

Use synchronous HTTP/JSON APIs initially for operations that require an
immediate response, unless a reviewed technical decision selects another
protocol.

Examples: - Frontend to API Gateway. - Appointment Service to Scheduling
Service for availability/capacity reservation. - Appointment Service to
Patient Service to validate a patient reference. - Appointment Service
to Doctor Service to validate doctor/branch association. - Queue Service
to validate an appointment reference when necessary.

Internal service calls must: - Authenticate the calling service. -
Authorize the operation and tenant context. - Have explicit timeouts. -
Use bounded retries only for safe/idempotent operations. - Avoid
unbounded call chains. - Propagate correlation/trace identifiers. -
Validate request and response schemas. - Fail clearly when a dependency
is unavailable.

### 6.2 Asynchronous communication

Use versioned domain events for decoupled side effects and workflows
that do not require an immediate response.

Potential event examples: - `OrganizationCreated` - `BranchCreated` -
`PatientRegistered` - `DoctorUpdated` - `ScheduleChanged` -
`AppointmentBooked` - `AppointmentCancelled` -
`AppointmentRescheduled` - `QueueEntryCreated` -
`QueuePositionChanged` - `AppointmentStatusChanged`

These are illustrative names, not final event contracts.

Events must: - Have a stable event ID. - Include event type and schema
version. - Include occurrence timestamp. - Include producer/service
identity. - Include organization and relevant branch context where
appropriate. - Carry only the minimum data required by consumers. -
Avoid credentials, secrets and unnecessary patient information.

Consumers must be idempotent. Duplicate delivery must not create
duplicate appointments, queue entries or audit actions.

### 6.3 Event broker decision

A message broker is part of the proposed microservices architecture, but
the exact technology is **not yet selected**.

Evaluate a lightweight broker such as RabbitMQ or NATS against: -
Delivery guarantees and acknowledgement behavior. - Operational
simplicity. - Python integration. - Retry and dead-letter support. -
Observability. - Deployment and backup requirements.

Do not adopt Kafka unless event volume, replay or streaming requirements
justify its operational cost.

The selected broker and event patterns must be recorded in an ADR before
implementation depends on them.

### 6.4 Transactional outbox and event reliability

A service must not update its database and then publish a critical event
in a way that can silently lose the event if the process crashes between
those actions.

Use the transactional outbox pattern where reliable publication is
required: 1. Update the service-owned business data. 2. Insert an outbox
record in the same local database transaction. 3. A publisher delivers
the event to the broker. 4. Mark the outbox record delivered after
broker acknowledgement. 5. Consumers process idempotently and record
their progress.

Define retry limits, dead-letter handling, monitoring and manual
recovery procedures.

## 7. Distributed workflows and consistency

### 7.1 No shared database transactions

A cross-service workflow cannot rely on a single ACID transaction
spanning all service databases.

Each service owns local transactions. Cross-service operations must use
explicit coordination, compensating actions or asynchronous state
transitions.

### 7.2 Appointment booking workflow

The exact booking orchestration must be detailed before implementation.
A recommended approach is:

1.  Frontend submits a booking request to Appointment Service through
    the gateway.
2.  Appointment Service validates the caller and tenant/branch context.
3.  Appointment Service validates patient and doctor references through
    their service contracts.
4.  Appointment Service requests a capacity reservation from Scheduling
    Service using an idempotent operation and reservation identifier.
5.  Scheduling Service atomically reserves capacity in its own database
    and returns a reservation result.
6.  Appointment Service creates the appointment in its own database and
    records the workflow state.
7.  Appointment Service records an outbox event for downstream
    queue/audit coordination.
8.  Queue Service creates or updates the appropriate queue record
    according to the agreed queue-entry timing.
9.  Services acknowledge events and update workflow state.
10. If a later step fails, the orchestrator performs a defined
    compensation, such as releasing the capacity reservation, or records
    a recoverable pending state for reconciliation.

The team must decide whether queue entry is created at booking time or
check-in time for each appointment model. This detail must follow
Business Rules V1.0 and the queue design; do not infer it from the
architecture diagram.

### 7.3 Saga/process manager

For workflows that span multiple services and require compensation, use
an explicit orchestrated saga/process manager rather than scattered ad
hoc API calls.

The initial Appointment Service may orchestrate the booking process, but
orchestration ownership and state must be documented. Avoid circular
orchestration between services.

### 7.4 Rescheduling and cancellation

-   Preserve the original appointment record and history.
-   Coordinate schedule capacity release/reservation and queue updates
    through explicit commands/events.
-   Make commands idempotent.
-   Define recovery for partial failure.
-   Never silently rewrite the original booking history.

### 7.5 Queue operations

Queue ordering and token allocation should remain local to Queue Service
so the critical ordering operation can be transactional within one
service database.

Appointment lifecycle changes and queue state changes must be
coordinated through explicit APIs/events, with clear source-of-truth
ownership and reconciliation behavior.

## 8. Data architecture and database ownership

### 8.1 Database-per-service principle

Each service owns its data store. Other services must not access its
tables directly.

For the initial deployment, separate logical PostgreSQL databases on one
PostgreSQL server may be used to reduce infrastructure overhead. Each
service must have its own database credentials and permissions limited
to its own database.

A shared PostgreSQL server does **not** mean a shared application
database. The logical ownership and access boundaries must remain
enforceable.

If separate database instances become necessary for availability,
scaling, security or operations, services should be migratable without
changing their public contracts.

### 8.2 Proposed data ownership

  -----------------------------------------------------------------------
  Service                             Authoritative data
  ----------------------------------- -----------------------------------
  Identity & Access                   Users, credentials, roles,
                                      permissions, memberships/scopes

  Organization                        Organizations and organization
                                      settings

  Branch & Facility Structure         Branches and rooms

  Patient                             Patient records and patient
                                      identifiers

  Doctor                              Doctor records and doctor-branch
                                      associations

  Scheduling                          Schedules, availability, capacity
                                      reservations, blocked periods

  Appointment                         Appointments, lifecycle and
                                      rescheduling links

  Queue                               Queue entries, token sequences,
                                      positions and queue actions

  Audit                               Audit events

  Notification (later)                Delivery requests, attempts and
                                      provider outcomes
  -----------------------------------------------------------------------

Platform administration ownership remains an open decision.

### 8.3 Cross-service references

-   Use stable IDs to reference records owned by another service.
-   Validate references through the owning service's API or trusted
    event-derived reference data.
-   Do not use cross-database joins as a substitute for service APIs.
-   If a service keeps a local read model or denormalized copy, it must
    be explicitly treated as a non-authoritative projection with a
    defined update/reconciliation strategy.
-   Never let a denormalized copy become an independent source of truth.

### 8.4 Tenant isolation across services

Organization ID is the tenant boundary for organization-owned records.
Branch ID is an additional operational scope where applicable.

Required controls: 1. Derive user identity and authorized scope from
trusted authentication context. 2. Do not trust client-supplied
organization IDs as proof of access. 3. Validate tenant context at the
gateway and again in each service. 4. Enforce tenant and branch
authorization in service-level application logic. 5. Scope every
tenant-owned database query and mutation. 6. Validate that referenced
patient, doctor, schedule, appointment and branch IDs belong to the same
organization as required. 7. Use database constraints within each
service to protect local relationships. 8. Ensure service-to-service
calls carry authenticated caller identity and verified tenant context.
9. Test list, detail, search, create, update, disable, export and audit
paths for cross-tenant access. 10. Test asynchronous consumers and
background jobs for tenant isolation. 11. Do not disclose another
tenant's data in errors, logs, events or metrics.

PostgreSQL Row-Level Security may be evaluated as additional defense in
depth within each service database. It is not assumed until the
connection/session tenant context, background jobs and privileged access
have been designed and tested.

### 8.5 Database migrations

-   Each service owns and versions its database migrations.
-   A service migration must not modify another service's database.
-   Review generated migrations before applying them.
-   Use backward-compatible expand/contract migrations for independently
    deployed services.
-   Do not deploy a breaking schema change before all consumers have
    migrated.
-   Test upgrade and rollback/recovery procedures.
-   Never rely on manual production schema edits.

## 9. API Gateway and external API design

### 9.1 Gateway responsibilities

The API Gateway/edge router is the frontend's controlled entry point. It
may provide: - TLS termination or integration with the reverse proxy. -
Route forwarding to services. - Request size and rate limits. -
Correlation/request IDs. - Coarse-grained authentication integration. -
Basic request filtering and security headers.

The gateway is not the sole authorization layer. Each service must
enforce its own authorization and tenant boundaries.

### 9.2 External API style

**Recommendation:** Versioned REST/JSON APIs over HTTPS.

Example public paths:

``` text
/api/v1/auth/
/api/v1/platform/organizations/
/api/v1/organizations/{organization_id}/branches/
/api/v1/patients/
/api/v1/doctors/
/api/v1/schedules/
/api/v1/appointments/
/api/v1/queue/
/api/v1/audit/
```

The gateway may route these paths to the relevant services. Exact route
names and ownership belong in the API specification.

### 9.3 API contract requirements

Every service API must document: - Service owner and responsibility. -
Endpoint and method. - Request and response schema. - Authentication
requirements. - Authorization and tenant/branch scope. - Error codes and
semantics. - Idempotency behavior. - Timeout expectations. -
Pagination/filtering where relevant. - Compatibility and deprecation
policy.

Use OpenAPI specifications for HTTP APIs. Keep contracts versioned in
the repository and validate implementation against them.

### 9.4 Internal service APIs

Internal APIs must not be treated as trusted merely because they are on
a private network. Require service authentication, authorization, input
validation, tenant context and bounded network access.

## 10. Authentication and authorization

The final authentication/session mechanism is an implementation
decision. The proposed baseline is secure staff authentication with
server-managed sessions or another reviewed approach suitable for the
Next.js/API Gateway/service topology.

Requirements: - Passwords use a modern password-hashing algorithm and
safe parameters. - Secrets are stored outside source control. - Cookies,
if used, have appropriate Secure, HttpOnly and SameSite attributes. -
State-changing requests are protected against CSRF where cookie-based
authentication is used. - Apply login throttling and safe account
recovery. - Enforce account activation/deactivation. - Apply least
privilege. - Distinguish platform, organization and branch scopes. -
Each service validates the claims and permissions relevant to its
operation. - Service-to-service authentication is required. - Important
account, role and permission changes are auditable. - Production
credentials and real patient data must never be exposed to development
agents.

A detailed role/permission matrix and token/session trust model must be
documented before implementation.

## 11. Audit, logging and observability

### 11.1 Business audit

Audit Service stores business audit records. Other services produce
audit-relevant events through defined contracts.

For important actions, record: - Actor identity. - Organization and
branch context where relevant. - Timestamp. - Action and target
reference. - Previous/new values where relevant. - Reason where required
by business rules.

Audit event delivery must be reliable. Use outbox publication for
critical events. Audit records must not be silently editable or
deletable by ordinary users.

### 11.2 Technical observability

Microservices require cross-service observability from the beginning.

Provide: - Structured logs with service name, environment and
correlation ID. - Distributed trace context propagation across gateway
and service calls. - Metrics for request rates, latency, error rates and
dependency health. - Health and readiness endpoints per service. -
Broker queue depth, retry and dead-letter monitoring. - Database
connection and query health. - Centralized error reporting. - Alerting
for critical service and workflow failures.

Do not put patient names, mobile numbers, credentials, session tokens or
full sensitive request bodies into routine logs, traces or metric
labels.

## 12. Deployment architecture

### 12.1 Initial deployment model

Each service is built and deployed as an independent container. The
frontend, gateway, services, event broker and database infrastructure
may initially be hosted on a small number of machines, subject to
capacity and security review.

Illustrative deployment:

``` text
Internet
   |
HTTPS Reverse Proxy
   |
API Gateway / Edge Router
   |
   +---- Frontend container
   |
   +---- Identity Service container ------ Identity DB
   +---- Organization Service container -- Organization DB
   +---- Branch Service container -------- Branch DB
   +---- Patient Service container ------- Patient DB
   +---- Doctor Service container -------- Doctor DB
   +---- Scheduling Service container --- Scheduling DB
   +---- Appointment Service container -- Appointment DB
   +---- Queue Service container --------- Queue DB
   +---- Audit Service container --------- Audit DB
   |
   +---- Event Broker
   |
   +---- Observability components
```

This is a logical deployment proposal. A separate physical PostgreSQL
server per service is not required initially. Separate logical databases
and service credentials may be hosted on one PostgreSQL server, with
access controls preventing cross-service database access.

### 12.2 Containers and orchestration

-   Docker images are built independently for each service.
-   Docker Compose is a candidate for local development and an initial
    small deployment.
-   Production orchestration must be selected based on availability,
    scaling and operations needs.
-   Kubernetes is not a mandatory Phase 1 dependency.
-   Keep service configuration externalized.
-   Define service health checks, restart behavior, resource limits and
    startup dependencies.
-   Do not rely on container startup order as proof that a dependency is
    ready.

### 12.3 Environments

Maintain separate configurations for: - Local development. - Automated
testing. - Staging/hackathon demonstration. - Production.

Use `.env.example` with placeholders only. Keep secrets outside Git and
limit access to the services that need them.

### 12.4 CI/CD

Each service should have an independently testable and buildable
pipeline, with shared reusable pipeline templates where appropriate.

A pipeline should: 1. Install pinned dependencies. 2. Run formatting and
lint checks. 3. Run static/type checks where applicable. 4. Run unit and
service integration tests. 5. Validate API contracts. 6. Validate
database migrations. 7. Run security/dependency checks. 8. Build the
service image. 9. Run cross-service contract/integration tests in a
controlled environment. 10. Require human approval before production
deployment.

Independent deployment does not remove the need for system-level
compatibility testing.

## 13. Security and privacy architecture

Security must be designed into the gateway, every service, each database
and the event infrastructure.

Minimum requirements: - Tenant and branch isolation in every service. -
Least-privilege user and service authorization. - Secure authentication
and service-to-service identity. - HTTPS at external boundaries and
protected internal communication. - Safe password hashing and secret
management. - Input validation and output encoding. - Rate limiting for
sensitive endpoints. - Restricted database credentials per service. -
Restricted broker permissions per producer/consumer. - Audit history for
sensitive changes. - Data minimization in events, logs and public-facing
surfaces. - Backup protection and access controls. - Documented incident
response and recovery.

Phase 1 does not include EMR/EHR, diagnoses, prescriptions, clinical
notes, vitals or payment credentials. Do not introduce these fields as
speculative future-proofing.

### 13.1 PQV security additions (2026-11-08)

Per product decision `AMSDP-PRODUCT-DECISION-PQV-2026-11-08`:

- **DQDS feeds** are org/branch-scoped, read-only, token-only (no PII).
- **PQT tracking tokens** are cryptographically unguessable, stored
  hashed where practical, revoked on consultation start/cancellation/
  reschedule, never reactivated; tracking responses are no-cache.
- **Provider credentials** for WhatsApp/SMS are encrypted at rest,
  org-scoped, and never exposed to the frontend, logs, or errors;
  organization admins can never read another org's settings or secrets.
- **Rate limiting** applies to login, patient creation, and public
  tracking endpoints (429 with headers).
- Configuration changes and notification events are audited append-only.

A production privacy/security/legal review for Bangladesh and the
selected hosting/provider environment is required before processing real
patient data. This architecture is not legal advice or a certification.

## 14. Reliability, resilience and performance

Microservices introduce partial failures. The architecture must handle
them explicitly.

Required design practices: - Explicit timeouts for every network call. -
Bounded retries with backoff for safe operations. - Idempotency keys for
retried commands that could create records. - Circuit breaking or
equivalent protection where justified. - Graceful degradation for
non-critical dependencies. - Durable outbox/event delivery for critical
events. - Dead-letter handling and operational replay/recovery
procedures. - Reconciliation for workflows that can remain pending after
partial failure. - Database transactions within each service. - No
assumption of a distributed ACID transaction. - Health/readiness checks
and alerting. - Backup and restore for each service database and broker
state as appropriate.

Performance targets and expected concurrent usage must be documented and
tested. Do not make unverified claims about response times, reduced
waiting time or offline support.

## 15. Testing architecture

Testing must occur at service level and system level.

### Service unit tests

-   Domain rules and invariants.
-   Input validation.
-   Authorization policies.
-   State transitions.
-   Capacity and token algorithms.
-   Error and retry behavior.

### Service integration tests

-   API endpoints.
-   Service-owned repositories and database constraints.
-   Migrations.
-   Transaction boundaries.
-   Outbox publication.
-   Consumer idempotency.

### Contract tests

-   Provider API conforms to published OpenAPI/contract.
-   Consumer expectations match provider contracts.
-   Event schemas remain compatible.
-   Breaking changes are detected before deployment.

### Cross-service integration tests

-   Patient registration to appointment booking.
-   Scheduling capacity reservation to appointment creation.
-   Appointment to queue coordination.
-   Walk-in to unified queue.
-   Cancellation/rescheduling and queue consistency.
-   Audit event delivery and reconstruction.
-   Recovery after a downstream service or broker outage.

### Security tests

-   Cross-tenant read/write attempts against every service.
-   Cross-branch access attempts.
-   Role/permission escalation.
-   Identifier substitution.
-   Forged or missing service identity.
-   Unauthorized audit access.
-   Session invalidation after account deactivation.
-   Sensitive-data leakage through logs, events and errors.

### Concurrency and resilience tests

-   Simultaneous bookings against limited capacity.
-   Token sequence allocation under concurrent requests.
-   Concurrent queue reorder/status operations.
-   Duplicate event delivery.
-   Broker outage and recovery.
-   Service timeout and retry behavior.
-   Partial booking workflow failure and compensation.

### End-to-end tests

Automate the core workflows in `AMSDP_MVP_SCOPE_V1.0.md` across the
deployed service environment.

A service is not complete merely because its container starts. It must
pass unit, integration, contract, security and relevant system tests.

## 16. AI-Assisted Development Constraints

Include only these principles:
1. AI development agents must follow the approved Business Rules, MVP Scope and System Architecture.
2. Each agent must work within its assigned microservice boundary.
3. Agents must respect service ownership, API contracts and database boundaries.
4. Cross-service contract changes require review and approval.
5. Security, tenant isolation and automated testing are mandatory.
6. Database migrations, security-sensitive changes and production deployments require human approval.

## 17. Proposed repository organization

The existing repository must be inspected before moving or renaming
files. This is a target proposal, not an instruction to restructure
blindly.

``` text
amsdp/
├── frontend/
│   └── src/
│       ├── app/
│       ├── features/
│       ├── components/
│       └── lib/
├── services/
│   ├── identity/
│   ├── organization/
│   ├── branches/
│   ├── patients/
│   ├── doctors/
│   ├── scheduling/
│   ├── appointments/
│   ├── queue/
│   └── audit/
├── api_gateway/
├── event_infrastructure/
├── ai_factory/
│   ├── agents/
│   ├── tasks/
│   ├── crews/
│   ├── tools/
│   └── workflows/
├── infrastructure/
│   ├── docker/
│   ├── deployment/
│   ├── monitoring/
│   └── scripts/
├── docs/
│   ├── product/
│   ├── architecture/
│   ├── decisions/
│   └── ...
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

The current repository uses `backend/`; do not rename it to `services/`
without inspecting its contents and agreeing a migration plan. The
target layout may instead retain a top-level `backend/services/`
directory. The final structure must support independent service
packages, builds, tests and deployment artifacts.

The `ai_factory/` directory is a development-time system. It must not be
bundled into AMSDP production services.

## 18. Proposed technology baseline

This stack is recommended for evaluation and must be confirmed against
the actual repository, installed dependencies and hosting constraints
before implementation.

  -----------------------------------------------------------------------
  Layer                   Proposed technology     Notes
  ----------------------- ----------------------- -----------------------
  Frontend                Next.js + TypeScript    Staff-facing web
                                                  application

  UI                      Tailwind CSS +          Candidate UI foundation
                          shadcn/ui               

  Service framework       Python + FastAPI        Independently
                                                  deployable APIs

  Database                PostgreSQL              Separate logical
                                                  database per service
                                                  initially

  ORM                     SQLAlchemy              Service-owned
                                                  persistence

  Migrations              Alembic                 Each service owns its
                                                  migrations

  API contracts           OpenAPI                 Versioned HTTP
                                                  contracts

  Event broker            RabbitMQ or NATS        Select after
                                                  evaluation; not yet
                                                  locked

  Containers              Docker                  Independent service
                                                  images

  Local orchestration     Docker Compose          Development and initial
                                                  small deployment
                                                  candidate

  Gateway / proxy         Caddy or Nginx plus     Select explicit roles
                          gateway routing         and avoid duplicate
                                                  responsibilities

  CI                      GitHub Actions          Per-service and
                                                  system-level quality
                                                  gates

  Backend tests           pytest                  Unit, integration and
                                                  contract tests

  Observability           Structured logs,        Exact stack to be
                          metrics and distributed selected
                          traces                  
  -----------------------------------------------------------------------

Do not install, upgrade or replace dependencies merely because they
appear in this proposal. Inspect current files and versions first. Pin
compatible versions and record the decision.

## 19. Architecture decisions summary

  -----------------------------------------------------------------------
  ID                      Decision                Status
  ----------------------- ----------------------- -----------------------
  ADR-001                 Adopt microservices     Product owner selected;
                          architecture from       formal ADR to record
                          inception               

  ADR-002                 Each service has        Foundational
                          independent code, API,  architecture rule
                          deployment and data     
                          ownership               

  ADR-003                 Each service owns its   Proposed implementation
                          database; separate      
                          logical PostgreSQL      
                          databases may share one 
                          server initially        

  ADR-004                 Organization is the     Required by approved
                          tenant boundary; branch product rules
                          is an additional scope  

  ADR-005                 Enforce tenant          Mandatory security rule
                          isolation in every      
                          service, not only at    
                          gateway                 

  ADR-006                 Use versioned REST/JSON Proposed
                          APIs over HTTPS         

  ADR-007                 Use asynchronous events Proposed
                          for decoupled workflows 
                          and reliable side       
                          effects                 

  ADR-008                 Use transactional       Proposed
                          outbox and idempotent   
                          consumers for critical  
                          event delivery          

  ADR-009                 Use explicit            Proposed
                          saga/process            
                          coordination for        
                          multi-service workflows 

  ADR-010                 Deploy each service as  Foundational
                          an independent          architecture rule
                          container               

  ADR-011                 Keep CrewAI AI Factory  Proposed
                          separate from AMSDP     
                          production runtime      

  ADR-012                 Require human approval  Development governance
                          for service contracts,  requirement
                          migrations, security    
                          and production changes  
  -----------------------------------------------------------------------

Formal ADR files must be created for decisions requiring a detailed
rationale and implementation consequences. The status column must be
updated as decisions are approved.

## 20. Open decisions before implementation

Resolve these in dependency order:

1.  Inspect current repository, manifests, dependency versions and
    environment.
2.  Confirm service decomposition and ownership, including whether
    Platform Administration is a separate service.
3.  Define service-to-service authentication and trusted tenant-context
    propagation.
4.  Choose API Gateway/edge routing technology and responsibilities.
5.  Choose event broker (RabbitMQ, NATS or another justified option).
6.  Define event envelope, schema versioning, retries, dead-letter and
    replay policies.
7.  Define service database provisioning and credentials.
8.  Define detailed database schema and service-owned migrations.
9.  Define appointment booking saga, capacity reservation and
    compensation.
10. Define queue creation timing and appointment/queue consistency
    rules.
11. Define authentication/session strategy and permission matrix.
12. Define API conventions, idempotency, timeouts and error contracts.
13. Define observability stack and correlation/trace propagation.
14. Choose deployment orchestration and hosting environment.
15. Define backup/restore, incident response and operational ownership.
16. Define expected workload and measurable performance targets.

Do not ask implementation agents to independently invent these
cross-cutting decisions. Resolve them centrally and publish the
contracts.

## 21. Implementation readiness gates

Broad parallel service implementation may begin when:

-   [ ] Business Rules V1.0 and MVP Scope V1.0 are in the repository and
    reviewed.
-   [ ] This microservices architecture is approved by the product
    owner.
-   [ ] Existing repository and dependencies have been inspected.
-   [ ] Service catalogue and ownership are agreed.
-   [ ] Service dependency graph is reviewed and free of circular
    dependencies.
-   [ ] Tenant isolation and service identity propagation are specified.
-   [ ] API Gateway and internal communication approach are selected.
-   [ ] Event broker and event reliability approach are selected for
    workflows that need events.
-   [ ] Database ownership and provisioning are defined.
-   [ ] Appointment booking saga and capacity reservation behavior are
    specified.
-   [ ] API and event contracts are versioned.
-   [ ] Automated unit, contract, integration and security gates are
    defined.
-   [ ] Human approval points for migrations, security and deployment
    are established.

Agents may work in parallel on independent service scaffolding and
contract tests after the common standards are approved. Cross-service
business workflows should not be implemented until their contracts and
failure behavior are agreed.

## 22. Governing principle

**Build AMSDP as independently deployable microservices from the
beginning. Each service must own a clear business capability, API
contract, data store and test boundary. Use CrewAI agents to develop
services in parallel under centrally governed contracts, integration
rules and human approval gates.**

The architecture must serve the real appointment and queue workflow,
protect patient and tenant data, and remain operationally manageable.
Microservices are a deliberate product architecture decision---not a
reason to ignore distributed-system complexity or skip engineering
discipline.
