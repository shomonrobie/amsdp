/* AMSDP facility + chamber model — pure helpers for the doctor and facility
 * screens (AMSDP-FACILITY-DOCTOR-01).
 *
 * The facility tree (floor → department → room) and the clinic session
 * (weekday + window + chamber) are server-owned; this module only shapes what
 * the API returns so the pages stay thin and the rules are unit-testable:
 *
 *  * a chamber reads as "৩য় তলা · কার্ডিওলজি · রুম ৩০২", skipping the parts a
 *    room does not have, so a room with no floor still names itself;
 *  * weekday numbering is 0 = Monday, exactly as `Schedule.slot_templates` and
 *    `schedule_sessions.day_of_week` store it;
 *  * `windowConflicts` mirrors the service's 409 rules (same doctor overlapping,
 *    same chamber overlapping, active rows only) so the form can warn *before*
 *    the request, while the server remains the authority that decides.
 */

/** Weekdays in the storage convention: 0 = Monday (never JavaScript's 0 = Sunday). */
export const WEEKDAYS = [
  { value: 0, en: 'Monday', enShort: 'Mon', bn: 'সোমবার', bnShort: 'সোম' },
  { value: 1, en: 'Tuesday', enShort: 'Tue', bn: 'মঙ্গলবার', bnShort: 'মঙ্গল' },
  { value: 2, en: 'Wednesday', enShort: 'Wed', bn: 'বুধবার', bnShort: 'বুধ' },
  { value: 3, en: 'Thursday', enShort: 'Thu', bn: 'বৃহস্পতিবার', bnShort: 'বৃহঃ' },
  { value: 4, en: 'Friday', enShort: 'Fri', bn: 'শুক্রবার', bnShort: 'শুক্র' },
  { value: 5, en: 'Saturday', enShort: 'Sat', bn: 'শনিবার', bnShort: 'শনি' },
  { value: 6, en: 'Sunday', enShort: 'Sun', bn: 'রবিবার', bnShort: 'রবি' },
];

/** BMDC verification states, in the order the backend accepts them. */
export const BMDC_STATUSES = ['unverified', 'pending_verification', 'verified', 'rejected'];

/** Permitted verification transitions — mirror of `profile.BMDC_TRANSITIONS`. */
export const BMDC_TRANSITIONS = {
  unverified: ['pending_verification', 'verified', 'rejected'],
  pending_verification: ['verified', 'rejected'],
  verified: ['rejected'],
  rejected: ['pending_verification', 'verified'],
};

/** Room types accepted by `facility.ROOM_TYPES`. */
export const ROOM_TYPES = ['consultation', 'procedure', 'ward', 'diagnostic', 'other'];

function localeOf(locale) {
  return locale === 'en' ? 'en' : 'bn';
}

/** "সোমবার" / "Monday", or the short form. Unknown days render as ''. */
export function dayName(day, locale = 'bn', short = false) {
  const row = WEEKDAYS.find((d) => d.value === Number(day));
  if (!row) return '';
  const l = localeOf(locale);
  return l === 'en' ? (short ? row.enShort : row.en) : (short ? row.bnShort : row.bn);
}

/** Minutes since midnight for `HH:MM`, or `null` when the value is not HH:MM. */
export function minutesOf(hhmm) {
  if (typeof hhmm !== 'string') return null;
  const m = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(hhmm.trim());
  if (!m) return null;
  return Number(m[1]) * 60 + Number(m[2]);
}

/** True when `value` is a 24-hour `HH:MM` string. */
export function isHhmm(value) {
  return minutesOf(value) !== null;
}

/** "09:00–12:00" — the window as the session list prints it. */
export function windowText(start, end) {
  if (!start || !end) return '';
  return `${start}–${end}`;
}

/** Half-open overlap: touching windows (09:00–10:00, 10:00–11:00) do not clash. */
export function overlaps(aStart, aEnd, bStart, bEnd) {
  const as = minutesOf(aStart);
  const ae = minutesOf(aEnd);
  const bs = minutesOf(bStart);
  const be = minutesOf(bEnd);
  if (as === null || ae === null || bs === null || be === null) return false;
  return as < be && bs < ae;
}

/**
 * Conflicts the service would answer with 409, computed ahead of the request.
 *
 * `candidate` is `{ id?, doctor_id?, room_id?, day_of_week, start_time,
 * end_time }`; `sessions` are session payloads from
 * `GET /api/v1/doctors/{id}/sessions` and/or
 * `GET /api/v1/branches/{id}/sessions`.  Retired rows never conflict, and a
 * candidate never conflicts with itself.
 *
 * Returns `{ doctor: [...], chamber: [...] }` — the caller decides which
 * message to show; the server still owns the decision.
 */
export function windowConflicts(candidate, sessions) {
  const result = { doctor: [], chamber: [] };
  if (!candidate) return result;
  const day = Number(candidate.day_of_week);
  const start = minutesOf(candidate.start_time);
  const end = minutesOf(candidate.end_time);
  if (!Number.isInteger(day) || start === null || end === null || end <= start) {
    return result;
  }
  (sessions || []).forEach((s) => {
    if (!s) return;
    if ((s.status || 'active') !== 'active') return;
    if (candidate.id && s.id === candidate.id) return;
    if (Number(s.day_of_week) !== day) return;
    if (!overlaps(candidate.start_time, candidate.end_time, s.start_time, s.end_time)) return;
    if (candidate.doctor_id && s.doctor_id === candidate.doctor_id) result.doctor.push(s);
    if (candidate.room_id && s.room_id === candidate.room_id) result.chamber.push(s);
  });
  return result;
}

/** "৩য় তলা · কার্ডিওলজি · রুম ৩০২" for any payload carrying chamber names. */
export function chamberText(row) {
  if (!row) return '';
  const parts = [row.floor_name, row.department_name, row.room_name]
    .map((p) => (p || '').trim())
    .filter(Boolean);
  return parts.join(' · ');
}

/** The chamber of a room record ("২য় তলা · মেডিসিন · রুম ২০১").
 *
 * A room record names itself `name`, while a session payload names it
 * `room_name`; mapping here keeps `chamberText` single-purpose and means the
 * picker label cannot silently lose the room number.
 */
export function roomChamberText(room) {
  if (!room) return '';
  return chamberText({
    floor_name: room.floor_name,
    department_name: room.department_name,
    room_name: room.name || room.room_name || '',
  });
}

/** Active rows only — the default view of every facility list. */
export function activeOnly(rows) {
  return (rows || []).filter((r) => (r.status || 'active') === 'active');
}

/**
 * Rooms grouped under their floor for the facility tree.
 *
 * Floors sort by `level` (then name); rooms with no floor come last under
 * `floor: null`, because "unassigned" is a state the operator must see rather
 * than a room that silently disappears.
 */
export function groupRoomsByFloor(rooms, floors) {
  const activeFloors = (floors || []).slice().sort((a, b) => {
    const la = a.level === null || a.level === undefined ? 999 : Number(a.level);
    const lb = b.level === null || b.level === undefined ? 999 : Number(b.level);
    if (la !== lb) return la - lb;
    return String(a.name || '').localeCompare(String(b.name || ''));
  });
  const groups = activeFloors.map((floor) => ({
    floor,
    rooms: (rooms || []).filter((r) => r.floor_id === floor.id),
  }));
  const orphans = (rooms || []).filter(
    (r) => !r.floor_id || !activeFloors.some((f) => f.id === r.floor_id));
  if (orphans.length) groups.push({ floor: null, rooms: orphans });
  return groups;
}

/** Rooms grouped by department (a room may sit on a floor *and* in a department). */
export function groupRoomsByDepartment(rooms, departments) {
  const groups = (departments || []).map((dept) => ({
    department: dept,
    rooms: (rooms || []).filter((r) => r.department_id === dept.id),
  }));
  const orphans = (rooms || []).filter(
    (r) => !r.department_id || !(departments || []).some((d) => d.id === r.department_id));
  if (orphans.length) groups.push({ department: null, rooms: orphans });
  return groups;
}

/**
 * `{ value, label }` options for a chamber picker — the label is the full
 * chamber so two rooms named "রুম ১" on different floors stay distinguishable.
 */
export function roomOptions(rooms) {
  return activeOnly(rooms)
    .slice()
    .sort((a, b) => roomChamberText(a).localeCompare(roomChamberText(b)))
    .map((r) => ({ value: r.id, label: roomChamberText(r) || r.name }));
}

/** How many active sessions occupy each room — the facility screen's usage column. */
export function roomUsage(sessions) {
  const counts = {};
  (sessions || []).forEach((s) => {
    if (!s || !s.room_id) return;
    if ((s.status || 'active') !== 'active') return;
    counts[s.room_id] = (counts[s.room_id] || 0) + 1;
  });
  return counts;
}

/** Totals for the facility header ("৩ তলা · ২ বিভাগ · ৮ কক্ষ"). */
export function facilityCounts(tree) {
  return {
    floors: ((tree && tree.floors) || []).length,
    departments: ((tree && tree.departments) || []).length,
    rooms: ((tree && tree.rooms) || []).length,
  };
}

const HONORIFICS = ['ডা.', 'ডাঃ', 'ডাক্তার', 'dr.', 'dr', 'doctor'];

/** Two-character avatar text for a doctor with no photograph ("ডা. রহিম উদ্দিন" → "রউ"). */
export function initials(name) {
  const parts = String(name || '').trim().split(/\s+/)
    .filter((p) => p && !HONORIFICS.includes(p.toLowerCase()));
  if (!parts.length) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2);
  return parts[0].charAt(0) + parts[1].charAt(0);
}

/** "ধানমন্ডি শাখা — ২য় তলা · রুম ২০১", or the branch plus the caller's "no chamber" label. */
export function assignmentText(assignment, roomsById, unassignedLabel) {
  if (!assignment) return '';
  const branch = assignment.branch_name || '';
  const room = roomsById && assignment.room_id ? roomsById[assignment.room_id] : null;
  const chamber = room ? roomChamberText(room) : (assignment.room_name || '');
  const place = chamber || unassignedLabel || '';
  return branch && place ? `${branch} — ${place}` : (branch || place);
}

/** Localised label for a BMDC verification state. */
export function bmdcLabel(status, locale = 'bn') {
  const l = localeOf(locale);
  const table = {
    unverified: { bn: 'যাচাই হয়নি', en: 'Unverified' },
    pending_verification: { bn: 'যাচাই চলছে', en: 'Pending verification' },
    verified: { bn: 'যাচাইকৃত', en: 'Verified' },
    rejected: { bn: 'যাচাই প্রত্যাখ্যাত', en: 'Rejected' },
  };
  const row = table[status] || table.unverified;
  return row[l];
}

/** Badge class for a verification state — verified green, rejected red, in-flight amber. */
export function bmdcBadgeClass(status) {
  if (status === 'verified') return 'badge badge-active';
  if (status === 'rejected') return 'badge badge-inactive';
  if (status === 'pending_verification') return 'badge badge-warn';
  return 'badge';
}

/** The states a doctor may move to from `status`, current state first. */
export function bmdcTransitions(status) {
  const current = BMDC_STATUSES.includes(status) ? status : 'unverified';
  return [current, ...(BMDC_TRANSITIONS[current] || [])];
}

/** A speciality's display name in the active locale, falling back to the other. */
export function specialityName(specialty, locale = 'bn') {
  if (!specialty) return '';
  const bn = (specialty.name_bn || '').trim();
  const en = (specialty.name_en || '').trim();
  return localeOf(locale) === 'en' ? (en || bn) : (bn || en);
}
