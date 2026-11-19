/* AMSDP appointment calendar — pure date/time model for the booking grid.
 *
 * No React, no DOM, no fetch. Every decision the calendar makes (which days are
 * shown, which times become rows, whether a cell is bookable, how many patients
 * are already in a slot) lives here so `frontend/tests/calendar-grid.test.mjs`
 * can exercise exactly the code the browser runs — the same split
 * `lib/bangla-name-sense/*` uses.
 *
 * TWO WEEK INDEXES LIVE IN THIS FILE. The names keep them apart:
 *
 *   pythonWeekday(iso)  0=Monday … 6=Sunday
 *     The index stored in `Schedule.slot_templates[].day_of_week`
 *     (backend/seed/seed_demo.py: "Mon-Fri morning/afternoon clinic" with
 *     day_of_week 0 on every doctor).
 *
 *   jsDay(iso)          0=Sunday … 6=Saturday
 *     `Date#getDay()`, used only to lay the display columns out.
 *
 * Dates are plain `YYYY-MM-DD` strings throughout: they sort lexicographically,
 * they never shift with a timezone, and they are what the API speaks.
 */

/** Saturday — the working week starts on শনিবার in Bangladesh (jsDay value). */
export const WEEK_START = 6;
/** Used only when a doctor has no published schedule for any visible day. */
export const DEFAULT_OPEN = '09:00';
export const DEFAULT_CLOSE = '17:00';
export const DEFAULT_STEP = 30;
/**
 * Slot length when a template omits `slot_duration_minutes`, and the cap on one
 * template's expansion. Both mirror `backend/common/slots.py`
 * (`DEFAULT_SLOT_DURATION`, `MAX_SLOTS_PER_TEMPLATE`) so the grid and
 * `/schedules/{id}/available-slots` cannot disagree about a slot boundary.
 * They are *not* `DEFAULT_STEP`: that is the empty-day row ladder, a display
 * fallback for a doctor with no published hours.
 */
export const DEFAULT_SLOT_DURATION = 15;
export const MAX_SLOTS_PER_TEMPLATE = 500;
/** Statuses that occupy a slot (mirrors backend capacity check). */
export const ACTIVE_STATUSES = Object.freeze([
  'BOOKED', 'AWAITING_CONFIRMATION', 'CONFIRMED', 'CHECKED_IN', 'IN_QUEUE',
]);

const pad2 = (n) => (n < 10 ? '0' + n : String(n));

/* ------------------------------------------------------------------ dates */

export function isoOf(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

export function parseIso(iso) {
  const [y, m, d] = String(iso || '').split('-').map(Number);
  return new Date(y || 1970, (m || 1) - 1, d || 1);
}

export function isIsoDate(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(String(value || ''));
}

export function addDays(iso, n) {
  const d = parseIso(iso);
  d.setDate(d.getDate() + n);
  return isoOf(d);
}

export function addMonths(iso, n) {
  const d = parseIso(iso);
  const day = d.getDate();
  d.setDate(1);
  d.setMonth(d.getMonth() + n);
  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
  d.setDate(Math.min(day, last));
  return isoOf(d);
}

export function jsDay(iso) {
  return parseIso(iso).getDay();
}

export function pythonWeekday(iso) {
  return (jsDay(iso) + 6) % 7;
}

export function startOfWeek(iso, weekStart = WEEK_START) {
  const d = parseIso(iso);
  d.setDate(d.getDate() - ((d.getDay() - weekStart + 7) % 7));
  return isoOf(d);
}

export function weekDates(iso, weekStart = WEEK_START) {
  const first = startOfWeek(iso, weekStart);
  return Array.from({ length: 7 }, (_, i) => addDays(first, i));
}

/* ------------------------------------------------------------------ times */

export function minutesOf(value) {
  const m = /^(\d{1,2}):(\d{2})/.exec(String(value || '').trim());
  if (!m) return null;
  const total = Number(m[1]) * 60 + Number(m[2]);
  return total >= 0 && total < 24 * 60 ? total : null;
}

export function timeOf(minutes) {
  const v = ((Math.round(minutes) % 1440) + 1440) % 1440;
  return `${pad2(Math.floor(v / 60))}:${pad2(v % 60)}`;
}

/** `'HH:MM'` sort key; unparseable times sort last. */
export function compareTime(a, b) {
  const x = minutesOf(a);
  const y = minutesOf(b);
  return (x === null ? 9999 : x) - (y === null ? 9999 : y);
}

/** The `HH:MM` an appointment belongs to, or `''` when it has no time (serial). */
export function slotOf(appt) {
  const minutes = minutesOf(appt && appt.start_time);
  return minutes === null ? '' : timeOf(minutes);
}

/* --------------------------------------------------------------- schedules */

/**
 * Expand one `slot_template` into bookable slots.
 *
 * `slot_duration_minutes` is the slot length, so a 09:00–13:00 clinic with
 * 15-minute slots yields 16 slots — the same arithmetic
 * `backend/common/slots.slot_starts` uses, and the same defaults: 15 minutes
 * when the field is absent, never under 5, never more than
 * `MAX_SLOTS_PER_TEMPLATE` from one template.
 */
export function expandTemplate(template, { limit = MAX_SLOTS_PER_TEMPLATE } = {}) {
  const start = minutesOf(template && template.start_time);
  const end = minutesOf(template && template.end_time);
  if (start === null || end === null || end <= start) return [];
  const step = Math.max(Number(template.slot_duration_minutes) || DEFAULT_SLOT_DURATION, 5);
  const capacity = Math.max(Number(template.max_patients) || 1, 1);
  const slots = [];
  for (let m = start; m < end && slots.length < limit; m += step) {
    slots.push({ start: timeOf(m), end: timeOf(Math.min(m + step, end)), capacity });
  }
  return slots;
}

/** Active schedules only: an inactive schedule publishes no clinic hours. */
function activeSchedules(schedules) {
  return (schedules || []).filter((s) => (s && (s.status || 'active')) === 'active');
}

/**
 * True when a schedule's effective window contains `iso`.
 *
 * Mirrors `_date_covered` in `backend/appointment/main.py` and the guard in
 * `GET /schedules/{id}/available-slots`: a schedule that starts next month
 * publishes nothing today. Without this the grid offered bookable cells for
 * dates the write path refuses — the same divergence F-15 records for weekdays.
 */
export function scheduleCovers(schedule, iso) {
  const from = String((schedule && schedule.effective_from) || '').slice(0, 10);
  const to = String((schedule && schedule.effective_to) || '').slice(0, 10);
  if (from && iso < from) return false;
  if (to && iso > to) return false;
  return true;
}

/** The `{schedule, template}` pairs that apply on `iso` for its weekday. */
export function templatesForDate(schedules, iso) {
  const weekday = pythonWeekday(iso);
  const out = [];
  activeSchedules(schedules).forEach((schedule) => {
    if (!scheduleCovers(schedule, iso)) return;
    (schedule.slot_templates || []).forEach((template) => {
      if (!template || typeof template !== 'object') return;
      // A template with no `day_of_week` applies to every day, exactly as
      // `backend/common/slots.templates_for_day` treats a row written before the
      // field was validated: closing a doctor's published hours is the worse
      // failure. (`Number(undefined)` is NaN, which used to match nothing.)
      const day = template.day_of_week;
      if (day !== undefined && day !== null && Number(day) !== weekday) return;
      out.push({ schedule, template });
    });
  });
  return out;
}

/**
 * Bookable slots for one date, one entry per start time.
 *
 * When two templates overlap (morning + afternoon clinic) the larger
 * `max_patients` wins, so the grid never under-reports capacity.
 */
export function slotsForDate(schedules, iso) {
  const merged = new Map();
  templatesForDate(schedules, iso).forEach(({ schedule, template }) => {
    expandTemplate(template).forEach((slot) => {
      const previous = merged.get(slot.start);
      if (!previous) {
        merged.set(slot.start, { ...slot, doctor_id: schedule.doctor_id || '' });
      } else {
        merged.set(slot.start, {
          ...previous,
          capacity: Math.max(previous.capacity, slot.capacity),
          end: compareTime(slot.end, previous.end) > 0 ? slot.end : previous.end,
        });
      }
    });
  });
  return [...merged.values()].sort((a, b) => compareTime(a.start, b.start));
}

/**
 * Patients allowed in `time` on `iso`.
 *
 * Falls back to 1 when no schedule covers that time — exactly what
 * `create_appointment` does when no template matches (`max_capacity = 1`).
 */
export function capacityFor(schedules, iso, time) {
  const at = minutesOf(time);
  if (at === null) return 1;
  const slot = slotsForDate(schedules, iso).find(
    (s) => minutesOf(s.start) <= at && at < minutesOf(s.end),
  );
  return slot ? slot.capacity : 1;
}

/* ------------------------------------------------------------ appointments */

/** `{ '2026-11-15': { '09:00': [appointment, …], '': [no-time appointments] } }` */
export function bucketAppointments(appointments) {
  const byDate = {};
  (appointments || []).forEach((appt) => {
    const date = (appt && appt.appointment_date) || '';
    if (!isIsoDate(date)) return;
    const slot = slotOf(appt);
    if (!byDate[date]) byDate[date] = {};
    if (!byDate[date][slot]) byDate[date][slot] = [];
    byDate[date][slot].push(appt);
  });
  Object.keys(byDate).forEach((date) => {
    Object.keys(byDate[date]).forEach((slot) => {
      byDate[date][slot].sort(
        (a, b) => String(a.created_at || '').localeCompare(String(b.created_at || '')),
      );
    });
  });
  return byDate;
}

/** Appointments on one date, in grid order (time, then creation). */
export function appointmentsOn(appointments, iso) {
  return (appointments || [])
    .filter((a) => a && a.appointment_date === iso)
    .sort((a, b) => compareTime(a.start_time, b.start_time)
      || String(a.created_at || '').localeCompare(String(b.created_at || '')));
}

/** How many of these appointments occupy a slot (cancelled ones still display). */
export function countActive(appointments) {
  return (appointments || []).filter((a) => ACTIVE_STATUSES.includes(a.status)).length;
}

/**
 * The grid's vertical axis: every time the visible days need a row for.
 *
 * Slot starts come from the schedules; appointment times are added on top so an
 * off-grid booking (the demo data contains 02:45 and 21:37) is never hidden.
 * With no schedules and no bookings the row set falls back to a plain
 * 09:00–17:00 ladder, which is what an unpublished clinic should look like.
 */
export function gridTimes({ schedules = [], dates = [], appointments = [], step = DEFAULT_STEP } = {}) {
  const times = new Set();
  (dates || []).forEach((iso) => {
    slotsForDate(schedules, iso).forEach((slot) => times.add(slot.start));
  });
  (appointments || []).forEach((appt) => {
    if (!appt || !(dates || []).includes(appt.appointment_date)) return;
    const slot = slotOf(appt);
    if (slot) times.add(slot);
  });
  if (times.size === 0) {
    for (let m = minutesOf(DEFAULT_OPEN); m < minutesOf(DEFAULT_CLOSE); m += step) {
      times.add(timeOf(m));
    }
  }
  return [...times].sort(compareTime);
}

/**
 * Everything the grid needs to render one cell.
 *
 * `closed`  — the doctor publishes no clinic hours on that weekday.
 * `past`    — that date is over; the UI refuses new bookings there.
 * `items`   — appointments in the cell, including cancelled ones, so nothing
 *             is ever hidden from the receptionist.
 */
export function cellState({ iso, time, schedules = [], byDate = {}, today = '' } = {}) {
  const items = ((byDate[iso] || {})[time]) || [];
  const capacity = capacityFor(schedules, iso, time);
  const booked = countActive(items);
  const closed = templatesForDate(schedules, iso).length === 0;
  const past = Boolean(today) && iso < today;
  return {
    iso,
    time,
    items,
    capacity,
    booked,
    remaining: Math.max(capacity - booked, 0),
    closed,
    past,
    full: booked >= capacity,
    bookable: !past && !closed && booked < capacity,
  };
}

/* ------------------------------------------------------- cell chip layout */

/**
 * Split a cell's appointments into the ones that fit and the ones summarised.
 *
 * A 15-minute slot in a week column is about three cards tall.  Rather than let
 * the fourth card overflow silently, or shrink every card until nobody can read
 * it, the cell shows the first `max` and a "+N more" summary.  Nothing is lost:
 * the summary counts the hidden rows, names them in its tooltip and switches the
 * grid to the day view, where the same cell has the full column height.
 *
 * `max` is never allowed to be 0 — a cell that renders no card at all would be
 * indistinguishable from an empty slot.
 */
export function chipLayout(items, { max = 3 } = {}) {
  const list = Array.isArray(items) ? items : [];
  const cap = Number.isFinite(Number(max)) ? Math.max(1, Math.trunc(Number(max))) : list.length;
  if (list.length <= cap) return { shown: list, hidden: 0, overflow: false };
  return { shown: list.slice(0, cap), hidden: list.length - cap, overflow: true };
}

/**
 * The "+N more" caption.  `template` is a translated pattern containing `{n}`
 * (e.g. `'আরও {n}'`); without one the label degrades to `+N` rather than to a
 * half-translated sentence.
 */
export function moreLabel(template, hidden) {
  const n = Math.max(0, Math.trunc(Number(hidden)) || 0);
  const text = String(template == null ? '' : template).trim();
  if (!text) return '+' + n;
  return text.includes('{n}') ? text.split('{n}').join(String(n)) : text + ' ' + n;
}

/* ------------------------------------------------------------------- views */

/**
 * The visible range for a view. `day` is one date, `week` is seven — both
 * inclusive and both `YYYY-MM-DD`, so they can be sent straight to
 * `GET /api/v1/appointments?date_from=…&date_to=…`.
 */
export function rangeFor(view, anchor) {
  if (view === 'day') return { from: anchor, to: anchor, dates: [anchor] };
  const dates = weekDates(anchor);
  return { from: dates[0], to: dates[6], dates };
}

/** Anchor of the neighbouring day (day view) or week (week view). */
export function shiftAnchor(view, anchor, delta) {
  return view === 'day' ? addDays(anchor, delta) : addDays(anchor, delta * 7);
}

/** How many appointments fall inside a range — the footer count. */
export function rangeTotal(appointments, range) {
  return (appointments || []).filter(
    (a) => a && a.appointment_date >= range.from && a.appointment_date <= range.to,
  ).length;
}

/* ------------------------------------------------------------------ labels */

export const WEEKDAYS = {
  bn: ['রবিবার', 'সোমবার', 'মঙ্গলবার', 'বুধবার', 'বৃহস্পতিবার', 'শুক্রবার', 'শনিবার'],
  en: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
};

export const WEEKDAYS_SHORT = {
  bn: ['রবি', 'সোম', 'মঙ্গল', 'বুধ', 'বৃহঃ', 'শুক্র', 'শনি'],
  en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
};

export const MONTHS = {
  bn: ['জানুয়ারি', 'ফেব্রুয়ারি', 'মার্চ', 'এপ্রিল', 'মে', 'জুন', 'জুলাই',
    'আগস্ট', 'সেপ্টেম্বর', 'অক্টোবর', 'নভেম্বর', 'ডিসেম্বর'],
  en: ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'],
};

const pick = (map, lang) => map[lang] || map.bn;

const BN_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];

/**
 * Bangla numerals for display text only — the same digits `Intl` produces for
 * `bn-BD`, which is what `lib/i18n.fmtDate` and the DQDS already show.
 * `YYYY-MM-DD` strings and `HH:MM` slot identifiers are never localised: they
 * are API values, and the schedules page and the database speak Latin digits.
 */
export function localizeDigits(value, lang = 'bn') {
  const text = String(value);
  return lang === 'bn' ? text.replace(/\d/g, (d) => BN_DIGITS[Number(d)]) : text;
}

/** 'শনিবার' / 'শনি' (short) — indexed by `jsDay`, the display-column order. */
export function weekdayName(iso, lang = 'bn', short = false) {
  return pick(short ? WEEKDAYS_SHORT : WEEKDAYS, lang)[jsDay(iso)];
}

/** 'শনি ১৪' — the column header of a week grid. */
export function dayLabel(iso, lang = 'bn') {
  return `${weekdayName(iso, lang, true)} ${localizeDigits(parseIso(iso).getDate(), lang)}`;
}

/** 'শনিবার, ১৫ নভেম্বর ২০২৬' — the day-view heading. */
export function formatDayLong(iso, lang = 'bn') {
  const d = parseIso(iso);
  const day = localizeDigits(d.getDate(), lang);
  return `${weekdayName(iso, lang)}, ${day} ${pick(MONTHS, lang)[d.getMonth()]} ${localizeDigits(d.getFullYear(), lang)}`;
}

/** '১৫ – ২১ নভেম্বর ২০২৬', collapsing whatever the two dates share. */
export function formatRange(from, to, lang = 'bn') {
  const months = pick(MONTHS, lang);
  const local = (n) => localizeDigits(n, lang);
  const a = parseIso(from);
  const b = parseIso(to);
  const [y1, y2] = [local(a.getFullYear()), local(b.getFullYear())];
  const [m1, m2] = [a.getMonth(), b.getMonth()];
  const [d1, d2] = [local(a.getDate()), local(b.getDate())];
  if (from === to) return `${d1} ${months[m1]} ${y1}`;
  if (y1 === y2 && m1 === m2) return `${d1} – ${d2} ${months[m1]} ${y1}`;
  if (y1 === y2) return `${d1} ${months[m1]} – ${d2} ${months[m2]} ${y1}`;
  return `${d1} ${months[m1]} ${y1} – ${d2} ${months[m2]} ${y2}`;
}

/** Today in the browser's own timezone — never `toISOString()`, which is UTC. */
export function todayIso(now = new Date()) {
  return isoOf(now);
}
