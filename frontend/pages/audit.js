export async function getServerSideProps(){return{props:{}}}
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin, LoadingState, EmptyState, ErrorAlert } from '../components/ui/Alert';
import DataTable from '../components/ui/DataTable';
import { getUser, apiFetch, can, getActiveBranch } from '../lib/auth';
import { t } from '../lib/i18n';

export default function Audit(){
  const user = getUser();
  const branchId = getActiveBranch();
  const [events, setEvents] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [action, setAction] = React.useState('');
  const [actor, setActor] = React.useState('');
  const [target, setTarget] = React.useState('');

  const load = () => {
    setLoading(true); setError('');
    const params = new URLSearchParams();
    if (action) params.set('action', action);
    if (actor) params.set('actor_id', actor);
    if (target) params.set('target_type', target);
    if (branchId) params.set('branch_id', branchId);
    apiFetch('/api/v1/dashboard/audit?' + params.toString())
      .then((d) => { setEvents(d || []); setLoading(false); })
      .catch((e) => { setError('Audit load failed: ' + (e.message || e)); setLoading(false); });
  };

  React.useEffect(load, [branchId]);

  if (!can('audit.read')) {
    return (<RequireLogin><AppShell active="/audit" breadcrumbs={[{ label: t('audit') }]}>
      <h1 className="page-title">{t('audit')}</h1>
      <div className="card" style={{ textAlign: 'center', padding: '2rem' }}><p style={{ color: '#c62828' }}>{t('permissionDenied')}</p></div>
    </AppShell></RequireLogin>);
  }

  return (
    <RequireLogin>
      <AppShell active="/audit" breadcrumbs={[{ label: t('dash'), href: '/dashboard' }, { label: t('audit') }]}>
        <h1 className="page-title">{t('audit')}</h1>
        <div className="flex mb-2 flex-wrap">
          <input placeholder={t('action')} value={action} onChange={(e) => setAction(e.target.value)} style={{ width: 220 }} />
          <input placeholder={t('role') + ' ID'} value={actor} onChange={(e) => setActor(e.target.value)} style={{ width: 180 }} />
          <input placeholder={t('entity')} value={target} onChange={(e) => setTarget(e.target.value)} style={{ width: 160 }} />
          <button className="btn" onClick={load} style={{ width: 'auto' }}>{t('search')}</button>
        </div>
        {error && <ErrorAlert>{error}</ErrorAlert>}
        {loading ? <LoadingState /> : events.length === 0 ? <EmptyState msg={t('empty')} /> : (
          <div className="table-wrap">
            <DataTable rowKey="id" rows={events}
              columns={[
                { render: (r) => (r.timestamp || '').slice(0, 19).replace('T', ' '), label: t('time') },
                { key: 'action', label: t('action') },
                { key: 'target_type', label: t('entity') },
                { key: 'actor_role', label: t('roleLabel') },
                { render: (r) => (r.before ? JSON.stringify(r.before) : ''), label: t('before') },
                { render: (r) => (r.after ? JSON.stringify(r.after) : ''), label: t('after') },
                { key: 'reason', label: t('reason') },
              ]}
            />
          </div>
        )}
      </AppShell>
    </RequireLogin>
  );
}