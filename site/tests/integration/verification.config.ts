import base from '../../playwright.config';
import { fileURLToPath } from 'node:url';
import { deployment } from './deployment.mjs';
const port = Number(process.env.AC_TEST_PORT);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('AC_TEST_PORT must be a valid port');
const url = `http://127.0.0.1:${port}`;
export default {
  ...base,
  testDir: fileURLToPath(new URL('./', import.meta.url)),
  testMatch: '**/*.spec.ts',
  use: { ...base.use, baseURL: url },
  webServer: { ...base.webServer, cwd: fileURLToPath(new URL('../../', import.meta.url)), command: `pnpm run preview --port ${port} --ignore-lock`, url: url + deployment.base },
};
