#!/usr/bin/env node
/* BanglaNameSense — dataset validation CLI.
 *
 * Usage (from frontend/):
 *   npm run validate:dataset
 *   node scripts/validate-bangla-name-sense.mjs [path/to/dataset.json]
 *
 * Prints the validation result without modifying the file. Exits non-zero when
 * the dataset is structurally invalid, so a refresh cannot be merged silently.
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { validateDataset } from '../lib/bangla-name-sense/validate-dataset.js';
import { createNameIndex } from '../lib/bangla-name-sense/matcher.js';
import { DATASET_SOURCE } from '../lib/bangla-name-sense/dataset.js';

const target = process.argv[2]
  || fileURLToPath(new URL('../data/bangla_name_sense.json', import.meta.url));

let raw;
try {
  raw = JSON.parse(readFileSync(target, 'utf8'));
} catch (error) {
  console.error(`dataset could not be read as JSON: ${target}`);
  console.error(`  ${error.message}`);
  process.exit(2);
}

const { ok, errors, warnings, stats } = validateDataset(raw);

console.log(`BanglaNameSense dataset validation — ${target}`);
console.log(`  records .............. ${stats.records}`);
console.log(`  distinct Bangla names  ${stats.distinctBangla}`);
console.log(`  duplicate records .... ${stats.duplicates} (suppressed at display time)`);
console.log(`  with English alias ... ${stats.withEnglishAlias}`);
console.log(`  gender metadata ...... ${stats.gendersPresent ? 'present, never used for matching or display' : 'absent'}`);

if (ok) {
  const index = createNameIndex(raw.names);
  console.log(`  search index ......... ${index.size} entries`);
  console.log(`  reference version .... ${DATASET_SOURCE.version}`);
  console.log('  result ............... VALID');
} else {
  console.log('  result ............... INVALID');
}

if (warnings.length) {
  console.log('\nwarnings:');
  for (const warning of warnings) console.log(`  - ${warning}`);
}

if (!ok) {
  console.error('\nerrors:');
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}
