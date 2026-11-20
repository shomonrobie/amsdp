# AMSDP QUE-006 — Intelligent Queue Voice Announcements Catalogue Addition

**Document ID:** `AMSDP_QUE-006_Queue_Voice_Announcements_Catalogue_Addition_V1.0.md`
**Version:** V1.0
**Date:** 2026-11-17
**Task:** Add Missing Core Feature to AMSDP MVP Feature Catalogue (documentation only)
**Branch:** `hackathon-mvp`
**Commit:** `7c039fa` (HEAD, no commit made — documentation-only task, per restrictions)

---

## 1. Summary

Added **QUE-006 — Intelligent Queue Voice Announcements (Bangla/English)** as a distinct AMSDP Core capability to the MVP feature catalogue:

`docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md`

This is a documentation-only task. No application code, database/migration, API, frontend, voice provider, or architecture changes were made. No commit or push was performed. All pre-existing local changes and untracked files were preserved.

---

## 2. Starting and final branch/commit

| Item | Value |
|---|---|
| Starting branch | `hackathon-mvp` |
| Starting commit | `7c039fa` |
| Final branch | `hackathon-mvp` |
| Final commit | `7c039fa` (unchanged — no commit made) |

---

## 3. Files changed

| File | Change |
|---|---|
| `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` | Added QUE-006 feature entry (section C.5); updated sections B, D, E, F.4, G.3, H, H.2 |

Note: `docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` is an **untracked** file on disk (pre-existing local work, registered in the docs index as Revision 31). Edits were applied to the working-tree file; nothing was committed.

No other files were modified. `docs/governance/AMSDP_Docs_Index_V1.0.md` carries a pre-existing local modification (not made in this task) that was left untouched.


---

## 4. New feature ID and catalogue entry

**Feature ID:** `QUE-006 — Intelligent Queue Voice Announcements (Bangla/English)`

Placed in section **C.5 Module QUE — Queue management & token operations**, after QUE-005 and before section C.6 (PAT). One stable feature ID (`QUE-006`) used throughout sections B, C, D, E, F, G, H.

The entry includes all required fields:
1. **Description** — audible in-facility queue announcements in Bangla/English, triggered by queue events; facility-configurable enable/disable and language; not forced on every facility; explicitly not automated outbound telephone calls to patients.
2. **Expected user roles** — `super_admin`, `org_admin`, `branch_admin` (configure); `receptionist`, `doctor` (trigger via queue call); patients (passive audience).
3. **Expected behaviour** — announcement on call event; configurable language; configurable enable/disable; queue-event triggering; no duplicates/conflicts; failure does not interrupt queue ops; authorized configuration; no unnecessary patient PII; browser/runtime verification required before claiming implementation.
4. **Feature-specific acceptance criteria** — 10 checkable criteria (see §6).
5. **Dependencies** — QUE-001, QUE-004, RBAC.
6. **Source references** — `docs/chatgpt/AMSDP_Connect_Proposed_Communication_and_AI_Capabilities.md` §1; `backend/queuing/main.py`.
7. **Implementation status** — NOT STARTED.
8. **Verification status** — NOT TESTED.
9. **Known gaps and limitations** — no TTS provider, no announcement service, no configuration, not browser verified, not accepted.

---

## 5. Evidence supporting Core classification

The established Product Owner decision is preserved from `docs/chatgpt/AMSDP_Connect_Proposed_Communication_and_AI_Capabilities.md` §1 scope boundary (lines 28–32):

> "Intelligent Queue Announcements / Bangla-English Queue Voice Callouts is a separate AMSDP Core capability. It must be documented in the relevant Core queue and implementation documents, not treated as a proposed conversational-AI feature in this document."

This is reconciled against:
- **MVP Scope exclusions** ("Automated SMS, WhatsApp, email or voice reminders") — these cover outbound patient reminders, distinct from in-facility audible queue callouts (per task clarification).
- **Distinct capabilities:** QUE-004 (staff queue actions/calling a patient), NOT-001 (notification outbox), L10N-001 (UI localization), QUE-006 (audible Bangla/English queue voice announcements) — all separate with different acceptance criteria.


---

## 6. Acceptance criteria added (Section E.6 QUE module)

1. [ ] Bangla queue voice announcement produced for a call event when Bangla is configured.
2. [ ] English queue voice announcement produced for a call event when English is configured.
3. [ ] Announcement language configurable per facility.
4. [ ] Announcements can be enabled/disabled per facility (not forced on every facility).
5. [ ] Announcements triggered by appropriate queue events (e.g., patient called to consultation).
6. [ ] No duplicate or conflicting announcements for the same queue event.
7. [ ] Voice-output failure does not fail or interrupt the queue call operation.
8. [ ] Only authorized roles (org/branch admin) may configure announcements.
9. [ ] Spoken announcements contain no unnecessary patient PII (no patient name/mobile).
10. [ ] Actual audio output verified at browser/runtime before implementation is claimed.

No AI, external telephony, WhatsApp, or other communication features were added to this Core feature (not in approved documentation).

---

## 7. Implementation and verification status (with evidence)

| Field | Value | Evidence |
|---|---|---|
| Implementation status | NOT STARTED | Grep for `tts`, `espeak`, `gTTS`, `pyttsx`, `speech`, `audio`, `announcement`, `voice callout`, `browser playback` across the tree returned **zero** implementation evidence. No voice generation, Bangla speech output, English speech output, TTS provider, announcement service, or configuration storage exists. |
| Verification status | NOT TESTED | No test evidence for audio output or announcement behaviour exists. |
| Browser verified | No | Not claimed; no browser/runtime audio verification evidence. |
| Accepted | No | Product Owner acceptance not yet obtained (this task stops for PO review). |

Per catalogue convention (Section F.3): IMPLEMENTED does not mean TESTED; verification status is never claimed without supporting evidence cited in the feature entry. No implementation or verification is claimed for QUE-006.


---

## 8. Revised feature count and reconciled readiness metrics (Section H)

| Metric | Before | After | Basis |
|---|---|---|---|
| Total identified features | 25 | **26** | Sections C–D (ORG-001 through QUE-006) |
| Features awaiting PO scope decisions | 25 | **26** | All checkboxes in section D unchecked |
| Features implemented | 17 | 17 | QUE-006 is NOT STARTED |
| Features partially implemented | 8 | 8 | Unchanged |
| Features tested | 23 | 23 | QUE-006 is NOT TESTED |
| Features browser verified | 0 | 0 | Unchanged |
| Features accepted | 0 | 0 | Unchanged |
| Features blocked | 0 | 0 | Unchanged |

The existing 25 features remain intact; the resulting catalogue contains 26 features. No existing equivalent QUE-006 feature was found (no duplication).

---

## 9. Product Owner decision boxes

All KEEP / REMOVE / DEFER boxes in section D remain **unchecked**, including the new QUE-006 row:

`| QUE-006 | Intelligent Queue Voice Announcements (Bangla/English) | [ ] | [ ] | [ ] | |`

No Product Owner scope decision was made in this task (Section I decision history unchanged — no new decision recorded). The Core classification reflects the pre-existing established decision in the Connect capabilities document §1, not a new PO decision.

---

## 10. Governance and skill compliance

- Applicable governance documents (per `.clinerules` §4 routing table): backend API/service endpoints, database schema, audit/data integrity, multi-tenant data, documentation reading/writing. No installed skills available (Skills Registry: NONE); governance documents applied directly.
- `.clinerules` §3 non-negotiables respected: no secrets exposed; server-side access enforcement not altered; cross-tenant access unchanged; tenant key remains `organization_id`; audit trail untouched; no schema/migration changes; no unverified capability claims.
- `.clinerules` §9 execution boundaries: documentation-only, single file, no terminal test execution, no git destructive operations.
- `.clinerules` §11 documentation output: report written under `docs/implementation/`; filename follows `AMSDP_<Topic>_<Version>.md`; no existing document overwritten.
- `.clinerules` §12 documentation reading: index read; catalogue, Connect capabilities document, business rules, MVP scope, queue implementation report, owner decisions, and git state all consulted before editing.


---

## 11. Deviations, exceptions, unresolved issues

- QUE-006 is NOT STARTED / NOT TESTED. Implementation (TTS provider selection, announcement service, enable/disable + language configuration, browser playback) is future work requiring separate Product Owner decisions and engineering effort.
- The catalogue file is currently untracked in git; this task made no commit (per restrictions). Commit/push requires separate owner instruction.
- Section I decision history was not extended because no new Product Owner decision was made in this task.

---

## 12. Final Git status

```
Branch: hackathon-mvp
Commit: 7c039fa (HEAD -> hackathon-mvp, origin/hackathon-mvp)
Working tree:
  M docs/governance/AMSDP_Docs_Index_V1.0.md     (pre-existing local modification — not made in this task, left untouched)
 ?? docs/governance/AMSDP_RBAC_Discovery_and_Current_State_Audit_V1.0.md  (pre-existing untracked — left untouched)
 ?? docs/product/AMSDP_MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md  (edited in this task — untracked, not committed)
```

No commit or push was performed. All local changes and untracked files preserved. Stopping for Product Owner review.

QUE-006 is recorded as Core MVP (section D checklist + section H.2 supporting approvals) and is **not** listed in sections G.1/G.2 as excluded or future, preventing contradictory classification.
