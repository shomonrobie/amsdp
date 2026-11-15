export async function getServerSideProps() { return { props: {} }; }
/* Schedules — clinic sessions and chamber assignment. AMSDP-FACILITY-DOCTOR-01.
 *
 * A *session* is the thing a patient can actually book: a weekday, a window
 * (start inclusive, end exclusive) and, optionally, a chamber.  This screen is
 * therefore the chamber-assignment screen, not a list of legacy schedule rows:
 *
 *  * it lists the branch's sessions from `GET /api/v1/branches/{id}/sessions`,
 *    grouped by weekday, showing doctor, window and chamber;
 *  * adding a session resolves the doctor's schedule for the branch first (the
 *    API nests sessions inside a schedule) and creates one only when none
 *    exists — a schedule with no sessions books nothing, so creating it early
 *    is harmless and keeps the request count down;
 *  * the form warns about the two conflicts `assert_no_conflict` answers with
 *    409 — the same doctor overlapping, and the same chamber overlapping —
 *    using `windowConflicts` from `lib/facility.js`.  The server still decides;
 *    the warning only saves a round trip.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import Modal from '../components/ui/Modal';
import { getUser, apiFetch, can, getActiveBranch } from '../lib/auth';
import { t, getLocale } from '../lib/i18n';
import {
  WEEKDAYS, dayName, roomOptions, chamberText, windowConflicts, windowText,
  isHhmm, minutesOf, activeOnly,
} from '../lib/facility';

const EMPTY_SESSION = {
  doctor_id: '', day_of_week: 0, start_time: '09:00', end_time: '13:00',
  room_id: '', slot_duration_minutes: '15', max_patients: '4',
};

/** Sessions grouped per weekday in storage order (0 = Monday). */
function byWeekday(sessions) {
  return WEEKDAYS.map((d) => ({
    day: d,
    rows: (sessions || []).filter((s) => Number(s.day_of_week) === d.value),
  })).filter((g) => g.rows.length);
}

export default function Schedules() {
  const user = getUser();
  const orgId = user.organization_id;
  const locale = getLocale();
  const mayManage = can('schedule.manage');

  const [branches, setBranches] = React.useState([]);
  const [branchId, setBranchId] = React.useState('');
  const [doctors, setDoctors] = React.useState([]);
  const [doctorId, setDoctorId] = React.useState('');
  const [sessions, setSessions] = React.useState([]);
  const [rooms, setRooms] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [form, setForm] = React.useState(null);
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (!orgId) return;
    apiFetch('/api/v1/orgs/' + orgId + '/branches')
      .then((d) => {
        const list = Array.isArray(d) ? d : (d.items || []);
        setBranches(list);
        const saved = getActiveBranch();
        const first = list.find((b) => b.id === saved) || list[0];
        if (first) setBranchId(first.id);
        else setLoading(false);
      })
      .catch((e) => { setErr(String(e.message || e)); setLoading(false); });
    apiFetch('/api/v1/doctors')
      .then((d) => setDoctors(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setDoctors([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  const loadBranch = React.useCallback(async (id) => {
    if (!id) return;
    setLoading(true);
    setErr('');
    try {
      const [rows, tree] = await Promise.all([
        apiFetch('/api/v1/branches/' + id + '/sessions'),
        apiFetch('/api/v1/branches/' + id + '/facility'),
      ]);
      setSessions(Array.isArray(rows) ? rows : (rows.items || []));
      setRooms(tree.rooms || []);
    } catch (e) {
      setErr(String(e.message || e));
      setSessions([]);
      setRooms([]);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { loadBranch(branchId); }, [branchId, loadBranch]);

  if (!user.id) return null;

  // A doctor can only hold a session in a branch they are actively assigned to;
  // the API answers 422 otherwise, so the picker offers only valid candidates.
  const assignedDoctors = activeOnly(doctors).filter((d) => (d.branches || []).some(
    (a) => a.branch_id === branchId && (a.status || 'active') === 'active'));

  const doctorName = (id) => {
    const d = doctors.find((x) => x.id === id);
    return d ? d.name : String(id || '').slice(0, 8);
  };

  const weekSessions = doctorId
    ? sessions.filter((s) => s.doctor_id === doctorId)
    : sessions;

  const openAdd = () => {
    setErr('');
    setNotice('');
    setForm({ ...EMPTY_SESSION, doctor_id: doctorId || '' });
  };

  const field = (key) => (e) => {
    const value = e.target.value;
    setForm((cur) => (cur ? { ...cur, [key]: value } : cur));
  };

  // The two 409s the service raises, computed ahead of the request.
  const candidate = form && {
    doctor_id: form.doctor_id,
    room_id: form.room_id,
    day_of_week: Number(form.day_of_week),
    start_time: form.start_time,
    end_time: form.end_time,
  };
  const conflicts = form ? windowConflicts(candidate, sessions) : { doctor: [], chamber: [] };
  const windowInvalid = !!form && minutesOf(form.end_time) !== null
    && minutesOf(form.start_time) !== null
    && minutesOf(form.end_time) <= minutesOf(form.start_time);

  const save = async () => {
    if (!form) return;
    setErr('');
    setNotice('');
    if (!form.doctor_id) { setErr(t('select')); return; }
    if (!isHhmm(form.start_time) || !isHhmm(form.end_time) || windowInvalid) {
      setErr(t('invalidWindow'));
      return;
    }
    setSaving(true);
    const window = {
      day_of_week: Number(form.day_of_week),
      start_time: form.start_time,
      end_time: form.end_time,
      slot_duration_minutes: Number(form.slot_duration_minutes) || 15,
      max_patients: Number(form.max_patients) || 1,
    };
    try {
      if (form.id) {
        // `room_id: null` means *unchanged* on this endpoint, so a cleared
        // chamber must say so explicitly.
        const patch = { ...window };
        if (form.room_id) patch.room_id = form.room_id;
        else patch.clear_chamber = true;
        await apiFetch('/api/v1/sessions/' + form.id, {
          method: 'PATCH',
          body: JSON.stringify(patch),
        });
        setForm(null);
        setNotice(t('savedOk'));
        await loadBranch(branchId);
        return;
      }
      // Sessions live inside a schedule, so resolve (or lazily create) the
      // doctor's schedule for this branch first.
      const found = await apiFetch(
        '/api/v1/schedules?doctor_id=' + form.doctor_id + '&branch_id=' + branchId);
      const list = Array.isArray(found) ? found : (found.items || []);
      let schedule = list.find((s) => (s.status || 'active') === 'active');
      if (!schedule) {
        schedule = await apiFetch('/api/v1/schedules', {
          method: 'POST',
          body: JSON.stringify({
            doctor_id: form.doctor_id,
            organization_id: orgId,
            branch_id: branchId,
            appointment_model: 'time_slot',
            slot_templates: [],
          }),
        });
      }
      await apiFetch('/api/v1/schedules/' + schedule.id + '/sessions', {
        method: 'POST',
        body: JSON.stringify({ ...window, room_id: form.room_id || null }),
      });
      setForm(null);
      setNotice(t('sessionCreated'));
      await loadBranch(branchId);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const retire = async () => {
    if (!form || !form.id) return;
    setErr('');
    setSaving(true);
    try {
      // Retiring keeps the row, so appointments booked into this chamber still
      // resolve the location they were booked into.
      await apiFetch('/api/v1/sessions/' + form.id, { method: 'DELETE' });
      setForm(null);
      setNotice(t('sessionRetired'));
      await loadBranch(branchId);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <RequireLogin>
      <AppShell active="/schedules" breadcrumbs={[{ label: t('schedules') }]}>
        <div>
          <div className="flex justify-between mb-2">
            <h1 className="page-title">{t('schedules')}</h1>
            {mayManage && (
              <button className="btn" style={{ width: 'auto' }} onClick={openAdd}>
                {t('addSession')}
              </button>
            )}
          </div>

          <div className="toolbar">
            <select aria-label={t('branch')} value={branchId}
              onChange={(e) => { setBranchId(e.target.value); setDoctorId(''); }}
              style={{ width: 'auto' }}>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            <select aria-label={t('doctor')} value={doctorId}
              onChange={(e) => setDoctorId(e.target.value)} style={{ width: 'auto' }}>
              <option value="">{t('allDoctors')}</option>
              {sessions.map((s) => s.doctor_id)
                .filter((v, i, all) => all.indexOf(v) === i)
                .map((id) => <option key={id} value={id}>{doctorName(id)}</option>)}
            </select>
          </div>

          {err && <div className="error" role="alert">{err}</div>}
          {notice && <div className="success" role="status">{notice}</div>}
          {!mayManage && <p className="muted">{t('manageOnly')}</p>}

          {loading ? (
            <div className="loading">{t('loading')}</div>
          ) : weekSessions.length === 0 ? (
            <div className="empty">{t('empty')}</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>{t('weekday')}</th>
                  <th>{t('doctor')}</th>
                  <th>{t('window')}</th>
                  <th>{t('chamber')}</th>
                  <th>{t('slotLength')}</th>
                  <th>{t('capacity')}</th>
                  <th>{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {byWeekday(weekSessions).map((group) => group.rows.map((s, index) => (
                  <tr key={s.id}>
                    <td>{index === 0 ? dayName(s.day_of_week, locale) : ''}</td>
                    <td>{s.doctor_name || doctorName(s.doctor_id)}</td>
                    <td>{windowText(s.start_time, s.end_time)}</td>
                    <td>{chamberText(s) || <span className="muted">{t('noChamber')}</span>}</td>
                    <td>{s.slot_duration_minutes || 15} {t('minutes')}</td>
                    <td>{s.max_patients || 1}</td>
                    <td>
                      {mayManage ? (
                        <button className="btn-outline"
                          style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
                          onClick={() => { setErr(''); setForm({ ...EMPTY_SESSION, ...s, id: s.id }); }}>
                          {t('edit')}
                        </button>
                      ) : <span className="muted">—</span>}
                    </td>
                  </tr>
                )))}
              </tbody>
            </table>
          )}
        </div>

        {form && (
          <Modal
            title={form.id ? t('edit') : t('addSession')}
            onClose={() => setForm(null)}
            footer={(
              <>
                <button className="btn-outline" onClick={() => setForm(null)}>{t('cancel')}</button>
                {form.id && (
                  <button className="btn btn-danger" disabled={saving} onClick={retire}>
                    {t('retireSession')}
                  </button>
                )}
                <button className="btn" disabled={saving || windowInvalid} onClick={save}>
                  {t('save')}
                </button>
              </>
            )}
          >
            {!form.id && (
              <div className="form-group">
                <label>{t('doctor')} *</label>
                <select value={form.doctor_id} onChange={field('doctor_id')}>
                  <option value="">{t('select')}</option>
                  {assignedDoctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                {assignedDoctors.length === 0 && (
                  <span className="muted">{t('assignBranches')}</span>
                )}
              </div>
            )}

            <div className="grid-2">
              <div className="form-group">
                <label>{t('weekday')}</label>
                <select value={form.day_of_week} onChange={field('day_of_week')}>
                  {WEEKDAYS.map((d) => (
                    <option key={d.value} value={d.value}>{dayName(d.value, locale)}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>{t('chamber')}</label>
                <select aria-label={t('chamber')} value={form.room_id} onChange={field('room_id')}>
                  <option value="">{t('noChamber')}</option>
                  {roomOptions(rooms).map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label>{t('start')}</label>
                <input type="time" value={form.start_time} onChange={field('start_time')} />
              </div>
              <div className="form-group">
                <label>{t('end')}</label>
                <input type="time" value={form.end_time} onChange={field('end_time')} />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label>{t('slotLength')}</label>
                <input type="number" min="5" max="480" step="5"
                  value={form.slot_duration_minutes} onChange={field('slot_duration_minutes')} />
              </div>
              <div className="form-group">
                <label>{t('capacity')}</label>
                <input type="number" min="1" max="500" step="1"
                  value={form.max_patients} onChange={field('max_patients')} />
              </div>
            </div>

            {windowInvalid && <div className="error">{t('invalidWindow')}</div>}
            {!windowInvalid && conflicts.doctor.length > 0 && (
              <div className="error" role="alert">{t('conflictDoctor')}</div>
            )}
            {!windowInvalid && conflicts.chamber.length > 0 && (
              <div className="error" role="alert">{t('conflictChamber')}</div>
            )}
            {form.id && (
              <p className="muted">{t('retireSession')}: {windowText(form.start_time, form.end_time)}</p>
            )}
          </Modal>
        )}
      </AppShell>
    </RequireLogin>
  );
}
