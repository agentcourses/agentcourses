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
    const theme = await box(page, 'header ac-theme-toggle button');

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

test('the pager sits 56 pixels below the page', async ({ page }) => {
  await page.setViewportSize(desktop);
  await open(page, article, 'light');
  const content = await box(page, '.sl-markdown-content');
  const pager = await box(page, '.pagination-links');
  expect(pager.y - (content.y + content.height), 'the gap above the previous and next links').toBeCloseTo(56, 0);
});

test('between 981 and 1240 pixels the folded contents bar spans the page column, gutter to gutter', async ({ page }) => {
  await page.setViewportSize({ width: 1100, height: 900 });
  await open(page, article, 'light');
  const content = await box(page, '.sl-markdown-content');
  const bar = await box(page, 'mobile-starlight-toc nav');
  expect(bar.x, 'the bar starts where the page column starts').toBeCloseTo(content.x, 0);
  expect(bar.x + bar.width, 'the bar stops at the right gutter').toBeCloseTo(1100 - 16, 0);
});

for (const [name, viewport] of [['phone', phone], ['desktop', desktop]] as const) {
  test(`the banner spans the window above the top bar on a ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await open(page, '/', 'light');
    const banner = await box(page, '.ac-banner');
    const header = await box(page, 'header.header');
    expect(banner.x, 'the banner starts at the window edge').toBe(0);
    expect(banner.width, 'the banner spans the window').toBe(viewport.width);
    expect(header.y, 'the top bar starts where the banner ends').toBeCloseTo(banner.y + banner.height, 0);
    const below = header.y + header.height;
    if (name === 'phone') {
      const menu = await box(page, '.sl-menu-button');
      expect(menu.y, 'the menu button sits inside the top bar').toBeGreaterThanOrEqual(header.y);
      expect(menu.y + menu.height, 'the menu button sits inside the top bar').toBeLessThanOrEqual(below);
      await page.getByRole('button', { name: 'Menu' }).click();
      expect((await box(page, '#starlight__sidebar')).y, 'the drawer opens below the top bar').toBeCloseTo(below, 0);
      const shade = await page.locator('#starlight__sidebar').evaluate((el) => parseFloat(getComputedStyle(el, '::backdrop').top));
      expect(shade, 'the shade behind the drawer starts below the top bar').toBeCloseTo(below, 0);
      expect((await box(page, 'mobile-starlight-toc nav')).y, 'the folded contents bar sits below the top bar').toBeCloseTo(below - 1, 0);
    } else {
      expect((await box(page, '.sidebar-pane')).y, 'the sidebar starts below the top bar').toBeCloseTo(below, 0);
      expect((await box(page, '.right-sidebar-container')).y, 'the contents column starts below the top bar').toBeCloseTo(below, 0);
    }
  });
}

for (const [name, viewport] of [['phone', phone], ['desktop', desktop]] as const) {
  test(`an in-page link lands below everything fixed at the top, banner included, on a ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await open(page, '/', 'light');
    await expect(page.locator('.ac-banner')).toBeVisible();
    // On a phone the folded contents bar is the lowest fixed element; on a desktop it is the top bar.
    const fixed = name === 'phone' ? await box(page, 'mobile-starlight-toc nav') : await box(page, 'header.header');
    if (name === 'phone') await page.evaluate(() => { location.hash = '#four-sample-stages'; });
    else await page.locator('.right-sidebar-panel a', { hasText: 'Four sample stages' }).click();
    const heading = page.locator('#four-sample-stages');
    await expect.poll(async () => (await heading.boundingBox())!.y, { message: 'the heading clears the fixed bars by 24 pixels' })
      .toBeCloseTo(fixed.y + fixed.height + 24, 0);
  });
}

test('the overview fixture renders stages, runner tiles, cards and a thesis', async ({ page }) => {
  await page.setViewportSize(desktop);
  await open(page, '/', 'light');
  const main = page.getByRole('main');
  await expect(main.locator('.ac-thesis')).toHaveCount(1);
  await expect(main.locator('.ac-stages > li')).toHaveCount(4);
  await expect(main.locator('.ac-runner')).toHaveCount(2);
  await expect(main.locator('.sl-link-card')).toHaveCount(2);
});
