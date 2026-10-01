import { useEffect, useState } from 'react';
import { praxisHealth } from '../api/praxis';
import type { PraxisHealth } from '../api/praxis';

export function useHealth() {
  const [health, setHealth] = useState<PraxisHealth | null>(null);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
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
  }, [revision]);
  return { health, checkedAt, error, loading, refresh: () => setRevision(v => v + 1) };
}
