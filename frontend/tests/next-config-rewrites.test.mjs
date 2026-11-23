/* QUE-006 / INT-4 — every service the browser calls must be reachable through
 * the application's own origin.
 *
 * The defect: `next.config.js` rewrote 18 prefixes but not `/api/v1/voice-packs`
 * or `/api/v1/platform/**`, so through the browser origin those routes answered
 * Next's own HTML 404 while the service behind it was healthy (G11 in the
 * acceptance-readiness report). No shipped UI called them, which is why no test
 * caught it.
 *
 * This file therefore does two things, and the second is the one that keeps
 * working:
 *   1. pins the routes the merge had to add (voice packs, platform defaults, the
 *      organization setting surfaces);
 *   2. **derives** the set of `/api/v1/<prefix>` paths the frontend actually
 *      calls from its own source and asserts that each one is proxied — so the
 *      next feature that forgets a rewrite fails here instead of in a browser.
 *
 * Nothing here starts Next: `rewrites()` is a pure configuration function.
 *
 * Run: cd frontend && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');
const REPO = path.resolve(FE, '..');

const config = require('../next.config.js');

/** Does one Next.js rewrite `source` match `target`? */
function matches(source, target) {
  const src = source.split('/');
  const tgt = target.split('/');
  for (let i = 0; i < src.length; i += 1) {
    const part = src[i];
    if (part.startsWith(':')) {
      // `:path*` — zero or more remaining segments.
      if (part.endsWith('*')) return true;
      if (i >= tgt.length) return false;
      continue;                        // a single segment parameter
    }
    if (i >= tgt.length || part !== tgt[i]) return false;
  }
  return src.length === tgt.length;
}

/** The rewrites that would receive `target`. */
function proxyFor(rewrites, target) {
  return rewrites.filter((rule) => matches(rule.source, target));
}

/** Every file whose source may contain a browser-issued API path.
 *
 * `tests/` is excluded on purpose: this file's own negative controls use
 * `/api/v1/unknown-thing`, which is not a route anybody calls.
 */
function frontendSources(dir) {
  const out = [];
  const roots = ['pages', 'components', 'lib'];
  (function walk(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (entry.name === 'node_modules' || entry.name === '.next') continue;
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (/\.(js|jsx|mjs)$/.test(entry.name)) out.push(full);
    }
  })(dir);
  return out.filter((file) => roots.some(
    (root) => file.startsWith(path.join(dir, root) + path.sep)));
}

const rewrites = await config.rewrites();

test('the rewrite list is a non-empty array of source/destination pairs', () => {
  assert.ok(Array.isArray(rewrites) && rewrites.length > 0);
  for (const rule of rewrites) {
    assert.equal(typeof rule.source, 'string');
    assert.match(rule.destination, /^https?:\/\/[a-z-]+:\d{4}\//, rule.destination);
    // No rewrite may point at the frontend itself (a loop).
    assert.ok(!rule.destination.includes('frontend:'), rule.destination);
  }
});

test('INT-4: the voice-pack registry is proxied to the organization service', () => {
  for (const target of ['/api/v1/voice-packs',
                        '/api/v1/voice-packs/demo-pack-001',
                        '/api/v1/voice-packs/demo-pack-001/manifest',
                        '/api/v1/voice-packs/demo-pack-001/approve']) {
    const hits = proxyFor(rewrites, target);
    assert.equal(hits.length, 1, target);
    assert.equal(hits[0].destination.split('/api/')[0],
                 'http://organization:8001', target);
  }
});

test('INT-4: the platform announcement defaults are proxied', () => {
  for (const target of ['/api/v1/platform/announcement-config']) {
    const hits = proxyFor(rewrites, target);
    assert.equal(hits.length, 1, target);
    assert.equal(hits[0].destination.split('/api/')[0],
                 'http://organization:8001', target);
  }
});

test('the organization settings surfaces are proxied by the /orgs rule', () => {
  for (const target of [
    '/api/v1/orgs/demo-org-001/announcement-config',
    '/api/v1/orgs/demo-org-001/announcement-config/rollback',
    '/api/v1/orgs/demo-org-001/appointment-config',
    '/api/v1/orgs/demo-org-001/queue-calling-config',
  ]) {
    const hits = proxyFor(rewrites, target);
    assert.equal(hits.length, 1, target);
    assert.equal(hits[0].destination.split('/api/')[0],
                 'http://organization:8001', target);
  }
});

test('an unknown path is not captured by any rewrite', () => {
  for (const target of ['/api/v1/unknown-thing', '/api/v2/patients',
                        '/api/v1/', '/health', '/queue', '/']) {
    assert.deepEqual(proxyFor(rewrites, target), [], target);
  }
});

test('the more specific scheduling rule still wins over the generic one', () => {
  const hits = proxyFor(rewrites, '/api/v1/branches/m5-branch/sessions');
  assert.ok(hits.length >= 1);
  assert.equal(hits[0].destination.split('/')[2], 'scheduling:8004');
});

test('the tracking page can read the token it displays', () => {
  // `pages/track/[token].js` fetches `/api/v1/track/<token>`. It was unproxied:
  // the same class of defect as INT-4, found by the derived scan below.
  const hits = proxyFor(rewrites, '/api/v1/track/' + 'a'.repeat(12));
  assert.equal(hits.length, 1);
  assert.equal(hits[0].destination.split('/api/')[0], 'http://appointment:8005');
  // The public route keeps working unchanged.
  assert.equal(proxyFor(rewrites, '/track/abc123').length, 1);
});

test('every /api/v1 prefix the frontend calls has a rewrite', () => {
  const prefixes = new Set();
  for (const file of frontendSources(FE)) {
    const source = fs.readFileSync(file, 'utf8');
    for (const match of source.matchAll(/\/api\/v1\/([A-Za-z0-9_-]+)/g)) {
      prefixes.add(match[1]);
    }
  }
  assert.ok(prefixes.size >= 10, [...prefixes].sort().join(', '));
  const unproxied = [...prefixes].sort().filter(
    (prefix) => proxyFor(rewrites, `/api/v1/${prefix}`).length === 0);
  assert.deepEqual(unproxied, [], 'unproxied API prefixes: ' + unproxied.join(', '));
});

test('a prefix added to the UI cannot be left unproxied (negative control)', () => {
  // The check above would be vacuous if the matcher matched everything; this
  // pins that it does not.
  assert.equal(proxyFor(rewrites, '/api/v1/not-a-service').length, 0);
  assert.equal(proxyFor(rewrites, '/api/v1/voice-packs/a/b/c').length, 1);
});

test('the repositories the source scan depends on are present', () => {
  assert.ok(fs.existsSync(path.join(REPO, 'backend', 'common', 'permissions.py')));
  assert.ok(fs.existsSync(path.join(FE, 'pages', 'queue.js')));
});
