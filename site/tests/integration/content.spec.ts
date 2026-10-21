import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { inspectLinkTargets } from './link-targets.mjs';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const routes = ['/', '/specification/', '/runners/', '/authors/quickstart/', '/authors/best-practices/', '/authors/checks/', '/authors/explain-back/', '/implementers/support/', '/implementers/conformance/'];
test('every foundation-mapped normative fragment and local article link resolves', async ({ page, request, baseURL }, info) => {
  const mapping = JSON.parse(execFileSync('uv', ['run', '--locked', 'python', 'tools/check_docs.py', '--site-map'], { cwd: root, encoding: 'utf8' }));
  const snapshots = new Map<string, { status: number; ids: string[] }>();
  const local = new Set<string>();
  for (const route of routes) {
    const response = await page.goto(route);
    expect(response?.status(), route).toBe(200);
    const rendered = await page.evaluate(() => ({
      ids: [...document.querySelectorAll('[id]')].map((node) => node.id),
      hrefs: [...document.querySelectorAll<HTMLAnchorElement>('main a[href]')].map((node) => node.href),
    }));
    snapshots.set(new URL(route, baseURL).href, { status: response!.status(), ids: rendered.ids });
    for (const href of rendered.hrefs) {
      if (new URL(href).origin === new URL(page.url()).origin) local.add(href);
    }
  }
  const ids = snapshots.get(new URL('/specification/', baseURL).href)!.ids;
  expect(new Set(ids).size, 'rendered IDs are unique').toBe(ids.length);
  for (const entry of mapping.anchors) expect(ids, entry.public).toContain(entry.public.split('#')[1]);
  const checks = await inspectLinkTargets(local, async (target: string, needsIDs: boolean) => {
    const known = snapshots.get(target);
    if (known) return known;
    if (!needsIDs) return { status: (await request.get(target)).status(), ids: [] };
    const response = await page.goto(target);
    expect(response, target).not.toBeNull();
    return { status: response!.status(), ids: await page.locator('[id]').evaluateAll((nodes) => nodes.map((node) => node.id)) };
  });
  expect(checks.map(({ href }) => href).sort(), 'every collected URL is checked').toEqual([...local].sort());
  for (const { href, status, fragmentPresent } of checks) {
    expect(status, href).toBe(200);
    expect(fragmentPresent, href).toBe(true);
  }
  await info.attach('complete-link-inventory', { contentType: 'application/json', body: JSON.stringify({ mappedAnchors: mapping.anchors.length, checks }) });
});
test('actual page and code clipboard controls copy the rendered production content', async ({ page, context, baseURL }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: new URL(baseURL!).origin });
  await page.goto('/authors/checks/');
  await page.getByRole('button', { name: 'Copy page', exact: true }).click();
  await expect(page.locator('.ac-copy-page [role="status"]')).toHaveText('Page copied to the clipboard.');
  const article = await page.evaluate(() => navigator.clipboard.readText());
  expect(article).toContain('AGENT_COURSE_DIR'); expect(article).not.toContain('Copy page');
  const code = page.locator('.expressive-code').first();
  const expected = await code.locator('code').innerText();
  await code.getByRole('button', { name: 'Copy to clipboard' }).click();
  await expect(code.locator('[aria-live]')).toHaveText('Copied!');
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(expected);
});
test('all schema downloads preserve their canonical bytes', async ({ request }) => {
  const inventory = JSON.parse(readFileSync(`${root}/site/public/schemas/manifest.json`, 'utf8'));
  const response = await request.get('/schemas/manifest.json');
  expect(await response.body()).toEqual(readFileSync(`${root}/site/public/schemas/manifest.json`));
  for (const release of inventory.releases) for (const schema of release.schemas) {
    const response = await request.get(new URL(schema.id).pathname); expect(response.status()).toBe(200);
    expect(await response.body()).toEqual(readFileSync(`${root}/site/public${new URL(schema.id).pathname}`));
    if (release.candidate === inventory.candidate) expect(await response.body()).toEqual(readFileSync(`${root}/${schema.path}`));
  }
});
