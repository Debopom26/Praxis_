/**
 * Route dispatch.
 *
 * Real data routes require a verified token. Guest routes render a separate static
 * preview without mounting authenticated pages or contacting the backend.
 */

import { useEffect } from 'react';

import { AuditPage } from './pages/AuditPage';
import { AccountsPage } from './pages/AccountsPage';
import { HealthPage } from './pages/HealthPage';
import { LivePage } from './pages/LivePage';
import { LoginPage } from './pages/LoginPage';
import { GuestPage } from './pages/GuestPage';
import { OverviewPage } from './pages/OverviewPage';
import { ProvenancePage } from './pages/ProvenancePage';
import { SessionsPage } from './pages/SessionsPage';
import { navigate, segments, useRoutePath } from './router';
import { AuthProvider, useAuth } from './state/auth';

function Routed() {
  const path = useRoutePath();
  const { session, guest } = useAuth();

  useEffect(() => {
    if (!session && !guest && path !== '/login') navigate('/login');
    if ((session || guest) && path === '/login') navigate('/overview');
  }, [session, guest, path]);

  if (guest) return <div className="route-view" key={path}><GuestPage /></div>;

  if (!session) return <div className="route-view route-view-login"><LoginPage /></div>;

  const head = segments(path)[0] ?? 'overview';
  let page;
  switch (head) {
    case 'accounts':
      page = session.role === 'admin' ? <AccountsPage /> : <OverviewPage />;
      break;
    case 'live':
      page = <LivePage />;
      break;
    case 'sessions':
      page = <SessionsPage />;
      break;
    case 'audit':
      page = <AuditPage />;
      break;
    case 'health':
      page = <HealthPage />;
      break;
    case 'provenance':
      page = <ProvenancePage />;
      break;
    default:
      page = <OverviewPage />;
  }

  return <div className="route-view" key={path}>{page}</div>;
}

export function App() {
  useEffect(() => {
    const keyboard = () => { document.documentElement.dataset.input = 'keyboard'; };
    const pointer = () => { document.documentElement.dataset.input = 'pointer'; };
    document.addEventListener('keydown', keyboard, true);
    document.addEventListener('pointerdown', pointer, true);
    return () => {
      document.removeEventListener('keydown', keyboard, true);
      document.removeEventListener('pointerdown', pointer, true);
    };
  }, []);

  return (
    <AuthProvider>
      <Routed />
    </AuthProvider>
  );
}
