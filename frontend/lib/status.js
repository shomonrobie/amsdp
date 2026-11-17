/* AMSDP status vocabulary — one map, every screen.
 *
 * Appointment, queue and record-lifecycle states used to be re-declared in each
 * page (`StatusBadge` had one list, the calendar had another, the queue page a
 * third), so the same state could be green in one place and grey in another.
 * This module is the single source: tone (which badge colour) and label (what a
 * receptionist reads) in both languages.
 *
 * Tones are the names exported by `components/ui/Badge.js`.
 */

/** @typedef {'neutral'|'info'|'primary'|'success'|'warning'|'danger'|'outline'|'purple'|'teal'|'orange'|'slate'|'brown'} Tone */

const STATUS = {
  // --- appointment lifecycle ------------------------------------------------
  BOOKED: { tone: 'primary', bn: 'বুক হয়েছে', en: 'Booked' },
  AWAITING_CONFIRMATION: { tone: 'warning', bn: 'নিশ্চিতকরণ বাকি', en: 'Awaiting confirmation' },
  CONFIRMED: { tone: 'success', bn: 'নিশ্চিত', en: 'Confirmed' },
  CHECKED_IN: { tone: 'teal', bn: 'চেক-ইন', en: 'Checked-in' },
  IN_QUEUE: { tone: 'orange', bn: 'কিউতে', en: 'In queue' },
  IN_CONSULTATION: { tone: 'purple', bn: 'পরামর্শ চলছে', en: 'In consultation' },
  COMPLETED: { tone: 'slate', bn: 'সম্পন্ন', en: 'Completed' },
  CANCELLED: { tone: 'danger', bn: 'বাতিল', en: 'Cancelled' },
  NO_SHOW: { tone: 'neutral', bn: 'অনুপস্থিত', en: 'No-show' },
  RESCHEDULED: { tone: 'brown', bn: 'পুনঃনির্ধারিত', en: 'Rescheduled' },

  // --- queue lifecycle ------------------------------------------------------
  WAITING: { tone: 'orange', bn: 'অপেক্ষমাণ', en: 'Waiting' },
  CALLED: { tone: 'info', bn: 'কল করা হয়েছে', en: 'Called' },
  SKIPPED: { tone: 'neutral', bn: 'বাদ দেওয়া', en: 'Skipped' },
  AWAITING_RECOVERY: { tone: 'warning', bn: 'পুনরুদ্ধারের অপেক্ষায়', en: 'Awaiting recovery' },

  // --- record lifecycle (branch, floor, doctor, session…) -------------------
  active: { tone: 'success', bn: 'সক্রিয়', en: 'Active' },
  inactive: { tone: 'neutral', bn: 'নিষ্ক্রিয়', en: 'Inactive' },
  retired: { tone: 'neutral', bn: 'নিষ্ক্রিয়', en: 'Retired' },
  pending: { tone: 'warning', bn: 'যাচাই চলছে', en: 'Pending verification' },
  verified: { tone: 'success', bn: 'যাচাইকৃত', en: 'Verified' },
  rejected: { tone: 'danger', bn: 'প্রত্যাখ্যাত', en: 'Rejected' },
  unverified: { tone: 'warning', bn: 'যাচাই হয়নি', en: 'Unverified' },
};

/** Coerce API casing (`booked`, `Checked_In`) to the canonical key. */
export function normaliseStatus(status) {
  const raw = String(status == null ? '' : status).trim();
  if (!raw) return '';
  if (STATUS[raw]) return raw;
  const upper = raw.toUpperCase();
  if (STATUS[upper]) return upper;
  const lower = raw.toLowerCase();
  if (STATUS[lower]) return lower;
  return upper;
}

/**
 * Resolve a status to `{ key, tone, label }`.
 * `locale` is `'bn'` (default) or `'en'`.  An unknown status never renders as an
 * empty pill: it is humanised (`IN_THEATRE` → `In theatre`) with a neutral tone.
 */
export function statusMeta(status, locale = 'bn') {
  const key = normaliseStatus(status);
  const known = STATUS[key];
  if (known) return { key, tone: known.tone, label: locale === 'en' ? known.en : known.bn };
  const human = key ? key.replace(/_/g, ' ').toLowerCase() : '';
  return {
    key,
    tone: 'neutral',
    label: human ? human.charAt(0).toUpperCase() + human.slice(1) : '—',
  };
}

/** Just the tone — for calendars, charts and card borders. */
export function statusTone(status) {
  return statusMeta(status).tone;
}

/** Just the label. */
export function statusLabel(status, locale = 'bn') {
  return statusMeta(status, locale).label;
}

/** Terminal states can no longer be checked in, started or completed. */
export const TERMINAL_STATUSES = Object.freeze([
  'COMPLETED', 'CANCELLED', 'NO_SHOW', 'RESCHEDULED',
]);

export function isTerminal(status) {
  return TERMINAL_STATUSES.includes(normaliseStatus(status));
}

/** Hex colours for inline-styled surfaces (the calendar grid chips). */
export const STATUS_HEX = Object.freeze({
  BOOKED: '#1a5c7a',
  AWAITING_CONFIRMATION: '#8a6d00',
  CONFIRMED: '#2e7d32',
  CHECKED_IN: '#00695c',
  IN_QUEUE: '#ef6c00',
  WAITING: '#ef6c00',
  CALLED: '#0b6b78',
  IN_CONSULTATION: '#6a1b9a',
  COMPLETED: '#455a64',
  CANCELLED: '#c62828',
  NO_SHOW: '#757575',
  RESCHEDULED: '#5d4037',
  SKIPPED: '#757575',
});

export function statusHex(status, fallback = '#607d8b') {
  return STATUS_HEX[normaliseStatus(status)] || fallback;
}

export default statusMeta;
