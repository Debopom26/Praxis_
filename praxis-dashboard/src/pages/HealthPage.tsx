import { AppShell } from '../components/AppShell';
import { Panel } from '../components/ui';
import { useHealth } from '../hooks/useHealth';
import { formatDateTime } from '../lib/format';

export function HealthPage() {
  const { health, checkedAt, error, loading, refresh } = useHealth();
  const okay = !!health && health.status === 'AVAILABLE' && !error;
  return <AppShell title="System Health" subtitle="Connection and system availability">
    <div className="content"><div className="page-head row between wrap gap-12">
      <div><h1 className="page-title">System Health</h1><p className="small muted">Connection and system availability</p></div>
      <button className="btn btn-ghost" disabled={loading} onClick={refresh}>{loading ? 'Checking…' : 'Refresh status'}</button>
    </div>
    <div className="grid grid-3">
      <Panel title="Connection"><strong>{error ? 'Not connected' : health ? 'Connected' : 'Checking…'}</strong></Panel>
      <Panel title="API and database"><strong role="status">{loading && !health && !error ? 'Checking…' : okay ? 'Available' : 'Unavailable'}</strong><p className="small muted">Model states are shown below separately.</p></Panel>
      <Panel title="Last checked"><span className="small">{checkedAt ? formatDateTime(checkedAt) : '—'}</span></Panel>
    </div></div>
    {health ? <div className="content"><Panel title="Components"><div className="table-wrap"><table className="data-table"><thead><tr><th>Service or model</th><th>Status</th><th>Details</th></tr></thead><tbody>
      {Object.entries(health.components).map(([name, item]) => <tr key={name}><td>{name}</td><td>{item.status}</td><td>{item.reason_codes.join(', ') || item.version || '—'}</td></tr>)}
    </tbody></table></div></Panel><div style={{ marginTop: 20 }}><Panel title="Artifacts"><div className="table-wrap"><table className="data-table"><thead><tr><th>Artifact</th><th>State</th><th>Details</th></tr></thead><tbody>
      {health.artifacts.map(item => <tr key={item.module}><td>{item.module}</td><td>{item.state}</td><td>{item.reason_codes.join(', ') || item.version || '—'}</td></tr>)}
    </tbody></table></div></Panel></div></div> : null}
  </AppShell>;
}
