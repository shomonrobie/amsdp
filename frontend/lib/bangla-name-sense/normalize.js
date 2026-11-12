/* BanglaNameSense — Unicode-aware input normalization.
 *
 * Pure functions only: no React, no DOM, no I/O. The same module is imported by
 * the React component and by the Node test suite, so matching behaviour cannot
 * drift between production and tests.
 *
 * Normalization is applied to SEARCH KEYS ONLY. A suggested name is always
 * displayed exactly as it appears in the dataset (`bn`), never re-written by
 * these functions (Master Feature List §25.8.3 rule 3).
 */

/* Bengali precomposed code points that NFC deliberately leaves decomposed,
 * because they are excluded from Unicode composition (they are canonical
 * equivalents, however, and a user's keyboard may produce either form).
 * Without this step `ড়` (U+09DC) and `ড়` (U+09A1 U+09BC) would not match. */
const NUKTA_COMPOSITIONS = [
  ['\u09A1\u09BC', '\u09DC'], // ড + ়  → ড়
  ['\u09A2\u09BC', '\u09DD'], // ঢ + ়  → ঢ়
  ['\u09AF\u09BC', '\u09DF'], // য + ়  → য়
];

/* Zero-width characters carry no phonetic value and are typed accidentally
 * (or inserted by some IMEs). They must not break a prefix match. */
const ZERO_WIDTH = /[\u200B\u200C\u200D\u2060\uFEFF]/g;

const MULTI_SPACE = /[\s\u00A0]+/g;

/** NFC + Bengali canonical composition + zero-width removal + whitespace collapse. */
function canonicalize(input) {
  let s = String(input == null ? '' : input);
  s = s.normalize('NFC');
  s = s.replace(ZERO_WIDTH, '');
  for (const [decomposed, composed] of NUKTA_COMPOSITIONS) {
    s = s.split(decomposed).join(composed);
  }
  return s.replace(MULTI_SPACE, ' ').trim();
}

/**
 * Normalize free-text typed into the name field, or a dataset `bn` value, into
 * the form used for matching.
 *
 * @param {string} input
 * @returns {string} normalized, lower-cased (Latin only; Bangla is caseless)
 */
export function normalizeBangla(input) {
  return canonicalize(input).toLowerCase();
}

/**
 * Normalize a dataset `en` alias or user input that is matched against it.
 * Latin matching is case-insensitive and whitespace-insensitive.
 *
 * @param {string} input
 * @returns {string}
 */
export function normalizeLatin(input) {
  return canonicalize(input).toLowerCase();
}

/**
 * Split normalized text into whitespace-delimited words.
 *
 * @param {string} input already normalized
 * @returns {string[]}
 */
export function wordsOf(input) {
  const s = typeof input === 'string' ? input : '';
  return s ? s.split(' ').filter(Boolean) : [];
}

/** True when the string contains at least one Bengali-script code point. */
export function hasBangla(text) {
  return /[\u0980-\u09FF]/.test(String(text == null ? '' : text));
}

/**
 * True when every query word can be found, in order, as a prefix of some word
 * of `candidateWords`. Used for multi-word matching and for alias matching.
 *
 * @param {string[]} queryWords normalized query split into words
 * @param {string[]} candidateWords normalized candidate split into words
 * @returns {boolean}
 */
export function matchesWordPrefixesInOrder(queryWords, candidateWords) {
  if (!queryWords.length || !candidateWords.length) return false;
  let from = 0;
  for (const q of queryWords) {
    let found = -1;
    for (let i = from; i < candidateWords.length; i += 1) {
      if (candidateWords[i].startsWith(q)) { found = i; break; }
    }
    if (found === -1) return false;
    from = found + 1;
  }
  return true;
}
