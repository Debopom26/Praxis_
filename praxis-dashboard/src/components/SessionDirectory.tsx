import { useId, useState } from 'react';
import { useSessionDirectory } from '../hooks/useSessionDirectory';
import { formatDateTime } from '../lib/format';
import { remoteLabel, sessionDuration } from '../lib/session';
import { Link } from '../router';
import { useAuth } from '../state/auth';
import { Panel } from './ui';

export function SessionDirectory({ title = 'Look up sessions', pastOnly = false }: { title?: string; pastOnly?: boolean }) {
  const id = useId();
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const { session, guest } = useAuth();
  const { rows, total, loading, error } = useSessionDirectory(query, offset, pastOnly ? false : undefined);
  return <Panel title={title}>
    <form className="toolbar session-search" onSubmit={e => { e.preventDefault(); setOffset(0); setQuery(input.trim()); }}>
      <div className="field grow"><label htmlFor={id}>Contact name or number</label>
        <input id={id} className="input" type="search" placeholder="Search by name or phone number" value={input} onChange={e => setInput(e.target.value)} />
      </div>
      <button type="submit" className="btn btn-primary">Look up sessions</button>
      {query ? <button type="button" className="btn btn-ghost" onClick={() => { setInput(''); setQuery(''); setOffset(0); }}>Clear</button> : null}
    </form>
    {error ? <p role="alert" className="note note-bad">Could not load sessions. Check the connection and try again.</p> : loading ? <p role="status">Loading sessions…</p> : rows.length ? <>
      <div className="table-wrap"><table className="data-table session-directory"><thead><tr><th>Calling from</th><th>Calling</th><th>Duration</th><th>Started</th><th>Analysis</th><th>Open</th></tr></thead>
        <tbody>{rows.map(row => { const analysis = row.latest_analysis; return <tr key={row.session_id}>
          <td data-label="Calling from">{row.owner_username || 'Account unavailable'}</td>
          <td data-label="Calling">{remoteLabel(row)}<div className="small muted">{row.connected ? 'Live call' : row.ended_at ? 'Ended' : 'No audio connection'}</div></td>
          <td data-label="Duration">{sessionDuration(row)}</td>
          <td data-label="Started">{formatDateTime(row.call_connected_at || row.created_at)}</td>
          <td data-label="Analysis">{analysis ? <>{row.connected ? 'Latest' : 'Last recorded'} experimental score: {analysis.experimental_score_0_100.toFixed(1)} / 100<div className="small muted">{analysis.action.replaceAll('_', ' ')} · {row.latest_analysis_at ? formatDateTime(row.latest_analysis_at) : 'Time unavailable'}</div></> : 'No recorded analysis'}</td>
          <td data-label="Open"><div className="toolbar"><Link className="btn btn-ghost btn-sm" to={`/live/${encodeURIComponent(row.session_id)}`}>View session</Link>{session?.role !== 'host' ? <Link className="btn btn-ghost btn-sm" to={`/audit/${encodeURIComponent(row.session_id)}`}>Audit</Link> : null}</div></td>
        </tr>; })}</tbody></table></div>
      <div className="toolbar" style={{ marginTop: 16 }}>
        <button className="btn btn-ghost btn-sm" disabled={offset === 0} onClick={() => setOffset(v => Math.max(0, v - 20))}>Previous</button>
        <span className="small muted">{offset + 1}–{offset + rows.length} of {total}</span>
        <button className="btn btn-ghost btn-sm" disabled={offset + rows.length >= total} onClick={() => setOffset(v => v + 20)}>Next</button>
      </div>
    </> : <p className="muted">{query ? 'No sessions match that name or number.' : guest ? 'No sessions found.' : 'No sessions available yet.'}</p>}
  </Panel>;
}
