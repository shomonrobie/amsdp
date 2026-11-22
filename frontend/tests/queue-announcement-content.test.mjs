/* QUE-006 — announcement content, token pronunciation and PII boundary.
 *
 * These are assertions about *what the patient hears*, not about the
 * implementation: the approved wording from
 * `AMSDP_QUE-006_Local_Audio_Announcement_Architecture_and_Implementation_
 * Plan_V1.0.md` §6.2/§6.3, the read-aloud form of a token, and the guarantee
 * that patient identity cannot reach the spoken text.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ANNOUNCEMENT_LANGUAGES,
  DOCTOR_PREFIX,
  SKIP_REASON,
  announcementEventKey,
  buildAnnouncement,
  doctorNameWithoutHonorific,
  doctorSegment,
  roomNumberForSpeech,
  spokenTokenNumber,
  TEMPLATES,
  toBanglaDigits,
  tokenSerial,
} from '../lib/announcements/content.js';


test('the approved Bangla sentence is spoken exactly as §6.3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'রহিম উদ্দিন', room: '৩০৫' },
    'bn'
  );
  assert.equal(result.ok, true);
  assert.equal(result.language, 'bn');
  assert.equal(result.text, 'টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।');
  assert.equal(result.fields.template, 'with_room');
  assert.equal(result.fields.derived, false);
  assert.equal(result.fields.reason, '');
});

test('the approved English sentence is spoken exactly as §6.2 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin', room: '305' },
    'en'
  );
  assert.equal(result.ok, true);
  assert.equal(result.text, 'Token number 4, Dr. Rahim Uddin, please proceed to Room 305.');
  assert.equal(result.fields.tokenNumber, '4');
  assert.equal(result.fields.tokenSerial, 4);
});

test('the templates carry no honorific: the segment builder adds it once', () => {
  assert.equal(TEMPLATES.bn.withRoom, 'টোকেন নম্বর {number}, {doctor}, কক্ষ {room}-এ আসুন।');
  assert.equal(TEMPLATES.en.withRoom,
    'Token number {number}, {doctor}, please proceed to Room {room}.');
  assert.deepEqual(DOCTOR_PREFIX, { bn: 'ডা.', en: 'Dr.' });
  assert.equal(doctorSegment('Rahim Uddin', 'en'), 'Dr. Rahim Uddin');
  assert.equal(doctorSegment('রহিম উদ্দিন', 'bn'), 'ডা. রহিম উদ্দিন');
});

test('an honorific already in the name is never spoken twice', () => {
  // Regression: the old template hard-coded "Dr." and produced "Dr. Dr.".
  const stored = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'Dr. Rahim Uddin', room: '305' }, 'en');
  assert.equal(stored.text, 'Token number 4, Dr. Rahim Uddin, please proceed to Room 305.');
  assert.equal(stored.fields.doctorName, 'Rahim Uddin');

  const bangla = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'ডা. রহিম উদ্দিন', room: '305' }, 'bn');
  assert.equal(bangla.text, 'টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।');

  assert.equal(doctorNameWithoutHonorific('Doctor Rahim'), 'Rahim');
  assert.equal(doctorNameWithoutHonorific('ডাক্তার রহিম'), 'রহিম');
  // A name that merely starts with the letters is not an honorific.
  assert.equal(doctorNameWithoutHonorific('Dravid Rao'), 'Dravid Rao');
  // A bare honorific leaves no name, which refuses rather than speaking "Dr.".
  assert.equal(doctorNameWithoutHonorific('Dr.'), '');
});

test('English without a room keeps the approved "please proceed" sentence', () => {
  const en = buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin' }, 'en');
  assert.equal(en.ok, true);
  assert.equal(en.text, 'Token number 4, Dr. Rahim Uddin, please proceed.');
  assert.equal(en.fields.template, 'no_room');
  assert.equal(en.fields.derived, true);
  assert.equal(en.fields.reason, SKIP_REASON.NO_ROOM);
  assert.equal(en.fields.room, null);

  // A blank room is "no room", not a room called space.
  assert.equal(buildAnnouncement({ token: '4', doctorName: 'X', room: '   ' }, 'en').text,
    'Token number 4, Dr. X, please proceed.');
});

test('Bangla without a room is refused, not half-spoken (§18 O-3)', () => {
  // The earlier code produced "টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, আসুন।" — a sentence
  // that reads as an order to *come*, with nothing saying where. Until the owner
  // approves an O-3 wording the refusal is structural, not advisory.
  assert.equal(TEMPLATES.bn.noRoom, null);
  const bn = buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'রহিম উদ্দিন' }, 'bn');
  assert.equal(bn.ok, false);
  assert.equal(bn.reason, SKIP_REASON.NO_ROOM);
  assert.equal(bn.text, undefined);
});

test('a room that is not a number degrades to the room-less sentence and says why', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin', room: 'Cabin A' }, 'en');
  assert.equal(result.ok, true);
  assert.equal(result.text, 'Token number 4, Dr. Rahim Uddin, please proceed.');
  assert.equal(result.fields.roomProvided, 'Cabin A');
  assert.equal(result.fields.reason, SKIP_REASON.ROOM_NOT_ANNOUNCEABLE);
  // Speaking a plausible-but-wrong room would be worse than speaking none.
  assert.equal(roomNumberForSpeech('Room 305'), null);
  assert.equal(roomNumberForSpeech('305'), '305');
  assert.equal(roomNumberForSpeech(' 305 '), '305');
  assert.equal(roomNumberForSpeech('12345'), null);
  assert.equal(roomNumberForSpeech(''), null);
});

test('the spoken token is the serial number, never the doctor-id fragment', () => {
  assert.equal(spokenTokenNumber('T-3F2A9C-001'), '1');
  assert.equal(spokenTokenNumber('T-3F2A9C-004'), '4');
  assert.equal(spokenTokenNumber('T-3F2A9C-012'), '12');
  assert.equal(spokenTokenNumber('004'), '4');
  assert.equal(spokenTokenNumber('12'), '12');
  assert.equal(tokenSerial('T-3F2A9C-012'), 12);
  assert.equal(tokenSerial('not-a-token'), null);
});

test('Bangla announcements speak Bangla digits in the sentence', () => {
  assert.equal(toBanglaDigits('305'), '৩০৫');
  const bn = buildAnnouncement(
    { token: 'T-3F2A9C-012', doctorName: 'রহিম উদ্দিন', room: '305' }, 'bn');
  assert.equal(bn.ok, true);
  assert.equal(bn.fields.tokenNumber, '১২');
  assert.equal(bn.fields.room, '৩০৫');
  assert.equal(bn.text, 'টোকেন নম্বর ১২, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।');
});

test('an internal identifier is never spoken', () => {
  // A UUID, its hex fragment, an empty token and a token with no number all
  // refuse: silence is better than reading an identifier aloud.
  assert.equal(spokenTokenNumber('3f2a9c11-2222-4333-8444-555566667777'), null);
  assert.equal(spokenTokenNumber('3f2a9c11222243338444555566667777'), null);
  assert.equal(spokenTokenNumber(''), null);
  assert.equal(spokenTokenNumber(null), null);
  assert.equal(spokenTokenNumber('T-ABCDEF-'), null);
  assert.equal(buildAnnouncement({ token: '3f2a9c11-2222-4333-8444-555566667777', doctorName: 'X' }, 'en').reason,
    SKIP_REASON.UNSPEAKABLE_TOKEN);
});

test('patient identity cannot reach the spoken text', () => {
  const payload = {
    token: 'T-3F2A9C-004',
    doctorName: 'Rahim Uddin',
    room: '305',
    patientName: 'Karim Mia',
    patient_name: 'Karim Mia',
    patient_id: 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',
    mobile: '01712345678',
    phone: '01712345678',
    notes: 'fever, 3 days',
  };
  const result = buildAnnouncement(payload, 'en');
  assert.equal(result.text, 'Token number 4, Dr. Rahim Uddin, please proceed to Room 305.');
  ['Karim', '01712345678', 'fever', 'aaaaaaaa'].forEach((leak) => {
    assert.ok(!result.text.includes(leak), 'leaked: ' + leak);
  });
});

test('a missing doctor name or language is refused, not spoken', () => {
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004' }, 'en').reason,
    SKIP_REASON.MISSING_DOCTOR_NAME);
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: '   ' }, 'bn').reason,
    SKIP_REASON.MISSING_DOCTOR_NAME);
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'Dr.' }, 'en').reason,
    SKIP_REASON.MISSING_DOCTOR_NAME);
  // No silent fallback: an unknown language is refused, never mapped to Bangla.
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'X' }, 'fr').reason,
    SKIP_REASON.UNSUPPORTED_LANGUAGE);
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'X' }, undefined).reason,
    SKIP_REASON.UNSUPPORTED_LANGUAGE);
  assert.deepEqual([...ANNOUNCEMENT_LANGUAGES], ['bn', 'en']);
});

test('free text is whitespace-collapsed so the sentence stays speakable', () => {
  const result = buildAnnouncement({ token: '7', doctorName: '  Dr.  A.   Rahman ' }, 'en');
  assert.equal(result.text, 'Token number 7, Dr. A. Rahman, please proceed.');
});

test('the event key identifies one queue event and repeats predictably', () => {
  assert.equal(announcementEventKey({ eventId: 'evt-9' }), 'event:evt-9');
  assert.equal(
    announcementEventKey({ queueEntryId: 'qe-1', action: 'call', revision: 2 }),
    'entry:qe-1:call:2'
  );
  // Same event twice ⇒ same key (that is what suppression keys on).
  assert.equal(
    announcementEventKey({ queueEntryId: 'qe-1', action: 'call', revision: 2 }),
    announcementEventKey({ queueEntryId: 'qe-1', action: 'call', revision: 2 })
  );
  // A different action or revision is a different event.
  assert.notEqual(
    announcementEventKey({ queueEntryId: 'qe-1', action: 'call', revision: 2 }),
    announcementEventKey({ queueEntryId: 'qe-1', action: 'recall', revision: 3 })
  );
  assert.equal(announcementEventKey({}), null);
  assert.equal(announcementEventKey({ eventId: 'evt-9', queueEntryId: 'qe-1' }), 'event:evt-9');
});
