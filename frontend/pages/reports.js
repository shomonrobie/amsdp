/* Operational reports — MP-23 / BR §43 (Product Owner decision PO-11, Option A).
 *
 * The backend (`appointment/reports.py`) computes one report: appointments by day,
 * doctor and branch, status counts, walk-ins, booking sources, queue activity and
 * utilisation, all from the same scoped row set, plus a `reconciliation` block
 * naming the identities that hold. This screen displays it and nothing else:
 *
 *  * it never recounts anything — every figure printed here comes from the server;
 *  * it never widens scope — the organisation is the token's, and a branch outside
 *    the caller's scope is the route's non-disclosing 404, shown as not found;
 *  * it refuses to ask a question the API refuses: a day *and* a period, an
 *    inverted period and a period beyond the route's ceiling are stopped here;
 *  * it prints "reconciles" only when the identities in the payload actually hold;
 *  * `percent: null` is printed as a dash, never as 0%, and unscheduled seats are
 *    shown in their own column so a day can honestly exceed 100%.
 */
import React from 'react';
import AppShell from '../components/AppShell';
import {
  RequireLogin, PermissionDenied, ErrorAlert, LoadingState,
} from '../components/ui/Alert';
import Button from '../components/ui/Button';
import { Field } from '../components/ui/Field';
import { Input, Select } from '../components/ui/Input';
import { getUser, apiFetch, can } from '../lib/auth';
import { t } from '../lib/i18n';
import {
  HEADLINE_KEYS, HEADLINE_ORDER, QUEUE_METRICS, isEmptyReport, isoDay,
  minutesText, percentText, periodInverted, periodTooLong, queueStateRows,
  reconciles, reportQuery, scopeOf, statusRows, utilisationRows,
} from '../lib/operational-report';

function failure(e) {
  const status = e && e.status;
  const body = e && e.body;
  const detail = typeof body === 'string' ? body
    : (body && (body.message || body.detail)) || (e && e.message) || '';
  if (status === 403) return t('repNoAccess');
  if (status === 404) return t('repNotFound');
  return String(detail || t('repLoadFailed'));
}

function Section({ title, testid, children }) {
  return (
    <section className="rounded border border-input bg-card p-3" data-testid={testid}>
      <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      <div className="mt-2 text-sm">{children}</div>
    </section>
  );
}

function CountTable({ head, rows, testid }) {
  if (!rows.length) {
    return (
      <p className="text-muted-foreground" data-testid={testid + '-empty'}>
        {t('repNoRows')}
      </p>
    );
  }
  return (
    <table className="w-full text-sm" data-testid={testid}>
      <thead>
        <tr className="text-left text-xs text-muted-foreground">
          {head.map((h, i) => <th key={String(i)} className="py-1 pr-3">{h}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id} className="border-t border-input">
            <td className="py-1 pr-3">{row.label}</td>
            <td className="py-1 pr-3">{row.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Reports() {
  const user = getUser();
  const mayRead = can('appointment.read');

  const [branches, setBranches] = React.useState([]);
  const [doctors, setDoctors] = React.useState([]);
  const [mode, setMode] = React.useState('day');
  const [day, setDay] = React.useState(isoDay(new Date()));
  const [from, setFrom] = React.useState(isoDay(new Date()));
  const [to, setTo] = React.useState(isoDay(new Date()));
  const [branchId, setBranchId] = React.useState('');
  const [doctorId, setDoctorId] = React.useState('');
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    if (!mayRead || !user.organization_id) return;
    apiFetch('/api/v1/orgs/' + encodeURIComponent(user.organization_id) + '/branches')
      .then((d) => setBranches(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setBranches([]));
    apiFetch('/api/v1/doctors')
      .then((d) => setDoctors(Array.isArray(d) ? d : (d.items || [])))
      .catch(() => setDoctors([]));
  }, [mayRead, user.organization_id]);

  const badRange = mode === 'range'
    && (!from || !to || periodInverted(from, to) || periodTooLong(from, to));

  const load = React.useCallback(async () => {
    if (!mayRead) return;
    if (badRange || (mode === 'day' && !day)) { setData(null); return; }
    setLoading(true);
    setErr('');
    try {
      setData(await apiFetch(reportQuery({ mode, day, from, to, branchId, doctorId })));
    } catch (e) {
      setErr(failure(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [mayRead, badRange, mode, day, from, to, branchId, doctorId]);

  React.useEffect(() => { load(); }, [load]);

  if (!user.id) return null;

  return (
    <AppShell>
      <RequireLogin>
        {!mayRead
          ? <PermissionDenied msg={t('repNoAccess')} />
          : (
            <div className="flex flex-col gap-4">
              <div>
                <h1 className="text-xl font-bold text-foreground" data-testid="rep-heading">
                  {t('repTitle')}
                </h1>
                <p className="text-sm text-muted-foreground">{t('repHint')}</p>
              </div>

              <div className="flex flex-wrap items-end gap-3">
                <div className="flex gap-2">
                  <Button variant={mode === 'day' ? 'primary' : 'ghost'} size="sm"
                    data-testid="rep-mode-day" onClick={() => setMode('day')}>
                    {t('repDay')}
                  </Button>
                  <Button variant={mode === 'range' ? 'primary' : 'ghost'} size="sm"
                    data-testid="rep-mode-range" onClick={() => setMode('range')}>
                    {t('repRange')}
                  </Button>
                </div>
                {mode === 'day' ? (
                  <Field label={t('date')} required>
                    <Input type="date" value={day} data-testid="rep-date"
                      onChange={(e) => setDay(e.target.value)} />
                  </Field>
                ) : (
                  <React.Fragment>
                    <Field label={t('repFrom')} required>
                      <Input type="date" value={from} data-testid="rep-from"
                        onChange={(e) => setFrom(e.target.value)} />
                    </Field>
                    <Field label={t('repTo')} required>
                      <Input type="date" value={to} data-testid="rep-to"
                        onChange={(e) => setTo(e.target.value)} />
                    </Field>
                  </React.Fragment>
                )}
                <Field label={t('branch')}>
                  <Select value={branchId} data-testid="rep-branch"
                    onChange={(e) => setBranchId(e.target.value)}>
                    <option value="">{t('allBranches')}</option>
                    {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </Select>
                </Field>
                <Field label={t('doctor')}>
                  <Select value={doctorId} data-testid="rep-doctor"
                    onChange={(e) => setDoctorId(e.target.value)}>
                    <option value="">{t('repAllDoctors')}</option>
                    {doctors.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </Select>
                </Field>
              </div>

              {badRange
                ? (
                  <ErrorAlert>
                    {periodTooLong(from, to) ? t('repTooLong') : t('repBadRange')}
                  </ErrorAlert>
                )
                : null}
              {err ? <ErrorAlert>{err}</ErrorAlert> : null}
              {loading ? <LoadingState msg={t('loading')} /> : null}
              {!loading && !badRange && data ? <ReportBody data={data} /> : null}
            </div>
          )}
      </RequireLogin>
    </AppShell>
  );
}


/* Everything below a successful load.  Each figure is printed from the payload;
   none of it is recomputed, so the screen cannot disagree with the API. */
function ReportBody({ data }) {
  const scope = scopeOf(data);
  const appointments = data.appointments || {};
  const headline = data.br43 || {};
  const queue = data.queue_activity || {};
  const utilisation = data.utilisation || {};
  const check = reconciles(data);

  const countRows = (rows, field) => (rows || []).map((row) => ({
    id: String(row[field]), label: String(row[field]), count: row.count,
  }));
  const labelled = (rows) => rows.map((row) => ({
    id: row.status || row.state,
    label: row.labelKey ? t(row.labelKey) : (row.status || row.state),
    count: row.count,
  }));

  return (
    <div className="flex flex-col gap-3" data-testid="rep-report">
      <p className="text-sm" data-testid="rep-scope">
        <strong>{t('repScope')}:</strong>{' '}
        {scope.from === scope.to ? scope.from : scope.from + ' → ' + scope.to}
        {' · '}{scope.branchId || t('repWholeOrg')}
        {scope.narrowed ? ' · ' + t('repNarrowed') : ''}
      </p>

      {isEmptyReport(data)
        ? (
          <p className="text-sm text-muted-foreground" data-testid="rep-empty">
            {t('repEmpty')}
          </p>
        )
        : null}

      <Section title={t('repHeadline')} testid="rep-headline">
        <ul className="flex flex-wrap gap-4">
          {HEADLINE_ORDER.map((name) => (
            <li key={name} data-testid={'rep-headline-' + name}>
              <span className="text-xs text-muted-foreground">{t(HEADLINE_KEYS[name])}</span>
              {' '}
              <strong>{headline[name] === undefined ? '—' : headline[name]}</strong>
            </li>
          ))}
          <li data-testid="rep-headline-total">
            <span className="text-xs text-muted-foreground">{t('repTotal')}</span>
            {' '}
            <strong>{appointments.total || 0}</strong>
          </li>
        </ul>
        <p className="mt-1 text-xs text-muted-foreground">{t('repHeadlineHint')}</p>
      </Section>

      <Section title={t('repStatusCounts')} testid="rep-status">
        <CountTable head={[t('repStatus'), t('repCount')]}
          rows={labelled(statusRows(data.status_counts))} testid="rep-status-table" />
      </Section>


      <Section title={t('repDimAppointments')} testid="rep-appointments">
        <div className="flex flex-col gap-2">
          <strong className="text-xs text-muted-foreground">{t('repByDay')}</strong>
          <CountTable head={[t('date'), t('repCount')]}
            rows={countRows(appointments.by_day, 'date')} testid="rep-by-day" />
          <strong className="text-xs text-muted-foreground">{t('repByDoctor')}</strong>
          <CountTable head={[t('doctor'), t('repCount')]}
            rows={countRows(appointments.by_doctor, 'doctor_id')} testid="rep-by-doctor" />
          <strong className="text-xs text-muted-foreground">{t('repByBranch')}</strong>
          <CountTable head={[t('branch'), t('repCount')]}
            rows={countRows(appointments.by_branch, 'branch_id')} testid="rep-by-branch" />
        </div>
      </Section>

      <Section title={t('repDimWalkIns')} testid="rep-walkins">
        <p>
          <strong>{t('repWalkIns')}:</strong> {data.walk_ins || 0}
        </p>
        <CountTable head={[t('repSource'), t('repCount')]}
          rows={countRows(data.booking_sources, 'source')} testid="rep-sources" />
      </Section>

      <Section title={t('repDimQueue')} testid="rep-queue">
        <ul className="flex flex-wrap gap-4">
          {QUEUE_METRICS.map((metric) => (
            <li key={metric.key} data-testid={'rep-queue-' + metric.key}>
              <span className="text-xs text-muted-foreground">{t(metric.labelKey)}</span>
              {' '}
              <strong>
                {metric.key.indexOf('avg_') === 0
                  ? minutesText(queue[metric.key]) : (queue[metric.key] || 0)}
              </strong>
            </li>
          ))}
        </ul>
        <CountTable head={[t('repStatus'), t('repCount')]}
          rows={labelled(queueStateRows(queue.by_status))} testid="rep-queue-states" />
        <CountTable head={[t('repSource'), t('repCount')]}
          rows={countRows(queue.by_source, 'source')} testid="rep-queue-sources" />
      </Section>


      <Section title={t('repDimUtilisation')} testid="rep-utilisation">
        <p>
          <strong>{t('repCapacity')}:</strong> {utilisation.capacity || 0}
          {' · '}<strong>{t('repClaimed')}:</strong> {utilisation.claimed || 0}
          {' · '}<strong>{t('repUnscheduled')}:</strong> {utilisation.unscheduled || 0}
          {' · '}<strong>{t('repUtilisation')}:</strong> {percentText(utilisation.percent)}
        </p>
        <p className="text-xs text-muted-foreground">{t('repUtilisationHint')}</p>
        <table className="w-full text-sm" data-testid="rep-utilisation-table">
          <thead>
            <tr className="text-left text-xs text-muted-foreground">
              <th className="py-1 pr-3">{t('doctor')}</th>
              <th className="py-1 pr-3">{t('repCapacity')}</th>
              <th className="py-1 pr-3">{t('repClaimed')}</th>
              <th className="py-1 pr-3">{t('repUnscheduled')}</th>
              <th className="py-1 pr-3">{t('repUtilisation')}</th>
            </tr>
          </thead>
          <tbody>
            {utilisationRows(utilisation).map((row) => (
              <tr key={row.doctorId} className="border-t border-input">
                <td className="py-1 pr-3">{row.doctorId}</td>
                <td className="py-1 pr-3">{row.capacity}</td>
                <td className="py-1 pr-3">{row.claimed}</td>
                <td className="py-1 pr-3">{row.unscheduled}</td>
                <td className="py-1 pr-3">{percentText(row.percent)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title={t('repReconciliation')} testid="rep-reconciliation">
        {check.ok
          ? <p data-testid="rep-reconciles">{t('repReconciled')}</p>
          : (
            <ErrorAlert>
              {t('repReconcileFailed')}
              {check.problems.length ? ': ' + check.problems.join(', ') : ''}
            </ErrorAlert>
          )}
      </Section>
    </div>
  );
}

