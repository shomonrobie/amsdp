// Diagnostics for .env.local / .env key shape — prints NO secret characters.
import fs from 'node:fs';

const out = [];
for (const f of ['.env.local', '.env']) {
  if (!fs.existsSync(f)) { out.push(`${f}: absent`); continue; }
  const raw = fs.readFileSync(f, 'utf8');
  out.push(`${f}: ${raw.split(/\r?\n/).length} line(s), ${raw.length} bytes`);
  for (const line of raw.split(/\r?\n/)) {
    if (!line.includes('GEMINI_API_KEY')) continue;
    const eq = line.indexOf('=');
    if (eq < 0) { out.push('  GEMINI_API_KEY line has no "="'); continue; }
    const v = line.slice(eq + 1);
    const t = v.trim();
    const quoted = t.startsWith('"') || t.startsWith("'");
    const inner = quoted ? t.slice(1, -1) : t;
    out.push([
      `  rawLen=${v.length}`,
      `trimmedLen=${t.length}`,
      `quoted=${quoted}`,
      `innerLen=${inner.length}`,
      `whitespaceInside=${/\s/.test(inner)}`,
      `charsetOk=${/^[A-Za-z0-9_.:-]+$/.test(inner)}`,
      `placeholderLike=${/(your|placeholder|xxx|example|insert|paste|here)/i.test(inner)}`,
      `carriageReturn=${/\r/.test(v)}`,
    ].join(' '));
  }
}
console.log(out.join('\n'));
