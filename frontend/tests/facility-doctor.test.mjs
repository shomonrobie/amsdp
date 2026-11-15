/* Facility, chamber and doctor-profile frontend contract.
 * AMSDP-FACILITY-DOCTOR-01.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 *
 * Three layers are covered, because each can break silently on its own:
 *
 *  1. `lib/phone.js` and `lib/facility.js` are pure modules — they are the exact
 *     code the browser runs, so they are tested directly.  The expectations come
 *     from the server: `backend/common/phone.py` for the number, and
 *     `backend/scheduling/sessions.py` (`assert_no_conflict`, half-open windows)
 *     for the chamber rules.
 *  2. `lib/i18n.js` must stay bilingual — one missing Bangla key silently
 *     renders an English word on a Bangla screen.
 *  3. The three redesigned pages must compile as JSX.  They are parsed with the
 *     SWC build that ships inside Next (a direct dependency), so a broken chunk
 *     fails here rather than in `next build`.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  normalizeMobile, isValidMobile, formatMobile, validateMobile, InvalidMobileNumber,
} from '../lib/phone.js';
import {
  WEEKDAYS, BMDC_TRANSITIONS, dayName, minutesOf, isHhmm, windowText, overlaps,
  windowConflicts, chamberText, activeOnly, groupRoomsByFloor, roomOptions,
  roomUsage, facilityCounts, initials, assignmentText, bmdcLabel, bmdcBadgeClass,
  bmdcTransitions, specialityName,
} from '../lib/facility.js';
import { DICT } from '../lib/i18n.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');

/* ------------------------------------------------------------------------- */
/* lib/phone.js — mirrors backend/common/phone.py                             */
/* ------------------------------------------------------------------------- */

test('mobile numbers normalise to the stored national form', () => {
  // Every shape the backend accepts must land on the same string, otherwise one
  // person can be registered twice under two spellings.
  const same = [
    '01711111111', '+8801711111111', '8801711111111', '017 1111 1111',
    '017-1111-1111', '1711111111', '  01711111111  ',
  ];
  same.forEach((value) => assert.equal(normalizeMobile(value), '01711111111', value));
});

test('the browser refuses exactly what the API refuses', () => {
  const bad = [
    '', '   ', null, undefined, '0171111111a', '01011111111', '01211111111',
    '017111111111', '+441711111111', '12345', '+8801711111',
  ];
  bad.forEach((value) => {
    assert.equal(isValidMobile(value), false, String(value));
    assert.throws(() => normalizeMobile(value), InvalidMobileNumber, String(value));
  });
  // 013–019 are the operator prefixes; 010/012 are PSTN and must not pass.
  ['013', '014', '015', '016', '017', '018', '019'].forEach((prefix) => {
    assert.equal(isValidMobile(prefix + '12345678'), true, prefix);
  });
  ['010', '012'].forEach((prefix) => {
    assert.equal(isValidMobile(prefix + '12345678'), false, prefix);
  });
});

test('display formats never corrupt a stored number', () => {
  assert.equal(formatMobile('01711111111'), '01711111111');
  assert.equal(formatMobile('01711111111', 'e164'), '+8801711111111');
  assert.equal(formatMobile('01711111111', 'spaced'), '017 1111 1111');
  // A legacy row that cannot be parsed must still render, unchanged.
  assert.equal(formatMobile('n/a'), 'n/a');
  assert.equal(formatMobile(null), '');
});

test('validateMobile reports the caller’s own message, never English', () => {
  const messages = { empty: 'EMPTY!', invalid: 'INVALID!' };
  assert.deepEqual(validateMobile('', messages), { ok: false, value: '', error: 'EMPTY!' });
  assert.deepEqual(validateMobile('0171111', messages), { ok: false, value: '', error: 'INVALID!' });
  assert.deepEqual(validateMobile('+8801711111111', messages),
    { ok: true, value: '01711111111', error: '' });
});

/* ------------------------------------------------------------------------- */
/* lib/facility.js — weekdays, windows and chambers                           */
/* ------------------------------------------------------------------------- */

test('weekdays use the storage convention, 0 = Monday', () => {
  // `Schedule.slot_templates` and `schedule_sessions.day_of_week` both store
  // Python's weekday(); JavaScript's 0 = Sunday would shift every session.
  assert.equal(WEEKDAYS[0].value, 0);
  assert.equal(dayName(0, 'en'), 'Monday');
  assert.equal(dayName(0, 'bn'), 'সোমবার');
  assert.equal(dayName(6, 'en'), 'Sunday');
  assert.equal(dayName(1, 'bn', true), 'মঙ্গল');
  assert.equal(dayName(9, 'en'), '');
});

test('windows parse as HH:MM and compare as half-open ranges', () => {
  assert.equal(minutesOf('09:00'), 540);
  assert.equal(minutesOf('09:30'), 570);
  assert.equal(minutesOf('9:00'), null);
  assert.equal(minutesOf('24:00'), null);
  assert.equal(isHhmm('21:30'), true);
  assert.equal(isHhmm('2130'), false);
  assert.equal(windowText('09:00', '13:00'), '09:00–13:00');

  // Touching windows do not conflict — the server compares start < end.
  assert.equal(overlaps('09:00', '10:00', '10:00', '11:00'), false);
  assert.equal(overlaps('09:00', '10:00', '09:30', '10:30'), true);
  assert.equal(overlaps('09:00', '13:00', '10:00', '11:00'), true);
  // An unparseable window never claims a conflict.
  assert.equal(overlaps('', '10:00', '09:00', '10:30'), false);
});

test('windowConflicts reproduces both 409s, and only for active rows', () => {
  const sessions = [
    { id: 's1', doctor_id: 'd1', room_id: 'r1', day_of_week: 0, start_time: '09:00', end_time: '12:00', status: 'active' },
    { id: 's2', doctor_id: 'd2', room_id: 'r2', day_of_week: 0, start_time: '09:00', end_time: '12:00', status: 'active' },
    { id: 's3', doctor_id: 'd2', room_id: 'r1', day_of_week: 1, start_time: '09:00', end_time: '12:00', status: 'active' },
    { id: 's4', doctor_id: 'd3', room_id: 'r1', day_of_week: 0, start_time: '09:00', end_time: '12:00', status: 'inactive' },
  ];
  const sameDoctor = windowConflicts(
    { doctor_id: 'd1', room_id: 'r2', day_of_week: 0, start_time: '10:00', end_time: '11:00' }, sessions);
  assert.deepEqual(sameDoctor.doctor.map((s) => s.id), ['s1']);
  assert.deepEqual(sameDoctor.chamber.map((s) => s.id), ['s2']);

  const sameChamber = windowConflicts(
    { doctor_id: 'd9', room_id: 'r1', day_of_week: 0, start_time: '11:30', end_time: '13:00' }, sessions);
  assert.deepEqual(sameChamber.doctor, []);
  assert.deepEqual(sameChamber.chamber.map((s) => s.id), ['s1'], 'retired s4 never conflicts');

  // A different weekday, a touching window and the row itself are all fine.
  assert.deepEqual(windowConflicts(
    { doctor_id: 'd1', room_id: 'r2', day_of_week: 2, start_time: '09:00', end_time: '10:00' }, sessions),
  { doctor: [], chamber: [] });
  assert.deepEqual(windowConflicts(
    { doctor_id: 'd1', room_id: 'r2', day_of_week: 0, start_time: '12:00', end_time: '13:00' }, sessions),
  { doctor: [], chamber: [] });
  assert.deepEqual(windowConflicts(
    { id: 's1', doctor_id: 'd1', room_id: 'r1', day_of_week: 0, start_time: '09:00', end_time: '12:00' }, sessions),
  { doctor: [], chamber: [] }, 'a session never conflicts with itself');
  // An inverted window is an invalid form, not a conflict — caught first.
  assert.deepEqual(windowConflicts(
    { doctor_id: 'd1', day_of_week: 0, start_time: '12:00', end_time: '09:00' }, sessions),
  { doctor: [], chamber: [] });
});

test('a chamber reads the way it is spoken, and skips what it does not have', () => {
  assert.equal(chamberText({ floor_name: '৩য় তলা', department_name: 'কার্ডিওলজি', room_name: 'রুম ৩০২' }),
    '৩য় তলা · কার্ডিওলজি · রুম ৩০২');
  assert.equal(chamberText({ floor_name: 'দ্বিতীয় তলা', room_name: 'রুম ২০১' }), 'দ্বিতীয় তলা · রুম ২০১');
  assert.equal(chamberText({ room_name: 'রুম ১' }), 'রুম ১');
  assert.equal(chamberText({}), '');
  assert.equal(chamberText(null), '');
});

test('rooms group under their floor, and unassigned rooms stay visible', () => {
  const floors = [
    { id: 'f2', name: '২য় তলা', level: 2 },
    { id: 'f1', name: '১ম তলা', level: 1 },
  ];
  const rooms = [
    { id: 'r1', name: 'রুম ২০১', floor_id: 'f2', floor_name: '২য় তলা' },
    { id: 'r2', name: 'রুম ১০১', floor_id: 'f1', floor_name: '১ম তলা' },
    { id: 'r3', name: 'রুম ৯', floor_id: null },
    { id: 'r4', name: 'রুম ৮', floor_id: 'gone' },
  ];
  const groups = groupRoomsByFloor(rooms, floors);
  assert.deepEqual(groups.map((g) => (g.floor ? g.floor.id : null)), ['f1', 'f2', null]);
  assert.deepEqual(groups[0].rooms.map((r) => r.id), ['r2']);
  assert.deepEqual(groups[2].rooms.map((r) => r.id), ['r3', 'r4'],
    'a room on a missing floor is shown under "unassigned", never dropped');
});

test('chamber options are labelled and filtered for a picker', () => {
  const options = roomOptions([
    { id: 'b', name: 'রুম ১', floor_name: '২য় তলা', status: 'active' },
    { id: 'a', name: 'রুম ১', floor_name: '১ম তলা', status: 'active' },
    { id: 'c', name: 'পুরোনো রুম', status: 'inactive' },
  ]);
  assert.equal(options.length, 2, 'a retired room is not offered');
  assert.deepEqual(options.map((o) => o.value), ['a', 'b']);
  assert.equal(options[0].label, '১ম তলা · রুম ১');
  assert.equal(options[1].label, '২য় তলা · রুম ১',
    'two rooms with the same name stay distinguishable by floor');
});

test('session usage counts active sessions only', () => {
  assert.deepEqual(roomUsage([
    { room_id: 'r1', status: 'active' },
    { room_id: 'r1', status: 'active' },
    { room_id: 'r1', status: 'inactive' },
    { room_id: 'r2', status: 'active' },
    { room_id: null, status: 'active' },
  ]), { r1: 2, r2: 1 });
  assert.deepEqual(roomUsage(null), {});
});

test('facility totals and active filtering', () => {
  assert.deepEqual(facilityCounts({ floors: [1, 2], departments: [1], rooms: [1, 2, 3] }),
    { floors: 2, departments: 1, rooms: 3 });
  assert.deepEqual(facilityCounts(null), { floors: 0, departments: 0, rooms: 0 });
  assert.deepEqual(activeOnly([{ status: 'active' }, { status: 'inactive' }, {}]).length, 2);
});

test('a doctor without a photograph still gets a readable avatar', () => {
  assert.equal(initials('ডা. রহিম উদ্দিন'), 'রউ', 'the honorific is not a name');
  assert.equal(initials('Dr. Karim Mia'), 'KM');
  assert.equal(initials('Rahima'), 'Ra');
  assert.equal(initials(''), '?');
  assert.equal(initials(null), '?');
});

test('the assignment line names the branch and the chamber, or says there is none', () => {
  const rooms = { r1: { id: 'r1', name: 'রুম ২০১', floor_name: '২য় তলা' } };
  assert.equal(
    assignmentText({ branch_name: 'ধানমন্ডি শাখা', room_id: 'r1' }, rooms, 'চেম্বার নেই'),
    'ধানমন্ডি শাখা — ২য় তলা · রুম ২০১');
  // The snapshot name survives a room that was renamed or is not loaded.
  assert.equal(
    assignmentText({ branch_name: 'ধানমন্ডি শাখা', room_id: 'gone', room_name: 'রুম ৩০১' }, rooms, 'চেম্বার নেই'),
    'ধানমন্ডি শাখা — রুম ৩০১');
  assert.equal(
    assignmentText({ branch_name: 'ধানমন্ডি শাখা', room_id: null }, rooms, 'চেম্বার নেই'),
    'ধানমন্ডি শাখা — চেম্বার নেই');
});

test('BMDC states and their permitted transitions mirror the server', () => {
  assert.equal(bmdcLabel('verified', 'bn'), 'যাচাইকৃত');
  assert.equal(bmdcLabel('verified', 'en'), 'Verified');
  assert.equal(bmdcLabel('pending_verification', 'en'), 'Pending verification');
  assert.equal(bmdcLabel('nonsense', 'en'), 'Unverified');
  assert.equal(bmdcBadgeClass('verified'), 'badge badge-active');
  assert.equal(bmdcBadgeClass('rejected'), 'badge badge-inactive');
  assert.equal(bmdcBadgeClass('pending_verification'), 'badge badge-warn');
  assert.equal(bmdcBadgeClass('unverified'), 'badge');

  // `verified` may only be revoked to `rejected` — never silently reset.
  assert.deepEqual(bmdcTransitions('verified'), ['verified', 'rejected']);
  assert.deepEqual(bmdcTransitions('unverified'),
    ['unverified', 'pending_verification', 'verified', 'rejected']);
  assert.deepEqual(bmdcTransitions(undefined),
    ['unverified', 'pending_verification', 'verified', 'rejected']);
  // Every target the UI offers is one the API accepts.
  Object.keys(BMDC_TRANSITIONS).forEach((from) => {
    bmdcTransitions(from).forEach((to) => {
      assert.ok(to === from || BMDC_TRANSITIONS[from].includes(to), `${from} -> ${to}`);
    });
  });
});

test('a speciality renders in the active locale, falling back to the other', () => {
  assert.equal(specialityName({ name_en: 'Cardiology', name_bn: 'কার্ডিওলজি' }, 'bn'), 'কার্ডিওলজি');
  assert.equal(specialityName({ name_en: 'Cardiology', name_bn: 'কার্ডিওলজি' }, 'en'), 'Cardiology');
  assert.equal(specialityName({ name_en: 'Cardiology', name_bn: '' }, 'bn'), 'Cardiology');
  assert.equal(specialityName(null, 'bn'), '');
});

/* ------------------------------------------------------------------------- */
/* lib/i18n.js — the screens must stay bilingual                              */
/* ------------------------------------------------------------------------- */

const PAGES = ['pages/doctors.js', 'pages/schedules.js', 'pages/facilities.js'];

test('every key exists in both languages, with a non-empty value', () => {
  const bn = Object.keys(DICT.bn).sort();
  const en = Object.keys(DICT.en).sort();
  assert.deepEqual(bn, en, 'bn and en dictionaries must carry the same keys');
  bn.forEach((key) => {
    assert.ok(String(DICT.bn[key]).trim().length > 0, `bn.${key} is empty`);
    assert.ok(String(DICT.en[key]).trim().length > 0, `en.${key} is empty`);
  });
});

test('every key the redesigned pages ask for is in the dictionary', () => {
  const used = new Set();
  PAGES.forEach((rel) => {
    const src = fs.readFileSync(path.join(FE, rel), 'utf8');
    for (const m of src.matchAll(/t\('([A-Za-z0-9_]+)'\)/g)) used.add(m[1]);
  });
  assert.ok(used.size > 50, 'the pages do ask for localised text');
  const missing = [...used].filter((key) => !(key in DICT.bn) || !(key in DICT.en));
  assert.deepEqual(missing, [], `missing dictionary keys: ${missing.join(', ')}`);
});

/* ------------------------------------------------------------------------- */
/* The redesigned pages must compile as JSX                                   */
/* ------------------------------------------------------------------------- */

let swc = null;
try {
  swc = (await import(FE + '/node_modules/next/dist/build/swc/index.js')).default;
} catch {
  swc = null;
}

test('doctors, schedules and facilities compile as JSX', async (t) => {
  if (!swc) return t.skip('next/dist/build/swc unavailable in this install');
  for (const rel of PAGES) {
    const source = fs.readFileSync(path.join(FE, rel), 'utf8');
    // No import rewriting here: this test only proves the file parses — a lost
    // brace in a JSX tree fails on the chunk that broke it.
    const out = await swc.transform(source, {
      filename: path.basename(rel),
      jsc: {
        parser: { syntax: 'ecmascript', jsx: true },
        transform: { react: { runtime: 'classic', development: false } },
      },
      module: { type: 'es6' },
    });
    assert.ok(out.code.length > 1000, `${rel} compiled to something substantial`);
  }
});

test('the pages read the shared model instead of re-deriving the rules', () => {
  const schedules = fs.readFileSync(path.join(FE, 'pages/schedules.js'), 'utf8');
  assert.match(schedules, /from '\.\.\/lib\/facility'/);
  assert.match(schedules, /windowConflicts/);
  assert.match(schedules, /roomOptions/);
  // The chamber picker must never send a room the API would price as retired.
  assert.match(schedules, /clear_chamber/);

  const doctors = fs.readFileSync(path.join(FE, 'pages/doctors.js'), 'utf8');
  assert.match(doctors, /from '\.\.\/lib\/phone'/);
  assert.match(doctors, /validateMobile/);
  assert.match(doctors, /\/branches\/' \+ a\.id/, 'a chamber is patched on the assignment');

  const facilities = fs.readFileSync(path.join(FE, 'pages/facilities.js'), 'utf8');
  assert.match(facilities, /groupRoomsByFloor/);
  assert.match(facilities, /roomUsage/);
  // Retiring must be a DELETE against the resource, never a local hide.
  assert.match(facilities, /method: 'DELETE'/);
  assert.match(facilities, /status: 'active'/, 'a retired record can be restored');
});

test('every API resource the pages call is proxied by next.config.js', () => {
  // A page can call a perfectly correct path and still 404, because the browser
  // talks to Next, not to the service: an unproxied path never leaves the
  // frontend. This is the defect class recorded as F-1 in the current-state
  // audit, so it is worth a test rather than a memory.
  const config = fs.readFileSync(path.join(FE, 'next.config.js'), 'utf8');
  const patterns = [...config.matchAll(/source: '([^']+)'/g)].map((m) => m[1]);
  assert.ok(patterns.length > 10, 'the rewrite table is present');

  const toRegExp = (pattern) => {
    const body = pattern.split('/').map((seg) => {
      if (seg.startsWith(':') && seg.endsWith('*')) return '.*';
      if (seg.startsWith(':')) return '[^/]+';
      return seg.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }).join('/');
    return new RegExp('^' + body + '$');
  };
  const compiled = patterns.map(toRegExp);

  const resources = new Set();
  PAGES.forEach((rel) => {
    const src = fs.readFileSync(path.join(FE, rel), 'utf8');
    for (const m of src.matchAll(/'(\/api\/v1\/([a-z0-9-]+))/g)) resources.add(m[2]);
  });
  assert.ok(resources.size >= 6, 'the pages do call several services');

  const unproxied = [...resources].filter((res) => {
    const probe = '/api/v1/' + res + '/PROBE-ID';
    return !compiled.some((re) => re.test(probe));
  });
  assert.deepEqual(unproxied, [], `unproxied resources: ${unproxied.join(', ')}`);
});
