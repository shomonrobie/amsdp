/* QUE-006 / OD-1 — the operator's audio boundary on the queue page.
 *
 * This file is a thin shell. Every decision lives in `lib/announcements/`
 * (adapter + controller); the component only renders that state and forwards a
 * click. It is deliberately *not* wired to a queue state change: the audible
 * announcement is a separate thing from `call`, from recall, and from an
 * outbound telephone call, and queue operations never await it.
 *
 * The panel renders nothing until mounted: the queue page is server-rendered,
 * and the browser's voice list cannot be known on the server, so rendering the
 * capability before mount would be a hydration mismatch.
 */
import React from 'react';
import { t, getLocale } from '../../lib/i18n';
import { createSpeechSynthesisAdapter } from '../../lib/announcements/speech-synthesis';
import { createAnnouncementController, ACTIVATION } from '../../lib/announcements/controller';

/** The state before the browser has been asked anything. */
export const INITIAL_STATE = Object.freeze({
  enabled: true,
  language: 'bn',
  supported: false,
  capability: 'unsupported',
  voiceLang: null,
  voiceName: null,
  voiceFallback: false,
  activation: ACTIVATION.UNKNOWN,
  requiresActivation: false,
  speaking: false,
  last: null,
});

/**
 * Own one adapter + controller for the lifetime of the page.
 * @returns {{state: object, announce: Function, activate: Function, cancel: Function}}
 */
export function useQueueAnnouncements() {
  const [state, setState] = React.useState(INITIAL_STATE);
  const controllerRef = React.useRef(null);

  React.useEffect(() => {
    const adapter = createSpeechSynthesisAdapter();
    // The facility language setting (OD-2) does not exist yet, so the client
    // speaks the operator's current interface language and never guesses.
    const controller = createAnnouncementController({
      adapter,
      language: getLocale() === 'en' ? 'en' : 'bn',
    });
    controllerRef.current = controller;
    const unsubscribe = controller.subscribe(setState);
    controller.start();
    setState(controller.getState());
    return () => {
      unsubscribe();
      controller.dispose();
      adapter.dispose();
      controllerRef.current = null;
    };
  }, []);

  const announce = React.useCallback(
    (payload, opts) => (controllerRef.current
      ? controllerRef.current.announce(payload, opts)
      : Promise.resolve({ status: 'unsupported' })),
    []
  );
  const activate = React.useCallback(
    () => (controllerRef.current
      ? controllerRef.current.activate()
      : Promise.resolve({ status: 'unsupported' })),
    []
  );
  const cancel = React.useCallback(
    () => { if (controllerRef.current) controllerRef.current.cancel(); },
    []
  );

  return { state, announce, activate, cancel };
}

function badgeClass(state) {
  if (!state.enabled) return 'badge';
  if (state.capability === 'ready' && state.activation === ACTIVATION.GRANTED) return 'badge badge-active';
  if (state.capability === 'unsupported' || state.capability === 'no_voice') return 'badge badge-inactive';
  if (state.activation === ACTIVATION.BLOCKED) return 'badge badge-inactive';
  return 'badge badge-warn';
}

function statusLabel(state) {
  if (!state.enabled) return t('announceAudioOff');
  if (state.capability === 'unsupported') return t('announceAudioUnsupported');
  if (state.capability === 'no_voice') return t('announceNoVoice');
  if (state.capability === 'pending_voices') return t('announceAudioPending');
  if (state.activation === ACTIVATION.BLOCKED) return t('announceAudioBlocked');
  if (state.activation !== ACTIVATION.GRANTED) return t('announceAudioOff');
  return t('announceAudioReady');
}

function outcomeLabel(last) {
  if (!last) return '';
  if (last.status === 'spoken') return t('announceLastSpoken');
  if (last.status === 'duplicate') return t('announceLastDuplicate');
  return t('announceLastSkipped');
}

/**
 * @param {{controller: {state: object, activate: Function}, canAnnounce: boolean}} props
 */
export default function QueueAnnouncements({ controller, canAnnounce }) {
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => { setMounted(true); }, []);

  const state = (controller && controller.state) || INITIAL_STATE;
  if (!mounted) return null;

  const showEnable = !!canAnnounce && state.supported && state.enabled
    && state.activation !== ACTIVATION.GRANTED;

  return (
    <div className="card" role="status" aria-live="polite">
      <div className="flex items-center justify-between flex-wrap" style={{ gap: 8 }}>
        <div>
          <strong>{t('announcements')}</strong>{' '}
          <span className={badgeClass(state)}>{statusLabel(state)}</span>
          {state.voiceFallback && <span className="muted"> · {t('announceVoiceFallback')}</span>}
        </div>
        {showEnable && (
          <button type="button" className="btn btn-sm" onClick={() => controller.activate()}>
            {t('enableAudio')}
          </button>
        )}
      </div>
      {showEnable && state.capability === 'ready' && (
        <p className="muted">{t('announceActivationHint')}</p>
      )}
      {state.capability === 'no_voice' && <p className="muted">{t('announceNoVoiceHint')}</p>}
      {(state.capability === 'unsupported' || state.capability === 'no_voice'
        || state.activation === ACTIVATION.BLOCKED) && (
        <p className="muted">{t('announceNeverBlocks')}</p>
      )}
      {state.last && (
        <p className="muted">
          {t('announceLast')}: {outcomeLabel(state.last)}
          {state.last.text ? ' — “' + state.last.text + '”' : ''}
        </p>
      )}
    </div>
  );
}
