/* QUE-006 / F3 — the per-event announcement store.
 *
 * These assertions pin the three defects F3.3 named, plus the bounded-memory and
 * privacy properties the store must never lose:
 *
 *   1. one event's memory must not erase another's (no single-slot store);
 *   2. a key must not be consumed before the attempt (a refusal or a failure
 *      must leave the patient announcable);
 *   3. what happened must be recorded, not merely that the key was seen — so
 *      retry, exhaustion and `needs_activation` are representable.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEDUPE_DEFAULTS,
  DEDUPE_STATE,
  createAnnouncementStore,
  retryDelayMs,
} from '../lib/announcements/dedupe.js';

function clock(start = 0) {
  let value = start;
  return { now: () => value, advance: (ms) => { value += ms; } };
}

function store(options = {}) {
  const time = clock(options.start || 0);
  return {
    time,
    s: createAnnouncementStore({ ...options, now: time.now }),
  };
}

test('the retry delay backs off and is capped', () => {
  assert.equal(retryDelayMs(1), 5000);
  assert.equal(retryDelayMs(2), 10000);
  assert.equal(retryDelayMs(3), 20000);
  assert.equal(retryDelayMs(9), 30000, 'never waits longer than the cap');
  assert.equal(retryDelayMs(0), 5000, 'an impossible count still waits once');
});

test('an unknown event is admitted', () => {
  const { s } = store();
  assert.deepEqual(s.shouldSuppress('a'), { suppress: false, status: '', reason: '' });
});

test('an in-flight attempt suppresses a second delivery of the same event', () => {
  const { s } = store();
  s.begin('a');
  const verdict = s.shouldSuppress('a');
  assert.equal(verdict.suppress, true);
  assert.equal(verdict.status, 'busy');
  assert.equal(s.get('a').state, DEDUPE_STATE.ATTEMPTING);
});

test('a completed event stays suppressed for its TTL and then expires', () => {
  const { s, time } = store({ completedTtlMs: 1000 });
  s.begin('a');
  s.settle('a', { status: 'completed' });
  assert.equal(s.shouldSuppress('a').status, 'duplicate');
  time.advance(999);
  assert.equal(s.shouldSuppress('a').status, 'duplicate');
  time.advance(1);
  assert.equal(s.shouldSuppress('a').suppress, false, 'expiry is evaluated on read');
  assert.equal(s.get('a'), null);
});

test("one event's memory does not erase another's", () => {
  // The defect F3.3(1): the old single slot forgot A as soon as B arrived, so a
  // re-delivery of A inside the window was spoken again.
  const { s } = store({ completedTtlMs: 60000 });
  s.begin('a');
  s.settle('a', { status: 'completed' });
  s.begin('b');
  s.settle('b', { status: 'completed' });

  assert.equal(s.shouldSuppress('a').reason, 'already_completed');
  assert.equal(s.shouldSuppress('b').reason, 'already_completed');
  assert.equal(s.size(), 2);
});


test('a refused attempt is not remembered as announced', () => {
  // The defect F3.3(2): a key consumed before the attempt left a blocked patient
  // never called.
  const { s } = store();
  s.begin('a');
  s.settle('a', { status: 'blocked', reason: 'autoplay' });
  assert.equal(s.get('a').state, DEDUPE_STATE.BLOCKED);

  // Without a gesture the store refuses, and says exactly why.
  const blocked = s.shouldSuppress('a');
  assert.equal(blocked.status, 'needs_activation');
  assert.equal(blocked.reason, 'activation_blocked');

  // A gesture may retry the same key.
  assert.equal(s.shouldSuppress('a', { userGesture: true }).suppress, false);
});

test('a failure is retried after the backoff and exhausts at the limit', () => {
  const { s, time } = store({ maxAttempts: 3 });
  s.begin('a');
  s.settle('a', { status: 'failed', reason: 'engine' });

  const first = s.shouldSuppress('a');
  assert.equal(first.status, 'retry_wait', 'not permanently suppressed');
  time.advance(DEDUPE_DEFAULTS.baseRetryMs);
  assert.equal(s.shouldSuppress('a').suppress, false, 'retryable after the backoff');

  s.begin('a');
  s.settle('a', { status: 'failed', reason: 'engine' });
  time.advance(DEDUPE_DEFAULTS.maxRetryMs);
  assert.equal(s.shouldSuppress('a').suppress, false);

  s.begin('a');
  s.settle('a', { status: 'failed', reason: 'engine' });
  const spent = s.shouldSuppress('a', { userGesture: true });
  assert.equal(spent.status, 'exhausted', 'a gesture cannot exceed the attempt budget');
  assert.equal(spent.reason, 'max_attempts');
  assert.equal(s.get('a').attempts, 3);
});

test('being interrupted counts as an attempt, like a failure', () => {
  const { s, time } = store({ maxAttempts: 1 });
  s.begin('a');
  s.settle('a', { status: 'interrupted', reason: 'cancelled' });
  const verdict = s.shouldSuppress('a');
  assert.equal(verdict.status, 'exhausted');
  assert.equal(s.get('a').expiresAt, time.now() + DEDUPE_DEFAULTS.failureTtlMs);
});

test('nothing heard means nothing remembered', () => {
  // `busy`/`unavailable` are not attempts: the engine never spoke, so the event
  // must remain announcable and must not consume the attempt budget.
  const { s } = store();
  for (const status of ['busy', 'unavailable', 'skipped']) {
    s.begin('a');
    assert.equal(s.settle('a', { status }), null);
    assert.equal(s.get('a'), null, `${status} leaves no record`);
  }
});

test('releasing an unheld key is harmless', () => {
  const { s } = store();
  s.release('never-seen');
  assert.equal(s.size(), 0);
});

test('the store is bounded and never evicts an in-flight attempt', () => {
  const { s } = store({ maxKeys: 4, completedTtlMs: 600000 });
  s.begin('live'); // in flight: must survive every eviction round
  for (let i = 0; i < 10; i += 1) {
    s.begin(`done-${i}`);
    s.settle(`done-${i}`, { status: 'completed' });
  }
  assert.ok(s.size() <= 4, `bounded, was ${s.size()}`);
  assert.ok(s.keys().includes('live'));
  assert.equal(s.shouldSuppress('live').status, 'busy');
});

test('a record carries no spoken text and no patient field', () => {
  // The store is a suppression map, not a log: it must never become a second
  // copy of what was said.
  const { s } = store();
  s.begin('qe-1:call:1');
  const record = s.settle('qe-1:call:1', { status: 'completed', reason: '' });
  assert.deepEqual(Object.keys(record).sort(), [
    'attempts', 'completedAt', 'expiresAt', 'firstAttemptAt', 'key',
    'lastAttemptAt', 'lastReason', 'state',
  ]);
});

test('resetting forgets every event', () => {
  const { s } = store();
  s.begin('a');
  s.settle('a', { status: 'completed' });
  s.reset();
  assert.equal(s.size(), 0);
  assert.equal(s.shouldSuppress('a').suppress, false);
});
