import { test, expect, type Page } from '@playwright/test';
import { article, desktop, open, phone, schemes, type Scheme } from './support';

// Baselines are recorded with macOS Chromium. Text rasterises differently on other systems,
// so the comparison runs only where the reviewed baselines were made; the behavioural design
// tests run everywhere.
test.skip(process.platform !== 'darwin', 'Reviewed screenshot baselines are macOS Chromium renders.');

async function settle(page: Page): Promise<void> {
  await page.evaluate(() => document.fonts.ready);
  await expect(page.locator('site-search button[data-open-modal]')).toBeEnabled();
  await page.mouse.move(0, 0);
}

const pages = [
  { name: 'article', path: article },
  { name: 'overview', path: '/' },
] as const;

for (const { name, path } of pages) {
  for (const [size, viewport] of [['phone', phone], ['desktop', desktop]] as const) {
    for (const scheme of schemes) {
      test(`${name} at ${size} size in ${scheme} mode`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await open(page, path, scheme);
        await settle(page);
        await expect(page).toHaveScreenshot(`${name}-${size}-${scheme}.png`, { maxDiffPixelRatio: 0.002 });
      });
    }
  }
}

test('runner showcase at desktop size in light mode', async ({ page }) => {
  await page.setViewportSize(desktop);
  await open(page, '/runners/', 'light');
  await settle(page);
  await expect(page).toHaveScreenshot('runners-desktop-light.png', { maxDiffPixelRatio: 0.002 });
});

for (const scheme of ['light', 'dark'] as Scheme[]) {
  test(`open drawer at phone size in ${scheme} mode`, async ({ page }) => {
    await page.setViewportSize(phone);
    await open(page, article, scheme);
    await settle(page);
    await page.getByRole('button', { name: 'Menu' }).click();
    await expect(page.locator('#starlight__sidebar')).toHaveCSS('transform', 'none');
    await expect(page).toHaveScreenshot(`drawer-phone-${scheme}.png`, { maxDiffPixelRatio: 0.002 });
  });
}
