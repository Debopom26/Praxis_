import { useEffect, useState } from 'react';
import { dashboardSessions } from '../api/praxis';
import type { DashboardSession } from '../api/praxis';
import { useAuth } from '../state/auth';

export function useSessionDirectory(query = '', offset = 0, active?: boolean) {
  const { session } = useAuth();
  const token = session?.accessToken;
  const [rows, setRows] = useState<DashboardSession[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    setRows([]); setTotal(0); setLoading(true); setError(false);
    async function check() {
      if (!token) { setLoading(false); return; }
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      try {
        const result = await dashboardSessions(token, query, offset, active, controller.signal);
        if (!disposed) { setRows(result.sessions); setTotal(result.total); setError(false); }
      } catch { if (!disposed) { setRows([]); setTotal(0); setError(true); } }
      finally {
        clearTimeout(timeout);
        if (!disposed) { setLoading(false); timer = setTimeout(check, 3000); }
      }
    }
    void check();
    return () => { disposed = true; clearTimeout(timer); controller?.abort(); };
  }, [token, query, offset, active, revision]);
  return { rows, total, loading, error, refresh: () => setRevision(v => v + 1) };
}
