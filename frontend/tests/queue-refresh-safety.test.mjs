/* QUE-006 / W2 — the refresh that makes a second terminal useful, safely.
 *
 * The queue has no event channel, so the page polls while it is visible. These
 * tests pin the parts that decide whether a refresh can cause a *wrong*
 * announcement:
 *
 *   - a hidden tab never refreshes (so it cannot speak for a call it slept
 *     through; on return the announcer's freshness rule decides);
 *   - coincident triggers (interval, focus, online, tab shown) coalesce into one
 *     refresh plus at most one follow-up, never a pile of parallel reads;
 *   - a failed refresh is reported, never thrown, and the last good list stays.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_REFRESH_INTERVAL_MS,
  createQueueRefresher,
} from '../lib/queue/queue-refresh.js';

function fakeDocument(visibility = 'visible') {
  const handlers = { visibilitychange: [] };
  return {
    visibilityState: visibility,
    handlers,
    addEventListener(type, handler) { (handlers[type] = handlers[type] || []).push(handler); },
    removeEventListener(type, handler) {
      handlers[type] = (handlers[type] || []).filter((h) => h !== handler);
    },
    fire(type) { (handlers[type] || []).slice().forEach((handler) => handler()); },
    count(type) { return (handlers[type] || []).length; },
  };
}

function fakeWindow() {
  const handlers = { online: [], focus: [] };
  return {
    handlers,
    addEventListener(type, handler) { (handlers[type] = handlers[type] || []).push(handler); },
    removeEventListener(type, handler) {
      handlers[type] = (handlers[type] || []).filter((h) => h !== handler);
    },
    fire(type) { (handlers[type] || []).slice().forEach((handler) => handler()); },
    count(type) { return (handlers[type] || []).length; },
  };
}

function fakeClock() {
  const timers = [];
  return {
    timers,
    setInterval(fn, ms) { timers.push({ fn, ms }); return timers.length; },
    clearInterval(handle) { timers[handle - 1] = null; },
    tick() { timers.slice().forEach((timer) => timer && timer.fn()); },
  };
}

test('W2 a hidden tab does not refresh, and says why', async () => {
  let calls = 0;
  const doc = fakeDocument('hidden');
  const refresher = createQueueRefresher({
    refresh: () => { calls += 1; },
    document: doc,
    window: fakeWindow(),
    setInterval: () => 1,
    clearInterval: () => {},
  });

  assert.deepEqual(await refresher.run('start'), { status: 'hidden' });
  assert.equal(calls, 0, 'a background tab must not re-read the queue');

  refresher.start();
  doc.visibilityState = 'visible';
  doc.fire('visibilitychange');
  await flush();
  assert.equal(calls, 1, 'showing the tab refreshes immediately');
  refresher.stop();
});

test('W2 returning to the tab, reconnecting and focusing all refresh', async () => {
  const reasons = [];
  const doc = fakeDocument('hidden');
  const win = fakeWindow();
  const refresher = createQueueRefresher({
    refresh: (reason) => { reasons.push(reason); },
    document: doc,
    window: win,
    setInterval: () => 1,
    clearInterval: () => {},
  });
  refresher.start();

  doc.visibilityState = 'visible';
  doc.fire('visibilitychange');
  await flush();
  win.fire('online');
  await flush();
  win.fire('focus');
  await flush();

  assert.deepEqual(reasons, ['visible', 'online', 'focus']);
  refresher.stop();
});

test('W2 coincident triggers coalesce into one refresh plus one follow-up', async () => {
  const reasons = [];
  let release = null;
  const refresher = createQueueRefresher({
    refresh: (reason) => {
      reasons.push(reason);
      if (reasons.length === 1) return new Promise((resolve) => { release = resolve; });
      return undefined;
    },
    document: fakeDocument('visible'),
    window: fakeWindow(),
  });

  const first = refresher.run('interval');
  assert.equal(refresher.isRunning(), true);
  assert.deepEqual(await refresher.run('focus'), { status: 'coalesced' });
  assert.deepEqual(await refresher.run('online'), { status: 'coalesced' });
  assert.deepEqual(reasons, ['interval'], 'one read is in flight, not three');

  release();
  assert.deepEqual(await first, { status: 'refreshed' });
  await flush();

  assert.deepEqual(reasons, ['interval', 'queued'], 'the missed triggers become one');
  assert.equal(refresher.isRunning(), false);
});

test('W2 a failed refresh is reported and never thrown', async () => {
  const seen = [];
  const refresher = createQueueRefresher({
    refresh: () => { throw new Error('backend down'); },
    document: fakeDocument('visible'),
    window: fakeWindow(),
    onError: (error) => seen.push(error.message),
  });

  const result = await refresher.run('interval');
  assert.equal(result.status, 'failed');
  assert.equal(result.error.message, 'backend down');
  assert.deepEqual(seen, ['backend down']);
  assert.equal(refresher.isRunning(), false, 'a failure does not wedge the timer');
});


const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

test('W2 an error surface that throws cannot break the timer', async () => {
  const refresher = createQueueRefresher({
    refresh: () => { throw new Error('nope'); },
    onError: () => { throw new Error('the surface is broken too'); },
  });
  const result = await refresher.run('interval');
  assert.equal(result.status, 'failed');
});

test('W2 the interval is the documented default and ticks only while visible', async () => {
  assert.equal(DEFAULT_REFRESH_INTERVAL_MS, 20000);

  let calls = 0;
  const clock = fakeClock();
  const doc = fakeDocument('visible');
  const refresher = createQueueRefresher({
    refresh: () => { calls += 1; },
    document: doc,
    window: fakeWindow(),
    setInterval: clock.setInterval,
    clearInterval: clock.clearInterval,
  });
  refresher.start();
  assert.equal(clock.timers.length, 1);
  assert.equal(clock.timers[0].ms, DEFAULT_REFRESH_INTERVAL_MS);

  clock.tick();
  await flush();
  assert.equal(calls, 1);

  doc.visibilityState = 'hidden';
  clock.tick();
  await flush();
  assert.equal(calls, 1, 'a hidden tab skips the tick entirely');

  refresher.stop();
  assert.equal(clock.timers[0], null, 'the interval is cleared on stop');
  assert.equal(doc.count('visibilitychange'), 0, 'the listeners are removed on stop');
});

test('W2 starting twice does not double every trigger', async () => {
  let calls = 0;
  const clock = fakeClock();
  const win = fakeWindow();
  const refresher = createQueueRefresher({
    refresh: () => { calls += 1; },
    document: fakeDocument('visible'),
    window: win,
    setInterval: clock.setInterval,
    clearInterval: clock.clearInterval,
  });
  refresher.start();
  refresher.start();
  assert.equal(clock.timers.length, 1, 'one interval, however often start is called');
  assert.equal(win.count('focus'), 1);

  win.fire('focus');
  await flush();
  assert.equal(calls, 1);
  refresher.stop();
});

test('W2 a refresher without a loader does nothing at all', async () => {
  const refresher = createQueueRefresher({ intervalMs: 0 });
  assert.deepEqual(await refresher.run('interval'), { status: 'unwired' });
  refresher.start();
  refresher.stop();
  assert.equal(refresher.isStarted(), false);
});
