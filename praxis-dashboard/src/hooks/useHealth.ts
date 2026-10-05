import { useEffect, useState } from 'react';
import { praxisHealth } from '../api/praxis';
import type { PraxisHealth } from '../api/praxis';
import { useAuth } from '../state/auth';

export function useHealth() {
  const { guest } = useAuth();
  const [health, setHealth] = useState<PraxisHealth | null>(null);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (guest) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    let controller: AbortController;
    async function check() {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);
      try {
        const result = await praxisHealth(controller.signal);
        if (!disposed) { setHealth(result); setCheckedAt(new Date().toISOString()); setError(false); }
      } catch { if (!disposed) { setHealth(null); setError(true); } }
      finally {
        clearTimeout(timeout);
        if (!disposed) { setLoading(false); timer = setTimeout(check, 10000); }
      }
    }
    setLoading(true);
    void check();
    return () => { disposed = true; clearTimeout(timer); controller?.abort(); };
  }, [revision, guest]);
  return { health: guest ? null : health, checkedAt: guest ? null : checkedAt,
    error: guest || error, loading: !guest && loading, refresh: () => setRevision(v => v + 1) };
}
