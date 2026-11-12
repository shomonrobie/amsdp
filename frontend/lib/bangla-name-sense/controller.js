/* BanglaNameSense — interaction state machine (pure, framework-agnostic).
 *
 * Every keyboard, pointer and touch decision the component makes lives here, so
 * the behaviour is unit-testable without a DOM or a browser. The React
 * component in `components/BanglaNameSense.js` is a thin shell over these
 * functions.
 *
 * Contract that the tests pin down (Master Feature List §25.8.2, §25.8.5):
 *   - typing NEVER selects or replaces the user's text;
 *   - Enter selects only when a suggestion is actively highlighted;
 *   - Escape closes the list and leaves the typed text untouched;
 *   - the user may always keep typing a name that is not in the dataset.
 */

export const Key = Object.freeze({
  DOWN: 'ArrowDown',
  UP: 'ArrowUp',
  ENTER: 'Enter',
  ESCAPE: 'Escape',
  TAB: 'Tab',
});

export const Action = Object.freeze({
  NONE: 'none',
  SEARCH: 'search',
  NAVIGATE: 'navigate',
  SELECT: 'select',
  CLOSE: 'close',
});

/** @returns {{query: string, suggestions: object[], open: boolean, activeIndex: number}} */
export function initialState(query = '') {
  return { query: String(query || ''), suggestions: [], open: false, activeIndex: -1 };
}

function closed(state) {
  return { ...state, open: false, activeIndex: -1 };
}

/**
 * React to a change of the input value.
 *
 * @param {{query: string}} state
 * @param {string} query the new raw text (exactly what the user typed)
 * @param {{search: Function}} index
 * @param {{maxSuggestions?: number, minQueryLength?: number}} [options]
 */
export function queryChanged(state, query, index, options = {}) {
  const text = String(query == null ? '' : query);
  const suggestions = index && typeof index.search === 'function'
    ? index.search(text, options)
    : [];
  return {
    state: {
      query: text,
      suggestions,
      open: suggestions.length > 0,
      activeIndex: -1,
    },
    action: Action.SEARCH,
  };
}

/** Keep the current text but re-open suggestions (used on focus). */
export function focused(state, index, options = {}) {
  return queryChanged(state, state.query, index, options);
}

/** Close the list without touching the text (blur). */
export function blurred(state) {
  return { state: closed(state), action: Action.CLOSE };
}

/**
 * @param {{query: string, suggestions: object[], open: boolean, activeIndex: number}} state
 * @param {string} key KeyboardEvent.key
 * @returns {{state: object, action: string, value?: string, preventDefault?: boolean}}
 */
export function keyDown(state, key) {
  const count = state.suggestions.length;

  switch (key) {
    case Key.DOWN: {
      if (!count) return { state, action: Action.NONE };
      const activeIndex = state.open
        ? (state.activeIndex + 1) % count
        : 0;
      return {
        state: { ...state, open: true, activeIndex },
        action: Action.NAVIGATE,
        preventDefault: true,
      };
    }

    case Key.UP: {
      if (!count) return { state, action: Action.NONE };
      const activeIndex = state.open
        ? (state.activeIndex - 1 + count) % count
        : count - 1;
      return {
        state: { ...state, open: true, activeIndex },
        action: Action.NAVIGATE,
        preventDefault: true,
      };
    }

    case Key.ENTER: {
      // Only an explicitly highlighted suggestion may be applied. With nothing
      // highlighted the keystroke is left alone, so a name that is not in the
      // dataset is submitted exactly as typed.
      if (state.open && state.activeIndex >= 0 && state.activeIndex < count) {
        const suggestion = state.suggestions[state.activeIndex];
        return {
          state: closed({ ...state, query: suggestion.bn }),
          action: Action.SELECT,
          value: suggestion.bn,
          preventDefault: true,
        };
      }
      return { state, action: Action.NONE };
    }

    case Key.ESCAPE:
      if (!state.open) return { state, action: Action.NONE };
      return { state: closed(state), action: Action.CLOSE, preventDefault: true };

    case Key.TAB:
      if (!state.open) return { state, action: Action.NONE };
      return { state: closed(state), action: Action.CLOSE };

    default:
      return { state, action: Action.NONE };
  }
}

/**
 * Select a suggestion by position — used by mouse and touch.
 *
 * @param {object} state
 * @param {number} index
 * @returns {{state: object, action: string, value?: string}}
 */
export function selectIndex(state, index) {
  if (index === null || index === undefined) return { state, action: Action.NONE };
  const i = Number(index);
  if (!Number.isInteger(i) || i < 0 || i >= state.suggestions.length) {
    return { state, action: Action.NONE };
  }
  const suggestion = state.suggestions[i];
  return {
    state: closed({ ...state, query: suggestion.bn }),
    action: Action.SELECT,
    value: suggestion.bn,
  };
}
