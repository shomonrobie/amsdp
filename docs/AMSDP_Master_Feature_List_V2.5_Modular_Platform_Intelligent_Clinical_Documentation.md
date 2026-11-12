# AMSDP — Master Feature List V2.5
## Modular Healthcare Platform & Intelligent Clinical Documentation Edition

**Document date:** 11 November 2026  
**Market focus:** Bangladesh  
**Document status:** **APPROVED MASTER FEATURE LIST — ACTIVE VERSION**, subject to the status of individual decisions, release gates and implementation authorizations stated herein.  
**Supersedes:** All prior AMSDP Master Feature List versions, including V1.x, V2.0, V2.1, V2.2, V2.3 and V2.4.  
**Historical preservation:** The complete V2.3 baseline is retained in Appendix A for traceability. V2.4's previous clinical-module proposal is superseded by this V2.5 specification and is not an independent source of current requirements.  
**Approval basis:** The Product Owner explicitly approved the revised Section C — Product Family and Module Catalogue — on 11 November 2026. This V2.5 document consolidates that approval with the subsequent product direction for Intelligent Clinical Documentation. Approval of this master list does not itself authorize every module for immediate implementation, paid provider procurement, production deployment, or any Git operation.  
**Core change-control rule:** V2.5 is the sole active Master Feature List. Older versions are historical records only. Where an older statement conflicts with V2.5, V2.5 governs. Individual prior product decisions remain in force unless expressly superseded by a later decision.

---

# Part I — V2.5 Executive Specification

## A. Purpose of V2.5

V2.5 establishes AMSDP as a modular healthcare practice platform for Bangladesh, with three connected product families:

1. **Practice Operations** — the foundational organization, patient-registration, appointment, scheduling, queue, communication and operational-management capabilities.
2. **Clinical Management** — optional encounter-based clinical documentation and digital prescription capabilities, designed around doctor-authored and doctor-approved records.
3. **Intelligent Clinical Documentation** — optional clinician-facing productivity tools, including templates, medicine catalogues, reusable prescription patterns, common instruction shortcuts and optional private doctor-only voice dictation with AI-assisted structuring.

V2.5 makes an explicit product distinction:

- AMSDP helps doctors document and manage decisions they make.
- AMSDP does not require doctors to consult or visibly interact with AI in front of patients.
- AMSDP does not record the patient-doctor conversation by default.
- AMSDP does not independently diagnose, choose treatment or prescribe.
- AI-generated material is a draft and cannot become a finalized clinical record or prescription without explicit doctor review and approval.

The product must remain useful when AI is unavailable, disabled or not purchased.

## B. Approved product positioning

**Primary public-facing positioning:**

**AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.**

This remains the approved positioning for the public website, hackathon materials and product communications. It must not be replaced by unverified claims about zero waiting, guaranteed consultation times or measured reductions in waiting time.

**Clinical product positioning:**

**AMSDP — Intelligent Clinical Documentation**  
*Less typing. Faster documentation. Complete clinical control.*

This is the approved direction for the optional clinical documentation product capability. It describes workflow assistance, not autonomous clinical intelligence or an AI doctor.

## C. Product family and module catalogue — APPROVED

| Product family | Module | Principal capabilities | Commercial treatment |
|---|---|---|---|
| Practice Operations | **AMSDP Core** | Organization/facility workspace, users, doctor entries, patient registration, appointments, schedules, walk-ins, queues, role-based access, audit and operational reports. | Foundational subscription. |
| Practice Operations | **Patient Queue Visibility (PQV)** | Digital Doctor Queue Display (DQDS) and Personal Queue Tracking (PQT), supporting public waiting-room visibility and private appointment-specific queue tracking. | Optional add-on, plan inclusion or bundle; plan decision remains configurable. |
| Practice Operations | **Patient Communication** | Approved one-way WhatsApp and SMS appointment confirmations, reminders and queue-related notifications, with organization-configurable settings and provider integration. | Optional capability; provider and usage costs apply. |
| Practice Operations | **Analytics & Reports** | Appointment, queue, utilization, operational performance and organization-level reporting. | Optional tier/add-on where commercially approved. |
| Clinical Management | **Clinical Records & Consultation Documentation** | Encounter-based consultation records, structured clinical-note templates, doctor-authored notes, symptoms, examination findings, assessment, treatment plans, advice and follow-up instructions. Supports draft, review, finalization and auditable amendments. | Separately activatable clinical module. |
| Clinical Management | **Digital Prescription Management** | Doctor-created, reviewed and approved prescriptions; medicine selection; dosage and instruction entry; reusable prescription templates; printing, downloading, secure storage and historical prescription retrieval. | Separately activatable; does not require AI. |
| Clinical Management | **Prescription Support Library** | Maintained medicine catalogue, generic and brand-name search, medicine autocomplete, doctor-specific favourite medicines, reusable prescription patterns and common instruction library. All selections remain under doctor control. | Included in Clinical Management or separately configurable. |
| Clinical Management | **Encounter History & Record Retrieval** | Organization-scoped consultation history, previous finalized notes, prescription history and encounter timelines for authorized clinical users. Records remain associated with their originating healthcare organization and applicable access permissions. | Depends on Clinical Management; advanced longitudinal functionality may be separately activated. |
| Intelligent Clinical Documentation | **Intelligent Clinical Documentation Assistant** | Optional private doctor-only voice dictation, Bangla/English speech-to-text, AI-assisted structuring of the doctor's dictated clinical notes, extraction of explicitly dictated medicines and instructions, catalogue matching, draft preparation and clinician-controlled correction and approval. | Premium optional capability; depends on Clinical Management. |
| Intelligent Clinical Documentation | **Clinical Summaries & Follow-up Assistance** | Draft summaries of previously recorded encounters, documentation assistance and follow-up information for authorized clinician review. Must use only available, authorized records and must not imply access to a complete medical history when one does not exist. | Optional future capability; depends on Clinical Management. |

### C.1 Commercial and activation principles

- AMSDP Core can be used without Clinical Management.
- Clinical Management can be used without AI capabilities.
- Digital Prescription Management does not require AI.
- Intelligent Clinical Documentation is optional and depends on Clinical Management.
- Module entitlements are enforced server-side.
- Exact plan names, prices, bundles, billing units, trial rules and usage limits remain commercial decisions.
- A feature-list approval is not approval to purchase or subscribe to a paid external service.

## D. Product dependency model

```text
AMSDP
│
├── Practice Operations
│   ├── AMSDP Core
│   │   ├── Organization and branch management
│   │   ├── Users, roles and permissions
│   │   ├── Patient registration
│   │   ├── Appointment and schedule management
│   │   ├── Walk-ins and queue management
│   │   └── Audit and operational reporting
│   ├── Patient Queue Visibility
│   │   ├── DQDS — public, token-only waiting-room display
│   │   └── PQT — private, appointment-specific tracking
│   ├── Patient Communication
│   │   ├── WhatsApp
│   │   └── SMS
│   └── Analytics & Reports
│
└── Clinical Management [optional]
    ├── Clinical Records & Consultation Documentation
    ├── Digital Prescription Management
    ├── Prescription Support Library
    └── Encounter History & Record Retrieval
        │
        └── Intelligent Clinical Documentation [optional]
            ├── Clinical-note and prescription templates
            ├── Doctor's favourites and common instructions
            ├── Private doctor-only voice dictation
            ├── Speech-to-text
            ├── AI-assisted note structuring
            └── Doctor-reviewed prescription preparation
```

- Clinical Management requires an active AMSDP Core organization.
- Intelligent Clinical Documentation requires Clinical Management.
- No AI capability is a prerequisite for ordinary notes or prescriptions.
- No optional module may disable or corrupt the Core appointment and queue workflows.
- Module entitlements and access permissions are separate controls: purchasing a module does not automatically grant every user access to its records.

## E. Product scope and precedence

The complete V2.3 baseline is retained in Appendix A. The following V2.5 amendments govern current interpretation:

| Historical V2.3/V2.4 topic | Active V2.5 interpretation |
|---|---|
| Appointment-first product | Remains the foundation of AMSDP Core. |
| Statement that AMSDP is not an EMR/EHR/HMS | AMSDP is not a complete hospital information system or enterprise EHR. It may offer bounded, optional, organization-scoped clinical documentation and prescription records. |
| Facility-owned patient records | Patient personal data is not treated as property owned outright by a clinic or AMSDP. The healthcare organization is responsible for lawful records it creates and maintains; AMSDP acts according to its actual legal role and processing arrangements. |
| Clinical notes and prescriptions excluded from Core | They remain excluded from AMSDP Core but are included in the optional Clinical Management module. |
| Patient Medical History | Initial scope is encounter-based, organization-scoped record retrieval. A centralized, cross-clinic longitudinal medical-history repository is not included. |
| AI Clinical Assistant with consent-based ambient recording | Superseded. The initial direction is private doctor-only dictation. Patient-doctor conversation recording is not a default feature and requires a separate product, privacy, legal and clinical approval. |
| AI medication/management suggestions | Superseded as an initial capability. The system may organize and match medicines and instructions explicitly dictated or selected by the doctor; it must not independently choose treatment. |
| AI-generated note | Optional draft created from doctor-authored dictation, not an autonomous interpretation of an unrecorded patient conversation. |
| Doctor workspace limited to appointment/queue in Core | Remains true for Core. An authorized doctor may additionally use separately activated Clinical Management. |

## F. Current hackathon release boundary

The current hackathon MVP remains governed by the approved AMSDP Core scope and existing task-level approvals.

- Existing appointment, queue, PQV, role, tenant-isolation and BanglaNameSense capabilities must be stabilized and demonstrated.
- The existence of Clinical Management and Intelligent Clinical Documentation in V2.5 does not automatically authorize their implementation in the hackathon release.
- Any hackathon demonstration of clinical documentation must be separately scoped, bounded, clearly identified as a demonstrator and must not destabilize the operational MVP.
- No fake clinical functionality: every demonstrated action must call a working API and persist appropriately, or be explicitly labelled as a prototype.
- No autonomous diagnosis, medication selection or prescribing.
- No mandatory recording of a patient-doctor conversation.
- The post-hackathon path may be a private-sector pilot, government/institutional pilot, further validation or paused development. None is guaranteed.

## G. Status vocabulary

- **Approved product direction:** the Product Owner has approved the capability or direction.
- **Approved feature requirement:** the expected behavior is approved, but implementation may still require a task and release plan.
- **Implemented:** code has been reported or evidenced as built.
- **Tested:** the specified tests have passed; scope and test evidence must be stated.
- **Accepted:** the Product Owner has explicitly accepted the delivered result.
- **Proposed future capability:** documented for consideration; not approved for implementation.
- **Excluded:** not permitted within the stated scope.
- **Pending decision:** requires an explicit Product Owner decision.

Approval of V2.5 does not imply that all modules are implemented, tested, accepted or production-ready.

---

# Part II — Practice Operations: Active Baseline

The following Practice Operations requirements remain active from the complete V2.3 baseline unless expressly amended in V2.5:

1. Facility-centric organization and branch management.
2. Organization and branch data isolation.
3. Doctor entries and optional doctor login.
4. Patient registration, search, duplicate handling and family/shared-mobile-number considerations.
5. Appointment creation, changes, status management and double-booking protection.
6. Doctor schedules, facility defaults and availability visibility.
7. Walk-in registration and queue placement.
8. Unified queue management, manual queue changes and queue audit history.
9. One-page daily appointment board and mobile-friendly interaction.
10. Role- and permission-controlled actions.
11. Appointment confirmations and reminders through independently configurable WhatsApp and SMS capabilities, subject to provider availability.
12. External advance-payment confirmation and minimal appointment payment state.
13. Patient Queue Visibility, including DQDS and PQT, under the approved product decision.
14. Queue recovery and repositioning under the approved role permissions and audit requirements.
15. BanglaNameSense patient-name assistance, preserving manual entry and existing patient-registration safeguards.
16. Operational reports and estimates that do not overstate certainty.
17. Security, tenant isolation, audit, reliability and mobile-friendly design.
18. One-command local application restartability and documented operational workflows, as separately implemented and accepted.
19. Existing product exclusions and release gates except where expressly amended by V2.5.

The complete detailed Practice Operations specification, including original acceptance criteria and historical approval annotations, is preserved in Appendix A. Appendix A is a traceability source; where its wording conflicts with this V2.5 active interpretation, V2.5 governs.

---

# Part III — Clinical Management: Functional Requirements

## 29. Clinical Management — Purpose and Boundaries

### 29.1 Purpose

Clinical Management provides optional, organization-scoped tools for doctors to document individual consultations, create and maintain finalized prescriptions, and retrieve records created within the authorized healthcare organization.

It is designed as a practical clinical documentation layer, not as a complete hospital information system or national electronic health-record repository.

### 29.2 Included capabilities

Subject to module activation and permissions, Clinical Management may provide:

- Patient-linked encounter records.
- Consultation dates, times and responsible doctor.
- Structured clinical-note templates.
- Doctor-authored free-text notes.
- Symptoms and patient-reported information.
- Examination findings actually observed and entered by an authorized clinician.
- Assessment or diagnosis entered/confirmed by the doctor.
- Treatment and non-medication plans.
- Doctor-created prescriptions.
- Medicine catalogue search and selection.
- Dosage, route, frequency, duration and instruction fields.
- Reusable prescription templates.
- Doctor-specific favourite medicines.
- Common instruction shortcuts.
- Printable/downloadable prescriptions.
- Encounter history and prescription retrieval.
- Auditable corrections and amendments.

### 29.3 Explicit boundaries

Clinical Management is not automatically:
- A complete EMR/EHR/HMS.
- A national or cross-clinic patient-history repository.
- A pharmacy inventory or dispensing system.
- A laboratory or radiology information system.
- A billing, insurance or claims adjudication system.
- A telemedicine service.
- An autonomous diagnostic or prescribing system.
- A substitute for clinical examination, professional judgment or professional accountability.

### 29.4 Relationship to AMSDP Core

- A patient may have an AMSDP appointment record without any clinical record.
- A clinical encounter must be created intentionally by an authorized user; it must not be fabricated merely because an appointment was booked, checked in, queued or completed.
- Appointment status and clinical encounter status are separate.
- A clinic can use AMSDP Core without activating Clinical Management.
- Clinical Management failure must not block appointment or queue operations.

## 30. Module Activation, Entitlements and Commercial Controls

### 30.1 Tenant and branch entitlements

- Clinical Management is activated at the subscribing organization level.
- Branch-level availability may be configured by an authorized organization administrator, subject to plan policy.
- A module purchase does not automatically grant every user clinical access.
- Backend authorization must enforce module entitlements and individual permissions.
- Hiding a menu item is not sufficient enforcement.

### 30.2 User authorization

- Clinical access is granted only to authorized users with appropriate organizational, branch and professional scope.
- Doctor permissions must be explicitly associated with the organization and applicable clinical workspace.
- Receptionists and assistants do not gain access to clinical notes or prescriptions merely because they manage appointments.
- Any delegated documentation support must be separately permissioned and audited.
- A doctor working at multiple organizations sees separate organization-scoped records.

### 30.3 Commercial decisions not fixed by this list

Pending:
- Module packaging and subscription price.
- Pricing by organization, branch, doctor, seat or usage.
- Whether prescription features are bundled with Clinical Management.
- AI usage allowance and overage pricing.
- Trial, pilot, cancellation and refund policy.
- Suspension, export, retention and read-only behavior after subscription expiry.
- Applicable taxes and local payment arrangements.

No paid provider, model, cloud or messaging expenditure is authorized by this specification.

### 30.4 Module lifecycle

Support states such as:
- Not available on plan.
- Available but not purchased.
- Purchased but not configured.
- Enabled.
- Temporarily unavailable.
- Suspended by authorized governance.
- Expired or cancelled.

Disabling a module must not silently delete records. Export, retention and lawful deletion must follow approved policy and applicable law.

## 31. Encounter and Consultation Workspace

### 31.1 Encounter creation

An authorized doctor should be able to:
1. Open the correct organization-local patient record.
2. Review records the doctor is permitted to access.
3. Start a consultation/encounter.
4. Associate it with the relevant appointment where applicable.
5. Record notes manually or use an approved template.
6. Save a draft.
7. Review and finalize the note.
8. Create or review a prescription.
9. Record follow-up instructions.
10. Complete the encounter according to the approved workflow.

### 31.2 Encounter states

The detailed encounter state model must distinguish at least:
- Draft.
- In progress.
- Pending doctor review.
- Finalized.
- Amended.
- Cancelled/entered-in-error, where policy permits.

A draft must never be represented as finalized. A finalized record must not be silently overwritten.

### 31.3 Encounter metadata

Where relevant, retain:
- Patient and organization references.
- Branch and doctor references.
- Appointment reference, if applicable.
- Encounter date/time.
- Created-by and finalized-by identities.
- Draft/final status.
- Version and amendment history.
- Source of imported or generated content.

## 32. Clinical Notes and Templates

### 32.1 Structured note template

The system should support configurable note templates with fields such as:
- Chief complaint.
- History of present illness.
- Relevant history.
- Current medicines, if known and recorded.
- Known allergies, if known and recorded.
- Review of systems, where used.
- Vital signs, only when actually measured and entered.
- Examination findings, only when actually performed and entered.
- Assessment/diagnosis entered or confirmed by the doctor.
- Investigation advice, where applicable.
- Treatment/management plan.
- Non-medication advice.
- Follow-up instructions.

Templates must allow irrelevant fields to remain blank. The system must not force a doctor to populate information that was not obtained.

### 32.2 Template library

- Provide a general consultation template.
- Permit organization-approved templates.
- Permit authorized doctors to create personal reusable templates.
- Support specialty-specific templates as separately configured options.
- Maintain template version and author.
- Do not imply that a template is a clinical guideline or treatment protocol unless separately reviewed and approved as such.
- Template changes must not retroactively alter finalized notes.

### 32.3 Manual documentation

- Provide free-text fields and structured fields.
- Support Bangla, English and Unicode.
- Preserve clinically meaningful text.
- Support save draft, edit, review and finalize.
- Provide clear save-state feedback.
- Maintain author, editor, timestamp and version metadata.
- Manual documentation must work without AI, microphone permission or internet access to an AI provider, subject to the platform's own availability.

### 32.4 Information provenance

The interface and data model must distinguish:
- Patient-reported information.
- Clinician-observed findings.
- Clinician-entered assessment.
- Imported information.
- AI-generated draft text.
- Clinician-confirmed final content.

AI inference must never be mislabeled as a patient statement or clinical observation.

## 33. Digital Prescription Management

### 33.1 Purpose

Enable authorized doctors to create, review, approve, store, print and retrieve prescriptions without requiring AI.

### 33.2 Prescription content

Where applicable:
- Patient identity and relevant demographic information.
- Healthcare organization and branch.
- Doctor identity and professional registration details, where required.
- Prescription date and encounter reference.
- Medicine name and catalogue reference.
- Generic/brand designation, where available.
- Strength and formulation.
- Dose.
- Route.
- Frequency.
- Duration.
- Quantity and refills, where applicable.
- Special instructions.
- Non-medication advice.
- Follow-up advice.
- Doctor signature/approval metadata.

Required fields and legal format must be validated with qualified Bangladesh clinical/legal review before production use.

### 33.3 Prescription workflow

- Doctor selects or enters medicines.
- Doctor enters or verifies all required prescribing fields.
- System validates completeness and highlights missing or inconsistent fields.
- Doctor previews the prescription.
- Doctor explicitly finalizes it.
- Finalized prescription is stored as an immutable version for ordinary users.
- Reprints reproduce the approved version.
- Corrections create an auditable amendment or replacement version; they do not erase the original.
- Voiding/cancellation requires authorization and a recorded reason.

### 33.4 No AI autonomous prescribing

- AI must not independently choose a medicine based on symptoms.
- AI must not silently add an inferred medicine to a prescription.
- AI must not invent strength, dose, route, frequency, duration, quantity or refills.
- AI may recognize and format explicitly doctor-dictated medicine details.
- Ambiguous medicine matches must be shown for doctor resolution.
- The doctor is responsible for verifying and approving the final prescription.

### 33.5 Printing and retrieval

- Generate a readable, printable prescription.
- Support appropriate Bangla and English rendering.
- Preserve prescription version, date and doctor identity.
- Permit authorized retrieval of historical prescriptions within the originating organization.
- Do not expose prescription details on public queue displays or unauthenticated pages.

## 34. Prescription Support Library

### 34.1 Medicine catalogue

- Maintain a controlled catalogue of medicine names and relevant attributes.
- Support search by generic name and brand name where verified.
- Display strength, formulation and other disambiguating details where available.
- Record catalogue source, version and maintenance date.
- Catalogue licensing and update responsibilities must be resolved before production use.
- Do not imply that catalogue inclusion is a clinical recommendation or endorsement.

### 34.2 Autocomplete and matching

- Offer search and autocomplete as the doctor types.
- Display sufficiently distinct medicine candidates.
- Require explicit doctor selection.
- Flag ambiguous names and strength/formulation mismatches.
- Do not auto-select a medicine merely because it is the highest-ranked text match.
- Preserve the doctor's entered text if no safe catalogue match exists, subject to validation rules.

### 34.3 Doctor favourites

- Allow a doctor to save frequently used medicines.
- Allow doctor-configured default instructions only where explicitly entered and reviewed.
- Favourites are shortcuts, not treatment recommendations.
- Favourites must be scoped to the correct doctor and organization.
- A favourite must never be silently inserted into a prescription.

### 34.4 Reusable prescription templates

- Permit reusable combinations or patterns where approved by the doctor.
- Require the doctor to review patient-specific details every time.
- Show that a template is a starting point, not an automatic prescription.
- Changes to a template must not alter previously finalized prescriptions.
- Provide an option to create organization-approved templates with governance controls.

### 34.5 Common instruction library

- Allow reusable common instructions.
- Support Bangla and English instruction text where validated.
- Allow doctor-specific and organization-approved entries.
- Require review before insertion into a prescription.
- Do not infer that an instruction is appropriate for every patient.

## 35. Encounter History and Record Retrieval

### 35.1 Initial scope

The initial Clinical Management record model is encounter-based and organization-scoped.

It may display:
- Previous finalized consultation notes created within the organization.
- Historical prescriptions created within the organization.
- Encounter dates and responsible doctors.
- Auditable amendments.
- Other records only where a separately approved capability and lawful basis exist.

### 35.2 Not a centralized medical-history repository

- AMSDP does not initially maintain a nationwide patient medical-history repository.
- A patient visiting two unrelated clinics does not automatically have their records merged.
- One clinic cannot automatically browse another clinic's records.
- Cross-organization sharing requires a separate approved legal, product and technical design.
- The system must not claim to know a patient's complete medical history when it only holds encounter records from one facility.

### 35.3 Patient access

- Provide an authorized process for a patient to request or obtain their historical prescriptions and other personal data, subject to applicable law and identity verification.
- Provide downloadable or printable copies where approved.
- Preserve provenance and authenticity indicators.
- Access requests must not permit unauthorized alteration of finalized records.
- Correction requests must follow an auditable process.
- Deletion requests must be evaluated against applicable retention and legal obligations.

### 35.4 Identity matching

- Keep organization-local patient identity separate from global identity assumptions.
- Avoid automatic cross-clinic identity matching.
- Handle shared phone numbers and family records according to existing patient-registration rules.
- Duplicate resolution must be authorized and auditable.
- Do not merge clinical records solely on a name or mobile-number match.

## 36. Intelligent Clinical Documentation Assistant

### 36.1 Product intent

The Intelligent Clinical Documentation Assistant is an optional clinician-facing productivity module. Its purpose is to reduce repetitive typing and documentation effort while preserving the doctor's professional control.

It is a documentation assistant, not an AI doctor, diagnostic engine or autonomous prescriber.

### 36.2 Initial capabilities

- Private doctor-only voice dictation.
- Bangla and English speech-to-text, with mixed-language support as a validation target.
- AI-assisted structuring of the doctor's dictated clinical note.
- Extraction of medicine names and instructions explicitly stated by the doctor.
- Matching dictated medicine text against the maintained catalogue.
- Draft preparation for doctor review.
- Clear display of uncertain or incomplete fields.
- Manual editing and correction.
- Explicit doctor approval before finalization.

### 36.3 Explicitly excluded initial workflow

- Mandatory recording of the patient-doctor conversation.
- Ambient listening during a consultation.
- Requiring a doctor to speak to an AI assistant in front of a patient.
- Showing the patient that the doctor is asking AI to select treatment.
- AI independently deciding a diagnosis or medication.
- Automatic finalization of notes or prescriptions.
- Concealed autonomous clinical decision-making.

Full patient-doctor conversation recording is not part of the initial scope. Any future proposal requires a separate product decision, legal and clinical review, consent design, privacy assessment, provider review and retention policy.

### 36.4 Two optional dictation modes

**Note Mode**
- Doctor dictates clinical findings and intended documentation.
- Speech-to-text produces a transcript.
- AI structures the doctor's words into the approved note template.
- Unspoken findings are not invented.
- Doctor reviews, edits and approves.

**Prescription Mode**
- Doctor dictates medicine names and the prescribing instructions they have decided.
- System transcribes the dictation.
- Catalogue matching presents candidate medicines.
- Missing or ambiguous medicine attributes are flagged.
- Doctor resolves ambiguity and verifies every prescribing field.
- Doctor explicitly approves the prescription.

The two modes may be used independently. Neither requires the patient conversation to be recorded.

### 36.5 Private workflow

- Dictation is initiated intentionally by the doctor from an authorized workspace.
- The UI clearly indicates microphone status.
- The doctor can pause, resume, stop, discard or retry.
- The feature must not start recording automatically when a patient record opens.
- The doctor must be able to use the feature in a private documentation step after the consultation.
- The doctor can choose manual entry instead.
- The product must not imply that patient-consultation recording is occurring when only doctor dictation is active.

### 36.6 Transcription and language requirements

Evaluate:
- Bangla speech.
- English speech.
- Bangla-English mixed speech.
- Medical terminology.
- Medicine brand and generic names.
- Strengths, units and quantities.
- Dosage and frequency phrases.
- Numbers and durations.
- Accents and dialect variation relevant to the target deployment.

Do not claim reliable Bangla medical transcription until it has been tested on representative, properly authorized data.

### 36.7 Draft integrity

- Preserve the original recognized transcript for the approved retention period, if retention is justified.
- Clearly distinguish transcript from structured note.
- Mark uncertain words, numbers and medicine matches.
- Do not silently normalize a medicine name to a different medicine.
- Do not silently convert a number, unit, frequency or duration.
- Preserve doctor corrections and approval metadata.
- AI output cannot directly write a finalized clinical record.

## 37. AI-Assisted Prescription Preparation — Safety Boundaries

### 37.1 Permitted assistance

The system may:
- Recognize a medicine name explicitly dictated or selected by the doctor.
- Search and match the text against the verified medicine catalogue.
- Display candidate matches with strength and formulation for doctor selection.
- Organize explicitly dictated dosage and instructions into structured fields.
- Identify missing or ambiguous fields.
- Insert doctor-approved reusable instructions when explicitly selected.
- Prepare an editable draft.

### 37.2 Prohibited behavior

The system must not:
- Independently choose a medicine based on symptoms.
- infer that a medicine should be prescribed because it is common for a condition.
- silently add a medicine that the doctor did not dictate or select.
- invent a strength, dose, route, frequency, duration, quantity or refill.
- convert an uncertain transcription into a confident prescription entry.
- use a doctor's favourites as automatic treatment recommendations.
- finalize, sign or issue a prescription.
- present a catalogue match as clinical validation.

### 37.3 Ambiguity handling

- Show multiple possible medicine matches where appropriate.
- Require explicit doctor selection.
- Flag unclear strength, formulation or units.
- Ask the doctor to clarify missing prescribing information.
- Allow manual entry under approved validation rules.
- If confidence is insufficient, abstain from matching rather than guess.

### 37.4 Doctor accountability

- The doctor reviews the final medicine and all prescription details.
- Approval must be an explicit action.
- Record who approved the prescription and when.
- AI processing metadata may be retained for traceability without duplicating unnecessary patient content.
- Clinical accountability remains with the responsible registered doctor under applicable professional rules.

## 38. Roles and Permissions for Clinical Modules

### 38.1 Doctor

Subject to organization, branch and module entitlements:
- View authorized patient records.
- Create and edit draft encounter notes.
- Use templates and favourites.
- Dictate notes privately if enabled.
- Create and edit prescription drafts.
- Review and finalize clinical notes and prescriptions.
- Amend finalized records through an auditable process.
- Retrieve authorized encounter history.

### 38.2 Receptionist

- Continue appointment and queue operations under existing permissions.
- Does not receive access to clinical notes or prescriptions by default.
- May access only the minimum clinical workflow information expressly authorized for a legitimate operational task.
- Cannot finalize or amend clinical notes or prescriptions unless a separate approved role decision explicitly grants a narrowly scoped permission.

### 38.3 Assistant

- Access only explicitly delegated functions.
- No default authority to diagnose, prescribe, approve or amend clinical records.
- Any delegated data-entry support must identify the actual author and the responsible clinician.

### 38.4 Organization and branch administrators

- Manage module entitlements and authorized user access.
- Do not automatically receive clinical access solely by virtue of administrative status.
- Access to clinical content must be separately permissioned and justified.
- Administrative access and clinical authorship must remain distinct.

### 38.5 Audit

Record relevant events including:
- Record creation.
- Record view/access where required by policy.
- Draft save.
- Edit.
- Finalization.
- Prescription approval.
- Amendment.
- Void/cancellation.
- Export or patient access request.
- Permission change.
- Module activation/deactivation.

Audit records should include actor, role, organization/branch, timestamp, action and relevant record reference.

## 39. Patient Data Governance, Privacy and Retention

### 39.1 Core principle

Patient personal data is not an asset that AMSDP or a healthcare organization may claim to own outright. The patient is the individual to whom the data relates and has applicable rights under law.

The healthcare organization is responsible for the lawful collection, creation, maintenance and use of records for its healthcare operations, according to its actual legal role. AMSDP's controller/processor or other legal role must be determined by its actual purposes and activities, not merely by the label used in a contract.

### 39.2 Data categories

Keep distinct:
- Patient identity and registration data.
- Appointment and queue operational data.
- Encounter notes.
- Finalized prescriptions.
- Doctor dictation audio.
- Transcription text.
- AI-generated drafts.
- Doctor-approved final records.
- Audit and technical operational data.

### 39.3 Audio policy

- Raw doctor dictation audio is temporary processing data by default.
- The initial product does not record the full patient-doctor conversation by default.
- Audio should be deleted after successful transcription and required verification, unless a separately approved lawful retention purpose applies.
- Temporary copies, caches and provider-side copies must be covered by the deletion and retention design.
- The product must not promise deletion until provider and infrastructure behavior has been verified.
- Retention periods and any exception require Bangladesh-specific legal review and an approved policy.
- A patient-data disclosure or notice must accurately describe the processing that occurs.

### 39.4 Transcript policy

- Retaining a transcript is a separate decision from retaining audio.
- The transcript may contain sensitive health information.
- Retain only where there is a defined, lawful and approved purpose.
- The doctor-approved note and prescription are distinct from the raw transcript.
- Transcript retention, correction, access and deletion must follow the approved record policy.

### 39.5 Third-party processing

Before sending identifiable or sensitive patient data to a speech or AI provider:
- Review legal basis and transparency requirements.
- Review provider security, retention, training-use and deletion terms.
- Review data location and cross-border transfer implications.
- Establish appropriate contractual and technical safeguards.
- Minimize transmitted data.
- Disable provider training/use where contractually and technically available and required by policy.
- Do not use consumer AI accounts or unapproved services for real patient data.

### 39.6 Patient rights and records access

- Provide a documented channel for patients to request access to their personal data and historical prescriptions.
- Verify requester identity and authority.
- Respond according to applicable law and policy.
- Preserve the distinction between access rights and the ability to edit finalized clinical records.
- Evaluate correction and deletion requests against applicable recordkeeping duties.
- Cross-organization disclosure requires its own lawful basis and authorization.

### 39.7 Security

- Enforce tenant and branch isolation.
- Use role-based and least-privilege access.
- Encrypt data in transit and at rest according to the approved architecture.
- Protect secrets and provider credentials.
- Avoid patient data in public endpoints, queue displays and ordinary logs.
- Apply secure backup, restore, export and deletion controls.
- Test authorization on backend endpoints and background jobs.
- Maintain an incident response process.

### 39.8 Legal review

The feature list is not legal advice. Before production clinical use, obtain Bangladesh-qualified legal and professional review of:
- Personal Data Protection Act, 2026 and applicable commencement/rules.
- BM&DC professional and telemedicine requirements, where applicable.
- DGDA guidance relevant to healthcare AI and medical software.
- Prescription format and electronic approval/signature requirements.
- Clinical record retention.
- Patient access, correction and deletion.
- Consent and transparency.
- Third-party processing and cross-border transfer.

## 40. AI Provider-Neutral Architecture and Operational Controls

### 40.1 Provider abstraction

- Keep speech-to-text and LLM providers behind replaceable service interfaces.
- Do not hard-code the product to one AI provider.
- Record provider/model version for traceability.
- Support local or approved deployment options if later validated and funded.
- Do not add microservices solely for speculative future scale.

### 40.2 Processing boundaries

- AI receives only the content required for the task.
- AI output is untrusted draft content.
- Validate model output against an expected schema.
- AI output cannot directly mutate or finalize clinical records.
- Prompt injection or malicious content inside dictated text must not override system policy.
- Provider failure must not block manual documentation.
- Retry logic must avoid duplicate notes, prescriptions or charges.

### 40.3 Traceability

Where applicable, record:
- Provider and model identifier/version.
- Processing timestamp.
- Task type.
- Input record/version reference.
- Output version/reference.
- Error or abstention state.
- Configuration/prompt version.

Avoid duplicating patient content in technical logs.

### 40.4 Quality evaluation

Before clinical use, evaluate:
- Bangla transcription accuracy.
- English transcription accuracy.
- Mixed-language transcription accuracy.
- Medical terminology recognition.
- Medicine matching accuracy.
- Numbers, units, strength, dose and frequency accuracy.
- Hallucinated or omitted content.
- Structured note factual consistency.
- Clinician correction rate.
- Latency, availability and cost.

Use synthetic or appropriately de-identified data wherever possible. Real-patient data use requires an approved governance basis.

## 41. Clinical Reporting and Analytics

Potential organization-scoped reports:
- Consultation volume.
- Notes pending review.
- Finalized consultation count.
- Prescription count.
- Documentation completion status.
- AI dictation usage and processing failures.
- Correction rates and unresolved transcription fields.
- Module usage and subscription utilization.

Restrictions:
- Do not treat AI acceptance rate as proof of clinical correctness.
- Do not rank doctors using simplistic clinical outcome metrics.
- Do not expose identifiable patient data in aggregate reports without authorization and necessity.
- Do not claim time savings or improved outcomes without valid measurement.
- Clinical analytics and performance management require separate approval.

## 42. Failure Modes and Degraded Operation

The system must handle:
- Microphone unavailable or permission denied.
- Speech-to-text provider unavailable.
- AI provider timeout.
- Network interruption.
- Catalogue unavailable.
- Clinical history unavailable.
- Subscription expiry.
- Permission revoked during a session.
- Corrupt or incomplete AI output.

Expected behavior:
- Manual note and prescription entry remains available to authorized users.
- No AI failure blocks appointment or queue operations.
- Incomplete AI output is never represented as final.
- Drafts are safely preserved where possible.
- Duplicate processing and duplicate prescriptions are prevented.
- Missing context and failed checks are clearly shown.
- No data is silently lost or silently finalized.
- Subscription expiry follows an approved access/export/retention policy.

## 43. Clinical Acceptance Criteria and Release Gates

### 43.1 Clinical Management foundation

- Correct patient and organization association.
- Tenant and branch isolation.
- Unauthorized users cannot access clinical records.
- Draft and finalized states are distinguishable.
- Author, editor, timestamp and version history are preserved.
- Manual documentation works without AI.
- Appointment completion does not fabricate a clinical note.
- Encounter records are separate from appointment status.

### 43.2 Digital prescriptions

- Only authorized doctors can approve/finalize prescriptions.
- Required fields are validated according to approved policy.
- Prescription preview matches the approved record.
- Bangla and English output is legible.
- Reprint preserves the approved version.
- Amendments and voids are audited.
- Unauthorized users cannot alter finalized prescriptions.
- No AI suggestion is automatically prescribed.

### 43.3 Prescription support library

- Catalogue source and version are traceable.
- Search results distinguish strength and formulation.
- Ambiguous matches require explicit doctor selection.
- Favourites do not auto-populate final prescriptions.
- Template use requires patient-specific review.
- Catalogue unavailability does not corrupt manual entry.

### 43.4 Private dictation and AI documentation

- Dictation starts only after explicit doctor action.
- The interface indicates microphone state.
- No ambient patient-conversation recording occurs by default.
- Note Mode and Prescription Mode are distinguishable.
- Bangla, English and mixed-language quality is evaluated.
- Uncertain words, numbers and medicine matches are flagged.
- AI does not invent vital signs, examination findings, diagnoses or history.
- AI output remains a draft.
- Doctor can edit, reject or approve.
- Only doctor-approved content becomes final.

### 43.5 Privacy and security

- Tenant isolation is tested across endpoints and background jobs.
- Role/permission tests cover all clinical actions.
- Sensitive data is absent from public endpoints and ordinary logs.
- Provider retention and data-use terms are reviewed.
- Audio deletion behavior is verified end-to-end.
- Patient access and correction workflows are tested.
- Backup/restore and export preserve record integrity.
- Applicable Bangladesh legal and professional review is complete before production use.

## 44. Roadmap and Release Boundaries

The following is a recommended sequence, not an automatic implementation authorization or fixed schedule.

| Phase | Scope | Release gate |
|---|---|---|
| R0 | Stabilize current AMSDP Core, PQV, BanglaNameSense and operational reliability | Existing MVP acceptance |
| R1 | Clinical workflow discovery, legal/privacy review, module entitlements and data model | Explicit clinical-module implementation approval |
| R2 | Manual encounter notes, structured templates and audit trail | Clinical access and record-integrity acceptance |
| R3 | Digital prescriptions, medicine catalogue, favourites, reusable templates and common instructions | Doctor approval, catalogue governance and print validation |
| R4 | Private doctor-only dictation and transcription | Privacy, provider, transcription-quality and cost gates |
| R5 | AI-assisted note structuring and prescription preparation from doctor-provided instructions | Clinical validation and doctor-review acceptance |
| R6 | Encounter summaries, advanced history, approved integrations and analytics | Separate product, legal and interoperability approval |

The current hackathon release remains governed by the approved Core scope and explicit task-level approvals. A roadmap entry does not authorize implementation.

## 45. Product Decisions and Governance Register

### 45.1 Approved by this V2.5 consolidation

1. Revised Section C — Product Family and Module Catalogue.
2. Product direction and naming: **AMSDP — Intelligent Clinical Documentation**.
3. Structured clinical-note templates and manual documentation as foundational Clinical Management capabilities.
4. Digital Prescription Management independent of AI.
5. Prescription Support Library: medicine catalogue, autocomplete, favourites, reusable prescription templates and common instruction library.
6. Private doctor-only voice dictation as the intended initial AI documentation workflow.
7. No mandatory patient-doctor conversation recording.
8. No requirement for doctors to interact with AI in front of patients.
9. AI organizes doctor-provided content; it does not independently choose treatment.
10. AI-generated notes and prescription drafts require explicit doctor review and approval.
11. Initial encounter history is organization-scoped; no automatic cross-clinic history sharing.
12. Patient personal data is not treated as property owned outright by AMSDP or the clinic.
13. Existing AMSDP Core, PQV and BanglaNameSense approved requirements remain active.
14. V2.5 supersedes prior Master Feature List versions as the sole active specification.

### 45.2 Still requiring separate decisions

1. Exact clinical module launch scope and implementation schedule.
2. Initial clinical specialties and target facility types.
3. Medicine catalogue source, licensing, maintenance and update process.
4. Prescription format, professional registration display and electronic signature requirements.
5. Required clinical note templates and organization customization policy.
6. Whether vitals, allergies and medication history are included in the first clinical release.
7. Audio/transcript exact retention period and deletion verification.
8. Speech-to-text and LLM provider selection, privacy terms and hosting location.
9. Bangla dialect coverage and minimum accuracy thresholds.
10. AI pricing, quotas, cost controls and subscription packaging.
11. Patient data access-request workflow and operational timelines.
12. Legal retention, correction, export and deletion policy.
13. Any future cross-organization record sharing.
14. Any future patient-doctor conversation recording.
15. Government-system integration and offline/outreach deployment.
16. Whether Clinical Management or a limited Intelligent Clinical Documentation demonstrator is included in a future hackathon release.
17. Real-patient pilot eligibility, clinical oversight and monitoring.
18. Production readiness and final acceptance of each module.

---

# Part IV — Current Hackathon Scope and Delivery Discipline

## 46. Hackathon objective

Deliver a reliable, working demonstration of the approved AMSDP Core workflows, with any separately approved differentiator implemented as a real, bounded vertical slice.

The hackathon is not a mandate to build the entire V2.5 platform.

## 47. Essential operational workflow

The demonstration should prioritize:
1. Organization and branch context.
2. User authentication and role authorization.
3. Patient registration and search.
4. Appointment creation and management.
5. Doctor schedule and availability.
6. Walk-in handling.
7. Queue placement, status and authorized repositioning/recovery.
8. DQDS public waiting-room display with no patient PII.
9. PQT private appointment-specific tracking.
10. BanglaNameSense in patient registration.
11. Persistent database records and auditable state changes.
12. Operational restartability and health checks.

## 48. Clinical documentation demonstrator boundary

If separately authorized for the hackathon, a bounded demonstrator may include:
- A doctor opens an authorized encounter.
- Doctor selects a note template.
- Doctor enters a note manually.
- Doctor selects a medicine from a catalogue or favourites.
- Doctor enters instructions.
- Doctor previews and finalizes the prescription.
- Optional private dictation may prepare a draft from doctor speech.
- Every demonstrated action uses a working API and persists to the database.

A prototype must be labelled as such. No fake AI accuracy, no autonomous medicine selection and no fabricated clinical claims.

## 49. Hackathon exclusions

Unless separately approved:
- Full EMR/EHR/HMS.
- Centralized national medical history.
- Autonomous diagnosis or prescribing.
- Ambient patient-conversation recording.
- Live AI interaction in front of patients.
- Pharmacy dispensing and inventory.
- Laboratory and radiology management.
- Insurance claims and advanced revenue cycle.
- Government-wide integrations.
- Full community-health-worker platform.
- Unvalidated clinical decision support.

## 50. Post-hackathon paths

Possible paths include:
- Private clinic validation and pilot.
- Institutional or government-supported pilot exploration.
- Further research and product validation.
- Limited maintenance or paused development if funding and adoption do not materialize.

No hackathon result, government recognition, funding or commercial adoption is guaranteed.

---

# Part V — Cross-Cutting Non-Functional Requirements

## 51. Security and organizational isolation

- Strict organization/tenant data isolation.
- Branch-scoped access where applicable.
- Server-side role and permission enforcement.
- Least privilege.
- Secure authentication and session handling.
- Protection of secrets and credentials.
- Sensitive data minimization in logs.
- Encryption in transit and at rest according to approved architecture.
- Audit trail for sensitive actions.
- Secure backup, restore, export and deletion.

## 52. Reliability and operational usability

- Clear health/readiness behavior.
- Safe startup, restart and shutdown procedures.
- No loss of persistent database volumes during ordinary restart.
- Repeatable local development startup.
- Clear logs without exposing patient data or secrets.
- Graceful failure of optional providers.
- Core appointment and queue functions remain usable if optional AI or messaging services fail.

## 53. Performance and accessibility

- Mobile-friendly layouts.
- Usable on common low-cost Android devices.
- Large touch targets for reception workflows.
- Clear keyboard navigation and form labels.
- Responsive behavior for desktop and mobile.
- Low-bandwidth operation where feasible.
- Avoid unnecessary polling and expensive AI calls.
- Public display must remain read-only and PII-minimized.

## 54. Audit and traceability

- Identify the actor, role, organization and branch for sensitive actions.
- Preserve timestamps and before/after values where appropriate.
- Maintain queue change and recovery audit history.
- Maintain clinical note and prescription version history.
- Record approval and amendment events.
- Avoid logging secrets or unnecessary clinical content.
- Keep implementation reports and product decisions traceable in the approved documentation structure.

## 55. Claims and impact measurement

- Do not claim zero waiting.
- Do not guarantee consultation start times.
- Distinguish waiting-area occupancy, physical waiting time and total appointment-to-consultation time.
- Do not claim measured reductions without pilot evidence.
- Do not claim AI clinical accuracy without a representative evaluation.
- Do not claim doctor time savings without valid measurement.
- Report operational metrics with definitions, denominators and limitations.

---

# Part VI — Change Control, Approval and Version Authority

## 56. Sole active specification

AMSDP Master Feature List V2.5 is the sole active Master Feature List as of 11 November 2026.

All previous Master Feature List versions are superseded for current product planning, feature interpretation and new implementation work. They may be retained for historical traceability but must not be used as competing active specifications.

## 57. Preservation of prior decisions

Superseding a feature-list document does not automatically revoke every separate Product Owner decision. Existing approved decisions remain active unless V2.5 expressly amends them or a later decision supersedes them.

Where there is conflict:
1. Latest explicit Product Owner decision governs.
2. V2.5 governs the active feature-list scope.
3. Older feature-list versions are historical reference only.
4. Implementation reports describe what was reported or tested; they do not independently approve product scope.
5. No implementation, commit, push, merge, deployment, paid provider purchase or external registration is authorized by silence.

## 58. Change request requirements

Every future change to this master list should include:
- Unique decision or change ID.
- Reason and problem statement.
- Affected module and sections.
- Scope and exclusions.
- Dependencies.
- Data/privacy/clinical implications.
- Commercial implications where relevant.
- Acceptance criteria.
- Approval status.
- Version and change history.

## 59. Document maintenance

- Preserve the full V2.3 baseline in Appendix A.
- Do not overwrite historical versions in place.
- Store new AMSDP documents under the governed `docs/` structure.
- Update the AMSDP documentation index when the document is placed in the repository.
- Distinguish product approval from implementation approval and release acceptance.
- Do not mark proposed capabilities as implemented or accepted without evidence.

---

# Appendix A — Complete V2.3 Historical Baseline (Preserved Verbatim; Not the Active Specification)

The following V2.3 source is retained in full for historical traceability. It is not a competing active specification. V2.5 amendments and decisions govern any conflicting wording.

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


---

# V2.4 Revision History and Change Record

| Version | Date | Status | Summary |
|---|---|---|---|
| V2.0 | 4 November 2026 baseline | Historical draft | Initial facility-centric master feature list. |
| V2.1 | 9 November 2026 | Consolidated draft for review; not approved as a whole | Reconciles approved business/product decisions, incorporates PQV/PQT/DQDS and N1/N2 scope, distinguishes approval from implementation, updates release priorities and adds acceptance/security guardrails. |
| V2.3 | 10 November 2026 baseline | Consolidated draft for Product Owner Review; not approved as a whole | Preserved consolidated baseline, including BanglaNameSense and approval/implementation registers. |
| V2.4 | 11 November 2026 | Modular Healthcare Platform Edition — consolidated draft for Product Owner Review; not approved as a whole | Adds modular product-family architecture; distinguishes AMSDP Core, optional Clinical Management and premium AI Clinical Assistant; defines proposed clinical records, digital prescription, patient history, consent-based recording, transcription, AI draft notes, clinician-reviewed suggestions, privacy, safety, subscription dependencies and proposed release gates. Preserves the complete V2.3 baseline without intentionally removing any existing feature or requirement. |

## V2.4 Change-Control Notes

1. V2.4 does not revoke any previously approved appointment, queue, PQV, notification, missed-turn recovery, BanglaNameSense, localization, security or tenant-isolation decision.
2. Existing feature priorities and implementation statuses are not changed merely by appearing in this document.
3. Clinical Management and AI Clinical Assistant are proposed optional modules; their inclusion in this catalogue is not blanket implementation authorization.
4. Digital Prescription is proposed as a non-AI clinical capability so that a clinic does not need to purchase AI to create doctor-approved prescriptions.
5. AI medication and management suggestions require separate clinical safety approval and must remain subject to doctor review and approval.
6. No AI-generated note, diagnosis, medication or prescription becomes a finalized clinical record without the required clinician action.
7. The current hackathon MVP remains focused on its already-approved scope unless the product owner explicitly changes that scope.
8. No provider, paid service, cloud deployment, production integration, expenditure, commit, push or merge is authorized by this revision.
9. The V2.3 baseline is reproduced in full above Part VIII and remains available for historical comparison.
10. Where V2.3 scope exclusions conflict with the new V2.4 modular product direction, the V2.4 Executive Amendment governs future planning, while the original V2.3 text remains preserved as historical baseline wording.

**End of AMSDP Master Feature List V2.4 — Modular Healthcare Platform Edition.**
