/* QUE-006 / W5 — voice-catalogue installer for the facility PC.
 *
 * The approved architecture (assignment §3.5) is a local agent that POLLS the
 * central server over an outbound HTTPS connection, verifies what it downloads,
 * installs atomically, keeps the previous catalogue for rollback, reports
 * status, and keeps working offline. Nothing here opens an inbound port.
 *
 * Layout under the install root:
 *
 *   <root>/packs/<packId>/current     -> the catalogue in use
 *   <root>/packs/<packId>/previous    -> the one before it, kept for rollback
 *   <root>/packs/<packId>/staging-*   -> a download in progress (never used)
 *   <root>/state.json                 -> last check, last install, last error
 *
 * Rules that make the guarantees real:
 *   - a package is downloaded and verified IN FULL inside staging before
 *     `current` is touched;
 *   - the swap is a rename, so a failure leaves either the old or the new tree,
 *     never a mixture;
 *   - a failure removes staging (interrupted download) and, if the swap was
 *     half-done, restores `previous`;
 *   - verification is by SHA-256 of the received bytes, not by file extension,
 *     and a path that could escape the pack directory is refused.
 *
 * Everything external (fs, fetch, clock, log) is injectable so the tests drive
 * it against a stub server and a temporary directory.
 */
import { createHash } from 'node:crypto';
import { promises as nodeFs } from 'node:fs';
import path from 'node:path';

export const INSTALL = Object.freeze({
  INSTALLED: 'installed',
  UP_TO_DATE: 'up-to-date',
  FAILED: 'failed',
  ROLLED_BACK: 'rolled-back',
});

export class InstallError extends Error {
  constructor(reason, detail) {
    super(reason + (detail ? ': ' + detail : ''));
    this.reason = reason;
    this.detail = detail || '';
  }
}

/** A pack id becomes a directory name, so it must be a plain token. */
export function safePackId(packId) {
  if (typeof packId !== 'string' || !packId) throw new InstallError('invalid_pack_id');
  if (!/^[A-Za-z0-9._-]+$/.test(packId) || packId === '.' || packId === '..') {
    throw new InstallError('invalid_pack_id', packId);
  }
  return packId;
}

/** A relative asset path, or a refusal. Absolute paths and `..` escape the pack. */
export function safeRelativePath(value) {
  if (typeof value !== 'string' || !value) throw new InstallError('invalid_path');
  if (value.includes('\\') || value.startsWith('/') || /^[A-Za-z]:/.test(value)) {
    throw new InstallError('invalid_path', value);
  }
  const parts = value.split('/');
  if (parts.some((part) => part === '' || part === '.' || part === '..')) {
    throw new InstallError('invalid_path', value);
  }
  return parts.join('/');
}

export function sha256(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

/**
 * Create an installer bound to one install root.
 *
 * @param {object} options
 * @param {string} options.root install root on the facility PC
 * @param {Function} [options.fetchImpl] `fetch`-compatible implementation
 * @param {() => string} [options.clock] ISO timestamp source
 * @param {(line: string) => void} [options.log]
 * @param {object} [options.fs] `fs/promises`-compatible subset
 */
export function createInstaller(options = {}) {
  const root = options.root;
  if (!root || typeof root !== 'string') throw new InstallError('invalid_root');
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  const clock = typeof options.clock === 'function'
    ? options.clock : () => new Date().toISOString();
  const log = typeof options.log === 'function' ? options.log : () => {};
  const fs = options.fs || nodeFs;

  const packsRoot = path.join(root, 'packs');
  const packDir = (packId) => path.join(packsRoot, safePackId(packId));
  const statePath = path.join(root, 'state.json');

  const ensureDir = (dir) => fs.mkdir(dir, { recursive: true });

  async function exists(target) {
    try {
      await fs.stat(target);
      return true;
    } catch (err) {
      return false;
    }
  }

  async function readState() {
    try {
      const parsed = JSON.parse(await fs.readFile(statePath, 'utf8'));
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (err) {
      return {};
    }
  }

  async function writeState(patch) {
    const next = { ...(await readState()), ...patch, updatedAt: clock() };
    await ensureDir(root);
    // Write-then-rename keeps the status file readable if the power goes.
    const temporary = statePath + '.tmp';
    await fs.writeFile(temporary, JSON.stringify(next, null, 2), 'utf8');
    await fs.rename(temporary, statePath);
    return next;
  }

  /** What is installed, what came before it, and what the agent last did. */
  async function status() {
    const state = await readState();
    const packs = {};
    let entries = [];
    try {
      entries = await fs.readdir(packsRoot);
    } catch (err) {
      entries = [];
    }
    for (const name of entries) {
      const dir = path.join(packsRoot, name);
      let version = null;
      try {
        const meta = JSON.parse(await fs.readFile(path.join(dir, 'current', 'pack.json'), 'utf8'));
        version = meta && Number.isFinite(meta.version) ? meta.version : null;
      } catch (err) {
        version = null;
      }
      packs[name] = {
        current: await exists(path.join(dir, 'current')),
        previous: await exists(path.join(dir, 'previous')),
        version,
      };
    }
    return { root, packs, ...state };
  }

  /**
   * Recovery after a crash or a power cut. Safe to call at every start.
   * @returns {Promise<{recovered: string[]}>}
   */
  async function recover() {
    const recovered = [];
    await ensureDir(packsRoot);
    const entries = await fs.readdir(packsRoot);
    for (const name of entries) {
      const dir = path.join(packsRoot, name);
      const inside = await fs.readdir(dir).catch(() => []);
      // A half-written staging tree is never usable.
      for (const item of inside.filter((entry) => entry.startsWith('staging-'))) {
        await fs.rm(path.join(dir, item), { recursive: true, force: true });
        recovered.push('removed staging ' + name + '/' + item);
      }
      const current = path.join(dir, 'current');
      const previous = path.join(dir, 'previous');
      if (!(await exists(current)) && (await exists(previous))) {
        await fs.rename(previous, current);
        recovered.push('promoted previous ' + name);
      }
    }
    if (recovered.length) await writeState({ recoveredAt: clock(), lastRecovery: recovered });
    return { recovered };
  }

  /** The directory the player should use right now — offline, no network. */
  async function activeRoot(packId) {
    const dir = packDir(packId);
    if (await exists(path.join(dir, 'current'))) return path.join(dir, 'current');
    if (await exists(path.join(dir, 'previous'))) return path.join(dir, 'previous');
    return null;
  }

  async function currentVersion(packId) {
    try {
      const meta = JSON.parse(
        await fs.readFile(path.join(packDir(packId), 'current', 'pack.json'), 'utf8'));
      return meta && Number.isFinite(meta.version) ? meta.version : null;
    } catch (err) {
      return null;
    }
  }

  async function download(url, accept) {
    if (typeof fetchImpl !== 'function') throw new InstallError('no_fetch');
    const response = await fetchImpl(url, {
      headers: { accept: accept || 'application/octet-stream' },
    });
    if (!response || response.ok !== true) {
      throw new InstallError('download_failed',
        url + ' -> ' + (response ? response.status : 'no response'));
    }
    return response;
  }

  async function writeFileAt(base, relative, bytes) {
    const target = path.join(base, safeRelativePath(relative));
    await ensureDir(path.dirname(target));
    await fs.writeFile(target, bytes);
  }

  /**
   * Poll-and-install one catalogue. The bundle is a small JSON index:
   * `{packId, version, files: [{path, sha256}]}`; every file is fetched relative
   * to the bundle URL and verified before it is written.
   *
   * @returns {Promise<{status: string, packId?: string, version?: number, reason?: string}>}
   */
  async function installPack({ packId, bundleUrl }) {
    const safeId = safePackId(packId);
    const dir = packDir(safeId);
    let staging = null;
    try {
      const indexResponse = await download(bundleUrl, 'application/json');
      const bundle = await indexResponse.json();
      if (!bundle || bundle.packId !== safeId) throw new InstallError('bundle_pack_mismatch');
      const version = Number(bundle.version);
      if (!Number.isFinite(version) || version <= 0) {
        throw new InstallError('bundle_version_invalid');
      }
      if (!Array.isArray(bundle.files) || !bundle.files.length) throw new InstallError('bundle_empty');
      if (!bundle.files.some((file) => file && file.path === 'pack.json')) {
        throw new InstallError('bundle_missing_manifest');
      }

      if ((await currentVersion(safeId)) === version) {
        await writeState({ lastCheck: clock(), lastResult: INSTALL.UP_TO_DATE, lastPack: safeId });
        return { status: INSTALL.UP_TO_DATE, packId: safeId, version };
      }

      await ensureDir(dir);
      staging = path.join(dir, 'staging-' + version);
      await fs.rm(staging, { recursive: true, force: true });
      await ensureDir(staging);

      for (const file of bundle.files) {
        const relative = safeRelativePath(file.path);
        const expected = String(file.sha256 || '').toLowerCase();
        if (!/^[a-f0-9]{64}$/.test(expected)) {
          throw new InstallError('bundle_checksum_missing', relative);
        }
        const response = await download(new URL(relative, bundleUrl).toString());
        const bytes = Buffer.from(await response.arrayBuffer());
        const actual = sha256(bytes);
        if (actual !== expected) {
          throw new InstallError('checksum_mismatch',
            relative + ' expected ' + expected + ' got ' + actual);
        }
        await writeFileAt(staging, relative, bytes);
      }

      const meta = JSON.parse(await fs.readFile(path.join(staging, 'pack.json'), 'utf8'));
      if (meta.id !== safeId || Number(meta.version) !== version) {
        throw new InstallError('manifest_identity_mismatch');
      }

      // ---- atomic swap: staging is complete and verified before this point ----
      const current = path.join(dir, 'current');
      const previous = path.join(dir, 'previous');
      if (await exists(previous)) await fs.rm(previous, { recursive: true, force: true });
      if (await exists(current)) await fs.rename(current, previous);
      try {
        await fs.rename(staging, current);
      } catch (err) {
        // Put the old tree back: a facility must never be left without audio.
        if (!(await exists(current)) && (await exists(previous))) {
          await fs.rename(previous, current);
        }
        throw new InstallError('install_failed', String(err && err.message ? err.message : err));
      }
      staging = null;

      await writeState({
        lastCheck: clock(),
        lastResult: INSTALL.INSTALLED,
        lastPack: safeId,
        lastVersion: version,
        installedAt: clock(),
        lastError: null,
      });
      log('installed ' + safeId + ' v' + version);
      return { status: INSTALL.INSTALLED, packId: safeId, version };
    } catch (err) {
      const reason = err instanceof InstallError ? err.reason : 'unexpected_error';
      const detail = err instanceof InstallError ? err.detail
        : String(err && err.message ? err.message : err);
      if (staging) await fs.rm(staging, { recursive: true, force: true }).catch(() => {});
      await writeState({
        lastCheck: clock(),
        lastResult: INSTALL.FAILED,
        lastPack: safeId,
        lastError: { reason, detail, at: clock() },
      }).catch(() => {});
      log('install failed for ' + safeId + ': ' + reason + ' ' + detail);
      return { status: INSTALL.FAILED, packId: safeId, reason, detail };
    }
  }

  /**
   * Return to the previous catalogue. The rolled-forward version is discarded,
   * so a rollback is a decision and not a toggle.
   */
  async function rollback(packId) {
    const safeId = safePackId(packId);
    const dir = packDir(safeId);
    const current = path.join(dir, 'current');
    const previous = path.join(dir, 'previous');
    if (!(await exists(previous))) {
      await writeState({ lastResult: INSTALL.FAILED, lastError: { reason: 'no_previous' } })
        .catch(() => {});
      return { status: INSTALL.FAILED, packId: safeId, reason: 'no_previous' };
    }
    const discard = path.join(dir, 'discard-' + Date.now());
    try {
      if (await exists(current)) await fs.rename(current, discard);
      await fs.rename(previous, current);
      if (await exists(discard)) await fs.rm(discard, { recursive: true, force: true });
      const version = await currentVersion(safeId);
      await writeState({
        lastResult: INSTALL.ROLLED_BACK, lastPack: safeId, lastVersion: version,
        rolledBackAt: clock(),
      });
      log('rolled back ' + safeId + ' to v' + version);
      return { status: INSTALL.ROLLED_BACK, packId: safeId, version };
    } catch (err) {
      if (!(await exists(current)) && (await exists(discard))) {
        await fs.rename(discard, current).catch(() => {});
      }
      return { status: INSTALL.FAILED, packId: safeId, reason: 'rollback_failed' };
    }
  }

  return { status, recover, activeRoot, installPack, rollback, currentVersion };
}
