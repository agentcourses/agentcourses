import { test, expect, type BrowserContext, type Page } from '@playwright/test';
import { article, desktop, open, phone } from './support';

const origin = 'http://127.0.0.1:4321';

async function allowClipboard(context: BrowserContext): Promise<void> {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin });
}

/** Denies clipboard writing at the browser level, as a viewer's site settings would. */
async function denyClipboardWrite(page: Page): Promise<void> {
  const session = await page.context().browser()!.newBrowserCDPSession();
  await session.send('Browser.setPermission', { permission: { name: 'clipboard-write' }, setting: 'denied', origin });
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

test.describe('copy controls', () => {
  test('Copy page copies the readable article and says so', async ({ page, context }) => {
    await allowClipboard(context);
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
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

  test('Copy page reports a refused clipboard honestly', async ({ page }) => {
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    await denyClipboardWrite(page);
    await page.getByRole('button', { name: 'Copy page' }).click();
    const status = page.locator('.ac-copy-page [role="status"]');
    await expect(status).toHaveText('Copy failed: the browser blocked clipboard access.');
    await expect(status).not.toContainText('copied to');
  });

  test('Copy page reports an empty article instead of copying nothing', async ({ page, context }) => {
    await allowClipboard(context);
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    await page.evaluate(() => navigator.clipboard.writeText('unchanged'));
    await page.locator('.sl-markdown-content').evaluate((el) => el.replaceChildren());
    await page.getByRole('button', { name: 'Copy page' }).click();
    await expect(page.locator('.ac-copy-page [role="status"]')).toHaveText('Nothing to copy: this page has no article text.');
    expect(await clipboard(page)).toBe('unchanged');
  });

  test('a code block copies exactly its code and announces it', async ({ page, context }) => {
    await allowClipboard(context);
    await page.setViewportSize(phone);
    await open(page, article, 'dark');
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

  test('a refused code copy never claims success without copying', async ({ page, context }) => {
    await page.setViewportSize(desktop);
    await open(page, article, 'light');
    await context.grantPermissions(['clipboard-read'], { origin });
    await page.evaluate(() => navigator.clipboard.writeText('unchanged').catch(() => undefined));
    await denyClipboardWrite(page);
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
