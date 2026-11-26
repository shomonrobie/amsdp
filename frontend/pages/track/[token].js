import React from 'react';
import { tIn } from '../../lib/i18n';

/* PQT — Personal Queue Tracking: account-free appointment visibility.
 *
 * MP-25 hardened this page rather than rewrote it:
 *
 *  * **The estimate is always labelled.** The waiting time is a forecast built
 *    from an average, so the number carries its marker beside it and the server
 *    marks it with `queue.estimate` — a bare number would read as a promise
 *    (R-13).
 *  * **A printable token card.** The QR image comes from
 *    `/api/v1/track/{token}/qr`; the print layout keeps the token and the QR and
 *    drops the screen-only furniture.  Nothing printed here identifies the
 *    patient: no name, no mobile number, no record id.
 *  * **One i18n mechanism (MP-28).** The page-local {bn,en} table is gone; these
 *    strings live in `lib/i18n.js` with every other screen's.
 */

/* Appointment statuses are the server's vocabulary; each maps to a label key. */
const STATUS_KEYS = {
  BOOKED: 'booked',
  CONFIRMED: 'pqtConfirmed',
  AWAITING_CONFIRMATION: 'pqtAwaiting',
  CHECKED_IN: 'checkedIn',
  IN_QUEUE: 'pqtInQueue',
  IN_CONSULTATION: 'inConsultationKey',
  COMPLETED: 'completedT',
  CANCELLED: 'cancelledT',
  NO_SHOW: 'noShow',
};

function getToken() {
  try {
    const m = window.location.pathname.match(/\/track\/(.+)/);
    return m ? m[1] : '';
  } catch (e) { return ''; }
}

function deviceLang() {
  try {
    return window.sessionStorage.getItem('locale') === 'en' ? 'en' : 'bn';
  } catch (e) { return 'bn'; }
}

export default function Track() {
  const [d, setD] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [lang, setLang] = React.useState('bn');
  const [printed, setPrinted] = React.useState(false);
  const token = getToken();

  React.useEffect(() => { setLang(deviceLang()); }, []);

  React.useEffect(() => {
    if (!token || token.length < 32) {
      setErr('error');
      setLoading(false);
      return undefined;
    }
    let cancelled = false;
    const read = () => fetch('/api/v1/track/' + encodeURIComponent(token))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
    read().then((j) => {
      if (cancelled) return;
      if (j) setD(j); else setErr('error');
      setLoading(false);
    });
    const iv = setInterval(() => {
      read().then((j) => { if (!cancelled && j) setD(j); });
    }, 15000);
    return () => { cancelled = true; clearInterval(iv); };
  }, [token]);

  /* Print is a browser action, never a server one: the page already on screen is
     what comes out of the printer. */
  function printCard() {
    setPrinted(true);
    try { window.print(); } catch (e) { /* unavailable — the card is still on screen */ }
  }

  const tr = (k) => tIn(lang, k);

  if (err) {
    return (
      <div className="pqt-root"><div className="pqt-card">
        <p style={{ color: '#888', textAlign: 'center', padding: '2rem' }}>{tr('error')}</p>
      </div></div>
    );
  }
  if (loading) {
    return (
      <div className="pqt-root"><div className="pqt-card">
        <p style={{ textAlign: 'center', padding: '2rem' }}>{tr('loading')}</p>
      </div></div>
    );
  }
  if (!d) return null;

  const a = d.appointment || {};
  const q = d.queue || {};
  const doc = d.doctor || {};
  const br = d.branch || {};
  const statusLabel = STATUS_KEYS[a.status] ? tr(STATUS_KEYS[a.status]) : (a.status || '-');
  const estimate = q.estimated_wait_min;
  const hasEstimate = estimate !== null && estimate !== undefined;

  return (
    <div className="pqt-root">
      <div className="pqt-card" data-testid="pqt-card">
        <h2 style={{ margin: '0 0 0.5rem' }} data-testid="pqt-title">{tr('pqtTitle')}</h2>
        <p style={{ fontSize: '0.75rem', color: '#888', marginBottom: '0.8rem' }}>{tr('pqtPrivacy')}</p>

        <div className="pqt-grid">
          <div><strong>{tr('doctor')}</strong><br />{doc.name || '-'}</div>
          <div><strong>{tr('branch')}</strong><br />{br.name || '-'}</div>
          <div><strong>{tr('date')}</strong><br />{a.date || '-'}</div>
          <div><strong>{tr('time')}</strong><br />{a.start_time || '-'}</div>
          <div><strong>{tr('status')}</strong><br />{statusLabel}</div>
          <div><strong>{tr('token')}</strong><br />{q.my_token || a.token_number || '-'}</div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #ddd', margin: '1rem 0' }} />

        <div className="pqt-queue">
          <div className="pqt-serving">
            {tr('pqtNowServing')}: <strong style={{ fontSize: '1.2rem', color: '#1a5c7a' }}>{q.currently_serving || '-'}</strong>
          </div>
          <div className="pqt-stats">
            <div><span className="stat-num">{q.patients_ahead ?? '-'}</span><br />{tr('pqtAhead')}</div>
            <div>
              {/* The marker is part of the number, never a footnote. */}
              <span className="stat-num" data-testid="pqt-estimate">
                {hasEstimate ? '\u2248 ' + estimate : '-'}
              </span>
              <br />{tr('pqtEta')} ({tr('minutes')})
            </div>
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #ddd', margin: '1rem 0' }} />
        <p style={{ fontSize: '0.75rem', color: '#c62828' }}>{tr('pqtWarn')}</p>
        <p style={{ fontSize: '0.7rem', color: '#888' }}>{tr('pqtStay')}</p>

        {/* MP-25 — the printable token card.  It carries the token and the QR and
            nothing that identifies the patient; @media print in global.css hides
            the screen-only furniture. */}
        <div className="pqt-print-block" data-testid="pqt-print-block">
          <img className="pqt-qr" alt={tr('pqtQrAlt')} data-testid="pqt-qr"
            src={'/api/v1/track/' + encodeURIComponent(token) + '/qr'} />
          <div className="pqt-print-side">
            <p className="pqt-print-hint">
              <strong>{q.my_token || a.token_number || '-'}</strong> — {tr('pqtPrintHint')}
            </p>
            <button type="button" className="btn btn-outline btn-sm"
              data-testid="pqt-print" onClick={printCard}>
              {tr('pqtPrint')}
            </button>
            {printed ? <span className="pqt-print-hint" data-testid="pqt-printed">{tr('pqtPrinted')}</span> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
