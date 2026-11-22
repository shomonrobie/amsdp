/**
 * Repository paths for the QUE-006 audio utility.
 *
 * Paths are derived from this module's own location, not from the current
 * working directory, so the scripts behave identically when invoked from the
 * repository root, from `scripts/`, or from an editor task.
 */

import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));

/** `scripts/que-006-audio/lib` -> repository root */
export const REPO_ROOT = path.resolve(here, '..', '..', '..');

/** Where the application expects the recordings (served statically by Next.js). */
export const AUDIO_ROOT = path.join(REPO_ROOT, 'frontend', 'public', 'audio');

/** Manifest consumed by the (future) prerecorded-audio playback engine. */
export const MANIFEST_PATH = path.join(AUDIO_ROOT, 'manifest.json');

/** Generation bookkeeping, deliberately outside `public/` so it is never served. */
export const WORK_ROOT = path.join(REPO_ROOT, 'scripts', 'que-006-audio', '.work');

/** Untouched API responses, kept for provenance and manual re-checks. */
export const MASTER_ROOT = path.join(WORK_ROOT, 'master');

/** Per-asset generation metadata (model, voice, timestamp, attempts). */
export const STATE_PATH = path.join(WORK_ROOT, 'state.json');

/** Machine-readable record of the most recent generation run. */
export const LAST_RUN_PATH = path.join(WORK_ROOT, 'last-run.json');

/** Absolute path of an asset's delivery file. */
export function audioPathFor(asset) {
  return path.join(AUDIO_ROOT, ...asset.filename.split('/'));
}

/** Absolute path of an asset's preserved master copy. */
export function masterPathFor(asset) {
  return path.join(MASTER_ROOT, ...asset.filename.split('/'));
}
