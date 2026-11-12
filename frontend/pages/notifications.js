export async function getServerSideProps(){return{props:{}}}
/* Organization notification settings (Sequence 3, WP6).
   WhatsApp/SMS toggles, reminder timing and provider health.

   Two hard rules are visible in this page's shape:
   * the provider list comes from the server's allow-list — the UI cannot
     invent or point the outbox at an unapproved provider;
   * no secret is ever rendered. Only booleans such as
     ``credentials_configured`` and the platform capability flags are shown;
     the credential itself stays server-side. */
import React from 'react';
import AppShell from '../components/AppShell';
import { RequireLogin, LoadingState, ErrorAlert, SuccessAlert, PermissionDenied } from '../components/ui/Alert';
import StatusBadge from '../components/ui/StatusBadge';
import { getUser, apiFetch, can } from '../lib/auth';
import { t, fmtDate } from '../lib/i18n';

const CHANNELS = ['whatsapp', 'sms'];
const COUNTERS = ['pending', 'retry_scheduled', 'sent', 'delivered', 'failed', 'cancelled'];

export default function Notifications(){
  const user = getUser();
  const orgId = user.organization_id || '';
  const canManage = can('org.manage');
  const [config, setConfig] = React.useState(null);
  const [status, setStatus] = React.useState(null);
  const [form, setForm] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [notice, setNotice] = React.useState('');

  const base = '/api/v1/orgs/' + encodeURIComponent(orgId);

  const load = () => {
    if (!orgId || !canManage) { setLoading(false); return; }
    setLoading(true); setError('');
    Promise.all([
      apiFetch(base + '/notification-config'),
      apiFetch(base + '/notification-status'),
    ]).then(([cfg, st]) => {
      setConfig(cfg);
      setStatus(st);
      setForm({
        whatsapp_enabled: cfg.whatsapp.enabled,
        sms_enabled: cfg.sms.enabled,
        whatsapp_provider: cfg.whatsapp.provider,
        sms_provider: cfg.sms.provider,
        reminder_lead_minutes: cfg.reminder_lead_minutes,
      });
      setLoading(false);
    }).catch((e) => { setError('Load failed: ' + (e.message || e)); setLoading(false); });
  };

  React.useEffect(() => { load(); }, [orgId]);

  const set = (key, value) => setForm(Object.assign({}, form, { [key]: value }));

  const save = async () => {
    if (saving || !form) return;             // duplicate-submit guard
    setSaving(true); setError(''); setNotice('');
    try {
      const updated = await apiFetch(base + '/notification-config',
        { method: 'PUT', body: JSON.stringify(form) });
      setConfig(updated);
      setNotice(t('savedChanges'));
      const st = await apiFetch(base + '/notification-status');
      setStatus(st);
    } catch (e) { setError('Save failed: ' + e.message); }
    finally { setSaving(false); }
  };

  if (!canManage) {
    return (
      <RequireLogin>
        <AppShell active="/notifications" breadcrumbs={[{ label: t('dash'), href: '/dashboard' }, { label: t('notifications') }]}>
          <h1 className="page-title">{t('notificationSettings')}</h1>
          <PermissionDenied />
        </AppShell>
      </RequireLogin>
    );
  }

  const providers = (config && config.platform && config.platform.implemented_providers) || [];
  const leads = (config && config.allowed_lead_minutes) || [];
  const integration = (status && status.platform) || (config && config.platform) || {};
  const label = (ch) => (ch === 'whatsapp' ? 'WhatsApp' : 'SMS');

  return (
    <RequireLogin>
      <AppShell active="/notifications" breadcrumbs={[{ label: t('dash'), href: '/dashboard' }, { label: t('notifications') }]}>
        <div className="flex justify-between mb-2">
          <h1 className="page-title">{t('notificationSettings')}</h1>
          <button className="btn" onClick={save} disabled={saving || !form}>
            {saving ? t('pleaseWait') : t('save')}</button>
        </div>
        <p className="org-ctx">{t('notificationHint')} {t('settingsFor')} {orgId}</p>
        {error && <ErrorAlert>{error}</ErrorAlert>}
        {notice && <SuccessAlert>{notice}</SuccessAlert>}
        {loading || !form ? <LoadingState /> : (
          <div>
            <div className="card">
              <h3>{t('providerStatus')}</h3>
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>{t('channel')}</th><th>{t('enabled')}</th><th>{t('provider')}</th>
                    <th>{t('status')}</th>
                  </tr></thead>
                  <tbody>
                    {CHANNELS.map((ch) => (
                      <tr key={ch}>
                        <td>{label(ch)}</td>
                        <td>
                          <input type="checkbox" checked={!!form[ch + '_enabled']}
                            aria-label={label(ch) + ' ' + t('enabled')}
                            onChange={(e) => set(ch + '_enabled', e.target.checked)} />
                        </td>
                        <td>
                          <select value={form[ch + '_provider'] || 'mock'}
                            aria-label={label(ch) + ' ' + t('provider')}
                            onChange={(e) => set(ch + '_provider', e.target.value)}>
                            {providers.map((p) => <option key={p} value={p}>{p}</option>)}
                          </select>
                        </td>
                        <td>
                          <StatusBadge status={config[ch].status} label={config[ch].status} />
                          {config[ch].credentials_configured
                            ? <span className="org-ctx" title={t('credentialsNote')}> ••••</span> : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="org-ctx">{t('platformProviders')}: {providers.join(', ') || '—'}</p>
              <p className="org-ctx">{t('credentialsNote')}</p>
            </div>

            <div className="card">
              <h3>{t('reminderTiming')}</h3>
              <div className="form-group" style={{ maxWidth: 280 }}>
                <label>{t('reminderTiming')}</label>
                <select value={form.reminder_lead_minutes}
                  aria-label={t('reminderTiming')}
                  onChange={(e) => set('reminder_lead_minutes', Number(e.target.value))}>
                  {leads.map((m) => (
                    <option key={m} value={m}>{m} {t('minutesBefore')}</option>
                  ))}
                </select>
              </div>
              <p className="org-ctx">
                {t('channel')} cooldown: {config.cooldown_minutes} min ·
                {t('lastAttempt')}: {config.updated_at ? fmtDate(config.updated_at) : '—'}
              </p>
            </div>

            <div className="card">
              <h3>{t('last24h')}</h3>
              {integration.integration_status === 'mock-only' && (
                <p className="org-ctx">{t('mockOnly')}</p>
              )}
              <p className="org-ctx">{t('integrationStatus')}: {integration.integration_status || '—'}
                {' · '}{t('platformProviders')}: {(integration.implemented_providers || []).join(', ') || '—'}
                {' / '}declared: {(integration.declared_providers || []).join(', ') || '—'}</p>
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>{t('status')}</th><th>{t('last24h')}</th><th>{t('lifetime')}</th>
                  </tr></thead>
                  <tbody>
                    {COUNTERS.map((c) => (
                      <tr key={c}>
                        <td>{c.replace('_', ' ')}</td>
                        <td>{(status.last_24h || {})[c] || 0}</td>
                        <td>{(status.lifetime || {})[c] || 0}</td>
                      </tr>
                    ))}
                    <tr>
                      <td><strong>{t('total')}</strong></td>
                      <td><strong>{(status.last_24h || {}).total || 0}</strong></td>
                      <td><strong>{(status.lifetime || {}).total || 0}</strong></td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <h4>{t('latestMessage')}</h4>
              {status.latest_message ? (
                <p className="org-ctx">
                  {status.latest_message.type} · {status.latest_message.channel} ·{' '}
                  <StatusBadge status={status.latest_message.status} label={status.latest_message.status} />{' '}
                  {t('sent')}: {status.latest_message.sent_at ? fmtDate(status.latest_message.sent_at) : '—'} ·{' '}
                  {t('delivered')}: {status.latest_message.delivered_at ? fmtDate(status.latest_message.delivered_at) : '—'}
                  {status.latest_message.error ? ' · ' + status.latest_message.error : ''}
                </p>
              ) : <p className="org-ctx">{t('empty')}</p>}
              <p className="org-ctx">{t('sent')} ≠ {t('delivered')} — {t('mockOnly')}</p>
            </div>
          </div>
        )}
      </AppShell>
    </RequireLogin>
  );
}
