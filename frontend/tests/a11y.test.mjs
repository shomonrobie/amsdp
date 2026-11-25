/* MP-29 — the rules that make the queue and appointment screens usable with a
 * keyboard, on a touch screen and at 360 px, asserted rather than described.
 *
 * `lib/a11y.js` holds the decisions (which chord reorders, how a move behaves at
 * the ends of the list) so they can be tested as data; this file tests them.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  MIN_TARGET_PX, REORDER_MODIFIER, moveWithin, positionLabel, reorderDelta, reorderRowProps,
} from '../lib/a11y.js';

const key = (k, mods = {}) => ({ key: k, altKey: false, ctrlKey: false, metaKey: false, shiftKey: false, ...mods });

test('the touch-target floor is 44 px and is the number the CSS uses', () => {
  assert.equal(MIN_TARGET_PX, 44);
  assert.equal(REORDER_MODIFIER, 'Alt');
});

test('only Alt+Arrow reorders; a bare arrow keeps scrolling the page', () => {
  assert.equal(reorderDelta(key('ArrowUp', { altKey: true })), -1);
  assert.equal(reorderDelta(key('ArrowDown', { altKey: true })), 1);
  // Bare arrows are the page's, not the row's.
  assert.equal(reorderDelta(key('ArrowUp')), 0);
  assert.equal(reorderDelta(key('ArrowDown')), 0);
  // A chord the browser owns (Ctrl+Alt = AltGr, Cmd+Alt = OS gesture) is left alone.
  assert.equal(reorderDelta(key('ArrowUp', { altKey: true, ctrlKey: true })), 0);
  assert.equal(reorderDelta(key('ArrowDown', { altKey: true, metaKey: true })), 0);
  // Alt with a non-arrow is not a reorder — Alt+Tab, Alt+F4 and Alt+letter stay put.
  assert.equal(reorderDelta(key('Tab', { altKey: true })), 0);
  assert.equal(reorderDelta(key('a', { altKey: true })), 0);
  assert.equal(reorderDelta(null), 0);
  assert.equal(reorderDelta({}), 0);
});

test('a move swaps two neighbours and leaves the input untouched', () => {
  const ids = ['a', 'b', 'c'];
  const down = moveWithin(ids, 0, 1);
  assert.deepEqual(down.list, ['b', 'a', 'c']);
  assert.equal(down.moved, true);
  assert.equal(down.from, 0);
  assert.equal(down.to, 1);
  assert.deepEqual(ids, ['a', 'b', 'c'], 'the caller list is never mutated');

  const up = moveWithin(ids, 2, -1);
  assert.deepEqual(up.list, ['a', 'c', 'b']);
  assert.equal(up.moved, true);
});

test('a move that would leave the list is refused, not clamped', () => {
  const ids = ['a', 'b', 'c'];
  for (const [index, delta] of [[0, -1], [2, 1], [1, 2], [5, -1], [-1, 1]]) {
    const result = moveWithin(ids, index, delta);
    assert.equal(result.moved, false, `index ${index} delta ${delta} must not move`);
    assert.deepEqual(result.list, ids, 'and must not reorder anything');
  }
});

test('an index that is not a position cannot corrupt the payload', () => {
  // The defect this task fixed: the table passed no index, so `move()` swapped
  // `undefined` into `entry_ids` and the server refused the reorder.
  const ids = ['a', 'b', 'c'];
  for (const index of [undefined, null, '', ' 1', NaN, 1.5, 'one']) {
    const result = moveWithin(ids, index, 1);
    assert.equal(result.moved, false, `index ${String(index)} is not a position`);
    assert.deepEqual(result.list, ids);
    assert.ok(result.list.every((id) => typeof id === 'string'),
      'no undefined may reach the request body');
  }
  assert.deepEqual(moveWithin(null, 0, 1), { list: [], moved: false, from: 0, to: 1 });
});

test('the position label is one-based and empty when meaningless', () => {
  assert.equal(positionLabel(0, 3), '1/3');
  assert.equal(positionLabel(2, 3), '3/3');
  assert.equal(positionLabel(3, 3), '');
  assert.equal(positionLabel(-1, 3), '');
  assert.equal(positionLabel(0, 0), '');
  assert.equal(positionLabel(undefined, 3), '');
  assert.equal(positionLabel('1', '3'), '2/3');
});

test('a movable row is focusable and moves on the chord only', () => {
  const moves = [];
  const props = reorderRowProps({
    index: 1, total: 3, canMove: true, label: 'Token A-014', onMove: (i, d) => moves.push([i, d]),
  });
  assert.equal(props.tabIndex, 0);
  assert.equal(props['aria-rowindex'], 2);
  assert.match(props['aria-label'], /A-014/);
  assert.match(props['aria-label'], /2\/3/);

  let prevented = 0;
  const fire = (event) => props.onKeyDown({ ...event, preventDefault: () => { prevented += 1; } });
  fire(key('ArrowUp', { altKey: true }));
  fire(key('ArrowDown', { altKey: true }));
  fire(key('ArrowDown'));           // bare arrow: page scroll, no move
  assert.deepEqual(moves, [[1, -1], [1, 1]]);
  assert.equal(prevented, 2, 'only the handled chords suppress the default');

  // No handler means no move: the chord must not throw.
  const noHandler = reorderRowProps({ index: 0, total: 1, canMove: true, label: 'x' });
  assert.doesNotThrow(() => noHandler.onKeyDown({ ...key('ArrowUp', { altKey: true }), preventDefault() {} }));
});

test('a read-only row is not a control', () => {
  const props = reorderRowProps({ index: 0, total: 2, canMove: false, label: 'Token B-002' });
  assert.equal(props.tabIndex, undefined);
  assert.equal(props.onKeyDown, undefined);
  assert.equal(props['aria-label'], 'Token B-002, 1/2', 'still readable');
});
