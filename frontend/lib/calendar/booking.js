/* AMSDP appointment calendar — the booking dialog's two explanations (F-18/F-19).
 *
 * The gap analysis records two moments where the booking dialog did not explain
 * itself:
 *
 *   F-19  a full slot showed only `booked/capacity` arithmetic, and a refused
 *         booking appended the server's untranslated English sentence after a
 *         translated prefix (`T('bookErr') + ': ' + String(e.message || e)`);
 *   F-18  a day with no published session offered an unrestricted time field as
 *         if it were equivalent to a listed slot, without saying what the
 *         booking would then be.
 *
 * This module owns the *decision* for both — which refusal the server sent, and
 * how a slot's remaining capacity is worded — so the page keeps only the DOM and
 * the words.  Pure: no React, no DOM, no fetch.  The split is the one `grid.js`,
 * `list.js` and `matches.js` already use, and
 * `tests/appointment-booking-feedback.test.mjs` exercises exactly the code the
 * browser runs.
 *
 * The refusal vocabulary is keyed on the `detail` sentences
 * `backend/appointment/main.py` raises (`slot_full: …`, `no_slot_covers_time: …`)
 * plus the HTTP status, never on a stack trace or an internal code path: the
 * browser is told *what to do next*, not where the check lives.
 */

/** At or below this many free seats the slot states its remaining room in words. */
export const SEATS_WORD_MAX = 3;

const toInt = (value, fallback) => {
  const n = Number(value);
  return Number.isFinite(n) ? Math.trunc(n) : fallback;
};

/** Seats still free in a slot, floored at 0. `slot_free` can never read negative. */
export function freeSeats(slot) {
  const capacity = Math.max(toInt(slot && slot.capacity, 1), 1);
  const booked = Math.max(toInt(slot && slot.booked, 0), 0);
  return Math.max(capacity - booked, 0);
}

/**
 * How a slot's remaining capacity should be worded.
 *
 * Returns `{key, n}` — an i18n key from the page's bilingual table plus the
 * number to substitute — or `null` when the arithmetic alone says enough (a
 * slot with plenty of room does not need a sentence).  A full slot and an
 * almost-full slot are therefore distinguishable by words, not only by opacity.
 */
export function seatsWord(slot) {
  const free = freeSeats(slot);
  if (free === 0) return { key: 'slotFull', n: 0 };
  if (free === 1) return { key: 'seatLast', n: 1 };
  if (free <= SEATS_WORD_MAX) return { key: 'seatsLeft', n: free };
  return null;
}

/**
 * Marker → refusal code, most specific first.
 *
 * The markers are the literal starts of the sentences the appointment service
 * raises, so a change on the server shows up here as `unknown` rather than as a
 * confidently wrong translation.
 */
const REFUSAL_MARKERS = Object.freeze([
  ['slot_full', 'slotFull'],
  ['no_slot_covers_time', 'noSlot'],
  ['no clinic session covers', 'outsideSession'],
  ['invalid date', 'badDate'],
  ['cannot reschedule', 'badTransition'],
  ['cannot transition', 'badTransition'],
  ['cannot transfer', 'badTransition'],
  ['patient not found', 'patientMissing'],
  ['doctor not found', 'doctorMissing'],
  ['branch not found', 'branchMissing'],
  ['appointment not found', 'notFound'],
  ['reason is required', 'needReason'],
  ['reason required', 'needReason'],
]);

/**
 * Refusal code → the page's caption key.
 *
 * Every code has a sentence with a next step, because a refusal the receptionist
 * cannot act on is the defect F-19 records.  `unknown` is honest rather than
 * invented: if the server says something this module does not recognise, the
 * dialog says so and offers a retry instead of pasting English into a Bangla
 * screen.
 */
export const REFUSAL_KEYS = Object.freeze({
  slotFull: 'errSlotFull',
  noSlot: 'errNoSlot',
  outsideSession: 'errOutsideSession',
  badDate: 'errBadDate',
  badTime: 'errBadTime',
  badTransition: 'errBadTransition',
  patientMissing: 'errPatient',
  doctorMissing: 'errDoctor',
  branchMissing: 'errBranch',
  notFound: 'errNotFound',
  needReason: 'errNeedReason',
  forbidden: 'errForbidden',
  unknown: 'errUnknown',
});

/** The `detail` the API answered with, when it is a sentence rather than a list. */
function detailText(err) {
  if (!err) return '';
  const body = err.body !== undefined && err.body !== null ? err.body : err.detail;
  if (typeof body === 'string') return body;
  // FastAPI validation errors arrive as a list of per-field objects.
  if (Array.isArray(body)) {
    return body.map((item) => {
      if (!item || typeof item !== 'object') return '';
      const loc = Array.isArray(item.loc) ? item.loc.join('.') : '';
      return `${loc} ${item.msg || ''}`.trim();
    }).join(' ');
  }
  if (typeof err.message === 'string') return err.message;
  return '';
}

/**
 * Which refusal the server sent, as a code from `REFUSAL_KEYS`.
 *
 * Sentence first, status second: a `404` for a foreign doctor and a `404` for a
 * dangling id both mean "not found", and the sentence is what distinguishes
 * them.  `403` is kept as its own code because the fix is different (ask an
 * administrator, not "search again").
 */
export function refusalCode(err) {
  const text = detailText(err);
  const lowered = text.toLowerCase();
  if (lowered) {
    if (/start_time|new_start_time|invalid time/.test(lowered)) return 'badTime';
    for (const [marker, code] of REFUSAL_MARKERS) {
      if (lowered.includes(marker)) return code;
    }
  }
  const status = toInt(err && err.status, 0);
  if (status === 403) return 'forbidden';
  if (status === 404) return 'notFound';
  return 'unknown';
}
