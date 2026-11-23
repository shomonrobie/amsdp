/**
 * Reader for the approved announcement templates in
 * `frontend/lib/announcements/content.js`.
 *
 * Read as text rather than imported: the frontend package has no `"type":
 * "module"`, so a Node `import()` of that file emits a module-detection warning
 * on every run. The parse is deliberately narrow and fails loudly if the shape
 * changes, so a silent template change cannot go unnoticed.
 */

import fs from 'node:fs';
import path from 'node:path';

import { REPO_ROOT } from './paths.mjs';

const DEFAULT_TEMPLATES_PATH = path.join(REPO_ROOT, 'frontend', 'lib', 'announcements', 'content.js');

/**
 * @param {string} [templatesPath]
 * @returns {{en: {withRoom: string, noRoom: string}, bn: {withRoom: string, noRoom: string}}}
 */
export function loadApprovedTemplates(templatesPath = DEFAULT_TEMPLATES_PATH) {
  const source = fs.readFileSync(templatesPath, 'utf8');
  const blockMatch = /export const TEMPLATES\s*=\s*Object\.freeze\(\{([\s\S]*?)\n\}\);/.exec(source);
  const body = blockMatch ? blockMatch[1] : source;
  const approved = {};
  const languageRe = /(\w{2})\s*:\s*Object\.freeze\(\{([\s\S]*?)\}\)/g;
  let match;
  while ((match = languageRe.exec(body)) !== null) {
    const [, language, section] = match;
    const withRoom = /withRoom:\s*'([^']*)'/.exec(section);
    const noRoom = /noRoom:\s*'([^']*)'/.exec(section);
    if (withRoom && noRoom) approved[language] = { withRoom: withRoom[1], noRoom: noRoom[1] };
  }
  if (!approved.en || !approved.bn) {
    throw new Error(`could not parse approved templates from ${templatesPath}`);
  }
  return approved;
}
