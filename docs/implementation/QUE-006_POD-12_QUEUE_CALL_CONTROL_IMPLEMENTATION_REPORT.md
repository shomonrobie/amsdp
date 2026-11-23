# AMSDP — QUE-006 POD-12: Queue Call Control and Automatic Announcement Trigger

> **Task ID:** `AMSDP-QUE-006-POD-12-QOP-001`
> **Date:** 2026-11-21
> **Owner decision implemented:** **POD-12 — APPROVED** (queue Call control; no new permissions)
> **Workstream:** QUE-006 W2 (queue announcement integration), server half of the trigger chain
> **Status:** **IMPLEMENTED** · **UNIT-TESTED** · **BUILD-VERIFIED** · **BACKEND NOT VERIFIED** ·
> **BROWSER NOT VERIFIED** · **W2 still PARTIALLY IMPLEMENTED** (see §12, §14)
> **HEAD:** `37cf3d1` — nothing staged, committed, pushed or deployed

---

## 1. Decision reference and scope

POD-12 approves a queue **Call** control so that an authorised operator can move a waiting entry to
`called` from the queue page, and that transition then feeds the existing W2 announcement seam.

The decision's constraints, and how each is honoured:

| POD-12 constraint | Where honoured |
|---|---|
| Receptionists call with their existing `queue.manage` | §4, §6 — the control is gated on `can('queue.manage')`; `receptionist` holds it in both matrices |
| Doctors call **only** where their existing permissions grant `queue.manage` | §6, §11 **DEV-1** — the doctor role does not hold it, so the control is not offered; no grant was invented |
| No new permissions, no weakened backend authorisation | §6 — `backend/common/permissions.py` is **unmodified** (`git status`); the route still calls `require_permission("queue.manage")` |
| `branch_admin` gains nothing through this task | §6 — it already held `queue.manage` via its pre-existing `queue.*` wildcard at HEAD; nothing was added |
| Voice/language configuration permission unchanged | Untouched — W3 is out of scope; no configuration surface was read or written |
| Queue operation independent of audio | §10 — the handler never references the announcer; the announcement is produced by the refetch's transition effect |

Everything in POD-12 §5 ("explicitly out of scope") was left alone: no W3/W4/W5/W6 work, no new audit
event (POD-4), no server event identity or cross-client dedupe (POD-8), no polling/WebSocket, no audio
asset, manifest, recording or wording change, **no schema migration and no permission grant**.

---

## 2. Preliminary inspection — what was actually verified in this session

The repository was checked against the recovered W1/W2 reports rather than trusted. Line numbers are
from the files as found today.

| Artefact | Verified fact |
|---|---|
| `backend/queuing/main.py:379-393` | `_TRANSITIONS["waiting"]` already contains `"call"`; `_NEXT_STATUS["call"] = "called"`. `skipped → called` is also permitted. |
| `backend/queuing/main.py:395-404` | `PATCH /api/v1/queue/{entry_id}` handles `call` under `require_permission("queue.manage")`; consultation actions use `queue.consult`; unknown actions 422. |
| `backend/queuing/main.py:406-462` | Scope check (`_scoped_entry_or_404`), doctor/assistant assignment check, transition validation, status history, `record_audit(... action=f"queue.{data.action}" ...)` → `queue.call`, commit, then notification hooks. The response is the updated entry. |
| `backend/common/permissions.py:82-103` | `receptionist` holds `queue.view, queue.reorder, queue.checkin, queue.manage, queue.recover, queue.reposition`. |
| `backend/common/permissions.py:104-122` | `doctor` holds `queue.view, queue.consult, queue.recover, queue.reposition` — **no `queue.manage`**; a comment states this is deliberate. |
| `backend/common/permissions.py` `DELEGABLE_CAPABILITIES` | Three appointment capabilities only. `queue.manage` cannot be granted, so no doctor can acquire it through the product. |
| `backend/identity/routes.py:390-393` | `grant_capability` refuses anything outside `DELEGABLE_CAPABILITIES`. |
| `backend/common/auth.py` `require_permission` | Raises **403**; consults `check_granted(resource, role, grants)` (role matrix ∪ explicit grants). |
| `frontend/pages/queue.js:47-56` | `canManage = can('queue.manage')`, `canConsult = can('queue.consult')`, `canAnnounce = canManage \|\| canConsult`, one `useQueueAnnouncements()` per page. |
| `frontend/pages/queue.js:72-94` (pre-edit) | `announceOnCall(entry)` existed and fired `{queueEntryId, action: 'call', token, room}` with `{source: 'event'}`; its comment stated that **no UI control** issued a `call`. |
| `frontend/pages/queue.js:113-122` | The tracker effect: `trackCalledTransitions(calledTracker.current, entries)` then `transitioned.forEach(announceOnCall)`; never awaited. |
| `frontend/lib/announcements/queue-transitions.js` | Seeds on first observation (so a load announces nothing), only reports a genuine transition, drops disappeared entries. |
| `frontend/pages/queue.js:124-129` (pre-edit) | `doAction` sends `PATCH /api/v1/queue/{id}` — **no single-flight guard** existed (`if (busy) return` is only on missed-turn/recover). |
| `frontend/lib/auth.js:17-45` | Frontend role mirror: `receptionist` has `queue.manage`; `doctor` does not; `branch_admin`/`org_admin` have `queue.*`. `can()` reads the **bare** `sessionStorage` global. |
| `frontend/tests/queue-announcements-boundary.test.mjs` | Enforces that every `t('key')` used by the page/panel exists in both dictionaries — so any new caption must be bilingual. |
| Repository state | HEAD `37cf3d1`; 9 modified / 26 untracked entries pre-existing; nothing staged. `frontend/node_modules` **absent**; no `pytest`, no venv, no Docker. |

Two pre-existing facts worth recording, both unchanged by this task: the dictionary already carried an
**orphan** `callNext` key (used by no page — the vocabulary for calling existed, the control did not),
and `backend/main.py` does not exist; the queue service is `backend/queuing/main.py`.

---

## 3. Files changed

| File | Change |
|---|---|
| `frontend/lib/queue/queue-call.js` | **New** (4,043 B raw / 3,944 B LF). `CALL_ACTION`, `isCallable()`, `createCallGate()`, `performCall()` — the authorisation, eligibility and single-flight decisions, with no dependency on React or audio. |
| `frontend/pages/queue.js` | Import + `calling` state + `callGate` ref + `callEntry()` handler + the Call button; the stale comment above `announceOnCall` corrected (it claimed no control exists). The seam body itself is **unchanged**. |
| `frontend/lib/i18n.js` | Three bilingual captions: `call`, `calledNotice`, `callFailed` (bn + en). No announcement wording touched. |
| `frontend/tests/queue-call-control.test.mjs` | **New** (14,992 B raw / 14,669 B LF, 18 tests) — the rules, the wiring and the two matrices. |
| `backend/queuing/tests/test_queue.py` | **Two tests added** (`test_receptionist_can_call_a_waiting_entry`, `test_doctor_cannot_call_without_queue_manage`). **Written, not executed** — see §7. |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Revision 47 and one `implementation/` row (this document). |

No other file was touched. `backend/common/permissions.py`, `backend/queuing/main.py`, the manifest,
every audio asset and every other announcement module are byte-identical to HEAD.

---

## 4. UI behaviour

The Call button lives in the existing actions cell of the existing `DataTable`, between the reorder
arrows and the consultation actions:

```jsx
{canManage && isCallable(r) && (
  <button className="btn btn-sm" disabled={!!busy || !!calling}
    onClick={() => callEntry(r)}>
    {calling === r.id ? t('pleaseWait') : t('call')}
  </button>
)}
```

Behaviour, requirement by requirement (POD-12 §4A):

- **Shown only for `waiting`** — `isCallable()` is the single eligibility rule (string id + status
  `waiting`). `called`, `in_consultation`, `completed`, `cancelled`, `no_show` and `skipped` are all
  false. The server also permits `skipped → called`; the interface deliberately does not surface it,
  because a skipped entry is *recovered* (BR §27A), not called — recorded as **DEV-2**.
- **Shown only when authorised** — `canManage` (`queue.manage`), the same decision the server enforces.
- **Same endpoint, same action** — `PATCH /api/v1/queue/{id}` with `{action: "call", reason: ""}`. No
  second route, no second transition: `performCall()` owns the payload, so the contract is testable
  (`assert.deepEqual(log, [{ id: 'qe-1', payload: { action: 'call', reason: '' } }])`).
- **No accidental repeats** — `callGate` is a **ref-held synchronous** single-flight guard, checked
  before any state change and again inside `performCall()`. React state is asynchronous, so a
  state-only guard could admit a second click in the same tick; this one cannot. Both buttons are also
  visually disabled while `busy` or `calling` is set, and the pending row reads "Please wait…".
- **Refresh through the existing pattern** — the success path calls the page's existing `loadQueue()`.
  No polling interval and no new transport were introduced (POD-12 §4D).
- **Honest feedback** — success sets a bilingual notice (`calledNotice`); any non-2xx sets an error
  (`callFailed: <server detail>`). A failure never renders a success notice, and never refreshes the
  list, so it cannot fabricate a `called` row.

`callEntry()` in full:

```js
const callEntry = async (entry) => {
  if (!canManage || !isCallable(entry)) return;   // UI mirror; the server decides
  if (callGate.current.current()) return;         // one call at a time
  setCalling(entry.id); setError(''); setNotice('');
  const result = await performCall({
    entry,
    authorised: canManage,
    gate: callGate.current,
    request: (id, payload) => apiFetch('/api/v1/queue/' + id,
      { method: 'PATCH', body: JSON.stringify(payload) }),
  });
  setCalling('');
  if (result.status === 'called') {
    setNotice(t('calledNotice'));
    loadQueue();
  } else if (result.status === 'failed') {
    setError(t('callFailed') + ': ' + ((result.error && result.error.message) || result.error));
  }
};
```

---

## 5. Backend behaviour

**Nothing in the backend was changed.** The approved action already existed and already did the right
thing; POD-12 asked for a control, not for a new capability. What the existing route does, and why it
was reused unchanged:

1. `require_permission("queue.manage")` — 403 for anyone else (fail closed).
2. `_scoped_entry_or_404` — cross-tenant/cross-branch reads resolve to **404**, never 403.
3. Doctor/assistant acting outside their assignment → **404**.
4. Transition validation against `_TRANSITIONS` — an ineligible status is **422**.
5. Status history appends `{from, to, action, actor, reason, at}`; `status` becomes `called`.
6. `record_audit(service="queuing", action="queue.call", before={"status": "waiting"},
   after={"status": "called"})` — the queue transition is audited **server-side, before the client is
   told**. This is the audit record that exists today; it is not an *announcement* audit event, which
   remains POD-4.
7. Commit, then `on_queue_changed` notification hooks fire; the updated entry is returned.

Because the audit, the transition and the commit all happen before the HTTP response, a client audio
failure cannot affect them — the ordering is the guarantee, not a client convention.

---

## 6. Permission verification by role

Both matrices were read today; the frontend mirror was executed with a real session
(`withRole(role, () => can('queue.manage'))` in the new test file), and the Python matrix was parsed
from source in the same test, so drift between them fails the suite.

| Role | Holds `queue.manage`? | Sees Call? | Evidence |
|---|---|---|---|
| `receptionist` | **Yes** (explicit, `permissions.py:100`) | **Yes** | frontend `can()` returns true; backend `require_permission` passes; `test_receptionist_can_call_a_waiting_entry` |
| `doctor` | **No** (`permissions.py:104-122`; and not delegable) | **No** | frontend `can()` returns false; backend answers **403**; `test_doctor_cannot_call_without_queue_manage` |
| `assistant` | No | No | frontend `can()` returns false |
| `branch_admin` | **Yes — pre-existing** via `queue.*` | Yes, unchanged | nothing granted by this task; the wildcard predates POD-12 (`git diff` shows `permissions.py` untouched) |
| `org_admin` | Yes — pre-existing via `queue.*` | Yes, unchanged | as above |
| `super_admin` | Yes — pre-existing via `queue.*` | Yes, unchanged | as above |

No permission, role, grant or matrix entry was added, removed or reordered. The doctor row is the
consequence of POD-12's own constraint rather than an omission — see **DEV-1**.

---

## 7. Automated tests — commands and real results

Run from `frontend/` with Node v24.12.0 (no dependency needed for the assertions themselves):

| Command | Result |
|---|---|
| `node --test tests/queue-call-control.test.mjs` | **18 tests, 18 pass, 0 fail, 0 skipped** (exit 0) |
| `node --test tests/queue-*.test.mjs` | **116 tests, 115 pass, 0 fail, 1 skipped** (exit 0) — the skip is the pre-existing JSX compile check, **DEV-3** |
| `node --test tests/*.test.mjs` | **288 tests, 284 pass, 2 fail, 2 skipped** (exit 1) |

The two failures are the same pre-existing, unrelated ones recorded by the W1/W2 recovery:
`tests/banglanamesense-dataset.test.mjs:60` (pinned dataset checksum) and
`tests/calendar-render.test.mjs:1` (Windows `E:` ESM URL). Both skip tests are the JSX compile checks
that report "next/dist/build/swc unavailable in this install" although the binary is present —
`calendar-render` fails for the same Windows import-path reason that makes those checks skip (**DEV-3**).
Arithmetic: the pre-existing population was 270 tests; 270 + 18 new = **288**.

What the 18 new tests cover, against POD-12 §6's required list:

| # | Requirement | Test |
|---|---|---|
| 1 | Authorised receptionist can call | `receptionist holds queue.manage in both matrices`, `a successful call sends exactly the documented payload` |
| 2 | Authorised **doctor** can call | **Not satisfiable** — no doctor holds `queue.manage`; covered instead as `doctor does NOT hold queue.manage, so Call is not offered` (**DEV-1**) |
| 3 | Callers without `queue.manage` rejected by the backend | `the call action uses the existing endpoint and action string` (asserts the route's `require_permission("queue.manage")`), plus the new Python test (written, not executed) |
| 4 | Frontend exposes no actionable control to unauthorised users | `the control is gated on queue.manage and on eligibility`, `an assistant is never offered the control`, `an unauthorised caller sends nothing either` |
| 5 | `waiting` can transition to `called` | `only a waiting entry is callable`, `a successful call sends exactly the documented payload` |
| 6 | An ineligible entry cannot be called | `only a waiting entry is callable`, `an ineligible entry is refused before any request exists` |
| 7 | A failed request does not announce | `a failed request is reported, never as a success`, `the page refreshes — and therefore announces — only on success` |
| 8 | A successful call triggers the seam | `a refresh that reveals a called entry produces one announcement`, `the announcement seam is unchanged and unawaited` |
| 9 | The action does not await audio | `the call module has no audio dependency at all` |
| 10 | Audio failure cannot affect the queue operation | `the call module has no audio dependency at all` (+ W2's controller tests, which prove `announce()` never rejects) |
| 11 | Repeated clicks cause no duplicate requests | `a second click while a call is pending sends nothing`, `the gate survives a rejected request` |
| 12 | Existing tests remain valid | the full run above; no test was deleted, skipped or weakened |

**Backend tests: written, not executed.** `pytest`, `fastapi` and `sqlalchemy` are not installed on
this host, there is no virtualenv and no Docker, and the queue suite requires PostgreSQL. The two added
tests were therefore only **syntax-checked** (`python -m py_compile backend/queuing/tests/test_queue.py`
→ OK, exit 0). They must not be counted as passing until they run on a backend-capable host.

---

## 8. Build result

`frontend/node_modules` was absent, so dependencies were installed with the lockfile-preserving
command (npm 10, registry reachable, `npm ping` → PONG 362 ms):

```
cd frontend; npm ci --no-audit --no-fund     → added 125 packages in 48s
cd frontend; npm run build                   → exit 0
```

Build output verified, not assumed:

```
▲ Next.js 14.2.35
  Linting and checking validity of types ...
  Creating an optimized production build ...
 ✓ Compiled successfully
 ✓ Generating static pages (8/8)
Route (pages)                Size     First Load JS
├ ƒ /queue                  13.4 kB          132 kB
```

**`frontend/package-lock.json` was not modified** (`npm ci` installs from the lock and does not write
it; `git status` shows no change to it). `node_modules/` and `.next/` are ignored by the existing
`.gitignore`, which was already modified in the working tree before this task and was not touched
further.

An independent compiler check was also run, because the suite's own JSX compile test skips (**DEV-3**):

```
node --input-type=module -e "…swc.transform(read('pages/queue.js'), {jsx:true})…"
→ compiled chars 42963, has callEntry true
```

So `pages/queue.js` — including the new button and handler — is **compiler-verified**, by the build and
by SWC directly.

---

## 9. Browser verification — not performed, blockers stated

The assignment (§7) requires a browser run of the receptionist and doctor workflows. **It was not
performed, and no browser evidence is claimed.** Exact blockers, each verified in this session:

1. **No backend runtime.** `python` is 3.13.5 with no `fastapi`, `sqlalchemy` or `pytest` installed, no
   virtualenv in the tree, and no Docker (`docker` is not on PATH). None of the seven services can be
   started, so `/api/v1/queue` cannot answer a PATCH.
2. **No database.** The queue service is PostgreSQL-backed (`backend/queuing/tests/test_queue.py`
   header); no PostgreSQL instance is reachable from this host.
3. **No browser automation tool.** Nothing in `frontend/devDependencies` or the repository drives a
   browser, so even a mocked front-end run could not produce "browser evidence" honestly.
4. **No audio output.** Prerecorded playback and the activation gesture need a real browser on a real
   speaker; nothing here can assert that a clip was heard.

What *is* proven instead, and what it does not cover: the build (§8), the rules and wiring (§7), and a
static read of the server route (§5). None of that is a substitute for clicking Call in a browser and
hearing the announcement; that step remains **VERIFIED: NO**.

---

## 10. Announcement triggering behaviour

The chain, end to end, with the link this task added marked:

1. Operator clicks **Call** on a `waiting` entry (new control, gated on `queue.manage`).
2. `performCall()` sends `PATCH /api/v1/queue/{id} {action:"call"}` — **once** (gate).
3. The server authorises, transitions, appends history, **audits `queue.call`**, commits, returns 200.
4. Only on the `called` result does the page call `loadQueue()`.
5. The refetch replaces `entries`; the tracker sees `waiting → called` for that id and reports one
   transition (first observation seeds, so a page load stays silent).
6. `transitioned.forEach(announceOnCall)` fires `{action:'call', source:'event'}` — **not awaited**, and
   it never calls the API.
7. The controller plays the configured transport; prerecorded is the default and is unchanged by this
   task. Playback outcomes are reported in the panel, never thrown.

Therefore:

- **Success → announced**: yes, through the existing seam, exactly once per observed transition.
- **Failure → silent**: a non-2xx never reaches step 4, so no `called` row exists to announce.
- **Audio failure → nothing blocked**: steps 3–4 are complete before any audio call is made; the
  controller converts every outcome to a status object and `announce()` never rejects.
- **Activation requirement preserved**: the automatic path passes `source: 'event'` and does **not**
  claim a user gesture. If the operator has not enabled audio, the panel says so; the call itself still
  succeeds. This is deliberate (POD-12 §4B: preserve the explicit activation requirement) and it means
  an announcement can be silent while the queue transition is correct — the honest behaviour, not a
  hidden fallback.
- **Wording untouched**: no phrase, language, token or room value changed; the payload still carries
  only `queueEntryId`, `action`, `token`, `room` — no patient name, doctor name, phone number or
  clinical detail.

---

## 11. Deviations and blockers

**DEV-1 — the doctor half of POD-12 cannot be exercised, and one required test cannot be satisfied.**
POD-12 says doctors may call "where their existing permissions grant `queue.manage`". No doctor role
holds it (`permissions.py:104-122`), and `queue.manage` is absent from `DELEGABLE_CAPABILITIES`
(`permissions.py:143-152`, enforced at `identity/routes.py:390`), so no administrator can grant it
either. Consequently: the Call control is **not** shown to a doctor, the server would answer **403**,
and required test #2 ("Authorised doctor can call a waiting entry") has no state it could assert.
Rather than fabricate the state, the suite asserts the truthful boundary in both matrices and the
backend test asserts the 403. **If doctors are meant to call patients, that needs its own owner
decision** — either a new capability or `queue.manage` for the doctor role — and it is deliberately not
taken here.

**DEV-2 — `skipped → called` exists server-side but is not offered.** `_TRANSITIONS["skipped"]`
includes `call`. The interface offers Call only for `waiting`, per POD-12 §4A, because a skipped entry
is recovered (BR §27A) and recovery already has its own control. No server behaviour changed.

**DEV-3 — the suite's JSX compile checks skip on Windows for the wrong reason.** Both checks do
`await import(FE + '/node_modules/next/dist/build/swc/index.js')`; a bare `E:/…` specifier is not a
valid ESM URL on Windows, so the import throws and the tests skip with "next/dist/build/swc unavailable
in this install". The binary **is** installed — loading it through `pathToFileURL()` compiles
`pages/queue.js` successfully (§8). `tests/calendar-render.test.mjs` fails for the same root cause. This
is a pre-existing test defect, outside POD-12's scope, recorded rather than fixed.

**DEV-4 — the frontend mirror ignores delegated capability grants.** `can()` in `frontend/lib/auth.js`
reads a role table only; `require_permission` on the server uses `check_granted` (matrix ∪ grants).
Today the divergence is unobservable for `queue.manage` (it cannot be delegated), but if a future
decision makes it delegable, a granted user would be authorised by the server and still see no control.

**DEV-5 — scope restriction, stated plainly.** No W3 language/voice configuration, no W4 room source,
no W5 distribution, no W6 asset work, no announcement audit event (POD-4), no server event identity or
cross-client dedupe (POD-8), no polling or real-time transport, no schema migration, no permission
change.

---

## 12. Remaining cross-terminal and audit limitations

These are **not** fixed by POD-12 and are unchanged from the W2 report:

1. **No polling.** The queue page refreshes only on its own actions or the manual Search button. A
   second terminal's call is seen only when an operator refreshes.
2. **A refresh that reveals another terminal's call can announce.** The tracker is tab-local: this tab
   remembers `waiting`, the refresh shows `called`, and the transition is announced here too. Cross-client
   deduplication needs server-supplied event identity — **POD-8**.
3. **Event identity is client-derived** (`entry:<id>:call:0`, no `revision`). A recall (`called →
   called`) is not a transition the tracker can see, and a re-call after reinsert would reuse the key.
4. **No announcement audit record exists.** `queue.call` is audited; "this announcement was played on
   terminal X at time T" is not — **POD-4**.
5. **No room** is returned by any queue endpoint, so the room clause is passed through as `undefined`
   rather than invented — **POD-2/W4**.
6. **Pronunciation** of recorded Bangla is not validated here — **O-3**.
7. **Silent-but-successful is possible**: if audio was never enabled, the call succeeds and nothing is
   heard. That is the approved behaviour (explicit activation), not a defect.

---

## 13. Repository state and preservation

- HEAD remains **`37cf3d1`**. Nothing was staged (`git diff --cached` empty), committed, pushed, reset,
  cleaned, stashed or reverted. No destructive Git command was run.
- The working tree still carries the **pre-existing 9 modified / 26 untracked** entries that were there
  before this task; none was overwritten, moved or deleted. Every pre-existing report, including the
  earlier `QUE-006_W1_..._REPORT.md` and `QUE-006_W2_QUEUE_INTEGRATION_REPORT.md`, is byte-unchanged.
- New untracked paths created by this task: `frontend/lib/queue/`, `frontend/tests/queue-call-control.test.mjs`,
  this report. Modified tracked paths: `frontend/pages/queue.js`, `frontend/lib/i18n.js`,
  `backend/queuing/tests/test_queue.py`, `docs/governance/AMSDP_Docs_Index_V1.0.md`.
- `backend/common/permissions.py`, `backend/queuing/main.py`, `backend/common/auth.py`, the audio
  manifest, `frontend/public/audio/**` and every other announcement module are **untouched**.
- Installed `frontend/node_modules/` (125 packages) and generated `frontend/.next/` are both ignored by
  the existing `.gitignore`; `frontend/package-lock.json` is unmodified. One temporary file written to
  `runs/` while capturing test output was deleted in the same session.
- Documentation was written under `docs/implementation/` only (§11 of `.clinerules`), and the index was
  updated in the same task (§12).

---

## 14. Exact remaining work before W2 can be accepted

W2 is **not** accepted by this task. In order, the shortest honest path:

1. **Run the backend suite on a backend-capable host** — `python -m pytest backend/queuing/tests/test_queue.py
   backend/tests/test_e2e.py backend/tests/test_sequence4.py` — and record the real counts. Until then
   the two new Python tests are written, not passing, and "backend-verified" is **NO**.
2. **Browser verification of the call flow** — receptionist login → select doctor/date → Call on a
   waiting entry → notice appears, row becomes `called`, announcement plays (after Enable audio);
   repeat with the server stopped to confirm the error path announces nothing; confirm a doctor login
   shows no Call control. Record the evidence and the build/run commands used.
3. **Product Owner decision on the doctor workflow (DEV-1)** — if doctors are expected to call
   patients, decide the permission route (new capability vs. `queue.manage` for the doctor role) and
   then extend the control, which already reads `can('queue.manage')` and needs no code change if the
   matrix changes.
4. **POD-8 (event identity / cross-client dedupe)** before any claim of "announced once across
   terminals"; **POD-4** before any claim of an announcement audit trail.
5. **POD-2/W4** before the room clause can be spoken, and **O-3** before pronunciation is asserted.
6. Only then restate W2's status; POD-12 being implemented does not complete W2.

---

## 15. Governance and Skill Compliance

| Domain (§4 routing) | Documents applied | Evidence of application |
|---|---|---|
| Frontend UI / components / a11y | `saas-frontend-ux.md` (as adapted), `docs/governance/AMSDP_Engineering_Governance_Assessment.md`, shared components, `frontend/lib/i18n.js` | Reused the existing `DataTable` actions cell and `btn btn-sm` primitives; no new component library; both captions added to `DICT.bn` **and** `DICT.en` (the boundary test enforces it) |
| Backend API / authorization | `saas-application-security.md` (adapted), Business Rules Part II | The existing route's `require_permission("queue.manage")` was reused and asserted; no endpoint added; no authorisation weakened |
| Multi-tenant / branch isolation | `saas-multitenant-data.md` (adapted), `backend/common/auth.py` | No query or scope logic was written; the 404-not-403 rule is properties of the reused route, recorded in §5 |
| Queue / workflow transitions | Business Rules Parts V–VII, M4/M5 reports | Reused `_TRANSITIONS` exactly; `skipped → called` left unexposed; the transition tracker was inspected and preserved |
| Documentation (writing/reading) | §11/§12, `AMSDP_Docs_Index_V1.0.md` | Index read first; report written under `docs/implementation/`; index row + Revision 47 added; no migration owed |
| Skills | **NONE installed** (verified: no `.clinerules/skills/`, `.claude/skills/`, repo `skills/`) | No skill was used or claimed. Governance documents plus existing code served the role, as §5 requires |

Non-negotiables checked: no secret, token or credential appears in this report; authorisation is enforced
server-side only (the UI gate is a mirror, stated as such in code and here); no audit record was deleted
or rewritten; no schema change and therefore no migration; nothing unverified is claimed as verified.

---

## 16. Final handoff

| State | Verdict | Basis |
|---|---|---|
| **Implemented** | **YES** | `queue-call.js`, the page wiring, two bilingual captions, two backend tests |
| **Unit-tested** | **YES** | 18/18 new tests; queue population 116 tests, 115 pass, 1 pre-existing skip |
| **Backend-verified** | **NO** | `pytest`/`fastapi`/`sqlalchemy`/PostgreSQL/Docker absent; `py_compile` only |
| **Build-verified** | **YES** | `npm run build` exit 0, "Compiled successfully", `/queue` 13.4 kB; SWC compiles `pages/queue.js` |
| **Browser-verified** | **NO** | no backend runtime, no database, no browser tool, no audio output — §9 |
| **Blocked / not verified** | Doctor workflow (**DEV-1**, needs an owner decision); `skipped` path (**DEV-2**, deliberate); cross-terminal dedupe (**POD-8**); announcement audit (**POD-4**); room clause (**POD-2/W4**); pronunciation (**O-3**) | each named with its decision reference |






