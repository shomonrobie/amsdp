export async function getServerSideProps() { return { props: {} }; }
/* Facilities — the branch tree: floors → departments → rooms, plus the
 * organization's speciality catalogue. AMSDP-FACILITY-DOCTOR-01.
 *
 * One branch at a time, because the facility hierarchy *is* branch
 * configuration.  The tree comes from `GET /api/v1/branches/{id}/facility`
 * (floors, departments and rooms in one round trip) and is placed on the page
 * with `groupRoomsByFloor`, which keeps a room with no floor visible under an
 * "unassigned" heading instead of silently dropping it.
 *
 * Nothing here deletes: retiring sets `status="inactive"`, so a session or an
 * appointment that already names the room keeps resolving it.  Retired records
 * are hidden by default and can be revealed and restored, which is the only way
 * back from a mistaken retirement without touching the database.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { getUser, apiFetch, can, getActiveBranch } from '../lib/auth';
import { t, getLocale } from '../lib/i18n';
import {
  ROOM_TYPES, groupRoomsByFloor, roomChamberText, roomUsage, facilityCounts,
  activeOnly, specialityName,
} from '../lib/facility';

const EMPTY_EDITOR = {
  kind: '', id: '', name: '', code: '', level: '', description: '',
  floor_id: '', department_id: '', room_type: 'consultation', capacity: '',
  name_en: '', name_bn: '', sort_order: '',
};

/** Copy a facility row into the editor shape. */
function toEditor(kind, row) {
  if (!row) return { ...EMPTY_EDITOR, kind };
  if (kind === 'specialty') {
    return {
      ...EMPTY_EDITOR, kind, id: row.id, code: row.code || '',
      name_en: row.name_en || '', name_bn: row.name_bn || '',
      sort_order: row.sort_order === null || row.sort_order === undefined ? '' : String(row.sort_order),
    };
  }
  return {
    ...EMPTY_EDITOR,
    kind,
    id: row.id,
    name: row.name || '',
    code: row.code || '',
    level: row.level === null || row.level === undefined ? '' : String(row.level),
    description: row.description || '',
    floor_id: row.floor_id || '',
    department_id: row.department_id || '',
    room_type: row.room_type || 'consultation',
    capacity: row.capacity === null || row.capacity === undefined ? '' : String(row.capacity),
  };
}

export default function Facilities() {
  const user = getUser();
  const orgId = user.organization_id;
  const locale = getLocale();
  const mayManage = can('facility.manage');

  const [branches, setBranches] = React.useState([]);
  const [branchId, setBranchId] = React.useState('');
  const [tree, setTree] = React.useState({ floors: [], departments: [], rooms: [] });
  const [sessions, setSessions] = React.useState([]);
  const [specialities, setSpecialities] = React.useState([]);
  const [showRetired, setShowRetired] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [editor, setEditor] = React.useState(null);
  const [retiring, setRetiring] = React.useState(null);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  const loadSpecialities = React.useCallback(() => {
    if (!orgId) return;
    // Specialities are organization-wide, so retired ones are always fetched —
    // hiding them would make a retired entry unrecoverable from this screen.
    apiFetch('/api/v1/orgs/' + orgId + '/specialties?include_inactive=true')
      .then((d) => setSpecialities(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setSpecialities([]));
  }, [orgId]);

  const loadBranch = React.useCallback(async (id, includeRetired) => {
    if (!id) return;
    setLoading(true);
    setErr('');
    try {
      const suffix = includeRetired ? '?include_inactive=true' : '';
      const [facility, rows] = await Promise.all([
        apiFetch('/api/v1/branches/' + id + '/facility' + suffix),
        apiFetch('/api/v1/branches/' + id + '/sessions'),
      ]);
      setTree({
        floors: facility.floors || [],
        departments: facility.departments || [],
        rooms: facility.rooms || [],
      });
      setSessions(Array.isArray(rows) ? rows : (rows.items || []));
    } catch (e) {
      setErr(String(e.message || e));
      setTree({ floors: [], departments: [], rooms: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { loadBranch(branchId, showRetired); }, [branchId, showRetired, loadBranch]);
  React.useEffect(() => { loadSpecialities(); }, [loadSpecialities]);

  if (!user.id) return null;

  const occupancy = roomUsage(sessions);
  const counts = facilityCounts(tree);

  const openEditor = (kind, row) => {
    setErr('');
    setNotice('');
    setEditor(toEditor(kind, row));
  };

  const field = (key) => (e) => {
    const value = e.target.value;
    setEditor((cur) => (cur ? { ...cur, [key]: value } : cur));
  };

  // One save routine for four resources: the endpoint and the payload differ,
  // the operator flow does not.
  const endpoint = (kind, id) => {
    if (kind === 'floor') {
      return id ? '/api/v1/floors/' + id : '/api/v1/branches/' + branchId + '/floors';
    }
    if (kind === 'department') {
      return id ? '/api/v1/departments/' + id : '/api/v1/branches/' + branchId + '/departments';
    }
    if (kind === 'room') {
      return id ? '/api/v1/rooms/' + id : '/api/v1/branches/' + branchId + '/rooms';
    }
    return id ? '/api/v1/specialties/' + id : '/api/v1/orgs/' + orgId + '/specialties';
  };

  const save = async () => {
    if (!editor) return;
    setErr('');
    setNotice('');
    setSaving(true);
    const { kind, id } = editor;
    let body;
    if (kind === 'specialty') {
      if (!editor.name_en.trim()) { setSaving(false); setErr(t('nameRequired')); return; }
      body = {
        name_en: editor.name_en.trim(),
        name_bn: editor.name_bn.trim(),
        code: editor.code.trim() || null,
        sort_order: editor.sort_order === '' ? 0 : Number(editor.sort_order),
      };
    } else if (kind === 'room') {
      if (!editor.name.trim()) { setSaving(false); setErr(t('nameRequired')); return; }
      body = {
        name: editor.name.trim(),
        code: editor.code.trim() || null,
        floor_id: editor.floor_id || null,
        department_id: editor.department_id || null,
        room_type: editor.room_type,
        capacity: editor.capacity === '' ? null : Number(editor.capacity),
        description: editor.description.trim(),
      };
    } else {
      if (!editor.name.trim()) { setSaving(false); setErr(t('nameRequired')); return; }
      body = {
        name: editor.name.trim(),
        code: editor.code.trim() || null,
        description: editor.description.trim(),
      };
      // `level` belongs to floors only; a department has no building level.
      if (kind === 'floor') body.level = editor.level === '' ? null : Number(editor.level);
    }
    try {
      await apiFetch(endpoint(kind, id), {
        method: id ? 'PATCH' : 'POST',
        body: JSON.stringify(body),
      });
      setEditor(null);
      setNotice(id ? t('savedOk') : t('createdOk'));
      if (kind === 'specialty') loadSpecialities();
      else await loadBranch(branchId, showRetired);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  const retire = async () => {
    if (!retiring) return;
    setErr('');
    setNotice('');
    try {
      await apiFetch(endpoint(retiring.kind, retiring.row.id), { method: 'DELETE' });
      setRetiring(null);
      setNotice(t('savedOk'));
      if (retiring.kind === 'specialty') loadSpecialities();
      else await loadBranch(branchId, showRetired);
    } catch (e) {
      setRetiring(null);
      setErr(String(e.message || e));
    }
  };

  const restore = async (kind, row) => {
    setErr('');
    setNotice('');
    try {
      // Re-activation is a status change, never a re-creation: the row keeps its
      // id, so every session and appointment that already points at it heals.
      await apiFetch(endpoint(kind, row.id), {
        method: 'PATCH',
        body: JSON.stringify({ status: 'active' }),
      });
      setNotice(t('savedOk'));
      if (kind === 'specialty') loadSpecialities();
      else await loadBranch(branchId, showRetired);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const rowActions = (kind, row) => {
    if (!mayManage) return <span className="muted">—</span>;
    const retired = (row.status || 'active') !== 'active';
    return (
      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
        <button className="btn-outline" style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
          onClick={() => openEditor(kind, row)}>{t('edit')}</button>
        {retired ? (
          <button className="btn-outline" style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
            onClick={() => restore(kind, row)}>{t('active')}</button>
        ) : (
          <button className="btn-outline" style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
            onClick={() => setRetiring({ kind, row })}>{t('retire')}</button>
        )}
      </div>
    );
  };

  const statusBadge = (row) => (
    <span className={'badge ' + ((row.status || 'active') === 'active' ? 'badge-active' : 'badge-inactive')}>
      {t((row.status || 'active') === 'active' ? 'active' : 'retired')}
    </span>
  );

  const roomsOnFloor = (floorId) => tree.rooms.filter((r) => (r.floor_id || '') === floorId).length;
  const roomsInDepartment = (departmentId) => tree.rooms.filter(
    (r) => (r.department_id || '') === departmentId).length;

  return (
    <RequireLogin>
      <AppShell active="/facilities" breadcrumbs={[{ label: t('facilities') }]}>
        <div>
          <div className="flex justify-between mb-2">
            <h1 className="page-title">{t('facilities')}</h1>
          </div>

          <div className="toolbar">
            <select aria-label={t('branch')} value={branchId}
              onChange={(e) => setBranchId(e.target.value)} style={{ width: 'auto' }}>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
            <label className="checkbox-row">
              <input type="checkbox" checked={showRetired}
                onChange={(e) => setShowRetired(e.target.checked)} />
              {t('retired')}
            </label>
            <span className="summary">
              <span>{counts.floors} {t('floors')}</span>
              <span>{counts.departments} {t('departments')}</span>
              <span>{counts.rooms} {t('rooms')}</span>
            </span>
          </div>

          {err && <div className="error" role="alert">{err}</div>}
          {notice && <div className="success" role="status">{notice}</div>}
          {!mayManage && <p className="muted">{t('manageOnly')}</p>}

          {loading ? (
            <div className="loading">{t('loading')}</div>
          ) : (
            <>
              <div className="card mt-2">
                <div className="flex justify-between mb-2">
                  <h3 className="page-title">{t('floors')}</h3>
                  {mayManage && (
                    <button className="btn" style={{ width: 'auto' }}
                      onClick={() => openEditor('floor')}>{t('addFloor')}</button>
                  )}
                </div>
                {tree.floors.length === 0 ? (
                  <div className="empty">{t('facilityEmpty')}</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>{t('name')}</th>
                        <th>{t('code')}</th>
                        <th>{t('level')}</th>
                        <th>{t('rooms')}</th>
                        <th>{t('status')}</th>
                        <th>{t('actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tree.floors.map((f) => (
                        <tr key={f.id}>
                          <td>{f.name}</td>
                          <td><code>{f.code}</code></td>
                          <td>{f.level === null || f.level === undefined
                            ? <span className="muted">—</span> : f.level}</td>
                          <td>{roomsOnFloor(f.id)}</td>
                          <td>{statusBadge(f)}</td>
                          <td>{rowActions('floor', f)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card mt-2">
                <div className="flex justify-between mb-2">
                  <h3 className="page-title">{t('departments')}</h3>
                  {mayManage && (
                    <button className="btn" style={{ width: 'auto' }}
                      onClick={() => openEditor('department')}>{t('addDepartment')}</button>
                  )}
                </div>
                {tree.departments.length === 0 ? (
                  <div className="empty">{t('facilityEmpty')}</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>{t('name')}</th>
                        <th>{t('code')}</th>
                        <th>{t('rooms')}</th>
                        <th>{t('status')}</th>
                        <th>{t('actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tree.departments.map((d) => (
                        <tr key={d.id}>
                          <td>{d.name}</td>
                          <td><code>{d.code}</code></td>
                          <td>{roomsInDepartment(d.id)}</td>
                          <td>{statusBadge(d)}</td>
                          <td>{rowActions('department', d)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card mt-2">
                <div className="flex justify-between mb-2">
                  <h3 className="page-title">{t('rooms')}</h3>
                  {mayManage && (
                    <button className="btn" style={{ width: 'auto' }}
                      onClick={() => openEditor('room')}>{t('addRoom')}</button>
                  )}
                </div>
                {tree.rooms.length === 0 ? (
                  <div className="empty">{t('noRooms')}</div>
                ) : (
                  groupRoomsByFloor(tree.rooms, tree.floors).map((group) => (
                    <div key={group.floor ? group.floor.id : 'unassigned'} className="tree-group">
                      <div className="tree-title">
                        {group.floor
                          ? `${group.floor.name}${group.floor.level === null || group.floor.level === undefined ? '' : ' · ' + group.floor.level}`
                          : t('unassigned')}
                        {' — '}
                        {group.rooms.length} {t('rooms')}
                      </div>
                      <table>
                        <thead>
                          <tr>
                            <th>{t('room')}</th>
                            <th>{t('department')}</th>
                            <th>{t('roomType')}</th>
                            <th>{t('capacity')}</th>
                            <th>{t('usedBySessions')}</th>
                            <th>{t('status')}</th>
                            <th>{t('actions')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {group.rooms.map((r) => (
                            <tr key={r.id}>
                              <td>
                                <strong>{r.name}</strong>
                                <div className="muted"><code>{r.code}</code></div>
                              </td>
                              <td>{r.department_name || <span className="muted">{t('unassigned')}</span>}</td>
                              <td>{r.room_type}</td>
                              <td>{r.capacity === null || r.capacity === undefined
                                ? <span className="muted">—</span> : r.capacity}</td>
                              <td>{occupancy[r.id] || 0}</td>
                              <td>{statusBadge(r)}</td>
                              <td>{rowActions('room', r)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))
                )}
              </div>

              <div className="card mt-2">
                <div className="flex justify-between mb-2">
                  <h3 className="page-title">{t('specialities')}</h3>
                  {mayManage && (
                    <button className="btn" style={{ width: 'auto' }}
                      onClick={() => openEditor('specialty')}>{t('add')}</button>
                  )}
                </div>
                {specialities.length === 0 ? (
                  <div className="empty">{t('empty')}</div>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>{t('name')}</th>
                        <th>{t('code')}</th>
                        <th>{t('status')}</th>
                        <th>{t('actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {specialities.map((s) => (
                        <tr key={s.id}>
                          <td>
                            {specialityName(s, locale)}
                            <div className="muted">{specialityName(s, locale === 'en' ? 'bn' : 'en')}</div>
                          </td>
                          <td><code>{s.code}</code></td>
                          <td>{statusBadge(s)}</td>
                          <td>{rowActions('specialty', s)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>

        {editor && (
          <Modal
            title={editor.id ? t('edit') : t('add')}
            onClose={() => setEditor(null)}
            footer={(
              <>
                <button className="btn-outline" onClick={() => setEditor(null)}>{t('cancel')}</button>
                <button className="btn" disabled={saving} onClick={save}>{t('save')}</button>
              </>
            )}
          >
            {editor.kind === 'specialty' ? (
              <>
                <div className="form-group">
                  <label>{t('name')} (EN) *</label>
                  <input value={editor.name_en} onChange={field('name_en')} autoFocus required />
                </div>
                <div className="form-group">
                  <label>{t('name')} (বাংলা)</label>
                  <input value={editor.name_bn} onChange={field('name_bn')} />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label>{t('code')}</label>
                    <input value={editor.code} onChange={field('code')}
                      placeholder="CARDIOLOGY" />
                  </div>
                  <div className="form-group">
                    <label>{t('order')}</label>
                    <input type="number" min="0" step="1" value={editor.sort_order}
                      onChange={field('sort_order')} />
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label>{t('name')} *</label>
                  <input value={editor.name} onChange={field('name')} autoFocus required />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label>{t('code')}</label>
                    <input value={editor.code} onChange={field('code')} placeholder="2F" />
                  </div>
                  {editor.kind === 'floor' && (
                    <div className="form-group">
                      <label>{t('level')}</label>
                      <input type="number" step="1" value={editor.level}
                        onChange={field('level')} placeholder="2" />
                    </div>
                  )}
                </div>
                {editor.kind === 'room' && (
                  <>
                    <div className="grid-2">
                      <div className="form-group">
                        <label>{t('floor')}</label>
                        <select value={editor.floor_id} onChange={field('floor_id')}>
                          <option value="">{t('unassigned')}</option>
                          {tree.floors.map((f) => (
                            <option key={f.id} value={f.id}>{f.name}</option>
                          ))}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>{t('department')}</label>
                        <select value={editor.department_id} onChange={field('department_id')}>
                          <option value="">{t('unassigned')}</option>
                          {tree.departments.map((d) => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="grid-2">
                      <div className="form-group">
                        <label>{t('roomType')}</label>
                        <select value={editor.room_type} onChange={field('room_type')}>
                          {ROOM_TYPES.map((rt) => <option key={rt} value={rt}>{rt}</option>)}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>{t('capacity')}</label>
                        <input type="number" min="0" step="1" value={editor.capacity}
                          onChange={field('capacity')} />
                      </div>
                    </div>
                  </>
                )}
                <div className="form-group">
                  <label>{t('description')}</label>
                  <textarea rows={2} value={editor.description}
                    onChange={field('description')} />
                </div>
              </>
            )}
          </Modal>
        )}

        {retiring && (
          <ConfirmDialog
            title={t('retireConfirm')}
            message={t('retireMsg')}
            onClose={() => setRetiring(null)}
            onConfirm={retire}
          />
        )}
      </AppShell>
    </RequireLogin>
  );
}
