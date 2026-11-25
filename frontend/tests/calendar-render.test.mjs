/* AppointmentCalendar — server-rendered markup contract.
 *
 * The rest of the suite covers the pure model (`calendar-grid.test.mjs`) and the
 * page-level contract (`appointments-calendar-integration.test.mjs`). Neither
 * can tell whether the component actually *emits* a usable calendar, because
 * `node --test` has no DOM.
 *
 * This test closes that gap without adding a dependency: the component is
 * compiled with the SWC binary that ships inside Next (a direct dependency,
 * `next/dist/build/swc`) and rendered with `react-dom/server`. The result is a
 * real HTML string built from real props, so a regression in JSX — a chip
 * downgraded to a <div>, a lost aria-label, a dropped row — fails here.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const fileUrl = (...parts) => pathToFileURL(path.join(FE, ...parts)).href;

/* Dynamic import() takes a URL, not a path. A bare absolute path only works on
 * POSIX ("/repo/..."); on Windows ("E:\repo\...") Node rejects it with
 * ERR_UNSUPPORTED_ESM_URL_SCHEME and the whole file fails before a single test
 * registers. Converting with pathToFileURL makes the same specifier valid on
 * both platforms without touching what is imported. */
let swc = null;
try {
  swc = (await import(pathToFileURL(path.join(FE, 'node_modules/next/dist/build/swc/index.js')).href)).default;
} catch {
  swc = null;
}

const React = (await import(pathToFileURL(path.join(FE, 'node_modules/react/index.js')).href)).default;
const { renderToStaticMarkup } =
  (await import(pathToFileURL(path.join(FE, 'node_modules/react-dom/server.node.js')).href)).default;

/** Compile the shipped component to ESM that a bare `node` process can import. */
let compiled = null;
async function loadComponent() {
  if (compiled) return compiled;
  const source = fs.readFileSync(path.join(FE, 'components/AppointmentCalendar.js'), 'utf8');
  // Bare specifiers are fine inside Next; here they must resolve from /tmp.
  const scoped = source
    .replace("from 'react'", `from '${fileUrl('node_modules/react/index.js')}'`)
    .replace("from '../lib/calendar/grid'", `from '${fileUrl('lib/calendar/grid.js')}'`)
    .replace("from '../lib/calendar/highlight'", `from '${fileUrl('lib/calendar/highlight.js')}'`)
    .replace("from '../lib/status'", `from '${fileUrl('lib/status.js')}'`);
  const { code } = await swc.transform(scoped, {
    filename: 'AppointmentCalendar.js',
    jsc: {
      parser: { syntax: 'ecmascript', jsx: true },
      transform: { react: { runtime: 'classic', development: false } },
    },
    module: { type: 'es6' },
  });
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'amsdp-cal-'));
  const file = path.join(dir, 'cal.mjs');
  fs.writeFileSync(file, code);
  try {
    compiled = (await import(pathToFileURL(file).href)).default;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  return compiled;
}

/* Fixtures shaped like the API: templates live inside the schedule. */
const WEEK = ['2026-11-14', '2026-11-15', '2026-11-16', '2026-11-17', '2026-11-18', '2026-11-19', '2026-11-20'];
const SCHEDULES = [{
  id: 's1', doctor_id: 'd1', status: 'active',
  slot_templates: [{
    day_of_week: 0, start_time: '09:00', end_time: '10:00',
    slot_duration_minutes: 15, max_patients: 4,
  }],
}];
const APPOINTMENTS = [
  { id: 'a1', appointment_date: '2026-11-16', start_time: '09:00', status: 'CONFIRMED', patient_name: 'রহিম উদ্দিন', token_number: 'A-12' },
  { id: 'a2', appointment_date: '2026-11-16', start_time: '09:00', status: 'CHECKED_IN', patient_name: 'করিম মিয়া' },
  { id: 'a3', appointment_date: '2026-11-16', start_time: '02:45', status: 'BOOKED', patient_name: 'জসিম' },
  { id: 'a4', appointment_date: '2026-11-18', start_time: '21:30', status: 'CANCELLED', patient_name: 'নাসিমা' },
];
const LABELS = {
  time: 'সময়', full: 'ভর্তি', closed: 'শিডিউল নেই', past: 'সময় শেষ',
  bookAt: 'বুক করুন', grid: 'অ্যাপয়েন্টমেন্ট',
};

const render = (Cal, overrides = {}) => renderToStaticMarkup(React.createElement(Cal, {
  dates: WEEK,
  appointments: APPOINTMENTS,
  schedules: SCHEDULES,
  today: '2026-11-17',
  lang: 'bn',
  labels: LABELS,
  patientName: (a) => a.patient_name,
  doctorName: () => 'ডা. রহমান',
  showDoctor: false,
  showCapacity: true,
  ...overrides,
}));

const rowsOf = (html) =>
  [...html.matchAll(/font-variant-numeric:tabular-nums">([^<]+)</g)].map((m) => m[1]);

test('the component renders a real grid, not just a wrapper', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const html = render(Cal);

  assert.match(html, /class="appt-cal-wrap"/);
  assert.match(html, /max-height:68vh/, 'the grid scrolls inside its own box');
  assert.match(html, /role="grid"[^>]*aria-label="অ্যাপয়েন্টমেন্ট"/);

  // One header per day, one gutter cell per row, and a full rectangle of cells.
  assert.equal((html.match(/font-weight:700;line-height:1\.1/g) || []).length, 7);
  const rows = rowsOf(html);
  assert.ok(rows.length > 0, 'no time rows were emitted');
  assert.equal((html.match(/role="gridcell"/g) || []).length, rows.length * 7);
  assert.equal((html.match(/aria-current="date"/g) || []).length, 1, 'today must be marked once');
});

test('every appointment is a real button chip, cancellations included', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const html = render(Cal);

  // a <div> with an onClick is unreachable by keyboard — the chips must be buttons.
  const chips = html.match(/title="[^"]*· (CONFIRMED|CHECKED_IN|BOOKED|CANCELLED)"/g) || [];
  assert.equal(chips.length, APPOINTMENTS.length, 'one chip per appointment, none hidden');

  assert.match(html, /text-decoration:line-through/, 'cancelled chip reads as struck through');
  assert.match(html, /A-12/, 'token number is on the chip');
  assert.match(html, /রহিম উদ্দিন/, 'patient name is on the chip');
});

test('a booking outside the published hours still gets a row, in order', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const rows = rowsOf(render(Cal));

  // 09:00–10:00 in 15-minute slots = 09:00/09:15/09:30/09:45, plus the two
  // off-grid demo bookings. A slot-only axis would have hidden a3 and a4.
  assert.deepEqual(rows, ['02:45', '09:00', '09:15', '09:30', '09:45', '21:30']);
});

test('every published slot is offered a "+", and capacity is shown honestly', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const html = render(Cal, { today: '2026-11-16' });

  const offered = [...html.matchAll(/aria-label="বুক করুন [^"]*?(\d{2}:\d{2})"/g)].map((m) => m[1]);
  // All four published Monday slots are clickable, including the 2-of-4 one.
  // 02:45 is NOT offered: a demo booking already sits there and no template
  // covers it, so capacity is 1 and the slot is full — the same fallback the
  // API applies. 21:30 IS offered: an empty out-of-hours row is bookable at
  // capacity 1. Whether such a row should offer "+" at all is open item O-R.
  assert.deepEqual(offered, ['09:00', '09:15', '09:30', '09:45', '21:30']);
  assert.match(html, />2\/4</, 'live booked/capacity on the slot');

  // A spent day offers nothing to click into.
  const spent = render(Cal, { today: '2026-11-18' });
  assert.equal((spent.match(/aria-label="বুক করুন [^"]+"/g) || []).length, 0);
});

test('the grid says why a cell cannot be used', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const html = render(Cal);

  // Tue 17 Nov is "today" here, so Monday's earlier open cells are spent.
  assert.match(html, />সময় শেষ</, 'past cells are labelled');
  // Only Monday has a template in this fixture.
  assert.match(html, />শিডিউল নেই</, 'unpublished weekdays are labelled, not blank');

  const closedHtml = render(Cal, { today: '2026-11-14' });
  assert.doesNotMatch(closedHtml, />সময় শেষ</, 'nothing is "past" when today is the first day');
});

test('day view renders a single column of the same grid', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const html = render(Cal, { dates: ['2026-11-16'], today: '2026-11-16' });

  assert.equal((html.match(/font-weight:700;line-height:1\.1/g) || []).length, 1);
  const rows = rowsOf(html);
  assert.equal((html.match(/role="gridcell"/g) || []).length, rows.length);
  assert.match(html, /aria-current="date"/);
});

test('a chip is a card: patient first, then time · doctor, status and chamber', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  const card = [{
    id: 'c1', appointment_date: '2026-11-16', start_time: '09:00', status: 'CONFIRMED',
    patient_name: 'রহিম উদ্দিন', token_number: 'A-12',
    location_label: '২য় তলা / কার্ডিওলজি / ২০৪',
  }];
  const html = render(Cal, { appointments: card, showDoctor: true });

  // The accessible name reads in the same order the card does.
  assert.ok(html.includes('aria-label="রহিম উদ্দিন · 09:00 · ডা. রহমান · নিশ্চিত"'),
    'the accessible name reads like the card');
  assert.ok(html.includes('>09:00 · ডা. রহমান<'), 'time and doctor share one line');
  assert.ok(html.includes('>নিশ্চিত<'), 'the status is spelled out, never colour-only');
  assert.ok(html.includes('>২য় তলা / কার্ডিওলজি / ২০৪<'),
    'the chamber says where to send the patient');
  assert.ok(html.includes('title="09:00 · রহিম উদ্দিন · A-12 · CONFIRMED"'),
    'the tooltip keeps the machine-readable status');
});

test('a week cell summarises what does not fit instead of clipping it', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();
  // Five patients in one 09:00 slot: three fit a week cell, two do not.
  const busy = Array.from({ length: 5 }, (_, i) => ({
    id: 'b' + i, appointment_date: '2026-11-16', start_time: '09:00',
    status: 'BOOKED', patient_name: 'রোগী ' + i,
  }));
  const labels = { ...LABELS, more: 'আরও {n}' };

  const week = render(Cal, { appointments: busy, labels });
  assert.equal((week.match(/title="[^"]*· BOOKED"/g) || []).length, 3,
    'a week cell shows three cards');
  assert.ok(week.includes('>আরও 2<'), 'the rest is counted, never silently dropped');
  // Without a day handler the summary is text, not a button that does nothing.
  assert.ok(!week.includes('class="appt-cal-more"'));

  const clickable = render(Cal, { appointments: busy, labels, onDayClick: () => {} });
  assert.ok(clickable.includes('class="appt-cal-more"'),
    'with a day handler the summary is a real control');
  assert.ok(clickable.includes('aria-label="আরও 2 — রোগী 3, রোগী 4"'),
    'the summary names the rows it stands for');

  // The day view has the full column height, so every card is shown there.
  const day = render(Cal, {
    dates: ['2026-11-16'], today: '2026-11-16', appointments: busy, labels,
  });
  assert.equal((day.match(/title="[^"]*· BOOKED"/g) || []).length, 5);
  assert.ok(!day.includes('>আরও '), 'nothing is summarised when everything fits');

  const plain = render(Cal, { appointments: busy });
  assert.ok(plain.includes('>+2<'), 'no translated template: the label degrades to +N');
});

test('the searched substring is marked inside the card, and escaped', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  const Cal = await loadComponent();

  // What was searched for is marked where it was found — on the name, and on a
  // token if it happens to match there.  Nothing else is touched.
  const html = render(Cal, { highlightTerm: 'রহিম' });
  assert.ok(html.includes('<mark class="appt-cal-hit">রহিম</mark>'), 'the match is marked');
  assert.equal((html.match(/<mark class="appt-cal-hit">/g) || []).length, 1,
    'only the matching card carries a mark');
  assert.ok(html.includes('করিম মিয়া'), 'an unmatched name is still rendered in full');

  // Matched on the token: the same treatment, still one card.
  const byToken = render(Cal, { highlightTerm: 'A-1' });
  assert.ok(byToken.includes('<mark class="appt-cal-hit">A-1</mark>'));

  // No term: identical markup to a page with no search, so the card does not
  // change shape when a filter is applied and cleared.
  const none = render(Cal, { highlightTerm: '' });
  assert.ok(!none.includes('<mark'), 'no search, no marks');

  // The term is data, never markup: a name containing HTML renders as text and
  // the search term cannot inject a tag either.
  const hostile = render(Cal, {
    appointments: [{ id: 'x1', appointment_date: '2026-11-16', start_time: '09:00',
      status: 'BOOKED', patient_name: '<img src=x onerror=alert(1)>' }],
    highlightTerm: '<img',
  });
  // The mark wraps escaped text; the rest of the name stays text too.
  assert.ok(hostile.includes('<mark class="appt-cal-hit">&lt;img</mark>'),
    'the marked span holds escaped text, not a live tag');
  assert.ok(hostile.includes('onerror=alert(1)&gt;'), 'the remainder is escaped, not executed');
  assert.ok(!/<img[\s>]/i.test(hostile), 'no tag is ever emitted from a patient name');
});


