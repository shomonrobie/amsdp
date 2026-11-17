# AMSDP Connect --- Proposed Communication and AI Capabilities

**Document status:** Proposal / hypothesis\
**Product:** AMSDP --- Healthcare Service-Delivery and Operations
Platform\
**Prepared:** 16 November 2026\
**Implementation status:** Not approved for implementation\
**Scope:** Optional communication, voice and AI capabilities for future
commercial and public-sector deployments

------------------------------------------------------------------------

## 1. Purpose

This document records potential communication and AI capabilities that
may extend AMSDP in the future. It separates ideas worth researching
from approved Core product functionality.

AMSDP's primary product value remains reliable healthcare service
delivery and operations: patient registration by authorized staff,
appointments, scheduling, doctor and room allocation, queue management,
operational visibility, governance and related workflows.

The capabilities in this document are **not committed Core features**.
They are hypotheses to validate through customer discovery,
public-sector engagement, technical evaluation and controlled pilots.

> **Important scope boundary:** Intelligent Queue Announcements /
> Bangla-English Queue Voice Callouts is a separate AMSDP Core
> capability. It must be documented in the relevant Core queue and
> implementation documents, not treated as a proposed conversational-AI
> feature in this document.

## 2. Product positioning

### 2.1 AMSDP Core

AMSDP Core provides the operational foundation for different healthcare
delivery models. Facilities should be able to adopt AMSDP's operational
capabilities without having to adopt conversational AI, WhatsApp booking
or locally hosted language models.

### 2.2 AMSDP Connect

**AMSDP Connect** is a proposed umbrella for optional patient and
workforce communication capabilities, potentially including:

-   WhatsApp-based service information and notifications.
-   Appointment reminders and status updates.
-   Assisted appointment enquiries.
-   Optional conversational interactions.
-   Voice-message intake and transcription.
-   Bangla and English speech interfaces.

The name does not imply that these capabilities are already implemented,
commercially validated or approved for the current MVP.

### 2.3 Different deployment contexts

The likely value proposition may differ by deployment:

  -----------------------------------------------------------------------
  Context                 Potential direction     Validation required
  ----------------------- ----------------------- -----------------------
  Private hospitals and   Operational             Willingness to pay,
  clinics                 notifications and       staff workflow fit,
                          selected communication  patient adoption,
                          conveniences            support cost

  Public hospitals        Service information,    Government
                          access support and      authorization,
                          selected communication  operational ownership,
                          workflows               procurement,
                                                  infrastructure and
                                                  integration

  Government community    Voice-enabled support   Field research, worker
  and outreach programmes for health workers,     needs, connectivity,
                          programme information,  governance and
                          follow-up and field     compatibility with
                          workflows               existing systems
  -----------------------------------------------------------------------

Do not assume that public-sector use cases are automatically viable.
They are hypotheses requiring stakeholder engagement and field
validation.

## 3. Proposed capability areas

All capabilities in this section are **proposed / hypothesis**, not
approved implementation commitments.

### 3.1 WhatsApp communication

Potential capabilities:

-   Appointment confirmation and status notifications.
-   Appointment reminders.
-   Instructions about facility location, arrival and check-in.
-   Follow-up or service-session reminders where authorized.
-   Patient-initiated enquiries about services and operational
    information.

A notification-only capability may be simpler to validate than
conversational booking. Any outbound messaging must comply with the
applicable official WhatsApp Business Platform requirements, templates,
consent and pricing.

### 3.2 Assisted appointment enquiry and booking support

A future assistant could collect a patient's preferred facility,
service, doctor or time and help them understand available options.

Two distinct operating modes must not be conflated:

**Mode A --- Assisted enquiry (candidate starting point)**

1.  The assistant collects the patient's request and preferences.
2.  It retrieves information from authoritative AMSDP services, where
    permitted.
3.  It explains options or forwards the request to authorized staff.
4.  Staff remain responsible for patient registration and appointment
    creation where the deployment's policy requires it.

**Mode B --- Patient self-service booking (future hypothesis)**

1.  The patient is identified through an approved workflow.
2.  The assistant presents only real availability returned by AMSDP.
3.  The patient explicitly confirms the selected appointment.
4.  AMSDP validates and creates the booking through its authorized
    appointment workflow.
5.  The patient receives a confirmation and tracking instructions.

Mode B changes the current Core operating assumption that staff create
patient records and appointments. It therefore requires a separate
product, policy, identity, security and workflow decision before
implementation. It must not be enabled implicitly.

### 3.3 Voice-message intake

A future user may send a Bangla or English voice message instead of
typing. Speech recognition could convert the message into text or
structured intent for review.

Potential uses include:

-   Service enquiries.
-   Appointment preferences.
-   Requests for a call-back.
-   Administrative information.
-   Voice-assisted forms.

Speech recognition output must be treated as uncertain input. The user
or authorized staff should confirm important details---especially names,
dates, times, phone numbers and facility choices---before any
consequential action.

### 3.4 Public-service information assistant

A controlled assistant could help people find approved operational
information, such as:

-   Which facility offers a specified service.
-   Facility location and opening or service hours.
-   Available service sessions.
-   Administrative preparation instructions.
-   Authorized referral or follow-up information.

It must retrieve information from maintained, approved sources. It must
not invent service availability or provide diagnosis, prescribing,
clinical triage or treatment decisions.

### 3.5 Community health worker and outreach support

Potential public-sector and programme use cases include:

-   Voice-enabled capture of household visit information.
-   Dictation of services delivered and follow-up requirements.
-   Referral and follow-up coordination.
-   Outreach session schedules and operational information.
-   Assistance completing structured administrative or programme forms.

A worker must be able to review and correct transcribed or extracted
information before submission. The system should complement authorized
government workflows and existing health information systems rather than
assume it replaces them.

## 4. Local and open-source AI strategy --- research hypothesis

Local or open-weight AI components may be worth evaluating for
deployments that require data-locality, offline or low-connectivity
operation, predictable inference costs, or greater control over model
hosting.

This is a research direction, not an architecture decision or a
commitment to operate a local LLM in every AMSDP deployment.

### 4.1 Potential component types

  -----------------------------------------------------------------------
  Component               Potential role          Current status
  ----------------------- ----------------------- -----------------------
  Large language model    Conversation handling,  Research hypothesis
  (LLM)                   intent extraction and   
                          constrained             
                          administrative          
                          assistance              

  Automatic speech        Bangla/English          Research hypothesis
  recognition (ASR)       speech-to-text          

  Text-to-speech (TTS)    Bangla/English spoken   Research hypothesis
                          responses               

  Deterministic workflow  Validate permissions,   Required design
  and policy services     business rules and      principle if AI
                          actions                 capabilities are later
                                                  implemented
  -----------------------------------------------------------------------

Candidate models, datasets and licences must be re-evaluated at the time
of a technical benchmark. No model or dataset listed in earlier
exploration should be treated as selected, approved or production-ready
without checking its current model card, licence, performance and
operational requirements.

### 4.2 Avoid unnecessary LLM use

Not every voice or communication feature needs an LLM:

-   Queue announcements should use deterministic queue events and
    controlled TTS templates.
-   Fixed reminders should use approved message templates.
-   Structured forms should use deterministic validation.
-   ASR may be sufficient for voice dictation.
-   An LLM should be considered only where flexible language
    understanding provides measurable value.

### 4.3 Local hosting does not mean zero cost

A local deployment may avoid some per-request hosted-model charges, but
it still incurs hardware or hosting, electricity, storage, connectivity,
maintenance, monitoring, model updates, security and operational-support
costs. WhatsApp platform charges, where applicable, remain separate.

A cost comparison must include total cost of ownership, expected
concurrency, latency, availability and support burden---not only
inference price.

## 5. Architecture principles if capabilities are approved later

AMSDP's approved architectural direction is **microservices**. Future
communication and AI capabilities should respect that direction.

Potential boundaries may include:

-   Channel adapter(s), such as an official WhatsApp integration.
-   Communication orchestration.
-   Speech processing (ASR/TTS).
-   Optional conversational/intent service.
-   Integration adapters to existing AMSDP domain services.

These are candidate boundaries for future design, not a mandate to
create all of these services now.

### 5.1 Authoritative systems

AI components must not become the source of truth for:

-   Patient identity or registration.
-   Appointment availability or creation.
-   Doctor schedules.
-   Room/chamber allocation.
-   Queue state or token allocation.
-   Permissions and tenant access.
-   Clinical records.

The existing authoritative AMSDP services must validate all requests and
enforce business rules. Model output is untrusted input.

### 5.2 Safe action flow

For any future consequential action:

1.  Receive the user's request.
2.  Extract a proposed intent or structured fields.
3.  Validate schema, identity context, permissions and tenant scope.
4.  Retrieve current data from the authoritative service.
5.  Present the proposed action and obtain required confirmation.
6.  Execute through the authorized domain service.
7.  Return the authoritative result.
8.  Record an appropriate audit event without unnecessarily retaining
    sensitive conversational content.

Use idempotency and duplicate-prevention controls for actions such as
booking or message dispatch.

### 5.3 Appointment, check-in and queue remain distinct

A confirmed appointment is not the same as patient arrival, check-in or
a queue token being called. Any future assistant must preserve the
existing AMSDP lifecycle and must not infer that a patient has checked
in merely because they confirmed an appointment.

## 6. WhatsApp and external channel dependencies

If WhatsApp capabilities are pursued:

-   Use the official Meta WhatsApp Business Platform and authorized
    providers only.
-   Verify webhook authenticity and protect credentials.
-   Follow applicable opt-in, template, messaging-window, media and
    pricing rules.
-   Define message delivery, retry and failure handling.
-   Prevent duplicate messages and duplicate bookings.
-   Keep channel-specific logic outside core appointment and queue
    business rules.
-   Do not automate consumer WhatsApp accounts or use unofficial
    scraping or reverse-engineered interfaces.

Provider availability, commercial terms and current platform
requirements must be checked during implementation planning.

## 7. Privacy, security and clinical boundaries

Any future communication or AI capability must undergo privacy, security
and operational review before a pilot.

Minimum principles:

-   Data minimization and a defined lawful basis/consent process.
-   Clear purpose, retention and deletion rules.
-   Encryption in transit and at rest.
-   Secrets held server-side, never embedded in frontend code.
-   Tenant isolation and least-privilege access.
-   Audit consequential actions.
-   Avoid logging patient identifiers, symptoms, message bodies, audio
    content or media URLs unless strictly necessary and governed.
-   Human escalation and correction paths.
-   Protection against prompt injection and malicious message content.
-   No diagnosis, prescribing or autonomous clinical triage by a
    general-purpose conversational assistant.
-   Emergency and urgent-care messaging must be separately clinically
    reviewed and must not imply that the assistant is an emergency
    service.

Patient recordings and conversations must not be used for model training
by default. Any proposed secondary use requires separate explicit
governance, appropriate legal basis and consent where required.

## 8. Validation plan

Do not move from concept to implementation solely because a model demo
works.

### 8.1 Private-sector discovery

Interview private hospitals and clinics to understand:

-   Which communication problems create measurable operational cost?
-   Are WhatsApp reminders already used, and what is missing?
-   Would providers pay for the proposed capability?
-   Who owns the workflow and handles exceptions?
-   What support, reliability and integration requirements would apply?
-   Would staff and patients actually use voice interactions?

### 8.2 Public-sector discovery

Engage relevant government stakeholders, facility operators and
community health workers to understand:

-   Which workflows are authorized for digitization or voice assistance?
-   Which existing government systems must remain authoritative?
-   Where do connectivity, device, language or workforce constraints
    occur?
-   Who owns content, service information and operational support?
-   What approvals, procurement and data-governance requirements apply?
-   What measurable burden or access problem should a pilot address?

### 8.3 Technical evaluation

If discovery justifies a prototype, evaluate:

-   Bangla (`bn-BD`) and English recognition accuracy in realistic
    environments.
-   Code-switching and regional speech variation.
-   Accuracy for names, dates, times, phone numbers and facility names.
-   TTS intelligibility and latency on actual devices.
-   LLM structured-output validity and refusal behaviour.
-   Human correction and escalation rates.
-   Offline/low-connectivity behaviour where required.
-   Total cost of ownership and concurrent-user capacity.
-   Security, privacy and operational resilience.

Use consented, appropriately governed test data. Do not use real patient
recordings as a casual development dataset.

## 9. Suggested staged roadmap

  -------------------------------------------------------------------------
  Stage                   Work                      Exit condition
  ----------------------- ------------------------- -----------------------
  0 --- Discovery         Private-sector interviews Validated problem,
                          and                       owner, workflow and
                          public-sector/workforce   target users
                          research                  

  1 --- Low-risk          Assess notification and   Confirmed channel,
  communication           service-information needs consent and operational
                                                    process

  2 --- Voice feasibility Benchmark Bangla/English  Measured quality on
                          ASR and TTS               representative,
                                                    governed test data

  3 --- Controlled        Prototype one narrow,     User testing, security
  prototype               non-clinical workflow     review and measurable
                                                    benefit

  4 --- Authorized pilot  Pilot with a willing      Pilot evidence,
                          organization and approved operating model and
                          data/process              support plan

  5 --- Product decision  Decide whether to         Explicit product and
                          productize, revise or     governance approval
                          stop                      
  -------------------------------------------------------------------------

No stage automatically authorizes the next. Each requires an explicit
decision based on evidence.

## 10. Success measures

Select measures according to the validated use case. Candidate measures
include:

-   User task completion and abandonment.
-   Staff time spent on the target workflow.
-   Reminder delivery and response rates.
-   Appointment enquiry completion and escalation rates.
-   Bangla and English ASR error rates.
-   Accuracy for dates, times, names and numbers.
-   TTS intelligibility and response latency.
-   Structured-output validity.
-   Duplicate booking or duplicate action rate (target: zero).
-   Human correction and escalation rates.
-   Service availability and failure recovery.
-   Cost per completed task and total cost of ownership.
-   User and staff satisfaction.

Do not use message volume or AI interaction count alone as evidence of
healthcare value.

## 11. Decisions and open questions

### Established direction

-   AMSDP is a healthcare service-delivery and operations platform, not
    a clinic-management product being retrofitted for government.
-   The approved architecture direction is microservices.
-   AMSDP Core must remain useful without conversational AI or WhatsApp
    self-service booking.
-   Intelligent Queue Announcements / Bangla-English Queue Voice
    Callouts is a separate Core capability, documented and implemented
    through the queue workstream.
-   Existing appointment, check-in and queue lifecycles must remain
    distinct.
-   AI must not become authoritative for AMSDP domain data or clinical
    decisions.

### Proposed, not approved

-   WhatsApp conversational booking.
-   Patient self-service booking through a conversational assistant.
-   Voice-message intake.
-   Local/open-source LLM deployment.
-   Bangla/English ASR and TTS for conversational interactions.
-   Public-service information assistant.
-   Community health worker voice assistant.
-   Outreach programme assistant.

### Decisions still required

-   Which specific user problem is worth solving first?
-   Which customer or public-sector organization will sponsor and
    operate a pilot?
-   Is the initial use case notification-only, assisted enquiry, voice
    dictation or something else?
-   What identity and confirmation process is authorized?
-   Which data sources and integrations are officially available?
-   What deployment model, service-level expectation and support budget
    are realistic?
-   What measurable evidence would justify productization?

## 12. Scope boundary

This document is a strategic proposal and research backlog. It does not
authorize implementation, change the current hackathon MVP, approve
patient self-service registration or booking, approve government-system
integration, select an AI model, or establish a production deployment
commitment.

**Intelligent Queue Announcements / Bangla-English Queue Voice Callouts
belongs to AMSDP Core and its separate queue documentation.** Keep its
scope, acceptance criteria and implementation status in that workstream.

------------------------------------------------------------------------

**End of document**
