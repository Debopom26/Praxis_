import { useSessionDirectory } from '../hooks/useSessionDirectory';
import { currentAnalysis, remoteLabel, sessionDuration } from '../lib/session';
import { formatDateTime } from '../lib/format';
import { Link } from '../router';
import { Panel } from './ui';

export function CurrentSessions() {
  const { rows, loading, error } = useSessionDirectory('', 0, true);
  return <Panel title="Current Sessions" action={<Link to="/live" className="text-link">Live monitoring →</Link>}>
    {error ? <p role="alert" className="note note-bad">Cannot check live sessions. Check the Praxis connection.</p>
      : loading ? <p role="status">Checking live sessions…</p>
      : !rows.length ? <p role="status" className="muted">No Active Sessions Currently</p>
      : <div className="current-session-list">{rows.map(row => {
        const analysis = row.latest_analysis;
        const fresh = currentAnalysis(row) !== null;
        return <div key={row.session_id} className="current-session-item">
          <div><strong>{row.owner_username || 'Account unavailable'}</strong><span className="small muted"> calling </span><strong>{remoteLabel(row)}</strong>
            <div className="small muted">Duration: {sessionDuration(row)}</div></div>
          <div><strong>{analysis ? `${analysis.experimental_score_0_100.toFixed(1)} / 100` : 'Awaiting analysis'}</strong>
            <div className="small muted">{analysis
              ? `${fresh ? 'Latest' : 'Earlier'}: ${analysis.action.replaceAll('_', ' ')} · ${row.latest_analysis_at ? formatDateTime(row.latest_analysis_at) : 'time unavailable'}`
              : 'No result yet'}</div></div>
          <Link className="btn btn-ghost btn-sm" to={`/live/${encodeURIComponent(row.session_id)}`}>View</Link>
        </div>;
      })}</div>}
  </Panel>;
}
