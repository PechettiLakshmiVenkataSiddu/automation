import crypto from 'node:crypto';
import dns from 'node:dns/promises';
import http from 'node:http';
import net from 'node:net';
import { URL } from 'node:url';
import { chromium } from 'playwright';

const secret = Buffer.from(process.env.BROWSER_GRANT_SECRET ?? '', 'utf8');
if (secret.length < 32) throw new Error('BROWSER_GRANT_SECRET must be at least 32 bytes.');
const controlPlaneUrl = process.env.CONTROL_PLANE_URL ?? '';
const executorSecret = process.env.BROWSER_EXECUTOR_SECRET ?? '';
if (!controlPlaneUrl || executorSecret.length < 32)
  throw new Error('Executor control-plane configuration is required.');

function verifyGrant(token) {
  const [encoded, signature] = token.split('.', 2);
  const expected = crypto.createHmac('sha256', secret).update(encoded).digest('hex');
  if (!signature || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected)))
    throw new Error('Invalid grant');
  const grant = JSON.parse(Buffer.from(encoded, 'base64url').toString('utf8'));
  if (grant.expires_at < Math.floor(Date.now() / 1000)) throw new Error('Expired grant');
  return grant;
}

function isPublicAddress(address) {
  if (net.isIP(address) === 4) {
    const [first, second] = address.split('.').map(Number);
    return !(
      first === 10 ||
      first === 127 ||
      first === 0 ||
      first >= 224 ||
      (first === 169 && second === 254) ||
      (first === 172 && second >= 16 && second <= 31) ||
      (first === 192 && second === 168)
    );
  }
  const normalized = address.toLowerCase();
  return !(
    normalized === '::1' ||
    normalized.startsWith('fe80:') ||
    normalized.startsWith('fc') ||
    normalized.startsWith('fd')
  );
}

async function safeTarget(value, hosts) {
  const target = new URL(value);
  if (target.protocol !== 'https:' || !hosts.includes(target.hostname.toLowerCase()))
    throw new Error('Egress denied');
  const addresses = await dns.lookup(target.hostname, { all: true, verbatim: true });
  if (!addresses.length || addresses.some(({ address }) => !isPublicAddress(address)))
    throw new Error('Unsafe target resolution');
  return target;
}

function redact(value) {
  return value.replace(/(password|token|authorization|cookie)\s*[:=]\s*[^\s"']+/gi, '[REDACTED]');
}

http
  .createServer(async (request, response) => {
    if (request.method !== 'POST' || request.url !== '/execute')
      return response.writeHead(404).end();
    let body = '';
    for await (const chunk of request) body += chunk;
    let browser;
    try {
      const { grant, action } = JSON.parse(body);
      const claims = verifyGrant(grant);
      if (claims.organization_id !== action.organization_id || claims.task_id !== action.task_id)
        throw new Error('Grant scope mismatch');
      const target = await safeTarget(action.url, action.allowed_hosts);
      const timeout = Math.min(Math.max(action.timeout_seconds, 1), 120) * 1000;
      browser = await chromium.launch({ headless: true });
      const page = await browser.newPage();
      await page.goto(target.href, { waitUntil: 'domcontentloaded', timeout });
      await page
        .locator('input[type=password]')
        .evaluateAll((items) => items.forEach((item) => (item.value = '••••••••')));
      const screenshot = await page.screenshot({ type: 'png' });
      const artifact = await fetch(`${controlPlaneUrl}/v1/browser-tasks/internal/artifacts`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'X-Browser-Executor-Secret': executorSecret,
        },
        body: JSON.stringify({
          organization_id: claims.organization_id,
          task_id: claims.task_id,
          artifact_type: 'screenshot',
          content_base64: screenshot.toString('base64'),
        }),
      });
      if (!artifact.ok) throw new Error('Artifact ingestion failed');
      response.writeHead(200, { 'content-type': 'application/json' }).end(
        JSON.stringify({
          task_id: claims.task_id,
          artifact: await artifact.json(),
          text: redact((await page.locator('body').innerText()).slice(0, 5000)),
        }),
      );
    } catch (error) {
      response
        .writeHead(422, { 'content-type': 'application/json' })
        .end(JSON.stringify({ error: 'browser_task_rejected', detail: redact(String(error)) }));
    } finally {
      await browser?.close();
    }
  })
  .listen(8080, '0.0.0.0');
