/* QUE-006 / W2 — queue integration: transport choice and the call transition.
 *
 * Two things are proven here:
 *   1. the controller plays the configured transport and reports only real
 *      outcomes (completed ⇒ spoken, anything else ⇒ failed/busy/cancelled);
 *   2. the page-level seam that turns a queue entry becoming `called` into an
 *      announcement is a pure transition rule, and the page never awaits it.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  ACTIVATION,
  createAnnouncementController,
} from '../lib/announcements/controller.js';
import { createPrerecordedPlayer, PLAYBACK } from '../lib/announcements/prerecorded-audio.js';
import { trackCalledTransitions } from '../lib/announcements/queue-transitions.js';
import { createCallAnnouncer } from '../lib/announcements/call-announcer.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const MANIFEST = JSON.parse(
  readFileSync(join(HERE, '..', 'public', 'audio', 'manifest.json'), 'utf8'));

function fakeAdapter(supported = true) {
  const calls = { speak: [], cancel: 0 };
  return {
    calls,
    isSupported: () => supported,
    isSpeaking: () => false,
    capability: () => ({ status: 'ready', voice: { voiceLang: 'bn-BD', name: 'Fake' }, voices: [] }),
    async speak(text, opts) { calls.speak.push({ text, opts }); return { status: 'spoken' }; },
    cancel() { calls.cancel += 1; },
    subscribeVoices() { return () => {}; },
  };
}

function fakePlayer(outcomes = [{ status: PLAYBACK.COMPLETED }], capability = 'ready') {
  const calls = { play: [], prime: 0, cancel: 0 };
  const queue = outcomes.slice();
  return {
    calls,
    async play(payload) {
      calls.play.push(payload);
      const next = queue.length > 1 ? queue.shift() : queue[0];
      return typeof next === 'function' ? next() : next;
    },
    async prime() { calls.prime += 1; return { status: 'primed' }; },
    cancel() { calls.cancel += 1; },
    getState() { return { playing: false, packId: 'platform.en.draft.v1', version: 1 }; },
    capability() { return { status: capability, packId: 'platform.en.draft.v1', version: 1, assets: 28 }; },
  };
}

const ENTRY = { queueEntryId: 'qe-1', action: 'call', token: 'T-3F2A9C-004' };

test('W2 prerecorded is the default transport when a player is supplied', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer();
  const controller = createAnnouncementController({ adapter, player, language: 'bn' });
  assert.equal(controller.getState().transport, 'prerecorded');
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, 'spoken');
  assert.equal(result.completed, true);
  assert.equal(adapter.calls.speak.length, 0, 'the browser voice list is not consulted');
  assert.equal(player.calls.play.length, 1);
  assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: undefined });
  controller.dispose();
});

test('W2 a playback failure is reported, never thrown, never spoken', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer([{ status: PLAYBACK.FAILED, reason: 'missing_asset', missing: ['en.digit.4'] }]);
  const controller = createAnnouncementController({ adapter, player });
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, 'failed');
  assert.equal(result.reason, 'missing_asset');
  assert.deepEqual(result.missing, ['en.digit.4']);
  assert.equal(controller.getState().last.status, 'failed');
  assert.equal(controller.getState().activation, ACTIVATION.UNKNOWN);
  controller.dispose();
});

test('W2 busy and cancelled are passed through unchanged', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer([{ status: PLAYBACK.BUSY }, { status: PLAYBACK.CANCELLED }]);
  const controller = createAnnouncementController({ adapter, player });
  assert.equal((await controller.announce({ ...ENTRY, queueEntryId: 'a' })).status, 'busy');
  assert.equal((await controller.announce({ ...ENTRY, queueEntryId: 'b' })).status, 'cancelled');
  controller.dispose();
});

test('W2 a blocked browser is not hammered without a fresh gesture', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer([{ status: PLAYBACK.FAILED, reason: 'blocked' },
    { status: PLAYBACK.COMPLETED }]);
  const controller = createAnnouncementController({ adapter, player });
  const blocked = await controller.announce({ ...ENTRY, queueEntryId: 'a' });
  assert.equal(blocked.status, 'failed');
  assert.equal(controller.getState().activation, ACTIVATION.BLOCKED);

  const quiet = await controller.announce({ ...ENTRY, queueEntryId: 'b' }, { source: 'event' });
  assert.equal(quiet.status, 'needs_activation');
  assert.equal(player.calls.play.length, 1, 'no second attempt without a gesture');

  const gesture = await controller.announce({ ...ENTRY, queueEntryId: 'c' }, { userGesture: true });
  assert.equal(gesture.status, 'spoken');
  assert.equal(player.calls.play.length, 2);
  controller.dispose();
});

test('W2 activate() unlocks by priming the pack, not by speaking', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer();
  const controller = createAnnouncementController({ adapter, player });
  const primed = await controller.activate();
  assert.equal(primed.status, 'primed');
  assert.equal(player.calls.prime, 1);
  assert.equal(adapter.calls.speak.length, 0);
  assert.equal(controller.getState().activation, ACTIVATION.GRANTED);
  assert.equal(controller.getState().last, null, 'a prime is not an announcement');
  controller.dispose();
});

test('W2 activate() with no silent clip grants nothing', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer();
  player.prime = async () => ({ status: 'unavailable', reason: 'no_prime_asset' });
  const controller = createAnnouncementController({ adapter, player });
  const primed = await controller.activate();
  assert.equal(primed.status, 'unavailable');
  assert.equal(controller.getState().activation, ACTIVATION.UNKNOWN);
  controller.dispose();
});

test('W2 an explicit speech strategy keeps the browser mechanism', async () => {
  const adapter = fakeAdapter();
  const player = fakePlayer();
  const controller = createAnnouncementController({ adapter, player, strategy: 'speech' });
  assert.equal(controller.getState().transport, 'speech');
  const result = await controller.announce(ENTRY);
  assert.equal(result.status, 'spoken');
  assert.equal(adapter.calls.speak.length, 1);
  assert.equal(player.calls.play.length, 0);
  controller.dispose();
});

test('W2 asking for prerecorded without a player is refused', () => {
  assert.throws(() => createAnnouncementController({
    adapter: fakeAdapter(), strategy: 'prerecorded',
  }), TypeError);
});

test('W2 capability follows the pack, not the browser voice list', async () => {
  const adapter = fakeAdapter(false); // no browser speech at all
  const pending = fakePlayer([{ status: PLAYBACK.COMPLETED }], 'pending');
  const loading = createAnnouncementController({ adapter, player: pending });
  assert.equal(loading.getState().capability, 'pending_voices');
  assert.equal(loading.getState().supported, true);
  loading.dispose();

  const empty = fakePlayer([{ status: PLAYBACK.COMPLETED }], 'no_voice');
  const missing = createAnnouncementController({ adapter, player: empty });
  assert.equal(missing.getState().capability, 'no_voice');
  missing.dispose();

  const ready = fakePlayer([{ status: PLAYBACK.COMPLETED }], 'ready');
  const player = createAnnouncementController({ adapter, player: ready });
  const result = await player.announce(ENTRY);
  assert.equal(result.status, 'spoken', 'prerecorded playback does not need browser voices');
  player.dispose();
});

test('W2 cancel() reaches the player', () => {
  const adapter = fakeAdapter();
  const player = fakePlayer();
  const controller = createAnnouncementController({ adapter, player });
  controller.cancel();
  assert.equal(player.calls.cancel, 1);
  assert.equal(adapter.calls.cancel, 0);
  controller.dispose();
});

test('W2 end to end: spoken is reported only when the final clip ends', async () => {
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

    emit(name) { (this.listeners.get(name) || []).slice().forEach((fn) => fn({ type: name })); }

    play() { this.paused = false; return Promise.resolve(); }

    pause() { if (this.paused) return; this.paused = true; this.emit('pause'); }

    end() { this.paused = true; this.emit('ended'); }
  }
  const settle = () => new Promise((resolve) => setImmediate(resolve));

  const pack = {
    id: 'platform.en.draft.v1', language: 'en', version: 1, basePath: '/audio', manifest: MANIFEST,
  };
  const player = createPrerecordedPlayer({ pack, audioFactory: (src) => new FakeAudio(src) });
  const controller = createAnnouncementController({ adapter: fakeAdapter(), player, language: 'en' });

  let settled = null;
  const pending = controller.announce({ queueEntryId: 'qe-9', token: 'T-1' })
    .then((result) => { settled = result; return result; });

  await settle();
  assert.equal(created.length, 1);
  created[0].end();
  await settle();
  assert.equal(settled, null, 'the first clip is not the announcement');
  created[1].end();
  await settle();
  assert.equal(settled, null);
  created[2].end();

  const result = await pending;
  assert.equal(result.status, 'spoken');
  assert.equal(result.completed, true);
  assert.equal(controller.getState().last.reason, '');
  assert.match(controller.getState().last.text, /^Token number 1/);
  controller.dispose();
});

test('W2 only a transition into `called` is announced', () => {
  const first = trackCalledTransitions(new Map(), [
    { id: 'a', status: 'called' },
    { id: 'b', status: 'waiting' },
  ]);
  assert.deepEqual(first.transitioned, [], 'entries already called on load stay silent');
  assert.equal(first.next.get('b'), 'waiting');

  const second = trackCalledTransitions(first.next, [
    { id: 'a', status: 'called' },
    { id: 'b', status: 'called' },
  ]);
  assert.deepEqual(second.transitioned.map((entry) => entry.id), ['b']);

  const third = trackCalledTransitions(second.next, [
    { id: 'a', status: 'called' },
    { id: 'b', status: 'called' },
  ]);
  assert.deepEqual(third.transitioned, [], 'an unchanged status is not a new event');
});

test('W2 transitions survive entries leaving and returning to the list', () => {
  let tracker = trackCalledTransitions(new Map(), [{ id: 'a', status: 'waiting' }]).next;
  tracker = trackCalledTransitions(tracker, []).next; // filtered out
  const back = trackCalledTransitions(tracker, [{ id: 'a', status: 'called' }]);
  assert.deepEqual(back.transitioned, [], 'a returning entry is seeded, not announced');
  assert.equal(back.next.get('a'), 'called');
});

test('W2 the transition rule tolerates junk', () => {
  assert.deepEqual(trackCalledTransitions(null, null), { next: new Map(), transitioned: [] });
  const result = trackCalledTransitions(new Map(), [null, {}, { id: 5 }, { id: 'x' }]);
  assert.deepEqual(result.transitioned, []);
  assert.equal(result.next.get('x'), '');
});

test('W2 the queue page wires the call seam and never awaits it', () => {
  const page = readFileSync(join(HERE, '..', 'pages', 'queue.js'), 'utf8');
  assert.match(page, /trackCalledTransitions\(calledTracker\.current, entries\)/);
  assert.match(page, /transitioned\.forEach\(\(entry\) => announceOnCall\(entry\)\)/);
  assert.equal(/await\s+announceOnCall/.test(page), false,
    'the call announcement is fire-and-forget');

  const start = page.indexOf('const announceOnCall');
  assert.ok(start > 0, 'the call seam exists');
  const body = page.slice(start, page.indexOf('\n  };', start))
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/[^\n]*/g, '');
  assert.equal(/await/.test(body), false, 'nothing in the seam waits for audio');
  assert.equal(/apiFetch/.test(body), false, 'announcing never writes queue state');
  assert.match(body, /source: 'event'/, 'an automatic announcement is marked as an event');
});

/* ---------------------------------------------------------------------------
 * QUE-006 / W2 — claim → play → report, and the page wiring around it.
 *
 * The tests below use the *real* controller (with a fake transport, as above)
 * and the real announcer, so the order of the three server-visible facts is
 * proven rather than asserted from source: the claim is made before anything
 * plays, the clip is played by the claim's owner only, and the outcome is
 * reported afterwards. The two source-level tests then pin the page and panel
 * wiring, which is JSX and therefore not importable in this suite.
 * ------------------------------------------------------------------------- */
test('W2 the claim, the clip and the record happen in that order', async () => {
  const order = [];
  const posts = [];
  const player = fakePlayer([{ status: PLAYBACK.COMPLETED }]);
  const playClip = player.play.bind(player);
  player.play = async (payload) => { order.push('play'); return playClip(payload); };

  const controller = createAnnouncementController({ adapter: fakeAdapter(), player, language: 'en' });
  const announcer = createCallAnnouncer({
    announce: (payload, opts) => controller.announce(payload, opts),
    describe: () => {
      const state = controller.getState();
      return {
        enabled: state.enabled,
        language: state.language,
        voicePackId: state.packId,
        voicePackVersion: state.packVersion,
        transport: state.transport,
      };
    },
    post: async (path, body) => {
      const isReport = path.endsWith('/outcome');
      posts.push({ path, body });
      order.push(isReport ? 'report' : 'claim');
      return isReport ? { settled: true } : { claimed: true, delivery_id: 'dlv-1' };
    },
  });

  const result = await announcer.announceCall({
    id: 'qe-1',
    token: 'T-3F2A9C-004',
    call_event_id: 'qce:1:4',
    call_event_at: new Date().toISOString(),
  });

  assert.deepEqual(order, ['claim', 'play', 'report'],
    'the call is claimed before it is spoken, and reported after');

  assert.equal(posts[0].path, '/api/v1/queue/qe-1/announcement');
  assert.equal(posts[0].body.event_id, 'qce:1:4', 'the server identity is what is claimed');
  assert.equal(posts[0].body.voice_pack_id, controller.getState().packId,
    'the record can answer which pack announced this');
  assert.equal(posts[0].body.transport, 'prerecorded');
  assert.equal(posts[0].body.organisation_id, undefined, 'scope is never sent by the client');

  assert.equal(posts[1].path, '/api/v1/queue/announcements/dlv-1/outcome');
  assert.deepEqual(posts[1].body, { outcome: 'completed', reason: '' },
    'only a confirmed `ended` is recorded as completed');

  assert.equal(result.status, 'announced');
  assert.equal(result.deliveryId, 'dlv-1');
  controller.dispose();
});

test('W2 one call, two terminals: only the claim owner speaks', async () => {
  const claimedEvents = new Set();
  const terminal = () => {
    const player = fakePlayer([{ status: PLAYBACK.COMPLETED }]);
    const controller = createAnnouncementController({ adapter: fakeAdapter(), player });
    const posts = [];
    const announcer = createCallAnnouncer({
      announce: (payload, opts) => controller.announce(payload, opts),
      describe: () => controller.getState(),
      post: async (path, body) => {
        posts.push({ path, body });
        if (path.endsWith('/outcome')) return { settled: true };
        if (claimedEvents.has(body.event_id)) return { claimed: false, reason: 'duplicate_event' };
        claimedEvents.add(body.event_id);
        return { claimed: true, delivery_id: 'dlv-' + claimedEvents.size };
      },
    });
    return { controller, player, posts, announcer };
  };

  const entry = {
    id: 'qe-1', token: 'T-1', call_event_id: 'qce:1:4', call_event_at: new Date().toISOString(),
  };
  const first = terminal();
  const second = terminal();

  const owned = await first.announcer.announceCall(entry, { source: 'event' });
  const foreign = await second.announcer.announceCall(entry, { source: 'event' });

  assert.equal(owned.status, 'announced');
  assert.equal(first.player.calls.play.length, 1);
  assert.equal(second.player.calls.play.length, 0, 'the losing terminal stays silent');
  assert.equal(foreign.status, 'skipped');
  assert.equal(foreign.reason, 'duplicate_event',
    'the server names the duplicate, and it is not an error');
  assert.equal(second.posts.length, 1, 'a refused claim writes nothing else');
  first.controller.dispose();
  second.controller.dispose();
});


test('W2 the page hands over the server identity and shows the quiet note', () => {
  const page = readFileSync(join(HERE, '..', 'pages', 'queue.js'), 'utf8');
  const panel = readFileSync(
    join(HERE, '..', 'components', 'queue', 'QueueAnnouncements.js'), 'utf8');

  // The operator's own repeat carries the server identity, and is marked as a
  // deliberate repeat: it is not claimed, so it is neither suppressed nor
  // recorded as a second delivery.
  assert.match(page, /eventId: entry\.call_event_id/);
  assert.match(page, /\{ source: 'operator', userGesture: true \}/);

  // The transition seam delegates to the announcer (claim → play → report) and
  // hands the result to the panel.
  assert.match(page, /callAnnouncer\.announceCall\(entry, \{ source: 'event' \}\)\.then\(setDelivery\)/,
    'the call seam claims before it plays');
  assert.match(page, /<QueueAnnouncements[^>]*delivery=\{delivery\}/,
    'the panel is told how the claim ended');

  // The panel turns the three "someone else has this call" reasons into one
  // muted sentence, and renders nothing for anything else.
  assert.match(panel, /reason === 'duplicate_event' \|\| reason === 'not_owner' \|\| reason === 'claim_rejected'/);
  assert.match(panel, /return t\('announceElsewhere'\)/);
  assert.match(panel, /\{deliveryNote\(delivery\) && \(\s*<p className="muted">/,
    'the note is muted, never an error surface');
});

test('W2 the refresh is a visible-tab timer that cannot blank the list', () => {
  const page = readFileSync(join(HERE, '..', 'pages', 'queue.js'), 'utf8');

  assert.match(page, /createQueueRefresher\(\{/);
  assert.match(page, /refresh: \(\) => loadQueueRef\.current\(\{ quiet: true \}\)/,
    'a background refresh does not raise the spinner');
  assert.match(page, /onError: \(e\) => setError\('Queue refresh failed: '/,
    'a failed refresh is reported on the page error surface');
  assert.match(page, /return \(\) => refresher\.stop\(\)/,
    'leaving the page stops the timer and its listeners');

  // The quiet path must not clear the list it could not reload.
  const start = page.indexOf('const loadQueue = (opts = {}) => {');
  assert.ok(start > 0, 'the loader exists');
  const body = page.slice(start, page.indexOf('\n  };', start));
  assert.match(body, /const quiet = opts\.quiet === true;/);
  assert.equal(/if \(quiet\)[^\n]*setEntries\(\[\]\)/.test(body), false,
    'a quiet refresh never empties the previous entries');
});

