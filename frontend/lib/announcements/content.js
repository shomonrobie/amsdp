/* QUE-006 — approved announcement content.
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
 * Approved wording — `AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_
 * Implementation_Plan_V1.0.md` §6.2/§6.3, quoted there as the sentence the
 * content tests must assert:
 *
 *   en  with room    Token number 4, Dr. Rahim Uddin, please proceed to Room 305.
 *   en  no room      Token number 4, Dr. Rahim Uddin, please proceed.
 *   bn  with room    টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।
 *   bn  no room      NOT APPROVED (§18 O-3) — refuse with `no_room` rather than
 *                    speak a sentence that reads as "…come".
 *
 * Two defects of the previous shipped wording are fixed here, not worked around
 * in the caller (§3.1 F1.4/F1.6):
 *
 *   1. the English sentence carries "please proceed to" (it used to jump
 *      straight from the doctor to "Room 305");
 *   2. the honorific is part of the *segment builder*, so a doctor name that
 *      already starts "Dr." is never spoken as "Dr. Dr.".
 */

/** Languages a queue announcement may be spoken in. */
export const ANNOUNCEMENT_LANGUAGES = Object.freeze(['bn', 'en']);

/** The honorific each language's doctor segment is prefixed with (§6.2/§6.3). */
export const DOCTOR_PREFIX = Object.freeze({ bn: 'ডা.', en: 'Dr.' });

/**
 * Approved templates. `{number}`, `{doctor}` and `{room}` are the only slots.
 *
 * `{doctor}` arrives already carrying its honorific exactly once (see
 * `doctorSegment`), which is why the template does not hard-code `Dr.`.
 *
 * `bn.noRoom` is `null` on purpose: the room-less Bangla sentence is an open
 * wording question (§18 O-3). A `null` template makes the refusal structural
 * instead of a comment somebody can forget.
 */
export const TEMPLATES = Object.freeze({
  bn: Object.freeze({
    withRoom: 'টোকেন নম্বর {number}, {doctor}, কক্ষ {room}-এ আসুন।',
    noRoom: null,
  }),
  en: Object.freeze({
    withRoom: 'Token number {number}, {doctor}, please proceed to Room {room}.',
    noRoom: 'Token number {number}, {doctor}, please proceed.',
  }),
});

/**
 * Why a sentence was refused or degraded, in the shared vocabulary of the
 * architecture plan §8.2. Returned verbatim by `buildAnnouncement().reason` and
 * by a plan's `reason`, so the panel never has to invent a phrase.
 */
export const SKIP_REASON = Object.freeze({
  UNSUPPORTED_LANGUAGE: 'unsupported_language',
  MISSING_DOCTOR_NAME: 'missing_doctor_name',
  UNSPEAKABLE_TOKEN: 'unspeakable_token',
  NO_ROOM: 'no_room',
  ROOM_NOT_ANNOUNCEABLE: 'room_not_announceable',
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

/** Honorifics a doctor name may already carry. Matched once, at the start. */
const HONORIFIC_RE = /^(?:dr\.?|doctor\.?|ডা\.?|ডাক্তার)(?=\s|$)/i;

/**
 * A room is announced as a number. Anything else ("Cabin A", "Room 305",
 * "৩০৫-এ") is not guessed at: it degrades to the room-less sentence and says
 * why (§6.4), because speaking a plausible-but-wrong room is worse than
 * speaking none.
 */
export const MAX_ROOM_DIGITS = 4;

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
 * The token serial as an integer — what the local-audio plan speaks as a clip
 * id. `null` means "not speakable", never `NaN` and never a guess.
 *
 * @param {unknown} token
 * @returns {number|null}
 */
export function tokenSerial(token) {
  const number = spokenTokenNumber(token);
  return number === null ? null : Number(number);
}

/**
 * Remove an honorific the name already carries so it is spoken exactly once.
 * `'Dr. Rahim Uddin'` and `'Rahim Uddin'` both yield `'Rahim Uddin'`.
 *
 * @param {unknown} value
 * @returns {string}
 */
export function doctorNameWithoutHonorific(value) {
  let name = cleanText(value);
  // Bounded, not `while(true)`: a pathological name ("Dr. Dr. Dr. …") must not
  // become an unbounded loop in an audio path.
  for (let pass = 0; pass < 3 && name; pass += 1) {
    const next = name.replace(HONORIFIC_RE, '').trim();
    if (next === name) break;
    name = next;
  }
  return name;
}

/**
 * The spoken doctor segment, honorific included exactly once, or `''` when the
 * name is absent after normalisation (which the caller treats as a refusal).
 *
 * @param {unknown} value
 * @param {'bn'|'en'} language
 * @returns {string}
 */
export function doctorSegment(value, language) {
  const lang = ANNOUNCEMENT_LANGUAGES.includes(language) ? language : null;
  if (!lang) return '';
  const name = doctorNameWithoutHonorific(value);
  if (!name) return '';
  return DOCTOR_PREFIX[lang] + ' ' + name;
}

/**
 * A room the announcer may speak, as ASCII digits, or `null`.
 *
 * @param {unknown} value
 * @returns {string|null}
 */
export function roomNumberForSpeech(value) {
  const raw = cleanText(value);
  if (!raw) return null;
  const digits = toAsciiDigits(raw).trim();
  if (!new RegExp('^[0-9]{1,' + MAX_ROOM_DIGITS + '}$').test(digits)) return null;
  return digits;
}

/**
 * Build the spoken text for one queue announcement.
 *
 * Only `token`, `doctorName` and `room` are read from `input`; every other key
 * is ignored, which is what keeps patient identity out of the spoken payload.
 *
 * @param {{token?: unknown, doctorName?: unknown, room?: unknown}} input
 * @param {string} language `'bn'` or `'en'` (no silent fallback)
 * @returns {{ok: true, language: string, text: string, fields: object}
 *          | {ok: false, reason: string, fields?: object}}
 */
export function buildAnnouncement(input, language) {
  const lang = ANNOUNCEMENT_LANGUAGES.includes(language) ? language : null;
  if (!lang) return { ok: false, reason: SKIP_REASON.UNSUPPORTED_LANGUAGE };

  const source = input && typeof input === 'object' ? input : {};
  const doctor = doctorSegment(source.doctorName, lang);
  if (!doctor) return { ok: false, reason: SKIP_REASON.MISSING_DOCTOR_NAME };

  const number = spokenTokenNumber(source.token);
  if (!number) return { ok: false, reason: SKIP_REASON.UNSPEAKABLE_TOKEN };

  const roomProvided = cleanText(source.room) || null;
  const room = roomNumberForSpeech(source.room);
  const template = room ? TEMPLATES[lang].withRoom : TEMPLATES[lang].noRoom;
  if (!template) {
    // Bangla without a room has no approved sentence (§18 O-3): refuse, never
    // speak the half-sentence that the old template produced.
    return {
      ok: false,
      reason: SKIP_REASON.NO_ROOM,
      fields: { roomProvided, hasRoom: false },
    };
  }

  const spokenNumber = lang === 'bn' ? toBanglaDigits(number) : number;
  const spokenRoom = lang === 'bn' && room ? toBanglaDigits(room) : room;

  const text = template
    .replace('{number}', spokenNumber)
    .replace('{doctor}', doctor)
    .replace('{room}', spokenRoom || '');

  return {
    ok: true,
    language: lang,
    text,
    fields: {
      tokenNumber: spokenNumber,
      tokenSerial: Number(number),
      doctorName: doctorNameWithoutHonorific(source.doctorName),
      doctor,
      room: spokenRoom || null,
      roomProvided,
      hasRoom: !!room,
      template: room ? 'with_room' : 'no_room',
      /** `true` when the approved template had to lose its room clause. */
      derived: !room,
      /** Why the room clause is absent; `''` on a complete sentence. */
      reason: room ? '' : (roomProvided
        ? SKIP_REASON.ROOM_NOT_ANNOUNCEABLE : SKIP_REASON.NO_ROOM),
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
