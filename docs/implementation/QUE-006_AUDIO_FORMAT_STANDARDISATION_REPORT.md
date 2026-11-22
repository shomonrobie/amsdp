# AMSDP QUE-006 — Audio Format Standardisation, Conversion and Validation Report

**Document ID:** `QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md`
**Version:** V1.1 — adds §17: the one missing Bangla recording was supplied and converted
**Date:** 2026-11-21
**Task:** QUE-006 — audio format standardisation, conversion and validation
**Branch:** `hackathon-mvp`
**Status (V1.1):** **COMPLETE** — 28 of 28 assets standardised and technically
validated: 28 WAV masters, 28 MP3 playback files, `manifest.json` summary
`complete: true`, strict validator exit 0 (§17).
**Status (V1.0, superseded):** PARTIALLY COMPLETE — 27 of 28 assets, with
`bn.phrase.room-locative` unrecorded and reported as a gap rather than filled. §17
records how that gap was closed by a real recording. §0–§16 are V1.0 text, left
unedited on purpose: they are the record of what was true when the recording did not
exist, and rewriting them would destroy the evidence that the gap was reported
honestly.

---

## 0. Verdict against the completion criteria (V1.0 — superseded by §0.1)

| # | Criterion (task §12) | Result | Evidence |
|---|---|---|---|
| 1 | All 28 original recordings preserved | **MET** | `frontend/.audio-originals-backup/` — 28 files, copied then re-hashed, 0 mismatches (§2) |
| 2 | All 28 WAV masters exist and pass technical validation | **NOT MET — 27/28** | `bn.phrase.room-locative` has no recording (§8) |
| 3 | All 28 MP3 playback files exist and pass technical validation | **NOT MET — 27/28** | same asset (§8) |
| 4 | Filenames match the required structure | **MET for 27 assets**; the 28th is deliberately absent rather than mislabelled | §5, §9 |
| 5 | The manifest accurately describes all 28 assets | **MET** | 28 entries; 27 `pass`, 1 `missing` with the reason recorded (§7) |
| 6 | All checksums verified | **MET** | 54 SHA-256 values verified against the files (§7) |
| 7 | The validation script runs successfully | **MET** | `validate-audio-assets.mjs` — exit 0 with `--allow-missing`, exit 1 strict (§6, §11) |
| 8 | The implementation report is created | **MET** | this document |

The task is **not** complete in the sense of "28 playable assets exist". It is
complete in the sense of "everything that exists is standardised, validated,
checksummed and documented, and what does not exist is named loudly". Criteria 2
and 3 fail for exactly one asset, and the failure is a **missing recording**, not a
conversion failure: fabricating a Bangla recording, or renaming an English silence
placeholder into the Bangla slot, would have produced a green table and a broken
announcement. That trade was refused (§9, §14 decision D-1).

### 0.1 V1.1 re-verdict — 2026-11-21, after the Bangla recording was supplied

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | All 28 original recordings preserved | **MET** | 29 files preserved and hash-verified, including the newly supplied `bn/phrase/room-locative.mpeg` (§17.3) |
| 2 | All 28 WAV masters exist and pass technical validation | **MET — 28/28** | `validate-audio-assets.mjs` strict: masters 28/28 (§17.5) |
| 3 | All 28 MP3 playback files exist and pass technical validation | **MET — 28/28** | same run: playback 28/28, CBR frame spread ≤ 0.3 kbps |
| 4 | Filenames match the required structure | **MET — 28/28** | `bn/phrase/room-locative.wav` + `.mp3` now exist; the placeholder was still not renamed into the slot |
| 5 | The manifest accurately describes all 28 assets | **MET** | 28 entries, all `technicalValidationStatus: pass`; `complete: true` (§17.4) |
| 6 | All checksums verified | **MET** | 56 SHA-256 values (28 masters + 28 playback) verified against the files (§17.5) |
| 7 | The validation script runs successfully | **MET** | `validate-audio-assets.mjs` **strict** exit 0 — `--allow-missing` not used (§17.5) |
| 8 | The implementation report is created | **MET** | this document, now V1.1 with §17 |

Criterion 2 and 3 were the two that failed in V1.0. They are now met by a **real
recording**, not by a rename, not by synthesis, and not by a tolerance change:
`bn/phrase/room-locative.mpeg` was supplied by the project owner, verified to be an
MP3 stream carrying 1.82 s of speech at a peak of −4.5 dB, and converted.

What remains true regardless of this pass: **no one has listened to any of the 28
clips.** Every `humanReviewStatus` is still `pending`, and prerecorded playback in
the frontend is still unimplemented (§17.7).

---

## 1. Original asset inventory (as found, before any change)

Inspected on disk at the start of the task, not taken from the manifest. The
manifest on disk claimed `ready 1, missing 27` — the filesystem disagreed, which
is the first discrepancy recorded here.

| # | File as found | Bytes | SHA-256 (first 12) | Container / codec | Rate · ch | Duration |
|---|---|---|---|---|---|---|
| 1 | `bn/number/digit-0.m4a` | 34,428 | `16fef484d0ca` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 2 | `bn/number/digit-1.m4a` | 31,288 | `69e6e9b67c72` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 3 | `bn/number/digit-2.m4a` | 31,184 | `7747307758fb` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 4 | `bn/number/digit-3.m4a` | 31,335 | `9a283f450739` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 5 | `bn/number/digit-4.m4a` | 32,154 | `08d4710f40e1` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 6 | `bn/number/digit-5.m4a` | 33,210 | `1bfa877f35b1` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 7 | `bn/number/digit-6.m4a` | 32,874 | `591749e02428` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 8 | `bn/number/digit-7.m4a` | 34,467 | `b3865bd07630` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 9 | `bn/number/digit-8.m4a` | 32,002 | `24a5a5f09f7a` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 10 | `bn/number/digit-9.m4a` | 32,507 | `2c52d3a1363a` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 11 | `bn/phrase/token-number.m4a` | 35,457 | `8bf9453c20f6` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 12 | `bn/phrase/room-prefix.m4a` | 32,320 | `82256e5bf07c` | mp4/m4a · aac | 48,000 · 1 | 1.82 s |
| 13 | `bn/phrase/no-room.m4a` | 40,430 | `fd64abe67b5f` | mp4/m4a · aac | 48,000 · 1 | 2.45 s |
| 14 | `bn/phrase/room-suffix.wav` | 14,444 | `651d0bac16d2` | wav · pcm_s16le | 24,000 · 1 | 0.30 s |
| 15 | `en/number/digit-0.mp3` | 30,311 | `5ac6af88d6b6` | mp3 | 44,100 · 1 | 0.836 s |
| 16 | `en/number/digit-1.mp3` | 27,803 | `29ff080bcffe` | mp3 | 44,100 · 1 | 0.679 s |
| 17 | `en/number/digit-2.mp3` | 26,550 | `5f16330d8c66` | mp3 | 44,100 · 1 | 0.601 s |
| 18 | `en/number/digit-3.mp3` | 30,311 | `2c3281043c0f` | mp3 | 44,100 · 1 | 0.836 s |
| 19 | `en/number/digit-4.mp3` | 31,565 | `1cf823a6a2aa` | mp3 | 44,100 · 1 | 0.914 s |
| 20 | `en/number/digit-5.mp3` | 29,057 | `786f044b250c` | mp3 | 44,100 · 1 | 0.758 s |
| 21 | `en/number/digit-6.mp3` | 30,311 | `e35daaa91af8` | mp3 | 44,100 · 1 | 0.836 s |
| 22 | `en/number/digit-7.mp3` | 29,057 | `7dcdfe40e055` | mp3 | 44,100 · 1 | 0.758 s |
| 23 | `en/number/digit-8.mp3` | 27,803 | `2250cb9083e1` | mp3 | 44,100 · 1 | 0.679 s |
| 24 | `en/number/digit-9.mp3` | 31,565 | `7d26396d3c78` | mp3 | 44,100 · 1 | 0.914 s |
| 25 | `en/phrase/token-number.mp3` | 34,073 | `ddbebc0c7ef1` | mp3 | 44,100 · 1 | 1.071 s |
| 26 | `en/phrase/proceed-to-room.mp3` | 44,522 | `79bf703d9af8` | mp3 | 44,100 · 1 | 1.724 s |
| 27 | `en/phrase/no-room.mp3` | 39,506 | `3c24c1b04ecd` | mp3 | 44,100 · 1 | 1.411 s |
| 28 | `en/phrase/room-suffix.wav` | 14,444 | `651d0bac16d2` | wav · pcm_s16le | 24,000 · 1 | 0.30 s |

**28 files, three formats, and no `room-locative` file at all.** Full hashes and
format facts are preserved in `frontend/.audio-originals-backup/ORIGINALS.json`.

### 1.1 Discrepancies found before conversion (reported, not assumed away)

| ID | Discrepancy | Evidence |
|---|---|---|
| **D-1** | `bn/phrase/room-suffix.wav` is **byte-identical to the English** `en/phrase/room-suffix.wav` — a 300 ms digital-silence placeholder, not a Bangla recording. `bn.phrase.room-locative` (`-এ আসুন।`) therefore **has no audio anywhere**. | identical SHA-256 `651d0bac16d2010f…`; `mean_volume = max_volume = -91.0 dB`; both 14,444 B |
| **D-2** | The manifest on disk claimed `ready 1 / missing 27`; the disk actually held 28 files. | manifest `summary` vs directory listing |
| **D-3** | `ffmpeg`/`ffprobe` are **not on `PATH`** in a fresh shell although 9.1 is installed. | `Get-Command ffmpeg` → nothing; `where.exe` → nothing; `C:\Program Files\WinGet\Links\ffmpeg.exe` → 9.1 |
| **D-4** | All ten Bangla digit clips are **exactly 1.820000 s**, as are `token-number` and `room-prefix`; English digits vary 0.60–0.91 s. | ffprobe durations; `silencedetect` in §6.3 |

Task §5 instructed renaming `bn/phrase/room-suffix.wav` to
`bn/phrase/room-locative.wav`. **That rename was not performed**, because its
premise is false: the file is not a misnamed Bangla locative recording, it is a
copy of the English silence placeholder. The original is preserved under its
original name in the backup, as §5 also requires.

---

## 2. Backup location and verification

**Location:** `frontend/.audio-originals-backup/` — outside `public/`, so it is
never served, and outside the audio directory, so no glob over the served tree can
pick it up. Git-ignored via `.gitignore` (`/frontend/.audio-originals-backup/`).

**Record:** `frontend/.audio-originals-backup/ORIGINALS.json` — one entry per
original with relative path, byte size, SHA-256, container, codec, sample rate,
channels, duration and preservation timestamp; `createdAt`
`2026-11-21T03:52:25.487Z`.

Verification performed by `backupOriginals()` on every run:

1. Copy the file, then **re-hash the copy** — a copy whose SHA-256 differs from the
   source is reported as a failure (`copy-mismatch`), never recorded as preserved.
2. **Never overwrite an existing backup copy.** If the tree's file differs from the
   preserved copy, that is a `conflict` for a human, and the run stops before
   converting anything (exit 4).
3. Only files that existed **before** standardisation enter the record. A delivery
   path created by this utility is never added, and an entry added by an earlier
   version of the pass was pruned once that rule was introduced (§13, defect 3).

**Result of the final run:** `copied+verified 0 · already preserved 27 · conflicts
0 · copy mismatches 0 · unreadable 0`, with **28** entries in the record and **28**
files under the backup root (plus `ORIGINALS.json` and the pre-standardisation
manifest). `validate-audio-assets.mjs` re-checks every preserved copy against its
recorded hash on each run (`every preserved original still verifies` → PASS).

The 28th entry is the superseded `en/phrase/room-suffix.wav`: the 24 kHz original
was replaced in place by its 44.1 kHz master, so its preserved copy is the only
surviving evidence of the original bytes. That is exactly what a backup is for.

Retained in the tree but **not** part of the delivery contract (never deleted, per
§3 "never delete original recordings"): the 13 `bn/**/*.m4a` sources and the
mislabelled `bn/phrase/room-suffix.wav` placeholder.

---

## 3. Conversion tool and version

| Tool | Version | Location | Used for |
|---|---|---|---|
| `ffmpeg` | **9.1-full_build-www.gyan.dev** | `C:\Program Files\WinGet\Links\ffmpeg.exe` | decode → WAV; encode MP3; full-file decode verification; `volumedetect`; `silencedetect` |
| `ffprobe` | **9.1-full_build-www.gyan.dev** | `C:\Program Files\WinGet\Links\ffprobe.exe` | stream facts, durations, per-frame MP3 sizes |

Nothing was downloaded or installed: both tools were already present and are
resolved by `lib/decode.mjs` (PATH first, then the known install directories), so a
stale shell `PATH` cannot make the utility believe ffmpeg is missing. `--dry-run`
works without ffmpeg; a real run refuses to start without it (exit 3) rather than
write files it cannot describe.

---

## 4. Conversion settings and commands

### 4.1 Master (WAV)

```text
ffmpeg -nostdin -y -v error -i <source> -ac 1 -ar 44100 -c:a pcm_s16le -f wav <master>.wav
```

PCM signed 16-bit, 44,100 Hz, mono. Sample-rate conversion is applied only where
the source differs (48 kHz AAC → 44.1 kHz); the English MP3s were already
44.1 kHz. **No** normalisation, noise reduction, pitch shift, time stretch,
trimming or silence removal is applied anywhere.

### 4.2 Playback (MP3)

```text
ffmpeg -nostdin -y -v error -i <master>.wav -ar 44100 -ac 1 -c:a libmp3lame \
       -b:a 128k -map_metadata -1 -f mp3 <playback>.mp3
```

Constant bit rate (libmp3lame writes CBR unless `-q:a` is given), mono, 44.1 kHz.
CBR is *verified*, not assumed: every MPEG frame's implied bit rate is computed
from its packet size, and a spread above 1 kbps across frames reports the file as
VBR. Measured spread for these files: 0.1 kbps — only the padding bit alternating.

### 4.3 Per-asset derivation — the lossy-chain decision

| Language | Source | Master | Playback | Why |
|---|---|---|---|---|
| English (13) | provider MP3, 44.1 kHz, 128 kbps | decode → PCM WAV | **the original MP3, byte-identical** | Decoding then re-encoding an MP3 is a second lossy generation that can only remove information. The file already met the playback contract exactly (measured, not assumed), so it was kept as delivered. |
| Bangla (13) | M4A / AAC 48 kHz | resample → PCM WAV | encoded **from the master** | Required by §4: playback files come from validated masters. |
| `en.phrase.room-suffix` | 24 kHz silent WAV | resample → 44.1 kHz PCM WAV | encoded from the master | In-place rewrite, allowed only after a verified backup existed (temp file → verify → swap). |

This is a deliberate deviation from the literal wording of §4 ("do not generate MP3
from an already compressed source … avoid unnecessary repeated lossy conversions"):
the two instructions conflict for an MP3-only source, and the no-additional-loss
rule was chosen. The resulting playback file is bit-identical to what the provider
delivered; re-encoding it would only have degraded it.

### 4.4 In-place conversion safety

ffmpeg 9.x refuses to read and write the same path (`Output … same as Input`).
Rather than special-casing one asset, `produceSafely()` in
`lib/audio-standard.mjs` writes to a sibling temporary file when
`source === target`, probes that temp file against the contract, and **only then**
renames it over the original. A conversion that produces the wrong format is
discarded and the original keeps its exact bytes.

---

## 5. Final asset inventory

### 5.1 Structure produced

```text
frontend/public/audio/
├── manifest.json
├── en/number/    digit-0..9  .wav + .mp3     (10 assets, 20 files)
├── en/phrase/    token-number, proceed-to-room, room-suffix, no-room  (.wav + .mp3)
├── bn/number/    digit-0..9  .wav + .mp3     (10 assets, 20 files)
└── bn/phrase/    token-number, room-prefix, no-room  (.wav + .mp3)
                  room-locative — ABSENT (no recording exists; see §8)
```

**27 WAV masters and 27 MP3 playback files.** The requirement is 28 of each; the
missing pair is `bn/phrase/room-locative.{wav,mp3}`.

### 5.2 Per-asset result

| Asset ID | Master B | Playback B | Duration | Master SHA-256 (12) | Playback SHA-256 (12) | Content | Derivation |
|---|---|---|---|---|---|---|---|
| `en.phrase.token-number` | 94,542 | 34,073 | 1.071 s | `5711db664564` | `ddbebc0c7ef1` | speech | original-mp3-preserved |
| `en.phrase.proceed-to-room` | 152,142 | 44,522 | 1.724 s | `b85c7834bc95` | `79bf703d9af8` | speech | original-mp3-preserved |
| `en.phrase.room-suffix` | 26,538 | 5,895 | 0.300 s | `e3c2c0c91761` | `32b5c34e085d` | intentional-pause | encoded-from-master |
| `en.phrase.no-room` | 124,494 | 39,506 | 1.411 s | `15337fd6a377` | `3c24c1b04ecd` | speech | original-mp3-preserved |
| `en.digit.0` | 73,806 | 30,311 | 0.836 s | `6138e67f3954` | `5ac6af88d6b6` | speech | original-mp3-preserved |
| `en.digit.1` | 59,982 | 27,803 | 0.679 s | `3523d18bb72a` | `29ff080bcffe` | speech | original-mp3-preserved |
| `en.digit.2` | 53,070 | 26,550 | 0.601 s | `a62f8e25cc19` | `5f16330d8c66` | speech | original-mp3-preserved |
| `en.digit.3` | 73,806 | 30,311 | 0.836 s | `b821bbd5c7ba` | `2c3281043c0f` | speech | original-mp3-preserved |
| `en.digit.4` | 80,718 | 31,565 | 0.914 s | `c2350b8aaa58` | `1cf823a6a2aa` | speech | original-mp3-preserved |
| `en.digit.5` | 66,894 | 29,057 | 0.758 s | `5cff0903646e` | `786f044b250c` | speech | original-mp3-preserved |
| `en.digit.6` | 73,806 | 30,311 | 0.836 s | `47547e0c2522` | `e35daaa91af8` | speech | original-mp3-preserved |
| `en.digit.7` | 66,894 | 29,057 | 0.758 s | `b8ce16cc2dbe` | `7dcdfe40e055` | speech | original-mp3-preserved |
| `en.digit.8` | 59,982 | 27,803 | 0.679 s | `e899f9ade1d2` | `2250cb9083e1` | speech | original-mp3-preserved |
| `en.digit.9` | 80,718 | 31,565 | 0.914 s | `e6782a5d25b8` | `7d26396d3c78` | speech | original-mp3-preserved |
| `bn.digit.0` | 160,602 | 30,137 | 1.820 s | `7a6d422a064e` | `97b9689d0957` | speech | encoded-from-master |
| `bn.digit.1` | 160,602 | 30,137 | 1.820 s | `132626abec96` | `9f6db964d104` | speech | encoded-from-master |
| `bn.digit.2` | 160,602 | 30,137 | 1.820 s | `73df37aa2bf1` | `d5dfca15fd9f` | speech | encoded-from-master |
| `bn.digit.3` | 160,602 | 30,137 | 1.820 s | `ae08cf730e7f` | `54d898712d8f` | speech | encoded-from-master |
| `bn.digit.4` | 160,602 | 30,137 | 1.820 s | `09a9ed355905` | `b5b92842803c` | speech | encoded-from-master |
| `bn.digit.5` | 160,602 | 30,137 | 1.820 s | `65520db27220` | `16f18846ee60` | speech | encoded-from-master |
| `bn.digit.6` | 160,602 | 30,137 | 1.820 s | `fd2df4828ef3` | `90bcf6905f02` | speech | encoded-from-master |
| `bn.digit.7` | 160,602 | 30,137 | 1.820 s | `60cb9e3cc041` | `e3fdd7bb5a3c` | speech | encoded-from-master |
| `bn.digit.8` | 160,602 | 30,137 | 1.820 s | `b4b1b9233173` | `d84e2639a368` | speech | encoded-from-master |
| `bn.digit.9` | 160,602 | 30,137 | 1.820 s | `f298ba78489e` | `f37e9506fed5` | speech | encoded-from-master |
| `bn.phrase.token-number` | 160,602 | 30,137 | 1.820 s | `13a8927edae9` | `b246463d96bb` | speech | encoded-from-master |
| `bn.phrase.room-prefix` | 160,602 | 30,137 | 1.820 s | `06c018c5efe5` | `900edc331d83` | speech | encoded-from-master |
| `bn.phrase.no-room` | 216,168 | 40,168 | 2.450 s | `a935bb5b2dca` | `28bf8c57b038` | speech | encoded-from-master |
| `bn.phrase.room-locative` | — | — | — | — | — | **missing-recording** | — |

Hashes are truncated to 12 hex characters for readability only; the **full 64-hex
values are in `frontend/public/audio/manifest.json`** (`masterChecksum`,
`playbackChecksum`) and were verified against the files byte-for-byte (§7).

---

## 6. WAV and MP3 validation results

Validation is performed by `scripts/que-006-audio/validate-audio-assets.mjs`, which
shares its per-asset evaluation with the manifest writer (`evaluateAsset()` in
`lib/audio-standard.mjs`), so the manifest cannot claim a status the validator would
contradict.

### 6.1 The twelve required checks, as implemented

| # | Required check | Implementation | Result |
|---|---|---|---|
| 1 | All 28 WAV masters exist | `master.exists` per asset | **27/28** (`bn.phrase.room-locative` absent) |
| 2 | All 28 MP3 playback files exist | `playback.exists` per asset | **27/28** (same asset) |
| 3 | Every file is non-empty | `bytes > 0` | PASS for all 54 present files |
| 4 | Every file decodes in ffmpeg | full `ffmpeg -f null -` decode; exit code and stderr checked | PASS 54/54 |
| 5 | Every file has a valid duration | ffprobe duration `> 0` and `≥ 0.05 s` | PASS 54/54 |
| 6 | Sample rate and channel count match | probe vs contract (44,100 Hz, 1 ch) | PASS 54/54 |
| 7 | MP3 files are actually MP3 | container `mp3` + codec `mp3` + CBR frame spread ≤ 1 kbps | PASS 27/27 |
| 8 | WAV files are actually PCM WAV | container `wav` + codec `pcm_s16le` + 16-bit | PASS 27/27 |
| 9 | No expected asset is missing | aggregate of 1 + 2 | **1 missing** (`bn.phrase.room-locative`) |
| 10 | No duplicate asset IDs | 28 unique ids, 56 unique paths, no two speech assets share bytes | PASS |
| 11 | Every manifest path resolves to an existing file | resolves inside `frontend/public/audio/`, exists whenever the entry claims it is present | PASS |
| 12 | SHA-256 checksums match the manifest | 54 values recomputed and compared | PASS 54/54 |

Checks beyond the required list are also reported: manifest `spokenText` equals the
catalogue cell verbatim; `technicalValidationStatus` equals a fresh evaluation;
`humanReviewStatus` is a known value; `playable.integratedWithApplication === false`;
and every preserved original still matches its recorded hash.

### 6.2 Verdicts actually produced

```text
$ node scripts/que-006-audio/validate-audio-assets.mjs            # strict
  assets 27/28 pass · warn 0 · fail 1 · masters 27/28 · playback 27/28
  verdict FAIL — 1 failing item(s) across 28 catalogue assets      exit 1

$ node scripts/que-006-audio/validate-audio-assets.mjs --allow-missing
  assets 27/28 pass · warn 1 · fail 0 · masters 27/28 · playback 27/28
  verdict PASS — 27 masters, 27 playback files; 1 asset absent and treated as pending work
                                                                   exit 0
```

Strict exit code 1 is **correct and intentional**: a missing Bangla clip must not
look like a pass. `--allow-missing` exists for pipelines that need the rest of the
set to proceed, and it still lists the missing asset as pending.

The generation-stage validator is green and honest as well:

```text
$ node scripts/que-006-audio/validate.mjs --allow-missing
  pass 27/28 (96%) · warn 1 · fail 0   verdict PASS            exit 0
```

### 6.3 Measurement notes that are not defects

- **English room suffix is digital silence** — `mean_volume = max_volume = -91.0 dB`
  over 0.300 s, identical before and after standardisation. Analysed in §9.
- **Bangla clips carry ~1 s of trailing silence** (discrepancy D-4), measured with
  `silencedetect=noise=-45dB:d=0.15` on the masters:

  | Asset | Speech ends | File ends | Trailing silence |
  |---|---|---|---|
  | `bn.digit.0` | 0.646 s | 1.820 s | 1.174 s |
  | `bn.digit.1` | 0.441 s | 1.820 s | 1.379 s |
  | `bn.phrase.token-number` | 0.889 s | 1.820 s | 0.931 s |

  All ten Bangla digits plus `token-number` and `room-prefix` are exactly 1.820 s,
  consistent with fixed-length padding at generation time. **Nothing was trimmed**:
  §4 forbids altering timing, and trimming is a content decision rather than a
  format conversion. Raised as open item **O-2** (§14) because a composed Bangla
  announcement will contain roughly one-second pauses between words.

---

## 7. Manifest structure and checksum verification

### 7.1 Structure

`frontend/public/audio/manifest.json` — schema `AMSDP-QUE-006-audio-assets/2.0`,
`version: "2.0"`, `locales: ["en","bn"]`, 28 entries.

Top-level keys: `version`, `schema`, `generatedAt`, `locales`, `formats` (master and
playback contract), `tool` (ffmpeg/ffprobe versions and the two scripts), `catalogue`,
`generator` (carried forward **verbatim** from the previous manifest — no speech was
regenerated), `backup`, `summary`, `playable`, `assets`.

Per asset: `id`, `language`, `category`, `spokenText`, `required`, `usage`,
`masterFile`, `playbackFile`, `masterChecksum`, `playbackChecksum`, `masterFormat`,
`playbackFormat`, `sampleRate`, `channels`, `durationSeconds`, `masterBytes`,
`playbackBytes`, `technicalValidationStatus`, `technicalProblems`, `humanReviewStatus`,
`contentStatus`, `contentIssue`, `notes`, `spokenTextNote`, `origin`,
`playbackDerivation`, `humanReview`.

`spokenText` is the catalogue value verbatim. The one declared deviation
(`en.phrase.no-room`, recorded with a leading comma) is not hidden: `spokenTextNote`
states the recorded text and points at `catalogue.mjs SPOKEN_TEXT_OVERRIDES`, and the
owner decision about it remains open.

### 7.2 Checksum verification

- 27 `masterChecksum` + 27 `playbackChecksum` values recomputed from the files and
  compared: **54/54 match** (`manifest checksums match the files` → PASS).
- Those values were written by the conversion pass from the files it had just
  produced, so the agreement is between two independent reads, not a copy of one.
- The 28 originals carry separate SHA-256 records in `ORIGINALS.json`, and every
  preserved copy is re-verified against them on each validation run.
- `rebuild-audio-manifest.mjs --check` confirms the manifest on disk matches a fresh
  build (`manifest.json is current`), so it has not been hand-edited.

`summary`: `total 28 · masterPresent 27 · playbackPresent 27 · technicalPass 27 ·
technicalMissing 1 · technicalFail 0 · contentIssues 1 · humanApproved 0 ·
humanPending 28 · complete false`.

`playable`: `readyForPlaybackEngine false` (one asset missing),
`integratedWithApplication false`, `humanReviewOutstanding true`.

---

## 8. Missing and failed assets

| Asset | Status | Cause | What would fix it |
|---|---|---|---|
| `bn.phrase.room-locative` | **missing** (master and playback) | No recording of `-এ আসুন।` exists anywhere in the tree. The only candidate, `bn/phrase/room-suffix.wav`, is byte-identical to the English silence placeholder (D-1). | Record the Bangla locative suffix with the same voice as the other Bangla clips, save it as `bn/phrase/room-locative.wav`, then run `standardise-audio.mjs`. The pipeline will convert it, manifest it and validate it with no code change. |

**Conversion failures: none.** 27 of 27 required conversions succeeded, and a
second identical run changed **no audio bytes** (idempotency verified by hashing the
whole tree before and after).

No asset was marked `fail`. The distinction matters: `missing` means "no recording
exists", `fail` means "a file exists but is wrong".

---

## 9. English room suffix assessment

The catalogue describes `en.phrase.room-suffix` as the full stop `.`, i.e. a
punctuation-only asset, and `catalogue.mjs` marks it `synthetic: 'silence'` with a
300 ms pause constant.

**Inspection of the recording, before and after standardisation:**

| Property | Value |
|---|---|
| Duration | 0.300 s |
| `mean_volume` | **−91.0 dB** |
| `max_volume` | **−91.0 dB** |
| Sample content | PCM silence (no sound event at all) |
| After conversion | 0.300 s, 44,100 Hz, 16-bit, mono, 26,538 B — still exactly −91.0 dB |

**Assessment: intentional short pause, retained.** Per task §6 this is the "only
silence or an intentional short pause" case: the file is kept as a short pause asset,
not replaced, and no speech was synthesised. The manifest records it as
`contentStatus: "intentional-pause"` with an explicit note that an engine must insert
a 300 ms pause here rather than play it as speech. It contains **no** unnatural
spoken sound and no unrelated audio, so the §6 escalation path (report and leave
unapproved) does not apply.

**Related finding (D-1), which does not resolve the same way:** the *Bangla* file at
`bn/phrase/room-suffix.wav` is the same silence, copied. The catalogue says the Bangla
locative suffix is spoken text (`-এ আসুন।`), so silence there is **not** an intentional
pause — it is a missing recording. It was therefore not renamed into
`bn/phrase/room-locative.wav`, and no file was created in its place. Renaming it would
have turned a visible gap into an invisible one: Bangla with-room announcements would
end at the room number and drop "please come in", with every technical check passing.

---

## 10. Human review status

**`humanReviewStatus` is `pending` for all 28 assets. Nothing was approved.**

- No human listened to any clip during this task, and no tool in this repository can
  listen. Technical validation (format, decodability, duration, checksums) says
  nothing about whether a clip *says* the right thing.
- Approval cannot be inherited from the previous manifest: it carried no per-asset
  human verdict, and every master was re-derived (44.1 kHz), so even a prior verdict
  would not apply.
- Approval is bound to the **playback checksum**. The manifest writer carries a
  verdict forward only when a previous manifest recorded one for byte-identical
  playback audio (`humanReviewFor()`); any re-encode resets it to `pending`. A person
  who listened to one file therefore cannot be credited with having listened to its
  replacement.
- Each entry states what the reviewer must confirm: English — pronunciation, pace and
  loudness; Bangla — pronunciation and intonation by a **native or fluent speaker**.

**Required next step:** a listening review of the 27 existing playback files —
English by any competent listener, Bangla by a native/fluent speaker — recorded by
setting `humanReviewStatus` per asset (and, if the review rejects a clip, the file is
recorded, not edited in place).

---

## 11. Commands to rerun validation and maintenance

All run from the repository root (`e:\amsdp`):

```powershell
# 1. Preserve originals, convert what is needed, rebuild manifest.json.
#    Idempotent: a file that already satisfies the contract is skipped.
node scripts/que-006-audio/standardise-audio.mjs

# 2. See the plan without writing anything.
node scripts/que-006-audio/standardise-audio.mjs --dry-run

# 3. Back up and verify the originals only, then stop.
node scripts/que-006-audio/standardise-audio.mjs --backup-only

# 4. Validate all assets (the twelve checks).
node scripts/que-006-audio/validate-audio-assets.mjs

# 5. Check only for missing files, or only verify checksums.
node scripts/que-006-audio/validate-audio-assets.mjs --mode missing
node scripts/que-006-audio/validate-audio-assets.mjs --mode checksums

# 6. Treat absent assets as pending work instead of failures.
node scripts/que-006-audio/validate-audio-assets.mjs --allow-missing

# 7. Rebuild manifest.json from the files on disk, or only report whether it is stale.
node scripts/que-006-audio/rebuild-audio-manifest.mjs
node scripts/que-006-audio/rebuild-audio-manifest.mjs --check

# 8. The generation-stage validator still runs and still checks the catalogue wording.
node scripts/que-006-audio/validate.mjs --allow-missing
```

Exit codes: `standardise-audio.mjs` — 0 done, 1 conversion failure, 2 usage, 3 ffmpeg
missing, 4 backup unverifiable. `validate-audio-assets.mjs` — 0 pass, 1 failure,
2 usage, 3 ffprobe/ffmpeg missing. `rebuild-audio-manifest.mjs` — 0 written/current,
1 stale under `--check`, 2 usage.

---

## 12. Announcement playback integration — explicitly outstanding

**The AMSDP frontend still uses browser speech synthesis. `QUE-006` prerecorded-audio
playback is NOT implemented, NOT integrated, and NOT accepted.**

Evidence, not assertion:

- `frontend/lib/announcements/speech-synthesis.js` — **unmodified** (`git diff` is
  empty; the file is not in the modified list).
- `frontend/lib/announcements/content.js` and `frontend/pages/queue.js` — not touched
  by this task; their pre-existing uncommitted modifications predate it and were left
  exactly as found.
- `manifest.json` states it itself, twice:
  `playable.integratedWithApplication = false` and `playable.readyForPlaybackEngine =
  false`. The validator fails the build if that flag is anything but `false`.
- No component reads `manifest.json`. A search across `frontend/` and `scripts/`
  (excluding this utility) finds **no consumer** of `audio/manifest.json`.

Prepared, not wired: the files, the manifest and the validation are in place for a
future prerecorded-audio engine. Producing assets is not the same as playing them, and
this report does not claim otherwise.

---

## 13. Defects found and fixed during implementation

Each was found by running the tool against the real files, not by inspection alone.

| # | Defect | How it surfaced | Fix | Regression evidence |
|---|---|---|---|---|
| 1 | ffmpeg refuses to convert a file onto itself (`Output … same as Input`), so `en/phrase/room-suffix.wav` could not be standardised in place. | First real run: `convert-failed` on exactly that asset. | `produceSafely()` writes to a sibling temp file when source = target, verifies it against the contract, then renames. | Re-run converted it; the preserved original is unchanged (`651d0bac…`). |
| 2 | `--dry-run` reported a false failure: the overwrite guard demanded a backup that the same run would create in phase 1. | Dry run disagreed with the real run. | The guard accepts a `would-copy` backup record when `dryRun` is set. | Dry run exits 0 and matches what the real run then did. |
| 3 | The backup record accumulated **this utility's own outputs** (39 converted files added on a second run), so `ORIGINALS.json` would have claimed converted files were originals. | Counting record entries after a re-run: 67 instead of 28. | Snapshot rule: the first pass preserves everything; later passes never add a delivery path and prune entries added after the first snapshot — **except** a path whose preserved copy holds pre-standardisation bytes (`en/phrase/room-suffix.wav`), kept as evidence. | Record is exactly **28** entries; all 28 hashes re-verified. |
| 4 | A declared-missing asset produced a second, misleading failure (`playback … skipped-no-master`). | JSON run report. | Cascades from a `declared-missing` master are reported as part of the same **gap**. | Run reports 2 gaps, 0 failures, exit 0. |
| 5 | `playbackDerivation` degraded from `encoded-from-master` to `existing-conformant` on the idempotent second run, losing provenance. | Comparing manifests across runs. | Derivation decided from durable signals: this run encoded it, or the path had no preserved original, or a preserved original matches byte-for-byte. | 13 `original-mp3-preserved` + 14 `encoded-from-master` + 1 null, stable across runs. |
| 6 | Validation check 11 treated the *named* path of a missing asset as an overclaim. | First validator run failed twice instead of once. | It now fails only when an entry **claims** the file is present (`technicalValidationStatus !== 'missing'`) and it is not. | One failure (the real one) remains; the overclaim test still catches a mislabelled entry. |
| 7 | `validate.mjs` hard-coded 24 kHz, generation-era checksums and v1 manifest fields, failing 29/28 on a correctly standardised tree. | Running it after conversion. | It detects `.work/standardisation.json`, reads the 44.1 kHz contract from the record, compares against that record and uses the v2 field names — and says so. | `validate.mjs --allow-missing` → PASS 27/28 with a `standardisation stage detected` check naming the switch. |
| 8 | *Process:* rewriting a source file with PowerShell `Get-Content`/`Set-Content` round-tripped UTF-8 through cp1252 and corrupted every non-ASCII character in `standardise-audio.mjs`. | Mojibake scan of the edited file (`Â·`, `â€"`). | Repaired by exact cp1252 → UTF-8 reversal, written without BOM. Later edits used the editor tool only. | No mojibake markers remain; first bytes `#!/`; `node --check` passes. |

---

## 14. Decisions, deviations and open items

### Decisions taken during the task

| ID | Decision | Rationale |
|---|---|---|
| **D-1** | The §5 rename of `bn/phrase/room-suffix.wav` → `room-locative.wav` was **not** performed, and no file was created in its place. | The file is a copy of the English silence placeholder (identical SHA-256, −91 dB). Renaming it would have made a missing Bangla recording indistinguishable from a present one at every technical layer. The original keeps its name and its backup. |
| **D-2** | English playback files are the **original MP3s, byte-identical**, not re-encodes of the masters. | Avoids a second lossy generation. The files already met the playback contract (measured). Documented deviation from §4's "generate playback from the master". |
| **D-3** | The 13 Bangla `.m4a` sources and the mislabelled `bn/phrase/room-suffix.wav` stay in `frontend/public/audio/`. | §3 forbids deleting originals. They are outside the contract, are never referenced by the manifest, and are reported here as retained. Removing them needs an owner decision (O-7). |
| **D-4** | The backup is a **snapshot taken before standardisation**, not a mirror of the current tree. | A backup that grows to include converted outputs stops being evidence of the originals. |
| **D-5** | `.gitignore` gained `/frontend/.audio-originals-backup/`. | ~1 MB of binary recordings should not enter the repository. The backup stays on disk as evidence; it is not a source artefact. |

### Deviations from the literal task text

1. §5 rename — see D-1.
2. §2 structure has 27 delivery pairs rather than 28, plus retained originals — see D-1 and D-3.
3. §4 "generate playback from the WAV masters" — applied to Bangla and to the punctuation asset; not applied to the English MP3-only sources (D-2).

### Open items

| ID | Owner action / decision | Blocks |
|---|---|---|
| **O-1** | Record `bn.phrase.room-locative` (`-এ আসুন।`) with the same Bangla voice, save as `bn/phrase/room-locative.wav`, run `standardise-audio.mjs`. | 28/28 completion; Bangla with-room announcements |
| **O-2** | Decide whether the ~1 s trailing silence in the Bangla clips should be trimmed in a **separate, approved** pass. Nothing was trimmed here. | Announcement pacing (audible ~1 s gaps) |
| **O-3** | Listening review of the 27 playback files; Bangla by a native/fluent speaker. Set `humanReviewStatus` per asset. | Demo use; any claim of pronunciation approval |
| **O-4** | Decide the `en.phrase.no-room` leading comma (recorded with it, catalogue cell omits it). | Wording sign-off |
| **O-5** | Decide which provider's voice is the product voice (`MVP_Feature_Catalogue` still records no TTS provider selected). | Any future re-generation |
| **O-6** | Implement and integrate the prerecorded-audio playback engine, then flip `integratedWithApplication`. | QUE-006 end-to-end |
| **O-7** | Approve removal (or retention) of the 13 `.m4a` sources and `bn/phrase/room-suffix.wav` from the served tree. | Repository hygiene; ~424 KB of unused static files |

---

## 15. Governance and skill compliance

### Documents read for this task (`.clinerules` §2 step 3, §12)

| Document | Used for |
|---|---|
| `.clinerules` | Precedence, non-negotiables, routing, documentation output rules |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Locating the relevant documents; updated by this task (Revision 41) |
| `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` | The 28 assets, approved spoken text, filenames, required formats |
| `scripts/que-006-audio/catalogue.mjs`, `lib/paths.mjs`, `lib/manifest.mjs`, `lib/decode.mjs`, `validate.mjs`, `README.md` | Existing conventions, tool resolution, CLI shape, exit codes |

### Routing applied (`.clinerules` §4)

| Domain | Governance applied | Skill |
|---|---|---|
| Audit / data integrity / reporting | `saas-observability.md` as adapted — evidence over claims, no fabricated results | **none installed** |
| Database / schema | none touched: no schema change, no migration, no table | — |
| Frontend UI / playback | ruled out of scope by the task; `speech-synthesis.js` untouched | — |
| Documentation | §11 output location, §12 index maintenance | **none installed** |

**Skills: NONE installed in this workspace** (`.clinerules` §5). No skill was
simulated, and no claim of skill usage appears here. The governance documents above
were the applied instructions.

### Non-negotiables (§3) checked

- No secret, token, key or credential appears in this report, the manifest, the
  scripts or the evidence files.
- No authorization, tenant or audit logic is in this task's scope, and none was
  touched. No schema change, so no migration question arises.
- No capability is claimed beyond what was run: every command result quoted here was
  executed in this session.
- No file was deleted. No git commit, push, stage or checkout was performed.

### Evidence standard (§7) applied to this task

| Statement | Level | Why |
|---|---|---|
| The standardisation, validator and manifest-builder scripts exist and are reachable | **IMPLEMENTED** | Files exist; `node --check` passes on every `.mjs` in the utility |
| The three new CLIs run and report | **TESTED** | Real runs; exit codes quoted verbatim (§6.2, §11) |
| 27 masters + 27 playback files exist at the contract format | **VERIFIED** | Second artefact: `ffprobe` stream facts + full `ffmpeg` decode + SHA-256 in `manifest.json`, cross-checked by an independent script run |
| The 28 originals are preserved byte-for-byte | **VERIFIED** | `ORIGINALS.json` hashes re-verified against the backup copies on every validation run |
| The audio says the right words / Bangla is correctly pronounced / it suits a clinic | **NOT VERIFIED** | Requires a human listener (§10); nothing here claims it |
| Any asset is pronunciation-approved | **NOT ACCEPTED** | No human review performed; `humanPending = 28` |
| Prerecorded playback works in the demo | **NOT IMPLEMENTED** | §12 |

### Files created / modified

| File | Change |
|---|---|
| `scripts/que-006-audio/lib/audio-standard.mjs` | **new** — format contract, asset specs, probing, loudness, safe conversion |
| `scripts/que-006-audio/lib/audio-backup.mjs` | **new** — snapshot backup with post-copy verification |
| `scripts/que-006-audio/lib/audio-standard-manifest.mjs` | **new** — manifest builder (v2 schema), human-review carry-over |
| `scripts/que-006-audio/standardise-audio.mjs` | **new** — backup → masters → playback → manifest |
| `scripts/que-006-audio/validate-audio-assets.mjs` | **new** — the twelve checks, three modes |
| `scripts/que-006-audio/rebuild-audio-manifest.mjs` | **new** — rebuild / `--check` |
| `scripts/que-006-audio/lib/decode.mjs` | added `runAudioTool` export and `encodeMp3()` |
| `scripts/que-006-audio/validate.mjs` | standardisation-aware expectations (§13 defect 7) |
| `scripts/que-006-audio/README.md` | standardised-format section, commands, manifest fields |
| `frontend/public/audio/**` | 27 masters added/converted, 14 playback files added; `bn/phrase/room-locative.*` deliberately absent |
| `frontend/public/audio/manifest.json` | rebuilt as schema 2.0 (previous version archived in the backup) |
| `frontend/.audio-originals-backup/**` | **new** — 28 preserved originals + `ORIGINALS.json` |
| `.gitignore` | `/frontend/.audio-originals-backup/` |
| `docs/implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` | **new** — this report |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | Revision 41 — this report registered |

**Not modified:** `frontend/lib/announcements/content.js`,
`frontend/lib/announcements/speech-synthesis.js`, queue logic, announcement
triggering, approved wording, and the spoken content of every recording.

---

## 16. Summary

The catalogue assets are now standardised to a single delivery contract — PCM WAV
master at 44.1 kHz / 16-bit / mono plus an MP3 playback file at 44.1 kHz / mono /
128 kbps CBR — with the originals preserved byte-for-byte outside the served tree, a
manifest that describes exactly what is on disk, and a validator that checks twelve
properties per asset and refuses to call a missing Bangla clip a pass.

**27 of 28 assets are complete and technically validated. One —
`bn.phrase.room-locative` — has no recording and is reported as missing rather than
filled with a placeholder.** Because of that, this task is **PARTIALLY COMPLETE**, and
prerecorded-audio playback in the frontend remains **outstanding and unimplemented**.

> **V1.1 addendum (2026-11-21):** the Bangla locative recording was supplied and
> converted, so the set is now **28/28**. This §16 conclusion describes the V1.0 state
> and is kept as written; §17 is the current outcome.









---

## 17. V1.1 — the missing Bangla recording was supplied and converted

Task: convert the already-supplied Bangla locative recording into the delivery
contract. **No speech was generated, no spoken content was changed, no queue or
announcement source was touched, no playback integration was written, and nothing was
committed.** The source file was preserved and backed up before conversion.

### 17.1 Source file as found

| Property | Value |
|---|---|
| Path | `frontend/public/audio/bn/phrase/room-locative.mpeg` |
| Exists | yes — `Test-Path` true, mtime `2026-11-21 04:30:54` |
| Bytes | 44,973 |
| SHA-256 | `7c2c58bc747dbd4bbe53820b32e07af2e3dbf460962ae6aff75b26f33fee3cbd` |
| ffprobe `format_name` | **`mp3`** — *not* `mpeg`; the extension does not describe the container |
| Codec | `mp3`, MPEG-1 Layer III |
| Sample rate | **48,000 Hz** (not 44.1 kHz — resampling was genuinely required) |
| Channels | 1 (mono) |
| Duration | 1.819979 s (`ffprobe`), reported as 1.82 s after conversion |
| Reported bit rate | 197,685 bps at container level; the stream's per-frame mode was **not** asserted, and it does not matter: the master is uncompressed PCM and the playback file is re-encoded |
| Loudness | `mean_volume -22.1 dB`, `max_volume -4.5 dB` — real speech, not silence |
| Speech extent | speech to 0.668146 s, then 1.151833 s of silence to the end |
| Decode check | `ffmpeg -v error -i … -f null NUL` → **exit 0**, no diagnostics |
| Rewritten by this task | **no** — hash identical before and after (§17.6) |

The extension is the trap this file sets, and the earlier pass fell into it in the
other direction: it saw `.mpeg`, no matching source candidate, and correctly refused
to invent one. Nothing here trusts the name. `ffprobe` reports what the bytes are, and
every fact in the table above comes from `ffprobe`/`ffmpeg`, not from the filename.

The trailing 1.15 s of silence is **in the supplied recording** (measured on the
`.mpeg` itself, 0.668146–1.819979 s), not introduced by conversion. Open item O-2 now
covers this clip too, and it is still an owner decision — nothing was trimmed.

### 17.2 Conversion settings

Both files were produced by the existing utility, not by hand-typed ffmpeg commands:
`standardise-audio.mjs` → `writeMaster()` → `transcodeToWav()`, then `writePlayback()` →
`encodeMp3()`. Those helpers write to a sibling temporary file when the target equals
the source, verify the result against the contract, and only then move it into place —
so a bad conversion can never destroy a recording.

**Master** — `frontend/public/audio/bn/phrase/room-locative.wav`

```
ffmpeg -nostdin -y -v error -i <source.mpeg> -ac 1 -ar 44100 -c:a pcm_s16le -f wav <target.wav>
```

**Playback** — `frontend/public/audio/bn/phrase/room-locative.mp3`, encoded **from the
validated master**, never from the source:

```
ffmpeg -nostdin -y -v error -i <master.wav> -ar 44100 -ac 1 -c:a libmp3lame -b:a 128k -map_metadata -1 -f mp3 <target.mp3>
```

No gain, loudness normalisation, noise reduction, trimming, pitch shift or
time-stretch is applied by either command. `libmp3lame` without `-q:a` writes CBR, and
the result was checked by frame size rather than by the container's average bit rate
(§17.5).

### 17.3 Originals preserved

The backup phase ran before any conversion. `bn/phrase/room-locative.mpeg` was copied
to `frontend/.audio-originals-backup/bn/phrase/room-locative.mpeg` and re-hashed after
copy:

| | Source (in tree) | Backup copy |
|---|---|---|
| Bytes | 44,973 | 44,973 |
| SHA-256 | `7c2c58bc…ee3cbd` | `7c2c58bc…ee3cbd` |
| Record status | — | `copied-verified` |
| Record path | — | `frontend/.audio-originals-backup/ORIGINALS.json` → `files["bn/phrase/room-locative.mpeg"]` |

No existing backup file was overwritten, and no preserved entry was rewritten: the
record now holds **29** entries (28 recordings found in the first pass plus this one),
and the validator re-verifies every preserved hash on each run — `29 originals
recorded and hash-verified` (§17.5). The in-tree source is also unchanged:
`7c2c58bc…ee3cbd` before and after (§17.6).

### 17.4 Manifest registration

`manifest.json` was rebuilt from what is on disk (schema
`AMSDP-QUE-006-audio-assets/2.0`) and contains exactly one entry for the asset:

| Field | Value |
|---|---|
| `id` | `bn.phrase.room-locative` |
| `spokenText` | `-এ আসুন।` — the catalogue value verbatim |
| `masterFile` / `playbackFile` | `bn/phrase/room-locative.wav` / `bn/phrase/room-locative.mp3` |
| `masterFormat` | `wav/pcm_s16le/44100Hz/mono/16-bit` |
| `playbackFormat` | `mp3/44100Hz/mono/128kbps/cbr` |
| `sampleRate` / `channels` / `durationSeconds` | 44100 / 1 / 1.82 |
| `masterBytes` / `masterChecksum` | 160,602 / `bc01c501c586c42b87b062d1fe01b5adcbb24afe8df33f17c8ddfdee87a1b98c` |
| `playbackBytes` / `playbackChecksum` | 30,137 / `b15c1b1608006c0cbb1d9008ebc5fb36ab32f5007d72eefc1762fa0a08a199f4` |
| `technicalValidationStatus` | `pass` (no technical problems) |
| `humanReviewStatus` | **`pending`** — not approved, not listened to |
| `contentStatus` / `contentIssue` | `speech` / `null` |
| `origin` | `frontend/public/audio/bn/phrase/room-locative.mpeg`, role `original-mpeg`, sha256 `7c2c58bc…`, 44,973 B, container `mp3` @ 48,000 Hz, `preserved: true` |
| `playbackDerivation` | `encoded-from-master` |

Manifest summary after the rebuild: `total 28 · masterPresent 28 · playbackPresent 28 ·
technicalPass 28 · technicalMissing 0 · technicalFail 0 · contentIssues 0 ·
humanApproved 0 · humanPending 28 · complete true`.

### 17.5 Validation results

All three scripts were run **strict** — `--allow-missing` was deliberately not used, so
an absent file would have been a failure rather than a warning.

**`validate-audio-assets.mjs` (12 checks) → exit 0, `verdict PASS`**

```
assets 28/28 pass · warn 0 · fail 0 · masters 28/28 · playback 28/28
```

Per-check evidence for this asset, as printed by the validator:

| Check | Observation |
|---|---|
| Master exists, decodes, matches contract | `pcm_s16le 44100Hz 1ch 16bit 1.82s 160602B` — `parsed by ffprobe+ffmpeg-decode` |
| Playback exists, decodes, matches contract | `mp3 44100Hz 1ch 1.82s 30137B base 128kbps CBR spread 0.3kbps` — the 0.3 kbps spread is the MPEG padding bit alternating, i.e. genuine CBR, not a VBR file reporting a 128 kbps average |
| 10 · no duplicate asset IDs | 28 unique ids |
| 10 · no duplicate output paths | 56 unique paths |
| 10 · no two speech assets share identical bytes | 27 speech assets, all byte-distinct — the new clip does **not** duplicate any other asset |
| 11 · manifest declares the catalogue size | 28 entries, expected 28 |
| 11 · manifest covers every catalogue asset | missing: none; not in catalogue: none |
| 11 · every manifest path resolves to an existing file | 56 paths resolve under `frontend/public/audio/` |
| 12 · manifest checksums match the files | **56 SHA-256 values verified** (28 masters + 28 playback) |
| 12 · manifest statuses match the files | every status matches a fresh evaluation |
| 12 · manifest spoken text matches the catalogue | every `spokenText` is the catalogue value verbatim, including `-এ আসুন।` |
| 12 · manifest claims no application integration | `integratedWithApplication=false` |
| P · preserved originals still verify | **29 originals recorded and hash-verified** |

**`validate.mjs` (generation-stage validator, standardisation-aware) → exit 0**

```
pass 28/28 (100%) · warn 0 · fail 0
verdict PASS — all 28 catalogue clips pass structural validation
```

with `bn.phrase.room-locative — 1820 ms, 160602 B, parsed by ffprobe+ffmpeg-decode`,
consistent with the other Bangla clips (1,820 ms / 160,602 B).

**`rebuild-audio-manifest.mjs --check` → exit 0**

```
manifest.json is current — matches the files on disk
```

**Idempotency** — a second `standardise-audio.mjs --dry-run` reports
`bn.phrase.room-locative — kept-valid` for **both** files (`already
wav/pcm_s16le/44100Hz/mono/16-bit (1.82s)`, `already mp3/44100Hz/mono/128kbps/cbr
(1.82s)`) and backup `copied+verified 0 · already preserved 28 · conflicts 0 · copy
mismatches 0`. A re-run therefore repairs and rewrites nothing, and in particular does
not re-encode the master from the MP3 it just produced.

### 17.6 What changed, and what did not

A SHA-256 baseline of all 70 files under `frontend/public/audio/` was taken before the
run and compared afterwards:

| Category | Result |
|---|---|
| Added | `bn/phrase/room-locative.wav` (160,602 B), `bn/phrase/room-locative.mp3` (30,137 B) |
| Changed | `manifest.json` only — it is the derived artefact this task is required to update |
| Removed | **none** |
| Every other audio file | byte-identical — all 26 existing masters, all 26 existing playback files and the 13 `.m4a` sources are untouched |
| Source `.mpeg` in the tree | unchanged: `7c2c58bc…ee3cbd` before and after |
| `bn/phrase/room-suffix.wav` (the placeholder) | still present, still unreferenced, still **not** renamed into the locative slot |

Code changes in this revision, all inside the QUE-006 utility and none in the
application:

- `lib/audio-standard.mjs` — removed the `missing-content` declaration for
  `bn.phrase.room-locative` (it now describes reality; the historical note is recorded
  here, not in the code), emptied `CONTENT_ISSUES`, and added
  `ORIGINAL_SOURCE_BY_ID` + `originalCandidatesFor()`, consulted by `originalFor()`.
- `standardise-audio.mjs` — the `--force` source resolution now uses that shared
  candidate list instead of its own hard-coded copy, so the two paths cannot drift.

The reason the override exists is worth stating plainly: without it, `originalFor()`
would have found `bn/phrase/room-locative.mp3` — the file this utility writes — and
derived the "master" from our own 128 kbps playback. That would have passed every check
while silently degrading the archive copy and destroying the provenance link to the
recording. The override names the `.mpeg` explicitly and ranks it first.

### 17.7 Status, remaining missing assets, and open items

**Asset count is now 28 of 28.** 28 masters, 28 playback files, 0 missing, 0 failing,
0 content issues, **0 human-approved**. The catalogue has **no remaining missing
asset**. What remains on disk outside the catalogue is byte evidence, deliberately kept:
the 13 `.m4a` generation sources, the original `bn/phrase/room-locative.mpeg`, and the
unreferenced placeholder `bn/phrase/room-suffix.wav`.

| Item | State after V1.1 |
|---|---|
| **O-1** — record `bn.phrase.room-locative` | **CLOSED** — supplied, converted, validated (§17.1–§17.5) |
| **O-2** — trim ~1 s of trailing silence? | **OPEN, now includes this clip** — the supplied recording itself carries 1.152 s of silence after speech ending at 0.668 s. Nothing was trimmed; this is a product decision about announcement pacing, and trimming would also change every other Bangla clip's timing |
| **O-3** — human listening review | **OPEN for all 28, including this one.** Every `humanReviewStatus` is `pending`. For this clip specifically: confirm `-এ আসুন।` is intelligible and correctly pronounced when concatenated after a room number, and that the sentence does not sound clipped when the room number is followed immediately by the suffix |
| **O-4** — `en.phrase.no-room` leading comma | UNCHANGED — owner decision, no wording edited |
| **O-5** — product TTS voice | UNCHANGED |
| **O-6** — implement the playback engine, then flip `integratedWithApplication` | **OPEN** — `speech-synthesis.js` was not touched, `manifest.json` still declares `integratedWithApplication: false`, and no frontend component reads it. The assets are playable files; nothing plays them in the app |
| **O-7** — retain or remove `.m4a` sources and the placeholder from the served tree | UNCHANGED |

**Honest quality note on this master.** The source is a lossy MP3 stream at 48 kHz, so
the 44.1 kHz PCM master is a lossless copy *of a lossy recording*: it preserves exactly
what was supplied and cannot restore detail the source never contained. Nothing was
upsampled, normalised, denoised or "repaired" to hide that, and the manifest records the
source container, rate and hash so the chain is auditable. A future higher-fidelity
recording of this phrase would strictly improve it.

### 17.8 Governance and skill compliance

| Requirement | How it was met |
|---|---|
| Documents read before acting (§2 step 3, §12) | `docs/governance/AMSDP_Docs_Index_V1.0.md` (navigation), this report (§1–§16, the contract it defines), `scripts/que-006-audio/README.md`, and the code that implements the contract (`lib/audio-standard.mjs`, `lib/audio-backup.mjs`, `lib/decode.mjs`, `standardise-audio.mjs`) |
| Skills (§5) | **No skill package is installed** in this workspace; none was claimed. The AMSDP governance documents and the existing QUE-006 utility were used instead |
| Non-negotiables (§3) | No secrets logged or quoted; no business rule, wording, queue or announcement logic touched; no schema change, so no migration was needed; audit trail untouched; nothing fabricated — the clip is a supplied recording, and its pronunciation is **not** claimed correct |
| Evidence standard (§7) | IMPLEMENTED: two files and a manifest entry exist. TESTED: three validation scripts, strict, exit 0. VERIFIED: independent `ffprobe`/`ffmpeg` reads of both files, SHA-256 comparison of source and backup, and a whole-tree hash diff proving nothing else moved. **NOT** verified: that the words are correct or well pronounced — that requires a human ear (§17.7 O-3) |
| Deviations disclosed | (1) The utility's own code changed, beyond "convert a file" — necessary because the asset was hard-coded as `missing-content` and its `.mpeg` source was invisible to source resolution; disclosed in §17.6. (2) The V1.0 text of this report was left intact and superseded by an addendum instead of being rewritten, so the earlier, honest "missing recording" finding remains on record. (3) Nothing was committed, pushed or deployed |
| Documentation placement (§11) | Report updated **in place** at `docs/implementation/QUE-006_AUDIO_FORMAT_STANDARDISATION_REPORT.md` (existing file, V1.0 → V1.1 addendum; no new document, so no manifest entry was required). `docs/governance/AMSDP_Docs_Index_V1.0.md` updated in the same task (§12 "keep the index current") |
| Tooling notes | `ffmpeg`/`ffprobe` 9.1 remain installed but **not on `PATH`**; they were reached through the existing `lib/decode.mjs` resolver, so nothing was installed for this task. UTF-8 files were edited with a UTF-8-preserving editor — the earlier PowerShell `Get-Content`/`Set-Content` corruption lesson (§13, defect 8) was not repeated, and the Bangla strings in this document and the manifest were verified intact after editing |





