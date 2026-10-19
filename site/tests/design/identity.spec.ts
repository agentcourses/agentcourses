import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { article, channels, desktop, isNeutral, open, phone, schemes } from './support';

const surfaces = { light: 'rgb(255, 255, 255)', dark: 'rgb(14, 14, 14)' };
const codePanels = { light: 'rgb(22, 22, 22)', dark: 'rgb(23, 23, 22)' };

async function style(page: Page, selector: string, property: string): Promise<string> {
  return page.locator(selector).first().evaluate((el, name) => getComputedStyle(el).getPropertyValue(name), property);
}

function px(value: string): number {
  return Number.parseFloat(value);
}

for (const scheme of schemes) {
  test(`typefaces, hierarchy and surfaces follow the identity in ${scheme} mode`, async ({ page }) => {
    const foreign: string[] = [];
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (url.hostname !== '127.0.0.1') foreign.push(request.url());
    });
    await page.setViewportSize(desktop);
    await open(page, article, scheme);
    await page.evaluate(() => document.fonts.ready);

    expect(await style(page, 'main h1', 'font-family')).toMatch(/^"Source Serif 4"/);
    expect(await style(page, '.sl-markdown-content p', 'font-family')).toMatch(/^"IBM Plex Sans"/);
    expect(await style(page, '.sl-markdown-content h2', 'font-family')).toMatch(/^"IBM Plex Sans"/);
    expect(await style(page, '.expressive-code pre code', 'font-family')).toMatch(/^"IBM Plex Mono"/);
    const loaded = await page.evaluate(() => ({
      title: document.fonts.check('600 38px "Source Serif 4"'),
      body: document.fonts.check('400 16px "IBM Plex Sans"'),
      mono: document.fonts.check('400 13px "IBM Plex Mono"'),
      faces: [...document.fonts].filter((face) => face.status === 'loaded').map((face) => face.family.replaceAll('"', '')),
    }));
    expect(loaded.title && loaded.body && loaded.mono, 'all three local typefaces are available').toBe(true);
    expect(new Set(loaded.faces)).toEqual(new Set(['Source Serif 4', 'IBM Plex Sans', 'IBM Plex Mono']));
    expect(foreign, 'no request leaves the site').toEqual([]);

    const h1 = px(await style(page, 'main h1', 'font-size'));
    const h2 = px(await style(page, '.sl-markdown-content h2', 'font-size'));
    const h3 = px(await style(page, '.sl-markdown-content h3', 'font-size'));
    const body = px(await style(page, '.sl-markdown-content p', 'font-size'));
    expect(h1).toBeGreaterThanOrEqual(30);
    expect(h1).toBeLessThanOrEqual(38);
    expect(await style(page, 'main h1', 'font-weight')).toBe('600');
    expect(h2).toBe(24);
    expect(await style(page, '.sl-markdown-content h2', 'font-weight')).toBe('600');
    expect(h3).toBe(18);
    expect(body).toBe(16);
    expect(px(await style(page, '.sl-markdown-content p', 'line-height'))).toBeCloseTo(27.2, 1);
    await expect(page.locator('.ac-page-description')).toHaveText(/^Design fixture for a long guide page\./);
    expect(px(await style(page, '.ac-page-description', 'font-size'))).toBe(18);
    await expect(page.locator('.ac-page-crumb')).toHaveText('For course authors');

    expect(await style(page, 'body', 'background-color')).toBe(surfaces[scheme]);
    expect(await style(page, '.expressive-code pre', 'background-color')).toBe(codePanels[scheme]);
    expect(await style(page, '.expressive-code pre code', 'color')).toBe('rgb(236, 236, 234)');
    expect(px(await style(page, '.header', 'height'))).toBe(60);

    const tinted = await page.evaluate(() => {
      const found: string[] = [];
      for (const el of document.querySelectorAll<HTMLElement>('body *')) {
        if (!el.checkVisibility()) continue;
        const computed = getComputedStyle(el);
        for (const property of ['color', 'background-color', 'border-top-color', 'border-left-color', 'fill', 'stroke']) {
          const value = computed.getPropertyValue(property);
          if (value.startsWith('rgb')) found.push(`${el.tagName.toLowerCase()}.${[...el.classList].join('.')} ${property} ${value}`);
        }
      }
      return found;
    });
    const coloured = tinted.filter((entry) => !isNeutral(entry.slice(entry.indexOf('rgb'))));
    expect(coloured, 'every visible colour is a neutral grey').toEqual([]);
  });
}

test('the open-book mark sits beside the wordmark and serves locally', async ({ page, request }) => {
  await page.setViewportSize(desktop);
  await open(page, '/', 'light');
  const title = page.locator('a.site-title');
  await expect(title).toHaveAccessibleName('Agent Courses');
  const mark = title.locator('.ac-mark');
  await expect(mark).toBeVisible();
  await expect(mark).toHaveAttribute('aria-hidden', 'true');
  expect(await mark.evaluate((el) => getComputedStyle(el).maskImage)).toContain('/mark.svg');
  expect(await mark.evaluate((el) => getComputedStyle(el).backgroundColor)).toBe(await title.evaluate((el) => getComputedStyle(el).color));
  expect((await mark.boundingBox())!.width).toBe(26);
  await expect(title.locator('.ac-wordmark')).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('lang', 'en-GB');
  expect(await page.locator('link[rel~="icon"]').getAttribute('href')).toBe('/mark.svg');
  const served = await request.get('/mark.svg');
  expect(served.status()).toBe(200);
  const source = readFileSync(new URL('../../public/mark.svg', import.meta.url));
  expect(Buffer.compare(await served.body(), source)).toBe(0);
});

test('the header compacts at 640 pixels and cards stack at 620 pixels', async ({ page }) => {
  const wordmarkWidth = async () => page.locator('a.site-title .ac-wordmark').evaluate((el) => el.getBoundingClientRect().width);
  await page.setViewportSize({ width: 641, height: 900 });
  await open(page, '/', 'light');
  expect(await wordmarkWidth(), 'wordmark shown above 640 pixels').toBeGreaterThan(40);
  await page.setViewportSize({ width: 640, height: 900 });
  expect(await wordmarkWidth(), 'wordmark hidden at 640 pixels').toBeLessThanOrEqual(1);
  await expect(page.locator('a.site-title')).toHaveAccessibleName('Agent Courses');

  const cards = page.locator('.sl-link-card');
  await page.setViewportSize({ width: 621, height: 900 });
  const [wideA, wideB] = [await cards.nth(0).boundingBox(), await cards.nth(1).boundingBox()];
  expect(wideA!.y, 'two columns above 620 pixels').toBe(wideB!.y);
  await page.setViewportSize({ width: 620, height: 900 });
  const [narrowA, narrowB] = [await cards.nth(0).boundingBox(), await cards.nth(1).boundingBox()];
  expect(narrowA!.x, 'one column at 620 pixels').toBe(narrowB!.x);
  expect(narrowB!.y).toBeGreaterThan(narrowA!.y);
});

test('runner tiles and stages use neutral outlines on a phone', async ({ page }) => {
  await page.setViewportSize(phone);
  await open(page, '/', 'dark');
  const last = page.locator('.ac-stages > li').last();
  const mark = last.locator('.ac-stages__mark');
  expect(channels(await mark.evaluate((el) => getComputedStyle(el).backgroundColor))[3], 'the final stage is filled').toBe(1);
  const columns = await page.locator('.ac-stages').evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(' ').length);
  expect(columns, 'stages use two columns on a phone').toBe(2);
  await expect(page.locator('.ac-runner--invitation .ac-runner__logo')).toHaveCSS('border-top-style', 'dashed');
});
