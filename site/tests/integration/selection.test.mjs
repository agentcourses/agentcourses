import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const site = fileURLToPath(new URL('../../', import.meta.url));
const require = createRequire(new URL('../../package.json', import.meta.url));
const cli = require.resolve('@playwright/test/cli');
const specimens = [
  'smoke.spec.ts', 'integration/content.spec.ts', 'integration/nested/routes.spec.ts',
  'design/layout.spec.ts', 'design/smoke.spec.ts', 'unrelated/smoke.spec.ts',
];
const selections = [
  ['ordinary production', 'production', [], specimens.slice(0, 3)],
  ['explicit integration', 'production', ['tests/integration'], specimens.slice(1, 3)],
  ['isolated design', 'design', [], specimens.slice(3, 5)],
];

for (const [name, mode, args, expected] of selections) {
  test(`browser selection: ${name} ignores checkout ancestors named integration`, (t) => {
    const temporary = mkdtempSync(join(tmpdir(), 'ac-selection-'));
    t.after(() => rmSync(temporary, { recursive: true, force: true }));
    const directory = join(temporary, 'integration', 'checkout', 'site');
    mkdirSync(directory, { recursive: true });
    for (const file of ['playwright.config.ts', 'package.json', 'scripts/deployment.mjs']) {
      const destination = join(directory, file);
      mkdirSync(dirname(destination), { recursive: true });
      cpSync(join(site, file), destination);
    }
    symlinkSync(join(site, 'node_modules'), join(directory, 'node_modules'), 'dir');
    for (const specimen of specimens) {
      const path = join(directory, 'tests', specimen);
      mkdirSync(dirname(path), { recursive: true });
      writeFileSync(path, `import { test } from '@playwright/test';\ntest(${JSON.stringify(specimen)}, () => {});\n`);
    }
    // Listing uses the real configuration and runner without starting a preview or browser.
    const result = spawnSync(process.execPath, [cli, 'test', '--list', '--reporter=json', ...args], {
      cwd: directory, encoding: 'utf8', env: { ...process.env, AC_SITE_MODE: mode },
    });
    assert.equal(result.status, 0, result.stdout + result.stderr);
    const report = JSON.parse(result.stdout);
    assert.deepEqual(report.errors, []);
    const titles = (suite) => [...(suite.specs ?? []).map((spec) => spec.title), ...(suite.suites ?? []).flatMap(titles)];
    assert.deepEqual(titles(report).sort(), [...expected].sort());
  });
}
