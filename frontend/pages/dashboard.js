export async function getServerSideProps(){return{props:{}}}
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin } from '../components/ui/Alert';
import { getUser, apiFetch, getActiveBranch } from '../lib/auth';
import { t } from '../lib/i18n';
import { LoadingState, EmptyState, ErrorAlert } from '../components/ui/Alert';

export default function Dashboard(){
  const user = getUser();
  const branchId = getActiveBranch();
  const [today, setToday] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    setLoading(true);
    const qs = branchId ? '?branch_id=' + encodeURIComponent(branchId) : '';
    apiFetch('/api/v1/dashboard/today' + qs)
      .then((d) => { setToday(d); setLoading(false); })
      .catch((e) => { setError(String(e && e.message || e)); setLoading(false); });
  }, [branchId]);

  const cards = today ? [
    { label: t('booked'), value: today.scheduled || 0 },
    { label: t('checkedIn'), value: today.checked_in || 0 },
    { label: t('waiting'), value: today.checked_in || 0 },
    { label: t('completedT'), value: today.completed || 0 },
    { label: t('cancelledT'), value: today.cancelled || 0 },
    { label: t('noShow'), value: today.no_show || 0 },
  ] : [];

  return (
    <RequireLogin>
      <AppShell active="/dashboard" breadcrumbs={[{ label: t('dash') }]}>
        <h1 className="page-title">{t('dash')}</h1>
        {error && <ErrorAlert>{error}</ErrorAlert>}
        {loading && <LoadingState />}
        {today && (
          <div className="flex flex-wrap">
            {cards.map((c) => (
              <div key={c.label} className="card" style={{ minWidth: 140, marginRight: 8, textAlign: 'center' }}>
                <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#1a5c7a' }}>{c.value}</div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>{c.label}</div>
              </div>
            ))}
          </div>
        )}
        {today && !loading && today.queue_length == null && <EmptyState msg={t('welcome') + ', ' + (user.display_name || user.username || '')} />}
      </AppShell>
    </RequireLogin>
  );
}