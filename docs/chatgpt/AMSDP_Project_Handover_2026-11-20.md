# AMSDP Project Handover

**Date:** 20 November 2026\
**Purpose:** Carry product decisions, implementation state, open work
and collaboration rules into a new ChatGPT conversation.

## 1. How to work on AMSDP

-   User is product owner. ChatGPT provides product/technical reasoning,
    reviews Cline reports/code and prepares task briefs only when asked.
    Cline performs local repository changes.
-   Discuss one task at a time. **Never issue a Cline prompt unless the
    user explicitly asks.**
-   Cline starts each task without prior context. Every prompt must be
    self-contained: project context, approved decisions, scope,
    boundaries, preservation requirements, acceptance criteria and
    reporting format.
-   Preserve all local modifications and untracked files. Never suggest
    destructive reset/clean/stash/checkout/branch operations without
    explicit approval.
-   Do not claim tests, browser playback, build verification or
    acceptance without evidence. Separate `OWNER-APPROVED`, `SPECIFIED`,
    `IMPLEMENTED`, `TESTED`, `BUILD VERIFIED`, `BROWSER VERIFIED`,
    `ACCEPTED`, `DEFERRED`, `BLOCKED`.
-   ChatGPT source review is not independent test execution. Do not
    address user by name unless explicitly asked.

## 2. Repository and current state

-   Repository: `shomonrobie/amsdp`; branch: `hackathon-mvp`.
-   Latest known pushed HEAD:
    `37cf3d1e9db76834044afd48fa5729463a26ec47`.
-   Latest reported local/remote state was equal (`0/0`) with clean
    working tree.
-   User authorized read-only GitHub inspection. Cline makes local
    changes/commits; ChatGPT has not modified repository files.
-   Recent commits:
    -   `37cf3d1` governance docs index/count corrections.
    -   `03d9252` Phase 3 queue gap-analysis catalogue/commit record.
    -   `3cacede` appointment Q1--Q5 specification/implementation docs.
    -   `66e545e` appointment capacity integrity, check-in authorization
        and capability grants.
    -   `e67327e` browser speech synthesis slice for QUE-006.
    -   `6b7ef4d` appointment/calendar reliability remediation
        F-01...F-19.
    -   `dee94997` operational RBAC workstreams A--D and Platform
        Identity groundwork.
    -   `0eaec020` Phase 0 MVP scope and Phase 1 operational RBAC.
-   Do not attribute 13 pre-existing untracked files to OD-1. User
    explicitly said they belonged to other workstreams and must be
    preserved.
-   User deliberately left some documentation index/reconciliation
    changes open; do not silently apply them.

## 3. Product scope --- owner-approved

AMSDP is currently an **appointment and queue management platform for
healthcare providers in Bangladesh**, initially for the Bangladesh
E-Health Hackathon & Symposium (3--5 December 2026), with a longer-term
SaaS direction.

### In scope

-   Appointment booking, rescheduling, cancellation and status
    lifecycle.
-   Doctor profiles, availability and schedules.
-   Organizations, branches, departments, floors and rooms.
-   Staff-managed patient registration and lookup for appointment
    operations.
-   Queue check-in, token generation, ordering, calling, missed-turn
    handling and recovery.
-   Doctor, receptionist/assistant and organization administration
    workflows.
-   Public token-only queue display (DQDS), with no patient-identifying
    information.
-   Private account-free appointment tracking links.
-   Bangla/English localization.
-   Branch/tenant authorization, audit and operational reporting.
-   SaaS administration, organizations, subscriptions/entitlements and
    approved deployment patterns.
-   **QUE-006 Intelligent Queue Announcements / Queue Voice Callouts**
    is an AMSDP Core capability, configurable and not forced on every
    facility.

### Explicitly outside current scope

Clinical records/consultation documentation, prescriptions, encounter
history, longitudinal records, cross-hospital record sharing, DGHS SHR
integration, AI diagnosis/clinical decision support, patient
self-registration/accounts/portal/self-service booking, payment
gateway/online collection, insurance/claims, clinical vitals and
clinical intake.

These may appear in a future module catalogue but must be marked
future/absent/out of current scope. Do not imply they are implemented.
AMSDP must not depend on independent hospitals sharing clinical records
or on a government mandate.

### MVP disposition

26 features across 14 modules: **25 KEEP / 1 DEFER**. `SYM-001` and
`QUE-006` are KEEP; `NOT-001` is DEFER. Capability classification and
release inclusion are separate decisions.

## 4. Approved business rules

Authoritative baseline: `docs/AMSDP_Business_Rules_V1.1.md`. Preserve
unless the owner explicitly approves a change.

-   Branches belong to an organization and are not separate tenants.
    Patient records are shared across branches within the organization
    subject to authorization.
-   Organization Admin manages authorized branches and organization-wide
    settings. Branch Admin is restricted to own branch.
-   Doctors can work across multiple branches/rooms by day/session.
    Schedule/session carries branch, time and optional
    floor/department/room. Multiple sessions/day supported.
-   Room overlap and same-doctor cross-branch overlap are rejected
    server-side with concurrency-safe validation. Frontend warnings are
    advisory.
-   Schedule changes must not silently rewrite existing/historical
    appointment locations. Appointment location snapshots remain
    historically stable.
-   Doctor profile: name, optional photo, BMDC number, designation,
    qualifications, structured specialties, optional
    subspecialty/experience/bio/languages, required mobile, optional
    alternate phone/email, active status.
-   BMDC registration required by default, configurable by Organization
    Admin. Number is not automatically verified; states
    `PENDING_VERIFICATION`, `VERIFIED`, `REJECTED`. Do not claim
    official BMDC integration.
-   Accepted BD phone examples: `01713002110`, `+8801713002110`,
    `8801713002110`; backend canonicalizes.
-   Consultation duration belongs to schedule/session, not permanent
    doctor profile.
-   Search existing patient before creating new. Add-New-Patient flows
    preserve entered form state.
-   Appointment and queue are separate lifecycles. Confirmed appointment
    does not imply check-in/waiting; token is generated at check-in.
-   Walk-in creates appointment from current time, selects/creates
    patient and reserves doctor/room; symptoms optional; queue check-in
    remains separate.
-   Token allocation uses atomic UPSERT keyed `(doctor_id, date)`.
-   DQDS is token-only; no patient PII.
-   Payment processing excluded; previously approved non-binding Boolean
    Yes/No flags default false/No.
-   Audit is append-only; `actor_id` required. Ordinary-role
    cross-tenant access fails closed with non-disclosing 404.
    Branch/doctor/assistant scope enforced server-side.

## 5. SaaS architecture decisions

### A1--A4

-   **A1 Microservices:** Microservices remain target architecture.
    Transitional compromises must be explicit. Existing current state
    historically used eight service processes sharing PostgreSQL and one
    Alembic chain. Do not silently redefine target as modular
    monolith/shared kernel or assume database-per-service approved.
-   **A2 Deployment:** Shared Multi-Tenant SaaS; Dedicated SaaS;
    Institution-Controlled or Approved Deployment. "Estate" means
    operator can run multiple deployment modes, not a fourth customer
    pattern.
-   **A3 Profiles:** Configurable presets independent of deployment:
    `private`, `government`, `ngo`, `community`, `outreach`.
-   **A4 Lifecycle/entitlement:** Platform Service authoritative;
    controlled/versioned distribution; tenant services enforce locally;
    no per-request synchronous platform RPC or direct shared
    business-data access. Tenant isolation, RBAC and commercial
    entitlement are independent.

### O-SaaS-1...16

1.  Separate platform identity from tenant organization identity;
    migrate legacy `super_admin` safely.
2.  Platform-only audit in `platform_audit_events`; tenant-affecting
    events in tenant `audit_events` with non-null `organization_id`.
3.  Lifecycle states: `active`, `grace`, `read_only`, `suspended`,
    `closed`. Grace = normal operation; read_only blocks writes but
    allows reads/exports; suspended blocks tenant reads/writes while
    sign-in remains for reason/support; closed blocks tenant access, no
    automatic deletion. Expiry never automatically suspends/deletes;
    scheduler max automatic action is read_only.
4.  Ten existing module keys approved; Core always available;
    absent/unimplemented modules cannot be sold; clinical modules out of
    current scope.
5.  `lifecycle_state` authoritative alongside legacy
    `organizations.status`; legacy field transitional and retired only
    via controlled migration.
6.  Dedicated deployment is long-term target, not hackathon
    prerequisite. Contracts may be enterprise, government,
    donor/programme, annual/institutional or dedicated; not all monthly.
7.  One global human identity may have independent memberships in
    multiple organizations. Each organization controls invitations,
    approval, suspension, revocation and roles. No cross-org membership
    discovery. Global identity grants no data access. Explicit org
    switch and request-time reauthorization. Government/NGO network may
    be one tenant with branches and authorized cross-branch access;
    separate legal institutions remain separate tenants absent formal
    sharing. No clinical record sharing approved.
8.  Separate platform administration and operations roles; multiple
    roles for one person only by explicit audited policy.
9.  Do not map legacy `organizations.status='inactive'` automatically to
    closed/suspended. Preserve legacy status; only safe validated active
    backfill with review list.
10. Tenant audit shows named platform operator and role, minimal
    unnecessary PII.
11. Password reuse history deferred.
12. Operator-assisted reset: authenticated authorized admin may receive
    one-time short-lived reset code, hashed, single-use and audited;
    never reveal new password.
13. Support grants require explicit `org_admin` consent for every grant;
    no grace preapproval; scoped, time-limited, reasoned, audited and
    tenant-visible.
14. Ordinary suspension requires four-eyes approval; emergency path
    requires later review/audit.
15. MFA required before production platform launch. Temporary hackathon
    exception only with documented risk and restricted operator group;
    not equivalent to MFA.
16. Closure requires Platform Admin + second-person approval. Retain
    data by default; anonymize/delete only after legal approval.

Six SaaS specs live under `docs/architecture/saas/`: Hybrid SaaS
Architecture, Current State Audit, Identity & Access Management, Tenant
& Organization Management, Subscription & Entitlement Management, Hybrid
SaaS Implementation Roadmap. They are specifications, not proof of
implementation/acceptance.

Reconciliation: - `597d9b1` reconciled six SaaS docs. - `7c039fa`
corrected MFA launch requirement, A3 profile list and stale
reconciliation status. - EQ-4, EQ-5, EQ-7 remain open. - Architecture
§15.2 has an observed orphan table row; roadmap §9.3 still says
platform-scope audit unavailable pending ADR-SAAS-009 despite O-SaaS-2
resolution. Treat as separate documentation reconciliation. - Platform
Identity workstream E is only partial in known evidence.

## 6. Operational RBAC state

Owner decisions: 1. Assistant-to-doctor assignment = multiple doctors.
2. Patient update permission = separate `patient.create` and
`patient.update`. 3. Self-escalation prohibited. 4. Protect last active
Organization Admin. 5. Separate platform identity immediately.

Reported implementation: - `StaffDoctorAssignment` model/table and
legacy backfill. - `assigned_doctor_ids` in auth context. - Patient
permissions split; PATCH uses `patient.update`. - Role hierarchy and
`can_grant_role`. - Self-escalation protection and last-admin row
locking. - Platform audit model/table/helper and platform role
dictionary. - Assignment loader contract: table absent =\> `None` allows
legacy fallback; table present/no active rows =\> `[]`, no fallback;
query failure =\> fail closed.

Caveats: - Platform Workstream E is partial: no complete separate
platform users/auth/JWT/platform auth endpoints; no proven legacy
`super_admin` migration execution; production MFA not complete in known
evidence. - Earlier full backend runs had 10 duplicate-mobile failures;
reports inconsistently labelled O-1/O-2. Inspect exact tests/baseline
before attributing. - A last-admin concurrency test was described as
sequential in prior source review; verify whether corrected. - Latest
user report: backend suite was **not run** on pushed tree because
`AMSDP_DATABASE_URL` was unset and OS role absent; fallback would hit
developer DB. Do not claim backend suite green. -
`backend/queuing/tests/test_queue.py` has an autouse fixture that
deletes all `queue_entries`; run only against a dedicated throwaway DB.

## 7. Appointment/calendar Phase 2

Gap analysis:
`docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md`.
It identified 19 findings: F-07 Critical; six High; nine Medium; three
Low. F-07 was check-in bypassing `appointment.modify`, allowing
read-only doctor check-in and queue creation.

Commit `6b7ef4d27edbf820bfcafc25a9c789235337823d` implemented
F-01...F-19: - Frontend capacity/refusal helpers and localized
feedback. - Slot capacity/reason display and improved empty-day
message. - Fixture weekday correction. - Reported frontend tests 179
passed and Next build succeeded. - Full backend run: 12 failures/572
passed; two e2e fixture failures were corrected, then scoped backend
subset passed 269. Full suite was not clean.

Later `AMSDP-APPT-OWNER-DECISIONS-01` documentation records: - F-01
CLOSED using `slot_allocations` + `UNIQUE (appointment_id)`, claimed
under doctor row lock; historical keys approximated; overruns reported
but not repaired. - F-18 CLOSED using persisted `unscheduled` type
behind reasoned, capability-gated, audited override. - Capabilities
`appointment.check_in`, `appointment.create_unscheduled`,
`appointment.book_cross_branch`. - Closed `DELEGABLE_CAPABILITIES`;
`check_granted = matrix ∪ grants`. - Grant endpoints allow
`org_admin`/`super_admin`, not `branch_admin`. - Branch narrowing in
`AuthContext.has_capability`. - Test map and docs updated. Later pushed
commits `66e545e`, `3cacede`, `37cf3d1` include Q1--Q5 related
implementation/docs. O-1...O-7 were still noted open in the prior
report, including Business Rules vocabulary and historical slot-overrun
repair policy. Verify current repository before changing.

## 8. Phase 3 --- current main workstream

Read-only gap analysis:
`docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`
(about 1,622 lines).

Cline reported 49 findings, none Critical: - Queue Operations: 19 (3
High, 11 Medium, 5 Low). - DQDS: 14 (2 High, 8 Medium, 4 Low). -
QUE-006: 10 (5 High, 4 Medium, 1 Low). - Integration: 6 (2 High, 4
Medium).

No tests were run in that read-only task due the destructive queue
fixture. Browser verification absent for DQDS, queue page and QUE-006.
The gap-analysis index row was deliberately left unapplied. Latest docs
index report: Revision 35; 92 docs on disk = 89 registered + 2 O-3 + 1
unregistered queue gap analysis. O-3 and queue gap-analysis index
registration remain open.

### Major findings

**Queue:** `call` action has no frontend control; solo doctor lacks
required call capability; recall missing; duplicate check-in race needs
DB protection/concurrency tests; recovery/repositioning and
numbering/scope unresolved; queue page lacks auto-refresh in inspected
state.\
**DQDS:** Uses `date.today()` while platform uses facility timezone;
Bangladesh can show prior day's queue from midnight to about 06:00 Dhaka
time. Room absent from QueueEntry/public payload. Need scope decision on
essential branch-wide display vs advanced multi-display/ETA/upcoming
tokens. Preserve token-only privacy.\
**QUE-006:** No full event/config/audio implementation at Phase 3
baseline; an OD-1 manual browser-speech slice has since been committed.

### OD-1...OD-7 owner decisions

1.  OD-1 announcement mechanism.
2.  OD-2 configuration ownership/level.
3.  OD-3 wording and token speakability.
4.  OD-4 DQDS scope (catalogue vs Business Rules §33).
5.  OD-5 doctor/assistant queue capability.
6.  OD-6 recovery scope vs PQV §H.
7.  OD-7 token numbering.

ChatGPT proposed recommendations, but **do not treat the full set as
owner-approved**. User has not explicitly approved the consolidated
OD-1...OD-7 package in known context. Proposed directions only: - OD-1
browser speech primary, external TTS fallback if Bangla voice
unavailable/unusable. - OD-2 organization defaults + branch overrides. -
OD-3 Bangla/English templates; no patient identity; serial-only number
speech; room only when assigned. - OD-4 essential branch-wide DQDS now;
advanced displays/ETA/upcoming-token features later. - OD-5 doctors and
assigned assistants operate queues within explicit scope; doctor alone
starts/completes consultation. - OD-6 approve missed-turn
recovery/repositioning, superseding PQV §H. - OD-7 configurable
daily/continuous numbering, scope, prefix and width; suggested default
daily-per-doctor.

Confirm owner decisions before implementing the dependent scope.

## 9. QUE-006 OD-1 implementation and review

Commit `e67327e`
(`feat(queue): add browser speech synthesis for QUE-006`).

Added: - `frontend/lib/announcements/content.js` -
`frontend/lib/announcements/speech-synthesis.js` -
`frontend/lib/announcements/controller.js` -
`frontend/components/queue/QueueAnnouncements.js` - announcement tests
and implementation report
`docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md`

Modified `frontend/pages/queue.js`, `frontend/lib/i18n.js`.

Implemented: - Browser Web Speech API adapter. - Locale selection
(`bn-BD`, `en-GB`). - Strict language matching; no silent language
substitution. - No patient identity in speech. - Serial/token-based
content. - Operator activation and manual announce action for called
entries. - Audio failure isolation. - 49 announcement-focused tests in
commit report; pushed frontend suite later reported 229/229 passed.

Not implemented/not verified: - Automatic server-event-driven
announcement. - External TTS fallback. - Persisted
organization/branch/facility settings. - Server-side announcement
audit. - Room in queue response; current frontend `entry.room` is
undefined. - Real browser/device playback and target-device Bangla voice
availability. - End-to-end event ordering/idempotency/recovery. This is
only an initial client-side/manual slice, not QUE-006 completion.

### ChatGPT source-review findings (not independently runtime reproduced)

1.  **High:** English template omitted "please proceed to". Intended
    wording:
    `Token number [number], Dr. [doctor's name], please proceed to Room [room number].`
    Current implementation/test asserted shorter wording. Align code and
    test with owner-approved template.
2.  **High:** Adapter resolved `spoken` on both `onstart` and `onend`;
    successful completion should be reported only on `onend`, with
    started/completed/error/interrupted distinguished.
3.  **Medium:** Single `lastEventKey`/`lastEventAt` does not suppress A
    → B → replay A. Use bounded TTL set/map. Failed/blocked attempts
    must not be permanently marked as successfully announced.
4.  **Medium/integration:** Backend queue serialization lacks room. If
    added, derive from appointment's historical location snapshot, not
    current doctor schedule.

Retain: browser-native local playback, strict locale matching, no
patient/clinical PII, distinct queue call vs audible announcement, queue
actions independent of audio success, no browser verification claim
without device test.

### External TTS question

User asked whether external provider fallback is needed. Recommendation
was: plan optional fallback, not mandatory for every facility. User has
**not explicitly approved revised architecture/provider**.

Candidates researched from official docs: - Microsoft Azure Speech lists
Bangladesh Bangla `bn-BD` voices `NabanitaNeural` and `PradeepNeural`. -
Google Cloud Gemini-TTS lists `bn-BD` as GA. - No pronunciation/quality
comparison yet. These are candidates, not selected providers.

If approved, safeguards: - Credentials backend-only. - Send only minimum
announcement text (token, doctor name, room if needed); never patient
identity or clinical data. - Bounded timeout/retries; queue operations
never wait for TTS. - Facility can disable cloud fallback. - Avoid
duplicates/replay storms after failures. - Dedicated/institution
deployments may configure their provider. - Internet outage makes cloud
TTS unavailable; local recordings may be an offline path. - Test real
Bangladesh Bangla pronunciation with native listeners.

## 10. Bangla/English audio asset preparation

User asked whether to record Bangla clips or have Cline do it.
Recommendation: user/native Bangla speaker creates natural recordings;
Cline implements asset catalogue, loading, number composition, playback,
caching and tests. This is guidance, not confirmation that recordings
exist.

Suggested initial Bangla clips: 1. `টোকেন নম্বর` 2. `এক` 3. `দুই` 4. `তিন`
5. `চার` 6. `পাঁচ` 7. `ছয়` 8. `সাত` 9. `আট` 10. `নয়` 11. `দশ` 12. `রুম`
13. `এ আসুন` 14. Optional `ডা.`

Use one speaker, quiet environment, consistent mic distance, no music,
natural pacing. Keep original WAV/PCM masters. Earlier suggested
profile: mono, 16-bit PCM, 24 kHz or 44.1 kHz; confirm final
format/naming with Cline before bulk recording.

English candidates: `Token number`, `one`...`ten`, `Room`,
`please proceed to`, `Dr.`

**Number issue:** clips 1--10 are only a prototype. Token/room numbers
can exceed 10. Do not naïvely concatenate digit clips; Bangla compound
numbers can sound unnatural. Define and test natural number composition
for the required range before scaling recordings. No recordings are
confirmed created.

## 11. Recommended next steps

1.  Confirm OD-1 architecture: browser speech primary? Optional cloud
    TTS fallback? Should locally recorded clips be offline fallback?
    What happens if no suitable voice/assets exist?
2.  If approved, prepare a narrow OD-1 correction task for English
    wording, speech lifecycle semantics and bounded TTL deduplication.
    Do not mix in provider integration, backend events, room
    serialization or facility settings without authorization.
3.  Finalize announcement templates, token/room number range, number
    composition, audio format/loudness/naming, offline behavior and
    asset versioning before recording a full library.
4.  Resolve OD-2...OD-7 explicitly.
5.  Implement Phase 3 in controlled slices:
    -   Queue call/recall controls and authorized solo-doctor workflow.
    -   Duplicate-entry integrity, recovery and concurrency protection.
    -   Queue usability/refresh and approved numbering.
    -   DQDS timezone correction and approved room/location display.
    -   QUE-006 event/configuration/announcement engine.
    -   Integration, browser/device verification and acceptance.
6.  Run queue tests only against a dedicated throwaway DB.
7.  Register Phase 3 gap analysis and resolve O-3/index/reconciliation
    items only when authorized.
8.  Continue SaaS roadmap after inspecting current implementation and
    launch priorities.

## 12. Verification rules and latest evidence

For every slice record exact commands, environment, test results, build
result, browser/device and locale/voice playback, DB/migration
verification, docs reconciliation, commit/push and remaining blockers.

Latest user-reported pushed-tree evidence: - Frontend: 229/229 passed. -
Python compileall clean. - Secret scan clean. - Migration had two
parents; inspect migration graph before migration operations. - Backend
suite **not run** because `AMSDP_DATABASE_URL` unset and OS role absent;
fallback would hit developer DB. - Browser/device playback **not
verified**. - Status: committed, pushed and statically verified; not
fully verified and not accepted.

Never collapse scoped tests, frontend tests, build, full backend suite
and browser verification into one generic "tests passed" statement.

## 13. First files to inspect in a new conversation

Read current repository versions: 1.
`docs/governance/AMSDP_Docs_Index_V1.0.md` 2.
`docs/AMSDP_Business_Rules_V1.1.md` 3.
`docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`
4. `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md` 5.
`docs/implementation/AMSDP_QUE-006_OD-1_Browser_Speech_Synthesis_Implementation_Report_V1.0.md`
6.
`docs/implementation/AMSDP_Appointment_and_Calendar_Reliability_Remediation_Report_V1.0.md`
7.
`docs/audit/AMSDP_Appointment_and_Calendar_Reliability_Gap_Analysis_V1.0.md`
8.
`docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md`
9. Six docs under `docs/architecture/saas/` 10. `.clinerules` and
current repository agent instructions.

OD-1 source: - `frontend/lib/announcements/content.js` -
`frontend/lib/announcements/speech-synthesis.js` -
`frontend/lib/announcements/controller.js` -
`frontend/components/queue/QueueAnnouncements.js` -
`frontend/pages/queue.js` - Related announcement tests -
`backend/queuing/main.py` for queue serialization/event contract

## 14. Instructions for the next ChatGPT conversation

Use this handover as context, but verify facts against current
repository and newer user reports. Preserve settled decisions. Do not
assume proposed OD-1...OD-7 recommendations are approved. Continue from
Phase 3/QUE-006, especially OD-1 code-review findings and external TTS
decision. Ask only the single most important clarification when needed.
Do not produce a Cline prompt until explicitly asked. Keep work
incremental and explain why the next task is recommended.

**End of handover.**
