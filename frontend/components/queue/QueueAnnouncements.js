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
import { createPrerecordedPlayer } from '../../lib/announcements/prerecorded-audio';
import { resolveAnnouncementConfig } from '../../lib/announcements/voice-packs';
import { createAnnouncementController, ACTIVATION } from '../../lib/announcements/controller';

/** The state before the browser has been asked anything. */
export const INITIAL_STATE = Object.freeze({
  enabled: true,
  language: 'bn',
  transport: 'prerecorded',
  supported: false,
  capability: 'pending_voices',
  packId: '',
  packVersion: 0,
  voiceLang: null,
  voiceName: null,
  voiceFallback: false,
  activation: ACTIVATION.UNKNOWN,
  requiresActivation: false,
  speaking: false,
  last: null,
});

/**
 * Own one adapter + player + controller for the lifetime of the page.
 * @returns {{state: object, announce: Function, activate: Function, cancel: Function}}
 */
export function useQueueAnnouncements() {
  const [state, setState] = React.useState(INITIAL_STATE);
  const controllerRef = React.useRef(null);

  React.useEffect(() => {
    // The facility language setting (OD-2) does not exist yet, so the client
    // speaks the operator's current interface language and never guesses.
    const language = getLocale() === 'en' ? 'en' : 'bn';

    // QUE-006: prerecorded playback is the primary mechanism. The pack is read
    // from the installed catalogue; until it arrives the player reports
    // "pending", never a substituted mechanism.
    let pack = null;
    let disposed = false;
    const player = createPrerecordedPlayer({ packProvider: () => pack });
    const adapter = createSpeechSynthesisAdapter();
    // A speech adapter is still required by the controller: browser speech is
    // the documented alternative transport, chosen explicitly by configuration.
    const controller = createAnnouncementController({ adapter, player, language });
    controllerRef.current = controller;
    const unsubscribe = controller.subscribe(setState);
    controller.start();
    setState(controller.getState());

    const loadPack = async () => {
      try {
        const response = await fetch('/audio/manifest.json', { cache: 'force-cache' });
        if (!response.ok || disposed) return;
        const manifest = await response.json();
        if (disposed) return;
        // The shipped catalogue is the built-in draft pack. Selection goes
        // through the precedence resolver so an organisation override (W3)
        // only has to supply configuration, not a new code path.
        const builtin = {
          [language]: {
            id: 'platform.' + language + '.draft.v1',
            language,
            version: 1,
            scope: 'platform',
            source: 'builtin',
            status: 'draft',
            basePath: '/audio',
            manifest,
          },
        };
        const resolved = resolveAnnouncementConfig({ builtin });
        pack = resolved.packs[language];
        controller.refresh();
      } catch (err) {
        // Offline or missing catalogue: the panel says so instead of speaking
        // with a different voice or a different language.
      }
    };
    loadPack();

    return () => {
      disposed = true;
      unsubscribe();
      controller.dispose();
      adapter.dispose();
      player.dispose();
      controllerRef.current = null;
    };
  }, []);

  const announce = React.useCallback(
    (payload, opts) => (controllerRef.current
      ? controllerRef.current.announce(payload, opts)
      : Promise.resolve({ status: 'unavailable' })),
    []
  );
  const activate = React.useCallback(
    () => (controllerRef.current
      ? controllerRef.current.activate()
      : Promise.resolve({ status: 'unavailable' })),
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
  if (state.capability === 'no_voice') {
    return state.transport === 'prerecorded' ? t('announcePackMissing') : t('announceNoVoice');
  }
  if (state.capability === 'pending_voices') return t('announceAudioPending');
  if (state.activation === ACTIVATION.BLOCKED) return t('announceAudioBlocked');
  if (state.activation !== ACTIVATION.GRANTED) return t('announceAudioOff');
  return t('announceAudioReady');
}

function outcomeLabel(last) {
  if (!last) return '';
  // D-6 (2026-11-22): a finished playback is `completed`; a sentence that
  // started and was stopped is `interrupted`. An interrupted sentence did begin,
  // so it reads as a failed playback rather than as "not played".
  if (last.status === 'completed') return t('announceLastSpoken');
  if (last.status === 'duplicate') return t('announceLastDuplicate');
  if (last.status === 'failed' || last.status === 'interrupted') return t('announceLastFailed');
  return t('announceLastSkipped');
}

/**
 * QUE-006 / W2 — how the *delivery claim* ended, when it is worth saying.
 *
 * A claim that another terminal won, or that the server refused, is not an error:
 * the call is being announced somewhere, or it is no longer the current call.
 * It is reported as a quiet note so an operator watching a second screen knows
 * why their terminal stayed silent. A stale or already-seen event says nothing.
 *
 * The note is deliberately *not* an error: the three reasons below are all
 * "someone else is handling this call", which the operator cannot fix.
 */
function deliveryNote(delivery) {
  if (!delivery || delivery.status !== 'skipped') return '';
  const reason = delivery.reason || '';
  if (reason === 'duplicate_event' || reason === 'not_owner' || reason === 'claim_rejected') {
    return t('announceElsewhere');
  }
  return '';
}

/**
 * @param {{controller: {state: object, activate: Function}, canAnnounce: boolean,
 *          delivery?: object}} props
 */
export default function QueueAnnouncements({ controller, canAnnounce, delivery }) {
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
      {state.capability === 'no_voice' && (
        <p className="muted">
          {state.transport === 'prerecorded' ? t('announcePackHint') : t('announceNoVoiceHint')}
        </p>
      )}
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
      {deliveryNote(delivery) && (
        <p className="muted">{deliveryNote(delivery)}</p>
      )}
    </div>
  );
}
