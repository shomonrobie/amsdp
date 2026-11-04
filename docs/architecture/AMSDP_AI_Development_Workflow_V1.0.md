# AMSDP AI Development Workflow V1.0

**Document ID:** AMSDP-AIFA-WF-001\
**Version:** 1.0\
**Status:** Proposed workflow baseline for review\
**Date:** 4 November 2026\
**Project:** Appointment Management System for Doctors & Patients
(AMSDP)\
**Parent documents:** -
`docs/architecture/AMSDP_AI_Factory_Architecture_V1.0.md` -
`docs/architecture/AMSDP_AI_Agent_Specification_V1.0.md`

------------------------------------------------------------------------

## 1. Purpose

This document defines how the AMSDP AI Factory uses CrewAI agents to
move work from an approved requirement to design, implementation,
verification, review, and release preparation.

It specifies:

-   workflow stages and their entry/exit criteria;
-   agent assignment and collaboration;
-   task dependencies and handoffs;
-   approval and stop gates;
-   parallel and sequential execution rules;
-   defect, change, and failure workflows;
-   required artifacts and evidence;
-   the minimum practical implementation sequence for the AI Factory.

The workflow applies to the development of AMSDP, which is an approved
microservices-based application. CrewAI agents are development-time
workers; they are not AMSDP runtime microservices.

## 2. Governing rules

Every workflow must follow these principles:

1.  Approved product and architecture documents are the source of truth.
2.  No implementation starts without a bounded task and testable
    acceptance criteria.
3.  Architecture, data ownership, API contracts, and security boundaries
    are explicit before dependent implementation.
4.  Every task has one accountable owner.
5.  Agents work only within their assigned scope and permissions.
6.  Cross-service work is coordinated through approved contracts, not
    direct database coupling.
7.  Tests and checks must actually run before results are reported.
8.  Independent verification is required for completed implementation.
9.  Human approval is required for specified product, architecture,
    security, migration, merge, and release decisions.
10. Production operations and real patient data are outside routine
    agent authority.
11. All durable decisions, task outcomes, and artifacts are recorded in
    the repository or approved run store.
12. When requirements conflict or material information is missing, the
    workflow pauses rather than guessing.

### 2.1 Source-of-truth hierarchy

Use this order:

1.  Explicit project-owner decisions recorded in the repository.
2.  `docs/product/AMSDP_Business_Rules_V1.0.md`
3.  `docs/product/AMSDP_MVP_SCOPE_V1.0.md`
4.  `docs/architecture/AMSDP_System_Architecture_V1.0.md`
5.  Approved service specifications, API specifications, database
    designs, and ADRs.
6.  `docs/architecture/AMSDP_AI_Factory_Architecture_V1.0.md`
7.  `docs/architecture/AMSDP_AI_Agent_Specification_V1.0.md`
8.  This workflow document and other approved AI Factory documents.
9.  Agent-generated proposals and assumptions.

If approved sources conflict, create a decision request and block the
affected work.

------------------------------------------------------------------------

## 3. Workflow overview

``` text
PROJECT OWNER / APPROVED BACKLOG
              |
              v
       1. TASK INTAKE
              |
              v
    2. CONTEXT VALIDATION
              |
              v
   3. REQUIREMENTS ANALYSIS
              |
              v
      4. ARCHITECTURE IMPACT
              |
              v
      5. DESIGN & CONTRACTS
              |
              v
      HUMAN DESIGN APPROVAL
              |
              v
       6. IMPLEMENTATION
              |
              v
       7. DEVELOPER SELF-CHECK
              |
              v
      8. INDEPENDENT QA REVIEW
              |
              v
       9. SECURITY REVIEW
       (when applicable)
              |
              v
       10. HUMAN REVIEW
              |
              v
        11. MERGE / CI
              |
              v
      12. RELEASE READINESS
              |
              v
      HUMAN DEPLOYMENT APPROVAL
              |
              v
        13. RELEASE / VERIFY
              |
              v
          TASK CLOSED
```

Not every task needs a new architecture design. The orchestrator may use
a shorter approved path for low-risk documentation, isolated bug fixes,
or routine refactoring. It must not skip a gate that is relevant to the
change.

### 3.1 Workflow types

  -----------------------------------------------------------------------
  Workflow ID             Workflow                Use
  ----------------------- ----------------------- -----------------------
  WF-01                   Requirement-to-Design   New feature or material
                                                  behavior change

  WF-02                   Service Implementation  Approved service-level
                                                  feature

  WF-03                   Frontend Delivery       Approved user interface
                                                  workflow

  WF-04                   Defect Resolution       Reproducible bug or
                                                  regression

  WF-05                   Architecture Decision   Service boundary,
                                                  integration, or
                                                  platform change

  WF-06                   Database Change         Schema, constraint,
                                                  index, or migration
                                                  work

  WF-07                   Security Review         Security-sensitive
                                                  change or scheduled
                                                  review

  WF-08                   Cross-Service           Workflow spanning
                          Integration             multiple microservices

  WF-09                   Release Readiness       Prepare an approved
                                                  change for release

  WF-10                   Documentation Update    Documentation changes
                                                  based on approved
                                                  decisions or verified
                                                  implementation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Standard workflow task record

Every workflow begins with a validated task record.

### 4.1 Required fields

``` yaml
task_id: "AMSDP-EXAMPLE-001"
title: "Short task title"
workflow_id: "WF-01"
task_type: "feature"
priority: "normal"
status: "PROPOSED"

requester: "project_owner_or_approved_backlog"

source_documents:
  - "docs/product/AMSDP_Business_Rules_V1.0.md"
  - "docs/product/AMSDP_MVP_SCOPE_V1.0.md"

affected_services: []

scope:
  included: []
  excluded: []

acceptance_criteria: []

dependencies: []

assigned_agent: null
supporting_agents: []

required_approvals: []

expected_artifacts: []

stop_conditions:
  - "Conflicting approved requirements"
  - "Missing required design or contract"
  - "Potential tenant-isolation weakness"
  - "Unapproved destructive or production operation"
```

This is a conceptual record schema. The factory implementation should
validate it and may add fields without removing the required meaning.

### 4.2 Intake validation

The orchestrator checks:

-   task ID is unique;
-   title and task type are present;
-   scope is bounded;
-   source documents exist;
-   acceptance criteria are testable or explicitly marked as needing
    refinement;
-   affected service is known when implementation is requested;
-   dependencies and required approvals are identified;
-   no prohibited production or patient-data action is requested.

Invalid tasks are returned for clarification. The orchestrator must not
silently create missing requirements.

------------------------------------------------------------------------

## 5. Workflow state machine

Use explicit states so that an agent cannot skip from request to
completion.

``` text
PROPOSED
   |
   v
INTAKE_VALIDATION
   |
   +---- invalid ----> NEEDS_CLARIFICATION
   |
   v
CONTEXT_VALIDATION
   |
   +---- conflict ----> BLOCKED
   |
   v
READY_FOR_ANALYSIS
   |
   v
ANALYSIS
   |
   v
DESIGN_REQUIRED? ---- yes ----> DESIGN
   |                              |
   no                             v
   |                       HUMAN_DESIGN_APPROVAL
   |                              |
   +------------------------------+
   |
   v
READY_FOR_IMPLEMENTATION
   |
   v
IN_PROGRESS
   |
   v
SELF_CHECK
   |
   v
INDEPENDENT_REVIEW
   |
   +---- defects ----> CHANGES_REQUESTED
   |                       |
   |                       +----> IN_PROGRESS
   |
   v
HUMAN_REVIEW
   |
   +---- rejected ----> CHANGES_REQUESTED
   |
   v
APPROVED_FOR_MERGE
   |
   v
MERGED
   |
   v
RELEASE_READINESS
   |
   v
AWAITING_DEPLOYMENT_APPROVAL
   |
   v
RELEASED
   |
   v
CLOSED
```

Additional states:

-   `BLOCKED`: work cannot safely proceed.
-   `NEEDS_CLARIFICATION`: requester must provide missing information.
-   `CANCELLED`: task was explicitly cancelled.
-   `FAILED`: workflow failed and cannot continue without intervention.
-   `NOT_APPLICABLE`: an optional stage was reviewed and formally
    determined not to apply.

### 5.1 State transition authority

  -----------------------------------------------------------------------
  Transition                          Allowed actor
  ----------------------------------- -----------------------------------
  Proposed → Intake Validation        Orchestrator

  Intake Validation → Needs           Orchestrator
  Clarification

  Context Validation → Blocked        Any agent may raise; orchestrator
                                      records

  Analysis → Design                   Orchestrator after analysis output

  Design → Human Design Approval      Orchestrator

  Human Design Approval → Ready for   Human approver
  Implementation

  In Progress → Self Check            Assigned implementation agent

  Self Check → Independent Review     Orchestrator after evidence
                                      validation

  Independent Review → Changes        QA/Security reviewer or
  Requested                           orchestrator

  Human Review → Approved for Merge   Authorized human reviewer

  Approved for Merge → Merged         Approved Git/repository process

  Release Readiness → Awaiting        Orchestrator after required checks
  Deployment Approval

  Awaiting Deployment Approval →      Authorized human operator
  Released

  Released → Closed                   Orchestrator after verification
                                      evidence
  -----------------------------------------------------------------------

Agents cannot grant human approvals or mark a protected merge/deployment
complete on behalf of an authorized person.

------------------------------------------------------------------------

## 6. WF-01 --- Requirement-to-Design workflow

### Purpose

Turn an approved product need into a traceable, implementation-ready
design package.

### Trigger

A new feature, workflow, or material change is requested.

### Agents

-   Primary: Product Analyst (A01)
-   Supporting: System Architect (A02), Service Architect (A03),
    Database Architect (A04), API Contract Designer (A05), QA Engineer
    (A08), Security Reviewer (A09)
-   Approver: Human project owner; architecture/security reviewers as
    applicable

### Sequence

#### Step 1 --- Product analysis

Product Analyst:

1.  Reads relevant approved Business Rules and MVP Scope.
2.  Identifies user roles and workflow.
3.  Drafts user stories and acceptance criteria.
4.  Identifies included and excluded behavior.
5.  Identifies permissions and audit requirements.
6.  Labels any assumptions and open questions.
7.  Produces requirement traceability.

**Output:** Product Requirements Package.

#### Step 2 --- Architecture impact

System Architect:

1.  Identifies affected microservices.
2.  Checks service ownership and dependencies.
3.  Determines whether the change is local or cross-service.
4.  Identifies API/event and data ownership impacts.
5.  Identifies architectural decisions requiring approval.

**Output:** Architecture Impact Assessment.

#### Step 3 --- Service design

For each affected service, Service Architect:

1.  Defines responsibilities and exclusions.
2.  Defines owned data and referenced data.
3.  Describes operations and service dependencies.
4.  Identifies authorization and tenant/branch context.
5.  Defines failure and observability expectations.

**Output:** Service Design Specification(s).

#### Step 4 --- Data and contract design

Database Architect:

-   produces schema and constraint proposal;
-   identifies indexes and concurrency rules;
-   prepares migration plan if required.

API Contract Designer:

-   produces API/event contracts;
-   defines request, response, errors, authorization, and idempotency;
-   identifies compatibility impact.

**Output:** Data Design and Contract Package.

#### Step 5 --- Test and security planning

QA Engineer:

-   maps acceptance criteria to test scenarios;
-   identifies boundary, concurrency, and regression cases.

Security Reviewer:

-   reviews authorization, tenant boundaries, sensitive data, and audit
    implications.

**Output:** Test Strategy and Security Review Notes.

#### Step 6 --- Human design approval

The human reviewer receives the complete design package and decides
whether it is approved, rejected, or returned for revision.

**Exit criteria:**

-   requirement and scope are clear;
-   affected services are identified;
-   data ownership and contracts are defined;
-   acceptance criteria are testable;
-   required architecture/security decisions are approved;
-   implementation tasks can be bounded.

No dependent implementation begins before required design approvals.

------------------------------------------------------------------------

## 7. WF-02 --- Service Implementation workflow

### Purpose

Implement one approved feature within one microservice.

### Trigger

An approved service design and implementation task are available.

### Agents

-   Primary: Backend Developer (A06)
-   Supporting: API Contract Designer (A05), Database Architect (A04),
    QA Engineer (A08), Security Reviewer (A09), Technical Writer (A11)
-   Approver: Human reviewer

### Preconditions

-   service specification approved;
-   API/event contract approved;
-   database design/migration approved where relevant;
-   acceptance criteria available;
-   working branch/worktree assigned;
-   task scope and file permissions set.

### Sequence

1.  Orchestrator creates an isolated work area.
2.  Backend Developer reads the approved inputs.
3.  Developer prepares a short implementation plan.
4.  Developer implements only the assigned service behavior.
5.  Developer adds or updates unit tests.
6.  Developer runs lint, type, unit, and relevant contract checks.
7.  Developer updates service documentation.
8.  Developer submits a diff summary and actual test results.
9.  Orchestrator checks task scope and required artifacts.
10. QA Engineer performs independent verification.
11. Security Reviewer reviews security-sensitive changes.
12. Human reviewer inspects the diff and evidence.

### Required outputs

-   source code changes;
-   tests;
-   migration files only when authorized;
-   documentation updates;
-   test execution evidence;
-   change summary;
-   known limitations.

### Exit criteria

-   acceptance criteria pass;
-   tests and quality gates pass or exceptions are explicitly approved;
-   no unauthorized cross-service changes;
-   tenant and authorization behavior is tested where relevant;
-   required reviews are complete;
-   human reviewer approves merge.

------------------------------------------------------------------------

## 8. WF-03 --- Frontend Delivery workflow

### Purpose

Implement a user-facing workflow against approved APIs.

### Agents

-   Primary: Frontend Developer (A07)
-   Supporting: Product Analyst (A01), API Contract Designer (A05), QA
    Engineer (A08), Security Reviewer (A09), Technical Writer (A11)
-   Approver: Human reviewer

### Preconditions

-   user story and acceptance criteria approved;
-   API contract available;
-   role/permission behavior documented;
-   UI and localization expectations defined.

### Sequence

1.  Product Analyst confirms workflow and acceptance criteria.
2.  API Contract Designer confirms endpoint and error behavior.
3.  Frontend Developer implements the workflow.
4.  Developer handles loading, empty, validation, success, and error
    states.
5.  Developer supports responsive layouts and Bangla/English where
    required.
6.  Developer adds component/workflow tests.
7.  QA Engineer independently tests the workflow.
8.  Security Reviewer checks sensitive display/access behavior when
    relevant.
9.  Technical Writer updates relevant usage documentation.
10. Human reviewer approves the change.

### AMSDP-specific checks

When relevant:

-   staff-mediated booking remains the approved MVP interaction model;
-   UI visibility is not treated as backend authorization;
-   queue status and appointment status are distinct;
-   queue reorder does not silently change appointment date/time;
-   public queue display does not expose patient personal information;
-   estimated reporting/waiting times are not shown as guarantees;
-   no unapproved payment or clinical features are introduced.

### Exit criteria

The user workflow works against the approved contract, required tests
pass, responsive/localization behavior is verified, and human review is
complete.

------------------------------------------------------------------------

## 9. WF-04 --- Defect Resolution workflow

### Purpose

Investigate and correct a defect without introducing unrelated behavior
changes.

### Trigger

A reproducible defect, failed test, regression, or verified production
issue is reported.

### Agents

-   Primary: QA Engineer (A08) for triage, or relevant developer for an
    already isolated defect
-   Supporting: relevant Backend/Frontend Developer, System Architect if
    cross-service, Security Reviewer if security-related
-   Approver: Human reviewer

### Sequence

#### Step 1 --- Defect intake

Record:

-   defect ID;
-   expected behavior;
-   actual behavior;
-   reproduction steps;
-   environment;
-   affected version/commit;
-   severity and impact;
-   synthetic data or sanitized evidence.

Do not include real patient data or secrets.

#### Step 2 --- Triage

QA Engineer classifies:

-   reproducible / not reproducible;
-   regression / existing defect;
-   local service / cross-service;
-   functional / data integrity / security / performance / usability;
-   severity and urgency.

If the defect suggests a tenant-isolation or data exposure issue,
escalate immediately to Security Reviewer and human owner.

#### Step 3 --- Root-cause investigation

The relevant developer inspects the code and tests. System Architect
joins if the cause involves service boundaries, contracts, or
distributed workflow behavior.

#### Step 4 --- Fix proposal

The developer provides:

-   root cause;
-   proposed minimal correction;
-   affected files/services;
-   regression test plan;
-   migration or data repair implications.

Human approval is required if the fix changes business rules,
architecture, security policy, or stored data in a material way.

#### Step 5 --- Implementation and verification

1.  Implement the bounded fix.
2.  Add a regression test.
3.  Run affected tests and relevant broader suite.
4.  QA reproduces the original scenario and verifies the fix.
5.  Security Reviewer retests security defects.
6.  Human reviewer approves the change.

### Exit criteria

The original defect is no longer reproducible, regression coverage
exists, relevant quality gates pass, and any data or security risk is
addressed.

------------------------------------------------------------------------

## 10. WF-05 --- Architecture Decision workflow

### Purpose

Evaluate a change to system architecture, service boundaries,
integration patterns, or platform design.

### Trigger

A proposal affects one or more of:

-   microservice boundaries;
-   service ownership or dependencies;
-   API gateway;
-   event broker or communication pattern;
-   database ownership;
-   consistency model;
-   authentication/authorization architecture;
-   deployment topology;
-   observability or resilience strategy.

### Agents

-   Primary: System Architect (A02)
-   Supporting: Service Architect(s) (A03), Database Architect (A04),
    API Contract Designer (A05), Security Reviewer (A09), DevOps
    Engineer (A10)
-   Approver: Human project owner

### Sequence

1.  Record the architectural problem and constraints.
2.  Identify affected services and existing decisions.
3.  Prepare at least one viable option; include alternatives when
    useful.
4.  Compare trade-offs: complexity, reliability, security, cost,
    maintainability, and migration impact.
5.  Review data ownership and cross-service implications.
6.  Review security and operational impact.
7.  Produce an ADR proposal.
8.  Obtain human approval.
9.  Update architecture and related specifications.
10. Create implementation tasks only after approval.

### Exit criteria

An explicit human decision is recorded, affected documents are updated,
and implementation work is traceable to the decision.

------------------------------------------------------------------------

## 11. WF-06 --- Database Change workflow

### Purpose

Safely design, implement, and verify a service-owned database change.

### Agents

-   Primary: Database Architect (A04)
-   Supporting: Service Architect (A03), Backend Developer (A06), QA
    Engineer (A08), Security Reviewer (A09)
-   Approver: Human reviewer; project owner for material data-risk
    changes

### Sequence

1.  Identify the service that owns the data.
2.  Define the business reason and affected records.
3.  Design schema, constraints, indexes, and data lifecycle.
4.  Check tenant and branch isolation.
5.  Assess lock duration, concurrency, data volume, and compatibility.
6.  Prepare forward migration and recovery/rollback plan.
7.  Test migration on a disposable database with synthetic fixtures.
8.  Verify existing application behavior and contract compatibility.
9.  Review destructive or irreversible steps with a human.
10. Implement migration in the assigned service.
11. Run migration and regression tests locally/CI.
12. Obtain required human approval before merge or release.

### Mandatory stop conditions

-   migration may delete or irreversibly alter data;
-   data ownership is unclear;
-   cross-service table access is proposed;
-   tenant scoping is not preserved;
-   production data is requested for routine testing;
-   no safe recovery plan exists for a high-risk migration.

### Exit criteria

Migration is tested, ownership and tenant rules are preserved, risk is
documented, and required approvals are recorded.

------------------------------------------------------------------------

## 12. WF-07 --- Security Review workflow

### Purpose

Independently assess a change or service for security and privacy risks.

### Trigger

A security-sensitive change, new service, new data flow,
authentication/authorization change, dependency addition, or scheduled
review.

### Agents

-   Primary: Security Reviewer (A09)
-   Supporting: relevant developer, System Architect, QA Engineer,
    DevOps Engineer
-   Approver: Human project owner for risk acceptance

### Sequence

1.  Define review scope and assets.
2.  Load relevant architecture, service, API, and data-flow documents.
3.  Inspect code/configuration and test evidence.
4.  Check authentication and authorization.
5.  Check tenant and branch scoping.
6.  Check input validation and output exposure.
7.  Check secrets, logs, errors, dependencies, and network
    configuration.
8.  Check auditability and sensitive-data handling.
9.  Run approved local security tests using synthetic data.
10. Record findings with severity, evidence, and remediation.
11. Developer fixes findings.
12. Security Reviewer retests.
13. Human owner decides any residual risk that requires acceptance.

### Finding format

Each finding must include:

-   finding ID;
-   severity;
-   affected service/component;
-   description;
-   impact;
-   evidence and reproduction steps;
-   recommended remediation;
-   owner;
-   status;
-   retest result.

### Exit criteria

No unresolved critical/high finding remains without explicit human risk
disposition. A reviewer cannot waive a finding on behalf of the project
owner.

------------------------------------------------------------------------

## 13. WF-08 --- Cross-Service Integration workflow

### Purpose

Implement and verify a business workflow that spans multiple AMSDP
microservices.

### Trigger

An approved feature requires more than one service to collaborate.

### Agents

-   Primary coordinator: System Architect (A02)
-   Supporting: relevant Service Architect(s), API Contract Designer
    (A05), Backend Developer(s) (A06), QA Engineer (A08), Security
    Reviewer (A09), DevOps Engineer (A10)
-   Approver: Human architecture reviewer and project owner as
    applicable

### Preconditions

-   affected services identified;
-   each service's data ownership explicit;
-   API/event contracts approved;
-   workflow consistency and failure behavior documented;
-   task dependencies mapped.

### Sequence

1.  System Architect prepares the service interaction map.
2.  API Contract Designer finalizes interfaces and event schemas.
3.  Each service receives a separate bounded implementation task.
4.  Orchestrator schedules work according to dependencies.
5.  Service agents implement independently in isolated work areas.
6.  Contract tests validate each service boundary.
7.  Integration environment runs the end-to-end workflow.
8.  QA tests success, failure, retry, timeout, and duplicate-delivery
    cases where applicable.
9.  Security Reviewer tests cross-service authorization and tenant
    propagation.
10. System Architect reviews integration behavior.
11. Human reviewer approves the combined change.

### Required integration checks

-   no direct access to another service's private database;
-   tenant context is propagated and revalidated;
-   retries do not create duplicate business operations;
-   timeouts and partial failures are handled;
-   event consumers are idempotent where required;
-   observability can correlate the workflow;
-   failure and compensation behavior is documented where relevant.

### Exit criteria

All service contracts and integration tests pass, cross-service behavior
is documented, and human approval is complete.

------------------------------------------------------------------------

## 14. WF-09 --- Release Readiness workflow

### Purpose

Prepare an approved set of changes for controlled release.

### Agents

-   Primary: DevOps Engineer (A10)
-   Supporting: QA Engineer (A08), Security Reviewer (A09), Technical
    Writer (A11), relevant service owners
-   Approver: Authorized human operator

### Sequence

1.  Confirm target version and included commits.
2.  Confirm all changes are merged through the approved process.
3.  Verify CI results.
4.  Verify database migration sequence and recovery plan.
5.  Verify configuration and secret references.
6.  Verify health checks and observability.
7.  Verify security findings and dependency scans.
8.  Confirm backup/recovery arrangements where applicable.
9.  Prepare release notes and deployment checklist.
10. Prepare rollback plan and verification steps.
11. Present release package to human operator.
12. Wait for explicit deployment approval.
13. Human operator executes approved deployment.
14. Verify service health and key workflows.
15. Record release result and close or reopen defects.

### Prohibited

The AI Factory must not autonomously deploy to production, modify
production infrastructure, or access production patient data.

### Exit criteria

Release artifacts and evidence are complete, deployment is
human-authorized, and post-release verification is recorded.

------------------------------------------------------------------------

## 15. WF-10 --- Documentation Update workflow

### Purpose

Keep documentation synchronized with approved decisions and verified
implementation.

### Agents

-   Primary: Technical Writer (A11)
-   Supporting: task owner and relevant specialist
-   Approver: Human reviewer when documentation changes an approved
    baseline

### Sequence

1.  Identify the source of the change.
2.  Confirm whether the source is approved or merely proposed.
3.  Inspect implementation diff and test evidence when documenting
    implemented behavior.
4.  Update only affected documentation.
5.  Preserve terminology and document hierarchy.
6.  Validate paths, commands, examples, and links where practical.
7.  Submit a summary and references.
8.  Obtain human approval for baseline changes.

### Exit criteria

Documentation accurately represents approved decisions or verified
behavior. Proposed or unverified content is clearly labeled.

------------------------------------------------------------------------

## 16. Parallel execution strategy

Parallel execution is permitted only when dependencies and file
ownership are understood.

### 16.1 Safe parallel examples

-   independent service specifications after a feature's overall
    architecture is approved;
-   backend and frontend implementation after the API contract is
    approved;
-   documentation for separate services;
-   independent test design and code review;
-   independent service implementations with separate contracts and
    workspaces.

### 16.2 Sequential requirements

These activities must remain sequential:

1.  Requirements clarification before dependent design.
2.  Architecture decision before implementation of an architecture
    change.
3.  Service/data ownership before database implementation.
4.  API contract approval before dependent frontend/backend integration.
5.  Migration review before applying a risky migration.
6.  Implementation before independent verification.
7.  Human approval before protected merge.
8.  Human deployment authorization before production release.

### 16.3 Parallel execution controls

-   one isolated branch/worktree per implementation task;
-   explicit file ownership;
-   no concurrent edits to the same file without coordination;
-   versioned API/event contracts;
-   bounded agent iteration and execution time;
-   orchestrator records task dependencies;
-   integration tests run after parallel work is combined.

### 16.4 Conflict resolution

When agents produce incompatible changes:

1.  Stop conflicting writes.
2.  Preserve each version separately.
3.  Record the conflict and affected files/contracts.
4.  Ask the System Architect or relevant owner to assess.
5.  Request a human decision if an approved rule or architecture must
    change.
6.  Integrate the selected approach.
7.  Rerun affected tests.

Never silently overwrite or discard another agent's work.

------------------------------------------------------------------------

## 17. Failure, retry, and escalation handling

### 17.1 Retry policy

Retry only when the failure is plausibly transient or the agent has a
concrete correction to make.

Examples:

-   temporary provider/rate-limit error: bounded retry with backoff;
-   tool invocation error: validate arguments and retry once or within
    configured limit;
-   failing test: inspect failure and make a targeted correction;
-   repeated identical failure: stop and report.

Do not retry indefinitely or repeatedly regenerate the same failed
output.

### 17.2 Failure categories

  ---------------------------------------------------------------------------
  Category                Examples                    Required action
  ----------------------- --------------------------- -----------------------
  Input failure           Missing task fields,        Needs clarification; do
                          missing source document     not proceed

  Requirement conflict    Business rule conflicts     Block and request
                          with architecture spec      decision

  Design failure          No safe service boundary or System Architect review
                          data ownership

  Tool failure            Command unavailable,        Record exact failure
                          permission denied           and stop dependent step

  Test failure            Unit/integration/contract   Create defect or
                          test fails                  request correction

  Security failure        Cross-tenant access, secret Stop affected work and
                          exposure                    escalate

  Resource failure        Timeout, rate limit, budget Bounded retry or human
                          exceeded                    intervention

  Integration failure     Contract mismatch, event    Coordinate service
                          incompatibility             owners

  Approval failure        Human rejects or requests   Return to the relevant
                          changes                     earlier stage
  ---------------------------------------------------------------------------

### 17.3 Mandatory stop and escalation conditions

Immediately stop the affected task when:

-   real patient data or production secrets are encountered;
-   cross-tenant data exposure is suspected;
-   authorization can be bypassed;
-   an agent is asked to weaken security or audit controls;
-   a destructive database or infrastructure action is requested without
    approval;
-   approved documents conflict;
-   a material product decision is missing;
-   the task requires production access;
-   a tool attempts to access files outside its authorized workspace.

Record the reason, preserve safe artifacts, and notify the human project
owner.

------------------------------------------------------------------------

## 18. AMSDP business-rule checkpoints

The orchestrator and relevant reviewers must apply these checks when a
workflow touches the corresponding functionality. These are guardrails
derived from the approved AMSDP product decisions; they are not a
request to implement every capability in every service.

### 18.1 Organization and branch

-   Organization is the tenant boundary.
-   No cross-organization patient, appointment, doctor, or staff access.
-   Branch permissions are enforced within the organization.
-   Patient records may be shared across branches within the same
    organization, subject to permissions.
-   Appointment records retain their branch association.

### 18.2 Patient and doctor records

-   Patient mandatory fields include name and mobile.
-   Multiple patients may share a mobile number within one organization.
-   Staff must select the correct patient record.
-   Doctor identity is facility-local.
-   Doctor mobile uniqueness follows the approved organization-level
    policy and Super Admin duplicate setting.
-   Duplicate patient records are not automatically merged.

### 18.3 Appointment lifecycle

-   Use the approved appointment status lifecycle.
-   Rescheduling preserves the original appointment and creates a linked
    new appointment.
-   Cancellation permissions and deadlines follow facility/platform
    configuration.
-   No-show is flagged for staff confirmation, not automatically
    finalized.
-   Late arrival is an indicator; staff decides the operational action.
-   Overbooking is disabled by default and permission/reason controlled.

### 18.4 Queue and tokens

-   Queue position is separate from appointment status.
-   Queue reordering does not silently alter appointment date/time.
-   Walk-in handling follows the configured policy.
-   Priority is staff-assigned and audited; the system does not perform
    clinical triage.
-   Token sequence follows the approved daily or continuous mode and
    doctor/room configuration.
-   Queue reordering does not regenerate tokens.
-   Voided/cancelled tokens are not reused by default.
-   Public queue displays do not expose patient personal data.

### 18.5 Scope and privacy

-   External payment processing remains outside the approved MVP scope.
-   Appointment-level confirmation state is not a payment ledger.
-   No clinical records, prescriptions, vitals, or medical decision
    support are added unless separately approved.
-   Estimated waiting/reporting time is not a guarantee.
-   Routine agent development uses synthetic data only.

------------------------------------------------------------------------

## 19. Required artifacts by workflow

  -----------------------------------------------------------------------
  Workflow                            Required artifacts
  ----------------------------------- -----------------------------------
  WF-01 Requirement-to-Design         Product Requirements Package,
                                      Architecture Impact Assessment,
                                      service specs, data/API contracts,
                                      test strategy, approval record

  WF-02 Service Implementation        Code diff, tests, migration if
                                      authorized, documentation,
                                      execution evidence, review

  WF-03 Frontend Delivery             UI diff, component/workflow tests,
                                      localization evidence,
                                      accessibility notes, review

  WF-04 Defect Resolution             Defect report, root-cause analysis,
                                      fix diff, regression test,
                                      verification report

  WF-05 Architecture Decision         Options analysis, ADR proposal,
                                      human decision, updated
                                      architecture docs

  WF-06 Database Change               Schema spec, migration, test
                                      evidence, recovery plan, approvals

  WF-07 Security Review               Security report, findings,
                                      remediation, retest evidence, risk
                                      decision

  WF-08 Cross-Service Integration     Interaction map, contracts, service
                                      changes, integration tests,
                                      security review

  WF-09 Release Readiness             Release notes, CI evidence,
                                      migration plan, rollback plan,
                                      approval, post-release verification

  WF-10 Documentation Update          Updated docs, source references,
                                      validation result, review
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 20. Human approval matrix

  -----------------------------------------------------------------------
  Decision/action                     Required approval
  ----------------------------------- -----------------------------------
  Clarify or change a business rule   Project owner

  Change MVP scope                    Project owner

  Add/remove a microservice           Project owner and architecture
                                      reviewer

  Change service data ownership       Project owner and architecture
                                      reviewer

  Change API contract in a breaking   Affected service owners and human
  way                                 reviewer

  Change authentication/authorization Security Reviewer and project owner
  design

  Change tenant-isolation behavior    Security Reviewer and project owner

  Approve high-risk/destructive       Database reviewer and project owner
  migration

  Add new patient-data category       Project owner and security/privacy
                                      review

  Add paid vendor or external         Project owner
  provider

  Merge protected-branch change       Authorized human
                                      reviewer/repository policy

  Change production infrastructure    Authorized human operator

  Deploy production release           Authorized human operator

  Accept unresolved security risk     Project owner with security review
                                      evidence
  -----------------------------------------------------------------------

The orchestrator must enforce approval gates as workflow state
transitions. Prompt instructions alone are insufficient.

------------------------------------------------------------------------

## 21. Run records and traceability

Every workflow run must produce a durable record.

### 21.1 Minimum run record

``` yaml
run_id: "RUN-unique-id"
task_id: "AMSDP-EXAMPLE-001"
workflow_id: "WF-02"
workflow_version: "1.0"
started_at: "ISO-8601 timestamp"
completed_at: "ISO-8601 timestamp"

source_commit: "git commit hash"
source_documents:
  - path: "docs/product/AMSDP_Business_Rules_V1.0.md"
    version_or_commit: "recorded reference"

agents:
  - agent_id: "A06"
    role: "Backend Developer"
    model_config_id: "backend-default"

artifacts:
  - "path/to/changed-file.py"
  - "path/to/test-report"

checks:
  - command: "actual command"
    exit_code: 0
    result: "PASS"

approvals: []
warnings: []
unresolved_items: []

final_status: "SUCCESS"
```

The schema is illustrative. Do not store API keys, passwords, patient
data, or full secret-bearing environment output in run records.

### 21.2 Traceability chain

A completed feature should be traceable through:

``` text
Approved Business Rule / MVP Requirement
                 |
                 v
             User Story
                 |
                 v
         Acceptance Criteria
                 |
                 v
       Service / API / Data Design
                 |
                 v
         Implementation Task
                 |
                 v
          Code and Tests
                 |
                 v
      QA / Security Evidence
                 |
                 v
          Human Approval
                 |
                 v
       Merge / Release Record
```

------------------------------------------------------------------------

## 22. Initial workflow implementation roadmap

The AI Factory should implement workflow capability in stages. Do not
automate every workflow before the foundation is reliable.

### Stage 1 --- Basic controlled workflow

Implement:

-   task intake and validation;
-   context loading;
-   Product Analyst workflow;
-   Technical Writer workflow;
-   structured output;
-   run record;
-   human review pause.

**Exit criteria:** the factory can produce a requirements or
documentation artifact from approved project documents and preserve a
reviewable run record.

### Stage 2 --- Architecture and design

Implement:

-   architecture impact workflow;
-   Service Architect;
-   Database Architect;
-   API Contract Designer;
-   decision request and approval gates.

**Exit criteria:** one feature can be transformed into an approved
service design package before code generation.

### Stage 3 --- Bounded implementation

Implement:

-   isolated workspaces/branches;
-   Backend Developer and Frontend Developer workflows;
-   test execution tools;
-   diff and scope validation;
-   developer self-check.

**Exit criteria:** one approved implementation task can be completed in
an isolated workspace with test evidence.

### Stage 4 --- Independent verification

Implement:

-   QA workflow;
-   Security Review workflow;
-   defect loop;
-   mandatory approval enforcement.

**Exit criteria:** implementation cannot be marked ready for merge
without required independent evidence and human approval.

### Stage 5 --- Cross-service and release readiness

Implement:

-   cross-service integration workflow;
-   release readiness workflow;
-   CI evidence collection;
-   rollback and release documentation;
-   human-only production deployment authorization.

**Exit criteria:** the factory can prepare a release package and
evidence set without autonomous production deployment.

### Stage 6 --- Optimization

Only after earlier stages are stable:

-   selective parallel execution;
-   bounded retries and resumable runs;
-   improved dashboards and cost reporting;
-   additional specialist agents when justified.

------------------------------------------------------------------------

## 23. Definition of Done for a workflow

A workflow is ready for regular use only when:

1.  Its trigger and intended outcome are clear.
2.  Required task inputs are validated.
3.  Relevant approved context is loaded and traceable.
4.  Agent sequence and ownership are explicit.
5.  Dependencies and parallelization rules are defined.
6.  Stop conditions and failure handling are implemented.
7.  Required tools enforce permissions.
8.  Outputs are structured and persisted.
9.  Quality gates are executed and evidence recorded.
10. Human approval gates cannot be bypassed.
11. Tests cover normal, invalid, blocked, and failure paths.
12. Documentation and workflow version are maintained.

------------------------------------------------------------------------

## 24. Approval and change control

This document is a proposed workflow baseline. It becomes approved only
after project-owner review.

Changes to workflow order, agent authority, approval gates,
service-boundary controls, or security handling require review before
implementation.

### Change history

  Version   Date              Description
  --------- ----------------- ---------------------------------------
  1.0       4 November 2026   Initial AMSDP AI Development Workflow

------------------------------------------------------------------------

**End of document**
