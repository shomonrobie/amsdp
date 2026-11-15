/* AMSDP Bangladeshi mobile numbers — the browser-side mirror of
 * `backend/common/phone.py`.
 *
 * Why this exists (AMSDP-FACILITY-DOCTOR-01)
 * ------------------------------------------
 * The doctor registration form must refuse a malformed number *before* the
 * request leaves the browser, and it must show the number in the same canonical
 * form the API stores (`01XXXXXXXXX`).  The backend remains the authority: this
 * module mirrors `normalize_bd_mobile` exactly, including the international
 * branch that rejects `+8801...`-shaped-but-wrong numbers, so the two cannot
 * disagree about what a valid number is.
 *
 * Only Bangladeshi mobile numbers are supported (single-country MVP), and the
 * operator prefix must be 013–019: 010/012 are PSTN and are refused.
 */

/** Canonical national form: 11 digits, operator prefix 013–019. */
const BD_MOBILE = /^01[3-9]\d{8}$/;

/** Characters that carry no information in a written phone number. */
const SEPARATORS = /[\s\-().]/g;

/** Anything that is not a digit — applied after the separators are gone. */
const NON_DIGITS = /\D/g;

/** Raised when a value cannot be a Bangladeshi mobile number. */
export class InvalidMobileNumber extends Error {
  constructor(message) {
    super(message);
    this.name = 'InvalidMobileNumber';
  }
}

/**
 * Return `value` in canonical national form (`01XXXXXXXXX`).
 *
 * Throws `InvalidMobileNumber` when the value is empty or is not a valid
 * Bangladeshi mobile number — it never returns a partially cleaned value, so a
 * caller either gets a storable number or a reason to show the operator.
 */
export function normalizeMobile(value) {
  if (value === null || value === undefined) {
    throw new InvalidMobileNumber('mobile number is required');
  }
  const raw = String(value).trim();
  if (!raw) throw new InvalidMobileNumber('mobile number is required');

  let cleaned = raw.replace(SEPARATORS, '');
  const international = cleaned.startsWith('+');
  cleaned = cleaned.replace(NON_DIGITS, '');

  let national;
  if (cleaned.startsWith('880')) {
    national = '0' + cleaned.slice(3);          // 8801711111111 -> 01711111111
  } else if (cleaned.startsWith('01')) {
    national = cleaned;                          // 01711111111
  } else if (international) {
    throw new InvalidMobileNumber(
      'invalid Bangladeshi mobile number: country code must be +880');
  } else if (cleaned.length === 10 && cleaned.startsWith('1')) {
    national = '0' + cleaned;                    // 1711111111 -> 01711111111
  } else {
    throw new InvalidMobileNumber('invalid Bangladeshi mobile number');
  }

  if (!BD_MOBILE.test(national)) {
    throw new InvalidMobileNumber(
      'invalid Bangladeshi mobile number (expected 01[3-9]XXXXXXXX)');
  }
  return national;
}

/** True when `value` normalises to a Bangladeshi mobile number. */
export function isValidMobile(value) {
  try {
    normalizeMobile(value);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Display helper for an already-valid number.
 *
 * `style='national'` (default) → `01711111111`, `'e164'` → `+8801711111111`,
 * `'spaced'` → `017 1111 1111`.  An unusable value is returned unchanged: a
 * malformed legacy row must still render.
 */
export function formatMobile(value, style = 'national') {
  let national;
  try {
    national = normalizeMobile(value);
  } catch (e) {
    return value === null || value === undefined ? '' : String(value);
  }
  if (style === 'e164') return '+88' + national;
  if (style === 'spaced') {
    return `${national.slice(0, 3)} ${national.slice(3, 7)} ${national.slice(7)}`;
  }
  return national;
}

/**
 * Validate a form field and return `{ ok, value, error }`.
 *
 * `emptyMessage` and `invalidMessage` are supplied by the caller from the
 * i18n dictionary so the page never hard-codes one language.
 */
export function validateMobile(value, messages = {}) {
  const empty = messages.empty || 'mobile number is required';
  const invalid = messages.invalid ||
    'invalid Bangladeshi mobile number (expected 01[3-9]XXXXXXXX)';
  const raw = value === null || value === undefined ? '' : String(value).trim();
  if (!raw) return { ok: false, value: '', error: empty };
  try {
    return { ok: true, value: normalizeMobile(raw), error: '' };
  } catch (e) {
    return { ok: false, value: '', error: invalid };
  }
}
