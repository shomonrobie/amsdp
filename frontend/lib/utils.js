/* AMSDP shared helpers — the small, dependency-light utilities every component
 * in the design system uses.
 *
 * `cn()` is the shadcn/ui convention: `clsx` for conditionals, `tailwind-merge`
 * so a caller-supplied `className` can override a variant default instead of
 * fighting it (`… p-1 p-3` style duplicates are impossible).
 */
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Compose class names; later conflicting Tailwind utilities win. */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/** A stable, non-empty id fragment for aria wiring (`label-for`, `aria-describedby`). */
export function fieldId(name, id) {
  return id || ('amsdp-' + String(name || 'field').replace(/[^a-zA-Z0-9_-]/g, '-'));
}

/** `500` → `৳ 500` / `Tk 500` — one money format for every screen. */
export function money(value, locale = 'bn') {
  if (value === null || value === undefined || value === '') return '—';
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  return (locale === 'en' ? 'Tk ' : '৳ ') + n.toLocaleString(locale === 'en' ? 'en-GB' : 'bn-BD');
}

/** Truncate a line of text on a word boundary, for compact cards. */
export function truncate(text, max = 28) {
  const s = String(text || '');
  if (s.length <= max) return s;
  return s.slice(0, max - 1).replace(/\s+\S*$/, '') + '…';
}
