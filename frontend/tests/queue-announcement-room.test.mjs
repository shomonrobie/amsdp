/* QUE-006 / INT-3 — the room reaches the spoken sentence on both paths.
 *
 * The trial merge left the *automatic* announcement reading `entry.room`, a
 * placeholder neither lineage's backend ever sent, while the operator's own
 * "Announce" button already read the room the queue payload actually carries:
 * `room_name`, the appointment booking snapshot serialized by
 * `backend/queuing/main.py::_entry_to_dict` (QUE-006 / F4, option R1). The
 * automatic path therefore could never name a room, and the two paths disagreed
 * about the field they believed in.
 *
 * These tests drive the *real* announcer and the *real* controller (with a fake
 * transport, exactly as `queue-announcement-w2-integration.test.mjs` does), so
 * what is asserted is what the page does, not what an isolated helper can print.
 *
 * Approved wording (Product Owner decision OD-3, doctor name removed):
 *   en, with room     Token number 4, please proceed to Room 305.
 *   en, without room  Token number 4, please come to the front.
 *   bn, with room     টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।
 *   bn, without room  টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।
 *
 * D-4 is decided (Product Owner, 2026-11-22): a room *is* announced when the
 * queue entry carries one (`room_name`), and an entry without a room uses the
 * approved room-less sentence. All four sentences are pinned below, and the
 * last two tests hold the decision itself: which variant was chosen is reported
 * by `fields.template`, and no other room-shaped field can create a room.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { createAnnouncementController } from '../lib/announcements/controller.js';
import { PLAYBACK } from '../lib/announcements/prerecorded-audio.js';
import { createCallAnnouncer } from '../lib/announcements/call-announcer.js';
import { buildAnnouncement } from '../lib/announcements/content.js';

const HERE = dirname(fileURLToPath(import.meta.url));

const EN_WITH_ROOM = 'Token number 4, please proceed to Room 305.';
const EN_NO_ROOM = 'Token number 4, please come to the front.';
const BN_WITH_ROOM = 'টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।';
const BN_NO_ROOM = 'টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।';

function fakeAdapter() {
  return {
    isSupported: () => true,
    isSpeaking: () => false,
    capability: () => ({ status: 'ready', voice: null, voices: [] }),
    async speak() { return { status: 'completed' }; },
    cancel() {},
    subscribeVoices() { return () => {}; },
  };
}

function fakePlayer() {
  const calls = { play: [] };
  return {
    calls,
    async play(payload) {
      calls.play.push(payload);
      return { status: PLAYBACK.COMPLETED };
    },
    async prime() { return { status: 'primed' }; },
    cancel() {},
    getState() { return { playing: false, packId: 'platform.en.draft.v1', version: 1 }; },
    capability() { return { status: 'ready', packId: 'platform.en.draft.v1', version: 1 }; },
  };
}

/**
 * A queue entry exactly as `_entry_to_dict` serializes a called entry whose
 * appointment carried a booking-time room snapshot.
 */
function backendEntry(overrides = {}) {
  return {
    id: 'qe-4',
    queue_entry_id: 'qe-4',
    token: 'T-3F2A9C-004',
    status: 'called',
    call_event_id: 'qce:qe-4:1',
    call_event_at: new Date().toISOString(),
    room_id: 'room-305',
    room_name: '305',
    location_label: 'Room 305',
    room_source: 'appointment_snapshot',
    ...overrides,
  };
}

/** The automatic path: the page's transition seam, wired to the real announcer. */
function automatic(language = 'en') {
  const player = fakePlayer();
  const controller = createAnnouncementController({
    adapter: fakeAdapter(), player, language,
  });
  const posts = [];
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
      posts.push({ path, body });
      return path.endsWith('/outcome')
        ? { settled: true }
        : { claimed: true, delivery_id: 'dlv-4' };
    },
  });
  return { announcer, controller, player, posts };
}

/**
 * The controller's success word is D-6's `completed` (approved 2026-11-22):
 * one vocabulary, so this asserts the word itself rather than accepting an
 * alias.
 */
function assertSpoken(result) {
  assert.equal(result.status, 'completed');
}

/**
 * The operator path: the payload `pages/queue.js::announceEntry` builds. The
 * page calls the controller directly — a deliberate repeat is neither claimed
 * nor suppressed — so it is reproduced here rather than routed through the
 * announcer.
 */
function operatorPayload(entry) {
  return {
    queueEntryId: entry.id,
    action: 'announce',
    eventId: entry.call_event_id,
    token: entry.token,
    room: entry.room_name,
  };
}

/* ---------------------------------------------------------------------------
 * The automatic path
 * ------------------------------------------------------------------------- */

test('INT-3 automatic, English: the room in the payload is spoken', async () => {
  const { announcer, controller, player, posts } = automatic('en');
  const result = await announcer.announceCall(backendEntry(), { source: 'event' });

  assert.equal(result.status, 'announced');
  assert.equal(result.outcome, 'completed');
  // The room reaches playback from the entry's serialized snapshot.
  assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: '305' });
  assert.equal(controller.getState().last.text, EN_WITH_ROOM);
  // The claim is unchanged by this fix and carries no room; the outcome is
  // reported only after the final clip ended.
  assert.equal(posts[0].body.event_id, 'qce:qe-4:1');
  assert.equal('room' in posts[0].body, false, 'the claim body is unchanged');
  assert.deepEqual(posts[1].body, { outcome: 'completed', reason: '' });
  controller.dispose();
});

test('INT-3 automatic, Bangla: the room is spoken in Bangla digits', async () => {
  const { announcer, controller, player } = automatic('bn');
  const result = await announcer.announceCall(backendEntry(), { source: 'event' });

  assert.equal(result.status, 'announced');
  assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: '305' });
  assert.equal(controller.getState().last.text, BN_WITH_ROOM);
  controller.dispose();
});

test('INT-3 automatic, English: no room degrades to the approved sentence', async () => {
  const { announcer, controller, player } = automatic('en');
  await announcer.announceCall(
    backendEntry({ room_name: '', room_id: '', room_source: '' }), { source: 'event' });
  assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: '' });
  assert.equal(controller.getState().last.text, EN_NO_ROOM);
  controller.dispose();
});

test('INT-3 automatic, Bangla: no room degrades to the approved sentence', async () => {
  const { announcer, controller, player } = automatic('bn');
  await announcer.announceCall(backendEntry({ room_name: '', room_id: '' }),
    { source: 'event' });
  assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: '' });
  assert.equal(controller.getState().last.text, BN_NO_ROOM);
  controller.dispose();
});

test('INT-3 automatic: a missing room field is not a room', async () => {
  const entry = backendEntry();
  delete entry.room_name;
  delete entry.room_id;
  const { announcer, controller } = automatic('en');
  const result = await announcer.announceCall(entry, { source: 'event' });
  assert.equal(result.status, 'announced');
  assert.equal(controller.getState().last.text, EN_NO_ROOM);
  controller.dispose();
});

test('INT-3 automatic: a null room field is not a room', async () => {
  const { announcer, controller } = automatic('en');
  await announcer.announceCall(backendEntry({ room_name: null }), { source: 'event' });
  assert.equal(controller.getState().last.text, EN_NO_ROOM);
  controller.dispose();
});

test('INT-3 automatic: the stale `room` placeholder is never read', async () => {
  // `room_name` is the payload's field; a legacy `room` key must not compete
  // with it, and must not be enough on its own to name a room.
  const both = automatic('en');
  await both.announcer.announceCall(backendEntry({ room: '999' }), { source: 'event' });
  assert.equal(both.controller.getState().last.text, EN_WITH_ROOM);
  assert.deepEqual(both.player.calls.play[0], { token: 'T-3F2A9C-004', room: '305' });
  both.controller.dispose();

  const staleOnly = automatic('en');
  const entry = backendEntry({ room: '999' });
  delete entry.room_name;
  await staleOnly.announcer.announceCall(entry, { source: 'event' });
  assert.equal(staleOnly.controller.getState().last.text, EN_NO_ROOM);
  staleOnly.controller.dispose();
});


/* ---------------------------------------------------------------------------
 * The operator-triggered path — same entry, same sentence
 * ------------------------------------------------------------------------- */

test('INT-3 operator: a manual repeat speaks the same room and wording', async () => {
  const entry = backendEntry();
  const player = fakePlayer();
  const controller = createAnnouncementController({
    adapter: fakeAdapter(), player, language: 'en',
  });

  const result = await controller.announce(operatorPayload(entry),
    { source: 'operator', userGesture: true });

  assertSpoken(result);
  assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: '305' });
  assert.equal(controller.getState().last.text, EN_WITH_ROOM);

  // A deliberate repeat is not suppressed as a duplicate of the automatic one.
  const again = await controller.announce(operatorPayload(entry),
    { source: 'operator', userGesture: true });
  assertSpoken(again);
  assert.equal(player.calls.play.length, 2);
  controller.dispose();
});

test('INT-3 operator: Bangla, with and without a room', async () => {
  const player = fakePlayer();
  const controller = createAnnouncementController({
    adapter: fakeAdapter(), player, language: 'bn',
  });

  await controller.announce(operatorPayload(backendEntry()),
    { source: 'operator', userGesture: true });
  assert.equal(controller.getState().last.text, BN_WITH_ROOM);

  await controller.announce(operatorPayload(backendEntry({ room_name: '' })),
    { source: 'operator', userGesture: true });
  assert.equal(controller.getState().last.text, BN_NO_ROOM);
  controller.dispose();
});

test('INT-3 operator: an entry without a room field still announces', async () => {
  const entry = backendEntry();
  delete entry.room_name;
  const controller = createAnnouncementController({
    adapter: fakeAdapter(), player: fakePlayer(), language: 'en',
  });
  const result = await controller.announce(operatorPayload(entry),
    { source: 'operator', userGesture: true });
  assertSpoken(result);
  assert.equal(controller.getState().last.text, EN_NO_ROOM);
  controller.dispose();
});

/* ---------------------------------------------------------------------------
 * The two paths agree on the field, and the wording is the approved wording
 * ------------------------------------------------------------------------- */

test('INT-3 both announcement paths read the payload field `room_name`', () => {
  const sources = [
    ['call-announcer.js',
      readFileSync(join(HERE, '..', 'lib', 'announcements', 'call-announcer.js'), 'utf8')],
    ['pages/queue.js', readFileSync(join(HERE, '..', 'pages', 'queue.js'), 'utf8')],
  ];
  for (const [name, source] of sources) {
    assert.match(source, /room: entry\.room_name/,
      `${name} announces the room the queue payload carries`);
    assert.equal(/room: entry\.room,/.test(source), false,
      `${name} does not read the stale placeholder`);
  }
});

test('INT-3 the four approved sentences are exactly what is spoken', () => {
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', room: '305' }, 'en').text,
    EN_WITH_ROOM);
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004' }, 'en').text, EN_NO_ROOM);
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', room: '305' }, 'bn').text,
    BN_WITH_ROOM);
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004' }, 'bn').text, BN_NO_ROOM);
  // No doctor identity, no honourific, no patient identity in any variant.
  for (const text of [EN_WITH_ROOM, EN_NO_ROOM, BN_WITH_ROOM, BN_NO_ROOM]) {
    assert.equal(/doctor|dr\.|স্যার|ডাক্তার/i.test(text), false);
  }
});

/* ---------------------------------------------------------------------------
 * D-4 (Product Owner, 2026-11-22) — a configured room is announced, an
 * unconfigured one uses the approved room-less sentence, and nothing has to
 * parse the sentence to know which happened
 * ------------------------------------------------------------------------- */

test('D-4 the approved variant that was used is reported, not inferred', () => {
  for (const language of ['en', 'bn']) {
    const withRoom = buildAnnouncement({ token: 'T-3F2A9C-004', room: '305' }, language);
    assert.equal(withRoom.fields.template, 'with_room', `${language}: a room was spoken`);
    assert.equal(withRoom.fields.hasRoom, true);
    assert.equal(withRoom.fields.derived, false);

    const noRoom = buildAnnouncement({ token: 'T-3F2A9C-004' }, language);
    assert.equal(noRoom.fields.template, 'no_room', `${language}: the clause was dropped`);
    assert.equal(noRoom.fields.hasRoom, false);
    assert.equal(noRoom.fields.derived, true,
      `${language}: the room-less sentence is the derived variant, and says so`);
  }
});

test('D-4 only `room_name` is a room: an id, a label or a source alone speaks the room-less sentence', async () => {
  // Each of these fields is room-shaped, and none of them is a room number. If
  // any of them could create a room, an internal identifier or a display label
  // would end up inside a spoken sentence.
  const aloneField = ['room_id', 'location_label', 'room_source'];
  for (const field of aloneField) {
    const { announcer, controller, player } = automatic('en');
    // `room_name` is present but empty: the backend sent no room to announce,
    // while the other room-shaped fields are populated.
    await announcer.announceCall(backendEntry({ room_name: '' }), { source: 'event' });

    assert.deepEqual(player.calls.play[0], { token: 'T-3F2A9C-004', room: '' },
      `${field} alone is not an announceable room`);
    assert.equal(controller.getState().last.text, EN_NO_ROOM, `${field} alone stays room-less`);
    assert.equal(/305/.test(controller.getState().last.text), false,
      `${field} never leaks a room into the sentence`);
    controller.dispose();
  }
});
