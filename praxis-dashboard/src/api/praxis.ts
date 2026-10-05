import { request } from './client';

export interface PraxisLogin {
  access_token: string;
  role: 'admin' | 'analyst' | 'host';
  tenant_id: string;
  username: string;
  expires_at: string;
}

export interface LatestAnalysis {
  experimental_score_0_100: number;
  regressor_status: string;
  action: string;
  message: string;
}

export interface RecordedAnalysis extends LatestAnalysis {
  timestamp: string;
}

export interface DashboardSession {
  session_id: string;
  tenant_id: string;
  call_id: string;
  owner_username: string | null;
  remote_name: string | null;
  remote_number: string | null;
  created_at: string;
  call_connected_at: string | null;
  ended_at: string | null;
  connected: boolean;
  latest_analysis: LatestAnalysis | null;
  latest_analysis_at: string | null;
  latest_risk: { risk_display_0_100: number; timestamp: string } | null;
  latest_policy: { action: string; timestamp: string } | null;
}

export interface PraxisHealth {
  service_version: string;
  status: string;
  components: Record<string, { status: string; version: string | null; reason_codes: string[] }>;
  artifacts: { module: string; state: string; version: string | null; reason_codes: string[] }[];
}

export interface PraxisAuditEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  call_id: string | null;
  final_risk: number | null;
  action: string | null;
  status: string;
  reason_codes: string[];
}

export function praxisLogin(username: string, password: string, tenantId: string) {
  return request<PraxisLogin>('/api/v1/auth/login', {
    method: 'POST', body: { username, password, tenant_id: tenantId },
  });
}

export function praxisRegister(tenantId: string, organizationName: string,
  username: string, password: string) {
  return request<{ status: string; tenant_id: string; username: string }>(
    '/api/v1/auth/register', {
      method: 'POST', body: {
        tenant_id: tenantId, organization_name: organizationName, username, password,
      },
    });
}

export function praxisCreateHost(token: string, username: string, password: string) {
  return request<{ status: string; tenant_id: string; username: string }>(
    '/api/v1/admin/hosts', {
      method: 'POST', token, body: { username, password },
    });
}

export function praxisHealth(signal?: AbortSignal) {
  return request<PraxisHealth>('/api/v1/health', { signal });
}

export function dashboardSessions(token: string, query = '', offset = 0,
                                  active?: boolean, signal?: AbortSignal) {
  const params = new URLSearchParams({ q: query, offset: String(offset), limit: '20' });
  if (active !== undefined) params.set('active', String(active));
  return request<{ sessions: DashboardSession[]; total: number }>(
    `/api/v1/dashboard/sessions?${params}`, { token, signal });
}

export function dashboardSession(id: string, token: string, signal?: AbortSignal) {
  return request<DashboardSession>(`/api/v1/dashboard/sessions/${encodeURIComponent(id)}`,
    { token, signal });
}

export function dashboardAnalysisHistory(id: string, token: string, offset = 0, signal?: AbortSignal) {
  return request<{ results: RecordedAnalysis[]; total: number }>(
    `/api/v1/dashboard/sessions/${encodeURIComponent(id)}/analysis?limit=20&offset=${offset}`,
    { token, signal });
}

export function praxisAudit(id: string, token: string, signal?: AbortSignal) {
  return request<PraxisAuditEvent[]>(`/api/v1/audit/${encodeURIComponent(id)}`,
    { token, signal });
}
