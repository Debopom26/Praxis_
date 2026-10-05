import { useState } from 'react';
import type { FormEvent } from 'react';

import { ApiError } from '../api/client';
import { praxisCreateHost } from '../api/praxis';
import { AppShell } from '../components/AppShell';
import { Panel } from '../components/ui';
import { useAuth } from '../state/auth';

export function AccountsPage() {
  const { session, guest } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setCreated(null);
    if (guest || !session || session.role !== 'admin') return;
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await praxisCreateHost(session.accessToken, username.trim(), password);
      setCreated(username.trim());
      setUsername('');
      setPassword('');
      setConfirmPassword('');
    } catch (cause) {
      setError(cause instanceof ApiError
        ? cause.status === 409 ? 'Username is already in use.'
          : cause.status === 429 ? 'Too many attempts. Please try again later.'
            : cause.message
        : 'Could not create the account.');
    } finally {
      setBusy(false);
    }
  }

  return <AppShell title="Accounts" subtitle="Add callers to your organization">
    <div className="content">
      <div className="page-head"><h1 className="page-title">Accounts</h1>
        <p className="small muted">{guest ? 'Sign in as an organization administrator to create caller accounts.' : `Create a separate sign-in for another person in organization ${session?.tenantId}.`}</p>
      </div>
      <Panel title="Add a caller">
        <form className="col gap-16" onSubmit={onSubmit}>
          <div className="field"><label htmlFor="new-username">Username</label>
            <input id="new-username" className="input" autoComplete="off" autoCapitalize="none"
              pattern="[A-Za-z0-9_.:@-]+" maxLength={128} value={username}
              onChange={event => setUsername(event.target.value)} required /></div>
          <div className="field"><label htmlFor="new-password">Initial password</label>
            <input id="new-password" className="input" type="password" autoComplete="new-password"
              minLength={12} value={password} onChange={event => setPassword(event.target.value)} required /></div>
          <div className="field"><label htmlFor="new-password-confirm">Confirm password</label>
            <input id="new-password-confirm" className="input" type="password" autoComplete="new-password"
              minLength={12} value={confirmPassword}
              onChange={event => setConfirmPassword(event.target.value)} required /></div>
          {error ? <p className="note note-bad" role="alert">{error}</p> : null}
          {created ? <p className="note" role="status">Account {created} created. Share the sign-in details privately.</p> : null}
          <button className="btn btn-accent" type="submit" disabled={busy || guest}>
            {busy ? 'Creating account…' : 'Create caller account'}
          </button>
          <p className="small muted">This account can use the caller app and dashboard. Only an organization administrator can add people to an existing organization.</p>
        </form>
      </Panel>
    </div>
  </AppShell>;
}
