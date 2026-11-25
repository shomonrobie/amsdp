/* Staff and permissions — MP-19 / MP-20.
 *
 * One screen for the whole staff lifecycle: who exists, what role they hold,
 * which branch their scope comes from, whether they can sign in, which of the
 * delegable capabilities they have been granted, and which doctors an assistant
 * works for.
 *
 * Three rules shape the wiring:
 *
 *  * The browser is never the boundary.  Every request here is re-authorised by
 *    the server (`staff.read` to list, `staff.manage` to write, organization-
 *    administrator authority to grant, `can_grant_role` to assign a role, and a
 *    non-disclosing 404 for another tenant's row).  This screen decides only
 *    what it *offers*, and it says so when it offers nothing.
 *  * The delegable capability catalogue is read from
 *    `GET /api/v1/staff/capabilities`, never hard-coded: a list kept in the
 *    browser drifts from the server, and then the UI offers a grant the API
 *    refuses or hides one it would accept.
 *  * A caller cannot change their own role here — the server refuses it, and
 *    offering it would only produce a red box.
 *
 * Deactivation is a status change, not a delete: the row, its audit trail and
 * the appointments it booked all survive, and the account is re-activatable.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import {
  RequireLogin, PermissionDenied,
} from '../components/ui/Alert';
import Modal from '../components/ui/Modal';
import { Field, FormRow } from '../components/ui/Field';
import { Input, Select } from '../components/ui/Input';
import { getUser, apiFetch, can } from '../lib/auth';
import { t } from '../lib/i18n';
import {
  ROLE_KEYS, grantableRoles, mayGrantCapabilities, needsBranch, capabilityLabelKey,
  assignedDoctorIds, isActiveStatus, validateNewStaff, staffMatchesFilter,
} from '../lib/staff-policy';

const LOCALES = ['bn', 'en'];
const EMPTY_NEW = {
  username: '', password: '', display_name: '', email: '', mobile: '',
  role: 'receptionist', branch_id: '', locale: 'bn',
};

function roleName(role) {
  return t(ROLE_KEYS[role] || 'roleLabel');
}

function statusName(status) {
  return t(isActiveStatus(status) ? 'active' : 'inactive');
}

function branchLabel(branches, id) {
  const found = (branches || []).find((b) => b.id === id);
  if (found) return found.name;
  return id ? String(id).slice(0, 8) : '';
}

/** Turn an API failure into a sentence the front desk can act on. */
function failure(e) {
  const status = e && e.status;
  const detail = String((e && (e.body || e.message)) || e || '');
  if (status === 403) return t('staffManageDenied');
  if (/username/i.test(detail) && /exist/i.test(detail)) return t('usernameTaken');
  if (/last .*admin|only active/i.test(detail)) return t('lastAdminGuard');
  if (/own role|own account|yourself/i.test(detail)) return t('ownRoleLocked');
  return detail || t('error');
}

export default function Staff() {
  const user = getUser();
  const orgId = user.organization_id || '';
  const mayRead = can('staff.read');
  const mayManage = can('staff.manage');
  const mayGrant = mayManage && mayGrantCapabilities(user.role);
  // Only the roles strictly below the caller's own, and only when a role change
  // would be accepted at all.
  const offerable = mayManage ? grantableRoles(user.role) : [];

  const [rows, setRows] = React.useState([]);
  const [branches, setBranches] = React.useState([]);
  const [doctors, setDoctors] = React.useState([]);
  const [catalogue, setCatalogue] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [q, setQ] = React.useState('');
  const [roleFilter, setRoleFilter] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState('');
  const [draft, setDraft] = React.useState(null);
  const [draftError, setDraftError] = React.useState('');
  const [editing, setEditing] = React.useState(null);
  const [saving, setSaving] = React.useState(false);

  const loadStaff = React.useCallback(async () => {
    if (!mayRead || !orgId) { setLoading(false); return; }
    setLoading(true);
    try {
      const list = await apiFetch(
        '/api/v1/staff/users?organization_id=' + encodeURIComponent(orgId));
      setRows(Array.isArray(list) ? list : (list.items || []));
      setErr('');
    } catch (e) {
      setErr(failure(e));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [mayRead, orgId]);

  React.useEffect(() => { loadStaff(); }, [loadStaff]);

  // The look-ups are separate from the roster on purpose: a caller allowed to
  // read staff but not the organization tree still gets a usable list, just with
  // no branch or doctor options to offer.
  React.useEffect(() => {
    if (!mayRead || !orgId) return;
    apiFetch('/api/v1/orgs/' + encodeURIComponent(orgId) + '/branches')
      .then((d) => setBranches(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setBranches([]));
    apiFetch('/api/v1/doctors')
      .then((d) => setDoctors(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setDoctors([]));
    apiFetch('/api/v1/staff/capabilities')
      .then((d) => setCatalogue((d && d.capabilities) || []))
      .catch(() => setCatalogue([]));
  }, [mayRead, orgId]);

  const openNew = () => {
    setErr(''); setNotice(''); setDraftError('');
    setDraft({ ...EMPTY_NEW, branch_id: branches[0] ? branches[0].id : '' });
  };

  const create = async () => {
    if (!draft) return;
    const check = validateNewStaff(draft, { branchRequired: needsBranch(draft.role) });
    if (!check.ok) {
      setDraftError(check.passwordTooShort ? t('passwordMin') : t('fillRequired'));
      return;
    }
    setSaving(true);
    setDraftError('');
    try {
      await apiFetch('/api/v1/staff/users', {
        method: 'POST',
        body: JSON.stringify({
          // The tenant comes from this session, and the server checks it against
          // the token anyway: `organization_id` in a body is never trusted.
          organization_id: orgId,
          username: draft.username.trim(),
          password: draft.password,
          display_name: draft.display_name.trim(),
          role: draft.role,
          branch_id: draft.branch_id || null,
          email: draft.email.trim() || null,
          mobile: draft.mobile.trim() || null,
          locale: draft.locale,
        }),
      });
      setDraft(null);
      setNotice(t('staffCreated'));
      await loadStaff();
    } catch (e) {
      setDraftError(failure(e));
    } finally {
      setSaving(false);
    }
  };

  const readGrants = async (id) => {
    const grants = await apiFetch('/api/v1/staff/users/' + id + '/capabilities');
    return (grants || []).filter((g) => (g.status || 'active') === 'active');
  };

  const grant = async (capability) => {
    if (!editing) return;
    setSaving(true);
    try {
      await apiFetch('/api/v1/staff/users/' + editing.id + '/capabilities', {
        method: 'POST',
        // A grant made while the staff member is organization-wide is
        // organization-wide; otherwise it is pinned to their own branch.
        body: JSON.stringify({ capability, branch_id: editing.branch_id || null }),
      });
      const grants = await readGrants(editing.id);
      setEditing((cur) => (cur ? { ...cur, grants, error: '' } : cur));
      setNotice(t('capabilityGranted'));
    } catch (e) {
      setEditing((cur) => (cur ? { ...cur, error: failure(e) } : cur));
    } finally {
      setSaving(false);
    }
  };

  const revoke = async (grantRow) => {
    if (!editing || !grantRow) return;
    setSaving(true);
    try {
      // A grant is scoped: revoking one made for a branch must name that branch,
      // otherwise the organization-wide row is left in place.
      const scope = grantRow.branch_id
        ? '?branch_id=' + encodeURIComponent(grantRow.branch_id) : '';
      await apiFetch('/api/v1/staff/users/' + editing.id + '/capabilities/'
        + encodeURIComponent(grantRow.capability) + scope, { method: 'DELETE' });
      const grants = await readGrants(editing.id);
      setEditing((cur) => (cur ? { ...cur, grants, error: '' } : cur));
      setNotice(t('capabilityRevoked'));
    } catch (e) {
      setEditing((cur) => (cur ? { ...cur, error: failure(e) } : cur));
    } finally {
      setSaving(false);
    }
  };

  const openEdit = async (row) => {
    setErr(''); setNotice('');
    setEditing({
      ...row,
      email: row.email || '',
      mobile: row.mobile || '',
      locale: row.locale || 'bn',
      branch_id: row.branch_id || '',
      status: row.status || 'active',
      grants: [],
      doctors: assignedDoctorIds(row),
      error: '',
    });
    // Grants are read per staff member; a failure here must not hide the rest of
    // the dialog, so it is reported inside it.
    try {
      const grants = await readGrants(row.id);
      setEditing((cur) => (cur && cur.id === row.id ? { ...cur, grants } : cur));
    } catch (e) {
      setEditing((cur) => (cur && cur.id === row.id ? { ...cur, error: failure(e) } : cur));
    }
  };

  const setEditField = (key, value) => {
    setEditing((cur) => (cur ? { ...cur, [key]: value, error: '' } : cur));
  };

  const saveEdit = async () => {
    if (!editing) return;
    // Diff against the row the server last sent, so an unchanged field is not
    // rewritten — and does not clutter the audit trail with a no-op change.
    const current = rows.find((r) => r.id === editing.id) || {};
    const patch = {};
    if ((editing.display_name || '') !== (current.display_name || '')) {
      patch.display_name = editing.display_name;
    }
    if ((editing.email || '') !== (current.email || '')) patch.email = editing.email;
    if ((editing.mobile || '') !== (current.mobile || '')) patch.mobile = editing.mobile;
    if ((editing.locale || 'bn') !== (current.locale || 'bn')) patch.locale = editing.locale;
    if (editing.role !== current.role) patch.role = editing.role;
    // `''` is "clear the scope" (organization-wide); the API distinguishes it
    // from an absent field, which means *unchanged*.
    if ((editing.branch_id || '') !== (current.branch_id || '')) {
      patch.branch_id = editing.branch_id || '';
    }
    if ((editing.doctors || []).join() !== assignedDoctorIds(current).join()) {
      patch.doctor_ids = editing.doctors || [];
    }
    if (!Object.keys(patch).length) { setEditing(null); return; }

    setSaving(true);
    try {
      await apiFetch('/api/v1/staff/users/' + editing.id, {
        method: 'PATCH', body: JSON.stringify(patch),
      });
      setEditing(null);
      setNotice(t('staffUpdated'));
      await loadStaff();
    } catch (e) {
      setEditing((cur) => (cur ? { ...cur, error: failure(e) } : cur));
    } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async () => {
    if (!editing) return;
    const next = isActiveStatus(editing.status) ? 'inactive' : 'active';
    setSaving(true);
    try {
      await apiFetch('/api/v1/staff/users/' + editing.id, {
        method: 'PATCH', body: JSON.stringify({ status: next }),
      });
      setEditing(null);
      setNotice(t('staffUpdated'));
      await loadStaff();
    } catch (e) {
      setEditing((cur) => (cur ? { ...cur, error: failure(e) } : cur));
    } finally {
      setSaving(false);
    }
  };

  if (!user.id) return null;

  const visible = rows
    .filter((r) => staffMatchesFilter(r, { q, role: roleFilter, status: statusFilter }))
    .slice()
    .sort((a, b) => String(a.display_name || a.username)
      .localeCompare(String(b.display_name || b.username)));

  const doctorNames = (ids) => ids.map((id) => {
    const found = (doctors || []).find((d) => d.id === id);
    return found ? found.name : String(id).slice(0, 8);
  }).join(', ');

  if (!mayRead) {
    return (
      <RequireLogin>
        <AppShell active="/staff" breadcrumbs={[{ label: t('staffTitle') }]}>
          <div>
            <h1 className="page-title">{t('staffTitle')}</h1>
            <PermissionDenied msg={t('permissionDenied')} />
          </div>
        </AppShell>
      </RequireLogin>
    );
  }

  return (
    <RequireLogin>
      <AppShell active="/staff" breadcrumbs={[{ label: t('staffTitle') }]}>
        <div>
          <div className="flex justify-between mb-2">
            <h1 className="page-title">{t('staffTitle')}</h1>
            {mayManage && (
              <button className="btn" style={{ width: 'auto' }}
                data-testid="staff-new" onClick={openNew}>
                {t('newStaff')}
              </button>
            )}
          </div>

          <div className="toolbar">
            <input aria-label={t('search')} placeholder={t('search')} data-testid="staff-search"
              value={q} onChange={(e) => setQ(e.target.value)} style={{ width: 'auto' }} />
            <select aria-label={t('roleLabel')} data-testid="staff-role-filter"
              value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}
              style={{ width: 'auto' }}>
              <option value="">{t('allRoles')}</option>
              {Object.keys(ROLE_KEYS).map((role) => (
                <option key={role} value={role}>{roleName(role)}</option>
              ))}
            </select>
            <select aria-label={t('status')} data-testid="staff-status-filter"
              value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
              style={{ width: 'auto' }}>
              <option value="">{t('allStatuses')}</option>
              <option value="active">{t('active')}</option>
              <option value="inactive">{t('inactive')}</option>
            </select>
          </div>

          {err && <div className="error" role="alert" data-testid="staff-error">{err}</div>}
          {notice && <div className="success" role="status" data-testid="staff-notice">{notice}</div>}
          {!mayManage && <p className="muted">{t('staffManageDenied')}</p>}

          {loading ? (
            <div className="loading">{t('loading')}</div>
          ) : visible.length === 0 ? (
            <div className="empty">{rows.length ? t('noResults') : t('empty')}</div>
          ) : (
            <table data-testid="staff-table">
              <thead>
                <tr>
                  <th>{t('username')}</th>
                  <th>{t('fullName')}</th>
                  <th>{t('roleLabel')}</th>
                  <th>{t('branchScope')}</th>
                  <th>{t('assignedDoctors')}</th>
                  <th>{t('status')}</th>
                  <th>{t('actions')}</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => {
                  const assigned = assignedDoctorIds(row);
                  return (
                    <tr key={row.id} data-testid={'staff-row-' + row.username}>
                      <td>{row.username}</td>
                      <td>{row.display_name}</td>
                      <td>{roleName(row.role)}</td>
                      <td>{row.branch_id
                        ? branchLabel(branches, row.branch_id)
                        : <span className="muted">{t('orgWide')}</span>}</td>
                      <td>{assigned.length
                        ? doctorNames(assigned)
                        : <span className="muted">{t('noDoctorsAssigned')}</span>}</td>
                      <td>
                        <span className={'badge ' + (isActiveStatus(row.status)
                          ? 'badge-active' : 'badge-inactive')}>
                          {statusName(row.status)}
                        </span>
                      </td>
                      <td>
                        {mayManage ? (
                          <button className="btn-outline"
                            style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
                            data-testid={'staff-manage-' + row.username}
                            onClick={() => openEdit(row)}>
                            {t('manage')}
                          </button>
                        ) : <span className="muted">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {draft && (
          <NewStaffDialog
            draft={draft} branches={branches} offerable={offerable}
            error={draftError} saving={saving}
            onChange={setDraft} onClose={() => setDraft(null)} onCreate={create}
          />
        )}
        {editing && (
          <EditStaffDialog
            state={editing} branches={branches} doctors={doctors} catalogue={catalogue}
            mayGrant={mayGrant} offerable={offerable} isSelf={editing.id === user.id}
            saving={saving} onChange={setEditField} onClose={() => setEditing(null)}
            onSave={saveEdit} onToggleStatus={toggleStatus}
            onGrant={grant} onRevoke={revoke}
          />
        )}
      </AppShell>
    </RequireLogin>
  );
}

/** Create a staff account.
 *
 * Only the roles the caller may actually assign are offered — the server refuses
 * the rest with a 403, and a drop-down full of refused choices teaches the
 * operator nothing.  The branch select keeps an explicit "all branches" option
 * for the organization-wide roles; a branch-scoped role must name a branch, so
 * the dialog requires one too.
 */
function NewStaffDialog({ draft, branches, offerable, error, saving, onChange, onClose, onCreate }) {
  const set = (key) => (e) => onChange({ ...draft, [key]: e.target.value });
  const branchRequired = needsBranch(draft.role);
  const roles = offerable.length ? offerable : [draft.role];

  return (
    <Modal
      title={t('newStaff')}
      onClose={onClose}
      size="lg"
      footer={(
        <>
          <button type="button" className="btn-outline" onClick={onClose} disabled={saving}>
            {t('cancel')}
          </button>
          <button type="button" className="btn" style={{ width: 'auto' }}
            data-testid="staff-create-submit" onClick={onCreate} disabled={saving}>
            {saving ? t('saving') : t('create')}
          </button>
        </>
      )}
    >
      <form noValidate onSubmit={(e) => { e.preventDefault(); onCreate(); }}>
        <FormRow>
          <Field label={t('username')} required>
            <Input name="username" autoComplete="off" value={draft.username}
              onChange={set('username')} data-testid="new-username" />
          </Field>
          <Field label={t('password')} hint={t('passwordMin')} required>
            <Input name="password" type="password" autoComplete="new-password"
              value={draft.password} onChange={set('password')} data-testid="new-password" />
          </Field>
          <Field label={t('fullName')} required>
            <Input name="display_name" value={draft.display_name}
              onChange={set('display_name')} data-testid="new-display-name" />
          </Field>
          <Field label={t('role')}>
            <Select name="role" value={draft.role} onChange={set('role')} data-testid="new-role">
              {roles.map((role) => (
                <option key={role} value={role}>{roleName(role)}</option>
              ))}
            </Select>
          </Field>
          <Field label={t('branchScope')}
            hint={branchRequired ? t('selectBranchFirst') : t('orgWide')}>
            <Select name="branch_id" value={draft.branch_id} onChange={set('branch_id')}
              data-testid="new-branch">
              {!branchRequired && <option value="">{t('orgWide')}</option>}
              {branches.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </Select>
          </Field>
          <Field label={t('language')}>
            <Select name="locale" value={draft.locale} onChange={set('locale')}>
              {LOCALES.map((code) => (
                <option key={code} value={code}>{code === 'bn' ? 'বাংলা' : 'English'}</option>
              ))}
            </Select>
          </Field>
          <Field label={t('email')}>
            <Input name="email" type="email" autoComplete="off" value={draft.email}
              onChange={set('email')} data-testid="new-email" />
          </Field>
          <Field label={t('mobile')}>
            <Input name="mobile" autoComplete="off" value={draft.mobile}
              onChange={set('mobile')} data-testid="new-mobile" />
          </Field>
        </FormRow>
        {error && (
          <div className="error" role="alert" data-testid="new-error"
            style={{ marginTop: '0.75rem' }}>{error}</div>
        )}
      </form>
    </Modal>
  );
}

/** Edit one staff member: profile, role, branch scope, capability grants, doctor
 * assignment and the active/inactive switch.
 *
 * Two things are deliberately not offered:
 *
 *  * a role change on your own row — the server refuses it, and self-demotion is
 *    the classic way to strand an organization with no administrator;
 *  * a capability grant when the caller is not an organization administrator.
 *    The catalogue is shown read-only instead, so the operator can see what the
 *    account holds without being offered a button that only returns 403.
 */
function EditStaffDialog({
  state, branches, doctors, catalogue, mayGrant, offerable, isSelf, saving,
  onChange, onClose, onSave, onToggleStatus, onGrant, onRevoke,
}) {
  const [confirming, setConfirming] = React.useState(false);
  const active = isActiveStatus(state.status);
  const roles = [state.role].concat(offerable.filter((r) => r !== state.role));
  const granted = {};
  (state.grants || []).forEach((g) => { granted[g.capability] = g; });

  const toggleDoctor = (id) => {
    const ids = state.doctors || [];
    onChange('doctors', ids.indexOf(id) >= 0 ? ids.filter((x) => x !== id) : ids.concat([id]));
  };

  return (
    <Modal
      title={t('editStaff') + ' — ' + (state.display_name || state.username)}
      onClose={onClose}
      size="lg"
      footer={(
        <>
          <button type="button" className="btn-outline" onClick={onClose} disabled={saving}>
            {t('cancel')}
          </button>
          <button type="button" className="btn-outline" data-testid="staff-toggle-status"
            disabled={saving}
            onClick={() => {
              // Deactivation is reversible, but it does stop sign-in, so it takes
              // a second, deliberate click.
              if (confirming) { setConfirming(false); onToggleStatus(); }
              else { setConfirming(true); }
            }}>
            {confirming ? t('confirm') : (active ? t('deactivate') : t('activate'))}
          </button>
          <button type="button" className="btn" style={{ width: 'auto' }}
            data-testid="staff-save" onClick={onSave} disabled={saving}>
            {saving ? t('saving') : t('save')}
          </button>
        </>
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="muted text-sm">{state.username}</span>
        <span className={'badge ' + (active ? 'badge-active' : 'badge-inactive')}>
          {statusName(state.status)}
        </span>
      </div>

      {confirming && (
        <div className="error" role="alert" data-testid="staff-status-confirm">
          {active ? t('deactivateConfirm') : t('activateConfirm')}
          {isSelf && active ? ' ' + t('lastActiveSelf') : ''}
        </div>
      )}

      <FormRow>
        <Field label={t('fullName')} required>
          <Input name="display_name" value={state.display_name}
            onChange={(e) => onChange('display_name', e.target.value)}
            data-testid="edit-display-name" />
        </Field>
        <Field label={t('email')}>
          <Input name="email" type="email" value={state.email}
            onChange={(e) => onChange('email', e.target.value)} data-testid="edit-email" />
        </Field>
        <Field label={t('mobile')}>
          <Input name="mobile" value={state.mobile}
            onChange={(e) => onChange('mobile', e.target.value)} data-testid="edit-mobile" />
        </Field>
        <Field label={t('language')}>
          <Select name="locale" value={state.locale}
            onChange={(e) => onChange('locale', e.target.value)}>
            {LOCALES.map((code) => (
              <option key={code} value={code}>{code === 'bn' ? 'বাংলা' : 'English'}</option>
            ))}
          </Select>
        </Field>
        <Field label={t('role')} hint={isSelf ? t('ownRoleLocked') : undefined}>
          <Select name="role" value={state.role} disabled={isSelf}
            onChange={(e) => onChange('role', e.target.value)} data-testid="edit-role">
            {roles.map((role) => (
              <option key={role} value={role}>{roleName(role)}</option>
            ))}
          </Select>
        </Field>
        <Field label={t('branchScope')}
          hint={needsBranch(state.role) ? t('selectBranchFirst') : t('orgWide')}>
          <Select name="branch_id" value={state.branch_id}
            onChange={(e) => onChange('branch_id', e.target.value)} data-testid="edit-branch">
            <option value="">{t('orgWide')}</option>
            {branches.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </Select>
        </Field>
      </FormRow>

      <div style={{ marginTop: '1rem' }}>
        <h3 className="text-sm font-semibold">{t('capabilities')}</h3>
        <p className="muted text-xs" style={{ marginBottom: '0.4rem' }}>{t('capabilityHint')}</p>
        {!catalogue.length ? <p className="muted text-sm">{t('loading')}</p> : (
          <div data-testid="staff-grants">
            {catalogue.map((cap) => {
              const row = granted[cap];
              return (
                <div key={cap} className="flex items-center justify-between gap-2"
                  style={{ padding: '0.2rem 0' }}>
                  <div>
                    <div className="text-sm">{t(capabilityLabelKey(cap))}</div>
                    <div className="muted text-xs">
                      {row
                        ? (row.branch_id ? branchLabel(branches, row.branch_id) : t('orgWide'))
                        : cap}
                    </div>
                  </div>
                  {mayGrant && (row ? (
                    <button type="button" className="btn-outline"
                      style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
                      data-testid={'staff-revoke-' + cap} disabled={saving}
                      onClick={() => onRevoke(row)}>
                      {t('revoke')}
                    </button>
                  ) : (
                    <button type="button" className="btn-outline"
                      style={{ width: 'auto', padding: '0.2rem 0.6rem' }}
                      data-testid={'staff-grant-' + cap} disabled={saving}
                      onClick={() => onGrant(cap)}>
                      {t('grant')}
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {state.role === 'assistant' && (
        <div style={{ marginTop: '1rem' }}>
          <h3 className="text-sm font-semibold">{t('assignDoctors')}</h3>
          <p className="muted text-xs">{t('doctorAssignmentHint')}</p>
          {!doctors.length ? <p className="muted text-sm">{t('empty')}</p> : (
            <div data-testid="staff-doctors"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill,minmax(12rem,1fr))',
                gap: '0.25rem',
              }}>
              {doctors.map((doc) => (
                <label key={doc.id} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" data-testid={'staff-doctor-' + doc.id}
                    checked={(state.doctors || []).indexOf(doc.id) >= 0} disabled={saving}
                    onChange={() => toggleDoctor(doc.id)} />
                  <span>{doc.name || doc.display_name || doc.id}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      {state.error && (
        <div className="error" role="alert" data-testid="edit-error"
          style={{ marginTop: '0.75rem' }}>{state.error}</div>
      )}
    </Modal>
  );
}
