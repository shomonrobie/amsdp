/* QUE-006 / W3 — voice-pack selection and configuration precedence.
 *
 * Assignment §8.2 asks for an explicit precedence model, and §4.2 forbids an
 * organisation from reaching another organisation's packs. Both are decisions,
 * so both live here as pure functions the UI can be tested against:
 *
 *   1. the organisation's chosen pack for that language, if it is published,
 *      for the same language, and owned by that organisation or the platform;
 *   2. otherwise the platform default for that language;
 *   3. otherwise the built-in draft pack;
 *   4. otherwise nothing — `no_voice_pack`, never a different language, never a
 *      different personality, never browser speech.
 *
 * Every step down is reported (`sources`, `warnings`) so the UI can say which
 * pack is in force and why a configured one was refused. Nothing is silently
 * substituted, which is the whole point of writing it down.
 *
 * The server half of W3 (voice-pack storage, upload, validation, approval,
 * publication, permissions) is NOT implemented — see the W3 report: this host
 * cannot run the backend stack, so it was not shipped unverified.
 */

/** The lifecycle a pack moves through (assignment §4.5). */
export const PACK_STATUS = Object.freeze({
  DRAFT: 'draft',
  VALIDATING: 'validating',
  PENDING_REVIEW: 'pending_review',
  APPROVED: 'approved',
  PUBLISHED: 'published',
  RETIRED: 'retired',
  REJECTED: 'rejected',
});

/** Only a published pack may be selected for production use (§4.5). */
export const SELECTABLE_STATUS = 'published';

/** Warning codes, so the UI can translate rather than guess. */
export const SELECTION_WARNING = Object.freeze({
  NOT_FOUND: 'pack_not_found',
  NOT_PUBLISHED: 'pack_not_published',
  LANGUAGE_MISMATCH: 'pack_language_mismatch',
  FOREIGN_ORGANIZATION: 'pack_foreign_organization',
  NO_PACK: 'no_voice_pack',
});

const LANGUAGES = Object.freeze(['bn', 'en']);

function listOf(value) {
  return Array.isArray(value) ? value.filter((item) => item && typeof item === 'object') : [];
}

function configuredId(config, language) {
  const packs = config && typeof config === 'object' ? config.voice_packs : null;
  const id = packs && typeof packs === 'object' ? packs[language] : null;
  return typeof id === 'string' && id ? id : null;
}

/**
 * Is *pack* usable by *organizationId* for *language*?
 * @returns {{ok: true} | {ok: false, reason: string}}
 */
export function checkSelectable(pack, language, organizationId) {
  if (!pack || typeof pack !== 'object') return { ok: false, reason: SELECTION_WARNING.NOT_FOUND };
  if (pack.language !== language) {
    return { ok: false, reason: SELECTION_WARNING.LANGUAGE_MISMATCH };
  }
  if (pack.status !== SELECTABLE_STATUS) {
    return { ok: false, reason: SELECTION_WARNING.NOT_PUBLISHED };
  }
  const owner = pack.organizationId || pack.organization_id || null;
  if (owner && owner !== organizationId) {
    // A pack that belongs to another organisation is never selectable, and the
    // reason is reported without disclosing whose it is.
    return { ok: false, reason: SELECTION_WARNING.FOREIGN_ORGANIZATION };
  }
  return { ok: true };
}

function findById(packs, id) {
  if (!id) return null;
  return listOf(packs).find((pack) => pack.id === id) || null;
}

function pick({ language, organizationId, organization, platform, packs, builtin }) {
  const warnings = [];
  const wanted = [
    { source: 'organization', id: configuredId(organization, language) },
    { source: 'platform', id: configuredId(platform, language) },
  ];

  for (const candidate of wanted) {
    if (!candidate.id) continue;
    const pack = findById(packs, candidate.id);
    if (!pack) {
      warnings.push({ language, source: candidate.source, reason: SELECTION_WARNING.NOT_FOUND });
      continue;
    }
    const verdict = checkSelectable(pack, language, organizationId);
    if (!verdict.ok) {
      warnings.push({ language, source: candidate.source, reason: verdict.reason });
      continue;
    }
    return { pack, source: candidate.source, warnings };
  }

  const fallback = builtin && builtin[language] ? builtin[language] : null;
  if (fallback) return { pack: fallback, source: 'builtin', warnings };

  warnings.push({ language, source: 'builtin', reason: SELECTION_WARNING.NO_PACK });
  return { pack: null, source: 'none', warnings };
}

/**
 * Resolve the announcement configuration for one facility.
 *
 * @param {object} input
 * @param {{language?: string, voice_packs?: object}} [input.organization] org override
 * @param {{language?: string, voice_packs?: object}} [input.platform] platform default
 * @param {Array<object>} [input.packs] every pack the caller may see
 * @param {object} [input.builtin] `{ en: pack, bn: pack }` shipped draft packs
 * @param {string|null} [input.organizationId]
 * @returns {{language: string, packs: object, sources: object, warnings: Array<object>}}
 */
export function resolveAnnouncementConfig(input = {}) {
  const organizationId = input.organizationId || null;
  const organization = input.organization && typeof input.organization === 'object'
    ? input.organization : {};
  const platform = input.platform && typeof input.platform === 'object' ? input.platform : {};
  const packs = listOf(input.packs);
  const builtin = input.builtin && typeof input.builtin === 'object' ? input.builtin : {};

  const language = LANGUAGES.includes(organization.language) ? organization.language
    : (LANGUAGES.includes(platform.language) ? platform.language : 'bn');

  const resolved = {};
  const sources = {};
  const warnings = [];
  LANGUAGES.forEach((lang) => {
    const result = pick({ language: lang, organizationId, organization, platform, packs, builtin });
    resolved[lang] = result.pack;
    sources[lang] = result.source;
    warnings.push(...result.warnings);
  });

  return { language, packs: resolved, sources, warnings };
}
