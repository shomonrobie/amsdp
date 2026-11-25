/* QUE-006 / POD-12 — the queue Call control and its announcement trigger.
 *
 * What this file proves, and how:
 *   - the eligibility and single-flight rules are real code (`lib/queue/queue-call.js`)
 *     and are exercised directly, with a fake request — no React, no DOM;
 *   - the page's *wiring* is asserted against its source, because the page is
 *     JSX and this project does not ship a DOM test renderer (the JSX compile
 *     check lives in `queue-announcements-boundary.test.mjs` and skips when the
 *     SWC binary is not installed);
 *   - the frontend role mirror in `lib/auth.js` is cross-checked against the
 *     authoritative backend matrix, so "who sees Call" cannot drift silently.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { can } from '../lib/auth.js';
import { DICT } from '../lib/i18n.js';
import { CALL_ACTION, createCallGate, isCallable, isRecallable, performCall, RECALL_ACTION } from '../lib/queue/queue-call.js';
import { trackCalledTransitions } from '../lib/announcements/queue-transitions.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');
const PAGE = fs.readFileSync(path.join(FE, 'pages', 'queue.js'), 'utf8');
const BACKEND_MATRIX = fs.readFileSync(
  path.join(REPO, 'backend', 'common', 'permissions.py'), 'utf8');
const QUEUE_API = fs.readFileSync(
  path.join(REPO, 'backend', 'queuing', 'main.py'), 'utf8');

/** Run `fn` with a browser-shaped session holding one role.
 *
 * `lib/auth.js` reads the *bare* `sessionStorage` global (a browser resolve it
 * from `window`, Node does not), so both are provided here.
 */
function withRole(role, fn) {
  const store = new Map([['amsdp_user', JSON.stringify({ id: 'u-1', role })]]);
  const sessionStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, v),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
  };
  globalThis.window = { sessionStorage };
  globalThis.sessionStorage = sessionStorage;
  try {
    return fn();
  } finally {
    delete globalThis.window;
    delete globalThis.sessionStorage;
  }
}

/** The page's handler body, comments stripped, so claims are about code. */
function handlerBody(name) {
  const start = PAGE.indexOf('const ' + name);
  assert.ok(start > 0, `pages/queue.js defines ${name}`);
  return PAGE.slice(start, PAGE.indexOf('\n  };', start))
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/[^\n]*/g, '');
}

/** A role block out of the authoritative Python matrix, comments stripped.
 *
 * The doctor block *mentions* `queue.manage` in a comment explaining what it
 * deliberately does not grant, so comments must go before any match.
 */
function pythonRoleBlock(role) {
  const start = BACKEND_MATRIX.indexOf(`"${role}": [`);
  assert.ok(start > 0, `backend matrix declares ${role}`);
  const end = BACKEND_MATRIX.indexOf('],', start);
  assert.ok(end > start, `backend matrix closes ${role}`);
  return BACKEND_MATRIX.slice(start, end).replace(/#[^\n]*/g, '');
}

function okRequest(log) {
  return async (id, payload) => { log.push({ id, payload }); return { status: 'called' }; };
}

// ---------------------------------------------------------------------------
// Who may call — the two matrices must agree
// ---------------------------------------------------------------------------

test('POD-12 receptionist holds queue.manage in both matrices', () => {
  assert.equal(withRole('receptionist', () => can('queue.manage')), true);
  assert.match(pythonRoleBlock('receptionist'), /"queue\.manage"/);
});

test('POD-12 doctor does NOT hold queue.manage; decision D is an org opt-in', () => {
  // POD-12: "Doctors may call ... where their existing permissions grant
  // queue.manage" and "Do not grant new permissions merely to make the
  // interface work". The doctor role holds it in neither matrix, and it is
  // absent from DELEGABLE_CAPABILITIES, so no grant can add it either.
  //
  // Owner decision D (QUE-006 / DEV-1) answers the product question without
  // inventing a capability: an *organization* may enable doctor queue-calling,
  // and the backend then permits the doctor's `call` for their own patients.
  assert.equal(withRole('doctor', () => can('queue.manage')), false);
  assert.doesNotMatch(pythonRoleBlock('doctor'), /queue\.manage/);
  const delegable = BACKEND_MATRIX.slice(BACKEND_MATRIX.indexOf('DELEGABLE_CAPABILITIES'));
  assert.doesNotMatch(delegable, /queue\.manage/,
    'queue.manage cannot be delegated, so no doctor can acquire it');
  // The doctor still holds what the organization-level rule depends on.
  assert.equal(withRole('doctor', () => can('queue.consult')), true);
});

test('POD-12 no role gained a capability: branch_admin already held queue.*', () => {
  // The task adds no permission. branch_admin's existing queue.* wildcard
  // already covered queue.manage at HEAD, which is why POD-12 forbids *adding*
  // one — there is nothing to add.
  assert.equal(withRole('branch_admin', () => can('queue.manage')), true);
  assert.match(pythonRoleBlock('branch_admin'), /"queue\.\*"/);
  assert.match(pythonRoleBlock('org_admin'), /"queue\.\*"/);
});

test('POD-12 an assistant is never offered the control', () => {
  assert.equal(withRole('assistant', () => can('queue.manage')), false);
});

// ---------------------------------------------------------------------------
// Server contract: one existing endpoint, one existing action, one permission
// ---------------------------------------------------------------------------

test('POD-12 the call action uses the existing endpoint and action string', () => {
  assert.equal(CALL_ACTION, 'call');
  assert.match(QUEUE_API, /_TRANSITIONS = \{[\s\S]*?"waiting":\s*\("call"/,
    'the server already permits waiting -> called');
  assert.match(QUEUE_API, /"call": "called"/);
  // Owner decision D: `queue.manage` remains the rule; an organization that
  // enables doctor queue-calling adds its doctors for their own patients, and
  // the own-patient scope is enforced afterwards by can_access_doctor.
  assert.match(QUEUE_API, /elif data\.action in \("call", "recall"\):[\s\S]{0,700}?check_granted\("queue\.manage"/,
    'call and recall are gated on queue.manage by default');
  assert.match(QUEUE_API, /"called":\s*\("recall"/,
    'MP-08: `recall` is the only repeat call from `called`');
  assert.doesNotMatch(QUEUE_API, /"called":\s*\("call"/,
    'a repeated `call` from `called` stays refused, so it cannot announce twice');
  assert.match(QUEUE_API, /_doctor_may_call\(auth\)/,
    'the only widening is the organization policy');
  assert.match(QUEUE_API, /get_queue_calling_config\(org\.config, org\.facility_type\)/,
    'the policy is read from the organization, never from the request body');
  assert.match(QUEUE_API,
    /data\.action in \("cancel", "mark_no_show", "reinsert"\)[\s\S]{0,200}?require_permission\("queue\.manage"\)/,
    'every other mutating action is untouched');
  assert.equal(/"action": "call"/.test(PAGE), false,
    'the page never invents a second call endpoint');
  assert.equal(/queue\/call/.test(PAGE), false, 'no duplicate route');
});

test('POD-12 a successful call sends exactly the documented payload', async () => {
  const log = [];
  const result = await performCall({
    entry: { id: 'qe-1', status: 'waiting' },
    authorised: true,
    gate: createCallGate(),
    request: okRequest(log),
  });
  assert.equal(result.status, 'called');
  assert.deepEqual(log, [{ id: 'qe-1', payload: { action: 'call', reason: '' } }]);
});

// ---------------------------------------------------------------------------
// Eligibility (required tests 5 and 6)
// ---------------------------------------------------------------------------

test('POD-12 only a waiting entry is callable', () => {
  assert.equal(isCallable({ id: 'qe-1', status: 'waiting' }), true);
  // The server also allows skipped -> called; the interface deliberately does
  // not, because a skipped entry is recovered (BR §27A), not called.
  for (const status of ['called', 'in_consultation', 'completed', 'cancelled', 'no_show', 'skipped', '']) {
    assert.equal(isCallable({ id: 'qe-1', status }), false, status);
  }
  for (const junk of [null, undefined, {}, { id: 7, status: 'waiting' }, 'qe-1']) {
    assert.equal(isCallable(junk), false, JSON.stringify(junk));
  }
});

test('POD-12 an ineligible entry is refused before any request exists', async () => {
  const log = [];
  for (const status of ['called', 'completed', 'cancelled']) {
    const result = await performCall({
      entry: { id: 'qe-1', status },
      authorised: true,
      gate: createCallGate(),
      request: okRequest(log),
    });
    assert.equal(result.status, 'ineligible', status);
  }
  assert.deepEqual(log, [], 'nothing was sent');
});

test('POD-12 an unauthorised caller sends nothing either', async () => {
  const log = [];
  const result = await performCall({
    entry: { id: 'qe-1', status: 'waiting' },
    authorised: false,
    gate: createCallGate(),
    request: okRequest(log),
  });
  assert.equal(result.status, 'forbidden');
  assert.deepEqual(log, [], 'the UI mirror is not the boundary, but it still does not call');
});

// ---------------------------------------------------------------------------
// Required tests 7, 9 and 11: failure, no audio coupling, duplicate submits
// ---------------------------------------------------------------------------

test('POD-12 a failed request is reported, never as a success', async () => {
  const log = [];
  const failure = Object.assign(new Error('cannot call from cancelled'), { status: 422 });
  const result = await performCall({
    entry: { id: 'qe-1', status: 'waiting' },
    authorised: true,
    gate: createCallGate(),
    request: async (id, payload) => { log.push({ id, payload }); throw failure; },
  });
  assert.equal(result.status, 'failed');
  assert.equal(result.error, failure);
  assert.equal(log.length, 1, 'the request was attempted');
});

test('POD-12 a second click while a call is pending sends nothing', async () => {
  const log = [];
  const gate = createCallGate();
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  const request = async (id, payload) => { log.push({ id, payload }); await pending; };

  const first = performCall({ entry: { id: 'qe-1', status: 'waiting' }, authorised: true, gate, request });
  // Same entry and a different entry, both while the first is in flight.
  const second = await performCall({ entry: { id: 'qe-1', status: 'waiting' }, authorised: true, gate, request });
  const third = await performCall({ entry: { id: 'qe-2', status: 'waiting' }, authorised: true, gate, request });
  assert.equal(second.status, 'busy');
  assert.equal(third.status, 'busy');
  assert.equal(log.length, 1, 'exactly one PATCH left the client');

  release();
  assert.equal((await first).status, 'called');
  assert.equal(gate.current(), '', 'the gate is released for the next call');

  // Reusable: the same entry may be called again later (a recall is a new act).
  const later = await performCall({ entry: { id: 'qe-1', status: 'waiting' }, authorised: true, gate, request: okRequest(log) });
  assert.equal(later.status, 'called');
});

test('POD-12 the gate survives a rejected request', async () => {
  const gate = createCallGate();
  await performCall({
    entry: { id: 'qe-1', status: 'waiting' },
    authorised: true,
    gate,
    request: async () => { throw new Error('offline'); },
  });
  assert.equal(gate.current(), '', 'a failure must not wedge the control');
});

test('POD-12 the call module has no audio dependency at all', () => {
  const src = fs.readFileSync(path.join(FE, 'lib', 'queue', 'queue-call.js'), 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/[^\n]*/g, '');
  assert.equal(/announce|audio|speech|play/i.test(src), false,
    'queue operations and playback stay independent');
  // And the page's handler never touches the announcer either.
  const body = handlerBody('callEntry');
  assert.equal(/announce/i.test(body), false, 'the handler does not speak');
  assert.equal(/await\s+announce/.test(PAGE), false);
});

// ---------------------------------------------------------------------------
// Required tests 4, 7, 8 and 10: the page wiring
// ---------------------------------------------------------------------------

test('POD-12 the control is gated on the effective call permission', () => {
  // Owner decision D: `queue.manage` holders always have Call; a caller with
  // queue.consult but not queue.manage has it only where the organization
  // enabled doctor queue-calling. The server enforces the same rule.
  assert.match(PAGE, /const canCall = canManage \|\| \(canConsult && doctorCallingEnabled\)/);
  assert.match(PAGE, /\{canCall && isCallable\(r\) && \(/,
    'the button exists only for an authorised user on a callable entry');
  assert.match(PAGE, /onClick=\{\(\) => callEntry\(r\)\}/);
  assert.match(PAGE, /<button className="btn btn-sm" disabled=\{!!busy \|\| !!calling\}/,
    'the button is disabled while a queue operation is pending');
  assert.match(PAGE, /const canManage = can\('queue\.manage'\)/);
  assert.match(PAGE, /const canCall = canManage/);
  assert.match(PAGE, /authorised: canCall/,
    'the handler and the button use the same decision');
  assert.match(PAGE, /\/queue-calling-config/,
    'the policy is read from the server, not assumed');
  assert.match(PAGE, /const callGate = React\.useRef\(createCallGate\(\)\)/);
});

test('POD-12 the page refreshes — and therefore announces — only on success', () => {
  const body = handlerBody('callEntry');
  const calledAt = body.indexOf("result.status === 'called'");
  const refreshAt = body.indexOf('loadQueue()');
  assert.ok(calledAt > 0, 'the success branch exists');
  assert.ok(refreshAt > calledAt, 'the refetch sits inside the success branch');
  assert.equal((body.match(/loadQueue\(\)/g) || []).length, 1,
    'a failed request never refreshes the list, so it never announces');
  assert.match(body, /result\.status === 'failed'\) \{\s*setError\(t\('callFailed'\)/,
    'a failure is surfaced as an error, not as a notice');
  assert.match(body, /setNotice\(t\('calledNotice'\)\)/);
});

test('POD-12 a refresh that reveals a called entry produces one announcement', () => {
  // This is the existing W2 tracker, unchanged: the refetch after a successful
  // call is what turns `waiting` into an announced `called` transition.
  const before = trackCalledTransitions(new Map(), [
    { id: 'qe-1', status: 'waiting' },
    { id: 'qe-2', status: 'called' },
  ]);
  assert.deepEqual(before.transitioned, [], 'loading the page announces nothing');

  const after = trackCalledTransitions(before.next, [
    { id: 'qe-1', status: 'called' },
    { id: 'qe-2', status: 'called' },
  ]);
  assert.deepEqual(after.transitioned.map((e) => e.id), ['qe-1']);

  const again = trackCalledTransitions(after.next, [
    { id: 'qe-1', status: 'called' },
    { id: 'qe-2', status: 'called' },
  ]);
  assert.deepEqual(again.transitioned, [], 'repeated renders do not repeat the announcement');
});

test('POD-12 the announcement seam is unchanged and unawaited', () => {
  assert.match(PAGE, /trackCalledTransitions\(calledTracker\.current, entries\)/);
  assert.match(PAGE, /transitioned\.forEach\(\(entry\) => announceOnCall\(entry\)\)/);
  assert.equal(/await\s+announceOnCall/.test(PAGE), false);
  const seam = handlerBody('announceOnCall');
  // QUE-006 / W2 moved the payload into the delivery announcer so that the server
  // call event is claimed before anything plays. The seam still announces a call
  // as an event, writes no queue state, and still never waits for audio.
  assert.match(seam, /callAnnouncer\.announceCall\(entry, \{ source: 'event' \}\)/);
  assert.equal(/apiFetch/.test(seam), false, 'announcing never writes queue state');
  const announcer = fs.readFileSync(
    path.join(FE, 'lib', 'announcements', 'call-announcer.js'), 'utf8');
  assert.match(announcer, /action: 'call'/, 'the announcement is a call');
  assert.match(announcer, /claimRequest\(entry, state\)/, 'the claim precedes playback');
});

test('POD-12 every caption the Call control needs is bilingual', () => {
  for (const key of ['call', 'calledNotice', 'callFailed', 'pleaseWait']) {
    assert.ok(key in DICT.bn, `bn.${key} is missing`);
    assert.ok(key in DICT.en, `en.${key} is missing`);
    assert.ok(String(DICT.bn[key]).trim().length > 0, `bn.${key} is empty`);
    assert.ok(String(DICT.en[key]).trim().length > 0, `en.${key} is empty`);
  }
  // The button label is not the status label: "Call" is an act, "Called" a state.
  assert.notEqual(DICT.en.call, DICT.en.calledKey);
  assert.notEqual(DICT.bn.call, DICT.bn.calledKey);
});

// ---------------------------------------------------------------------------
// MP-08 — the recall control
// ---------------------------------------------------------------------------

test('MP-08 a recall is its own action, not a repeated call', () => {
  assert.equal(RECALL_ACTION, 'recall');
  assert.notEqual(RECALL_ACTION, CALL_ACTION);
  // The server records it as a call event (queuing/events.py counts both), so
  // the identity rule is unchanged: a new history record, a new `qce:` id.
  assert.match(QUEUE_API, /_NEXT_STATUS = \{[\s\S]*?"recall": "called"/);
});

test('MP-08 only an already-called entry is recallable', () => {
  assert.equal(isRecallable({ id: 'qe-1', status: 'called' }), true);
  for (const status of ['waiting', 'in_consultation', 'completed', 'cancelled', 'no_show', 'skipped', '']) {
    assert.equal(isRecallable({ id: 'qe-1', status }), false, status);
  }
  for (const junk of [null, undefined, {}, { id: 7, status: 'called' }, 'qe-1']) {
    assert.equal(isRecallable(junk), false, JSON.stringify(junk));
  }
  // The two controls never overlap: one status, one button.
  assert.equal(isCallable({ id: 'qe-1', status: 'called' }), false);
});

test('MP-08 a recall sends exactly the recall payload', async () => {
  const log = [];
  const result = await performCall({
    entry: { id: 'qe-1', status: 'called' },
    authorised: true,
    gate: createCallGate(),
    action: RECALL_ACTION,
    request: okRequest(log),
  });
  assert.equal(result.status, 'called');
  assert.equal(result.action, RECALL_ACTION);
  assert.deepEqual(log, [{ id: 'qe-1', payload: { action: 'recall', reason: '' } }]);
});

test('MP-08 a recall of an ineligible entry sends nothing', async () => {
  const log = [];
  for (const status of ['waiting', 'completed', 'skipped']) {
    const result = await performCall({
      entry: { id: 'qe-1', status },
      authorised: true,
      gate: createCallGate(),
      action: RECALL_ACTION,
      request: okRequest(log),
    });
    assert.equal(result.status, 'ineligible', status);
  }
  assert.deepEqual(log, [], 'nothing was sent');
});

test('MP-08 an unknown action is refused before any request exists', async () => {
  const log = [];
  const result = await performCall({
    entry: { id: 'qe-1', status: 'called' },
    authorised: true,
    gate: createCallGate(),
    action: 'call_again',
    request: okRequest(log),
  });
  assert.equal(result.status, 'unsupported');
  assert.deepEqual(log, []);
});

test('MP-08 a recall shares the single-flight gate with a call', async () => {
  const log = [];
  const gate = createCallGate();
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  const request = async (id, payload) => { log.push({ id, payload }); await pending; };

  const call = performCall({ entry: { id: 'qe-1', status: 'waiting' }, authorised: true, gate, request });
  const recall = await performCall({
    entry: { id: 'qe-2', status: 'called' }, authorised: true, gate, action: RECALL_ACTION, request,
  });
  assert.equal(recall.status, 'busy', 'two announcements may not be in flight');
  assert.equal(log.length, 1);
  release();
  assert.equal((await call).status, 'called');
  assert.equal(gate.current(), '');
});


test('MP-08 the tracker treats a new call event as a new call', () => {
  // `called -> called`: the status never moves, so only the event id can tell
  // the browser that the patient was called again.
  const loaded = trackCalledTransitions(new Map(), [
    { id: 'qe-1', status: 'called', call_event_id: 'qce:qe-1:0' },
  ]);
  assert.deepEqual(loaded.transitioned, [], 'seeded, never announced on load');

  const same = trackCalledTransitions(loaded.next, [
    { id: 'qe-1', status: 'called', call_event_id: 'qce:qe-1:0' },
  ]);
  assert.deepEqual(same.transitioned, [], 'a repeated render announces nothing');

  const recalled = trackCalledTransitions(same.next, [
    { id: 'qe-1', status: 'called', call_event_id: 'qce:qe-1:3' },
  ]);
  assert.deepEqual(recalled.transitioned.map((e) => e.call_event_id), ['qce:qe-1:3'],
    'a new server event is a new call, even though the status is unchanged');

  const again = trackCalledTransitions(recalled.next, [
    { id: 'qe-1', status: 'called', call_event_id: 'qce:qe-1:3' },
  ]);
  assert.deepEqual(again.transitioned, []);
});

test('MP-08 the tracker still announces the ordinary status transition', () => {
  const before = trackCalledTransitions(new Map(), [
    { id: 'qe-1', status: 'waiting', call_event_id: '' },
  ]);
  const after = trackCalledTransitions(before.next, [
    { id: 'qe-1', status: 'called', call_event_id: 'qce:qe-1:1' },
  ]);
  assert.deepEqual(after.transitioned.map((e) => e.id), ['qe-1'],
    'one announcement, not two, when status and event change together');
});

test('MP-08 the page wires a recall control to the same gate', () => {
  assert.match(PAGE, /\{canCall && isRecallable\(r\) && \(/,
    'the recall button exists only for an authorised user on a called entry');
  assert.match(PAGE, /onClick=\{\(\) => recallEntry\(r\)\}/);
  const body = handlerBody('recallEntry');
  assert.match(body, /action: RECALL_ACTION/, 'the recall action is explicit');
  assert.match(body, /gate: callGate\.current/, 'the same single-flight gate');
  assert.match(body, /result\.status === 'called'\) \{\s*setNotice\(t\('recalledNotice'\)\)/);
  assert.equal((body.match(/loadQueue\(\)/g) || []).length, 1,
    'a failed recall never refreshes, so it never announces');
  assert.equal(/announce/i.test(body), false, 'the handler does not speak');
});

test('MP-08 every caption the Recall control needs is bilingual', () => {
  for (const key of ['recall', 'recalledNotice', 'recallFailed']) {
    assert.ok(key in DICT.bn, `bn.${key} is missing`);
    assert.ok(key in DICT.en, `en.${key} is missing`);
    assert.ok(String(DICT.bn[key]).trim().length > 0, `bn.${key} is empty`);
    assert.ok(String(DICT.en[key]).trim().length > 0, `en.${key} is empty`);
  }
  assert.notEqual(DICT.en.recall, DICT.en.call, 'Recall is not Call');
  assert.notEqual(DICT.bn.recall, DICT.bn.call);
});

