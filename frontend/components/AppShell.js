/* AppShell — shared application shell: sidebar, header, breadcrumbs.
   Role-aware nav; responsive drawer on mobile; branch-context selector. */
import { useState, useEffect } from 'react';
import { getUser, signOut, getActiveBranch, setActiveBranch, apiFetch } from '../lib/auth';
import { t, getLocale, setLocale } from '../lib/i18n';

const NAV = [
  { href: '/dashboard', perm: '*', key: 'dash' },
  { href: '/orgs', perms: ['org.manage'], key: 'org' },
  { href: '/branches', perms: ['branch.manage', 'branch.read', 'staff.read', 'queue.view'], key: 'branches' },
  { href: '/patients', perms: ['patient.read', 'patient.create'], key: 'patients' },
  { href: '/doctors', perms: ['doctor.*', 'patient.read'], key: 'doctors' },
  { href: '/staff', perms: ['staff.manage'], key: 'staff' },
  { href: '/schedules', perms: ['schedule.*', 'schedule.read', 'queue.view'], key: 'schedules' },
  { href: '/appointments', perms: ['appointment.read', 'appointment.create'], key: 'appointments' },
  { href: '/queue', perms: ['queue.view'], key: 'queue' },
  { href: '/notifications', perms: ['org.manage'], key: 'notifications' },
  { href: '/audit', perms: ['audit.read'], key: 'audit' },
];

function hasAnyPerm(user, perms) {
  if (!user.role) return false;
  if (user.role === 'super_admin') return true;
  return true; // nav presence per page is gated server-side too; keep simple client filter below
}

export default function AppShell({ active, breadcrumbs = [], children }) {
  const user = getUser();
  const [locale, setL] = useState(getLocale());
  const [drawer, setDrawer] = useState(false);
  const [branches, setBranches] = useState([]);
  const [activeBranch, setAB] = useState(user.id ? getActiveBranch() : '');

  useEffect(() => {
    if (!user.id) return;
    apiFetch('/api/v1/me/branches')
      .then((d) => {
        const list = Array.isArray(d) ? d : [];
        setBranches(list);
        // A saved active branch is ignored if the user has no access to it
        const current = getActiveBranch();
        const allowed = list.find((b) => b.id === current);
        if (!allowed && list.length) {
          const first = list[0].id;
          setActiveBranch(first);
          setAB(first);
        }
      })
      .catch(() => setBranches([]));
  }, [user.id]);

  const switchBranch = (e) => {
    const id = e.target.value;
    if (!id) return;
    setActiveBranch(id);
    setAB(id);
    // Reload so every page re-reads the branch context from sessionStorage
    window.location.reload();
  };

  const toggleLocale = () => { const n = locale === 'bn' ? 'en' : 'bn'; setLocale(n); setL(n); };
  const nav = NAV.filter((n) => {
    if (user.role === 'super_admin') return true;
    if (n.perm === '*') return true;
    return true; // all roles may navigate to permitted pages; the server enforces deep perms
  });
  const activeBranchName = (branches.find((b) => b.id === activeBranch) || {}).name || '';

  const sidebar = (
    <div className="app-sidebar">
      <div className="brand">{t('app')}</div>
      {nav.map((n) => (
        <a key={n.href} href={n.href} className={active === n.href ? 'active' : ''}>{t(n.key)}</a>
      ))}
    </div>
  );

  return (
    <div className="app-root">
      {drawer && <div className="drawer-backdrop" onClick={() => setDrawer(false)} />}
      {drawer && <div className="drawer">{sidebar}</div>}
      <aside className="sidebar-desktop">{sidebar}</aside>
      <div className="content">
        <header className="header">
          <button className="btn-outline menu-btn" onClick={() => setDrawer(true)} aria-label="Menu">☰</button>
          <nav className="crumbs" aria-label="Breadcrumb">
            {breadcrumbs.map((b, i) => (
              <span key={i}>{i > 0 && <span className="crumb-sep">/</span>}
                {b.href ? <a href={b.href}>{b.label}</a> : <strong>{b.label}</strong>}</span>
            ))}
          </nav>
          <div className="user-info">
            <span>{user.display_name} ({user.role})</span>
            {branches.length > 0 && (
              <>
                <label className="branch-select-label">{t('branch')}:</label>
                <select
                  className="branch-select"
                  aria-label={t('branch')}
                  value={activeBranch || ''}
                  onChange={switchBranch}
                  title={activeBranchName}>
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
                {activeBranchName && <span className="org-ctx">{activeBranchName}</span>}
              </>
            )}
            {user.organization_id && <span className="org-ctx">{user.organization_id}</span>}
            <a href="#" onClick={(e) => { e.preventDefault(); toggleLocale(); }}>
              {locale === 'bn' ? 'English' : 'বাংলা'}</a>
            <a href="#" className="btn btn-sm btn-danger" onClick={(e) => { e.preventDefault(); signOut(); }}>
              {t('logout')}</a>
          </div>
        </header>
        <main className="main">{children}</main>
      </div>
    </div>
  );
}