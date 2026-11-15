export async function getServerSideProps() { return { props: {} }; }
/* Doctor Management — directory, profile, chambers and BMDC verification.
 * AMSDP-FACILITY-DOCTOR-01.
 *
 * The page is a directory first: one row per doctor showing the mobile in the
 * canonical `01XXXXXXXXX` form the API stores, the specialities as structured
 * links (not one free-text string), every branch with its chamber, the
 * consultation fee and the BMDC verification state.
 *
 * All rules live elsewhere and are only *applied* here:
 *  * `lib/phone.js`    — mirrors `backend/common/phone.py`, so a malformed
 *                        number is refused before the request is sent;
 *  * `lib/facility.js` — chamber labels, BMDC labels and the permitted
 *                        verification transitions;
 *  * `lib/auth.js`     — `can()` mirrors `backend/common/permissions.py`.
 * The server still decides; the UI never offers what the API would refuse, and
 * a refused call is shown with the API's own message.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import Modal from '../components/ui/Modal';
import { getUser, apiFetch, can } from '../lib/auth';
import { t, getLocale } from '../lib/i18n';
import { validateMobile, formatMobile } from '../lib/phone';
import {
  initials, bmdcLabel, bmdcBadgeClass, bmdcTransitions, specialityName,
  roomOptions, chamberText, activeOnly,
} from '../lib/facility';

/** A blank profile form; `branches` holds one entry per assigned branch. */
const EMPTY_FORM = {
  id: '', name: '', mobile: '', registration_number: '', qualification: '',
  consultation_fee: '', specialty_ids: [], branches: [], photoSrc: '',
};

/** Chamber of one assignment, preferring the loaded facility over the snapshot. */
function assignmentChamber(assignment, rooms) {
  const room = assignment.room_id
    ? (rooms || []).find((r) => r.id === assignment.room_id) : null;
  return room ? chamberText(room) : (assignment.room_name || '');
}

export default function Doctors() {
  const user = getUser();
  const orgId = user.organization_id;
  const mayManage = can('doctor.create') || can('doctor.manage');

  const [items, setItems] = React.useState([]);
  const [specialities, setSpecialities] = React.useState([]);
  const [branches, setBranches] = React.useState([]);
  const [roomsByBranch, setRoomsByBranch] = React.useState({});
  const [filters, setFilters] = React.useState({ q: '', branch_id: '', specialty_id: '', status: '' });
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [form, setForm] = React.useState(null);
  const [verify, setVerify] = React.useState(null);
  const [saving, setSaving] = React.useState(false);

  const doctorsUrl = React.useCallback((f) => {
    const p = new URLSearchParams();
    if ((f.q || '').trim()) p.set('q', f.q.trim());
    if (f.branch_id) p.set('branch_id', f.branch_id);
    if (f.specialty_id) p.set('specialty_id', f.specialty_id);
    if (f.status) p.set('status', f.status);
    const qs = p.toString();
    return '/api/v1/doctors' + (qs ? '?' + qs : '');
  }, []);

  const loadDoctors = React.useCallback(async (f) => {
    setLoading(true);
    setErr('');
    try {
      const data = await apiFetch(doctorsUrl(f));
      setItems(Array.isArray(data) ? data : (data.items || []));
    } catch (e) {
      setErr(String(e.message || e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [doctorsUrl]);

  React.useEffect(() => {
    if (!user.id) return;
    loadDoctors(filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  React.useEffect(() => {
    if (!orgId) return;
    apiFetch('/api/v1/orgs/' + orgId + '/specialties')
      .then((d) => setSpecialities(activeOnly(Array.isArray(d) ? d : (d.items || []))))
      .catch(() => setSpecialities([]));
    apiFetch('/api/v1/orgs/' + orgId + '/branches')
      .then(async (d) => {
        const list = Array.isArray(d) ? d : (d.items || []);
        setBranches(list);
        // One facility read per branch: the branch API has no room list that
        // also carries the floor and department names a chamber label needs.
        const pairs = await Promise.all(list.map(async (b) => {
          try {
            const tree = await apiFetch('/api/v1/branches/' + b.id + '/facility');
            return [b.id, tree.rooms || []];
          } catch (e) { return [b.id, []]; }
        }));
        setRoomsByBranch(Object.fromEntries(pairs));
      })
      .catch(() => setBranches([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  if (!user.id) return null;

  // ---------------------------------------------------------------------
  // Form state
  // ---------------------------------------------------------------------

  const openCreate = () => {
    setErr('');
    setNotice('');
    setForm({ ...EMPTY_FORM });
  };

  const openEdit = async (doctor) => {
    setErr('');
    setNotice('');
    const assigned = (doctor.branches || [])
      .filter((a) => (a.status || 'active') === 'active')
      .map((a) => ({
        assignment_id: a.id,
        branch_id: a.branch_id,
        branch_name: a.branch_name,
        room_id: a.room_id || '',
        is_primary: !!a.is_primary,
      }));
    setForm({
      id: doctor.id,
      name: doctor.name || '',
      mobile: doctor.mobile || '',
      registration_number: doctor.registration_number || '',
      qualification: doctor.qualification || '',
      consultation_fee: doctor.consultation_fee === null || doctor.consultation_fee === undefined
        ? '' : String(doctor.consultation_fee),
      specialty_ids: (doctor.specialty_ids || []).slice(),
      branches: assigned,
      photoSrc: '',
    });
    if (doctor.has_photo) {
      try {
        const p = await apiFetch('/api/v1/doctors/' + doctor.id + '/photo');
        setForm((cur) => (cur && cur.id === doctor.id
          ? { ...cur, photoSrc: 'data:' + (p.mime_type || 'image/jpeg') + ';base64,' + p.photo_base64 }
          : cur));
      } catch (e) { /* a photo that fails to load must not block the form */ }
    }
  };

  const field = (key) => (e) => {
    const value = e.target.value;
    setForm((cur) => (cur ? { ...cur, [key]: value } : cur));
  };

  const toggleSpecialty = (id) => setForm((cur) => {
    if (!cur) return cur;
    const has = cur.specialty_ids.includes(id);
    return {
      ...cur,
      specialty_ids: has
        ? cur.specialty_ids.filter((s) => s !== id)
        : cur.specialty_ids.concat(id),
    };
  });

  /** Add or remove a branch; the first branch added becomes the primary one. */
  const toggleBranch = (branchId) => setForm((cur) => {
    if (!cur) return cur;
    if (cur.branches.some((b) => b.branch_id === branchId)) {
      const left = cur.branches.filter((b) => b.branch_id !== branchId);
      // Same outcome as the server's promote_primary(): never leave the doctor
      // without a primary branch while one assignment remains.
      if (left.length && !left.some((b) => b.is_primary)) {
        left[0] = { ...left[0], is_primary: true };
      }
      return { ...cur, branches: left };
    }
    const branch = branches.find((b) => b.id === branchId);
    return {
      ...cur,
      branches: cur.branches.concat([{
        assignment_id: '',
        branch_id: branchId,
        branch_name: branch ? branch.name : '',
        room_id: '',
        is_primary: cur.branches.length === 0,
      }]),
    };
  });

  const setPrimary = (branchId) => setForm((cur) => (cur ? {
    ...cur,
    branches: cur.branches.map((b) => ({ ...b, is_primary: b.branch_id === branchId })),
  } : cur));

  const setRoom = (branchId, roomId) => setForm((cur) => (cur ? {
    ...cur,
    branches: cur.branches.map((b) => (b.branch_id === branchId ? { ...b, room_id: roomId } : b)),
  } : cur));

  // ---------------------------------------------------------------------
  // Persistence
  // ---------------------------------------------------------------------

  const save = async () => {
    if (!form) return;
    setErr('');
    setNotice('');
    if (!form.name.trim()) {
      setErr(t('nameRequired'));
      return;
    }
    const mobile = validateMobile(form.mobile, {
      empty: t('mobileRequired'), invalid: t('invalidMobile'),
    });
    if (!mobile.ok) {
      setErr(mobile.error);
      return;
    }
    const primary = form.branches.find((b) => b.is_primary);
    const payload = {
      name: form.name.trim(),
      mobile: mobile.value,
      registration_number: form.registration_number.trim(),
      qualification: form.qualification.trim(),
      consultation_fee: form.consultation_fee === '' ? null : Number(form.consultation_fee),
      specialty_ids: form.specialty_ids,
      branch_ids: form.branches.map((b) => b.branch_id),
      primary_branch_id: primary ? primary.branch_id : null,
    };
    setSaving(true);
    const editing = !!form.id;
    try {
      const saved = editing
        ? await apiFetch('/api/v1/doctors/' + form.id, {
          method: 'PATCH', body: JSON.stringify(payload),
        })
        : await apiFetch('/api/v1/doctors', {
          method: 'POST', body: JSON.stringify(payload),
        });
      // A chamber belongs to the *assignment*, not the doctor, so it is
      // reconciled per branch once the record exists.  An empty string clears
      // the chamber — the API's way of telling "clear" from "unchanged".
      await Promise.all((saved.branches || []).map(async (a) => {
        const want = form.branches.find((b) => b.branch_id === a.branch_id);
        if (!want) return;
        const desired = want.room_id || '';
        if ((a.room_id || '') === desired) return;
        await apiFetch('/api/v1/doctors/' + saved.id + '/branches/' + a.id, {
          method: 'PATCH',
          body: JSON.stringify({ room_id: desired }),
        });
      }));
      setForm(null);
      setNotice(editing ? t('savedOk') : t('createdOk'));
      await loadDoctors(filters);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const openVerify = (doctor) => {
    setErr('');
    setNotice('');
    // `bmdcTransitions` returns the current state plus every permitted target;
    // the current state is dropped because re-recording it changes nothing.
    const options = bmdcTransitions(doctor.bmdc_verification_status)
      .filter((s) => s !== doctor.bmdc_verification_status);
    setVerify({
      doctor,
      options,
      status: options[0] || 'pending_verification',
      note: '',
    });
  };

  const submitVerify = async () => {
    if (!verify) return;
    setErr('');
    setSaving(true);
    try {
      await apiFetch('/api/v1/doctors/' + verify.doctor.id + '/verification', {
        method: 'POST',
        body: JSON.stringify({ status: verify.status, note: verify.note }),
      });
      setVerify(null);
      setNotice(t('savedOk'));
      await loadDoctors(filters);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const uploadPhoto = (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file || !form) return;
    setErr('');
    const reader = new FileReader();
    reader.onload = async () => {
      const dataUrl = String(reader.result || '');
      const comma = dataUrl.indexOf(',');
      if (comma < 0) return;
      const meta = dataUrl.slice(5, comma);            // image/png;base64
      const base64 = dataUrl.slice(comma + 1);
      try {
        await apiFetch('/api/v1/doctors/' + form.id + '/photo', {
          method: 'POST',
          body: JSON.stringify({
            photo_base64: base64,
            mime_type: meta.split(';')[0] || 'image/jpeg',
          }),
        });
        setForm((cur) => (cur ? { ...cur, photoSrc: dataUrl } : cur));
        setNotice(t('savedOk'));
      } catch (e) {
        setErr(String(e.message || e));
      }
    };
    reader.readAsDataURL(file);
  };

  const removePhoto = async () => {
    if (!form || !form.id) return;
    setErr('');
    try {
      await apiFetch('/api/v1/doctors/' + form.id + '/photo', { method: 'DELETE' });
      setForm((cur) => (cur ? { ...cur, photoSrc: '' } : cur));
      setNotice(t('savedOk'));
      await loadDoctors(filters);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const applyFilters = (next) => {
    setFilters(next);
    loadDoctors(next);
  };

  const locale = getLocale();

  return (
    <RequireLogin>
      <AppShell active="/doctors" breadcrumbs={[{ label: t('doctors') }]}>
        <div>
          <div className="flex justify-between mb-2">
            <h1 className="page-title">{t('doctors')}</h1>
            {mayManage && (
              <button className="btn" style={{ width: 'auto' }} onClick={openCreate}>
                {t('add')}
              </button>
            )}
          </div>

          <div className="toolbar">
            <input
              placeholder={t('searchDoctors')}
              aria-label={t('searchDoctors')}
              value={filters.q}
              style={{ maxWidth: 320 }}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
              onKeyDown={(e) => { if (e.key === 'Enter') applyFilters(filters); }}
            />
            <select aria-label={t('branch')} value={filters.branch_id}
              onChange={(e) => applyFilters({ ...filters, branch_id: e.target.value })}
              style={{ width: 'auto' }}>
              <option value="">{t('allBranches')}</option>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            <select aria-label={t('speciality')} value={filters.specialty_id}
              onChange={(e) => applyFilters({ ...filters, specialty_id: e.target.value })}
              style={{ width: 'auto' }}>
              <option value="">{t('allSpecialities')}</option>
              {specialities.map((s) => (
                <option key={s.id} value={s.id}>{specialityName(s, locale)}</option>
              ))}
            </select>
            <select aria-label={t('status')} value={filters.status}
              onChange={(e) => applyFilters({ ...filters, status: e.target.value })}
              style={{ width: 'auto' }}>
              <option value="">{t('allStatus')}</option>
              <option value="active">{t('active')}</option>
              <option value="inactive">{t('inactive')}</option>
            </select>
            <button className="btn-outline" style={{ width: 'auto' }}
              onClick={() => applyFilters(filters)}>{t('search')}</button>
          </div>

          {err && <div className="error" role="alert">{err}</div>}
          {notice && <div className="success" role="status">{notice}</div>}
          {!mayManage && <p className="muted">{t('manageOnly')}</p>}

          {loading ? (
            <div className="loading">{t('loading')}</div>
          ) : items.length === 0 ? (
            <div className="empty">{t('empty')}</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>{t('doctor')}</th>
                  <th>{t('mobile')}</th>
                  <th>{t('specialities')}</th>
                  <th>{t('chamberWindow')}</th>
                  <th>{t('fee')}</th>
                  <th>{t('bmdc')}</th>
                  <th>{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((d) => {
                  // Only an active assignment is a current chamber; retired ones
                  // stay in the payload for history but are not shown as current.
                  const assigned = activeOnly(d.branches || []);
                  return (
                    <tr key={d.id}>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span className="avatar" aria-hidden="true">{initials(d.name)}</span>
                          <div>
                            <strong>{d.name}</strong>
                            {d.status !== 'active' && (
                              <span className="badge badge-inactive" style={{ marginLeft: '0.4rem' }}>
                                {t('inactive')}
                              </span>
                            )}
                            <div className="muted">
                              {[d.qualification, d.registration_number].filter(Boolean).join(' · ')}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>{formatMobile(d.mobile)}</td>
                      <td>
                        {(d.specialties || []).length
                          ? (d.specialties || []).map((s) => specialityName(s, locale)).join(', ')
                          : <span className="muted">{t('unassigned')}</span>}
                      </td>
                      <td>
                        {assigned.length === 0 ? (
                          <span className="muted">{t('noChamber')}</span>
                        ) : assigned.map((a) => (
                          <div key={a.id}>
                            {a.is_primary && (
                              <span className="badge badge-active" style={{ marginRight: '0.35rem' }}>
                                {t('primary')}
                              </span>
                            )}
                            {a.branch_name}
                            {' — '}
                            {assignmentChamber(a, roomsByBranch[a.branch_id]) || t('unassigned')}
                          </div>
                        ))}
                      </td>
                      <td>
                        {d.consultation_fee === null || d.consultation_fee === undefined
                          ? <span className="muted">—</span>
                          : Number(d.consultation_fee)}
                      </td>
                      <td>
                        <span className={bmdcBadgeClass(d.bmdc_verification_status)}>
                          {bmdcLabel(d.bmdc_verification_status, locale)}
                        </span>
                      </td>
                      <td>
                        {mayManage ? (
                          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                            <button className="btn-outline"
                              style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
                              onClick={() => openEdit(d)}>{t('edit')}</button>
                            <button className="btn-outline"
                              style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
                              onClick={() => openVerify(d)}>{t('verify')}</button>
                          </div>
                        ) : <span className="muted">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {form && (
          <Modal
            title={form.id ? t('edit') : t('add')}
            onClose={() => setForm(null)}
            footer={(
              <>
                <button className="btn-outline" onClick={() => setForm(null)}>{t('cancel')}</button>
                <button className="btn" disabled={saving} onClick={save}>{t('save')}</button>
              </>
            )}
          >
            <div className="grid-2">
              <div className="form-group">
                <label>{t('photo')}</label>
                <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                  {form.photoSrc ? (
                    <img className="avatar" src={form.photoSrc} alt={form.name} />
                  ) : (
                    <span className="avatar" aria-hidden="true">{initials(form.name)}</span>
                  )}
                  <div className="stack">
                    <input type="file" accept="image/jpeg,image/png,image/webp" onChange={uploadPhoto} />
                    <span className="muted">{t('photoHint')}</span>
                    {form.photoSrc && (
                      <button className="btn-outline" type="button" onClick={removePhoto}
                        style={{ width: 'auto', padding: '0.2rem 0.6rem' }}>
                        {t('removePhoto')}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>{t('name')} *</label>
              <input value={form.name} onChange={field('name')} autoFocus required />
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label>{t('mobile')} *</label>
                <input value={form.mobile} onChange={field('mobile')}
                  placeholder="01711111111" inputMode="tel" required />
              </div>
              <div className="form-group">
                <label>{t('registrationNumber')}</label>
                <input value={form.registration_number}
                  onChange={field('registration_number')} placeholder="BMDC / A-12345" />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label>{t('qualification')}</label>
                <input value={form.qualification} onChange={field('qualification')}
                  placeholder="MBBS, FCPS" />
              </div>
              <div className="form-group">
                <label>{t('consultationFee')}</label>
                <input type="number" min="0" step="1" value={form.consultation_fee}
                  onChange={field('consultation_fee')} placeholder="500" />
              </div>
            </div>

            <div className="form-group">
              <label>{t('specialities')}</label>
              {specialities.length === 0 ? (
                <span className="muted">{t('empty')}</span>
              ) : (
                <div className="grid-2">
                  {specialities.map((s) => (
                    <label key={s.id} className="checkbox-row">
                      <input type="checkbox"
                        checked={form.specialty_ids.includes(s.id)}
                        onChange={() => toggleSpecialty(s.id)} />
                      {specialityName(s, locale)}
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="form-group">
              <label>{t('assignBranches')}</label>
              {branches.length === 0 && <span className="muted">{t('empty')}</span>}
              {branches.map((b) => {
                const row = form.branches.find((x) => x.branch_id === b.id);
                const options = roomOptions(roomsByBranch[b.id] || []);
                return (
                  <div key={b.id} className="tree-group">
                    <label className="checkbox-row">
                      <input type="checkbox" checked={!!row} onChange={() => toggleBranch(b.id)} />
                      <strong>{b.name}</strong>
                    </label>
                    {row && (
                      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        <label className="checkbox-row">
                          <input type="radio" name="primary-branch"
                            checked={!!row.is_primary} onChange={() => setPrimary(b.id)} />
                          {t('primaryBranch')}
                        </label>
                        <select aria-label={t('chamber')} value={row.room_id}
                          onChange={(e) => setRoom(b.id, e.target.value)}
                          style={{ width: 'auto', maxWidth: 300 }}>
                          <option value="">{t('noChamber')}</option>
                          {options.map((o) => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                        {options.length === 0 && <span className="muted">{t('noRooms')}</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </Modal>
        )}

        {verify && (
          <Modal
            title={t('verifyTitle')}
            onClose={() => setVerify(null)}
            footer={(
              <>
                <button className="btn-outline" onClick={() => setVerify(null)}>{t('cancel')}</button>
                <button className="btn" disabled={saving || verify.options.length === 0}
                  onClick={submitVerify}>{t('save')}</button>
              </>
            )}
          >
            <p>
              <strong>{verify.doctor.name}</strong>
              {' — '}
              <span className={bmdcBadgeClass(verify.doctor.bmdc_verification_status)}>
                {bmdcLabel(verify.doctor.bmdc_verification_status, locale)}
              </span>
            </p>
            {!verify.doctor.registration_number && (
              <p className="muted">{t('registrationNumber')}</p>
            )}
            {verify.options.length === 0 ? (
              <p className="muted">{t('bmdcStatus')}</p>
            ) : (
              <>
                <div className="form-group">
                  <label>{t('bmdcStatus')}</label>
                  <select value={verify.status}
                    onChange={(e) => setVerify({ ...verify, status: e.target.value })}>
                    {verify.options.map((s) => (
                      <option key={s} value={s}>{bmdcLabel(s, locale)}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>{t('bmdcNote')}</label>
                  <textarea rows={3} value={verify.note}
                    onChange={(e) => setVerify({ ...verify, note: e.target.value })} />
                </div>
              </>
            )}
          </Modal>
        )}
      </AppShell>
    </RequireLogin>
  );
}


