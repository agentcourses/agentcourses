import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

process.env.PLAYWRIGHT_BROWSERS_PATH ??= fileURLToPath(new URL('./.browsers', import.meta.url));

const design = process.env.AC_SITE_MODE === 'design';
const directory = fileURLToPath(new URL(design ? './tests/design' : './tests', import.meta.url));
if (!existsSync(fileURLToPath(new URL('./tests/smoke.spec.ts', import.meta.url)))) {
  throw new Error('The required production smoke test is missing');
}
export default defineConfig({
  testDir: directory,
  testMatch: design ? '**/*.spec.ts' : 'smoke.spec.ts',
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:4321', ...devices['Desktop Chrome'] },
  webServer: {
    command: 'pnpm run preview --port 4321 --ignore-lock',
    url: 'http://127.0.0.1:4321',
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
