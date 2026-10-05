/**
 * Sign-in screen.
 *
 * The credentials and organization are verified by the live Praxis backend.
 */

import { lazy, Suspense, useState } from 'react';
import type { FormEvent } from 'react';

import { IconAlertTriangle, IconLock } from '../components/Icons';
import { BrandLogo } from '../components/BrandLogo';
import { useAuth } from '../state/auth';
import { ApiError } from '../api/client';
import { praxisRegister } from '../api/praxis';

const LoginWaterBackground = lazy(() => import('../components/LoginWaterBackground'));

export function LoginPage() {
  const { signIn, busy, error } = useAuth();
  const [username, setUsername] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [password, setPassword] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [creating, setCreating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    if (!creating) {
      await signIn(username.trim(), password, tenantId.trim());
      return;
    }
    if (password !== confirmPassword) {
      setFormError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await praxisRegister(tenantId.trim(), organizationName.trim(), username.trim(), password);
      setCreating(false);
      setConfirmPassword('');
      await signIn(username.trim(), password, tenantId.trim());
    } catch (cause) {
      setFormError(cause instanceof ApiError
        ? cause.status === 409 ? 'Organization ID or username is already in use.'
          : cause.status === 429 ? 'Too many attempts. Please try again later.'
            : cause.status === 422 ? 'Check the organization ID, username and password.'
              : cause.message
        : 'Account creation failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <Suspense fallback={null}><LoginWaterBackground /></Suspense>
      <section className="login-intro" aria-label="About Praxis">
        <span className="eyebrow">PRAXIS / VOICE INTEGRITY</span>
        <h1>A clearer view.<br /><span>A more informed decision.</span></h1>
        <p>Bring the signals behind every conversation into focus. Your sessions, evidence, and decisions, in one workspace.</p>
        <div className="login-features"><span>01 / Monitor sessions</span><span>02 / Explore evidence</span><span>03 / Trace decisions</span></div>
      </section>
      <form className="glass login-card" onSubmit={onSubmit}>
        <div className="login-brand">
          <BrandLogo />
        </div>

        <div className="login-heading"><h2>{creating ? 'Create your workspace.' : 'Welcome back.'}</h2>
          <p>{creating ? 'Start a new Praxis organization and its administrator account.' : 'Sign in to your voice integrity workspace.'}</p></div>

        <div className="col gap-16">
          <div className="field">
            <label htmlFor="tenant-id">{creating ? 'New organization ID' : 'Organization ID'}</label>
            <input id="tenant-id" className="input" autoComplete="organization"
              value={tenantId} onChange={(event) => setTenantId(event.target.value)}
              pattern="[A-Za-z0-9_.:@-]+" maxLength={128} required />
          </div>
          {creating ? <div className="field">
            <label htmlFor="organization-name">Organization name</label>
            <input id="organization-name" className="input" autoComplete="organization"
              value={organizationName} onChange={(event) => setOrganizationName(event.target.value)}
              maxLength={256} required />
          </div> : null}
          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              className="input"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              pattern="[A-Za-z0-9_.:@-]+"
              maxLength={128}
              enterKeyHint="next"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete={creating ? 'new-password' : 'current-password'}
              minLength={creating ? 12 : undefined}
              enterKeyHint="go"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {creating ? <div className="field">
            <label htmlFor="confirm-password">Confirm password</label>
            <input id="confirm-password" className="input" type="password"
              autoComplete="new-password" minLength={12} value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)} required />
          </div> : null}

          {(formError || (!creating && error)) ? (
            <div className="note note-bad">
              <IconAlertTriangle />
              <div>{formError || error}</div>
            </div>
          ) : null}

          <button type="submit" className="btn btn-accent" disabled={busy || submitting}>
            <IconLock />
            {submitting ? 'Creating account…' : busy ? 'Signing in…' : creating ? 'Create organization' : 'Sign in'}
          </button>

        </div>
        <p className="login-foot">
          {creating ? 'Already belong to an organization? Its administrator must create your caller account.'
            : 'Use the same Praxis organization account as your connected caller app.'}
          {' '}<button className="text-link" type="button" onClick={() => { setCreating(!creating); setFormError(null); }}>
            {creating ? 'Sign in instead' : 'New organization? Create an account'}
          </button>
        </p>
      </form>
    </div>
  );
}
