#!/usr/bin/env node
/**
 * One-off repair helper (safe to delete): reverses accidental cp1252 mojibake.
 *
 * Why it exists: a file edited as UTF-8 was later round-tripped through
 * PowerShell `Get-Content` / `Set-Content -Encoding utf8`, which read the UTF-8
 * bytes as cp1252 and re-encoded them, turning "—" into "â€”". This maps the
 * cp1252 characters back to their original bytes and decodes as UTF-8 again.
 *
 * Usage: node scripts/que-006-audio/.work/fix-encoding.cjs <file> [--write]
 */
const fs = require('node:fs');

const CP1252_REVERSE = {
  0x20ac: 0x80, 0x201a: 0x82, 0x0192: 0x83, 0x201e: 0x84, 0x2026: 0x85,
  0x2020: 0x86, 0x2021: 0x87, 0x02c6: 0x88, 0x2030: 0x89, 0x0160: 0x8a,
  0x2039: 0x8b, 0x0152: 0x8c, 0x017d: 0x8e, 0x2018: 0x91, 0x2019: 0x92,
  0x201c: 0x93, 0x201d: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97,
  0x02dc: 0x98, 0x2122: 0x99, 0x0161: 0x9a, 0x203a: 0x9b, 0x0153: 0x9c,
  0x017e: 0x9e, 0x0178: 0x9f,
};

const filePath = process.argv[2];
const write = process.argv.includes('--write');
if (!filePath) {
  console.error('usage: fix-encoding.cjs <file> [--write]');
  process.exit(2);
}

const original = fs.readFileSync(filePath, 'utf8');
const bytes = [];
for (const char of original) {
  const code = char.codePointAt(0);
  if (code < 0x100) bytes.push(code);
  else if (CP1252_REVERSE[code] !== undefined) bytes.push(CP1252_REVERSE[code]);
  else bytes.push(...Buffer.from(char, 'utf8'));
}

let repaired;
try {
  repaired = Buffer.from(bytes).toString('utf8');
} catch {
  repaired = null;
}

const score = (text) => (text.match(/[\u00c2\u00e2\u20ac]/g) || []).length;
if (!repaired || score(repaired) >= score(original)) {
  console.log('no repair needed (or repair would not improve the text)');
  process.exit(0);
}

console.log(`repaired: mojibake markers ${score(original)} -> ${score(repaired)}`);
if (write) {
  fs.writeFileSync(filePath, repaired, 'utf8');
  console.log(`written: ${filePath}`);
} else {
  console.log('dry run; pass --write to apply');
}
