/* QUE-006 / OD-1 — the announcement controller.
 *
 * These assertions fix the decisions that must not drift: the facility switch,
 * duplicate suppression, one-at-a-time playback, user activation, and the fact
 * that no outcome ever throws into the queue page.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ACTIVATION,
  createAnnouncementController,
} from '../lib/announcements/controller.js';

function fakeAdapter(options = {}) {
  const statuses = options.statuses ? options.statuses.slice() : ['spoken'];
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

test('an unsupported browser is reported, not thrown', async () => {
  const controller = createAnnouncementController({ adapter: fakeAdapter({ supported: false }) });
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, 'unsupported');
  assert.equal(controller.getState().capability, 'unsupported');
  controller.dispose();
});

test('the same queue event is spoken once', async () => {
  const time = clock();
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter, now: time.now, dedupeWindowMs: 5000 });

  assert.equal((await controller.announce(ENTRY)).status, 'spoken');
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
  assert.equal((await controller.announce(ENTRY)).status, 'spoken');
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
  const adapter = fakeAdapter({ statuses: ['blocked', 'spoken'] });
  const controller = createAnnouncementController({ adapter, dedupeWindowMs: 0 });

  assert.equal((await controller.announce(ENTRY)).status, 'blocked');
  assert.equal(controller.getState().activation, ACTIVATION.BLOCKED);

  // No gesture: the event is recorded as needing activation and audio is untouched.
  assert.equal((await controller.announce({ ...ENTRY, revision: 2 })).status, 'needs_activation');
  assert.equal(adapter.calls.speak.length, 1);

  // A click may retry, and success clears the blocked state.
  const recovered = await controller.announce({ ...ENTRY, revision: 3 }, { userGesture: true });
  assert.equal(recovered.status, 'spoken');
  assert.equal(controller.getState().activation, ACTIVATION.GRANTED);
  assert.equal(controller.getState().requiresActivation, false);
  controller.dispose();
});

test('overlapping playback is surfaced as busy, never overlapped', async () => {
  const adapter = fakeAdapter({ statuses: ['busy'] });
  const controller = createAnnouncementController({ adapter, dedupeWindowMs: 0 });
  assert.equal((await controller.announce(ENTRY)).status, 'busy');
  assert.equal(controller.getState().last.status, 'busy');
  controller.dispose();
});

test('activating audio is a gesture, and reports what the browser did', async () => {
  const granted = createAnnouncementController({ adapter: fakeAdapter({ statuses: ['spoken'] }) });
  assert.equal((await granted.activate()).status, 'spoken');
  assert.equal(granted.getState().activation, ACTIVATION.GRANTED);
  assert.equal(granted.getState().last, null, 'priming is not an announcement');
  granted.dispose();

  const blocked = createAnnouncementController({ adapter: fakeAdapter({ statuses: ['blocked'] }) });
  assert.equal((await blocked.activate()).status, 'blocked');
  assert.equal(blocked.getState().activation, ACTIVATION.BLOCKED);
  assert.equal(blocked.getState().requiresActivation, true);
  blocked.dispose();
});

test('content that cannot be spoken is skipped with a reason', async () => {
  const adapter = fakeAdapter();
  const controller = createAnnouncementController({ adapter });

  const noToken = await controller.announce({ queueEntryId: 'qe-9', doctorName: 'Rahim Uddin' });
  assert.equal(noToken.status, 'skipped');
  assert.equal(noToken.reason, 'unspeakable_token');

  const badLang = await controller.announce(ENTRY, { language: 'fr' });
  assert.equal(badLang.status, 'spoken', 'an unknown language falls back to the configured one');

  assert.equal(adapter.calls.speak.length, 1);
  controller.dispose();
});

test('an exploding engine is an error outcome, not an exception', async () => {
  const controller = createAnnouncementController({ adapter: fakeAdapter({ throws: true }) });
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, 'error');
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
  assert.equal(lines[0].outcome, 'spoken');
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
  assert.deepEqual(seen, ['initial', 'spoken']);

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
