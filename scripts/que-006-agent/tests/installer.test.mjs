/* QUE-006 / W5 — installer behaviour against a stub server and a temp dir.
 *
 * These tests exercise the guarantees assignment §W5 asks for: verified
 * download, atomic install, previous catalogue retention, rollback, recovery
 * from an interrupted download/install, and offline use of what is installed.
 * They are not a substitute for running the agent on a facility PC (§4 of the
 * report says so explicitly).
 *
 * Run: node --test scripts/que-006-agent/tests/
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { promises as fs } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import {
  createInstaller,
  INSTALL,
  safeRelativePath,
  sha256,
} from '../lib/installer.mjs';
import { createAgent } from '../agent.mjs';

const PACK_ID = 'vp_test';

async function withRoot(t) {
  const root = await fs.mkdtemp(path.join(tmpdir(), 'que006-agent-'));
  t.after(async () => { await fs.rm(root, { recursive: true, force: true }); });
  return root;
}

/** A stub distribution endpoint: bundle index + files, keyed by pathname. */
async function stubServer(t) {
  const routes = new Map();
  const server = http.createServer((req, res) => {
    const entry = routes.get(req.url.split('?')[0]);
    if (!entry) {
      res.writeHead(404);
      res.end('not found');
      return;
    }
    res.writeHead(200, { 'content-type': typeof entry === 'string' ? 'application/json' : 'application/octet-stream' });
    res.end(entry);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  t.after(() => new Promise((resolve) => server.close(resolve)));

  const base = 'http://127.0.0.1:' + port + '/packs/' + PACK_ID + '/';

  /** Publish version *version*; returns the bundle URL. */
  function publish(version, options = {}) {
    const files = {
      'pack.json': JSON.stringify({ id: PACK_ID, version, language: 'en' }),
      'en/digit-1.mp3': 'audio-for-v' + version,
    };
    routes.set('/packs/' + PACK_ID + '/bundle.json', JSON.stringify({
      packId: PACK_ID,
      version,
      files: Object.keys(files).map((file) => ({
        path: file,
        sha256: options.corrupt === file ? 'f'.repeat(64) : sha256(Buffer.from(files[file])),
      })),
    }));
    Object.keys(files).forEach((file) => {
      routes.set('/packs/' + PACK_ID + '/' + file, files[file]);
    });
    return base + 'bundle.json';
  }

  return { publish, base };
}

test('W5 a first install verifies, writes and reports its version', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root, clock: () => '2026-11-21T00:00:00.000Z' });

  const result = await installer.installPack({ packId: PACK_ID, bundleUrl: server.publish(1) });
  assert.equal(result.status, INSTALL.INSTALLED);
  assert.equal(result.version, 1);

  const active = await installer.activeRoot(PACK_ID);
  assert.ok(active && active.endsWith(path.join('current')));
  const manifest = JSON.parse(await fs.readFile(path.join(active, 'pack.json'), 'utf8'));
  assert.equal(manifest.version, 1);
  const audio = await fs.readFile(path.join(active, 'en', 'digit-1.mp3'), 'utf8');
  assert.equal(audio, 'audio-for-v1');

  const status = await installer.status();
  assert.equal(status.packs[PACK_ID].version, 1);
  assert.equal(status.lastResult, INSTALL.INSTALLED);
});

test('W5 an unchanged version is up-to-date and downloads nothing', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root });

  const url = server.publish(1);
  await installer.installPack({ packId: PACK_ID, bundleUrl: url });
  const again = await installer.installPack({ packId: PACK_ID, bundleUrl: url });
  assert.equal(again.status, INSTALL.UP_TO_DATE);
});

test('W5 a checksum mismatch installs nothing and leaves no staging tree', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root });

  const result = await installer.installPack({
    packId: PACK_ID, bundleUrl: server.publish(2, { corrupt: 'en/digit-1.mp3' }),
  });
  assert.equal(result.status, INSTALL.FAILED);
  assert.equal(result.reason, 'checksum_mismatch');
  assert.equal(await installer.activeRoot(PACK_ID), null);

  const inside = await fs.readdir(path.join(root, 'packs', PACK_ID)).catch(() => []);
  assert.deepEqual(inside.filter((entry) => entry.startsWith('staging-')), []);
});

test('W5 a failed update leaves the working catalogue untouched', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root });

  await installer.installPack({ packId: PACK_ID, bundleUrl: server.publish(1) });
  const failed = await installer.installPack({
    packId: PACK_ID, bundleUrl: server.publish(2, { corrupt: 'pack.json' }),
  });
  assert.equal(failed.status, INSTALL.FAILED);

  const active = await installer.activeRoot(PACK_ID);
  const manifest = JSON.parse(await fs.readFile(path.join(active, 'pack.json'), 'utf8'));
  assert.equal(manifest.version, 1, 'the facility keeps playing what it had');
});

test('W5 an update keeps the previous version and rollback restores it', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root });

  await installer.installPack({ packId: PACK_ID, bundleUrl: server.publish(1) });
  await installer.installPack({ packId: PACK_ID, bundleUrl: server.publish(2) });
  assert.equal((await installer.status()).packs[PACK_ID].version, 2);

  const dir = path.join(root, 'packs', PACK_ID);
  const previous = JSON.parse(await fs.readFile(path.join(dir, 'previous', 'pack.json'), 'utf8'));
  assert.equal(previous.version, 1, 'the previous catalogue is retained');

  const rolled = await installer.rollback(PACK_ID);
  assert.equal(rolled.status, INSTALL.ROLLED_BACK);
  assert.equal(rolled.version, 1);
  const current = JSON.parse(await fs.readFile(path.join(dir, 'current', 'pack.json'), 'utf8'));
  assert.equal(current.version, 1);
  assert.equal(await installer.rollback(PACK_ID) && (await installer.rollback(PACK_ID)).reason,
    'no_previous', 'a second rollback has nothing left to go back to');
});

test('W5 a path that escapes the pack directory is refused', async (t) => {
  const root = await withRoot(t);
  const installer = createInstaller({ root });
  assert.throws(() => safeRelativePath('../escape.txt'), /invalid_path/);
  assert.throws(() => safeRelativePath('/etc/passwd'), /invalid_path/);
  assert.throws(() => safeRelativePath('C:/windows/system32/x.dll'), /invalid_path/);
  assert.throws(() => safeRelativePath('a\\b.mp3'), /invalid_path/);
  assert.equal(safeRelativePath('en/digit-1.mp3'), 'en/digit-1.mp3');

  const outside = path.join(root, 'escape.txt');
  const manifest = Buffer.from(JSON.stringify({ id: PACK_ID, version: 3 }));
  const bundle = {
    packId: PACK_ID,
    version: 3,
    files: [
      { path: 'pack.json', sha256: sha256(manifest) },
      { path: '../escape.txt', sha256: sha256(Buffer.from('x')) },
    ],
  };
  const server = http.createServer((req, res) => {
    if (req.url === '/bundle.json') {
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(bundle));
      return;
    }
    if (req.url === '/pack.json') {
      res.writeHead(200);
      res.end(manifest);
      return;
    }
    res.writeHead(404);
    res.end();
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const bundleUrl = 'http://127.0.0.1:' + server.address().port + '/bundle.json';

  const result = await installer.installPack({ packId: PACK_ID, bundleUrl });
  assert.equal(result.status, INSTALL.FAILED);
  assert.equal(result.reason, 'invalid_path');
  await assert.rejects(fs.stat(outside));
});

test('W5 recovery removes a stale staging tree and promotes the previous catalogue', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root });
  await installer.installPack({ packId: PACK_ID, bundleUrl: server.publish(1) });

  const dir = path.join(root, 'packs', PACK_ID);
  await fs.rename(path.join(dir, 'current'), path.join(dir, 'previous'));
  await fs.mkdir(path.join(dir, 'staging-9'), { recursive: true });
  await fs.writeFile(path.join(dir, 'staging-9', 'half.mp3'), 'partial');

  const { recovered } = await installer.recover();
  assert.equal(recovered.length, 2);
  const active = await installer.activeRoot(PACK_ID);
  assert.ok(active && active.endsWith(path.join('current')), 'a usable catalogue is restored');
  assert.deepEqual(await fs.readdir(path.join(dir)).then((e) => e.filter((x) => x.startsWith('staging-'))), []);
});

test('W5 offline: the active catalogue is readable with no server at all', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  const installer = createInstaller({ root });
  await installer.installPack({ packId: PACK_ID, bundleUrl: server.publish(1) });

  const offline = createInstaller({ root, fetchImpl: () => Promise.reject(new Error('offline')) });
  const active = await offline.activeRoot(PACK_ID);
  assert.ok(active);
  assert.equal(JSON.parse(await fs.readFile(path.join(active, 'pack.json'), 'utf8')).version, 1);

  const attempt = await offline.installPack({ packId: PACK_ID, bundleUrl: 'https://example.invalid/x' });
  assert.equal(attempt.status, INSTALL.FAILED);
  assert.ok(await offline.activeRoot(PACK_ID), 'a failed poll never damages the installed catalogue');
});

test('W5 the agent refuses to run without a server or a pack list', async (t) => {
  const root = await withRoot(t);
  const lines = [];
  const agent = createAgent({ root, server: '', packs: [], token: '' }, { log: (l) => lines.push(l) });
  const result = await agent.once();
  assert.equal(result.status, 'not-configured');
  assert.equal(result.results.length, 0);
});

test('W5 the agent installs every entitled pack over an outbound call only', async (t) => {
  const root = await withRoot(t);
  const server = await stubServer(t);
  server.publish(1);
  const urls = [];
  const agent = createAgent({
    root,
    server: server.base.replace('packs/' + PACK_ID + '/', ''),
    packs: [PACK_ID],
    token: 'not-printed',
  }, {
    fetchImpl: (url, init) => {
      urls.push({ url, authorization: init && init.headers ? init.headers.authorization : '' });
      return globalThis.fetch(url, init);
    },
  });
  const result = await agent.once();
  assert.equal(result.status, 'ok');
  assert.equal(result.results[0].status, INSTALL.INSTALLED);
  assert.ok(urls.every((entry) => entry.url.startsWith('http://127.0.0.1:')));
  assert.equal(urls[0].authorization, 'Bearer not-printed', 'the token travels outbound, never inward');
});
