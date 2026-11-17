/* AMSDP application entry — global stylesheet order matters:
 *
 *   1. tokens.css   — CSS custom properties (colour, type, space, focus)
 *   2. global.css   — the legacy component classes un-migrated pages still use
 *   3. tailwind.css — the utility layer last, so utilities can override legacy
 *
 * Preflight is disabled in `tailwind.config.js`, so step 3 is purely additive:
 * nothing that an un-migrated page relies on is re-styled.
 */
import React from 'react';
import '../styles/tokens.css';
import '../styles/global.css';
import '../styles/tailwind.css';
import { getLocale } from '../lib/i18n';

export default function AMSDPApp({ Component, pageProps }) {
  // The document language follows the session locale so `:lang(bn)` leading,
  // hyphenation and screen-reader pronunciation match what is on screen.  Runs
  // on every render (a cheap attribute write) because the language switch lives
  // in the shell, not in this component.
  React.useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = getLocale();
    }
  });

  return <Component {...pageProps} />;
}