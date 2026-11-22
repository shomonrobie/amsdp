# QUE-006 W2 — Queue Announcement Integration (implementation report)

**Assignment ID:** `AMSDP-QUE-006-W2-QUEUE-INTEGRATION`
**Date:** 2026-11-21
**Depends on:** W1 (prerecorded engine) — complete
**Status:** **PARTIALLY IMPLEMENTED** — the whole integration path is built and unit-verified; the
*automatic on `call`* trigger has no user-facing control to fire it, because QOP-001/POD-12 (a queue
`call` button) is an open Product Owner decision.

---

## 1. Files changed

| File | Change |
|---|---|
| `frontend/lib/announcements/controller.js` | Accepts a `player` and an explicit `strategy`; transport `prerecorded` is the default when a player is supplied; new `playPrerecorded()` outcome mapping; transport-aware capability; `activate()` primes the pack instead of speaking; `cancel()` reaches the player; new `refresh()`; `getState()` reports `transport`, `packId`, `packVersion`. |
| `frontend/lib/announcements/prerecorded-audio.js` | New `capability()` (ready / no_voice / pending) and `prime()` — a real, inaudible gesture unlock that plays the catalogue's 300 ms `intentional-pause` clip. |
| `frontend/lib/announcements/queue-transitions.js` | **New.** Pure rule: which entries *just became* `called`. |
| `frontend/components/queue/QueueAnnouncements.js` | Builds the player over the installed catalogue (`/audio/manifest.json`, client-side only), keeps the speech adapter as the documented alternative, reports a missing pack honestly. |
| `frontend/pages/queue.js` | New `announceOnCall(entry)` seam (fire-and-forget, `source: 'event'`) and a transition effect that announces a `waiting → called` change once. |
| `frontend/lib/i18n.js` | Three bilingual keys: `announceLastFailed`, `announcePackMissing`, `announcePackHint`. |
| `frontend/tests/queue-announcement-w2-integration.test.mjs` | **New**, 15 tests. |

## 2. Requirement-by-requirement status

| Assignment requirement (§W2) | Status | Evidence / limitation |
|---|---|---|
| Announcement occurs automatically on the approved queue-call event | **PARTIALLY IMPLEMENTED** | `trackCalledTransitions()` + the effect in `pages/queue.js` announce a `waiting → called` transition exactly once. The transition can only be observed where a `call` happens — and no page has a `call` control (gap analysis QOP-001: zero occurrences of `'call'` in `frontend/`). QOP-001/POD-12 is open, so no button was invented. |
| Receptionist and doctor workflows can trigger queue calls as authorised | **BLOCKED (POD-12)** | Permissions are server-side already (`queue.manage` / `queue.consult`); the UI control is QUE-001 work. |
| Playback does not block the queue transaction | **IMPLEMENTED AND VERIFIED** | `announceOnCall` is never awaited; static test strips comments and fails on any `await` in the seam; the queue write path (`doAction`) is untouched and still contains no audio reference. |
| Duplicate events do not produce duplicate announcements | **IMPLEMENTED AND VERIFIED** | Two independent guards: the transition tracker (an unchanged `called` status is not an event) and the controller's event key + 5 s window. Tests: *only a transition into `called` is announced*, *an unchanged status is not a new event*. |
| Failed playback does not reverse or block a successful queue call | **IMPLEMENTED AND VERIFIED** | `announce()` never rejects; every failure is an outcome object. The server transaction commits before the client announces. |
| No patient or doctor identity is announced | **IMPLEMENTED AND VERIFIED** | The seam passes `token` and `room` only; `content.js` templates have no doctor slot (doctor-name removal report). |
| Playback completion and failure are accurately represented | **IMPLEMENTED AND VERIFIED** | `completed` → `spoken` **only** from the final `ended` (end-to-end test); anything else → `failed` with reason, rendered as "playback failed" (new bilingual key). Browser start is never reported as completion. |
| Existing queue functionality remains intact | **IMPLEMENTED AND VERIFIED** | `doAction`, transitions, recovery and cancel paths untouched; the boundary suite re-compiles the page and its pinned assertions still pass. |

## 3. The transport decision, stated plainly

`QueueAnnouncements.js` now builds `createPrerecordedPlayer({ packProvider })` and hands it to the
controller. Consequences worth recording:

- **Prerecorded is the transport**; the browser voice list no longer decides anything for the queue
  page. A device with zero Bangla voices still plays Bangla, because the clips are files.
- **The catalogue is read once per page**, client-side, from `/audio/manifest.json`. Until it arrives
  the panel says "Preparing voice" (`pending_voices`), not "no voice" — a missing catalogue and a
  missing voice are different facts, and the engine now reports them differently.
- **A missing catalogue is shown, not worked around**: `announcePackMissing` + `announcePackHint`
  state that no other language or voice is substituted.
- **Speech is still available, but only by explicit configuration** (`strategy: 'speech'`). Asking for
  `prerecorded` without a player throws, so a mechanism substitution can never happen by accident.
- **Unlocking is a real play()**: `activate()` plays the catalogue's own 300 ms silence. If a pack has
  no such clip, activation reports `unavailable` and grants nothing — it does not pretend to be ready.

## 4. Test evidence

`frontend/tests/queue-announcement-w2-integration.test.mjs` — **15/15 pass**:

1. prerecorded is the default transport when a player is supplied
2. a playback failure is reported, never thrown, never spoken
3. busy and cancelled pass through unchanged
4. a blocked browser is not hammered without a fresh gesture
5. `activate()` unlocks by priming the pack, not by speaking
6. `activate()` with no silent clip grants nothing
7. an explicit speech strategy keeps the browser mechanism
8. asking for prerecorded without a player is refused (TypeError)
9. capability follows the pack, not the browser voice list
10. `cancel()` reaches the player
11. end to end: `spoken` only when the final clip ends
12. only a transition into `called` is announced
13. transitions survive entries leaving and returning
14. the transition rule tolerates junk
15. the queue page wires the call seam and never awaits it

Whole announcement battery: **90 tests, 89 pass, 0 fail, 1 skipped** (node v24.12.0).

## 5. Known limitations

| # | Limitation |
|---|---|
| L-1 | **No `call` button exists**, so the automatic trigger cannot be exercised through the product UI. Wiring and rule are tested; the user-facing event is POD-12. |
| L-2 | **Automatic announcements need an unlocked page.** A browser refuses audio outside a gesture, so the first automatic announcement on a fresh page resolves `failed('blocked')` and the panel asks the operator to enable audio. No workaround was invented (no silent autoplay tricks). |
| L-3 | **No server-side announcement record** — nothing in the audit trail says an announcement was made. POD-4 is open; none was added. |
| L-4 | **No browser run.** Playback, pause, and refusal behaviours are proven against a fake element only. |
| L-5 | The panel still shows the operator's interface locale as the announcement language (OD-2 facility configuration does not exist yet; W3 is where a configured language would come from). |

## 6. Regression check

The four pre-existing announcement suites pass unchanged (53 tests: 52 pass, 1 skipped), including the
pinned boundary assertions *announcing is not a queue action* and *the panel defers browser state until
after mount*. The queue page's own behaviour was not rewritten: the seam was added beside `doAction`,
not inside it.

**Caveat on the two JSX files.** The boundary suite's *the queue page and the announcement panel compile
as JSX* test **skips** in this workspace, because `frontend/node_modules` is not installed (no
`next/dist/build/swc`). The edits to `pages/queue.js` and `QueueAnnouncements.js` are therefore **not
compiler-verified**: they were reviewed by reading the final file state and their behaviour is asserted by
the static tests, but `next build` has not been run. Anyone continuing this work should run
`npm install && npm run build` in `frontend/` before treating the page as deployable.

## 7. Governance and skill compliance (`.clinerules` §6)

- **Domains (§4):** Frontend UI/components; Queue/workflow transitions (Business Rules Parts V–VII).
  Applied: the controller keeps the decisions, the engine keeps the transport, the page keeps no
  decision.
- **Skills:** none installed (§5) — none claimed.
- **Non-negotiables (§3):** UI is not the authorisation boundary (nothing here grants access); no
  secret is logged; no patient/doctor identity in the payload; no schema, permission or audit change.
- **Evidence standard (§7):** every statement above is IMPLEMENTED (code reachable) or VERIFIED
  (named test passing in this tree). Browser-level claims are explicitly excluded.
- **Report location (§11):** `docs/implementation/`.
