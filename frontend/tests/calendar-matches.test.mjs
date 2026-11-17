/* AMSDP appointment calendar — cross-date match index contract (D-2).
 *
 * `lib/calendar/matches.js` is the browser half of
 * `GET /api/v1/appointments/matches`: what it asks for and how it reads the
 * counts back.  Tested here without React, a DOM or a network; the API side of
 * the same contract lives in
 * `backend/appointment/tests/test_appointment_calendar_filters.py`
 * (`TestMatchIndexSpansAllAuthorizedDates`).
 *
 * The property that matters most is the one this file keeps asserting from
 * several angles: the three reads (grid, list, index) answer the *same*
 * question, so a number in the banner can never describe rows the calendar
 * would refuse to show.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  MATCHES_PATH, MATCH_FILTER_FIELDS, buildMatchParams, parseMatchIndex,
  matchSummary, nearestMatchDate, matchesBannerKey,
} from '../lib/calendar/matches.js';
import {
  emptyQuery, setFilter, buildFilterParams, buildListParams,
} from '../lib/calendar/list.js';

const WINDOW = { from: '2026-11-14', to: '2026-11-20' };

const query = (patch) => Object.keys(patch)
  .reduce((q, key) => setFilter(q, key, patch[key]), emptyQuery());

test('the index is asked the filters and never the date window', () => {
  assert.equal(MATCHES_PATH, '/api/v1/appointments/matches');
  const q = query({ q: 'রহিম', status: 'CONFIRMED', doctor_id: 'd1', branch_id: 'b1' });

  // No window parameters, even though the same query carries them for the list:
  // the whole point of D-2 is that the answer is not limited to the seven days
  // on screen.
  assert.deepEqual(buildMatchParams(q, '2026-11-16'), {
    q: 'রহিম', doctor_id: 'd1', status: 'CONFIRMED', branch_id: 'b1', near: '2026-11-16',
  });
  assert.deepEqual(MATCH_FILTER_FIELDS.slice(), ['q', 'doctor_id', 'status', 'branch_id']);

  // A date bound on the query is a window, not a filter: the index ignores it.
  const bounded = query({ date_from: '2026-01-01', date_to: '2026-01-31' });
  const params = buildMatchParams(bounded, '2026-01-10');
  assert.equal('date_from' in params, false);
  assert.equal('date_to' in params, false);
  assert.equal(params.near, '2026-01-10');
});

test('the request says exactly what it means', () => {
  // Blank filters are omitted, not sent empty; sort/page/limit never travel.
  assert.deepEqual(buildMatchParams(emptyQuery()), {});
  const q = { ...emptyQuery(), q: '  রহিম  ', status: '  ', doctor_id: '', page: 3, limit: 50, sort: 'date' };
  assert.deepEqual(buildMatchParams(q, '  '), { q: 'রহিম' },
    'only the non-blank filter survives, trimmed as the list trims it');

  // `near` falls back to the query's own start bound, then to nothing at all.
  assert.equal(buildMatchParams(query({ date_from: '2026-11-14' })).near, '2026-11-14');
  assert.equal('near' in buildMatchParams(emptyQuery()), false);
  // An unparseable query is a blank query, never a crash.
  assert.deepEqual(buildMatchParams(null), {});
  assert.deepEqual(buildMatchParams(undefined, null), {});
});

test('an unknown answer shape reports no matches, never an invented number', () => {
  const empty = { total: 0, dates: [], truncated: false };
  for (const junk of [null, undefined, 'nonsense', 42, [], {}]) {
    assert.deepEqual(parseMatchIndex(junk), empty, JSON.stringify(junk) + ' is not an index');
  }

  // Counts and dates are coerced; anything unusable is dropped rather than
  // turned into NaN, -3 or a date the calendar cannot navigate to.
  const parsed = parseMatchIndex({
    total: '6',
    dates: [
      { date: '2026-12-01', count: '2' },
      { date: '2026-12-01', count: 1 },
      { date: 'not-a-date', count: 4 },
      { date: '2026-12-05', count: -2 },
      { date: '2026-12-06' },
      null,
    ],
    truncated: 'yes',
  });
  assert.equal(parsed.total, 6);
  assert.deepEqual(parsed.dates, [
    { date: '2026-12-01', count: 2 },
    { date: '2026-12-01', count: 1 },
    { date: '2026-12-05', count: 0 },
    { date: '2026-12-06', count: 0 },
  ]);
  assert.equal(parsed.truncated, true, 'a truncated answer is never read as complete');

  // No usable total: the listed counts are the only evidence there is.
  assert.equal(parseMatchIndex({ dates: [{ date: '2026-12-01', count: 3 }] }).total, 3);
  assert.equal(parseMatchIndex({ total: -5, dates: [] }).total, 0);
});

test('the summary splits the answer at the edges of the visible window', () => {
  const index = parseMatchIndex({
    total: 6,
    dates: [
      { date: '2026-11-14', count: 1 },   // first day of the week — inside
      { date: '2026-11-17', count: 2 },   // inside
      { date: '2026-11-20', count: 1 },   // last day — inside
      { date: '2026-11-13', count: 1 },   // the day before — outside
      { date: '2026-11-21', count: 1 },   // the day after — outside
    ],
  });
  const week = matchSummary(index, WINDOW);
  assert.equal(week.total, 6);
  assert.equal(week.inWindow, 4, 'both bounds are inclusive');
  assert.equal(week.outOfRange, 2);
  assert.equal(week.otherDateCount, 2);
  assert.deepEqual(week.otherDates.map((d) => d.date), ['2026-11-13', '2026-11-21']);

  // Day view: the same index, one date inside.
  const day = matchSummary(index, { from: '2026-11-17', to: '2026-11-17' });
  assert.equal(day.inWindow, 2);
  assert.equal(day.outOfRange, 4);
  assert.equal(day.otherDateCount, 4);

  // Everything inside: nothing to announce, so the banner stays away.
  const inside = matchSummary(
    parseMatchIndex({ total: 2, dates: [{ date: '2026-11-17', count: 2 }] }), WINDOW,
  );
  assert.equal(inside.outOfRange, 0);

  // No window at all: nothing is hidden, so nothing is "out of range".  A
  // caller that forgets the window cannot make the banner claim matches the
  // calendar is withholding.
  const bare = matchSummary(index);
  assert.equal(bare.inWindow, 6);
  assert.equal(bare.outOfRange, 0);
  assert.equal(bare.otherDateCount, 0);
});

test('a truncated date list still reports the true number of matches', () => {
  // The server caps how many dates it lists but counts every matching row.
  const index = parseMatchIndex({
    total: 500,
    dates: [{ date: '2026-12-01', count: 2 }, { date: '2026-12-02', count: 3 }],
    truncated: true,
  });
  const summary = matchSummary(index, WINDOW);
  assert.equal(summary.inWindow, 0);
  assert.equal(summary.outOfRange, 500, 'the total is exact even when the dates are not');
  assert.equal(summary.otherDateCount, 2);
  assert.equal(summary.truncated, true, 'the caller must be able to say "more dates exist"');

  // Not truncated: the listed counts are the whole truth.
  const exact = matchSummary(
    parseMatchIndex({ total: 5, dates: [{ date: '2026-12-01', count: 5 }] }), WINDOW,
  );
  assert.equal(exact.outOfRange, 5);
  assert.equal(exact.truncated, false);
});

test('the summary reads a raw index too, so a caller cannot pass the wrong thing', () => {
  const raw = { total: 3, dates: [{ date: '2026-12-01', count: 3 }], truncated: false };
  assert.deepEqual(matchSummary(raw, WINDOW), matchSummary(parseMatchIndex(raw), WINDOW));
  // An empty window hides nothing, so the whole index is "on screen".
  const loose = matchSummary(parseMatchIndex(raw), { from: '', to: '' });
  assert.equal(loose.inWindow, 3);
  assert.equal(loose.outOfRange, 0);
});

test('the banner navigates to the date closest to the calendar', () => {
  // The window is 2026-11-14 … 2026-11-20, so all three of these are elsewhere.
  const summary = matchSummary(parseMatchIndex({
    total: 3,
    dates: [
      { date: '2026-11-02', count: 1 },
      { date: '2026-11-22', count: 1 },  // five days after the anchor below
      { date: '2026-11-30', count: 1 },
    ],
  }), WINDOW);
  assert.equal(summary.otherDateCount, 3);

  assert.equal(nearestMatchDate(summary, '2026-11-17'), '2026-11-22');
  assert.equal(nearestMatchDate(summary, '2026-11-27'), '2026-11-30');
  // Equidistant: the earlier date wins, so the same click always lands the same.
  assert.equal(nearestMatchDate(summary, '2026-11-26'), '2026-11-22');
  // No anchor: the first date the server listed (already nearest-ordered).
  assert.equal(nearestMatchDate(summary, ''), '2026-11-02');
  assert.equal(nearestMatchDate(summary, 'not-a-date'), '2026-11-02');
  // Nowhere to go.
  assert.equal(nearestMatchDate(matchSummary(parseMatchIndex({}), WINDOW), '2026-11-17'), '');
  assert.equal(nearestMatchDate(null, '2026-11-17'), '');
});

test('the banner sentence inflects both numbers it reports', () => {
  const summary = (dates, extra = {}) => matchSummary(
    parseMatchIndex({ total: dates.reduce((s, d) => s + d.count, 0), dates, ...extra }),
    WINDOW,
  );

  // One match on one other date — the case browser verification caught reading
  // "1 more matches on 1 other dates".
  const one = summary([{ date: '2026-11-13', count: 1 }]);
  assert.equal(one.outOfRange, 1);
  assert.equal(one.otherDateCount, 1);
  assert.equal(matchesBannerKey(one), 'otherDatesOne');

  // Several matches, still one other date.
  const oneDate = summary([{ date: '2026-11-13', count: 4 }]);
  assert.equal(oneDate.outOfRange, 4);
  assert.equal(oneDate.otherDateCount, 1);
  assert.equal(matchesBannerKey(oneDate), 'otherDatesOneDate');

  // The plain plural, and the case where the banner is not shown at all.
  assert.equal(
    matchesBannerKey(summary([{ date: '2026-11-13', count: 1 }, { date: '2026-11-21', count: 2 }])),
    'otherDates',
  );
  const inWindow = summary([{ date: '2026-11-16', count: 3 }]);
  assert.equal(inWindow.outOfRange, 0);
  assert.equal(matchesBannerKey(inWindow), 'otherDatesOne',
    'nothing to show: any key is fine, but it must be a real one');

  // Truncated: the count is exact, the date list is not — never a crash, never
  // a placeholder left dangling.
  const truncated = summary(
    [{ date: '2026-12-01', count: 2 }, { date: '2026-12-02', count: 2 }],
    { truncated: true, total: 90 },
  );
  assert.equal(truncated.outOfRange, 90);
  assert.equal(matchesBannerKey(truncated), 'otherDates');

  // A missing or unusable summary cannot pick a sentence nobody can render.
  for (const junk of [null, undefined, {}, { outOfRange: 'x' }]) {
    assert.equal(typeof matchesBannerKey(junk), 'string');
  }
});

test('the three reads answer the same question', () => {
  const q = query({ q: 'রহিম', status: 'CONFIRMED', doctor_id: 'd1', branch_id: 'b1' });
  const filters = buildFilterParams(q, WINDOW);
  const list = buildListParams(q, WINDOW);
  const index = buildMatchParams(q, '2026-11-16');

  // Every filter the grid sends is a filter the list sends, unchanged.
  for (const key of Object.keys(filters)) {
    assert.equal(list[key], filters[key], key + ' must not differ between the reads');
  }
  // …and every filter the index sends is one of the grid's, minus the window.
  for (const key of Object.keys(index)) {
    if (key === 'near') continue;
    assert.equal(filters[key], index[key], key + ' must not differ between the reads');
  }
  // Paging is the list's alone; the grid takes the window and no paging.
  for (const key of ['sort', 'order', 'page', 'limit']) {
    assert.equal(key in filters, false, key + ' is not a filter');
    assert.ok(key in list, 'the list pages');
  }
  // D-1 — the branch scope travels to all three, because it is a scope, not a
  // convenience filter: a search must never reach past the token's branch.
  assert.equal(filters.branch_id, 'b1');
  assert.equal(list.branch_id, 'b1');
  assert.equal(index.branch_id, 'b1');
  // The index is the only read without a window; that is the whole point of it.
  assert.equal('date_from' in index, false);
  assert.equal(filters.date_from, WINDOW.from);
  assert.equal(list.date_from, WINDOW.from);
});
