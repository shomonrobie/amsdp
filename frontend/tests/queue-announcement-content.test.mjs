/* QUE-006 / OD-1 — announcement content, token pronunciation and PII boundary.
 *
 * These are assertions about *what the patient hears*, not about the
 * implementation: the approved OD-3 wording (doctor name removed), the
 * read-aloud form of a token, and the guarantee that patient identity and
 * doctor identity cannot reach the spoken text.
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

test('the approved Bangla template with room is spoken exactly as OD-3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', room: '৩০৫' },
    'bn'
  );
  assert.equal(result.ok, true);
  assert.equal(result.language, 'bn');
  assert.equal(result.text, 'টোকেন নম্বর ৪, কক্ষ ৩০৫-এ আসুন।');
  assert.equal(result.fields.template, 'with_room');
  assert.equal(result.fields.derived, false);
});

test('the approved English template with room is spoken exactly as OD-3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004', room: '305' },
    'en'
  );
  assert.equal(result.text, 'Token number 4, please proceed to Room 305.');
  assert.equal(result.fields.tokenNumber, '4');
});

test('the approved Bangla template without room is spoken exactly as OD-3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004' },
    'bn'
  );
  assert.equal(result.ok, true);
  assert.equal(result.text, 'টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।');
  assert.equal(result.fields.template, 'no_room');
  assert.equal(result.fields.derived, true);
});

test('the approved English template without room is spoken exactly as OD-3 records it', () => {
  const result = buildAnnouncement(
    { token: 'T-3F2A9C-004' },
    'en'
  );
  assert.equal(result.text, 'Token number 4, please come to the front.');
  assert.equal(result.fields.template, 'no_room');
  assert.equal(result.fields.derived, true);
});

test('the templates themselves carry the approved punctuation', () => {
  assert.equal(TEMPLATES.bn.withRoom, 'টোকেন নম্বর {number}, কক্ষ {room}-এ আসুন।');
  assert.equal(TEMPLATES.bn.noRoom, 'টোকেন নম্বর {number}, অনুগ্রহ করে সামনে আসুন।');
  assert.equal(TEMPLATES.en.withRoom, 'Token number {number}, please proceed to Room {room}.');
  assert.equal(TEMPLATES.en.noRoom, 'Token number {number}, please come to the front.');
});

test('with no room assigned the room clause is dropped, not invented', () => {
  const bn = buildAnnouncement({ token: 'T-3F2A9C-004' }, 'bn');
  const en = buildAnnouncement({ token: 'T-3F2A9C-004' }, 'en');
  assert.equal(bn.text, 'টোকেন নম্বর ৪, অনুগ্রহ করে সামনে আসুন।');
  assert.equal(en.text, 'Token number 4, please come to the front.');
  assert.equal(bn.fields.derived, true);
  assert.equal(en.fields.derived, true);
  // A blank room is "no room", not a room called space.
  assert.equal(buildAnnouncement({ token: '4', room: '   ' }, 'en').text,
    'Token number 4, please come to the front.');
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
  const bn = buildAnnouncement({ token: 'T-3F2A9C-012' }, 'bn');
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
  assert.equal(buildAnnouncement({ token: '3f2a9c11-2222-4333-8444-555566667777' }, 'en').reason,
    'unspeakable_token');
});

test('patient identity cannot reach the spoken text', () => {
  const payload = {
    token: 'T-3F2A9C-004',
    room: '305',
    patientName: 'Karim Mia',
    patient_name: 'Karim Mia',
    patient_id: 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',
    mobile: '01712345678',
    phone: '01712345678',
    notes: 'fever, 3 days',
  };
  const result = buildAnnouncement(payload, 'en');
  assert.equal(result.text, 'Token number 4, please proceed to Room 305.');
  ['Karim', '01712345678', 'fever', 'aaaaaaaa'].forEach((leak) => {
    assert.ok(!result.text.includes(leak), 'leaked: ' + leak);
  });
});

test('a missing doctor name does not prevent announcement generation', () => {
  // Doctor name is never required; omission must not block an announcement.
  const withDoctor = buildAnnouncement({ token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin', room: '305' }, 'en');
  const withoutDoctor = buildAnnouncement({ token: 'T-3F2A9C-004', room: '305' }, 'en');
  assert.equal(withDoctor.ok, true);
  assert.equal(withoutDoctor.ok, true);
  assert.equal(withDoctor.text, 'Token number 4, please proceed to Room 305.');
  assert.equal(withoutDoctor.text, 'Token number 4, please proceed to Room 305.');
});

test('doctor name and honourific never appear in the announcement', () => {
  // Even when doctor-name input is supplied, it must not surface in speech.
  const cases = [
    { token: 'T-3F2A9C-004', doctorName: 'Dr. Rahim Uddin', room: '305' },
    { token: 'T-3F2A9C-004', doctorName: 'Rahim Uddin', room: '305' },
    { token: 'T-3F2A9C-004', doctorName: 'ডা. রহিম উদ্দিন', room: '৩০৫' },
    { token: 'T-3F2A9C-004', doctorName: 'ডাক্তার রহিম উদ্দিন', room: '৩০৫' },
  ];
  for (const c of cases) {
    const en = buildAnnouncement(c, 'en');
    const bn = buildAnnouncement(c, 'bn');
    assert.equal(en.ok, true, 'English must not refuse doctor-name input');
    assert.equal(bn.ok, true, 'Bangla must not refuse doctor-name input');
    assert.ok(!en.text.includes('Dr.'), 'English must not contain Dr.');
    assert.ok(!en.text.includes('Doctor'), 'English must not contain Doctor');
    assert.ok(!en.text.includes('Rahim'), 'English must not contain the doctor name');
    assert.ok(!en.text.includes('Uddin'), 'English must not contain the doctor name');
    assert.ok(!bn.text.includes('ডা.'), 'Bangla must not contain ডা.');
    assert.ok(!bn.text.includes('ডাক্তার'), 'Bangla must not contain ডাক্তার');
    assert.ok(!bn.text.includes('রহিম'), 'Bangla must not contain the doctor name');
    assert.ok(!bn.text.includes('উদ্দিন'), 'Bangla must not contain the doctor name');
  }
});

test('a missing language is refused, not spoken', () => {
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', room: '305' }, 'fr').reason, 'unsupported_language');
  assert.equal(buildAnnouncement({ token: 'T-3F2A9C-004', room: '305' }, undefined).reason, 'unsupported_language');
});

test('free text is whitespace-collapsed so the sentence stays speakable', () => {
  const result = buildAnnouncement({ token: '7', room: '  305  ' }, 'en');
  assert.equal(result.text, 'Token number 7, please proceed to Room 305.');
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
