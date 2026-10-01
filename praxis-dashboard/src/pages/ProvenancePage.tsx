import { AppShell } from '../components/AppShell';
import { Panel } from '../components/ui';
import { Link } from '../router';

export function ProvenancePage() {
  return <AppShell title="Help" subtitle="Using your voice integrity workspace">
    <div className="content content-narrow">
      <div className="page-head"><h1 className="page-title">Using Praxis</h1><p className="muted">Follow live calls and review past analysis.</p></div>
      <div className="col gap-16">
        <Panel title="Check your connection"><p>Overview shows “Praxis connected” when the backend responds and “Not connected” when it cannot be reached. System Health shows a basic Okay or Not okay service check. This is connection status, not a verdict on a call.</p><Link className="text-link" to="/health">Check system availability →</Link></Panel>
        <Panel title="Connected workspace"><p>This dashboard uses your Praxis account and displays sessions recorded by the Praxis backend. The connected Android app supplies a contact name only when Android permits it; otherwise a number or “Contact not supplied” appears.</p></Panel>
        <Panel title="Follow a live call"><p>The Current Sessions panel shows calls with an active audio connection. Live Monitoring updates from recorded backend results. If Android silences the microphone during a cellular call, Praxis cannot analyze that audio; an active connection alone does not mean a score is available.</p></Panel>
        <Panel title="Find sessions and past analysis"><p>Sessions lists conversations from your workspace. Search by caller name or phone number, then choose View analysis. The same lookup is available in Audit Trail and in Live Monitoring’s Past call analysis panel.</p><p style={{ marginTop: 12 }}>Names and numbers are supplied by the calling application; missing details show “Not supplied”. A displayed name does not verify a caller’s identity. Search needs those details to be supplied.</p><Link className="btn btn-primary btn-sm" style={{ marginTop: 16 }} to="/sessions">View sessions</Link></Panel>
        <Panel title="Review the record"><p>Administrator and analyst accounts can view recorded audit events in time order. Refresh history to retrieve newer events.</p></Panel>
        <Panel title="Understand the analysis"><p>A dash or “No analysis yet” means no result has been recorded. “Unavailable” means a check could not provide evidence. Neither means a conversation is safe. Risk assessment remains experimental; review the evidence before acting.</p></Panel>
      </div>
    </div>
  </AppShell>;
}
