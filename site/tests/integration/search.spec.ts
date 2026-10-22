import { deployed } from './deployment.mjs';
import { test, expect, type Page } from '@playwright/test';

async function openSearch(page: Page) {
  // Starlight enables the button before its idle-loaded Pagefind input exists.
  await expect(page.locator('site-search input.pagefind-ui__search-input')).toBeAttached();
  await page.locator('site-search button[data-open-modal]').click();
  const dialog = page.getByRole('dialog', { name: 'Search' });
  await expect(dialog).toBeVisible();
  const input = dialog.locator('input.pagefind-ui__search-input');
  await expect(input).toBeFocused();
  return { dialog, input };
}

test('Pagefind searches distinctive specification body text and reports no results', async ({ page }) => {
  await page.goto(deployed('/'));
  const { dialog, input } = await openSearch(page);
  await input.fill('Unicode full case folding');
  const result = dialog.locator('.pagefind-ui__result-link').first();
  expect(new URL((await result.getAttribute('href'))!, page.url()).pathname).toBe(deployed('/specification/'));
  await result.click();
  await expect(page).toHaveURL(/\/specification\//);
  await expect(page.locator('main')).toContainText('Unicode full case folding');
  await page.waitForLoadState('load');
  await openSearch(page);
  await input.fill('zzqxnomatchproduction');
  await expect(dialog.getByText('No results for zzqxnomatchproduction')).toBeVisible();
  await expect(dialog.locator('.pagefind-ui__result')).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
});
test('design-only search text is absent from production Pagefind', async ({ page }) => {
  await page.goto(deployed('/'));
  const { dialog, input } = await openSearch(page);
  await input.fill('quillwort');
  await expect(dialog.getByText('No results for quillwort')).toBeVisible();
});
