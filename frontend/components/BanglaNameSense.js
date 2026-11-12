import React from 'react';
import datasetJson from '../data/bangla_name_sense.json';
import { buildDataset } from '../lib/bangla-name-sense/dataset.js';
import {
  initialState, queryChanged, focused, blurred, keyDown, selectIndex, Action,
} from '../lib/bangla-name-sense/controller.js';

/* BanglaNameSense — reusable, Bangla-first name autocomplete.
 *
 * AMSDP component conventions apply: React function component, plain
 * JavaScript, global.css classes (no CSS-in-JS, no new dependency).
 *
 * The dataset is bundled once at build time and searched locally, so typing
 * never issues a network request and never leaves the browser.
 *
 * Props
 *   id, name              input identity (id is also the labels' htmlFor target)
 *   value, onChange(text) controlled value — onChange receives ONLY what the
 *                         user typed or the exact `bn` of a picked suggestion
 *   label                 visible label text (a "*" is added when required)
 *   required              renders the asterisk + aria-required; validation stays
 *                         with the surrounding form
 *   placeholder, disabled, autoFocus, className
 *   maxSuggestions        default 8
 *   minQueryLength        default 1
 *   labels                { count } — live-region wording (Bangla by default)
 *   index                 optional pre-built index (tests / other datasets)
 */

const DEFAULT_LABELS = { count: 'প্রস্তাব' };

const dataset = buildDataset(datasetJson);

export default function BanglaNameSense({
  id = 'bns-input',
  name,
  value = '',
  onChange = () => {},
  label,
  required = false,
  placeholder,
  disabled = false,
  autoFocus = false,
  className = '',
  maxSuggestions,
  minQueryLength,
  labels,
  index,
} = {}) {
  const searchIndex = index || dataset.index;
  const options = { maxSuggestions, minQueryLength };
  const L = { ...DEFAULT_LABELS, ...(labels || {}) };
  const listId = `${id}-listbox`;

  const [state, setState] = React.useState(() => initialState(value));
  const lastPick = React.useRef({ index: -1, at: 0 });

  // Keep the machine in sync when the parent resets the field (e.g. after save).
  React.useEffect(() => {
    setState((s) => (s.query === value ? s : {
      ...s, query: value, open: false, activeIndex: -1, suggestions: [],
    }));
  }, [value]);

  const applyText = (text) => {
    const next = queryChanged(state, text, searchIndex, options);
    setState(next.state);
    onChange(text);
  };

  const pick = (i) => {
    const now = Date.now();
    if (lastPick.current.index === i && now - lastPick.current.at < 400) return;
    lastPick.current = { index: i, at: now };
    const result = selectIndex(state, i);
    if (result.action === Action.SELECT) {
      setState(result.state);
      onChange(result.value);
    }
  };

  const handleKeyDown = (event) => {
    if (event.nativeEvent && event.nativeEvent.isComposing) return;
    const result = keyDown(state, event.key);
    if (result.preventDefault) event.preventDefault();
    if (result.action === Action.SELECT) {
      setState(result.state);
      onChange(result.value);
    } else if (result.state !== state) {
      setState(result.state);
    }
  };

  const handleFocus = () => {
    if (disabled) return;
    setState(focused(state, searchIndex, options).state);
  };

  const handleBlur = () => {
    setState(blurred(state).state);
  };

  const open = state.open && state.suggestions.length > 0;
  const activeId = open && state.activeIndex >= 0
    ? `${id}-option-${state.activeIndex}`
    : undefined;

  return (
    <div className={`bns-field ${className}`.trim()}>
      {label && (
        <label htmlFor={id}>
          {label}{required ? '*' : ''}
        </label>
      )}
      <div className="bns-wrap">
        <input
          id={id}
          name={name}
          type="text"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listId}
          aria-activedescendant={activeId}
          aria-required={required || undefined}
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          autoFocus={autoFocus}
          disabled={disabled}
          placeholder={placeholder}
          value={value}
          onChange={(e) => applyText(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
        />
        {open && (
          <ul className="bns-list" id={listId} role="listbox" aria-label={label || 'suggestions'}>
            {state.suggestions.map((s, i) => (
              <li
                key={s.bn}
                id={`${id}-option-${i}`}
                role="option"
                aria-selected={i === state.activeIndex}
                className={`bns-option${i === state.activeIndex ? ' bns-option-active' : ''}`}
                onMouseDown={(e) => { e.preventDefault(); pick(i); }}
                onTouchStart={(e) => { e.preventDefault(); pick(i); }}
                onClick={() => pick(i)}
              >
                <span className="bns-name">{s.bn}</span>
                {s.en ? <span className="bns-alias">{s.en}</span> : null}
              </li>
            ))}
          </ul>
        )}
        <span className="bns-status" role="status" aria-live="polite">
          {open ? `${L.count}: ${state.suggestions.length}` : ''}
        </span>
      </div>
    </div>
  );
}
