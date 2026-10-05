import { useEffect, useState } from 'react';
import { dashboardAnalysisHistory } from '../api/praxis';
import type { RecordedAnalysis } from '../api/praxis';
import { formatDateTime } from '../lib/format';
import { useAuth } from '../state/auth';
import { Panel } from './ui';

export function AnalysisHistory({ sessionId }: { sessionId: string }) {
  const { session, guest } = useAuth();
  const [offset, setOffset] = useState(0);
  const [results, setResults] = useState<RecordedAnalysis[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(false);
  useEffect(() => { setOffset(0); setResults([]); }, [sessionId]);
  useEffect(() => {
    if (guest || !session) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    const check = async () => {
      controller = new AbortController();
      try {
        const result = await dashboardAnalysisHistory(sessionId, session.accessToken, offset, controller.signal);
        if (!stopped) { setResults(result.results); setTotal(result.total); setError(false); }
      } catch { if (!stopped) setError(true); }
      finally { if (!stopped) timer = setTimeout(check, 3000); }
    };
    void check();
    return () => { stopped = true; clearTimeout(timer); controller?.abort(); };
  }, [sessionId, session?.accessToken, offset, guest]);

  return <Panel title="Recorded analysis">
    {error ? <p role="alert" className="note note-bad">Cannot load analysis history.</p>
      : results.length ? <>
        <div className="table-wrap"><table className="data-table session-directory">
          <thead><tr><th>Time</th><th>Experimental score</th><th>Guidance</th></tr></thead>
          <tbody>{results.map((item, index) => <tr key={item.timestamp + index}>
            <td data-label="Time">{formatDateTime(item.timestamp)}</td>
            <td data-label="Experimental score">{item.experimental_score_0_100.toFixed(1)} / 100</td>
            <td data-label="Guidance"><strong>{item.action.replaceAll('_', ' ')}</strong><div className="small muted">{item.message}</div></td>
          </tr>)}</tbody>
        </table></div>
        <div className="toolbar" style={{ marginTop: 16 }}>
          <button className="btn btn-ghost btn-sm" disabled={offset === 0}
            onClick={() => setOffset(value => Math.max(0, value - 20))}>Newer</button>
          <span className="small muted">{offset + 1}–{offset + results.length} of {total}</span>
          <button className="btn btn-ghost btn-sm" disabled={offset + results.length >= total}
            onClick={() => setOffset(value => value + 20)}>Older</button>
        </div>
      </> : <p className="muted">No recorded analysis for this session.</p>}
  </Panel>;
}
