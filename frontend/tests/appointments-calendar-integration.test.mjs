/* Appointments calendar view — integration and regression-preservation tests.
 *
 * The pages are JSX, which plain Node cannot parse without a bundler, and the
 * project deliberately has no DOM/component-test dependency. These tests
 * therefore pin the *contract* between the page, the calendar component and the
 * pure model — the same approach banglanamesense-integration.test.mjs uses — and
 * prove that nothing the receptionist could do before the refactor was lost.
 *
 * Complemented by `npm run build` (the page and component must compile in the
 * real Next pipeline), `tests/calendar-grid.test.mjs` (the arithmetic) and the
 * backend suite (the range filter the grid depends on).
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = (rel) => readFileSync(new URL(rel, import.meta.url), 'utf8');
const page = read('../pages/appointments.js');
const component = read('../components/AppointmentCalendar.js');
const model = read('../lib/calendar/grid.js');

test('the page renders the reusable calendar component, not an inline grid', () => {
  assert.match(page, /import AppointmentCalendar from '\.\.\/components\/AppointmentCalendar'/);
  assert.match(page, /<AppointmentCalendar/);
  assert.match(component, /export default function AppointmentCalendar/);
});

test('calendar arithmetic is imported from the tested pure model', () => {
  assert.match(page, /from '\.\.\/lib\/calendar\/grid'/);
  for (const fn of ['rangeFor', 'shiftAnchor', 'formatRange', 'formatDayLong', 'todayIso',
    'slotsForDate', 'slotOf', 'ACTIVE_STATUSES']) {
    assert.ok(page.includes(fn), `page must use ${fn} from the model`);
  }
  assert.match(component, /from '\.\.\/lib\/calendar\/grid'/);
  // The component is presentational: no fetching, no direct API access.
  assert.doesNotMatch(component, /fetch\(|apiFetch|XMLHttpRequest/);
});

test('the grid asks for one server-side date window per view, filtered like the list', () => {
  assert.match(model, /export function rangeFor/);
  // One builder produces the filter half of the grid request and of the list
  // request, so the search box cannot apply to one view and not the other —
  // the defect AMSDP-CALENDAR-FILTER-01 (F-1/F-2) recorded.
  assert.match(page, /buildFilterParams\(query, \{ from: range\.from, to: range\.to \}\)/);
  assert.match(page, /'\/api\/v1\/appointments\?' \+ gridParams/);
  // Every shared control writes into the one query object the grid reads.
  assert.match(page, /setFilter\(q, 'q', searchText\)/);
  assert.match(page, /setQuery\(\(q\) => setFilter\(q, 'status', e\.target\.value\)\)/);
  assert.match(page, /setQuery\(\(q\) => setFilter\(q, 'branch_id', v\)\)/);
  assert.match(page, /setFilter\(q, 'doctor_id', value\)/);
  // The regression guard: the grid request used to be the window alone, which
  // is exactly how a search could change the list while the calendar ignored it.
  assert.doesNotMatch(page, /new URLSearchParams\(\{ date_from: range\.from, date_to: range\.to \}\)/);
});

test('a search says where the matches it cannot show are (D-2)', () => {
  // The index is a tested pure module plus one counts-only request.
  assert.match(page, /from '\.\.\/lib\/calendar\/matches'/);
  for (const fn of ['MATCHES_PATH', 'buildMatchParams', 'parseMatchIndex',
    'matchSummary', 'nearestMatchDate']) {
    assert.ok(page.includes(fn), `page must use ${fn} from the matches model`);
  }
  assert.match(page, /apiFetch\(MATCHES_PATH \+ '\?' \+ matchesParams\)/);
  // The window is deliberately *not* sent: the answer has to cover every date
  // the token may read, or the banner would only describe this week.
  assert.match(page, /buildMatchParams\(query\)/);
  assert.doesNotMatch(page, /buildMatchParams\(query, \{ from/);
  // …and it is not asked while the list is on screen, where every match is
  // already reachable by paging.
  assert.match(page, /if \(view === 'list' \|\| !matchIndexWanted\) return ''/);
  // The banner is announced, not just painted, and offers the nearest date.
  assert.match(page, /className='appt-matches' role='status' aria-live='polite'/);
  assert.match(page, /onClick=\{\(\) => setAnchor\(nearestOther\)\}/);
  assert.match(page, /outOfRange > 0/);
});

test('the matched substring is marked on the card, from the committed term', () => {
  // What is marked is what the server was asked for, not the keystroke buffer.
  assert.match(page, /highlightTerm=\{query\.q\}/);
  assert.match(component, /from '\.\.\/lib\/calendar\/highlight'/);
  assert.match(component, /highlightSegments\(text, term\)/);
  // A semantic <mark>, not a colour-only cue, and never dangerouslySetInnerHTML.
  assert.match(component, /<mark key=\{i\} className="appt-cal-hit">/);
  assert.doesNotMatch(component, /dangerouslySetInnerHTML/);
});

test('booking sends the same payload contract as before the refactor', () => {
  for (const field of ['patient_id', 'doctor_id', 'appointment_date', 'start_time',
    'booking_source']) {
    assert.ok(page.includes(field), `booking payload must still carry ${field}`);
  }
  assert.match(page, /booking_source: 'reception'/);
  assert.match(page, /apiFetch\('\/api\/v1\/appointments', \{\s*method: 'POST'/);
});

test('walk-in, check-in, status change and cancel-with-reason are preserved', () => {
  assert.match(page, /'\/api\/v1\/appointments\/walk-in'/);
  assert.match(page, /'\/api\/v1\/appointments\/' \+ appt\.id \+ '\/check-in'/);
  assert.match(page, /'\/api\/v1\/appointments\/' \+ appt\.id \+ '\/status'/);
  // Cancellation still demands a reason, through the shared dialog.
  assert.match(page, /<ConfirmDialog[^>]*requireReason/);
  assert.match(page, /changeStatus\(target, 'CANCELLED', reason\)/);
});

test('the previous table survives as the list view', () => {
  assert.match(page, /view === 'list'/);
  for (const column of ['tk', 'p', 'd', 'dt', 'tm', 'st']) {
    assert.ok(page.includes(`T('${column}')`), `list view keeps the ${column} column`);
  }
  assert.match(page, /ACTIONS\[a\.status\] \|\| \[\]/);
});

test('the list view searches, filters, sorts and pages on the server', () => {
  // The query model is the tested pure module, not ad-hoc string building.
  assert.match(page, /from '\.\.\/lib\/calendar\/list'/);
  for (const fn of ['buildListParams', 'parseEnvelope', 'pageWindow', 'toggleSort',
    'setFilter', 'clearFilters', 'isFiltered', 'setLimit', 'setPage', 'ariaSort']) {
    assert.ok(page.includes(fn), `page must use ${fn} from the list model`);
  }
  // One request to the paged endpoint, built from that model.
  assert.match(page, /'\/api\/v1\/appointments\/list\?' \+ listParams/);
  assert.match(page, /apiFetch\('\/api\/v1\/appointments\/list\?'/);
  // Sorting is announced on the header, not implied by an arrow alone.
  assert.match(page, /aria-sort=\{ariaSort\(query, column\)\}/);
  // Search is debounced, so typing does not fire a request per keystroke.
  assert.match(page, /setTimeout\(\(\) => \{\s*setQuery\(\(q\) => \(q\.q === searchText/);
  // The page size is restricted to what the API accepts.
  assert.match(page, /LIST_PAGE_SIZES\.map\(\(n\) => <option key=\{n\} value=\{n\}>\{n\}<\/option>\)/);
  // Bookings and status changes refresh the list as well as the grid.
  assert.match(page, /await refresh\(\)/);
});

test('the grid is keyboard reachable and screen-reader labelled', () => {
  // Chips and "+" cells are buttons, never click handlers on a div.
  assert.match(component, /role="grid"/);
  assert.match(component, /role="gridcell"/);
  assert.match(component, /aria-label=\{`\$\{labels\.bookAt \|\| 'Book'\}/);
  assert.match(component, /aria-current=\{iso === todayDate \? 'date' : undefined\}/);
  assert.match(page, /aria-pressed=\{view === v\}/);
  assert.match(page, /aria-label=\{T\('prev'\)\}/);
  assert.match(page, /aria-label=\{T\('searchPatient'\)\}/);
});

test('appointments are never hidden behind the schedule grid', () => {
  // Off-grid times become rows instead of disappearing.
  assert.match(model, /times\.add\(slot\)/);
  assert.match(model, /if \(times\.size === 0\)/);
  // Cancelled rows still display; only active ones consume capacity.
  assert.match(model, /export const ACTIVE_STATUSES/);
  assert.match(model, /remaining: Math\.max\(capacity - booked, 0\)/);
});
