/* QUE-006 / W1 — announcement segment resolution for prerecorded playback.
 *
 * The approved wording lives in `content.js`; this module turns the *same*
 * payload into the ordered list of recorded clips that speak it. It is pure —
 * no DOM, no `Audio`, no timers — which is what lets the tests compare the
 * segment list against the approved text instead of trusting inspection.
 *
 * Asset ids come from the catalogue's recorded roles (`<lang>.phrase.<role>`,
 * `<lang>.digit.<0-9>`), never from file names, and the files are resolved
 * against the *pack's own* `basePath` + manifest. A new English or Bangla voice
 * — or version 2 of either — is therefore new data, not new code (assignment
 * §4.1/§4.5, W1 requirement 12).
 *
 * Deliberate refusals, never silent substitutions:
 *   - an unsupported language is refused, never mapped to another language;
 *   - an unspeakable token is refused rather than read aloud (content.js rule);
 *   - a room with no digits is refused rather than spelled out letter by letter;
 *   - a required asset the manifest does not list fails the whole announcement
 *     *before* any audio element is created (roadmap §8.1 AC-3).
 *
 * The one non-speech segment is the catalogue's own `intentional-pause` asset
 * (300 ms of silence, `en.phrase.room-suffix`). The manifest's note says an
 * engine must insert a pause there, not speak it, so it becomes a timed gap
 * carrying the catalogue's duration. No inter-clip gap is invented anywhere
 * else: POD-3 (pause policy) is still an open owner decision.
 */
import { ANNOUNCEMENT_LANGUAGES, buildAnnouncement } from './content.js';

/** Where a pack's files live when it does not say otherwise. */
export const DEFAULT_BASE_PATH = '/audio';

/** What one segment is. */
export const SEGMENT_KIND = Object.freeze({
  PHRASE: 'phrase',
  DIGIT: 'digit',
  PAUSE: 'pause',
});

/**
 * Recorded roles per language. A pack may override these (`pack.roles`) if a
 * future catalogue names its clips differently; the built-in catalogue uses
 * exactly these ids.
 */
export const ROLES = Object.freeze({
  en: Object.freeze({
    prefix: 'en.phrase.token-number',
    noRoom: 'en.phrase.no-room',
    roomPrefix: 'en.phrase.proceed-to-room',
    roomSuffix: 'en.phrase.room-suffix',
  }),
  bn: Object.freeze({
    prefix: 'bn.phrase.token-number',
    noRoom: 'bn.phrase.no-room',
    roomPrefix: 'bn.phrase.room-prefix',
    roomSuffix: 'bn.phrase.room-locative',
  }),
});

const BN_DIGIT_RE = /[\u09E6-\u09EF]/g;

/** Bangla digits → ASCII, so asset ids stay language-neutral. */
export function toAsciiDigits(value) {
  return String(value == null ? '' : value).replace(
    BN_DIGIT_RE, (d) => String(d.charCodeAt(0) - 0x09e6));
}

/** Every digit in *value*, in order, as single ASCII characters. */
export function digitsOf(value) {
  const found = toAsciiDigits(value).match(/[0-9]/g);
  return found ? found : [];
}

/** `basePath` + `file`, with exactly one slash between them. */
export function joinBasePath(basePath, file) {
  const base = String(basePath == null || basePath === '' ? DEFAULT_BASE_PATH : basePath)
    .replace(/\/+$/, '');
  const name = String(file == null ? '' : file).replace(/^\.?\/+/, '');
  return base + '/' + name;
}

/** Accept a pack descriptor, a bare manifest, or `{manifest}` — always one shape. */
export function normalisePack(pack) {
  const source = pack && typeof pack === 'object' ? pack : {};
  const manifest = source.manifest && typeof source.manifest === 'object'
    ? source.manifest : source;
  const assets = Array.isArray(source.assets) ? source.assets
    : (Array.isArray(manifest.assets) ? manifest.assets : []);
  return {
    id: typeof source.id === 'string' ? source.id : '',
    language: typeof source.language === 'string' ? source.language : '',
    version: Number.isFinite(source.version) ? source.version : 0,
    scope: source.scope === 'organization' ? 'organization' : 'platform',
    organizationId: source.organizationId || null,
    basePath: typeof source.basePath === 'string' && source.basePath
      ? source.basePath : DEFAULT_BASE_PATH,
    status: typeof source.status === 'string' ? source.status : 'draft',
    source: source.source === 'organization' || source.source === 'platform'
      ? source.source : 'builtin',
    roles: source.roles && typeof source.roles === 'object' ? source.roles : null,
    manifest,
    assets,
  };
}

/** Asset id → asset, for one pack's manifest. */
export function indexAssets(pack) {
  const index = new Map();
  normalisePack(pack).assets.forEach((asset) => {
    if (asset && typeof asset.id === 'string' && asset.id) index.set(asset.id, asset);
  });
  return index;
}

function rolesFor(normalised, language) {
  if (normalised.roles && normalised.roles[language]) return normalised.roles[language];
  return ROLES[language] || null;
}

function digitIds(language, digits) {
  return digits.map((digit) => language + '.digit.' + digit);
}

function toSegment(asset, pack) {
  const kind = asset.contentStatus === 'intentional-pause'
    ? SEGMENT_KIND.PAUSE
    : (asset.category === 'digit' ? SEGMENT_KIND.DIGIT : SEGMENT_KIND.PHRASE);
  const seconds = Number(asset.durationSeconds);
  return {
    assetId: asset.id,
    src: joinBasePath(pack.basePath, asset.playbackFile),
    kind,
    spokenText: typeof asset.spokenText === 'string' ? asset.spokenText : '',
    durationMs: kind === SEGMENT_KIND.PAUSE && Number.isFinite(seconds)
      ? Math.round(seconds * 1000) : 0,
  };
}

/**
 * Resolve the ordered clips for one announcement.
 *
 * @param {{token?: unknown, room?: unknown}} input same payload as `buildAnnouncement`
 * @param {object} pack pack descriptor or manifest
 * @returns {{ok: true, language: string, packId: string, version: number,
 *            source: string, basePath: string, segments: Array<object>,
 *            spokenText: string, approvedText: string, fields: object}
 *          | {ok: false, reason: string, missing?: string[], packId?: string}}
 */
export function resolveSegments(input, pack) {
  const normalised = normalisePack(pack);
  const language = normalised.language;
  if (!ANNOUNCEMENT_LANGUAGES.includes(language)) {
    return { ok: false, reason: 'unsupported_language' };
  }
  if (!normalised.assets.length) {
    return { ok: false, reason: 'manifest_unavailable', packId: normalised.id };
  }
  const roles = rolesFor(normalised, language);
  if (!roles) return { ok: false, reason: 'unsupported_language' };

  // The wording contract is content.js's, not this module's: if it refuses the
  // payload, playback refuses it for the same reason.
  const content = buildAnnouncement(input, language);
  if (!content.ok) return { ok: false, reason: content.reason };

  const tokenDigits = digitsOf(content.fields.tokenNumber);
  if (!tokenDigits.length) return { ok: false, reason: 'unspeakable_token' };

  const room = content.fields.room;
  const roomDigits = room ? digitsOf(room) : [];
  if (room && !roomDigits.length) return { ok: false, reason: 'unspeakable_room' };

  const ids = [roles.prefix, ...digitIds(language, tokenDigits)];
  if (room) {
    ids.push(roles.roomPrefix, ...digitIds(language, roomDigits), roles.roomSuffix);
  } else {
    ids.push(roles.noRoom);
  }

  const index = indexAssets(normalised);
  const missing = ids.filter((id) => {
    const asset = index.get(id);
    return !asset || typeof asset.playbackFile !== 'string' || !asset.playbackFile;
  });
  if (missing.length) {
    return { ok: false, reason: 'missing_asset', missing, packId: normalised.id, language };
  }

  const segments = ids.map((id) => toSegment(index.get(id), normalised));
  return {
    ok: true,
    language,
    packId: normalised.id,
    version: normalised.version,
    source: normalised.source,
    basePath: normalised.basePath,
    segments,
    // Clips are separate utterances, so they are joined with a space: two digit
    // clips are "one" + "zero", never the word "onezero".
    spokenText: segments.map((segment) => segment.spokenText).join(' '),
    approvedText: content.text,
    fields: content.fields,
  };
}
