# AMSDP Website Content & Copywriting Proposal

**Source documents:** AMSDP Master Feature List V2.5 (active) and V2.3 (historical baseline).  
**Derivation rule:** All headlines, value propositions, feature descriptions, and workflows are derived strictly from V2.5 and V2.3. Pricing tier names, prices, and commercial packaging are illustrative suggestions only; V2.5 states that exact plan names, prices, bundles, and billing units remain commercial decisions. No HTML, CSS, or JS is included in this proposal.

---

## 1. Landing Page

### 1.1 Hero Section

**Headline:**  
Less Waiting. Less Crowding. Better Healthcare Experiences.

**Subheadline:**  
AMSDP is a lightweight, facility-centric appointment management platform for Bangladeshi hospitals, clinics, and independent medical practices. Help authorized staff manage doctor schedules, patient registration, appointments, walk-ins, serials, and queues—without replacing your existing clinic software.

**Value proposition bullets:**
- Facility-first subscription: hospitals, clinics, and independent chambers subscribe as organizations; data stays isolated per tenant.
- Lightweight doctor entries: create appointment profiles without requiring the doctor to create an AMSDP account.
- Three appointment models: time-slot, serial-based, and hybrid—configurable by facility, doctor, or location.
- Patient Queue Visibility: public token-only waiting-room display (DQDS) and private appointment-specific tracking (PQT) via unguessable link and QR code—no patient account required.
- One-way operational notifications: WhatsApp and SMS appointment confirmations and pre-visit reminders (5- or 10-minute options), provider-dependent.
- Mobile-first, low-bandwidth staff experience with Bangla and English UI support.

**Primary CTA:**  
Start Managing Appointments

**Secondary CTA:**  
See the Modular Platform

**UI component ideas:**
- Hero banner with background illustration of a clinic reception desk and queue board.
- Left column: headline, subheadline, value proposition list, two CTAs (primary button, secondary outline button).
- Right column: mockup of the One-Page Daily Appointment Board showing a serial queue with statuses (BOOKED, CHECKED_IN, IN_CONSULTATION, COMPLETED).
- Animated badge: "Bangladesh-focused • Mobile-friendly • Low-bandwidth optimized"

### 1.2 Core Problem / Solution

**Section headline:**  
Built for how Bangladeshi facilities actually work

**Problem copy:**  
Patients call or walk in. Receptionists and assistants manage schedules on paper or fragmented tools. Physical waiting areas crowd because patients have no visibility into queue position. Facilities need appointment control without becoming a full hospital management system.

**Solution copy:**  
AMSDP gives facility staff a single working screen for daily operations: register patients, book appointments, manage walk-ins, reorder queues, and track attendance. Patients stay informed through SMS/WhatsApp reminders and private tracking links—no portal, no login, no self-booking required.

**UI component ideas:**
- Two-column "Problem vs. Solution" layout with icons.
- Problem side: red-tinted icons (crowded waiting room, phone ringing, paper register).
- Solution side: green-tinted icons (digital board, SMS bubble, QR code, queue token).

### 1.3 Key Platform Pillars

**Section headline:**  
Three connected product families

**Pillar 1: Practice Operations**  
**Headline:** Appointment and queue management, simplified  
**Copy:** Organization workspaces, users and roles, patient registration, doctor entries, schedules, walk-ins, unified queue, audit history, and operational reports.  
**UI component idea:** Card with icon of a calendar and checklist.

**Pillar 2: Patient Queue Visibility (PQV)**  
**Headline:** Transparency without exposing patient data  
**Copy:** Public Digital Doctor Queue Display (DQDS) shows token-only queue status with no patient PII. Private Personal Queue Tracking (PQT) lets patients check their own appointment status via a secure, unguessable link or printed QR code.  
**UI component idea:** Split card showing a public waiting-room screen on the left and a mobile tracking page on the right.

**Pillar 3: Clinical Management & Intelligent Documentation (Optional)**  
**Headline:** Less typing. Faster documentation. Complete clinical control.  
**Copy:** Optional encounter notes, structured templates, digital prescriptions, medicine catalogue, and private doctor-only voice dictation with AI-assisted drafting. The doctor always reviews and approves; AI never prescribes or finalizes autonomously.  
**UI component idea:** Card with a stethoscope and document icon, marked "Optional module."

### 1.4 Social Proof / Compliance Placeholders

**Section headline:**  
Trusted by facilities. Built for Bangladesh.

**Placeholder blocks:**
- [Placeholder: Facility logo grid — hospitals, clinics, independent chambers]
- [Placeholder: "Join [X] facilities in Bangladesh" counter]
- [Placeholder: Compliance badges — tenant isolation, role-based access, audit logging, Bangla Unicode support]
- [Placeholder: Data privacy statement — patient personal data is not treated as property owned outright by AMSDP or the clinic; organization responsible for lawful records]

**UI component idea:** Horizontal logo strip with grayscale facility logos; compliance badge row with tooltips.

### 1.5 Primary CTAs

**CTA 1 (Hero):**  
Button text: Start Managing Appointments  
Link: /get-started or /request-demo

**CTA 2 (Hero secondary):**  
Button text: Explore Modular Platform  
Link: /features

**CTA 3 (Bottom hero bar):**  
Headline: Ready to reduce waiting and crowding?  
Button: Book a Facility Demo  
Link: /demo

---

## 2. Features & Modular Platform Page

### 2.1 Page Headline & Intro

**Page headline:**  
The Modular Healthcare Platform for Bangladesh

**Intro copy:**  
AMSDP is organized into connected product families. Start with AMSDP Core for appointment operations. Add Patient Queue Visibility and Patient Communication as needed. Activate Clinical Management and Intelligent Clinical Documentation only when your facility is ready—each module is independently entitled and server-side enforced.

**UI component idea:**  
A horizontal product-family navigator (Practice Operations → Clinical Management → Intelligent Clinical Documentation) that filters the module grid below.

### 2.2 Interactive Tabs / Accordions

**Interaction pattern:**  
Use category tabs at the top (Practice Operations, Clinical Management, Intelligent Clinical Documentation). Inside each category, render accordion cards for every module. Clicking a module expands detailed workflow, capabilities, and a "See it in action" CTA.

---

#### Tab: Practice Operations

**Accordion 1: AMSDP Core**

**Module headline:**  
AMSDP Core — Foundational Appointment Platform

**Subheadline:**  
Organization workspaces, patient registration, doctor entries, scheduling, queues, and role-based access.

**Key capabilities (from V2.5/V2.3):**
- Facility subscription and independent facility workspaces with strict tenant isolation.
- Lightweight doctor entries: mandatory name and mobile number; system-generated facility-local Doctor ID.
- Patient registration: mandatory name and mobile number; shared mobile numbers supported for family records; duplicate warnings, no auto-merge.
- Appointment creation: select patient, doctor, branch, date, model, slot/serial, and booking source (phone, in-person, assistant, reception, walk-in).
- Appointment models: time-slot based, serial-based, and hybrid.
- Canonical appointment statuses: BOOKED, AWAITING_CONFIRMATION, CONFIRMED, CHECKED_IN, IN_QUEUE, IN_CONSULTATION, COMPLETED, CANCELLED, NO_SHOW, RESCHEDULED.
- Doctor schedules: working days, start/end times, breaks, blocked dates, duration, serial capacity.
- Walk-in registration and four placement policies: end of queue, first-come-first-served, reserved capacity, staff-controlled placement.
- Unified queue with manual position changes, skip, absent marking, and audit history.
- One-Page Daily Appointment Board: date, doctor selector, patient search, add appointment/walk-in, queue list, check-in controls, quick reschedule/cancel.
- Roles: super_admin, org_admin, branch_admin, receptionist, doctor (optional login), assistant.
- Audit logging for appointment changes, queue adjustments, priority assignments, and permission changes.
- Bangla and English interface support; Unicode Bangla input; mobile-friendly, low-bandwidth design.

**Workflow steps:**
1. Staff logs in with organization-scoped role.
2. Search or register patient (name + mobile number).
3. Select doctor and check schedule.
4. Create appointment under time-slot, serial, or hybrid model.
5. Patient arrives; staff checks them in and updates queue status.
6. Doctor or authorized staff completes consultation; appointment moves to COMPLETED.

**UI component idea:**  
Accordion expands to show a mini-screenshot of the Daily Appointment Board with drag-and-drop queue cards and status chips.

**CTA microcopy:**  
See Core in Action →

---

**Accordion 2: Patient Queue Visibility (PQV)**

**Module headline:**  
Patient Queue Visibility — DQDS & PQT

**Subheadline:**  
Public waiting-room displays and private patient tracking without patient accounts.

**Key capabilities:**
- Digital Doctor Queue Display (DQDS): public, read-only waiting-room display; token-based visibility only; no patient name, mobile, DOB, age, or other PII; organization/branch-scoped.
- Personal Queue Tracking (PQT): appointment-specific private tracking page via cryptographically unguessable tracking token and printed QR code; shows token, doctor/branch, currently-serving token, patients ahead, estimated wait time (labelled estimate), and status.
- Tracking-token expiry and revocation on consultation start, cancellation, or reschedule; revoked tokens never reactivated.
- No-cache responses for private tracking pages; rate limiting for public endpoints.
- Live queue position and patients-ahead re-evaluated on every request.

**Workflow steps:**
1. Staff books an appointment; system generates a tracking token.
2. Reception prints a QR code or shares the link manually (fallback).
3. Patient opens the link on their phone to see their position and estimated wait.
4. Waiting-room screen shows only tokens and queue status—no patient names.

**UI component idea:**  
Side-by-side preview: a wall-mounted DQDS screen showing "Now Serving: T-12" and a mobile phone showing "Your turn: 3 patients ahead."

**CTA microcopy:**  
Explore PQV Demo →

---

**Accordion 3: Patient Communication**

**Module headline:**  
Patient Communication — WhatsApp & SMS

**Subheadline:**  
One-way operational notifications, independently configurable per organization.

**Key capabilities:**
- N1 Appointment Confirmation: triggered immediately after successful booking; includes date/visiting time, doctor, facility/branch, queue token/reference, PQT link, and instructions.
- N2 Pre-Visit Reminder ("Queue Turn Protection"): default 10 minutes before expected visit; organization-configurable 5- or 10-minute options; includes tracking link and notes that estimates can change.
- WhatsApp and SMS are independently configurable organization-level channels.
- Booking remains functional if messaging is disabled, unconfigured, or unavailable.
- Delivery claimed only after provider confirmation; no silent delivery claims.
- Cooldown and deduplication; pending reminders cancelled on cancellation, reschedule, consultation start, or check-in.

**Workflow steps:**
1. Appointment booked successfully.
2. N1 confirmation queued immediately.
3. N2 reminder scheduled based on organization lead-time setting.
4. If queue changes, reminder schedule adjusts to avoid duplicates.
5. Staff can manually share tracking links as fallback.

**UI component idea:**  
Mock chat bubbles showing a WhatsApp confirmation and an SMS reminder with a tracking link.

**CTA microcopy:**  
Review Notification Templates →

---

**Accordion 4: Analytics & Reports**

**Module headline:**  
Analytics & Reports

**Subheadline:**  
Operational visibility limited to appointment operations.

**Key capabilities:**
- Appointments by day, by doctor, and by branch/location.
- Booked, completed, cancelled, and no-show counts.
- Walk-in counts and queue activity.
- Appointment source counts (phone, in-person, assistant, reception, walk-in).
- Schedule utilization where meaningful for the selected appointment model.
- No revenue, billing, payment settlement, or clinical-performance analytics.

**UI component idea:**  
Simple dashboard cards with counters and a weekly appointment trend line.

**CTA microcopy:**  
View Sample Report →

---

#### Tab: Clinical Management

**Accordion 5: Clinical Records & Consultation Documentation**

**Module headline:**  
Clinical Records & Consultation Documentation

**Subheadline:**  
Encounter-based clinical notes created and approved by doctors.

**Key capabilities:**
- Patient-linked encounter records with consultation date, time, and responsible doctor.
- Structured clinical-note templates: chief complaint, history, examination findings, assessment, treatment plan, advice, follow-up instructions.
- Doctor-authored free-text notes; draft, review, and finalize workflow.
- Encounter states: Draft, In progress, Pending doctor review, Finalized, Amended, Cancelled/entered-in-error.
- Encounter metadata: patient, organization, branch, doctor, appointment reference, date/time, created-by, finalized-by, version, amendment history.
- Information provenance: patient-reported, clinician-observed, clinician-entered assessment, imported, AI-generated draft, clinician-confirmed final.
- Manual documentation works without AI, microphone, or AI-provider internet access.
- Templates allow blank fields; system does not force unobtained information.

**Workflow steps:**
1. Doctor opens authorized patient record.
2. Starts a consultation/encounter and associates it with the appointment where applicable.
3. Selects a template or enters free-text notes manually.
4. Saves a draft, reviews, and finalizes.
5. Optionally creates a prescription.
6. Finalized record is stored with audit history; drafts are never represented as finalized.

**UI component idea:**  
Split view: left side shows note template fields; right side shows a finalized note with "Finalized by Dr. [Name] • [Timestamp]" badge.

**CTA microcopy:**  
Preview Clinical Note Editor →

---

**Accordion 6: Digital Prescription Management**

**Module headline:**  
Digital Prescription Management

**Subheadline:**  
Doctor-created, reviewed, and approved prescriptions—no AI required.

**Key capabilities:**
- Prescription content: patient identity, organization/branch, doctor identity and professional registration details (where required), prescription date, encounter reference, medicine name, generic/brand designation, strength, formulation, dose, route, frequency, duration, quantity/refills, special instructions, non-medication advice, follow-up advice, doctor signature/approval metadata.
- Workflow: doctor selects/enters medicines, verifies fields, system validates completeness, doctor previews, doctor explicitly finalizes, stored as immutable version.
- Corrections create auditable amendment or replacement versions; originals are not erased.
- Voiding/cancellation requires authorization and a recorded reason.
- Printable/downloadable prescriptions with Bangla and English rendering.
- Historical prescription retrieval within the originating organization.
- No AI autonomous prescribing: AI does not choose medicines, invent doses, or silently add items.

**Workflow steps:**
1. Doctor opens encounter and selects medicines from catalogue or favourites.
2. Enters dose, route, frequency, duration.
3. System highlights missing or inconsistent fields.
4. Doctor previews the prescription.
5. Doctor explicitly approves/finalizes.
6. System stores immutable version; reprint reproduces the approved version.

**UI component idea:**  
Prescription preview card showing doctor name, patient reference, medicine list with dosage, and a "Finalize Prescription" button.

**CTA microcopy:**  
Try Prescription Builder →

---

**Accordion 7: Prescription Support Library**

**Module headline:**  
Prescription Support Library

**Subheadline:**  
Medicine catalogue, favourites, templates, and common instructions—all under doctor control.

**Key capabilities:**
- Controlled medicine catalogue with generic and brand-name search; strength, formulation, and disambiguating details; catalogue source, version, and maintenance date recorded.
- Autocomplete and matching as the doctor types; explicit doctor selection required; ambiguous names flagged.
- Doctor favourites: frequently used medicines; doctor-configured default instructions only where explicitly entered and reviewed; never auto-inserted.
- Reusable prescription templates: doctor reviews patient-specific details every time; template changes do not alter finalized prescriptions.
- Common instruction library: Bangla and English text where validated; doctor-specific and organization-approved entries; review required before insertion.

**UI component idea:**  
Search bar with medicine autocomplete dropdown showing "Paracetamol 500mg tablet" and a "Add to Prescription" button.

**CTA microcopy:**  
Browse Medicine Catalogue →

---

**Accordion 8: Encounter History & Record Retrieval**

**Module headline:**  
Encounter History & Record Retrieval

**Subheadline:**  
Organization-scoped access to previous finalized notes and prescriptions.

**Key capabilities:**
- Display previous finalized consultation notes and historical prescriptions created within the organization.
- Encounter dates and responsible doctors; auditable amendments.
- Not a centralized, cross-clinic medical-history repository; one clinic cannot automatically browse another clinic's records.
- Authorized patient access process to request or obtain historical prescriptions and personal data, subject to applicable law and identity verification.
- Duplicate resolution is authorized and auditable; no merging solely on name or mobile-number match.

**UI component idea:**  
Timeline card showing "Encounter #104 — 12 Oct 2026 — Dr. Rahman — Finalized" with a "View Prescription" link.

**CTA microcopy:**  
View Record Retrieval Flow →

---

#### Tab: Intelligent Clinical Documentation

**Accordion 9: Intelligent Clinical Documentation Assistant**

**Module headline:**  
Intelligent Clinical Documentation Assistant

**Subheadline:**  
Optional private doctor-only dictation and AI-assisted drafting. The doctor remains in complete control.

**Key capabilities:**
- Private doctor-only voice dictation; initiated intentionally by the doctor from an authorized workspace.
- Bangla and English speech-to-text, with mixed-language support as a validation target.
- AI-assisted structuring of the doctor's dictated clinical note into approved templates.
- Extraction of medicine names and instructions explicitly stated by the doctor.
- Catalogue matching for dictated medicine text; ambiguous matches shown for doctor resolution.
- Draft preparation for doctor review; clear display of uncertain or incomplete fields.
- Manual editing, correction, rejection, or approval.
- Only doctor-approved content becomes finalized.
- UI clearly indicates microphone status; doctor can pause, resume, stop, discard, or retry.
- No automatic recording when a patient record opens; doctor can choose manual entry instead.

**Explicitly excluded (initial scope):**
- Mandatory recording of the patient-doctor conversation.
- Ambient listening during consultation.
- Requiring the doctor to speak to AI in front of a patient.
- AI independently deciding diagnosis or medication.
- Automatic finalization of notes or prescriptions.
- Concealed autonomous clinical decision-making.

**Workflow steps (Note Mode):**
1. Doctor opens encounter and selects Note Mode dictation.
2. Doctor dictates clinical findings and intended documentation.
3. Speech-to-text produces transcript; AI structures into the note template.
4. Doctor reviews, edits uncertain fields, and approves.
5. Approved content becomes the finalized note.

**Workflow steps (Prescription Mode):**
1. Doctor dictates medicine names and instructions they have decided.
2. System transcribes and matches against the medicine catalogue.
3. Missing or ambiguous attributes are flagged.
4. Doctor resolves ambiguity, verifies all fields, and approves.
5. Approved content becomes the prescription draft.

**UI component idea:**  
Microphone toggle button with status indicator ("Listening…" / "Paused") and a side panel showing the live transcript and structured draft note.

**CTA microcopy:**  
Try Dictation Demo →

---

**Accordion 10: Clinical Summaries & Follow-up Assistance**

**Module headline:**  
Clinical Summaries & Follow-up Assistance

**Subheadline:**  
Draft summaries and documentation assistance for authorized clinician review (optional future capability).

**Key capabilities:**
- Draft summaries of previously recorded encounters using only available, authorized records.
- Does not imply access to a complete medical history when one does not exist.
- Depends on Clinical Management; optional future capability.

**UI component idea:**  
Summary card with "Draft — Doctor review required" warning and an "Edit & Approve" button.

**CTA microcopy:**  
Learn More →

---

## 3. Solutions / Use Cases Page

### 3.1 Page Headline

**Page headline:**  
Workflows Built for Every Role in Your Facility

**Intro copy:**  
AMSDP supports the canonical staff roles defined for facility workspaces: super_admin, org_admin, branch_admin, receptionist, doctor (optional login), and assistant. Patients do not need AMSDP accounts. Below are tailored workflows by role and facility type.

### 3.2 Role-Based Use Cases

**Role 1: Hospital Administrator / Super Admin**

**Headline:**  
Govern Your Platform, Not Just One Clinic

**Copy:**  
Create, activate, suspend, and manage subscriber accounts. Manage subscription plans, limits, and expiry. Configure available appointment models, policy options, default values, and permission templates. Set doctor mobile-number uniqueness policy. View tenant-level usage and system health. All functions remain platform-level; no routine cross-tenant access to patient or appointment content.

**Key actions:**
- Manage subscriber organizations.
- Configure platform-wide limits and defaults.
- Monitor system health and audit metadata.

**CTA:**  
See Admin Dashboard →

---

**Role 2: Clinic Receptionist / Appointment Operator**

**Headline:**  
Run the Front Desk from One Screen

**Copy:**  
Search patient records, register new patients, create/reschedule/cancel appointments according to permission, register walk-ins, check patients in, update attendance status, view doctor schedules, and manage queue position if authorized. The One-Page Daily Appointment Board is the main working screen.

**Key actions:**
- Patient search by mobile number, name, or internal ID.
- Appointment creation under time-slot, serial, or hybrid models.
- Walk-in registration and queue placement.
- Check-in and status updates.

**CTA:**  
Try Receptionist Workflow →

---

**Role 3: Doctor / Clinician**

**Headline:**  
Document Consultations on Your Terms

**Copy:**  
A doctor account is optional. Where enabled, doctors can view their own appointment list and queue, see schedule information and appointment changes, and update limited appointment statuses if permitted. With Clinical Management activated, authorized doctors can create and finalize encounter notes, build prescriptions, use templates and favourites, and optionally use private voice dictation.

**Key actions:**
- View personal appointment queue.
- Start and complete consultations (with appropriate permissions).
- Finalize clinical notes and prescriptions.
- Use private dictation (optional module).

**CTA:**  
Explore Doctor Workspace →

---

**Role 4: Assistant**

**Headline:**  
Support Assigned Doctors with Scoped Access

**Copy:**  
Manage appointments for assigned doctor(s), register patients and walk-ins, check patients in, update queue status and position, and reschedule or cancel appointments when permitted. Access is limited to assigned doctor(s) and permitted branch/facility operations. This is an appointment-operations assignment, not HR or workforce management.

**Key actions:**
- Appointment management for assigned doctors.
- Walk-in registration and check-in.
- Queue position updates.

**CTA:**  
See Assistant Permissions →

---

### 3.3 Facility-Type Use Cases

**Facility 1: Hospitals**

**Headline:**  
Multi-Department Appointment Control

**Copy:**  
Manage branches or locations within a single organization. Configure doctor schedules across departments. Patient records are shared across branches within the organization; each appointment retains its assigned branch. Strict tenant isolation keeps hospital data separate from other subscribers.

**Facility 2: Clinics**

**Headline:**  
Lightweight Scheduling for Busy Clinics

**Copy:**  
Single-branch setup works without configuring departments, floors, or rooms. Fast patient registration, serial or time-slot appointments, and walk-in handling on mobile-friendly screens.

**Facility 3: Independent Medical Practices / Personal Chambers**

**Headline:**  
Your Chamber, Your Workspace

**Copy:**  
An independent doctor's personal chamber can subscribe as its own facility. Create lightweight doctor entries without the doctor's participation. Manage patient registration, appointments, and queues independently with full data isolation.

**UI component idea:**  
Three facility cards with icons (hospital building, clinic, doctor's chamber) and a "Select your facility type" CTA leading to a tailored demo.

---

### 3.4 Common Workflow Scenarios

**Scenario 1: Phone Booking**

**Copy:**  
Patient calls the clinic. Receptionist searches for or registers the patient, checks the internal schedule, decides when to book, creates the appointment, and communicates details outside AMSDP. N1 confirmation is sent via WhatsApp/SMS if configured.

**Scenario 2: Walk-In**

**Copy:**  
Patient arrives without an appointment. Staff registers them (name + mobile number) and places them in the queue according to the facility's configured policy: end of queue, first-come-first-served, reserved capacity, or staff-controlled placement.

**Scenario 3: Serial Queue Day**

**Copy:**  
Doctor uses a serial-based model. Patients receive tokens. The waiting-room DQDS shows currently-serving tokens. Patients use PQT links to check how many patients are ahead. Staff can manually reorder the queue with audit history.

**Scenario 4: Time-Slot Consultation**

**Copy:**  
Doctor uses time-slot model with configured duration. Appointments are assigned to defined slots. Staff checks patients in and moves them through CHECKED_IN → IN_QUEUE → IN_CONSULTATION → COMPLETED.

**Scenario 5: Missed Turn Recovery**

**Copy:**  
If a patient is unavailable when called, authorized staff explicitly confirms the missed turn. Default: patient is deferred to the end of the same active queue. Authorized override allows moving to any valid position in that queue with reason and audit. No automatic NO_SHOW.

**UI component idea:**  
Scenario cards with step numbers and a "Simulate this workflow" button.

---

## 4. Pricing & Plans Page

### 4.1 Page Headline

**Page headline:**  
Simple, Modular Pricing for Bangladeshi Facilities

**Intro copy:**  
AMSDP Core is the foundational subscription. Optional modules—Patient Queue Visibility, Patient Communication, Analytics & Reports, Clinical Management, and Intelligent Clinical Documentation—can be activated based on your facility's needs. Module entitlements are enforced server-side. Exact plan names, prices, bundles, billing units, trial rules, and usage limits are commercial decisions and are subject to final approval.

**Disclaimer:**  
Pricing shown below is illustrative and proposed for discussion only. It is not an approved commercial offer.

### 4.2 Suggested Tier Structure

**Tier 1: AMSDP Core**

**Headline:**  
Appointment Operations

**Suggested for:**  
Hospitals, clinics, and independent chambers that need scheduling, registration, and queue management.

**Included capabilities:**
- Organization workspace and branch management.
- Users, roles, and permissions (super_admin, org_admin, branch_admin, receptionist, doctor, assistant).
- Lightweight doctor entries.
- Patient registration and search (including shared mobile numbers and duplicate warnings).
- Appointment creation: time-slot, serial, and hybrid models.
- Doctor schedule configuration.
- Daily appointment board and check-in/attendance.
- Walk-in registration and placement.
- Unified queue management with manual adjustments and audit history.
- Strict tenant isolation and audit logging.
- Bangla and English UI; mobile-friendly, low-bandwidth design.

**Suggested CTA:**  
Start with Core →

---

**Tier 2: Core + Patient Queue Visibility (PQV)**

**Headline:**  
Add Waiting-Room Transparency

**Suggested for:**  
Facilities that want to reduce physical crowding with public displays and patient tracking.

**Includes everything in Core, plus:**
- Digital Doctor Queue Display (DQDS): public, token-only, no PII.
- Personal Queue Tracking (PQT): private tracking via unguessable token and QR code.
- Token expiry and revocation; no-cache private responses; rate-limited public endpoints.

**Suggested CTA:**  
Add PQV →

---

**Tier 3: Core + Patient Communication**

**Headline:**  
Keep Patients Informed

**Suggested for:**  
Facilities that want automated one-way reminders and confirmations.

**Includes everything in Core, plus:**
- N1 Appointment Confirmation (WhatsApp and/or SMS).
- N2 Pre-Visit Reminder (5- or 10-minute configurable lead time).
- Cooldown, deduplication, and provider-confirmed delivery reporting.
- Manual link-sharing fallback.

**Note:**  
WhatsApp and SMS delivery depend on provider accounts and configuration; not included in base software fee.

**Suggested CTA:**  
Add Communication →

---

**Tier 4: Core + Clinical Management**

**Headline:**  
Document Consultations & Prescriptions

**Suggested for:**  
Practices that want optional encounter notes and digital prescriptions.

**Includes everything in Core, plus:**
- Clinical Records & Consultation Documentation (templates, draft/finalize, audit).
- Digital Prescription Management (catalogue, favourites, templates, print/retrieve).
- Prescription Support Library (medicine search, common instructions).
- Encounter History & Record Retrieval (organization-scoped).

**Note:**  
Requires separate clinical-module implementation approval and Bangladesh-qualified legal/professional review before production use.

**Suggested CTA:**  
Activate Clinical Management →

---

**Tier 5: Full Platform (Core + Clinical + Intelligent Documentation)**

**Headline:**  
Complete Practice Platform with AI Assistance

**Suggested for:**  
Facilities ready for optional private doctor-only dictation and AI-assisted drafting.

**Includes everything in Tier 4, plus:**
- Intelligent Clinical Documentation Assistant (private dictation, Bangla/English speech-to-text, AI-assisted note structuring, catalogue matching).
- Clinical Summaries & Follow-up Assistance (optional future capability).

**Note:**  
AI output is always a draft; doctor review and approval required. No ambient patient recording.

**Suggested CTA:**  
Request Full Platform Demo →

---

### 4.3 Modular Add-Ons

**Add-on list:**
- Patient Queue Visibility (PQV) — DQDS + PQT
- Patient Communication — WhatsApp and SMS channels (provider costs apply separately)
- Analytics & Reports — operational appointment reporting
- Clinical Management — notes, prescriptions, history
- Intelligent Clinical Documentation — private dictation and AI-assisted drafting

**Copy:**  
Mix and match modules. A clinic can run Core without Clinical Management. Clinical Management can be used without AI capabilities. Digital Prescription Management does not require AI.

**UI component idea:**  
Toggle switches for each add-on with a live "Estimated monthly total" placeholder.

---

### 4.4 Feature Comparison Matrix

| Feature | Core | Core + PQV | Core + Communication | Core + Clinical | Full Platform |
|---|---|---|---|---|---|
| Organization workspace & tenant isolation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Doctor entries & patient registration | ✅ | ✅ | ✅ | ✅ | ✅ |
| Appointment models (time-slot, serial, hybrid) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Daily appointment board & queue management | ✅ | ✅ | ✅ | ✅ | ✅ |
| Walk-in registration & placement | ✅ | ✅ | ✅ | ✅ | ✅ |
| Role-based access & audit logging | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bangla/English UI, mobile-friendly | ✅ | ✅ | ✅ | ✅ | ✅ |
| DQDS public queue display (no PII) | ❌ | ✅ | ❌ | ❌ | ✅ |
| PQT private tracking link & QR | ❌ | ✅ | ❌ | ❌ | ✅ |
| WhatsApp/SMS N1 & N2 notifications | ❌ | ❌ | ✅ | ❌ | ✅ |
| Operational reports | ❌ | ❌ | ❌ | ❌ | ✅ |
| Clinical encounter notes & templates | ❌ | ❌ | ❌ | ✅ | ✅ |
| Digital prescriptions & medicine catalogue | ❌ | ❌ | ❌ | ✅ | ✅ |
| Encounter history & record retrieval | ❌ | ❌ | ❌ | ✅ | ✅ |
| Private doctor-only dictation | ❌ | ❌ | ❌ | ❌ | ✅ |
| AI-assisted note/prescription drafting | ❌ | ❌ | ❌ | ❌ | ✅ |

**Footnote:**  
✅ = Included. ❌ = Not included. Module availability subject to entitlement and separate commercial approval.

**UI component idea:**  
Interactive table with column filters and a "Compare selected plans" button.

---

### 4.5 Primary CTA

**Headline:**  
Choose the modules your facility needs.

**Button:**  
Get a Custom Quote  
Link: /pricing or /contact-sales

**Secondary text:**  
No patient portal. No payment gateway. No forced clinical records. Pay only for the modules you activate.

---

## 5. Interactive Demo / Clinical Documentation Preview Section

### 5.1 Section Headline

**Section headline:**  
See AMSDP in Action

**Intro copy:**  
Explore a guided walkthrough of the daily appointment board, queue management, and—if separately authorized—the clinical documentation demonstrator. Every demonstrated action uses a working API and persists appropriately; prototypes are explicitly labelled.

### 5.2 Interactive Walkthrough Components

**Component 1: Receptionist Board Simulator**

**Headline:**  
Manage Today's Queue

**Copy:**  
Simulate a receptionist's morning: register a patient, book a serial appointment, check in a walk-in, and reorder the queue using drag-and-drop or move-up/move-down buttons.

**Proposed interactions:**
- Click "Register Patient" → enter name and mobile number → see duplicate warning if applicable.
- Click "Book Appointment" → select doctor, date, and serial → see slot/serial assigned.
- Click "Check In" → status changes to CHECKED_IN.
- Drag a queue card up/down → see audit log entry (previous position, new position, actor, timestamp, reason).
- Click "Complete Consultation" → status moves to COMPLETED.

**UI component idea:**  
A Kanban-style board with columns: BOOKED, CHECKED_IN, IN_QUEUE, IN_CONSULTATION, COMPLETED. Cards show patient name (placeholder), serial number, and status chip.

**CTA:**  
Reset Simulation →

---

**Component 2: Patient Queue Tracking (PQT) Preview**

**Headline:**  
See What Your Patients See

**Copy:**  
Open a private tracking page via an unguessable token or QR code. View your token, doctor/branch, currently-serving token, patients ahead, and estimated wait time.

**Proposed interactions:**
- Enter a sample tracking token (or scan a mock QR code).
- See "You are patient #4. Currently serving: T-08. Estimated wait: ~20 minutes (estimate)."
- Polling simulation: queue position updates every few seconds without page reload.
- Display "No-cache" and "token revoked" states for cancelled/rescheduled appointments.

**UI component idea:**  
Mobile phone frame showing the PQT page with large, readable tokens and a "Return before your turn" guidance message.

**CTA:**  
Generate Sample Token →

---

**Component 3: DQDS Waiting-Room Display**

**Headline:**  
Waiting-Room Screen (Public, No PII)

**Copy:**  
View a read-only public display showing only tokens and queue status. No patient names, mobile numbers, or personal information.

**Proposed interactions:**
- Toggle between "Empty queue" and "Active queue" states.
- See currently-serving token and upcoming tokens.
- Observe auto-refresh without staff interaction.

**UI component idea:**  
Wide screen mockup with large token text: "NOW SERVING: T-12" and "NEXT: T-13, T-14, T-15".

**CTA:**  
View Display Mode →

---

### 5.3 Clinical Documentation Preview (Optional Demonstrator)

**Headline:**  
Doctor's Clinical Workspace (Bounded Demonstrator)

**Copy:**  
If separately authorized for demonstration, this preview shows a doctor opening an encounter, selecting a note template, entering a note manually, choosing a medicine from the catalogue, and finalizing a prescription. Optional private dictation may prepare a draft from doctor speech.

**Proposed interactions:**
- Select patient record (organization-scoped).
- Start encounter → choose "General Consultation" template.
- Fill structured fields: chief complaint, assessment, treatment plan.
- Select medicine from catalogue → enter dose, route, frequency, duration.
- Preview prescription → click "Finalize Prescription" → see immutable version stored.
- Optional: Click "Dictate Note" → microphone indicator activates → transcript appears → AI structures draft → doctor edits and approves.

**Explicit disclaimers (must be shown in UI):**
- This is a demonstrator, not a live clinical system.
- No autonomous diagnosis or prescribing.
- No ambient patient-conversation recording.
- AI output is a draft; doctor approval required.
- Every action calls a working API and persists to the database (or is explicitly labelled as prototype).

**UI component idea:**  
Two-pane view: left side shows the encounter note editor; right side shows the prescription builder with medicine search and a "Finalize" button. A red banner at the top reads "DEMONSTRATOR — NOT FOR LIVE CLINICAL USE."

**CTA:**  
Start Clinical Demo →

---

### 5.4 Demo Navigation & Compliance

**Copy:**  
All demo data is sample or synthetic. No real patient data is used in the public demo. Role-based access is simulated; unauthorized actions are blocked with permission messages.

**UI component idea:**  
A top navigation bar with three demo paths: "Receptionist Flow," "Patient Tracking Flow," and "Doctor Clinical Flow." Each path has a progress indicator and an "Exit Demo" button.

---

## 6. Global Copy & Style Notes

**Tone:**  
Clear, professional, facility-focused, and reassuring. Avoid clinical jargon where plain language works. Emphasize staff empowerment, not patient self-service.

**Language:**  
English primary; Bangla UI support noted as a platform capability. All patient-facing copy in the demo should be simple and translatable.

**Prohibited claims (per V2.5/V2.3):**
- Do not claim zero waiting or guaranteed consultation times.
- Do not claim measured reductions in waiting time without pilot data.
- Do not claim AI clinical accuracy or autonomous diagnosis/prescribing.
- Do not claim a national or cross-clinic patient medical-history repository.
- Do not claim patient accounts, self-booking, or a patient portal.
- Do not claim payment processing or bKash/Nagad integration.

**Approved positioning lines:**
- Public: "Less Waiting. Less Crowding. Better Healthcare Experiences."
- Clinical: "AMSDP — Intelligent Clinical Documentation: Less typing. Faster documentation. Complete clinical control."

**Placeholder conventions:**  
Use [Placeholder: ...] for testimonials, logos, metrics, and pricing figures that require product owner or commercial approval.

---

**End of proposal.**
