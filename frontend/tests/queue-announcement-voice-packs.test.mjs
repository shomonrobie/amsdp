/* QUE-006 / W3 — configuration precedence and organisation isolation.
 *
 * Assignment §8.2 requires an explicit precedence model and §4.2 requires that
 * an organisation can never reach another organisation's pack. Both are proven
 * here as pure rules, including the refusals, because a precedence order that is
 * only described in prose is not a precedence order.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  checkSelectable,
  PACK_STATUS,
  resolveAnnouncementConfig,
  SELECTION_WARNING,
} from '../lib/announcements/voice-packs.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const MANIFEST = JSON.parse(
  readFileSync(join(HERE, '..', 'public', 'audio', 'manifest.json'), 'utf8'));

function pack(id, language, overrides = {}) {
  return {
    id,
    language,
    version: 1,
    status: PACK_STATUS.PUBLISHED,
    basePath: '/audio/packs/' + id,
    manifest: MANIFEST,
    ...overrides,
  };
}

const BUILTIN = {
  en: pack('platform.en.draft.v1', 'en', { status: PACK_STATUS.DRAFT, basePath: '/audio' }),
  bn: pack('platform.bn.draft.v1', 'bn', { status: PACK_STATUS.DRAFT, basePath: '/audio' }),
};

test('W3 an organisation override wins over the platform default', () => {
  const packs = [
    pack('vp_platform_en_male_v1', 'en'),
    pack('vp_org_en_female_v1', 'en', { organizationId: 'org_a' }),
  ];
  const resolved = resolveAnnouncementConfig({
    organizationId: 'org_a',
    organization: { language: 'en', voice_packs: { en: 'vp_org_en_female_v1' } },
    platform: { language: 'bn', voice_packs: { en: 'vp_platform_en_male_v1' } },
    packs,
    builtin: BUILTIN,
  });
  assert.equal(resolved.language, 'en', 'the organisation language wins');
  assert.equal(resolved.packs.en.id, 'vp_org_en_female_v1');
  assert.equal(resolved.sources.en, 'organization');
  assert.equal(resolved.packs.bn.id, 'platform.bn.draft.v1', 'no org choice means builtin');
  assert.equal(resolved.sources.bn, 'builtin');
  assert.deepEqual(resolved.warnings, []);
});

test('W3 the platform default is used when the organisation has no override', () => {
  const packs = [pack('vp_platform_bn_male_v2', 'bn', { version: 2 })];
  const resolved = resolveAnnouncementConfig({
    organizationId: 'org_a',
    platform: { language: 'bn', voice_packs: { bn: 'vp_platform_bn_male_v2' } },
    packs,
    builtin: BUILTIN,
  });
  assert.equal(resolved.packs.bn.id, 'vp_platform_bn_male_v2');
  assert.equal(resolved.sources.bn, 'platform');
  assert.equal(resolved.packs.bn.version, 2);
});

test('W3 another organisation\'s pack is refused and reported, never used', () => {
  const packs = [pack('vp_org_b_en_v1', 'en', { organizationId: 'org_b' })];
  const resolved = resolveAnnouncementConfig({
    organizationId: 'org_a',
    organization: { voice_packs: { en: 'vp_org_b_en_v1' } },
    packs,
    builtin: BUILTIN,
  });
  assert.equal(resolved.packs.en.id, 'platform.en.draft.v1');
  assert.equal(resolved.sources.en, 'builtin');
  assert.deepEqual(resolved.warnings, [{
    language: 'en',
    source: 'organization',
    reason: SELECTION_WARNING.FOREIGN_ORGANIZATION,
  }]);
});

test('W3 an unpublished or retired pack is not selectable', () => {
  ['draft', 'validating', 'pending_review', 'approved', 'retired', 'rejected'].forEach((status) => {
    const verdict = checkSelectable(pack('vp_x', 'en', { status }), 'en', 'org_a');
    assert.equal(verdict.ok, false, status + ' must not be selectable');
    assert.equal(verdict.reason, SELECTION_WARNING.NOT_PUBLISHED);
  });
  assert.equal(checkSelectable(pack('vp_x', 'en'), 'en', 'org_a').ok, true);
});

test('W3 a language mismatch is a refusal, not a reroute', () => {
  const packs = [pack('vp_en', 'en')];
  const resolved = resolveAnnouncementConfig({
    organizationId: 'org_a',
    organization: { voice_packs: { bn: 'vp_en' } },
    packs,
    builtin: BUILTIN,
  });
  assert.equal(resolved.packs.bn.id, 'platform.bn.draft.v1');
  assert.equal(resolved.warnings[0].reason, SELECTION_WARNING.LANGUAGE_MISMATCH);
});

test('W3 a missing pack id and a missing catalogue are distinct facts', () => {
  const missing = resolveAnnouncementConfig({
    organizationId: 'org_a',
    organization: { voice_packs: { en: 'vp_ghost' } },
    packs: [],
    builtin: BUILTIN,
  });
  assert.equal(missing.warnings[0].reason, SELECTION_WARNING.NOT_FOUND);
  assert.equal(missing.packs.en.id, 'platform.en.draft.v1');

  const nothing = resolveAnnouncementConfig({ packs: [], builtin: {} });
  assert.equal(nothing.packs.en, null);
  assert.equal(nothing.sources.en, 'none');
  assert.deepEqual(nothing.warnings.map((w) => w.reason),
    [SELECTION_WARNING.NO_PACK, SELECTION_WARNING.NO_PACK]);
  assert.equal(nothing.language, 'bn', 'the documented default, not a guess per announcement');
});

test('W3 an invalid configured language falls back to the platform, then to bn', () => {
  assert.equal(resolveAnnouncementConfig({
    organization: { language: 'fr' }, platform: { language: 'en' }, builtin: BUILTIN,
  }).language, 'en');
  assert.equal(resolveAnnouncementConfig({
    organization: { language: 'fr' }, platform: { language: 'de' }, builtin: BUILTIN,
  }).language, 'bn');
});

test('W3 the queue panel resolves its pack through the precedence rule', () => {
  const panel = readFileSync(join(HERE, '..', 'components', 'queue', 'QueueAnnouncements.js'), 'utf8');
  assert.match(panel, /resolveAnnouncementConfig\(\{ builtin \}\)/);
  assert.match(panel, /pack = resolved\.packs\[language\]/);
});
