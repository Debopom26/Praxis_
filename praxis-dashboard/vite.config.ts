import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// The dashboard talks to the FastAPI backend. In development these proxies keep the
// browser on a single origin, so no CORS relaxation is needed on the backend
// (SRS Sec.18 keeps the security surface small rather than opening it for convenience).
export default defineConfig(({ mode }) => {
  const BACKEND = loadEnv(mode, '.', 'PRAXIS_').PRAXIS_DEV_BACKEND ?? 'http://127.0.0.1:8000';
  return {
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // REST control plane (SRS Sec.6.2).
      '/api': {
        target: BACKEND,
        changeOrigin: true,
        // Live result streaming uses WSS on the same path prefix (SRS Sec.6.3).
        ws: true,
      },
    },
  },
  };
});
