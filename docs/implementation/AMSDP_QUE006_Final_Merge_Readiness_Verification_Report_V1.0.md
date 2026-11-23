# AMSDP — QUE-006 W2 Final Merge-Readiness Verification Report (V1.0)

> **Task:** `AMSDP-QUE006-W2-FINAL-MERGE-READINESS-VERIFICATION-2026-11-23`
> **Date:** 2026-11-23 · **Author:** engineering agent (Ubuntu workspace)
> **Environment:** an **isolated** copy of the product stack — compose project `q6fmr`,
> file `/tmp/que006_fmr/compose.fmr.yml`, host ports 59010–59027 and the application
> origin `http://127.0.0.1:59030`, its own volumes and network, so nothing in this
> report can have been produced by the demo stack or by the developer's own data.
> **Evidence base:** raw logs written during this session under `/tmp/que006_fmr/`
> (cited per claim below).
> **Verdict:** **MERGE-READY, CONDITIONALLY.** The announcement defect that blocked the
> merge is **FIXED** (`IMPLEMENTED` + `TESTED` + `VERIFIED`). Four **owner decisions**
> remain open by design (D-3, D-5, D-7, O-2) and **audibility is NOT VERIFIED** (§9).

---

## 0. Plain summary

1. The merge blocker was **real and total**: in a real browser the queue page could never
   leave *"audio off"*, because every clip that finished naturally was reported as a
   failure. Root cause and fix: §3. Before/after browser evidence: §3.6.
2. With the fix in the shipped bundle, a real Chromium run drives the whole W2 pipeline:
   enable audio → `call` → claim (`201 claimed:true`) → four clips played to their **end**
   → outcome reported `completed` → the panel states the announcement was heard (§5).
3. INT-4 and decisions **B**, **C** and **D** are re-verified **live over the deployed
   origin** (application proxy + RBAC + database + audit), not in a test double (§4).
4. Suites: frontend **368/368**; targeted backend **187 passed / 0 failed**. One
   whole-tree backend failure is explained and disproved as a product defect (§6.3).
5. Schema: exactly **one** Alembic head, and the live database is at it (§7).
6. What this report does **not** claim: that anything was *heard*. There is no speaker in
   headless Chromium. `AC-2` "played to end" is proven; audibility is **NOT VERIFIED** (§9).

---

## 1. Scope

In scope, and each item addressed below:

| # | Item | Where |
|---|---|---|
| 1 | **INT-4** — W3 voice-pack / platform announcement routes reachable through the application origin, with RBAC intact | §4.1 |
| 2 | **Decision B** — doctor create contract: a foreign-branch-only payload is refused, not silently accepted | §4.3 |
| 3 | **Decision C** — a retired staff↔doctor assignment is not serialised | §4.4 |
| 4 | **Decision D** — facility doctor queue-calling policy: default off, org-scoped, audited, non-disclosing refusals | §4.5 |
| 5 | **D-3, D-5, D-7, O-2** — the four carried-forward items, written up with status and closing condition | §8 |
| 6 | **G10** — real-browser proof of the announcement pipeline (enable → call → claim → play → outcome) | §5 |
| 7 | The **merge-blocking defect** in announcement playback | §3 |

Out of scope: any change to product behaviour, any new dependency, any commit or push.
Nothing in this task touched the demo stack.

---

## 2. Method, and why these results are trustworthy

The verification was designed so that a *false positive is hard*:

* **Production topology.** Every request — page, API and audio asset — went through the
  Next application origin `:59030`, so the rewrite proxy, the token-derived scope and the
  RBAC checks ran exactly as they will in deployment. Requests were never sent straight to
  the service containers.
* **A negative control for the proxy.** `GET /api/v1/unknown-thing` returns **Next's own
  HTML 404** (`text/html; charset=utf-8`), while every rewritten API route returns
  `application/json`. That control is what makes "200 JSON" evidence of a *backend* reply
  rather than of a page that happens to answer 200 (`api_matrix2.log`).
* **Two layers of evidence per claim.** HTTP status *and* database row *and* audit row
  where a write was involved; for the browser, the DOM *and* the media-element event trace
  *and* the HTTP exchanges the page issued.
* **Measurement defects were repaired, not explained away.** The first attempt to verify
  decision D was inconclusive because the demo `doctor` login owns **no** doctor assignment
  (RBAC-R3, §9) and one parser used `sed` on JSON. Both were fixed: JSON is now parsed with
  `python3`, and a doctor staff user that actually holds the assignment is created through
  the product's own API before the measurement (`api_matrix3.sh`). The result then flipped
  from *inconclusive* to *verified* — which is the correct behaviour of an honest harness.
* **The browser harness measures events, not intentions.** An init script wraps
  `HTMLMediaElement.prototype.play` and records, for every element the engine plays, the
  ordered events with `currentTime`, `duration`, `ended` and `paused` **at each event**. A
  finished clip is therefore a recorded `currentTime == duration` fact, not an inference.
* **Everything is reproducible.** The matrix scripts, the Playwright script and the compose
  file are kept with the logs; every count below can be re-derived from them.

---

## 3. The merge blocker: the queue page could never enable announcements

### 3.1 Symptom (reproduced in a real browser, pre-fix)

Run against the pre-fix build (`/tmp/que006_fmr/g10_run2.log`):

```
badge before enable = badge badge-warn :: অডিও বন্ধ      (audio off)
clicked Enable audio
badge after enable  = badge badge-warn :: অডিও বন্ধ      (still off)
enable button still present = 1
media so far = [{ src: /audio/en/phrase/room-suffix.mp3,
                  events: [playing, pause, ended], duration: 0.3, finalTime: 0.3 }]
```

The priming clip **did** play, and it **did** reach its end (`finalTime 0.3` of
`duration 0.3`) — yet activation never became `granted`, the panel stayed *audio off*, and
because the controller refuses to announce while activation is not granted, **no
announcement could ever play**. Queue calls still committed server-side, so the failure was
silent from the operator's point of view: the patient was called, nobody was told.

### 3.2 Root cause

`frontend/lib/announcements/prerecorded-audio.js`, `playSegment()`. The HTML media element
specification's *"ended playback"* steps set `ended = true`, then **queue a `pause` event**,
then fire `ended`. The listener was:

```js
pause: () => done(cancelled
  ? { status: PLAYBACK.INTERRUPTED, reason: 'cancelled' }
  : { status: PLAYBACK.FAILED, reason: FAILURE.INTERRUPTED }),
```

The first listener to fire wins (`done()` latches `settled`), and `pause` fires **before**
`ended`. So every *natural* end of every clip was resolved as `FAILED / interrupted`.
Consequences:

* `prime()` saw `step.status !== COMPLETED`, returned `{ status: 'interrupted' }`, so
  `activate()` left `activation` at `UNKNOWN` → the panel never left *audio off* → **the
  automatic call announcement could never run**;
* a clip that had actually finished was recorded and reported as a failed playback, i.e.
  the outcome record (`/announcements/{id}/outcome`) would have said failure for a success;
* the browser's own event trace is unambiguous: `pause` arrives with `t = 0.3`,
  `d = 0.3`, `ended = true`, `paused = true`.

### 3.3 Fix — `playedToEnd()`: a pause taken at the end of the media *is* completion

```js
function playedToEnd() {
  if (element.ended === true) return true;
  const duration = Number(element.duration);
  const time = Number(element.currentTime);
  return Number.isFinite(duration) && duration > 0
    && Number.isFinite(time) && time >= duration - 0.05;
}

pause: () => {
  if (!cancelled && playedToEnd()) {
    done({ status: PLAYBACK.COMPLETED });
    return;
  }
  done(cancelled
    ? { status: PLAYBACK.INTERRUPTED, reason: 'cancelled' }
    : { status: PLAYBACK.FAILED, reason: FAILURE.INTERRUPTED });
},
```

Design notes:

* The tolerance is **50 ms of media time**, not wall-clock. It absorbs the sub-frame gap
  between the final sample and the queued pause while still refusing a pause taken earlier
  in the clip — and it is an order of magnitude smaller than the shortest real clip in the
  catalogue (a ~300 ms intentional pause; spoken digits are ~1.8 s).
* A **genuine** mid-clip pause is unchanged: not cancelled → `FAILED / INTERRUPTED`;
  cancelled → `INTERRUPTED / cancelled`. A stop is still a stop.
* `ended` remains the primary signal; the duration comparison only covers the event order
  the browser actually produces.
* Nothing was aliased or loosened in the outcome vocabulary — **D-6 stands** (`completed` /
  `interrupted` only, no pre-merge spellings reintroduced).
* No new dependency, no API change, and no change to the queue transaction: audio is still
  fire-and-forget, and a playback failure still cannot reverse a successful call.

### 3.4 Tests added (3, in `frontend/tests/queue-announcement-prerecorded.test.mjs`)

| Test | What it pins |
|---|---|
| `AC-2 a browser natural end (pause before ended) is completed, not interrupted` | the exact Chromium ordering — `pause` with `ended:true`, then `ended` → `COMPLETED` |
| `AC-2 a natural end of the prime clip reports primed` | the activation path at player level: `prime()` returns `{status:'primed'}` after a natural end |
| `AC-2 a pause taken before the end of the media is still interrupted` | the guard against over-correcting: an early pause with `ended:false` stays `FAILED/INTERRUPTED` |

The fake media element gained `finishNaturally()`, which reproduces the browser's ordering
(set `ended`, emit `pause`, emit `ended`) instead of only emitting `ended`.

### 3.5 Why the existing suite could not have caught it

The fake media element emitted **`ended` alone** for a natural end. It never modelled
"`pause` first, then `ended`", which is exactly what Chromium does — so the suite stayed
green while the feature was dead in every real browser. This is the classic case of a test
double being more forgiving than the product; the regression test now encodes the browser's
ordering, so the double can no longer be kinder than the browser.

### 3.6 Before / after — same harness, same stack, same day

| | Pre-fix (`g10_run2.log`, 14:11) | Post-fix, shipped build (`g10_browser_run5.log`, 16:35) |
|---|---|---|
| Badge after pressing *Enable audio* | `badge badge-warn :: অডিও বন্ধ` | **`badge badge-active :: অডিও চালু`** |
| Enable button afterwards | still present (`1`) | **gone (`0`)** |
| Media elements played | 1 — the prime only | **4** — prime + `token-number` + `digit-3` + `no-room` |
| Each clip's final position | `0.3 / 0.3` | `0.3/0.3`, `1.82/1.82`, `1.82/1.82`, `2.45/2.45` |
| Claim / outcome | none — nothing was announced | `POST …/announcement → 201 claimed:true`; `POST …/outcome → 200 status:"completed"` |
| Panel after the call | unchanged | `সর্বশেষ ঘোষণা: শোনানো হয়েছে — “টোকেন নম্বর ৩, অনুগ্রহ করে সামনে আসুন।”` |

The signed-off run used a **probe-free** build. The temporary instrumentation used to
isolate the defect was removed, the image rebuilt, and the running container's own source
tree confirms `function playedToEnd` present (`1`) and `__lastPrime` / `__queueAnnState`
absent (`0`) — so what is verified here is the shipped code, not an instrumented variant
(`149_src_check.txt`), and `git diff frontend/components/queue/QueueAnnouncements.js` is
empty after the revert.

---

## 4. Live API verification — INT-4 and decisions B, C, D

All requests below were sent to the **application origin** `http://127.0.0.1:59030`, through
the Next rewrite proxy, against the real services and the real PostgreSQL. Raw logs:
`api_matrix.log`, `api_matrix2.log`, `api_matrix3.log`.

### 4.1 INT-4 — W3 voice-pack and platform announcement routes (VERIFIED)

| Request (as org_admin unless stated) | Result | Meaning |
|---|---|---|
| `GET /api/v1/voice-packs` | `200` `application/json` | the W3 registry is reachable through the proxy |
| `GET /api/v1/platform/announcement-config` | `403` `application/json` `{"detail":"insufficient permissions"}` | **admin-only**, enforced server-side, JSON not a page |
| `GET /api/v1/orgs/demo-org-001/announcement-config` | `200` | organisation override readable by its own admin |
| `GET /api/v1/orgs/demo-org-001/queue-calling-config` | `200` | facility policy readable |
| `GET /api/v1/track/<bogus>` | `404` `{"detail":"not found"}` | public token route refuses a non-token |
| *negative control* `GET /api/v1/unknown-thing` | `404` `text/html` | an unwritten path is answered by **Next**, proving the JSON above came from the backend |

**This supersedes the INT-4 finding of `AMSDP_QUE006_Acceptance_Readiness_Verification_Report_V1.0.md`.**
At that point `frontend/next.config.js` had no rewrite for `/api/v1/voice-packs` or
`/api/v1/platform/**`, and both returned Next's own 404 through the application origin. The
merge now carries those rewrites (`next.config.js:46`, `:51`), and both routes answer through
the proxy with RBAC intact — so the previous finding is closed, not repeated.

### 4.2 The proxy really rewrites (and only where it is configured)

The negative control above is the load-bearing evidence: `text/html` for an unrouted path,
`application/json` for every routed one. A page-level 200 can no longer be mistaken for a
backend success.

### 4.3 Decision B — doctor create contract: a foreign branch is refused (VERIFIED)

```
POST /api/v1/doctors  { branch_ids: [<branch of another organisation>] }
  -> 422 {"detail":"branch not found in this organization"}
  -> doctors with that name in the DB: 0
```

The refusal is a `422` validation error, **not** a silent success and not a 404: the caller
is a legitimate admin of their own organisation, so the payload is what is wrong. Nothing was
written (verified by re-query). A same-organisation branch list succeeds.

### 4.4 Decision C — a retired staff↔doctor assignment is not serialised (VERIFIED)

`api_matrix2.log`: a staff user is created with `branch_ids`/`doctor` assignment, then the
assignment is retired through the product API.

```
created  9f00db4f-… branch_ids=["demo-br-001"]     (assignment live)
after retire: branch_ids=(empty)                    (nothing serialised)
```

`api_matrix3.log` adds the database view of the re-add:

```
db rows: inactive/false | 1     (the retired row is retained, inactive)
db rows: active/true    | 1     (the re-added assignment is the only active one)
```

So retirement is a state change, not a delete — history is preserved — and the API stops
advertising a retired assignment, which is what decision C asked for.

### 4.5 Decision D — facility doctor queue-calling policy (VERIFIED)

The policy is organisation-scoped and defaults to **off**. Measured with a doctor staff user
that genuinely holds the assignment (§9, RBAC-R3 explains why the demo `doctor` login could
not be used):

| Step | Result |
|---|---|
| policy default (`GET /orgs/demo-org-001/queue-calling-config`) | `doctor_queue_calling_enabled: false` |
| doctor calls own patient, policy **off** | `403 {"detail":"insufficient permissions"}` |
| assistant calls, policy off | `403` |
| receptionist still calls, policy off | `200` — the front-desk role keeps the action |
| `PUT` policy **on** as org_admin (own org) | `200` |
| doctor calls **own** patient, policy on | `200`; DB row `called`; audit `queue.call by doctor` |
| doctor calls **another doctor's** patient | `404 {"detail":"queue entry not found"}`; DB row unchanged `waiting` |
| `recall` action | `422 {"detail":"unknown action: recall"}` |
| `PUT` as receptionist | `403` |
| `PUT` to a **foreign** organisation | `404 {"detail":"organization not found"}` |
| cross-branch read | `404` (non-disclosing) |
| policy restored | `PUT off → 200` |

Every non-disclosing refusal is a **404**, never a 403 that would confirm the row exists, and
every allowed call is audited with the actor's role. The policy was restored to `off` at the
end of the matrix, so the stack is left in its shipped default state.

---

## 5. G10 — real-browser verification of the announcement pipeline

Harness: `g10_playwright.cjs` (Playwright, headless Chromium) driving the **product UI** on
`:59030`. It logs in as the receptionist, selects the doctor, presses *Enable audio*, creates a
fresh waiting entry through the page's own session, presses the entry's *Call* control, and
records (a) every media element played, with its event trace, (b) every claim/outcome HTTP
exchange the page issues, (c) the panel's rendered text.

Final run, probe-free build (`g10_browser_run5.log`):

```
badge before enable = badge badge-warn   :: অডিও বন্ধ
clicked Enable audio
badge after enable  = badge badge-active :: অডিও চালু          <- activation granted
enable button still present = 0                                <- the gesture is consumed
clicked Call

 #0 phrase/room-suffix.mp3  events=[playing,pause,ended] dur=0.3  final=0.3
 #1 phrase/token-number.mp3 events=[playing,pause,ended] dur=1.82 final=1.82
 #2 number/digit-3.mp3      events=[playing,pause,ended] dur=1.82 final=1.82
 #3 phrase/no-room.mp3      events=[playing,pause,ended] dur=2.45 final=2.45

POST /api/v1/queue/qe-T-DR002-003/announcement -> 201
     {"claimed":true,"event_id":"qce:qe-T-DR002-003:1","delivery_id":"0f87526d-…","status":"requested"}
POST /api/v1/queue/announcements/0f87526d-…/outcome -> 200
     {"event_id":"qce:qe-T-DR002-003:1","status":"completed"}

panel: কিউ ঘোষণা  অডিও চালু | সর্বশেষ ঘোষণা: শোনানো হয়েছে — “টোকেন নম্বর ৩, …”
```

What this **proves**:

1. The activation gesture works: the panel leaves *audio off* and the enable control
   disappears — the exact state the pre-fix build could never reach.
2. The prime clip is the catalogue's silent pause asset (`room-suffix`, 300 ms), i.e. audio
   was unlocked *inaudibly*, not by speaking an announcement out of context.
3. The spoken sentence is assembled from **four** catalogue clips — phrase, token number,
   the token digit, and the approved room-less sentence — played **sequentially**, each to its
   own `duration` (AC-2, AC-5: no overlap, no substitution).
4. The W2 pipeline ran in the deployed topology: the page **claimed** the server-owned call
   event (`qce:<entry>:1`, `claimed:true`, `delivery_id` issued) and **reported the outcome**
   `completed` — so the audit trail says "announced", and it says it only once.
5. The call itself is a separate transaction: the earlier run on a UUID entry records the
   `PATCH /api/v1/queue/def830ec-… → 200` that performs `call` (`g10_browser_run4.log`), and
   this run's claim exists only because that transition had already committed (the delivery
   event is `qce:<entry>:1`, minted from the append-only status history). Audio is therefore
   still fire-and-forget: a playback failure cannot reverse the call (AC-7).

What this **cannot prove**, and does not claim: that anyone *heard* it (§9).

---

## 6. Suites and builds

### 6.1 Frontend — `npm test` (`node --test tests/*.test.mjs`)

```
tests 368   pass 368   fail 0   duration_ms 6092
```

Run on the **final tree**, after the temporary probe was reverted (`136_fe_suite.log`). This
includes the three new AC-2 regression tests.

### 6.2 Backend — targeted run

```
187 passed, 3 warnings in 164.90s
```

(`84_targeted.log`) — the targeted backend run for this merge review. The log records the
migration steps it applied (`add_queue_announcement_deliveries`,
`add_voice_packs_and_platform_announcement_config`) and ends `187 passed, 3 warnings`. It is
cited for the count and for the fact that the announcement/voice-pack migrations apply
cleanly on the way in.

### 6.3 Backend — whole tree, and the one failure

```
1 failed, 790 passed, 50 warnings in 801.70s
FAILED tests/test_tracking_tokens.py::test_tracking_qr_cache_headers
E  ModuleNotFoundError: No module named 'qrcode'
   appointment/tracking.py:227
```

**Diagnosis — environment, not product.** `appointment/tracking.py` imports `qrcode` lazily
inside the endpoint (line 227). `qrcode>=7.4` **is** a declared dependency of that service
(`backend/appointment/requirements.txt:8`) and **is** installed in its image: `import qrcode`
succeeds inside the running `q6fmr-appointment-1` container. The unit-test environment in
which the suite ran does not install that service's requirements, so the import fails there
only. No source change was made to paper over it.

**Independent verification instead** (`api_qr.log`), over the deployed origin:

```
POST /api/v1/appointments/demo-appt-2026-11-20-01/tracking-token -> 201, tracking_url issued
GET  /api/v1/track/{token}/qr  -> 200
     content-type: image/png
     cache-control: no-store, private, no-cache, must-revalidate
     pragma: no-cache
     667 bytes, magic 89504e470d0a1a0a, PNG 328x328
negative controls: short token 404 · unknown 32+ token 404 · anonymous issue 401
```

That is exactly the behaviour the failing test asserts (a PNG with no-cache headers), now
observed against a live service rather than a test double.

### 6.4 Frontend build

`docker compose build frontend` + `up -d` exited 0 and printed `CLEAN_BUILD_UP`
(`127_build_clean.log`); the rebuilt image serves the fixed behaviour (§5).

---

## 7. Schema state — one head, and the database is at it

Computed from the tree (16 revision files, parents resolved, multi-parent merge revision
handled):

```
revision files : 16
heads          : ['c4d8e2a91f60']
head files     : ['c4d8e2a91f60_add_voice_packs_and_platform_config.py']
dangling parents: []
```

and read back from the live database:

```
SELECT version_num FROM alembic_version;   ->  c4d8e2a91f60
```

So there is no double head, no orphaned parent, and the migrated stack is exactly at the
single head (`116_heads.txt`, `120_heads.txt`, `145_current.txt`). `alembic current` inside
the service image is not executable (`alembic` is not on that image's PATH); the DB read is
the stronger check and is what is cited.

---

## 8. The four carried-forward items, written up

These are **owner decisions**, not defects. This task did not take any of them; it states
each one precisely enough for a decision to be made, with the code evidence.

### 8.1 D-3 — F3's bounded per-event store: integrate it, or retire it

* **What exists.** `frontend/lib/announcements/dedupe.js` exports a bounded per-event store
  (`createAnnouncementStore`, `DEDUPE_STATE`, `DEDUPE_DEFAULTS`, `retryDelayMs`) and has its
  own passing test. **No production file imports it** — verified by grep across
  `lib/`, `pages/`, `components/`: the only mentions outside its own test are prose in
  comments.
* **What the controller actually does.** A **single-slot** window:
  `controller.js:322` — `if (lastEventKey === key && (at - lastEventAt) < dedupeWindowMs)`
  → records `duplicate`. One remembered event key, `dedupeWindowMs` (default 5 000 ms), and a
  `source: 'operator'` call deliberately bypasses it.
* **Why it is not obviously wrong.** W2 moved *cross-terminal* identity to the server
  (`UNIQUE(call_event_id)` claim, `qce:<entry>:<index>`), which the single-slot window never
  needed to do. What the single slot **does not** model is the intra-tab case F3 was written
  for: several distinct events inside the window, and retry/exhaustion after a failed
  playback.
* **Options, both defensible.** (a) wire the store into `announce()`, keeping
  `dedupeWindowMs` as the bound; (b) delete `dedupe.js` and its test and document the
  single-slot window as the intended policy. Leaving dead code in the tree is the only option
  that is *not* defensible longer term.
* **Current status: OPEN — requires Product Owner decision.** No dedupe code was changed by
  this task.

### 8.2 D-5 — documentation-index revision numbering

* **What happened.** Two document lineages advanced the same index independently: the Windows
  lineage occupies **Revisions 36–48**; the Ubuntu lineage's two unmerged edits claimed
  **Revisions 36 and 37**. Assigning numbers is the index owner's act, so the index carries an
  explicitly **unnumbered "trial-merge annex"** recording the unmerged revisions and the
  documents that were never registered.
* **What this report did about it.** It is registered **in that annex, with no revision
  number** — the same treatment as the three preceding QUE-006 reports. Nothing was
  renumbered, no number was invented.
* **What would close it.** The index owner confirms that 48 is the true head; the annex
  entries are then assigned numbers in one pass, and the snapshot counts in the header are
  recomputed with the index's own maintenance command.
* **Current status: OPEN — requires Product Owner decision.**

### 8.3 D-7 — is an operator's manual repeat a second delivery record?

* **What is implemented.** An operator repeat goes through `announce(..., {source:
  'operator', userGesture: true})`, which **bypasses duplicate suppression and does not
  claim**. The comment of record in `pages/queue.js`: *"An operator repeat is deliberate, so it
  is neither claimed nor suppressed: one call event has one delivery record, and a repeat is
  not a second delivery."* The delivery table therefore holds **one** row per call event
  regardless of how many times a person presses *announce* again.
* **The open question.** Whether the audit trail *should* record the repeat (an operator
  speaking the same token twice is an operational fact someone may later need). Recording it
  requires a second record type — a delivery row cannot be reused without breaking the
  `UNIQUE(call_event_id)` guarantee that makes the cross-terminal claim correct.
* **Current status: OPEN — requires Product Owner decision.** Behaviour is deliberate and
  documented, not accidental.

### 8.4 O-2 — facility-level enable/disable and language configuration storage

* **What exists.** Platform defaults and an organisation override
  (`organizations.config["announcement"]`, served by the W3 endpoints verified in §4.1), plus
  the per-operator *Enable audio* gesture (a browser activation, not a configuration).
* **What does not exist.** No per-facility (branch) announcement setting and no stored
  facility language: `useQueueAnnouncements` speaks the operator's **current interface
  language** (`getLocale() === 'en' ? 'en' : 'bn'`) and never guesses, precisely because
  there is nothing to read. A facility that wants Bangla announcements with an English UI
  cannot say so yet.
* **Why it was not invented here.** It is a product surface (who may set it, what it
  overrides, what happens to an in-flight announcement) — not an implementation detail, and
  D-4 needed none of it.
* **Current status: OPEN — requires Product Owner decision.** No configuration surface was
  added.

---

## 9. Open items and claims deliberately not made

| # | Item | Why it is open |
|---|---|---|
| 1 | **Audibility (B-8)** | Headless Chromium has **no audio device**. What is proven is that each clip was *played by the browser to its full duration* and that the pipeline reported `completed`. Nobody has heard the sentence on a speaker, and no pronunciation judgement is made. **NOT VERIFIED.** |
| 2 | **RBAC-R3 — demo data** | The demo `doctor` login holds **zero** `staff_doctor_assignments` rows, so every doctor action fails closed for that account. This is a pre-existing demo-**data** condition, not a code defect: a doctor staff user created through the product API with `doctor_ids: [demo-dr-002]` can call their own patient and is refused a foreign one (§4.5). The demo seed should be corrected so the shipped login matches the documented role. |
| 3 | **Test-harness dependency gap** | The unit-test environment used for the backend run does not install the appointment service's requirements, so `qrcode` is missing and one test fails on import. Not a product defect; the endpoint is verified live instead (§6.3). The harness environment should install per-service requirements. |
| 4 | **Two unclassified 404 console errors** | The browser run logs two `404` resource errors (once before login, once after enabling audio). Every `/api/` exchange in the same run is `200`/`201`, so it is a static-asset request, most plausibly the favicon; it is recorded rather than diagnosed, and is cosmetic. |
| 5 | **`alembic current` not runnable in the service image** | `alembic` is not on that image's PATH. The schema position was read from `alembic_version` instead, which is the authoritative record (§7). |
| 6 | **Two-terminal observation** | The cross-terminal claim is verified through its server-side effect (`claimed:true`, one `delivery_id`), not by running two browsers and watching one stay silent. |

Claims **not** made in this report: that the announcement is intelligible, correctly
pronounced, or audible at a given volume; that the delivery claim is correct under
simultaneous presses from two physical terminals; that any owner decision has been taken.

---

## 10. Governance and Skill Compliance

*(Required by `.clinerules` §6 and §2 step 11.)*

### 10.1 Documents read and applied

| Domain (`.clinerules` §4 row) | Governance applied |
|---|---|
| Frontend UI / components / announcements | `saas-frontend-ux.md` (as adapted, Assessment §3); the announcement components under `frontend/components/queue/` and `frontend/lib/announcements/`; `frontend/lib/i18n.js` conventions |
| Queue / workflow transitions / tokens | Business Rules Parts V–VII as recorded in the QUE-006 implementation reports; the W2 claim/outcome design in `AMSDP_QUE006_W2_RELIABILITY_COMPLETION_REPORT.md` |
| Multi-tenant data / RBAC | `saas-multitenant-data.md` (adapted); `backend/common/auth.py` scope checks, `backend/common/permissions.py`; the non-disclosing-404 rule |
| Database schema / migrations | `saas-multitenant-data.md` §4–5; the Alembic chain under `backend/alembic/versions/` |
| Audit / data integrity | `saas-observability.md` (adapted); `backend/common/audit.py`; Business Rules Part X |
| Documentation (read + write) | `.clinerules` §11/§12; `docs/governance/AMSDP_Docs_Index_V1.0.md`, including its trial-merge annex |

Opened in this session: the docs index (annex region and the QUE-006 registration rows); the
QUE-006 implementation reports (targeted greps for the definitions of D-3, D-5, D-7, O-2 and
for the D-4/D-6 closure record); `frontend/lib/announcements/{controller,prerecorded-audio}.js`;
`frontend/components/queue/QueueAnnouncements.js`; the queue page wiring;
`backend/appointment/tracking.py`, `requirements.txt` and `Dockerfile`; the Alembic revision
files; and the harness files listed in §11. Every claim in this report cites a file or a log
opened in this session.

### 10.2 Skills

**No skill package is installed in this workspace** (`.clinerules` §5, re-verified: no
`.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`). No skill was used and none is
claimed; the governance documents above served in their place. Installing a formal skill
remains an owner decision (Skill Routing Architecture §6).

### 10.3 Non-negotiables — how each was honoured

| Non-negotiable | Evidence |
|---|---|
| No secrets logged or exposed | no token, password or JWT is quoted in this report; the tracking token in §6.3 is elided |
| Server-side authorisation, never the UI | RBAC measured over the API (§4); a disabled button is never treated as a security boundary |
| Cross-tenant / cross-branch fails closed with **404** | §4.5: foreign doctor's entry `404`, foreign-org `PUT` `404`, cross-branch read `404` |
| `organization_id` is the only tenant key | no second tenant column introduced; nothing schema-changing was added |
| Audit is append-only and denials are recorded | §4.5 `queue.call by doctor` written; no audit row deleted or rewritten; the retired assignment is retained as an inactive row (§4.4) |
| Forward-only, idempotent Alembic migrations | **no migration was written or modified**; the chain has one head and the database is at it (§7) |
| No unverified capability claimed | §9 lists what is *not* proven; §3.5 records that the suite could not have caught the defect |
| No destructive git operations | diffs and review only; `git diff frontend/components/queue/QueueAnnouncements.js` is empty, so no one else's work was disturbed |

### 10.4 Deviations and exceptions

* A **temporary instrumentation probe** was added to `QueueAnnouncements.js` to locate the
  defect and **removed before sign-off**; the rebuilt image proves the shipped source is clean
  (§3.6). The probe never entered a verified artefact.
* The **test harness**, not the product, was found wanting for the QR test (§6.3, §9 item 3);
  product behaviour was verified out of band rather than "fixed" in the test environment.

---

## 11. Files changed by this task

| File | Change |
|---|---|
| `frontend/lib/announcements/prerecorded-audio.js` | `playedToEnd()` added; a pause at the end of the media resolves `COMPLETED`; genuine early pauses unchanged (+28 / −3) |
| `frontend/tests/queue-announcement-prerecorded.test.mjs` | 3 AC-2 regression tests plus `finishNaturally()`, a fake that models the browser's `pause`-before-`ended` order (+64) |
| `frontend/components/queue/QueueAnnouncements.js` | **no net change** — the temporary probe was added and reverted; `git diff` is empty |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | one registration subsection (§*Final merge-readiness verification*, single-row table) appended to the **unnumbered** trial-merge annex — no revision number claimed (D-5) |

Verification artefacts (outside the repository, listed so every number is reproducible):
`compose.fmr.yml`, `api_matrix_fmr.sh`, `api_matrix2.sh`, `api_matrix3.sh`, `api_qr.sh`,
`g10_playwright.cjs`, and the logs `api_matrix{,2,3}.log`, `api_qr.log`,
`g10_run2.log`, `g10_browser_run4.log`, `g10_browser_run5.log`, `136_fe_suite.log`,
`84_targeted.log`, `96_faildetail.txt`, `120_heads.txt`, `145_current.txt`,
`149_src_check.txt`.

Not changed: no backend file, no migration, no dependency, no configuration, no product
document, and no test outside the one file above. The stack was left with the doctor
queue-calling policy at its default `off`.

---

## 12. Verdict

**The merge blocker is fixed and verified; whether to merge is an owner decision.**

| Gate | State | Basis |
|---|---|---|
| Announcement reachable and played end-to-end in a real browser | **PASS** | §5 — activation granted, 4 clips to their full duration, claim `201`, outcome `completed` |
| The defect is regression-tested at the level the browser exhibits it | **PASS** | §3.4 — 3 tests, one encoding the browser's exact event order |
| Frontend suite | **PASS** | 368 / 368 (§6.1) |
| Backend targeted suites | **PASS** | 187 / 187 (§6.2) |
| Backend whole tree | **1 known environment failure**, explained and disproved as a product defect | §6.3 |
| INT-4 through the deployed origin | **PASS** | §4.1 |
| Decision B | **PASS** | §4.3 |
| Decision C | **PASS** | §4.4 |
| Decision D | **PASS** | §4.5 |
| Schema: single head, database at head | **PASS** | §7 |
| Audibility on a real speaker | **NOT VERIFIED** | §9 #1 — no audio device in the harness |
| Owner decisions D-3, D-5, D-7, O-2 | **OPEN, deliberately** | §8 |

Recommended next steps, in order:

1. Let the product owner sign off the four decisions in §8, so the tree stops carrying dead
   and unnumbered artefacts.
2. Correct the demo seed so the `doctor` login holds its assignment (**RBAC-R3**) — the
   documented role and the shipped data currently disagree.
3. Install per-service requirements in the backend test harness, so the whole tree is green
   for the right reason rather than by absence of a dependency.
4. Make one observation on a real facility terminal with a human listener, to close **B-8** —
   the one property this report can establish everything about except that a person can hear
   it.



