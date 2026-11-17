# AMSDP — Configurable Multi-Sector Architecture Implementation Plan

**Document Version:** 1.0  
**Date:** 16 November 2026  
**Status:** PROPOSED — Post-Hackathon Implementation Roadmap  
**Project:** AMSDP  
**Architecture Direction:** Microservices  
**Priority:** Post-MVP Strategic Development

---

## 1. Executive Summary

AMSDP is intended to become a configurable healthcare service-delivery and operations platform supporting multiple healthcare delivery models.

The platform must accommodate:

- Private hospitals and clinic networks.
- Independent private healthcare facilities.
- Government hospitals and healthcare facilities.
- Government primary healthcare networks.
- Community clinics.
- NGO-operated healthcare facilities.
- Outreach and satellite healthcare services.
- Public health programmes.
- Hybrid healthcare organizations.

The objective is not to create separate AMSDP products for these sectors.

Instead, AMSDP will provide one common platform with configurable deployment profiles, organizational structures, facility types, operational modules, workflows, governance rules and integrations.

The architecture must support different healthcare delivery models without compromising service independence, tenant isolation, security, auditability or maintainability.

### Implementation timing

This initiative will begin after the Bangladesh E-Health Hackathon & Symposium MVP has been completed, demonstrated and stabilized.

No implementation of this initiative should interrupt the current hackathon MVP development unless an architectural issue creates an immediate blocker.

---

## 2. Current Development Position

AMSDP is currently focused on delivering its hackathon MVP.

Existing development includes:

- Organization and branch management.
- Doctor management.
- Facility hierarchy.
- Doctor chamber and schedule management.
- Appointment management.
- Queue management.
- Patient-facing appointment tracking.
- Role-based access.
- Multi-branch organizational operations.
- Audit and governance mechanisms.
- Frontend operational interfaces.

The current product is primarily optimized for private outpatient clinic operations.

The post-hackathon initiative will expand its underlying domain model and configuration capabilities.

### Important architectural distinction

We must distinguish:

1. Current implemented capabilities.
2. Approved target architecture.
3. Future capabilities that have not yet been implemented.

The existence of a planned capability must never be reported as an implemented or verified feature.

Before beginning this initiative, conduct a fresh repository and architecture assessment. Do not assume that previously discussed implementation details still reflect the current codebase.

---

## 3. Product Vision

**AMSDP shall be a configurable, multi-sector healthcare service-delivery and operations platform.**

A deployment may be configured for private healthcare, public healthcare, community healthcare, outreach programmes or hybrid operating models.

Installation profiles shall provide initial configuration presets, while authorized administrators may extend or modify instance configuration without requiring a separate product version or installation.

All configurations must preserve:

- Microservices architecture.
- Tenant isolation.
- Explicit service boundaries.
- Service-level authorization.
- Auditability.
- Data ownership.
- Configurable governance.
- Backward compatibility.
- Operational reliability.

---

## 4. Core Architectural Principles

The following principles should guide the implementation.

### 4.1 One Platform, Multiple Healthcare Delivery Models

Do not create separate codebases for private and public healthcare.

Common capabilities should be reusable across different healthcare delivery models.

Differences should be handled through configuration, policies, workflows and authorized capabilities.

### 4.2 Microservices Architecture

AMSDP will follow the approved microservices architecture.

Each domain service must have:

- Clearly defined responsibilities.
- Explicit API contracts.
- Appropriate data ownership.
- Independent service evolution and deployment.
- Service-level authentication and authorization.
- Tenant-aware operations.
- Health monitoring and observability.

Do not introduce database-per-service as an automatic requirement. Data ownership and persistence strategy must follow separately approved architecture decisions.

### 4.3 Configuration over Hard-Coding

Avoid spreading conditions such as:

- `isGovernment`
- `isPrivate`
- `isCommunityClinic`

throughout unrelated services and frontend components.

Use explicit configuration, capability definitions, policy evaluation and workflow rules.

### 4.4 Preserve Existing Functionality

Existing appointment, queue, doctor, facility and organization functionality must remain operational.

Migration must be incremental.

No destructive schema replacement or indiscriminate data reset is acceptable for production or existing user environments.

### 4.5 Configurable Governance

Different healthcare sectors have different management structures.

A generic role hierarchy must not be imposed on every deployment.

Authorization must account for:

- Organization.
- Agency.
- Administrative jurisdiction.
- Facility.
- Assigned responsibilities.
- Explicit permissions.
- Delegated authority.

---

## 5. Target Configuration Architecture

AMSDP should support three primary configuration levels.

### 5.1 Instance Configuration

Defines the overall deployment.

Examples:

- Private healthcare deployment.
- Government healthcare deployment.
- Community healthcare deployment.
- Outreach programme deployment.
- Hybrid healthcare deployment.

Instance configuration controls:

- Enabled deployment profiles.
- Available modules and capabilities.
- Supported administrative hierarchy templates.
- Default localization.
- Integration availability.
- Security and governance defaults.
- Platform-wide operational settings.

An instance may support more than one healthcare delivery model.

### 5.2 Organization Configuration

Defines how an individual organization operates.

Examples:

Private healthcare:

- Organization.
- Branches.
- Departments.
- Doctors.
- Schedules.
- Rooms.

Government healthcare:

- Government authority.
- Directorate or agency.
- Administrative jurisdiction.
- Facilities.
- Programmes.
- Supervisory relationships.

NGO healthcare:

- Organization.
- Project or programme.
- Operational regions.
- Permanent facilities.
- Outreach locations.
- Assigned personnel.

Organization configuration must not assume that every organization has branches.

### 5.3 Facility Configuration

Defines the operating arrangements of an individual facility.

Examples:

- Facility type.
- Facility classification.
- Services offered.
- Departments.
- Rooms.
- Staff assignments.
- Operating schedules.
- Appointment requirements.
- Queue configuration.
- Outreach responsibilities.

A small Community Clinic must not be forced to configure floors, departments and rooms when those concepts are not relevant to its operations.

---

## 6. Installation and Deployment Profiles

Introduce installation profiles as configuration presets.

Initial proposed profiles:

| Profile | Intended use |
|---|---|
| Private Healthcare Network | Private hospital and clinic groups |
| Independent Healthcare Facility | Individual healthcare facilities |
| Government Health Network | Government health authorities and networks |
| Community Healthcare | Community clinics and primary healthcare |
| Outreach and Public Health | Outreach programmes and satellite services |
| Hybrid Healthcare Network | Mixed healthcare delivery models |

These profiles are starting configurations, not separate products.

### Installation workflow

A future installation process should support:

1. Install AMSDP platform components.
2. Configure instance identity.
3. Select one or more deployment profiles.
4. Configure default country and localization.
5. Select applicable organizational hierarchy templates.
6. Enable required functional modules.
7. Configure initial governance and role templates.
8. Configure approved external integrations.
9. Create the initial platform administrator.
10. Validate configuration.
11. Initialize the deployment.

### Important requirement

Changing an installation profile later must not require reinstalling AMSDP.

An authorized administrator must be able to enable additional capabilities and configure new organizational relationships while preserving existing data.

Profile changes must be audited.

---

## 7. Target Domain Capabilities

The following are proposed domain capabilities. They are not a finalized list of independently deployable microservices.

### 7.1 Organization and Administrative Structure

Responsibilities:

- Organization management.
- Government agency representation.
- Administrative jurisdictions.
- Organizational relationships.
- Branches and operational units.
- Supervisory relationships.
- Organizational configuration.

### 7.2 Facility Registry

Responsibilities:

- Hospitals.
- Clinics.
- Community Clinics.
- Upazila Health Complexes.
- Union-level facilities.
- Other recognized facility types.
- Facility classification.
- Facility ownership.
- Facility location.
- Facility operating status.
- Facility relationships.

The design should support mapping to recognized external facility identifiers, including applicable DGHS facility registry identifiers.

### 7.3 Identity and Access Management

Responsibilities:

- User identity.
- Authentication.
- Role templates.
- Permission management.
- Jurisdiction-based access.
- Tenant isolation.
- Delegated permissions.
- Service-to-service authentication.

### 7.4 Workforce Management

Responsibilities:

- Doctors.
- Nurses.
- Health workers.
- Administrative personnel.
- Facility assignments.
- Programme assignments.
- Duty schedules.
- Workforce availability.

### 7.5 Appointment and Patient Flow

Responsibilities:

- Patient registration.
- Appointment scheduling.
- Appointment lifecycle.
- Check-in.
- Queue allocation.
- Queue monitoring.
- Consultation flow.

Appointment and queue lifecycles must remain distinct.

Outreach service contacts must not automatically be treated as appointments.

### 7.6 Community and Outreach Operations

Responsibilities:

- Outreach locations.
- Outreach session scheduling.
- Field worker assignments.
- Household visits.
- Community service contacts.
- Session attendance.
- Services delivered.
- Referrals.
- Follow-up requirements.
- Session completion.

### 7.7 Programme Management

Responsibilities:

- Programme registration.
- Programme configuration.
- Programme locations.
- Assigned personnel.
- Service targets.
- Programme activity.
- Target versus achievement.
- Programme reporting.

Examples include:

- EPI.
- Maternal and child health.
- Family planning.
- Nutrition.
- NCD screening.
- Other approved public health programmes.

### 7.8 Referral and Follow-up

Responsibilities:

- Referral creation.
- Referral destination.
- Referral status.
- Referral completion.
- Follow-up scheduling.
- Continuity of care.

### 7.9 Reporting and Analytics

Responsibilities:

- Organization-level reporting.
- Facility-level reporting.
- Administrative jurisdiction reporting.
- Programme reporting.
- Outreach reporting.
- Operational performance.
- Data completeness.
- External reporting integration.

### 7.10 Audit and Governance

Responsibilities:

- Append-only audit records.
- Actor identification.
- Configuration change history.
- Permission change history.
- Administrative action history.
- Cross-service audit correlation.

7.11 Identity Verification & Government Interoperability

Objective

Introduce an optional, secure identity-verification capability that enables authorized AMSDP healthcare deployments to verify patient or beneficiary identity through officially approved government identity services.

This capability is particularly relevant to:

Government Healthcare Deployment.

Community Healthcare Deployment.

Outreach Programme Deployment.

The objective is to improve identity accuracy, reduce duplicate or inconsistent patient records, support beneficiary identification, and strengthen interoperability with authorized government systems.

Potential Integration: Bangladesh National Identity (NID)

AMSDP may integrate with the Bangladesh Election Commission's National Identity (NID) verification services, subject to formal authorization, eligibility, applicable agreements, and technical requirements.

Potential capabilities include:

Verification of an individual's NID information.

Confirmation of identity attributes permitted by the authorized service.

Assisted patient registration using verified information.

Recording identity-verification status and verification references.

Reducing duplicate patient registrations across participating healthcare organizations, where legally and technically permitted.

The availability of individual identity attributes, such as name, date of birth, photograph, and address, must be established through the official authorization and API agreement. Verification access must not be assumed to grant unrestricted access to NID records.

Deployment Applications

A. Government Healthcare Deployment

Support identity verification during patient registration.

Improve consistency of patient demographic records.

Support authorized beneficiary identification across government healthcare facilities.

Potentially facilitate interoperability with approved government health information systems.

B. Community Healthcare Deployment

Assist community healthcare workers with patient identity verification.

Support more consistent household and beneficiary records.

Help identify existing patient records and reduce duplication.

Provide an alternative registration process for individuals without an NID.

C. Outreach Programme Deployment

Support beneficiary identification during outreach sessions and household visits.

Improve beneficiary record consistency across programmes and service locations.

Support authorized programme reporting and follow-up.

Associate service records with verified identities where appropriate and permitted.

Architectural Approach

Implement identity verification through an independently managed integration boundary, preferably an Identity Verification Service or equivalent domain service within the AMSDP microservices architecture.

The integration should:

Support configurable identity providers rather than hard-code dependence on one provider.

Keep API credentials, certificates, and authentication mechanisms on the backend.

Expose only the permitted verification results to authorized AMSDP services.

Enforce organization, facility, role, and jurisdiction-based authorization.

Maintain auditable verification attempts and outcomes.

Support secure communication, response validation, and failure handling.

Avoid unnecessary replication or retention of government identity data.

Identity verification should be configurable at the AMSDP instance level and enabled only for deployments with the required authorization.

Privacy, Consent and Governance

NID verification must not be mandatory for receiving healthcare services.

Individuals without an NID must still be able to register and receive services.

Children and other individuals without an NID must have appropriate alternative registration workflows.

Collect and process only the identity information necessary for the authorized purpose.

Obtain and record appropriate patient authorization or consent where legally required.

Restrict access to identity information according to staff roles and organizational responsibilities.

Protect identity information in storage, transmission, logs, and audit records.

Do not expose full NID numbers or sensitive identity responses unnecessarily.

Do not automatically overwrite existing patient information with returned identity data.

Failed or unavailable verification services must not prevent legitimate healthcare registration.

Government Interoperability Beyond NID

The broader identity-verification architecture should remain extensible to other officially authorized government identity, facility-registry, and beneficiary-verification services.

Potential future interoperability areas include:

Government healthcare facility registries.

Authorized public health information systems.

Government programme and beneficiary registries.

Approved national health information exchange mechanisms.

Each integration must have its own documented authorization, data-sharing purpose, API contract, security requirements, and governance controls.

Implementation Phases

Feasibility and Authorization Assessment: Establish eligibility, application requirements, permitted data attributes, fees, agreements, and technical access with the relevant government authority.

Integration Specification: Define identity-verification workflows, data contracts, security requirements, audit events, and failure handling.

Identity Verification Foundation: Develop the provider-independent integration boundary and configuration mechanisms.

Initial Authorized Integration: Implement and test the NID integration only after official access and technical specifications are available.

Deployment Validation: Validate the capability in government healthcare, community healthcare, and outreach programme scenarios.

Further Interoperability: Assess additional officially authorized identity and government information services.

Scope Boundary

Identity verification is an administrative and interoperability capability. It must not become a condition for accessing healthcare, and it must not be treated as a substitute for clinical identity assessment or professional judgment.

Strategic Direction: Identity Verification & Government Interoperability will be an optional post-hackathon AMSDP capability, with particular value for government healthcare, community healthcare, and outreach programme deployments.

---

## 8. Post-Hackathon Implementation Roadmap

Implementation should be divided into controlled phases.

Each phase must have its own specification, implementation plan, tasks, tests and acceptance criteria.

### Phase 0 — Hackathon MVP Completion and Stabilization

**Priority: Immediate**

Complete the currently approved MVP.

Activities:

- Complete outstanding MVP functionality.
- Resolve known functional defects.
- Verify organization and branch isolation.
- Verify appointment and queue lifecycles.
- Verify doctor and facility management.
- Verify appointment location snapshots.
- Complete frontend usability improvements.
- Validate realistic demo data.
- Run backend and frontend tests.
- Complete production build.
- Verify critical workflows in the browser.
- Document known limitations.
- Stabilize the hackathon demonstration environment.

Deliverables:

- MVP implementation report.
- Test evidence.
- Browser verification evidence.
- Known limitations register.
- Hackathon demonstration baseline.

**Exit condition:** The MVP is accepted for its intended hackathon scope.

Do not start the multi-sector implementation during this phase.

### Phase 1 — Post-Hackathon Assessment and Architecture Baseline

**Priority: Critical**

Conduct a comprehensive review of the actual repository after MVP completion.

Activities:

1. Review existing microservices and their responsibilities.
2. Review current organization and tenant models.
3. Review facility and branch data models.
4. Review user roles and authorization.
5. Review existing migrations.
6. Review inter-service communication.
7. Review database ownership and persistence.
8. Review audit mechanisms.
9. Review existing frontend architecture.
10. Identify hard-coded private-clinic assumptions.

Classify findings:

- Reusable.
- Requires extension.
- Requires refactoring.
- Missing.
- Architectural risk.
- Requires product decision.

Deliverables:

- Current architecture assessment.
- Target architecture document.
- Architecture decision records.
- Migration risk register.
- Dependency map.
- Prioritized implementation backlog.

**Exit condition:** Existing architecture and required changes are understood and approved.

### Phase 2 — Product Domain and Configuration Specifications

**Priority: Critical**

Define the configuration system before implementation.

Create specifications for:

1. Instance configuration.
2. Deployment profiles.
3. Organizational structures.
4. Administrative hierarchies.
5. Facility classifications.
6. Module and capability management.
7. Configuration policies.
8. Role templates.
9. Jurisdiction-based permissions.
10. Configuration auditing.

Important decisions:

- Can one instance host multiple independent organizations?
- Can organizations use different delivery models?
- Can an organization operate multiple programmes?
- Can a facility participate in multiple programmes?
- Can an outreach location be shared across programmes?
- How are government agencies represented?
- How are cross-agency relationships authorized?

Deliverables:

- Configuration domain specification.
- Organizational hierarchy specification.
- Facility registry specification.
- Authorization and governance specification.
- Capability and module specification.

**Exit condition:** Domain models and governance rules are approved.

### Phase 3 — Configuration Foundation

**Priority: Highest implementation priority**

Build the reusable configuration foundation.

Proposed capabilities:

- Instance configuration registry.
- Organization configuration.
- Deployment profile definitions.
- Capability registry.
- Configuration validation.
- Configuration versioning.
- Configuration change audit.
- Safe configuration updates.
- Configuration retrieval APIs.

Important requirements:

- Configuration changes must be validated.
- Unauthorized users cannot change protected settings.
- Configuration changes must be auditable.
- Configuration updates must not silently alter historical records.
- Services must have a clear mechanism for receiving configuration updates.
- Services must behave safely if configuration is missing or invalid.

Do not implement every deployment profile immediately.

Start with the smallest configuration foundation capable of supporting existing private healthcare functionality without breaking it.

Deliverables:

- Configuration service or approved equivalent.
- Configuration contracts.
- Configuration validation tests.
- Configuration audit integration.
- Migration and compatibility documentation.

**Exit condition:** Existing private healthcare operations work through the new configuration foundation.

### Phase 4 — Organization and Administrative Hierarchy

**Priority: High**

Extend the current organization and facility model.

Support configurable structures such as:

Private:

Organization → Branch → Facility.

Government:

Authority → Directorate / Agency → Division → District → Upazila → Union → Facility.

NGO:

Organization → Project / Programme → Region → Facility / Outreach Location.

These are templates, not mandatory fixed structures.

Requirements:

- Configurable hierarchy levels.
- Parent-child relationships.
- Multiple organization types.
- Facility-to-jurisdiction mapping.
- Effective dates where necessary.
- Historical relationship preservation.
- Explicit authority and ownership relationships.
- Tenant isolation.

Do not assume that every administrative relationship is a simple parent-child hierarchy. Some facilities and programmes may have relationships with multiple authorities.

Deliverables:

- Extended organizational model.
- Administrative hierarchy APIs.
- Facility registry enhancements.
- Migration scripts.
- Hierarchy management interfaces.
- Authorization tests.

**Exit condition:** Private organization structures remain functional, and alternative administrative hierarchies can be represented without hard-coded assumptions.

### Phase 5 — Facility Classification and Service Configuration

**Priority: High**

Introduce facility classification independent of organization type.

Potential facility categories:

- Hospital.
- Medical college hospital.
- Specialized hospital.
- General hospital.
- Upazila Health Complex.
- Union Sub-Centre.
- Union Health and Family Welfare Centre.
- Community Clinic.
- Private clinic.
- Diagnostic centre.
- Outreach service location.

The classification catalogue must be configurable and versionable.

Facility configuration should describe:

- Facility type.
- Ownership.
- Responsible authority.
- Administrative location.
- Operating status.
- Services offered.
- Workforce.
- Operating schedule.
- Available departments.
- Available rooms.
- Referral relationships.

A facility's type should not automatically determine every operational capability.

For example, a Community Clinic may use patient registration and service encounters without needing a hospital-style appointment calendar.

Deliverables:

- Facility classification model.
- Service catalogue.
- Facility capability configuration.
- Facility management interface.
- Data migration and validation.

**Exit condition:** Different facility types can be represented and configured without changing core service code for each type.

### Phase 6 — Governance, Roles and Jurisdiction-Based Access

**Priority: Critical**

Extend authorization to support public and private governance structures.

Support:

- Instance-level administrators.
- Organization administrators.
- Directorate or agency administrators.
- Division-level administrators.
- District-level administrators.
- Upazila-level administrators.
- Facility administrators.
- Programme administrators.
- Outreach supervisors.
- Healthcare workers.

These are configurable role templates, not universally valid job permissions.

Requirements:

- Scope-based authorization.
- Facility-level access.
- Administrative jurisdiction access.
- Programme-specific permissions.
- Explicit delegation.
- Cross-organization restrictions.
- Service-level authorization.
- Fail-closed behavior.
- Non-disclosing cross-tenant access.
- Append-only audit records.

Do not grant access merely because two facilities are in the same district or because a user has a similarly named job title.

Deliverables:

- Updated authorization model.
- Role and permission catalogue.
- Jurisdiction access rules.
- Delegation model.
- Security test suite.
- Audit verification report.

**Exit condition:** Cross-tenant and cross-jurisdiction access is tested and correctly restricted.

### Phase 7 — Community and Outreach Operations

**Priority: High**

Introduce outreach as a first-class operational capability.

Do not model an outreach session as a permanent facility or an ordinary appointment.

Support:

- Outreach programme.
- Session.
- Location.
- Supervising facility.
- Assigned personnel.
- Service types.
- Target population.
- Planned attendance.
- Actual service contacts.
- Referrals.
- Follow-ups.
- Supplies and equipment, where applicable.
- Session completion.

Support different outreach activities:

- EPI sessions.
- Satellite clinics.
- Family-planning services.
- Maternal and child health services.
- Nutrition services.
- Community screening.
- Household visits.

The model should distinguish:

1. Outreach session.
2. Household visit.
3. Individual service contact.
4. Clinical encounter.
5. Referral.
6. Follow-up activity.

Deliverables:

- Outreach domain specification.
- Outreach APIs and service implementation.
- Outreach planning interface.
- Field activity recording interface.
- Outreach dashboard.
- Integration tests.

**Exit condition:** An authorized organization can plan, execute and report outreach activities without requiring ordinary clinic appointment workflows.

### Phase 8 — Programme Management and Reporting

**Priority: High**

Introduce configurable programme management.

Support:

- Programme registration.
- Programme ownership.
- Geographic coverage.
- Participating facilities.
- Assigned workers.
- Service targets.
- Programme activities.
- Target achievement.
- Programme reporting.

Reporting should support:

- Facility performance.
- Administrative jurisdiction performance.
- Programme performance.
- Outreach coverage.
- Service delivery.
- Referral completion.
- Reporting completeness.

Investigate interoperability with:

- DHIS2.
- DGHS facility registry.
- Relevant DGFP information systems.
- Other officially supported national health information systems.

Do not assume that AMSDP should replace existing government reporting systems.

Prefer documented, authorized interoperability using agreed data standards and contracts.

Deliverables:

- Programme management capability.
- Programme dashboard.
- Reporting APIs.
- Interoperability assessment.
- Integration specifications.

**Exit condition:** Programme activity can be managed and reported independently of ordinary appointment and queue operations.

### Phase 9 — Deployment Profiles and Installation Experience

**Priority: Medium to High**

Once the configuration foundation and domain models are stable, implement the installation and setup experience.

Provide:

- Private healthcare preset.
- Government healthcare preset.
- Community healthcare preset.
- Outreach programme preset.
- Hybrid preset.

The installation process should configure:

- Instance identity.
- Deployment profile.
- Localization.
- Administrative hierarchy templates.
- Enabled modules.
- Default roles.
- Security defaults.
- Integration availability.

Requirements:

- Profile validation.
- Repeatable setup.
- Configuration export and import.
- Safe upgrades.
- Profile changes without reinstalling.
- Audited administrative changes.

Deliverables:

- Instance setup workflow.
- Configuration templates.
- Deployment documentation.
- Upgrade documentation.
- Installation verification tests.

**Exit condition:** A new instance can be configured for a selected operating model without requiring a separate product codebase.

### Phase 10 — Cross-Sector Validation

**Priority: Critical before general release**

Validate AMSDP against representative deployment scenarios.

Scenario A — Private clinic network:

- One organization.
- Four branches.
- Shared patient records within the organization.
- Branch-specific operational permissions.
- Doctor schedules across branches.
- Organization-wide reporting.

Scenario B — Independent public hospital:

- One facility.
- Facility-specific administration.
- OPD and queue operations.
- Staff assignments.
- Facility reporting.

Scenario C — Government administrative network:

- Administrative hierarchy.
- Multiple facilities.
- Jurisdiction-based access.
- District and Upazila dashboards.
- Appropriate agency separation.

Scenario D — Community healthcare:

- Community Clinics.
- Assigned health workers.
- Community service contacts.
- Referrals.
- Local reporting.

Scenario E — Outreach programme:

- Multiple outreach locations.
- Scheduled sessions.
- Assigned workers.
- Service contacts.
- Follow-ups.
- Programme reporting.

Scenario F — Hybrid organization:

- Permanent healthcare facilities.
- Community facilities.
- Outreach services.
- Multiple programmes.
- Different user roles.

Validation must include:

- Functional testing.
- Authorization testing.
- Tenant isolation testing.
- Concurrency testing.
- Data migration testing.
- Service integration testing.
- Browser verification.
- Performance testing.
- Backup and recovery testing.

**Exit condition:** All approved scenarios pass their acceptance criteria.

---

## 9. Frontend Strategy

AMSDP should retain one application and one shared visual identity.

Different users should see different workspaces based on:

- Deployment configuration.
- Organization.
- Facility.
- Administrative jurisdiction.
- Programme assignment.
- Permissions.

### Proposed dashboard types

| User type | Default dashboard |
|---|---|
| Private Organization Admin | Organization Overview |
| Private Clinic Admin | Clinic Overview |
| Public national administrator | National Health Overview |
| Directorate administrator | Directorate Overview |
| Civil Surgeon | District Health Overview |
| UH&FPO | Upazila Health Operations |
| Facility Administrator | Facility Overview |
| Community Clinic supervisor | Community Clinic Overview |
| Outreach Supervisor | Community & Outreach Operations |
| Community Health Worker | Assigned Activities |

Dashboard visibility and actions must be authorization-driven.

Do not assume that every deployment uses every dashboard type.

---

## 10. Data Migration and Backward Compatibility

This initiative must preserve the existing MVP's data and functionality.

Before structural changes:

1. Review existing schemas.
2. Document current relationships.
3. Identify data ownership.
4. Design additive migrations where practical.
5. Define data transformation rules.
6. Back up affected environments.
7. Test migrations on representative copies.
8. Validate record counts and relationships.
9. Test rollback or recovery procedures.
10. Document the migration.

Historical appointment locations, audit records and other immutable operational snapshots must not be silently rewritten.

No production data reset is permitted as part of this initiative.

---

## 11. Security and Governance Requirements

Security must be considered across all phases.

Minimum requirements:

- Tenant isolation.
- Organization isolation.
- Jurisdiction-based access.
- Service-level authorization.
- Explicit delegation.
- Secure inter-service authentication.
- Append-only audit records.
- Actor identification.
- Configuration change auditing.
- Sensitive data access controls.
- Fail-closed authorization.
- Secure integration credentials.
- Data minimization.
- Backup and recovery procedures.

Government deployments may require additional security, hosting, data residency and compliance controls. These must be assessed against applicable official requirements before deployment.

---

## 12. Documentation Structure

Maintain the existing AMSDP documentation conventions.

Proposed new documentation:

```text
docs/
├── architecture/
│   ├── AMSDP_Configurable_Multi_Sector_Architecture_V1.0.md
│   ├── AMSDP_Configuration_Architecture_V1.0.md
│   ├── AMSDP_Administrative_Hierarchy_Model_V1.0.md
│   ├── AMSDP_Facility_Registry_Architecture_V1.0.md
│   └── AMSDP_Public_Private_Governance_Model_V1.0.md
│
├── product/
│   ├── AMSDP_Deployment_Profiles_V1.0.md
│   ├── AMSDP_Multi_Sector_Product_Requirements_V1.0.md
│   └── AMSDP_Community_Outreach_Requirements_V1.0.md
│
├── implementation/
│   ├── AMSDP_Configuration_Foundation_Implementation_Report_V1.0.md
│   ├── AMSDP_Administrative_Hierarchy_Implementation_Report_V1.0.md
│   └── ...
│
├── integrations/
│   ├── AMSDP_DHIS2_Interoperability_Assessment_V1.0.md
│   └── AMSDP_DGHS_Facility_Registry_Integration_V1.0.md
│
└── chatgpt/
    └── AMSDP_Configurable_Multi_Sector_Architecture_Implementation_Plan_V1.0.md
```

The proposed files are future deliverables. Do not create empty placeholder documents simply to match this directory structure.

---

## 13. Development Governance

Use GitHub Spec Kit or the approved specification-driven development process for significant architectural and domain changes.

For each major phase:

1. Establish the approved requirements.
2. Create the feature specification.
3. Review existing architecture.
4. Document relevant research.
5. Produce the technical plan.
6. Produce ordered implementation tasks.
7. Review security and migration implications.
8. Implement incrementally.
9. Run automated tests.
10. Perform browser or operational verification where applicable.
11. Produce an implementation report.
12. Obtain acceptance before proceeding to dependent work.

Small maintenance tasks may use a lightweight process.

No phase should be marked VERIFIED or ACCEPTED without appropriate evidence.

Preserve unrelated local modifications and existing workstreams.

Do not use destructive repository, Git or database operations without explicit authorization.

---

## 14. Prioritization

| Phase | Priority | Dependency |
|---|---|---|
| 0. MVP completion | Immediate | Current work |
| 1. Architecture assessment | Critical | Phase 0 |
| 2. Domain specifications | Critical | Phase 1 |
| 3. Configuration foundation | Critical | Phase 2 |
| 4. Administrative hierarchy | High | Phase 3 |
| 5. Facility classification | High | Phases 3–4 |
| 6. Governance and access | Critical | Phases 3–4 |
| 7. Community and outreach | High | Phases 3–6 |
| 8. Programme management | High | Phases 4–7 |
| 9. Deployment profiles | Medium–High | Phases 3–8 |
| 10. Cross-sector validation | Critical | All approved capabilities |

These are dependency and priority classifications, not fixed calendar commitments.

Actual scheduling should follow the post-hackathon architecture assessment.

---

## 15. What Is Explicitly Out of Scope for the Hackathon MVP?

Unless separately approved, the following remain post-hackathon scope:

- Government administrative hierarchy.
- National or district-level dashboards.
- Community Clinic operational model.
- Outreach session management.
- Public health programme management.
- Government-specific deployment presets.
- DHIS2 interoperability.
- DGHS facility registry integration.
- Multi-agency governance.
- Cross-sector deployment configuration.
- National-scale deployment workflows.

The current MVP should not be delayed by attempting to implement these capabilities prematurely.

---

## 16. Immediate Decisions to Preserve

The following product and architecture decisions should be treated as the current proposed direction:

1. AMSDP is one configurable healthcare service-delivery and operations platform.
2. Private and public healthcare are supported through configuration, not separate products.
3. The approved architecture is microservices.
4. Installation profiles provide initial configuration presets.
5. Profiles do not permanently restrict platform capabilities.
6. Configuration exists at instance, organization and facility levels.
7. One instance may support multiple organizations, subject to approved tenancy and security architecture.
8. Different organizations may use different healthcare delivery models.
9. Public administrative hierarchies must be configurable.
10. Outreach is a first-class operational concept, not a permanent clinic or ordinary appointment.
11. Public health programmes are distinct from ordinary clinic operations.
12. Existing MVP functionality must remain backward-compatible.
13. Government interoperability must use approved, documented integration contracts.
14. Security, tenant isolation and auditability are mandatory.

These decisions should be formally reviewed and incorporated into the approved AMSDP product and architecture documentation after the hackathon.

---

## 17. Final Recommendation

The immediate objective is to finish AMSDP's hackathon MVP successfully.

After the hackathon, the first task should not be coding a government dashboard or adding a government installation profile.

It should be a structured assessment of the existing implementation and the creation of an approved target architecture for configurable multi-sector healthcare operations.

The recommended implementation sequence is:

**MVP Stabilization → Architecture Assessment → Domain Specifications → Configuration Foundation → Administrative Hierarchy → Facility Registry → Governance → Community and Outreach → Programme Management → Deployment Profiles → Cross-Sector Validation.**

This sequence reduces architectural risk and avoids building public-sector workflows on assumptions inherited from private clinic management.

The long-term goal is to make AMSDP adaptable to Bangladesh's diverse healthcare delivery structures while preserving a unified, maintainable and independently deployable microservices platform.
