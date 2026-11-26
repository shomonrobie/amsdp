/* MP-04 — the voice-pack administration surface.
 *
 * The screen is JSX, so the rules it *offers* live in `lib/voice-pack-admin.js`
 * and are tested here.  The important assertion is not that the module is
 * self-consistent: it is that the module still matches
 * `backend/organization/voice_pack_policy.py`, which is the only thing that
 * decides what is allowed.  If the policy changes and the mirror does not, these
 * tests fail rather than letting the page offer a step the API will refuse.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  ACTIONS, ACTION_LABELS, BUCKET_KEYS, BUCKETS, CONFIG_ROLES, FILTER_STATUSES,
  INHERIT, PACK_LANGUAGES, PLATFORM_ROLES, REFUSAL_KEYS, ROLLBACK_LANGUAGES,
  SELECTABLE_STATUS, STATUSES, STATUS_LABELS, actionsFor, bucketOf, configPayload,
  configPayloadIsEmpty, groupPacks, hasOrgOverride, isManageable, isMutable,
  isPlatformPack, mayReadLibrary, packLabel, refusalKey, rollbackBody, roleOf,
  selectableFor, selectablePacks, statusLabelKey,
} from '../lib/voice-pack-admin.js';
import { DICT } from '../lib/i18n.js';
import { hasPermission } from '../lib/auth.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');

const PAGE = fs.readFileSync(path.join(FE, 'pages', 'voice-packs.js'), 'utf8');
const POLICY = fs.readFileSync(
  path.join(REPO, 'backend', 'organization', 'voice_pack_policy.py'), 'utf8');
const ROUTES = fs.readFileSync(
  path.join(REPO, 'backend', 'organization', 'voice_packs.py'), 'utf8');
const CONFIG = fs.readFileSync(
  path.join(REPO, 'backend', 'organization', 'announcement_config.py'), 'utf8');

/** The Python `PACK_STATUS` literal, as a name -> slug map. */
function policyStatuses() {
  const block = POLICY.slice(POLICY.indexOf('PACK_STATUS = {'),
    POLICY.indexOf('STATUSES: tuple'));
  const out = {};
  for (const m of block.matchAll(/"([A-Z_]+)": "([a-z_]+)"/g)) out[m[1]] = m[2];
  assert.ok(Object.keys(out).length >= 7, 'PACK_STATUS did not parse');
  return out;
}

/** `TRANSITIONS` as action -> { from, to }, read from the policy source. */
function policyTransitions() {
  const statuses = policyStatuses();
  const block = POLICY.slice(POLICY.indexOf('TRANSITIONS: dict'),
    POLICY.indexOf('TRANSITION_ROLES: dict'));
  const out = {};
  const re = /"([a-z_]+)": \(\s*\(([\s\S]*?)\),\s*PACK_STATUS\["([A-Z_]+)"\],?\s*\)/g;
  for (const m of block.matchAll(re)) {
    const from = [...m[2].matchAll(/PACK_STATUS\["([A-Z_]+)"\]/g)]
      .map((x) => statuses[x[1]]);
    out[m[1]] = { from, to: statuses[m[3]] };
  }
  assert.ok(Object.keys(out).length >= 6,
    'TRANSITIONS did not parse: ' + JSON.stringify(out));
  return out;
}

/** `TRANSITION_ROLES` as action -> role list. */
function policyTransitionRoles() {
  const end = POLICY.indexOf('ALLOW_SYNTHESIS_FALLBACK');
  const block = POLICY.slice(POLICY.indexOf('TRANSITION_ROLES: dict'),
    end < 0 ? POLICY.length : end);
  const out = {};
  /* `approve` and friends are written as `PLATFORM_ROLES`, not a literal
     tuple, so a named constant has to be resolved rather than silently skipped. */
  for (const m of block.matchAll(/"([a-z_]+)": (PLATFORM_ROLES|\(([^)]*)\)),/g)) {
    out[m[1]] = m[2] === 'PLATFORM_ROLES'
      ? policyTuple('PLATFORM_ROLES: tuple')
      : [...m[2].matchAll(/"([a-z_]+)"/g)].map((x) => x[1]);
  }
  assert.ok(Object.keys(out).length >= 6,
    'TRANSITION_ROLES did not parse: ' + JSON.stringify(out));
  return out;
}

/** A quoted tuple such as `VOICE_CONFIG_ROLES: tuple[str, ...] = ("a", "b")`. */
function policyTuple(name) {
  const at = POLICY.indexOf(name);
  assert.ok(at >= 0, name + ' is not declared in the policy');
  const line = POLICY.slice(at, POLICY.indexOf('\n', at) + 1);
  return [...line.matchAll(/"([a-z_]+)"/g)].map((m) => m[1]);
}

test('the transition table is the policy table, read from the policy file', () => {
  const expected = policyTransitions();
  const ours = Object.keys(ACTIONS).filter((a) => expected[a]).sort();
  assert.deepEqual(ours, Object.keys(expected).sort(),
    'the screen and the policy do not offer the same steps');
  for (const [action, spec] of Object.entries(expected)) {
    assert.deepEqual([...ACTIONS[action].from].sort(), [...spec.from].sort(),
      action + ': source statuses differ from TRANSITIONS');
  }
});

test('every action is gated on the same role the policy gates it on', () => {
  const expected = policyTransitionRoles();
  for (const [action, roles] of Object.entries(expected)) {
    assert.deepEqual([...ACTIONS[action].roles].sort(), [...roles].sort(),
      action + ': roles differ from TRANSITION_ROLES');
  }
  assert.deepEqual([...PLATFORM_ROLES], policyTuple('PLATFORM_ROLES: tuple'));
  assert.deepEqual([...CONFIG_ROLES], policyTuple('VOICE_CONFIG_ROLES: tuple'));
});

test('availability is a platform-only control on a published platform pack', () => {
  assert.deepEqual(ACTIONS.availability.roles, ['super_admin']);
  assert.deepEqual(ACTIONS.availability.from, ['published']);
  const offered = actionsFor({ status: 'published', organization_id: null },
    { role: 'org_admin', organization_id: 'org-1' });
  const availability = offered.find((a) => a.action === 'availability');
  assert.equal(availability.allowed, false,
    'an organisation administrator may not release a platform pack');
  assert.equal(availability.reason, 'vpPlatformOnly');
  assert.equal(offered.some((a) => ['approve', 'publish', 'retire']
    .includes(a.action) && a.allowed), false,
  'an organisation administrator can never approve, publish or retire');
});

test('a tenant pack is never manageable by another tenant', () => {
  const foreign = { status: 'draft', organization_id: 'org-2' };
  assert.equal(isManageable(foreign,
    { role: 'org_admin', organization_id: 'org-1' }), false);
  assert.equal(isManageable(foreign,
    { role: 'org_admin', organization_id: 'org-2' }), true);
  /* `policy.require_pack_access` lets the platform administrator administer any
     pack — support work depends on it, and `super_admin` is the only role that may
     approve or publish, so refusing here would make an organisation's
     `pending_review` version impossible to approve from any screen. */
  assert.equal(isManageable(foreign,
    { role: 'super_admin', organization_id: 'org-1' }), true,
  'the platform administrator administers any pack, as require_pack_access says');
  assert.ok(/def require_pack_access/.test(POLICY));
  assert.ok(/if role in PLATFORM_ROLES:\s*\n\s*return/.test(POLICY),
    'the policy short-circuits platform roles before the ownership check');
  assert.equal(isManageable({ status: 'draft', organization_id: null },
    { role: 'super_admin' }), true);
  assert.equal(isManageable({ status: 'draft', organization_id: 'org-1' },
    { role: 'branch_admin', organization_id: 'org-1' }), false);
  assert.equal(isManageable({ status: 'published', organization_id: null },
    { role: 'org_admin', organization_id: 'org-1' }), false,
  'a tenant administrator never administers a platform pack');
  assert.equal(mayReadLibrary({ role: 'branch_admin' }), false);
  assert.equal(mayReadLibrary({ role: 'org_admin' }), true);
  assert.equal(roleOf(null), '');
});

test('status, role and bucket vocabulary matches the policy exactly', () => {
  const expected = policyStatuses();
  assert.deepEqual([...STATUSES], Object.values(expected));
  assert.equal(SELECTABLE_STATUS, expected.PUBLISHED);
  assert.equal(STATUSES.length, Object.keys(STATUS_LABELS).length,
    'every status needs a label');
  for (const status of STATUSES) {
    const key = statusLabelKey(status);
    assert.ok(DICT.bn[key], status + ' has no Bangla label');
    assert.ok(DICT.en[key], status + ' has no English label');
  }
  for (const bucket of BUCKETS) {
    assert.ok(DICT.bn[BUCKET_KEYS[bucket.key]], bucket.key + ' heading has no Bangla');
    assert.ok(DICT.en[BUCKET_KEYS[bucket.key]], bucket.key + ' heading has no English');
    for (const status of bucket.statuses) {
      assert.equal(bucketOf(status), bucket.key,
        status + ' is in ' + bucketOf(status) + ', not ' + bucket.key);
      assert.ok(STATUSES.includes(status), 'unknown status in a bucket: ' + status);
    }
  }
  assert.deepEqual([...FILTER_STATUSES], [''].concat(STATUSES));
  assert.deepEqual([...PACK_LANGUAGES], policyTuple('LANGUAGES: tuple'));
});


test('selectability is the policy rule: published, own or released', () => {
  const user = { role: 'org_admin', organization_id: 'org-1' };
  assert.equal(selectableFor({ status: 'draft', organization_id: 'org-1' }, user), false);
  assert.equal(selectableFor({ status: 'published', organization_id: 'org-1' }, user), true);
  assert.equal(selectableFor({ status: 'published', organization_id: 'org-2' }, user), false,
    'another tenant\'s published pack is not selectable');
  assert.equal(selectableFor({ status: 'published', organization_id: null,
    available_to_organizations: false }, user), false,
  'an unreleased platform pack is not selectable');
  assert.equal(selectableFor({ status: 'published', organization_id: null,
    available_to_organizations: true }, user), true);

  const rows = [
    { id: 'own-bn', language: 'bn', status: 'published', organization_id: 'org-1' },
    { id: 'own-en', language: 'en', status: 'published', organization_id: 'org-1' },
    { id: 'released-bn', language: 'bn', status: 'published', organization_id: null,
      available_to_organizations: true },
    { id: 'withheld-bn', language: 'bn', status: 'published', organization_id: null,
      available_to_organizations: false },
    { id: 'draft-bn', language: 'bn', status: 'draft', organization_id: 'org-1' },
  ];
  assert.deepEqual(selectablePacks(rows, user, 'bn').map((p) => p.id),
    ['own-bn', 'released-bn']);
  assert.equal(selectablePacks(rows, user).length, 3);
});

test('a configuration change omits untouched languages and clears only on inherit', () => {
  assert.deepEqual(configPayload({ language: 'bn', voice_packs: {} }),
    { language: 'bn' });
  assert.deepEqual(
    configPayload({ language: '', voice_packs: { bn: 'pack-1' } }),
    { voice_packs: { bn: 'pack-1' } },
    'an untouched language must not be sent at all');
  assert.deepEqual(configPayload({ voice_packs: { bn: INHERIT } }),
    { voice_packs: { bn: null } },
    'clearing an override is explicit: null, never a missing key');
  assert.equal(configPayloadIsEmpty(configPayload({ language: '', voice_packs: {} })),
    true);
  assert.equal(configPayloadIsEmpty(configPayload({ voice_packs: { en: 'p' } })), false);
});

test('the library is grouped by lifecycle bucket, newest version first', () => {
  const packs = [
    { id: 'live', language: 'bn', voice_name: 'female', version: 1, status: 'published' },
    { id: 'old-draft', language: 'bn', voice_name: 'female', version: 1, status: 'draft' },
    { id: 'new-draft', language: 'bn', voice_name: 'female', version: 2, status: 'draft' },
    { id: 'review', language: 'bn', voice_name: 'female', version: 3, status: 'pending_review' },
    { id: 'gone', language: 'en', voice_name: 'male', version: 1, status: 'retired' },
  ];
  const groups = groupPacks(packs);
  assert.deepEqual(groups.map((g) => g.key), ['needsWork', 'inReview', 'live', 'archived']);
  assert.deepEqual(groups[0].items.map((p) => p.id), ['new-draft', 'old-draft']);
  assert.deepEqual(groupPacks([]), []);
});

test('a refusal is translated only when the phrase exists in the policy', () => {
  const sources = POLICY + '\n' + ROUTES + '\n' + CONFIG;
  for (const [phrase, key] of Object.entries(REFUSAL_KEYS)) {
    /* The map used to list invented machine tags (`pack_missing_metadata`, …)
       that no route ever emits, so it never fired.  Every phrase must exist in
       the server source, which is what makes this a mapping and not decoration. */
    assert.ok(sources.indexOf(phrase) >= 0,
      `"${phrase}" does not appear in the voice-pack policy, routes or config`);
    assert.equal(refusalKey('409: ' + phrase + ' — detail'), key);
    assert.ok(DICT.bn[key], phrase + ' has no Bangla label');
    assert.ok(DICT.en[key], phrase + ' has no English label');
  }
  assert.equal(refusalKey('something unexpected'), '');
  assert.equal(refusalKey(''), '');
  assert.equal(refusalKey(null), '');
});


test('the page is wired to the existing routes and decides nothing locally', () => {
  assert.ok(PAGE.includes("from '../lib/voice-pack-admin'"),
    'the page must import the tested module, not carry its own copy');
  assert.ok(PAGE.includes("'/api/v1/voice-packs'"), 'the library route is not called');
  assert.ok(PAGE.includes("+ '/' + action"),
    'the transition POST is built from the action name the policy defines');
  assert.ok(PAGE.includes('/preview'), 'audition is not wired');
  for (const action of Object.keys(ACTIONS)) {
    assert.ok(ROUTES.includes('"/{pack_id}/' + action + '"'),
      'the API exposes no /{pack_id}/' + action + ' route');
    assert.ok(ACTION_LABELS[action], action + ' has no button label');
    assert.ok(DICT.bn[ACTION_LABELS[action]], action + ' label has no Bangla string');
    assert.ok(DICT.en[ACTION_LABELS[action]], action + ' label has no English string');
  }
  assert.ok(CONFIG.includes('/api/v1/orgs/{org_id}/announcement-config'));
  assert.ok(CONFIG.includes('/api/v1/platform/announcement-config'));
  assert.ok(PAGE.includes('/announcement-config'), 'the configuration read is not wired');
  assert.equal(/(?<![\w.])fetch\s*\(/.test(PAGE), false,
    'the page must use apiFetch, which carries the token and the 401 handling');
});

test('the page never substitutes browser speech for a missing pack', () => {
  assert.equal(/speechSynthesis/i.test(PAGE), false);
  assert.equal(/SpeechSynthesisUtterance/.test(PAGE), false);
  assert.equal(/synthesis/i.test(PAGE), false);
  assert.ok(/ALLOW_SYNTHESIS_FALLBACK = False/.test(POLICY),
    'the policy constant must stay False; the screen offers no way to change it');
});

test('platform packs are recognised by an absent organization, like pack_owner', () => {
  assert.equal(isPlatformPack({ organization_id: null }), true);
  assert.equal(isPlatformPack({}), true);
  assert.equal(isPlatformPack({ organization_id: 'org-1' }), false);
  assert.equal(packLabel({ language: 'bn', voice_name: 'female', version: 2,
    organization_id: null }), 'bn female v2 (platform)');
  assert.equal(packLabel({ language: 'en', voice_name: 'male', version: 1,
    organization_id: 'org-1' }), 'en male v1 (org)');
  assert.equal(packLabel(null), '');
  assert.equal(isMutable({ status: 'draft' }), true);
  assert.equal(isMutable({ status: 'pending_review' }), true);
  assert.equal(isMutable({ status: 'published' }), false);
  assert.equal(isMutable({ status: 'approved' }), false);
});

test('the audit trail is never offered for deletion', () => {
  assert.equal(/\bdelete\b/i.test(PAGE), false,
    'a pack is retired, never deleted, so the page must not offer a delete');
  assert.ok(ROUTES.includes('"voice_pack.availability_changed"'),
    'releasing a pack is audited, and the page relies on it');
});


test('the availability call sends an explicit target, as the route demands', () => {
  /* `POST /{pack_id}/availability` takes `AvailabilityChange{available: bool}`.
     A body-less POST is a 422, and a toggle that sends "the opposite of what the
     label said" is worse, so the page must send the value it intends. */
  assert.ok(/class AvailabilityChange\(BaseModel\):\s*\n\s*available: bool/.test(ROUTES),
    'the route no longer takes an explicit `available` target');
  assert.ok(PAGE.includes("available: !pack.available_to_organizations"),
    'the availability call must send the intended value');
  assert.equal(/actionsFor\(pack, user\)\.filter\(\(a\) => a\.action !== 'availability'\)/
    .test(PAGE), true,
  'availability must be offered once, by the switch that can supply the value');
});


test('the configuration view is read as the server sends it', () => {
  /* `GET /orgs/{id}/announcement-config` returns `organization` as the override
     block only; the platform view carries `inherited`.  Reading `inherited` from
     the organisation block (as the screen first did) is always undefined, so the
     hint could never appear. */
  assert.ok(CONFIG.includes('"organization": org_block'));
  assert.ok(CONFIG.includes('"inherited": True'));
  assert.equal(hasOrgOverride({}), false);
  assert.equal(hasOrgOverride(null), false);
  assert.equal(hasOrgOverride({ voice_packs: {} }), false);
  assert.equal(hasOrgOverride({ language: 'bn' }), true);
  assert.equal(hasOrgOverride({ voice_packs: { bn: 'pack-1' } }), true);
  assert.ok(PAGE.includes('hasOrgOverride(view.organization)'),
    'the screen derives "inherited" from the override block it actually receives');
  assert.ok(PAGE.includes("view.inherited"),
    'the platform scope still reads the flag the platform route does send');
});

test('rollback is offered, and names only the language', () => {
  /* `POST /orgs/{org_id}/announcement-config/rollback` took `{language}` and chose
     the target itself.  It existed but no screen called it, so restoring an
     earlier approved version still required curl. */
  assert.ok(CONFIG.includes('/announcement-config/rollback'));
  assert.ok(/class RollbackRequest\(BaseModel\):\s*\n\s*language: str/.test(CONFIG),
    'the rollback body is a single language, not a pack id');
  assert.deepEqual(rollbackBody('bn'), { language: 'bn' });
  assert.deepEqual([...ROLLBACK_LANGUAGES], [...PACK_LANGUAGES]);
  assert.ok(PAGE.includes("/rollback"), 'the rollback route is not wired');
  assert.ok(PAGE.includes('rollbackBody(lang)'),
    'the rollback body is not built by the module');
  assert.ok(DICT.bn.vpRollback && DICT.en.vpRollback, 'rollback has no label');
  assert.ok(DICT.bn.vpRolledBack && DICT.en.vpRolledBack, 'rollback has no confirmation');
});

test('the page is gated on the capability the routes require', () => {
  /* `GET /voice-packs` and `GET /{id}/preview` require `org.read`; the page's own
     gate and the sidebar entry must ask for that same capability, and the
     client-side mirror must grant it to the role the policy allows to configure. */
  assert.ok(/require_permission\("org\.read"\)/.test(ROUTES),
    'the library route no longer requires org.read');
  assert.ok(PAGE.includes("can('org.read')"),
    'the page must ask for the capability the route enforces');
  const nav = fs.readFileSync(path.join(FE, 'components', 'AppShell.js'), 'utf8');
  assert.ok(/href: '\/voice-packs'/.test(nav), 'the library has no sidebar entry');
  assert.ok(hasPermission({ role: 'org_admin' }, 'org.read'),
    'org_admin holds org.read on the server, so the mirror must grant it');
  assert.equal(hasPermission({ role: 'branch_admin' }, 'org.read'), false,
    'branch_admin holds no org.read: voice configuration is organization-wide');
});

