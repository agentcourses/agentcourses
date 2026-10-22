import { deployed } from './deployment.mjs';
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
const routes = ['/', '/specification/', '/runners/', '/authors/quickstart/', '/authors/best-practices/', '/authors/checks/', '/authors/explain-back/', '/implementers/support/', '/implementers/conformance/'];
for (const width of [390, 1440]) for (const colorScheme of ['light', 'dark'] as const) {
  test(`real content remains accessible at ${width}px in ${colorScheme}`, async ({ page }, info) => {
    test.setTimeout(180_000);
    await page.setViewportSize({ width, height: 1000 }); await page.emulateMedia({ colorScheme });
    for (const route of routes) {
      await page.goto(deployed(route));
      await expect(page.locator('html')).toHaveAttribute('data-theme', colorScheme);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), route).toBe(true);
      await expect(page.locator('site-search button[data-open-modal]')).toBeVisible();
      await expect(page.getByRole('button', { name: 'Copy page', exact: true })).toBeVisible();
      const violations = (await new AxeBuilder({ page }).analyze()).violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`);
      expect(violations, route).toEqual([]);
      if (route === '/' || route === '/specification/') await page.screenshot({ path: info.outputPath(`${route === '/' ? 'overview' : 'specification'}-${width}-${colorScheme}.png`), fullPage: false });
    }
  });
}
