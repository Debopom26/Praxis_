interface Env { PRAXIS_BACKEND_ORIGIN: string }

export const onRequest = async (context: { request: Request; env: Env }): Promise<Response> => {
  const origin = context.env.PRAXIS_BACKEND_ORIGIN;
  if (!origin) return new Response('Praxis backend is not configured', { status: 503 });
  let backend: URL;
  try { backend = new URL(origin); } catch { return new Response('Invalid backend origin', { status: 503 }); }
  if (backend.protocol !== 'https:' || backend.username || backend.password || backend.pathname !== '/' || backend.search || backend.hash) {
    return new Response('Backend must be an HTTPS origin', { status: 503 });
  }
  const incoming = new URL(context.request.url);
  const target = new URL(incoming.pathname + incoming.search, backend);
  const headers = new Headers(context.request.headers);
  headers.delete('host');
  headers.delete('cookie');
  const response = await fetch(target, {
    method: context.request.method,
    headers,
    body: ['GET', 'HEAD'].includes(context.request.method) ? undefined : context.request.body,
    redirect: 'manual',
  });
  const outgoing = new Headers(response.headers);
  outgoing.delete('set-cookie');
  outgoing.set('Cache-Control', 'no-store');
  return new Response(response.body, { status: response.status, headers: outgoing });
};
