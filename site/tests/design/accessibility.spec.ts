import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { article, contrast, desktop, destinations, open, phone, schemes } from './support';

const ink = { light: 'rgb(20, 20, 20)', dark: 'rgb(237, 237, 235)' };
/** Code panels are dark in both modes, so their rings use the code text colour. */
const codeInk = 'rgb(236, 236, 234)';

/** Waits until every overflowing code panel and table has joined the tab order. */
async function scrollRegionsSettled(page: Page): Promise<void> {
  await expect.poll(() => page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('.expressive-code pre, .sl-markdown-content table')]
      .filter((el) => el.scrollWidth > el.clientWidth && !el.hasAttribute('tabindex'))
      .map((el) => el.tagName.toLowerCase())), { message: 'overflowing regions without keyboard access' }).toEqual([]);
}

async function audit(page: Page, label: string, regions: string[] = []): Promise<void> {
  await scrollRegionsSettled(page);
  const builder = new AxeBuilder({ page });
  for (const region of regions) builder.include(region);
  const results = await builder.analyze();
  const summary = results.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`);
  expect(summary, `axe violations on ${label}`).toEqual([]);
  expect(results.passes.some((rule) => rule.id === 'color-contrast'), `contrast was evaluated on ${label}`).toBe(true);
}

interface RingSample {
  name: string;
  share: number;
  pixels: number;
}

/**
 * Measures the focused element's ring as a reader sees it. The same clip is captured with and
 * without focus, and each pixel on the straight sides of the outline band is compared between
 * the two captures. `share` is the fraction of those pixels whose colour changes by at least
 * 3:1, so a ring drawn in a colour close to its surroundings scores near zero.
 */
async function ringSample(page: Page): Promise<RingSample | null> {
  const handle = await page.evaluateHandle(() => document.activeElement);
  const geometry = await handle.evaluate((node) => {
    const el = node as HTMLElement | null;
    if (!el || el === document.body || !el.checkVisibility()) return null;
    const style = getComputedStyle(el);
    const box = el.getBoundingClientRect();
    const context = el.closest('.expressive-code') ? 'code ' : el.closest('.sl-banner') ? 'banner ' : el.closest('.sl-link-card') ? 'card ' : '';
    const label = (el.getAttribute('aria-label') ?? el.getAttribute('title') ?? el.textContent ?? '').trim().replace(/\s+/g, ' ').slice(0, 28);
    return {
      name: `${context}${el.tagName.toLowerCase()} "${label}"`,
      x: box.x, y: box.y, w: box.width, h: box.height,
      offset: Number.parseFloat(style.outlineOffset) || 0,
      width: style.outlineStyle === 'none' ? 0 : Number.parseFloat(style.outlineWidth) || 0,
      vw: window.innerWidth, vh: window.innerHeight,
    };
  });
  if (!geometry) return null;
  if (geometry.width === 0) return { name: geometry.name, share: 0, pixels: 0 };
  const reach = Math.max(geometry.offset + geometry.width, 0) + 3;
  const left = Math.max(0, Math.floor(geometry.x - reach));
  const top = Math.max(0, Math.floor(geometry.y - reach));
  const clip = {
    x: left,
    y: top,
    width: Math.min(geometry.vw, Math.ceil(geometry.x + geometry.w + reach)) - left,
    height: Math.min(geometry.vh, Math.ceil(geometry.y + geometry.h + reach)) - top,
  };
  const focused = (await page.screenshot({ clip, animations: 'disabled', caret: 'hide' })).toString('base64');
  await handle.evaluate((el) => (el as HTMLElement).blur());
  const unfocused = (await page.screenshot({ clip, animations: 'disabled', caret: 'hide' })).toString('base64');
  await handle.evaluate((el) => (el as HTMLElement).focus());
  const measured = await page.evaluate(async ({ a, b, g, c }) => {
    const pixels = async (data: string) => {
      const bitmap = await createImageBitmap(await (await fetch(`data:image/png;base64,${data}`)).blob());
      const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
      const context = canvas.getContext('2d')!;
      context.drawImage(bitmap, 0, 0);
      return context.getImageData(0, 0, bitmap.width, bitmap.height);
    };
    const [on, off] = [await pixels(a), await pixels(b)];
    const channel = (v: number) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; };
    const lum = (d: Uint8ClampedArray, i: number) => 0.2126 * channel(d[i]) + 0.7152 * channel(d[i + 1]) + 0.0722 * channel(d[i + 2]);
    const [x0, x1, y0, y1] = [g.x, g.x + g.w, g.y, g.y + g.h];
    let total = 0;
    let changed = 0;
    for (let py = 0; py < on.height; py += 1) {
      for (let px = 0; px < on.width; px += 1) {
        const cx = c.x + px + 0.5;
        const cy = c.y + py + 0.5;
        const withinX = cx >= x0 && cx <= x1;
        const withinY = cy >= y0 && cy <= y1;
        let distance: number;
        if (withinX && withinY) distance = -Math.min(cx - x0, x1 - cx, cy - y0, y1 - cy);
        else if (withinX) distance = cy < y0 ? y0 - cy : cy - y1;
        else if (withinY) distance = cx < x0 ? x0 - cx : cx - x1;
        else continue;
        if (distance < g.offset + 0.5 || distance > g.offset + g.width - 0.5) continue;
        const i = (py * on.width + px) * 4;
        const [l1, l2] = [lum(on.data, i), lum(off.data, i)];
        total += 1;
        if ((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05) >= 3) changed += 1;
      }
    }
    return { share: total ? changed / total : 0, pixels: total };
  }, { a: focused, b: unfocused, g: geometry, c: clip });
  await handle.dispose();
  return { name: geometry.name, ...measured };
}

/** Text colour and the first opaque background behind an element. */
async function colours(page: Page, selector: string): Promise<[string, string]> {
  return page.locator(selector).first().evaluate((el) => {
    let node: Element | null = el;
    let background = 'rgb(255, 255, 255)';
    while (node) {
      const value = getComputedStyle(node).backgroundColor;
      if (value && !value.endsWith(', 0)') && value !== 'transparent') {
        background = value;
        break;
      }
      node = node.parentElement;
    }
    return [getComputedStyle(el).color, background] as [string, string];
  });
}

for (const scheme of schemes) {
  test(`axe finds no violations on any destination in ${scheme} mode`, async ({ page }) => {
    await page.setViewportSize(desktop);
    for (const destination of destinations) {
      await open(page, destination.path, scheme);
      await expect(page.locator('site-search button[data-open-modal]')).toBeEnabled();
      await audit(page, `${destination.path} (${scheme}, desktop)`);
    }
  });
}

// Starlight shows "⌘ K" on Apple platforms and "Ctrl K" elsewhere, so the search button is
// audited under each platform the browser can report, not only the one running the tests.
for (const platform of ['MacIntel', 'Win32', 'Linux x86_64']) {
  test(`the search button passes axe when the platform reports ${platform}`, async ({ page }) => {
    await page.addInitScript((value) => {
      Object.defineProperty(Navigator.prototype, 'platform', { configurable: true, get: () => value });
    }, platform);
    await page.setViewportSize(desktop);
    await open(page, '/', 'light');
    const button = page.locator('site-search button[data-open-modal]');
    await expect(button).toBeEnabled();
    const keys = await button.locator('kbd kbd').allTextContents();
    expect(keys).toEqual([platform === 'MacIntel' ? '⌘' : 'Ctrl', 'K']);
    await expect(button).toHaveAccessibleName(`Search ${keys.join(' ')}`);
    await audit(page, `/ (desktop, ${platform})`);
  });
}

test('overflowing code and tables gain keyboard access even when the browser never goes idle', async ({ page }) => {
  // A busy page may never reach an idle period, so keyboard access must not wait for one.
  await page.addInitScript(() => {
    window.requestIdleCallback = () => 0;
    window.cancelIdleCallback = () => undefined;
  });
  for (const viewport of [desktop, phone]) {
    await page.setViewportSize(viewport);
    await open(page, article, 'light');
    await scrollRegionsSettled(page);
    const regions = page.locator('.expressive-code pre, .sl-markdown-content table');
    for (let index = 0; index < await regions.count(); index += 1) {
      const region = regions.nth(index);
      if (!(await region.evaluate((el) => el.scrollWidth > el.clientWidth))) continue;
      await region.focus();
      await expect(region, `overflowing region ${index} at ${viewport.width} pixels takes keyboard focus`).toBeFocused();
    }
  }
});

test('axe finds no violations on a phone, with the drawer open and with search open', async ({ page }) => {
  await page.setViewportSize(phone);
  for (const destination of destinations) {
    await open(page, destination.path, 'light');
    await audit(page, `${destination.path} (phone)`);
  }
  await open(page, article, 'dark');
  await page.getByRole('button', { name: 'Menu' }).click();
  await expect(page.locator('#starlight__sidebar')).toBeVisible();
  // While the drawer is open Starlight makes the page behind it inert, like a modal, so the
  // audit covers what remains operable: the top bar and the drawer.
  await audit(page, 'open drawer (phone, dark)', ['header.header', '#starlight__sidebar']);
  await page.keyboard.press('Escape');

  await page.setViewportSize(desktop);
  await open(page, article, 'light');
  await expect(page.locator('site-search button[data-open-modal]')).toBeEnabled();
  await expect(page.locator('#starlight__search input')).toBeAttached();
  await page.keyboard.press('Control+k');
  const input = page.locator('#starlight__search input');
  await expect(input).toBeFocused();
  await input.fill('quillwort');
  await expect(page.locator('.pagefind-ui__result-link').first()).toBeVisible();
  await audit(page, 'search results (desktop, light)');
});

for (const scheme of schemes) {
  test(`keyboard focus is a two-pixel ring in its surface's ink, offset by two pixels, in ${scheme} mode`, async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, article, scheme);
    await expect(page.locator('site-search button[data-open-modal]')).toBeEnabled();
    await scrollRegionsSettled(page);
    const seen: string[] = [];
    for (let step = 0; step < 45; step += 1) {
      await page.keyboard.press('Tab');
      const ring = await page.evaluate(() => {
        const el = document.activeElement as HTMLElement | null;
        if (!el || el === document.body || !el.checkVisibility()) return null;
        const style = getComputedStyle(el);
        const code = !!el.closest('.expressive-code');
        const context = el.closest('.sl-link-card') ? 'card ' : code ? 'code ' : '';
        const name = `${context}${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''} "${(el.textContent ?? '').trim().slice(0, 24)}"`;
        // A code panel fills its frame, so its ring sits two pixels inside the edge.
        const inset = code && el.tagName === 'PRE';
        return { name, code, inset, style: style.outlineStyle, width: style.outlineWidth, colour: style.outlineColor, offset: style.outlineOffset };
      });
      if (!ring) continue;
      seen.push(ring.name);
      expect(ring.style, `${ring.name} outline style`).toBe('solid');
      expect(ring.width, `${ring.name} outline width`).toBe('2px');
      expect(ring.colour, `${ring.name} outline colour`).toBe(ring.code ? codeInk : ink[scheme]);
      expect(ring.offset, `${ring.name} outline offset`).toBe(ring.inset ? '-4px' : '2px');
    }
    for (const expected of ['a.site-title', 'button', 'card a', '"Runner showcase"', 'Copy page', 'code pre', 'code button']) {
      expect(seen.some((name) => name.includes(expected)), `focus reached ${expected}`).toBe(true);
    }
  });
}

const ringPages = [
  { label: 'article on desktop', path: article, viewport: desktop },
  { label: 'article on a phone', path: article, viewport: phone },
  { label: 'overview on desktop', path: '/', viewport: desktop },
] as const;

for (const scheme of schemes) {
  for (const { label, path, viewport } of ringPages) {
    test(`every focus ring stands out from what surrounds it: ${label}, ${scheme} mode`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await open(page, path, scheme);
      await expect(page.locator('site-search button[data-open-modal]')).toBeEnabled();
      await scrollRegionsSettled(page);
      await page.evaluate(() => document.fonts.ready);
      const samples: RingSample[] = [];
      for (let step = 0; step < 60; step += 1) {
        await page.keyboard.press('Tab');
        const sample = await ringSample(page);
        if (sample) samples.push(sample);
      }
      const faint = samples
        .filter((s) => s.pixels === 0 || s.share < 0.8)
        .map((s) => `${s.name}: ${(s.share * 100).toFixed(0)}% of ${s.pixels} ring pixels change by 3:1`);
      const lowest = samples.reduce((low, s) => (s.share < low.share ? s : low), samples[0]);
      test.info().annotations.push({ type: 'lowest ring share', description: `${lowest.name}: ${(lowest.share * 100).toFixed(1)}% of ${lowest.pixels} pixels` });
      for (const s of samples.filter((x) => x.name.startsWith('code button') || x.name.startsWith('banner a'))) {
        test.info().annotations.push({ type: 'ring share', description: `${s.name}: ${(s.share * 100).toFixed(1)}% of ${s.pixels} pixels` });
      }
      expect(samples.length, 'focus visited the page controls').toBeGreaterThan(10);
      expect(faint, 'focus rings that blend into their surroundings').toEqual([]);
      if (path === article) {
        expect(samples.some((s) => s.name.startsWith('code button')), 'a code-copy button was measured').toBe(true);
      } else {
        expect(samples.some((s) => s.name.startsWith('banner a')), 'the banner link was measured').toBe(true);
      }
    });
  }
}

test('the drawer animates only when the viewer allows motion', async ({ page }) => {
  await page.setViewportSize(phone);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await open(page, article, 'light');
  const duration = () => page.locator('#starlight__sidebar').evaluate((el) => getComputedStyle(el).transitionDuration);
  expect(await duration()).toContain('0.2s');
  await expect(page.locator('#starlight__sidebar .caret').first()).toHaveCSS('transition-duration', '0.2s');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.getByRole('button', { name: 'Menu' }).click();
  await expect(page.locator('#starlight__sidebar')).toBeVisible();
  expect((await duration()).split(', ').every((value) => value === '0s'), 'no drawer transition under reduced motion').toBe(true);
  const transforms = await page.locator('#starlight__sidebar').evaluate((el) => el.getAnimations().length);
  expect(transforms, 'no running drawer animation').toBe(0);
  const caret = page.locator('#starlight__sidebar .caret').first();
  await expect(caret, 'group carets do not animate').toHaveCSS('transition-duration', '0s');
});

test('wide tables and long code scroll locally and can be reached by keyboard on a phone', async ({ page }) => {
  await page.setViewportSize(phone);
  await open(page, article, 'light');
  await scrollRegionsSettled(page);
  for (const selector of ['.sl-markdown-content table', '.expressive-code pre']) {
    const region = page.locator(selector).first();
    const box = await region.evaluate((el) => ({ scroll: el.scrollWidth, client: el.clientWidth, overflow: getComputedStyle(el).overflowX }));
    expect(box.scroll, `${selector} is wider than its frame`).toBeGreaterThan(box.client);
    expect(['auto', 'scroll']).toContain(box.overflow);
    await region.focus();
    await expect(region, `${selector} accepts keyboard focus`).toBeFocused();
    await expect(region).toHaveAttribute('tabindex', '0');
    await expect(region).toHaveCSS('outline-style', 'solid');
    await expect(region).toHaveCSS('outline-width', '2px');
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowRight');
    await expect.poll(() => region.evaluate((el) => el.scrollLeft), { message: `${selector} scrolls with the keyboard` }).toBeGreaterThan(0);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
});

for (const scheme of schemes) {
  test(`text colour pairs meet 4.5:1 in ${scheme} mode`, async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, '/', scheme);
    const selectors = [
      '.sl-markdown-content p',
      '.ac-page-description',
      '.sidebar-content a:not([aria-current])',
      '.sidebar-content a[aria-current="page"]',
      '.right-sidebar-panel a',
      '.sl-banner',
      '.ac-chip',
      '.ac-stages p',
      '.ac-runner--invitation .ac-runner__logo',
      '.sl-markdown-content th',
      'site-search button[data-open-modal] > span',
      '.sl-link-card .description',
    ];
    for (const selector of selectors) {
      const [fg, bg] = await colours(page, selector);
      expect(contrast(fg, bg), `${selector}: ${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
    }
    await open(page, article, scheme);
    const comment = page.locator('.expressive-code pre .ec-line').nth(1).locator('span').first();
    const [fg, bg] = await comment.evaluate((el) => [getComputedStyle(el).color, getComputedStyle(el.closest('pre')!).backgroundColor]);
    expect(contrast(fg, bg), `code comment: ${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
  });
}
