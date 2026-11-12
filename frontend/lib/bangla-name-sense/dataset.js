/* BanglaNameSense — dataset metadata and index construction.
 *
 * Kept free of the JSON import itself (`import` attributes are not portable
 * between Next's bundler and Node's ESM loader), so this module is importable
 * by both the React component and the Node test suite. The component passes the
 * bundled JSON in; the tests pass the file read from disk. Same code path.
 */

import { createNameIndex } from './matcher.js';
import { validateDataset } from './validate-dataset.js';

/** Provenance record, mirrored in `frontend/data/README.md`. */
export const DATASET_SOURCE = Object.freeze({
  name: 'BanglaNameSense name dataset',
  file: 'data/bangla_name_sense.json',
  upstreamPath: '~/bangla_name_sense/bangla_name_sense.json',
  version: '1.0.0-2026-11-10',
  sha256: 'ac037c24ebaf0208324351352bd62cedf2de16fbfde6a7d02966c55b8879e51e',
  bytes: 80517,
  records: 718,
  distinctBangla: 701,
  importedOn: '2026-11-10',
  license: 'UNCONFIRMED — provenance and redistribution rights must be confirmed before publishing this dataset',
  metadataFieldsUnused: ['gender'],
});

/** An index that never suggests anything — used when the dataset is unusable. */
const EMPTY_INDEX = createNameIndex([]);

/**
 * Validate the dataset and build the search index.
 *
 * A broken dataset must never break patient registration: on validation failure
 * this returns an empty index (no suggestions) plus the errors, so the name
 * field keeps working as a plain text input.
 *
 * @param {unknown} raw parsed dataset JSON
 * @param {typeof DATASET_SOURCE} [meta]
 * @returns {{ok: boolean, validation: object, index: object, meta: object}}
 */
export function buildDataset(raw, meta = DATASET_SOURCE) {
  const validation = validateDataset(raw);
  const records = validation.ok && raw && Array.isArray(raw.names) ? raw.names : [];
  const index = validation.ok ? createNameIndex(records) : EMPTY_INDEX;

  if (!validation.ok && typeof console !== 'undefined') {
    console.warn('[BanglaNameSense] dataset validation failed — suggestions disabled',
      validation.errors);
  }

  return { ok: validation.ok, validation, index, meta };
}
