/* QUE-006 / W1 — prerecorded player (roadmap §8.1 AC-2 … AC-7).
 *
 * A fake `Audio` element and fake timers drive every scenario, so the engine is
 * tested without a browser (AC-8). Nothing here claims browser playback: these
 * tests prove the *logic* — completion only from `ended`, refusal before sound,
 * one announcement at a time, no network, no rejection into the caller.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  createPrerecordedPlayer,
  FAILURE,
  PLAYBACK,
  reasonForMediaError,
} from '../lib/announcements/prerecorded-audio.js';

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

/** Let the engine's awaits advance between synthetic events. */
function settle() {
  return new Promise((resolve) => setImmediate(resolve));
}

function fakeAudioEnvironment() {
  const created = [];
  class FakeAudio {
    constructor(src) {
      this.src = src;
      this.error = null;
      this.paused = true;
      this.listeners = new Map();
      created.push(this);
    }

    addEventListener(name, fn) {
      if (!this.listeners.has(name)) this.listeners.set(name, []);
      this.listeners.get(name).push(fn);
    }

    removeEventListener(name, fn) {
      const list = this.listeners.get(name) || [];
      const index = list.indexOf(fn);
      if (index >= 0) list.splice(index, 1);
    }

    emit(name) {
      (this.listeners.get(name) || []).slice().forEach((fn) => fn({ type: name }));
    }

    play() {
      this.paused = false;
      return Promise.resolve();
    }

    pause() {
      if (this.paused) return;
      this.paused = true;
      this.emit('pause');
    }

    end() {
      this.paused = true;
      this.emit('ended');
    }

    fail(code) {
      this.error = { code };
      this.emit('error');
    }

    listenerCount() {
      let total = 0;
      this.listeners.forEach((list) => { total += list.length; });
      return total;
    }
  }
  return {
    created,
    FakeAudio,
    audioFactory: (src) => new FakeAudio(src),
    rejectingFactory() {
      return (src) => {
        const element = new FakeAudio(src);
        element.play = () => Promise.reject(new Error('NotAllowedError'));
        return element;
      };
    },
  };
}

function fakeTimers() {
  const pending = new Map();
  let next = 1;
  return {
    setTimeout(fn, ms) { const id = next++; pending.set(id, { fn, ms }); return id; },
    clearTimeout(id) { pending.delete(id); },
    runAll() {
      const items = Array.from(pending.values());
      pending.clear();
      items.forEach((item) => item.fn());
    },
    delays() { return Array.from(pending.values()).map((item) => item.ms); },
    size() { return pending.size; },
  };
}

test('AC-2 completed is reported only after the final clip ends', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });
  let outcome = null;
  const pending = player.play({ token: 'T-1' }).then((result) => { outcome = result; return result; });

  await settle();
  assert.equal(audio.created.length, 1);
  audio.created[0].end();
  await settle();
  assert.equal(outcome, null, 'the prefix alone is not the sentence');
  assert.equal(audio.created.length, 2);

  audio.created[1].end();
  await settle();
  assert.equal(outcome, null, 'the digits alone are not the sentence');
  assert.equal(audio.created.length, 3);

  audio.created[2].end();
  const result = await pending;
  assert.equal(result.status, PLAYBACK.COMPLETED);
  assert.equal(result.completedSegments, 3);
  assert.equal(result.segmentCount, 3);
  assert.equal(result.packId, 'platform.en.draft.v1');
  assert.equal(result.language, 'en');
  assert.equal(player.getState().playing, false);
});

test('AC-2 a cut-off mid-sentence is failed(interrupted), not completed', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });
  const pending = player.play({ token: '12' });
  await settle();
  audio.created[0].end();
  await settle();
  audio.created[1].fail(1); // MEDIA_ERR_ABORTED
  const result = await pending;
  assert.equal(result.status, PLAYBACK.FAILED);
  assert.equal(result.reason, FAILURE.INTERRUPTED);
  assert.equal(result.completedSegments, 1);
  assert.equal(result.failedAssetId, 'en.digit.1');
});

test('AC-2 an unexpected pause is interrupted, not success', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });
  const pending = player.play({ token: '8' });
  await settle();
  audio.created[0].pause();
  const result = await pending;
  assert.equal(result.status, PLAYBACK.FAILED);
  assert.equal(result.reason, FAILURE.INTERRUPTED);
});

test('AC-3 a missing asset fails before any audio element exists', async () => {
  const trimmed = {
    id: 'platform.en.broken.v1',
    language: 'en',
    version: 1,
    manifest: { assets: MANIFEST.assets.filter((asset) => asset.id !== 'en.digit.7') },
  };
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({ pack: trimmed, audioFactory: audio.audioFactory });
  const result = await player.play({ token: '7' });
  assert.equal(result.status, PLAYBACK.FAILED);
  assert.equal(result.reason, FAILURE.MISSING_ASSET);
  assert.deepEqual(result.missing, ['en.digit.7']);
  assert.equal(audio.created.length, 0, 'no partial sentence was started');
  assert.equal(player.getState().playing, false);
});

test('AC-4 a corrupt clip fails as decode_error and the player stays usable', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });

  const bad = player.play({ token: '3' });
  await settle();
  audio.created[0].end();
  await settle();
  audio.created[1].fail(3); // MEDIA_ERR_DECODE
  const failed = await bad;
  assert.equal(failed.status, PLAYBACK.FAILED);
  assert.equal(failed.reason, FAILURE.DECODE_ERROR);
  assert.equal(failed.failedAssetId, 'en.digit.3');

  const good = player.play({ token: '1' });
  await settle();
  audio.created[2].end();
  await settle();
  audio.created[3].end();
  await settle();
  audio.created[4].end();
  const result = await good;
  assert.equal(result.status, PLAYBACK.COMPLETED, 'a decode failure must not poison the engine');
});

test('AC-5 a second announcement while one plays is busy, never overlapping', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });
  const first = player.play({ token: '1' });
  await settle();
  const second = await player.play({ token: '2' });
  assert.equal(second.status, PLAYBACK.BUSY);
  assert.equal(audio.created.length, 1, 'the second call created no audio');

  audio.created[0].end();
  await settle();
  audio.created[1].end();
  await settle();
  audio.created[2].end();
  assert.equal((await first).status, PLAYBACK.COMPLETED);
});

test('AC-6 an installed Bangla catalogue plays with no network access', async () => {
  const audio = fakeAudioEnvironment();
  const fetched = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (...args) => {
    fetched.push(args[0]);
    return Promise.reject(new Error('offline'));
  };
  try {
    const player = createPrerecordedPlayer({
      pack: builtin('bn'), audioFactory: audio.audioFactory, timers: fakeTimers() });
    const pending = player.play({ token: '5', room: '2' });
    for (let index = 0; index < 5; index += 1) {
      await settle();
      audio.created[index].end();
    }
    const result = await pending;
    assert.equal(result.status, PLAYBACK.COMPLETED);
    assert.equal(result.segmentCount, 5);
    assert.equal(fetched.length, 0, 'nothing is fetched while playing installed clips');
    audio.created.forEach((element) => {
      assert.equal(/^https?:/i.test(element.src), false);
      assert.match(element.src, /^\/audio\/bn\//);
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('AC-6 the intentional-pause asset becomes a 300 ms gap, not a clip', async () => {
  const audio = fakeAudioEnvironment();
  const timers = fakeTimers();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers });
  const pending = player.play({ token: '5', room: '3' });
  for (let index = 0; index < 4; index += 1) {
    await settle();
    audio.created[index].end();
  }
  await settle();
  assert.equal(audio.created.length, 4, 'the silence file is not loaded');
  assert.deepEqual(timers.delays(), [300]);
  timers.runAll();
  const result = await pending;
  assert.equal(result.status, PLAYBACK.COMPLETED);
  assert.equal(result.completedSegments, 5);
});

test('a browser refusal is failed(blocked) and never rejects into the caller', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.rejectingFactory(), timers: fakeTimers() });
  const result = await player.play({ token: '2' });
  assert.equal(result.status, PLAYBACK.FAILED);
  assert.equal(result.reason, FAILURE.BLOCKED);
});

test('cancel() stops the sentence, detaches listeners and reports cancelled', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });
  const pending = player.play({ token: '12' });
  await settle();
  assert.equal(player.cancel(), true);
  const result = await pending;
  assert.equal(result.status, PLAYBACK.CANCELLED);
  assert.equal(audio.created[0].listenerCount(), 0);
  assert.equal(player.getState().playing, false);
});

test('cancel() during the intentional pause also reports cancelled', async () => {
  const audio = fakeAudioEnvironment();
  const timers = fakeTimers();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers });
  const pending = player.play({ token: '5', room: '3' });
  for (let index = 0; index < 4; index += 1) {
    await settle();
    audio.created[index].end();
  }
  await settle();
  assert.equal(timers.size(), 1);
  player.cancel();
  assert.equal(timers.size(), 0, 'the pending pause timer is cleared');
  assert.equal((await pending).status, PLAYBACK.CANCELLED);
});

test('a different pack version is selected without recreating the player', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({
    pack: builtin('en'), audioFactory: audio.audioFactory, timers: fakeTimers() });
  const organizationPack = builtin('en', {
    id: 'org.acme.en.female.v2',
    version: 2,
    scope: 'organization',
    organizationId: 'org_acme',
    source: 'organization',
    basePath: '/audio/packs/acme-en-female-v2',
  });
  assert.equal(player.setPack(organizationPack), true);
  assert.equal(player.getState().packId, 'org.acme.en.female.v2');
  assert.equal(player.getState().version, 2);

  const pending = player.play({ token: '2' });
  await settle();
  assert.match(audio.created[0].src, /^\/audio\/packs\/acme-en-female-v2\//);
  assert.equal(player.setPack(builtin('bn')), false, 'no voice change mid-sentence');
  assert.equal(player.cancel(), true);
  const result = await pending;
  assert.equal(result.status, PLAYBACK.CANCELLED);
  assert.equal(result.packId, 'org.acme.en.female.v2');
});

test('media errors map to the honest reason', () => {
  assert.equal(reasonForMediaError({ code: 1 }), FAILURE.INTERRUPTED);
  assert.equal(reasonForMediaError({ code: 2 }), FAILURE.NETWORK_ERROR);
  assert.equal(reasonForMediaError({ code: 3 }), FAILURE.DECODE_ERROR);
  assert.equal(reasonForMediaError({ code: 4 }), FAILURE.UNSUPPORTED_SOURCE);
  assert.equal(reasonForMediaError(null), FAILURE.ERROR);
});

test('AC-7 the queue page never awaits playback (static check)', () => {
  const source = readFileSync(join(HERE, '..', 'pages', 'queue.js'), 'utf8');
  // Comments may describe the rule; only code may break it.
  const stripComments = (text) => text
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/[^\n]*/g, '');

  const announceStart = source.indexOf('const announceEntry');
  const announceEnd = source.indexOf('const loadQueue');
  assert.ok(announceStart > 0 && announceEnd > announceStart, 'announceEntry still exists');
  const announceBody = stripComments(source.slice(announceStart, announceEnd));
  assert.equal(/await/.test(announceBody), false, 'the announce trigger is fire-and-forget');
  assert.match(announceBody, /announcements\.announce\(/);

  const actionStart = source.indexOf('const doAction');
  const actionEnd = source.indexOf('const checkIn');
  assert.ok(actionStart > 0 && actionEnd > actionStart, 'doAction still exists');
  assert.equal(/announce/i.test(stripComments(source.slice(actionStart, actionEnd))), false,
    'a queue action must not be coupled to audio');

  assert.equal(/await\s+announcements\.announce/.test(stripComments(source)), false,
    'nothing in the queue page awaits an announcement');
});

test('the engine refuses to play after dispose without throwing', async () => {
  const audio = fakeAudioEnvironment();
  const player = createPrerecordedPlayer({ pack: builtin('en'), audioFactory: audio.audioFactory });
  player.dispose();
  const result = await player.play({ token: '1' });
  assert.equal(result.status, PLAYBACK.FAILED);
  assert.equal(result.reason, FAILURE.AUDIO_UNAVAILABLE);
});
