import { deployed } from './integration/deployment.mjs';
import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

test('the built overview opens with only active production navigation', async ({ page }) => {
  const response = await page.goto(deployed('/'));
  expect(response?.status()).toBe(200);
  expect(response?.headers()['content-type']).toContain('text/html');
  await expect(page.getByRole('heading', { name: 'Agent Courses', exact: true, level: 1 })).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
  const stage = JSON.parse(readFileSync(new URL('../../tools/document-stage.json', import.meta.url), 'utf8')).stage;
  if (stage === 'foundation' || stage === 'course' || stage === 'records') {
    const links = await page.locator('#starlight__sidebar a').evaluateAll((items) => items.map((item) => new URL((item as HTMLAnchorElement).href).pathname));
    expect(links).toEqual([deployed('/')]);
  }
});
