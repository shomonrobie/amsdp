/* Modal / Dialog focus retention — source-level regression guard.
 * AMSDP-FRONTEND-UX-DEMO-01.
 *
 * The defect this guards: `components/ui/Modal.js` used to run
 *
 *   useEffect(() => { panel.focus(); … }, [onClose]);
 *
 * Callers pass an inline arrow (`onClose={() => setEditor(null)}`), so every
 * keystroke re-rendered the caller, gave `onClose` a new identity, re-ran the
 * effect and pulled the caret out of the field after the first character. A
 * receptionist could not type a patient's name into any dialog form.
 *
 * The fix deletes the effect instead of patching it: `Modal` is a thin wrapper
 * over the Radix-based `Dialog`, which focuses once on open, traps focus inside
 * the panel and never re-focuses on re-render.
 *
 * Scope, stated honestly: like the rest of this suite, this is a source-level
 * contract test (`node --test` here has no DOM harness; the jsdom attempt is
 * recorded in the implementation report as abandoned on this host for memory
 * reasons). It cannot simulate typing, so it does not prove the browser
 * behaviour; it proves that the two conditions that made the defect possible
 * cannot come back — a modal that owns a focus effect, and an effect keyed on a
 * callback prop. Behavioural confirmation is the browser acceptance run in the
 * implementation report.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FE = path.resolve(HERE, '..');

const read = (rel) => fs.readFileSync(path.join(FE, rel), 'utf8');
const stripComments = (source) =>
  source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

/** Index of the delimiter that closes the one at `start` (quote/comment naive, which is enough here). */
function matchClose(source, start) {
  const open = source[start];
  const close = { '(': ')', '{': '}', '[': ']' }[open];
  let depth = 0;
  for (let i = start; i < source.length; i += 1) {
    if (source[i] === open) depth += 1;
    else if (source[i] === close) {
      depth -= 1;
      if (depth === 0) return i;
    }
  }
  return -1;
}

/** The full argument text of every `<name>(…)` call in `source`. */
function callSlices(source, name) {
  const slices = [];
  const pattern = new RegExp(`${name}\\s*\\(`, 'g');
  let match;
  while ((match = pattern.exec(source))) {
    const open = match.index + match[0].length - 1;
    const end = matchClose(source, open);
    if (end === -1) continue;
    slices.push({ index: match.index, text: source.slice(open, end + 1) });
    pattern.lastIndex = end + 1;
  }
  return slices;
}

function lineOf(source, index) {
  return source.slice(0, index).split('\n').length;
}

const MODAL = 'components/ui/Modal.js';
const DIALOG = 'components/ui/Dialog.js';

test('Modal is a thin wrapper over the shared Dialog', () => {
  const source = stripComments(read(MODAL));
  assert.match(
    source,
    /import\s+Dialog\s+from\s+'\.\/Dialog'/,
    'Modal renders the shared Dialog rather than its own overlay implementation',
  );
  assert.match(source, /<Dialog\b/, 'Modal returns a <Dialog>');
  assert.match(source, /\bopen\b/, 'Modal always renders the dialog open (it is mounted to be shown)');
  for (const prop of ['title', 'onClose', 'footer', 'size', 'initialFocusRef']) {
    assert.match(source, new RegExp(`${prop}=\\{`), `Modal still forwards \`${prop}\``);
  }
  assert.doesNotMatch(
    source,
    /useEffect|useLayoutEffect/,
    'Modal must own no effect at all — the old focus effect is what broke typing',
  );
  assert.doesNotMatch(source, /\.focus\(/, 'Modal must never call .focus() itself');
});

test('Dialog is the Radix primitive, so focus is managed once on open', () => {
  const source = stripComments(read(DIALOG));
  assert.match(
    source,
    /from\s+'@radix-ui\/react-dialog'/,
    'Dialog is built on @radix-ui/react-dialog (the shadcn/ui foundation)',
  );
  for (const part of ['Root', 'Portal', 'Overlay', 'Content', 'Title', 'Description']) {
    assert.match(source, new RegExp(`DialogPrimitive\\.${part}`), `uses DialogPrimitive.${part}`);
  }
  assert.match(source, /onOpenChange=\{handleOpenChange\}/, 'open state is controlled by Radix');
  assert.match(source, /onClose\s*&&\s*onClose\(\)/, 'a close request still reaches the caller');

  // The initial-focus hook is an event handler (`onOpenAutoFocus`), not an
  // effect: Radix runs it once when the panel opens.
  const focusCalls = source.match(/\.focus\(/g) || [];
  assert.equal(focusCalls.length, 1, 'Dialog has exactly one programmatic focus, the initial one');
  assert.ok(
    source.indexOf('onOpenAutoFocus') !== -1 &&
      source.indexOf('onOpenAutoFocus') < source.indexOf('.focus('),
    'the only .focus() sits inside onOpenAutoFocus, which Radix runs on open only',
  );

  // The regression itself: no effect may depend on `onClose`.
  for (const call of callSlices(source, 'useEffect')) {
    assert.doesNotMatch(
      call.text,
      /onClose/,
      `useEffect at line ${lineOf(source, call.index)} references onClose — a callback prop ` +
        'has a new identity on every render, so this re-runs on every keystroke',
    );
  }
});



test('no component or page focuses from inside an effect', () => {
  const roots = ['components', 'pages'];
  const offenders = [];

  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
        walk(full);
        continue;
      }
      if (!entry.name.endsWith('.js')) continue;
      const source = stripComments(fs.readFileSync(full, 'utf8'));
      for (const hook of ['useEffect', 'useLayoutEffect']) {
        for (const call of callSlices(source, hook)) {
          if (/\.focus\(/.test(call.text)) {
            offenders.push(`${path.relative(FE, full)}:${lineOf(source, call.index)} (${hook})`);
          }
        }
      }
    }
  };

  for (const root of roots) walk(path.join(FE, root));

  assert.deepEqual(
    offenders,
    [],
    'a focus() inside an effect is the focus-loss defect class: it re-runs whenever ' +
      'a dependency changes identity and steals the caret mid-typing',
  );
});
