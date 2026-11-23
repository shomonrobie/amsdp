/* QUE-006 — approved announcement content (product owner decision OD-3).
 *
 * This module is the *only* place announcement wording is assembled, so the
 * spoken surface can be reviewed in one file. It is deliberately pure: no DOM,
 * no timers, no React — the tests in `tests/queue-announcement-content.test.mjs`
 * pin the exact Bangla and English strings.
 *
 * Privacy contract (QUE-006 acceptance criterion 9, ANN-007):
 *   - the spoken payload is built from two fields only — the token serial and
 *     an optional room number;
 *   - the doctor's name and honourific are never spoken: they are removed from
 *     every template so no doctor identity can leak into the announcement;
 *   - patient identity is never read, so it cannot leak into the template;
 *   - the raw token is never spoken, because today's token is
 *     `T-<doctor-id fragment>-<serial>` and the fragment is an internal
 *     identifier. Only the trailing serial is spoken, as a plain number.
 *
 * Approved wording (OD-3, doctor name removed):
 *   bn (with room)  টোকেন নম্বর [সংখ্যা], কক্ষ [কক্ষ নম্বর]-ে আসুন।
 *   bn (no room)    টোকেন নম্বর [সংখ্যা], অনুগ্রহ করে সামনে আসুন।
 *   en (with room)  Token number [number], please proceed to Room [number].
 *   en (no room)    Token number [number], please come to the front.
 *
 * Room wording — D-4, product owner decision 2026-11-22.
 *
 * A room is announced whenever one is *configured* for the queue entry: both
 * announcement paths hand over `entry.room_name`, the appointment's booking-time
 * room snapshot (`backend/queuing/main.py::_entry_to_dict`, F4 option R1), and
 * the approved `withRoom` sentence names it. When the entry carries no room —
 * the ordinary case, because a room is optional on an appointment — the
 * approved `noRoom` sentence is spoken instead of inventing one. There is no
 * facility-level room switch to consult: the announcement configuration stores
 * the language and the voice packs only
 * (`backend/organization/announcement_config.py`), so the payload is the single
 * input and these two sentences are the only possible outcomes.
 * `fields.template` (`'with_room'` / `'no_room'`) and `fields.derived` report
 * which one was used, so a caller never has to parse the sentence to find out.
 */

/** Languages a queue announcement may be spoken in (OD-3). */
export const ANNOUNCEMENT_LANGUAGES = Object.freeze(['bn', 'en']);

/** Approved templates. `{number}` and `{room}` are the only slots. */
export const TEMPLATES = Object.freeze({
  bn: Object.freeze({
    withRoom: 'টোকেন নম্বর {number}, কক্ষ {room}-এ আসুন।',
    noRoom: 'টোকেন নম্বর {number}, অনুগ্রহ করে সামনে আসুন।',
  }),
  en: Object.freeze({
    withRoom: 'Token number {number}, please proceed to Room {room}.',
    noRoom: 'Token number {number}, please come to the front.',
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
 * Only `token` and `room` are read from `input`; every other key — including
 * `doctorName`, `patientName`, `patient_id`, `mobile`, `notes` — is ignored,
 * which is what keeps patient identity and doctor identity out of the spoken
 * payload. A doctor name is never required and never spoken.
 *
 * @param {{token?: unknown, room?: unknown}} input
 * @param {string} language `'bn'` or `'en'` (OD-3; no silent fallback)
 * @returns {{ok: true, language: string, text: string, fields: object}
 *          | {ok: false, reason: string}}
 */
export function buildAnnouncement(input, language) {
  const lang = ANNOUNCEMENT_LANGUAGES.includes(language) ? language : null;
  if (!lang) return { ok: false, reason: 'unsupported_language' };

  const source = input && typeof input === 'object' ? input : {};

  const number = spokenTokenNumber(source.token);
  if (!number) return { ok: false, reason: 'unspeakable_token' };

  const room = cleanText(source.room);
  const spokenNumber = lang === 'bn' ? toBanglaDigits(number) : number;
  // The room is spoken in the language's own digits: the approved Bangla
  // sentence is `কক্ষ ৩০৫-এ আসুন।`, and the queue payload carries the room name
  // as ASCII (`room_name: '305'`). `fields.room` keeps the payload's own value,
  // so segment resolution (`segments.js`) and every caller are unaffected.
  const spokenRoom = lang === 'bn' ? toBanglaDigits(room) : room;
  const template = room ? TEMPLATES[lang].withRoom : TEMPLATES[lang].noRoom;

  const text = template
    .replace('{number}', spokenNumber)
    .replace('{room}', spokenRoom);

  return {
    ok: true,
    language: lang,
    text,
    fields: {
      tokenNumber: spokenNumber,
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
