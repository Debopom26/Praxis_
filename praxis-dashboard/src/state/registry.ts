/**
 * Sessions created by this browser.
 *
 * The locked SRS Sec.6.2 surface has no "list sessions" endpoint, so the console cannot
 * enumerate a tenant's sessions. Rather than invent one, it remembers the sessions it
 * created itself. Everything shown here was returned by a real `POST /api/v1/sessions`
 * call; nothing is fabricated.
 */

import type { SessionContext, SessionStartResponse, SessionState } from '../api/types';

const STORAGE_KEY = 'praxis.sessions.v1';
const LIMIT = 50;

export interface SessionRecord {
  sessionId: string;
  callId: string;
  hostAppId: string;
  claimedIdentity: string | null;
  state: SessionState;
  createdAt: string;
  /**
   * The context this console submitted. Stored because the backend's session summary
   * (SRS Sec.6.2) does not return the context object, so there is no other way for the
   * console to show what was sent. It is labelled as submitted-by-this-console in the UI.
   */
  context: SessionContext | null;
}

function toRecord(response: SessionStartResponse): SessionRecord {
  return {
    sessionId: response.session_id,
    callId: response.call_id,
    hostAppId: response.host_app_id,
    claimedIdentity: response.claimed_identity,
    state: response.state,
    createdAt: response.created_at,
    context: response.context,
  };
}

export function loadSessionRecords(): SessionRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((entry): entry is Partial<SessionRecord> => {
        if (typeof entry !== 'object' || entry === null) return false;
        const candidate = entry as Partial<SessionRecord>;
        return typeof candidate.sessionId === 'string' && typeof candidate.callId === 'string';
      })
      .map((candidate) => ({
        sessionId: candidate.sessionId as string,
        callId: candidate.callId as string,
        hostAppId: candidate.hostAppId ?? '',
        claimedIdentity: candidate.claimedIdentity ?? null,
        state: candidate.state ?? 'CREATED',
        createdAt: candidate.createdAt ?? '',
        context: typeof candidate.context === 'object' ? candidate.context : null,
      }));
  } catch {
    return [];
  }
}

function persist(records: SessionRecord[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(records.slice(0, LIMIT)));
  } catch {
    /* storage full or disabled: the console still works, it just forgets */
  }
}

export function rememberSession(response: SessionStartResponse): SessionRecord[] {
  const record = toRecord(response);
  const next = [record, ...loadSessionRecords().filter((r) => r.sessionId !== record.sessionId)];
  persist(next);
  return next.slice(0, LIMIT);
}

export function forgetSession(sessionId: string): SessionRecord[] {
  const next = loadSessionRecords().filter((r) => r.sessionId !== sessionId);
  persist(next);
  return next;
}

export function findSessionRecord(sessionId: string): SessionRecord | null {
  return loadSessionRecords().find((r) => r.sessionId === sessionId) ?? null;
}
