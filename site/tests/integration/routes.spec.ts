import { deployment, deployed } from './deployment.mjs';
import { test, expect } from '@playwright/test';
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
export const paths = ['/', '/specification/', '/runners/', '/authors/quickstart/', '/authors/best-practices/', '/authors/checks/', '/authors/explain-back/', '/implementers/support/', '/implementers/conformance/'];
const dist = fileURLToPath(new URL('../../dist/', import.meta.url));
function htmlRoutes(directory: string, prefix = ''): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry): string[] => entry.isDirectory() ? htmlRoutes(`${directory}/${entry.name}`, `${prefix}${entry.name}/`) : entry.name === 'index.html' ? [`/${prefix}`] : []);
}
test('all nine real routes form a closed navigation graph with no fixture destinations', async ({ page }) => {
  expect(htmlRoutes(dist).sort()).toEqual([...paths].sort());
  for (const path of paths) {
    const response = await page.goto(deployed(path));
    expect(response?.status(), path).toBe(200);
    await expect(page.locator('main h1')).toBeVisible();
    const sidebar = await page.locator('#starlight__sidebar a').evaluateAll((links) => links.map((a) => new URL((a as HTMLAnchorElement).href).pathname));
    expect(sidebar, path).toEqual(paths.map(deployed));
    for (const href of await page.locator('.pagination-links a').evaluateAll((links) => links.map((a) => new URL((a as HTMLAnchorElement).href).pathname))) expect(paths.map(deployed)).toContain(href);
    const content = await page.locator('main').innerText();
    expect(content).not.toMatch(/Design fixture|quillwort|Evaluating courses/);
    const body = readFileSync(`${dist}${path.slice(1)}index.html`, 'utf8');
    expect(body).not.toContain('/evaluating-courses/');
  }
  expect((await page.goto(deployed('/unknown-course-route/')))?.status()).toBe(404);
});

test('the deployed base contains canonical pages, all browser assets, home and runner links', async ({ page, request }) => {
  const failed: string[] = [];
  const requested = new Set<string>();
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.hostname !== '127.0.0.1') return;
    requested.add(url.pathname);
    if (response.status() >= 400 || !url.pathname.startsWith(deployment.base)) failed.push(`${response.status()} ${url.pathname}`);
  });
  page.on('requestfailed', (request) => failed.push(request.url()));
  for (const path of paths) {
    await page.goto(deployed(path));
    await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', deployment.site + deployed(path));
    await expect(page.locator('a.site-title')).toHaveAttribute('href', deployed('/'));
    const favicon = await page.locator('link[rel="shortcut icon"], link[rel="icon"]').getAttribute('href');
    expect(favicon).toBe(deployed('/mark.svg'));
    expect((await request.get(favicon!)).status()).toBe(200);
    const urls = await page.locator('a[href], [src], link[href]').evaluateAll((nodes) => nodes.flatMap((node) => {
      const value = node.getAttribute('href') ?? node.getAttribute('src');
      if (!value) return [];
      const url = new URL(value, document.URL);
      return url.origin === location.origin ? [url.pathname] : [];
    }));
    for (const url of urls) {
      expect(url.startsWith(deployment.base), url).toBe(true);
      expect(url).not.toContain('/agentcourses/agentcourses/');
    }
  }
  await page.goto(deployed('/runners/'));
  await expect(page.getByRole('link', { name: 'Build a runner' })).toHaveAttribute('href', deployed('/implementers/support/'));
  await expect(page.locator('main a').filter({ hasText: 'receipt experiment report' })).toHaveAttribute('href', 'https://github.com/agentcourses/agentcourses/blob/main/docs/delivery/call-receipts.md#host-evidence');
  await page.getByRole('link', { name: 'Build a runner' }).click();
  await expect(page).toHaveURL(new RegExp(deployed('/implementers/support/') + '$'));
  await page.locator('a.site-title').click();
  expect(new URL(page.url()).pathname).toBe(deployed('/'));
  await page.evaluate(() => document.fonts.ready);
  expect([...requested].some((path) => path.includes('/_astro/') && path.endsWith('.css'))).toBe(true);
  expect([...requested].some((path) => path.includes('/_astro/') && path.endsWith('.js'))).toBe(true);
  expect([...requested].some((path) => path.includes('/fonts/') && path.endsWith('.woff2'))).toBe(true);
  expect(failed).toEqual([]);
});
