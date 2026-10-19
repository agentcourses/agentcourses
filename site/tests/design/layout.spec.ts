import { test, expect, type Page } from '@playwright/test';
import { article, desktop, destinations, open, phone, schemes } from './support';

async function documentOverflow(page: Page): Promise<number> {
  return page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
}

for (const [name, viewport] of [['phone', phone], ['desktop', desktop]] as const) {
  for (const scheme of schemes) {
    test(`the article fixture fits a ${name} viewport in ${scheme} mode`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await open(page, article, scheme);
      const main = page.getByRole('main');
      await expect(page.getByRole('heading', { level: 1, name: 'Writing checks' })).toBeVisible();

      // The fixture exercises headings, long code, a wide table, a callout, cards and numbered steps.
      await expect(main.locator('.sl-markdown-content h2')).toHaveCount(4);
      await expect(main.locator('.sl-markdown-content h3').first()).toBeVisible();
      await expect(main.locator('.expressive-code pre').first()).toBeVisible();
      await expect(main.locator('.sl-markdown-content table')).toHaveCount(1);
      await expect(main.locator('.starlight-aside')).toHaveCount(1);
      await expect(main.locator('.sl-steps > li')).toHaveCount(3);
      await expect(main.locator('.sl-link-card')).toHaveCount(2);
      await expect(main.locator('a[rel="prev"]')).toBeVisible();
      await expect(main.locator('a[rel="next"]')).toBeVisible();

      expect(await documentOverflow(page), 'the document never scrolls sideways').toBeLessThanOrEqual(0);

      const code = main.locator('.expressive-code pre').first();
      const scroll = await code.evaluate((el) => ({ scroll: el.scrollWidth, client: el.clientWidth }));
      expect(scroll.scroll, 'long code scrolls inside its own panel').toBeGreaterThan(scroll.client);

      const content = await main.locator('.sl-markdown-content').boundingBox();
      expect(content).not.toBeNull();
      expect(content!.width, 'the reading column stays within 760 pixels').toBeLessThanOrEqual(760);
      expect(content!.x, 'a left gutter of at least 16 pixels').toBeGreaterThanOrEqual(16);
      expect(viewport.width - (content!.x + content!.width), 'a right gutter of at least 16 pixels').toBeGreaterThanOrEqual(16);

      if (name === 'phone') {
        const table = main.locator('.sl-markdown-content table');
        const box = await table.evaluate((el) => ({ scroll: el.scrollWidth, client: el.clientWidth }));
        expect(box.scroll, 'the wide table scrolls inside itself').toBeGreaterThan(box.client);
      }
    });
  }
}

test('every fixture destination fits a phone without sideways scrolling', async ({ page }) => {
  await page.setViewportSize(phone);
  for (const destination of destinations) {
    await open(page, destination.path, 'light');
    expect(await documentOverflow(page), `${destination.path} has no document overflow`).toBeLessThanOrEqual(0);
  }
});

test('the overview fixture renders stages, runner tiles, cards and a thesis', async ({ page }) => {
  await page.setViewportSize(desktop);
  await open(page, '/', 'light');
  const main = page.getByRole('main');
  await expect(main.locator('.ac-thesis')).toHaveCount(1);
  await expect(main.locator('.ac-stages > li')).toHaveCount(4);
  await expect(main.locator('.ac-runner')).toHaveCount(2);
  await expect(main.locator('.sl-link-card')).toHaveCount(2);
});
