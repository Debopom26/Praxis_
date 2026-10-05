import { useEffect, useState } from 'react';
import { praxisAudit } from '../api/praxis';
import type { PraxisAuditEvent } from '../api/praxis';
import { AppShell } from '../components/AppShell';
import { SessionDirectory } from '../components/SessionDirectory';
import { Panel } from '../components/ui';
import { formatDateTime } from '../lib/format';
import { Link, segments, useRoutePath } from '../router';
import { useAuth } from '../state/auth';

export function AuditPage() {
  const id = segments(useRoutePath())[1];
  const { session, guest } = useAuth();
  const [events, setEvents] = useState<PraxisAuditEvent[]>([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    if (guest || !id || !session || session.role === 'host') return;
    const controller = new AbortController();
    setLoading(true); setError(false);
    praxisAudit(id, session.accessToken, controller.signal)
      .then(result => { if (!controller.signal.aborted) setEvents(result); })
      .catch(() => { if (!controller.signal.aborted) setError(true); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [id, session?.accessToken, session?.role, reload, guest]);
  return <AppShell title="Audit Trail" subtitle="Recorded history of a conversation">
    <div className="content"><div className="page-head"><h1 className="page-title">Audit Trail</h1>
      <p className="small muted">Recorded events from the Praxis backend.</p></div>
      {session?.role === 'host' ? <Panel title="Audit access"><p>Audit history requires an administrator or analyst account.</p></Panel> : <>
        <SessionDirectory />
        {id ? <div style={{ marginTop: 20 }}><div className="toolbar" style={{ marginBottom: 16 }}>
          <Link to={`/live/${encodeURIComponent(id)}`} className="btn btn-ghost btn-sm">View session</Link>
          <button className="btn btn-primary btn-sm" disabled={loading} onClick={() => setReload(v => v + 1)}>Refresh history</button>
        </div>
          {error ? <p role="alert" className="note note-bad">Could not load audit history.</p> :
            <Panel title="Recorded events" action={<span className="small muted">{events.length} events</span>}>
              {loading && !events.length ? <p role="status">Loading events…</p> : !events.length ? <p>No events recorded yet.</p> :
                <ol className="audit-timeline">{[...events].sort((a,b) => a.timestamp.localeCompare(b.timestamp)).map(item =>
                  <li key={item.event_id}><time className="small muted">{formatDateTime(item.timestamp)}</time>
                    <div><strong>{item.event_type.replace(/[._]/g, ' ')}</strong>
                      {item.final_risk !== null ? <p className="small">Recorded risk: {item.final_risk} / 100</p> : null}
                      {item.action ? <p className="small">Action: {item.action.replaceAll('_', ' ')}</p> : null}
                      {item.reason_codes.length ? <p className="small muted">{item.reason_codes.join(', ')}</p> : null}
                    </div></li>)}</ol>}
            </Panel>}
        </div> : null}
      </>}
    </div>
  </AppShell>;
}
