/* BanglaNameSense — keyboard / pointer / touch interaction tests.
 *
 * The component is a thin shell; every interaction decision lives in
 * `lib/bangla-name-sense/controller.js`, so these tests exercise the exact code
 * the browser runs (no DOM needed, no test framework dependency added).
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { buildDataset } from '../lib/bangla-name-sense/dataset.js';
import {
  initialState, queryChanged, focused, blurred, keyDown, selectIndex, Action, Key,
} from '../lib/bangla-name-sense/controller.js';

const raw = JSON.parse(readFileSync(new URL('../data/bangla_name_sense.json', import.meta.url), 'utf8'));
const index = buildDataset(raw).index;

const typed = (state, text) => queryChanged(state, text, index).state;

test('typing shows suggestions without touching the typed value', () => {
  const state = typed(initialState(), 'রফিক');
  assert.equal(state.query, 'রফিক');
  assert.equal(state.open, true);
  assert.ok(state.suggestions.length > 0);
  assert.equal(state.activeIndex, -1, 'nothing may be highlighted automatically');
});

test('no suggestion is selected until the user asks for one', () => {
  const state = typed(initialState(), 'রফিক');
  const result = keyDown(state, Key.ENTER);
  assert.equal(result.action, Action.NONE);
  assert.equal(result.value, undefined);
  assert.equal(result.state.query, 'রফিক', 'the typed text must be preserved');
});

test('ArrowDown / ArrowUp move the highlight with wrap-around', () => {
  let state = typed(initialState(), 'রফিক');
  const count = state.suggestions.length;

  state = keyDown(state, Key.DOWN).state;
  assert.equal(state.activeIndex, 0);
  state = keyDown(state, Key.DOWN).state;
  assert.equal(state.activeIndex, 1);
  state = keyDown(state, Key.UP).state;
  assert.equal(state.activeIndex, 0);
  state = keyDown(state, Key.UP).state;
  assert.equal(state.activeIndex, count - 1, 'ArrowUp from the first item wraps to the last');
  state = keyDown(state, Key.DOWN).state;
  assert.equal(state.activeIndex, 0, 'ArrowDown from the last item wraps to the first');
});

test('Enter selects the highlighted suggestion and closes the list', () => {
  let state = typed(initialState(), 'রফিক');
  state = keyDown(state, Key.DOWN).state;
  const highlighted = state.suggestions[state.activeIndex];
  const result = keyDown(state, Key.ENTER);
  assert.equal(result.action, Action.SELECT);
  assert.equal(result.value, highlighted.bn);
  assert.equal(result.state.open, false);
  assert.equal(result.state.activeIndex, -1);
});

test('Escape closes the list and keeps the typed text', () => {
  const state = typed(initialState(), 'রফি');
  const result = keyDown(state, Key.ESCAPE);
  assert.equal(result.action, Action.CLOSE);
  assert.equal(result.state.open, false);
  assert.equal(result.state.query, 'রফি');
});

test('Tab closes the list without selecting', () => {
  const state = keyDown(typed(initialState(), 'রফি'), Key.DOWN).state;
  const result = keyDown(state, Key.TAB);
  assert.equal(result.action, Action.CLOSE);
  assert.equal(result.value, undefined);
  assert.equal(result.state.query, 'রফি');
});

test('arrow keys do nothing when there is nothing to show', () => {
  const empty = typed(initialState(), 'zzzz');
  assert.equal(keyDown(empty, Key.DOWN).action, Action.NONE);
  assert.equal(keyDown(empty, Key.UP).action, Action.NONE);
});

test('a name absent from the dataset can be typed and submitted', () => {
  const state = typed(initialState(), 'অচেনা নাম');
  assert.deepEqual(state.suggestions, []);
  assert.equal(state.open, false);
  assert.equal(state.query, 'অচেনা নাম');

  const enter = keyDown(state, Key.ENTER);
  assert.equal(enter.action, Action.NONE);
  assert.equal(enter.value, undefined);
});

test('focus re-opens suggestions for existing text; blur closes them', () => {
  const typedState = typed(initialState(), 'রফিক');
  const reopened = focused({ ...typedState, open: false, activeIndex: -1 }, index).state;
  assert.equal(reopened.open, true);
  assert.equal(reopened.activeIndex, -1);

  const closed = blurred(reopened).state;
  assert.equal(closed.open, false);
  assert.equal(closed.query, 'রফিক');
});

test('pointer and touch selection pick the row that was tapped', () => {
  const state = typed(initialState(), 'রফিক');
  const result = selectIndex(state, 2);
  assert.equal(result.action, Action.SELECT);
  assert.equal(result.value, state.suggestions[2].bn);
  assert.equal(result.state.open, false);
});

test('an out-of-range pointer index is ignored instead of throwing', () => {
  const state = typed(initialState(), 'রফিক');
  for (const bad of [-1, 999, 1.5, 'x', null]) {
    assert.equal(selectIndex(state, bad).action, Action.NONE);
  }
});

test('editing after selecting continues from the selected text', () => {
  const state = typed(initialState(), 'রফিক');
  const picked = selectIndex(state, 0).state;
  const chosen = picked.query;
  assert.ok(chosen.startsWith('রফিক'), 'selection applies exactly the suggested bn');

  const edited = typed(picked, `${chosen} আ`);
  assert.equal(edited.query, `${chosen} আ`);
  assert.equal(edited.activeIndex, -1, 'editing clears any highlight');
  assert.equal(edited.open, edited.suggestions.length > 0);
});
