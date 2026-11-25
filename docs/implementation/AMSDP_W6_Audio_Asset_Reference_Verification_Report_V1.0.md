# AMSDP — W6 Audio Asset Reference Verification Report V1.0

> **Task ID:** `AMSDP-PO-DECISIONS-2026-11-25` (POD-7 / W6 asset cleanup)
> **Version:** 1.0 · **Date:** 25 November 2026
> **Status:** **COMPLETE — verified by manifest comparison; one file removed, 70 untouched.**
> **Authority:** PO-08 Option B, POD-7 ("authorised to remove the unreferenced audio files **with the
> list recorded**"), 25 November 2026; brief limitation: *do not delete audio files under POD-7
> without first verifying and documenting the exact unreferenced file list.*

---

## 1. Why a static "is it referenced?" search would have been wrong

The earlier figure in circulation was **"15 unreferenced audio files"**. It came from searching the
code for filenames, and that method cannot work here: the playback layer **composes** paths at run
time (`<language>/number/digit-<n>.mp3`, `<language>/phrase/<phrase>.mp3`, plus a configurable
`basePath` for voice packs), so a file can be served without its name appearing anywhere in source.

The authoritative declaration is the served manifest, `frontend/public/audio/manifest.json`, which
names every asset's `masterFile`, `playbackFile` and `origin.file` together with its checksum.

## 2. Method

1. Read the manifest and collect **every** string value whose path ends in `.mp3`, `.wav`, `.m4a`,
   `.mpeg` or `.ogg` (recursively, at any depth).
2. Enumerate every file under `frontend/public/audio` (excluding the manifest itself).
3. Compare the two sets in both directions.

## 3. Result

| Measure | Value |
|---|---|
| Audio files on disk before the cleanup | **71** |
| Distinct asset paths declared in the manifest | **70** |
| Declared but **missing** on disk | **0** |
| On disk but **not declared** | **1** — `bn/phrase/room-suffix.wav` |
| Audio files on disk after the cleanup | **70** |

Per directory before the cleanup: `bn/number` 30 (ten digits × wav/mp3/m4a), `bn/phrase` 13,
`en/number` 20, `en/phrase` 8. Every one of the 70 declared paths resolves to a file; nothing the
manifest promises is absent.

## 4. The exact list acted on

| File | Why it is unreferenced | Disposition |
|---|---|---|
| `frontend/public/audio/bn/phrase/room-suffix.wav` | A **Bangla** master with **no manifest entry** and no Bangla consumer. The Bangla phrase actually served is `bn/phrase/room-locative.*`; the *English* `en/phrase/room-suffix.wav` **is** declared (`manifest.json:186`) and is untouched | **Removed.** The file was tracked by git first (`git rm`), so it is recoverable from history |

**Nothing else was deleted.** In particular the `.wav` masters, the `.m4a` originals and the `.mp3`
playback files that the manifest declares all remain — including the whole `en/phrase/room-suffix`
set.

## 5. Correction carried forward

The "**15 unreferenced**" figure is **withdrawn**. The measured position is one undeclared file out of
71, and after removal the tree and the manifest agree exactly (70 = 70). Any future cleanup must
repeat this comparison rather than a filename search; the manifest is the contract.

## 6. What this does not establish

- It does **not** establish that the audio is correct, audible or well-pronounced. That is **POD-11**
  (reviewer: **Faria Bushra**) and remains **unproven** — no human has confirmed audibility in the
  room, so MP-32's acceptance cell is still open.
- It does **not** re-encode, normalise or re-validate any asset. No checksum changed: the 70 remaining
  files are byte-identical to their declared `playbackChecksum` / `masterChecksum` values.
- It does **not** close **POD-1 / POD-3 / POD-8 / POD-9 / POD-10** (ranges, inter-clip gap, trailing
  silence, comma discrepancy, reference voice) — all carried forward by PO-08.

## 7. Document control

| Field | Value |
|---|---|
| Evidence | The comparison script, its JSON output and the resulting `git rm` are recorded in §3–§4; the file is recoverable from git history |
| Placement | `docs/implementation/` per `.clinerules` §11 |
| Registration | Docs Index **Revision 49** (D-5 first application) |

*End of report.*
