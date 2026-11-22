#!/usr/bin/env node
/**
 * QUE-006 — static server for the composed-announcement preview.
 *
 * Serves one page from this folder and mount-points the read-only trees it needs:
 *
 *   /                 preview/            index.html, preview.css, preview.js, compose.mjs
 *   /announcements/   frontend/lib/announcements/   the approved wording module
 *   /audio/           frontend/public/audio/        the 28 delivered clips
 *   /samples/         preview/generated/samples/    the 20 composed WAVs
 *   /generated/       preview/generated/            samples.json, clip-analysis.json, data.json
 *
 * Why a server at all: `preview.js` imports `compose.mjs` as an ES module and
 * `fetch`es WAV bytes, and browsers refuse both from `file://`. Serving the two
 * trees from their real locations (rather than copying them into a staging
 * folder) is also what makes the page prove the delivered files, not copies.
 *
 * Nothing is written: the server is GET/HEAD only, binds to loopback by default,
 * refuses dotfiles, and resolves every request through a mount root so a crafted
 * path cannot escape it. It touches no product code and no database — it is a
 * reviewer's tool, started and stopped by hand.
 *
 * Usage:
 *   node scripts/que-006-audio/preview/server.mjs [--port 8616] [--host 127.0.0.1] [--quiet]
 */

import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { AUDIO_ROOT, REPO_ROOT } from '../lib/paths.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const GENERATED_DIR = path.join(here, 'generated');
const SAMPLES_DIR = path.join(GENERATED_DIR, 'samples');
const ANNOUNCEMENTS_DIR = path.join(REPO_ROOT, 'frontend', 'lib', 'announcements');

const argv = process.argv.slice(2);

/** @param {string} name @param {string|number} fallback */
function option(name, fallback) {
  const index = argv.indexOf(name);
  const value = index >= 0 ? argv[index + 1] : undefined;
  return value && !value.startsWith('--') ? value : fallback;
}

const PORT = Number(option('--port', process.env.QUE006_PREVIEW_PORT || 8616));
const HOST = String(option('--host', '127.0.0.1'));
const QUIET = argv.includes('--quiet');

const CONTENT_TYPES = new Map(Object.entries({
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.csv': 'text/csv; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.wav': 'audio/wav',
  '.mp3': 'audio/mpeg',
}));

/**
 * URL prefix -> directory on disk. Order matters: the first match wins, so the
 * catch-all `/` mount is last.
 */
const MOUNTS = [
  { prefix: '/announcements/', root: ANNOUNCEMENTS_DIR, label: 'frontend/lib/announcements' },
  { prefix: '/audio/', root: AUDIO_ROOT, label: 'frontend/public/audio' },
  { prefix: '/samples/', root: SAMPLES_DIR, label: 'preview/generated/samples' },
  { prefix: '/generated/', root: GENERATED_DIR, label: 'preview/generated' },
  { prefix: '/', root: here, label: 'preview' },
];

/**
 * Resolve a URL path to a file inside one mount, or explain why it was refused.
 *
 * @param {string} pathname
 * @returns {{file: string, mount: string}|{status: number, reason: string}}
 */
function resolveRequest(pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    return { status: 400, reason: 'malformed percent-encoding' };
  }
  if (decoded.includes('\0')) return { status: 400, reason: 'NUL byte in path' };

  const mount = MOUNTS.find((entry) => decoded === entry.prefix.slice(0, -1) || decoded.startsWith(entry.prefix));
  if (!mount) return { status: 404, reason: 'no mount for this path' };

  const relative = decoded === mount.prefix.slice(0, -1) ? '' : decoded.slice(mount.prefix.length);
  const segments = relative.split('/').filter(Boolean);
  if (segments.some((segment) => segment.startsWith('.'))) {
    return { status: 404, reason: 'dotfiles are not served' };
  }

  const target = path.resolve(mount.root, segments.join(path.sep));
  const within = path.relative(mount.root, target);
  if (within.startsWith('..') || path.isAbsolute(within)) {
    return { status: 404, reason: 'path escapes its mount' };
  }

  let file = target;
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
    return { status: 404, reason: 'not found' };
  }
  return { file, mount: mount.label };
}


const server = http.createServer((req, res) => {
  const method = req.method || 'GET';
  if (method !== 'GET' && method !== 'HEAD') {
    res.writeHead(405, { Allow: 'GET, HEAD', 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('This preview server is read-only.\n');
    return;
  }

  const pathname = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`).pathname;
  const resolved = resolveRequest(pathname);

  if (!('file' in resolved)) {
    res.writeHead(resolved.status, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(`${resolved.status} ${resolved.reason}\n`);
    if (!QUIET) console.log(`${resolved.status} ${pathname} — ${resolved.reason}`);
    return;
  }

  const type = CONTENT_TYPES.get(path.extname(resolved.file).toLowerCase()) || 'application/octet-stream';
  const size = fs.statSync(resolved.file).size;
  res.writeHead(200, {
    'Content-Type': type,
    'Content-Length': size,
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  });
  if (method === 'HEAD') {
    res.end();
  } else {
    fs.createReadStream(resolved.file).pipe(res);
  }
  if (!QUIET) console.log(`${method} ${pathname} — ${resolved.mount}/${path.basename(resolved.file)}`);
});

server.on('error', (error) => {
  const message = error && error.code === 'EADDRINUSE'
    ? `port ${PORT} is already in use — pass --port <number>`
    : String(error && error.message ? error.message : error);
  console.error(`\nQUE-006 preview server could not start: ${message}\n`);
  process.exitCode = 1;
});

server.listen(PORT, HOST, () => {
  const url = `http://${HOST}:${PORT}/`;
  console.log('QUE-006 — composed-announcement preview server');
  console.log('');
  console.log(`  url            : ${url}`);
  console.log('  mode           : read-only (GET/HEAD), loopback only, no writes');
  console.log('  mounts         :');
  for (const mount of MOUNTS) {
    console.log(`                   ${mount.prefix.padEnd(17)} ${mount.label}`);
  }
  console.log('');
  console.log('  Press Ctrl+C to stop. Nothing in frontend/ or the database is modified.');
  console.log('');
});

/** Close cleanly so a re-run does not leave the port bound. */
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    console.log('\nStopping the QUE-006 preview server.');
    server.close(() => process.exit(0));
  });
}
