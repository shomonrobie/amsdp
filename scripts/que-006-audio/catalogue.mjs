/**
 * QUE-006 — audio generation catalogue as data.
 *
 * The single source of truth is
 * `docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md` (V1.0). This
 * module repeats its 28 rows in code so the generator, the validator and the
 * manifest writer cannot drift from each other, and provides two independent
 * cross-checks:
 *
 *   1. `diffAgainstDoc()` reads the catalogue markdown tables back and reports
 *      any row where the code and the document disagree (asset id, language,
 *      spoken text, filename).
 *   2. `diffComposedAgainstApproved()` rebuilds the four approved announcement
 *      sentences by concatenating the catalogue clips in the composition order
 *      `frontend/lib/announcements/content.js` declares, so a clip whose text
 *      cannot reproduce the approved wording is reported before audio is spent.
 *
 * Nothing here talks to the network. Spoken text is copied verbatim: no
 * translation, no paraphrase, no added words, no doctor name or honourific.
 */

import fs from 'node:fs';
import path from 'node:path';

export const CATALOGUE_DOC = 'docs/implementation/QUE-006_AUDIO_GENERATION_CATALOGUE.md';
export const CATALOGUE_VERSION = 'V1.0';

/** Punctuation-only asset: a spoken full stop would be unnatural (catalogue §2.1). */
export const PUNCTUATION_ASSET_ID = 'en.phrase.room-suffix';
/** Playback pause this asset stands for, in milliseconds. */
export const PUNCTUATION_PAUSE_MS = 300;

/**
 * The 28 catalogue assets, in catalogue order.
 *
 * @type {ReadonlyArray<{id: string, language: 'en'|'bn', category: 'phrase'|'number',
 *   spokenText: string, filename: string, required: boolean, usage: string,
 *   synthetic?: 'silence'}>}
 */
export const ASSETS = Object.freeze([
  // --- 2.1 Fixed announcement phrases (English) -----------------------------
  Object.freeze({ id: 'en.phrase.token-number', language: 'en', category: 'phrase', spokenText: 'Token number ', filename: 'en/phrase/token-number.wav', required: true, usage: 'Prefix before token number in all English announcements' }),
  Object.freeze({ id: 'en.phrase.proceed-to-room', language: 'en', category: 'phrase', spokenText: ', please proceed to Room ', filename: 'en/phrase/proceed-to-room.wav', required: true, usage: 'Between token number and room number in English with-room announcements' }),
  Object.freeze({ id: 'en.phrase.room-suffix', language: 'en', category: 'phrase', spokenText: '.', filename: 'en/phrase/room-suffix.wav', required: true, usage: 'Terminal full stop after room number in English with-room announcements', synthetic: 'silence' }),
  Object.freeze({ id: 'en.phrase.no-room', language: 'en', category: 'phrase', spokenText: ' please come to the front.', filename: 'en/phrase/no-room.wav', required: true, usage: 'Complete suffix in English no-room announcements' }),

  // --- 2.2 Digit components (English) --------------------------------------
  Object.freeze({ id: 'en.digit.0', language: 'en', category: 'number', spokenText: 'zero', filename: 'en/number/digit-0.wav', required: true, usage: 'Digit 0 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.1', language: 'en', category: 'number', spokenText: 'one', filename: 'en/number/digit-1.wav', required: true, usage: 'Digit 1 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.2', language: 'en', category: 'number', spokenText: 'two', filename: 'en/number/digit-2.wav', required: true, usage: 'Digit 2 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.3', language: 'en', category: 'number', spokenText: 'three', filename: 'en/number/digit-3.wav', required: true, usage: 'Digit 3 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.4', language: 'en', category: 'number', spokenText: 'four', filename: 'en/number/digit-4.wav', required: true, usage: 'Digit 4 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.5', language: 'en', category: 'number', spokenText: 'five', filename: 'en/number/digit-5.wav', required: true, usage: 'Digit 5 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.6', language: 'en', category: 'number', spokenText: 'six', filename: 'en/number/digit-6.wav', required: true, usage: 'Digit 6 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.7', language: 'en', category: 'number', spokenText: 'seven', filename: 'en/number/digit-7.wav', required: true, usage: 'Digit 7 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.8', language: 'en', category: 'number', spokenText: 'eight', filename: 'en/number/digit-8.wav', required: true, usage: 'Digit 8 in token and room numbers' }),
  Object.freeze({ id: 'en.digit.9', language: 'en', category: 'number', spokenText: 'nine', filename: 'en/number/digit-9.wav', required: true, usage: 'Digit 9 in token and room numbers' }),
  // --- 2.3 Digit components (Bangla) ---------------------------------------
  Object.freeze({ id: 'bn.digit.0', language: 'bn', category: 'number', spokenText: '০', filename: 'bn/number/digit-0.wav', required: true, usage: 'Digit ০ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.1', language: 'bn', category: 'number', spokenText: '১', filename: 'bn/number/digit-1.wav', required: true, usage: 'Digit ১ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.2', language: 'bn', category: 'number', spokenText: '২', filename: 'bn/number/digit-2.wav', required: true, usage: 'Digit ২ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.3', language: 'bn', category: 'number', spokenText: '৩', filename: 'bn/number/digit-3.wav', required: true, usage: 'Digit ৩ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.4', language: 'bn', category: 'number', spokenText: '৪', filename: 'bn/number/digit-4.wav', required: true, usage: 'Digit ৪ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.5', language: 'bn', category: 'number', spokenText: '৫', filename: 'bn/number/digit-5.wav', required: true, usage: 'Digit ৫ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.6', language: 'bn', category: 'number', spokenText: '৬', filename: 'bn/number/digit-6.wav', required: true, usage: 'Digit ৬ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.7', language: 'bn', category: 'number', spokenText: '৭', filename: 'bn/number/digit-7.wav', required: true, usage: 'Digit ৭ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.8', language: 'bn', category: 'number', spokenText: '৮', filename: 'bn/number/digit-8.wav', required: true, usage: 'Digit ৮ in token and room numbers' }),
  Object.freeze({ id: 'bn.digit.9', language: 'bn', category: 'number', spokenText: '৯', filename: 'bn/number/digit-9.wav', required: true, usage: 'Digit ৯ in token and room numbers' }),

  // --- 2.1 Fixed announcement phrases (Bangla) -----------------------------
  Object.freeze({ id: 'bn.phrase.token-number', language: 'bn', category: 'phrase', spokenText: 'টোকেন নম্বর ', filename: 'bn/phrase/token-number.wav', required: true, usage: 'Prefix before token number in all Bangla announcements' }),
  Object.freeze({ id: 'bn.phrase.room-prefix', language: 'bn', category: 'phrase', spokenText: ', কক্ষ ', filename: 'bn/phrase/room-prefix.wav', required: true, usage: 'Between token number and room number in Bangla with-room announcements' }),
  Object.freeze({ id: 'bn.phrase.room-locative', language: 'bn', category: 'phrase', spokenText: '-এ আসুন।', filename: 'bn/phrase/room-locative.wav', required: true, usage: 'Locative suffix after room number in Bangla with-room announcements' }),
  Object.freeze({ id: 'bn.phrase.no-room', language: 'bn', category: 'phrase', spokenText: ', অনুগ্রহ করে সামনে আসুন।', filename: 'bn/phrase/no-room.wav', required: true, usage: 'Complete suffix in Bangla no-room announcements' }),
]);
export const ASSET_BY_ID = new Map(ASSETS.map((asset) => [asset.id, asset]));
export const ASSET_IDS = ASSETS.map((asset) => asset.id);
export const CATALOGUE_ASSET_COUNT = ASSETS.length;

/** English and Bangla asset counts, derived — never typed by hand. */
export const COUNT_BY_LANGUAGE = ASSETS.reduce((acc, asset) => {
  acc[asset.language] = (acc[asset.language] || 0) + 1;
  return acc;
}, /** @type {Record<string, number>} */ ({}));

/** @param {'en'|'bn'} language */
export function assetsForLanguage(language) {
  return ASSETS.filter((asset) => asset.language === language);
}

/** @param {string} id */
export function getAsset(id) {
  const asset = ASSET_BY_ID.get(id);
  if (!asset) throw new Error(`Unknown catalogue asset id: ${id}`);
  return asset;
}

/**
 * Spoken-text overrides — where the recorded text must differ from the catalogue
 * cell, and why.
 *
 * This table exists so a deviation is *declared in code* rather than applied
 * invisibly. Each entry is a finding that the product owner still has to ratify;
 * it is reported in the run log and in the implementation report, never folded
 * silently into the catalogue table (which stays a faithful transcription of the
 * catalogue document, and therefore still diff-matches it).
 *
 * @type {Readonly<Record<string, {spokenText: string, reason: string}>>}
 */
export const SPOKEN_TEXT_OVERRIDES = Object.freeze({
  'en.phrase.no-room': Object.freeze({
    spokenText: ', please come to the front.',
    reason: 'The catalogue cell reads " please come to the front." and omits the leading comma. '
      + 'The approved English template is "Token number {number}, please come to the front." and the '
      + 'parallel Bangla row (", অনুগ্রহ করে সামনে আসুন।") does carry the comma, so without it the '
      + 'concatenated English sentence is unpunctuated ("...number 12 please come to the front"). '
      + 'Recorded with the comma; the catalogue document should be corrected by its owner.',
  }),
});

/**
 * The text actually used for a clip: the catalogue cell, or its declared
 * override. Keeps the leading/trailing padding that makes clips concatenate.
 *
 * @param {{id: string, spokenText: string}} asset
 */
export function recordedTextFor(asset) {
  const override = SPOKEN_TEXT_OVERRIDES[asset.id];
  return override ? override.spokenText : asset.spokenText;
}

/**
 * Rebuild the four approved announcement templates by concatenating the
 * catalogue clip texts in composition order, leaving the number and room slots
 * as `{number}` / `{room}` placeholders (the digit clips supply those).
 *
 * @returns {{en: {withRoom: string, noRoom: string}, bn: {withRoom: string, noRoom: string}}}
 */
export function composeTemplates() {
  const text = (id) => recordedTextFor(getAsset(id));
  return {
    en: {
      withRoom: text('en.phrase.token-number') + '{number}' + text('en.phrase.proceed-to-room') + '{room}' + text('en.phrase.room-suffix'),
      noRoom: text('en.phrase.token-number') + '{number}' + text('en.phrase.no-room'),
    },
    bn: {
      withRoom: text('bn.phrase.token-number') + '{number}' + text('bn.phrase.room-prefix') + '{room}' + text('bn.phrase.room-locative'),
      noRoom: text('bn.phrase.token-number') + '{number}' + text('bn.phrase.no-room'),
    },
  };
}

/**
 * Compare the composed catalogue templates with the approved templates in
 * `frontend/lib/announcements/content.js`.
 *
 * A mismatch is reported, never silently corrected: the catalogue is the source
 * of truth for what is recorded, and the approved wording is the source of truth
 * for what may be spoken. When the two disagree the difference is an open item
 * for the product owner.
 *
 * @param {{en: {withRoom: string, noRoom: string}, bn: {withRoom: string, noRoom: string}}} approved
 * @returns {Array<{language: string, variant: string, catalogue: string, approved: string}>}
 */
export function diffComposedAgainstApproved(approved) {
  const composed = composeTemplates();
  const findings = [];
  for (const language of ['en', 'bn']) {
    for (const variant of ['withRoom', 'noRoom']) {
      const fromCatalogue = composed[language][variant];
      const fromCode = approved[language][variant];
      if (fromCatalogue !== fromCode) {
        findings.push({ language, variant, catalogue: fromCatalogue, approved: fromCode });
      }
    }
  }
  return findings;
}

/**
 * Parse the catalogue markdown back into rows, so the table above can be proved
 * against the document rather than trusted.
 *
 * @param {string} markdown
 * @returns {Array<{id: string, language: 'en'|'bn', spokenText: string, filename: string}>}
 */
export function parseCatalogueDoc(markdown) {
  const rows = [];
  const rowRe = /^\|\s*`((?:en|bn)\.[^`]+)`\s*\|([^|]*)\|([^|]*)\|([^|]*)\|/;
  for (const line of String(markdown).split(/\r?\n/)) {
    const match = rowRe.exec(line);
    if (!match) continue;
    const [, id, rawLanguage, rawText, rawFilename] = match;
    const language = /Bangla/i.test(rawLanguage) ? 'bn' : 'en';
    const spokenText = rawText.trim().replace(/^`([\s\S]*)`$/, '$1');
    const filename = rawFilename.trim().replace(/^`([\s\S]*)`$/, '$1');
    rows.push({ id, language, spokenText, filename });
  }
  return rows;
}

/**
 * Diff the code catalogue against the catalogue document.
 *
 * @param {string} repoRootAbsolute
 * @returns {{ok: boolean, documentRows: number, mismatches: string[]}}
 */
export function diffAgainstDoc(repoRootAbsolute) {
  const docPath = path.join(repoRootAbsolute, CATALOGUE_DOC);
  if (!fs.existsSync(docPath)) {
    return { ok: false, documentRows: 0, mismatches: [`catalogue document not found: ${CATALOGUE_DOC}`] };
  }
  const rows = parseCatalogueDoc(fs.readFileSync(docPath, 'utf8'));
  const mismatches = [];
  const seen = new Set();

  for (const row of rows) {
    seen.add(row.id);
    const asset = ASSET_BY_ID.get(row.id);
    if (!asset) {
      mismatches.push(`${row.id}: in ${CATALOGUE_DOC} but missing from catalogue.mjs`);
      continue;
    }
    if (asset.language !== row.language) {
      mismatches.push(`${row.id}: language ${asset.language} in code vs ${row.language} in document`);
    }
    if (asset.spokenText !== row.spokenText) {
      mismatches.push(`${row.id}: spoken text ${JSON.stringify(asset.spokenText)} in code vs ${JSON.stringify(row.spokenText)} in document`);
    }
    if (asset.filename !== row.filename) {
      mismatches.push(`${row.id}: filename ${asset.filename} in code vs ${row.filename} in document`);
    }
  }
  for (const id of ASSET_IDS) {
    if (!seen.has(id)) mismatches.push(`${id}: in catalogue.mjs but absent from ${CATALOGUE_DOC}`);
  }
  return { ok: mismatches.length === 0, documentRows: rows.length, mismatches };
}

