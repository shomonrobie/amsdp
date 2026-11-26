/* Queue history — MP-24 / BR §30.
 *
 * The queue page shows the live board.  This screen answers the other question
 * the front desk asks: what happened to everybody who was in this queue today —
 * completed, cancelled, skipped and no-show included — for one doctor and one
 * day.
 *
 * It consumes the existing `GET /api/v1/queue/history`, whose contract is
 * unchanged: `doctor_id` and `date` are required, `status` and `branch_id` are
 * optional, the doctor/assistant may only read their own assigned doctor, and a
 * branch outside the caller's scope is a non-disclosing 404.  The screen adds no
 * authority of its own; it filters nothing client-side except the rendering of a
 * status the server already returned.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import {
  RequireLogin, PermissionDenied, ErrorAlert, LoadingState,
} from '../components/ui/Alert';
import { Field } from '../components/ui/Field';
import { Input, Select } from '../components/ui/Input';
import { getUser, apiFetch, can } from '../lib/auth';
import { t } from '../lib/i18n';
import { STATUS_OPTIONS, historyQuery, summarise } from '../lib/queue/history';

const PAGE_SIZE = 50;

function todayIso() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

export default function QueueHistory() {
  const user = getUser();
  const mayView = can('queue.view');
  const [branches, setBranches] = React.useState([]);
  const [doctors, setDoctors] = React.useState([]);
  const [branchId, setBranchId] = React.useState(user.branch_id || '');
  const [doctorId, setDoctorId] = React.useState(user.doctor_id || '');
  const [day, setDay] = React.useState(todayIso());
  const [status, setStatus] = React.useState('');
  const [rows, setRows] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [page, setPage] = React.useState(0);

  React.useEffect(() => {
    if (!mayView || !user.organization_id) return;
    apiFetch('/api/v1/orgs/' + encodeURIComponent(user.organization_id) + '/branches')
      .then((d) => setBranches(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setBranches([]));
    apiFetch('/api/v1/doctors')
      .then((d) => setDoctors(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setDoctors([]));
  }, [mayView, user.organization_id]);

  const load = React.useCallback(async () => {
    if (!mayView || !doctorId || !day) { setRows([]); return; }
    setLoading(true);
    setErr('');
    try {
      const data = await apiFetch(historyQuery({ doctorId, day, status, branchId }));
      setRows(Array.isArray(data) ? data : (data.items || []));
      setPage(0);
    } catch (e) {
      setErr(String((e && (e.body || e.message)) || e) || t('histLoadFailed'));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [mayView, doctorId, day, status, branchId]);

  React.useEffect(() => { load(); }, [load]);

  const counts = summarise(rows);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const visible = rows.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  if (!user.id) return null;

  return (
    <AppShell>
      <RequireLogin>
        {!mayView
          ? <PermissionDenied msg={t('permissionDenied')} />
          : (
            <div className="flex flex-col gap-4">
              <div>
                <h1 className="text-xl font-bold text-foreground" data-testid="history-heading">
                  {t('histTitle')}
                </h1>
                <p className="text-sm text-muted-foreground">{t('histHint')}</p>
              </div>

              <div className="flex flex-wrap items-end gap-3">
                <Field label={t('branch')}>
                  <Select value={branchId} data-testid="history-branch"
                    onChange={(e) => setBranchId(e.target.value)}>
                    <option value="">{t('allBranches')}</option>
                    {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </Select>
                </Field>
                <Field label={t('doctor')} required>
                  <Select value={doctorId} data-testid="history-doctor"
                    onChange={(e) => setDoctorId(e.target.value)}>
                    <option value="">{t('select')}</option>
                    {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </Select>
                </Field>
                <Field label={t('date')} required>
                  <Input type="date" value={day} data-testid="history-date"
                    onChange={(e) => setDay(e.target.value)} />
                </Field>
                <Field label={t('status')}>
                  <Select value={status} data-testid="history-status"
                    onChange={(e) => setStatus(e.target.value)}>
                    <option value="">{t('histAllStatuses')}</option>
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s.value} value={s.value}>{t(s.labelKey)}</option>
                    ))}
                  </Select>
                </Field>
              </div>

              {err ? <ErrorAlert>{err}</ErrorAlert> : null}

              {loading
                ? <LoadingState msg={t('loading')} />
                : (rows.length === 0
                  ? <p className="text-sm text-muted-foreground" data-testid="history-empty">{t('histEmpty')}</p>
                  : (
                    <div className="flex flex-col gap-2">
                      <p className="text-xs text-muted-foreground" data-testid="history-summary">
                        {t('total')}: {rows.length}
                        {STATUS_OPTIONS.map((s) => (
                          <span key={s.value}> · {t(s.labelKey)}: {counts[s.value] || 0}</span>
                        ))}
                      </p>
                      <table className="w-full text-sm" data-testid="history-table">
                        <thead>
                          <tr className="text-left text-xs uppercase text-muted-foreground">
                            <th scope="col">{t('token')}</th>
                            <th scope="col">{t('position')}</th>
                            <th scope="col">{t('patient')}</th>
                            <th scope="col">{t('status')}</th>
                            <th scope="col">{t('source')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {visible.map((row) => (
                            <tr key={row.id} className="border-t border-border"
                              data-testid={'history-row-' + row.id}>
                              <td className="font-semibold">{row.token}</td>
                              <td>{row.position}</td>
                              <td>{row.patient_name || t('empty')}</td>
                              <td>{t(statusKey(row.status))}</td>
                              <td>{row.entry_source || ''}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {pages > 1
                        ? (
                          <div className="flex items-center gap-2 text-sm">
                            <button type="button" className="btn btn-outline btn-sm"
                              disabled={page === 0} data-testid="history-prev"
                              onClick={() => setPage((p) => Math.max(0, p - 1))}>
                              {t('aptPrevPage')}
                            </button>
                            <span data-testid="history-page">{page + 1} / {pages}</span>
                            <button type="button" className="btn btn-outline btn-sm"
                              disabled={page >= pages - 1} data-testid="history-next"
                              onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}>
                              {t('aptNextPage')}
                            </button>
                          </div>
                        )
                        : null}
                    </div>
                  ))}
            </div>
          )}
      </RequireLogin>
    </AppShell>
  );
}

/* The queue statuses are the server's vocabulary; each has exactly one label key. */
function statusKey(status) {
  const found = STATUS_OPTIONS.find((s) => s.value === status);
  return found ? found.labelKey : 'status';
}
