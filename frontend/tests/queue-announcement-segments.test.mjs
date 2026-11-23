/* QUE-006 / W1 — segment resolution (roadmap §8.1 AC-1, AC-3, AC-6 support).
 *
 * AC-1 says the segment list must be proven against the approved text, not by
 * inspection. The manifest states what each clip contains (`spokenText`), so
 * concatenating the resolved clips in order and comparing that with
 * `buildAnnouncement()`'s approved sentence is the honest check: it fails if a
 * clip is in the wrong place, missing, or a digit is skipped.
 *
 * The comparison is normalised for two documented reasons (TF-2, TF-4):
 *   - punctuation is not spoken, and the catalogue clips carry their own commas
 *     and full stops;
 *   - English digit clips speak the word ("five") while Bangla digit clips
 *     speak the glyph ("৫"), and the template carries a numeral.
 * The normaliser maps both sides to one shape; it never relaxes word order.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { buildAnnouncement } from '../lib/announcements/content.js';
import {
  digitsOf,
  joinBasePath,
  resolveSegments,
  SEGMENT_KIND,
  toAsciiDigits,
} from '../lib/announcements/segments.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const MANIFEST = JSON.parse(
  readFileSync(join(HERE, '..', 'public', 'audio', 'manifest.json'), 'utf8'));

function builtin(language, overrides = {}) {
  return {
    id: 'platform.' + language + '.draft.v1',
    language,
    version: 1,
    basePath: '/audio',
    manifest: MANIFEST,
    ...overrides,
  };
}

const NUMBER_WORDS = ['zero', 'one', 'two', 'three', 'four', 'five',
  'six', 'seven', 'eight', 'nine'];
const NUMBER_WORD_RE = new RegExp('\\b(' + NUMBER_WORDS.join('|') + ')\\b', 'g');

/** One shape for both sides of the comparison. */
function spokenShape(value) {
  // Whitespace is dropped last: it marks clip boundaries on the segment side
  // ("one" + "zero", "৫" + "-এ") but is not audible, so it must not decide the
  // comparison. Word order and content remain strict.
  return toAsciiDigits(value)
    .toLowerCase()
    .replace(NUMBER_WORD_RE, (word) => String(NUMBER_WORDS.indexOf(word)))
    .replace(/[.,!?;:।\-–—'"()]/g, '')
    .replace(/\s+/g, '');
}

const TOKENS = ['T-3F2A9C-001', '7', '012', '101', '11', '999', '240', '৭'];
const ROOMS = [null, undefined, '5', '101', '৩'];

test('AC-1 every resolved segment list speaks the approved sentence', () => {
  let checked = 0;
  ['en', 'bn'].forEach((language) => {
    TOKENS.forEach((token) => {
      ROOMS.forEach((room) => {
        const resolved = resolveSegments({ token, room }, builtin(language));
        assert.equal(resolved.ok, true,
          language + ' token=' + token + ' room=' + room + ' refused: ' + resolved.reason);
        assert.equal(spokenShape(resolved.spokenText), spokenShape(resolved.approvedText),
          language + ' token=' + token + ' room=' + room);
        assert.equal(resolved.approvedText, buildAnnouncement({ token, room }, language).text);
        checked += 1;
      });
    });
  });
  assert.equal(checked, 80);
});

test('AC-1 the segment order is the catalogue contract, not an accident', () => {
  const englishRoom = resolveSegments({ token: 'T-3F2A9C-012', room: '3' }, builtin('en'));
  assert.deepEqual(englishRoom.segments.map((s) => s.assetId), [
    'en.phrase.token-number',
    'en.digit.1',
    'en.digit.2',
    'en.phrase.proceed-to-room',
    'en.digit.3',
    'en.phrase.room-suffix',
  ]);

  const englishPlain = resolveSegments({ token: 'T-3F2A9C-012' }, builtin('en'));
  assert.deepEqual(englishPlain.segments.map((s) => s.assetId), [
    'en.phrase.token-number',
    'en.digit.1',
    'en.digit.2',
    'en.phrase.no-room',
  ]);

  const banglaRoom = resolveSegments({ token: '5', room: '12' }, builtin('bn'));
  assert.deepEqual(banglaRoom.segments.map((s) => s.assetId), [
    'bn.phrase.token-number',
    'bn.digit.5',
    'bn.phrase.room-prefix',
    'bn.digit.1',
    'bn.digit.2',
    'bn.phrase.room-locative',
  ]);

  // The catalogue's only non-speech clip is the intentional pause (TF-3).
  const pause = englishRoom.segments[englishRoom.segments.length - 1];
  assert.equal(pause.kind, SEGMENT_KIND.PAUSE);
  assert.equal(pause.durationMs, 300);
  assert.equal(englishPlain.segments.some((s) => s.kind === SEGMENT_KIND.PAUSE), false);
});

test('TF-1 a second voice pack version needs no code change', () => {
  const pack = builtin('en', {
    id: 'platform.en.male.v2',
    version: 2,
    basePath: '/audio/packs/platform-en-male-v2/',
    manifest: {
      schema: 'AMSDP-QUE-006-audio-assets/2.0',
      assets: MANIFEST.assets.map((asset) => (asset.id === 'en.digit.4'
        ? { ...asset, playbackFile: 'digit-four-v2.mp3' }
        : asset)),
    },
  });
  const resolved = resolveSegments({ token: '4' }, pack);
  assert.equal(resolved.ok, true);
  assert.equal(resolved.packId, 'platform.en.male.v2');
  assert.equal(resolved.version, 2);
  assert.equal(resolved.segments[1].assetId, 'en.digit.4');
  assert.equal(resolved.segments[1].src, '/audio/packs/platform-en-male-v2/digit-four-v2.mp3');
  assert.equal(resolved.segments[0].src, '/audio/packs/platform-en-male-v2/en/phrase/token-number.mp3');
});

test('AC-6 assets resolve to local paths under the pack base path', () => {
  const resolved = resolveSegments({ token: '7', room: '2' }, builtin('bn'));
  assert.equal(resolved.ok, true);
  resolved.segments.forEach((segment) => {
    assert.match(segment.src, /^\/audio\/bn\//);
    assert.equal(segment.src.includes('http'), false);
    assert.equal(segment.src.includes('..'), false);
  });
});

test('refusals are explicit and never substituted', () => {
  assert.equal(resolveSegments({ token: '1' }, builtin('fr')).reason, 'unsupported_language');
  assert.equal(resolveSegments({ token: 'fr' }, builtin('en')).reason, 'unspeakable_token');
  assert.equal(resolveSegments({ token: '3f2a9c1e-1111-4222-8333-444455556666' }, builtin('en')).reason,
    'unspeakable_token');
  assert.equal(resolveSegments({ token: '4', room: 'A' }, builtin('en')).reason, 'unspeakable_room');
  assert.equal(resolveSegments({ token: '4' }, { id: 'empty', language: 'en', manifest: { assets: [] } }).reason,
    'manifest_unavailable');
});

test('AC-3 a missing asset is reported by id, before any playback exists', () => {
  const trimmed = {
    id: 'platform.en.broken.v1',
    language: 'en',
    version: 1,
    manifest: { assets: MANIFEST.assets.filter((asset) => asset.id !== 'en.digit.7') },
  };
  const resolved = resolveSegments({ token: '7' }, trimmed);
  assert.equal(resolved.ok, false);
  assert.equal(resolved.reason, 'missing_asset');
  assert.deepEqual(resolved.missing, ['en.digit.7']);
});

test('helpers keep digit and path handling honest', () => {
  assert.deepEqual(digitsOf('১০৩'), ['1', '0', '3']);
  assert.deepEqual(digitsOf('T-AB12CD-007'), ['1', '2', '0', '0', '7']);
  assert.deepEqual(digitsOf(''), []);
  assert.equal(joinBasePath('/audio/', '/en/digit-1.mp3'), '/audio/en/digit-1.mp3');
  assert.equal(joinBasePath(undefined, 'en/digit-1.mp3'), '/audio/en/digit-1.mp3');
  assert.equal(joinBasePath('/packs/v2', 'a.mp3'), '/packs/v2/a.mp3');
});
