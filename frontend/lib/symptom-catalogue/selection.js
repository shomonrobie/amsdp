/* Symptom selection — the pure state machine behind `components/SymptomPicker`.
 *
 * Everything a keystroke decides lives here, so the rules can be tested without
 * a DOM or a browser (the same split BanglaNameSense uses between
 * `controller.js` and its component).  The React component is a thin shell: it
 * owns the text in the search box and renders; it owns no rule.
 *
 * The shape is deliberately two lists rather than one:
 *
 *   { ids: string[], texts: string[] }
 *
 * because the server distinguishes them (`symptom_ids` / `symptom_texts`) and
 * the record must keep the distinction.  Both are optional; an empty selection
 * is the normal case and submits a booking with no symptoms at all.
 *
 * Contract:
 *   - nothing is ever selected without an explicit act (pick, comma, Tab, Enter
 *     on a highlighted suggestion);
 *   - the same catalogue entry cannot be added twice, and neither can the same
 *     free-text description (compared through the Bengali normaliser);
 *   - the list is ordered the way the receptionist built it.
 */

import { textKey, MAX_TEXT_LENGTH } from './matcher.js';

/** Upper bound, mirroring the server's `MAX_SYMPTOMS`. */
export const DEFAULT_MAX_SYMPTOMS = 20;

/** An empty selection — what every booking form starts with. */
export function emptySelection() {
  return { ids: [], texts: [] };
}

/** How many symptoms are selected (catalogue + free text). */
export function countOf(selection) {
  const s = selection || emptySelection();
  return (s.ids || []).length + (s.texts || []).length;
}

/** True when another symptom may be added. */
export function hasRoom(selection, max = DEFAULT_MAX_SYMPTOMS) {
  return countOf(selection) < max;
}

/** True when this catalogue entry is already selected. */
export function isSelected(selection, id) {
  return Boolean(selection && (selection.ids || []).includes(String(id)));
}

/**
 * Add a catalogue entry.
 *
 * @returns {{selection: object, changed: boolean, reason: string}}
 *          reason ∈ added | duplicate | full | invalid
 */
export function addCatalogue(selection, entry, options = {}) {
  const max = Number.isInteger(options.max) ? options.max : DEFAULT_MAX_SYMPTOMS;
  const current = selection || emptySelection();
  const id = entry && entry.id ? String(entry.id) : '';
  if (!id) return { selection: current, changed: false, reason: 'invalid' };
  if (isSelected(current, id)) {
    return { selection: current, changed: false, reason: 'duplicate' };
  }
  if (!hasRoom(current, max)) return { selection: current, changed: false, reason: 'full' };
  return {
    selection: { ids: current.ids.concat(id), texts: current.texts.slice() },
    changed: true,
    reason: 'added',
  };
}


/**
 * Add a free-text description.
 *
 * Whitespace is collapsed as it is stored so the chip and the record agree, and
 * duplicates are compared through `textKey` — so trailing spaces, doubled inner
 * spaces or a different Latin case do not create a second chip.
 *
 * @returns {{selection: object, changed: boolean, reason: string, text: string}}
 *          reason ∈ added | duplicate | empty | too-long | full
 */
export function addFreeText(selection, rawText, options = {}) {
  const max = Number.isInteger(options.max) ? options.max : DEFAULT_MAX_SYMPTOMS;
  const current = selection || emptySelection();
  const text = String(rawText == null ? '' : rawText).split(/\s+/).filter(Boolean).join(' ');
  if (!text) return { selection: current, changed: false, reason: 'empty', text: '' };
  if (text.length > MAX_TEXT_LENGTH) {
    return { selection: current, changed: false, reason: 'too-long', text };
  }
  const key = textKey(text);
  if (current.texts.some((existing) => textKey(existing) === key)) {
    return { selection: current, changed: false, reason: 'duplicate', text };
  }
  if (!hasRoom(current, max)) {
    return { selection: current, changed: false, reason: 'full', text };
  }
  return {
    selection: { ids: current.ids.slice(), texts: current.texts.concat(text) },
    changed: true,
    reason: 'added',
    text,
  };
}

/**
 * Remove one chip.
 *
 * @param {{kind: 'catalogue'|'free_text', id?: string, text?: string}} chip
 */
export function removeChip(selection, chip) {
  const current = selection || emptySelection();
  if (!chip || !chip.kind) return current;
  if (chip.kind === 'catalogue') {
    return {
      ids: current.ids.filter((id) => id !== String(chip.id)),
      texts: current.texts.slice(),
    };
  }
  if (chip.kind === 'free_text') {
    const key = textKey(chip.text);
    return {
      ids: current.ids.slice(),
      texts: current.texts.filter((text) => textKey(text) !== key),
    };
  }
  return current;
}

/** The request payload fragment.  Both fields are always present, usually empty. */
export function toPayload(selection) {
  const s = selection || emptySelection();
  return { symptom_ids: s.ids.slice(), symptom_texts: s.texts.slice() };
}

/** Stable chip identity for React keys and for removal. */
export function chipKey(chip) {
  if (!chip) return '';
  return chip.kind === 'catalogue' ? `cat:${chip.id}` : `txt:${textKey(chip.text)}`;
}

/**
 * Resolve a comma or Tab "finish this entry" gesture.
 *
 * The gesture is honoured only when the typed text identifies exactly one
 * catalogue entry (see `resolveCommit` in `matcher.js`); otherwise the caller
 * leaves the keystroke alone — Tab moves to the next control and a comma stays
 * a comma, which is what keeps free text like "মাথা ব্যথা, জ্বর" typeable.
 *
 * @returns {{selection: object, changed: boolean, entry: object|null, reason: string}}
 */
export function commitFromQuery(index, query, selection, options = {}) {
  const current = selection || emptySelection();
  const resolved = index && typeof index.resolveCommit === 'function'
    ? index.resolveCommit(query, { ...options, excludeIds: current.ids })
    : { entry: null, reason: 'none' };
  if (!resolved.entry) {
    return { selection: current, changed: false, entry: null, reason: resolved.reason };
  }
  const added = addCatalogue(current, resolved.entry, options);
  return {
    selection: added.selection,
    changed: added.changed,
    entry: resolved.entry,
    reason: added.changed ? resolved.reason : added.reason,
  };
}

/** All chips of a selection, in the order they were built (catalogue first). */
export function chipsOf(selection, index) {
  const s = selection || emptySelection();
  const chips = [];
  for (const id of s.ids) {
    const entry = index && typeof index.byId === 'function' ? index.byId(id) : null;
    chips.push({
      kind: 'catalogue',
      id,
      name_en: entry ? entry.name_en : '',
      name_bn: entry ? entry.name_bn : '',
    });
  }
  for (const text of s.texts) chips.push({ kind: 'free_text', text });
  return chips;
}
