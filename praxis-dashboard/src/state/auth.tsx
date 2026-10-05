/**
 * Authentication state.
 *
 * The console holds the JWT it was issued and nothing else. `tenant_id` is displayed but
 * never sent: the backend derives it from the signed token on every request
 * (SRS Sec.18).
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';

import {
  ApiError,
  clearAuthSession,
  isExpired,
  loadAuthSession,
  saveAuthSession,
} from '../api/client';
import { praxisLogin } from '../api/praxis';
import type { AuthSession } from '../api/client';

interface AuthState {
  session: AuthSession | null;
  guest: boolean;
  exploreAsGuest: () => void;
  /** True while the sign-in request is in flight. */
  busy: boolean;
  error: string | null;
  signIn: (username: string, password: string, tenantId: string) => Promise<boolean>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [guest, setGuest] = useState(false);
  const attempt = useRef(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Restore on mount. An already-expired token is discarded rather than left to fail
  // on the first request.
  useEffect(() => {
    const restored = loadAuthSession();
    if (!restored) return;
    if (isExpired(restored)) {
      clearAuthSession();
      return;
    }
    setSession(restored);
  }, []);

  const signIn = useCallback(async (username: string, password: string, tenantId: string): Promise<boolean> => {
    const currentAttempt = ++attempt.current;
    setBusy(true);
    setError(null);
    try {
      const response = await praxisLogin(username, password, tenantId);
      if (currentAttempt !== attempt.current) return false;
      const next: AuthSession = {
        accessToken: response.access_token,
        role: response.role,
        tenantId: response.tenant_id,
        username,
        expiresAt: response.expires_at,
      };
      saveAuthSession(next);
      setGuest(false);
      setSession(next);
      return true;
    } catch (cause) {
      if (currentAttempt !== attempt.current) return false;
      const message =
        cause instanceof ApiError
          ? cause.status === 401
            ? 'Invalid organization ID, username or password.'
            : cause.message
          : 'Sign-in failed.';
      setError(message);
      return false;
    } finally {
      if (currentAttempt === attempt.current) setBusy(false);
    }
  }, []);

  const signOut = useCallback(() => {
    ++attempt.current;
    clearAuthSession();
    setSession(null);
    setGuest(false);
    setBusy(false);
    setError(null);
  }, []);

  const exploreAsGuest = useCallback(() => {
    ++attempt.current;
    setGuest(true);
    setBusy(false);
    setError(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ session, guest, exploreAsGuest, busy, error, signIn, signOut }),
    [session, guest, exploreAsGuest, busy, error, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>.');
  return context;
}
