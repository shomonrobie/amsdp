#!/usr/bin/env node
/* QUE-006 / W5 — the facility-side voice-catalogue agent (CLI).
 *
 * Runs on the facility's local PC and only ever makes OUTBOUND requests to the
 * configured server. There is no listener, no inbound port and no remote control
 * path: the server cannot reach in, by design (assignment §3.5).
 *
 * Usage
 *   node scripts/que-006-agent/agent.mjs --status
 *   node scripts/que-006-agent/agent.mjs --once
 *   node scripts/que-006-agent/agent.mjs --interval 900000
 *   node scripts/que-006-agent/agent.mjs --rollback <packId>
 *
 * Configuration (environment only — never a CLI argument, so a token cannot end
 * up in a process list or a shell history):
 *   AMSDP_VOICE_ROOT    install root (default: ./voice-packs)
 *   AMSDP_VOICE_SERVER  base URL of the distribution endpoint (HTTPS)
 *   AMSDP_VOICE_PACKS   comma-separated pack ids the organisation is entitled to
 *   AMSDP_VOICE_TOKEN   bearer token for the distribution endpoint
 */
import path from 'node:path';
import process from 'node:process';

import { createInstaller, INSTALL } from './lib/installer.mjs';

function readConfig(env = process.env) {
  const root = env.AMSDP_VOICE_ROOT ? path.resolve(env.AMSDP_VOICE_ROOT) : path.resolve('voice-packs');
  const server = typeof env.AMSDP_VOICE_SERVER === 'string' ? env.AMSDP_VOICE_SERVER.trim() : '';
  const packs = String(env.AMSDP_VOICE_PACKS || '')
    .split(',').map((value) => value.trim()).filter(Boolean);
  // The token is held in memory only, and is never printed by this program.
  const token = typeof env.AMSDP_VOICE_TOKEN === 'string' ? env.AMSDP_VOICE_TOKEN : '';
  return { root, server, packs, token };
}

export function createAgent(config, options = {}) {
  const log = options.log || ((line) => console.log(line));
  const baseFetch = options.fetchImpl || ((url, init) => globalThis.fetch(url, init));
  // The bearer token is attached here, once, so every outbound call carries it
  // and no other code path can forget or log it.
  const fetchImpl = (url, init = {}) => {
    const headers = { ...(init.headers || {}) };
    if (config.token) headers.authorization = 'Bearer ' + config.token;
    return baseFetch(url, { ...init, headers });
  };
  const installer = createInstaller({ root: config.root, fetchImpl, log });

  function bundleUrl(packId) {
    if (!config.server) return null;
    const base = config.server.endsWith('/') ? config.server : config.server + '/';
    return new URL('packs/' + encodeURIComponent(packId) + '/bundle.json', base).toString();
  }

  async function once() {
    await installer.recover();
    if (!config.server) {
      return { status: 'not-configured', reason: 'AMSDP_VOICE_SERVER is unset', results: [] };
    }
    if (!config.packs.length) {
      return { status: 'not-configured', reason: 'AMSDP_VOICE_PACKS is empty', results: [] };
    }
    const results = [];
    for (const packId of config.packs) {
      const url = bundleUrl(packId);
      // Sequential on purpose: one catalogue at a time, so a failure cannot
      // leave two packs half-installed and the disk usage stays predictable.
      results.push(await installer.installPack({ packId, bundleUrl: url }));
    }
    return { status: results.every((r) => r.status !== INSTALL.FAILED) ? 'ok' : 'degraded', results };
  }

  return { installer, once, bundleUrl };
}

async function main(argv) {
  const config = readConfig();
  const agent = createAgent(config);
  const arg = (name) => argv.includes(name);

  if (arg('--status')) {
    process.stdout.write(JSON.stringify(await agent.installer.status(), null, 2) + '\n');
    return 0;
  }
  if (arg('--rollback')) {
    const index = argv.indexOf('--rollback');
    const packId = argv[index + 1];
    const result = await agent.installer.rollback(packId);
    process.stdout.write(JSON.stringify(result) + '\n');
    return result.status === INSTALL.ROLLED_BACK ? 0 : 1;
  }
  if (arg('--interval')) {
    const index = argv.indexOf('--interval');
    const interval = Math.max(60000, Number(argv[index + 1]) || 900000);
    for (;;) {
      const result = await agent.once();
      process.stdout.write(JSON.stringify(result) + '\n');
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
  }
  const result = await agent.once();
  process.stdout.write(JSON.stringify(result) + '\n');
  return result.status === 'ok' || result.status === 'not-configured' ? 0 : 1;
}

if (process.argv[1] && process.argv[1].replace(/\\/g, '/').endsWith('que-006-agent/agent.mjs')) {
  main(process.argv.slice(2)).then((code) => process.exit(code)).catch((err) => {
    process.stderr.write('agent failed: ' + (err && err.message ? err.message : String(err)) + '\n');
    process.exit(1);
  });
}
