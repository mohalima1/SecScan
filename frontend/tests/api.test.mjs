import test from 'node:test';
import assert from 'node:assert/strict';

globalThis.window = new EventTarget();

test('API starts a scan directly using JSON without cookies or CSRF', async () => {
  const api = await import('../src/lib/api.ts');
  const requests = [];
  globalThis.fetch = async (url, init) => {
    requests.push({ url, init });
    return Response.json({ scan_id: 'scan-1' }, { status: 202 });
  };
  const result = await api.startScan('http://127.0.0.1:8081/', ['zap']);
  assert.equal(result.scan_id, 'scan-1');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, '/api/scan/start');
  assert.equal(requests[0].init.credentials, 'omit');
  assert.equal(requests[0].init.headers['X-CSRF-Token'], undefined);
  assert.equal(requests[0].init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(requests[0].init.body), { target: 'http://127.0.0.1:8081/', tools: ['zap'] });
});

test('forbidden requests preserve the server error', async () => {
  const api = await import('../src/lib/api.ts');
  globalThis.fetch = async () => Response.json({ error: 'This browser origin is not allowed.' }, { status: 403 });
  await assert.rejects(api.getHistory(), error => error.status === 403 && error.message === 'This browser origin is not allowed.');
});

test('queued results cannot be mistaken for a clean finished scan', async () => {
  const api = await import('../src/lib/api.ts');
  globalThis.fetch = async () => Response.json({ status: 'running' }, { status: 202 });
  await assert.rejects(api.getScanResults('scan-1'), error => error.status === 409);
});

test('non-JSON backend failures produce a useful HTTP error', async () => {
  const api = await import('../src/lib/api.ts');
  globalThis.fetch = async () => new Response('Bad Gateway', { status: 502 });
  await assert.rejects(api.getHistory(), error => error.status === 502 && error.message.includes('502'));
});
