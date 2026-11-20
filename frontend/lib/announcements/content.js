/* QUE-006 — approved announcement content (product owner decision OD-3).
 *
 * This module is the *only* place announcement wording is assembled, so the
 * spoken surface can be reviewed in one file. It is deliberately pure: no DOM,
 * no timers, no React — the tests in `tests/queue-announcement-content.test.mjs`
 * pin the exact Bangla and English strings.
 *
 * Privacy contract (QUE-006 acceptance criterion 9, ANN-007):
 *   - the spoken payload is built from three fields only — the token serial,
 *     the doctor's name and an optional room number;
 *   - patient identity is never read, so it cannot leak into the template;
 *   - the raw token is never spoken, because today's token is
 *     `T-<doctor-id fragment>-<serial>` and the fragment is an internal
 *     identifier. Only the trailing serial is spoken, as a plain number.
 *
 * Approved wording (OD-3):
 *   bn  টোকেন নম্বর [সংখ্যা], ডা. [ডাক্তারের নাম], কক্ষ [কক্ষ নম্বর]-এ আসুন।
 *   en  Token number [number], Dr. [doctor name], Room [room].
 *
 * Room-less variants (documented dependency, see the implementation report):
 * no queue payload or queue endpoint carries a room today, so the room clause
 * is dropped rather than invented. Both variants are marked `derived` in the
 * returned `fields` so a caller can tell which one was used.
 */

/** Languages a queue announcement may be spoken in (OD-3). */
export const ANNOUNCEMENT_LANGUAGES = Object.freeze(['bn', 'en']);

/** Approved templates. `{number}`, `{doctor}` and `{room}` are the only slots. */
export const TEMPLATES = Object.freeze({
  bn: Object.freeze({
    withRoom: 'টোকেন নম্বর {number}, ডা. {doctor}, কক্ষ {room}-এ আসুন।',
    noRoom: 'টোকেন নম্বর {number}, ডা. {doctor}, আসুন।',
  }),
  en: Object.freeze({
    withRoom: 'Token number {number}, Dr. {doctor}, Room {room}.',
    noRoom: 'Token number {number}, Dr. {doctor}.',
  }),
});

/** Fields that must never influence the spoken text. Declared so it is explicit. */
export const PATIENT_FIELDS = Object.freeze([
  'patientName', 'patient_name', 'patient', 'patientId', 'patient_id',
  'mobile', 'phone', 'mobile_number', 'appointment_id', 'notes',
]);

const BN_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];
const BN_DIGIT_RE = /[\u09E6-\u09EF]/g;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const HEX32_RE = /^[0-9a-f]{32}$/i;
/** A serial longer than this is not a queue serial — refuse rather than speak it. */
const MAX_SERIAL_DIGITS = 9;

/** ASCII digits → Bangla digits, so a Bangla voice reads `৪` not "four". */
export function toBanglaDigits(value) {
  return String(value == null ? '' : value).replace(/[0-9]/g, (d) => BN_DIGITS[Number(d)]);
}

/** Bangla digits → ASCII digits (tokens are issued in ASCII, but be tolerant). */
function toAsciiDigits(value) {
  return String(value).replace(BN_DIGIT_RE, (d) => String(d.charCodeAt(0) - 0x09e6));
}

/** Collapse whitespace and drop control characters from free text. */
function cleanText(value) {
  return String(value == null ? '' : value)
    .replace(/[\u0000-\u001f\u007f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * The number an announcement may speak for a queue token.
 *
 * `T-3F2A9C-001` → `'1'`   (the trailing serial, without leading zeros)
 * `004`         → `'4'`
 * a UUID        → `null`   (an internal identifier is never spoken)
 *
 * @param {unknown} token
 * @returns {string|null}
 */
export function spokenTokenNumber(token) {
  const raw = cleanText(token);
  if (!raw) return null;
  if (UUID_RE.test(raw) || HEX32_RE.test(raw)) return null;
  const groups = toAsciiDigits(raw).match(/[0-9]+/g);
  if (!groups || !groups.length) return null;
  const serial = groups[groups.length - 1];
  if (serial.length > MAX_SERIAL_DIGITS) return null;
  const asNumber = Number(serial);
  if (!Number.isFinite(asNumber)) return null;
  return String(asNumber);
}

/**
 * Build the spoken text for one queue announcement.
 *
 * Only `token`, `doctorName` and `room` are read from `input`; every other key
 * is ignored, which is what keeps patient identity out of the spoken payload.
 *
 * @param {{token?: unknown, doctorName?: unknown, room?: unknown}} input
 * @param {string} language `'bn'` or `'en'` (OD-3; no silent fallback)
 * @returns {{ok: true, language: string, text: string, fields: object}
 *          | {ok: false, reason: string}}
 */
export function buildAnnouncement(input, language) {
  const lang = ANNOUNCEMENT_LANGUAGES.includes(language) ? language : null;
  if (!lang) return { ok: false, reason: 'unsupported_language' };

  const source = input && typeof input === 'object' ? input : {};
  const doctorName = cleanText(source.doctorName);
  if (!doctorName) return { ok: false, reason: 'missing_doctor_name' };

  const number = spokenTokenNumber(source.token);
  if (!number) return { ok: false, reason: 'unspeakable_token' };

  const room = cleanText(source.room);
  const spokenNumber = lang === 'bn' ? toBanglaDigits(number) : number;
  const template = room ? TEMPLATES[lang].withRoom : TEMPLATES[lang].noRoom;

  const text = template
    .replace('{number}', spokenNumber)
    .replace('{doctor}', doctorName)
    .replace('{room}', room);

  return {
    ok: true,
    language: lang,
    text,
    fields: {
      tokenNumber: spokenNumber,
      doctorName,
      room: room || null,
      hasRoom: !!room,
      template: room ? 'with_room' : 'no_room',
      /** `true` when the approved template had to lose its room clause. */
      derived: !room,
    },
  };
}

/**
 * Stable identity for one announcement event, used for duplicate suppression.
 *
 * An explicit event id wins; otherwise the queue entry, action and revision
 * form the key. A missing entry id yields `null` (no suppression possible).
 *
 * @param {{eventId?: unknown, queueEntryId?: unknown, action?: unknown, revision?: unknown}} input
 * @returns {string|null}
 */
export function announcementEventKey(input = {}) {
  const source = input && typeof input === 'object' ? input : {};
  const eventId = cleanText(source.eventId);
  if (eventId) return 'event:' + eventId;

  const entryId = cleanText(source.queueEntryId);
  if (!entryId) return null;

  const action = cleanText(source.action) || 'announce';
  const revision = Number(source.revision);
  const safeRevision = Number.isFinite(revision) && revision >= 0 ? Math.trunc(revision) : 0;
  return 'entry:' + entryId + ':' + action + ':' + safeRevision;
}
