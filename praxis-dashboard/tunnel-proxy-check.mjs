import assert from 'node:assert/strict';
import fs from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

const source = fs.readFileSync('functions/api/[[path]].ts', 'utf8');
const code = stripTypeScriptTypes(source);
const { onRequest } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
const request = new Request('https://dashboard.example/api/v1/health');
let target;
globalThis.fetch = async (url) => { target = url.toString(); return new Response('{}'); };
const env = {
  PRAXIS_BACKEND_ORIGIN: 'https://old.trycloudflare.com',
  PRAXIS_TUNNEL: { get: async () => 'https://new.trycloudflare.com' },
};
assert.equal((await onRequest({ request, env })).status, 200);
assert.equal(target, 'https://new.trycloudflare.com/api/v1/health');
env.PRAXIS_TUNNEL.get = async () => 'https://next.trycloudflare.com';
await onRequest({ request, env });
assert.equal(target, 'https://next.trycloudflare.com/api/v1/health');
env.PRAXIS_TUNNEL.get = async () => null;
assert.equal((await onRequest({ request, env })).status, 503);
env.PRAXIS_TUNNEL.get = async () => { throw new Error('quota'); };
assert.equal((await onRequest({ request, env })).status, 503);
env.PRAXIS_TUNNEL.get = async () => 'http://unsafe.example';
assert.equal((await onRequest({ request, env })).status, 503);
env.PRAXIS_TUNNEL.get = async () => 'https://new.trycloudflare.com';
const upgrade = { status: 101, webSocket: {} };
globalThis.fetch = async () => upgrade;
assert.equal(await onRequest({ request, env }), upgrade);
console.log('PASS: dynamic address changes, fail-closed lookup, HTTPS validation, socket metadata');
