/* AMSDP appointment list — pure query/response model for the paged list view.
 *
 * The calendar (`lib/calendar/grid.js`) decides *where* an appointment sits on a
 * time axis; this module decides *what to ask the server for* once the
 * receptionist switches to the list, and how to read the answer back.  No React,
 * no DOM, no fetch: `tests/calendar-list.test.mjs` exercises exactly the code the
 * browser runs — the same split the grid model uses.
 *
 * Why the server does the work: the list view exists so one appointment can be
 * found among thousands.  Filtering an already-fetched week would only ever
 * search the week on screen, which is precisely the limitation this view
 * removes.  So search, filters, sorting and paging are all part of the query.
 *
 * Everything here mirrors `GET /api/v1/appointments/list`
 * (backend/appointment/main.py): the same whitelisted sort keys, the same page
 * sizes and the same `{items,total,page,limit,pages}` envelope.  A key the API
 * would reject is normalised here rather than sent, so a typo in the UI can
 * never turn into a 422 on the desk.
 */

/** Page sizes the API accepts (must stay a subset of its `limit` range). */
export const LIST_PAGE_SIZES = Object.freeze([25, 50, 100]);
export const DEFAULT_LIMIT = 25;

/** Sort keys the API accepts; anything else is replaced, never forwarded. */
export const SORT_KEYS = Object.freeze(['date', 'patient', 'doctor', 'branch', 'status']);

/** First click on a column picks the order a receptionist expects from it. */
export const DEFAULT_ORDER = Object.freeze({
  date: 'desc', patient: 'asc', doctor: 'asc', branch: 'asc', status: 'asc',
});

/** The filter fields — the ones "clear filters" touches and "is filtered" reads. */
export const FILTER_FIELDS = Object.freeze([
  'q', 'doctor_id', 'status', 'branch_id', 'date_from', 'date_to',
]);

const str = (value) => (value == null ? '' : String(value));
const positiveInt = (value, fallback) => {
  const n = Math.trunc(Number(value));
  return Number.isFinite(n) && n >= 1 ? n : fallback;
};

/** A blank query: the state the list opens in, and the state it resets to. */
export function emptyQuery() {
  return {
    q: '', doctor_id: '', status: '', branch_id: '', date_from: '', date_to: '',
    sort: 'date', order: 'desc', page: 1, limit: DEFAULT_LIMIT,
  };
}

/**
 * Coerce an arbitrary object into a query the API will accept.
 *
 * Unknown keys are dropped, filters become strings, `page` is at least 1,
 * `limit` is one of {@link LIST_PAGE_SIZES}, `sort` is whitelisted and `order`
 * falls back to the default for that sort key.
 */
export function normaliseQuery(patch = {}) {
  const base = emptyQuery();
  const input = patch && typeof patch === 'object' ? patch : {};
  const out = { ...base };
  for (const key of FILTER_FIELDS) if (key in input) out[key] = str(input[key]);
  const sort = SORT_KEYS.includes(input.sort) ? input.sort : base.sort;
  out.sort = sort;
  const order = str(input.order).toLowerCase();
  out.order = order === 'asc' || order === 'desc' ? order : DEFAULT_ORDER[sort];
  out.page = positiveInt(input.page, base.page);
  const limit = Number(input.limit);
  out.limit = LIST_PAGE_SIZES.includes(limit) ? limit : base.limit;
  return out;
}

/** True when any filter narrows the result set (sorting and paging do not). */
export function isFiltered(query) {
  const q = normaliseQuery(query);
  return FILTER_FIELDS.some((key) => q[key].trim() !== '');
}

/** Apply one filter and return to page 1 — the old page may no longer exist. */
export function setFilter(query, key, value) {
  const q = normaliseQuery(query);
  if (!FILTER_FIELDS.includes(key)) return q;
  return { ...q, [key]: str(value), page: 1 };
}

/** Drop every filter, keep the sort and the page size, return to page 1. */
export function clearFilters(query) {
  const q = normaliseQuery(query);
  const out = { ...q, page: 1 };
  FILTER_FIELDS.forEach((key) => { out[key] = ''; });
  return out;
}

export function setPage(query, page) {
  return { ...normaliseQuery(query), page: positiveInt(page, 1) };
}

/** Changing the page size restarts at page 1; page 3 of 25 has no page-3-of-100. */
export function setLimit(query, limit) {
  const q = normaliseQuery(query);
  const requested = Number(limit);
  return { ...q, limit: LIST_PAGE_SIZES.includes(requested) ? requested : q.limit, page: 1 };
}

/**
 * Sort by `key`.  Clicking the column already sorted flips the direction;
 * clicking a different column starts in that column's natural direction.
 */
export function toggleSort(query, key) {
  const q = normaliseQuery(query);
  if (!SORT_KEYS.includes(key)) return q;
  if (q.sort === key) return { ...q, order: q.order === 'asc' ? 'desc' : 'asc', page: 1 };
  return { ...q, sort: key, order: DEFAULT_ORDER[key], page: 1 };
}

/** `aria-sort` for a column header: never a colour-only sort indicator. */
export function ariaSort(query, key) {
  const q = normaliseQuery(query);
  if (q.sort !== key) return 'none';
  return q.order === 'asc' ? 'ascending' : 'descending';
}

/**
 * The **filter half** of an appointment read — what the shared toolbar says.
 *
 * This is the one function that answers "which appointments match what the
 * receptionist typed": the Week/Day grid passes it the visible range, the paged
 * list adds sorting and paging on top, and the match index (`matches.js`) drops
 * the range deliberately.  Keeping it in one place is the fix for the defect
 * that let the search box change the list while the calendar ignored it: there
 * is no second copy of these predicates to drift.
 *
 * Empty filters are omitted rather than sent blank, so the request says what it
 * means.  `window` is the calendar's visible date range (`{ from, to }`): a
 * read answers "these days, filtered", which keeps the views on the same ground
 * and means a receptionist never loses the date context by switching.
 */
export function buildFilterParams(query, window = {}) {
  const q = normaliseQuery(query);
  const params = {};
  FILTER_FIELDS.forEach((key) => {
    const value = q[key].trim();
    if (value) params[key] = value;
  });
  const from = str(window && window.from).trim() || q.date_from;
  const to = str(window && window.to).trim() || q.date_to;
  if (from) params.date_from = from;
  if (to) params.date_to = to;
  return params;
}

/**
 * The paged list's request: the shared filters, then sorting and paging.
 *
 * `page` and `limit` are always present because the list is a page by
 * definition; the filter half never is (see {@link buildFilterParams}).
 */
export function buildListParams(query, window = {}) {
  const q = normaliseQuery(query);
  return {
    ...buildFilterParams(q, window),
    sort: q.sort,
    order: q.order,
    page: String(q.page),
    limit: String(q.limit),
  };
}

/**
 * Read the `{items,total,page,limit,pages}` envelope defensively.
 *
 * A bare array (the shape the unpaged endpoint returns) is accepted too, so a
 * route falling back to the old endpoint cannot blank the table.  Nothing here
 * trusts `total`: a page that arrives with more rows than it claimed still
 * reports what it actually holds.
 */
export function parseEnvelope(data) {
  if (Array.isArray(data)) {
    return {
      items: data, total: data.length, page: 1,
      limit: data.length || DEFAULT_LIMIT, pages: data.length ? 1 : 0,
    };
  }
  const body = data && typeof data === 'object' ? data : {};
  const items = Array.isArray(body.items) ? body.items : [];
  const rawTotal = Math.trunc(Number(body.total));
  const total = Number.isFinite(rawTotal) ? Math.max(0, rawTotal) : items.length;
  const limit = positiveInt(body.limit, DEFAULT_LIMIT);
  const rawPages = Math.trunc(Number(body.pages));
  const pages = Number.isFinite(rawPages) && rawPages > 0
    ? rawPages
    : (total ? Math.ceil(total / limit) : 0);
  const page = Math.min(positiveInt(body.page, 1), Math.max(1, pages));
  return { items, total, page, limit, pages };
}

/**
 * The page buttons to show: a sliding window of at most `span` numbers.
 *
 * `truncatedStart`/`truncatedEnd` let the caller draw a "…" instead of a jump —
 * a screen-reader user hears "more pages", never an unexplained gap.
 */
export function pageWindow(page, pages, span = 5) {
  const total = Math.max(0, Math.trunc(Number(pages)) || 0);
  const current = Math.min(positiveInt(page, 1), Math.max(1, total));
  if (!total) return { first: 0, last: 0, numbers: [], truncatedStart: false, truncatedEnd: false };
  const size = Math.max(1, Math.trunc(Number(span)) || 5);
  let first = Math.max(1, current - Math.floor((size - 1) / 2));
  let last = Math.min(total, first + size - 1);
  first = Math.max(1, last - size + 1);
  const numbers = [];
  for (let n = first; n <= last; n += 1) numbers.push(n);
  return { first, last, numbers, truncatedStart: first > 1, truncatedEnd: last < total };
}
