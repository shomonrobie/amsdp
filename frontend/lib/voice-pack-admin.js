/* Voice-pack administration rules — MP-04 (Product Owner decision PO-12).
 *
 * MP-04 asks for one thing: *an operator configures and publishes a pack without
 * curl*, while **every `voice_pack_policy.py` refusal stays enforced
 * server-side**.  So this module deliberately mirrors the policy only to decide
 * what to *offer*; it never decides what is *allowed*.  A button rendered here
 * is a convenience — if the policy disagrees, the router answers 403/409/422 and
 * the page shows the server's refusal verbatim.
 *
 * The mirror is kept honest by tests (`tests/voice-pack-admin.test.mjs`) that
 * assert the same transitions, the same roles and the same selectability rule as
 * `backend/organization/voice_pack_policy.py`.  When the policy changes, the
 * test fails here rather than drifting silently.
 *
 * `ALLOW_SYNTHESIS_FALLBACK = false`: the interface never substitutes browser
 * speech for a missing pack, so nothing in this module offers such a toggle.
 */

/** Statuses, in lifecycle order, exactly as `PACK_STATUS` defines them. */
export const STATUSES = Object.freeze([
  'draft', 'validating', 'pending_review', 'approved', 'published', 'retired',
  'rejected',
]);

/** Only a published pack may be offered for production use. */
export const SELECTABLE_STATUS = 'published';

/** Roles that may read and configure the library (`VOICE_CONFIG_ROLES`). */
export const CONFIG_ROLES = Object.freeze(['super_admin', 'org_admin']);

/** The only role that may approve, publish, retire or release a pack. */
export const PLATFORM_ROLES = Object.freeze(['super_admin']);

/**
 * `action -> { from: [...statuses], roles: [...], note, capability }`.
 *
 * A copy of `TRANSITIONS` / `TRANSITION_ROLES` / `ACTION_CAPABILITY`, with the
 * capability carried so the page can explain a missing button in the same terms
 * the API would use.
 */
export const ACTIONS = Object.freeze({
  validate: {
    from: ['draft', 'rejected', 'validating'],
    roles: ['super_admin', 'org_admin'],
    capability: 'org.manage',
    note: '',
  },
  submit: {
    from: ['draft', 'rejected'],
    roles: ['super_admin', 'org_admin'],
    capability: 'org.manage',
    note: '',
  },
  approve: {
    from: ['pending_review'],
    roles: ['super_admin'],
    capability: 'platform.admin',
    note: 'vpReviewNote',
  },
  reject: {
    from: ['pending_review'],
    roles: ['super_admin'],
    capability: 'platform.admin',
    note: 'vpRejectNote',
  },
  publish: {
    from: ['approved'],
    roles: ['super_admin'],
    capability: 'platform.admin',
    note: '',
  },
  retire: {
    from: ['published', 'approved', 'pending_review', 'rejected'],
    roles: ['super_admin'],
    capability: 'platform.admin',
    note: '',
  },
  availability: {
    from: ['published'],
    roles: ['super_admin'],
    capability: 'platform.admin',
    note: '',
  },
});

/** Status → i18n key, so the screen never prints a raw slug. */
export const STATUS_LABELS = Object.freeze({
  draft: 'vpStatusDraft',
  validating: 'vpStatusValidating',
  pending_review: 'vpStatusPendingReview',
  approved: 'vpStatusApproved',
  published: 'vpStatusPublished',
  retired: 'vpStatusRetired',
  rejected: 'vpStatusRejected',
});

/** Bucket key -> i18n key, so grouping headings are translated. */
export const BUCKET_KEYS = Object.freeze({
  needsWork: 'vpNeedsWork',
  inReview: 'vpInReview',
  live: 'vpLive',
  archived: 'vpArchived',
});

/** Action -> i18n key, so a button carries no hard-coded English. */
export const ACTION_LABELS = Object.freeze({
  validate: 'vpActionValidate',
  submit: 'vpActionSubmit',
  approve: 'vpActionApprove',
  reject: 'vpActionReject',
  publish: 'vpActionPublish',
  retire: 'vpActionRetire',
  availability: 'vpActionAvailability',
});

/** The buckets the library is grouped into, in the order an operator works. */
export const BUCKETS = Object.freeze([
  { key: 'needsWork', statuses: ['draft', 'rejected', 'validating'] },
  { key: 'inReview', statuses: ['pending_review', 'approved'] },
  { key: 'live', statuses: ['published'] },
  { key: 'archived', statuses: ['retired'] },
]);

export function roleOf(user) {
  return String((user && user.role) || '');
}

/** May this user open the library at all? (The server still gates each route.) */
export function mayReadLibrary(user) {
  return CONFIG_ROLES.includes(roleOf(user));
}

/** Is this pack platform-wide (`organization_id === null`)? */
export function isPlatformPack(pack) {
  return !(pack && pack.organization_id);
}

/**
 * A pack the caller can administer at all.
 *
 * Mirrors `policy.require_pack_access` exactly, because over-hiding is a defect
 * too: `super_admin` may administer **any** pack (including a tenant's, which is
 * how a facility's pending version gets reviewed at all), a platform pack is
 * administered only by `super_admin`, and an organisation's pack only by that
 * organisation.  Anything else is the router's non-disclosing 404.
 */
export function isManageable(pack, user) {
  const role = roleOf(user);
  if (!CONFIG_ROLES.includes(role)) return false;
  if (PLATFORM_ROLES.includes(role)) return true;
  if (isPlatformPack(pack)) return false;
  const own = String((user && user.organization_id) || '');
  return !!own && String(pack.organization_id) === own;
}

export function statusLabelKey(status) {
  return STATUS_LABELS[status] || '';
}

/** Which bucket a status belongs to, so the library groups like the lifecycle. */
export function bucketOf(status) {
  const hit = BUCKETS.find((b) => b.statuses.indexOf(status) >= 0);
  return hit ? hit.key : 'needsWork';
}

/**
 * The actions to *offer* for *pack*, given *user*.
 *
 * Each entry is `{ action, labelKey, note, allowed, reason }`.  `allowed: false`
 * entries are returned rather than dropped so the screen can explain *why* a
 * step is unavailable (wrong status versus wrong role) instead of leaving the
 * operator to guess -- the server's answer would be 409 or 403 respectively.
 */
export function actionsFor(pack, user) {
  if (!pack || !pack.status) return [];
  const role = roleOf(user);
  const result = [];
  Object.keys(ACTIONS).forEach((action) => {
    const spec = ACTIONS[action];
    if (spec.from.indexOf(pack.status) < 0) return;
    if (action === 'availability' && !isPlatformPack(pack)) return;
    const roleOk = spec.roles.includes(role);
    const scopeOk = isManageable(pack, user);
    let reason = '';
    if (!isPlatformPack(pack) && !scopeOk) {
      reason = 'vpNotYourPack';
    } else if (!roleOk) {
      reason = 'vpPlatformOnly';
    }
    result.push({
      action,
      labelKey: ACTION_LABELS[action],
      note: spec.note,
      allowed: roleOk && scopeOk,
      reason: roleOk && scopeOk ? '' : reason,
    });
  });
  return result;
}

/** Is the pack still open to content replacement (`MUTABLE_STATUSES`)? */
export function isMutable(pack) {
  return !!pack && ['draft', 'rejected', 'validating', 'pending_review']
    .indexOf(pack.status) >= 0;
}

/**
 * Can this pack be selected for production use right now?
 *
 * Mirrors `check_selectable`: published, right language, and either the caller
 * organisation's own pack or a platform pack it has released.  The page shows
 * this so a tenant administrator sees that an unreleased platform pack exists but
 * cannot be chosen -- the same answer the configuration route gives.
 */
export function selectableFor(pack, user) {
  if (!pack || pack.status !== SELECTABLE_STATUS) return false;
  if (!isPlatformPack(pack)) {
    return !!user && String(pack.organization_id) === String(user.organization_id || '');
  }
  return !!pack.available_to_organizations;
}

/** Only these packs may be written into a configuration selection. */
export function selectablePacks(packs, user, language) {
  return (packs || []).filter((p) => (!language || p.language === language)
    && selectableFor(p, user));
}

/** The default option for a configuration `select`: "inherit the platform default". */
export const INHERIT = '';

/**
 * Build the body for `PUT .../announcement-config`.
 *
 * Only the keys the operator actually touched are sent: an untouched language
 * stays `undefined` (no change) rather than being sent as `null` (clear), because
 * `None` means *clear the override* and sending it by accident would silently
 * drop a facility's chosen voice.
 */
export function configPayload(draft) {
  const body = {};
  if (draft && draft.language) body.language = draft.language;
  const packs = {};
  Object.keys((draft && draft.voice_packs) || {}).forEach((lang) => {
    const value = draft.voice_packs[lang];
    if (value !== undefined) packs[lang] = value === INHERIT ? null : value;
  });
  if (Object.keys(packs).length) body.voice_packs = packs;
  return body;
}

/** `true` when the draft would send nothing — the API answers 422 for that. */
export function configPayloadIsEmpty(body) {
  return !body || Object.keys(body).length === 0;
}

/**
 * Describe a review refusal in the screen's language.
 *
 * A policy refusal arrives as `{ detail: "..." }` — the router re-raises
 * `PolicyError.detail` verbatim — so the keys below are **phrases that exist in
 * `voice_pack_policy.py` / `voice_packs.py` today**, not invented tags.  An
 * earlier version of this table listed eight machine tags (`pack_missing_metadata`,
 * `pack_not_validated`, …) that the policy never emits, which meant the mapping
 * never fired and quietly degraded to "show the English detail".  The test parses
 * the policy source and fails if a key here stops existing there.
 *
 * An unrecognised detail is shown verbatim rather than replaced by a vague
 * apology, because the operator needs the actual reason.
 */
export const REFUSAL_KEYS = Object.freeze({
  'must pass technical validation': 'vpRefuseNotValidated',
  'must be approved by a named reviewer': 'vpRefuseNotApproved',
  'a named reviewer and review time are required': 'vpRefuseHumanReview',
  'is not valid from status': 'vpRefuseWrongStatus',
  'pack version is immutable': 'vpRefuseImmutable',
  'insufficient permissions': 'vpPlatformOnly',
  'platform configuration is not available': 'vpRefusePlatformScope',
  'availability applies to platform packs only': 'vpRefuseAvailabilityScope',
  'only a published pack can be released': 'vpRefuseReleaseNeedsPublished',
  'no changes supplied': 'vpRefuseNoChanges',
});

export function refusalKey(detail) {
  const text = String(detail || '');
  const tag = Object.keys(REFUSAL_KEYS).find((k) => text.indexOf(k) >= 0);
  return tag ? REFUSAL_KEYS[tag] : '';
}

/** Group the library for display: bucket -> language -> versions, newest first. */
export function groupPacks(packs) {
  const groups = BUCKETS.map((b) => ({ key: b.key, items: [] }));
  const byKey = {};
  groups.forEach((g) => { byKey[g.key] = g; });
  (packs || []).slice().sort((a, b) => {
    if (a.language !== b.language) return a.language < b.language ? -1 : 1;
    if (a.voice_name !== b.voice_name) return a.voice_name < b.voice_name ? -1 : 1;
    return (b.version || 0) - (a.version || 0);
  }).forEach((p) => {
    const group = byKey[bucketOf(p.status)];
    if (group) group.items.push(p);
  });
  return groups.filter((g) => g.items.length > 0);
}

/** `bn v2` — the label a version is referred to by, never only its uuid-like id. */
export function packLabel(pack) {
  if (!pack) return '';
  const scope = isPlatformPack(pack) ? 'platform' : 'org';
  return pack.language + ' ' + (pack.voice_name || '') + ' v' + (pack.version || 1)
    + ' (' + scope + ')';
}

/** Statuses an operator may filter the library by, plus "all". */
export const FILTER_STATUSES = [''].concat(STATUSES);

/** Languages the registry accepts (`policy.LANGUAGES`). */
export const PACK_LANGUAGES = Object.freeze(['bn', 'en']);

/**
 * Has this facility configured anything of its own?
 *
 * `GET /api/v1/orgs/{id}/announcement-config` returns `organization` as the
 * *override* block only — the platform view carries an explicit `inherited` flag,
 * the organisation view does not — so an empty block is the honest signal that the
 * platform defaults are in force.  (The screen used to read
 * `view.organization.inherited`, which the organisation route never sends, so the
 * "inherited" hint could never appear.)
 */
export function hasOrgOverride(block) {
  if (!block) return false;
  if (block.language) return true;
  return Object.keys(block.voice_packs || {}).length > 0;
}

/**
 * The body `POST .../announcement-config/rollback` expects.
 *
 * One language, never both: English and Bangla roll back independently, and the
 * server picks the target (`policy.rollback_target`) — the screen does not guess
 * which earlier version is the right one.
 */
export function rollbackBody(language) {
  return { language };
}

/** Languages an operator may roll back — the policy's two, nothing invented. */
export const ROLLBACK_LANGUAGES = PACK_LANGUAGES;
