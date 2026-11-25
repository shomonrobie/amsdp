/* MP-29 — accessibility and touch rules expressed as data.
 *
 * The queue and appointment screens were usable only with a mouse and only on a
 * desktop: the reorder arrows were 30 px wide 0.8 rem buttons with no accessible
 * name, a row could not be reached by keyboard at all, and no layout rule existed
 * below 480 px. The rules that fix that are kept here as plain functions rather
 * than inline in the page, so they can be asserted by `node --test` without a
 * browser or a new dependency — the same approach `lib/staff-policy.js` and
 * `lib/dashboard.js` already use.
 *
 * Nothing here authorises anything. The screen only mirrors a decision the
 * server already takes (`queue.manage`); a keyboard chord that this module maps
 * is still refused on the server by whoever lacks the capability.
 */

/** Smallest acceptable pointer target, in CSS pixels.
 *
 * WCAG 2.5.5 (AAA) asks for 44×44; 2.5.8 (AA) for 24×24. The reception desk is
 * a touch surface, so the larger floor is used and asserted in `global.css`.
 */
export const MIN_TARGET_PX = 44;

/** Modifier that turns an arrow key into a reorder gesture.
 *
 * Bare `ArrowUp`/`ArrowDown` stay page scrolling — the queue is a long list and
 * hijacking those keys is a worse defect than the one being fixed.
 */
export const REORDER_MODIFIER = 'Alt';

/** The reorder delta for a key event: -1 up, +1 down, 0 not a reorder chord. */
export function reorderDelta(event) {
  if (!event || typeof event.key !== 'string') return 0;
  if (event.altKey !== true) return 0;
  if (event.ctrlKey === true || event.metaKey === true) return 0;
  if (event.key === 'ArrowUp') return -1;
  if (event.key === 'ArrowDown') return 1;
  return 0;
}

/** A list index as an integer, or `null` when the value is not a position.
 *
 * `Number(null)` and `Number('')` are both `0`, so a numeric cast would make a
 * missing index look like the first row — exactly the failure that produced a
 * `undefined` in the reorder payload. Only a real integer or a digit string is
 * a position.
 */
export function toPosition(value) {
  if (typeof value === 'number') {
    return Number.isInteger(value) && value >= 0 ? value : null;
  }
  if (typeof value === 'string' && /^\d+$/.test(value)) return Number(value);
  return null;
}

/** Move `index` by `delta` in `list`, without mutating the argument.
 *
 * Returns `{ list, moved, from, to }`. An index that is not a position — the
 * defect this task found: the table never passed the row index, so `move()`
 * swapped `undefined` into the payload — yields `moved: false` and an unchanged
 * copy instead of a corrupt id list.
 */
export function moveWithin(list, index, delta) {
  const out = Array.isArray(list) ? list.slice() : [];
  const from = toPosition(index);
  const step = toPosition(delta === 0 ? 0 : Math.abs(Number(delta)));
  const backwards = Number(delta) < 0;
  const valid = from !== null && step !== null && step > 0
    && Number.isInteger(Number(delta)) && Number(delta) !== 0;
  const to = valid ? from + (backwards ? -step : step) : NaN;
  const moved = valid && from < out.length && to >= 0 && to < out.length;
  if (!moved) return { list: out, moved: false, from, to };
  const [item] = out.splice(from, 1);
  out.splice(to, 0, item);
  return { list: out, moved: true, from, to };
}

/** One-based "position/total" label, or '' when the arguments are not positions. */
export function positionLabel(index, total) {
  const i = toPosition(index);
  const n = toPosition(total);
  if (i === null || n === null || n <= 0 || i >= n) return '';
  return `${i + 1}/${n}`;
}

/** Props that make a table row reachable and reorderable from the keyboard.
 *
 * `label` is the row's accessible name (token + position), so a screen reader
 * announces which patient is being moved rather than "row 3". When `canMove`
 * is false the row stays readable but is not a control.
 */
export function reorderRowProps({ index, total, label, canMove, onMove }) {
  const position = positionLabel(index, total);
  const props = {
    'aria-rowindex': Number.isInteger(Number(index)) ? Number(index) + 1 : undefined,
    'aria-label': [label, position].filter(Boolean).join(', ') || undefined,
  };
  if (!canMove) return props;
  return {
    ...props,
    tabIndex: 0,
    onKeyDown: (event) => {
      const delta = reorderDelta(event);
      if (!delta) return;
      event.preventDefault();
      if (typeof onMove === 'function') onMove(index, delta);
    },
  };
}
