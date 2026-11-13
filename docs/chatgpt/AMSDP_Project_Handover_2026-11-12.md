# AMSDP Project Handover

## Conversation closeout and continuation context

**Document created:** 2026-11-12\
**Timestamp:** 2026-11-12 13:14:44 Bangladesh Standard Time (UTC+06:00)\
**Project:** AMSDP\
**Purpose:** Preserve the decisions, product direction, repository
status, implementation governance and immediate next steps for a new
ChatGPT conversation.

------------------------------------------------------------------------

## 1. Executive summary

AMSDP completed its first hackathon MVP push to `origin/hackathon-mvp`:
seven commits were created and pushed successfully. A documentation-only
follow-up, C-8, was authorized and a Cline prompt was provided, but
**C-8 completion has not yet been reported**.

The next phase is to implement the approved **AMSDP Master Feature List
V2.5** incrementally, using the existing MVP as the foundation. Do not
rebuild the application or implement all of V2.5 at once.

The latest product-scope clarification (2026-11-12) is definitive:
**payment, billing, insurance/claims, patient portal and external
EHR/hospital integrations are not deferred features. They are outside
AMSDP's intended product scope unless the product owner explicitly
changes that decision.**

Recommended next product task: a read-only baseline audit comparing the
actual committed repository against V2.5, using the clarified product
scope. Then prepare a dependency-aware release roadmap and
accept/stabilize the existing Practice Operations MVP before expanding
into Clinical Management.

------------------------------------------------------------------------

## 2. Governance and working relationship

-   AMSDP is the primary mission. AILI exists only to support AMSDP;
    AILI development is frozen unless explicitly requested.
-   The user is product owner and final approver.
-   ChatGPT provides product, architecture, requirements, quality and
    acceptance oversight.
-   Cline performs hands-on repository inspection and implementation.
-   Never claim Cline implemented, tested, accepted or deployed anything
    unless the user supplies evidence/report.
-   User works in Ubuntu local environment. ChatGPT cannot inspect that
    local filesystem directly; Cline instructions must be precise and
    bounded.
-   Prefer complete vertical slices: backend, persistence,
    security/permissions, frontend and tests together.
-   Demo data is acceptable; fake functionality is not. Demo
    interactions must call real APIs and persist to PostgreSQL.
-   Every Cline task must have a meaningful unique task ID.
-   Cline instructions should specify task ID, scope, dependencies,
    acceptance criteria, tests, boundaries and completion report.
-   Preserve unrelated owner changes.
-   Never stage, commit, push, merge, deploy, reset, clean, stash,
    revert or discard work without explicit authorization.
-   Avoid repetitive audits and unnecessary process expansion;
    prioritize a working user-facing MVP.
-   Do not address the user by name.

**Cline prompt format:** Complete instructions use a writing block with
`variant="chat_message"`, title and unique five-digit ID, with concise
framing unless the user asks for only the prompt.

------------------------------------------------------------------------

## 3. Product identity and positioning

### Approved public positioning

**AMSDP --- Less Waiting. Less Crowding. Better Healthcare
Experiences.**

This remains the primary public-facing positioning.

Core idea: - Patients should not have to remain inside a crowded waiting
area throughout their entire estimated wait when it is safe and
appropriate to step away. - Patients can monitor their queue remotely
and return before their turn. - Facilities gain better patient-flow
visibility and may reduce unnecessary waiting-area occupancy.

Do not claim zero waiting, guaranteed consultation times, or measured
reductions without pilot evidence. Distinguish physical waiting-area
time, waiting-area occupancy and total appointment-to-consultation time.

### Three connected product layers

1.  **AMSDP Practice Operations** --- organization/branch operations,
    staff, patient registration, appointments, queues and patient queue
    visibility.
2.  **AMSDP Clinical Management** --- encounters, organization-scoped
    encounter history, clinical notes, vitals/observations and digital
    prescriptions.
3.  **AMSDP Intelligent Clinical Documentation** --- private doctor
    dictation and AI-assisted structuring, with doctor control.

These are modular. A small practice can use Practice Operations without
being forced to activate Clinical Management.

------------------------------------------------------------------------

## 4. Confirmed product scope and exclusions

### 4.1 In-scope product areas

#### A. Practice Operations

-   Organization and branch management.
-   Doctor and staff management.
-   Patient registration and operational patient records.
-   BanglaNameSense in patient registration.
-   Doctor availability and appointment scheduling.
-   Receptionist-managed appointment booking.
-   Appointment confirmation and reminders (WhatsApp and SMS product
    scope approved; provider integration is not assumed implemented).
-   Patient check-in.
-   Queue management, repositioning and recovery.
-   Public Digital Queue Display (DQDS).
-   Private, account-free Patient Queue Tracking (PQT).
-   Appointment cancellation and rescheduling.
-   Role-based access control and organization/branch isolation.
-   Audit history and operational reporting.
-   One-command restartability and reliable persistence.

#### B. Clinical Management

-   Organization-scoped encounter management and encounter history.
-   Clinical notes, structured templates and manual note entry.
-   Vitals and relevant clinical observations.
-   Practice-specific clinical configuration.

Clinical Management is optional and organization-scoped. It must not be
a prerequisite for a clinic that only wants Practice Operations.

#### C. Digital Prescription

-   Medicine catalogue, search and autocomplete.
-   Doctor-specific medicine favourites.
-   Common instructions library.
-   Structured prescription templates.
-   Manual prescription creation.
-   Dosage, frequency and duration entry.
-   Prescription preview and printing.
-   Prescription history linked to encounters.
-   Explicit doctor review and approval.

A doctor must be able to create a complete prescription without AI.

#### D. Intelligent Clinical Documentation

-   Private doctor-only voice dictation after consultation.
-   AI-assisted structuring of doctor-provided information into
    clinical-note sections.
-   Recognition of explicitly dictated medicines and instructions.
-   Medicine-catalogue matching where possible.
-   Warnings for ambiguity or missing information.
-   Draft review, editing and explicit doctor approval.
-   Secure persistence of approved clinical documentation.

### 4.2 Explicitly out of scope --- not deferred

The product owner clarified on 2026-11-12 that these capabilities were
never intended to be part of AMSDP's product direction. Do not classify
them as missing or deferred V2.5 implementation work:

  Capability                                        Classification
  ------------------------------------------------- ----------------
  Payment gateway integrations                      Out of scope
  bKash, Nagad, Rocket and Bangla QR integrations   Out of scope
  Advance or partial appointment payments           Out of scope
  Billing and revenue-cycle management              Out of scope
  Insurance and claims management                   Out of scope
  Patient portal and patient accounts               Out of scope
  Patient self-service booking through a portal     Out of scope
  Patient secure-messaging inbox                    Out of scope
  External hospital/EHR integrations                Out of scope

Do not create workstreams, APIs, database models or roadmap tasks for
these capabilities unless the product owner explicitly reopens scope.

### 4.3 Patient-facing functionality that remains in scope

Excluding a patient portal does **not** exclude patient-facing queue
visibility.

#### DQDS --- Digital Queue Display (approved P0)

-   Public, read-only waiting-room display.
-   Token-only.
-   Must not display patient names, phone numbers, DOB, age or other
    PII.
-   Separate from private patient tracking.

#### PQT --- Patient Queue Tracking (approved P0)

-   Appointment-specific private tracking via unguessable token URL/QR.
-   No patient account, password, portal, self-booking or mandatory app.
-   Receptionist books appointment; system generates tracking link/token
    and QR.
-   Patient accesses link via WhatsApp/SMS or printed QR.
-   Shows own token, doctor/branch, currently serving token, patients
    ahead, ETA/status.
-   15-second polling in approved implementation scope.
-   Token revoked when consultation starts, appointment is cancelled or
    rescheduled; never reactivated.
-   Store token hash at rest; treat token as a capability credential;
    use no-cache private responses.
-   ETA is an estimate, not a guarantee; communicate queue changes and
    return buffer.
-   Do not encourage patients requiring urgent care or told to remain to
    leave.
-   No-show is staff-confirmed under grace-period policy; never
    automatic based on elapsed time, tracking-page activity or message
    status.

------------------------------------------------------------------------

## 5. Approved operational decisions

### 5.1 Missed-turn recovery

Approved for MVP: - Default staff-confirmed recovery moves an
unavailable patient to the end of the same applicable active queue. -
Authorized staff may reposition to another valid position in the same
queue when necessary. - Preserve original appointment and token
identity/history. - No cancel/recreate/reschedule as a recovery
mechanism. - Explicit action; mandatory reason for repositioning. -
Audit old/new position/status, actor, role, timestamp, action type and
reason. - No cross-doctor, cross-branch, cross-date or cross-room
movement. - No automatic missed-turn detection. - AMSDP does not
clinically triage or determine urgency.

### 5.2 Doctor and receptionist queue permissions

Decision ID:
`AMSDP-PRODUCT-DECISION-DOCTOR-RECEPTIONIST-QUEUE-RECOVERY-2026-11-10`

Both `doctor` and `receptionist` may have `queue.recover` and
`queue.reposition`, subject to authorized organization, branch and
applicable doctor/day queue.

-   Receptionist: recover to end of same queue and reposition to valid
    position with mandatory reason.
-   Doctor retains both permissions.
-   Audit actor/role/time/old-new position/reason.
-   Preserve original appointment and token history.
-   No cross-doctor/branch/date movement.
-   No automatic detection.

This supersedes earlier doctor-only approval. Existing implementation
was reported to grant both roles; verify against code/tests rather than
reimplementing without cause.

### 5.3 Messaging

WhatsApp and SMS are approved P0 product scope, independently
configurable at organization-admin level. Provider integration is not
assumed implemented.

-   N1 appointment confirmation immediately after booking.
-   N2 pre-visit reminder, default 10 minutes before expected visit;
    admin can configure approved 5/10-minute options/range.
-   Queue-aware scheduling, cooldown and deduplication.
-   Cancel pending reminders on cancellation, reschedule, consultation
    start or check-in.
-   Avoid unnecessary return reminder after check-in.
-   Booking must work if messaging is unavailable or unconfigured.
-   Never claim delivery unless provider confirms.
-   Organization-scoped provider configuration/secrets; platform Super
    Admin controls approved providers/restrictions.
-   Mock adapter/manual link sharing fallback first.
-   No paid provider registration or purchase without owner approval.

### 5.4 BanglaNameSense

Approved as a core MVP differentiator; implementation was reported
complete, but product-owner acceptance remains distinct from
implementation.

-   Source: `~/bangla_name_sense/bangla_name_sense.json`.
-   JSON structure: `{total_count, names}`; each record
    `{en,bn,gender}`.
-   Inspected dataset: 718 records, 701 distinct Bangla strings, 718
    unique English strings, 404 female / 314 male; no missing fields.
-   Dataset is not comprehensive or authoritative.
    Provenance/authorship/redistribution license require confirmation
    before publishing/redistributing.
-   Preserve source JSON; deduplicate suggestions at runtime/display.
-   `bn` primary display; `en` optional search alias.
-   Ignore `gender` completely for
    suggestion/filtering/ranking/inference.
-   Frontend-only local feature; no backend service, DB table,
    migration, AI calls or per-keystroke API calls.
-   Initially integrated into existing patient registration name-entry
    field.
-   Prefix/multi-word matching, optional English alias, deterministic
    ranking.
-   Accessible keyboard/mouse/touch.
-   Manual entry always allowed; never auto-select or overwrite.
-   Preserve patient API, validation, duplicate warning, authorization,
    tenant isolation and persistence.

Implementation report:
`docs/implementation/AMSDP_BanglaNameSense_Implementation_Report_V1.0.md`

Earlier reported frontend tests: 43 passed. Browser-level verification
was not present in the earlier audit. `frontend/pages/patients.js` and
`frontend/styles/global.css` were mixed-ownership files and excluded
from the initial push.

### 5.5 Clinical documentation boundaries

-   AI must not require interaction in front of patients.
-   Do not make doctors appear dependent on AI.
-   No ambient recording of patient-doctor conversations in initial
    scope.
-   Voice dictation is private doctor-only dictation after consultation.
-   AI can organize doctor-provided content and extract explicitly
    dictated medicines/instructions.
-   AI must not autonomously diagnose, select medication, prescribe or
    invent missing clinical details.
-   AI output is a draft; explicit doctor review/approval is mandatory.
-   No centralized cross-clinic medical-history repository. Encounter
    history is organization-scoped.
-   Patient personal data is not automatically owned by clinic or AMSDP;
    legal roles depend on actual processing purposes and activities.
-   Audio temporary processing/deletion by default, subject to approved
    lawful retention and verified provider deletion.
-   Privacy/legal/provider review required before real patient data
    flows to AI services.

------------------------------------------------------------------------

## 6. Master Feature List V2.5 governance

-   V2.5 is the sole active Master Feature List and supersedes
    V1.x--V2.4 for active planning.
-   V2.3 complete source is preserved in V2.5 Appendix A for historical
    traceability.
-   V2.5 includes product modules, practice operations, Clinical
    Management, Digital Prescription, medicine support library,
    encounter history, Intelligent Clinical Documentation, private
    doctor dictation, AI drafting rules, data governance, role
    permissions, release gates, hackathon scope and roadmap.
-   V2.5 is a product feature catalogue, not blanket authorization to
    implement every feature immediately.
-   Task-level product approvals and scope decisions govern
    implementation.
-   Apply the explicit out-of-scope clarification in Section 4.2 when
    auditing V2.5. Do not report excluded capabilities as missing
    implementation.
-   V2.5 file previously generated as
    `AMSDP_Master_Feature_List_V2.5_Modular_Platform_Intelligent_Clinical_Documentation.md`.
-   Earlier verification: 129,129 bytes, 2,762 lines, SHA-256
    `6be222504b9dabe1a108e0a922e340705c482de7ece75dccec26baf7a1939f7e`.
-   Verify its current repository path and index entry before assuming
    the latest Git state.

------------------------------------------------------------------------

## 7. Release strategy

Do not rebuild the MVP or attempt a big-bang implementation.

### Release 1 --- Practice Operations MVP stabilization and acceptance

Validate the committed MVP end to end: 1. Organization and branch setup.
2. Doctor and staff management. 3. Patient registration and
BanglaNameSense. 4. Doctor availability and appointment scheduling. 5.
Receptionist-managed booking. 6. Appointment confirmation and check-in.
7. Queue management and repositioning. 8. DQDS public display. 9. PQT
private account-free tracking. 10. Missed-turn recovery. 11.
Cancellation and rescheduling. 12. Audit history and role permissions.
13. Organization/branch isolation. 14. Mobile responsiveness. 15.
One-command restart and PostgreSQL persistence.

Acceptance criteria: - Receptionist registers a patient and books an
appointment. - Doctor sees the correct applicable queue. - Receptionist
checks in the patient. - Queue changes appear correctly. - Patient
privately tracks only their own queue without account creation. - Public
display reveals no patient-identifying information. - Recovery preserves
original appointment/token history. - Role and tenant isolation are
verified. - Restart does not lose persisted data.

Do not add new modules before existing workflows pass acceptance.

### Release 2 --- Clinical Management

-   Optional, organization-scoped encounters.
-   Encounter creation linked to patient and appointment as appropriate.
-   Structured and manual clinical notes.
-   Vitals/clinical observations.
-   Organization-scoped encounter history.
-   Permissions, audit and privacy controls.

Suggested vertical slice:
`Patient → Appointment → Check-in → Encounter → Clinical Note → Encounter History`

### Release 3 --- Digital Prescription

-   Medicine catalogue and search/autocomplete.
-   Doctor favourites.
-   Common instructions.
-   Structured prescription templates.
-   Manual prescription creation.
-   Dose/frequency/duration fields.
-   Preview/print.
-   Encounter-linked prescription history.
-   Explicit doctor approval.

No AI dependency for ordinary prescription creation.

### Release 4 --- Intelligent Clinical Documentation

-   Private doctor-only dictation after consultation.
-   Speech-to-text.
-   AI organization into structured note draft.
-   Explicitly dictated medicine/instruction extraction.
-   Catalogue matching.
-   Ambiguity/missing-field warnings.
-   Doctor edit/review/approval.
-   Approved record persistence.
-   Privacy, retention and provider review before real patient data use.

**Do not create releases/workstreams for payment, billing, insurance,
patient portal, secure messaging inbox or external EHR/hospital
integrations. Those are explicitly out of product scope.**

------------------------------------------------------------------------

## 8. Recommended next tasks

### Task 1 --- Read-only baseline audit

**Task ID:** `AMSDP-V25-MVP-BASELINE-AUDIT-2026-11-12`

Objective: Compare the actual committed repository implementation
against the active V2.5 feature list, applying the clarified product
scope.

For every in-scope feature, classify: - Implemented and verified. -
Implemented but not verified. - Partially implemented. - Not
implemented. - Requires product decision. - Deferred to a later approved
release.

Classify explicitly out-of-scope features separately; do not count them
as gaps.

Requirements: - Read `.clinerules`, documentation index, V2.5 and
relevant product decision docs. - Inspect actual repository code, APIs,
models, migrations, frontend, permissions and tests. - Distinguish code
presence from working end-to-end behavior. - Cite actual file paths and
relevant tests/evidence. - Do not rely solely on previous Cline
reports. - No code changes, migrations, staging, commits or pushes. -
Produce a feature-by-feature traceability matrix and evidence-based gap
analysis.

### Task 2 --- Release roadmap

**Task ID:** `AMSDP-V25-RELEASE-ROADMAP-2026-11-12`

Use the baseline audit to produce: - Dependency-aware releases. -
P0/P1/P2/P3 priorities. - Vertical-slice task breakdown. -
Database/API/frontend/security/test impacts. - Acceptance criteria. -
Explicit scope exclusions. - Risks and product decisions required.

### Task 3 --- Release 1 acceptance

**Task ID:** `AMSDP-RELEASE-1-MVP-ACCEPTANCE-2026-11-12`

Test the existing Practice Operations MVP end to end. Separate
implementation status, test evidence and product-owner acceptance. Do
not treat prior implementation reports as acceptance.

------------------------------------------------------------------------

## 9. Repository and Git status --- last reported

### First MVP push

The first push to `origin/hackathon-mvp` completed successfully on
2026-11-12.

  -------------------------------------------------------------------------------------------------------------------------------------------------
  Commit           Hash                             Paths Subject
  ---------------- ---------------- --------------------- -----------------------------------------------------------------------------------------
  C-1              `261e1f4`                           45 `chore(governance): add the agent rules and the AMSDP documentation set`

  C-2              `8ab01d0`                            4 `chore(infra): environment-driven credentials and the documented env contract`

  C-3              `1448612`                           86 `feat(backend): multi-service identity, org, patient, doctor, scheduling, queue, audit`

  C-4              `3cff475`                           24 `feat(frontend): shared shell and application pages`

  C-5              `e240bc5`                           13 `feat(frontend): BanglaNameSense patient-name suggestion`

  C-6              `7f39b4d`                            7 `chore(ai_factory): execution fixes and AILI reports`

  C-7              `a0d6ded`                           14 `docs(demo): hackathon runbook, rotated credential sheet and demo images`
  -------------------------------------------------------------------------------------------------------------------------------------------------

Full C-7 hash: `a0d6dedea34109f8199915f919096e32cb6c68a6`

Reported remote verification: -
`HEAD = origin/hackathon-mvp = a0d6dedea34109f8199915f919096e32cb6c68a6`. -
193 unique paths changed from `eb87cac..HEAD`. - Exact path-set equality
checked for each commit group. - Fourteen exclusions remained
uncommitted. - Secret scan of 43,539 added lines: zero hits. -
Repository reported private; anonymous GitHub GET returned 404. -
`origin/main` remained at `eb87cac`; hackathon branch was seven commits
ahead with no divergence.

### C-8 follow-up

C-8 was authorized and a Cline prompt provided.

Exact authorized paths: 1.
`docs/audit/AMSDP_Tree_Commit_and_Push_Execution_Record_V1.0.md` 2.
`docs/governance/AMSDP_Docs_Index_V1.0.md`

Proposed commit: `docs(audit): record MVP commit and push execution`

**C-8 completion has not been reported** in this conversation. Verify
current Git state before assuming it was committed or pushed.

### Remaining follow-up items from last report

-   R-1: Redacted M2 security report vs keep excluded.
-   R-2: Four demo passwords remain documented in remote history; rotate
    before public mirror/broader distribution.
-   R-3: `frontend/pages/patients.js` and `frontend/styles/global.css`
    follow-up/acceptance; both were excluded from the first push because
    of mixed ownership.
-   R-5: No CI workflow exists; CI is not claimed and may be deferred.
-   Fast-forwarding `main` was optional and recommended to defer.

Do not let these housekeeping items distract from hackathon MVP
validation. Never treat credentials already in Git history as safe
merely because the repository is private. Rotate any still-live
credentials before wider distribution.

### Previously documented exclusions from the first push

The final execution report listed fourteen excluded paths, including: -
`_tools/*` (8 paths). - `docker-compose.demo.yml`. -
`docs/security/*`. - `AMFSDP_Master_Feature_List_V2.0_Draft.md`. -
`docs/architecture/AMSDP_System_Architecture_V1.0.md`. -
`frontend/pages/patients.js`. - `frontend/styles/global.css`.

Verify the current post-C-8 state before relying on exact working-tree
counts.

------------------------------------------------------------------------

## 10. Credential and security notes

-   Earlier audit found a local-only credential exposure in
    `refs/cline/*`; user-reported final audit stated it was not on
    `origin/main`, and credential rotation was verified.
-   The C-7 report states the committed closeout report had no
    demo-password literals and committed additions passed the secret
    scan.
-   A live demo admin password had previously been reported in
    `origin/main` (B-12). Ensure it has been rotated and the demo still
    works.
-   Four other documented demo passwords were reported as needing
    rotation before public mirror/broader distribution.
-   Never reproduce secrets in prompts, terminal output or
    documentation.
-   `docs/security/*` and the M2 security report were excluded from the
    first push.
-   Privacy and security review is required before processing real
    patient data or sending patient information to external AI/messaging
    providers.

------------------------------------------------------------------------

## 11. Documentation governance

-   New AMSDP reports belong under `docs/` in appropriate subject
    folders.
-   `ai_factory/docs/` remains AI Factory operational material and
    legacy reports; do not place new AMSDP reports there.
-   Do not overwrite/delete historical documentation.
-   Owner-controlled documents are read-only unless the owner explicitly
    authorizes specific edits.
-   Moves require collision checks, SHA-256 before/after and manifest
    entry.
-   Each Cline task begins by reading
    `docs/governance/AMSDP_Docs_Index_V1.0.md` and relevant docs.
-   Update the index in the same task when documents are added or moved.
-   If index and tree disagree, inspect actual tree and report
    discrepancy.
-   Do not cite documents as inspected unless actually opened in the
    current task.
-   Preserve `.clinerules` §11 and §12 requirements.

------------------------------------------------------------------------

## 12. Implementation and acceptance principles

1.  A feature listed in V2.5 is not automatically authorized for
    immediate implementation.
2.  Product scope exclusions must not be misreported as missing
    features.
3.  Do not rebuild working MVP foundations.
4.  Prefer one complete vertical slice over disconnected screens.
5.  Every user-facing action must call a real API and persist correctly
    where persistence is required.
6.  Demo data is acceptable; fake actions are not.
7.  Protected operations must enforce server-side authorization,
    organization/branch boundaries and audit requirements.
8.  Public displays must not expose patient PII.
9.  Private patient tracking must use secure unguessable capability
    tokens, hashed at rest and revocable.
10. Do not claim message delivery without provider confirmation.
11. No automatic no-show or missed-turn decisions.
12. AI outputs remain drafts until doctor approval.
13. No autonomous clinical diagnosis, medicine selection or prescribing.
14. Separate implemented, tested, verified and product-owner-accepted
    statuses.
15. Do not stage/commit/push without explicit authorization.

------------------------------------------------------------------------

## 13. How the next conversation should begin

Suggested opening message:

> Continue AMSDP using the attached handover document as the
> authoritative conversation context. First, confirm the current
> repository/C-8 status from the evidence I provide. Then help me
> prepare the read-only V2.5-to-MVP baseline audit using the clarified
> product scope. Do not propose payment, billing, insurance, patient
> portal or external EHR integrations; these are explicitly out of
> scope. Do not ask Cline to modify code until the baseline audit and
> release plan are reviewed.

The next assistant should: 1. Acknowledge the handover. 2. Preserve
product scope and governance decisions. 3. Avoid reopening settled
decisions without new evidence. 4. Ask for/use latest Cline/Git status
if current repository state matters. 5. Prepare the bounded read-only
baseline audit instruction when requested.

------------------------------------------------------------------------

## 14. Source and evidence caveat

This handover consolidates decisions and status reports supplied in the
prior conversation. Repository status, C-8 completion, credential
rotation and implementation claims are not independently re-verified by
this document. Treat reported evidence as project history and verify
current state before any new repository action.

**End of handover.**
