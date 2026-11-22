/**
 * QUE-006 — composed-announcement preview page.
 *
 * Two jobs, one shared rule set:
 *
 *   1. play the 20 generated sample WAVs (byte-identical concatenations built by
 *      `compose-wav.mjs`), with the caption and the clip timeline beside each one;
 *   2. compose any token/room on the fly from the delivered clips, using
 *      `compose.mjs` — the very module the generator used — so the page cannot
 *      drift from the samples it is reviewing.
 *
 * Wording is never written here. The caption comes from
 * `frontend/lib/announcements/content.js` (`buildAnnouncement`), imported over
 * HTTP, which is the module the product itself uses. If the approved templates
 * change, this page changes with them.
 *
 * Playback goes through one Web Audio path for both jobs: buffers are fetched
 * from the delivered files, decoded, and scheduled at exact offsets, so a
 * junction pause is a scheduling gap and never an edit to a file. A clip that
 * fails to load or decode aborts the announcement and says which clip failed —
 * it is never skipped silently.
 */

import {
  DEFAULT_PAUSE_MS,
  MAX_DIGITS,
  PAUSE_OPTIONS_MS,
  ROLE_LABELS,
  digitAssetId,
  pauseBefore,
  planSegments,
} from './compose.mjs';
import { buildAnnouncement } from '/announcements/content.js';

const DATA_URL = '/generated/data.json';
const REVIEW_URL = '/generated/review-template.csv';

/** @type {Record<string, string>} what each review-template column asks for */
const REVIEW_FIELD_HELP = {
  sample_id: 'Copied from this page — do not retype.',
  sample_number: 'The row number (1–20) so a filled row can be matched back.',
  language: 'en or bn, as generated.',
  announcement_type: 'with_room or no_room, as generated.',
  token: 'Token number spoken in the sample.',
  room: 'Room number spoken, or empty for a no-room sample.',
  expected_text: 'The approved wording; the caption you heard.',
  duration_seconds: 'File duration, measured from the written file.',
  sha256_12: 'First 12 hex characters of the sample hash — identifies the exact bytes.',
  segment_count: 'How many clips were concatenated.',
  verdict: 'pass, fail, or needs-fix. Leave empty until you have listened.',
  intelligibility_1_5: '1 unintelligible … 5 effortlessly understood, over a clinic speaker.',
  pronunciation_1_5: '1 wrong word or digit … 5 correct and natural. Bangla needs a fluent speaker.',
  natural_prosody_1_5: '1 robotic or wrongly stressed … 5 like a person at a desk.',
  digit_clarity_1_5: '1 digits run together or are clipped … 5 every digit separate and clear.',
  room_clarity_1_5: '1 room number unclear … 5 unmistakable, or n/a for no-room.',
  junction_pause_ok: 'yes if the joins sound right at 0 ms; no if a pause is needed.',
  audible_artefacts: 'none, clipping, noise, or other — say where.',
  observations: 'What you actually heard, in your own words.',
  defect_severity: 'none, minor, or major.',
  follow_up_action: 'Nothing, or the asset to re-record and why.',
  reviewer: 'Your name.',
  review_date: 'Date of the listening session (YYYY-MM-DD).',
};

const state = {
  data: null,
  assets: new Map(),
  samples: [],
  playingId: null,
};

/** Playback engine state. */
let context = null;
let sources = [];
let playToken = 0;
let stopTimer = null;
const bufferCache = new Map();

const $ = (id) => document.getElementById(id);

/**
 * Write the page-level status line.
 * @param {string} text
 * @param {'info'|'ok'|'warn'|'error'} [tone]
 */
function setStatus(text, tone = 'info') {
  const node = $('status');
  if (!node) return;
  node.textContent = text;
  if (tone === 'info') node.removeAttribute('data-tone');
  else node.setAttribute('data-tone', tone);
}

/** @param {number} seconds */
function formatSeconds(seconds) {
  return `${Number(seconds).toFixed(3)} s`;
}

/** @param {string} value */
function shortHash(value) {
  return String(value || '').slice(0, 12);
}

/** @param {string} tag @param {string} [className] @param {string} [text] */
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}


/**
 * Fetch and decode one clip, once per session.
 * @param {string} url
 * @returns {Promise<AudioBuffer>}
 */
async function decodeClip(url) {
  if (bufferCache.has(url)) return bufferCache.get(url);
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${url} answered HTTP ${response.status}`);
  const bytes = await response.arrayBuffer();
  if (bytes.byteLength < 44) {
    throw new Error(`${url} returned ${bytes.byteLength} bytes — too short to be a WAV`);
  }
  const audioContext = ensureContext();
  const buffer = await audioContext.decodeAudioData(bytes);
  bufferCache.set(url, buffer);
  return buffer;
}

/** @returns {AudioContext} */
function ensureContext() {
  if (!context) {
    const Ctor = window.AudioContext || window.webkitAudioContext;
    if (!Ctor) throw new Error('this browser has no Web Audio support');
    context = new Ctor();
  }
  if (context.state === 'suspended') context.resume();
  return context;
}

/** Stop whatever is playing and clear the row highlight. */
function stopPlayback() {
  playToken += 1;
  if (stopTimer) clearTimeout(stopTimer);
  stopTimer = null;
  for (const source of sources) {
    try { source.stop(); } catch { /* already ended */ }
  }
  sources = [];
  markPlaying(null);
}

/** @param {string|null} id */
function markPlaying(id) {
  state.playingId = id;
  for (const row of document.querySelectorAll('#samples-body tr')) {
    row.dataset.playing = String(row.dataset.sampleId === id);
  }
}

/**
 * Schedule a sequence of clips back to back.
 *
 * Each item is `{url, assetId, pauseBeforeMs}`; the pause is applied as a gap in
 * the schedule, never as audio. Resolves when playback finishes (or rejects with
 * the failing clip's message), so the caller can report a real completion rather
 * than an optimistic one.
 *
 * @param {Array<{url: string, assetId: string, pauseBeforeMs?: number}>} items
 * @returns {Promise<{seconds: number, superseded?: boolean}>}
 */
async function playSequence(items) {
  stopPlayback();
  const token = playToken;
  const audioContext = ensureContext();

  const decoded = [];
  for (const item of items) {
    let buffer;
    try {
      buffer = await decodeClip(item.url);
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      throw new Error(`could not load ${item.assetId}: ${reason}`);
    }
    decoded.push({ item, buffer });
  }

  const begin = audioContext.currentTime + 0.08;
  let cursor = begin;
  const scheduled = [];
  for (const entry of decoded) {
    cursor += Math.max(0, Number(entry.item.pauseBeforeMs) || 0) / 1000;
    const source = audioContext.createBufferSource();
    source.buffer = entry.buffer;
    source.connect(audioContext.destination);
    source.start(cursor);
    scheduled.push(source);
    cursor += entry.buffer.duration;
  }
  sources = scheduled;

  const seconds = cursor - begin;
  const last = scheduled[scheduled.length - 1];
  await new Promise((resolve) => {
    let settled = false;
    const done = () => {
      if (settled) return;
      settled = true;
      resolve();
    };
    last.onended = done;
    if (token !== playToken) done();
  });
  if (token !== playToken) return { seconds, superseded: true };
  sources = [];
  markPlaying(null);
  return { seconds };
}

/* ------------------------------------------------------------------ data ---- */

/** Load the generated indexes the page is built from. */
async function loadData() {
  const response = await fetch(DATA_URL, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${DATA_URL} answered HTTP ${response.status}`);
  const data = await response.json();
  if (!data || !Array.isArray(data.samples) || data.samples.length === 0) {
    throw new Error(`${DATA_URL} contains no samples — run compose-wav.mjs first`);
  }
  state.data = data;
  state.samples = data.samples;
  state.assets = new Map((data.assets || []).map((asset) => [asset.id, asset]));
  return data;
}

/** Fill the header facts from the index, not from hard-coded prose. */
function renderFacts() {
  const { data } = state;
  const contract = data.contract || {};
  $('fact-contract').textContent = `${contract.sampleRate} Hz · ${contract.channels === 1 ? 'mono' : `${contract.channels} ch`} · ${contract.bitsPerSample}-bit PCM`;
  const bn = state.samples.filter((sample) => sample.language === 'bn').length;
  $('fact-samples').textContent = `${state.samples.length} samples (${state.samples.reduce((sum, sample) => sum + sample.segments.length, 0)} clip copies, ${bn} Bangla)`;
  const summary = data.summary || {};
  $('fact-catalogue').textContent = summary.catalogueUnchanged
    ? `untouched — ${summary.catalogueFilesHashed} files hashed before and after`
    : 'UNVERIFIED — the generator did not confirm the catalogue was unchanged';
  $('fact-generated').textContent = String(data.generatedAt || '').replace('T', ' ').replace('.000Z', ' UTC').replace('Z', ' UTC');
}

/**
 * An ordered clip list with the pause before each clip.
 *
 * @param {Array<{assetId: string, role: string, durationSeconds: number, pauseBeforeMs: number}>} segments
 * @returns {HTMLOListElement}
 */
function segmentList(segments) {
  const list = el('ol', 'timeline');
  segments.forEach((segment, position) => {
    const item = el('li');
    if (segment.pauseBeforeMs > 0) {
      item.appendChild(el('span', 'pause', `+${segment.pauseBeforeMs} ms pause · `));
    }
    const asset = state.assets.get(segment.assetId);
    const label = ROLE_LABELS[segment.role] || segment.role;
    item.appendChild(document.createTextNode(`${position + 1}. ${label} — ${segment.assetId} (${formatSeconds(segment.durationSeconds)})`));
    if (asset && asset.speech && asset.speech.speechStartSeconds == null) {
      item.appendChild(el('span', 'silent', ' — deliberate silence: punctuation-only asset, not spoken'));
    }
    list.appendChild(item);
  });
  return list;
}

/** @param {object} sample */
function timelineFor(sample) {
  const details = el('details');
  details.appendChild(el('summary', null, `${sample.segments.length} clips`));
  details.appendChild(segmentList(sample.segments));
  return details;
}

/** Render one table row per generated sample. */
function renderSamples() {
  const body = $('samples-body');
  body.replaceChildren();

  state.samples.forEach((sample, index) => {
    const row = el('tr');
    row.dataset.sampleId = sample.id;
    row.dataset.language = sample.language;

    const number = el('td', null, String(index + 1));
    number.dataset.label = '#';

    const identity = el('td');
    identity.dataset.label = 'Sample';
    identity.appendChild(el('span', 'id', sample.id));
    identity.appendChild(el('span', 'hash', `${shortHash(sample.sha256)} · ${sample.segments.length} clips`));

    const pattern = el('td', null, sample.announcementTypeLabel);
    pattern.dataset.label = 'Pattern';

    const caption = el('td', 'caption');
    caption.dataset.label = 'Caption';
    if (sample.language === 'bn') caption.appendChild(el('span', 'bn', sample.expectedText));
    else caption.textContent = sample.expectedText;

    const duration = el('td', 'dur', formatSeconds(sample.durationSeconds));
    duration.dataset.label = 'Duration';

    const playCell = el('td');
    playCell.dataset.label = 'Play';
    const button = el('button', 'secondary', 'Play');
    button.type = 'button';
    button.setAttribute('aria-label', `Play sample ${index + 1}: ${sample.expectedText}`);
    button.addEventListener('click', () => { void playSample(sample, button); });
    playCell.appendChild(button);

    const timelineCell = el('td');
    timelineCell.dataset.label = 'Timeline';
    timelineCell.appendChild(timelineFor(sample));

    row.append(number, identity, pattern, caption, duration, playCell, timelineCell);
    body.appendChild(row);
  });
}

/* -------------------------------------------------------------- playback ---- */

/**
 * Play one generated sample WAV.
 * @param {object} sample
 * @param {HTMLButtonElement} button
 */
async function playSample(sample, button) {
  const label = sample.expectedText;
  markPlaying(sample.id);
  button.disabled = true;
  setStatus(`Playing ${sample.id} — ${label}`);
  try {
    const { seconds } = await playSequence([
      { url: `/${sample.url}`, assetId: sample.id, pauseBeforeMs: 0 },
    ]);
    setStatus(`${sample.id} finished — ${seconds.toFixed(3)} s played, ${label}`, 'ok');
  } catch (error) {
    markPlaying(null);
    setStatus(`Sample ${sample.id} could not be played: ${error instanceof Error ? error.message : error}`, 'error');
  } finally {
    button.disabled = false;
  }
}

/** The samples the filter currently shows. */
function visibleSamples() {
  const filter = $('language-filter').value;
  return state.samples.filter((sample) => filter === 'all' || sample.language === filter);
}

/** Play every visible sample in order, stopping at the first failure. */
async function playAllVisible() {
  const queue = visibleSamples();
  if (queue.length === 0) {
    setStatus('No samples match the filter.', 'warn');
    return;
  }
  const button = $('play-all');
  button.disabled = true;
  try {
    for (let index = 0; index < queue.length; index += 1) {
      const sample = queue[index];
      markPlaying(sample.id);
      setStatus(`Playing ${index + 1} of ${queue.length} — ${sample.id} — ${sample.expectedText}`);
      const { superseded } = await playSequence([
        { url: `/${sample.url}`, assetId: sample.id, pauseBeforeMs: 0 },
      ]);
      if (superseded) {
        setStatus('Playback stopped.', 'warn');
        return;
      }
    }
    setStatus(`All ${queue.length} samples played to completion.`, 'ok');
  } catch (error) {
    markPlaying(null);
    setStatus(`Playback stopped: ${error instanceof Error ? error.message : error}`, 'error');
  } finally {
    button.disabled = false;
    markPlaying(null);
  }
}

/* -------------------------------------------------------------- composer ---- */

/** Read the composer form. */
function readComposer() {
  return {
    language: $('language').value === 'bn' ? 'bn' : 'en',
    token: $('token').value.trim(),
    hasRoom: $('has-room').checked,
    room: $('room').value.trim(),
    pauseMs: Number($('pause').value) || 0,
  };
}

/** Populate the pause select from the shared rule set, default selected. */
function fillPauseOptions() {
  const select = $('pause');
  select.replaceChildren();
  for (const ms of PAUSE_OPTIONS_MS) {
    const option = el('option', null, ms === 0 ? '0 ms (as generated)' : `${ms} ms`);
    option.value = String(ms);
    if (ms === DEFAULT_PAUSE_MS) option.selected = true;
    select.appendChild(option);
  }
}

/** Clear the plan panel and show one message. */
function planMessage(text, tone = 'problem') {
  const host = $('plan');
  host.replaceChildren(el('p', tone, text));
}

/**
 * Compose and play one announcement from the delivered clips.
 *
 * @param {SubmitEvent} [event]
 */
async function runComposer(event) {
  if (event) event.preventDefault();
  const request = readComposer();

  // 1. Approved wording first: this is the product's own function, so a caption
  //    shown here is the caption the product would say.
  const announcement = buildAnnouncement(
    request.hasRoom ? { token: request.token, room: request.room } : { token: request.token },
    request.language,
  );
  if (!announcement.ok) {
    planMessage(`Cannot announce this: the product refuses the input with "${announcement.reason}". A token must contain a number; internal identifiers are refused rather than spoken.`);
    return;
  }

  // 2. Clip plan. `fields.room` is the room text as the product uses it, so a
  //    room that is not a plain number is refused *for audio* while the wording
  //    above stays visible — the two can legitimately disagree.
  const plan = planSegments({
    language: request.language,
    tokenDigits: announcement.fields.tokenNumber,
    roomDigits: announcement.fields.hasRoom ? announcement.fields.room : null,
  });
  if (!plan.ok) {
    const host = $('plan');
    host.replaceChildren(
      el('h3', null, 'Approved wording'),
      el('p', 'caption', announcement.text),
      el('p', 'problem', `No audio can be composed: ${plan.detail}.`),
    );
    return;
  }

  const missing = [];
  const segments = plan.segments.map((segment, index) => {
    const asset = state.assets.get(segment.assetId);
    if (!asset) missing.push(segment.assetId);
    return {
      assetId: segment.assetId,
      role: segment.role,
      pauseBeforeMs: pauseBefore(plan.segments, index, request.pauseMs),
      durationSeconds: asset ? asset.durationSeconds : null,
      url: asset ? `/${asset.url}` : null,
    };
  });
  if (missing.length > 0) {
    planMessage(`No audio can be composed: ${missing.join(', ')} is not in the delivered catalogue. Nothing is played rather than playing a partial announcement.`);
    return;
  }

  const spoken = segments.reduce((sum, segment) => sum + segment.durationSeconds, 0)
    + segments.reduce((sum, segment) => sum + segment.pauseBeforeMs / 1000, 0);

  const host = $('plan');
  host.replaceChildren();
  host.appendChild(el('h3', null, `${request.language === 'bn' ? 'Bangla' : 'English'} · ${announcement.fields.template === 'with_room' ? 'with room' : 'no room'} · ${request.pauseMs} ms junction pause`));
  host.appendChild(el('p', 'caption', announcement.text));
  host.appendChild(el('p', 'meta', `${segments.length} clips · ${formatSeconds(spoken)} of audio and silence · token ${announcement.fields.tokenNumber}${announcement.fields.room ? ` · room ${announcement.fields.room}` : ''}`));
  host.appendChild(segmentList(segments));

  const playButton = $('compose-play');
  playButton.disabled = true;
  setStatus(`Playing the composed announcement — ${announcement.text}`);
  try {
    const { seconds, superseded } = await playSequence(segments);
    if (superseded) setStatus('Playback stopped.', 'warn');
    else setStatus(`Composed announcement finished — ${seconds.toFixed(3)} s played, ${announcement.text}`, 'ok');
  } catch (error) {
    setStatus(`Playback stopped: ${error instanceof Error ? error.message : error}`, 'error');
  } finally {
    playButton.disabled = false;
  }
}

/* --------------------------------------------------------- review record ---- */

/**
 * Render the review-template columns from the CSV itself.
 *
 * Reading the header rather than a local copy means the page cannot describe a
 * template that differs from the file the reviewer downloads.
 */
async function renderReviewFields() {
  const tbody = $('review-fields');
  try {
    const response = await fetch(REVIEW_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const header = (await response.text()).replace(/^\uFEFF/, '').split(/\r?\n/, 1)[0];
    const columns = header.split(',').map((name) => name.trim()).filter(Boolean);
    if (columns.length === 0) throw new Error('the header row is empty');
    tbody.replaceChildren();
    for (const column of columns) {
      const row = el('tr');
      row.append(
        el('td', null, column),
        el('td', null, REVIEW_FIELD_HELP[column] || '(see the preparation report for the definition)'),
      );
      tbody.appendChild(row);
    }
  } catch (error) {
    const row = el('tr');
    const cell = el('td', null, `The review template could not be read: ${error instanceof Error ? error.message : error}. Generate it with make-review-template.mjs.`);
    cell.colSpan = 2;
    row.appendChild(cell);
    tbody.replaceChildren(row);
  }
}

/* ------------------------------------------------------------------ wiring -- */

function wireEvents() {
  $('language-filter').addEventListener('change', () => {
    const filter = $('language-filter').value;
    for (const row of document.querySelectorAll('#samples-body tr')) {
      row.hidden = filter !== 'all' && row.dataset.language !== filter;
    }
    setStatus(`${visibleSamples().length} sample(s) shown.`);
  });

  $('play-all').addEventListener('click', () => { void playAllVisible(); });
  $('stop-all').addEventListener('click', () => {
    stopPlayback();
    setStatus('Playback stopped.', 'warn');
  });

  $('has-room').addEventListener('change', (event) => {
    $('room').disabled = !event.target.checked;
  });

  $('composer').addEventListener('submit', (event) => { void runComposer(event); });
  $('compose-stop').addEventListener('click', () => {
    stopPlayback();
    setStatus('Playback stopped.', 'warn');
  });

  window.addEventListener('pagehide', stopPlayback);
}

async function init() {
  fillPauseOptions();
  wireEvents();
  await renderReviewFields();

  try {
    const data = await loadData();
    renderFacts();
    renderSamples();
    const unverified = data.summary && data.summary.catalogueUnchanged === false;
    setStatus(
      unverified
        ? `${state.samples.length} samples loaded, but the generator reported the catalogue may have changed — do not review until that is resolved.`
        : `${state.samples.length} samples loaded. Play one, or compose your own. Nothing is approved until the review record is signed.`,
      unverified ? 'error' : 'info',
    );
  } catch (error) {
    setStatus(
      `The sample collection could not be loaded: ${error instanceof Error ? error.message : error}. Generate it with "node scripts/que-006-audio/preview/compose-wav.mjs".`,
      'error',
    );
    $('samples-body').replaceChildren();
  }
}

void init();
