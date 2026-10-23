import { test, expect, type Page } from '@playwright/test';
import { desktop, phone, open, contrast } from './support';

async function dismiss(page: Page) {
  const button = page.getByRole('button', { name: 'Dismiss announcement' });
  await button.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.ac-banner')).toBeHidden();
  await expect(page.locator('header .site-title')).toBeFocused();
}

// Change served notice copy or identity without changing the browser's stored dismissal.
async function noticeVariant(page: Page, variant: 'wording' | 'candidate') {
  await page.route('**/*', async (route) => {
    if (route.request().resourceType() !== 'document') return route.continue();
    const response = await route.fetch();
    let body = await response.text();
    if (variant === 'wording') body = body.replaceAll('This is the documentation design fixture.', 'Updated design notice for this candidate.');
    else body = body.replace(/data-candidate="[^"]*"/g, 'data-candidate="next-design-candidate"');
    await route.fulfill({ response, body });
  });
}

test('teaching precedes reader tasks', async ({ page }) => {
  await open(page, '/');
  const tasks = page.getByRole('navigation', { name: 'Choose your next task' });
  await expect(tasks).toBeVisible();
  await expect(tasks.getByRole('link')).toHaveText(['Write a small course', 'Check author requirements', 'Add course support', 'Check runner duties']);
  const exchange = page.getByRole('region', { name: 'A teaching exchange' });
  await expect(exchange.locator('li')).toHaveText([
    'Tutor What should your project help someone do?',
    'Learner Make a clear first contribution.',
    'Tutor Choose the first change. Then explain why it helps.',
  ]);
  expect(await exchange.evaluate((el) => !!(el.compareDocumentPosition(document.querySelector('[aria-label="Choose your next task"]')!) & Node.DOCUMENT_POSITION_FOLLOWING))).toBe(true);
  await expect(tasks.getByRole('link', { name: 'Write a small course' })).toHaveAttribute('href', '/authors/quickstart/');
  await tasks.getByRole('link', { name: 'Write a small course' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Quickstart');
});

for (const [name, viewport, control] of [
  ['phone', phone, 'mobile-starlight-toc'],
  ['desktop', desktop, 'starlight-toc'],
] as const) {
  test(`direct subsection selects on ${name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await open(page, '/specification/#a-sample-subsection');
    const selected = page.locator(`${control} a[aria-current="true"]`);
    await expect(selected).toHaveCount(1);
    await expect(selected).toHaveAttribute('href', '#a-sample-subsection');
    for (const view of ['starlight-toc', 'mobile-starlight-toc']) {
      await expect(page.locator(`${view} a[aria-current="true"]`)).toHaveCount(1);
      await expect(page.locator(`${view} a[aria-current="true"]`)).toHaveAttribute('href', '#a-sample-subsection');
    }
    // Wait for Starlight's idle observer as well as the initial fragment selection.
    await page.waitForTimeout(350);
    await expect(selected).toHaveAttribute('href', '#a-sample-subsection');
    await page.evaluate(() => { location.hash = '#sample-section-two'; });
    await expect(selected).toHaveAttribute('href', '#sample-section-two');
    await page.goBack();
    await expect(selected).toHaveAttribute('href', '#a-sample-subsection');
    await page.goForward();
    await expect(selected).toHaveAttribute('href', '#sample-section-two');
    await page.evaluate(() => { location.hash = '#unknown-subsection'; });
    await expect(page.locator('starlight-toc a[aria-current], mobile-starlight-toc a[aria-current]')).toHaveCount(0);
    if (name === 'phone') await expect(page.locator('mobile-starlight-toc .display-current')).toHaveText('');
  });
}

test('dismissal belongs to candidate', async ({ page }) => {
  await open(page, '/');
  await dismiss(page);
  await page.reload();
  await expect(page.locator('.ac-banner')).toBeHidden();
  await noticeVariant(page, 'wording');
  await page.reload();
  await expect(page.locator('.ac-banner')).toBeHidden();
});

test('new candidate returns notice', async ({ page }) => {
  await open(page, '/');
  await dismiss(page);
  await noticeVariant(page, 'candidate');
  await page.reload();
  await expect(page.locator('.ac-banner')).toBeVisible();
});

test('licence and candidate survive dismissal', async ({ page }) => {
  await open(page, '/');
  await dismiss(page);
  const footer = page.getByRole('region', { name: 'Publication status and licence' });
  await expect(footer).toContainText('Design candidate');
  const licence = footer.getByRole('link', { name: 'Apache-2.0' });
  await expect(licence).toHaveAttribute('href', '/specification/#licence');
  const colours = await licence.evaluate((el) => ({ fg: getComputedStyle(el).color, bg: getComputedStyle(document.body).backgroundColor }));
  expect(contrast(colours.fg, colours.bg)).toBeGreaterThanOrEqual(4.5);
});


test('source adapter rejects invalid sources before rendering', async () => {
  const { readingPaths, sampleReadingSource } = await import('../../src/components/reading-paths');
  expect(readingPaths(sampleReadingSource)).toBe(sampleReadingSource);
  const invalid = [
    { ...sampleReadingSource, candidate: ' ' },
    { ...sampleReadingSource, author: [] },
    { ...sampleReadingSource, runner: [] },
    { ...sampleReadingSource, exchange: [] },
    { ...sampleReadingSource, exchange: [{ speaker: 'other', text: 'Sample' }] },
    ...['', 'https://outside.example/', '//outside.example/', '/\\outside', '/%2f%2foutside', '/%5coutside', '/%2e%2e/outside', '/bad path', '/%zz'].flatMap((href) => [
      { ...sampleReadingSource, author: [{ label: 'Write', href }] },
      { ...sampleReadingSource, runner: [{ label: 'Build', href }] },
      { ...sampleReadingSource, licence: { label: 'Licence', href } },
    ]),
    { ...sampleReadingSource, author: [{ label: '', href: '/' }] },
    { ...sampleReadingSource, runner: [{ label: ' ', href: '/' }] },
    { ...sampleReadingSource, licence: { label: '', href: '/' } },
  ];
  for (const source of invalid) expect(() => readingPaths(source as typeof sampleReadingSource)).toThrow('Invalid reading source:');
});

test('candidate storage refusal still permits keyboard dismissal', async ({ page }) => {
  await page.addInitScript(() => {
    const attempts = { get: [] as string[], set: [] as string[], remove: [] as string[] };
    Reflect.set(window, 'candidateStorageAttempts', attempts);
    const get = Storage.prototype.getItem;
    const set = Storage.prototype.setItem;
    const remove = Storage.prototype.removeItem;
    Storage.prototype.getItem = function (key) {
      if (key.startsWith('ac-candidate-dismissed:')) {
        attempts.get.push(key);
        throw new DOMException('Storage refused', 'SecurityError');
      }
      return get.call(this, key);
    };
    Storage.prototype.setItem = function (key, value) {
      if (key.startsWith('ac-candidate-dismissed:')) {
        attempts.set.push(key);
        throw new DOMException('Storage refused', 'SecurityError');
      }
      return set.call(this, key, value);
    };
    Storage.prototype.removeItem = function (key) {
      if (key.startsWith('ac-candidate-dismissed:')) {
        attempts.remove.push(key);
        throw new DOMException('Storage refused', 'SecurityError');
      }
      return remove.call(this, key);
    };
  });
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.setViewportSize(phone);
  await open(page, '/');
  await dismiss(page);
  await expect(page.getByRole('region', { name: 'Publication status and licence' })).toContainText('Design candidate');
  expect(await page.evaluate(() => Reflect.get(window, 'candidateStorageAttempts'))).toEqual({
    get: ['ac-candidate-dismissed:Design candidate'],
    set: ['ac-candidate-dismissed:Design candidate'],
    remove: [], // Dismissal stores identity; it does not delete a preference.
  });
  expect(errors).toEqual([]);
});

for (const viewport of [phone, desktop]) {
  for (const scheme of ['light', 'dark'] as const) {
    test(`licence is readable after dismissal at ${viewport.width} in ${scheme}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await open(page, '/', scheme);
      await dismiss(page);
      const licence = page.getByRole('region', { name: 'Publication status and licence' }).getByRole('link', { name: 'Apache-2.0' });
      await licence.scrollIntoViewIfNeeded();
      await expect(licence).toBeVisible();
      const colours = await licence.evaluate((el) => ({ fg: getComputedStyle(el).color, bg: getComputedStyle(document.body).backgroundColor }));
      expect(contrast(colours.fg, colours.bg)).toBeGreaterThanOrEqual(4.5);
      await licence.focus();
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(/\/specification\/#licence$/);
      await expect(page.getByRole('heading', { name: 'Licence', exact: true })).toBeVisible();
    });
  }
}
