import { AppShell } from '../components/AppShell';
import { SessionDirectory } from '../components/SessionDirectory';

export function SessionsPage() {
  return <AppShell title="Sessions" subtitle="Review and look up analysis sessions">
    <div className="content"><div className="page-head"><h1 className="page-title">Sessions</h1>
      <p className="small muted">Review conversations and search by caller name or number.</p></div>
      <SessionDirectory title="Sessions" />
    </div>
  </AppShell>;
}
