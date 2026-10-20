import { test, expect, type BrowserContext, type Page } from '@playwright/test';
import { article, desktop, open, phone } from './support';

/**
 * The origin of the site under test, taken from the configured base address, so clipboard
 * permissions follow whichever port the preview server uses.
 */
function siteOrigin(baseURL: string | undefined): string {
  if (!baseURL) throw new Error('The Playwright configuration must set a base URL for the site under test');
  return new URL(baseURL).origin;
}

/** Fails unless the page under test is served from the origin that permissions were set for. */
function expectSiteOrigin(page: Page, origin: string): void {
  expect(new URL(page.url()).origin, 'clipboard permissions apply to the tested site only').toBe(origin);
}

async function allowClipboard(context: BrowserContext, origin: string): Promise<void> {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin });
}

/**
 * Denies clipboard writing at the browser level for the tested site, as a viewer's site
 * settings would. The setting names the test's own browser context; without it Chromium
 * applies the setting to its default context, which the test page does not use. The browser
 * session stays open, because the setting lasts only as long as the session that made it.
 */
async function denyClipboardWrite(page: Page, origin: string): Promise<void> {
  const target = await page.context().newCDPSession(page);
  const { targetInfo } = await target.send('Target.getTargetInfo');
  await target.detach();
  const browser = await page.context().browser()!.newBrowserCDPSession();
  await browser.send('Browser.setPermission', {
    permission: { name: 'clipboard-write' },
    setting: 'denied',
    origin,
    browserContextId: targetInfo.browserContextId,
  });
}

/** The clipboard-write permission as the page under test sees it. */
async function clipboardWriteState(page: Page): Promise<string> {
  return page.evaluate(async () => (await navigator.permissions.query({ name: 'clipboard-write' as PermissionName })).state);
}

async function clipboard(page: Page): Promise<string> {
  return page.evaluate(() => navigator.clipboard.readText());
}

test.describe('search', () => {
  test('the search button names its visible shortcut and opens with a click', async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    const button = page.locator('site-search button[data-open-modal]');
    await expect(button).toBeEnabled();
    const shortcut = (await button.locator('kbd kbd').allTextContents()).join(' ');
    expect(shortcut).toMatch(/^(Ctrl|⌘) K$/);
    await expect(button).toHaveAccessibleName(`Search ${shortcut}`);
    await expect(button).toHaveAttribute('aria-keyshortcuts', /^(Control|Meta)\+K$/);

    await button.click();
    const dialog = page.getByRole('dialog', { name: 'Search' });
    await expect(dialog).toBeVisible();
    const input = dialog.locator('input.pagefind-ui__search-input');
    await expect(input).toBeFocused();

    await input.fill('quillwort');
    const result = dialog.locator('.pagefind-ui__result-link').first();
    await expect(result).toHaveText('Writing checks');
    await expect(result).toHaveAttribute('href', /\/authors\/checks\/$/);

    await input.fill('zzqxnomatch');
    await expect(dialog.getByText('No results for zzqxnomatch')).toBeVisible();
    await expect(dialog.locator('.pagefind-ui__result')).toHaveCount(0);

    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
    await expect(button, 'focus returns to the search button').toBeFocused();
  });

  test('the keyboard shortcut opens and closes search, and results are reachable by keyboard', async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, '/', 'dark');
    await expect(page.locator('site-search button[data-open-modal]')).toBeEnabled();
    // Pagefind builds its input when the browser is idle; the shortcut is tested once it exists.
    await expect(page.locator('#starlight__search input')).toBeAttached();
    await page.keyboard.press('Control+k');
    const dialog = page.getByRole('dialog', { name: 'Search' });
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('input.pagefind-ui__search-input')).toBeFocused();
    await page.keyboard.type('quillwort');
    const result = dialog.locator('.pagefind-ui__result-link').first();
    await expect(result).toHaveText('Writing checks');
    await page.keyboard.press('Tab');
    await expect(dialog.locator(':focus')).toHaveCount(1);
    await page.keyboard.press('Control+k');
    await expect(dialog).toBeHidden();
  });

  test('search stays reachable as an icon button on a phone', async ({ page }) => {
    await page.setViewportSize(phone);
    await open(page, article, 'light');
    const button = page.locator('site-search button[data-open-modal]');
    await expect(button).toBeVisible();
    await expect(button.locator('kbd').first()).toBeHidden();
    await expect(button).toHaveAccessibleName(/^Search/);
    await button.click();
    await expect(page.getByRole('dialog', { name: 'Search' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByRole('dialog', { name: 'Search' })).toBeHidden();
  });
});

test.describe('banner and theme', () => {
  test('dismissing the banner closes it on later pages and moves focus to the site title', async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, '/', 'light');
    const banner = page.locator('.ac-banner');
    await expect(banner).toBeVisible();
    await page.getByRole('button', { name: 'Dismiss announcement' }).click();
    await expect(banner).toBeHidden();
    await expect(page.locator('header.header .site-title'), 'focus moves to the site title').toBeFocused();
    expect((await page.locator('header.header').boundingBox())!.y, 'the top bar moves up to the window edge').toBe(0);
    await page.reload();
    await expect(banner, 'the banner stays dismissed').toBeHidden();
    expect((await page.locator('header.header').boundingBox())!.y).toBe(0);
  });

  test('the theme toggle switches theme with the keyboard, names the next theme and keeps the choice', async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, '/', 'light');
    const toggle = page.locator('header ac-theme-toggle button');
    await expect(toggle).toHaveAccessibleName('Switch to dark theme');
    await toggle.focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(toggle).toHaveAccessibleName('Switch to light theme');
    await page.goto(article);
    await expect(page.locator('html'), 'the chosen theme carries to the next page').toHaveAttribute('data-theme', 'dark');
    await page.locator('header ac-theme-toggle button').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    expect(await page.evaluate(() => localStorage.getItem('starlight-theme'))).toBe('light');
  });
});

test.describe('copy controls', () => {
  test('Copy page copies the readable article and says so', async ({ page, context, baseURL }) => {
    const origin = siteOrigin(baseURL);
    await allowClipboard(context, origin);
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    expectSiteOrigin(page, origin);
    expect(await clipboardWriteState(page)).toBe('granted');
    await page.evaluate(() => navigator.clipboard.writeText('before'));
    const button = page.getByRole('button', { name: 'Copy page' });
    await button.focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('.ac-copy-page [role="status"]')).toHaveText('Page copied to the clipboard.');
    const text = await clipboard(page);
    expect(text.startsWith('Writing checks\n\nDesign fixture for a long guide page.')).toBe(true);
    expect(text).toContain('The rare word quillwort appears only here');
    expect(text).toContain('echo "Sample check passed"');
    expect(text).toContain('Sample callout');
    for (const control of ['Copy page', 'Copy to clipboard', 'Section titled', 'Runner showcase', 'On this page', 'For course authors']) {
      expect(text, `copied text excludes "${control}"`).not.toContain(control);
    }
  });

  test('Copy page reports a refused clipboard honestly', async ({ page, baseURL }) => {
    const origin = siteOrigin(baseURL);
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    expectSiteOrigin(page, origin);
    await denyClipboardWrite(page, origin);
    expect(await clipboardWriteState(page), 'the refusal applies to the tested site').toBe('denied');
    await page.getByRole('button', { name: 'Copy page' }).click();
    const status = page.locator('.ac-copy-page [role="status"]');
    await expect(status).toHaveText('Copy failed: the browser blocked clipboard access.');
    await expect(status).not.toContainText('copied to');
  });

  test('Copy page reports an empty article instead of copying nothing', async ({ page, context, baseURL }) => {
    const origin = siteOrigin(baseURL);
    await allowClipboard(context, origin);
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    expectSiteOrigin(page, origin);
    expect(await clipboardWriteState(page)).toBe('granted');
    await page.evaluate(() => navigator.clipboard.writeText('unchanged'));
    await page.locator('.sl-markdown-content').evaluate((el) => el.replaceChildren());
    await page.getByRole('button', { name: 'Copy page' }).click();
    await expect(page.locator('.ac-copy-page [role="status"]')).toHaveText('Nothing to copy: this page has no article text.');
    expect(await clipboard(page)).toBe('unchanged');
  });

  test('a code block copies exactly its code and announces it', async ({ page, context, baseURL }) => {
    const origin = siteOrigin(baseURL);
    await allowClipboard(context, origin);
    await page.setViewportSize(phone);
    await open(page, article, 'dark');
    expectSiteOrigin(page, origin);
    expect(await clipboardWriteState(page)).toBe('granted');
    const block = page.getByRole('figure', { name: 'checks/sample-check.sh' });
    const copy = block.getByRole('button', { name: 'Copy to clipboard' });
    await expect(copy).toBeVisible();
    await copy.focus();
    await page.keyboard.press('Enter');
    await expect(block.locator('[aria-live]')).toHaveText('Copied!');
    const text = await clipboard(page);
    expect(text.startsWith('#!/bin/sh\n')).toBe(true);
    expect(text.endsWith('echo "Sample check passed"')).toBe(true);
  });

  test('a refused code copy never claims success without copying', async ({ page, context, baseURL }) => {
    const origin = siteOrigin(baseURL);
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    expectSiteOrigin(page, origin);
    await context.grantPermissions(['clipboard-read'], { origin });
    await page.evaluate(() => navigator.clipboard.writeText('unchanged').catch(() => undefined));
    await denyClipboardWrite(page, origin);
    expect(await clipboardWriteState(page), 'the refusal applies to the tested site').toBe('denied');
    const block = page.getByRole('figure', { name: 'checks/sample-check.sh' });
    await block.getByRole('button', { name: 'Copy to clipboard' }).click();
    await page.waitForTimeout(300);
    const announced = (await block.locator('[aria-live]').textContent()) ?? '';
    const copied = await clipboard(page);
    test.info().annotations.push({
      type: 'refused code copy',
      description: announced.includes('Copied!') ? 'announced, and the code reached the clipboard' : 'not announced, and the clipboard kept its earlier text',
    });
    if (announced.includes('Copied!')) {
      expect(copied.endsWith('echo "Sample check passed"'), 'success is only announced when the code reached the clipboard').toBe(true);
    } else {
      expect(copied).not.toContain('Sample check passed');
    }
  });
});
