/* Appointment calendar model — date, slot and capacity tests.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 *
 * The calendar keeps every decision in `lib/calendar/grid.js` and leaves the
 * React component as a thin rendering shell, so these tests exercise the exact
 * code the browser runs. Fixtures follow the real shapes: `slot_templates` as
 * seeded by backend/seed/seed_demo.py and appointments as returned by
 * `GET /api/v1/appointments`.
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  isoOf, parseIso, addDays, addMonths, jsDay, pythonWeekday, startOfWeek, weekDates,
  minutesOf, timeOf, compareTime, slotOf,
  expandTemplate, templatesForDate, slotsForDate, capacityFor, scheduleCovers,
  bucketAppointments, appointmentsOn, countActive, gridTimes, cellState,
  rangeFor, shiftAnchor, rangeTotal,
  dayLabel, formatDayLong, formatRange, weekdayName, todayIso,
  DEFAULT_SLOT_DURATION, MAX_SLOTS_PER_TEMPLATE,
} from '../lib/calendar/grid.js';

/* A Monday clinic 09:00–13:00 with 15-minute slots — the demo shape
 * (seed_demo.py DEMO_SCHEDULE_TEMPLATES[0]). */
const MONDAY_CLINIC = {
  id: 'sch-1', doctor_id: 'demo-dr-001', status: 'active', appointment_model: 'time_slot',
  slot_templates: [{ day_of_week: 0, start_time: '09:00', end_time: '13:00',
    slot_duration_minutes: 15, max_patients: 4 }],
};
const ALL_WEEK_CLINIC = {
  id: 'sch-2', doctor_id: 'demo-dr-002', status: 'active',
  slot_templates: [0, 1, 2, 3, 4, 5, 6].map((day) => ({ day_of_week: day,
    start_time: '10:00', end_time: '11:00', slot_duration_minutes: 30, max_patients: 2 })),
};
const INACTIVE_CLINIC = {
  id: 'sch-3', doctor_id: 'demo-dr-003', status: 'inactive',
  slot_templates: [{ day_of_week: 0, start_time: '09:00', end_time: '10:00',
    slot_duration_minutes: 15, max_patients: 4 }],
};

/** 2026-11-16 is a Monday; 2026-11-15 is the Sunday before it. */
const MON = '2026-11-16';
const SUN = '2026-11-15';

const appt = (over = {}) => ({
  id: Math.random().toString(36).slice(2), appointment_date: MON, start_time: '09:00',
  status: 'BOOKED', token_number: 'T-001', patient_id: 'p1', doctor_id: 'demo-dr-001',
  created_at: '2026-11-14T10:00:00', ...over,
});

test('a local Date round-trips through YYYY-MM-DD without a timezone shift', () => {
  assert.equal(isoOf(new Date(2026, 10, 15)), '2026-11-15');
  assert.equal(isoOf(parseIso('2026-11-15')), '2026-11-15');
  // Midnight-local must never render as the previous day, the usual toISOString bug.
  assert.equal(isoOf(new Date(2026, 0, 1, 0, 0, 0)), '2026-01-01');
  assert.match(todayIso(), /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(isoOf(parseIso(todayIso())), todayIso());
});

test('addDays crosses month and year boundaries', () => {
  assert.equal(addDays('2026-11-30', 1), '2026-12-01');
  assert.equal(addDays('2026-01-01', -1), '2025-12-31');
  assert.equal(addDays('2028-02-28', 1), '2028-02-29'); // leap year
  assert.equal(addMonths('2026-01-31', 1), '2026-02-28'); // clamped, not 03-03
});

test('the display week starts on Saturday, the working week in Bangladesh', () => {
  assert.equal(startOfWeek(SUN), '2026-11-14');       // Sat 14 … Fri 20
  assert.equal(jsDay('2026-11-14'), 6);
  const dates = weekDates(SUN);
  assert.equal(dates.length, 7);
  assert.equal(dates[0], '2026-11-14');
  assert.equal(dates[6], '2026-11-20');
  assert.deepEqual(weekDates('2026-11-14'), dates, 'any day of the week resolves alike');
});

test('slot_templates are indexed 0=Monday, as the seed writes them', () => {
  assert.equal(pythonWeekday(MON), 0);
  assert.equal(pythonWeekday('2026-11-15'), 6); // Sunday last, Python order
  assert.equal(jsDay(MON), 1);
});

test('a 09:00–13:00 clinic with 15-minute slots yields 16 slots', () => {
  const slots = expandTemplate(MONDAY_CLINIC.slot_templates[0]);
  assert.equal(slots.length, 16);
  assert.equal(slots[0].start, '09:00');
  assert.equal(slots[0].end, '09:15');
  assert.equal(slots[15].start, '12:45');
  assert.equal(slots[15].end, '13:00');
  assert.ok(slots.every((s) => s.capacity === 4));
  assert.deepEqual(expandTemplate({ start_time: '13:00', end_time: '09:00' }), []);
  assert.deepEqual(expandTemplate({}), []);
});

test('only the template matching the date weekday publishes hours', () => {
  assert.equal(templatesForDate([MONDAY_CLINIC], MON).length, 1);
  assert.equal(templatesForDate([MONDAY_CLINIC], SUN).length, 0);
  assert.equal(templatesForDate([INACTIVE_CLINIC], MON).length, 0, 'inactive schedules are closed');
  assert.equal(slotsForDate([ALL_WEEK_CLINIC], SUN).length, 2, '30-minute slots');
});

test('the slot defaults are the ones backend/common/slots.py uses', () => {
  // F-16: the browser must expand a template with the same arithmetic the
  // availability read publishes, or a free slot is shown where the API refuses.
  assert.equal(DEFAULT_SLOT_DURATION, 15);
  assert.equal(MAX_SLOTS_PER_TEMPLATE, 500);
  const bare = expandTemplate({ start_time: '09:00', end_time: '10:00' });
  assert.equal(bare.length, 4, '15-minute default, not the 30-minute row ladder');
  assert.equal(bare[3].start, '09:45');
  assert.equal(expandTemplate({ start_time: '09:00', end_time: '10:00' },
    { limit: 2 }).length, 2, 'the cap is respected');
  // A sub-5-minute duration is a configuration accident, not a consultation.
  const tiny = expandTemplate({ start_time: '09:00', end_time: '09:30',
    slot_duration_minutes: 1 });
  assert.equal(tiny[1].start, '09:05');
});

test('a template without day_of_week publishes every day', () => {
  // A row written before the field was validated applies to every day in
  // `templates_for_day`; the grid used to treat it as matching nothing.
  const legacy = { id: 'sch-legacy', doctor_id: 'd', status: 'active',
    slot_templates: [{ start_time: '09:00', end_time: '10:00',
      slot_duration_minutes: 30, max_patients: 3 }] };
  assert.equal(templatesForDate([legacy], MON).length, 1);
  assert.equal(templatesForDate([legacy], SUN).length, 1);
  assert.equal(slotsForDate([legacy], SUN).length, 2);
});

test('a schedule publishes nothing outside its effective window', () => {
  const bounded = { id: 'sch-4', doctor_id: 'demo-dr-004', status: 'active',
    effective_from: '2026-11-16', effective_to: '2026-11-20',
    slot_templates: [0, 1, 2, 3, 4, 5, 6].map((day) => ({ day_of_week: day,
      start_time: '09:00', end_time: '10:00', slot_duration_minutes: 30,
      max_patients: 2 })) };
  assert.equal(scheduleCovers(bounded, '2026-11-16'), true);
  assert.equal(scheduleCovers(bounded, '2026-11-15'), false, 'before the window');
  assert.equal(scheduleCovers(bounded, '2026-11-21'), false, 'after the window');
  assert.equal(scheduleCovers({ id: 's' }, '2026-11-21'), true, 'unbounded');
  assert.equal(slotsForDate([bounded], SUN).length, 0);
  assert.equal(slotsForDate([bounded], MON).length, 2);
  const closed = cellState({ iso: SUN, time: '09:00', schedules: [bounded] });
  assert.equal(closed.closed, true);
  assert.equal(closed.bookable, false);
  const open = cellState({ iso: MON, time: '09:00', schedules: [bounded] });
  assert.equal(open.bookable, true);
  // An `effective_from` carrying a full timestamp still compares as a date.
  assert.equal(scheduleCovers({ effective_from: '2026-11-16T00:00:00' },
    '2026-11-16'), true);
});

test('overlapping templates keep the larger capacity and never duplicate a start', () => {
  const wide = { id: 's', doctor_id: 'd', status: 'active',
    slot_templates: [
      { day_of_week: 0, start_time: '09:00', end_time: '10:00', slot_duration_minutes: 15, max_patients: 2 },
      { day_of_week: 0, start_time: '09:00', end_time: '10:00', slot_duration_minutes: 15, max_patients: 5 },
    ] };
  const slots = slotsForDate([wide], MON);
  assert.equal(slots.length, 4);
  assert.equal(slots[0].capacity, 5);
});

test('capacity falls back to the backend default of 1 outside a template', () => {
  assert.equal(capacityFor([MONDAY_CLINIC], MON, '09:00'), 4);
  assert.equal(capacityFor([MONDAY_CLINIC], MON, '12:45'), 4);
  assert.equal(capacityFor([MONDAY_CLINIC], MON, '13:00'), 1, 'half-open interval');
  assert.equal(capacityFor([MONDAY_CLINIC], SUN, '09:00'), 1);
  assert.equal(capacityFor([], MON, '09:00'), 1);
});

test('times parse, format and sort defensively', () => {
  assert.equal(minutesOf('09:15'), 555);
  assert.equal(minutesOf('9:05'), 545);
  assert.equal(minutesOf(''), null);
  assert.equal(minutesOf('24:00'), null);
  assert.equal(minutesOf('abc'), null);
  assert.equal(timeOf(555), '09:15');
  assert.equal(timeOf(1439), '23:59');
  assert.deepEqual(['11:00', '09:00', ''].sort(compareTime), ['09:00', '11:00', '']);
  assert.equal(slotOf({ start_time: '09:15:00' }), '09:15');
  assert.equal(slotOf({ start_time: '' }), '');
});

test('appointments bucket by date and time, keeping a slot for time-less rows', () => {
  const rows = [
    appt({ id: 'a', start_time: '09:00' }),
    appt({ id: 'b', start_time: '09:00' }),
    appt({ id: 'c', start_time: '21:37', appointment_date: '2026-11-17' }),
    appt({ id: 'd', start_time: '', appointment_date: MON }),
    { id: 'e' /* no date — malformed rows are ignored, not crashed on */ },
  ];
  const byDate = bucketAppointments(rows);
  assert.equal(byDate[MON]['09:00'].length, 2);
  assert.equal(byDate[MON]['21:37'], undefined);
  assert.equal(byDate['2026-11-17']['21:37'].length, 1);
  assert.equal(byDate[MON][''].length, 1, 'serial bookings stay visible');
  assert.deepEqual(bucketAppointments(null), {});
  assert.equal(appointmentsOn(rows, MON).length, 3);
  assert.equal(countActive(rows), 4);
  assert.equal(countActive([appt({ status: 'CANCELLED' })]), 0);
});

test('the row axis adds off-grid appointment times instead of hiding them', () => {
  const dates = weekDates(SUN);
  const times = gridTimes({ schedules: [MONDAY_CLINIC], dates, appointments: [
    appt({ start_time: '02:45' }), appt({ start_time: '21:37', appointment_date: '2026-11-17' }),
  ] });
  assert.ok(times.includes('02:45'), 'off-grid booking keeps a row');
  assert.ok(times.includes('21:37'));
  assert.ok(times.includes('09:00'));
  assert.deepEqual(times, [...times].sort(compareTime));
});

test('an empty clinic falls back to a 09:00–17:00 ladder', () => {
  const times = gridTimes({ schedules: [], dates: ['2026-11-16'], appointments: [] });
  assert.equal(times[0], '09:00');
  assert.equal(times[times.length - 1], '16:30');
  assert.equal(times.length, 16);
});

test('cellState reports open, full, closed and past cells correctly', () => {
  const byDate = bucketAppointments([
    appt({ start_time: '09:00', status: 'CONFIRMED' }),
    appt({ start_time: '09:00', status: 'CANCELLED' }),
  ]);
  const open = cellState({ iso: MON, time: '09:00', schedules: [MONDAY_CLINIC], byDate, today: SUN });
  assert.equal(open.items.length, 2, 'cancelled rows still display');
  assert.equal(open.booked, 1, 'only active rows consume capacity');
  assert.equal(open.capacity, 4);
  assert.equal(open.bookable, true);
  assert.equal(open.closed, false);

  const full = cellState({ iso: MON, time: '10:00', schedules: [MONDAY_CLINIC], today: SUN,
    byDate: bucketAppointments(Array.from({ length: 4 }, () => appt({ start_time: '10:00' }))) });
  assert.equal(full.full, true);
  assert.equal(full.bookable, false);
  assert.equal(full.remaining, 0);

  const closed = cellState({ iso: SUN, time: '09:00', schedules: [MONDAY_CLINIC], today: SUN });
  assert.equal(closed.closed, true);
  assert.equal(closed.bookable, false);

  const past = cellState({ iso: '2026-11-01', time: '09:00', schedules: [ALL_WEEK_CLINIC], today: SUN });
  assert.equal(past.past, true);
  assert.equal(past.bookable, false);
});

test('ranges and navigation cover exactly what the grid draws', () => {
  const week = rangeFor('week', SUN);
  assert.equal(week.from, '2026-11-14');
  assert.equal(week.to, '2026-11-20');
  assert.equal(week.dates.length, 7);
  const day = rangeFor('day', SUN);
  assert.deepEqual(day, { from: SUN, to: SUN, dates: [SUN] });
  assert.equal(shiftAnchor('week', SUN, 1), '2026-11-22');
  assert.equal(shiftAnchor('week', SUN, -1), '2026-11-08');
  assert.equal(shiftAnchor('day', SUN, 1), MON);
  assert.equal(shiftAnchor('day', MON, -1), SUN);
  assert.equal(rangeTotal([appt({ appointment_date: '2026-11-14' }),
    appt({ appointment_date: '2026-11-21' })], week), 1, 'range end is inclusive');
});

test('labels read correctly in Bangla and English', () => {
  assert.equal(weekdayName(MON, 'bn'), 'সোমবার');
  assert.equal(weekdayName(MON, 'bn', true), 'সোম');
  assert.equal(dayLabel(MON, 'bn'), 'সোম ১৬');
  assert.equal(formatDayLong(MON, 'bn'), 'সোমবার, ১৬ নভেম্বর ২০২৬');
  assert.equal(formatDayLong(MON, 'en'), 'Monday, 16 November 2026');
  assert.equal(formatRange('2026-11-14', '2026-11-20', 'bn'), '১৪ – ২০ নভেম্বর ২০২৬');
  assert.equal(formatRange('2026-11-14', '2026-11-20', 'en'), '14 – 20 November 2026');
  assert.equal(formatRange('2026-11-28', '2026-12-04', 'en'), '28 November – 4 December 2026');
  assert.equal(formatRange('2026-12-28', '2027-01-03', 'en'), '28 December 2026 – 3 January 2027');
  assert.equal(formatRange(MON, MON, 'en'), '16 November 2026');
});


