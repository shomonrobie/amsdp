/* QUE-006 / W2 — the announcement delivery protocol and its announcer.
 *
 * The queue announcement is only reliable if three things are true, so each is
 * pinned separately here:
 *
 *   1. **identity comes from the server.** `call_event_id` is derived from
 *      `status_history`; the browser never manufactures one, and an entry
 *      without one is never announced. This is what makes a recall a new event
 *      rather than a suppressed repeat.
 *   2. **the claim decides who speaks.** The first terminal to claim plays; the
 *      rest are told `claimed: false` and stay silent — the duplicate protection
 *      survives two browsers, two tabs and a reload.
 *   3. **the recorded outcome is what the browser observed.** `completed` only
 *      when the final clip ended; a started-but-unconfirmed clip is `failed`.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DELIVERY_OUTCOME,
  MAX_EVENT_ID_LENGTH,
  MAX_REASON_LENGTH,
  OUTCOME_VALUES,
  claimRequest,
  classifyAnnouncement,
  deliveryPath,
  eventIdOf,
  isFreshCallEvent,
  outcomeRequest,
} from '../lib/announcements/delivery.js';
import { createCallAnnouncer } from '../lib/announcements/call-announcer.js';

const AT = '2026-11-21T09:15:00.000Z';
const NOW = Date.parse(AT) + 1000; // one second after the call

function calledEntry(overrides = {}) {
  return {
    id: 'qe-1',
    status: 'called',
    token: 'T-3F2A9C-004',
    call_event_id: 'qce:1:4',
    call_event_at: AT,
    ...overrides,
  };
}

const STATE = {
  enabled: true,
  language: 'bn',
  // The names `describe()` returns: the controller state is mapped to these by
  // the page, so this fixture is what the announcer actually receives.
  voicePackId: 'platform.bn.draft.v1',
  voicePackVersion: 1,
  transport: 'prerecorded',
};

/** A network double that records every request and answers by path. */
function fakePost(answers = {}) {
  const calls = [];
  const post = async (path, body) => {
    calls.push({ path, body });
    const answer = answers[path];
    if (answer instanceof Error) throw answer;
    return typeof answer === 'function' ? answer(path, body) : (answer || {});
  };
  return { calls, post };
}

/** A controller double: records the payloads it was asked to play. */
function fakeAnnounce(result = { status: 'completed', completed: true }) {
  const calls = [];
  const announce = async (payload, opts) => {
    calls.push({ payload, opts });
    return typeof result === 'function' ? result(payload, opts) : result;
  };
  return { calls, announce };
}

test('W2 the event identity is the server id, never a local guess', () => {
  assert.equal(eventIdOf(calledEntry()), 'qce:1:4');
  assert.equal(eventIdOf(calledEntry({ call_event_id: '  qce:1:7  ' })), 'qce:1:7');
  assert.equal(eventIdOf(calledEntry({ call_event_id: '' })), '', 'an empty id is no id');
  assert.equal(eventIdOf(calledEntry({ call_event_id: 7 })), '', 'a number is not an id');
  assert.equal(eventIdOf(calledEntry({ call_event_id: undefined })), '');
  assert.equal(eventIdOf(null), '');
  assert.equal(eventIdOf({ status: 'called', token: 'T-1' }), '',
    'an entry from before the backend change is never announced');

  const long = 'qce:' + '9'.repeat(MAX_EVENT_ID_LENGTH * 2);
  assert.equal(eventIdOf({ call_event_id: long }).length, MAX_EVENT_ID_LENGTH);
});

test('W2 a recall is a new event; a repeated response is the same event', () => {
  // The server appends a history record per call, so the index — and therefore
  // the id — moves on with every recall of the same entry.
  assert.notEqual(eventIdOf({ call_event_id: 'qce:1:4' }),
    eventIdOf({ call_event_id: 'qce:1:6' }));
  assert.equal(eventIdOf({ call_event_id: 'qce:1:4' }),
    eventIdOf({ call_event_id: 'qce:1:4' }));
});


test('W2 the claim request carries the event and the voice that announced it', () => {
  assert.equal(claimRequest({ id: 'qe-1' }, STATE), null, 'no event id, no claim');

  const request = claimRequest(calledEntry(), STATE);
  assert.equal(request.path, '/api/v1/queue/qe-1/announcement');
  assert.deepEqual(request.body, {
    event_id: 'qce:1:4',
    language: 'bn',
    voice_pack_id: 'platform.bn.draft.v1',
    voice_pack_version: 1,
    transport: 'prerecorded',
  });
  // Scope is derived server-side from the token: the request never names an
  // organisation, branch or actor.
  for (const key of ['organization_id', 'branch_id', 'actor_id', 'user_id']) {
    assert.equal(key in request.body, false, `the claim must not send ${key}`);
  }
});

test('W2 the claim request answers a half-known controller honestly', () => {
  const request = claimRequest(calledEntry(), {});
  assert.equal(request.body.language, 'bn', 'the facility default, not a guess');
  assert.equal(request.body.voice_pack_id, '');
  assert.equal(request.body.voice_pack_version, 0);
  assert.equal(request.body.transport, 'prerecorded');

  const speech = claimRequest(calledEntry(), { transport: 'speech', language: 'en', voicePackVersion: '2' });
  assert.equal(speech.body.transport, 'speech');
  assert.equal(speech.body.language, 'en');
  assert.equal(speech.body.voice_pack_version, 2, 'a numeric string is read as its number');
});

test('W2 the entry id and delivery id are encoded into their paths', () => {
  assert.equal(deliveryPath('qe/1 2'), '/api/v1/queue/qe%2F1%202/announcement');
  assert.equal(deliveryPath(42), '/api/v1/queue/42/announcement');
});

test('W2 the outcome request is only built from an outcome the server accepts', () => {
  assert.deepEqual(OUTCOME_VALUES, [
    'completed', 'failed', 'blocked', 'interrupted', 'skipped_busy', 'skipped_duplicate',
  ]);

  const request = outcomeRequest('dlv-1', DELIVERY_OUTCOME.COMPLETED);
  assert.equal(request.path, '/api/v1/queue/announcements/dlv-1/outcome');
  assert.deepEqual(request.body, { outcome: 'completed', reason: '' });

  assert.equal(outcomeRequest('dlv-1', 'spoken'), null,
    'a playback status is not a server outcome');
  assert.equal(outcomeRequest('dlv-1', 'requested'), null,
    '`requested` is the server fact; a client may not report it');
  assert.equal(outcomeRequest('', 'completed'), null);
  assert.equal(outcomeRequest('dlv-1', 'failed', 'x'.repeat(MAX_REASON_LENGTH * 2))
    .body.reason.length, MAX_REASON_LENGTH);
});

test('W2 only a fresh call event may be announced automatically', () => {
  const fresh = calledEntry();
  assert.equal(isFreshCallEvent(fresh, { now: NOW }), true);
  assert.equal(isFreshCallEvent(fresh, { now: NOW + 60000 }), true);
  assert.equal(isFreshCallEvent(fresh, { now: NOW + 121000 }), false,
    'a call from two minutes ago is history, not an instruction');
  assert.equal(isFreshCallEvent(fresh, { now: Date.parse(AT) - 4000 }), true,
    'a server clock a few seconds ahead is tolerated');
  assert.equal(isFreshCallEvent(fresh, { now: Date.parse(AT) - 60000 }), false,
    'a timestamp from the future is not evidence of a fresh call');
  assert.equal(isFreshCallEvent(fresh, { now: NOW, maxAgeMs: 0 }), false);
  assert.equal(isFreshCallEvent(fresh, { now: NOW, maxAgeMs: 5000 }), true);

  assert.equal(isFreshCallEvent({ call_event_at: '' }, { now: NOW }), false);
  assert.equal(isFreshCallEvent({ call_event_at: 'yesterday' }, { now: NOW }), false,
    'an unknown age is treated as stale');
  assert.equal(isFreshCallEvent({}, { now: NOW }), false);
  assert.equal(isFreshCallEvent(null, { now: NOW }), false);
});

test('W2 the recorded outcome is what the browser actually observed', () => {
  const cases = [
    [{ status: 'completed', completed: true }, 'completed', ''],
    [{ status: 'completed' }, 'failed', 'completion_unconfirmed'],
    [{ status: 'completed', completed: 'yes' }, 'failed', 'completion_unconfirmed'],
    [{ status: 'failed', reason: 'missing_asset' }, 'failed', 'missing_asset'],
    [{ status: 'failed', reason: 'blocked' }, 'blocked', 'blocked'],
    [{ status: 'blocked' }, 'blocked', ''],
    [{ status: 'needs_activation' }, 'blocked', 'needs_activation'],
    [{ status: 'disabled' }, 'blocked', 'disabled'],
    [{ status: 'interrupted' }, 'interrupted', ''],
    [{ status: 'busy' }, 'skipped_busy', ''],
    [{ status: 'duplicate' }, 'skipped_duplicate', ''],
    [{ status: 'skipped', reason: 'no_token' }, 'failed', 'content_no_token'],
    [{ status: 'unavailable' }, 'failed', 'status_unavailable'],
    // D-6 (2026-11-22): the pre-merge spellings are gone. A stale word is
    // recorded as an honest failure — never guessed into a delivery.
    [{ status: 'spoken', completed: true }, 'failed', 'status_spoken'],
    [{ status: 'cancelled' }, 'failed', 'status_cancelled'],
    [{}, 'failed', 'status_unknown'],
    [null, 'failed', 'status_unknown'],
  ];
  for (const [result, outcome, reason] of cases) {
    const settled = classifyAnnouncement(result);
    assert.equal(settled.outcome, outcome, JSON.stringify(result));
    assert.equal(settled.reason, reason, JSON.stringify(result));
    assert.ok(OUTCOME_VALUES.includes(settled.outcome), 'never an unknown outcome');
  }
});

test('W2 a claim is paid for before anything plays', async () => {
  const post = fakePost({ '/api/v1/queue/qe-1/announcement': { claimed: true, delivery_id: 'dlv-1' } });
  const play = fakeAnnounce();
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => STATE, post: post.post, now: () => NOW,
  });

  const result = await announcer.announceCall(calledEntry(), { source: 'event' });

  assert.equal(post.calls.length, 2, 'the claim, then the outcome');
  assert.equal(post.calls[0].path, '/api/v1/queue/qe-1/announcement');
  assert.equal(play.calls.length, 1, 'exactly one playback');
  assert.equal(play.calls[0].payload.action, 'call');
  assert.equal(play.calls[0].payload.eventId, 'qce:1:4',
    'the controller suppresses on the server id');
  assert.equal(play.calls[0].opts.source, 'event');
  assert.equal(post.calls[1].path, '/api/v1/queue/announcements/dlv-1/outcome');
  assert.deepEqual(post.calls[1].body, { outcome: 'completed', reason: '' });
  assert.equal(result.status, 'announced');
  assert.equal(result.outcome, 'completed');
  announcer.reset();
});

test('W2 the second terminal claims, is refused, and stays silent', async () => {
  const post = fakePost({
    '/api/v1/queue/qe-1/announcement': { claimed: false, reason: 'duplicate_event' },
  });
  const play = fakeAnnounce();
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => STATE, post: post.post, now: () => NOW,
  });

  const result = await announcer.announceCall(calledEntry(), { source: 'event' });

  assert.equal(play.calls.length, 0, 'the owner of the claim is the only terminal that speaks');
  assert.equal(post.calls.length, 1, 'a refused claim reports nothing back');
  assert.equal(result.status, 'skipped');
  assert.equal(result.reason, 'duplicate_event', 'shown as a quiet note, not an error');
  assert.equal(announcer.stateOf('qce:1:4'), 'foreign');
  announcer.reset();
});

test('W2 a claim the server refuses is not played and not reported', async () => {
  for (const status of [404, 409, 422]) {
    const post = fakePost({
      '/api/v1/queue/qe-1/announcement': Object.assign(new Error('no'), { status }),
    });
    const play = fakeAnnounce();
    const announcer = createCallAnnouncer({
      announce: play.announce, describe: () => STATE, post: post.post, now: () => NOW,
    });

    const result = await announcer.announceCall(calledEntry(), { source: 'event' });
    assert.equal(play.calls.length, 0, `${status}: nothing is spoken`);
    assert.equal(result.status, 'skipped');
    assert.equal(result.reason, 'claim_rejected');
    assert.equal(post.calls.length, 1, `${status}: no outcome is invented`);
    announcer.reset();
  }
});


test('W2 an entry without a server event id is never announced', async () => {
  const post = fakePost();
  const play = fakeAnnounce();
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => STATE, post: post.post, now: () => NOW,
  });

  const result = await announcer.announceCall({ id: 'qe-1', token: 'T-1', status: 'called' });

  assert.equal(result.status, 'skipped');
  assert.equal(result.reason, 'no_event_id');
  assert.equal(post.calls.length, 0, 'no claim is made for an unknown event');
  assert.equal(play.calls.length, 0);
});

test('W2 a hidden tab may catch up on state but never speaks an old call', async () => {
  const post = fakePost({ '/api/v1/queue/qe-1/announcement': { claimed: true, delivery_id: 'dlv-1' } });
  const play = fakeAnnounce();
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => STATE, post: post.post,
    now: () => NOW + 600000, // ten minutes later
  });

  const result = await announcer.announceCall(calledEntry(), { source: 'event' });

  assert.equal(result.reason, 'stale_event');
  assert.equal(post.calls.length, 0, 'a stale event is not even claimed');
  assert.equal(play.calls.length, 0, 'nobody is called from a stale list');

  // The operator's own repeat is a decision, not a notification: it is unaffected.
  const repeat = await announcer.announceCall(calledEntry(), { source: 'operator' });
  assert.equal(repeat.status, 'announced');
  assert.equal(play.calls.length, 1);
  assert.equal(play.calls[0].opts.source, 'operator');
  announcer.reset();
});

test('W2 the same event is announced once per tab even if the list re-renders', async () => {
  const post = fakePost({ '/api/v1/queue/qe-1/announcement': { claimed: true, delivery_id: 'dlv-1' } });
  const play = fakeAnnounce();
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => STATE, post: post.post, now: () => NOW,
  });

  await announcer.announceCall(calledEntry(), { source: 'event' });
  const second = await announcer.announceCall(calledEntry(), { source: 'event' });

  assert.equal(second.reason, 'duplicate_local');
  assert.equal(play.calls.length, 1);
  assert.equal(post.calls.length, 2, 'the second render adds no request at all');
  announcer.reset();
});

test('W2 a disabled facility claims nothing, so the record stays honest', async () => {
  const post = fakePost();
  const play = fakeAnnounce();
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => ({ ...STATE, enabled: false }),
    post: post.post, now: () => NOW,
  });

  const result = await announcer.announceCall(calledEntry(), { source: 'event' });

  assert.equal(result.reason, 'disabled');
  assert.equal(post.calls.length, 0);
  assert.equal(play.calls.length, 0);
});

test('W2 a playback failure is recorded, and never reaches the queue', async () => {
  const post = fakePost({ '/api/v1/queue/qe-1/announcement': { claimed: true, delivery_id: 'dlv-1' } });
  const play = fakeAnnounce({ status: 'failed', reason: 'missing_asset' });
  const announcer = createCallAnnouncer({
    announce: play.announce, describe: () => STATE, post: post.post, now: () => NOW,
  });

  const result = await announcer.announceCall(calledEntry(), { source: 'event' });

  assert.equal(result.status, 'announced', 'the claim was ours, so the outcome is recorded');
  assert.equal(result.outcome, 'failed');
  assert.deepEqual(post.calls[1].body, { outcome: 'failed', reason: 'missing_asset' });
  announcer.reset();
});

test('W2 an announcer never throws, whatever the network or the player does', async () => {
  const claimFails = createCallAnnouncer({
    announce: fakeAnnounce().announce,
    describe: () => STATE,
    post: fakePost({ '/api/v1/queue/qe-1/announcement': new Error('network down') }).post,
    now: () => NOW,
  });
  const broken = await claimFails.announceCall(calledEntry(), { source: 'event' });
  assert.equal(broken.status, 'failed', 'a claim that could not be sent is not a crash');
  assert.equal(broken.reason, 'claim_failed');

  // A claim that succeeded, then a player that throws, then an outcome report
  // that also fails: three different failures, no exception, no second playback.
  const post = fakePost({
    '/api/v1/queue/qe-1/announcement': { claimed: true, delivery_id: 'dlv-1' },
    '/api/v1/queue/announcements/dlv-1/outcome': new Error('audit unavailable'),
  });
  let plays = 0;
  const announcer = createCallAnnouncer({
    announce: async () => { plays += 1; throw new Error('audio device gone'); },
    describe: () => STATE, post: post.post, now: () => NOW,
  });
  const result = await announcer.announceCall(calledEntry(), { source: 'event' });
  assert.equal(plays, 1);
  assert.equal(result.status, 'announced');
  assert.equal(result.outcome, 'failed', 'the lost report does not change what was heard');
  announcer.reset();
});

test('W2 an announcer without a transport or a network writes nothing', async () => {
  const announcer = createCallAnnouncer({ describe: () => STATE, now: () => NOW });
  const result = await announcer.announceCall(calledEntry(), { source: 'event' });
  assert.equal(result.status, 'skipped');
  assert.equal(result.reason, 'not_wired');
});
