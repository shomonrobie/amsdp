# AMSDP — QUE-006 Trial Merge: B-1 and INT-3 Corrections and Re-verification, V1.0

**Date:** 2026-11-22 · **Branch:** `trial/que006-windows-ubuntu-merge` (HEAD `41ac51a`, `MERGE_HEAD` `2fc007a`) · **Status:** two defects fixed and regression-tested; trial merge re-verified; **nothing committed, pushed, migrated, deployed or restarted**; acceptance still blocked by **D-4**, **D-6** and the absence of browser/audio evidence.

This is the follow-up to `docs/implementation/AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md` (hereafter **V1.0**). It continues the *same* uncommitted trial merge — no second merge was started, the integration branch was not replaced, and no previously resolved conflict was reopened.

> **Amendment (2026-11-23) — D-4 and D-6 are closed.** Both were decided by the Product Owner on 2026-11-22 and are now implemented and regression-tested; the frontend suite is green (`355/355`) and the build compiles. Wherever this report records **D-4** or **D-6** as open (§11, §12, §13, §15) or describes the nine D-6 failures as current, `docs/implementation/AMSDP_QUE006_D4_D6_Decision_Closure_Report_V1.0.md` supersedes that row. Everything else here is unchanged and still stands, including **B-5** and **B-8**.


**What changed since V1.0:**

| Item | V1.0 | Now |
|---|---|---|
| **B-1** voice-pack API `TypeError` | open, 13 W3 API tests failing | **fixed**; 13/13 pass, 7 new regression tests pass |
| **INT-3** automatic room announcement | open, gated on D-4 | **fixed** (field consistency only); 12 new regression tests pass |
| **B-9** cross-tenant selection disclosure (new, found while verifying B-1) | unknown — masked by B-1 | **fixed**; 1 new regression test passes |
| Backend suite | 738 pass / 25 fail / 763 | see §6.3 |
| Frontend suite | 332 pass / 9 fail / 341 | **344 pass / 9 fail / 353** (the same nine D-6 failures, +12 new passes) |
| Production build | compiled | **compiled** (✓ `Compiled successfully`, exit 0) |
| Migration graph | one head after correction | one head, re-proven from an **empty** database |

---

## 1. Executive summary

* **B-1's real cause was a count read as a container.** `voice_pack_policy.validate_pack_upload` returns `assets` as the *number* of distinct stored paths; `voice_packs.py` wrapped it in `len()` when writing the creation audit reason. Every upload that had already passed validation therefore raised `TypeError: object of type 'int' has no len()` and answered **500** instead of **201**. One line, no contract change: the audit reason now reads the count it was given. 13 previously failing W3 API tests pass; 7 new regression tests pin the response body, the audit reason in both trails, invalid input, the org-scope stamp and the permission/tenant refusals.
* **A second defect was hiding behind B-1** and is reported and fixed as **B-9**: the organisation configuration `PUT` handed *every* voice pack to the selection check, so naming another tenant's pack answered `pack_foreign_organization` — an existence oracle that confirms the pack exists and who owns it — while naming a pack that never existed answered `pack_not_found`. The check now sees only this organisation's packs plus platform packs, so a foreign pack is indistinguishable from an absent one, while an **unreleased platform pack** still answers `pack_not_available` (the refusal the approved test pins). This is a `.clinerules` §3 non-disclosure rule, not a product choice.
* **INT-3 was exactly the reported field mismatch.** The automatic path (`frontend/lib/announcements/call-announcer.js`) read `entry.room`; the backend serializes the appointment booking snapshot as `room_name` (`backend/queuing/main.py::_entry_to_dict`), which is what the operator path in `pages/queue.js` already read. The automatic path now reads `room_name` too: one field, one convention, no second room key introduced, no queue-entry or snapshot behaviour touched. All four approved sentences now come out of the **real** announcer and the **real** controller, for both paths.
* **One conformance item surfaced while testing the Bangla sentence (INT-3b).** The approved Bangla wording names the room in Bangla digits (`কক্ষ ৩০৫-এ আসুন।`), but `buildAnnouncement` localised only the token number, so an ASCII `room_name` of `305` rendered `কক্ষ 305-এ` in the Bangla text (the prerecorded path was already correct — it plays `bn.digit.*` clips). The rendered Bangla text now localises the room's digits. `fields.room` is unchanged, so segment resolution and every caller see the payload exactly as before.
* **The trial merge is still not a deliverable.** Nine frontend tests still fail, all from the open **D-6** vocabulary decision; three backend queue tests still fail on pre-existing test defects; the nine doctor-test collisions do not reproduce on a clean schema (§6.4); and no browser, speaker or second terminal was available, so **every audible claim remains NOT VERIFIED**.
* **Nothing was committed, pushed, migrated on the live database, deployed, rebuilt or restarted.** All nine `amsdp-*` containers were left untouched; the disposable PostgreSQL used for the suites shares nothing with the live stack and is stopped at the end.

---

## 2. Starting-state verification

Recorded before any edit, and it matched V1.0 exactly — so no discrepancy had to be escalated:

| Check | Value |
|---|---|
| Branch | `trial/que006-windows-ubuntu-merge` |
| `HEAD` | `41ac51a0aea6a4462d3e2356cd5f3e58da57b326` |
| `MERGE_HEAD` | `2fc007a3f7a96639c3df36341c6081cee4d24a48` (`origin/hackathon-mvp`) |
| Commits on the branch | 54 |
| Staged entries | 176 (163 additions, 13 modifications), unchanged from V1.0 |
| Unstaged difference | **none** |
| Conflict markers / `.orig` / `.rej` | none |
| Merge commit | **none** (the merge is still uncommitted, as V1.0 left it) |

**Files identified for the two defects before editing:**

| Defect | File | Line (as found) |
|---|---|---|
| B-1 | `backend/organization/voice_packs.py` | 504 — `reason=f"{len(result['assets'])} asset(s), "` |
| INT-3 | `frontend/lib/announcements/call-announcer.js` | 143 — `room: entry.room,` |

Both line numbers matched the reports, so the diagnosis in V1.0 and in the trial hand-over was confirmed before a byte was changed.

---

## 3. B-1 — the voice-pack API `TypeError`

### 3.1 Root cause (established from the code, then reproduced)

1. `POST /api/v1/voice-packs` validates the whole upload **before** writing anything: `result = policy.validate_pack_upload(payload)`.
2. `validate_pack_upload` returns `{"ok", "problems", "assets", "bytes", "checksums"}` where **`assets` is `len(seen)` — an integer count of distinct stored paths** (confirmed at its return statement), and `bytes` is a running total.
3. `voice_packs.py:504` passed that integer to `len()` while composing the audit reason, so the `TypeError` fired *after* validation succeeded and *inside* the transaction:
   * every **invalid** upload still answered 422 (it never reached the line), which is why the failure looked like "only valid uploads crash";
   * every **valid** upload answered 500, so `create_pack()`'s `assert 201` failed at the first step of each test that needed a pack.
4. All 13 failing W3 API tests build a pack through that helper, so one line took out the entire configuration surface — including the permission matrix and the tenant-isolation tests, which never got to run their assertions. V1.0 §9.3 reproduced the same failure on the pure remote branch, so it is pre-existing and not a merge seam.

### 3.2 Correction (smallest correct change, contract preserved)

`backend/organization/voice_packs.py` — the audit reason now reads the count it was given; the response body and every other field are untouched:

```python
        _audit(session, pack, "voice_pack.created", auth,
               after=_summary(pack),
               reason=f"{result['assets']} asset(s), "
                      f"{result['bytes']} byte(s) uploaded")
```

Why this side of the contract, and not the policy: the response body already publishes the same integer (`"assets": result["assets"]`, `"bytes": result["bytes"]`), the policy's own docstring documents `assets` as a count, and no client consumes it as a list. Changing the policy to return a list would have altered a documented contract to accommodate a bug in its caller.

**Preserved deliberately:** the 201/422/409/404/403 status semantics; the `draft` + `pending` + not-released state of a new pack; validation strictness (the 422 payload still carries every problem); `_scope_of`'s token-derived scope; both audit trails (`voice_pack.created` in `platform_audit_events` for a platform pack, `audit_events` for a tenant pack); and pack versioning/approval behaviour — no product decision had to change.

### 3.3 Regression tests added (`TestUploadContract`, 6 tests)

| Test | What it pins |
|---|---|
| `test_a_valid_upload_answers_201_with_a_counted_summary` | 201; `draft`/`pending`/not released; `validation == {status: pass, problems: [], assets: 1, bytes: len(audio)}`; `assets` is an `int` — the exact value B-1 wrapped |
| `test_the_creation_reason_counts_the_assets_it_stored` | the `platform_audit_events` row: action `voice_pack.created`, target `id@version`, reason `"1 asset(s), … byte(s) uploaded"`, actor role |
| `test_an_organisation_upload_is_stamped_with_its_own_scope` | an `org_admin` upload is 201, `organization_id == ORG`, and its event is in `audit_events` (tenant trail) with the same counted reason |
| `test_an_invalid_upload_is_a_refusal_not_a_crash` | a checksum-mismatched upload is **422** with `voice pack upload failed validation` + `checksum_mismatch`, and **no row is stored** |
| `test_an_upload_for_another_organisation_is_a_non_disclosing_404` | a foreign-org upload is 404, names neither the pack nor the organisation, and stores nothing |
| `test_a_branch_administrator_cannot_upload` | `branch_admin` is 403 and stores nothing (product decision: no configuration access) |

### 3.4 Results — all 13 previously failing W3 API tests

All 13 now pass, and **none of them was modified**: `TestWhoMayConfigure` (3), `TestConfiguration` (5), `TestLifecycleAndVersions` (4), `TestUploadAndPreview::test_preview_does_not_change_the_configuration` (1).

```
backend/organization/tests/test_voice_packs_api.py + test_voice_pack_policy.py
74 passed, 1 warning in 84.10s
```

(61 pre-existing API tests + 7 new = 68 in the API module, plus the 6 policy-module tests run alongside — all green.)

---

## 4. B-9 — a cross-tenant refusal that disclosed existence (found while verifying B-1)

### 4.1 How it surfaced

Fixing B-1 let the 13 W3 tests run past their fixtures for the first time. Twelve passed and one — `TestWhoMayConfigure::test_cross_organisation_access_is_a_non_disclosing_404`, an approved test that had simply never been reached — failed with:

```
assert 'pack_not_found' in '{"detail":{"message":"invalid announcement configuration",
                                        "problems":["en: pack_foreign_organization"]}}'
```

An organisation administrator who names another tenant's pack learned that the pack **exists** and **belongs to another organisation**. That is an existence oracle across tenants, which `.clinerules` §3 forbids ("cross-tenant access fails closed, non-disclosing").

### 4.2 Root cause

`backend/organization/announcement_config.py::update_organization_config` built its `visible` list as `session.query(VoicePack).all()` — every pack in the installation — although the *screen* path (`_organization_view`) filtered to the caller's own packs plus released platform packs. The selection checker therefore saw the foreign pack and reached `check_selectable`'s owner test, which answers `pack_foreign_organization`.

### 4.3 Correction (two reads, two purposes — no product behaviour invented)

* `_visible_pack_rows(session, auth)` — the **screen's** list (own packs + released platform packs). Extracted from `_organization_view`, whose behaviour is unchanged.
* `_selection_pack_rows(session, auth)` — the **selection's** list (own packs + *all* platform packs). Deliberately wider so an unreleased platform pack can still answer `pack_not_available` — the refusal the approved test `test_a_platform_pack_that_was_not_released_cannot_be_selected` pins, and one that discloses nothing tenant-specific because the platform catalogue is not tenant data. Another organisation's pack is still excluded.

`update_organization_config` now calls `_selection_pack_rows`. Net effect on the two approved tests: foreign pack → `pack_not_found`; unreleased platform pack → `pack_not_available`; both green.

### 4.4 Regression test added (`TestCrossTenantRefusalsDoNotDisclose`, 1 test)

`test_a_foreign_pack_and_an_absent_pack_get_the_same_refusal` creates and publishes another organisation's pack, then compares the two responses: both 422, **byte-identical bodies**, and neither the owning organisation's id nor the pack id appears in the refusal. That is the strongest available proof without a timing oracle — the endpoint cannot tell a foreign pack from a pack that never existed.

---

## 5. INT-3 — the automatic room announcement

### 5.1 Data flow, traced end to end

| Step | Where | Room field |
|---|---|---|
| Queue entry row | `common/models.py` (`QueueEntry`) | none — the room is **not** on the queue entry |
| Booking-time snapshot | `common/locations.py::room_payload(Appointment)` | produces `room_id`, `room_name`, `label`, `source` |
| Backend response | `queuing/main.py::_entry_to_dict` + `_rooms_for` (one query per page) | `"room_name": room.get("room_name") or ""` |
| Frontend entry | `pages/queue.js` `entries` state | `entry.room_name` |
| **Operator** path | `pages/queue.js::announceEntry` | `room: entry.room_name` ✅ |
| **Automatic** path | `pages/queue.js` transition seam → `call-announcer.js` | `room: entry.room` ❌ (never sent by either backend) |
| Claim / report | `delivery.js::claimRequest` / `outcomeRequest` | no room — unchanged |
| Content | `content.js::buildAnnouncement` | reads `input.room` |
| Playback | `controller.js` → `player.play({token, room})` → `segments.js` | `content.fields.room` → digit clips |

An entry reaches the announcer as the same object the backend serialized, so `room_name` was already present at the seam — the automatic path simply read a key that never existed, and `undefined` quietly produced the approved *room-less* sentence. The queue call itself was never affected.

### 5.2 Correction

`frontend/lib/announcements/call-announcer.js` — one field, the same one the operator path reads:

```js
        token: entry.token,
        room: entry.room_name,
```

with an in-file comment recording why (`room_name` = the appointment booking snapshot, option R1) and that an entry without an announceable room degrades to the approved room-less sentence inside `buildAnnouncement` rather than inventing one.

**Not changed:** `pages/queue.js` (already correct — so the approved boundary test that pins `room: entry.room_name` there needed no edit), `delivery.js` (the claim body still carries no room), `controller.js`, `segments.js`, the backend serializer, the room snapshot rules, and the queue call/permission paths. No second room key was introduced: `entry.room` is now read **nowhere**, and a test asserts that.


### 5.3 INT-3b — the Bangla sentence now names the room in Bangla digits

Writing the required "Bangla with room" test exposed a second, content-level gap. The approved sentence is `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।`, and the existing content test only ever exercised it with the room **already** in Bangla digits (`room: '৩০৫'`). The backend, however, sends `room_name: '305'` (an ASCII room name from the database), and `buildAnnouncement` localised only the token number — so the Bangla *text* came out as `কক্ষ 305-এ আসুন।` while the *prerecorded* path was already correct (it converts the room to `bn.digit.*` clips).

`frontend/lib/announcements/content.js` now localises the room's digits for the rendered text, exactly as it already did for the token number:

```js
  const spokenRoom = lang === 'bn' ? toBanglaDigits(room) : room;
```

`fields.room` still carries the payload's own value, so `segments.js` (which normalises either representation through `digitsOf`) and every other caller are unaffected, and the existing approved-content test that passes `'৩০৫'` still passes unchanged. This changes no wording decision — it makes the code produce the approved wording it was already documenting.

### 5.4 Regression tests added (`queue-announcement-room.test.mjs`, 12 tests)

Driven through the **real** `createCallAnnouncer` + **real** `createAnnouncementController` (with a fake transport, as the W2 integration suite does), so the assertions are about what the page does, not about a helper's isolated output. The fixture is the exact backend shape (`_entry_to_dict`): `room_name: '305'`, `room_id`, `location_label`, `room_source: 'appointment_snapshot'`.

| # | Test | Asserts |
|---|---|---|
| 1 | automatic, English, with room | `player.play({token, room: '305'})`; text `Token number 4, please proceed to Room 305.`; outcome `completed` reported; claim body unchanged (no `room` key) |
| 2 | automatic, Bangla, with room | text `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।` |
| 3 | automatic, English, `room_name: ''` | `Token number 4, please come to the front.`; `room: ''` |
| 4 | automatic, Bangla, `room_name: ''` | `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` |
| 5 | automatic, **missing** `room_name` | room-less sentence; still announced |
| 6 | automatic, **null** `room_name` | room-less sentence |
| 7 | automatic, stale `room` placeholder | `{room: '999', room_name: '305'}` speaks **305**; `room: '999'` alone speaks the **room-less** sentence |
| 8 | operator repeat, English | same room, same sentence; a second deliberate repeat is not suppressed (2 plays) |
| 9 | operator, Bangla with/without room | both approved Bangla sentences |
| 10 | operator, missing room field | still announces the room-less sentence |
| 11 | both call sites | `call-announcer.js` **and** `pages/queue.js` both read `room: entry.room_name`, and neither contains `room: entry.room,` |
| 12 | the four approved sentences | exact strings for en/bn × with/without room; no doctor name, honourific or patient identity in any variant |

Test 11 is the source-level guard against the two paths drifting apart again; tests 1–10 are behavioural and go through the actual shipment path, satisfying the "not merely a helper" requirement.

### 5.5 Results

```
cd frontend && node --test tests/queue-announcement-room.test.mjs
12 tests, 12 pass, 0 fail
```

One assertion in this file is deliberately vocabulary-neutral (`['spoken', 'completed'].includes(status)`) so the file does not prejudge **D-6**.

### 5.6 Asset-level runtime proof against the shipped catalogue (not a browser)

The four sentences were resolved through the **real** `segments.js` against the **real** shipped `public/audio/manifest.json`, which is what the prerecorded path actually plays:

| Input | `ok` | missing | approvedText | segments |
|---|---|---|---|---|
| en, room `305` | true | — | `Token number 4, please proceed to Room 305.` | 7 (`prefix + digit + roomPrefix + 3 digits + roomSuffix`) |
| en, no room | true | — | `Token number 4, please come to the front.` | 3 |
| bn, room `305` | true | — | `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।` | 7 (Bangla digit clips `৩ ০ ৫`) |
| bn, no room | true | — | `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` | 3 |

So the catalogue can speak every sentence INT-3 now emits, with no missing asset. What this does **not** prove is that a human hears it — see §9.


---

## 6. Fresh verification — backend

### 6.1 The test environment (isolated, no live data)

| Item | Value |
|---|---|
| Server | disposable `postgres:17` container `que006-fix-pg`, published on `127.0.0.1:55433` only |
| Schema | created **from empty** by `alembic upgrade head` on this tree — no dump, no restored live copy |
| Live stack | not addressed, not read, not written; `amsdp-db-1` (`postgres:16-alpine`) never contacted |
| Interpreter | `.venv/bin/python` (Python 3.14), `AMSDP_DATABASE_URL` pointing at `55433` |

Using an empty schema is a deliberate change from V1.0 (which restored a backup copy): it removes any "the data made it fail" explanation, and it doubles as a migration smoke test from scratch (§8).

### 6.2 Targeted suites

| Suite | Result |
|---|---|
| `organization/tests/test_voice_packs_api.py` + `test_voice_pack_policy.py` | **74 passed**, 1 warning (84.10s) — includes all 13 previously failing W3 tests and the 7 new ones |
| `queuing/tests/` + `tests/test_queue_room_snapshot.py` | **103 passed, 3 failed** (37.07s) — the same three pre-existing queue failures; every room-snapshot test green |
| `frontend` room/announcement tests | see §7 (12 new, all green) |

### 6.3 Full backend suite

```
.venv/bin/python -m pytest backend -q
12 failed, 758 passed, 50 warnings in 995.80s (0:16:35)
```

**770 tests** (V1.0: 763). The +7 are this task's new tests (6 upload-contract, 1 non-disclosure). **13 tests that failed in V1.0 now pass** — all thirteen W3 API tests — and **no test that passed in V1.0 now fails**: the remaining 12 are exactly the 12 non-W3 names from V1.0's 25.

### 6.4 Classification of every remaining failure

| # | Tests | Diagnosis | Class |
|---|---|---|---|
| 9 | `doctor/tests/test_doctor.py` (`TestDoctorCreate`, `TestDoctorSearch` ×3, `TestDoctorReadUpdate` ×5) | `409 — "a doctor with this mobile number already exists"`. The module's fixture creates doctors on a **fixed mobile number** and does not purge them, so the second and later tests in the class collide. Reproduced on a **clean** schema, so it is test isolation, not data and not this merge. | **Pre-existing test defect** (V1.0 **B-5**), unrelated to QUE-006 |
| 2 | `test_doctor_cannot_call_without_queue_manage`, `test_successful_call_publishes_a_server_event_id` | `status_history` now contains the `'' → waiting` creation row (1, not 0) and the call-event identity is `…:1` where the test expects `…:0`. Both are **stale expectations** about the event index that W2's server-side identity introduced; the authorisation and event-publishing behaviour under test is not failing. | **Pre-existing expectation drift**, needs an owner decision on the intended index (documented, not changed here) |
| 1 | `test_announcement_failure_cannot_block_the_queue` | `NameError: name 'after' is not defined` — the test body uses an unbound variable. A defect **in the test file**, not in the product. | **Pre-existing test bug** |

Nothing in this list is a merge regression, and nothing in it is caused by the B-1, B-9 or INT-3 changes: all 12 names were already failing in V1.0 and on the pure `origin/hackathon-mvp` worktree (V1.0 §9.3, 29 failures there). The one overlap worth naming explicitly: the two queue expectations concern the `call_event_id` index that INT-3's announcement path consumes, so they are reported for a decision rather than quietly edited to match the code.

**Skipped tests:** none. **Environment-related failures:** none — the schema is clean, so the doctor collisions are fixture logic, not leftover data.

---

## 7. Fresh verification — frontend

### 7.1 Full suite

```
cd frontend && npm test
ℹ tests 353   ℹ pass 344   ℹ fail 9   ℹ cancelled 0   ℹ skipped 0   ℹ todo 0
```

**Compared with V1.0 (341 total / 332 pass / 9 fail):** +12 tests, +12 passes, **the same nine failures**. No test was weakened, skipped, renamed or removed to reach this result, and the 12 new tests are the INT-3 suite in §5.4.

### 7.2 The nine failures are unchanged, and all are D-6

`W2 prerecorded is the default transport when a player is supplied` · `W2 busy and cancelled are passed through unchanged` · `W2 a blocked browser is not hammered without a fresh gesture` · `W2 capability follows the pack, not the browser voice list` · `W2 end to end: spoken is reported only when the final clip ends` · `a blocked browser is not hammered, but a new gesture may recover it` · `activating audio is a gesture, and reports what the browser did` · `an exploding engine is an error outcome, not an exception` · `an unsupported browser is reported, not thrown`.

Every one is an assertion that the controller still says `spoken`/`cancelled`, while F2 made `completed`/`interrupted` canonical and kept the old words as aliases (`speech-synthesis.js::OUTCOME`). That is **D-6**, still open: the merged code is internally consistent (the delivery classifier accepts both spellings), but the two test lineages disagree on the literal. Deciding it changes the persisted `outcome` strings, so it stays where V1.0 left it.

### 7.3 Suites that pass, including everything this task touched

`queue-announcement-room.test.mjs` (new, 12) · `queue-announcement-content.test.mjs` (approved wording, including the Bangla with-room sentence) · `queue-announcement-segments.test.mjs` · `queue-announcement-prerecorded.test.mjs` · `queue-announcement-voice-packs.test.mjs` · `queue-announcement-dedupe.test.mjs` · `queue-announcement-delivery.test.mjs` · `queue-announcements-boundary.test.mjs` (the approved `room: entry.room_name` boundary test, untouched and green) · plus the W2 integration tests that do not assert the contested literal.

### 7.4 Production build

```
cd frontend && npm run build
✓ Compiled successfully
BUILD_EXIT=0
```

The `amsdp-frontend-1` container has no host mounts and runs `npm start` from its own image, so this host-side build cannot reach or disturb the running application.

---

## 8. Migration graph

Re-verified on the same disposable server, from an **empty** database:

| Check | Result |
|---|---|
| `alembic heads` | **one head**: `c4d8e2a91f60` |
| `alembic upgrade head` (empty → head) | 18 revisions applied in order, ending `a7c3f19d2b64 → c4d8e2a91f60` |
| `alembic current` | `c4d8e2a91f60 (head)` |
| Tables created | `voice_packs`, `platform_announcement_config`, `queue_announcement_deliveries` (plus the pre-existing schema) |

The V1.0 correction (re-parenting `a7c3f19d2b64` onto `a9c4e1f7b2d8`) is therefore not just a graph fix on a restored backup: a **fresh installation** now builds one linear chain to a single head. No migration was run against the live Ubuntu database, and none of its data was read or written.

---

## 9. Runtime and browser verification — partly VERIFIED, audible playback **NOT VERIFIED**

No browser was driven, no audio device was used, no second terminal existed, and no service was rebuilt or restarted. What could be verified without them was verified; nothing else is claimed.

| Check | Status | Evidence / reason |
|---|---|---|
| Automatic English announcement **with room** — sentence and room reaching playback | **VERIFIED (unit + asset level)** | Real announcer + real controller: `player.play({token, room: '305'})`, text `Token number 4, please proceed to Room 305.`; real catalogue resolves 7 segments, none missing (§5.6) |
| Automatic Bangla announcement **with room** | **VERIFIED (unit + asset level)** | text `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।`; catalogue resolves 7 clips including `bn.digit` `৩ ০ ৫` |
| Both **no-room** cases | **VERIFIED (unit + asset level)** | approved room-less sentences; 3 segments each, none missing |
| Operator-triggered announcement | **VERIFIED (unit level)** | same room and sentence through the operator payload; a deliberate repeat is not suppressed |
| Missing / null / empty room | **VERIFIED (unit level)** | degrades to the approved room-less sentence; never invents a room |
| Completed-playback reporting | **NOT VERIFIED** end-to-end | the outcome mapping and request shape are unit-tested, but no claim/outcome round trip against a running service was made |
| Duplicate event handling across terminals | **NOT VERIFIED** | needs two browsers and a live claim endpoint |
| Queue operation independent of audio | **VERIFIED (source + unit level)** | the announcement is fire-and-forget; the boundary test proves the click path makes no API call and the seam never awaits |
| Audible playback in a real browser (both languages, all four variants) | **NOT VERIFIED** | requires a served trial build and a human at a speaker |
| W3 permission matrix in a live UI | **NOT VERIFIED** in the browser; the API-level matrix now passes (§3.4) | no browser |
| Tenant isolation end-to-end | **NOT VERIFIED** in the browser; the API-level non-disclosure tests now pass (§3.4, §4.4) | no browser |

**Why no isolated runtime was stood up:** the frontend calls nine live services; a safe trial runtime needs a parallel compose project and a rebuilt image — precisely the rebuild/restart the task forbids. Claiming an audible result would break the evidence standard.

---

## 10. Exact Git state (unchanged branch, nothing committed)

| Item | Value |
|---|---|
| Branch | `trial/que006-windows-ubuntu-merge` (unchanged) |
| `HEAD` | `41ac51a0aea6a4462d3e2356cd5f3e58da57b326` (unchanged) |
| `MERGE_HEAD` | `2fc007a3f7a96639c3df36341c6081cee4d24a48` (unchanged) |
| Merge commit | **none** |
| Conflicts | none outstanding; no conflict markers, `.orig` or `.rej` anywhere |
| Unintended deletions | none — the 163 additions and 13 modifications from V1.0 are still staged, plus this task's files |
| Windows target commit | untouched; `2fc007a` was never amended, rewritten or committed to |
| Ubuntu work recoverable | yes — `wip/que006-ubuntu-preservation` @ `41ac51a`, and the external preservation set in `/home/shomonrobie/amsdp_preservation_20261122/` |
| Website proposal preserved | untouched by this task (nothing outside the files listed below was edited) |
| Documentation index changes | intact, and extended with this report (§11 below) |

**Files changed by this task (staged at the end of the task; no commit):**

| File | Change |
|---|---|
| `backend/organization/voice_packs.py` | B-1 fix (audit reason reads the count) + comment |
| `backend/organization/announcement_config.py` | B-9 fix (selection visibility helper) |
| `backend/organization/tests/test_voice_packs_api.py` | +7 tests (`TestUploadContract`, `TestCrossTenantRefusalsDoNotDisclose`) |
| `frontend/lib/announcements/call-announcer.js` | INT-3 fix (`room: entry.room_name`) + comment |
| `frontend/lib/announcements/content.js` | INT-3b (Bangla room digits in the rendered text) |
| `frontend/tests/queue-announcement-room.test.mjs` | new, 12 tests |
| `docs/implementation/AMSDP_QUE006_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md` | this report |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | unregistered-documents annex extended |

**Final staged state (after the last `git add`):** **178 staged entries** (165 additions, 13 modifications) against `41ac51a`, and **0 unstaged**, 0 untracked — the two additions over V1.0's 176 are the new frontend test file and this report.

**Exported again (additive — nothing overwritten).** V1.0's artefacts (`07_…`, `08_…`) predate this task's fixes, so a complete copy of the *current* resolved tree was written beside them in `/home/shomonrobie/amsdp_preservation_20261122/`:

| Artefact | Contents |
|---|---|
| `10_trial-merge-b1-int3-resolved.patch` | `git diff --cached --binary HEAD` of the whole staged resolved tree vs `41ac51a`, including every file in the table above; **verified with `git apply --check` against a pristine `41ac51a` worktree** (`PATCH_APPLIES`) |
| `11_trial-merge-b1-int3-files.tar.gz` | the same 178 files as a tarball (178 members) |
| `12_final-digests.txt` | SHA-256 of both artefacts, the file count and the exact Git state |

The earlier V1.0 artefacts were left exactly as they were; nothing in the preservation directory was deleted, renamed or rewritten.

---

## 11. Decisions that remain open (unchanged by this task)

Nothing in this task was used to close a product decision. The three the task names explicitly stay exactly where they were, and the four carried over from V1.0 are untouched.

| ID | Question | State after this task |
|---|---|---|
| **D-3** | Is F3's per-event dedupe store integrated, or is `dedupe.js` dead code? | **open.** No dedupe code was touched; the controller's duplicate window behaves exactly as before |
| **D-5** | Documentation index revision numbering (Windows occupied 36–48; the Ubuntu local edits used 36 and 37) | **open.** This report is registered in the *unregistered* annex, claiming no revision number (§14) |
| **D-7** | Does an operator's manual repeat create a separate delivery/audit record? | **open.** The operator path still makes no claim and writes no delivery row, as merged |
| **D-1** | Which baseline has authority for future comparisons | unchanged |
| **D-2** | Close F1 | unchanged |
| **D-4** | Are rooms announced at all? | **unchanged as a decision, but no longer blocked by a code defect.** INT-3 now makes the automatic path honour whatever the payload carries, and `pages/queue.js` still holds the single line to revert if rooms are to stay unannounced (V1.0 §7.2) |
| **D-6** | Outcome vocabulary (`completed`/`interrupted` vs `spoken`/`cancelled`) | **open, and now the only thing keeping the frontend suite red** — nine tests |

---

## 12. Remaining blockers and risks

| ID | Risk / blocker | Severity | Owner |
|---|---|---|---|
| ~~**B-1**~~ | ~~voice-pack upload `TypeError`, 13 W3 tests failing~~ | **closed** — fixed and regression-tested (§3) | — |
| ~~**B-9**~~ | ~~cross-tenant selection disclosed `pack_foreign_organization`~~ | **closed** — fixed and regression-tested (§4) | — |
| ~~**B-3**~~ | ~~INT-3: automatic path cannot speak a room~~ | **closed** as a code defect (§5); the *policy* question stays with **D-4** | — |
| **B-2** | D-6 vocabulary collision: nine frontend tests fail and the persisted `outcome` strings depend on the choice | **High** (audit semantics) | Product Owner decision |
| **B-4** | F3's per-event store not integrated; `dedupe.js` dead code | **Medium** | D-3 |
| **B-5** | Pre-existing test defects: doctor fixture 409 collisions (9), queuing `NameError` and `:0`/`:1` expectations (3) | **Medium** (the suite cannot be a gate yet) | Engineering fix — **not** attempted here, because changing them would mean editing tests to fit the code |
| **B-6** | Index numbering unresolved | **Medium** | D-5 |
| **B-7** | The merge lives in the index only; nothing is committed | **Medium** | Mitigated: re-exported (§10) |
| **B-8** | No browser, speaker or two-terminal evidence | **High** for acceptance | Cannot be closed in this task |
| **B-10** *(new, minor)* | `validate_pack_upload` checks a file's own `checksum` before the manifest's `playbackChecksum`, so a manifest that declares a different checksum than the uploaded bytes is accepted when the file entry also carries a checksum | **Low** (found while writing the invalid-upload test) | Engineering — recorded, deliberately **not** changed: tightening validation is a behaviour change outside B-1's scope |

---

## 13. Evidence status (kept deliberately separate)

| Category | Items |
|---|---|
| **VERIFIED** | All 13 previously failing W3 API tests pass · 74/74 in the W3 API + policy modules · 770 backend tests, 758 pass / 12 fail, the 12 being exactly V1.0's non-W3 names · frontend 353 tests, 344 pass / 9 fail, the same nine as V1.0 · `npm run build` ✓ `Compiled successfully` (exit 0) · one migration head `c4d8e2a91f60` and a clean 18-revision `upgrade head` from an empty database · all four approved sentences resolve against the shipped catalogue with no missing asset (7/3/7/3 segments) · `HEAD`/`MERGE_HEAD`/branch unchanged, no conflict markers, no unstaged difference |
| **IMPLEMENTED** | B-1 fix · B-9 fix · INT-3 fix · INT-3b room-digit localisation · 7 backend regression tests · 12 frontend regression tests · this report · index annex entry |
| **TESTED** | The three targeted backend suites, the full backend suite, the full frontend suite, the new room test file, the production build, the migration chain on a disposable server |
| **NOT VERIFIED** | Every audible item in §9 · end-to-end completion reporting against a server · duplicate handling across two terminals · the W3 permission matrix and tenant isolation **in a browser** (API level verified) · any product-owner acceptance |
| **BLOCKED** | **B-2/D-6** (nine frontend failures) and **B-8** (no runtime evidence) block acceptance; **D-4** decides whether the room sentence ships as now |

---

## 14. Governance and skill compliance (`.clinerules` §6)

**Documents read before planning:** `docs/governance/AMSDP_Docs_Index_V1.0.md` (navigation), then `docs/implementation/AMSDP_QUE006_Trial_Merge_Integration_Report_V1.0.md` (the state to continue), the product decisions in `docs/product/AMSDP_Business_Rules_V1.0.md` and the QUE-006 plan of record it references, plus the code paths themselves. Routing rows applied: *Backend API* and *Multi-tenant data* (B-1, B-9), *Frontend UI* and *Queue / scheduling / workflow* (INT-3), *Database schema* (migration re-check), *Documentation* (§11/§12 — this report and the index).

**Skills:** **none installed** in this workspace (`.clinerules` §5). None was used or claimed; governance documents were applied directly.

**Non-negotiables honoured, with evidence:**
* *Server-side scope from the token* — untouched; `_scope_of` still derives the organisation from the authenticated context, and the new tests confirm a foreign-org upload is a 404 that stores nothing.
* *Cross-tenant access fails closed, non-disclosing* — **strengthened** (§4): a foreign pack and an absent pack now produce byte-identical refusals.
* *Never weaken validation* — the upload still validates everything before writing, still refuses with the complete problem list, and the invalid-input test asserts the 422 together with the absence of a stored row.
* *No silent product decisions* — D-3, D-5 and D-7 are untouched; D-4 and D-6 are explicitly left open; the one behaviour-visible change (Bangla room digits) is presented as conformance to the approved sentence, with the alternative recorded.
* *Audit append-only* — no audit row was deleted or rewritten; the new tests only read the trails.
* *Forward-only migrations* — no migration file was modified in this task; the chain was re-proven from empty.
* *Never claim an unverified capability* — §9 and §13 keep NOT VERIFIED items explicit.
* *No secrets* — no credential, token or key appears in this report; the disposable database's password is a throwaway value created for the container and is not recorded here.
* *No destructive Git, no push, no merge commit, no deployment, no live-DB access, no rebuild/restart* — verified in §10 and §12.

**Deviations, declared:**
1. A **third defect (B-9)** was fixed beyond the two the task names. It fails an approved test and violates a `.clinerules` §3 non-negotiable, and it was invisible until B-1 was fixed; leaving it would have meant leaving a known cross-tenant disclosure in the tree.
2. **INT-3b** changed `content.js` (Bangla room digits). It is not a wording change — it makes the rendered Bangla text match the already-approved sentence the task quotes verbatim.
3. A disposable `postgres:17` container was used again for the suites and stopped afterwards. It shares no volume, port or credential with the live stack.
4. This report is **new** rather than an edit of V1.0, so V1.0 remains an accurate record of the state before these fixes. Both are registered in the index annex, unnumbered, pending D-5.
5. Exports were added under new file names (`10_…`, `11_…`, `12_…`); no existing artefact was replaced.

**Report location:** `docs/implementation/AMSDP_QUE006_Trial_Merge_Fixes_B1_INT3_Verification_Report_V1.0.md` — collision-checked before writing; no document was moved or renamed, so no migration-manifest entry is required.


---

## 15. Recommendation

**Ready for Product Owner acceptance review as a *base*; not ready to commit, deploy or call accepted.**

* **What changed for the better:** the entire W3 voice-configuration API surface now works and is regression-tested (B-1); a cross-tenant disclosure is closed (B-9); the automatic and operator room paths finally agree, so all four approved sentences are produced by the real code (INT-3/INT-3b); and the backend suite lost 13 failures and gained none (`758/770`), while the frontend stayed exactly at its nine D-6 failures (`344/353`) with 12 new passes.
* **What still stands between this tree and a merge commit:** **D-6** (nine frontend tests, and the persisted outcome strings), **D-4** (whether rooms are spoken at all — the code now honours the payload either way), **B-8** (no browser/speaker/two-terminal evidence), and the pre-existing test defects in **B-5** that keep the suite from being a trustworthy gate.
* **Minimum bar before any merge commit:** settle D-6 and D-4; fix B-5's test defects (or record them as accepted debt); run the browser/audio checklist in §9 on a parallel stack; then re-run both suites and the build against the final resolved state.

**Nothing further was done:** no commit, no push, no deployment, no live migration, no rebuild or restart, and no declaration that the trial merge is accepted.

---

## 16. Reproducing this verification

```bash
# isolated database (never the live one)
docker run -d --name que006-fix-pg -p 127.0.0.1:55433:5432 \
  -e POSTGRES_USER=amsdp -e POSTGRES_PASSWORD=<throwaway> -e POSTGRES_DB=amsdp postgres:17
export AMSDP_DATABASE_URL='postgresql+psycopg2://amsdp:<throwaway>@127.0.0.1:55433/amsdp'
(cd backend && ../.venv/bin/alembic heads && ../.venv/bin/alembic upgrade head)

# targeted suites
.venv/bin/python -m pytest backend/organization/tests/test_voice_packs_api.py \
  backend/organization/tests/test_voice_pack_policy.py -q
.venv/bin/python -m pytest backend/queuing/tests/ backend/tests/test_queue_room_snapshot.py -q
# full suite
.venv/bin/python -m pytest backend -q

# frontend
(cd frontend && node --test tests/queue-announcement-room.test.mjs && npm test && npm run build)

docker stop que006-fix-pg && docker rm que006-fix-pg
```

**Final Git state:** branch `trial/que006-windows-ubuntu-merge`, `HEAD` `41ac51a`, `MERGE_HEAD` `2fc007a`, everything staged, **no merge commit, no push, no deployment**.


