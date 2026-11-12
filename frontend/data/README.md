# BanglaNameSense dataset — provenance and rules

`bangla_name_sense.json` in this folder is a **byte-identical copy** of the
BanglaNameSense source dataset. It is bundled into the frontend at build time and
searched locally in the browser; it is never uploaded, and no request is made per
keystroke.

## Source and version

| Item | Value |
|---|---|
| Upstream source | `~/bangla_name_sense/bangla_name_sense.json` (BanglaNameSense repository, working copy) |
| Integrated copy | `frontend/data/bangla_name_sense.json` |
| Local dataset version | `1.0.0-2026-11-10` |
| Imported on | 2026-11-10 |
| SHA-256 | `ac037c24ebaf0208324351352bd62cedf2de16fbfde6a7d02966c55b8879e51e` |
| Size | 80,517 bytes |
| Records | 718 (`total_count` = 718, matches the array length) |
| Distinct Bangla names | 701 (17 records repeat an existing `bn` string) |
| Fields per record | `bn` (Bangla name), `en` (English / transliterated alias), `gender` (dataset metadata) |
| License | **UNCONFIRMED** — authorship, provenance and redistribution rights must be confirmed before public redistribution |

The upstream file is preserved unchanged at its original location. This copy is
not edited by hand: to refresh it, replace the file and re-run
`npm run validate:dataset` (see below). The SHA-256 recorded here and in
`lib/bangla-name-sense/dataset.js` must then be updated in the same change.

## Rules this dataset obeys

- `bn` is the primary display value; `en` is an optional search alias.
- `gender` is **never** used for filtering, ranking or display. It is not read by
  the matcher and never reaches the UI.
- Duplicate `bn` values are suppressed at display time by
  `lib/bangla-name-sense/matcher.js`; the source file is never rewritten.
- No patient or other private application data may be added here. The validator
  fails if a record or the root object contains fields such as `mobile`, `phone`,
  `address`, `date_of_birth`, `nid`, `patient_id` or `organization_id`.

## Validate after any change

```bash
cd frontend
npm run validate:dataset      # or: node scripts/validate-bangla-name-sense.mjs <path>
npm test                      # full BanglaNameSense suite, including dataset checks
```

The command prints record counts, duplicate count and the search-index size, and
exits non-zero when the structure is invalid.
