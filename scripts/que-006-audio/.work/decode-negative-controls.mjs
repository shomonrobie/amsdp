// Negative controls for lib/decode.mjs — proves the decoder check is not vacuous.
// Writes deliberately broken files into .work/ and reports what verifyDecode says.
import fs from 'node:fs';
import path from 'node:path';
import { verifyDecode, detectDecoder } from '../lib/decode.mjs';
import { inspectAudioFile } from '../lib/audio-file.mjs';

const work = path.join(import.meta.dirname, '..', '..', '..', 'frontend', 'public', 'audio', 'en', 'phrase', 'room-suffix.wav');
const dir = path.join(import.meta.dirname, 'decode-negative-controls');
fs.mkdirSync(dir, { recursive: true });

const tooling = detectDecoder();
console.log(`tooling: ${tooling.detail}`);

const good = fs.readFileSync(work);
const cases = {
  'truncated-mid-data.wav': good.subarray(0, 44 + 1000),
  'header-only.wav': good.subarray(0, 44),
  'not-audio.wav': Buffer.from('this is not a wav file at all, just text'.repeat(4), 'utf8'),
};

for (const [name, bytes] of Object.entries(cases)) {
  const file = path.join(dir, name);
  fs.writeFileSync(file, bytes);
  const result = verifyDecode(file);
  const container = inspectAudioFile(file);
  console.log(`\n${name} (${bytes.length} B)`);
  console.log(`  decoder verified=${result.verified} method=${result.method} durationMs=${result.probe?.durationMs}`);
  console.log(`  decoder detail=${result.detail}`);
  console.log(`  container parse ok=${container.decodable} durationMs=${container.durationMs} problems=${container.problems.join('; ') || 'none'}`);
}

const goodResult = verifyDecode(work);
console.log(`\ncontrol: the real 300 ms pause asset`);
console.log(`  verified=${goodResult.verified} method=${goodResult.method} durationMs=${goodResult.probe?.durationMs} codec=${goodResult.probe?.codecName}`);
