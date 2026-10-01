import type { DashboardSession } from '../api/praxis';

export function sessionDuration(session: DashboardSession, now = Date.now()): string {
  const start = Date.parse(session.call_connected_at ?? session.created_at);
  const end = session.ended_at ? Date.parse(session.ended_at) : now;
  if (!Number.isFinite(start) || !Number.isFinite(end)) return '—';
  const seconds = Math.max(0, Math.floor((end - start) / 1000));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remaining = seconds % 60;
  return hours ? `${hours}:${String(minutes).padStart(2, '0')}:${String(remaining).padStart(2, '0')}`
    : `${minutes}:${String(remaining).padStart(2, '0')}`;
}

/** Freshness is only a display guard; it is not a model threshold or risk calibration. */
export function currentAnalysis(session: DashboardSession, now = Date.now()) {
  if (!session.connected || !session.latest_analysis || !session.latest_analysis_at) return null;
  const age = now - Date.parse(session.latest_analysis_at);
  return Number.isFinite(age) && age >= 0 && age <= 30_000 ? session.latest_analysis : null;
}

export function remoteLabel(session: DashboardSession): string {
  return session.remote_name || session.remote_number || 'Contact not supplied';
}
