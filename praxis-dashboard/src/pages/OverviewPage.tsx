import { AppShell } from '../components/AppShell';
import { Panel } from '../components/ui';
import { CurrentSessions } from '../components/CurrentSessions';
import { useHealth } from '../hooks/useHealth';
import { Link } from '../router';

export function OverviewPage() {
  const { health, error } = useHealth();
  return <AppShell title="Overview" subtitle="Your conversations at a glance">
    <div className="content overview-content">
      <section className="overview-hero"><div className="hero-copy"><div className="eyebrow">PRAXIS / VOICE INTEGRITY</div>
        <h1>Clarity in every<br /><span>conversation.</span></h1>
        <p>Follow a conversation as it happens, or review its recorded history.</p>
        <div className="hero-actions"><Link to="/sessions" className="btn hero-primary">View past sessions →</Link><Link to="/live" className="btn hero-secondary">Live monitoring →</Link></div>
      </div></section>
      <div style={{ marginTop: 24 }}><CurrentSessions /></div>
      <div style={{ marginTop: 24 }}><Panel title="Praxis connection"><div className="connection-state" role="status">
        <span className={`connection-dot ${error ? 'offline' : health ? 'online' : ''}`} />
        <strong>{error ? 'Not connected' : health ? 'Praxis connected' : 'Checking connection…'}</strong>
      </div></Panel></div>
      <div className="grid grid-2" style={{ marginTop: 20 }}>
        <Panel title="Service connection"><strong>{error ? 'Not connected' : health ? 'Connected' : 'Checking connection…'}</strong>
          <p className="small muted" style={{ marginTop: 8 }}>Check System Health for system availability.</p>
          <Link to="/health" className="text-link" style={{ marginTop: 12 }}>View system health →</Link>
        </Panel>
        <Panel title="Your sessions"><p className="small muted">Find and open conversations from Sessions.</p><Link to="/sessions" className="text-link" style={{ marginTop: 12 }}>Manage sessions →</Link></Panel>
      </div>
    </div>
  </AppShell>;
}
