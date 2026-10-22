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
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(200);
    await expect(page.locator('main h1')).toBeVisible();
    const sidebar = await page.locator('#starlight__sidebar a').evaluateAll((links) => links.map((a) => new URL((a as HTMLAnchorElement).href).pathname));
    expect(sidebar, path).toEqual(paths);
    for (const href of await page.locator('.pagination-links a').evaluateAll((links) => links.map((a) => new URL((a as HTMLAnchorElement).href).pathname))) expect(paths).toContain(href);
    const content = await page.locator('main').innerText();
    expect(content).not.toMatch(/Design fixture|quillwort|Evaluating courses/);
    const body = readFileSync(`${dist}${path.slice(1)}index.html`, 'utf8');
    expect(body).not.toContain('/evaluating-courses/');
  }
  expect((await page.goto('/unknown-course-route/'))?.status()).toBe(404);
});
