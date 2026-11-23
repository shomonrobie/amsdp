# AMSDP QUE-006 — Audio Generation Catalogue

**Document ID:** `QUE-006_AUDIO_GENERATION_CATALOGUE.md`
**Version:** V1.0
**Date:** 2026-11-20
**Task:** QUE-006 — Remove doctor names and create audio generation catalogue
**Branch:** `hackathon-mvp`
**Status:** PREPARATION SPECIFICATION — recordings not yet generated; local prerecorded audio playback not yet implemented

---

## 1. Source and basis

This catalogue is derived from the actual implemented announcement code in
`frontend/lib/announcements/content.js`. The composition strategy is:

- Templates use two slots only: `{number}` (token serial) and `{room}` (optional room number).
- The doctor's name and honourific (`Dr.`, `ডা.`, `ডাক্তার`) have been removed from all templates.
- Numbers are spoken digit by digit: `spokenTokenNumber()` extracts the trailing serial, and `toBanglaDigits()` converts each ASCII digit to its Bangla equivalent.
- Room numbers are spoken as the same digit sequence; Bangla appends the locative suffix `-এ`.

**Approved wording (verbatim):**

| Language | With room | Without room |
|---|---|---|
| English | `Token number 4, please proceed to Room 305.` | `Token number 4, please come to the front.` |
| Bangla | `টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।` | `টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।` |

No doctor name, title or honourific recording appears anywhere in this catalogue.

---

## 2. Complete asset inventory

### 2.1 Fixed announcement phrases

| Asset ID | Language | Spoken text | Filename | Destination folder | Format | Voice instructions | Usage | Required? |
|---|---|---|---|---|---|---|---|---|
| `en.phrase.token-number` | English | `Token number ` | `en/phrase/token-number.wav` | `public/audio/en/phrase/` | WAV (master), MP3 (playback) | Clear British English, professional hospital announcement voice, calm neutral intelligible | Prefix before token number in all English announcements | Required |
| `en.phrase.proceed-to-room` | English | `, please proceed to Room ` | `en/phrase/proceed-to-room.wav` | `public/audio/en/phrase/` | WAV (master), MP3 (playback) | Same as above | Between token number and room number in English with-room announcements | Required |
| `en.phrase.room-suffix` | English | `.` | `en/phrase/room-suffix.wav` | `public/audio/en/phrase/` | WAV (master), MP3 (playback) | Same as above | Terminal full stop after room number in English with-room announcements | Required |
| `en.phrase.no-room` | English | ` please come to the front.` | `en/phrase/no-room.wav` | `public/audio/en/phrase/` | WAV (master), MP3 (playback) | Same as above | Complete suffix in English no-room announcements | Required |
| `bn.phrase.token-number` | Bangla | `টোকেন নম্বর ` | `bn/phrase/token-number.wav` | `public/audio/bn/phrase/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla, professional hospital announcement voice, calm neutral clearly articulated | Prefix before token number in all Bangla announcements | Required |
| `bn.phrase.room-prefix` | Bangla | `, কক্ষ ` | `bn/phrase/room-prefix.wav` | `public/audio/bn/phrase/` | WAV (master), MP3 (playback) | Same as above | Between token number and room number in Bangla with-room announcements | Required |
| `bn.phrase.room-locative` | Bangla | `-এ আসুন।` | `bn/phrase/room-locative.wav` | `public/audio/bn/phrase/` | WAV (master), MP3 (playback) | Same as above | Locative suffix after room number in Bangla with-room announcements | Required |
| `bn.phrase.no-room` | Bangla | `, অনুগ্রহ করে সামনে আসুন।` | `bn/phrase/no-room.wav` | `public/audio/bn/phrase/` | WAV (master), MP3 (playback) | Same as above | Complete suffix in Bangla no-room announcements | Required |

### 2.2 Token-number and room-number digit components (English)

Each digit 0–9 requires an individual recording. Numbers are composed digit by digit (e.g. `305` = `3` + `0` + `5`).

| Asset ID | Language | Spoken text | Filename | Destination folder | Format | Voice instructions | Usage | Required? |
|---|---|---|---|---|---|---|---|---|
| `en.digit.0` | English | `zero` | `en/number/digit-0.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 0 in token and room numbers | Required |
| `en.digit.1` | English | `one` | `en/number/digit-1.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 1 in token and room numbers | Required |
| `en.digit.2` | English | `two` | `en/number/digit-2.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 2 in token and room numbers | Required |
| `en.digit.3` | English | `three` | `en/number/digit-3.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 3 in token and room numbers | Required |
| `en.digit.4` | English | `four` | `en/number/digit-4.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 4 in token and room numbers | Required |
| `en.digit.5` | English | `five` | `en/number/digit-5.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 5 in token and room numbers | Required |
| `en.digit.6` | English | `six` | `en/number/digit-6.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 6 in token and room numbers | Required |
| `en.digit.7` | English | `seven` | `en/number/digit-7.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 7 in token and room numbers | Required |
| `en.digit.8` | English | `eight` | `en/number/digit-8.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 8 in token and room numbers | Required |
| `en.digit.9` | English | `nine` | `en/number/digit-9.wav` | `public/audio/en/number/` | WAV (master), MP3 (playback) | Clear British English | Digit 9 in token and room numbers | Required |

### 2.3 Token-number and room-number digit components (Bangla)

Each Bangla digit ০–৯ requires an individual recording. Numbers are composed digit by digit (e.g. `৩০৫` = `৩` + `০` + `৫`).

| Asset ID | Language | Spoken text | Filename | Destination folder | Format | Voice instructions | Usage | Required? |
|---|---|---|---|---|---|---|---|---|
| `bn.digit.0` | Bangla | `০` | `bn/number/digit-0.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ০ in token and room numbers | Required |
| `bn.digit.1` | Bangla | `১` | `bn/number/digit-1.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ১ in token and room numbers | Required |
| `bn.digit.2` | Bangla | `২` | `bn/number/digit-2.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ২ in token and room numbers | Required |
| `bn.digit.3` | Bangla | `৩` | `bn/number/digit-3.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৩ in token and room numbers | Required |
| `bn.digit.4` | Bangla | `৪` | `bn/number/digit-4.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৪ in token and room numbers | Required |
| `bn.digit.5` | Bangla | `৫` | `bn/number/digit-5.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৫ in token and room numbers | Required |
| `bn.digit.6` | Bangla | `৬` | `bn/number/digit-6.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৬ in token and room numbers | Required |
| `bn.digit.7` | Bangla | `৭` | `bn/number/digit-7.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৭ in token and room numbers | Required |
| `bn.digit.8` | Bangla | `৮` | `bn/number/digit-8.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৮ in token and room numbers | Required |
| `bn.digit.9` | Bangla | `৯` | `bn/number/digit-9.wav` | `public/audio/bn/number/` | WAV (master), MP3 (playback) | Native Bangladeshi Bangla | Digit ৯ in token and room numbers | Required |

---

## 3. Number coverage

### 3.1 Supported ranges

The implementation in `frontend/lib/announcements/content.js` has **no explicitly bounded supported range**. The constraints are:

- `MAX_SERIAL_DIGITS = 9` — a token serial longer than 9 digits is refused (`unspeakable_token`).
- Token serials are extracted as the trailing digit group from tokens like `T-3F2A9C-004` → `4`.
- Room numbers are passed through as free text (cleaned of whitespace) and spoken as-is, digit by digit.
- UUIDs and 32-character hex strings are refused as internal identifiers.

Because the implementation composes numbers digit by digit using individual digit recordings, **any number within the 9-digit serial limit can be pronounced** as long as all 10 digit recordings exist for the language.

### 3.2 Implementation gap

The code has no clearly bounded supported range for room numbers. Room numbers are treated as free text with no length limit enforced. The token serial is capped at 9 digits.

**Recommendation for owner approval:** Adopt a concrete supported range of:
- Token serials: 1–999 (1 to 3 digits), matching the `MAX_SERIAL_DIGITS = 9` upper bound with a practical operational limit.
- Room numbers: 1–999 (1 to 3 digits), consistent with typical hospital room numbering.

This requires digit recordings 0–9 only (10 per language), which this catalogue provides. No compound-number recordings (e.g. "twenty", "thirty") are needed because the implementation speaks digits individually.

### 3.3 Composition rules

| Aspect | Rule |
|---|---|
| Token number | Extract trailing digit group from token; strip leading zeros; speak each digit individually |
| Bangla token number | Convert each ASCII digit to Bangla digit (`০`–`৯`); speak each Bangla digit individually |
| Room number | Speak each digit individually (English) or each Bangla digit individually (Bangla) |
| Bangla room locative | Append `-এ` (as part of `bn.phrase.room-locative`) after the room digits |
| Number separator | No separator between digit clips; clips are concatenated directly |

---

## 4. Recording instructions

### 4.1 English prompts

For every English clip, use an AI audio-generation prompt equivalent to:

> "Record a single spoken phrase in clear, natural British English. Professional hospital announcement voice. Calm, neutral, and intelligible delivery. No background music, no sound effects, no artificial reverberation. No extra spoken words before or after the phrase. Consistent loudness and recording quality across all clips. One clip per asset ID. WAV master preferred (44.1 kHz / 16-bit PCM or better)."

### 4.2 Bangla prompts

For every Bangla clip, use an AI audio-generation prompt equivalent to:

> "Record a single spoken phrase in native Bangladeshi Bangla pronunciation. Professional hospital announcement voice. Calm, neutral, and clearly articulated delivery. No background music, no sound effects, no artificial reverberation. No extra spoken words before or after the phrase. Consistent loudness and recording quality across all clips. One clip per asset ID. WAV master preferred (44.1 kHz / 16-bit PCM or better)."

### 4.3 General requirements (all clips)

- No background music.
- No sound effects.
- No artificial reverberation.
- No extra spoken words.
- One clip per asset ID.
- Consistent loudness and recording quality.
- WAV master preferred; the playback format required by the implementation is MP3 (see §5).
- Generated recordings require human review, particularly Bangla pronunciation, before being approved for production use.

---

## 5. Destination folder structure

The current implementation uses **browser speech synthesis** (`window.speechSynthesis`) via `frontend/lib/announcements/speech-synthesis.js`. There is **no existing audio asset structure** in the codebase — no `public/audio/` folder, no asset loader, no manifest, and no pre-recorded audio playback.

This catalogue proposes the following folder structure for when pre-recorded audio is implemented:

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

All paths are relative to the application root (`e:/amsdp/`).

WAV files are the master format. MP3 versions should be generated for playback (smaller file size, broader browser support). The implementation will need an asset-loading layer that maps asset IDs to these filenames.

---

## 6. Manifest and validation requirements

### 6.1 Current state

The current implementation has **no manifest, no asset loader, no checksum requirements, and no missing-file detection**. All audio is generated by the browser's Web Speech API. The catalogue is therefore a **preparation specification**.

### 6.2 Recommended manifest (for future implementation)

When pre-recorded audio is implemented, a manifest file should be created at:

`public/audio/manifest.json`

**Suggested schema:**

```json
{
  "version": "1.0",
  "locales": ["en", "bn"],
  "assets": [
    {
      "id": "en.phrase.token-number",
      "language": "en",
      "category": "phrase",
      "filename": "en/phrase/token-number.mp3",
      "spokenText": "Token number ",
      "required": true,
      "checksum": "sha256:..."
    },
    ...
  ]
}
```

**Asset ID-to-filename mapping:** Each asset ID maps to exactly one filename under `public/audio/`.

**Required metadata:** `id`, `language`, `category`, `filename`, `spokenText`, `required`, `checksum`.

**Checksum requirements:** SHA-256 of the MP3 file, to detect corruption or tampering.

**Supported file formats:** WAV (master), MP3 (playback).

**Missing-file detection:** The validator must check that every `required: true` asset has a corresponding file on disk.

**Invalid-file detection:** The validator must verify each file's checksum matches the manifest.

### 6.3 Validation command

A validation script should be implemented (future work) that:

1. Reads `public/audio/manifest.json`.
2. For each required asset, checks the file exists at `public/audio/<filename>`.
3. For each asset with a checksum, verifies SHA-256.
4. Reports missing required recordings clearly.
5. **Never** reports an incomplete catalogue as ready.

---

## 7. Demo workflow

### Prerequisites

- AI audio-generation tool access (for generating clips from the prompts in §4).
- The AMSDP frontend running locally (`next dev` in `e:/amsdp/frontend/`).

### Steps

1. **Generate audio clips:** Use the prompts in §4 to generate each recording listed in §2. One clip per asset ID.
2. **Download clips:** Save each generated clip as WAV master (and derive MP3 for playback).
3. **Save under documented folders:** Place files under `public/audio/<language>/<category>/` as specified in §5.
4. **Create manifest:** Write `public/audio/manifest.json` with the schema in §6.2.
5. **Run asset validation:** Execute the validation script (to be implemented) to confirm all required recordings are present and valid.
6. **Load or refresh the catalogue:** The frontend announcement layer must be extended to load the manifest and map asset IDs to audio files (future work — currently not implemented).
7. **Open the AMSDP demo:** Navigate to the `/queue` page in a browser.
8. **Test English and Bangla announcements:** With and without rooms, confirm that actual recordings are played.
9. **Confirm actual recordings are played:** Verify that the audio output matches the recorded clips, not browser speech synthesis.

### Important limitation

**The local prerecorded-audio engine is not yet implemented.** The current implementation uses browser speech synthesis (`window.speechSynthesis`). This catalogue is a **preparation specification** for the recording assets. Actual local recording playback remains outstanding. Do not pretend it is already supported, and do not silently fall back to browser speech synthesis or placeholder audio and claim that local recordings were successfully tested.

---

## 8. Asset count

| Category | English | Bangla | Total |
|---|---|---|---|
| Fixed phrases | 4 | 4 | 8 |
| Digit recordings (0–9) | 10 | 10 | 20 |
| **Grand total** | **14** | **14** | **28** |

**28 recording assets** are listed in this catalogue.