import { AppShell } from '../components/AppShell';
import { ActionPill, Panel } from '../components/ui';
import { ACTION_DESCRIPTION } from '../api/types';
import { Link, segments, useRoutePath } from '../router';
import { useAuth } from '../state/auth';

const SECTIONS: Record<string, { title: string; description: string; panels: [string, string][] }> = {
  overview: {
    title: 'Overview', description: 'Explore how Praxis brings conversation evidence into one workspace.',
    panels: [
      ['Current Sessions', 'No live sessions are displayed in guest preview. Sign in when the server is online to see callers, called contacts, call duration and active risk analysis.'],
      ['Your sessions', 'Open Sessions to learn how conversation history and evidence are reviewed.'],
    ],
  },
  live: {
    title: 'Live Monitoring', description: 'Understand the signals behind an ongoing conversation.',
    panels: [
      ['Active risk analysis', 'Authenticated calls supply audio to Praxis. The backend returns risk and policy guidance as new speech is analysed. No live score is generated in this preview.'],
      ['Evidence', 'Audio authenticity, speaker verification, linguistic signals, context and prosody contribute available evidence. Missing evidence is reported explicitly. An AI voice alone is not proof of a scam.'],
    ],
  },
  sessions: {
    title: 'Sessions', description: 'Review conversations and their analysis history.',
    panels: [
      ['Session history', 'Signed-in users can open their organization’s recorded sessions to review call details, analysis windows and policy decisions. Guest access exposes no private records.'],
      ['Retention', 'Stored evidence depends on organization retention settings. Raw audio is not retained by default.'],
    ],
  },
  audit: {
    title: 'Audit Trail', description: 'Trace changes and decisions within your organization.',
    panels: [['Protected audit records', 'Sign in with an authorized organization account to inspect actual audit events. This preview does not fetch or create audit records.']],
  },
  health: {
    title: 'System Health', description: 'Understand service and model availability.',
    panels: [['Not checked in guest preview', 'Guest exploration works without the Praxis backend. API, database, model and artifact health are not checked here. Sign in to see actual readiness and unavailable components.']],
  },
  provenance: {
    title: 'Help', description: 'A quick tour of the Praxis workspace.',
    panels: [
      ['Explore the workspace', 'Use Overview for current calls, Live Monitoring for analysis, Sessions for recorded history, Audit Trail for traceability and System Health for service readiness.'],
      ['Connect a real call', 'Sign in with the same organization account as the Praxis caller app. Real calls, account management and private evidence require an online backend and authentication.'],
    ],
  },
};

export function GuestPage() {
  const route = segments(useRoutePath())[0] ?? 'overview';
  const section = (SECTIONS[route] ?? SECTIONS.overview)!;
  const { signOut } = useAuth();
  return <AppShell title={section.title} subtitle="Guest preview · No backend connection required">
    <div className="content overview-content">
      <div className="note" role="note" style={{ marginBottom: 24 }}>
        <div><strong>Guest preview</strong><p>Explore the workspace without signing in. Live analysis and private records are available after sign-in.</p>
          <button type="button" className="text-link" onClick={signOut}>Go to sign in →</button>
        </div>
      </div>
      <section className="overview-hero"><div className="hero-copy">
        <div className="eyebrow">PRAXIS / VOICE INTEGRITY</div>
        <h1>{route === 'overview' ? <>Clarity in every<br /><span>conversation.</span></> : section.title}</h1>
        <p>{section.description}</p>
        <div className="hero-actions"><Link to="/live" className="btn hero-primary">Explore live monitoring →</Link><Link to="/sessions" className="btn hero-secondary">Explore sessions →</Link></div>
      </div></section>
      <div className="grid grid-2" style={{ marginTop: 24 }}>
        {section.panels.map(([title, description]) => <Panel key={title} title={title}><p className="muted">{description}</p></Panel>)}
      </div>
      {(route === 'overview' || route === 'live') && <div style={{ marginTop: 24 }}><Panel title="Policy guidance · explanation only">
        <div className="grid grid-2">{(['ALLOW', 'WARN', 'SECONDARY_VERIFICATION', 'ESCALATE', 'HOLD'] as const).map(action => <div key={action}><ActionPill action={action} /><p className="small muted">{ACTION_DESCRIPTION[action]}</p></div>)}</div>
      </Panel></div>}
    </div>
  </AppShell>;
}
