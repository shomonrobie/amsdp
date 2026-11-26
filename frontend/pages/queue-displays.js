/* Queue displays — MP-39 / MP-35 / MP-45.
 *
 * The administration half of the multi-display DQDS.  The public board
 * (`pages/queue-display/[org]/[branch].js`) can only read; this screen is where
 * a facility decides which doctors each television shows, in which language, and
 * which optional fields it may publish.
 *
 * What the screen deliberately does *not* do:
 *
 *  * It is not the authorisation boundary.  The server decides
 *    `queue.display.manage` on every call and answers a non-disclosing 404 for
 *    another tenant's or branch's display; hiding a button here is a courtesy,
 *    not a control.
 *  * It never filters what the board publishes.  `show_room`,
 *    `show_estimated_wait` and `show_waiting_count` are applied while the public
 *    payload is built (`queuing/display.py`), so a field switched off is
 *    *absent* from the response rather than hidden with CSS.
 *  * It never deletes.  `status='disabled'` retires a display, and the public
 *    route then answers 404 exactly as it does for an unknown code.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import {
  RequireLogin, PermissionDenied, ErrorAlert, SuccessAlert, LoadingState,
} from '../components/ui/Alert';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import { Field, FormRow } from '../components/ui/Field';
import { Input, Select } from '../components/ui/Input';
import { getUser, apiFetch, can } from '../lib/auth';
import { t } from '../lib/i18n';
import {
  EMPTY_DISPLAY, SCOPE_TYPES, LANGUAGES, SCOPE_LABEL_KEYS,
  validateDisplayDraft, createPayload, patchPayload, displayUrl,
} from '../lib/displays';

function failure(e) {
  const status = e && e.status;
  const detail = String((e && (e.body || e.message)) || e || '');
  if (status === 403) return t('dispManageDenied');
  if (status === 409 || /already/i.test(detail)) return t('dispCodeTaken');
  return detail || t('saveFailed');
}

export default function QueueDisplays() {
  const user = getUser();
  const orgId = user.organization_id || '';
  const mayManage = can('queue.display.manage');

  const [branches, setBranches] = React.useState([]);
  const [branchId, setBranchId] = React.useState('');
  const [displays, setDisplays] = React.useState([]);
  const [doctors, setDoctors] = React.useState([]);
  const [departments, setDepartments] = React.useState([]);
  const [rooms, setRooms] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState('');
  const [notice, setNotice] = React.useState('');
  const [copied, setCopied] = React.useState('');
  const [draft, setDraft] = React.useState(null);      /* the create/edit form */
  const [original, setOriginal] = React.useState(null); /* the row as the server sent it */
  const [draftError, setDraftError] = React.useState('');
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (!mayManage || !orgId) { setLoading(false); return; }
    apiFetch('/api/v1/orgs/' + encodeURIComponent(orgId) + '/branches')
      .then((d) => {
        const list = Array.isArray(d) ? d : (d.items || []);
        setBranches(list);
        // A branch-scoped administrator already has a branch; only an
        // organization-wide caller has to choose one.
        setBranchId(user.branch_id || (list[0] ? list[0].id : ''));
      })
      .catch(() => { setBranches([]); setLoading(false); });
    apiFetch('/api/v1/doctors')
      .then((d) => setDoctors(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setDoctors([]));
  }, [mayManage, orgId, user.branch_id]);

  const loadDisplays = React.useCallback(async () => {
    if (!mayManage || !branchId) { setLoading(false); return; }
    setLoading(true);
    try {
      const d = await apiFetch('/api/v1/queue/displays?branch_id='
        + encodeURIComponent(branchId));
      setDisplays((d && d.displays) || []);
      setErr('');
    } catch (e) {
      setErr(failure(e));
      setDisplays([]);
    } finally {
      setLoading(false);
    }
  }, [mayManage, branchId]);

  React.useEffect(() => { loadDisplays(); }, [loadDisplays]);

  /* Departments and rooms are scope targets and are read per branch: the server
     refuses a room or department that is not this branch's. */
  React.useEffect(() => {
    if (!mayManage || !branchId) { setDepartments([]); setRooms([]); return; }
    apiFetch('/api/v1/branches/' + encodeURIComponent(branchId) + '/departments')
      .then((d) => setDepartments(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setDepartments([]));
    apiFetch('/api/v1/branches/' + encodeURIComponent(branchId) + '/rooms')
      .then((d) => setRooms(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setRooms([]));
  }, [mayManage, branchId]);

  const branch = branches.find((b) => b.id === branchId) || null;

  const openNew = () => {
    setErr(''); setNotice(''); setDraftError('');
    setOriginal(null);
    setDraft({ ...EMPTY_DISPLAY });
  };

  const openEdit = (row) => {
    setErr(''); setNotice(''); setDraftError('');
    setOriginal(row);
    setDraft({
      ...EMPTY_DISPLAY,
      ...row,
      department_id: row.department_id || '',
      room_id: row.room_id || '',
      doctor_ids: row.doctor_ids || [],
    });
  };

  const set = (key, value) => setDraft((cur) => (cur ? { ...cur, [key]: value } : cur));

  const toggleDoctor = (id) => setDraft((cur) => {
    if (!cur) return cur;
    const ids = cur.doctor_ids || [];
    return {
      ...cur,
      doctor_ids: ids.indexOf(id) >= 0 ? ids.filter((x) => x !== id) : ids.concat([id]),
    };
  });

  const save = async () => {
    if (!draft) return;
    const check = validateDisplayDraft(draft);
    if (!check.ok) { setDraftError(t(check.error)); return; }
    if (!branchId) { setDraftError(t('dispBranchRequired')); return; }
    setSaving(true);
    setDraftError('');
    try {
      if (draft.id) {
        // Only what changed is sent, so a no-op save writes no audit row.
        const patch = patchPayload(draft, original || {});
        if (Object.keys(patch).length) {
          await apiFetch('/api/v1/queue/displays/' + encodeURIComponent(draft.id), {
            method: 'PATCH', body: JSON.stringify(patch),
          });
        }
        setNotice(t('dispUpdated'));
      } else {
        await apiFetch('/api/v1/queue/displays', {
          method: 'POST', body: JSON.stringify(createPayload(draft, branchId)),
        });
        setNotice(t('dispCreated'));
      }
      setDraft(null);
      setOriginal(null);
      await loadDisplays();
    } catch (e) {
      setDraftError(failure(e));
    } finally {
      setSaving(false);
    }
  };

  /* Disabling is the retirement path: one audited PATCH, no delete. */
  const toggleStatus = async (row) => {
    setSaving(true);
    try {
      await apiFetch('/api/v1/queue/displays/' + encodeURIComponent(row.id), {
        method: 'PATCH',
        body: JSON.stringify({ status: row.status === 'active' ? 'disabled' : 'active' }),
      });
      setNotice(t('dispUpdated'));
      await loadDisplays();
    } catch (e) {
      setErr(failure(e));
    } finally {
      setSaving(false);
    }
  };

  const copyUrl = async (row) => {
    const url = window.location.origin
      + displayUrl((branch && branch.code) || '', row.code);
    try {
      await navigator.clipboard.writeText(url);
    } catch (e) {
      // Clipboard access can be refused (insecure origin, denied permission).
      // The address is already on screen, so nothing is lost.
    }
    setCopied(row.id);
  };

  if (!user.id) return null;

  return (
    <AppShell>
      <RequireLogin>
        {!mayManage
          ? <PermissionDenied msg={t('dispManageDenied')} />
          : (
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h1 className="text-xl font-bold text-foreground" data-testid="displays-heading">
                    {t('dispTitle')}
                  </h1>
                  <p className="text-sm text-muted-foreground">{t('dispHint')}</p>
                </div>
                <div className="flex flex-wrap items-end gap-2">
                  <Field label={t('branch')}>
                    <Select value={branchId} data-testid="displays-branch"
                      onChange={(e) => setBranchId(e.target.value)}>
                      {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                    </Select>
                  </Field>
                  <Button data-testid="displays-new" onClick={openNew}>{t('dispNew')}</Button>
                </div>
              </div>

              {err ? <ErrorAlert>{err}</ErrorAlert> : null}
              {notice ? <SuccessAlert>{notice}</SuccessAlert> : null}

              {loading
                ? <LoadingState msg={t('loading')} />
                : (displays.length === 0
                  ? (
                    <p className="text-sm text-muted-foreground" data-testid="displays-empty">
                      {t('dispEmpty')}
                    </p>
                  )
                  : (
                    <ul className="flex flex-col gap-2" data-testid="displays-list">
                      {displays.map((row) => (
                        <li key={row.id} className="rounded border border-input bg-card p-3"
                          data-testid={'display-row-' + row.id}>
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div>
                              <div className="font-semibold text-foreground">{row.name}</div>
                              <div className="text-xs text-muted-foreground">
                                <span data-testid={'display-code-' + row.id}>{row.code}</span>
                                {' · '}{t('dispLanguage')}: {row.language}
                                {' · '}{t(SCOPE_LABEL_KEYS[row.scope_type] || 'dispScopeBranch')}
                                {' · '}{row.status === 'active' ? t('dispEnabled') : t('dispDisabled')}
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <Button variant="ghost" size="sm"
                                data-testid={'display-edit-' + row.id} onClick={() => openEdit(row)}>
                                {t('edit')}
                              </Button>
                              <Button variant="ghost" size="sm"
                                data-testid={'display-status-' + row.id} onClick={() => toggleStatus(row)}>
                                {row.status === 'active' ? t('dispDisable') : t('dispEnable')}
                              </Button>
                              <Button variant="ghost" size="sm"
                                data-testid={'display-copy-' + row.id} onClick={() => copyUrl(row)}>
                                {copied === row.id ? t('dispCopied') : t('dispCopy')}
                              </Button>
                            </div>
                          </div>
                          <div className="mt-2 text-xs text-muted-foreground">
                            {t('dispUrl')}:{' '}
                            <code data-testid={'display-url-' + row.id}>
                              {displayUrl((branch && branch.code) || '', row.code)}
                            </code>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ))}
            </div>
          )}
      </RequireLogin>

      {draft
        ? (
          <Modal title={draft.id ? t('dispEdit') : t('dispNew')}
            onClose={() => { setDraft(null); setOriginal(null); }}
            footer={(
              <div className="flex justify-end gap-2">
                <Button variant="ghost" onClick={() => { setDraft(null); setOriginal(null); }}>
                  {t('cancel')}
                </Button>
                <Button data-testid="display-save" disabled={saving} onClick={save}>
                  {saving ? t('saving') : t('save')}
                </Button>
              </div>
            )}>
            <FormRow>
              <Field label={t('dispName')} required>
                <Input value={draft.name} data-testid="display-name"
                  onChange={(e) => set('name', e.target.value)} />
              </Field>
              <Field label={t('dispCode')} hint={t('dispCodeHint')} required>
                <Input value={draft.code} data-testid="display-code"
                  onChange={(e) => set('code', e.target.value)} />
              </Field>
              <Field label={t('dispLanguage')}>
                <Select value={draft.language} data-testid="display-language"
                  onChange={(e) => set('language', e.target.value)}>
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>{l === 'bn' ? 'বাংলা' : 'English'}</option>
                  ))}
                </Select>
              </Field>
              <Field label={t('dispScope')}>
                <Select value={draft.scope_type} data-testid="display-scope"
                  onChange={(e) => set('scope_type', e.target.value)}>
                  {SCOPE_TYPES.map((s) => (
                    <option key={s} value={s}>{t(SCOPE_LABEL_KEYS[s])}</option>
                  ))}
                </Select>
              </Field>
              {draft.scope_type === 'department'
                ? (
                  <Field label={t('dispDepartment')} required>
                    <Select value={draft.department_id} data-testid="display-department"
                      onChange={(e) => set('department_id', e.target.value)}>
                      <option value="">{t('select')}</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </Select>
                  </Field>
                ) : null}
              {draft.scope_type === 'room'
                ? (
                  <Field label={t('dispScopeRoom')} required>
                    <Select value={draft.room_id} data-testid="display-room"
                      onChange={(e) => set('room_id', e.target.value)}>
                      <option value="">{t('select')}</option>
                      {rooms.map((r) => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                      ))}
                    </Select>
                  </Field>
                ) : null}
              <Field label={t('dispFooter')} hint={t('dispFooterHint')}>
                <Input value={draft.footer_text} data-testid="display-footer"
                  onChange={(e) => set('footer_text', e.target.value)} />
              </Field>
            </FormRow>

            {draft.scope_type === 'doctors'
              ? (
                <fieldset className="mt-3" data-testid="display-doctors">
                  <legend className="text-sm font-semibold text-foreground">{t('dispDoctors')}</legend>
                  <p className="text-xs text-muted-foreground">{t('dispDoctorsHint')}</p>
                  <div className="mt-1 flex flex-col gap-1">
                    {doctors.map((d) => (
                      <label key={d.id} className="flex items-center gap-2 text-sm">
                        <input type="checkbox"
                          checked={(draft.doctor_ids || []).indexOf(d.id) >= 0}
                          onChange={() => toggleDoctor(d.id)} />
                        <span>{d.name}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )
              : null}

            {/* MP-45 — the facility decides which optional fields its public
                board may publish.  The server removes a field that is off; this
                checkbox is the control, not the enforcement. */}
            <fieldset className="mt-3">
              <legend className="text-sm font-semibold text-foreground">{t('view')}</legend>
              {[['show_room', 'dispShowRoom'],
                ['show_estimated_wait', 'dispShowWait'],
                ['show_waiting_count', 'dispShowCount']].map(([key, labelKey]) => (
                  <label key={key} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={!!draft[key]}
                      data-testid={'display-' + key}
                      onChange={(e) => set(key, e.target.checked)} />
                    <span>{t(labelKey)}</span>
                  </label>
                ))}
            </fieldset>

            {draftError ? <ErrorAlert>{draftError}</ErrorAlert> : null}
          </Modal>
        )
        : null}
    </AppShell>
  );
}
