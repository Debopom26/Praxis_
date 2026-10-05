import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { chromium } from '@playwright/test';

const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4197', '--strictPort'], { stdio: 'pipe' });
let browser;
try {
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Preview startup timeout')), 15000);
    server.stdout.on('data', chunk => { if (chunk.toString().includes('4197')) { clearTimeout(timeout); resolve(); } });
    server.on('exit', code => { clearTimeout(timeout); reject(new Error(`Preview exited: ${code}`)); });
  });
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  let calls = 0;
  await page.route('**/api/**', route => { calls++; return route.abort(); });
  await page.goto(`${process.env.GUEST_TEST_URL ?? 'http://127.0.0.1:4197'}/#/login`);
  await page.getByRole('button', { name: 'Explore as guest' }).click();
  for (const label of ['Overview', 'Live Monitoring', 'Sessions', 'Audit Trail', 'System Health', 'Help']) {
    await page.getByRole('link', { name: label, exact: true }).click();
    await page.getByText('Guest preview', { exact: true }).last().waitFor();
    assert.equal(await page.locator('.header-title').innerText(), label);
  }
  assert.equal(calls, 0, 'Guest must not contact offline APIs');
  assert.equal(await page.evaluate(() => sessionStorage.getItem('praxis.auth.session.v1')), null);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('link', { name: 'Sessions', exact: true }).click();
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'Mobile layout must fit');
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.getByRole('button', { name: 'Go to sign in' }).click();
  await page.getByRole('button', { name: 'Sign in', exact: true }).waitFor();

  // A late successful login must not replace an explicitly chosen guest preview.
  await page.unroute('**/api/**');
  let pending;
  await page.route('**/api/**', route => { pending = route; });
  await page.locator('#tenant-id').fill('test');
  await page.locator('#username').fill('judge');
  await page.locator('#password').fill('not-a-real-password');
  const requested = page.waitForRequest(request => request.url().includes('/api/'));
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await requested;
  await page.getByRole('button', { name: 'Explore as guest' }).click();
  assert.ok(pending);
  await pending.fulfill({ contentType: 'application/json', body: JSON.stringify({ access_token: 'test-token', role: 'admin', tenant_id: 'test', expires_at: '2099-01-01T00:00:00Z' }) });
  await page.waitForTimeout(150);
  assert.equal(await page.locator('.sidebar-profile .who').innerText(), 'Guest');
  assert.equal(await page.evaluate(() => sessionStorage.getItem('praxis.auth.session.v1')), null);
  assert.deepEqual(errors, []);
  console.log('PASS: offline guest navigation, zero API calls, mobile layout, exit, late-login isolation.');
} finally {
  await browser?.close();
  server.kill();
}
