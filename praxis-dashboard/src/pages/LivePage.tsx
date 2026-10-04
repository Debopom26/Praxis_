import { useEffect, useState } from 'react';
import { dashboardSession } from '../api/praxis';
import type { DashboardSession } from '../api/praxis';
import { AppShell } from '../components/AppShell';
import { CurrentSessions } from '../components/CurrentSessions';
import { AnalysisHistory } from '../components/AnalysisHistory';
import { SessionDirectory } from '../components/SessionDirectory';
import { Panel } from '../components/ui';
import { useSessionDirectory } from '../hooks/useSessionDirectory';
import { formatDateTime } from '../lib/format';
import { currentAnalysis, remoteLabel, sessionDuration } from '../lib/session';
import { Link, segments, useRoutePath } from '../router';
import { useAuth } from '../state/auth';

export function LivePage() {
  const id = segments(useRoutePath())[1];
  const { rows, loading, error } = useSessionDirectory();
  const { session } = useAuth();
  const [detail, setDetail] = useState<DashboardSession | null>(null);
  const [detailError, setDetailError] = useState(false);
  useEffect(() => {
    if (!id || !session) { setDetail(null); return; }
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    const check = async () => {
      controller = new AbortController();
      try { const result = await dashboardSession(id, session.accessToken, controller.signal);
        if (!stopped) { setDetail(result); setDetailError(false); }
      } catch { if (!stopped) { setDetail(null); setDetailError(true); } }
      finally { if (!stopped) timer = setTimeout(check, 3000); }
    };
    setDetail(null); setDetailError(false);
    void check();
    return () => { stopped = true; clearTimeout(timer); controller?.abort(); };
  }, [id, session?.accessToken]);
  const selected = id ? detail : rows.find(row => row.connected);
  const analysis = selected?.latest_analysis ?? null;
  const analysisFresh = selected ? currentAnalysis(selected) !== null : false;
  return <AppShell title="Live Monitoring" subtitle="Current call analysis">
    <div className="content"><div className="page-head"><h1 className="page-title">Live Monitoring</h1>
      <p className="small muted">Live status and the most recent usable analysis from Praxis.</p></div>
      <CurrentSessions />
      {error || detailError ? <p role="alert" className="note note-bad">Cannot load session details.</p> : loading && !id ? <p role="status">Loading session…</p> : id && !selected ? <p role="status">Checking session…</p> : selected ?
        <div style={{ marginTop: 20 }}><Panel title={selected.connected ? 'Active analysis' : 'Last recorded analysis'}>
          <div className="grid grid-2">
            <div><div className="eyebrow">Calling from</div><strong>{selected.owner_username || 'Account unavailable'}</strong></div>
            <div><div className="eyebrow">Calling</div><strong>{remoteLabel(selected)}</strong></div>
            <div><div className="eyebrow">Call duration</div><strong>{sessionDuration(selected)}</strong></div>
            <div><div className="eyebrow">Audio connection</div><strong>{selected.connected ? 'Connected' : 'Disconnected'}</strong></div>
          </div>
          <div style={{ marginTop: 20 }}>
            {analysis ? <><div className="eyebrow">{selected.connected && analysisFresh ? 'Latest experimental score' : 'Last recorded experimental score'}</div>
              <div className="risk-value">{analysis.experimental_score_0_100.toFixed(1)} <span>/ 100</span></div>
              <p className="note note-info"><strong>Recommended action: {analysis.action.replaceAll('_', ' ')}</strong><br />{analysis.message}</p>
              <p className="small muted">{analysis.regressor_status.replaceAll('_', ' ')} · Result recorded {selected.latest_analysis_at ? formatDateTime(selected.latest_analysis_at) : 'at an unknown time'}</p></>
              : <p role="status" className="note note-info">{selected.connected ? 'Awaiting usable audio and current analysis. No score is available.' : 'No analysis was recorded for this call.'}</p>}
          </div>
          {session?.role !== 'host' ? <Link to={`/audit/${encodeURIComponent(selected.session_id)}`} className="text-link">View audit trail →</Link> : null}
        </Panel><div style={{ marginTop: 20 }}><AnalysisHistory sessionId={selected.session_id} /></div></div> : null}
      <div style={{ marginTop: 20 }}><SessionDirectory title="Past call analysis" pastOnly /></div>
    </div>
  </AppShell>;
}
