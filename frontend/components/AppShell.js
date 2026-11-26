/* AppShell — shared application shell: sidebar, header, breadcrumbs.
   Role-aware nav; responsive drawer on mobile; branch-context selector. */
import { useState, useEffect } from 'react';
import { getUser, signOut, getActiveBranch, setActiveBranch, apiFetch, can } from '../lib/auth';
import { tIn, getLocale, setLocale } from '../lib/i18n';

const NAV = [
  { href: '/dashboard', perm: '*', key: 'dash' },
  { href: '/orgs', perms: ['org.manage'], key: 'org' },
  { href: '/branches', perms: ['branch.manage', 'branch.read', 'staff.read', 'queue.view'], key: 'branches' },
  { href: '/facilities', perms: ['facility.read'], key: 'facilities' },
  { href: '/patients', perms: ['patient.read', 'patient.create'], key: 'patients' },
  { href: '/doctors', perms: ['doctor.*', 'patient.read'], key: 'doctors' },
  { href: '/staff', perms: ['staff.manage'], key: 'staff' },
  { href: '/schedules', perms: ['schedule.*', 'schedule.read', 'queue.view'], key: 'schedules' },
  { href: '/appointments', perms: ['appointment.read', 'appointment.create'], key: 'appointments' },
  { href: '/queue', perms: ['queue.view'], key: 'queue' },
  { href: '/reports', perms: ['appointment.read'], key: 'reports' },
  { href: '/queue-displays', perms: ['queue.display.manage'], key: 'queueDisplays' },
  { href: '/voice-packs', perms: ['org.read'], key: 'voicePacks' },
  { href: '/notifications', perms: ['org.manage'], key: 'notifications' },
  { href: '/audit', perms: ['audit.read'], key: 'audit' },
];

/**
 * Nav visibility is a convenience, not an authorization boundary: every page and
 * every endpoint checks the capability again server-side.  Hiding an entry the
 * role cannot read keeps the menu honest (a receptionist sees Facilities but not
 * Staff), and a role that reaches a page by URL still gets the server's answer.
 */
function visible(user, item) {
  if (!user.role) return false;
  if (item.perm === '*') return true;
  return (item.perms || []).some((p) => can(p));
}

export default function AppShell({ active, breadcrumbs = [], children }) {
  // The session and the preferred locale live in sessionStorage, which the server
  // cannot see.  Reading them during render made the first client pass disagree
  // with the server HTML, so React threw the server tree away (error #418 →
  // #423) and the shell flashed empty.  They are read once after mount instead:
  // server HTML and the first client render now agree, and the shell fills in.
  const [user, setUser] = useState({});
  const [locale, setL] = useState('bn');
  const [drawer, setDrawer] = useState(false);
  const [branches, setBranches] = useState([]);
  const [activeBranch, setAB] = useState('');

  useEffect(() => {
    const session = getUser();
    setUser(session);
    setL(getLocale());
    if (session.id) setAB(getActiveBranch());
  }, []);

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
  const nav = NAV.filter((n) => visible(user, n));
  const activeBranchName = (branches.find((b) => b.id === activeBranch) || {}).name || '';

  const sidebar = (
    <div className="app-sidebar">
      <div className="brand">{tIn(locale, 'app')}</div>
      {nav.map((n) => (
        <a key={n.href} href={n.href} className={active === n.href ? 'active' : ''}>{tIn(locale, n.key)}</a>
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
                <label className="branch-select-label">{tIn(locale, 'branch')}:</label>
                <select
                  className="branch-select"
                  aria-label={tIn(locale, 'branch')}
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
              {tIn(locale, 'logout')}</a>
          </div>
        </header>
        <main className="main">{children}</main>
      </div>
    </div>
  );
}