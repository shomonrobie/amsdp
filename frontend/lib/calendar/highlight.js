/* AMSDP appointment calendar — marking the matched part of a name.
 *
 * When a search narrows the calendar, the card on screen is the *answer* to the
 * question, so the substring that matched should be visible in it.  This module
 * produces the segments; the component renders them as `<mark>` and nothing else.
 *
 * Two rules, both safety rules rather than taste:
 *
 *   * **Substring only.**  The term is user input.  It is never compiled into a
 *     RegExp (a stray `*` or `(` would throw or match the wrong thing) and never
 *     into HTML (React escapes the segments, and a name containing `<script>` is
 *     text, not markup).  `%` and `_` are literal characters here, exactly as the
 *     server's escaped `ILIKE` treats them.
 *   * **Case-insensitive, like the server.**  `ILIKE` folds case for Latin text
 *     and leaves Bangla alone; `toLowerCase()` does the same, so what is marked
 *     is what the server matched.
 *
 * Pure: no React, no DOM — `tests/calendar-highlight.test.mjs`.
 */

/** Longest term worth marking; mirrors the server's `SEARCH_MAX_LENGTH`. */
export const MAX_TERM = 120;

/**
 * `text` as `[{ text, match }]` segments covering it exactly once.
 *
 * The segments always reassemble into the original string, so marking can never
 * truncate or reorder a name.  An empty term, or one that does not occur, yields
 * a single `match: false` segment — the caller renders every name the same way.
 */
export function highlightSegments(text, term) {
  const source = text == null ? '' : String(text);
  const needle = (term == null ? '' : String(term)).trim().slice(0, MAX_TERM);
  if (!source || !needle) return [{ text: source, match: false }];

  const haystack = source.toLowerCase();
  const find = needle.toLowerCase();
  const segments = [];
  let at = 0;
  for (;;) {
    const hit = haystack.indexOf(find, at);
    if (hit < 0) break;
    if (hit > at) segments.push({ text: source.slice(at, hit), match: false });
    segments.push({ text: source.slice(hit, hit + find.length), match: true });
    at = hit + find.length;
  }
  if (!segments.length) return [{ text: source, match: false }];
  if (at < source.length) segments.push({ text: source.slice(at), match: false });
  return segments;
}

/** True when `term` actually occurs in `text` — the caller marks on evidence. */
export function hasHighlight(text, term) {
  return highlightSegments(text, term).some((segment) => segment.match);
}
