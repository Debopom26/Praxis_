/**
 * Typed REST client for the locked Praxis API surface (SRS Sec.6.2).
 *
 * Two deliberate choices:
 *  - The access token is sent only in the `Authorization` header. `tenant_id` is never
 *    sent by the client: it is derived by the backend from the signed token (SRS Sec.18).
 *  - Errors keep the backend's machine-readable `code`, so the UI can distinguish
 *    "session does not exist" from "you may not see it" without parsing prose.
 */

import type { UserRole } from './types';

const AUTH_STORAGE_KEY = 'praxis.auth.session.v1';

export interface AuthSession {
  accessToken: string;
  role: UserRole;
  tenantId: string;
  username: string;
  expiresAt: string;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly detail: unknown;

  constructor(init: { code: string; message: string; status: number; detail?: unknown }) {
    super(init.message);
    this.name = 'ApiError';
    this.code = init.code;
    this.status = init.status;
    this.detail = init.detail ?? null;
  }
}

/* ------------------------------------------------------------------ *
 * Session persistence
 * ------------------------------------------------------------------ */

/**
 * Tokens live in `sessionStorage`, which is cleared when the tab closes. This is a
 * deliberate, documented trade-off for the V1 local prototype: the token is not
 * durable, but it is also readable by any script on this origin. A production build
 * needs the token out of JS reach entirely (httpOnly cookie or a native keystore).
 */
export function loadAuthSession(): AuthSession | null {
  try {
    const raw = sessionStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<AuthSession>;
    if (typeof parsed.accessToken !== 'string' || typeof parsed.tenantId !== 'string') return null;
    if (typeof parsed.role !== 'string') return null;
    return {
      accessToken: parsed.accessToken,
      role: parsed.role as UserRole,
      tenantId: parsed.tenantId,
      username: typeof parsed.username === 'string' ? parsed.username : 'unknown',
      expiresAt: typeof parsed.expiresAt === 'string' ? parsed.expiresAt : '',
    };
  } catch {
    return null;
  }
}

export function saveAuthSession(session: AuthSession): void {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function clearAuthSession(): void {
  sessionStorage.removeItem(AUTH_STORAGE_KEY);
}

/** True when the token's own expiry claim has already passed. */
export function isExpired(session: AuthSession): boolean {
  if (!session.expiresAt) return false;
  const expiry = Date.parse(session.expiresAt);
  return Number.isFinite(expiry) && expiry <= Date.now();
}

/* ------------------------------------------------------------------ *
 * Transport
 * ------------------------------------------------------------------ */

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT';
  body?: unknown;
  token?: string | null;
  signal?: AbortSignal | undefined;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (options.token) headers['Authorization'] = `Bearer ${options.token}`;

  const init: RequestInit = { method: options.method ?? 'GET', headers };
  if (options.body !== undefined) init.body = JSON.stringify(options.body);
  if (options.signal) init.signal = options.signal;

  let response: Response;
  try {
    response = await fetch(path, init);
    const canWake = init.method === 'POST' &&
      ['/api/v1/auth/login', '/api/v1/auth/register'].includes(path);
    const deadline = Date.now() + 10 * 60 * 1000;
    while (canWake && response.status === 503 && Date.now() < deadline) {
      const problem = await response.clone().json().catch(() => null) as { code?: string } | null;
      if (problem?.code !== 'PRAXIS_STARTING') break;
      window.dispatchEvent(new CustomEvent('praxis-starting'));
      await new Promise(resolve => setTimeout(resolve, 5000));
      if (options.signal?.aborted) throw new Error('Request cancelled');
      response = await fetch(path, init);
    }
  } catch {
    throw new ApiError({
      code: 'NETWORK_ERROR',
      status: 0,
      message:
        'Cannot reach the Praxis backend. Check the API connection or ask the backend team for its development endpoint.',
    });
  }

  const text = await response.text();
  const payload = text.length > 0 ? safeJson(text) : null;

  if (!response.ok) {
    const problem = (payload ?? {}) as { code?: unknown; message?: unknown; detail?: unknown };
    throw new ApiError({
      code: typeof problem.code === 'string' ? problem.code :
        typeof problem.detail === 'string' ? problem.detail : `HTTP_${response.status}`,
      status: response.status,
      message:
        typeof problem.message === 'string'
          ? problem.message
          : response.status === 502
            ? 'Cannot reach the Praxis backend. Check that it is running at the configured API address (PRAXIS_DEV_BACKEND in local development).'
          : `Request failed with status ${response.status}.`,
      detail: problem.detail,
    });
  }

  return payload as T;
}

