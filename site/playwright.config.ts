import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { deploymentProfile } from './scripts/deployment.mjs';

process.env.PLAYWRIGHT_BROWSERS_PATH ??= fileURLToPath(new URL('./.browsers', import.meta.url));

const design = process.env.AC_SITE_MODE === 'design';
const deployment = deploymentProfile(design ? 'design' : 'production');
const directory = fileURLToPath(new URL(design ? './tests/design' : './tests', import.meta.url));
const productionDirectory = fileURLToPath(new URL('./tests/', import.meta.url)).replaceAll('\\', '/').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
if (!existsSync(fileURLToPath(new URL('./tests/smoke.spec.ts', import.meta.url)))) {
  throw new Error('The required production smoke test is missing');
}
export default defineConfig({
  testDir: directory,
  // Playwright matches absolute paths, so checkout directory names must not select suites.
  testMatch: design ? '**/*.spec.ts' : new RegExp(`^${productionDirectory}(?:smoke\\.spec\\.ts|integration/.*\\.spec\\.ts)$`),
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:4321', ...devices['Desktop Chrome'] },
  webServer: {
    command: 'pnpm run preview --port 4321 --ignore-lock',
    url: 'http://127.0.0.1:4321' + deployment.base,
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
