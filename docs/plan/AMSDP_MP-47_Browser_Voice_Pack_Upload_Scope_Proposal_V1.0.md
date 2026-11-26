# AMSDP — MP-47 Browser-Based Voice-Pack Upload — Scope Proposal V1.0

**Status:** **PROPOSED — not implemented, not tested, not accepted.** Product Owner-authorised as a *separate,
independently scoped* work package by **PO-D1 Option C** (26 November 2026). Awaiting detailed specification and
implementation authorisation.
**Written:** 26 November 2026 · **Repository:** `E:\amsdp` · **Branch:** `hackathon-mvp` @ `fd4d365`
**Authority:** `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §7 (PO-D1).
**Predecessor context:** `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` §2.1 and §12 (why
upload was excluded from MP-04) and §9.3 (the question that PO-D1 has now answered).

**What this document is.** A *scope proposal*: what the package would cover, what already exists and must be
reused, what depends on what, what could go wrong, which decisions are still the Product Owner's, and how the work
would be proved. It contains **no implementation** and commits to **no** format, size, retention or storage policy
of its own — every number quoted below is an existing constant in the codebase, cited with file and line.

---

## 0. Why this package exists

MP-04 gave an operator full administration of the voice-pack library — preview, validate, submit, approve, reject,
publish, retire, availability release, organisation configuration, platform defaults and rollback — **without
`curl`**, except at one point: creating a version. Creating a version is `POST /api/v1/voice-packs`, which takes a
complete JSON document with every audio asset base64-encoded inside it. That is a machine-to-machine contract, not
a form a facility administrator can fill in.

The MP-04 verification pass raised this as **PO-D1** (three options: A — leave it out; B — add a small upload form
to MP-04; C — its own work package). The Product Owner chose **C**, on the grounds that the approved MP-04 scope
should be preserved and the additional capability managed independently.

The consequence matters for how this work is judged: **MP-47 is not an MP-04 defect fix.** MP-04 is to be accepted
against its existing requirements. MP-47 is judged against the acceptance criteria in §10 of this document, on its
own evidence.

---

## 1. What already exists and must be reused

Nothing here is to be rebuilt. The inventory is the reason this package is smaller than it looks: the registry,
the validation engine, the storage layout, the access control and the audit trail all exist and are tested.

| Capability needed by the upload form | Already exists | Where |
|---|---|---|
| Create one pack version | `POST /api/v1/voice-packs`, `org.manage`, answers **201** with a counted summary or **422** with a complete `problems` list | `backend/organization/voice_packs.py:452` |
| The upload body contract | `VoicePackUpload` (id, language, voice_name, description, personality, version, manifest, compatibility, files[], organization_id) and `AssetPayload` (`path`, `contentBase64`, `checksum`) | `voice_packs.py:263`, `:257` |
| Whole-upload validation before any byte is written | `policy.validate_pack_upload()` → `{ok, problems, assets, bytes, checksums}`; never raises on hostile input | `backend/organization/voice_pack_policy.py:795` |
| Real container sniffing (extension is not trusted) | `sniff_container()`, `SUPPORTED_CONTAINERS = ("wav", "mp3", "m4a")`, `EXTENSION_CONTAINER` maps `mp4→m4a` | `voice_pack_policy.py:649`, `:623`, `:625` |
| Size / shape ceilings | `MAX_ASSET_BYTES = 8 MiB`, `MAX_PACK_BYTES = 64 MiB`, `MAX_PACK_ASSETS = 250`, sample rate 8000–48000, channels 1–2, asset duration 0.05–60 s | `voice_pack_policy.py:612`–`:619` |
| Content integrity | SHA-256 against **both** the file entry's own `checksum` and the manifest's `playbackChecksum` (B-10) | `voice_pack_policy.py:895`–`:907` |
| Path-traversal defence | `PACK_ID_RE`, `SAFE_SEGMENT_RE`, resolved-path comparison inside the pack root (two independent checks) | `voice_pack_policy.py:602`, `:610`; `voice_packs.py:213` |
| Storage | assets written under `AMSDP_VOICE_PACK_ROOT` (default `backend/var/voice-packs`), one directory per pack version, outside the web root | `voice_packs.py:59`, `:229` |
| Asset delivery and auditioning | `GET /{pack_id}/assets/{asset_path}` (declared-path allowlist, `queue.view`, non-disclosing 404) and `GET /{pack_id}/preview` (read-only descriptor + problems) | `voice_packs.py:406`, `:382` |
| Who may create | `VOICE_CONFIG_ROLES = ("super_admin", "org_admin")`; platform scope is `super_admin` only; a foreign organisation is a 404 | `voice_pack_policy.py:60`, `:63`, `:205`, `:233` |
| Version numbering | `policy.next_version()` — never reuses a number, never overwrites a published version | `voice_pack_policy.py:389`; `voice_packs.py:488` |
| Lifecycle after creation | validate → submit → approve → reject → publish → retire, each audited | `voice_packs.py:548`, `:580` |
| Audit | `voice_pack.created` with after-state and a reason naming the asset and byte counts; tenant packs to `audit_events`, platform packs to `platform_audit_events` | `voice_packs.py:191`, `:520` |
| A screen to land in | MP-04's library, buckets, filters, detail panel and refusal translator | `frontend/pages/voice-packs.js`, `frontend/lib/voice-pack-admin.js` |
| Test scaffolding for the API contract | `TestUploadContract` (201 summary, audit reason, tenant stamping, refusal-not-crash, cross-tenant 404, branch admin refused), `TestUploadAndPreview` | `backend/organization/tests/test_voice_packs_api.py:462`, `:418` |

**The gap is therefore narrow and specific:** a browser cannot easily produce that JSON body (base64 of up to
250 assets, with checksums), and there is no screen that lets a person choose files, see what will be uploaded,
and correct a refusal in one round.

---

## 2. Proposed scope — the twelve required areas

Each area is stated as a requirement with an identifier so the specification and the tests can trace to it.
`U-01…U-12` are the Product Owner's twelve points, in order.

### U-01 Uploading a new voice-pack version through the browser

A screen (extension of the MP-04 `/voice-packs` surface, or a dedicated `/voice-packs/new` route — a design choice,
see U-D9) where an authorised operator:

1. enters or confirms pack metadata: `id`, `language` (`bn`/`en`), `voice_name`, `description`, `personality`,
   optional `version`;
2. selects the audio file(s) for the pack's manifest entries;
3. uses **Submit** and receives either a 201 summary or a complete, itemised refusal.

**Reuse:** the request is the same `POST /api/v1/voice-packs` contract. The frontend composes the JSON body —
computing base64 and SHA-256 in the browser — rather than adding a second upload path to the backend. That keeps one
server-side validation engine, one audit action and one set of tests authoritative. Whether a *multipart* endpoint is
worth adding is option B in §4 and is deliberately **not** assumed here.

### U-02 Supported audio formats and file-size limits

**These are not new decisions.** The server already enforces, and any browser path must comply with:

| Constraint | Existing value | Source |
|---|---|---|
| Accepted containers | `wav`, `mp3`, `m4a` (a `.mp4` holding AAC is accepted as `m4a`) | `voice_pack_policy.py:623`, `:625` |
| Per-asset ceiling | 8 MiB (8,388,608 bytes) | `voice_pack_policy.py:612` |
| Per-pack ceiling | 64 MiB in total across all assets | `voice_pack_policy.py:613` |
| Asset count ceiling | 250 files | `voice_pack_policy.py:614` |
| Sample rate | 8000–48000 Hz | `voice_pack_policy.py:615`–`:616` |
| Channels | mono or stereo | `voice_pack_policy.py:617` |
| Asset duration | 0.05–60.0 seconds | `voice_pack_policy.py:618`–`:619` |

What the Product Owner still has to decide is **not** the numbers but their browser-side treatment — **U-D1**
(whether the form additionally narrows the accepted set for usability, e.g. WAV only) and **U-D2** (whether
base64-in-JSON transport is acceptable at 64 MiB, which inflates the request body by roughly a third).

### U-03 File validation and error reporting

Client-side: accepted-extension and size pre-checks with an immediate, local message, so a 40 MiB file that can never
pass is not uploaded first. Server-side: authoritative validation stays exactly where it is. The `422` body's
`problems` array (codes such as `file x.wav:asset_too_large`, `file x.wav:extension_mismatch`,
`asset a1:missing_required_asset`, `pack:too_large`) must be rendered **per problem, attached to the field or file it
concerns**, not as one opaque banner — and every problem in the first response must be shown at once, because the
endpoint deliberately returns the complete list so an upload is corrected in one round.

The refusal translator in `frontend/lib/voice-pack-admin.js` (`REFUSAL_KEYS`) currently covers lifecycle and policy
refusals; the new `file:`/`asset:`/`pack:` upload codes need Bangla *and* English strings in
`frontend/lib/i18n.js`, with a fallback that never shows a raw code to an operator.


### U-04 Previewing or checking uploaded audio before submission

Before the upload is sent, the operator can play each chosen file locally (`URL.createObjectURL` + `<audio>`), see
its name, size and computed checksum, and remove it. After a successful upload the existing MP-04 path is reused
unchanged (`GET /{pack_id}/preview` for the descriptor and problems, `/assets/…` for playback of the stored copy).
**No new audition mechanism is proposed** — MP-04 already owns auditioning, and the stored copy is the one a reviewer
must hear.

### U-05 Version creation and integration with the existing voice-pack lifecycle

A created version is `draft`, `validation_status` = `pass`/`fail`, `review_status` = `pending`,
`available_to_organizations` = `false`. It then follows the existing transitions validate → submit → approve →
publish → retire (`voice_packs.py:548`; `voice_pack_policy.py:114`). The upload form must offer **no** shortcut to
`approved`, `published` or `available`: nothing becomes selectable because an upload succeeded, and publication still
requires a named human reviewer (`voice_pack_policy.py:457`–`:519`). On 201 the screen shows the new version in the
library and points at the next legal step, mirroring the API's own `next` hint.

Version numbering: leave `version` empty and the server allocates `max + 1` within the `(organization_id, language,
voice_name)` family; entering an already-used number is a `409`. The form states which of the two behaviours it is
using **before** submission.

### U-06 Role and permission requirements

Creation requires `org.manage` **and** a role in `VOICE_CONFIG_ROLES` (`super_admin`, `org_admin`). Consequently
branch administrators, receptionists and doctors must not see the upload entry point at all — and, independently of
the UI, the endpoint continues to refuse them (`.clinerules` §3: a hidden button is not authorisation). The client
permission mirror in `frontend/lib/auth.js` must be re-checked against `backend/common/permissions.py` for
`org.manage` before the entry point is gated on it; the MP-04 pass found a real defect of exactly this kind for
`org.read`.

### U-07 Organisation and platform-level access restrictions

- An `org_admin` uploads into **its own** organisation; `organization_id` in the body is *compared*, never used to
  select scope (`voice_packs.py:263`, `:469`).
- A tenant administrator addressing the platform scope is refused (`platform_scope_forbidden`, 403).
- Cross-organisation attempts are **404**, never 403 (non-disclosing).
- Platform packs (`organization_id = NULL`) are created by `super_admin` only and stay invisible to tenants until
  `available_to_organizations` is set on the existing MP-04 screen.

### U-08 Audit events and traceability

Every successful upload writes `voice_pack.created` with the after-state and a reason naming asset and byte counts
(`voice_packs.py:520`). Permission denials (403) are refusals recorded by the shared authorisation layer. **`422`
validation refusals are currently returned to the client but not audited.** Whether upload validation refusals should
also be audited is **U-D5**: auditing them improves traceability, but lets any authorised operator write unbounded
audit rows by uploading junk. This proposal does not decide it and does not propose changing `audit.py`.

### U-09 Secure file handling, storage and access

Existing guarantees the browser path must not weaken:

- assets land only under `AMSDP_VOICE_PACK_ROOT`, in the version's own directory, at a policy-validated relative
  path, with a resolved-path comparison against the root (`voice_packs.py:213`–`:250`);
- the declared extension must match the bytes' real container (`sniff_container`, `voice_pack_policy.py:649`);
- **no** filesystem path is ever returned to a client, and no static URL serves a pack;
- assets are served only through the authenticated route, and an unpublished pack is streamed only to a caller who
  may administer it (`_may_stream`, `voice_packs.py:310`).

New handling introduced by this package is confined to the browser: reading files with `File.arrayBuffer()`, base64
encoding, hashing with `crypto.subtle.digest('SHA-256')`, and releasing object URLs on unmount. No server-side
storage redesign is proposed. Storage capacity, retention of superseded asset bytes and quota are **U-D3**/**U-D4** —
open, and not invented here.

### U-10 Failure handling and recovery

- Network failure mid-upload: nothing is stored for a `422` (validation precedes any write,
  `voice_packs.py:461`–`:472`). A failure *after* the row is created can leave a version whose assets are incomplete;
  the existing `_file_problems` check (`voice_packs.py:558`) already detects assets declared in the manifest but
  absent on disk, and that check is the recovery signal to surface.
- A `409` must say **which** of the two collisions occurred (duplicate pack id, or duplicate version number within
  the voice family) and what to change.
- Retry must not be silent: re-submitting the identical body after a `409` is not idempotent, so the form requires
  the operator to change the id or the version explicitly rather than retrying automatically.
- Browser-side state (files chosen, metadata typed) survives a server refusal, so a correction does not mean
  re-selecting every file.

### U-11 Frontend and backend tests

The proposed set is in §9. Because the backend contract already exists and is tested, the new tests are mostly
frontend plus integration.

### U-12 Browser verification and acceptance criteria

§10. Per `.clinerules` §7 nothing in this package may be called VERIFIED on the strength of a green suite; the
browser run is a separate, recorded artefact.

---

## 3. Non-goals

Explicitly **outside** this package, so its scope cannot creep:

- **Any change to MP-04.** Its screen, its transitions, its audit actions and its acceptance criteria stay as
  approved. If MP-47 lands, it adds an entry point; it does not re-open MP-04's evidence.
- **Any change to `POST /api/v1/voice-packs` semantics** under option A (the recommended transport). Validation,
  refusals, audit action and status on creation stay exactly as tested today.
- **Server-side audio processing** — transcoding, normalisation, loudness, trimming, waveform generation, speech
  synthesis. `ALLOW_SYNTHESIS_FALLBACK = False` (`voice_pack_policy.py:154`) stays false: a missing pack is never
  filled by a synthesised voice.
- **Installing packs on a facility PC.** That is the W5 agent (`scripts/que-006-agent/`), unchanged.
- **Clinical document upload.** `docs/product/AMSDP_MVP_SCOPE_V1.0.md:552` excludes medical document uploads; voice
  packs are platform configuration, and this package does not widen that exclusion.
- **Storage or deployment changes** — bucket, volume, quota, retention, CDN, virus scanning. Each is either an open
  Product Owner decision (§7) or explicitly out of scope for this package.
- **Retro-fitting existing packs**, bulk import, or editing a published version's assets (a published version is
  replaced by a new one; `assert_mutable`, `voice_pack_policy.py:445`).

---

## 4. Technical options

The decision to be taken at specification time is **how the browser's bytes reach the existing validator**. The
proposal recommends **A**.

### Option A — browser composes the existing JSON contract *(recommended)*

The form reads files with `File.arrayBuffer()`, base64-encodes each, computes SHA-256 with `crypto.subtle.digest`,
and posts the existing `VoicePackUpload` body.

- **Reuses** the whole server contract, its tests and its audit action; **no** backend change.
- **Cost:** the request body is ~4/3 the audio size (up to ~85 MiB for a maximal pack), so memory in the browser
  and a request-size limit somewhere in front of FastAPI both matter — that is U-D2, not an assumption.
- **Risk:** a large pack holds the whole payload in memory twice in the browser (File + JSON string). Bounded by
  64 MiB of audio, and the form can process files sequentially and warn above a threshold.

### Option B — new multipart endpoint on the backend

Add `POST /api/v1/voice-packs/upload` accepting `multipart/form-data`, streaming assets to a staging directory and
then running the same `policy.validate_pack_upload` on the staged bytes.

- **Advantage:** no base64 inflation; true streaming; a natural place for a per-request size limit.
- **Cost:** a second creation path means a second chance to forget a check, and the audit action, the 201 body and
  the refusal contract must be kept identical to the JSON path. Needs its own tests mirroring `TestUploadContract`.
- **Also opens** questions this package must not answer by accident: where staging lives, who cleans it up, and how
  a half-written staging directory is reaped.

### Option C — direct-to-object-storage upload with a presigned URL

- **Not proposed for the Hackathon Version.** It presupposes an object store and a retention policy that AMSDP has
  not chosen (U-D3/U-D4), and it moves validation away from the write (`validate_pack_upload` runs on bytes the
  server never saw until after the write). It stays on the table only if the Product Owner decides the storage policy
  itself.

**Recommendation:** A, with the request-size ceiling and the browser memory profile measured during implementation
rather than assumed. If measurement shows A is not viable at the documented ceilings, the correct response is to
bring that evidence back to the Product Owner — not to switch transport silently.

---

## 5. Dependencies

| # | Dependency | Why it blocks | Status |
|---|---|---|---|
| D1 | **PO-D1 decided** (Option C, separate package) | Defines the package and protects MP-04's scope | **MET** — `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §7 |
| D2 | MP-04 admin surface on `/voice-packs` | The upload entry point lands in an existing, tested screen; building the screen first would duplicate MP-04 | IMPLEMENTED, frontend TESTED, build VERIFIED (MP-04 report V1.1) |
| D3 | W3 creation API + its contract tests | Option A reuses them unchanged | IMPLEMENTED, TESTED (`test_voice_packs_api.py`, 6 upload-contract tests) |
| D4 | A reachable non-production PostgreSQL at `127.0.0.1:5433` | Nothing in this package can be VERIFIED without login tokens, seeded data and a live stack. **Currently unavailable** (connection refused, no Docker) | **BLOCKED** |
| D5 | Answers to U-D1…U-D9 | Formats/transport/roles/retention must be approved, not guessed | **OPEN** |
| D6 | Implementation authorisation | PO-D1 authorises the *proposal*, not the build | **REQUIRED** |

No new library is proposed. `crypto.subtle` and `URL.createObjectURL` are platform APIs; the frontend's existing
`apiFetch` helper carries the auth header.

---

## 6. Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | A second creation path (option B) drifts from the JSON contract, so an upload can bypass a check that `validate_pack_upload` makes | High | Medium | Prefer option A; if B is chosen, its tests must mirror `TestUploadContract` case-for-case and the audit action must be the same `voice_pack.created` |
| R2 | Request-size limits in front of FastAPI truncate or reject a legitimate pack with an opaque error | Medium | High (untested today) | Measure the real ceiling early; surface a specific, translated message instead of a generic network failure; record the ceiling as configuration, not as folklore |
| R3 | Browser memory exhaustion on a maximal pack (64 MiB audio → ~85 MiB base64, plus copies) | Medium | Medium | Sequential per-file processing, a warning above a documented threshold, and a measured browser run in the acceptance evidence |
| R4 | A client-side pre-check drifts from the server's rules (e.g. the UI accepts a container the policy refuses) and the operator gets a confusing two-stage refusal | Medium | Medium | One shared source of truth: the frontend test parses `voice_pack_policy.py` for the container list and ceilings, exactly as the MP-04 tests already parse the Python sources rather than trusting copies |
| R5 | The permission mirror in `frontend/lib/auth.js` disagrees with `backend/common/permissions.py` for `org.manage` — the MP-04 pass already found one such defect | High | Medium | Re-verify the mirror row before gating the entry point; add a test that reads both sources and fails on disagreement |
| R6 | An upload that "succeeds" is mistaken for a published voice | High | Low | The 201 body already carries `status: draft` and a `next` hint; the screen must display both and offer no publication shortcut |
| R7 | `422` refusals remain unaudited, so a disputed upload has no trail | Medium | Medium | U-D5 — an owner decision, not an agent's |
| R8 | Storage grows without bound as versions accumulate under `AMSDP_VOICE_PACK_ROOT` | Medium | High over time | U-D3/U-D4; out of scope to decide here, but it must not be silently ignored |

---

## 7. Outstanding specification and Product Owner decisions

None of these may be assumed by the implementer. Each changes behaviour a user can see or a policy the platform
enforces.

| # | Decision needed | Why it cannot be guessed | Suggested default (for the owner to accept, amend or reject) |
|---|---|---|---|
| **U-D1** | Does the browser form **narrow** the accepted containers below the server's `wav`/`mp3`/`m4a`? | A narrower set is friendlier but hides a legitimate server capability | Offer all three; the server remains authoritative |
| **U-D2** | Is base64-in-JSON transport acceptable at the documented ceilings (8 MiB/asset, 64 MiB/pack), or must a multipart path be authorised (§4 option B)? | It decides whether the backend changes at all | Accept A and measure; return to the owner if measurement fails |
| **U-D3** | **Storage location and capacity** for pack assets — is `backend/var/voice-packs` (or the `AMSDP_VOICE_PACK_ROOT` override) still the approved home, and what is the per-organisation quota? | No approved quota exists in the documents read | Keep the existing root; quota unspecified → no quota enforced yet, stated honestly in the UI |
| **U-D4** | **Retention of superseded asset bytes** — when a version is retired, are its files kept, archived or deleted? | `.clinerules` §3 forbids rewriting the audit trail; assets are a different question and no rule exists | Keep everything; add no deletion |
| **U-D5** | Should `422` validation refusals be **audited**? | It is an audit-trail policy decision with a cost (unbounded rows) | Do not audit 422s; audit 403s as today |
| **U-D6** | May an **`org_admin`** upload, or is upload platform-only? | Today `org_admin` may (it holds `org.manage`); a browser form makes that far easier to exercise, which may not be intended | Keep the tested behaviour: `org_admin` may upload into its own organisation |
| **U-D7** | Is a **human-readable manifest editor** in scope, or is the manifest supplied as a file alongside the audio? | The manifest is a structured catalogue; hand-editing JSON in a browser is a different product | Manifest uploaded as a `.json` file validated by the existing `validate_manifest`; no in-browser editor |
| **U-D8** | Must an operator **confirm** the SHA-256 shown in the UI against an externally supplied digest before submission? | This is a supply-chain control some owners require and others find obstructive | Show the digest; do not make it a required confirmation |
| **U-D9** | Route and placement: extend `/voice-packs` with a panel, or add `/voice-packs/new`? | Affects navigation, the i18n key set and the browser acceptance script | A panel on the existing page, behind the `org.manage` gate |

If any answer above is "not yet", the correct outcome is that the package waits — not that the implementer picks.

---

## 8. Security and negative paths

The browser is untrusted input by definition; the server checks are the authorisation, and every one of them must
be exercised through the *new* surface too. The hostile cases this package must prove, all already understood by
`validate_pack_upload`:

| # | Attempt | Required outcome |
|---|---|---|
| N1 | A `.mp3` that is really an executable or a WAV | `422`, `file …:unrecognised_container` or `extension_mismatch`, nothing written |
| N2 | `path` containing `../` or an absolute path | `422`, `file …:invalid_path`-class code, nothing written |
| N3 | A file larger than 8 MiB / a pack larger than 64 MiB / more than 250 files | `422`, `asset_too_large` / `pack:too_large` / manifest refusal |
| N4 | Audio that differs from the manifest's `playbackChecksum` | `422`, `manifest_checksum_mismatch` (B-10) |
| N5 | A required manifest asset not supplied | `422`, `asset …:missing_required_asset` |
| N6 | Upload while signed in as branch administrator / receptionist / doctor | hidden in the UI **and** `403` from the API |
| N7 | Upload naming another organisation's `organization_id` | `404` (non-disclosing), never `403` |
| N8 | `org_admin` addressing the platform scope | `403`, `platform_scope_forbidden` |
| N9 | Re-use of an existing pack id, or of an existing version number in the family | `409` with a distinguishable message |
| N10 | Fetching an asset of an unpublished pack as a non-administrator | `404` |
| N11 | A crafted manifest path that resolves outside the pack root | `422` at write time, and `404` on read |
| N12 | Upload that succeeds and is then assumed published | `status: draft`, `review_status: pending`, `available_to_organizations: false`, not selectable |

No credential, token or filesystem path may appear in any error the new surface renders (`.clinerules` §3).

---

## 9. Proposed tests

**Backend** — expected to be **zero new tests** under option A, because the endpoint is unchanged; the package must
still *re-run* the existing contract suite and record the result. Under option B, a mirror of
`TestUploadContract` (201 summary, audit reason, tenant stamping, refusal-not-crash, cross-tenant 404, branch admin
refused) is mandatory.

**Frontend (`node --test` `.test.mjs` files under `frontend/tests/`, following
`voice-pack-admin.test.mjs`)** — new cases:

- the entry point is visible to `org_admin`/`super_admin` and **absent** for branch admin, receptionist and doctor;
- metadata validation refuses empty `id`/`voice_name`/`description`/`personality` before submission;
- a file with a refused extension is rejected locally with a translated message, and nothing is posted;
- a file above the ceiling is rejected locally, and the ceiling is the one **parsed from `voice_pack_policy.py`**,
  not a copied constant;
- SHA-256 computed in the test's harness matches the payload actually posted;
- a `422` with several `problems` renders **every** problem, each translated, none as a raw code;
- a `409` renders the collision-specific message;
- a `201` renders `draft` + the `next` hint and offers no publication shortcut;
- the `org.manage` mirror row in `frontend/lib/auth.js` agrees with `backend/common/permissions.py`.

**i18n** — every new key present in both `bn` and `en`; the existing one-off coverage audit pattern (resolve the
runtime-selected keys, assert zero missing per language) is repeated for the new keys.

**Browser verification (not automatable in this environment yet)** — `org_admin` signs in, uploads a small WAV pack,
sees the itemised refusal for a deliberately broken file, corrects it, gets a 201, finds the version in the library,
runs validate → submit → approve → publish, and the audit trail shows `voice_pack.created` with the expected counts.

---

## 10. Acceptance criteria

MP-47 may be called **ACCEPTED** only when all of the following hold, each with a recorded artefact:

1. **AC-47-01** All U-D decisions in §7 are answered by the Product Owner and reflected in the specification.
2. **AC-47-02** An authorised `org_admin` creates a version from the browser and it appears as `draft` in the
   library, with `validation_status` reflecting the server's verdict.
3. **AC-47-03** Every negative path N1–N12 produces the stated outcome, demonstrated individually.
4. **AC-47-04** No unauthorised role can reach or use the surface (UI absence **and** API refusal recorded).
5. **AC-47-05** A refusal with multiple problems is corrected in **one** round without re-selecting files.
6. **AC-47-06** The audit trail contains `voice_pack.created` with the correct scope (tenant vs platform trail) and
   counts for the accepted upload, and no audit row is altered or removed.
7. **AC-47-07** The full frontend suite and the unchanged backend contract suite pass in this tree, with counts
   recorded.
8. **AC-47-08** A production build succeeds (`next build`, exit 0) with the new route/panel in the summary.
9. **AC-47-09** Browser verification is recorded against a live stack and a seeded non-production database — not
   inferred from tests.
10. **AC-47-10** i18n coverage is complete in `bn` and `en`; no raw refusal code is user-visible.
11. **AC-47-11** No secret, token, filesystem path or storage URL appears in any response, log line or report.
12. **AC-47-12** MP-04 is untouched: its report's evidence still holds, and no MP-04 file is edited to accommodate
    MP-47.

Status today: **none of AC-47-01…AC-47-12 is met.** This is a proposal.

---

## 11. Governance and skill compliance

| Requirement (`.clinerules`) | How this document complies |
|---|---|
| §2 automatic routing | Domains identified: **frontend UI**, **backend API**, **multi-tenant data**, **audit**, **documentation**. `docs/governance/AMSDP_Docs_Index_V1.0.md` read; product/plan/decision documents loaded before writing |
| §3 non-negotiables | Server-side authority restated (U-06/U-07); 404-not-403 for cross-tenant; `organization_id` derived from the token, never the body; audit append-only, no deletion proposed; **no format, size, retention or storage policy invented** — existing constants cited by file:line, open ones pushed to §7 |
| §7 evidence standard | Status is **PROPOSED**; nothing claimed IMPLEMENTED, TESTED, VERIFIED or ACCEPTED. §10 lists the twelve criteria that are all currently unmet |
| §11 documentation output | Written to `docs/plan/` — the ratified home for plans, roadmaps and work-package registers. New filename, no collision; no existing document overwritten, moved or deleted |
| §12 reading policy | Documents read before planning; every claim about code cites the file opened in this session; no remembered paths were used |
| §9 execution boundaries | No code written, no schema touched, no test executed on behalf of this package, no commit/push/migrate/reseed/deploy |
| §5 skills registry | **No skill installed** for this domain. Governance documents and the existing codebase were used instead; no skill use is claimed |

**Reuse before invention.** Option A deliberately proposes *no new backend endpoint*: the package's value is a
browser surface over a contract that already exists, is validated in one place and is covered by six upload-contract
tests.

---

## 12. Document control

| Field | Value |
|---|---|
| Document | `docs/plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md` |
| Work-package id | **MP-47** — verified free: no `MP-47`/`MP-48`/`MP-49`/`MP-5x` occurrence anywhere in `docs/`, `backend/` or `ai_factory/docs/`; the highest identifier in issue is **MP-46** (`docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md`, `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`) |
| Authority | `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` §7 (PO-D1, 26 November 2026) |
| Status | **PROPOSED** — Product Owner-authorised as a separate package; awaiting U-D answers, specification and implementation authorisation |
| Version | V1.0 (first issue) |
| Supersedes | nothing |
| Related | MP-04 (admin surface), MP-23 (operational reporting), F-50 / QUE-006 (voice-pack registry), W3 API, W5 installer |
| Next action owned by | **Product Owner** — answer U-D1…U-D9 (§7) and authorise implementation, or park the package |

