/**
 * Application shell: fixed sidebar, sticky header, content column
 * (docs/design.md Sec.5.1).
 */

import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';

import type { StreamStatus } from './ConnectionBanner';
import { Link, useRoutePath } from '../router';
import { useAuth } from '../state/auth';
import { BrandLogo } from './BrandLogo';
import { useColorMode } from '../state/colorMode';
import { ConnectionPill } from './ConnectionBanner';
import {
  IconActivity,
  IconFileText,
  IconGrid,
  IconHeart,
  IconInfo,
  IconList,
  IconLock,
  IconLogout,
  IconMenu,
  IconX,
} from './Icons';

interface NavEntry {
  to: string;
  label: string;
  icon: ReactNode;
}

const SECTIONS: ReadonlyArray<{ label: string; items: ReadonlyArray<NavEntry> }> = [
  {
    label: 'Monitoring',
    items: [
      { to: '/overview', label: 'Overview', icon: <IconGrid /> },
      { to: '/live', label: 'Live Monitoring', icon: <IconActivity /> },
    ],
  },
  {
    label: 'Records',
    items: [
      { to: '/sessions', label: 'Sessions', icon: <IconList /> },
      { to: '/audit', label: 'Audit Trail', icon: <IconFileText /> },
    ],
  },
  {
    label: 'Platform',
    items: [
      { to: '/accounts', label: 'Accounts', icon: <IconLock /> },
      { to: '/health', label: 'System Health', icon: <IconHeart /> },
      { to: '/provenance', label: 'Help', icon: <IconInfo /> },
    ],
  },
];

function activeSection(path: string): string {
  const match = SECTIONS.flatMap((section) => section.items).find(
    (item) => path === item.to || path.startsWith(`${item.to}/`),
  );
  return match ? match.to : '';
}

export function AppShell({
  title,
  subtitle,
  streamStatus,
  children,
}: {
  title: string;
  subtitle?: string;
  streamStatus?: StreamStatus;
  children: ReactNode;
}) {
  const path = useRoutePath();
  const { session, guest, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const { darkMode, toggleColorMode } = useColorMode();
  const current = activeSection(path);
  const menuRef = useRef<HTMLButtonElement>(null);
  const asideRef = useRef<HTMLElement>(null);
  const mainRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mobile = matchMedia('(max-width: 860px)');
    const sync = () => {
      if (asideRef.current) asideRef.current.inert = mobile.matches && !menuOpen;
      if (mainRef.current) mainRef.current.inert = mobile.matches && menuOpen;
      if (!mobile.matches) setMenuOpen(false);
    };
    sync();
    mobile.addEventListener('change', sync);
    return () => mobile.removeEventListener('change', sync);
  }, [menuOpen]);

  useEffect(() => {
    if (!menuOpen) return;
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    asideRef.current?.querySelector<HTMLAnchorElement>('[aria-current="page"]')?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false);
        if (mainRef.current) mainRef.current.inert = false;
        menuRef.current?.focus();
      }
      if (event.key === 'Tab') {
        const controls = asideRef.current?.querySelectorAll<HTMLElement>('a[href], button');
        const first = controls?.[0];
        const last = controls?.[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', onKey);
    return () => { document.body.style.overflow = oldOverflow; document.removeEventListener('keydown', onKey); };
  }, [menuOpen]);

  // Close the drawer whenever the route changes, so a tap-through does not leave it
  // covering the new page on a phone.
  useEffect(() => {
    setMenuOpen(false);
  }, [path]);

  const initials = (guest ? 'Guest' : session?.username ?? '?').slice(0, 2).toUpperCase();



  return (
    <div className="shell">
      <a className="skip-link" href="#main-content" onClick={(event) => { event.preventDefault(); document.getElementById('main-content')?.focus(); }}>Skip to content</a>
      <aside id="praxis-navigation" ref={asideRef} className={`sidebar atd-glass__rail${menuOpen ? ' open' : ''}`} aria-label="Workspace navigation">
        <Link to="/overview" className="sidebar-logo atd-glass__brand" aria-label="Praxis — Overview" onClick={() => setMenuOpen(false)}>
          <BrandLogo />
        </Link>
        <button type="button" className="drawer-close icon-btn" aria-label="Close navigation" onClick={() => { setMenuOpen(false); if (mainRef.current) mainRef.current.inert = false; menuRef.current?.focus(); }}><IconX /></button>

        <span className="atd-glass__hairline" aria-hidden="true" />
        <nav className="sidebar-nav atd-glass__dock" aria-label="Main navigation">
          {SECTIONS.map((section) => (
            <div key={section.label}>
              <div className="nav-section-label">{section.label}</div>
              {section.items.filter(item => item.to !== '/accounts' || guest || session?.role === 'admin').map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`nav-item atd-glass__item${current === item.to ? ' active' : ''}`}
                  aria-current={current === item.to ? 'page' : undefined}
                >
                  <span className="nav-icon atd-glass__icon">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          ))}
        </nav>

        <span className="atd-glass__hairline" aria-hidden="true" />
        <div className="sidebar-bottom">
          <div className="sidebar-tenant">
            Workspace
            <br />
            <strong>{guest ? 'Guest preview' : session?.tenantId ?? '\u2014'}</strong>
          </div>
          <div className="theme-control">
            <span className="theme-control-label">Appearance</span>
            <button type="button" className="theme-toggle" role="switch" aria-checked={darkMode} aria-label="Dark mode" onClick={toggleColorMode}>
              <svg className="theme-toggle-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                {darkMode ? <><path d="M20.5 15.2A8.5 8.5 0 0 1 8.8 3.5 8.5 8.5 0 1 0 20.5 15.2Z" /><path d="M16 3v4M14 5h4" /></> : <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></>}
              </svg>
              <span className="theme-toggle-label">Dark mode</span>
              <span className="theme-switch-track" aria-hidden="true"><span /></span>
            </button>
          </div>
          <div className="sidebar-profile">
            <div className="avatar">{initials}</div>
            <div className="grow">
              <div className="who truncate">{guest ? 'Guest' : session?.username ?? 'unknown'}</div>
              <div className="role">{guest ? 'Read-only preview' : session?.role ?? '\u2014'}</div>
            </div>
            <button
              type="button"
              className="icon-btn"
              onClick={signOut}
              title={guest ? 'Exit guest preview' : 'Sign out'}
              aria-label={guest ? 'Exit guest preview' : 'Sign out'}
            >
              <IconLogout />
            </button>
          </div>
        </div>
      </aside>

      <div
        className={menuOpen ? 'overlay show' : 'overlay'}
        onClick={() => setMenuOpen(false)}
        aria-hidden="true"
      />

      <div className="main" ref={mainRef}>
        <header className="topheader">
          <div className="header-left">
            <button
              ref={menuRef}
              type="button"
              className="hamburger"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
              aria-expanded={menuOpen}
              aria-controls="praxis-navigation"
            >
              {menuOpen ? <IconX /> : <IconMenu />}
            </button>
            <div className="grow">
              <div className="header-title truncate">{title}</div>
              {subtitle ? <div className="header-sub truncate">{subtitle}</div> : null}
            </div>
          </div>
          <div className="header-right">
            <span className="workspace-chip"><span className="workspace-orbit" aria-hidden="true" /> {guest ? 'Guest · Not connected' : session?.username ?? 'Workspace'}</span>
            {streamStatus ? <ConnectionPill status={streamStatus} /> : null}
          </div>
        </header>

        <main id="main-content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
