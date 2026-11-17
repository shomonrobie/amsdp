/* Symptom catalogue search — the booking form's index over the bilingual
 * catalogue.
 *
 * REUSE, NOT A SECOND ENGINE
 * --------------------------
 * Every Unicode and Bengali decision lives once, in
 * `../bangla-name-sense/normalize.js`, the module BanglaNameSense ships: NFC,
 * the three nukta compositions (ড়/ঢ়/য় typed either way), zero-width removal,
 * whitespace collapse, Latin case-folding and the ordered word-prefix matcher.
 * This module imports those functions; it does not re-implement them, and it
 * does not modify `bangla-name-sense/matcher.js` or `controller.js`.
 *
 * What is added here is catalogue-specific:
 *
 *   1. **Several aliases per entry** — the Bangla name, the English name, the
 *      Bangla synonyms and the English synonyms are all search keys, so
 *      searching `মাথাব্যথা`, `headache`, `মাথা ব্যথা` or `head pain` finds the
 *      same entry.
 *   2. **A context tie-break** — a symptom tagged with one of the selected
 *      doctor's specialities sorts above an equally good text match.  It is a
 *      tie-break only: text relevance is compared first, so context can never
 *      push a worse textual match above a better one, and no entry is ever
 *      filtered out because it lacks the tag.
 *   3. **Never a selection** — `search()` only ranks.  Nothing in this module
 *      adds a symptom to the visit; that is an explicit receptionist act.
 *
 * Ranking is deterministic: rank, then context, then `sort_order`, then the
 * code.  Two identical calls always produce the same list (no locale collation,
 * no Map iteration order, no randomness) — which is what lets the tests pin
 * exact expectations.
 */

import {
  normalizeBangla,
  normalizeLatin,
  wordsOf,
  matchesWordPrefixesInOrder,
} from '../bangla-name-sense/normalize.js';

export const RANK = Object.freeze({
  EXACT: 0,
  PREFIX: 1,
  WORD: 2,
  NONE: -1,
});

/** Suggestions shown at once.  A reception desk reads a short list, not a page. */
export const DEFAULT_MAX_SUGGESTIONS = 8;

/** Free-text descriptions are short by policy (mirrors the server's 200). */
export const MAX_TEXT_LENGTH = 200;

function ordinal(a, b) {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

function pushKey(keys, seen, value, source, normalise) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (!text) return;
  const key = normalise(text);
  if (!key || seen.has(key)) return;
  seen.add(key);
  keys.push({ key, words: wordsOf(key), source });
}


/**
 * Build the immutable search index from the catalogue payload.
 *
 * @param {Array<object>} items catalogue entries as `GET /api/v1/symptoms` returns them
 * @param {{includeInactive?: boolean}} [options]
 * @returns {{size: number, entries: ReadonlyArray<object>, search: Function,
 *            resolveCommit: Function, byId: Function}}
 */
export function createCatalogueIndex(items, options = {}) {
  if (!Array.isArray(items)) {
    throw new TypeError('createCatalogueIndex(items): items must be an array');
  }
  const includeInactive = Boolean(options.includeInactive);

  const entries = [];
  for (const item of items) {
    if (!item || typeof item !== 'object') continue;
    const id = item.id ? String(item.id) : '';
    const nameEn = typeof item.name_en === 'string' ? item.name_en.trim() : '';
    const nameBn = typeof item.name_bn === 'string' ? item.name_bn.trim() : '';
    // A retired entry is not offered for a new booking, ever.  It stays in the
    // index only when a caller explicitly asks (admin review screens).
    if (!id || !nameEn
      || (!includeInactive && item.status && item.status !== 'active')) {
      continue;
    }

    const keys = [];
    const seen = new Set();
    // Order matters: a Bangla-name match is preferred over a synonym match at
    // the same rank, which follows the Bangla-first convention of every other
    // bilingual control in AMSDP.
    pushKey(keys, seen, nameBn, 'name_bn', normalizeBangla);
    pushKey(keys, seen, nameEn, 'name_en', normalizeLatin);
    for (const synonym of item.synonyms_bn || []) {
      pushKey(keys, seen, synonym, 'synonym_bn', normalizeBangla);
    }
    for (const synonym of item.synonyms_en || []) {
      pushKey(keys, seen, synonym, 'synonym_en', normalizeLatin);
    }
    if (!keys.length) continue;

    entries.push(Object.freeze({
      id,
      code: item.code || '',
      name_en: nameEn,
      name_bn: nameBn || nameEn,
      category: item.category || 'general',
      specialty_hints: Object.freeze((item.specialty_hints || []).slice()),
      sort_order: Number.isFinite(item.sort_order) ? item.sort_order : 100,
      review_status: item.review_status || 'unreviewed',
      keys: Object.freeze(keys),
    }));
  }

  // Stable starting order, so an empty query is meaningful too.
  entries.sort((a, b) => a.sort_order - b.sort_order || ordinal(a.code, b.code));

  const byIdMap = new Map(entries.map((entry) => [entry.id, entry]));

  /**
   * Does the entry's ranking hint list intersect the booking context?
   *
   * Matching is deliberately loose (exact, or one contains the other) because a
   * speciality may be recorded as free text ("Cardiology") rather than as a
   * catalogue code ("cardiology").  Loose matching can only make a tie-break
   * fire; it can never hide an entry.
   */
  function contextMatch(hints, contextCodes) {
    if (!hints.length || !contextCodes.length) return false;
    const wanted = contextCodes.map((c) => String(c || '').toLowerCase()).filter(Boolean);
    return hints.some((hint) => {
      const h = String(hint || '').toLowerCase();
      return h && wanted.some((code) => code === h || code.includes(h) || h.includes(code));
    });
  }

  function scoreEntry(entry, query, queryWords) {
    let best = { rank: RANK.NONE, matchedIn: '' };
    for (const key of entry.keys) {
      let rank = RANK.NONE;
      if (key.key === query) rank = RANK.EXACT;
      else if (key.key.startsWith(query)) rank = RANK.PREFIX;
      else if (matchesWordPrefixesInOrder(queryWords, key.words)) rank = RANK.WORD;
      if (rank !== RANK.NONE && (best.rank === RANK.NONE || rank < best.rank)) {
        best = { rank, matchedIn: key.source };
      }
    }
    return best;
  }

  /**
   * Rank the catalogue for `query`.
   *
   * @param {string} query what the receptionist typed (either script)
   * @param {{maxSuggestions?: number, excludeIds?: Iterable<string>,
   *          contextSpecialtyCodes?: string[]}} [options]
   * @returns {Array<{id: string, code: string, name_en: string, name_bn: string,
   *                  rank: number, match: string, context: boolean}>}
   */
  function search(query, options = {}) {
    const max = Number.isInteger(options.maxSuggestions) && options.maxSuggestions > 0
      ? options.maxSuggestions
      : DEFAULT_MAX_SUGGESTIONS;
    const excluded = new Set(options.excludeIds ? Array.from(options.excludeIds) : []);
    const contextCodes = options.contextSpecialtyCodes || [];
    const q = normalizeBangla(query);

    const scored = [];
    if (!q) {
      // Nothing typed: offer the most common entries, context first.  This is
      // an empty suggestion list with a useful default order — never a
      // selection, and the receptionist still has to choose.
      for (const entry of entries) {
        if (excluded.has(entry.id)) continue;
        scored.push({
          entry,
          rank: RANK.NONE,
          match: 'browse',
          context: contextMatch(entry.specialty_hints, contextCodes),
        });
      }
    } else {
      const queryWords = wordsOf(q);
      for (const entry of entries) {
        if (excluded.has(entry.id)) continue;
        const { rank, matchedIn } = scoreEntry(entry, q, queryWords);
        if (rank === RANK.NONE) continue;
        scored.push({
          entry,
          rank,
          match: matchedIn || 'none',
          context: contextMatch(entry.specialty_hints, contextCodes),
        });
      }
    }

    // Text relevance first, context only to break a tie, then the catalogue's
    // own commonness order, then the code so the result is total.
    scored.sort((a, b) => a.rank - b.rank
      || Number(b.context) - Number(a.context)
      || a.entry.sort_order - b.entry.sort_order
      || ordinal(a.entry.code, b.entry.code));

    return scored.slice(0, max).map((hit) => ({
      id: hit.entry.id,
      code: hit.entry.code,
      name_en: hit.entry.name_en,
      name_bn: hit.entry.name_bn,
      rank: hit.rank,
      match: hit.match,
      context: hit.context,
    }));
  }

  /**
   * Resolve a comma/Tab "complete this entry" gesture.
   *
   * Returns the single unambiguous entry, or `null`.  Unambiguous means either
   * an entry whose name or synonym *equals* what was typed, or the only entry
   * that matches at all.  Two prefix matches ("মাথা" → মাথাব্যথা and মাথা ঘোরা)
   * are ambiguous on purpose: a desk control must not guess which complaint the
   * patient has.
   *
   * @returns {{entry: object|null, reason: string}}
   */
  function resolveCommit(query, options = {}) {
    const excluded = new Set(options.excludeIds ? Array.from(options.excludeIds) : []);
    const q = normalizeBangla(query);
    if (!q) return { entry: null, reason: 'empty' };

    const exact = entries.filter((entry) => !excluded.has(entry.id)
      && entry.keys.some((key) => key.key === q));
    if (exact.length === 1) return { entry: exact[0], reason: 'exact' };
    if (exact.length > 1) return { entry: null, reason: 'ambiguous' };

    const results = search(q, { ...options, maxSuggestions: 2 });
    if (results.length === 1) {
      return { entry: byIdMap.get(results[0].id) || null, reason: 'only-match' };
    }
    if (!results.length) return { entry: null, reason: 'none' };
    return { entry: null, reason: 'ambiguous' };
  }

  return Object.freeze({
    size: entries.length,
    entries: Object.freeze(entries.slice()),
    search,
    resolveCommit,
    byId: (id) => byIdMap.get(String(id)) || null,
  });
}

/**
 * Duplicate-suppression key for a free-text description.
 *
 * Case-folded and whitespace-collapsed with the same Bangla normaliser as
 * search, so "মাথা ব্যথা" and "মাথা   ব্যথা" are one complaint.  The server keeps
 * its own key (`appointment/symptoms.text_key`) and remains the authority; this
 * one exists so the UI can refuse a duplicate before a request is made.
 */
export function textKey(text) {
  return normalizeBangla(text);
}

