import { test, expect, type Page } from '@playwright/test';
import { article, desktop, destinations, missingFixtures, open, phone } from './support';

const pane = '#starlight__sidebar';

async function focusedRegion(page: Page): Promise<string> {
  return page.evaluate(() => {
    const active = document.activeElement;
    if (!active || active === document.body) return 'outside';
    if (active.closest('.main-frame')) return 'main';
    if (active.closest('#starlight__sidebar')) return 'drawer';
    if (active.closest('header.header')) return 'header';
    if (active.closest('.sl-menu-button')) return 'menu';
    return `other:${active.tagName.toLowerCase()}`;
  });
}

async function drawerOpen(page: Page): Promise<boolean> {
  return page.locator(pane).evaluate((el) => el.matches(':popover-open'));
}

test('every one of the nine destinations has its own fixture', () => {
  expect(missingFixtures(), 'fixtures that a design build would miss').toEqual([]);
});

test('the sidebar lists the nine destinations in order and marks the current page', async ({ page }) => {
  await page.setViewportSize(desktop);
  for (const destination of destinations) {
    await open(page, destination.path, 'light');
    const links = page.locator(`${pane} a`);
    expect(await links.evaluateAll((items) => items.map((item) => new URL((item as HTMLAnchorElement).href).pathname)))
      .toEqual(destinations.map((d) => d.path));
    await expect(links).toHaveText(destinations.map((d) => d.label));
    const current = page.locator(`${pane} a[aria-current="page"]`);
    await expect(current).toHaveCount(1);
    await expect(current).toHaveAttribute('href', destination.path);
  }
  await expect(page.locator(`${pane} summary`)).toHaveText(['For course authors', 'For runner implementers']);
});

test('the sidebar is docked above 980 pixels and becomes a drawer at 980', async ({ page }) => {
  await page.setViewportSize({ width: 981, height: 900 });
  await open(page, article, 'light');
  const menu = page.getByRole('button', { name: 'Menu' });
  await expect(menu).toBeHidden();
  await expect(page.locator(pane)).toBeVisible();
  expect(await page.locator(pane).getAttribute('popover')).toBeNull();

  await page.setViewportSize({ width: 980, height: 900 });
  await expect(menu).toBeVisible();
  await expect(page.locator(pane)).toBeHidden();
  await expect(page.locator(pane)).toHaveAttribute('popover', 'auto');
  const main = await page.locator('main').boundingBox();
  expect(main!.x, 'content uses the full width once the sidebar is a drawer').toBeLessThan(40);
});

for (const viewport of [phone, { width: 980, height: 900 }]) {
  test(`the drawer is keyboard operable at ${viewport.width} pixels`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await open(page, article, 'light');
    const menu = page.getByRole('button', { name: 'Menu' });
    // The page behind must turn inert in the same task that opens the drawer, and back again
    // when it closes; a later event would let a fast Tab reach the page first.
    const inert = await page.evaluate(() => {
      const main = document.querySelector<HTMLElement>('.main-frame')!;
      document.querySelector<HTMLElement>('.sl-menu-button')!.click();
      const opened = main.inert;
      document.getElementById('starlight__sidebar')!.hidePopover();
      return { opened, closed: main.inert };
    });
    expect(inert, 'inert follows the drawer synchronously').toEqual({ opened: true, closed: false });

    await menu.focus();
    await page.keyboard.press('Enter');
    await expect(page.locator(pane)).toBeVisible();
    expect(await drawerOpen(page)).toBe(true);
    await expect(page.locator(`${pane} a[aria-current="page"]`)).toBeVisible();

    const regions = new Set<string>();
    for (let step = 0; step < 24; step += 1) {
      await page.keyboard.press('Tab');
      regions.add(await focusedRegion(page));
    }
    expect(regions.has('drawer'), 'tabbing reaches the drawer links').toBe(true);
    expect(regions.has('main'), 'tabbing never reaches the page behind the drawer').toBe(false);

    await page.locator(`${pane} a`).first().focus();
    await page.keyboard.press('Escape');
    expect(await drawerOpen(page), 'Escape closes the drawer').toBe(false);
    await expect(menu, 'focus returns to the menu button').toBeFocused();
    await expect(page.locator(pane)).toBeHidden();

    await page.keyboard.press('Space');
    expect(await drawerOpen(page), 'Space reopens the drawer').toBe(true);
    await page.locator(`${pane} a`, { hasText: 'Conformance' }).focus();
    await page.keyboard.press('Enter');
    await page.waitForURL('**/implementers/conformance/');
    expect(await drawerOpen(page), 'a new page starts with the drawer closed').toBe(false);
  });
}

test('the scrim closes the drawer on a phone', async ({ page }) => {
  await page.setViewportSize(phone);
  await open(page, article, 'dark');
  await page.getByRole('button', { name: 'Menu' }).click();
  expect(await drawerOpen(page)).toBe(true);
  const drawer = await page.locator(pane).boundingBox();
  expect(drawer!.width, 'the drawer leaves part of the page visible').toBeLessThanOrEqual(320);
  await page.mouse.click(phone.width - 10, phone.height - 40);
  expect(await drawerOpen(page)).toBe(false);
});

test('the contents column shows above 1240 pixels and folds into the page control at 1240', async ({ page }) => {
  await page.setViewportSize({ width: 1241, height: 900 });
  await open(page, article, 'light');
  const column = page.locator('.right-sidebar-panel');
  const control = page.locator('mobile-starlight-toc');
  await expect(column).toBeVisible();
  await expect(control).toBeHidden();
  await page.setViewportSize({ width: 1240, height: 900 });
  await expect(column).toBeHidden();
  await expect(control.getByText('On this page')).toBeVisible();
  const heading = page.locator('main h1');
  const top = (await heading.boundingBox())!.y;
  expect(top, 'the folded contents control does not cover the title').toBeGreaterThan(60 + 48);
});
