export async function getServerSideProps(){return{props:{}}}
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin, LoadingState, EmptyState, ErrorAlert, SuccessAlert } from '../components/ui/Alert';
import DataTable from '../components/ui/DataTable';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import StatusBadge from '../components/ui/StatusBadge';
import QueueAnnouncements, { useQueueAnnouncements } from '../components/queue/QueueAnnouncements';
import { trackCalledTransitions } from '../lib/announcements/queue-transitions';
import { createCallAnnouncer } from '../lib/announcements/call-announcer';
import { createQueueRefresher } from '../lib/queue/queue-refresh';
import { createCallGate, isCallable, performCall } from '../lib/queue/queue-call';
import { getUser, apiFetch, can, getActiveBranch } from '../lib/auth';
import { t } from '../lib/i18n';

const ST = { waiting: 'waiting', called: 'called', in_consultation: 'in_consultation', skipped: 'skipped', completed: 'completed', cancelled: 'cancelled', no_show: 'no_show' };
const ST_LABELS = {
  waiting: 'waitingKey', called: 'calledKey', in_consultation: 'inConsultationKey', skipped: 'skippedKey',
  completed: 'completedKey', cancelled: 'cancelledKey', no_show: 'noShowKey',
};
const WALK_POLICIES = ['end_of_queue', 'first_come', 'reserved_capacity', 'staff_placement'];

export default function Queue(){
  const user = getUser();
  const branchId = getActiveBranch();
  const [doctors, setDoctors] = React.useState([]);
  const [patients, setPatients] = React.useState([]);
  const [appointments, setAppointments] = React.useState([]);
  const [docId, setDocId] = React.useState('');
  const [date, setDate] = React.useState(new Date().toISOString().slice(0, 10));
  const [entries, setEntries] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [showCi, setShowCi] = React.useState(false);
  const [showWi, setShowWi] = React.useState(false);
  const [ciAppt, setCiAppt] = React.useState('');
  const [wiPat, setWiPat] = React.useState('');
  const [wiPolicy, setWiPolicy] = React.useState('end_of_queue');
  const [cancelTarget, setCancelTarget] = React.useState(null);
  // Sequence 3 / BR §27A — missed-turn + recovery state
  const [missedTarget, setMissedTarget] = React.useState(null);
  const [recoverTarget, setRecoverTarget] = React.useState(null);
  const [recoverMode, setRecoverMode] = React.useState('end_of_queue');
  const [recoverPosition, setRecoverPosition] = React.useState('1');
  const [recoverReason, setRecoverReason] = React.useState('');
  const [busy, setBusy] = React.useState('');
  const [notice, setNotice] = React.useState('');
  // QUE-006 / POD-12 — the entry whose `call` request is in flight, if any.
  const [calling, setCalling] = React.useState('');
  // QUE-006 / W2 — the last delivery-claim result, shown as a quiet note (it is
  // never rendered as an error: losing a claim is normal on a second terminal).
  const [delivery, setDelivery] = React.useState(null);
  const callGate = React.useRef(createCallGate());

  const canManage = can('queue.manage');
  const canConsult = can('queue.consult');
  const canRecover = can('queue.recover');
  const canReposition = can('queue.reposition');

  // QUE-006 / OD-1: the audible announcement is a client-side mechanism. It is
  // offered to the roles the catalogue names as triggers (front desk and doctor)
  // and it never changes queue state — `call` and recall stay separate actions.
  const canAnnounce = canManage || canConsult;
  const announcements = useQueueAnnouncements();

  const announceEntry = (entry) => {
    announcements.announce(
      {
        queueEntryId: entry.id,
        action: 'announce',
        // The server identity, when the backend provides one. An operator repeat
        // is deliberate (`source: 'operator'`), so it is neither claimed nor
        // suppressed: one call event has one delivery record, and a repeat is
        // not a second delivery.
        eventId: entry.call_event_id,
        token: entry.token,
        // Doctor name removed from announcements (QUE-006 doctor-name removal).
        // No queue endpoint returns a room yet; omitted rather than invented.
        room: entry.room,
      },
      { source: 'operator', userGesture: true }
    );
  };

  // QUE-006 / W2 — the delivery claim (V-12) and the persisted outcome (POD-4).
  //
  // This is the only place in the page that writes an announcement record, and
  // it writes it *outside* the queue transaction: the call has already committed
  // by the time a transition is observed, so a claim or a lost outcome report can
  // never reverse it.
  //
  // The controller state is read through a ref: `useQueueAnnouncements` returns a
  // fresh object on every render, and the voice pack arrives after mount. A
  // captured copy would claim with an empty pack id for the rest of the session.
  const announcementsRef = React.useRef(announcements);
  React.useEffect(() => { announcementsRef.current = announcements; });
  const callAnnouncer = React.useMemo(() => createCallAnnouncer({
    announce: (payload, opts) => announcementsRef.current.announce(payload, opts),
    describe: () => {
      const state = announcementsRef.current.state || {};
      return {
        enabled: state.enabled,
        language: state.language,
        voicePackId: state.packId,
        voicePackVersion: state.packVersion,
        transport: state.transport,
      };
    },
    post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  }), []);

  // QUE-006 / W2 — the queue-call trigger.
  //
  // A `call` (waiting → called) makes the entry audible. The announcement is
  // fired and *forgotten*: the queue transaction has already committed on the
  // server and this page never awaits audio, so a playback failure cannot
  // reverse a successful call. The announcer first claims the server-generated
  // call event, so exactly one terminal speaks, and then reports the outcome.
  //
  // There is now a `call` control (QUE-006 / POD-12, below). It does not speak:
  // it PATCHes the entry and lets the refetch produce the transition this seam
  // observes. Audio therefore stays optional — a failed request never refreshes
  // the list, so it never announces.
  const announceOnCall = (entry) => {
    callAnnouncer.announceCall(entry, { source: 'event' }).then(setDelivery);
  };

  // QUE-006 / W2 — a background refresh must not flash a spinner over a list the
  // operator is reading, and a failed refresh must not empty it: the previous
  // entries stay, and only the error surface changes.
  const loadQueue = (opts = {}) => {
    const quiet = opts.quiet === true;
    if (!docId || !date) { setEntries([]); return Promise.resolve(); }
    if (!quiet) { setLoading(true); setError(''); }
    return apiFetch(`/api/v1/queue?doctor_id=${encodeURIComponent(docId)}&date=${encodeURIComponent(date)}`)
      .then((d) => { setEntries(d.entries || []); if (!quiet) setLoading(false); })
      .catch((e) => { setError('Queue load failed: ' + (e.message || e)); if (!quiet) setLoading(false); });
  };

  const loadRefs = () => {
    apiFetch('/api/v1/doctors').then((d) => setDoctors(d.items || [])).catch(() => {});
    apiFetch('/api/v1/patients?page=1&limit=100').then((d) => setPatients(d.items || [])).catch(() => {});
    apiFetch('/api/v1/appointments?date=' + date).then((d) => setAppointments(Array.isArray(d) ? d : [])).catch(() => {});
  };

  React.useEffect(() => { loadRefs(); }, [date]);
  React.useEffect(() => { loadQueue(); }, [docId, date]);

  // QUE-006 / W2 — cross-terminal delivery and safe refresh.
  //
  // The queuing service publishes no events, so a second terminal only sees a
  // call by re-reading the queue. The refresher re-reads while the tab is
  // visible (interval, focus, back-online, tab shown) and never while it is
  // hidden; the announcer then decides — from the server's `call_event_id` and
  // its freshness — whether anything found there may still be spoken. The
  // latest `loadQueue` is read through a ref so a direction or date change is
  // picked up without tearing the listeners down.
  const loadQueueRef = React.useRef(loadQueue);
  React.useEffect(() => { loadQueueRef.current = loadQueue; });

  React.useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const refresher = createQueueRefresher({
      refresh: () => loadQueueRef.current({ quiet: true }),
      document: typeof document === 'undefined' ? null : document,
      window,
      onError: (e) => setError('Queue refresh failed: ' + ((e && e.message) || e)),
    });
    refresher.start();
    return () => refresher.stop();
  }, []);

  // QUE-006 / W2: announce the transition into `called`, once. The tracker is
  // seeded on first observation, so entries already called when the page loads
  // stay silent; the controller's event key suppresses a repeat of the same
  // entry. The call is not awaited — the queue operation has already committed.
  const calledTracker = React.useRef(new Map());
  React.useEffect(() => {
    const { next, transitioned } = trackCalledTransitions(calledTracker.current, entries);
    calledTracker.current = next;
    transitioned.forEach((entry) => announceOnCall(entry));
  }, [entries]);

  // QUE-006 / POD-12 — the approved queue Call action (gap QOP-001).
  //
  // `call` is the existing server transition: PATCH /api/v1/queue/{id} with
  // action "call", authorised by `queue.manage`. Nothing is invented here — the
  // gate only stops a second click from sending a second request while the
  // first is pending, and the list is refreshed *only* when the server answered
  // successfully, so a failed call cannot produce a `called` row (and therefore
  // cannot be announced). The announcement itself is the refetch's job.
  const callEntry = async (entry) => {
    if (!canManage || !isCallable(entry)) return;   // UI mirror; the server decides
    if (callGate.current.current()) return;         // one call at a time
    setCalling(entry.id); setError(''); setNotice('');
    const result = await performCall({
      entry,
      authorised: canManage,
      gate: callGate.current,
      request: (id, payload) => apiFetch('/api/v1/queue/' + id,
        { method: 'PATCH', body: JSON.stringify(payload) }),
    });
    setCalling('');
    if (result.status === 'called') {
      setNotice(t('calledNotice'));
      loadQueue();
    } else if (result.status === 'failed') {
      setError(t('callFailed') + ': ' + ((result.error && result.error.message) || result.error));
    }
  };

  const doAction = async (id, action, reason) => {
    try {
      await apiFetch('/api/v1/queue/' + id, { method: 'PATCH', body: JSON.stringify({ action, reason: reason || '' }) });
      loadQueue();
    } catch (e) { setError('Action failed: ' + e.message); }
  };

  const checkIn = async () => {
    try { await apiFetch('/api/v1/queue/check-in', { method: 'POST', body: JSON.stringify({ appointment_id: ciAppt }) });
      setShowCi(false); setCiAppt(''); loadQueue(); }
    catch (e) { setError('Check-in failed: ' + e.message); }
  };

  const walkIn = async () => {
    try { await apiFetch('/api/v1/queue/enqueue', { method: 'POST',
      body: JSON.stringify({ doctor_id: docId, patient_id: wiPat, entry_source: 'walk_in', walk_in_policy: wiPolicy }) });
      setShowWi(false); setWiPat(''); loadQueue(); }
    catch (e) { setError('Walk-in failed: ' + e.message); }
  };

  // Sequence 3 / BR §27A — staff-confirmed missed turn. The token and the
  // appointment are preserved server-side; this UI never decides scope.
  const markMissedTurn = async (id, reason) => {
    if (busy) return;                        // duplicate-submit guard
    setBusy(id + ':missed'); setError(''); setNotice('');
    try {
      await apiFetch('/api/v1/queue/' + id + '/missed-turn',
        { method: 'POST', body: JSON.stringify({ reason: reason || '' }) });
      setNotice(t('missedTurnRecorded'));
      setMissedTarget(null);
      loadQueue();
    } catch (e) { setError('Missed turn failed: ' + e.message); }
    finally { setBusy(''); }
  };

  // Sequence 3 / BR §27A.3 — recovery. Default re-entry is the end of the
  // queue; a position override needs queue.reposition and a written reason
  // (the server rejects a missing reason with 422 — the UI is not the boundary).
  const recoverEntry = async () => {
    if (!recoverTarget || busy) return;      // duplicate-submit guard
    const override = recoverMode === 'position_override';
    if (override && !recoverReason.trim()) {
      setError(t('recoveryReason') + ' *');
      return;
    }
    setBusy(recoverTarget.id + ':recover'); setError(''); setNotice('');
    const body = override
      ? { target_position: Number(recoverPosition), reason: recoverReason.trim() }
      : { reason: recoverReason.trim() };
    try {
      await apiFetch('/api/v1/queue/' + recoverTarget.id + '/recover',
        { method: 'POST', body: JSON.stringify(body) });
      setNotice(t('recoveredNotice'));
      setRecoverTarget(null); setRecoverReason(''); setRecoverMode('end_of_queue');
      loadQueue();
    } catch (e) { setError('Recovery failed: ' + e.message); }
    finally { setBusy(''); }
  };

  const move = async (idx, dir) => {
    const ids = entries.map((e) => e.id);
    const j = idx + dir;
    if (j < 0 || j >= ids.length) return;
    [ids[idx], ids[j]] = [ids[j], ids[idx]];
    try { await apiFetch('/api/v1/queue/reorder', { method: 'POST',
      body: JSON.stringify({ entry_ids: ids, reason: dir < 0 ? 'manual_move_up' : 'manual_move_down' }) });
      loadQueue(); }
    catch (e) { setError('Reorder failed: ' + e.message); }
  };

  const bookable = appointments.filter((a) => ['CONFIRMED'].includes(a.status));

return (
    <RequireLogin>
      <AppShell active="/queue" breadcrumbs={[{ label: t('dash'), href: '/dashboard' }, { label: t('queue') }]}>
        <div className="flex justify-between mb-2">
          <h1 className="page-title">{t('queue')}</h1>
          {canManage && (
            <div className="flex items-center gap-2">
              <button className="btn" onClick={() => setShowCi(true)}>{t('checkIn')}</button>
              <button className="btn" onClick={() => setShowWi(true)}>{t('walkIn')}</button>
            </div>
          )}
        </div>
        <div className="flex mb-2 flex-wrap">
          <select value={docId} onChange={(e) => setDocId(e.target.value)} style={{ width: 220 }}>
            <option value="">{t('doctor')}</option>
            {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ width: 160 }} />
          <button className="btn" onClick={loadQueue} style={{ width: 'auto' }}>{t('search')}</button>
        </div>
        {error && <ErrorAlert>{error}</ErrorAlert>}
        {notice && <SuccessAlert>{notice}</SuccessAlert>}
        <QueueAnnouncements controller={announcements} canAnnounce={canAnnounce} delivery={delivery} />
        {loading ? <LoadingState /> : entries.length === 0 ? <EmptyState msg={t('empty')} /> : (
          <div className="table-wrap">
            <DataTable rowKey="id" rows={entries}
              columns={[
                { key: 'position', label: '#' },
                { key: 'token', label: t('token') },
                { render: (r) => r.patient_name || (r.patient_id || '').substring(0, 8), label: t('patients') },
                { key: 'entry_source', label: t('source') },
                { render: (r) => (<span><StatusBadge status={r.status} label={t(ST_LABELS[r.status] || r.status) || r.status} />
                  {r.status === 'skipped' && <span className="org-ctx"> {t('awaitingRecovery')}</span>}</span>), label: t('status') },
                { render: (r, i) => (
                  <div className="flex flex-wrap">
                    {canManage && <><button className="btn btn-sm btn-outline" onClick={() => move(i, -1)}>↑</button>
                      <button className="btn btn-sm btn-outline" onClick={() => move(i, 1)}>↓</button></>}
                    {canManage && isCallable(r) && (
                      <button className="btn btn-sm" disabled={!!busy || !!calling}
                        onClick={() => callEntry(r)}>
                        {calling === r.id ? t('pleaseWait') : t('call')}
                      </button>
                    )}
                    {canConsult && r.status === 'waiting' && <button className="btn btn-sm" onClick={() => doAction(r.id, 'start_consultation')}>{t('start')}</button>}
                    {canConsult && r.status === 'in_consultation' && <button className="btn btn-sm" style={{ background: '#2e7d32' }} onClick={() => doAction(r.id, 'complete_consultation')}>{t('complete')}</button>}
                    {canManage && r.status === 'waiting' && <button className="btn btn-sm btn-danger" onClick={() => setCancelTarget(r.id)}>{t('cancel')}</button>}
                    {canAnnounce && r.status === 'called' && (
                      <button className="btn btn-sm btn-outline" disabled={!!busy}
                        onClick={() => announceEntry(r)}>{t('announce')}</button>
                    )}
                    {canRecover && ['waiting', 'called'].includes(r.status) && (
                      <button className="btn btn-sm btn-outline" disabled={!!busy}
                        onClick={() => { setError(''); setNotice(''); setMissedTarget(r); }}>
                        {t('missedTurn')}</button>)}
                    {canRecover && r.status === 'skipped' && (
                      <button className="btn btn-sm btn-outline" disabled={!!busy}
                        onClick={() => { setError(''); setNotice(''); setRecoverTarget(r); }}>
                        {t('recover')}</button>)}
                  </div>
                ), label: t('actions') },
              ]}
            />
          </div>
        )}

        {showCi && (
          <Modal title={t('checkIn')} onClose={() => setShowCi(false)}
            footer={<><button className="btn-outline" onClick={() => setShowCi(false)}>{t('cancel')}</button>
              <button className="btn" onClick={checkIn}>{t('checkIn')}</button></>}>
            <div className="form-group"><label>{t('appointments')}</label>
              <select value={ciAppt} onChange={(e) => setCiAppt(e.target.value)}>
                <option value="">{t('select')}...</option>
                {bookable.map((a) => <option key={a.id} value={a.id}>
                  {(a.token_number || a.id.substring(0, 8)) + ' · ' + a.patient_id.substring(0, 8) + ' @' + a.appointment_date}</option>)}
              </select></div>
          </Modal>
        )}

        {showWi && (
          <Modal title={t('walkIn')} onClose={() => setShowWi(false)}
            footer={<><button className="btn-outline" onClick={() => setShowWi(false)}>{t('cancel')}</button>
              <button className="btn" onClick={walkIn}>{t('submit')}</button></>}>
            <div className="form-group"><label>{t('patients')}</label>
              <select value={wiPat} onChange={(e) => setWiPat(e.target.value)}>
                <option value="">{t('select')}...</option>
                {patients.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.mobile})</option>)}
              </select></div>
            <div className="form-group"><label>{t('policy')}</label>
              <select value={wiPolicy} onChange={(e) => setWiPolicy(e.target.value)}>
                {WALK_POLICIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select></div>
          </Modal>
        )}

        {missedTarget && (
          <ConfirmDialog title={t('missedTurnTitle')} message={t('missedTurnMsg')}
            onClose={() => setMissedTarget(null)}
            onConfirm={(reason) => markMissedTurn(missedTarget.id, reason)} />
        )}

        {recoverTarget && (
          <Modal title={t('recoverTitle')} onClose={() => setRecoverTarget(null)}
            footer={<><button className="btn-outline" onClick={() => setRecoverTarget(null)}>{t('cancel')}</button>
              <button className="btn"
                disabled={!!busy || (recoverMode === 'position_override' && !recoverReason.trim())}
                onClick={recoverEntry}>{busy ? t('pleaseWait') : t('confirm')}</button></>}>
            <p>{t('recoverMsg')}</p>
            <div className="form-group"><label>{t('recoveryMode')}</label>
              <select value={recoverMode} onChange={(e) => setRecoverMode(e.target.value)}>
                <option value="end_of_queue">{t('endOfQueue')}</option>
                {canReposition && <option value="position_override">{t('atPosition')}...</option>}
              </select></div>
            {recoverMode === 'position_override' && (
              <div className="form-group"><label>{t('position')}</label>
                <select value={recoverPosition} onChange={(e) => setRecoverPosition(e.target.value)}>
                  {Array.from({ length: entries.length + 1 }, (_, n) => n + 1)
                    .map((n) => <option key={n} value={n}>{n}</option>)}
                </select></div>
            )}
            <div className="form-group">
              <label>{t('recoveryReason')}{recoverMode === 'position_override' ? ' *' : ''}</label>
              <input value={recoverReason} onChange={(e) => setRecoverReason(e.target.value)} />
            </div>
            {recoverTarget.token && <p className="org-ctx">{t('token')}: {recoverTarget.token}</p>}
          </Modal>
        )}

        {cancelTarget && (
          <ConfirmDialog title="Cancel queue entry" message="Cancel this patient's queue entry?" requireReason
            onClose={() => setCancelTarget(null)}
            onConfirm={(reason) => { doAction(cancelTarget, 'cancel', reason); setCancelTarget(null); }} />
        )}
      </AppShell>
    </RequireLogin>
  );
}