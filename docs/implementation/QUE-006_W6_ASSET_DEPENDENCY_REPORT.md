# QUE-006 W6 — Audio Asset Distribution and Cleanup (dependency report)

**Assignment ID:** `AMSDP-QUE-006-W6-ASSET-CLEANUP`
**Date:** 2026-11-21
**Status:** **DEPENDENCY REPORT ONLY — no file moved, renamed or deleted.** O-7/POD-7 is an open owner
decision and every asset in the tree is either in use, provenance evidence, or a retained original.

---

## 1. Counts, re-counted in this task (not carried over)

| Measure | Value | How |
|---|---|---|
| Files under `frontend/public/audio/` (excluding the manifest) | **71** | `Get-ChildItem -Recurse -File` |
| Referenced by the manifest (`masterFile` + `playbackFile`) | **56** (28 × 2) | manifest parse |
| Manifest itself | 1 | |
| **Unreferenced** | **15** — 493,073 bytes | set difference |
| Preserved originals outside `public/` | `frontend/.audio-originals-backup/` — 31 files (29 recordings + `ORIGINALS.json` + record) | directory count |
| Manifest assets | 28 (14 `en`, 14 `bn`) | `Group-Object language` |
| Categories | 8 `phrase`, 20 `number` | `Group-Object category` |
| Content status | 27 `speech`, 1 `intentional-pause` | `Group-Object contentStatus` |
| Human review | **28 pending** (no asset is approved) | `Group-Object humanReviewStatus` |

The earlier roadmap's figure of 15 unreferenced files **is confirmed** by this recount.

## 2. The 15 unreferenced files

| File | Bytes | What it is |
|---|---|---|
| `bn/number/digit-0.m4a` … `digit-9.m4a` (10) | ~32 KB each | The original Bangla source recordings (decision D-3 kept them) |
| `bn/phrase/token-number.m4a` | 35,457 | Bangla source |
| `bn/phrase/room-prefix.m4a` | 32,320 | Bangla source |
| `bn/phrase/no-room.m4a` | 40,430 | Bangla source |
| `bn/phrase/room-locative.mpeg` | 44,973 | The supplied Bangla recording, byte-preserved |
| `bn/phrase/room-suffix.wav` | 14,444 | An English-silence copy under a Bangla name — the mislabelled placeholder |

## 3. Dependency classification

| Class | Files | Used by |
|---|---|---|
| Playback files (served, referenced) | 28 `.mp3` | The built-in draft pack, every language, both room variants |
| WAV masters (referenced) | 28 `.wav` | Provenance + future re-encode — **not** played |
| Retained originals (unreferenced) | 13 `.m4a` + 1 `.mpeg` | Provenance only — no runtime dependency |
| Mislabelled placeholder (unreferenced) | `bn/phrase/room-suffix.wav` | Nothing. It must not be renamed to make it look used (POD-7) |
| Backups | `frontend/.audio-originals-backup/` | The only byte-for-byte copy of the 29 originals |
| Pack manifests | `frontend/public/audio/manifest.json` | The built-in pack; every playback file above is reached through it |

**No organisation-specific pack exists yet** (W3's server half is not implemented), so nothing in the tree
is currently referenced by an organisation pack — a fact that will change the moment W3 lands.

### 3.1 The minimum a working pack needs

| Variant | Assets | Count per language |
|---|---|---|
| No-room announcements | `phrase.token-number`, `phrase.no-room`, `digit.0…9` | 12 |
| With-room announcements | the above **plus** `phrase.room-prefix`/`proceed-to-room` and `phrase.room-locative`/`room-suffix` | 14 |

Both languages are therefore fully covered by the 28 referenced assets, and the `intentional-pause` clip
must be **published even though it is silent**, because the engine's gesture unlock and the English
with-room pause both depend on it.

## 4. Why nothing was removed

Removing the 15 files would be a **served-tree** change with three consequences the owner has not ruled on:

1. The `.m4a`/`.mpeg` files are the only record of what was actually recorded; the backup is outside
   `public/` but has not been re-verified byte-for-byte in this task.
2. `bn/phrase/room-suffix.wav` is a known defect (an English silence clip under a Bangla name). Deleting it
   destroys the evidence of the defect; renaming it would hide it.
3. No pack publication mechanism exists yet (W3), so any future reference to these files cannot be ruled out
   by the current catalogue alone.

Deleting them would therefore trade an open question for an irreversible act. **POD-7** asks the owner to
decide; until then the tree is untouched.

## 5. What a safe cleanup would look like (for the owner's decision)

1. Keep every WAV master and the whole backup — they are provenance, not payload.
2. Serve only `playbackFile` paths; the manifest already does this, so ignoring the unreferenced files costs
   nothing at runtime.
3. Remove the 13 `.m4a` + 1 `.mpeg` from the **served** tree only after `ORIGINALS.json` is re-verified
   against the backup (SHA-256 for all 29).
4. Decide `bn/phrase/room-suffix.wav` explicitly — keep it as documented evidence, or delete it and record
   the deletion. Never rename it.
5. Re-run the W6 count afterwards and diff it against this report.

## 6. Governance and skill compliance (`.clinerules` §6)

- **Domain (§4):** Asset distribution / operational hygiene. Applied: **no destructive action**; the
  report is the deliverable the assignment asks for when dependencies and rollback are not established.
- **Skills:** none installed (§5) — none claimed.
- **Non-negotiables (§3):** draft recordings untouched (DR-1); nothing deleted, moved or renamed; the audit
  trail of what was recorded is preserved.
- **Evidence:** every count in §1 is reproducible with the commands named in the table.
