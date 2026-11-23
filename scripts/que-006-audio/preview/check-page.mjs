#!/usr/bin/env node
/**
 * QUE-006 — drive the preview page in a real browser and check it works.
 *
 * The page is JavaScript: a passing `node --check` proves nothing about whether
 * the table renders, whether playback finishes, or whether a bad input is
 * refused. This script launches the Chromium browser already installed on the
 * machine (Chrome or Edge), talks to it over the DevTools protocol using Node's
 * built-in `WebSocket`, and asserts on the live DOM.
 *
 * No npm packages and no browser download: if neither browser is present the
 * script reports SKIPPED and exits 2, which the report must reproduce as
 * "not verified" rather than silently treating as a pass.
 *
 * Usage:
 *   node scripts/que-006-audio/preview/check-page.mjs [--port 8617] [--page-port 9300]
 *
 * The preview server must already be running (server.mjs).
 */

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const PROFILE_DIR = path.join(here, 'generated', '.chrome-profile');

const argv = process.argv.slice(2);
function option(name, fallback) {
  const index = argv.indexOf(name);
  const value = index >= 0 ? argv[index + 1] : undefined;
  return value && !value.startsWith('--') ? value : fallback;
}

const PAGE_PORT = Number(option('--port', 8617));
const DEBUG_PORT = Number(option('--page-port', 9300));
const PAGE_URL = `http://127.0.0.1:${PAGE_PORT}/`;

const CANDIDATES = [
  path.join(process.env['PROGRAMFILES'] || 'C:\\Program Files', 'Google', 'Chrome', 'Application', 'chrome.exe'),
  path.join(process.env['PROGRAMFILES(X86)'] || 'C:\\Program Files (x86)', 'Google', 'Chrome', 'Application', 'chrome.exe'),
  path.join(process.env['LOCALAPPDATA'] || '', 'Google', 'Chrome', 'Application', 'chrome.exe'),
  path.join(process.env['PROGRAMFILES'] || 'C:\\Program Files', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
  path.join(process.env['PROGRAMFILES(X86)'] || 'C:\\Program Files (x86)', 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
];

/** @returns {string|null} */
function findBrowser() {
  for (const candidate of CANDIDATES) {
    if (candidate && fs.existsSync(candidate)) return candidate;
  }
  return null;
}

/**
 * The harness does not start the server: an unreachable page must be reported as
 * such, not as a browser failure. This probe makes that distinction explicit.
 * @returns {Promise<boolean>}
 */
async function pageIsServed() {
  try {
    const response = await fetch(PAGE_URL, { method: 'GET' });
    const body = await response.text();
    return response.ok && body.includes('samples-body');
  } catch {
    return false;
  }
}

/** @param {number} ms */

/**
 * Minimal DevTools-protocol client over Node's built-in WebSocket.
 */
class Devtools {
  /** @param {string} url websocket debugger url */
  constructor(url) {
    this.url = url;
    this.nextId = 1;
    this.pending = new Map();
    this.errors = [];
  }

  /** @returns {Promise<void>} */
  connect() {
    return new Promise((resolve, reject) => {
      const socket = new WebSocket(this.url);
      this.socket = socket;
      const timer = setTimeout(() => reject(new Error('timed out connecting to the browser')), 20_000);
      socket.addEventListener('open', () => {
        clearTimeout(timer);
        resolve();
      });
      socket.addEventListener('error', (event) => {
        clearTimeout(timer);
        reject(new Error(`browser websocket error: ${event.message || 'unknown'}`));
      });
      socket.addEventListener('message', (event) => {
        const message = JSON.parse(String(event.data));
        if (message.id && this.pending.has(message.id)) {
          const { resolve: done, reject: fail } = this.pending.get(message.id);
          this.pending.delete(message.id);
          if (message.error) fail(new Error(`${message.error.message} (${message.error.code})`));
          else done(message.result);
          return;
        }
        if (message.method === 'Runtime.exceptionThrown') {
          const detail = message.params && message.params.exceptionDetails;
          const described = detail && detail.exception ? detail.exception.description : null;
          this.errors.push(`uncaught: ${described || (detail && detail.text) || 'unknown exception'}`);
        }
        if (message.method === 'Runtime.consoleAPICalled' && message.params && message.params.type === 'error') {
          const text = (message.params.args || []).map((arg) => arg.value ?? arg.description ?? '').join(' ');
          this.errors.push(`console.error: ${text}`);
        }
      });
    });
  }

  /**
   * @param {string} method
   * @param {object} [params]
   * @returns {Promise<any>}
   */
  send(method, params = {}) {
    const id = this.nextId;
    this.nextId += 1;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error(`${method} did not answer within 30 s`));
        }
      }, 30_000);
    });
  }

  /**
   * Evaluate an expression in the page and return its value.
   * @param {string} expression
   * @param {{awaitPromise?: boolean}} [options]
   */
  async evaluate(expression, options = {}) {
    const result = await this.send('Runtime.evaluate', {
      expression,
      awaitPromise: options.awaitPromise === true,
      returnByValue: true,
      userGesture: true,
    });
    if (result.exceptionDetails) {
      const detail = result.exceptionDetails;
      const described = detail.exception ? detail.exception.description : null;
      throw new Error(`page threw: ${described || detail.text}`);
    }
    return result.result ? result.result.value : undefined;
  }

  close() {
    try { this.socket.close(); } catch { /* already closed */ }
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));


/* ------------------------------------------------------------------ harness -- */

const results = [];

/**
 * @param {string} id
 * @param {string} title
 * @param {boolean} ok
 * @param {string} detail
 */
function record(id, title, ok, detail) {
  results.push({ id, title, ok, detail });
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${id.padEnd(6)} ${title}${detail ? ` — ${detail}` : ''}`);
}

/** Poll an async predicate until it is truthy or the deadline passes. */
async function until(predicate, { timeoutMs = 30_000, intervalMs = 100, label = 'condition' } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const value = await predicate();
    if (value) return value;
    await sleep(intervalMs);
  }
  throw new Error(`timed out after ${timeoutMs} ms waiting for ${label}`);
}

/** @param {number} port */
async function waitForDebugger(port) {
  return until(async () => {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }, { timeoutMs: 40_000, label: 'the DevTools endpoint' });
}

/** @param {number} port @param {string} url */
async function newPageTarget(port, url) {
  const response = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
  if (!response.ok) throw new Error(`could not open a page target: HTTP ${response.status}`);
  return response.json();
}

function readSamples() {
  const file = path.join(here, 'generated', 'samples.json');
  if (!fs.existsSync(file)) throw new Error(`${file} is missing — run compose-wav.mjs first`);
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}


/* ----------------------------------------------------------------- checks -- */

/**
 * The table must exist before anything else is worth testing.
 * @param {Devtools} page
 * @param {Array<object>} expected
 */
async function checkRender(page, expected) {
  const rows = await until(
    async () => {
      const count = await page.evaluate("document.querySelectorAll('#samples-body tr').length");
      return count === expected.length ? count : 0;
    },
    { label: `${expected.length} sample rows`, timeoutMs: 20_000 },
  ).catch(() => 0);
  if (rows === 0) {
    const diagnostic = await page.evaluate("document.getElementById('status').textContent");
    record('11.1', 'page loads and renders every sample row', false,
      `0 rows — the status line says: ${String(diagnostic).slice(0, 240)}`);
    return false;
  }
  record('11.1', 'page loads and renders every sample row', rows === expected.length, `${rows} of ${expected.length} rows`);

  const dom = await page.evaluate(`(() => Array.from(document.querySelectorAll('#samples-body tr')).map((row) => ({
    id: row.dataset.sampleId,
    language: row.dataset.language,
    caption: (row.querySelector('td.caption') || {}).textContent || '',
    playable: Boolean(row.querySelector('button')),
  })))()`);

  const idMismatch = expected.findIndex((sample, index) => !dom[index] || dom[index].id !== sample.id);
  record('11.2', 'sample ids render in the generated order', idMismatch === -1,
    idMismatch === -1 ? `${dom.length} ids in order` : `row ${idMismatch + 1} is "${dom[idMismatch] && dom[idMismatch].id}"`);

  const captionMismatch = expected.findIndex((sample, index) => !dom[index] || dom[index].caption.trim() !== sample.expectedText.trim());
  record('11.3', 'every caption equals the approved wording', captionMismatch === -1,
    captionMismatch === -1 ? `${dom.length} captions compared with samples.json` : `row ${captionMismatch + 1}: "${dom[captionMismatch] && dom[captionMismatch].caption}"`);

  const unplayable = dom.filter((row) => !row.playable).length;
  record('11.4', 'every row has a play button', unplayable === 0, `${dom.length - unplayable} of ${dom.length} rows`);
  return idMismatch === -1 && captionMismatch === -1 && unplayable === 0;
}

/** @param {Devtools} page @param {Array<object>} expected */
async function checkFilter(page, expected) {
  const bnExpected = expected.filter((sample) => sample.language === 'bn').length;
  const filtered = await page.evaluate(`(() => {
    const select = document.getElementById('language-filter');
    select.value = 'bn';
    select.dispatchEvent(new Event('change'));
    const rows = Array.from(document.querySelectorAll('#samples-body tr'));
    const visible = rows.filter((row) => !row.hidden);
    const visibleIds = visible.map((row) => row.dataset.sampleId);
    select.value = 'all';
    select.dispatchEvent(new Event('change'));
    return { visible: visible.length, visibleIds, restored: rows.filter((row) => !row.hidden).length };
  })()`);
  const allBangla = filtered.visibleIds.every((id) => {
    const sample = expected.find((entry) => entry.id === id);
    return sample ? sample.language === 'bn' : false;
  });
  record('11.5', 'the language filter hides exactly the other language',
    filtered.visible === bnExpected && allBangla && filtered.restored === expected.length,
    `${filtered.visible} Bangla rows shown, ${filtered.restored} rows restored`);
}

/** @param {Devtools} page @param {Array<object>} expected */
async function checkPlayback(page, expected) {
  const first = expected[0];
  const played = await page.evaluate(`(async () => {
    const started = Date.now();
    document.querySelector('#samples-body tr button').click();
    const status = document.getElementById('status');
    while (Date.now() - started < 60_000) {
      if (/finished|could not be played/i.test(status.textContent)) break;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    return { text: status.textContent, tone: status.getAttribute('data-tone'), wallMs: Date.now() - started };
  })()`, { awaitPromise: true });
  const ok = /finished/i.test(played.text) && played.tone === 'ok';
  record('11.6', 'a sample plays to completion', ok,
    `${played.wallMs} ms wall time for a ${first.durationSeconds} s file — ${played.text.slice(0, 110)}`);
}


/**
 * A Bangla sample, because the Bangla clips carry far more trailing silence and
 * are the only rows whose duration cannot be judged by eye.
 * @param {Devtools} page @param {Array<object>} expected
 */
async function checkBangla(page, expected) {
  const sample = expected.find((entry) => entry.language === 'bn' && entry.announcementType === 'with_room');
  const played = await page.evaluate(`(async () => {
    const row = document.querySelector('#samples-body tr[data-sample-id="${sample.id}"]');
    if (!row) return { missing: true };
    const started = Date.now();
    row.querySelector('button').click();
    const status = document.getElementById('status');
    while (Date.now() - started < 90_000) {
      if (/finished|could not be played/i.test(status.textContent)) break;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    return { text: status.textContent, tone: status.getAttribute('data-tone'), wallMs: Date.now() - started };
  })()`, { awaitPromise: true });
  const ok = !played.missing && /finished/i.test(played.text) && played.tone === 'ok'
    && played.wallMs >= sample.durationSeconds * 1000 * 0.9;
  record('11.7', 'a Bangla sample plays to completion at its full length', ok,
    `${sample.id}: ${played.wallMs} ms wall time for ${sample.durationSeconds} s — ${played.text.slice(0, 100)}`);
}

/** @param {Devtools} page */
async function checkReviewFields(page) {
  const csv = fs.readFileSync(path.join(here, 'generated', 'review-template.csv'), 'utf8').replace(/^\uFEFF/, '');
  const columns = csv.split(/\r?\n/, 1)[0].split(',');
  const rendered = await page.evaluate("Array.from(document.querySelectorAll('#review-fields tr td:first-child')).map((cell) => cell.textContent)");
  const same = rendered.length === columns.length && columns.every((column, index) => rendered[index] === column);
  record('11.8', 'the review-record table mirrors the CSV header', same,
    `${rendered.length} rows rendered from a ${columns.length}-column header`);
}

/** @param {Devtools} page */
async function checkRefusals(page) {

  const refused = await page.evaluate(`(() => {
    document.getElementById('token').value = '3f2a9c1e-0b44-4f2a-9a6b-1c2d3e4f5a6b';
    document.getElementById('has-room').checked = true;
    document.getElementById('room').value = '305';
    document.getElementById('composer').requestSubmit();
    return document.getElementById('plan').textContent;
  })()`);
  record('11.9', 'an internal identifier is refused, never spoken',
    refused.includes('Cannot announce this') && refused.includes('unspeakable_token'),
    refused.replace(/\s+/g, ' ').slice(0, 150));

  const room = await page.evaluate(`(() => {
    document.getElementById('token').value = '7';
    document.getElementById('has-room').checked = true;
    document.getElementById('room').disabled = false;
    document.getElementById('room').value = 'ICU-2';
    const before = document.getElementById('status').textContent;
    document.getElementById('composer').requestSubmit();
    const plan = document.getElementById('plan');
    return {
      text: plan.textContent,
      caption: (plan.querySelector('p.caption') || {}).textContent || '',
      statusChanged: document.getElementById('status').textContent !== before,
      timeline: plan.querySelectorAll('ol.timeline li').length,
      problem: Boolean(plan.querySelector('p.problem')),
    };
  })()`);
  record('11.10', 'a non-numeric room shows the wording but schedules no audio',
    room.text.includes('No audio can be composed') && room.caption.includes('ICU-2')
      && room.statusChanged === false && room.problem === true && room.timeline === 0,
    room.text.replace(/\s+/g, ' ').slice(0, 150));
}

/** @param {Devtools} page */
async function checkComposer(page) {
  const composed = await page.evaluate(`(async () => {
    document.getElementById('language').value = 'en';
    document.getElementById('token').value = '12';
    document.getElementById('has-room').checked = true;
    document.getElementById('room').disabled = false;
    document.getElementById('room').value = '305';
    document.getElementById('pause').value = '100';
    const started = Date.now();
    document.getElementById('composer').requestSubmit();
    const status = document.getElementById('status');
    while (Date.now() - started < 60_000) {
      if (/finished|stopped/i.test(status.textContent)) break;
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    const plan = document.getElementById('plan');
    return {
      text: status.textContent,
      tone: status.getAttribute('data-tone'),
      caption: (plan.querySelector('p.caption') || {}).textContent || '',
      timeline: plan.querySelectorAll('ol.timeline li').length,
      wallMs: Date.now() - started,
    };
  })()`, { awaitPromise: true });
  const ok = /finished/i.test(composed.text) && composed.tone === 'ok'
    && composed.caption.trim() === 'Token number 12, please proceed to Room 305.'
    && composed.timeline > 0;
  record('11.11', 'a hand-made announcement composes and plays to completion', ok,
    `${composed.wallMs} ms, ${composed.timeline} clips — ${composed.caption} — ${composed.text.slice(0, 90)}`);
}


/* ------------------------------------------------------------------- main -- */

async function main() {
  const browserPath = findBrowser();
  if (!browserPath) {
    console.log('SKIPPED — neither Chrome nor Edge was found on this machine.');
    console.log('          The page is therefore NOT verified in a browser. Say so in the report.');
    process.exitCode = 2;
    return;
  }

  if (!(await pageIsServed())) {
    console.error(`FAIL — nothing is serving ${PAGE_URL}.`);
    console.error(`       Start it first, in another terminal:  node scripts/que-006-audio/preview/server.mjs --port ${PAGE_PORT}`);
    process.exitCode = 2;
    return;
  }

  const payload = readSamples();
  const expected = payload.samples;

  console.log('QUE-006 — browser check of the composed-announcement preview');
  console.log('');
  console.log(`  browser : ${browserPath}`);
  console.log(`  page    : ${PAGE_URL}`);
  console.log('');

  fs.mkdirSync(PROFILE_DIR, { recursive: true });
  const child = spawn(browserPath, [
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--autoplay-policy=no-user-gesture-required',
    '--mute-audio',
    `--user-data-dir=${PROFILE_DIR}`,
    `--remote-debugging-port=${DEBUG_PORT}`,
    'about:blank',
  ], { stdio: 'ignore' });

  let page = null;
  const cleanup = () => {
    if (page) page.close();
    try { child.kill(); } catch { /* already gone */ }
    // The headless profile is scrap: never leave a browser profile in the tree.
    setTimeout(() => {
      try { fs.rmSync(PROFILE_DIR, { recursive: true, force: true }); } catch { /* Windows may still hold a handle */ }
    }, 500);
  };

  (async () => {
    await waitForDebugger(DEBUG_PORT);
    // Open a blank target first, then navigate: connecting before the page runs is
    // the only way Runtime.exceptionThrown can see an exception thrown at load.
    const target = await newPageTarget(DEBUG_PORT, 'about:blank');
    page = new Devtools(target.webSocketDebuggerUrl);
    await page.connect();
    await page.send('Runtime.enable');
    await page.send('Page.enable');
    await page.send('Page.navigate', { url: PAGE_URL });
    await until(async () => (await page.evaluate("Boolean(document.getElementById('status'))")), { label: 'the page markup' });
    await until(async () => (await page.evaluate('document.readyState')) === 'complete', { label: 'the page load' });

    const rendered = await checkRender(page, expected);
    if (rendered) {
      await checkFilter(page, expected);
      await checkPlayback(page, expected);
      await checkBangla(page, expected);
      await checkReviewFields(page);
      await checkRefusals(page);
      await checkComposer(page);
    }

    record('11.12', 'no uncaught exception and no console error', page.errors.length === 0,
      page.errors.length === 0 ? 'the console stayed clean for the whole session' : page.errors.join(' | ').slice(0, 220));

    cleanup();

    const failed = results.filter((result) => !result.ok);
    console.log('');
    if (failed.length === 0) {
      console.log(`PASS — ${results.length}/${results.length} browser checks passed.`);
    } else {
      console.log(`FAIL — ${failed.length} of ${results.length} browser checks failed: ${failed.map((result) => result.id).join(', ')}`);
      process.exitCode = 1;
    }
  })().catch((error) => {
    cleanup();
    console.error('');
    console.error(`FAIL — the browser check could not run: ${error instanceof Error ? error.message : error}`);
    process.exitCode = 1;
  });
}

await main();
