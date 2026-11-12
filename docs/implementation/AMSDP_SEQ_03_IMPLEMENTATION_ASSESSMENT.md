# AMSDP — Sequence 3 Implementation Assessment

**Sequence ID:** `AMSDP-SEQ-03-QUEUE-RECOVERY-NOTIFICATIONS-2026-11-09`
**Work package:** `AMSDP-SEQ-03-WP1-QUEUE-RECOVERY-NOTIFICATION-AUDIT-2026-11-09`
**Date:** 9 November 2026
**Status:** audit complete — implementation proceeds only from this baseline.

> This document records what actually exists in the tree at the start of
> Sequence 3. Nothing here is derived from planning documents: every row was
> verified by reading the source, the alembic chain, the live development
> database (`127.0.0.1:5433`, head `a1f2b3c4d5e6`), or the test suite.

---

## 1. Governing references actually used

| Reference | Path | Use in this sequence |
|---|---|---|
| Business Rules V1.1 (authoritative) | `docs/AMSDP_Business_Rules_V1.1.md` | §27A missed-turn recovery (APPROVED FOR MVP, 2026-11-09), §8 permissions, §18 statuses, §20–§21 no-show/late arrival, §27–§28 queue management/priority, §35–§36 communication, §40 audit |
| MVP Scope V1.1 | `docs/AMSDP_MVP_SCOPE_V1.1.md` | missed-turn recovery acceptance, notification scope addendum |
| Master Feature List V2.2 | `docs/AMSDP_Master_Feature_List_V2.2_Consolidated_Draft.md` | §25.7 / §25.8 approval record, N1/N2 definitions |
| PQV product decision V1.0 | `docs/product/AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md` | §D two-stage notifications, §K acceptance criteria, provider-dependency boundary |
| M9 readiness assessment | `docs/product/AMSDP_M9_Implementation_Readiness_Assessment.md` | §14 outbox design, §16 PQT implementation, §18 DQDS implementation |
| Sequence 2 completion report | `docs/implementation/AMSDP_SEQ_02_COMPLETION_REPORT.md` | prior state, DQDS endpoint contract, deferral of M9-D/E |
| `.clinerules`, `agent-rules/` | repository root, `ai_factory/docs/agent-rules/` | governance precedence, non-negotiables, evidence standard |

**Document conflict resolved:** `AMSDP_PQV_Patient_Queue_Visibility_Decision_V1.0.md`
row 3 still reads *"Missed-Turn Recovery — NOT APPROVED FOR MVP"*. That decision is
superseded by the later, dated Business Rules **V1.1 §27A** and MVP Scope V1.1
amendment ("APPROVED FOR MVP, 9 November 2026"). No silent override is made: V1.1
is the newer authoritative text and is applied here; the V1.0 record is left
untouched as the historical record (V1.1 §27A "Version control" clause).

---

## 2. Audit method

1. Read every backend service module that owns a lifecycle touched by this
   sequence (`appointment/main.py`, `queuing/main.py`, `queuing/display.py`,
   `organization/main.py`, `common/*`).
2. Confirmed the database shape from the live development database, not from
   models alone: `alembic current` → `a1f2b3c4d5e6 (head)`; tables
   `alembic_version, appointments, audit_events, branches, doctor_branches,
   doctors, organizations, patients, queue_entries, queue_sequences, schedules,
   staff_users, tracking_tokens`.
3. Confirmed the alembic chain is single-headed:
   `5f3fce6757cf → ccf34da72c1b → c7d3601e2486 → 9d8a1f2b3c4d → 3c8e5d0a9b2f → a1f2b3c4d5e6`.
4. Grepped the whole backend for `notification`, `outbox`, `reminder`, `channel`,
   `sms`, `whatsapp` — **zero** matches in `backend/**/*.py`. No notification
   code exists.
5. Read the frontend shell, shared UI components, i18n dictionary and the queue
   page to establish component and i18n conventions.
6. Read the test suites to establish fixture, token and cleanup conventions.

---


## 3. Requirement classification

Legend: **IMPLEMENTED-VERIFIED** = code exists and prior evidence confirms it;
**PARTIAL** = some mechanism exists but the required behaviour does not;
**MISSING** = nothing exists; **BLOCKED** = external dependency;
**DEFERRED** = outside this sequence's authorization.

### 3.1 Missed-turn recovery (WP2/WP3)

| Requirement | State | Evidence in tree |
|---|---|---|
| `skipped` queue status semantics | PARTIAL | `queuing/main.py:34` `ACTIVE_STATUSES` includes `skipped`; `display.py:83–86` counts skipped as waiting but never as serving; `appointment/tracking.py:171` treats it as active. **No transition into `skipped` exists** — `_TRANSITIONS` (`main.py:246–254`) allows only *out of* `skipped` (`call`, `reinsert`, `start_consultation`, `cancel`). The status is currently unreachable through any API. |
| Staff-confirmed missed-turn action | MISSING | No action/endpoint writes `skipped`. |
| End-of-queue deferral default | MISSING | `queue/reorder` (`main.py:325–359`) can move entries but is a bulk arbitrary reorder with no missed-turn semantics, no default, no status change, and no `SELECT … FOR UPDATE` (not concurrency-guarded). |
| Position override with mandatory reason | PARTIAL | `reorder` accepts an optional reason for any entry; no override validation, no reason requirement. |
| Appointment/token preservation during recovery | N/A (must be enforced) | Nothing currently writes appointments from the queue service except `complete_consultation` → `COMPLETED` and `start_consultation` → token revoke. Any recovery implementation must not touch those paths. |
| No automatic `NO_SHOW` | IMPLEMENTED-VERIFIED | Only `queue_action(action="mark_no_show")` sets `no_show`, gated behind `queue.manage` + explicit staff call (`main.py:263–271`). No timer, cron or inference exists anywhere. |
| Audit of queue movement | PARTIAL | `record_audit(...)` is used for `queue.checkin`, `queue.enqueue`, `queue.<action>`, `queue.reorder` — correct helper, correct table, atomic with the change. No missed-turn/recovery action types exist. |
| Concurrency safety | PARTIAL | `queue_sequences` gives atomic token/position allocation on check-in/enqueue (`main.py:54–66`); `reorder` and status actions use no row locks or optimistic versioning. |
| Permission for recovery | MISSING | `queue.manage` / `queue.reorder` / `queue.consult` exist (`common/permissions.py`); no `queue.recover` / `queue.reposition`. Doctors hold only `queue.view` + `queue.consult`, so today a doctor cannot move a queue entry at all. |
| Staff UI to mark unavailable / recover | MISSING | `frontend/pages/queue.js` renders ↑/↓ reorder, start/complete, cancel. No skip, no recovery, no skipped-row action. |
| Priority/emergency entries | NOT MODELLED | `queue_entries` has **no priority column** (BR §28 is unimplemented in the schema). Nothing can be displaced by an append-at-end operation; documented as a limitation, not silently assumed. |

### 3.2 Notification infrastructure (WP4/WP5/WP6)

| Requirement | State | Evidence |
|---|---|---|
| Notification model / table | MISSING | Not in `common/models.py`; not in the live database. |
| Outbox, worker, scheduler | MISSING | Nothing in `backend/**/*.py` (grep for `outbox`, `notification`, `reminder`). No cron, no background task, no scheduler dependency. |
| Provider adapters (WhatsApp/SMS) | MISSING | No adapter, no client library in any `requirements.txt`, no credentials configured. |
| Organization-level configuration pattern | IMPLEMENTED-VERIFIED (pattern) | `organizations.config` JSON + `common/config.py` (`get_queue_config`, `reserved_for_capacity`) is the established pattern: typed accessors with safe defaults, "default-disabled → behaviour identical to prior releases". `branches.config` exists too. |
| Org-admin settings UI | PARTIAL | `frontend/pages/orgs.js` is a minimal legacy page (create/list only, no shared components); `AppShell` nav has no settings entry. No channel configuration surface exists. |
| Permission for org settings | IMPLEMENTED-VERIFIED | `org.manage` (org_admin, super_admin) + `require_org_access()`; `branch_admin` deliberately lacks it. |
| Secrets handling | IMPLEMENTED-VERIFIED (pattern) | `common/log_redaction.py` + `AMSDP_TRACKING_PEPPER` model: secrets live in env only and are never returned in responses. |
| Two-stage events N1/N2 | MISSING | No hook in `appointment/main.py`. |
| Reminder cancellation on lifecycle changes | PARTIAL | The **pattern** exists: `common/tracking_tokens.py::revoke_for_appointment` is called transactionally from appointment status change, reschedule, transfer and queue consultation start. Reminders reuse this exact hook placement. |
| Non-blocking guarantee | MISSING | Nothing to be non-blocking yet; booking currently commits and returns with no side-channel work. |

### 3.3 Regression surface (must not break)

| Surface | State | Where |
|---|---|---|
| Appointment lifecycle + capacity | IMPLEMENTED-VERIFIED | `appointment/main.py` (`VALID_TRANSITIONS`, capacity check, reschedule, transfer) |
| Queue ordering, check-in, tokens | IMPLEMENTED-VERIFIED | `queuing/main.py`, `queue_sequences` |
| PQT tracking tokens | IMPLEMENTED-VERIFIED | `appointment/tracking.py`, `common/tracking_tokens.py` |
| DQDS public board | IMPLEMENTED-VERIFIED | `queuing/display.py`, `frontend/pages/queue-display/[org]/[branch].js` |
| Dashboard aggregates | IMPLEMENTED-VERIFIED | `appointment/dashboard.py`, `tests/test_dashboard.py` |
| Frontend build | VERIFIED (Sequence 2) | `next build` EXIT=0, 9/9 static pages |

### 3.4 External dependencies

| Dependency | Classification | Consequence |
|---|---|---|
| WhatsApp provider selection, account, sender ID, approved template, credits | **BLOCKED (product-owner approval)** | Provider-neutral boundary + mock adapter only. No real provider is selected, registered or paid for. |
| SMS provider / sender ID / credits | **BLOCKED (product-owner approval)** | Same as above. |
| Provider credentials | **BLOCKED (not provisioned)** | Config reports existence via env only; credentials are never stored in the DB, logged, or returned. |
| Durable distributed rate limiter (M9-F) | DEFERRED (prior sequence) | Unchanged; not re-opened here. |
| Real delivery confirmation | **BLOCKED (provider-dependent)** | States `sent` and `delivered` are modelled separately; only a provider ack may set `delivered`. The mock adapter never sets it. |
| Background worker supervision | PARTIAL (deployment decision) | Standalone worker process implemented and documented; running it under process supervision is a deployment act, out of scope. |


## 4. Reuse decisions (nothing rewritten)

| Need | Reused artefact | Decision |
|---|---|---|
| Audit | `common/audit.py::record_audit` | Reuse for `queue.missed_turn`, `queue.recover`, `queue.reposition`, `org.notification_config_updated`. No parallel audit system. |
| Tenant/branch isolation | `require_permission`, `AuthContext`, org-scoped queries | Reuse exactly. Cross-org/branch access → 404 (non-disclosing) per `.clinerules` §3. |
| Queue ordering | `queue_entries.position` + `position_history` | Reuse; recovery appends/inserts and renumbers, never changes token/date/doctor/branch. |
| Org config | `organizations.config` JSON + typed accessor module | Reuse pattern: new `common/notifications/config.py` with defaults (channels disabled). **No new settings table.** |
| Lifecycle hooks | `tracking_tokens.revoke_for_appointment` placement | Mirror the placement for reminder cancellation so the hook set stays consistent. |
| Token allocation | `_next_sequence` | Untouched — recovery never allocates tokens. |
| UI | `AppShell`, `Modal`, `ConfirmDialog`, `DataTable`, `StatusBadge`, `Alert`, `lib/i18n` | Reuse; add keys to both dictionaries. |
| Tests | `tests/test_dqds.py` / `tests/test_security.py` fixtures | Reuse scoped-seed + JWT-token conventions; delete only this sequence's own rows. |

---

## 5. Planned deltas (and why each is the minimum)

| Delta | Rationale |
|---|---|
| `backend/queuing/recovery.py` (new APIRouter, mounted in `queuing/main.py` like `display.py`) | Missed-turn confirmation + recovery belong to the queue service; a separate router keeps the existing `PATCH /queue/{id}` transition table and its gates untouched. |
| `common/permissions.py`: add `queue.recover`, `queue.reposition`; granted explicitly to receptionist and doctor, and to admin roles through the existing `queue.*` wildcard | BR §27A.1 requires "authorized staff member or doctor"; §27A.4 requires an explicit permission for confirmation **and** for queue repositioning, enforced server-side. Two narrow named permissions avoid granting doctors the broad `queue.reorder` / `queue.manage` (cancel, no-show) powers. **Flagged for product-owner confirmation in Sequence 4** because BR §8's matrix is marked FINALIZED; the change is additive and widens no existing permission. |
| New table `notifications` + one forward-only, idempotent migration | Persistent outbox rows are required for dedup, cooldown, retry and cancellation. `down_revision = a1f2b3c4d5e6` (current single head). |
| `common/notifications/*` package | Outbox logic, config accessor, provider boundary, best-effort hooks, standalone worker. |
| `backend/organization/notification_config.py` (new APIRouter) | Org-admin configuration lives with the org service (owner of `organizations.config`). |
| Best-effort hook call sites in `appointment/main.py` and `queuing/main.py` | N1/N2 creation and reminder cancellation, always after the business transaction commits and always exception-swallowing, so messaging can never block booking, queue updates, consultation lifecycle or recovery. |
| `frontend/pages/queue.js` recovery workflow, `frontend/pages/notifications.js`, `lib/i18n.js`, `lib/auth.js`, `AppShell.js` | WP3 and WP6 surfaces using existing components and permission gating (defence in depth only — the server remains the boundary). |

---

## 6. Explicit non-goals confirmed from the authorization

- No patient accounts, self-booking, portal, or patient-facing recovery.
- No clinical triage, urgency scoring, or automatic priority grant.
- No billing, payment, subscription, or provider-credit work.
- No provider selection, registration, credentials, or paid subscriptions.
- No change to approved Business Rules or product scope documents.
- No AILI changes, no commit/push/merge/deploy, no Sequence 4 work,
  no system-wide acceptance claim.

---

## 7. Blockers carried forward

1. **Provider integration** — real WhatsApp/SMS delivery cannot be implemented or
   claimed without product-owner approval of provider, account, sender ID,
   template, credentials and cost. Only the provider-neutral boundary and the
   mock adapter are in scope.
2. **Worker supervision** — the worker process is implemented; running it as a
   supervised service is a deployment act (M9-F / Sequence 4 territory).
3. **Priority queue entries** — BR §28 remains unimplemented in the schema; the
   recovery action appends/inserts without displacing any existing position, so
   nothing priority-related can be broken, but "preserve priority rules" cannot
   be evidenced against a model that does not exist.
4. **RBAC matrix addition** — `queue.recover` / `queue.reposition` are new named
   permissions; product-owner confirmation is requested at Sequence 4 acceptance.

---

## 8. Verdict

Missed-Turn Recovery is **not implemented** (the `skipped` status exists but is
unreachable), and notification infrastructure is **entirely absent**. Both are
implementable inside the existing architecture with one new table, one new
migration, three new backend routers/modules, and additive UI. No working
functionality needs to be rewritten, and no prerequisite is missing.

---

