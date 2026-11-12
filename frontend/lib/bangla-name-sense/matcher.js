/* BanglaNameSense — matching engine and deterministic ranking.
 *
 * Pure JavaScript, no React, no network, no AI service. The whole dataset is
 * held in memory once per page load, so a keystroke costs a linear scan of
 * ~700 short strings and never issues a request (Master Feature List §25.8.4).
 *
 * Matching rules (in rank order — lower rank is shown first):
 *
 *   0  EXACT       the typed text equals the whole Bangla name
 *   1  PREFIX      the Bangla name starts with the typed text
 *   2  WORD        every typed word prefixes a word of the Bangla name, in order
 *                  (this is what makes "রহমান র" and "রফিক র" work)
 *   3  ALIAS       the typed text prefixes the English alias, or its words
 *                  (case-insensitive: "rof" matches "Rofik Rahman")
 *
 * Ranking is fully deterministic: rank first, then the raw number of code
 * points (shorter names are more precise), then plain ordinal comparison of the
 * Bangla string. Ordinal comparison is used on purpose — ICU collation differs
 * between Node and browser builds, which would make the order machine-dependent.
 */

import {
  normalizeBangla,
  normalizeLatin,
  wordsOf,
  matchesWordPrefixesInOrder,
} from './normalize.js';

export const DEFAULT_MAX_SUGGESTIONS = 8;
export const DEFAULT_MIN_QUERY_LENGTH = 1;

export const RANK = Object.freeze({
  EXACT: 0,
  PREFIX: 1,
  WORD: 2,
  ALIAS: 3,
  NONE: -1,
});

const rankLabels = ['exact', 'prefix', 'word', 'alias'];

/**
 * Ordinal (code-point) comparison — deterministic across runtimes.
 * @param {string} a
 * @param {string} b
 * @returns {number}
 */
function compareOrdinal(a, b) {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

function toAliasList(record) {
  const aliases = [];
  const seen = new Set();
  const en = typeof record.en === 'string' ? record.en.trim() : '';
  if (en) {
    const key = normalizeLatin(en);
    if (key && !seen.has(key)) {
      seen.add(key);
      aliases.push({ en, key, words: wordsOf(key) });
    }
  }
  return aliases;
}


/**
 * Build an immutable search index from validated dataset records.
 *
 * Duplicate Bangla names are collapsed here: the first record for a normalized
 * `bn` wins for display, and any later record contributes its English alias to
 * that entry. The source records are never mutated.
 *
 * @param {Array<{bn: string, en?: string}>} records
 * @returns {{size: number, sourceCount: number, distinctCount: number,
 *            search: (query: string, options?: object) => object[],
 *            entries: ReadonlyArray<object>}}
 */
export function createNameIndex(records) {
  if (!Array.isArray(records)) {
    throw new TypeError('createNameIndex(records): records must be an array');
  }

  const byKey = new Map();
  const order = [];

  for (const record of records) {
    if (!record || typeof record.bn !== 'string') continue;
    const display = record.bn.trim();
    if (!display) continue;
    const key = normalizeBangla(display);
    if (!key) continue;

    let entry = byKey.get(key);
    if (!entry) {
      entry = {
        bn: display, // displayed exactly as the dataset has it — never rewritten
        key,
        words: wordsOf(key),
        codePoints: Array.from(display).length,
        aliases: [],
      };
      byKey.set(key, entry);
      order.push(entry);
    }

    for (const alias of toAliasList(record)) {
      if (!entry.aliases.some((a) => a.key === alias.key)) entry.aliases.push(alias);
    }
  }

  // Stable, deterministic candidate order before any query is applied.
  order.sort((a, b) => a.codePoints - b.codePoints || compareOrdinal(a.bn, b.bn));


  const entries = Object.freeze(order.map((e) => Object.freeze({
    bn: e.bn,
    key: e.key,
    words: Object.freeze(e.words.slice()),
    codePoints: e.codePoints,
    aliases: Object.freeze(e.aliases.map((a) => Object.freeze({ ...a }))),
  })));

  /**
   * @param {string} query raw text from the name input
   * @param {{maxSuggestions?: number, minQueryLength?: number}} [options]
   * @returns {Array<{bn: string, en: string, score: number, match: string}>}
   */
  function search(query, options = {}) {
    const maxSuggestions = Number.isInteger(options.maxSuggestions) && options.maxSuggestions > 0
      ? options.maxSuggestions
      : DEFAULT_MAX_SUGGESTIONS;
    const minQueryLength = Number.isInteger(options.minQueryLength) && options.minQueryLength >= 0
      ? options.minQueryLength
      : DEFAULT_MIN_QUERY_LENGTH;

    const q = normalizeBangla(query);
    if (!q || Array.from(q).length < minQueryLength) return [];
    const queryWords = wordsOf(q);

    const scored = [];
    for (const entry of entries) {
      let score = RANK.NONE;
      let match = '';

      if (entry.key === q) {
        score = RANK.EXACT;
        match = 'exact';
      } else if (entry.key.startsWith(q)) {
        score = RANK.PREFIX;
        match = 'prefix';
      } else if (queryWords.length > 1 && matchesWordPrefixesInOrder(queryWords, entry.words)) {
        score = RANK.WORD;
        match = 'word';
      } else {
        for (const alias of entry.aliases) {
          if (alias.key.startsWith(q) || matchesWordPrefixesInOrder(queryWords, alias.words)) {
            score = RANK.ALIAS;
            match = 'alias';
            break;
          }
        }
      }

      if (score !== RANK.NONE) {
        scored.push({ entry, score, match });
      }
    }

    scored.sort((a, b) => a.score - b.score
      || a.entry.codePoints - b.entry.codePoints
      || compareOrdinal(a.entry.bn, b.entry.bn));

    const seen = new Set();
    const results = [];
    for (const { entry, score, match } of scored) {
      if (seen.has(entry.key)) continue; // duplicate suppression, belt and braces
      seen.add(entry.key);
      results.push({
        bn: entry.bn,
        en: entry.aliases.length ? entry.aliases[0].en : '',
        score,
        match,
      });
      if (results.length >= maxSuggestions) break;
    }
    return results;
  }

  return Object.freeze({
    size: entries.length,
    sourceCount: records.length,
    distinctCount: entries.length,
    entries,
    search,
  });
}

/** Human-readable rank name, used by tests and the validation CLI. */
export function rankLabel(score) {
  return rankLabels[score] || 'none';
}
