/* QUE-006 / OD-1 — announcement content, token pronunciation and PII boundary.
 *
 * These are assertions about *what the patient hears*, not about the
 * implementation: the approved OD-3 wording, the read-aloud form of a token,
 * and the guarantee that patient identity cannot reach the spoken text.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  announcementEventKey,
  buildAnnouncement,
  spokenTokenNumber,
  TEMPLATES,
  toBanglaDigits,
} from '../lib/announcements/content.js';

test('the approved Bangla template is spoken exactly as OD-3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'রহিম উদ্দিন', room: '৩০৫' },
    'bn'
  );
  assert.equal(result.ok, true);
  assert.equal(result.language, 'bn');
  assert.equal(result.text, 'টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, কক্ষ ৩০৫-এ আসুন।');
  assert.equal(result.fields.template, 'with_room');
  assert.equal(result.fields.derived, false);
});

test('the approved English template is spoken exactly as OD-3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin', room: '305' },
    'en'
  );
  assert.equal(result.text, 'Token number 4, Dr. Rahim Uddin, Room 305.');
  assert.equal(result.fields.tokenNumber, '4');
});

test('the templates themselves carry the approved punctuation', () => {
  assert.equal(TEMPLATES.bn.withRoom, 'টোকেন নম্বর {number}, ডা. {doctor}, কক্ষ {room}-এ আসুন।');
  assert.equal(TEMPLATES.en.withRoom, 'Token number {number}, Dr. {doctor}, Room {room}.');
});

test('with no room assigned the room clause is dropped, not invented', () => {
  const bn = buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'রহিম উদ্দিন' }, 'bn');
  const en = buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin' }, 'en');
  assert.equal(bn.text, 'টোকেন নম্বর ৪, ডা. রহিম উদ্দিন, আসুন।');
  assert.equal(en.text, 'Token number 4, Dr. Rahim Uddin.');
  assert.equal(bn.fields.derived, true);
  assert.equal(en.fields.derived, true);
  // A blank room is "no room", not a room called space.
  assert.equal(buildAnnouncement({ token: '4', doctorName: 'X', room: '   ' }, 'en').text,
    'Token number 4, Dr. X.');
});

test('the spoken token is the serial number, never the doctor-id fragment', () => {
  assert.equal(spokenTokenNumber('T-3F2A9C-001'), '1');
  assert.equal(spokenTokenNumber('T-3F2A9C-004'), '4');
  assert.equal(spokenTokenNumber('T-3F2A9C-012'), '12');
  assert.equal(spokenTokenNumber('004'), '4');
  assert.equal(spokenTokenNumber('12'), '12');
});

test('Bangla announcements speak Bangla digits', () => {
  assert.equal(toBanglaDigits('305'), '৩০৫');
  const bn = buildAnnouncement({ token: 'T-3F2A9C-012', doctorName: 'ডাক্তার' }, 'bn');
  assert.equal(bn.fields.tokenNumber, '১২');
  assert.ok(bn.text.includes('১২'));
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
    'unspeakable_token');
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
  assert.equal(result.text, 'Token number 4, Dr. Rahim Uddin, Room 305.');
  ['Karim', '01712345678', 'fever', 'aaaaaaaa'].forEach((leak) => {
    assert.ok(!result.text.includes(leak), 'leaked: ' + leak);
  });
});

test('a missing doctor name or language is refused, not spoken', () => {
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004' }, 'en').reason, 'missing_doctor_name');
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: '   ' }, 'bn').reason, 'missing_doctor_name');
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'X' }, 'fr').reason, 'unsupported_language');
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'X' }, undefined).reason, 'unsupported_language');
});

test('free text is whitespace-collapsed so the sentence stays speakable', () => {
  const result = buildAnnouncement({ token: '7', doctorName: '  Dr.  A.   Rahman ' }, 'en');
  assert.equal(result.text, 'Token number 7, Dr. Dr. A. Rahman.');
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
});
