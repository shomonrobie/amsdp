/* BanglaNameSense — dataset structural validation.
 *
 * Shared by the automated tests and by `frontend/scripts/validate-bangla-name-sense.mjs`
 * so a dataset refresh is checked with exactly the same rules the tests use
 * (Master Feature List §25.8.3 rule 2).
 *
 * The validator NEVER modifies the dataset: it only reports.
 */

import { normalizeBangla, hasBangla } from './normalize.js';

/* Fields that would put private application data into a public name list.
 * Their presence is treated as an error, not a warning (§25.8.3, README). */
const FORBIDDEN_FIELDS = [
  'patient_id', 'patientId', 'mobile', 'phone', 'address', 'date_of_birth',
  'dob', 'age', 'nid', 'email', 'appointment_id', 'organization_id',
];

/**
 * @param {unknown} dataset parsed JSON (root object)
 * @returns {{ok: boolean, errors: string[], warnings: string[],
 *            stats: {records: number, distinctBangla: number, duplicates: number,
 *                    banglaNames: number, withEnglishAlias: number,
 *                    gendersPresent: boolean}}}
 */
export function validateDataset(dataset) {
  const errors = [];
  const warnings = [];

  const stats = {
    records: 0,
    distinctBangla: 0,
    duplicates: 0,
    banglaNames: 0,
    withEnglishAlias: 0,
    gendersPresent: false,
  };

  if (!dataset || typeof dataset !== 'object' || Array.isArray(dataset)) {
    errors.push('root value must be an object');
    return { ok: false, errors, warnings, stats };
  }

  const rootKeys = Object.keys(dataset);
  for (const forbidden of rootKeys) {
    if (FORBIDDEN_FIELDS.includes(forbidden)) {
      errors.push(`root must not contain patient/application data field "${forbidden}"`);
    }
  }

  const { names } = dataset;
  if (!Array.isArray(names)) {
    errors.push('missing "names" array');
    return { ok: false, errors, warnings, stats };
  }
  stats.records = names.length;

  if (dataset.total_count == null) {
    warnings.push('missing "total_count" declaration');
  } else if (typeof dataset.total_count !== 'number') {
    errors.push('"total_count" must be a number');
  } else if (dataset.total_count !== names.length) {
    errors.push(`"total_count" ${dataset.total_count} does not match ${names.length} records`);
  }

  const seenBangla = new Set();

  names.forEach((record, i) => {
    const where = `names[${i}]`;

    if (!record || typeof record !== 'object' || Array.isArray(record)) {
      errors.push(`${where} must be an object`);
      return;
    }

    for (const key of Object.keys(record)) {
      if (FORBIDDEN_FIELDS.includes(key)) {
        errors.push(`${where} must not contain patient/application data field "${key}"`);
      }
    }

    const bn = record.bn;
    if (typeof bn !== 'string' || !bn.trim()) {
      errors.push(`${where}.bn must be a non-empty string`);
    } else {
      if (!hasBangla(bn)) errors.push(`${where}.bn contains no Bengali-script characters`);
      stats.banglaNames += 1;
      const key = normalizeBangla(bn);
      if (seenBangla.has(key)) stats.duplicates += 1;
      else seenBangla.add(key);
    }

    const en = record.en;
    if (typeof en !== 'string' || !en.trim()) {
      errors.push(`${where}.en must be a non-empty string`);
    } else if (hasBangla(en)) {
      warnings.push(`${where}.en contains Bengali script (expected a Latin alias)`);
    } else {
      stats.withEnglishAlias += 1;
    }
  });

  stats.distinctBangla = seenBangla.size;
  stats.gendersPresent = names.some((r) => r && r.gender != null);

  if (stats.duplicates > 0) {
    warnings.push(`${stats.duplicates} duplicate Bangla name record(s) — suppressed at display time, source preserved`);
  }
  if (stats.withEnglishAlias !== stats.records) {
    warnings.push(`${stats.records - stats.withEnglishAlias} record(s) have no usable English alias`);
  }

  return { ok: errors.length === 0, errors, warnings, stats };
}
