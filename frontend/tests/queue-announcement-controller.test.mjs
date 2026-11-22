/* QUE-006 — the announcement controller.
 *
 * These assertions fix the decisions that must not drift: the facility switch,
 * duplicate suppression, one-at-a-time playback, user activation, the refusal of
 * content that cannot be spoken, and the fact that no outcome ever throws into
 * the queue page.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ACTIVATION,
  createAnnouncementController,
} from '../lib/announcements/controller.js';
import { OUTCOME } from '../lib/announcements/speech-synthesis.js';

function fakeAdapter(options = {}) {
  const statuses = options.statuses ? options.statuses.slice() : [OUTCOME.COMPLETED];
  const calls = { speak: [], cancel: 0, subscribe: 0 };
  return {
    calls,
    supported: options.supported !== false,
    isSupported() { return this.supported; },
    isSpeaking: () => options.speaking === true,
    capability: () => (options.supported === false
      ? { status: 'unsupported', voice: null, voices: [] }
      : { status: 'ready', voice: { voiceLang: 'bn-BD', name: 'Bangla', fallback: false }, voices: [] }),
    listVoices: () => [],
    async speak(text, opts) {
      calls.speak.push({ text, opts });
      if (options.throws) throw new Error('engine exploded');
      const status = statuses.length > 1 ? statuses.shift() : statuses[0];
      return { status };
    },
    cancel() { calls.cancel += 1; },
    subscribeVoices() { calls.subscribe += 1; return () => { calls.subscribe -= 1; }; },
  };
}

function clock(start = 1000) {
  let value = start;
  return { now: () => value, advance: (ms) => { value += ms; } };
}

const ENTRY = {
  queueEntryId: 'qe-1',
  action: 'call',
  revision: 1,
  token: 'T-3F2A9C-004',
  doctorName: 'Rahim Uddin',
  // A room is required for Bangla: the room-less Bangla sentence is unapproved
  // (§18 O-3), so every Bangla fixture carries one.
  room: '305',
};

test('a controller needs a speech adapter', () => {
  assert.throws(() => createAnnouncementController({}), TypeError);
});

test('a disabled facility attempts nothing at all', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, enabled: false });
  const result = await controller.announce(ENTRY, { source: 'event' });
  assert.equal(result.status, 'disabled');
  assert.equal(adapter.calls.speak.length, 0);
  controller.dispose();
});

test('an unsupported browser is reported as unavailable, not thrown', async () => {
  const controller = createAnnouncementController({ adapter: fakeAdapter({ supported: false }) });
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, OUTCOME.UNAVAILABLE);
  assert.equal(result.reason, 'unsupported');
  assert.equal(controller.getState().capability, 'unsupported');
  controller.dispose();
});

test('the same queue event is spoken once', async () => {
  const time = clock();
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, now: time.now, dedupeWindowMs: 5000 });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.COMPLETED);
  time.advance(1000);
  assert.equal((await controller.announce(ENTRY)).status, 'duplicate');
  assert.equal(adapter.calls.speak.length, 1, 'the second attempt never reaches the engine');
  controller.dispose();
});

test('the same event is announced again after the suppression window', async () => {
  const time = clock();
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, now: time.now, dedupeWindowMs: 5000 });

  await controller.announce(ENTRY);
  time.advance(6000);
  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.COMPLETED);
  assert.equal(adapter.calls.speak.length, 2);
  controller.dispose();
});

test('a different event is never suppressed', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, dedupeWindowMs: 5000 });
  await controller.announce(ENTRY);
  await controller.announce({ ...ENTRY, revision: 2 });
  await controller.announce({ ...ENTRY, queueEntryId: 'qe-2' });
  assert.equal(adapter.calls.speak.length, 3);
  controller.dispose();
});

test('an operator repeat is deliberate and bypasses suppression', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, dedupeWindowMs: 5000 });
  await controller.announce(ENTRY, { source: 'operator', userGesture: true });
  await controller.announce(ENTRY, { source: 'operator', userGesture: true });
  assert.equal(adapter.calls.speak.length, 2);
  controller.dispose();
});

test('a blocked browser is not hammered, but a new gesture may recover it', async () => {
  const adapter = fakeAdapter({ statuses: [OUTCOME.BLOCKED, OUTCOME.COMPLETED] });
  const controller = createAnnouncementController({ adapter, dedupeWindowMs: 0 });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.BLOCKED);
  assert.equal(controller.getState().activation, ACTIVATION.BLOCKED);

  // No gesture: the event is recorded as needing activation and audio is untouched.
  assert.equal((await controller.announce({ ...ENTRY, revision: 2 })).status, 'needs_activation');
  assert.equal(adapter.calls.speak.length, 1);

  // A click may retry, and success clears the blocked state.
  const recovered = await controller.announce({ ...ENTRY, revision: 3 }, { userGesture: true });
  assert.equal(recovered.status, OUTCOME.COMPLETED);
  assert.equal(controller.getState().activation, ACTIVATION.GRANTED);
  assert.equal(controller.getState().requiresActivation, false);
  controller.dispose();
});

test('overlapping playback is surfaced as busy, never overlapped', async () => {
  const adapter = fakeAdapter({ statuses: [OUTCOME.BUSY] });
  const controller = createAnnouncementController({ adapter, dedupeWindowMs: 0 });
  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.BUSY);
  assert.equal(controller.getState().last.status, OUTCOME.BUSY);
  controller.dispose();
});

test('activating audio is a gesture, and reports what the browser did', async () => {
  const granted = createAnnouncementController({ adapter: fakeAdapter() });
  assert.equal((await granted.activate()).status, OUTCOME.COMPLETED);
  assert.equal(granted.getState().activation, ACTIVATION.GRANTED);
  assert.equal(granted.getState().last, null, 'priming is not an announcement');
  granted.dispose();

  const blocked = createAnnouncementController({
    adapter: fakeAdapter({ statuses: [OUTCOME.BLOCKED] }),
  });
  assert.equal((await blocked.activate()).status, OUTCOME.BLOCKED);
  assert.equal(blocked.getState().activation, ACTIVATION.BLOCKED);
  assert.equal(blocked.getState().requiresActivation, true);
  blocked.dispose();
});

test('content that cannot be spoken is skipped with a reason', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter });

  const noToken = await controller.announce({ queueEntryId: 'qe-9', doctorName: 'Rahim Uddin', room: '305' });
  assert.equal(noToken.status, 'skipped');
  assert.equal(noToken.reason, 'unspeakable_token');

  const badLang = await controller.announce(ENTRY, { language: 'fr' });
  assert.equal(badLang.status, OUTCOME.COMPLETED, 'an unknown language falls back to the configured one');

  assert.equal(adapter.calls.speak.length, 1);
  controller.dispose();
});

test('a Bangla entry without a room is skipped, not spoken half a sentence', async () => {
  // §18 O-3: the room-less Bangla wording is unapproved, so the controller
  // refuses it and says why instead of speaking "…, আসুন।".
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter });
  const noRoom = { ...ENTRY };
  delete noRoom.room;
  const result = await controller.announce(noRoom);
  assert.equal(result.status, 'skipped');
  assert.equal(result.reason, 'no_room');
  assert.equal(adapter.calls.speak.length, 0);

  // The same entry is speakable in English, which has an approved sentence.
  const english = await controller.announce(noRoom, { language: 'en' });
  assert.equal(english.status, OUTCOME.COMPLETED);
  assert.equal(adapter.calls.speak[0].text,
    'Token number 4, Dr. Rahim Uddin, please proceed.');
  controller.dispose();
});

test('an exploding engine is a failed outcome, not an exception', async () => {
  const controller = createAnnouncementController({ adapter: fakeAdapter({ throws: true }) });
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, OUTCOME.FAILED);
  assert.equal(result.reason, 'adapter_threw');
  controller.dispose();
});

test('outcomes are observable without leaking the spoken text', async () => {
  const lines = [];
  const controller = createAnnouncementController({
    adapter: fakeAdapter(),
    logger: (line) => lines.push(line),
  });
  await controller.announce(ENTRY);
  assert.equal(lines.length, 1);
  assert.equal(lines[0].event, 'queue.announcement');
  assert.equal(lines[0].outcome, OUTCOME.COMPLETED);
  assert.equal(lines[0].language, 'bn');
  assert.equal(lines[0].queueEntryId, 'entry:qe-1:call:1');
  // The record identifies the event; it never carries the sentence or a patient.
  assert.deepEqual(Object.keys(lines[0]).sort(), ['event', 'language', 'outcome', 'queueEntryId', 'reason']);
  controller.dispose();
});

test('state changes are published to subscribers, including voice arrivals', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter });
  const seen = [];
  const unsubscribe = controller.subscribe((state) => seen.push(state.last ? state.last.status : 'initial'));
  controller.start();
  assert.equal(adapter.calls.subscribe, 1, 'the browser voice list is being watched');

  await controller.announce(ENTRY);
  assert.deepEqual(seen, ['initial', OUTCOME.COMPLETED]);

  unsubscribe();
  controller.stop();
  assert.equal(adapter.calls.subscribe, 0, 'the voice listener is released');

  await controller.announce({ ...ENTRY, revision: 2 });
  assert.equal(seen.length, 2, 'a removed subscriber is not called again');
  controller.dispose();
});

test('the language and the facility switch can be changed at runtime', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, language: 'bn' });

  controller.setLanguage('en');
  assert.equal(controller.getState().language, 'en');
  await controller.announce(ENTRY);
  assert.equal(adapter.calls.speak[0].opts.language, 'en');
  assert.ok(adapter.calls.speak[0].text.startsWith('Token number 4,'));

  controller.setEnabled(false);
  assert.equal((await controller.announce({ ...ENTRY, revision: 2 })).status, 'disabled');
  controller.dispose();
});

/* --- F3: the store behind suppression, end to end ------------------------- */

test("a re-delivery of an earlier event is still suppressed after a newer one", async () => {
  // F3.3(1): the old single slot forgot A as soon as B arrived.
  const time = clock();
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({
    adapter, now: time.now, dedupe: { completedTtlMs: 60000 },
  });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.COMPLETED);
  assert.equal((await controller.announce({ ...ENTRY, queueEntryId: 'qe-2' })).status, OUTCOME.COMPLETED);
  time.advance(1000);
  const again = await controller.announce(ENTRY);
  assert.equal(again.status, 'duplicate');
  assert.equal(again.reason, 'already_completed');
  assert.equal(adapter.calls.speak.length, 2, 'only the two distinct events were spoken');
  controller.dispose();
});

test('a browser-blocked event is called once the operator enables audio', async () => {
  // F3.3(2): a refusal must not consume the event.
  const adapter = fakeAdapter({ statuses: [OUTCOME.BLOCKED, OUTCOME.COMPLETED, OUTCOME.COMPLETED] });
  const controller = createAnnouncementController({
    adapter, now: clock().now, dedupe: { blockedTtlMs: 60000 },
  });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.BLOCKED);
  // The same event, re-delivered before activation, is not attempted again.
  assert.equal((await controller.announce(ENTRY)).status, 'needs_activation');
  assert.equal(adapter.calls.speak.length, 1);

  // The enabling gesture primes and then replays the blocked event exactly once.
  assert.equal((await controller.activate()).status, OUTCOME.COMPLETED);
  assert.equal(adapter.calls.speak.length, 3, 'prime + one replay');
  assert.equal(controller.getState().last.status, OUTCOME.COMPLETED);

  // The replay satisfied the event: a further delivery is a duplicate.
  assert.equal((await controller.announce(ENTRY)).status, 'duplicate');
  controller.dispose();
});

test('a failed announcement is retried, then given up on', async () => {
  // F3.3(3): a failure is neither "announced" nor retried forever.
  const time = clock();
  const adapter = fakeAdapter({ statuses: [OUTCOME.FAILED] });
  const controller = createAnnouncementController({
    adapter, now: time.now, dedupe: { maxAttempts: 2, baseRetryMs: 1000, maxRetryMs: 2000 },
  });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.FAILED);
  const tooSoon = await controller.announce(ENTRY);
  assert.equal(tooSoon.status, 'retry_wait', 'no tight retry loop');
  assert.equal(adapter.calls.speak.length, 1);

  time.advance(1000);
  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.FAILED);
  const spent = await controller.announce(ENTRY, { userGesture: true });
  assert.equal(spent.status, 'exhausted');
  assert.equal(adapter.calls.speak.length, 2, 'the budget is two attempts');
  controller.dispose();
});

test('an unheard event is not remembered: busy and unavailable both retry', async () => {
  const adapter = fakeAdapter({ statuses: [OUTCOME.BUSY, OUTCOME.UNAVAILABLE, OUTCOME.COMPLETED] });
  const controller = createAnnouncementController({
    adapter, now: clock().now, dedupe: { completedTtlMs: 60000, baseRetryMs: 0 },
  });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.BUSY);
  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.UNAVAILABLE);
  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.COMPLETED);
  assert.equal(adapter.calls.speak.length, 3);
  assert.equal(controller.getState().dedupe.keys, 1, 'only the completed attempt is remembered');
  controller.dispose();
});

test('suppression is scoped to events: an operator repeat is never blocked', async () => {
  const time = clock();
  const adapter = fakeAdapter({ statuses: [OUTCOME.FAILED] });
  const controller = createAnnouncementController({
    adapter, now: time.now, dedupe: { maxAttempts: 1, baseRetryMs: 0, maxRetryMs: 0 },
  });

  assert.equal((await controller.announce(ENTRY)).status, OUTCOME.FAILED);
  // The budget is spent for automatic delivery, but a deliberate repeat is the
  // operator's decision and must still reach the engine.
  assert.equal((await controller.announce(ENTRY)).status, 'exhausted');
  assert.equal((await controller.announce(ENTRY, { source: 'operator', userGesture: true })).status,
    OUTCOME.FAILED);
  assert.equal(adapter.calls.speak.length, 2);
  controller.dispose();
});
