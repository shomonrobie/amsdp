/* AMSDP appointment calendar — the cross-date match index (owner decision D-2).
 *
 * A Week or Day grid can only show the dates on screen, but the search box in
 * the shared toolbar searches *every* date the token may read.  Something has to
 * tell the receptionist that the name they typed did match — just not this week.
 * That is what `GET /api/v1/appointments/matches` answers, and this module is its
 * client half: ask the question, read the counts-only answer, and turn it into
 * the one sentence the calendar shows plus the date to navigate to.
 *
 * The answer is deliberately counts only (`{total, dates:[{date,count}],
 * truncated}`).  The browser never learns who is on those other dates, only that
 * they exist, so a search cannot become a way to read the organization's history
 * — navigating there fetches the week through the ordinary, authorised route.
 *
 * Pure: no React, no DOM, no fetch — `tests/calendar-matches.test.mjs` exercises
 * exactly the code the browser runs, the same split `grid.js` and `list.js` use.
 */
import { normaliseQuery } from './list.js';

/** The endpoint the calendar asks for the counts. */
export const MATCHES_PATH = '/api/v1/appointments/matches';

/**
 * The filters the index accepts.  No date window on purpose: the whole point is
 * that the answer is *not* limited to the dates on screen.
 */
export const MATCH_FILTER_FIELDS = Object.freeze(['q', 'doctor_id', 'status', 'branch_id']);

const str = (value) => (value == null ? '' : String(value));
const dayNumber = (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(str(iso));
  if (!m) return null;
  // UTC arithmetic: a local-timezone day count would make a date "closer" or
  // "further" by the offset rather than by the calendar.
  return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])) / 86400000;
};
const count = (value) => {
  const n = Math.trunc(Number(value));
  return Number.isFinite(n) && n > 0 ? n : 0;
};

/**
 * The request for the date index, as a plain object for `URLSearchParams`.
 *
 * Built from the same query object the grid and the list are built from, so the
 * three reads can never answer slightly different questions.  `near` is the
 * anchor day (the calendar's own date): the server orders the date list by
 * distance from it, so a truncated list keeps the dates the receptionist can
 * actually reach with one click.
 */
export function buildMatchParams(query, near = '') {
  const q = normaliseQuery(query);
  const params = {};
  MATCH_FILTER_FIELDS.forEach((key) => {
    const value = q[key].trim();
    if (value) params[key] = value;
  });
  const anchor = str(near).trim() || q.date_from;
  if (anchor) params.near = anchor;
  return params;
}

/**
 * Read `{total, dates, truncated}` defensively.
 *
 * An unknown shape degrades to "no matches known", never to a crash or to a
 * banner claiming matches nobody counted.  Malformed dates are dropped; a
 * negative or non-numeric count becomes 0; a missing `total` is the sum of the
 * dates actually listed.
 */
export function parseMatchIndex(data) {
  const body = data && typeof data === 'object' ? data : {};
  const rows = Array.isArray(body.dates) ? body.dates : [];
  const dates = [];
  rows.forEach((row) => {
    const iso = str(row && row.date).trim();
    if (dayNumber(iso) === null) return;
    dates.push({ date: iso, count: count(row && row.count) });
  });
  const listed = dates.reduce((sum, row) => sum + row.count, 0);
  const rawTotal = Math.trunc(Number(body.total));
  const total = Number.isFinite(rawTotal) && rawTotal >= 0 ? rawTotal : listed;
  return { total, dates, truncated: Boolean(body.truncated) };
}

/**
 * What the banner needs: how many matches the visible window holds, how many it
 * does not, and on which other dates.
 *
 * `inWindow` counts only the dates the grid is showing, so `outOfRange` is the
 * part of the answer the calendar cannot display.  When the server truncated its
 * date list, `outOfRange` is derived from the exact `total` instead of the
 * shortened list, and `atLeast` says so — a number printed next to "more" must
 * never understate the truth silently.
 */
export function matchSummary(index, window = {}) {
  const parsed = index && Array.isArray(index.dates)
    ? index
    : parseMatchIndex(index);
  const from = str(window && window.from).trim();
  const to = str(window && window.to).trim();
  const inWindowBounds = (iso) => {
    if (from && dayNumber(iso) < dayNumber(from)) return false;
    if (to && dayNumber(iso) > dayNumber(to)) return false;
    return true;
  };
  let inWindow = 0;
  const otherDates = [];
  parsed.dates.forEach((row) => {
    if (inWindowBounds(row.date)) inWindow += row.count;
    else otherDates.push(row);
  });
  const listedOutOfRange = otherDates.reduce((sum, row) => sum + row.count, 0);
  const outOfRange = parsed.truncated
    ? Math.max(0, parsed.total - inWindow)
    : listedOutOfRange;
  return {
    total: parsed.total,
    inWindow,
    outOfRange,
    otherDates,
    otherDateCount: otherDates.length,
    truncated: parsed.truncated,
  };
}

/**
 * Which sentence fits these counts.
 *
 * English inflects *both* numbers, so a single `'{n} more matches on {d} other
 * dates'` template cannot be right for every count: browser verification of S02
 * showed a receptionist reading "1 more matches on 1 other dates".  The three
 * keys below cover every reachable combination.
 *
 * `otherDateCount` can never exceed `outOfRange` (a date contributes at least one
 * match), so "one match on several dates" is unreachable and has no key.  The
 * `d <= 1` branch is written that way rather than `d === 1` so a truncated index
 * that named no dates still produces a sentence instead of a dangling placeholder.
 */
export function matchesBannerKey(summary) {
  const outOfRange = summary ? Math.trunc(Number(summary.outOfRange)) || 0 : 0;
  const otherDateCount = summary ? Math.trunc(Number(summary.otherDateCount)) || 0 : 0;
  if (outOfRange <= 1) return 'otherDatesOne';
  if (otherDateCount <= 1) return 'otherDatesOneDate';
  return 'otherDates';
}

/**
 * The other date to jump to: the one closest to `anchor`.
 *
 * Ties break towards the earlier date, so clicking the same banner twice always
 * lands on the same day.  Returns `''` when there is nowhere to go.
 */
export function nearestMatchDate(summary, anchor = '') {
  const dates = (summary && Array.isArray(summary.otherDates)) ? summary.otherDates : [];
  if (!dates.length) return '';
  const pivot = dayNumber(anchor);
  if (pivot === null) return dates[0].date;
  let best = dates[0];
  let bestGap = Math.abs(dayNumber(best.date) - pivot);
  dates.forEach((row) => {
    const gap = Math.abs(dayNumber(row.date) - pivot);
    if (gap < bestGap || (gap === bestGap && row.date < best.date)) {
      best = row;
      bestGap = gap;
    }
  });
  return best.date;
}
