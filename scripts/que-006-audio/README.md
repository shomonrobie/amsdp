# QUE-006 Audio Generation Utility

Standalone tooling that generates, validates and manifests the 28 prerecorded
announcement clips listed in
`docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` (14 English,
14 Bangla) using **Gemini TTS** or **ElevenLabs TTS**. The provider is a flag
(`--provider gemini|elevenlabs`, default `gemini`); everything downstream — the
manifest, the state file and `validate.mjs` — is provider-agnostic because both
providers are made to return a WAV file.

It is deliberately **outside the application**: it shares no code with the
backend or the frontend, it runs only when a human invokes it, and it writes
files into `frontend/public/audio/` plus a `manifest.json` describing them. The
AMSDP frontend does **not** consume that manifest yet — see
[Integration status](#integration-status).

## Requirements

- Node.js 18 or newer (native `fetch`, `node:crypto`, ESM `.mjs`).
- **No npm packages.** No install step, no lockfile, no build: the utility uses
  Node built-ins only, so it cannot perturb either package's dependency tree.
- An API key for the chosen provider: `GEMINI_API_KEY` (Gemini) or
  `ELEVEN_LABS_API_KEY` / `ELEVENLABS_API_KEY` (ElevenLabs).

`ffmpeg`/`ffprobe` are **optional**. Neither is needed to generate with either
provider's default format, and `validate.mjs` uses them when present — as they
are on this machine (ffmpeg/ffprobe 9.1 via WinGet) — to add a real codec-level
decode to every row. They are also required for the one exception: an ElevenLabs
`mp3_*`/`opus_*` output format, which must be converted to WAV before delivery.
Without ffmpeg the utility refuses that combination instead of writing a file it
cannot describe. See
[Validation limits](#validation-limits--read-this-before-trusting-a-green-result).

## Files

| Path | Purpose |
|---|---|
| `catalogue.mjs` | The 28-asset table transcribed from the catalogue document, the rebuild/diff helpers, and the declared spoken-text overrides |
| `generate.mjs` | CLI: selection, preflight, synthesis, retries, state, manifest, catalogue self-check |
| `validate.mjs` | CLI: independent validation of the files and manifest on disk |
| `lib/audio-file.mjs` | WAV/MP3 container parsers, silence/peak measurement, SHA-256, silent-WAV writer |
| `lib/decode.mjs` | Optional real-decode evidence: ffprobe stream facts + a full ffmpeg decode, cross-checked against the container |
| `lib/gemini-tts.mjs` | Gemini client: request body, error classification, response extraction, model/voice listing |
| `lib/elevenlabs-tts.mjs` | ElevenLabs client: `xi-api-key`, `output_format` allow-list, error classification, model/voice listing |
| `lib/provider.mjs` | Provider selection, config resolution, and the guarantee that a response is always a WAV buffer |
| `lib/tts-error.mjs` | The single error shape both clients throw, so retry/stop rules are provider-independent |
| `lib/manifest.mjs` | Generation state (`.work/state.json`), atomic JSON writes, `manifest.json` construction |
| `lib/preflight.mjs` | Key, model, voice and one-clip synthesis probe |
| `lib/approved-templates.mjs` | Reads the approved wording from `frontend/lib/announcements/content.js` |
| `lib/paths.mjs` | Every path used by the utility, in one place |
| `lib/env.mjs` | Reads provider settings and the key (env → `.env.local` → `.env`), describes key shape, redacts secrets |
| `.work/` | Git-ignored working area: state, last-run record, master copies, superseded drafts |

## API key setup

The key is taken from the first source that has it, and the source is reported:

1. the provider's process environment variable,
2. `.env.local` at the repository root (git-ignored),
3. `.env` at the repository root.

| Provider | Variables read, in order |
|---|---|
| `gemini` | `GEMINI_API_KEY` |
| `elevenlabs` | `ELEVEN_LABS_API_KEY`, then `ELEVENLABS_API_KEY` |

Both ElevenLabs spellings are accepted because both are in circulation: the task
that commissioned this utility used `ELEVEN_LABS_API_KEY`, ElevenLabs' own
documentation uses `ELEVENLABS_API_KEY`. Whichever is set is the one reported.

```powershell
# current shell only
$env:GEMINI_API_KEY = '<your key>'
$env:ELEVEN_LABS_API_KEY = '<your key>'

# or persist for the signed-in user (a new shell is needed afterwards)
[Environment]::SetEnvironmentVariable('ELEVEN_LABS_API_KEY', '<your key>', 'User')
```

```bash
# or a file the utility reads automatically (repository root, git-ignored)
printf 'ELEVEN_LABS_API_KEY=%s\n' '<your key>' > .env.local
```

A shell variable set with `$env:NAME = '...'` lives only in that PowerShell
process, and the agent's shell is a different process — so a value set in your
window is invisible to a run started elsewhere. `.env.local` avoids that.

The reverse can also bite: a **stale** `$env:ELEVEN_LABS_API_KEY` left in a shell
takes precedence over `.env.local` and, if it is a placeholder like `sk_xxx`,
produces a `401` that looks like a bad key. The resolver therefore never lets a
value that *cannot* be a real key (too short, wrong prefix) shadow one that can,
and it prints a `WARNING ignored an unusable key value from …` line saying which
value was skipped and which was used instead. If that warning appears, clear the
stale variable (`Remove-Item Env:\ELEVEN_LABS_API_KEY`) or start a fresh shell.

The key is never printed, logged, written to `manifest.json`, or placed in a
command line by this utility; every diagnostic passes through `redact()`. Do not
paste a key into a report, an issue, a commit message or a chat.

`--preflight-only` reports the key's **shape** — its length and whether the
expected prefix is present — never its value:

| Provider | Expected shape | Failure the shape predicts |
|---|---|---|
| Gemini | 39 characters, starts `AIza` | HTTP 400 `API_KEY_INVALID`, which reads like a model problem |
| ElevenLabs | starts `sk_`, around 51 characters | HTTP **401 or 400** carrying `invalid_api_key` in the body |

Both cases are classified as `api-key-invalid` and stop the run, rather than
blaming the model, the voice or the text. On ElevenLabs the **status code is not
stable** — a 6-character placeholder was answered with 401 and a well-shaped but
invalid key with 400, both with `invalid_api_key` in the body — so the client
matches the body as well as the status. A shortened value is the usual cause;
`sk_xxx` is a placeholder, not a key. If preflight prints an unusual length,
re-copy the whole key before changing anything else.

### ElevenLabs key scopes

A key can be genuine and still fail, because a 401 also carries
`missing_permissions` when the key authenticated but was not scoped for the call.
That is a **different** error (`key-permissions`) with different advice: re-copying
the key cannot fix a missing scope.

| Scope | Needed for | If absent |
|---|---|---|
| `models_read` | `GET /models` — verifying the model id exists | **warning only**: the configured model is used unverified, which is legitimate for a least-privilege key |
| `voices_read` | `--list-voices`, and checking the configured ids are real | **warning only**: pass ids from the dashboard instead (`--voice-en`/`--voice-bn`) |
| text-to-speech (the synthesis scope) | `POST /text-to-speech/{voice_id}` | the probe fails naming the scope, and generation stops |

Verified against the live API: a real key without the read scopes reports
`401 missing_permissions … missing the permission voices_read` (or `models_read`).
The utility names the missing scope rather than telling you to re-copy the key.
Because a synthesis-only key is a valid configuration, listing failures are
warnings — the synthesis probe is the real test — while a rejected key remains a
hard failure.

## Configuration

The provider is chosen by `--provider gemini|elevenlabs`, or by
`QUE006_TTS_PROVIDER`; the default is `gemini`. Provider, model, voice and output
format actually used are recorded **per asset** in `manifest.json`, so changing a
setting later cannot retroactively relabel existing files.

**Gemini**

| Variable | Default | Meaning |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | API key |
| `GEMINI_TTS_MODEL` | `gemini-3.8-flash-tts` | TTS model for **both** languages |
| `GEMINI_VOICE_EN` | `Kore` | Voice for the 14 English clips |
| `GEMINI_VOICE_BN` | `Kore` | Voice for the 14 Bangla clips |
| `GEMINI_TTS_STYLE_EN` | *(none)* | Optional `speech_metadata` style annotation for English |
| `GEMINI_TTS_STYLE_BN` | *(none)* | Optional `speech_metadata` style annotation for Bangla |
| `GEMINI_API_BASE` | `https://generativelanguage.googleapis.com/v1beta` | API base URL |

**ElevenLabs**

| Variable | Default | Meaning |
|---|---|---|
| `ELEVEN_LABS_API_KEY` / `ELEVENLABS_API_KEY` | *(required)* | API key, sent as `xi-api-key` |
| `ELEVENLABS_TTS_MODEL` | `eleven_multilingual_v2` | Model id; `eleven_flash_v2_5` is the cheaper option |
| `ELEVENLABS_VOICE_ID_EN` | *(none — required)* | Voice id for English clips |
| `ELEVENLABS_VOICE_ID_BN` | *(none — required)* | Voice id for Bangla clips |
| `ELEVENLABS_VOICE_ID` | *(none)* | Used for both languages when the per-language value is unset |
| `ELEVENLABS_OUTPUT_FORMAT` | `wav_24000` | `output_format`; also settable with `--output-format` |
| `ELEVENLABS_API_BASE` | `https://api.elevenlabs.io/v1` | Regional hosts (`api.eu…`, `api.us…`) are supported |

No ElevenLabs voice id is defaulted or guessed. A made-up id either fails or
resolves to a voice nobody chose, so the utility fails closed with an instruction
instead: run `--list-voices`, which prints the ids, names and language labels this
key can actually use, then set the two variables above.

Two documented ElevenLabs details are encoded in the client because they change
behaviour: `pcm_*` output is **refused** (headerless samples whose bit depth would
have to be assumed, and a wrong guess mis-declares the WAV header), and
`wav_44100`/`pcm_44100` are avoided by default because the API restricts 44.1 kHz
PCM/WAV to Pro tier — `wav_24000` needs no paid tier and matches the 24 kHz the
Gemini path produces. `language_code` is never sent, since it is documented as
unsupported for `eleven_multilingual_v2`.

Privacy note: ElevenLabs logs generation requests by default (`enable_logging`
defaults to true; zero-retention mode is enterprise-only). The text sent here is
the fixed announcement catalogue — no patient data, no token numbers — but the
request history in the account will show those phrases. This is stated rather than
silently changed; the utility does not send `enable_logging=false`.

## Commands

Run everything from the repository root.

```powershell
# plan only: provider, selection, model, voices and which files already exist — no network, no writes
node scripts/que-006-audio/generate.mjs --all --dry-run

# verify key, model visibility, voice listing and one tiny synthesis probe
node scripts/que-006-audio/generate.mjs --preflight-only

# 4-asset smoke set before spending quota on all 28
node scripts/que-006-audio/generate.mjs --smoke

# the full catalogue (resumable — valid existing files are skipped)
node scripts/que-006-audio/generate.mjs --all

# one language, an explicit list, or a quota-capped run
node scripts/que-006-audio/generate.mjs --en
node scripts/que-006-audio/generate.mjs --asset en.digit.4,bn.digit.4
node scripts/que-006-audio/generate.mjs --all --limit 6

# regenerate a clip even though a valid file exists
node scripts/que-006-audio/generate.mjs --asset bn.phrase.no-room --force
```

Provider-specific:

```powershell
# which voices can this key use? (ids, names, language labels) — no generation
node scripts/que-006-audio/generate.mjs --provider elevenlabs --list-voices

# ElevenLabs, English first, with explicit voice ids and the cheaper model
node scripts/que-006-audio/generate.mjs --provider elevenlabs --en `
  --model eleven_flash_v2_5 `
  --voice-en <voice id> --voice-bn <voice id>

# a lossy output format: ffmpeg converts it to the WAV the catalogue delivers
node scripts/que-006-audio/generate.mjs --provider elevenlabs --asset en.digit.4 `
  --output-format mp3_44100_128
```

```powershell
# catalogue self-check: code vs document vs approved templates in content.js
node scripts/que-006-audio/generate.mjs --check-catalogue

# rebuild manifest.json from whatever is on disk, without calling the API
node scripts/que-006-audio/generate.mjs --rebuild-manifest

# validate the result, independently of the generator
node scripts/que-006-audio/validate.mjs
node scripts/que-006-audio/validate.mjs --allow-missing   # while generation is incomplete
node scripts/que-006-audio/validate.mjs --json            # machine-readable report
node scripts/que-006-audio/validate.mjs --quiet           # problems and verdict only
```

`generate.mjs` exit codes: `0` all selected assets valid · `1` at least one
asset failed · `2` no API key or bad arguments · `3` stopped on an
auth/permission/quota/model/format blocker (resume later with the same command).

`validate.mjs` exit codes: `0` pass · `1` failure(s) · `2` usage error.

## Output

```
frontend/public/audio/
  manifest.json                        describes every clip, including absent ones
  en/phrase/token-number.wav
  en/phrase/proceed-to-room.wav
  en/phrase/room-suffix.wav            300 ms silent WAV (punctuation-only asset)
  en/phrase/no-room.wav
  en/number/digit-0.wav … digit-9.wav
  bn/phrase/token-number.wav
  bn/phrase/room-prefix.wav
  bn/phrase/room-locative.wav
  bn/phrase/no-room.wav
  bn/number/digit-0.wav … digit-9.wav
```

Working area (git-ignored). `state.json` is the provenance record the manifest
is built from — keep it if the delivered files are kept:

```
scripts/que-006-audio/.work/
  state.json          per-asset generation record (model, voice, sha256, bytes, duration)
  last-run.json       summary of the most recent run
  master/<same layout> identical copy of every delivered file
```

A failed or invalid clip is **never** left in `frontend/public/audio/`: it is
written to `.work/` first, validated, and only then moved into place, so the
application cannot serve a half-written or non-audio file.

## Manifest and its honest claims

`manifest.json` (schema `AMSDP-QUE-006-audio-assets/2.0`) records per asset the
catalogue text, both file paths, both SHA-256 values, both format descriptions,
sample rate, channels, duration, `technicalValidationStatus`, `humanReviewStatus`,
the content expectation and the provenance of the source recording.

| Field | Meaning |
|---|---|
| `technicalValidationStatus` | `pass` — both files exist, decode, and match the contract. `missing` — a file is absent. `fail` — present but wrong |
| `contentStatus` | `speech`, `intentional-pause` (the punctuation asset), or `missing-recording` |
| `humanReviewStatus` | `pending` unless a person listened to **these exact playback bytes**. A re-encode resets it |
| `playbackDerivation` | `encoded-from-master`, `original-mp3-preserved` or `existing-conformant` |
| `origin` | the source file, its SHA-256 and format, and where its preserved copy lives |

`summary.complete` is true only when all 28 are technically valid, and
`playable.integratedWithApplication` is hard-coded `false` because the frontend
does not read this manifest yet: a green manifest must never be read as "the demo
now plays recordings". Technical validation is not pronunciation approval.

The generation-stage validator (`validate.mjs`) still runs and still checks the
catalogue against `content.js`. When `.work/standardisation.json` exists it reads
the 44.1 kHz contract from that record and compares checksums against it instead
of against the generation record, and it says so in its report rather than
quietly relaxing anything.

## Special handling — the punctuation-only asset

`en.phrase.room-suffix` has the spoken text `.`, a terminal full stop. Speaking
"dot" would be wrong — a full stop is a pause. The utility therefore writes a
deliberate 300 ms silent WAV (`PUNCTUATION_PAUSE_MS`) and states in the manifest
that the playback engine must insert a pause there instead of playing speech.
The same rule would apply to any future punctuation-only row.

## Declared spoken-text overrides

`catalogue.mjs` holds `SPOKEN_TEXT_OVERRIDES`: clips whose *recorded* text
deliberately differs from the catalogue cell, each with a written reason. Today
there is exactly one:

- `en.phrase.no-room` — the catalogue cell omits the leading comma, while the
  approved template in `frontend/lib/announcements/content.js` reads
  `Token number {number}, please come to the front.` (and the parallel Bangla
  row does carry the comma). Without it the concatenated English sentence has no
  punctuation before "please". The clip is recorded **with** the comma.

This is a finding for the product owner, not a silent fix: the catalogue table
and the catalogue document remain in agreement, and `--check-catalogue` prints
every override with its reason. Correcting the source cell belongs to the owner
of that document.

## Audio format

The delivery format is always WAV, whichever provider runs — that is the one
guarantee `lib/provider.mjs` enforces, because the catalogue, the manifest and
`validate.mjs` all expect it.

- **Gemini** returns base64 audio inside an interaction response. The utility
  decodes it, requires a WAV container, and rejects anything else rather than
  shipping an unplayable file. Expected properties: 24 kHz, 16-bit PCM, mono —
  each verified per file, since the API contract is not a per-response guarantee.
- **ElevenLabs** is asked for `wav_24000` by default. That body is a complete WAV
  file carrying its own sample rate, bit depth and channels, so no header is
  invented and nothing is assumed. `pcm_*` is refused for exactly that reason.
  If a lossy format is requested (`mp3_*`, `opus_*`), ffmpeg converts it to
  16-bit PCM mono WAV and the conversion and tool version are recorded per asset;
  with no ffmpeg the asset fails instead of being written unconverted.

No resampling or loudness normalisation is performed at generation time. `ffmpeg`
**is** installed (9.1, `C:\Program Files\WinGet\Links`) and is used by the
standardisation pass described next.

### Standardised delivery format (2026-11-21)

The generation stage above produced 24 kHz WAV. A separate, idempotent pass now
normalises the whole set to the delivery contract, and that is the state the
manifest describes:

| Role | File | Format |
|---|---|---|
| Master | `<name>.wav` | PCM WAV, 44.1 kHz, 16-bit, mono |
| Playback | `<name>.mp3` | MP3, 44.1 kHz, mono, 128 kbps CBR |

How each asset was derived (recorded per asset in `manifest.json`):

- English recordings were delivered **as MP3** by the provider, so that MP3 is
  the recording. The master is a decode of it to 44.1 kHz PCM, and the playback
  file is the original MP3 left byte-identical — decoding and re-encoding a lossy
  file would remove information for no gain.
- Bangla recordings were delivered as **M4A/AAC 48 kHz**. The master resamples to
  44.1 kHz PCM, and the playback MP3 is encoded **from that master**.
- One Bangla clip, `bn/phrase/room-locative.mpeg`, was supplied by hand and is an
  **MP3 stream inside a `.mpeg`-named file** (ffprobe: `mp3`, 48 kHz, mono, 1.82 s).
  The extension is misleading, so nothing infers a container from it — ffprobe
  reports what is actually there. That file is the recording: the master is derived
  from it and the playback MP3 is encoded from that master. Any future source whose
  name does not follow the `.m4a`/`.mp3` pattern must be declared in
  `ORIGINAL_SOURCE_BY_ID` (`lib/audio-standard.mjs`); without that declaration the
  pass would derive the master from our own 128 kbps playback.
- `en/phrase/room-suffix.wav` existed at 24 kHz as deliberate silence; it was
  rewritten in place at 44.1 kHz only after a verified copy was preserved.
- Nothing is trimmed, normalised, noise-reduced, pitch-shifted or time-stretched.
  No speech was regenerated.

Originals are preserved byte-for-byte in `frontend/.audio-originals-backup/`
(git-ignored, with sizes, SHA-256 and format facts in `ORIGINALS.json`).

```powershell
# preserve the originals, convert what is needed, rebuild manifest.json
node scripts/que-006-audio/standardise-audio.mjs

# show the plan without writing anything
node scripts/que-006-audio/standardise-audio.mjs --dry-run

# validate all 28 assets (12 checks) — exit 0 only when all pass
node scripts/que-006-audio/validate-audio-assets.mjs

# only check for missing files, or only verify checksums
node scripts/que-006-audio/validate-audio-assets.mjs --mode missing
node scripts/que-006-audio/validate-audio-assets.mjs --mode checksums

# rebuild manifest.json from the files on disk, or check whether it is stale
node scripts/que-006-audio/rebuild-audio-manifest.mjs
node scripts/que-006-audio/rebuild-audio-manifest.mjs --check
```

All four run from the repository root. `--allow-missing` reports absent assets as
pending work instead of failures; the strict default is deliberate, because a
missing Bangla clip must not look like a pass.

## Resume, retries and cost control

- A run is resumable at any time: clips that are already valid are skipped, and
  `--force` overrides that.
- Transient failures (429, 5xx, network) are retried up to 4 attempts with
  exponential backoff capped at 30 s. Auth, permission, quota-exhaustion,
  plan-restriction and model/voice-not-found responses are treated as blockers:
  the run stops immediately with exit code 3 rather than hammering the API.
  A concurrency 429 from ElevenLabs is the one deliberate exception — the free
  plan allows two simultaneous requests while this utility sends one at a time,
  so it is retried rather than treated as exhausted quota.
- `--smoke` (4 clips), `--limit <n>` and `--dry-run` exist to spend as little
  quota as possible before a full run.
- `--preflight-only` performs only very short syntheses (`"ok"` for English,
  `টোকেন` for Bangla) to prove key, model and voice work end to end. With
  `--provider gemini` that is one request; with `elevenlabs` it is one per
  configured voice, because English working says nothing about the Bangla clip.
  `--no-probe` skips only that step. A rejected key skips the probes entirely, so
  a wrong key never costs a billable request.

## Validation limits — read this before trusting a green result

`validate.mjs` proves that each file exists, is non-empty, its container parses
(RIFF chunk walk / MPEG frame headers), its declared rate/channels/bit depth are
sane, its duration is inside a plausible band for its category, it is not
digitally silent, its SHA-256 matches the generation record, no two clips are
byte-identical, and `manifest.json` agrees with both the catalogue and the disk.

**Decode depth is reported, not assumed.** Each row carries `decodeVerifiedBy`:

| Value | Meaning |
|---|---|
| `ffprobe+ffmpeg-decode` | ffprobe read the stream and ffmpeg decoded every sample with no error **and** the decoded duration is positive; the decoded rate/channels/bit depth/duration were compared with the container's own declaration |
| `riff-structure` / `mpeg-frame-header` | no decoder available in this run — the container parsed, nothing more |

What the decoder can and cannot catch, measured on this machine
(`scripts/que-006-audio/.work/decode-negative-controls.mjs`):

- a text file renamed `.wav` → ffprobe and ffmpeg both reject it (row fails);
- a 44-byte WAV header with no samples → ffprobe reports no duration, so the row
  fails even though ffmpeg exits 0;
- a WAV truncated mid-`data` → ffmpeg still "decodes" it cleanly, because PCM
  carries no checksums; the **container parse** catches it (declared data size
  exceeds the file) and the decoded duration (21 ms) contradicts the declared
  300 ms. This is why both layers run.

It does **not** prove:

- that a clip contains the correct words,
- that the Bangla is pronounced or intoned correctly,
- that the level suits the target clinic hardware.

Every generated file therefore still needs **human listening review**, and the 14
Bangla clips need a native or fluent speaker. That review has not been done, and
no script here can do it.

## Human review preparation — `preview/`

`preview/` is the review aid for the delivered clips: it composes the 28 assets
into whole announcements and plays them in a browser, so a human can judge them
before any playback engine is written. It is **outside** the application in the
same way the rest of this utility is — it reads
`frontend/lib/announcements/content.js` and `frontend/public/audio/`, and writes
only to `preview/generated/`.

| Path | Purpose |
|---|---|
| `preview/compose.mjs` | Plan a composed announcement: wording (delegated to the product's `buildAnnouncement()`), clip order, junction pauses |
| `preview/compose-wav.mjs` | CLI: write 20 composed WAVs (`samples/`), plus `samples.json`, `data.json`, `clip-analysis.json`, `source-baseline.json` |
| `preview/make-review-template.mjs` | CLI: write `review-template.csv` and `.md` from `samples.json` |
| `preview/server.mjs` | Loopback-only static server for the page, the clips, the composed samples and the JSON payloads |
| `preview/index.html`, `preview.css`, `preview.js` | The reviewer page: 20 samples, per-sample clip timeline, live composer |
| `preview/check-page.mjs` | Headless-Chrome check of the page over the DevTools protocol (12 checks, no dependency) |
| `preview/generated/` | Git-ignored build output (20 WAVs, 14.15 MB, plus JSON and the review record) |

```bash
node scripts/que-006-audio/preview/compose-wav.mjs          # build the 20 samples
node scripts/que-006-audio/preview/make-review-template.mjs # write the review record
node scripts/que-006-audio/preview/server.mjs --port 8617   # serve the page on 127.0.0.1 only
node scripts/que-006-audio/preview/check-page.mjs --port 8617 --page-port 9341
```

The composed samples are **byte-for-byte concatenations** of the delivered clips:
no ffmpeg, no re-encode, no trimming, no loudness change. Each sample's SHA-256
and per-segment source range is recorded in `samples.json`, and the run aborts if
any catalogue file changed underneath it (`source-baseline.json`). The 20 samples
use 0 ms of inserted pause by design — the clips' own trailing silence already
separates them; the page's composer lets the reviewer hear 0–300 ms and prints
the measured tail of each clip.

What this does **not** do: it does not approve anything (`humanReviewStatus` stays
`pending` for every asset), it is not the application's playback engine, and a
green `check-page.mjs` run proves only that the page renders, plays and refuses
correctly — never that an announcement sounds acceptable. The reasoning, the
measurements (Bangla clips carry 0.874–1.388 s of trailing silence each) and the
open items are in
`docs/implementation/QUE-006_COMPOSED_ANNOUNCEMENT_HUMAN_VERIFICATION_PREPARATION_REPORT.md`.

## Integration status

The AMSDP frontend still speaks announcements through the browser
`window.speechSynthesis` path. The clips produced here are **not** heard in the
application until a prerecorded-audio engine exists that loads `manifest.json`,
maps an announcement to `language → phrase/number` clips, composes them with the
number and room inserts, and honours the silent pause asset. That engine is
separate work and is not part of this utility.

## Limitations and open items

1. **API keys** — no clip can be generated without a key the provider accepts, and
   this is the current blocker on both paths. The Gemini key in `.env.local` is
   rejected with `API_KEY_INVALID`; the ElevenLabs path has never been run with a
   real key, so its synthesis is unproven (only its key rejection is verified, see
   the implementation report). 27 of 28 files are still pending.
2. **ElevenLabs is untested end to end.** The client, the preflight, the provider
   switch and the 401 classification are exercised against the live API with a
   rejected key; **no successful ElevenLabs clip exists**. Whether
   `eleven_multilingual_v2` speaks Bangla acceptably is explicitly *not* claimed —
   the model page lists 29 languages but its language list was not retrievable.
3. **Transcoding / loudness** — only the lossy-format conversion described in
   [Audio format](#audio-format) happens; no resampling and no loudness
   normalisation.
4. **Bangla listening review** — outstanding and mandatory before demo use, and
   doubly so for any provider change.
5. **`en.phrase.no-room` catalogue cell** — declared override awaiting an owner
   decision (see above).
6. **Playback engine** — not implemented; `integratedWithApplication` stays
   `false` until it exists.
7. **Loudness** — no normalisation and no per-device level check; the clinic
   hardware must be tested by ear.
8. **Provider choice is a product decision.** Both providers are implemented, and
   neither is declared correct for a hospital announcement voice by any approved
   document (`MVP_Feature_Catalogue…V1.0.md` still reads "No TTS provider
   selected"). Switching engine changes every clip, so it needs an owner decision
   plus a fresh listening review — not just a flag.
