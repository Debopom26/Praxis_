// Reuse the Pages API proxy so both hosting modes keep the same backend contract.
import { onRequest } from './functions/api/[[path]]';

interface Env {
  PRAXIS_BACKEND_ORIGIN: string;
  ASSETS: { fetch(request: Request): Promise<Response> };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (new URL(request.url).pathname.startsWith('/api/')) {
      return onRequest({ request, env });
    }
    return env.ASSETS.fetch(request);
  },
};
