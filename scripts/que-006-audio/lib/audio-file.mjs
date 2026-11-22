/**
 * Audio-file introspection and silent-WAV writing — Node built-ins only.
 *
 * What this can and cannot prove is deliberate:
 *
 *   - It parses the container (`RIFF/WAVE` chunk list, MPEG frame header) and
 *     reports duration, sample rate, channel count and bit depth from the file
 *     itself, never from a filename.
 *   - It measures peak amplitude so a silent or empty clip is distinguishable
 *     from a real recording.
 *   - It does **not** run a codec itself. Structural parsing is the strongest
 *     check Node built-ins alone can make; when ffprobe/ffmpeg are installed,
 *     `lib/decode.mjs` adds a real decode and the validator records which method
 *     produced each record via `decodeVerifiedBy`.
 */

import fs from 'node:fs';
import crypto from 'node:crypto';

/**
 * Detect the container from magic bytes.
 *
 * @param {Buffer} buffer
 * @returns {'wav'|'mp3'|'unknown'}
 */
export function detectFormat(buffer) {
  if (!buffer || buffer.length < 12) return 'unknown';
  if (buffer.toString('ascii', 0, 4) === 'RIFF' && buffer.toString('ascii', 8, 12) === 'WAVE') return 'wav';
  if (buffer.toString('ascii', 0, 3) === 'ID3') return 'mp3';
  if (buffer[0] === 0xff && (buffer[1] & 0xe0) === 0xe0) return 'mp3';
  return 'unknown';
}

/**
 * Walk the RIFF chunk list of a WAV file.
 *
 * @param {Buffer} buffer
 * @returns {null | {ok: boolean, format?: number, sampleRate?: number, channels?: number,
 *   bitsPerSample?: number, dataOffset?: number, dataSize?: number, durationSeconds?: number,
 *   problems: string[]}}
 */
export function parseWav(buffer) {
  if (detectFormat(buffer) !== 'wav') return null;
  const problems = [];
  const result = { ok: true, problems };

  const riffSize = buffer.readUInt32LE(4);
  // Streaming writers leave the size at 0 or 0xFFFFFFFF; both are tolerated, but
  // a size larger than the file is a truncation signal.
  if (riffSize !== 0 && riffSize !== 0xffffffff && riffSize + 8 > buffer.length) {
    problems.push(`RIFF size ${riffSize + 8} exceeds file size ${buffer.length} (truncated?)`);
  }

  let offset = 12;
  let fmt = null;
  let data = null;
  while (offset + 8 <= buffer.length) {
    const chunkId = buffer.toString('ascii', offset, offset + 4);
    let chunkSize = buffer.readUInt32LE(offset + 4);
    const body = offset + 8;
    if (chunkId === 'fmt ' && body + 16 <= buffer.length) {
      fmt = {
        format: buffer.readUInt16LE(body),
        channels: buffer.readUInt16LE(body + 2),
        sampleRate: buffer.readUInt32LE(body + 4),
        byteRate: buffer.readUInt32LE(body + 8),
        bitsPerSample: body + 16 <= buffer.length ? buffer.readUInt16LE(body + 14) : 0,
      };
    } else if (chunkId === 'data') {
      // A chunk that runs past EOF is truncated: clamp it and record it.
      const available = buffer.length - body;
      if (chunkSize > available) {
        problems.push(`data chunk declares ${chunkSize} bytes but only ${available} are present (truncated)`);
        chunkSize = Math.max(0, available);
      }
      data = { offset: body, size: chunkSize };
    }
    if (chunkSize < 0) break;
    offset = body + chunkSize + (chunkSize % 2); // chunks are word aligned
    if (chunkId === 'data') break;                // the audio data is the tail
  }

  if (!fmt) problems.push('no fmt chunk');
  if (!data) problems.push('no data chunk');
  if (fmt && data) {
    const blockAlign = fmt.channels * Math.max(1, fmt.bitsPerSample / 8);
    if (!fmt.sampleRate) problems.push('sample rate is zero');
    if (!blockAlign) problems.push('block alignment is zero');
    result.format = fmt.format;
    result.channels = fmt.channels;
    result.sampleRate = fmt.sampleRate;
    result.bitsPerSample = fmt.bitsPerSample;
    result.dataOffset = data.offset;
    result.dataSize = data.size;
    result.durationSeconds = fmt.byteRate ? data.size / fmt.byteRate : 0;
    if (data.size === 0) problems.push('data chunk is empty');
    if (blockAlign && data.size % blockAlign !== 0) problems.push('data size is not a whole number of sample frames');
  }

  result.ok = problems.length === 0;
  return result;
}
/**
 * Estimate an MP3 duration from its first valid MPEG frame header.
 * Used only as a sanity check on playback copies; WAV is the master format.
 *
 * @param {Buffer} buffer
 */
export function parseMp3(buffer) {
  if (detectFormat(buffer) !== 'mp3') return null;
  const bitrateTable = {
    1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320], // MPEG-1 Layer III, kbps
    2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],     // MPEG-2 Layer III, kbps
  };
  const sampleRateTable = { 0: 44100, 1: 48000, 2: 32000 };

  let offset = 0;
  if (buffer.length > 10 && buffer.toString('ascii', 0, 3) === 'ID3') {
    const size = ((buffer[6] & 0x7f) << 21) | ((buffer[7] & 0x7f) << 14) | ((buffer[8] & 0x7f) << 7) | (buffer[9] & 0x7f);
    offset = 10 + size;
  }
  while (offset + 4 < buffer.length) {
    if (buffer[offset] === 0xff && (buffer[offset + 1] & 0xe0) === 0xe0) break;
    offset += 1;
  }
  if (offset + 4 >= buffer.length) return { ok: false, problems: ['no MPEG frame header found'] };

  const versionBits = (buffer[offset + 1] >> 3) & 0x03; // 3 = MPEG-1
  const layerBits = (buffer[offset + 1] >> 1) & 0x03;   // 1 = Layer III
  const bitrateIndex = (buffer[offset + 2] >> 4) & 0x0f;
  const sampleRateIndex = (buffer[offset + 2] >> 2) & 0x03;
  const table = versionBits === 3 ? bitrateTable[1] : bitrateTable[2];
  const bitrate = layerBits === 1 && bitrateIndex > 0 && bitrateIndex < table.length ? table[bitrateIndex] * 1000 : 0;
  const sampleRate = versionBits === 3 ? sampleRateTable[sampleRateIndex] : 0;

  const problems = [];
  if (!bitrate) problems.push('unsupported MPEG bitrate index (VBR or corrupt)');
  if (!sampleRate) problems.push('unsupported MPEG sample rate');
  const audioBytes = buffer.length - offset;
  return {
    ok: problems.length === 0,
    problems,
    sampleRate: sampleRate || null,
    durationSeconds: bitrate ? (audioBytes * 8) / bitrate : null,
  };
}

/**
 * Highest absolute 16-bit sample value in the data chunk.
 *
 * @param {Buffer} buffer
 * @param {number} dataOffset
 * @param {number} dataSize
 */
function peakPcm16(buffer, dataOffset, dataSize) {
  const end = Math.min(buffer.length, dataOffset + dataSize);
  let peak = 0;
  for (let i = dataOffset; i + 1 < end; i += 2) {
    const sample = buffer.readInt16LE(i);
    const magnitude = sample === -32768 ? 32768 : Math.abs(sample);
    if (magnitude > peak) peak = magnitude;
  }
  return peak;
}
/**
 * Full inspection of one file on disk: identity, container facts, checksum,
 * silence and truncation signals.
 *
 * @param {string} filePath
 * @param {{expectSilence?: boolean}} [options]
 */
export function inspectAudioFile(filePath, options = {}) {
  const record = {
    path: filePath,
    exists: false,
    size: 0,
    format: 'unknown',
    mimeType: null,
    sampleRate: null,
    channels: null,
    bitsPerSample: null,
    durationSeconds: null,
    durationMs: null,
    peakAmplitude: null,
    silent: null,
    sha256: null,
    decodable: false,
    decodeVerifiedBy: 'none',
    problems: [],
  };

  let buffer;
  try {
    const stat = fs.statSync(filePath);
    if (!stat.isFile()) {
      record.problems.push('not a regular file');
      return record;
    }
    record.exists = true;
    record.size = stat.size;
    if (stat.size === 0) {
      record.problems.push('file is zero bytes');
      return record;
    }
    buffer = fs.readFileSync(filePath);
  } catch (err) {
    record.problems.push(`cannot read file: ${err && err.code ? err.code : 'error'}`);
    return record;
  }

  record.sha256 = crypto.createHash('sha256').update(buffer).digest('hex');
  record.format = detectFormat(buffer);

  if (record.format === 'wav') {
    const wav = parseWav(buffer);
    record.mimeType = 'audio/wav';
    if (!wav) {
      record.problems.push('WAV parse failed');
      return record;
    }
    record.problems.push(...wav.problems);
    record.sampleRate = wav.sampleRate ?? null;
    record.channels = wav.channels ?? null;
    record.bitsPerSample = wav.bitsPerSample ?? null;
    record.durationSeconds = wav.durationSeconds ?? null;
    if (typeof wav.dataOffset === 'number' && wav.bitsPerSample === 16) {
      record.peakAmplitude = peakPcm16(buffer, wav.dataOffset, wav.dataSize || 0);
    }
    record.decodable = wav.ok;
    record.decodeVerifiedBy = 'riff-structure';
  } else if (record.format === 'mp3') {
    const mp3 = parseMp3(buffer);
    record.mimeType = 'audio/mpeg';
    if (mp3) {
      record.problems.push(...mp3.problems);
      record.sampleRate = mp3.sampleRate ?? null;
      record.durationSeconds = mp3.durationSeconds ?? null;
      record.decodable = mp3.ok;
      record.decodeVerifiedBy = 'mpeg-frame-header';
    } else {
      record.problems.push('MP3 parse failed');
    }
  } else {
    record.problems.push('unrecognised container (not WAV or MP3)');
  }

  if (typeof record.durationSeconds === 'number') {
    record.durationMs = Math.round(record.durationSeconds * 1000);
  }
  if (typeof record.peakAmplitude === 'number') {
    record.silent = record.peakAmplitude === 0;
    // Digital silence in a clip that must contain speech means the render failed
    // even though the file parses. A punctuation pause is allowed to be silent.
    if (record.silent && !options.expectSilence) record.problems.push('file is digitally silent (no audio samples)');
  }
  if (record.decodable && record.problems.length) record.decodable = false;

  return record;
}
/**
 * Write a silent mono WAV of the requested length.
 *
 * Used only for the punctuation-only asset (`en.phrase.room-suffix`), where the
 * catalogue's spoken text is a full stop and the playback engine should insert a
 * pause rather than say "dot".
 *
 * @param {string} filePath
 * @param {{durationMs: number, sampleRate?: number, bitsPerSample?: number}} options
 */
export function writeSilentWav(filePath, options) {
  const durationMs = options.durationMs;
  const sampleRate = options.sampleRate || 24000;
  const bitsPerSample = options.bitsPerSample || 16;
  const channels = 1;
  const frames = Math.max(1, Math.round((durationMs / 1000) * sampleRate));
  const blockAlign = channels * (bitsPerSample / 8);
  const dataSize = frames * blockAlign;
  const buffer = Buffer.alloc(44 + dataSize); // sample area stays zero-filled

  buffer.write('RIFF', 0, 'ascii');
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write('WAVE', 8, 'ascii');
  buffer.write('fmt ', 12, 'ascii');
  buffer.writeUInt32LE(16, 16);          // PCM fmt chunk size
  buffer.writeUInt16LE(1, 20);           // PCM
  buffer.writeUInt16LE(channels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * blockAlign, 28);
  buffer.writeUInt16LE(blockAlign, 32);
  buffer.writeUInt16LE(bitsPerSample, 34);
  buffer.write('data', 36, 'ascii');
  buffer.writeUInt32LE(dataSize, 40);

  const dir = pathDirname(filePath);
  if (dir) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(filePath, buffer);
  return { bytes: buffer.length, durationMs, sampleRate, bitsPerSample, channels };
}

function pathDirname(filePath) {
  const index = Math.max(filePath.lastIndexOf('/'), filePath.lastIndexOf('\\'));
  return index > 0 ? filePath.slice(0, index) : null;
}

/** Plain-language description of a format, for the manifest and logs. */
export function describeAudio(record) {
  if (!record || !record.format || record.format === 'unknown') return 'unknown';
  if (record.format === 'wav') {
    const parts = ['WAV'];
    if (record.sampleRate) parts.push(`${record.sampleRate} Hz`);
    if (record.bitsPerSample) parts.push(`${record.bitsPerSample}-bit`);
    if (record.channels) parts.push(record.channels === 1 ? 'mono' : record.channels === 2 ? 'stereo' : `${record.channels} ch`);
    return parts.join(', ');
  }
  return 'MP3';
}



