# AMSDP — MP-08 Implementation Report: announcement-safe recall

**Status:** TESTED (not VERIFIED — no live browser and no live credential were available; see §5)
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`)
**Task source:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`, MP-08, as amended by Appendix E /
Amendment A-2. Behaviour decision taken by the Product Owner (register Q-5, option **(a)**).
**Register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §2 (row MP-08), §4 (Q-5 closed), §9
(resolution note).

---

## 1. Requirement

MP-08 acceptance criterion, quoted from the plan: *"Two calls for one entry produce two delivery rows with distinct
`qce:` keys; both audited; position unchanged."*

### 1.1 The conflict, and how it was resolved

The plan described a `called → called` transition driven by the existing `call` action. The shipped code refuses
that on purpose: `backend/queuing/tests/test_queue.py::test_duplicate_call_request_creates_no_second_event` asserts a
second `call` from `called` is **422**, and `backend/queuing/events.py` states the reason in its module docstring —
a retried or double-submitted HTTP request must not be able to produce a second audible announcement. That is what
"announcement-safe" means, so the plan's literal wording argued against the plan's own criterion.

The conflict was recorded before any code was written (register §9) with three options. The Product Owner chose
**option (a)**: an explicit, separate `recall` action. The duplicated-`call` 422 therefore survives untouched, and a
recall is an operator-chosen act with its own history record, its own `qce:` id, its own audit event and its own UI
control.

---

## 2. Change

No migration: `status_history` is already a JSON column and `action` was already stored in each record.

| File | Change |
|---|---|
| `backend/queuing/events.py` | Module docstring rewritten (recall is its own action; duplicate `call` still 422). `RECALL_ACTION = "recall"` and `CALL_ACTIONS = (CALL_ACTION, RECALL_ACTION)` added. `call_events()` now matches `action in CALL_ACTIONS` and publishes the record's `action` on each event, so a caller can distinguish a first call from a recall without parsing ids. The function stays tolerant (non-list history → `[]`) and the identity rule is unchanged: the *n*-th qualifying record is `qce:<entry>:<n-1>`. |
| `backend/queuing/main.py` | `_TRANSITIONS["called"] = ("recall", "start_consultation", "cancel", "mark_no_show")` — `call` is **not** in it. `_NEXT_STATUS["recall"] = "called"`. `QueueAction` comment lists `recall`. Permission gate is `elif data.action in ("call", "recall")`, so recall needs `queue.manage`, or a doctor whose organization enables `doctor_queue_calling_enabled` — the same answer as `call`, not a second capability. Audit is written as `action=f"queue.{data.action}"` (line 572), so a recall writes `queue.recall` and a first call still writes `queue.call`. |
| `backend/queuing/tests/test_queue.py` | New `class TestQueueRecall(_AnnouncementFixture)`, 9 tests (§3.1). |
| `backend/queuing/tests/test_queue_events.py` | `_recall()` pure-data helper + 3 tests on `call_events()`/`current_call_event()`/`is_current_call_event()` (§3.1). |
| `frontend/lib/queue/queue-call.js` | `RECALL_ACTION`, `RECALLABLE_STATUS = 'called'`, `isRecallable()`; `performCall()` gained an `action` parameter (default `CALL_ACTION`) and refuses an unknown action with `unsupported` before any request is made. Every result now carries `action`. |
| `frontend/lib/announcements/queue-transitions.js` | The tracker now also records the entry's `call_event_id`, because a recall never changes the status: a **new event id** is a new call. An entry with no published id behaves exactly as before; the first observation still only seeds the tracker. |
| `frontend/pages/queue.js` | `recallEntry(entry)` handler and a Recall control rendered only for `canCall && isRecallable(r)`. It shares the same single-flight gate as `call` and refetches only on success, so a failed recall never announces. |
| `frontend/lib/i18n.js` | Three keys in both languages: `recall`, `recalledNotice`, `recallFailed`. |
| `frontend/tests/queue-call-control.test.mjs` | Import of the new exports, the stale `elif data.action == "call":` contract pattern updated to the new gate, and 10 new tests (§3.1). |

Nothing was removed: the missed-turn → recover → `call` path still works and still yields the second `qce:` id that
`test_recall_gets_a_new_event_id` proves.

---

## 3. Tests

### 3.1 New tests

`backend/queuing/tests/test_queue.py::TestQueueRecall` (9):

1. `test_recall_from_called_appends_a_distinct_call_event` — 200, new `call_event_id`, later index, `call_count == 2`.
2. `test_two_calls_for_one_entry_produce_two_delivery_rows` — MP-08's criterion: two delivery rows, two distinct `qce:` keys.
3. `test_the_superseded_event_can_no_longer_be_claimed` — the first claim is now **409**.
4. `test_both_the_call_and_the_recall_are_audited` — the audit trail contains `queue.call` **and** `queue.recall`.
5. `test_position_and_token_are_unchanged_by_a_recall` — position, tracking token and `position_history` untouched.
6. `test_a_duplicate_call_is_still_refused_after_a_recall` — `call` from `called` is still **422** (the invariant).
7. `test_recall_is_refused_from_waiting` — **422** (the transition, not just the permission, enforces it).
8. `test_recall_requires_queue_manage` — doctor without the grant and without the policy: **403**.
9. `test_recall_follows_the_organizations_doctor_calling_policy` — doctor with `doctor_calling_enabled`: **200**, `call_count == 2`.

`backend/queuing/tests/test_queue_events.py` (3): a `call` + `recall` history counts two events in order with
`actions == ["call", "recall"]` and `call_count == 2`; a recall supersedes the earlier event id (old id no longer
current, new id current); a record whose `action` is `recall` but which did **not** end in `called` produces no event.

`frontend/tests/queue-call-control.test.mjs` (10 new): the action string and the `_TRANSITIONS`/`_NEXT_STATUS` server
contract (including an assertion that `"called"` does **not** gain `"call"`); `isRecallable` accepts only `called`; the
recall payload is `{action: 'recall', reason: ''}`; an ineligible recall sends nothing; an unknown action is refused
before a request exists; a recall shares the single-flight gate; the tracker announces a new event id on
`called → called` and still announces the ordinary status transition exactly once; the page wires the control to the
same gate and never speaks from the handler; the three captions are bilingual and distinct from the call captions.

### 3.2 Executed results

Commands, with `AMSDP_DATABASE_URL=postgresql+psycopg2://amsdp@127.0.0.1:55432/amsdp` and `AMSDP_ENV` unset:

| Suite | Command | Result |
|---|---|---|
| Backend, whole tree | `python -m pytest backend -q -p no:warnings` | **`808 passed in 756.71s`**, 0 failed. Baseline was 796 → 796 + 9 + 3 = 808; arithmetic closes, nothing skipped or deselected |
| Backend, queue | `python -m pytest backend/queuing/tests/test_queue.py -q` | **`93 passed`** (84 before + 9) |
| Backend, events | `python -m pytest backend/queuing/tests/test_queue_events.py -q` | **`16 passed`** (13 before + 3) |
| Frontend, whole suite | `npm test` in `frontend/` | **373 tests / 369 pass / 2 fail / 2 skipped**; the 2 failures are the pre-existing `banglanamesense-dataset` and `calendar-render` (register Q-3), unchanged by this work |
| Frontend, queue trio | `node --test tests/queue-call-control.test.mjs tests/queue-refresh-safety.test.mjs tests/queue-announcement-w2-integration.test.mjs` | **`55 passed, 0 failed`** |

### 3.3 Mutation check — the tests are not vacuous

`"recall"` was removed from `_TRANSITIONS["called"]` in `backend/queuing/main.py`, then the new tests were re-run:

```
FAILED backend/queuing/tests/test_queue.py::TestQueueRecall::test_recall_from_called_appends_a_distinct_call_event
FAILED …::test_two_calls_for_one_entry_produce_two_delivery_rows
FAILED …::test_the_superseded_event_can_no_longer_be_claimed
FAILED …::test_both_the_call_and_the_recall_are_audited
FAILED …::test_a_duplicate_call_is_still_refused_after_a_recall
FAILED …::test_recall_follows_the_organizations_doctor_calling_policy
6 failed, 4 passed, 83 deselected in 2.52s
```

The four that still passed are the *refusal* tests (recall from `waiting` → 422, `queue.manage` → 403, and the
position/token tests), which is the correct behaviour for a mutation that removes the capability rather than the guard.

`main.py` was then restored from a byte copy. SHA-256 before mutation and after restoration are identical:
`1315700B25B33AF64D95A4D7E5501BD3B9B39D7BA5F17D814F1B48D06240736D`. The recall tests were re-run after
restoration: **`10 passed`**.


---

## 4. Verification evidence

- **IMPLEMENTED** — code exists and is reachable in the routes and pages described in §2.
- **TESTED** — the named tests in §3.2 pass in this tree, and §3.3 shows they fail when the capability is removed.
- **VERIFIED** — *not claimed.* No second, independent artefact exists: no browser was driven, no live deployment was
  called, and the frontend tests are source-contract regexes over page source, not a rendered DOM (§5).
- **ACCEPTED** — not claimed. The Product Owner decided the *behaviour* (option (a)), which is not the same as
  accepting the implementation.

The still-unconfirmed carry-over checks from the previous window were re-run and are now confirmed in this session:

| Check | Result |
|---|---|
| `date.today(` absent from `backend/queuing/display.py` | **absent** (no match) |
| `display.py` unchanged since MP-06 | SHA-256 `3F9FD04789B5D1F4F9C9755D04665F44C66DE334E0720A34E7F17DA819595E73`, **equal** to `runs/display.py.orig` |
| `dashboard.js` unchanged since MP-07 | SHA-256 `EF40892FC7216741270CD8D5778C861E3A0CB1E54DAC26816AF46C2F8D688B0D`, **equal** to `runs/dashboard.js.orig` |
| `git status --porcelain` | only intended files plus the pre-existing owner edits (business-rules documents, `.clinerules`) and the multi-display documents from PO-13; nothing staged, reverted or cleaned |

---

## 5. Known limitations and remaining gaps

1. **No live observation.** The recall has never been executed against a deployed environment; it is proven against
   the scratch database and the ASGI test client only. This is the same limitation as MP-06/MP-07 and keeps the work
   at TESTED.
2. **Frontend evidence is source-contract.** The Recall button, the gate reuse and the bilingual captions are asserted
   by regular expressions over `frontend/pages/queue.js` and `frontend/lib/**`, not by a rendered page. The repository
   ships no DOM renderer. A green frontend suite is weaker than a green backend suite and is never labelled VERIFIED.
3. **The tracker relies on the server's 409 for stale events.** `trackCalledTransitions()` treats a *different*
   `call_event_id` as a new call. If an older queue payload arrived after a newer one (out-of-order responses), the
   older id would look like a new event; the delivery claim refuses it with 409 because it is no longer the current
   event, so nothing is spoken twice. The protection is server-side by design; a monotone client-side ordering was not
   added because it would duplicate a rule the server already owns.
4. **`recall` is not offered for `skipped`.** An entry that was skipped is re-called through
   `skipped → reinsert → call`, which is a distinct, audited path. If the product wants a one-step recall from
   `skipped` as well, that is another `_TRANSITIONS` entry plus one test, and a separate decision.
5. **The plan wording is not amended.** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` still
   describes the transition as `called → called` via `call`. It is the owner's document; the deviation is recorded
   here and in register §9 rather than edited by an agent.
6. **Q-3 remains open.** The two pre-existing frontend reds (`banglanamesense-dataset`, `calendar-render`) are
   untouched and still untriaged.

---

## 6. Governance and Skill Compliance

**Documents read for this task (per `.clinerules` §2 step 3 and §12):**
`docs/governance/AMSDP_Docs_Index_V1.0.md` (navigation), `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md`
(§2, §4, §5, §9), `docs/product/AMSDP_Business_Rules_V1.0.md` (queue rules, read-only, cited not modified),
`docs/implementation/AMSDP_MP-05_…_V1.0.md` and `AMSDP_MP-06_/MP-07_…_V1.0.md` (report conventions and evidence
vocabulary). Domain routing applied: **Backend API / service endpoints** and **Queue / scheduling / workflow
transitions**, plus **Frontend UI** for the control — none of these rows has an installed skill.

**Skills:** none installed in this workspace (§5 of `.clinerules`; verified again — no `.clinerules/skills/`,
`.claude/skills/`, no repo `skills/`). **No skill was used, and none is claimed.** The governance documents above were
the applied material.

**Non-negotiables checked:**
- *Server-side authorisation, never the UI:* the Recall control is a mirror; the real gate is the `queue.manage` /
  organisation-policy check in `main.py`, proven by the 403 test. A hidden or absent button grants nothing.
- *Cross-tenant / cross-branch fails closed at 404:* `_scoped_entry_or_404` and `can_access_doctor` are unchanged and
  still run before the transition check.
- *Denials audited, not swallowed:* the refusal paths raise before the audit write, exactly as for `call`; the
  successful recall writes `queue.recall`.
- *Append-only audit:* no audit row is updated or deleted; the recall adds a row.
- *No secret in any artefact:* nothing from `docs/demo/AMSDP_Demo_Credentials_V1.0.md` was read into this report, and
  the scratch database URL contains no password.
- *Forward-only schema change:* none was needed — `status_history` is JSON, not a column per action.
- *Honest evidence:* §4 states plainly what is not VERIFIED and §5 lists every gap.

**Execution boundaries (§9):** the only commands run were test suites, hash reads, `git status` and the intended
mutation (reverted byte-identically, hash recorded). No server was started, no database was re-seeded, no destructive
git command was used.

**Deviations:** the plan's literal `call`-driven `called → called` transition was deliberately not implemented, on the
Product Owner's decision (register Q-5 → option (a)). Recorded here, in register §4 and §9, and not silently.

**Report location (§11):** written to `docs/implementation/`, matching the other `AMSDP_MP-*` implementation reports.
No document was moved or renamed, so no migration-manifest entry was required.

