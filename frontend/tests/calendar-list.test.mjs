/* AMSDP appointment list — pure model contract.
 *
 * `lib/calendar/list.js` is the only thing that decides what the list view asks
 * the server for and how it reads the answer back, so it is tested here without
 * React, a DOM or a network.  The API side of the same contract lives in
 * `backend/appointment/tests/test_appointment_list.py`.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  LIST_PAGE_SIZES, DEFAULT_LIMIT, SORT_KEYS, DEFAULT_ORDER,
  emptyQuery, normaliseQuery, isFiltered, setFilter, clearFilters,
  setPage, setLimit, toggleSort, ariaSort, buildFilterParams, buildListParams,
  parseEnvelope, pageWindow,
} from '../lib/calendar/list.js';

test('the list opens on page 1 of 25, newest first', () => {
  const q = emptyQuery();
  assert.equal(q.page, 1);
  assert.equal(q.limit, DEFAULT_LIMIT);
  assert.equal(DEFAULT_LIMIT, 25);
  assert.equal(q.sort, 'date');
  assert.equal(q.order, 'desc');
  assert.equal(isFiltered(q), false);
  // A fresh blank query every time — two list views must not share state.
  assert.notEqual(emptyQuery(), q);
});

test('a query is coerced into what the API will accept', () => {
  const q = normaliseQuery({
    q: '  রহিম  ', doctor_id: 'd1', status: 'CONFIRMED', branch_id: 'b1',
    sort: 'patient', order: 'ASC', page: '3', limit: '50', secret: 'ignored',
  });
  assert.equal(q.q, '  রহিম  ', 'the raw text is kept so the input does not jump');
  assert.equal(q.doctor_id, 'd1');
  assert.equal(q.sort, 'patient');
  assert.equal(q.order, 'asc', 'order is case-folded');
  assert.equal(q.page, 3, 'page arrives as a string from a <select>');
  assert.equal(q.limit, 50);
  assert.equal('secret' in q, false, 'unknown keys never reach the request');

  // Anything the API would 422 on is replaced here instead.
  const bad = normaliseQuery({ sort: 'surname', order: 'sideways', limit: 7, page: 0 });
  assert.equal(bad.sort, 'date');
  assert.equal(bad.order, DEFAULT_ORDER.date);
  assert.equal(bad.limit, DEFAULT_LIMIT);
  assert.equal(bad.page, 1);

  // The natural direction differs per column: names read A→Z, dates newest first.
  assert.equal(normaliseQuery({ sort: 'status' }).order, 'asc');
  assert.equal(normaliseQuery({ sort: 'date' }).order, 'desc');
  for (const key of SORT_KEYS) assert.ok(DEFAULT_ORDER[key], key + ' has a direction');
});

test('the request says exactly what it means', () => {
  const window = { from: '2026-11-14', to: '2026-11-20' };
  const params = buildListParams(emptyQuery(), window);
  assert.deepEqual(params, {
    date_from: '2026-11-14', date_to: '2026-11-20',
    sort: 'date', order: 'desc', page: '1', limit: '25',
  }, 'blank filters are omitted, the calendar window is carried over');

  const filtered = buildListParams(
    normaliseQuery({ q: '  রহিম ', status: 'CONFIRMED', sort: 'patient', page: 2 }),
    window,
  );
  assert.deepEqual(filtered, {
    q: 'রহিম', status: 'CONFIRMED', date_from: '2026-11-14', date_to: '2026-11-20',
    sort: 'patient', order: 'asc', page: '2', limit: '25',
  }, 'the search term is trimmed on the wire, not in the input');
  assert.ok(!('doctor_id' in filtered), 'an unset filter is absent, not empty');

  // URLSearchParams is what the page actually calls.
  const qs = new URLSearchParams(filtered).toString();
  assert.ok(qs.includes('sort=patient'));
  assert.ok(qs.includes('date_from=2026-11-14'));
});

test('one builder produces the filter half for every read', () => {
  // AMSDP-CALENDAR-FILTER-01 (F-1/F-2): the grid, the list and the match index
  // must answer the same question.  `buildFilterParams` is that one builder, and
  // `buildListParams` must be exactly it plus sorting and paging — no second
  // copy of the predicates to drift.
  const window = { from: '2026-11-14', to: '2026-11-20' };
  const q = normaliseQuery({ q: ' রহিম ', status: 'CONFIRMED', branch_id: 'b1',
    doctor_id: 'd1', sort: 'patient', order: 'asc', page: 3, limit: 100 });

  assert.deepEqual(buildFilterParams(q, window), {
    q: 'রহিম', status: 'CONFIRMED', branch_id: 'b1', doctor_id: 'd1',
    date_from: '2026-11-14', date_to: '2026-11-20',
  }, 'the shared filters plus the visible window — nothing else');

  // The list is that object plus its own keys, and never re-derives a filter.
  const list = buildListParams(q, window);
  for (const key of Object.keys(buildFilterParams(q, window))) {
    assert.equal(list[key], buildFilterParams(q, window)[key], key + ' must be shared');
  }
  assert.deepEqual(Object.keys(list).sort(), [
    'branch_id', 'date_from', 'date_to', 'doctor_id', 'limit', 'order', 'page', 'q', 'sort', 'status',
  ]);

  // A window argument wins over a date bound on the query (the calendar's own
  // range is the truth on screen); without one, the query's bound is used.
  const bounded = normaliseQuery({ date_from: '2026-01-01', date_to: '2026-01-31' });
  assert.equal(buildFilterParams(bounded, window).date_from, '2026-11-14');
  assert.equal(buildFilterParams(bounded).date_from, '2026-01-01');
  // No filters, no window: nothing is sent at all, so the server defaults apply.
  assert.deepEqual(buildFilterParams(emptyQuery()), {});
  assert.deepEqual(buildFilterParams(null, null), {});
});

test('the envelope is read defensively', () => {
  const env = parseEnvelope({ items: [{ id: 'a' }], total: 340, page: 2, limit: 25, pages: 14 });
  assert.deepEqual(env, { items: [{ id: 'a' }], total: 340, page: 2, limit: 25, pages: 14 });

  // Missing `pages` is derived, not left undefined.
  assert.equal(parseEnvelope({ items: [], total: 340, limit: 25, page: 1 }).pages, 14);
  // A bare array (the old unpaged endpoint) still renders.
  assert.deepEqual(parseEnvelope([{ id: 'a' }, { id: 'b' }]),
    { items: [{ id: 'a' }, { id: 'b' }], total: 2, page: 1, limit: 2, pages: 1 });
  // Nothing at all is an empty list, never an exception.
  assert.deepEqual(parseEnvelope(undefined),
    { items: [], total: 0, page: 1, limit: 25, pages: 0 });
  assert.deepEqual(parseEnvelope({}), { items: [], total: 0, page: 1, limit: 25, pages: 0 });
  // A page past the end is clamped to the last real page.
  assert.equal(parseEnvelope({ items: [], total: 30, page: 99, limit: 25, pages: 2 }).page, 2);
});

test('the page window slides, never runs off either end', () => {
  assert.deepEqual(pageWindow(1, 1).numbers, [1]);
  assert.deepEqual(pageWindow(1, 14).numbers, [1, 2, 3, 4, 5]);
  assert.deepEqual(pageWindow(7, 14).numbers, [5, 6, 7, 8, 9]);
  assert.deepEqual(pageWindow(14, 14).numbers, [10, 11, 12, 13, 14]);
  const first = pageWindow(1, 14);
  assert.equal(first.truncatedStart, false);
  assert.equal(first.truncatedEnd, true);
  const last = pageWindow(14, 14);
  assert.equal(last.truncatedStart, true);
  assert.equal(last.truncatedEnd, false);
  // No pages at all is not one page.
  assert.deepEqual(pageWindow(1, 0), {
    first: 0, last: 0, numbers: [], truncatedStart: false, truncatedEnd: false,
  });
  assert.deepEqual(pageWindow(9, 3).numbers, [1, 2, 3], 'a page past the end clamps');
});

test('sorting flips within a column and restarts at page 1', () => {
  const dateDesc = emptyQuery();
  const byPatient = toggleSort(dateDesc, 'patient');
  assert.equal(byPatient.sort, 'patient');
  assert.equal(byPatient.order, 'asc', 'a new column starts in its natural direction');
  const flipped = toggleSort(byPatient, 'patient');
  assert.equal(flipped.sort, 'patient');
  assert.equal(flipped.order, 'desc');
  assert.equal(toggleSort(setPage(byPatient, 4), 'patient').page, 1,
    'page 4 of the old sort is gone');
  // An unknown column is a no-op: the header must not claim a sort it did not do.
  assert.deepEqual(toggleSort(byPatient, 'mobile'), byPatient);
  assert.equal(ariaSort(byPatient, 'patient'), 'ascending');
  assert.equal(ariaSort(flipped, 'patient'), 'descending');
  assert.equal(ariaSort(byPatient, 'date'), 'none');
});

test('filters reset the page, and clearing them keeps the sort', () => {
  const base = { ...emptyQuery(), page: 3, limit: 50, sort: 'doctor', order: 'desc' };
  const typed = setFilter(base, 'q', 'করিম');
  assert.equal(typed.q, 'করিম');
  assert.equal(typed.page, 1);
  assert.equal(typed.sort, 'doctor', 'typing does not disturb the sort');
  assert.equal(isFiltered(typed), true);
  assert.equal(setFilter(base, 'status', 'CONFIRMED').page, 1);

  const cleared = clearFilters(setFilter(typed, 'doctor_id', 'd1'));
  assert.equal(isFiltered(cleared), false, 'clearing removes every filter');
  assert.equal(cleared.sort, 'doctor');
  assert.equal(cleared.limit, 50, 'the chosen page size survives a clear');
  assert.equal(setPage(base, 2).page, 2);
  assert.equal(setPage(base, 0).page, 1, 'page 0 is not a page');
});

test('the page size is one the API accepts', () => {
  const q = setLimit(emptyQuery(), 100);
  assert.equal(q.limit, 100);
  assert.ok(LIST_PAGE_SIZES.includes(q.limit));
  assert.equal(setLimit(setPage(q, 3), 50).page, 1, 'page 3 of 100 does not exist at 50');
  assert.equal(setLimit(q, 999).limit, 100, 'an unsupported size is refused, not forwarded');
});
