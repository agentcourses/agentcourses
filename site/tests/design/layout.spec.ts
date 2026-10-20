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
        const frame = main.locator('.sl-markdown-content .ac-table');
        const box = await frame.evaluate((el) => ({ scroll: el.scrollWidth, client: el.clientWidth }));
        expect(box.scroll, 'the wide table scrolls inside its frame').toBeGreaterThan(box.client);
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

async function box(page: Page, selector: string): Promise<{ x: number; y: number; width: number; height: number }> {
  const found = await page.locator(selector).first().boundingBox();
  expect(found, `${selector} is laid out`).not.toBeNull();
  return found!;
}

for (const width of [2000, 1440]) {
  test(`the frame is a centred 1480-pixel shell that the top bar shares at ${width} pixels`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await open(page, '/', 'light');
    const inset = Math.max(0, (width - 1480) / 2) + 16;
    const sidebar = await box(page, '.sidebar-pane');
    const content = await box(page, '.sl-markdown-content');
    const contents = await box(page, '.right-sidebar-panel');
    const title = await box(page, '.site-title');
    const search = await box(page, 'site-search button[data-open-modal]');
    const theme = await box(page, 'starlight-theme-select');

    expect(sidebar.x, 'the sidebar starts at the shell edge').toBeCloseTo(inset, 0);
    expect(title.x, 'the site title lines up with the sidebar').toBeCloseTo(sidebar.x, 0);
    expect(content.x, 'the page starts 48 pixels after the sidebar').toBeCloseTo(sidebar.x + sidebar.width + 48, 0);
    expect(contents.x + contents.width, 'the contents column ends at the shell edge').toBeCloseTo(width - inset, 0);
    expect(theme.x + theme.width, 'the theme control lines up with the contents column').toBeCloseTo(contents.x + contents.width, 0);
    expect(search.x + search.width / 2, 'search is centred in the top bar').toBeCloseTo(width / 2, 0);
  });
}

test('the stages rise in equal steps whatever the length of their text', async ({ page }) => {
  await page.setViewportSize(desktop);
  await open(page, '/', 'light');
  const steps = await page.locator('.ac-stages > li').evaluateAll((items) => items.map((item) => item.getBoundingClientRect()).map(({ top, height }) => ({ top, height })));
  expect(steps).toHaveLength(4);
  for (const step of steps) expect(step.height, 'every step is the same height').toBeCloseTo(steps[0].height, 0);
  for (let i = 1; i < steps.length; i += 1) expect(steps[i - 1].top - steps[i].top, `step ${i + 1} sits 18 pixels above step ${i}`).toBeCloseTo(18, 0);
});

test('a narrow table fills the reading column, header shading included', async ({ page }) => {
  await page.setViewportSize(desktop);
  await open(page, '/', 'light');
  const content = await box(page, '.sl-markdown-content');
  const frame = await box(page, '.sl-markdown-content .ac-table');
  const header = await box(page, '.sl-markdown-content .ac-table thead tr');
  expect(frame.width, 'the table frame spans the reading column').toBeCloseTo(content.width, 0);
  expect(header.width, 'the header row spans its frame, less the two border pixels').toBeCloseTo(frame.width - 2, 0);
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
