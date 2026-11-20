/* Appointment booking feedback — F-18 and F-19 of the reliability gap analysis.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 *
 * Two things are proved here, and one thing is not.  Proved: the slot wording
 * and the refusal vocabulary are decided by `lib/calendar/booking.js` — the
 * exact module the browser imports — for every refusal sentence the appointment
 * service raises, and the booking dialog uses those decisions instead of pasting
 * the server's English into a Bangla screen (the old
 * `T('bookErr') + ': ' + String(e.message || e)`).  Not proved: how the dialog
 * looks in a browser.  No browser run was performed; the JSX structure is pinned
 * by source contract, the same split `symptom-picker-contract.test.mjs` uses.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  freeSeats, seatsWord, refusalCode, REFUSAL_KEYS, SEATS_WORD_MAX,
} from '../lib/calendar/booking.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const read = (rel) => fs.readFileSync(path.join(FE, rel), 'utf8');

const PAGE = 'pages/appointments.js';
const MODULE = 'lib/calendar/booking.js';

/** Code only — the comments are where the reasoning lives, not the rules. */
const stripComments = (source) =>
  source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

/** An error shaped exactly as `lib/auth.apiFetch` builds it. */
const refusal = (status, detail) =>
  Object.assign(new Error(String(detail)), { status, body: detail });

test('free seats are counted from capacity and live bookings, never below zero', () => {
  assert.equal(freeSeats({ capacity: 4, booked: 1 }), 3);
  assert.equal(freeSeats({ capacity: 4, booked: 4 }), 0);
  assert.equal(freeSeats({ capacity: 2, booked: 5 }), 0, 'overbooked never reads negative');
  assert.equal(freeSeats({}), 1, 'the backend default capacity is 1');
  assert.equal(freeSeats(null), 1);
  assert.equal(freeSeats({ capacity: '3', booked: '2' }), 1, 'payload strings still count');
  assert.equal(freeSeats({ capacity: 0, booked: 0 }), 1, 'capacity is never below 1');
});

test('a nearly full slot says its remaining room in words', () => {
  assert.equal(SEATS_WORD_MAX, 3);
  assert.deepEqual(seatsWord({ capacity: 4, booked: 4 }), { key: 'slotFull', n: 0 });
  assert.deepEqual(seatsWord({ capacity: 4, booked: 3 }), { key: 'seatLast', n: 1 });
  assert.deepEqual(seatsWord({ capacity: 4, booked: 2 }), { key: 'seatsLeft', n: 2 });
  assert.equal(seatsWord({ capacity: 4, booked: 0 }), null, 'an empty slot needs no sentence');
  assert.equal(seatsWord({ capacity: 8, booked: 3 }), null, 'five free is still plenty');
  // 3/4 and 4/4 must not read the same, which is what the arithmetic alone did.
  const almost = seatsWord({ capacity: 4, booked: 3 });
  const full = seatsWord({ capacity: 4, booked: 4 });
  assert.notEqual(almost.key, full.key);
});


test('every refusal the appointment service raises maps to one code', () => {
  const cases = [
    // appointment/main.py `_guard_slot`
    [refusal(422, 'slot_full: capacity 4 reached for the 09:00–09:15 slot '
      + '(3 booked, 0 free) — choose another slot'), 'slotFull'],
    [refusal(422, 'no_slot_covers_time: this doctor publishes no slot for '
      + '2031-06-02 covering 09:07 — book inside the doctor\'s configured hours'), 'noSlot'],
    // appointment/main.py `_resolve_location`
    [refusal(422, 'no clinic session covers this time — book inside the '
      + 'doctor\'s session window'), 'outsideSession'],
    [refusal(422, 'invalid date, use YYYY-MM-DD'), 'badDate'],
    [refusal(422, 'invalid date'), 'badDate'],
    [refusal(422, 'patient not found'), 'patientMissing'],
    [refusal(404, 'doctor not found'), 'doctorMissing'],
    [refusal(404, 'appointment not found'), 'notFound'],
    [refusal(422, 'cannot transition from BOOKED to COMPLETED'), 'badTransition'],
    [refusal(422, 'cannot reschedule CANCELLED'), 'badTransition'],
    [refusal(422, 'cannot transfer COMPLETED'), 'badTransition'],
    [refusal(422, 'cancellation reason is required'), 'needReason'],
    [refusal(422, 'no-show reason required'), 'needReason'],
    [refusal(404, 'branch not found'), 'branchMissing'],
    // FastAPI's own validation body: a list, not a sentence.
    [refusal(422, [{ loc: ['body', 'start_time'], msg: 'String should match pattern' }]),
      'badTime'],
  ];
  for (const [err, code] of cases) {
    assert.equal(refusalCode(err), code, `${err.body} must read as ${code}`);
  }
});

test('a refusal the module cannot read is reported as unread, not guessed', () => {
  assert.equal(refusalCode(refusal(500, 'internal error')), 'unknown');
  assert.equal(refusalCode(new Error('Failed to fetch')), 'unknown');
  assert.equal(refusalCode(null), 'unknown');
  assert.equal(refusalCode({}), 'unknown');
  // The status is the fallback only when the sentence says nothing.
  assert.equal(refusalCode({ status: 403, body: '' }), 'forbidden');
  assert.equal(refusalCode({ status: 404, body: '' }), 'notFound');
});

test('each code has a caption, and every caption exists in both languages', () => {
  const page = read(PAGE);
  const keys = [...Object.values(REFUSAL_KEYS),
    'slotFull', 'seatLast', 'seatsLeft', 'noSlotsHint'];
  for (const key of keys) {
    const hits = (page.match(new RegExp(`(^|[\\s{,])${key}:'`, 'g')) || []).length;
    assert.equal(hits, 2, `${key} must be defined in Bangla and in English`);
  }
  // One code, one caption: the count is the guard against a new refusal code
  // shipping without words.  Q1 added four outside-hours codes
  // (`needsOverride`, `overrideLimit`, `overrideDisabled`, `useWalkIn`).
  assert.equal(Object.keys(REFUSAL_KEYS).length, 17, 'no code is left captionless');
});

test('the booking dialog translates refusals instead of pasting the server sentence', () => {
  const page = read(PAGE);
  assert.doesNotMatch(page, /setBookError\(T\('bookErr'\) \+ ':' \+ String/,
    'the raw server sentence must not reach a Bangla screen');
  assert.doesNotMatch(page, /setError\(T\('actionErr'\) \+ ':' \+ String/);
  assert.equal((page.match(/refusalText\(e\)/g) || []).length, 4,
    'both booking paths and both status paths use the shared vocabulary');
  assert.match(page, /function refusalText\(err\)/);
  assert.match(page, /REFUSAL_KEYS\[refusalCode\(err\)\]/);
});

test('the slot button writes remaining seats as words, and explains a full one', () => {
  const page = read(PAGE);
  assert.match(page, /const word = seatsWord\(s\);/);
  assert.match(page, /fill\(T\(word\.key\), \{ n: word\.n \}\)/);
  assert.match(page, /title=\{T\('capacity'\) \+ ': ' \+ s\.capacity \+ ' · ' \+ seats\}/,
    'the tooltip says why the button is disabled, not only a number');
});

test('an empty day explains the fallback it offers (F-18)', () => {
  const page = read(PAGE);
  assert.match(page, /\{T\('noSlots'\)\}/);
  assert.match(page, /\{T\('noSlotsHint'\)\}/,
    'the free-text field must state that the booking falls outside every session');
  // The field itself is kept: a time outside every session still places the
  // card on the day.  Q1 closed the ambiguity — with nothing published the
  // booking is an outside-hours acceptance, so the dialog asks for the reason
  // the server requires and sends `appointment_type: 'unscheduled'`.
  assert.match(page, /<input type='time' value=\{book\.time\} aria-label=\{T\('tm'\)\}/);
  assert.match(page, /id='book-override-reason'/);
  assert.match(page, /\{T\('overrideHint'\)\}/);
});

test('the module stays pure, so the browser and these tests run the same code', () => {
  const source = stripComments(read(MODULE));
  assert.doesNotMatch(source, /^\s*import\s/m, 'no imports: no React, no fetch, no i18n');
  assert.doesNotMatch(source, /require\(/);
  assert.doesNotMatch(source, /\bwindow\.|\bdocument\./);
});
