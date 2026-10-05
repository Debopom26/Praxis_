/**
 * Route dispatch.
 *
 * Every route below is reachable only with a verified token. The console holds no local
 * notion of who may see what: the backend answers that on each request, and a session
 * belonging to another tenant resolves as not found.
 */

import { useEffect } from 'react';

import { AuditPage } from './pages/AuditPage';
import { AccountsPage } from './pages/AccountsPage';
import { HealthPage } from './pages/HealthPage';
import { LivePage } from './pages/LivePage';
import { LoginPage } from './pages/LoginPage';
import { OverviewPage } from './pages/OverviewPage';
import { ProvenancePage } from './pages/ProvenancePage';
import { SessionsPage } from './pages/SessionsPage';
import { navigate, segments, useRoutePath } from './router';
import { AuthProvider, useAuth } from './state/auth';

function Routed() {
  const path = useRoutePath();
  const { session } = useAuth();

  useEffect(() => {
    if (!session && path !== '/login') navigate('/login');
    if (session && path === '/login') navigate('/overview');
  }, [session, path]);

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
