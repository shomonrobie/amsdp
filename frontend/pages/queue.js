export async function getServerSideProps(){return{props:{}}}
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin, LoadingState, EmptyState, ErrorAlert, SuccessAlert } from '../components/ui/Alert';
import DataTable from '../components/ui/DataTable';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import StatusBadge from '../components/ui/StatusBadge';
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

  const canManage = can('queue.manage');
  const canConsult = can('queue.consult');
  const canRecover = can('queue.recover');
  const canReposition = can('queue.reposition');

  const loadQueue = () => {
    if (!docId || !date) { setEntries([]); return; }
    setLoading(true); setError('');
    apiFetch(`/api/v1/queue?doctor_id=${encodeURIComponent(docId)}&date=${encodeURIComponent(date)}`)
      .then((d) => { setEntries(d.entries || []); setLoading(false); })
      .catch((e) => { setError('Queue load failed: ' + (e.message || e)); setLoading(false); });
  };

  const loadRefs = () => {
    apiFetch('/api/v1/doctors').then((d) => setDoctors(d.items || [])).catch(() => {});
    apiFetch('/api/v1/patients?page=1&limit=100').then((d) => setPatients(d.items || [])).catch(() => {});
    apiFetch('/api/v1/appointments?date=' + date).then((d) => setAppointments(Array.isArray(d) ? d : [])).catch(() => {});
  };

  React.useEffect(() => { loadRefs(); }, [date]);
  React.useEffect(() => { loadQueue(); }, [docId, date]);

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
            <div className="flex">
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
                    {canConsult && r.status === 'waiting' && <button className="btn btn-sm" onClick={() => doAction(r.id, 'start_consultation')}>{t('start')}</button>}
                    {canConsult && r.status === 'in_consultation' && <button className="btn btn-sm" style={{ background: '#2e7d32' }} onClick={() => doAction(r.id, 'complete_consultation')}>{t('complete')}</button>}
                    {canManage && r.status === 'waiting' && <button className="btn btn-sm btn-danger" onClick={() => setCancelTarget(r.id)}>{t('cancel')}</button>}
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