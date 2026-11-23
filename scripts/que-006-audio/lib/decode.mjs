/**
 * Optional real-decoder verification with ffprobe/ffmpeg.
 *
 * `audio-file.mjs` parses containers with Node built-ins only; that proves the
 * RIFF/MPEG structure is sane, never that a codec can decode the samples. When
 * ffprobe/ffmpeg happen to be installed, this module adds the missing evidence:
 *
 *   - ffprobe reports what it actually decoded (codec, rate, channels, depth,
 *     duration), which is compared against the container's own declaration;
 *   - ffmpeg decodes the whole file to a null sink, so a corrupt sample run or a
 *     truncated frame surfaces as a non-zero exit or a stderr line.
 *
 * Both tools are optional. When they are absent, `detectDecoder()` says so and
 * callers fall back to structure-only records — the utility never claims a
 * decode it did not perform.
 */

import { spawnSync } from 'node:child_process';
import path from 'node:path';

/** Installed tool locations worth trying when the shell PATH is stale. */
const FALLBACK_DIRS = [
  'C:\\Program Files\\WinGet\\Links',
  'C:\\ffmpeg\\bin',
  'C:\\Program Files\\ffmpeg\\bin',
  ...(process.env.LOCALAPPDATA ? [path.join(process.env.LOCALAPPDATA, 'Microsoft', 'WinGet', 'Links')] : []),
  '/usr/local/bin',
  '/usr/bin',
  '/opt/homebrew/bin',
];

const TOOL_TIMEOUT_MS = 30_000;

/** @type {null | ReturnType<typeof detectDecoder>} */
let cached = null;

/**
 * Run a command and capture its output without throwing.
 *
 * @param {string} exe
 * @param {string[]} args
 * @returns {{ok: boolean, status: number|null, stdout: string, stderr: string, code: string|null}}
 */
function run(exe, args) {
  const result = spawnSync(exe, args, {
    encoding: 'utf8',
    windowsHide: true,
    timeout: TOOL_TIMEOUT_MS,
    maxBuffer: 4 * 1024 * 1024,
  });
  return {
    ok: !result.error && result.status === 0,
    status: result.status,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
    code: result.error && result.error.code ? result.error.code : null,
  };
}

/**
 * Resolve one tool by name, falling back to known install directories when the
 * inherited PATH is stale (a common Windows case after a fresh install).
 *
 * @param {'ffprobe'|'ffmpeg'} name
 */
function resolveTool(name) {
  const direct = run(name, ['-version']);
  if (direct.ok) {
    const match = new RegExp(`^${name} version (\\S+)`).exec(direct.stdout.split(/\r?\n/)[0] || '');
    return { exe: name, version: match ? match[1] : 'unknown' };
  }

  for (const dir of FALLBACK_DIRS) {
    const candidate = path.join(dir, process.platform === 'win32' ? `${name}.exe` : name);
    const attempt = run(candidate, ['-version']);
    if (attempt.ok) {
      const match = new RegExp(`^${name} version (\\S+)`).exec(attempt.stdout.split(/\r?\n/)[0] || '');
      return { exe: candidate, version: match ? match[1] : 'unknown' };
    }
  }
  return null;
}

/**
 * Detect a usable decoder once per process.
 *
 * @returns {{available: boolean, ffprobe: {exe: string, version: string}|null,
 *   ffmpeg: {exe: string, version: string}|null, detail: string}}
 */
export function detectDecoder() {
  if (cached) return cached;
  const ffprobe = resolveTool('ffprobe');
  const ffmpeg = resolveTool('ffmpeg');
  const available = Boolean(ffprobe || ffmpeg);
  const parts = [];
  if (ffprobe) parts.push(`ffprobe ${ffprobe.version}`);
  if (ffmpeg) parts.push(`ffmpeg ${ffmpeg.version}`);
  cached = {
    available,
    ffprobe,
    ffmpeg,
    detail: available ? parts.join(' + ') : 'no ffprobe or ffmpeg on PATH or in the known install directories',
  };
  return cached;
}

/**
 * Ask ffprobe what it decodes from a file.
 *
 * @param {string} filePath
 * @returns {{ok: boolean, codecName: string|null, sampleRate: number|null,
 *   channels: number|null, bitsPerSample: number|null, durationMs: number|null,
 *   detail: string}}
 */
export function probeWithFfprobe(filePath) {
  const tooling = detectDecoder();
  const empty = {
    ok: false, codecName: null, sampleRate: null, channels: null,
    bitsPerSample: null, durationMs: null, detail: 'ffprobe unavailable',
  };
  if (!tooling.ffprobe) return empty;

  const result = run(tooling.ffprobe.exe, [
    '-v', 'error',
    '-select_streams', 'a:0',
    '-show_entries', 'stream=codec_name,sample_rate,channels,bits_per_sample,duration:format=duration,format_name',
    '-of', 'json',
    filePath,
  ]);
  if (!result.ok) {
    const why = result.stderr.trim().slice(0, 300) || result.code || `exit ${result.status}`;
    return { ...empty, detail: `ffprobe failed: ${why}` };
  }
  let parsed;
  try {
    parsed = JSON.parse(result.stdout);
  } catch {
    return { ...empty, detail: 'ffprobe output was not JSON' };
  }
  const stream = (parsed.streams || [])[0];
  if (!stream) return { ...empty, detail: 'ffprobe found no audio stream' };

  const streamDuration = Number(stream.duration);
  const formatDuration = Number(parsed.format?.duration);
  const seconds = Number.isFinite(streamDuration) ? streamDuration
    : (Number.isFinite(formatDuration) ? formatDuration : null);

  return {
    ok: true,
    codecName: stream.codec_name || null,
    sampleRate: stream.sample_rate ? Number(stream.sample_rate) : null,
    channels: typeof stream.channels === 'number' ? stream.channels : null,
    bitsPerSample: typeof stream.bits_per_sample === 'number' && stream.bits_per_sample > 0 ? stream.bits_per_sample : null,
    durationMs: seconds === null ? null : Math.round(seconds * 1000),
    detail: `ffprobe ${tooling.ffprobe.version} decoded ${stream.codec_name || 'audio'}`,
  };
}

/**
 * Decode the whole file to a null sink. A clean exit with no stderr is the
 * strongest local evidence that the samples are intact.
 *
 * @param {string} filePath
 * @returns {{checked: boolean, clean: boolean, detail: string}}
 */
export function decodeWithFfmpeg(filePath) {
  const tooling = detectDecoder();
  if (!tooling.ffmpeg) return { checked: false, clean: false, detail: 'ffmpeg unavailable' };

  const result = run(tooling.ffmpeg.exe, ['-nostdin', '-v', 'error', '-i', filePath, '-f', 'null', '-']);
  const noise = result.stderr.trim();
  if (!result.ok) {
    const message = noise.split(/\r?\n/).slice(0, 3).join(' | ') || `exit ${result.status}`;
    return { checked: true, clean: false, detail: `ffmpeg could not decode the file: ${message.slice(0, 300)}` };
  }
  if (noise) {
    return { checked: true, clean: false, detail: `ffmpeg decoded with warnings: ${noise.split(/\r?\n/).slice(0, 3).join(' | ').slice(0, 300)}` };
  }
  return { checked: true, clean: true, detail: `ffmpeg ${tooling.ffmpeg.version} decoded every sample without error` };
}

/**
 * One call that returns everything a validator row needs.
 *
 * Note the explicit `durationMs > 0` requirement: ffmpeg will decode a 44-byte
 * PCM header that contains no samples at all and exit 0, and it cannot detect a
 * truncated PCM tail (PCM carries no checksums). Measured duration is therefore
 * part of the pass condition, and the caller still cross-checks it against the
 * container's own duration — see the negative controls recorded in the report.
 *
 * @param {string} filePath
 */
export function verifyDecode(filePath) {
  const tooling = detectDecoder();
  if (!tooling.available) {
    return { available: false, verified: false, method: 'none', probe: null, decode: null, detail: tooling.detail };
  }
  const probe = probeWithFfprobe(filePath);
  const decode = decodeWithFfmpeg(filePath);
  const hasDuration = typeof probe.durationMs === 'number' && probe.durationMs > 0;
  const verified = Boolean(probe.ok && hasDuration && decode.checked && decode.clean);
  const methods = [];
  if (probe.ok) methods.push('ffprobe');
  if (decode.checked && decode.clean) methods.push('ffmpeg-decode');
  const problems = [];
  if (!probe.ok) problems.push(probe.detail);
  else if (!hasDuration) problems.push('decoder measured no duration — the file may contain a header and no samples');
  if (!decode.checked) problems.push(decode.detail);
  else if (!decode.clean) problems.push(decode.detail);
  return {
    available: true,
    verified,
    method: methods.length ? methods.join('+') : 'failed',
    probe,
    decode,
    detail: verified ? `${probe.detail}; ${decode.detail}` : problems.join('; '),
  };
}

/**
 * Convert one audio file to a PCM WAV using ffmpeg.
 *
 * This is the only use of ffmpeg here that is not verification, and it exists
 * for one narrow reason: the ElevenLabs path may be asked for a lossy container
 * (`mp3_*`, `opus_*`) and the catalogue delivers WAV. The default format there is
 * `wav_*`, so this is the exception, not the normal path.
 *
 * Returns `{ok: false}` with a reason when ffmpeg is absent — the caller must
 * fail the asset rather than write a file it cannot describe.
 *
 * @param {string} inputPath
 * @param {string} outputPath
 * @param {{channels?: number, sampleRate?: number}} [options]
 * @returns {{ok: boolean, detail: string, toolVersion: string|null}}
 */
export function transcodeToWav(inputPath, outputPath, options = {}) {
  const tooling = detectDecoder();
  if (!tooling.ffmpeg) {
    return { ok: false, detail: 'ffmpeg is not installed, so a lossy container cannot be converted to WAV', toolVersion: null };
  }

  const args = ['-nostdin', '-y', '-v', 'error', '-i', inputPath, '-ac', String(options.channels ?? 1)];
  if (options.sampleRate) args.push('-ar', String(options.sampleRate));
  args.push('-c:a', 'pcm_s16le', '-f', 'wav', outputPath);

  const result = run(tooling.ffmpeg.exe, args);
  if (!result.ok) {
    const message = result.stderr.trim().split(/\r?\n/).slice(0, 3).join(' | ') || `exit ${result.status}`;
    return { ok: false, detail: `ffmpeg could not convert the file: ${message.slice(0, 300)}`, toolVersion: tooling.ffmpeg.version };
  }
  return { ok: true, detail: `ffmpeg ${tooling.ffmpeg.version} converted to 16-bit PCM WAV`, toolVersion: tooling.ffmpeg.version };
}

/**
 * Run a tool through this module's resolver.
 *
 * Exported so the standardisation tools share one definition of where ffmpeg
 * lives (PATH, then the known install directories) instead of each re-deriving it
 * and drifting.
 *
 * @param {string} exe
 * @param {string[]} args
 */
export { run as runAudioTool };

/**
 * Encode a PCM master to a constant-bit-rate mono MP3.
 *
 * Used by the QUE-006 standardisation pass, which must turn each 44.1 kHz WAV
 * master into a 128 kbps CBR playback file. `libmp3lame` writes CBR unless asked
 * for VBR (`-q:a`), so the bit rate here is a real ceiling on every frame rather
 * than an average.
 *
 * @param {string} inputPath
 * @param {string} outputPath
 * @param {{sampleRate?: number, channels?: number, bitRate?: number}} [options]
 * @returns {{ok: boolean, detail: string, toolVersion: string|null, args: string[]|null}}
 */
export function encodeMp3(inputPath, outputPath, options = {}) {
  const tooling = detectDecoder();
  if (!tooling.ffmpeg) {
    return { ok: false, detail: 'ffmpeg is not installed, so no MP3 can be produced', toolVersion: null, args: null };
  }
  const sampleRate = options.sampleRate ?? 44100;
  const channels = options.channels ?? 1;
  const kbps = Math.round((options.bitRate ?? 128000) / 1000);
  const args = [
    '-nostdin', '-y', '-v', 'error',
    '-i', inputPath,
    '-ar', String(sampleRate),
    '-ac', String(channels),
    '-c:a', 'libmp3lame',
    '-b:a', `${kbps}k`,
    '-map_metadata', '-1',
    '-f', 'mp3',
    outputPath,
  ];
  const result = run(tooling.ffmpeg.exe, args);
  if (!result.ok) {
    const message = result.stderr.trim().split(/\r?\n/).slice(0, 3).join(' | ') || `exit ${result.status}`;
    return { ok: false, detail: `ffmpeg could not encode the MP3: ${message.slice(0, 300)}`, toolVersion: tooling.ffmpeg.version, args };
  }
  return {
    ok: true,
    detail: `ffmpeg ${tooling.ffmpeg.version} encoded ${kbps} kbps ${sampleRate} Hz mono MP3`,
    toolVersion: tooling.ffmpeg.version,
    args,
  };
}

