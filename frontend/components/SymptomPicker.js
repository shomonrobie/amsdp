/* SymptomPicker / OnsetField — the receptionist's two questions.
 *
 * AMSDP-SYMPTOM-01.  Used by the booking dialog (and the walk-in dialog) on
 * `/appointments`:
 *
 *   "আপনার কী কী সমস্যা হচ্ছে?" / "What problems are you having?"
 *      → SymptomPicker: search the bilingual catalogue, pick several, or type
 *        the patient's own words.  Optional.  Empty by default.
 *   "কখন থেকে সমস্যা হচ্ছে?" / "When did the problem start?"
 *      → OnsetField: one of seven answers, plus an optional short note.
 *
 * NOTHING IS SELECTED FOR THE RECEPTIONIST.  The component receives the booking
 * context (the selected doctor's speciality codes) and uses it only to order
 * equally good text matches — see `lib/symptom-catalogue/matcher.js`.  Age and
 * sex are not passed at all: they may not influence what a patient is asked or
 * offered.
 *
 * FOCUS DISCIPLINE (the defect class AMSDP-FRONTEND-UX-DEMO-01 fixed)
 * -------------------------------------------------------------------
 * This component owns no effect and never focuses from one.  The only
 * `.focus()` calls are inside user-event handlers (after adding or removing a
 * chip, so the caret stays in the search box); `dialog-focus.test.mjs` fails if
 * a `.focus()` ever appears inside an effect in `components/` again.
 *
 * Markup reuses the existing `.bns-*` combobox classes from `styles/global.css`
 * — the same listbox the patient search inside this dialog already uses — and
 * Tailwind utilities for the chips.  No new stylesheet, no new dependency.
 */
import React from 'react';
import { cn } from '../lib/utils';
import { createCatalogueIndex } from '../lib/symptom-catalogue/matcher.js';
import {
  addCatalogue, addFreeText, chipKey, chipsOf, commitFromQuery, countOf,
  emptySelection, hasRoom, removeChip, DEFAULT_MAX_SYMPTOMS,
} from '../lib/symptom-catalogue/selection.js';

const DEFAULT_LABELS = {
  title: 'উপসর্গ',
  optional: 'ঐচ্ছিক',
  prompt: 'আপনার কী কী সমস্যা হচ্ছে?',
  placeholder: 'উপসর্গ খুঁজুন — বাংলা বা ইংরেজি',
  selected: 'নির্বাচিত উপসর্গ',
  none: 'কোনো উপসর্গ নির্বাচন করা হয়নি',
  remove: 'সরান',
  freeText: 'নিজের ভাষায়',
  addFree: 'নিজের ভাষায় লিখে যোগ করুন',
  alreadySelected: 'এই উপসর্গটি আগেই নির্বাচন করা হয়েছে',
  full: 'আরও উপসর্গ যোগ করা যাবে না',
  hint: 'ঐচ্ছিক — রোগী যা বলছেন তাই লিখুন। এটি রোগনির্ণয় নয়।',
  listLabel: 'উপসর্গের প্রস্তাব',
  onsetTitle: 'কখন থেকে সমস্যা হচ্ছে?',
  onsetNotAsked: 'জিজ্ঞাসা করা হয়নি',
  onsetNote: 'সংক্ষিপ্ত বিবরণ',
  onsetNotePlaceholder: 'যেমন: প্রায় চার দিন ধরে, সকালে বেশি',
};


export function SymptomPicker({
  id = 'symptom-picker',
  catalogue,
  value,
  onChange,
  maxSymptoms = DEFAULT_MAX_SYMPTOMS,
  lang = 'bn',
  contextSpecialtyCodes,
  disabled = false,
  labels,
}) {
  const L = { ...DEFAULT_LABELS, ...(labels || {}) };
  const selection = value || emptySelection();
  const index = React.useMemo(
    () => createCatalogueIndex(Array.isArray(catalogue) ? catalogue : []),
    [catalogue],
  );
  const contextCodes = contextSpecialtyCodes || [];

  const [query, setQuery] = React.useState('');
  const [active, setActive] = React.useState(-1);
  const [open, setOpen] = React.useState(false);
  const [note, setNote] = React.useState('');
  const inputRef = React.useRef(null);

  const listId = `${id}-listbox`;
  const searchId = `${id}-input`;
  const chips = chipsOf(selection, index);
  const room = hasRoom(selection, maxSymptoms);

  const suggestions = index.search(query, {
    maxSuggestions: 8,
    excludeIds: selection.ids,
    contextSpecialtyCodes: contextCodes,
  });
  // The free-text row appears only when the typed text does not already name a
  // catalogue entry exactly, so the receptionist can always record the
  // patient's own words when the catalogue has no match.
  const trimmed = query.trim();
  const exact = trimmed
    ? index.resolveCommit(trimmed, { excludeIds: selection.ids })
    : { entry: null };
  const showFree = Boolean(trimmed) && !exact.entry && room;
  const total = suggestions.length + (showFree ? 1 : 0);
  const showList = open && !disabled && total > 0;
  const activeId = showList && active >= 0
    ? (active < suggestions.length ? `${id}-option-${active}` : `${id}-option-free`)
    : undefined;

  const focusInput = () => {
    // Event handler, not an effect: the caret returns to the search box only
    // because the receptionist just acted on the list or on a chip.
    if (inputRef.current && typeof inputRef.current.focus === 'function') {
      inputRef.current.focus();
    }
  };

  const pick = (entry) => {
    const result = addCatalogue(selection, entry, { max: maxSymptoms });
    if (result.changed) {
      onChange(result.selection);
      setQuery('');
      setActive(-1);
      setOpen(false);
      setNote('');
    } else {
      setNote(result.reason === 'duplicate' ? L.alreadySelected : L.full);
    }
    focusInput();
  };

  const addText = (text) => {
    const result = addFreeText(selection, text, { max: maxSymptoms });
    if (result.changed) {
      onChange(result.selection);
      setQuery('');
      setActive(-1);
      setOpen(false);
      setNote('');
    } else {
      setNote(result.reason === 'duplicate' ? L.alreadySelected
        : result.reason === 'too-long' ? L.hint : L.full);
    }
    focusInput();
  };

  const choose = (optionIndex) => {
    if (optionIndex >= 0 && optionIndex < suggestions.length) {
      pick(suggestions[optionIndex]);
      return;
    }
    if (showFree && optionIndex === suggestions.length) addText(query);
  };

  const commitShortcut = () => {
    const result = commitFromQuery(index, query, selection, {
      max: maxSymptoms, contextSpecialtyCodes: contextCodes,
    });
    if (!result.changed) return false;
    onChange(result.selection);
    setQuery('');
    setActive(-1);
    setOpen(false);
    setNote('');
    focusInput();
    return true;
  };

  const handleKeyDown = (event) => {
    // Never fight an IME: while a Bangla input method is composing, the key is
    // part of the word the receptionist is typing.
    if (event.nativeEvent && event.nativeEvent.isComposing) return;

    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      if (!total) return;
      event.preventDefault();
      const delta = event.key === 'ArrowDown' ? 1 : -1;
      setOpen(true);
      setActive((current) => {
        if (!showList || current < 0) return delta > 0 ? 0 : total - 1;
        return (current + delta + total) % total;
      });
      return;
    }

    if (event.key === 'Enter') {
      // Only a highlighted row is chosen; plain typing never selects.
      if (showList && active >= 0 && active < total) {
        event.preventDefault();
        choose(active);
      }
      return;
    }

    if (event.key === 'Escape') {
      if (showList) {
        event.preventDefault();
        setOpen(false);
        setActive(-1);
      }
      return;
    }

    if (event.key === 'Tab') {
      if (showList && active >= 0 && active < total) {
        event.preventDefault();
        choose(active);
        return;
      }
      // Tab completes the entry only when it is unambiguous; otherwise it stays
      // a Tab and moves the caret to the next control.
      if (trimmed && commitShortcut()) event.preventDefault();
      return;
    }

    if (event.key === ',') {
      // Comma completes an unambiguous entry; when nothing matches it stays a
      // comma so "মাথা ব্যথা, জ্বর" remains typeable as free text.
      if (trimmed && commitShortcut()) event.preventDefault();
    }
  };

  const removeSelected = (chip) => {
    onChange(removeChip(selection, chip));
    setActive(-1);
    focusInput();
  };

  const chipLabel = (chip) => (chip.kind === 'catalogue'
    ? (lang === 'en' ? (chip.name_en || chip.name_bn) : (chip.name_bn || chip.name_en))
    : chip.text);

  return (
    <div className="form-group">
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor={searchId}>{L.title}</label>
        <span className="text-xs font-normal text-muted-foreground">{L.optional}</span>
      </div>
      <p className="mb-1 text-xs text-muted-foreground">{L.prompt}</p>

      {chips.length > 0 ? (
        <ul className="mb-1.5 flex flex-wrap gap-1" aria-label={L.selected}>
          {chips.map((chip) => (
            <li key={chipKey(chip)}>
              <span
                className={cn(
                  'inline-flex items-center gap-1 rounded-pill border px-2 py-0.5 text-sm',
                  chip.kind === 'catalogue'
                    ? 'border-[hsl(var(--primary)/0.35)] bg-accent text-primary'
                    : 'border-dashed border-input bg-card text-foreground',
                )}
              >
                <span>{chipLabel(chip)}</span>
                {chip.kind === 'free_text' && (
                  <span className="text-[0.68rem] font-semibold uppercase tracking-wide text-muted-foreground">
                    {L.freeText}
                  </span>
                )}
                <button
                  type="button"
                  className="rounded-pill px-1 text-base leading-none text-muted-foreground hover:text-destructive"
                  aria-label={`${L.remove}: ${chipLabel(chip)}`}
                  onClick={() => removeSelected(chip)}
                >
                  ×
                </button>
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-1.5 text-xs italic text-muted-foreground">{L.none}</p>
      )}

      <div className="bns-wrap">
        <input
          ref={inputRef}
          id={searchId}
          type="text"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showList}
          aria-controls={listId}
          aria-activedescendant={activeId}
          aria-label={L.title}
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          disabled={disabled || !room}
          value={query}
          placeholder={room ? L.placeholder : L.full}
          onChange={(event) => {
            setQuery(event.target.value);
            setActive(-1);
            setOpen(true);
            setNote('');
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setOpen(true)}
          onBlur={() => { setOpen(false); setActive(-1); }}
        />
        {showList && (
          <ul className="bns-list" id={listId} role="listbox" aria-label={L.listLabel}>
            {suggestions.map((suggestion, optionIndex) => (
              <li
                key={suggestion.id}
                id={`${id}-option-${optionIndex}`}
                role="option"
                aria-selected={active === optionIndex}
                className={'bns-option' + (active === optionIndex ? ' bns-option-active' : '')}
                onMouseDown={(event) => { event.preventDefault(); choose(optionIndex); }}
                onTouchStart={(event) => { event.preventDefault(); choose(optionIndex); }}
              >
                <span className="bns-name">
                  {lang === 'en' ? suggestion.name_en : suggestion.name_bn}
                </span>
                <span className="bns-alias">
                  {lang === 'en' ? suggestion.name_bn : suggestion.name_en}
                </span>
              </li>
            ))}
            {showFree && (
              <li
                id={`${id}-option-free`}
                role="option"
                aria-selected={active === suggestions.length}
                className={'bns-option'
                  + (active === suggestions.length ? ' bns-option-active' : '')}
                onMouseDown={(event) => { event.preventDefault(); addText(query); }}
                onTouchStart={(event) => { event.preventDefault(); addText(query); }}
              >
                <span className="bns-name">“{trimmed}”</span>
                <span className="bns-alias">{L.addFree}</span>
              </li>
            )}
          </ul>
        )}
        <span className="bns-status" role="status" aria-live="polite">
          {note || (showList ? `${countOf(selection)}/${maxSymptoms}` : '')}
        </span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{L.hint}</p>
    </div>
  );
}

export function OnsetField({
  id = 'symptom-onset',
  value = '',
  note = '',
  onChange,
  onNoteChange,
  options,
  disabled = false,
  labels,
}) {
  const L = { ...DEFAULT_LABELS, ...(labels || {}) };
  const list = Array.isArray(options) ? options : [];
  const noteId = `${id}-note`;
  return (
    <div className="form-group">
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor={id}>{L.onsetTitle}</label>
        <span className="text-xs font-normal text-muted-foreground">{L.optional}</span>
      </div>
      <select
        id={id}
        aria-label={L.onsetTitle}
        value={value || ''}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{L.onsetNotAsked}</option>
        {list.map((option) => (
          <option key={option.code} value={option.code}>
            {`${option.name_bn || option.name_en} / ${option.name_en}`}
          </option>
        ))}
      </select>
      <label htmlFor={noteId} className="mt-1 block text-xs font-normal text-muted-foreground">
        {L.onsetNote}
      </label>
      <input
        id={noteId}
        type="text"
        aria-label={L.onsetNote}
        placeholder={L.onsetNotePlaceholder}
        maxLength={200}
        disabled={disabled || !value}
        value={note || ''}
        onChange={(event) => onNoteChange(event.target.value)}
      />
    </div>
  );
}

export default SymptomPicker;

