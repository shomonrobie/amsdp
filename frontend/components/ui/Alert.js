/* Alert — error/success/empty/loading/permission states. */
import { t } from '../../lib/i18n';

export function ErrorAlert({ children }) {
  return <div className="error" role="alert">{children}</div>;
}

export function SuccessAlert({ children }) {
  return <div className="success">{children}</div>;
}

export function LoadingState({ msg }) {
  return <div className="loading">{msg || t('loading')}</div>;
}

export function EmptyState({ msg }) {
  return <div className="empty">{msg || t('empty')}</div>;
}

export function PermissionDenied({ msg }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
      <p style={{ color: '#c62828', fontWeight: 600 }}>{msg || t('permissionDenied')}</p>
    </div>
  );
}

export function RequireLogin({ children }) {
  const _u = typeof window === 'undefined' ? {} : (() => { try { return JSON.parse(sessionStorage.getItem('amsdp_user') || '{}'); } catch (e) { return {}; } })();
  if (!_u.id) {
    return <div className="card" style={{ maxWidth: 400, margin: '4rem auto', textAlign: 'center', padding: '2rem' }}>
      <h1 style={{ color: '#1a5c7a' }}>{t('app')}</h1>
      <p style={{ margin: '1rem 0', color: '#c62828' }}>{t('loginRequired')}</p>
      <a href="/" className="btn">{t('goLogin')}</a>
    </div>;
  }
  return children;
}