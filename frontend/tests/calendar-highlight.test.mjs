/* AMSDP appointment calendar — marking the matched substring (D-2).
 *
 * `lib/calendar/highlight.js` decides which spans of a patient name or token are
 * the part the search matched; `AppointmentCalendar` renders them as `<mark>`.
 * The safety properties are the point of the module, so they are the point of
 * these tests: the term is user input, and it must never become a pattern, an
 * HTML string, or a reason for the visible text to change.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  MAX_TERM, highlightSegments, hasHighlight,
} from '../lib/calendar/highlight.js';

/** The marked substrings, in order. */
const marks = (text, term) => highlightSegments(text, term)
  .filter((s) => s.match).map((s) => s.text);

/** The segments must always reconstruct the original string exactly. */
const rejoin = (text, term) => highlightSegments(text, term).map((s) => s.text).join('');

test('nothing is marked when there is nothing to look for', () => {
  // A name is rendered identically whether or not a search is running, so the
  // card markup does not change shape when a filter is applied and removed.
  for (const term of ['', '   ', null, undefined]) {
    assert.deepEqual(highlightSegments('রহিম উদ্দিন', term),
      [{ text: 'রহিম উদ্দিন', match: false }], JSON.stringify(term));
  }
  assert.deepEqual(highlightSegments('', 'রহিম'), [{ text: '', match: false }]);
  assert.deepEqual(highlightSegments(null, 'রহিম'), [{ text: '', match: false }]);
  assert.deepEqual(highlightSegments(undefined, undefined), [{ text: '', match: false }]);
});

test('the matched substring is marked and the rest is untouched', () => {
  // Bangla: the server's ILIKE matches a substring, so the marking must find the
  // same one — including when it starts mid-word.
  assert.equal(rejoin('রহিম উদ্দিন', 'হিম'), 'রহিম উদ্দিন');
  assert.deepEqual(highlightSegments('রহিম উদ্দিন', 'হিম'), [
    { text: 'র', match: false },
    { text: 'হিম', match: true },
    { text: ' উদ্দিন', match: false },
  ]);
  assert.deepEqual(marks('রহিম উদ্দিন', 'রহিম'), ['রহিম']);

  // A match at the very end needs no trailing empty segment.
  assert.deepEqual(highlightSegments('Token 12', '12'), [
    { text: 'Token ', match: false },
    { text: '12', match: true },
  ]);
  // A whole-string match is one segment, not three.
  assert.deepEqual(highlightSegments('12', '12'), [{ text: '12', match: true }]);
});

test('marking is case-insensitive, exactly as the search is', () => {
  // The server filters with ILIKE; a name marked only when typed in the same
  // case would suggest the search had failed.
  assert.deepEqual(marks('Rahim Uddin', 'rahim'), ['Rahim']);
  assert.deepEqual(marks('Rahim Uddin', 'RAH'), ['Rah']);
  assert.equal(rejoin('Rahim Uddin', 'RAH'), 'Rahim Uddin', 'the original case is preserved');
  // Bangla is caseless; the same path must not corrupt it.
  assert.deepEqual(marks('রহিম উদ্দিন', 'উদ্দিন'), ['উদ্দিন']);
});

test('every occurrence is marked, and the segments tile the name', () => {
  assert.deepEqual(marks('Rahim Rahima Rahim', 'rahim'), ['Rahim', 'Rahim', 'Rahim']);
  assert.equal(rejoin('Rahim Rahima Rahim', 'rahim'), 'Rahim Rahima Rahim');
  // Overlapping candidates are consumed left to right, so no segment overlaps.
  const segments = highlightSegments('aaaa', 'aa');
  assert.deepEqual(segments.map((s) => s.text), ['aa', 'aa']);
  assert.deepEqual(segments.map((s) => s.match), [true, true]);
  // A dense name still tiles: no duplicated or dropped characters.
  assert.equal(rejoin('বাংলাদেশ বাংলাদেশ', 'দেশ'), 'বাংলাদেশ বাংলাদেশ');
});

test('the term is a literal string, never a pattern', () => {
  // RegExp metacharacters must match themselves: `*` alone would throw as a
  // pattern, `.` would match anything, `(` would be invalid.
  assert.deepEqual(marks('12 * 3', '*'), ['*']);
  assert.deepEqual(marks('Rahim Khan', '.'), [], 'a dot is not "any character"');
  assert.deepEqual(marks('Rahim (Khan)', '('), ['(']);
  assert.deepEqual(marks('Rahim [K] Khan', '[K]'), ['[K]']);
  assert.equal(highlightSegments('Rahim * Khan', '*').length, 3);

  // `%` and `_` are the server's escaped LIKE wildcards — literal here too, so
  // what is marked is what was matched rather than "everything".
  assert.deepEqual(marks('Rahim Khan', '%'), []);
  assert.deepEqual(marks('Rahim Khan', '_'), []);
  assert.deepEqual(marks('50% off', '%'), ['%']);
});

test('marking never interprets the text as markup', () => {
  // A patient name containing HTML is data.  This module returns text; the
  // component escapes it.  Nothing here may produce a tag.
  const evil = '<script>alert(1)</script>';
  assert.equal(rejoin(evil, 'script'), evil);
  assert.deepEqual(marks(evil, 'script'), ['script', 'script']);
  highlightSegments(evil, 'script').forEach((s) => {
    assert.equal(typeof s.text, 'string');
    assert.deepEqual(Object.keys(s).sort(), ['match', 'text'], 'segments carry no HTML');
  });
});

test('a term that cannot occur marks nothing', () => {
  assert.deepEqual(marks('Rahim Khan', 'karim'), []);
  assert.deepEqual(highlightSegments('Rahim', 'Rahim Khan'), [{ text: 'Rahim', match: false }]);
  assert.equal(hasHighlight('Rahim Khan', 'karim'), false);
  assert.equal(hasHighlight('Rahim Khan', 'khan'), true);
});

test('the term is trimmed and capped, so a long box cannot make work for nothing', () => {
  // Pasted whitespace is noise, not part of the name.
  assert.deepEqual(marks('Rahim Khan', '  khan  '), ['Khan']);
  // Anything longer than MAX_TERM can never be a substring of a short name; the
  // cap keeps a pathological paste from being searched character by character.
  assert.equal(MAX_TERM, 120);
  const long = 'x'.repeat(MAX_TERM + 30);
  assert.deepEqual(marks('Rahim Khan', long), []);
  assert.deepEqual(marks('x'.repeat(MAX_TERM), long), ['x'.repeat(MAX_TERM)],
    'the cap truncates the term, it does not disable marking');
});
