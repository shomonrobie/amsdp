/* QUE-006 / OD-1 — the Web Speech API adapter.
 *
 * The adapter is the only browser-specific part of the mechanism, so it is
 * exercised here against a fake `speechSynthesis`: voice selection, the
 * "silence is not success" rule, overlap, cancellation and cleanup.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  CAPABILITY,
  createSpeechSynthesisAdapter,
  OUTCOME,
  pickVoice,
} from '../lib/announcements/speech-synthesis.js';

class FakeUtterance {
  constructor(text) {
    this.text = text;
    this.lang = '';
    this.voice = null;
    this.volume = 1;
    this.rate = 1;
  }
}

function fakeTimers() {
  const pending = new Map();
  let next = 1;
  return {
    setTimeout(fn) { const id = next++; pending.set(id, fn); return id; },
    clearTimeout(id) { pending.delete(id); },
    runAll() { const fns = Array.from(pending.values()); pending.clear(); fns.forEach((fn) => fn()); },
    size() { return pending.size; },
  };
}

function fakeSynth(voices, options = {}) {
  const calls = { speak: [], cancel: 0 };
  const listeners = new Set();
  return {
    calls,
    getVoices() {
      if (options.getVoicesThrows) throw new Error('no voices');
      return options.voices || voices;
    },
    speak(utterance) {
      calls.speak.push(utterance);
      if (options.speakThrows) throw new Error('boom');
      if (options.onSpeak) { options.onSpeak(utterance); return; }
      if (options.fireStart === false) return;
      if (typeof utterance.onstart === 'function') utterance.onstart();
      if (options.fireEnd === false) return;
      if (typeof utterance.onend === 'function') utterance.onend();
    },
    cancel() { calls.cancel += 1; },
    addEventListener(type, fn) { listeners.add(fn); },
    removeEventListener(type, fn) { listeners.delete(fn); },
    fireVoicesChanged() { listeners.forEach((fn) => fn()); },
    listenerCount() { return listeners.size; },
  };
}

const BN_VOICE = { name: 'Bangla Bangladesh', lang: 'bn-BD', localService: true, default: true };
const BN_OTHER = { name: 'Bangla India', lang: 'bn-IN', localService: true };
const EN_VOICE = { name: 'English UK', lang: 'en-GB', localService: true, default: true };

function build(voices, options = {}) {
  const synth = fakeSynth(voices, options);
  const timers = fakeTimers();
  const adapter = createSpeechSynthesisAdapter({
    synth, Utterance: FakeUtterance, timers, startTimeoutMs: 1500,
  });
  return { synth, timers, adapter };
}

test('without a speech engine the adapter is unavailable, not broken', async () => {
  const adapter = createSpeechSynthesisAdapter({ scope: {}, synth: null, Utterance: null });
  assert.equal(adapter.isSupported(), false);
  assert.equal(adapter.capability('bn').status, CAPABILITY.UNSUPPORTED);
  assert.deepEqual(await adapter.speak('hello', { language: 'en' }), {
    status: OUTCOME.UNAVAILABLE, reason: 'unsupported',
  });
  adapter.cancel();
  adapter.dispose();
});

test('a voice is only chosen for the language that was asked for', () => {
  assert.equal(pickVoice([EN_VOICE], 'bn'), null);
  assert.equal(pickVoice([BN_VOICE], 'en'), null);
  const picked = pickVoice([EN_VOICE, BN_VOICE], 'bn');
  assert.equal(picked.voice, BN_VOICE);
  assert.equal(picked.matched, true);
  assert.equal(picked.fallback, false);
});

test('another region of the same language is a marked fallback', () => {
  const picked = pickVoice([EN_VOICE, BN_OTHER], 'bn');
  assert.equal(picked.voice, BN_OTHER);
  assert.equal(picked.matched, false);
  assert.equal(picked.fallback, true);
});

test('a local voice is preferred over a network voice', () => {
  const remote = { name: 'Remote Bangla', lang: 'bn-BD', localService: false };
  const local = { name: 'Local Bangla', lang: 'bn-BD', localService: true };
  assert.equal(pickVoice([remote, local], 'bn').voice, local);
});

test('capability distinguishes "no voices yet" from "no voice for this language"', () => {
  const empty = build([]);
  assert.equal(empty.adapter.capability('bn').status, CAPABILITY.PENDING);
  empty.adapter.dispose();

  const englishOnly = build([EN_VOICE]);
  assert.equal(englishOnly.adapter.capability('bn').status, CAPABILITY.NO_VOICE);
  assert.equal(englishOnly.adapter.capability('en').status, CAPABILITY.READY);
  englishOnly.adapter.dispose();
});

test('speaking sets the language and the chosen voice, and reports completed', async () => {
  const { adapter, synth } = build([BN_VOICE]);
  const result = await adapter.speak('টোকেন নম্বর ৪', { language: 'bn' });
  assert.equal(result.status, OUTCOME.COMPLETED);
  assert.equal(result.voice.lang, 'bn-BD');
  assert.equal(typeof result.durationMs, 'number');
  assert.equal(synth.calls.speak.length, 1);
  assert.equal(synth.calls.speak[0].text, 'টোকেন নম্বর ৪');
  assert.equal(synth.calls.speak[0].voice, BN_VOICE);
  assert.equal(synth.calls.speak[0].lang, 'bn-BD');
  adapter.dispose();
});

test('start is progress, not completion: only `end` resolves completed', async () => {
  // The F2 defect: resolving on `start` reported an announcement as delivered
  // before it had finished. After `start` the adapter must still be speaking.
  const { adapter, timers } = build([EN_VOICE], { fireEnd: false });
  let settled = null;
  const pending = adapter.speak('Token number 4', { language: 'en' })
    .then((result) => { settled = result; return result; });

  assert.equal(settled, null, '`start` alone must not settle the promise');
  assert.equal(adapter.isSpeaking(), true);

  timers.runAll();
  const result = await pending;
  assert.equal(result.status, OUTCOME.FAILED);
  assert.equal(result.reason, 'no_end_event');
  assert.equal(adapter.isSpeaking(), false, 'a stuck engine is released, not left speaking');
  adapter.dispose();
});

test('Bangla without a Bangla voice refuses instead of using English', async () => {
  const { adapter, synth } = build([EN_VOICE]);
  const result = await adapter.speak('টোকেন নম্বর ৪', { language: 'bn' });
  assert.equal(result.status, OUTCOME.UNAVAILABLE);
  assert.equal(synth.calls.speak.length, 0, 'nothing may be spoken in the wrong language');
  adapter.dispose();
});

test('an empty voice list is unavailable, and nothing is spoken', async () => {
  const { adapter, synth } = build([]);
  const result = await adapter.speak('hello', { language: 'en' });
  assert.equal(result.status, OUTCOME.UNAVAILABLE);
  assert.equal(synth.calls.speak.length, 0);
  adapter.dispose();
});

test('silence is not success: no start event becomes blocked', async () => {
  const { adapter, timers, synth } = build([EN_VOICE], { fireStart: false });
  const pending = adapter.speak('hello', { language: 'en' });
  assert.equal(timers.size(), 1, 'a start timeout is armed');
  timers.runAll();
  const result = await pending;
  assert.equal(result.status, OUTCOME.BLOCKED);
  assert.equal(result.reason, 'no_start_event');
  assert.equal(synth.calls.cancel, 1, 'the silent utterance is cancelled');
  assert.equal(adapter.isSpeaking(), false);
  adapter.dispose();
});

test('an autoplay refusal reported by the engine is blocked', async () => {
  const { adapter } = build([EN_VOICE], {
    onSpeak: (u) => u.onerror({ error: 'not-allowed' }),
  });
  const result = await adapter.speak('hello', { language: 'en' });
  assert.equal(result.status, OUTCOME.BLOCKED);
  assert.equal(result.reason, 'not-allowed');
  adapter.dispose();
});

test('a cancelled utterance is reported as interrupted, not as completed', async () => {
  const { adapter } = build([EN_VOICE], {
    onSpeak: (u) => u.onerror({ error: 'canceled' }),
  });
  const result = await adapter.speak('hello', { language: 'en' });
  assert.equal(result.status, OUTCOME.INTERRUPTED);
  assert.equal(result.reason, 'canceled');
  adapter.dispose();
});

test('one utterance at a time: a second call is busy, replace cancels the first', async () => {
  const { adapter, timers } = build([EN_VOICE], { fireStart: false });
  const first = adapter.speak('first', { language: 'en' });
  assert.equal(adapter.isSpeaking(), true);
  assert.deepEqual(await adapter.speak('second', { language: 'en' }), {
    status: OUTCOME.BUSY, language: 'en',
  });

  const replacement = adapter.speak('replacement', { language: 'en', replace: true });
  assert.equal((await first).status, OUTCOME.INTERRUPTED, 'the superseded utterance is stopped');
  // This engine never reports `start`, so the replacement times out as blocked.
  timers.runAll();
  assert.equal((await replacement).status, OUTCOME.BLOCKED);
  adapter.dispose();
});

test('a throwing engine becomes a failed result, never a rejection', async () => {
  const { adapter } = build([EN_VOICE], { speakThrows: true });
  const result = await adapter.speak('hello', { language: 'en' });
  assert.equal(result.status, OUTCOME.FAILED);
  assert.equal(result.reason, 'speak_threw');
  assert.equal(adapter.isSpeaking(), false);
  adapter.dispose();
});

test('a throwing getVoices() is treated as "no voices", not as a crash', async () => {
  const { adapter } = build([EN_VOICE], { getVoicesThrows: true });
  assert.equal(adapter.capability('en').status, CAPABILITY.PENDING);
  assert.equal((await adapter.speak('hello', { language: 'en' })).status, OUTCOME.UNAVAILABLE);
  adapter.dispose();
});

test('empty text is refused before the engine is touched', async () => {
  const { adapter, synth } = build([EN_VOICE]);
  const result = await adapter.speak('', { language: 'en' });
  assert.equal(result.status, OUTCOME.FAILED);
  assert.equal(result.reason, 'empty_text');
  assert.equal(synth.calls.speak.length, 0);
  adapter.dispose();
});

test('the priming utterance is silent and needs no voice', async () => {
  const { adapter, synth } = build([]);
  const result = await adapter.speak(' ', { language: 'bn', prime: true, volume: 0 });
  assert.equal(result.status, OUTCOME.COMPLETED);
  assert.equal(synth.calls.speak[0].volume, 0);
  adapter.dispose();
});

test('voice changes are subscribed and unsubscribed cleanly', () => {
  const { adapter, synth } = build([BN_VOICE]);
  let seen = 0;
  const unsubscribe = adapter.subscribeVoices(() => { seen += 1; });
  assert.equal(synth.listenerCount(), 1);
  synth.fireVoicesChanged();
  assert.equal(seen, 1);
  unsubscribe();
  assert.equal(synth.listenerCount(), 0);
  adapter.dispose();
  assert.equal(synth.listenerCount(), 0);
});

test('dispose stops speech and refuses further playback', async () => {
  const { adapter, synth } = build([EN_VOICE], { fireStart: false });
  const pending = adapter.speak('hello', { language: 'en' });
  adapter.dispose();
  assert.equal((await pending).status, OUTCOME.INTERRUPTED);
  assert.equal(synth.calls.cancel, 1);
  assert.equal((await adapter.speak('again', { language: 'en' })).status, OUTCOME.UNAVAILABLE);
});
