# QUE-006 — Gemini TTS Audio Generation Utility: Implementation Report

> **Task:** `AMSDP-QUE-006-GEMINI-TTS-UTILITY`
> **Date:** 2026-11-20
> **Written to:** `docs/implementation/QUE-006_Gemini_Audio_Generation_Implementation_Report.md`
> (governance §11 — subject subfolder `implementation/`; no existing document was
> moved, renamed, overwritten or deleted, so no migration-manifest entry is
> required.)
> **Scope:** build, verify and operate a standalone utility in
> `scripts/que-006-audio/` that generates, validates and manifests the 28
> catalogue audio assets (14 English, 14 Bangla) specified by
> `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md`.
>
> **Status — read this first.** The utility is **IMPLEMENTED** (code exists and
> runs) and **TESTED** (the named command runs below were executed in this
> session and their real exit codes are recorded). The audio is **NOT GENERATED**:
> a key now exists in `.env.local`, but Google rejects it as
> `API_KEY_INVALID` (the resolved value is 35 characters, not the 39 of an AI
> Studio key), so **0 of the 27 spoken clips exist**. Only the one synthetic silent
> pause asset exists. Nothing here is VERIFIED in the §7 sense and nothing is
> ACCEPTED. No claim in this report rests on a run that was not performed.
> **Revision 2 (2026-11-20, §11)** replaced the "no decoder on this machine"
> finding: `ffmpeg`/`ffprobe` 9.1 were installed mid-session and the validator now
> performs a real decode. Sections 1–10 are corrected in place; §11 records what
> changed and why.

## 1. What was built

A dependency-free Node utility: no `package.json`, no npm package added, no
`node_modules`, Node built-ins only, never imported by the application.

| File | Purpose |
|---|---|
| `scripts/que-006-audio/catalogue.mjs` | The 28-asset table transcribed from the catalogue document; `composeTemplates()`; `diffComposedAgainstApproved()`; `parseCatalogueDoc()` / `diffAgainstDoc()`; `SPOKEN_TEXT_OVERRIDES` with `recordedTextFor()` |
| `scripts/que-006-audio/generate.mjs` | CLI: argument parsing, selection, preflight, per-asset synthesis with classified retries, resume/skip, state recording, atomic manifest writing, `--check-catalogue` self-check |
| `scripts/que-006-audio/validate.mjs` | Independent validator: catalogue integrity, per-file structural checks, cross-file and manifest-vs-disk consistency, `--json` / `--quiet` / `--allow-missing` |
| `scripts/que-006-audio/lib/gemini-tts.mjs` | API client: request construction, HTTP error classification (transient vs blocking), response audio extraction, model and voice listing |
| `scripts/que-006-audio/lib/audio-file.mjs` | WAV and MP3 container parsers, PCM peak/silence measurement, SHA-256, silent-WAV writer |
| `scripts/que-006-audio/lib/decode.mjs` | Optional codec-level evidence: ffprobe stream facts plus a full ffmpeg decode to a null sink, both cross-checked against the container declaration (revision 2, §11) |
| `scripts/que-006-audio/lib/manifest.mjs` | Generation state, atomic JSON writes, per-asset description from disk, manifest construction |
| `scripts/que-006-audio/lib/preflight.mjs` | Key, model, voice and single-clip synthesis probe |
| `scripts/que-006-audio/lib/approved-templates.mjs` | Reads the approved wording out of `frontend/lib/announcements/content.js` as text (never imports the frontend module, so no ESM interop warning and no chance of the script mutating app code) |
| `scripts/que-006-audio/lib/env.mjs` | `GEMINI_*` settings and key resolution (process env → `.env.local` → `.env`) with redaction on every diagnostic |
| `scripts/que-006-audio/lib/paths.mjs` | Every path in one place |
| `scripts/que-006-audio/README.md` | Operator documentation: requirements, key setup and precedence, configuration, complete command reference, exit codes, output layout, manifest status semantics, validation limits, integration status, open items |

No file under `frontend/`, `backend/`, `ai_factory/` or `tests/` was modified by
this task. `git status --porcelain` reports `scripts/` and `frontend/public/` as
untracked (`??`); nothing was staged or committed.

## 2. Catalogue and API contract as implemented

- **Assets:** 28 = 14 English + 14 Bangla. Per language: 4 fixed phrases and 10
  digit recordings. 27 are spoken; 1 — `en.phrase.room-suffix`, the terminal full
  stop — is a deliberate 300 ms silent WAV, because a full stop is a pause, not a
  spoken word.
- **Model:** a single multilingual TTS model serves both languages
  (`GEMINI_TTS_MODEL`, default `gemini-3.8-flash-tts`); default voice `Kore` for
  both, configurable per language (`GEMINI_VOICE_EN` / `GEMINI_VOICE_BN`).
- **Request:** `POST {GEMINI_API_BASE}/interactions` with the model, the recorded
  text, `response_format: {type: "audio"}`, a `speech_config` voice entry and
  `store: false`.
- **Response:** base64 audio. The extractor looks at `output_audio` /
  `outputAudio` (the documented shape) and only then falls back to a
  depth-limited nested scan; the path that produced the bytes is recorded per
  asset as `responsePath`, so a fallback can never masquerade as the documented
  shape.
- **Accepted container:** WAV only, decoded from base64 to bytes. The expected
  24 kHz / 16-bit / mono output is *measured per file*, not assumed, because the
  API contract is not a per-response guarantee.
- **Safety:** the key is never printed, logged, hashed into a filename or written
  into the manifest; every diagnostic goes through `redact()`. The key is read
  from the process environment first, then a git-ignored `.env.local`, then
  `.env`, and the resolution order is reported without revealing the value.

## 3. Verification actually performed

Every row below was executed in this session on this machine. Exit codes are the
observed ones.

| Command | Observed result |
|---|---|
| `node --check` on all 10 `.mjs` sources | all pass, exit 0 |
| `generate.mjs --help` / `validate.mjs --help` | exit 0, 41 and 11 lines of usage |
| `generate.mjs --check-catalogue` | **PASS** — 28 document rows agree with `catalogue.mjs`; with-room and no-room templates compose identically to the approved `content.js` wording for both languages; the single declared override printed with its reason; exit 0 |
| `generate.mjs --smoke --dry-run` | exit 0 — 4 assets planned (`en.digit.4`, `bn.digit.4`, `en.phrase.token-number`, `bn.phrase.token-number`), key reported `MISSING — generation would stop with exit 2`, no network call, no write |
| `generate.mjs --limit 3` | exit **2** — key blocker reported before any request; "Nothing was generated, no file was written, and `manifest.json` was not modified" |
| `generate.mjs --all` (key absent) | exit **2** — same blocker, same guarantee |
| `generate.mjs --preflight-only` | exit **2** — key blocker raised before the probe; no API call made |
| `generate.mjs --asset en.phrase.room-suffix --no-probe` | exit 0 — `skip (valid WAV, 24000 Hz, 16-bit, mono, 300 ms)`, run summary `generated 0 · skipped 1 · failed 0`, catalogue `1/28 ready` |
| `validate.mjs` | exit **1** — `pass 1/28 (4%) · warn 0 · fail 27`, verdict FAIL, every failure `file not present` |
| `validate.mjs --allow-missing` | exit **0** — `pass 1/28 (4%) · warn 27 · fail 0`, verdict "PASS — no failures; 1/28 clips validated on disk, 27 still pending generation" |
| `validate.mjs --json --allow-missing` | parses as JSON: 8 checks, `counts {total:28, pass:1, warn:27, fail:0, coverage:"4%"}` |
| `generate.mjs --rebuild-manifest` | exit 0 — manifest rebuilt from disk without an API call: `1/28 assets ready; 27 outstanding`, each listed `missing` with its expected path |
| `generate.mjs --asset en.phrase.room-suffix --no-probe` (repeat) | exit 0 — `skip (valid WAV, 24000 Hz, 16-bit, mono, 300 ms)`, so resume correctly refuses to re-spend quota on a valid clip |
| **Revision 2** — `generate.mjs --preflight-only` (key present in `.env.local`) | exit **3** — `api-key` check **warn** (`35-character key; an AI Studio key is 39 characters and starts "AIza"`), `model-visible` **fail** and `synthesis-probe` **fail** both classified `api-key-invalid: key rejected by Google (400): API key not valid`. Nothing was generated or written |
| **Revision 2** — `generate.mjs --smoke --dry-run` (key present) | exit 0 — `api key present (.env.local (repository root))`, 4 assets planned, no network call |
| **Revision 2** — `generate.mjs --check-catalogue` | **PASS**, exit 0, unchanged after the revision |
| **Revision 2** — `validate.mjs --allow-missing` | exit **0** — `pass 1/28 (4%) · warn 27 · fail 0`; header now reads `decoder ffprobe 9.1-full_build-www.gyan.dev + ffmpeg 9.1-full_build-www.gyan.dev`, `method riff/mpeg container parse + ffprobe stream facts + ffmpeg full-file decode`; the pause asset row is `parsed by ffprobe+ffmpeg-decode` |
| **Revision 2** — `validate.mjs --allow-missing --json` | exit 0, parses: `counts {total:28, pass:1, warn:27, fail:0}`; the pause row carries `decodeVerifiedBy: "ffprobe+ffmpeg-decode"`, `decoderCodec: "pcm_s16le"`, `decoderDurationMs: 300`, `durationMs: 300` — the decoder and the container agree |
| **Revision 2** — `node --check` on all changed sources (`validate.mjs`, `lib/{decode,env,preflight,gemini-tts,audio-file}.mjs`) | all pass, exit 0 |
| **Revision 2** — `scripts/que-006-audio/.work/decode-negative-controls.mjs` | 3 deliberately broken files + 1 control, run against the real decoder (see §11) |

The validator states its own limits in every run. Revision 1 read `decoder none on
this machine — no ffmpeg or ffprobe available` / `method container-structure`; from
revision 2 it reads `decoder ffprobe 9.1-full_build-www.gyan.dev + ffmpeg
9.1-full_build-www.gyan.dev` / `method riff/mpeg container parse + ffprobe stream
facts + ffmpeg full-file decode`, and still closes with "What this does not
establish: that the words are correct, Bangla pronunciation, perceived loudness,
and whether the voice suits a clinic."

Non-ASCII integrity was confirmed from the actual console output: the Bangla
override reason and the Bangla catalogue text render correctly
(`", অনুগ্রহ করে সামনে আসুন।"`), so the encoding repair in §7 is effective.

## 4. Current on-disk state

| Artefact | Observed state |
|---|---|
| `frontend/public/audio/en/phrase/room-suffix.wav` | 14,444 B; WAV 24,000 Hz, 16-bit, mono; 300 ms; digitally silent (intentional); decoded by `ffprobe+ffmpeg-decode` (`pcm_s16le`, 300 ms measured); SHA-256 matches `.work/state.json` |
| the other 27 clips | absent — reported as `file not present` |
| `frontend/public/audio/manifest.json` | `ready 1 / total 28`, `catalogueComplete: false`, `playable.integratedWithApplication: false` |
| `scripts/que-006-audio/.work/state.json` | one generation record (the synthetic pause), marked synthetic rather than an API call |
| `scripts/que-006-audio/.work/last-run.json` | summary of the most recent run |

The manifest deliberately does not claim integration, and `validate.mjs` asserts
`integratedWithApplication === false` — so a future accidental flip to `true`
fails validation instead of silently overclaiming that the demo plays recordings.

## 5. Evidence levels reached

- **IMPLEMENTED** — all 11 modules exist and are reachable from the two CLIs
  (`lib/decode.mjs` added in revision 2); `node --check` passes on each.
- **TESTED** — the commands in §3 were executed, with the exit codes shown,
  including the revision-2 runs of preflight, dry-run, catalogue check and both
  validator modes, plus the decoder negative controls in §11. There are no unit
  tests for this utility and none are claimed. The existing project suites
  (`frontend/tests/`, backend tests) were **not** run; they are unaffected because
  no application file was changed by this task.
- **VERIFIED** — **nothing.** No clip has been heard, played in a browser or
  confirmed to contain its intended words. One file (the silent pause) is now
  codec-decoded by two independent tools, which is strong evidence that it is a
  valid WAV — but it contains no speech, so it verifies the format, not the
  product.
- **ACCEPTED** — nothing.

## 6. Blockers and open items

1. **The API key — the only thing preventing delivery, and it is now a rejected
   key rather than a missing one.** `.env.local` at the repository root contains
   `GEMINI_API_KEY`; the utility resolves it and Google rejects it:
   `400 API key not valid` on both `GET /models` and the synthesis probe, which the
   client classifies as `api-key-invalid` (blocking, `stopRun`). The resolved value
   is 35 characters and does not begin `AIza`, while an AI Studio key is 39
   characters beginning `AIza` — consistent with a truncated or partial paste.
   Nothing about the model id, voice or text can fix this. Preflight now prints the
   key's length (never its value) so this is diagnosable without echoing a secret.
   To proceed: re-copy the complete key from AI Studio into `.env.local`, then run
   `--preflight-only`, then `--smoke`, then `--all`. **Revision 3 added a second
   provider (ElevenLabs) so the same job can be done without Google**, but that path
   is likewise blocked until a real `sk_…` key is supplied — see §12.
2. **Decoder now present and used (revision 2).** `ffmpeg` and `ffprobe` 9.1
   (`full_build-www.gyan.dev`, installed via WinGet into
   `C:\Program Files\WinGet\Links`) are available. `lib/decode.mjs` uses them:
   ffprobe reports the decoded stream facts and ffmpeg decodes every sample to a
   null sink; `validate.mjs` cross-checks both against the container declaration
   and records the method per row (`decodeVerifiedBy`). No transcoding, resampling
   or MP3 output is produced — nothing asks for it.
3. **Listening review outstanding — mandatory.** No clip has been heard. The 14
   Bangla clips require a native or fluent speaker before any demo use. No script
   in this utility can substitute for that review: a clean decode proves the
   samples are readable, not that the words are right.
4. **`en.phrase.no-room` carries a declared override awaiting an owner decision.**
   The catalogue cell reads `" please come to the front."` while the approved
   `content.js` template is `"Token number {number}, please come to the front."`
   and the parallel Bangla row does include the comma. The clip is recorded
   **with** the comma and the deviation is printed by `--check-catalogue` and
   warned about by `validate.mjs`. The catalogue document is left unmodified —
   correcting it belongs to its owner. Until then, catalogue cell and recording
   knowingly differ by one comma.
5. **No playback engine.** The frontend still speaks through
   `window.speechSynthesis`. These files are not heard in the application until a
   prerecorded-audio engine loads `manifest.json`, maps an announcement to
   language + phrase/number clips, composes the number and room inserts, and
   honours the silent pause asset. `integratedWithApplication` stays `false`.
6. **Loudness unverified.** No normalisation is applied and no per-device level
   check exists; the clinic hardware must be checked by ear.

## 7. Deviations and incidents (disclosed)

- **Superseded drafts retained, not deleted.** An earlier partial `generate.mjs`
  and an earlier `validate.mjs` draft are kept under
  `scripts/que-006-audio/.work/` (`generate.mjs.old-partial`,
  `validate.mjs.superseded-draft`). The working files were rewritten, not
  patched, because the drafts lacked the catalogue-integrity and
  manifest-consistency checks this report relies on.
- **Encoding incident, repaired and verified.** A PowerShell
  `Get-Content` / `Set-Content -Encoding utf8` round-trip re-encoded
  `validate.mjs` and mangled its non-ASCII characters. The file was restored with
  a purpose-built reverse-mapping helper
  (`scripts/que-006-audio/.work/fix-encoding.cjs`), the BOM was stripped,
  `node --check` passed, and the Bangla strings now print correctly (§3).
  Lesson recorded in the utility's working notes: never round-trip these UTF-8
  files through `Get-Content`/`Set-Content`; use Node or `[System.IO.File]`.
- **Dry-run boundary honoured.** The Git safety rule was followed: nothing was
  staged, committed, reset, cleaned or stashed. `scripts/` and
  `frontend/public/` remain untracked; the pre-existing uncommitted changes to
  `docs/governance/AMSDP_Docs_Index_V1.0.md`, `frontend/lib/announcements/content.js`,
  `frontend/pages/queue.js` and the two `frontend/tests/` files were left exactly
  as found, apart from the deliberate index registration described in §8.

## 8. Governance and skill compliance

**Domain routing (§4).** The task spanned three rows:

- *LLM / AI tooling* → §8 LLM Execution Routing Policy and the AI Factory
  documentation boundary. Applied: this task calls a hosted multimodal API from a
  standalone script; it does not route agent execution through the local Ollama
  model, so §8's local-model rule does not apply to a TTS HTTP client. No
  `ai_factory/` code was touched.
- *Audit / data integrity* → `saas-observability.md` (adapted, redaction rule).
  Applied: the API key is redacted from every diagnostic, never written to state
  or manifest, and `.env.local` is expected to be git-ignored; the manifest is a
  provenance record, not an audit-trail substitute.
- *Documentation* → §11 output location, §12 reading policy.

**Documents read (paths actually opened in this session).**

- `docs/governance/AMSDP_Docs_Index_V1.0.md` (navigation; §2 step 3, §12)
- `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` (the asset table
  the code transcribes, and its proposed manifest schema)
- `docs/implementation/QUE-006_Doctor_Name_Removal_and_Audio_Catalogue_Implementation_Report.md`
  (the approved wording and the state of QUE-006 before this task)
- `frontend/lib/announcements/content.js` (read as text by
  `lib/approved-templates.mjs`; read-only, not modified)

**Skills (§5).** **No skill was used, because none is installed.** No
`.clinerules/skills/`, `.claude/skills/` or repository `skills/` directory exists
in this workspace. Per §5 the relevant project governance documents were used
instead; this is stated rather than dressed up as skill usage.

**Non-negotiables (§3) — how each was honoured:**

| Rule | How it was honoured |
|---|---|
| Never log or expose secrets | Key resolved once, held in memory, every diagnostic through `redact()`; the key never reaches state, manifest, filename, log or this report |
| UI is never the safety boundary | Not applicable — no UI was built or changed |
| Server-side authorization | Not applicable — no endpoint, no tenant data, no request-body principal |
| Cross-tenant / cross-branch → 404 | Not applicable — no org/branch-scoped data touched |
| Single tenant key | Not applicable — no schema or query touched; no second tenant column exists after this task |
| Audit trail append-only | Nothing written to any audit table; a standalone script holds no DB connection |
| Denials recorded | Not applicable — no authorization decision is made by this utility |
| Forward-only idempotent migrations | No schema change; no Alembic revision was created |
| Never claim unverified capability | Every claim in §3 is tied to a command that ran; VERIFIED is explicitly empty; no CI gate is claimed |
| No tool/library because it was merely discovered | Zero new dependencies; Node built-ins only |

**Execution boundaries (§9).** Scripts were executed only to verify the utility,
which the task required; the application was not started and its test suites were
not run. Terminal output was kept small. No destructive git command was issued.
The pre-existing modifications in the working tree were left intact.

**Evidence standard (§7).** IMPLEMENTED and TESTED are claimed with named
commands and observed exit codes. VERIFIED and ACCEPTED are claimed for nothing.

## 9. How to finish the job

```powershell
# 0. replace the rejected key in .env.local with the complete AI Studio key
#    (preflight prints its length, never its value: 39 characters is right)
node scripts/que-006-audio/generate.mjs --preflight-only

# 1. prove key + model + voice with one very short synthesis
node scripts/que-006-audio/generate.mjs --preflight-only

# 3. four clips, cheaply, then listen to them
node scripts/que-006-audio/generate.mjs --smoke
node scripts/que-006-audio/validate.mjs --allow-missing

# 4. the remaining clips (resumable; already-valid clips are skipped)
node scripts/que-006-audio/generate.mjs --all

# 5. full structural validation
node scripts/que-006-audio/validate.mjs
```

Step 5 can reach "28/28 ready" and still leave the real review undone: it will
not tell you whether a Bangla digit sounds like that digit. That remains human
work, and it is the only remaining gate before these files could be used in a
demo — together with the playback engine that does not exist yet.

## 10. Summary

- 11 modules and one README in `scripts/que-006-audio/` (10 at revision 1, plus
  `lib/decode.mjs` at revision 2); no dependency added; no application file
  changed; nothing committed.
- Catalogue integrity is machine-checked against both the catalogue document and
  the approved `content.js` wording, and passes.
- The utility fails closed: without a key it exits 2 and writes nothing; with a
  rejected key it exits 3 and names the real cause instead of blaming the model;
  with no decoder it says so instead of claiming a decode; with 27 clips absent it
  reports 1/28 ready and refuses to call the catalogue complete.
- Audio generation is blocked on a **valid** `GEMINI_API_KEY` alone. Everything
  else needed to finish is in the utility and documented in its README.

## 11. Revision 2 — 2026-11-20: rejected key diagnosed, real decoder added

Trigger: the project owner reported that `GEMINI_API_KEY` had been added to
`.env.local` and that `ffmpeg` 9.1 (`full_build-www.gyan.dev`) was installed.

**What the session established, in order.**

1. **The key resolves and Google rejects it.** `--preflight-only` read the key from
   `.env.local` and received `400 API key not valid. Please pass a valid API key.`
   on `GET /models`, `GET /voices` and the synthesis probe. No request succeeded, so
   no audio could be produced. `.env.local` holds exactly one line
   (`GEMINI_API_KEY=…`, 50 bytes) with no quotes, no whitespace and no placeholder
   marker, so the paste itself is clean; the value is simply 35 characters and does
   not start with `AIza`. A Google AI Studio key is 39 characters starting `AIza`.
   No secret was printed at any point: the diagnostic reports length and two
   boolean shape facts only.
2. **Diagnostics were made to match the real failure.** Before this revision a
   rejected key produced `bad-request` with the guidance "check the model id, voice
   name and input text" — actively misleading. Two changes:
   - `lib/gemini-tts.mjs` now recognises key-rejection bodies
     (`API_KEY_INVALID`, `API_KEY_EXPIRED`, `API key not valid`, `API key expired`)
     **before** the generic 400 branch and classifies them `api-key-invalid` with
     `stopRun: true` and guidance that points at the key.
   - `lib/env.mjs` gained `describeKeyShape()`; `lib/preflight.mjs` reports the
     resolved key's length and shape (`api-key` is `warn` rather than `pass` when it
     is not 39 characters beginning `AIza`) and adds a warning naming truncation as
     the likely cause.
3. **The decoder is now real.** `ffmpeg`/`ffprobe` are installed under
   `C:\Program Files\WinGet\Links` (WinGet), but the agent shell's inherited `PATH`
   was stale and could not see them. `lib/decode.mjs` resolves them by name first,
   then from known install directories, so a stale shell no longer matters.
   `validate.mjs` now, per file:
   - reads the stream with `ffprobe -show_entries … -of json`;
   - decodes the whole file with `ffmpeg -v error -i <file> -f null -`;
   - requires a **positive measured duration** as part of the pass condition;
   - compares decoded rate/channels/bit depth/duration with the container's own
     declaration (±50 ms on duration), failing the row on disagreement;
   - records `decodeVerifiedBy`, `decodeDetail`, `decoderCodec` and
     `decoderDurationMs` per row, so the report states which method produced the
     evidence.
   The run header now prints the resolved tool versions, and the "does not
   establish" text no longer claims codec-level verification is impossible.
4. **The decoder was tested against deliberately broken files**, not only against a
   good one (`scripts/que-006-audio/.work/decode-negative-controls.mjs`):

   | Case | Decoder verdict | Container verdict |
   |---|---|---|
   | text file renamed `.wav` (160 B) | rejected — `Invalid data found when processing input` (ffprobe and ffmpeg) | `unrecognised container` |
   | 44-byte WAV header, no samples | **rejected** — ffmpeg exits 0 but ffprobe reports no duration, which the pass condition requires | `data chunk is empty`, `digitally silent` |
   | real 300 ms WAV truncated to 1,044 B | **accepted** — ffmpeg decodes PCM without error, measuring 21 ms | `RIFF size 14444 exceeds file size 1044`, `data chunk declares 14400 bytes but only 1000 are present` |
   | control: the real 300 ms pause asset | accepted — `pcm_s16le`, 300 ms | parses, silent as intended |

   The third row is the important one: PCM carries no checksums, so ffmpeg cannot
   detect a truncated tail. This is why the container parse and the decoded-vs-
   declared duration comparison both remain mandatory, and why the README states
   the decoder's limits instead of implying a decode settles everything.
5. **Nothing was generated.** After the fixes, `--preflight-only` still exits 3 on
   `api-key-invalid`, so the pause asset remains the only file on disk and
   `manifest.json` still reports `ready 1 / total 28`.

**What revision 2 did not do.** It did not obtain a working key, generate or listen
to any clip, build the playback engine, resolve the `en.phrase.no-room` override, or
flip `integratedWithApplication`. Evidence levels in §5 are unchanged: the utility
is IMPLEMENTED and TESTED, nothing is VERIFIED or ACCEPTED.

**Files changed in revision 2.** `scripts/que-006-audio/lib/decode.mjs` (new),
`validate.mjs`, `lib/gemini-tts.mjs`, `lib/env.mjs`, `lib/preflight.mjs`,
`lib/audio-file.mjs` (header comment only), `README.md`, this report, and
`docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 38 entry and the size/date of
this report). No application file, no `frontend/` file and no tracked project
document other than the index was touched; nothing was staged or committed.




## 12. Revision 3 — 2026-11-20: ElevenLabs added as a selectable provider

Trigger: the project owner asked whether `$env:ELEVEN_LABS_API_KEY = "sk_xxx"`
would let the utility use ElevenLabs. The literal answer was **no** — that command
sets a variable that dies with the shell, `sk_xxx` is a placeholder rather than a
key, and nothing in the utility read that name. The owner then chose the option
"add an ElevenLabs provider (provider switch, `xi-api-key`, multilingual_v2 +
Flash v2.5, ffmpeg transcode to WAV)".

**Contract facts verified before writing code**, from
`https://elevenlabs.io/docs/api-reference/text-to-speech/convert.md` and
`https://elevenlabs.io/docs/models.md` (read 2026-11-20):

| Fact | Consequence in the implementation |
|---|---|
| `POST /v1/text-to-speech/{voice_id}?output_format=…`, auth header **`xi-api-key`** | A Gemini-style `x-goog-api-key` header would fail silently; the client sets `xi-api-key` only |
| Body is `{ text, model_id }`; `model_id` defaults to `eleven_multilingual_v2` | `eleven_multilingual_v2` is the default; `eleven_flash_v2_5` is a documented cheaper option, not the default |
| `output_format` is an enum of 28 values (`alaw_8000`, `mp3_*`, `opus_*`, `pcm_*`, `ulaw_8000`, `wav_*`) with default `mp3_44100_128` | The value is checked against that enum before a request; anything else is refused with the list |
| "PCM and WAV formats with 44.1kHz sample rate requires you to be subscribed to **Pro tier or above**" | `wav_44100` / `pcm_44100` are **not** used by default. Default is `wav_24000`, which needs no paid tier and matches the 24 kHz the Gemini path produced |
| A `wav_*` response is a complete WAV file (its own rate/depth/channels) | The normal path needs no decoder and no assumption about sample size |
| `language_code` "is not supported for multilingual_v2 models" | Never sent |
| `enable_logging` defaults to true; zero-retention is enterprise-only | Left at the default and **documented** in the README rather than silently changed; the text is the fixed announcement catalogue, no patient data |
| Regional hosts exist (`api.us…`, `api.eu…`, `api.in…`, `api.sg…`) | `ELEVENLABS_API_BASE` is configurable |
| Bengali: the models page states 29 languages for Multilingual v2, but the per-model language list returned HTTP 403 to this session's fetcher | **No claim is made that Bangla works.** Only a successful synthesis probe — and later a native speaker — can establish it |

**Design decisions, and why.**

- `wav_24000` rather than `pcm_*`: headerless PCM would force the utility to
  *assume* 16-bit samples and write a header to match. A wrong assumption produces a
  file that plays at the wrong speed and still passes a naive check. `pcm_*` is
  therefore **refused** with an explanatory message, and `wav_*` is used so the
  response declares its own format.
- One WAV guarantee, one pipeline: `lib/provider.mjs` is the only place that knows
  which service answered. It returns a WAV buffer, so `generate.mjs`, the atomic
  state record and `validate.mjs` are unchanged in what they accept. Lossy formats
  (`mp3_*`/`opus_*`) are converted with ffmpeg and the conversion is recorded per
  asset; with no ffmpeg the asset fails rather than being delivered unconverted.
- One error type: `lib/tts-error.mjs` defines `TtsError`, and both
  `GeminiError` and `ElevenLabsError` extend it. Retry/stop policy stays
  provider-independent, and each error carries `provider`.
- No invented voice id. There is no correct default voice, and a guessed id either
  404s or resolves to a voice nobody chose. `ELEVENLABS_VOICE_ID_EN` / `_BN` are
  required and `--list-voices` prints the ids, names and language labels the key can
  actually use.
- Classification order matters again: ElevenLabs returns **401** for a bad key
  (Google returns 400), a **402/quota** body for exhausted characters, and
  **400/422** for tier or format problems. Key rejection is tested first, then quota,
  then plan-gating, so the guidance cannot blame the voice or the text.
  Measurement that vindicated matching on the body rather than the status: the
  6-character placeholder `sk_xxx` was answered with **HTTP 401**, while a
  well-shaped 51-character but invalid key was answered with **HTTP 400** — both
  with `{"detail":{"status":"invalid_api_key","message":…}}`. A classifier keyed on
  `status === 401` alone would have mis-filed the second case as `bad-request` and
  blamed the voice or the format. Both are classified `api-key-invalid`.
- A concurrency 429 is retried, not fatal: the free plan permits two simultaneous
  requests while this utility sends one at a time, so a 429 there is transient
  rather than exhausted quota.
- Provider-aware preflight: the probe runs once **per configured voice** (English
  `"ok"`, Bangla `টোকেন`), because English passing says nothing about the Bangla
  clip. A rejected key short-circuits before any probe, so a wrong key costs zero
  billable requests.

**Verification actually performed in this revision** (commands run in the agent
shell on this machine; no key value was printed at any point):

| # | Check | Result |
|---|---|---|
| 1 | Syntax of every module (`node --check`, 16 files) | all pass |
| 2 | `--check-catalogue` (Gemini-era regression) | PASS — 28 rows agree with the catalogue document, composed templates identical, override still declared |
| 3 | `--dry-run --provider elevenlabs` | prints provider, `eleven_multilingual_v2`, `wav_24000`, `api key MISSING`; exit 0, no network, no writes |
| 4 | `--provider elevenlabs` with no key | exit **2** with guidance naming `ELEVEN_LABS_API_KEY` (and `ELEVENLABS_API_KEY` as accepted) — not the Gemini variable |
| 5 | `--dry-run` with the default provider | unchanged Gemini behaviour (`gemini-3.8-flash-tts`, `Kore`, key from `.env.local`), exit 0 |
| 6 | **Live API with a rejected key** (`ELEVEN_LABS_API_KEY=sk_xxx`) | real 401 reached `api.elevenlabs.io`; body `{"detail":{"status":"invalid_api_key","message":"Invalid API key"}}` classified **`api-key-invalid`** with `stopRun`, and the key-shape check flagged 6 characters / `sk_` prefix as a placeholder; exit **3**, nothing written |
| 7 | `--list-voices` with the same rejected key | exit **3**, classified error plus guidance — no unhandled exception, no stack trace |
| 8 | Rejected-key short-circuit | `[skipped] synthesis-probe: skipped: the key was rejected` — no billable attempt after a 401 |
| 9 | `validate.mjs --allow-missing` | exit 0, `1/28 ready`, decoder `ffprobe 9.1 + ffmpeg 9.1`, manifest recomputation agrees |
| 10 | Second rejection shape: a fake but **well-shaped** 51-character `sk_…` key | shape check reports "standard ElevenLabs shape" (pass); the API answers **HTTP 400** `API key is invalid.` — still classified `api-key-invalid`, probes short-circuited, exit 3 |

**What this revision did not do, and cannot claim.**

- It did **not** generate a single ElevenLabs clip: no valid key was supplied.
  Row 6 proves the client reaches the API and classifies a refusal; it proves
  nothing about synthesis.
- It does **not** claim Bangla support. The language list was unreachable (403), so
  the first real run must be `--preflight-only`, whose Bangla probe is the first
  evidence — and a native speaker's ear remains the only acceptable final check.
- It did not rebuild `frontend/public/audio/manifest.json`, so that file still
  describes the Gemini-era configuration; it is regenerated by any run, including
  `--rebuild-manifest`, and its `generator` block reports current configuration
  rather than a claim about older files.
- Evidence levels in §5 are unchanged: the provider layer is IMPLEMENTED and
  TESTED (syntax, argument handling, error classification against the live API);
  no audio is VERIFIED and nothing is ACCEPTED.
- Provider choice remains a **product decision**. No approved document names a TTS
  provider (`MVP_Feature_Catalogue_and_Acceptance_Checklist_V1.0.md` still reads
  "No TTS provider selected"), so this revision adds capability without declaring
  which engine the demo should ship with.

**Files changed in revision 3.** New: `scripts/que-006-audio/lib/elevenlabs-tts.mjs`,
`scripts/que-006-audio/lib/tts-error.mjs`, `scripts/que-006-audio/lib/provider.mjs`.
Modified: `scripts/que-006-audio/generate.mjs` (provider flag, `--list-voices`,
`--model`, `--voice-en/--voice-bn/--voice`, `--output-format`, provider-aware
preflight call, provider fields in state and manifest),
`scripts/que-006-audio/lib/preflight.mjs` (ElevenLabs checks + per-voice probes +
rejected-key short-circuit), `scripts/que-006-audio/lib/env.mjs` (per-provider key
resolution, provider-aware `describeKeyShape`, `sk_…`/`xi-api-key` redaction),
`scripts/que-006-audio/lib/gemini-tts.mjs` (`GeminiError extends TtsError`),
`scripts/que-006-audio/lib/decode.mjs` (`transcodeToWav`),
`scripts/que-006-audio/lib/manifest.mjs` (provider/format provenance),
`scripts/que-006-audio/README.md`, this report, and
`docs/governance/AMSDP_Docs_Index_V1.0.md` (this report's size/date and a
Revision 39 entry). No application, `frontend/` or other tracked project document
was touched; nothing was staged or committed.

---

## 13. Revision 4 — a real ElevenLabs key arrived, and exposed three defects

**Date:** 2026-11-21. **Task:** `AMSDP-QUE-006-GEMINI-TTS-UTILITY` (continuation).
**Outcome:** the key is real and authenticates against `api.elevenlabs.io`, but it
is **scoped for nothing this utility needs**, so **no clip was generated**. Three
defects in the revision-3 code were found by the live API and fixed.

### 13.1 What was actually in `.env.local`

The file held two variables. Neither was the one the utility reads:

| Variable found | Shape | What it actually was |
|---|---|---|
| `ELEVENLABS_VOICE_ID_EN` | 51 characters, `sk_3…` | the **ElevenLabs API key**, stored under a voice-id name |
| `GEMINI_API_KEY` | 35 characters, `sk-9…` | an `sk-` style key (OpenRouter/DeepSeek family), **not** a Google AI Studio key |

The first explains why every ElevenLabs run reported a missing key; the second
explains the `API_KEY_INVALID` refusals recorded in §11 for Google — the value was
never a Google key, so no amount of re-copying the *name* would have helped.

Repair (no value was printed, and `.env.local` is git-ignored via
`.gitignore:20 .env.*`): the file was backed up **outside the repository** to
`%TEMP%\amsdp-env-local-<timestamp>.bak`, then written back with the same two
values — the `sk_…` line **renamed** to `ELEVENLABS_API_KEY`, and a comment added
above the `sk-` line recording that it is not an AI Studio key. Values, order and
byte content were otherwise preserved. The `GEMINI_API_KEY` line was deliberately
**not** deleted: it is somebody's real credential and the owner decides its fate.

### 13.2 The key authenticates but is not scoped — and that was misclassified

Live responses from the genuine key (verbatim bodies, no key material):

| Call | Response |
|---|---|
| `GET /v1/models` | `401` `{"detail":{"status":"missing_permissions","message":"The API key you used is missing the permission models_read to execute this operation."}}` |
| `GET /v1/voices` | `401` `{"detail":{"status":"missing_permissions",… "voices_read" …}}` |

Revision 3 classified every 401 as `api-key-invalid` and advised "re-copy the key".
That advice is wrong here: the key is correct, its **scope** is not, and re-copying
cannot fix a missing scope. A user following that guidance would loop.

- **Defect 1 — fixed.** `classifyHttpError()` now tests `missing_permissions`
  **before** the rejected-key branch, classifies it `key-permissions` (stopRun, not
  retryable), names the missing scope, and points at
  `elevenlabs.io → Profile → API Keys` (add `voices_read`, or the synthesis scope)
  instead of at re-copying.
- **Defect 2 — fixed.** Preflight treated a failed `GET /models` as a hard failure,
  which would block a **synthesis-only least-privilege key** that is perfectly
  usable. A `key-permissions` error on `/models` is now a **warning** ("the
  configured model is used unverified"), a rejected key is still a hard failure, and
  the short-circuit for "skip the probes" now fires only on a `fail`, not on a warn.

- **Defect 3 — fixed.** A stale `ELEVEN_LABS_API_KEY=sk_xxx` left in one shell
  **silently shadowed** the complete 51-character key in `.env.local`; the only
  symptom was a 401, and it cost real diagnostic time in this session. `resolveApiKey()`
  now gathers every candidate in precedence order and refuses to let a value that
  cannot be a real key (wrong prefix, implausible length) win over one that can,
  returning the skipped values in `ignored`; `generate.mjs` prints
  `WARNING ignored an unusable key value from …` naming both sources. Nothing is
  overridden silently, and equal-shape values still obey the documented precedence.

### 13.3 Verification performed in this revision

| # | Check | Result |
|---|---|---|
| 11 | Key resolution, clean shell | `api-key: [pass] … 51-character key, standard ElevenLabs shape`, `key from .env.local (repository root)` |
| 12 | **Live `GET /models`** with the real key | reached the API, `401 missing_permissions … models_read`, now classified `key-permissions` |
| 13 | **Live `GET /voices`** with the real key | reached the API, `401 missing_permissions … voices_read`, classified `key-permissions`; `--list-voices` exits 3 with the scope-naming guidance **and** the dashboard-id fallback |
| 14 | Stale-env shadowing, forced | with `$env:ELEVEN_LABS_API_KEY='sk_xxx'` set, the run printed the `WARNING ignored an unusable key value from environment variable … (6 characters)` line and used the 51-character `.env.local` key |
| 15 | Syntax + regressions after the fixes | all modules pass `node --check`; `--check-catalogue` 0; both `--dry-run` paths 0; `validate.mjs --allow-missing` 0 |

### 13.4 State of the blocker, precisely

Generation is blocked by **two owner-only actions**, not by code:

1. **Grant the key scopes** (or create a key with them): `models_read`,
   `voices_read`, and the text-to-speech scope. Without `voices_read` this
   utility cannot discover a voice id; the dashboard's Voices → ID value can be
   passed with `--voice-en`/`--voice-bn` instead, but synthesis itself still needs
   its scope, which only the probe can confirm.
2. **Supply the two voice ids** once the listing works.

Consequently the evidence levels of §5 stand unchanged: the provider layer is
IMPLEMENTED and TESTED; **no audio is VERIFIED** (still 1/28 clips on disk, and that
one is Gemini-era); nothing is ACCEPTED. Bangla remains unproven for
`eleven_multilingual_v2` — the language list is still unreachable with this key
(403/insufficient scope), so the preflight probe plus a native speaker remain the
only acceptable evidence.

**Files changed in revision 4.** New: none.
Modified: `scripts/que-006-audio/lib/env.mjs` (candidate-based resolution that
cannot be shadowed by an unusable value, `ignored` reporting),
`scripts/que-006-audio/lib/elevenlabs-tts.mjs` (`key-permissions` classification
with the missing scope named), `scripts/que-006-audio/lib/preflight.mjs`
(least-privilege keys: listing permission errors are warnings; short-circuit only
on hard failures), `scripts/que-006-audio/generate.mjs` (shadowing warning,
dashboard-id fallback in `--list-voices`), `scripts/que-006-audio/README.md`
(scope table, shadowing note), this report, `.env.local` (variable **rename** only,
values preserved, git-ignored) and `docs/governance/AMSDP_Docs_Index_V1.0.md`.

