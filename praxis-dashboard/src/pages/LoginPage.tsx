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

const LoginWaterBackground = lazy(() => import('../components/LoginWaterBackground'));

export function LoginPage() {
  const { signIn, busy, error } = useAuth();
  const [username, setUsername] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [password, setPassword] = useState('');

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await signIn(username.trim(), password, tenantId.trim());
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

        <div className="login-heading"><h2>Welcome back.</h2><p>Sign in to your voice integrity workspace.</p></div>

        <div className="col gap-16">
          <div className="field">
            <label htmlFor="tenant-id">Organization ID</label>
            <input id="tenant-id" className="input" autoComplete="organization"
              value={tenantId} onChange={(event) => setTenantId(event.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              className="input"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
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
              autoComplete="current-password"
              enterKeyHint="go"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {error ? (
            <div className="note note-bad">
              <IconAlertTriangle />
              <div>{error}</div>
            </div>
          ) : null}

          <button type="submit" className="btn btn-accent" disabled={busy}>
            <IconLock />
            {busy ? 'Signing in\u2026' : 'Sign in'}
          </button>

        </div>
        <p className="login-foot">Use the same Praxis organization account as your connected caller app.</p>
      </form>
    </div>
  );
}
