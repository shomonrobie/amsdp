import React from 'react';
import Link from 'next/link';
import AppShell from '../components/AppShell';
import { LoadingState, EmptyState, ErrorAlert, RequireLogin } from '../components/ui/Alert';
import { getUser, apiFetch, getActiveBranch } from '../lib/auth';
import { t } from '../lib/i18n';
import {
  activityQuery, activityRows, dashboardQuery, perDoctorRows, quickActionsFor,
  selectableBranches,
} from '../lib/dashboard';

// MP-22: the dashboard is the screen an operator lands on, so it carries the
// three things they would otherwise hunt for — the day's figures, the branch and
// date those figures are about (both selectable, both server-checked), and what
// has just happened. Every figure comes from `/api/v1/dashboard/today`, which
// derives the tenant from the token; the selectors narrow the answer and can
// never widen it, because the server answers a non-disclosing 404 for a branch
// the caller does not hold. `date` is the *facility* day: the server defaults it
// to the organization's own today, not the server's UTC date.
//
// Q-2 (approved 2026-11-25): the tiles answer two different questions and must
// not be aliased. **Waiting** is `queue_length` — live queue entries for the day,
// the same population the public board shows, so an appointment-less walk-in
// counts. **In queue** is `in_queue` — appointment *records* whose status is
// IN_QUEUE, a booking-state tally that the queue panel shows separately under its
// own label. The two differ by exactly the walk-ins.
export default function Dashboard() {
  const user = getUser();
  const activeBranch = getActiveBranch();
  const [branchId, setBranchId] = React.useState(activeBranch || '');
  const [date, setDate] = React.useState('');
  const [branches, setBranches] = React.useState([]);
  const [today, setToday] = React.useState(null);
  const [activity, setActivity] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!user || !user.organization_id) return;
    apiFetch('/api/v1/orgs/' + encodeURIComponent(user.organization_id) + '/branches')
      .then((rows) => setBranches(selectableBranches(rows, user)))
      .catch(() => setBranches([]));
  }, [user && user.organization_id]);

  React.useEffect(() => {
    if (!user) return;
    setLoading(true);
    const qs = dashboardQuery({ branchId, date });
    apiFetch('/api/v1/dashboard/today' + qs)
      .then((d) => { setToday(d); setLoading(false); })
      .catch((e) => { setError(String(e && e.message || e)); setLoading(false); });
  }, [user && user.user_id, branchId, date]);

  React.useEffect(() => {
    if (!user) return;
    apiFetch('/api/v1/dashboard/audit' + activityQuery({ branchId, limit: 8 }))
      .then((rows) => setActivity(activityRows(rows)))
      .catch(() => setActivity([]));
  }, [user && user.user_id, branchId]);

  const cards = today ? [
    { label: t('booked'), value: today.scheduled || 0 },
    { label: t('checkedIn'), value: today.checked_in || 0 },
    { label: t('waiting'), value: today.queue_length || 0 },
    { label: t('completedT'), value: today.completed || 0 },
    { label: t('cancelledT'), value: today.cancelled || 0 },
    { label: t('noShow'), value: today.no_show || 0 },
  ] : [];
  const doctors = today ? perDoctorRows(today) : [];
  const actions = quickActionsFor(user);

  return (
    <RequireLogin>
      <AppShell active="/dashboard" breadcrumbs={[{ label: t('dash') }]}>
        <h1 className="page-title">{t('dash')}</h1>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 12 }}>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.8rem' }}>
            <span>{t('branch')}</span>
            <select value={branchId} onChange={(e) => setBranchId(e.target.value)} aria-label={t('branch')}>
              <option value="">{t('allBranches')}</option>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.8rem' }}>
            <span>{t('date')}</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} aria-label={t('date')} />
          </label>
          {date && <button type="button" onClick={() => setDate('')}>{t('today')}</button>}
        </div>

        {error && <ErrorAlert>{error}</ErrorAlert>}
        {loading && <LoadingState />}
        {today && (
          <>
            <p role="status" style={{ fontSize: '0.85rem', color: '#555' }}>
              {t('showingDay')}: {today.date}
              {today.facility_today && today.date !== today.facility_today
                ? ' (' + t('facilityToday') + ': ' + today.facility_today + ')' : ''}
            </p>
            <div className="flex flex-wrap">
              {cards.map((c) => (
                <div key={c.label} className="card" style={{ minWidth: 140, marginRight: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#1a5c7a' }}>{c.value}</div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>{c.label}</div>
                </div>
              ))}
            </div>

            <section className="card" style={{ marginTop: 16 }}>
              <h2 style={{ fontSize: '1rem' }}>{t('queueToday')}</h2>
              <p role="status">
                {t('waitingNow')}: {today.queue_length == null ? 0 : today.queue_length}
                {' · '}{t('inQueueRecords')}: {today.in_queue == null ? 0 : today.in_queue}
                {' · '}{t('walkIns')}: {today.walk_ins || 0}
              </p>
              {doctors.length === 0
                ? <EmptyState msg={t('noBookings')} />
                : (
                  <table>
                    <thead><tr><th>{t('doctor')}</th><th>{t('booked')}</th></tr></thead>
                    <tbody>
                      {doctors.map((d) => (
                        <tr key={d.doctorId}><td>{d.name}</td><td>{d.count}</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
            </section>

            <section className="card" style={{ marginTop: 16 }}>
              <h2 style={{ fontSize: '1rem' }}>{t('quickActions')}</h2>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {actions.map((a) => (
                  <Link key={a.href} href={a.href} className="btn-outline">{t(a.key)}</Link>
                ))}
              </div>
            </section>

            <section className="card" style={{ marginTop: 16 }}>
              <h2 style={{ fontSize: '1rem' }}>{t('recentActivity')}</h2>
              {activity.length === 0
                ? <EmptyState msg={t('noActivity')} />
                : (
                  <ul>
                    {activity.map((row, i) => (
                      <li key={row.action + ':' + i}>
                        {row.labelKey ? t(row.labelKey) : row.action}
                        {row.role ? ' · ' + row.role : ''}
                        {row.when ? ' · ' + row.when : ''}
                      </li>
                    ))}
                  </ul>
                )}
            </section>
          </>
        )}
        {today && !loading && today.queue_length == null && <EmptyState msg={t('welcome') + ', ' + (user.display_name || user.username || '')} />}
      </AppShell>
    </RequireLogin>
  );
}

