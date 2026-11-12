# AMSDP — Master Feature List V2.4
## Modular Healthcare Platform Edition

**Document date:** 11 November 2026  
**Market focus:** Bangladesh  
**Document status:** Consolidated Draft for Product Owner Review — **NOT APPROVED AS A WHOLE**. Existing approved decisions retain their individual approval status. New clinical-module direction is recorded as a proposed product expansion and does not, by itself, authorize implementation, deployment, expenditure, provider registration, commit, push or merge.  
**Baseline retained:** AMSDP Master Feature List V2.3 (Consolidated Draft), reproduced in full in Part VIII of this document.  
**Change-control principle:** No feature, requirement, decision, exclusion, acceptance criterion or historical note from V2.3 is intentionally removed. V2.4 adds a modular product architecture and an explicitly scoped optional clinical product family. Where an older V2.3 statement conflicts with a V2.4 amendment, the V2.4 amendment below governs for future product planning; the original V2.3 wording remains preserved in the baseline section for traceability.

---

# V2.4 Executive Amendment — Read This Before the Preserved V2.3 Baseline

## A. What V2.4 changes

V2.4 evolves the product description from a narrowly appointment-only product into a **modular healthcare practice platform**, while retaining appointment management as the foundational product and the current hackathon/MVP priority.

The platform has two product families:

1. **Practice Operations** — the existing AMSDP appointment, scheduling, queue, patient-flow, communication and operational capabilities.
2. **Clinical Management and Intelligence** — an optional product family for clinical records, consultation documentation, prescriptions, patient medical history and AI-assisted clinical workflows.

This is an expansion of the product architecture and roadmap. It is not a direction to turn the current MVP into a full hospital information system, nor an instruction to implement all optional modules immediately.

## B. Product positioning amendment

**Updated product description:** AMSDP is a modular, facility-centric healthcare practice platform for Bangladesh. Its foundational product manages patient registration for facility workflows, appointments, schedules, queues and patient-flow visibility. Facilities may separately activate optional clinical capabilities, including clinical records, digital prescriptions and AI-assisted consultation documentation.

**Core product promise remains unchanged:** make daily appointment operations simple, fast, flexible and reliable, while helping facilities improve patient-flow visibility and reduce unnecessary physical waiting.

The approved patient-facing positioning remains:

**AMSDP — Less Waiting. Less Crowding. Better Healthcare Experiences.**

The clinical modules extend the platform; they do not replace or weaken this positioning.

## C. Product family and module catalogue

| Product family | Module | Principal capabilities | Commercial treatment |
|---|---|---|---|
| Practice Operations | AMSDP Core | Organization/facility workspace, users, doctor entries, patient registration, appointments, schedules, walk-ins, queues, audit and operational reports | Foundational subscription |
| Practice Operations | Patient Queue Visibility (PQV) | Digital Doctor Queue Display (DQDS) and Personal Queue Tracking (PQT) | Optional add-on, plan inclusion or bundle; plan decision remains configurable |
| Practice Operations | Patient Communication | Approved one-way WhatsApp and SMS appointment/queue notifications | Optional capability; provider and usage costs apply |
| Practice Operations | Analytics & Reports | Appointment, queue, utilization and operational reporting | Optional tier/add-on where commercially approved |
| Clinical Management | Clinical Records & Consultation | Encounter/consultation records, doctor-authored clinical notes, diagnoses, examination findings, plans and follow-up | Separately activatable clinical module |
| Clinical Management | Digital Prescription | Doctor-authored, reviewed, approved, stored, printable/downloadable prescriptions | Separately activatable; does not require AI |
| Clinical Management | Patient Medical History | Longitudinal, organization-scoped clinical history and encounter timeline | Depends on Clinical Management |
| Clinical Intelligence | AI Clinical Assistant | Consent-based audio capture, speech-to-text, AI-generated draft notes, clinician-reviewed suggestions and documentation assistance | Premium optional add-on; depends on Clinical Management |
| Clinical Intelligence | Clinical Summaries & Follow-up | Draft summaries of prior encounters and follow-up information for clinician review | Optional future capability; depends on Clinical Management |

**Commercial principle:** a facility may subscribe to AMSDP Core without purchasing Clinical Management or AI Clinical Assistant. A facility may use Clinical Management without purchasing AI Clinical Assistant. AI Clinical Assistant is an add-on, not a prerequisite for basic clinical records or digital prescriptions.

The precise plan names, prices, billing units, usage limits, bundles, trial rules and entitlements are not decided by this feature list.

## D. Dependency model

The intended logical dependency is:

```text
AMSDP Core
├── Practice Operations
│   ├── Patient Queue Visibility (DQDS + PQT)
│   ├── Patient Communication (WhatsApp + SMS)
│   └── Operational Analytics
└── Clinical Management [optional paid module]
    ├── Clinical Records & Consultation
    ├── Digital Prescription
    ├── Patient Medical History
    └── AI Clinical Assistant [optional premium add-on]
        ├── Consent-based audio capture
        ├── Speech-to-text
        ├── AI draft clinical notes
        ├── AI clinical suggestions
        └── Clinician review and approval
```

- AMSDP Core is the platform foundation.
- Clinical Management requires an active AMSDP Core tenant.
- AI Clinical Assistant requires both AMSDP Core and Clinical Management.
- Digital Prescription and ordinary clinical documentation must work without AI.
- Disabling or not purchasing AI must not disable access to a facility's existing clinical records or finalized prescriptions, subject to the facility's subscription, retention and export policies.
- Module dependencies must be enforced server-side, not merely hidden in the user interface.

## E. Scope and precedence amendments to V2.3

The following V2.3 passages remain preserved in the baseline below but are amended for V2.4 planning:

| V2.3 reference | V2.3 position | V2.4 interpretation |
|---|---|---|
| §2, lines describing AMSDP as not a PMS/EMR/EHR | AMSDP is not a complete HMS, EMR/EHR or PMS | AMSDP remains not a full HMS. It may offer optional, bounded clinical-record and practice-management capabilities. It must not be represented as a comprehensive hospital information system or full enterprise EHR. |
| §3.2, clinical exclusions | Clinical notes, prescriptions and full clinical history are excluded | These are excluded from AMSDP Core, but are candidates for the optional Clinical Management module under this V2.4 amendment. |
| §4.4, facility-owned patient records | Patient records support appointment operations | Core patient identity/registration remains separate from optional clinical records. Clinical data is added only when Clinical Management is activated and authorized. |
| §4.5, appointment-first | AMSDP is not the clinical system of record | Appointment-first remains the core product principle. An activated Clinical Management module may become the facility's system of record for the clinical records created and maintained within that module. |
| §5.4, doctor workspace | Doctor access limited to appointments and queues | The existing appointment role remains. With module entitlement and explicit clinical permissions, doctors may additionally use Clinical Management. |
| §21, exclusions | Prescriptions, diagnoses, clinical notes and EMR excluded | Excluded from Core, not excluded from the overall modular platform. |
| §23, optional extensions | Appointment-related extensions only | Clinical Management and AI Clinical Assistant are optional product-family extensions, subject to separate approval and release planning. |
| §26.10, safety | Existing appointment/PQV safety rules | Retain all existing guardrails and add the clinical privacy, consent, AI and prescribing safeguards in Part VII below. |

No existing appointment, queue, PQV, notification, BanglaNameSense, tenant-isolation, security or acceptance requirement is removed by these amendments.

## F. Non-expansion of current hackathon MVP

Unless the product owner separately approves a scope change:

- The current hackathon delivery remains focused on the approved AMSDP Core and its already-approved MVP/P0 features.
- Clinical Management is a future optional product module; its addition to this master catalogue is not implementation authorization.
- AI Clinical Assistant is a proposed premium add-on and is not part of the current hackathon release gate.
- No current appointment or queue task should be delayed or destabilized to implement the clinical roadmap.
- Product architecture should avoid blocking future clinical modules, but speculative infrastructure should not be built ahead of a validated requirement.
- Existing features and approved decisions retain their original status.

## G. Status vocabulary for the new modules

The product direction to offer optional Clinical Management and an AI Clinical Assistant is recorded in V2.4 as a **proposed product expansion for owner review**. The detailed functional scope below is a product proposal, not a blanket approval.

Unless explicitly changed by a later product-owner decision:

| Capability | V2.4 product status | Implementation status |
|---|---|---|
| Modular product architecture and independent module entitlements | Proposed for approval | Not authorized by this document |
| Clinical Records & Consultation | Proposed optional module | Pending separate approval and planning |
| Digital Prescription | Proposed optional clinical capability | Pending separate approval and planning |
| Patient Medical History | Proposed optional clinical capability | Pending separate approval and planning |
| Consent-based recording | Proposed AI module capability | Pending separate approval and safety/legal review |
| Speech-to-text | Proposed AI module capability | Pending separate approval and provider assessment |
| AI-generated draft notes | Proposed AI module capability | Pending separate approval and clinical validation |
| AI medication/management suggestions | Proposed; high-risk clinical decision-support capability | Requires separate clinical safety approval; not authorized |
| Clinician approval workflow | Mandatory design constraint if AI clinical functionality is approved | Not implemented by this document |

---

# Part VII — Proposed Optional Clinical Management and Clinical Intelligence Requirements

> **Status notice:** The following sections define a detailed candidate scope for product-owner review. They do not silently approve the clinical modules, certify clinical safety, authorize clinical deployment, or authorize implementation. Each module requires an explicit approval decision and a bounded implementation plan.

## 29. Clinical Product Family — Purpose and Boundaries

### 29.1 Purpose

The Clinical Management product family is intended to let an eligible healthcare facility maintain structured clinical records associated with its patients and consultations, create doctor-reviewed prescriptions, and support continuity of care.

The AI Clinical Assistant is intended to reduce clinicians' documentation burden by helping convert a consultation conversation into a draft transcript and structured note, and by presenting carefully bounded clinical suggestions for clinician review.

The intended workflow is **clinician-led**. The system supports documentation and review; it does not replace the clinician's examination, judgment, diagnosis, prescribing responsibility or patient communication.

### 29.2 What the clinical family is and is not

It may provide:
- Patient-linked consultation/encounter records.
- Doctor-authored and doctor-approved clinical notes.
- Structured assessment and plan.
- Diagnoses recorded by an authorized clinician.
- Examination findings and observations entered by an authorized user.
- Medication and allergy records where supported by a verified workflow.
- Digital prescriptions created and finalized by authorized doctors.
- Patient clinical-history timelines.
- Attachments and investigation results in a separately approved scope.
- AI-assisted transcription and draft documentation.
- AI suggestions that are explicitly unapproved until clinician action.

It is not automatically:
- A complete hospital information system.
- A replacement for laboratory, radiology, pharmacy, billing, insurance or inventory systems.
- A clinical triage engine.
- An autonomous diagnostic or prescribing system.
- A substitute for clinical examination or professional judgment.
- A patient self-service portal or telemedicine service.
- A cross-facility or national health-record exchange.
- A guarantee that AI-generated information is accurate.

### 29.3 Relationship to AMSDP Core

- AMSDP Core remains usable without any clinical module.
- Core patient registration remains available for appointment operations.
- A patient may have an appointment record without having any clinical record.
- A patient may have a clinical record only within an organization that has activated Clinical Management and only where an authorized clinician has created one.
- Clinical records must be linked to the correct organization-local patient record and, where applicable, the relevant appointment/encounter.
- A consultation record must not be fabricated merely because an appointment was booked, checked in or placed in a queue.
- An appointment can be completed operationally without an AI note or digital prescription.
- AI failure must never block appointment operations or ordinary manual clinical documentation.

## 30. Modular Subscription, Entitlements and Activation

### 30.1 Tenant-level entitlement

- Optional modules are enabled at the subscribing organization/tenant level.
- A tenant may purchase AMSDP Core only.
- Clinical Management may be activated independently as an add-on.
- AI Clinical Assistant may be activated only when Clinical Management is active.
- Entitlement checks must be enforced by backend authorization and service logic.
- Hiding a menu item is not sufficient entitlement enforcement.
- Every module must declare its dependencies, permissions, data access, usage limits and failure behavior.

### 30.2 Branch and doctor access

- Organization administrators may configure which eligible branches use an activated module, subject to the plan and platform policy.
- Module activation at organization level does not automatically grant every user clinical access.
- Clinical permissions are granted to authorized users according to role, professional responsibility, branch scope and organization policy.
- A doctor must be explicitly authorized for the relevant organization and clinical workspace.
- Receptionists and assistants do not receive clinical access merely because they can manage appointments.
- Any delegated clinical-support permissions require separate, carefully limited product decisions.
- A doctor working at two organizations sees separate organization-local records; no cross-organization patient history is automatically combined.

### 30.3 Subscription and billing behavior

The following remain pending commercial decisions:
- Plan names and packaging.
- Whether Clinical Management is priced per organization, branch, doctor, seat or another unit.
- Whether Digital Prescription is bundled with Clinical Management.
- AI pricing per minute, consultation, token, user, monthly allowance or hybrid usage.
- Included transcription/LLM quotas.
- Overage pricing and spending caps.
- Trial and pilot policy.
- Suspension, read-only access, export and retention after expiry.
- Refund and cancellation policy.
- Taxes and local payment arrangements.

No paid provider account, model subscription, cloud service or expenditure is authorized by this feature list.

### 30.4 Module lifecycle

A future module lifecycle should support:
- Not available on plan.
- Available but not purchased.
- Purchased but not configured.
- Enabled.
- Temporarily unavailable due to dependency/provider failure.
- Suspended by authorized platform governance.
- Expired or cancelled.

Disabling a module must not silently delete clinical records, prescriptions, transcripts or audit history. Data retention, export and lawful deletion rules require separate approval.

## 31. Clinical Management — Core Functional Scope

### 31.1 Consultation/encounter workspace

An authorized doctor should be able to:
1. Open the relevant organization-local patient record.
2. Review permitted prior clinical history.
3. Start a consultation/encounter associated with the correct patient and, where applicable, appointment.
4. Record consultation information manually.
5. Save a draft.
6. Review and finalize the clinical note.
7. Create or update a prescription.
8. Record follow-up instructions.
9. Complete the clinical encounter under the approved workflow.

The clinical encounter lifecycle should be separately defined and must not be conflated with the appointment lifecycle. A completed appointment does not necessarily mean a clinical note is finalized, and a saved draft note does not mean the consultation is clinically complete.

### 31.2 Clinical note

A clinical note may include the following sections, configured according to facility workflow:

- Patient and encounter reference.
- Consultation date and time.
- Treating doctor.
- Chief complaint.
- History of present illness.
- Relevant past medical history.
- Current medication history.
- Known allergies and adverse reactions.
- Relevant family/social history, where collected.
- Review of systems, where recorded.
- Vital signs, if actually measured and entered from a reliable source.
- Physical examination findings, if actually performed and entered.
- Assessment/diagnosis entered or confirmed by the doctor.
- Differential considerations, if the doctor chooses to document them.
- Investigation orders or results, where supported.
- Treatment/management plan.
- Medication plan.
- Non-medication advice.
- Follow-up instructions.
- Doctor's signature/approval metadata.

The system must distinguish:
- Patient-reported information.
- Clinician-observed findings.
- Imported information from a connected/attached source.
- AI-generated draft content.
- Clinician-confirmed content.

The application must not represent an AI inference as a patient statement or a clinician observation.

### 31.3 Structured and free-text documentation

- Support structured fields and free-text notes.
- Permit doctors to use their preferred concise clinical language.
- Preserve clinically meaningful text and Unicode Bangla/English.
- Support mixed Bangla-English documentation where validated.
- Do not silently translate or normalize clinical meaning.
- Provide explicit save state and draft/final status.
- Preserve author, editor, timestamps and version history.
- Corrections to finalized records must be auditable and must not erase the historical version.

### 31.4 Clinical diagnosis

A diagnosis capability, if approved, should:
- Allow the doctor to enter a diagnosis manually.
- Optionally use a curated terminology/catalogue if selected and licensed.
- Distinguish confirmed diagnosis from provisional assessment or differential consideration.
- Record who entered or confirmed it and when.
- Never convert an AI suggestion into a confirmed diagnosis automatically.
- Never infer a diagnosis solely from a medication or transcription.
- Avoid forcing a diagnosis when the doctor has not made one.

The terminology standard, coding system, catalogue source and licensing are pending decisions.

### 31.5 Clinical observations and vital signs

A future capability may record observations such as blood pressure, pulse, temperature, respiratory rate, oxygen saturation, weight, height and other relevant measurements.

Requirements:
- Store value, unit, measurement time and recording source.
- Identify who entered or verified the observation.
- Distinguish measured values from patient-reported values.
- Do not fabricate missing measurements.
- Preserve original values when corrected, with an audit trail.
- Define supported units, validation ranges and outlier warnings through clinical review.
- Do not interpret a measurement as a diagnosis without clinician review.

This capability is proposed and is not automatically part of the first clinical release.

## 32. Digital Prescription

### 32.1 Product intent

Digital Prescription should allow an authorized doctor to create, review, approve, save, print and download a prescription associated with the correct patient and consultation.

It must be available without purchasing AI Clinical Assistant.

### 32.2 Prescription contents

A configurable prescription may include:
- Facility/clinic identity and contact details.
- Branch/chamber details where applicable.
- Doctor name and professional registration details, if verified and required.
- Patient name and an appropriate patient identifier.
- Patient age or date of birth only when accurately recorded and relevant.
- Prescription date/time.
- Encounter reference.
- Doctor-entered diagnosis/assessment.
- Medication name.
- Generic name where available.
- Brand name if selected by the doctor and available in the approved catalogue.
- Strength and dosage form.
- Dose.
- Route.
- Frequency.
- Duration.
- Quantity.
- Dispensing/refill instructions where applicable.
- Special administration instructions.
- Non-pharmacological advice.
- Investigation requests, if supported.
- Follow-up instructions.
- Doctor's signature/approval representation according to applicable rules.

The application must not invent missing patient demographics, doctor credentials or medication details.

### 32.3 Medication catalogue

If a medication catalogue is introduced:
- Use a verified, maintained source with appropriate licensing.
- Store generic name, brand name where permitted, strength, dosage form and relevant catalogue identifiers.
- Avoid treating free-text similarity as proof that two products are equivalent.
- Display catalogue provenance/version and update date.
- Support manual entry where permitted by the approved clinical policy.
- Do not let an LLM invent a medication catalogue entry.
- Clearly flag unavailable or unmatched medicines rather than silently substituting.

The catalogue provider, content, licensing, local Bangladesh formulary coverage and maintenance owner are pending decisions.

### 32.4 Prescription workflow and states

Suggested states:
1. `DRAFT`
2. `PENDING_DOCTOR_REVIEW` (if AI or delegated drafting is used)
3. `APPROVED`
4. `PRINTED` / `DOWNLOADED` as delivery events, not necessarily clinical states
5. `AMENDED` through a new auditable version
6. `VOIDED` with authorized reason, where legally and operationally appropriate

Only an authorized doctor may finalize/approve a prescription under the approved permission model.

A generated PDF or print preview must not be treated as approved merely because it exists.

### 32.5 Printing and download

- Provide a clean, legible print layout suitable for common clinic printers.
- Support Bangla and English Unicode.
- Support PDF download where technically available.
- Include a unique prescription reference.
- Include doctor and facility details from verified records.
- Make the approved/final status clear.
- Preserve the exact approved prescription version that was printed/downloaded.
- Reprinting must not silently modify the prescription.
- Record print/download actor and timestamp where appropriate.
- Do not expose another patient's prescription through predictable IDs or shared links.

### 32.6 Prescription correction and cancellation

- Do not silently overwrite a finalized prescription.
- Require an authorized amendment or void action with reason.
- Preserve the previous version and approval metadata.
- Make the current valid version unambiguous.
- Prevent unauthorized staff from changing medication, dose or instructions.
- The exact legal rules for prescription amendment, electronic signature and retention require Bangladesh-specific professional/legal review.

## 33. Patient Medical History and Longitudinal Record

### 33.1 Purpose

Provide authorized clinicians with a coherent history of clinical encounters within the same subscribing organization, helping them understand prior consultations and treatment decisions.

### 33.2 Patient history timeline

Where Clinical Management is active, the patient history may display:
- Consultation/encounter date.
- Treating doctor.
- Branch/chamber.
- Chief complaint.
- Approved clinical note.
- Confirmed diagnosis/assessment.
- Finalized prescription.
- Recorded allergies.
- Medication history, where supported.
- Vital observations, where supported.
- Investigation requests and results, where supported.
- Follow-up instructions.
- Amendments and corrections.
- Attachments, where supported.

Drafts must be clearly distinguished from finalized clinical records.

### 33.3 History access

- Clinical history is organization-scoped.
- Branch access is controlled by explicit permissions and the approved clinical access policy.
- Appointment access does not automatically grant clinical-history access.
- Receptionists must not receive clinical access solely through appointment permissions.
- Doctors should access only records required for their authorized work.
- Access to sensitive clinical records should be auditable.
- No automatic cross-organization record matching or sharing is allowed.
- A doctor's employment/association change must not automatically transfer patient records to another organization.

### 33.4 History quality and correction

- Preserve source, author, date and status of each record.
- Distinguish historical imported data from records created in AMSDP.
- Never present missing history as proof that a condition or medication does not exist.
- Support correction through an auditable amendment workflow.
- Avoid automatic merging of patient records.
- If patient identity is uncertain, require human confirmation and do not merge histories automatically.

### 33.5 Patient identity and duplicate handling

The existing V2.3 patient identity rules remain in force:
- Facility/organization-local patient records.
- Shared mobile numbers may represent multiple family members.
- No automatic merge based only on name or mobile number.
- Staff must select the correct patient.
- Clinical records must never be attached to a patient based solely on approximate name matching.
- BanglaNameSense remains a name-entry aid, not an identity verification or patient matching mechanism.

## 34. AI Clinical Assistant — Product Scope

### 34.1 Purpose

AI Clinical Assistant is a premium optional add-on intended to assist an authorized doctor during and after a consultation by:
- Capturing audio where consent and policy permit.
- Converting speech into editable text.
- Preparing a structured draft clinical note.
- Extracting candidate clinical facts for clinician verification.
- Offering bounded, evidence-aware medication and management suggestions for clinician review.
- Helping summarize relevant prior clinical history where authorized.

The AI must remain an assistive drafting and decision-support tool. It must not act as an autonomous clinician.

### 34.2 Consultation workflow

Proposed workflow:

1. Doctor opens the correct patient and encounter.
2. System displays recording status and consent requirements.
3. Doctor obtains and records the required patient consent.
4. Doctor explicitly starts recording.
5. Doctor may pause, resume or stop recording.
6. Audio is processed by the configured speech-to-text component.
7. Transcript is displayed for review and correction.
8. AI prepares a structured draft note from the verified or clearly labelled transcript.
9. AI identifies uncertain, missing or conflicting information.
10. AI may produce separate medication and non-medication suggestion drafts, subject to approved safety controls.
11. Doctor reviews the transcript, note and suggestions.
12. Doctor edits, accepts or rejects content.
13. Doctor finalizes the clinical note.
14. Doctor independently creates and approves any prescription.
15. Approved records are stored in the patient's clinical history.
16. Audio is retained or deleted according to the configured retention policy and applicable consent/legal requirements.

No stage should silently convert AI output into an approved clinical record.

### 34.3 Audio recording controls

The doctor interface should support:
- Start recording.
- Pause recording.
- Resume recording.
- Stop recording.
- Visible recording indicator.
- Clear consent status.
- Clear audio-processing status.
- Error/retry status.
- Manual note entry when recording is unavailable.
- Explicit discard action where permitted.
- Clear indication of whether audio is retained or scheduled for deletion.

Recording must not begin automatically when a doctor opens a patient record or appointment.

### 34.4 Patient consent

Before recording:
- Obtain explicit, informed consent in a language the patient can understand.
- Explain the purpose of recording and AI-assisted documentation.
- Explain whether audio will be retained, for how long and who may access it.
- Record consent outcome, time, method and the responsible staff/doctor.
- Respect refusal without denying ordinary consultation or manual documentation.
- Provide a way to stop recording and handle withdrawal according to the approved policy.
- Do not treat consent to receive care, appointment booking or operational SMS/WhatsApp as consent to audio recording or AI processing.

The exact consent wording, legal basis, withdrawal handling and record-retention requirements require local legal and clinical review before deployment.

### 34.5 Speech-to-text requirements

Candidate requirements:
- Bangla speech support.
- English speech support.
- Mixed Bangla-English code-switching support.
- Medical vocabulary handling.
- Punctuation and paragraph segmentation.
- Speaker separation only where reliable and validated.
- Timestamps or segment references where useful.
- Confidence/uncertainty indication where supported.
- Editable transcript.
- Manual correction.
- Clear language/model/provider metadata for audit.
- Graceful handling of poor audio, overlapping speech, noise and unsupported accents.

The system must not assume that speaker diarization is always correct. It must not label a statement as doctor-authored or patient-reported when speaker attribution is uncertain.

### 34.6 Transcript integrity

- Preserve the original machine-generated transcript version for traceability according to the retention policy.
- Store doctor-corrected transcript as a separate version or auditable revision.
- Record who corrected it and when.
- Do not silently replace the original transcription.
- Clearly mark uncertain words and unintelligible sections.
- Never invent missing words to make a transcript appear complete.
- Permit the doctor to proceed with a manual note if transcription quality is inadequate.

### 34.7 AI-generated clinical note

The AI may prepare a draft using a structured template, such as:

| Note section | Intended content |
|---|---|
| Subjective | Patient-reported complaint, symptoms, duration and relevant history |
| Objective | Only findings explicitly stated as observed/measured by the clinician or supplied from a verified source |
| Assessment | Doctor's stated assessment; AI may separately flag possible considerations for review, never silently confirm them |
| Plan | Doctor-stated plan and separately labelled AI suggestions awaiting review |

Potential additional fields:
- Chief complaint.
- History of present illness.
- Relevant history.
- Current medications.
- Allergies.
- Review of systems.
- Examination.
- Vital signs.
- Assessment.
- Plan.
- Follow-up.

Rules:
- Do not invent examination findings.
- Do not invent vital signs.
- Do not invent patient history.
- Do not convert patient speculation into a confirmed diagnosis.
- Do not represent a medication mentioned in conversation as a new prescription unless the doctor confirms it.
- Distinguish patient statements from clinician statements and AI-generated suggestions.
- Flag conflicting statements and missing information.
- Preserve the transcript as the source reference for generated content where technically feasible.
- The note remains a draft until the doctor approves it.

### 34.8 AI extraction and uncertainty handling

For extracted facts, the interface should distinguish:
- Explicitly stated in the conversation.
- Present in an existing clinical record.
- Inferred by the model.
- Not available/unknown.
- Conflicting or uncertain.

The AI must not fill unknown fields with assumptions. It should ask the doctor to verify material ambiguities rather than selecting one interpretation silently.

## 35. AI Medication and Management Suggestions

### 35.1 Scope and safety classification

This is the highest-risk capability in the proposed clinical family. It requires a separate clinical-safety approval and validation plan before implementation or real-patient use.

Potential suggestion categories:
- Medication options for doctor consideration.
- Non-pharmacological management.
- Self-care and lifestyle advice.
- Possible investigations for doctor consideration.
- Follow-up timing considerations.
- Potential contraindications, precautions and interaction alerts.

These are suggestions, not prescriptions, orders or clinical decisions.

### 35.2 Mandatory clinician control

- Every AI suggestion is visibly labelled `AI-GENERATED — NOT APPROVED`.
- The doctor may accept, edit, reject or ignore each suggestion.
- No suggestion is automatically added to the finalized note or prescription.
- No prescription is finalized or printed as approved without explicit doctor approval.
- The doctor must verify patient, medication, strength, dose, route, frequency, duration and quantity.
- The doctor remains responsible for the final clinical decision.
- The system must record the doctor's disposition of suggestions where appropriate.

### 35.3 Medication safety context

Before presenting a medication suggestion, the system should use available, relevant and authorized information, which may include:
- Patient age, if reliably recorded.
- Weight, if relevant and measured.
- Documented allergies and adverse reactions.
- Current medication list.
- Relevant medical history.
- Relevant diagnoses/conditions confirmed by the clinician.
- Pregnancy/breastfeeding status only if explicitly recorded and appropriate to use.
- Relevant kidney/liver or other clinical factors only where reliable information exists.
- Drug-drug interactions and contraindications from a verified clinical knowledge source.
- Relevant formulary availability, where maintained.

If important information is missing, the system must disclose that limitation and avoid unsupported certainty.

### 35.4 Verified medication catalogue and clinical sources

- Medication names and product details must come from a verified catalogue/formulary, not free-form LLM invention.
- Interaction and contraindication checks must use a maintained, validated source where available.
- Source name, version and update date should be traceable.
- Catalogue and clinical-reference licensing must be confirmed.
- Bangladesh-specific drug naming, strengths, brands and availability require local clinical/pharmacy review.
- The AI must not claim that a medicine is available in a facility pharmacy unless a validated inventory integration exists and is separately approved.

### 35.5 Dosage and treatment instructions

- AI-generated dose, route, frequency and duration are high-risk draft content.
- The doctor must explicitly verify each field.
- Do not calculate pediatric, weight-based, renal-adjusted or other complex dosing unless a validated clinical rule source and appropriate safeguards have been approved.
- Do not silently round or normalize a dose.
- If the model or source cannot establish a safe recommendation, it must abstain or request clinician review.
- Do not suggest controlled/restricted medicines without a separately approved policy and legal review.
- Never fabricate a drug, strength, formulation or dosing schedule.

### 35.6 Non-medication suggestions

Non-medication advice may include general self-care, hydration, rest, lifestyle or follow-up suggestions where clinically appropriate. It must:
- Be clearly marked as AI-generated draft advice.
- Be checked by the doctor for relevance and safety.
- Avoid replacing urgent assessment or emergency care.
- Avoid presenting generic advice as individualized treatment without adequate context.
- Be edited or rejected by the doctor before inclusion in the final plan.

### 35.7 Abstention and escalation

The AI should abstain from making a recommendation when:
- The transcript is materially unreliable.
- Patient identity is uncertain.
- Critical clinical context is missing.
- The patient's age or other relevant information is unknown for a context where it matters.
- Allergy or interaction status cannot be assessed adequately.
- The proposed medication is not found in the verified catalogue.
- The clinical situation appears urgent or outside validated scope.
- Sources conflict or the model confidence is insufficient.
- The requested recommendation falls outside the approved use case.

The AI must not independently triage or decide emergency priority. It may surface a clearly labelled warning for the doctor to assess, subject to clinical validation.

## 36. Doctor Review, Approval and Clinical Accountability

### 36.1 Review workspace

The doctor should be able to review, side by side where practical:
- Original transcript.
- Corrected transcript.
- AI-generated draft note.
- Existing patient history used as context.
- AI suggestions.
- Final clinical note.
- Prescription draft.

### 36.2 Actions

For each AI-generated note section or suggestion, the doctor should be able to:
- Accept.
- Edit and accept.
- Reject.
- Leave unselected.
- Request regeneration where supported.
- Add manual content.

Regeneration must not erase previous versions or doctor edits without explicit confirmation.

### 36.3 Approval requirements

- Only an appropriately authorized doctor can approve/finalize clinical notes and prescriptions, subject to the final role and professional policy.
- The identity of the approving doctor must be recorded.
- Approval timestamp and version must be recorded.
- A doctor must not approve content without being able to review it.
- AI output must remain distinguishable from doctor-authored content.
- The system must not imply that AI has signed, authorized or prescribed anything.

### 36.4 Amendment and audit trail

Record, as appropriate:
- Encounter creation and closure.
- Recording consent and recording lifecycle events.
- Audio access, processing and deletion.
- Transcript generation and corrections.
- AI model/provider and relevant version metadata.
- AI note generation and regeneration.
- Suggestions shown to the doctor.
- Doctor acceptance, modification or rejection.
- Clinical note finalization and amendment.
- Prescription creation, approval, printing, download, amendment and voiding.
- Access to sensitive clinical records.
- Export and deletion actions.

Audit records must not include raw audio, full transcripts, secrets or unnecessary sensitive clinical content unless explicitly required and protected by a separately approved design.

## 37. Audio, Transcript and Clinical Data Privacy

### 37.1 Data classification

The following are sensitive clinical information:
- Audio recordings.
- Transcripts.
- AI-generated notes.
- Doctor-approved notes.
- Diagnoses and assessments.
- Prescriptions.
- Allergies and medication history.
- Investigation results.
- Clinical attachments.
- AI prompts/responses containing patient information.

They require stronger protection than ordinary appointment metadata.

### 37.2 Audio retention policy

**Proposed default:** delete original audio after successful transcription and doctor verification, unless the facility has an explicitly approved retention configuration and appropriate consent/legal basis.

Requirements:
- Audio retention must be configurable only within platform policy and applicable law.
- The patient must be informed of the applicable retention approach before recording.
- A failed transcription must not silently delete the only available source before the doctor can decide how to proceed.
- Deletion must be verifiable and auditable.
- Backups, temporary processing storage and provider-side retention must be considered.
- Deleting audio must not delete a finalized clinical note or prescription.
- Retaining audio must have a defined purpose, access policy and retention period.
- No indefinite audio retention by default.

This proposed default requires explicit owner approval and legal/clinical review before it becomes binding.

### 37.3 Third-party AI and speech providers

Before sending patient audio or clinical data to an external provider:
- Provider suitability and contractual terms must be reviewed.
- Data location, processing location and subprocessors must be understood.
- Retention and deletion commitments must be checked.
- Training/data-use policies must be reviewed.
- Security controls and incident processes must be assessed.
- Applicable cross-border transfer and Bangladesh requirements must be reviewed.
- Organization-level enablement and consent disclosures must be supported where required.

No provider is selected or authorized by this document.

### 37.4 Access and tenant isolation

- Clinical records must be organization-scoped.
- Every clinical API request must enforce organization scope and the user's clinical permission.
- Appointment permissions alone do not grant clinical access.
- Branch restrictions must be enforced where configured.
- AI processing jobs must retain tenant and patient context safely and must not mix data between tenants.
- Background jobs, caches, temporary files, vector stores and logs must preserve tenant isolation.
- No patient content may be used to answer another tenant's request.
- Public DQDS/PQT surfaces must remain free of clinical data.

### 37.5 Security controls

Candidate requirements:
- Encryption in transit.
- Encryption at rest for sensitive clinical data and audio.
- Secure secret management.
- Strict access controls and least privilege.
- Session and access logging.
- Secure deletion and retention enforcement.
- No patient data in analytics or error logs by default.
- No raw audio/transcript in application logs.
- No clinical data in public URLs or referrers.
- Rate limiting and abuse protection.
- Backup and recovery controls.
- Security review before external clinical deployment.

## 38. Clinical Roles and Permissions — Proposed Extension

Existing canonical roles remain unchanged:
- `super_admin`
- `org_admin`
- `branch_admin`
- `receptionist`
- `doctor`
- `assistant`

Clinical permissions should be added as separate capabilities rather than assuming every role has them.

Candidate permissions include:
- `clinical.patient_history.view`
- `clinical.encounter.create`
- `clinical.encounter.view`
- `clinical.encounter.edit_draft`
- `clinical.note.finalize`
- `clinical.note.amend`
- `clinical.prescription.create`
- `clinical.prescription.approve`
- `clinical.prescription.amend`
- `clinical.prescription.void`
- `clinical.record.export`
- `clinical.record.access_audit`
- `clinical.audio.record`
- `clinical.audio.view`
- `clinical.audio.delete`
- `clinical.ai.process`
- `clinical.ai.suggestion.review`

Rules:
- The permission catalogue and role grants require separate approval.
- Doctor role does not automatically imply access to every patient's records.
- Receptionist role does not automatically include clinical-note or prescription access.
- Assistant role does not automatically include clinical access.
- Organization administrators manage module activation and user access, but should not automatically receive clinical content access solely because they are administrators.
- Platform Super Admin must not receive routine unrestricted access to clinical content.
- Emergency/break-glass access, if ever required, needs a separate approval, reason, time limit, alert and audit process.
- No cross-tenant clinical access.

## 39. Clinical Data Lifecycle and Interoperability

### 39.1 Record lifecycle

Define lifecycle rules for:
- Draft encounter.
- Finalized encounter.
- Corrected/amended encounter.
- Voided record where legally appropriate.
- Imported historical record.
- Archived record.
- Exported record.
- Retained/deleted data under approved retention policy.

Finalized clinical records must not be silently overwritten.

### 39.2 Data export

A future export workflow may support authorized export of:
- Clinical notes.
- Prescriptions.
- Consultation timeline.
- Relevant attachments.
- Audit metadata where legally appropriate.

Export format, identity verification, patient request workflow, fees and legal obligations require separate approval.

### 39.3 Interoperability

Potential future integrations:
- Laboratory information systems.
- Diagnostic imaging/report systems.
- Pharmacy systems.
- External hospital/clinic software.
- Health information exchange standards, if appropriate.

No integration, standard, partner, cross-organization sharing or external data exchange is approved by this document.

## 40. AI Provider-Neutral Architecture and Operational Controls

### 40.1 Provider abstraction

AI and speech capabilities should be accessed through provider-independent interfaces so that AMSDP's clinical records do not depend on a single model vendor.

Separate interfaces should be considered for:
- Audio transcription.
- Language detection.
- Speaker diarization, if supported.
- Clinical note drafting.
- Structured fact extraction.
- Clinical suggestion generation.
- Clinical reference/catalogue lookup.

### 40.2 AI processing boundaries

- AI services receive only the minimum necessary context.
- Patient/tenant context must be validated before processing.
- Provider responses are untrusted draft content.
- Model output must be validated against expected schemas.
- Tool/model output must not directly execute database mutations or finalize clinical records.
- Prompt injection or malicious content inside transcripts must not override system safety policy.
- AI provider failure must not prevent manual note entry or prescription creation.
- Retry and timeout behavior must avoid duplicate records or duplicate billing where possible.

### 40.3 Traceability

Where appropriate, record:
- Provider identifier.
- Model identifier/version.
- Processing timestamp.
- Task type.
- Input record/version references.
- Output version/reference.
- Error/abstention status.
- Applicable configuration/prompt version.

Avoid storing duplicate patient content in operational logs.

### 40.4 Quality monitoring

Before clinical use, evaluate:
- Bangla transcription quality.
- English transcription quality.
- Mixed-language transcription quality.
- Medical terminology accuracy.
- Speaker attribution accuracy.
- Hallucinated or omitted clinical facts.
- Note completeness and factual consistency.
- Medication catalogue matching.
- Unsafe or unsupported recommendations.
- Clinician correction rate.
- Latency, availability and cost.

Evaluation must use appropriately authorized, de-identified or synthetic data wherever possible. Real-patient data use requires a separate approved governance basis.

## 41. Clinical Reporting and Analytics — Proposed

Potential reports:
- Consultation volume.
- Notes pending doctor review.
- Finalized consultation count.
- Prescription count.
- AI transcription usage and processing failures.
- AI suggestion acceptance/edit/rejection counts.
- Documentation time saved, if measured through a valid methodology.
- Clinical module usage and subscription utilization.

Restrictions:
- Do not use AI acceptance rate as a proxy for clinical correctness.
- Do not rank doctors by simplistic clinical outcome metrics.
- Do not expose identifiable patient information in aggregate reports unless authorized and necessary.
- Do not claim time savings or improved clinical outcomes without a valid evaluation.
- Clinical analytics and performance management require separate product and governance approval.

## 42. Clinical Module Failure and Degraded Modes

The platform must remain safe and usable when:
- Audio recording is unavailable.
- Microphone permission is denied.
- Speech-to-text provider is unavailable.
- AI provider times out.
- Network connectivity is interrupted.
- Medication catalogue is unavailable.
- Clinical history cannot be loaded.
- A subscription entitlement expires.
- A user loses permission during a session.

Expected behavior:
- Manual documentation remains available where the user is authorized.
- No AI failure should block ordinary appointment or queue operations.
- No incomplete AI result is presented as final.
- Draft content is saved safely where possible.
- Duplicate AI processing and duplicate prescriptions are prevented.
- The doctor is informed of missing context or failed checks.
- Clinical records remain protected during degraded operation.
- Module expiry must follow an approved read-only/export/retention policy and must not silently delete data.

## 43. Clinical Acceptance Criteria — Proposed Release Gates

### 43.1 Clinical Management foundation

- Correct patient and organization association is enforced.
- Unauthorized users cannot access clinical records.
- Draft and finalized states are distinguishable.
- Clinical notes preserve author, editor, timestamps and version history.
- Finalized notes cannot be silently overwritten.
- Manual documentation works without AI.
- Patient history displays only authorized records.
- Appointment completion does not fabricate a clinical note.

### 43.2 Digital Prescription

- Only authorized doctors can approve/finalize prescriptions.
- Required medication fields are validated according to approved policy.
- Prescription preview matches the approved record.
- Bangla and English print output is legible.
- Reprinting preserves the same approved version.
- Amendments and voids are audited.
- Unauthorized users cannot alter finalized prescriptions.
- No AI suggestion is automatically prescribed.

### 43.3 Recording and transcription

- Recording cannot start without the required consent state.
- Recording indicator is visible.
- Start, pause, resume and stop behave correctly.
- Refusal does not block ordinary consultation.
- Bangla, English and mixed-language quality is evaluated.
- Uncertain words and speaker attribution are not presented as certain.
- Transcript corrections are auditable.
- Audio retention/deletion follows the approved policy.
- Provider failure does not block manual notes.

### 43.4 AI notes

- AI output is always a draft.
- AI does not invent vital signs, examination findings, diagnoses or history.
- Patient-reported and clinician-observed facts are distinguished.
- Uncertain and conflicting content is flagged.
- Doctor can edit, accept or reject content.
- Original and corrected versions remain traceable.
- Only doctor-approved content becomes a finalized clinical note.

### 43.5 AI suggestions

- Suggestions are clearly marked unapproved.
- Medication names map to verified catalogue entries.
- Missing safety context is disclosed.
- Contraindication/interaction checks use validated sources where available.
- Doctor must verify medication and every prescribing field.
- AI cannot finalize or issue a prescription.
- Unsupported or unsafe requests trigger abstention.
- Clinical validation is completed before any real-patient deployment.

### 43.6 Security and governance

- Tenant isolation is tested across all clinical endpoints and background jobs.
- Role/permission tests cover all clinical actions.
- Sensitive data is absent from public endpoints and ordinary logs.
- Provider data-use and retention terms are reviewed.
- Consent and retention workflows are tested.
- Audit trails are tamper-resistant to the extent required by the approved architecture.
- Backup/restore includes approved clinical records and retention controls.
- Applicable legal and professional review is complete before production use.

## 44. Clinical Roadmap and Release Boundaries — Proposed

The following is a candidate sequence, not an approved schedule:

| Phase | Candidate scope | Gate |
|---|---|---|
| C0 | Product decisions, clinical workflow discovery, legal/privacy review, data model and module entitlement design | Explicit product approval |
| C1 | Clinical Management foundation, manual encounter notes and audit trail | Clinical workflow and access-control acceptance |
| C2 | Digital Prescription and patient clinical-history timeline | Doctor approval, print validation and record integrity |
| C3 | Consent-based audio capture and editable transcription | Consent, privacy, provider and transcription-quality gates |
| C4 | AI-generated structured draft notes | Clinical validation and doctor-review acceptance |
| C5 | AI medication and management suggestions | Separate clinical safety approval, verified catalogue/reference data and validation |
| C6 | Clinical summaries, integrations and advanced analytics | Separate product and interoperability approval |

The current AMSDP hackathon MVP remains governed by the existing P0 scope and current task authorizations. This proposed clinical roadmap does not alter the immediate delivery priority.

## 45. New Product Decisions Required

The following require explicit owner decisions before the relevant module is approved:

1. Approve or reject the modular platform direction and product-family structure.
2. Approve or reject Clinical Management as a separately purchasable module.
3. Approve or reject Digital Prescription as part of Clinical Management.
4. Approve or reject Patient Medical History as part of Clinical Management.
5. Approve or reject AI Clinical Assistant as a premium add-on.
6. Confirm initial target customers: independent chambers, clinics, hospitals, or a staged subset.
7. Decide whether clinical records are strictly organization-local in the first release (recommended).
8. Define clinical roles and access boundaries.
9. Decide whether audio is deleted after transcription and doctor verification by default (proposed default).
10. Approve consent and withdrawal policy after legal/clinical review.
11. Decide which languages and dialects are required for initial transcription.
12. Select and approve speech-to-text provider only after privacy, security, quality and cost review.
13. Select and approve LLM provider only after privacy, security, quality and cost review.
14. Decide medication catalogue/formulary source and licensing.
15. Decide whether medication suggestions are permitted in the first AI release or deferred until after AI notes are validated.
16. Approve clinical safety validation and real-patient pilot criteria.
17. Decide electronic signature and prescription legal requirements.
18. Decide clinical record retention, export, correction and deletion policies.
19. Decide subscription packaging, usage limits and AI cost controls.
20. Decide whether investigation results and attachments are included in the first clinical release.
21. Decide whether any future cross-facility record exchange is ever desired; no such sharing is assumed.
22. Complete Bangladesh-specific legal, privacy, professional and regulatory review before production deployment.

---

# Part VIII — Preserved V2.3 Baseline (Complete, Retained for Traceability)

The complete V2.3 source text follows. It is retained rather than shortened or selectively summarized so that every previously documented feature, requirement, approval marker, exclusion, decision, acceptance criterion, historical caveat and reference remains available. Apply the V2.4 amendments in the Executive Amendment and Part VII when interpreting conflicting scope statements for future planning.

---

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
