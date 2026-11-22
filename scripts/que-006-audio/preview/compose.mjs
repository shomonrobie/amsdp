/**
 * QUE-006 — composed-announcement clip order, shared by Node and the browser.
 *
 * `compose-wav.mjs` imports this module to build the fixed sample collection, and
 * `preview.js` imports this same file over HTTP while the preview server runs, so
 * the generated sample WAVs and the live preview cannot disagree about which
 * clips are played, in which order, at which junction.
 *
 * The module is deliberately free of Node, DOM and Web Audio APIs. It does one
 * thing: turn a (language, token digits, room digits) request into an ordered
 * clip list plus the pause that precedes each clip.
 *
 * It does **not** render wording. The expected text always comes from the
 * approved templates in `frontend/lib/announcements/content.js` — read as text by
 * `../lib/approved-templates.mjs` on the Node side and imported directly by the
 * browser page — so a template edit cannot be silently mirrored here, and a
 * preview cannot show text the product would not say.
 *
 * Composition follows `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md`
 * §3.3 ("Composition rules"):
 *
 *   - numbers are spoken digit by digit, one clip per digit;
 *   - there is no separator between digit clips — they are concatenated
 *     directly, which is also why the default junction pause is 0 ms;
 *   - a Bangla room number is followed immediately by the bound `-এ`, so
 *     `bn.phrase.room-locative` is butted against the last room digit with
 *     nothing inserted between them (a pause there would split a suffix from
 *     the word it belongs to).
 */

/** Languages the app may announce in (OD-3). */
export const LANGUAGES = Object.freeze(['en', 'bn']);

/**
 * Longest digit run this tool will compose.
 *
 * Mirrors `MAX_SERIAL_DIGITS = 9` in `frontend/lib/announcements/content.js`.
 * That limit exists in product code for the *token serial* only: room numbers
 * are free text there with no length check, and the catalogue records the 1–999
 * range as a *recommendation awaiting owner approval*, not a rule. This cap is
 * therefore a tool guard against pathological input, not a business rule, and it
 * is reported as an open item rather than presented as approved.
 */
export const MAX_DIGITS = 9;

/**
 * Junction pause used by the generated sample collection.
 *
 * 0 ms: the catalogue specifies direct concatenation, and the shipped clips
 * already carry their own trailing room tone (up to ~1.15 s in the Bangla set),
 * so adding silence on top would only lengthen the gaps rather than improve the
 * delivery. The preview page can raise it at playback time without touching any
 * file; the sample WAVs stay at this value.
 */
export const DEFAULT_PAUSE_MS = 0;

/** Pauses the preview page offers, in milliseconds. */
export const PAUSE_OPTIONS_MS = Object.freeze([0, 50, 100, 150, 200, 300]);

/**
 * Roles that are grammatically bound to the clip before them.
 *
 * A pause is never inserted before these: `-এ আসুন।` is a locative suffix,
 * `.` is a full stop, and `no-room` opens with its own leading ", " / space,
 * which already carries the pause recorded into the clip.
 */
export const SUFFIX_ROLES = Object.freeze(['room-locative', 'room-suffix', 'no-room']);

/** How each role is labelled in the preview and in the report. */
export const ROLE_LABELS = Object.freeze({
  'token-number': 'token-number phrase',
  digit: 'digit',
  'room-prefix': 'room prefix',
  'room-locative': 'locative suffix (bound)',
  'room-suffix': 'full stop (bound)',
  'no-room': 'no-room suffix (bound)',
});

/**
 * The clip that carries one digit, in one language.
 *
 * @param {'en'|'bn'} language
 * @param {number} digit 0–9
 * @returns {string}
 */
export function digitAssetId(language, digit) {
  return `${language}.digit.${digit}`;
}


/**
 * Read one digit character as 0–9.
 *
 * Accepts ASCII digits and the Bangla digits `০`–`৯`, because
 * `buildAnnouncement()` already returns a token number in Bangla digits for
 * `bn`. Anything else is `null` rather than a guess.
 *
 * @param {string} char
 * @returns {number|null}
 */
export function digitValue(char) {
  if (typeof char !== 'string' || char.length === 0) return null;
  const code = char.codePointAt(0);
  if (code >= 0x30 && code <= 0x39) return code - 0x30;      // '0'–'9'
  if (code >= 0x09e6 && code <= 0x09ef) return code - 0x09e6; // '০'–'৯'
  return null;
}

/**
 * Turn a digit string into `[0..9, ...]`, or explain why it cannot be spoken.
 *
 * @param {unknown} value
 * @param {string} field `'token'` or `'room'`, used in the problem code
 * @returns {{ok: true, digits: number[]} | {ok: false, problem: string, detail: string}}
 */
function readDigits(value, field) {
  const text = typeof value === 'number' ? String(value) : String(value == null ? '' : value).trim();
  if (!text) {
    return { ok: false, problem: `${field}_empty`, detail: `no ${field} number was supplied` };
  }
  const digits = [];
  for (const char of [...text]) {
    const digit = digitValue(char);
    if (digit === null) {
      return {
        ok: false,
        problem: `${field}_not_digits`,
        detail: `${field} "${text}" contains "${char}", which is not a digit; the catalogue speaks digits one at a time and must not invent a reading`,
      };
    }
    digits.push(digit);
  }
  if (digits.length > MAX_DIGITS) {
    return {
      ok: false,
      problem: `${field}_too_long`,
      detail: `${field} "${text}" has ${digits.length} digits; this tool composes at most ${MAX_DIGITS} (mirrors MAX_SERIAL_DIGITS)`,
    };
  }
  return { ok: true, digits };
}

/**
 * Build the ordered clip list for one announcement.
 *
 * @param {{language: 'en'|'bn', tokenDigits: string|number, roomDigits?: string|number|null}} request
 * @returns {{ok: true, language: 'en'|'bn', tokenDigits: number[], roomDigits: number[]|null,
 *   hasRoom: boolean, segments: Array<{assetId: string, role: string}>}
 *   | {ok: false, problem: string, detail: string}}
 */
export function planSegments(request) {
  const source = request && typeof request === 'object' ? request : {};
  const language = source.language;
  if (!LANGUAGES.includes(language)) {
    return {
      ok: false,
      problem: 'unsupported_language',
      detail: `language "${String(language)}" is not one of ${LANGUAGES.join(', ')}`,
    };
  }

  const token = readDigits(source.tokenDigits, 'token');
  if (!token.ok) return token;

  const roomText = source.roomDigits == null ? '' : String(source.roomDigits).trim();
  const room = roomText ? readDigits(roomText, 'room') : { ok: true, digits: null };
  if (!room.ok) return room;

  const hasRoom = Array.isArray(room.digits);

  /** @type {Array<{assetId: string, role: string}>} */
  const segments = [{ assetId: `${language}.phrase.token-number`, role: 'token-number' }];
  for (const digit of token.digits) segments.push({ assetId: digitAssetId(language, digit), role: 'digit' });

  if (hasRoom) {
    segments.push({
      assetId: `${language}.phrase.${language === 'bn' ? 'room-prefix' : 'proceed-to-room'}`,
      role: 'room-prefix',
    });
    for (const digit of room.digits) segments.push({ assetId: digitAssetId(language, digit), role: 'digit' });
    segments.push({
      assetId: `${language}.phrase.${language === 'bn' ? 'room-locative' : 'room-suffix'}`,
      role: language === 'bn' ? 'room-locative' : 'room-suffix',
    });
  } else {
    segments.push({ assetId: `${language}.phrase.no-room`, role: 'no-room' });
  }

  return {
    ok: true,
    language,
    tokenDigits: token.digits,
    roomDigits: hasRoom ? room.digits : null,
    hasRoom,
    segments,
  };
}

/**
 * Silence inserted *before* segment `index`.
 *
 * Zero for the first clip (nothing may precede the prefix) and zero before a
 * bound suffix. The caller supplies the junction pause; it is never baked into
 * the clips.
 *
 * @param {Array<{role: string}>} segments
 * @param {number} index
 * @param {number} pauseMs
 * @returns {number}
 */
export function pauseBefore(segments, index, pauseMs) {
  if (index <= 0) return 0;
  const role = segments[index] && segments[index].role;
  if (SUFFIX_ROLES.includes(role)) return 0;
  const value = Number(pauseMs);
  return Number.isFinite(value) && value > 0 ? Math.round(value) : 0;
}

/**
 * The digit clip ids a plan must contain, in order, for a given span.
 *
 * Used by the validator to prove that every digit is present exactly once per
 * occurrence, in order, with none added or dropped — including repeats such as
 * `11` and zeros such as `100`.
 *
 * @param {{language: 'en'|'bn', tokenDigits: number[], roomDigits: number[]|null}} plan
 * @returns {{token: string[], room: string[]}}
 */
export function expectedDigitClips(plan) {
  const language = plan.language;
  return {
    token: plan.tokenDigits.map((digit) => digitAssetId(language, digit)),
    room: (plan.roomDigits || []).map((digit) => digitAssetId(language, digit)),
  };
}
