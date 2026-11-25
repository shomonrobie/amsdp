/* MP-10 / BR §25 — the walk-in form reflects the facility's placement policy.
 *
 * What this file proves:
 *   - the two client-side decisions are real code (`lib/queue/walk-in.js`) and
 *     are exercised directly — no React, no DOM;
 *   - the request body can never carry a placement policy, and can carry a
 *     position only where the facility's policy asks staff for one;
 *   - every policy label resolves in Bangla and English;
 *   - the page is wired to the organization endpoint, not to a local select;
 *   - the backend agrees: the request models no longer accept the retired field.
 *
 * Run: cd frontend && npm test        (node --test, no dependency added)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DICT } from '../lib/i18n.js';
import {
  PLACEMENT_POLICIES,
  STAFF_PLACEMENT,
  buildEnqueueBody,
  effectivePolicy,
  needsPosition,
  policyLabelKey,
} from '../lib/queue/walk-in.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');
const PAGE = fs.readFileSync(path.join(FE, 'pages', 'queue.js'), 'utf8');
const QUEUE_API = fs.readFileSync(
  path.join(REPO, 'backend', 'queuing', 'main.py'), 'utf8');
const PLACEMENT = fs.readFileSync(
  path.join(REPO, 'backend', 'queuing', 'placement.py'), 'utf8');

const readPolicy = (policy) => ({ walk_in_policy: policy });

test('an unknown or missing policy falls back to end_of_queue', () => {
  assert.equal(effectivePolicy(null), 'end_of_queue');
  assert.equal(effectivePolicy({}), 'end_of_queue');
  assert.equal(effectivePolicy({ walk_in_policy: 'round_robin' }), 'end_of_queue');
  for (const policy of PLACEMENT_POLICIES) {
    assert.equal(effectivePolicy(readPolicy(policy)), policy);
  }
});

test('only staff placement asks the operator for a position', () => {
  for (const policy of PLACEMENT_POLICIES) {
    assert.equal(needsPosition(readPolicy(policy)), policy === STAFF_PLACEMENT);
  }
  assert.equal(needsPosition(null), false, 'a failed read must not demand a position');
});

test('every policy label exists in Bangla and English', () => {
  for (const policy of PLACEMENT_POLICIES) {
    const key = policyLabelKey(policy);
    assert.ok(DICT.bn[key], `bn is missing ${key}`);
    assert.ok(DICT.en[key], `en is missing ${key}`);
    assert.ok(DICT.bn[key] !== DICT.en[key] || policy === 'end_of_queue',
      `${key} must be translated, not copied`);
  }
  assert.equal(policyLabelKey('nonsense'), 'endOfQueue', 'unknown labels are not raw ids');
});

test('the enqueue body never carries a placement policy', () => {
  for (const policy of PLACEMENT_POLICIES) {
    const built = buildEnqueueBody({
      doctorId: 'doc-1', patientId: 'pat-1', config: readPolicy(policy),
      position: '2',
    });
    assert.equal(built.ok, true);
    assert.equal('walk_in_policy' in built.body, false, `${policy} leaked a policy`);
    assert.deepEqual(Object.keys(built.body).sort(),
      policy === STAFF_PLACEMENT
        ? ['doctor_id', 'entry_source', 'patient_id', 'position']
        : ['doctor_id', 'entry_source', 'patient_id']);
  }
});

test('a position is sent only under staff placement', () => {
  const appended = buildEnqueueBody({
    doctorId: 'doc-1', patientId: 'pat-1', config: readPolicy('end_of_queue'),
    position: '2',
  });
  assert.equal('position' in appended.body, false, 'the position is not ours to send');

  const placed = buildEnqueueBody({
    doctorId: 'doc-1', patientId: 'pat-1', config: readPolicy('staff_placement'),
    position: '3',
  });
  assert.equal(placed.body.position, 3);
});

test('staff placement without a usable position is refused before the request', () => {
  for (const position of ['', null, undefined, 0, -1, '2.5', 'abc']) {
    const built = buildEnqueueBody({
      doctorId: 'doc-1', patientId: 'pat-1',
      config: readPolicy('staff_placement'), position,
    });
    assert.equal(built.ok, false, `accepted ${JSON.stringify(position)}`);
    assert.equal(built.error, 'position_required');
  }
});

test('a missing patient or doctor is refused before the request', () => {
  assert.deepEqual(buildEnqueueBody({ patientId: 'pat-1' }),
    { ok: false, error: 'doctor_required' });
  assert.deepEqual(buildEnqueueBody({ doctorId: 'doc-1' }),
    { ok: false, error: 'patient_required' });
});

test('the page reads the policy from the organization, not from a select', () => {
  assert.match(PAGE, /\/walk-in-config/, 'the policy comes from the server');
  assert.match(PAGE, /buildEnqueueBody\(/, 'the body is built by the tested module');
  assert.match(PAGE, /needsPosition\(placement\)/, 'the position field follows the policy');
  assert.match(PAGE, /policyLabelKey\(effectivePolicy\(placement\)\)/,
    'the label is translated, never the raw identifier');
  assert.equal(/walk_in_policy/.test(PAGE), false,
    'the page must not send the retired field');
  assert.equal(/WALK_POLICIES/.test(PAGE), false,
    'the local policy list is gone — the options belong to the platform');
});

test('the backend request models no longer accept the retired policy field', () => {
  assert.equal(/walk_in_policy\s*:\s*(str|Optional)/.test(QUEUE_API), false,
    'walk_in_policy must not be a request model field any more');
  for (const policy of PLACEMENT_POLICIES) {
    assert.ok(PLACEMENT.includes(policy),
      `backend placement does not know ${policy}`);
  }
});

test('the page never places a patient client-side', () => {
  // The position is the server's answer. The page may show it, but computing
  // one here would be a second, untestable placement implementation.
  assert.equal(/position\s*=\s*(max|Math\.max)/i.test(PAGE), false);
  assert.equal(/entry_source:\s*['"]/.test(PAGE), false,
    'the enqueue body belongs to lib/queue/walk-in.js');
});
