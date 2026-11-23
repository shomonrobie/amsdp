# AMSDP QUE-006 — Doctor Name Removal and Audio Catalogue Implementation Report

**Document ID:** `QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md`
**Version:** V1.0
**Date:** 2026-11-20
**Task:** QUE-006 — Remove doctor names and create audio generation catalogue
**Branch:** `hackathon-mvp`
**Working tree at start:** All pre-existing local changes preserved; nothing overwritten, staged, committed, or pushed.

---

## 1. Executive summary

This task completes two QUE-006 corrections:

1. **Doctor names removed** from all English and Bangla announcement templates and logic. The four owner-approved sentences are implemented verbatim. Doctor information is preserved in all unrelated UI, queue data, appointment records, and other functionality.
2. **Audio generation catalogue created** at `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` listing all 28 recording assets required by the implemented announcement composition strategy, with exact filenames, asset IDs, destination folders, and recording instructions.

Local prerecorded audio playback is **not yet implemented** — the current mechanism remains browser speech synthesis (`window.speechSynthesis`). The catalogue is a preparation specification.

---

## 2. Repository baseline and working-tree preservation

- **Branch:** `hackathon-mvp`
- **Working-tree preservation:** All pre-existing modified and untracked files were left exactly as found. No file owned by another workstream was touched. No `git reset`, `git stash`, `git checkout .`, or destructive operation was performed. Nothing was staged, committed, or pushed.
- **Pre-existing test failures:** 2 failures unrelated to announcements (banglanamesense-dataset hash mismatch, calendar-render) were present before this task and remain unchanged.

---

## 3. Files changed

| File | Change |
|---|---|
| `frontend/lib/announcements/content.js` | Removed `{doctor}` slot and `Dr.`/`ডা.` from all templates; removed `doctorName` extraction and `missing_doctor_name` refusal; removed `{doctor}` replacement; removed `doctorName` from `fields`; updated JSDoc and header comment |
| `frontend/tests/queue-announcement-content.test.mjs` | Updated all test expectations to approved wording (doctor removed); added 4 new tests: missing doctor name does not prevent generation, doctor name/honourific never appear, plus updated with-room/without-room tests for both languages |
| `frontend/tests/queue-announcement-controller.test.mjs` | Removed `doctorName` from `ENTRY` test fixture |
| `frontend/pages/queue.js` | Removed `doctorName: entry.doctor_name` from `announceEntry` call |
| `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` | **New** — complete audio generation catalogue (28 assets) |
| `docs/implementation/QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md` | **New** — this report |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Registered both new documents (Revision 36) |

---

## 4. Exact before/after announcement wording

### English — with room

| Before (OD-3, with doctor) | After (doctor removed) |
|---|---|
| `Token number {number}, Dr. {doctor}, Room {room}.` | `Token number {number}, please proceed to Room {room}.` |
| Example: `Token number 4, Dr. Rahim Uddin, Room 305.` | Example: `Token number 4, please proceed to Room 305.` |

### English — without room

| Before (OD-3, with doctor) | After (doctor removed) |
|---|---|
| `Token number {number}, Dr. {doctor}.` | `Token number {number}, please come to the front.` |
| Example: `Token number 4, Dr. Rahim Uddin.` | Example: `Token number 4, please come to the front.` |

### Bangla — with room

| Before (OD-3, with doctor) | After (doctor removed) |
|---|---|
| `টোকেন নম্বর {number}, ডা. {doctor}, কক্ষ {room}-এ আসুন।` | `টোকেন নম্বর {number}, কক্ষ {room}-এ আসুন।` |
| Example: `টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।` | Example: `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।` |

### Bangla — without room

| Before (OD-3, with doctor) | After (doctor removed) |
|---|---|
| `টোকেন নম্বর {number}, ডা. {doctor}, আসুন।` | `টোকেন নম্বর {number}, অনুগ্রহ করে সামনে আসুন।` |
| Example: `টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, আসুন।` | Example: `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` |

---

## 5. Confirmation that doctor names are absent from generated announcements

**IMPLEMENTED and TESTED.** The `buildAnnouncement()` function no longer reads `doctorName` from input, does not check for its presence, and never interpolates it into the spoken text. The `fields.doctorName` property has been removed. All four doctor-name input variants tested (`Dr. Rahim Uddin`, `Rahim Uddin`, `ডা. রহিম উদ্দিন`, `ডাক্তার রহিম উদ্দিন`) produce announcements with no doctor name or honourific. Doctor information is preserved in queue data, appointment records, and the UI — only the spoken announcement excludes it.

---

## 6. Catalogue location and complete asset inventory

**Location:** `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md`

**Complete asset inventory (28 assets):**

| Category | English | Bangla | Total |
|---|---|---|---|
| Fixed phrases | 4 | 4 | 8 |
| Digit recordings (0–9) | 10 | 10 | 20 |
| **Grand total** | **14** | **14** | **28** |

Every asset includes: Asset ID, Language, Spoken text, Filename, Destination folder, Audio format, Voice instructions, Usage, Required/Optional. No doctor name, title or honourific recording is included.

---

## 7. Number ranges and composition rules

**Implementation gap identified:** The code has no explicitly bounded supported range for room numbers. Token serials are capped at 9 digits (`MAX_SERIAL_DIGITS = 9`).

**Composition rules:**
- Token number: trailing digit group extracted, leading zeros stripped, each digit spoken individually
- Bangla token number: ASCII digits converted to Bangla digits (`০`–`৯`), each spoken individually
- Room number: each digit spoken individually (same digit recordings as token numbers)
- Bangla room locative: `-এ` appended as part of `bn.phrase.room-locative`
- No separator between digit clips

**Recommendation for owner approval:** Token serials 1–999, room numbers 1–999.

---

## 8. Audio folder structure

**Proposed (not yet implemented):**

```
public/audio/
  en/
    phrase/
      token-number.wav
      proceed-to-room.wav
      room-suffix.wav
      no-room.wav
    number/
      digit-0.wav  through  digit-9.wav
  bn/
    phrase/
      token-number.wav
      room-prefix.wav
      room-locative.wav
      no-room.wav
    number/
      digit-0.wav  through  digit-9.wav
```

All paths relative to application root. WAV master; MP3 for playback.

---

## 9. Manifest and validation implementation

**NOT IMPLEMENTED.** The current implementation has no manifest, no asset loader, no checksum requirements, and no missing-file detection. All audio is generated by browser speech synthesis. The catalogue documents the recommended manifest schema (`public/audio/manifest.json`) and validation behavior for future implementation.

---

## 10. AI recording generation workflow

Documented in §7 of the catalogue. Requires AI audio-generation tool access, human review (particularly Bangla pronunciation), WAV masters and MP3 playback files, manifest creation, and asset validation. Not yet executed.

---

## 11. Demo replay workflow

Documented in §7 of the catalogue. Nine steps from generating clips to confirming actual recordings are played. Cannot be completed until local prerecorded audio playback is implemented.

---

## 12. Tests run and actual results

**Command:** `cd frontend && node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test tests/queue-announcement-*.test.mjs`

**Results: 48/48 pass, 0 fail.**

| Test file | Tests | Pass | Fail |
|---|---|---|---|
| `queue-announcement-content.test.mjs` | 15 | 15 | 0 |
| `queue-announcement-controller.test.mjs` | 15 | 15 | 0 |
| `queue-announcement-speech.test.mjs` | 18 | 18 | 0 |
| **Total** | **48** | **48** | **0** |

**Broader suite:** Full frontend suite was 217/229 pass before this task (2 pre-existing failures unrelated to announcements). Announcement-specific tests all pass.

---

## 13. Browser/device verification status

**NOT VERIFIED.** No browser or device playback run was performed. The announcement mechanism is unit-tested but not verified audible on any device. Local prerecorded audio playback is **not implemented** — the current mechanism remains browser speech synthesis (`window.speechSynthesis`).

---

## 14. Remaining limitations and blockers

| Item | Status | Details |
|---|---|---|
| Local prerecorded audio playback | NOT IMPLEMENTED | Browser speech synthesis is the only playback mechanism; no `public/audio/` folder, no asset loader, no manifest |
| Audio asset validation script | NOT IMPLEMENTED | No validation command or script exists |
| Manifest file | NOT IMPLEMENTED | `public/audio/manifest.json` does not exist |
| Audio recordings | NOT GENERATED | 28 assets specified but none recorded |
| Browser/device verification | NOT VERIFIED | No audible playback confirmed on any device |
| Doctor name removal | IMPLEMENTED + TESTED | All four approved sentences implemented; doctor names absent from announcements |

---

## 15. Acceptance checklist

| Criterion | Status | Evidence |
|---|---|---|
| English with-room sentence exact | TESTED | `Token number 4, please proceed to Room 305.` |
| English without-room sentence exact | TESTED | `Token number 4, please come to the front.` |
| Bangla with-room sentence exact | TESTED | `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।` |
| Bangla without-room sentence exact | TESTED | `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` |
| Doctor names absent from announcements | TESTED | 4 input variants tested; no `Dr.`, `Doctor`, `ডা.`, `ডাক্তার` or names in output |
| Announcement works without doctor input | TESTED | Missing doctor name does not block generation |
| Token serial rules preserved | TESTED | `spokenTokenNumber` tests all pass |
| Room and room-less behaviour | TESTED | Both `derived` and non-`derived` paths tested |
| Deduplication behaviour | TESTED | Controller tests all pass (15/15) |
| Room snapshot behaviour | NOT AFFECTED | `queue.js` change only removes `doctorName` from announce payload |
| Audio catalogue created | IMPLEMENTED | 28 assets documented at `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` |
| Asset validation implemented | NOT IMPLEMENTED | No validator exists yet |
| Prerecorded audio playback implemented | NOT IMPLEMENTED | Browser speech synthesis only |
| Browser/device verification | NOT VERIFIED | No audible playback run performed |

**Overall:** Doctor name removal is IMPLEMENTED, TESTED, and the four approved sentences are verified. Audio catalogue is IMPLEMENTED as a specification. Local prerecorded audio playback, asset validation, and browser verification are NOT IMPLEMENTED / NOT VERIFIED. Nothing is ACCEPTED (acceptance is a Product Owner act).