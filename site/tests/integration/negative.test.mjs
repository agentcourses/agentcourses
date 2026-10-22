import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { rmSync, writeFileSync, appendFileSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fixture, cli, root } from './support.mjs';
const cases = [
  ['missing page', (d) => rmSync(join(d, 'site/src/content/docs/authors/checks.mdx')), ['required-file']],
  // README and the candidate handoff also link to the removed author quickstart.
  ['missing author group', (d) => rmSync(join(d, 'site/src/content/docs/authors'), { recursive: true }), ['missing-link', 'missing-link', ...Array(4).fill('required-file')]],
  ['lower marker', (d) => writeFileSync(join(d, 'tools/document-stage.json'), '{"stage":"runners"}'), ['stage-regression']],
  ['missing marker', (d) => rmSync(join(d, 'tools/document-stage.json')), ['missing-link', 'missing-stage', 'required-file']],
  ['unknown public fragment', (d) => appendFileSync(join(d, 'site/src/content/docs/index.mdx'), '\n[Unknown](/specification/#format--not-real)\n'), ['public-anchor']],
];
for (const [label, mutate, expected] of cases) test(label + ' fails candidate source inspection with exact findings', (t) => {
  const dir = fixture(t); const generated = cli('generate.mjs', dir); assert.equal(generated.status, 0, generated.stderr);
  mutate(dir);
  const result = spawnSync(join(root, '.venv/bin/python'), [join(root, 'tools/check_docs.py'), '--root', dir, '--scope', 'candidate'], { encoding: 'utf8' });
  assert.equal(result.status, 1, result.stdout + result.stderr);
  const findings = result.stderr.trim().split('\n').filter(Boolean).map((line) => line.split(': ')[1]);
  assert.deepEqual(findings.sort(), expected.sort());
});
test('a known future canonical link exports before composition and resolves after generation', (t) => {
  const dir = fixture(t); rmSync(join(dir, 'site/src/content/docs/specification.mdx'), { force: true });
  const map = spawnSync(join(root, '.venv/bin/python'), [join(root, 'tools/check_docs.py'), '--root', dir, '--site-map'], { encoding: 'utf8' });
  assert.equal(map.status, 0, map.stdout + map.stderr);
  assert.ok(JSON.parse(map.stdout).anchors.some((a) => a.public === '/specification/#execution--check-results'));
  assert.equal(cli('generate.mjs', dir).status, 0);
});
test('the ordinary gate rejects committed composition drift before any build hook repairs it', (t) => {
  const dir = fixture(t); assert.equal(cli('generate.mjs', dir).status, 0);
  const path = join(dir, 'site/src/content/docs/specification.mdx'); appendFileSync(path, '\nStale generated output.\n');
  const before = readFileSync(path);
  const result = spawnSync('make', ['check', `CHECK_ROOT=${dir}`], { cwd: root, encoding: 'utf8' });
  assert.equal(result.status, 2, result.stdout + result.stderr);
  const findings = result.stderr.split('\n').filter((line) => line.startsWith('{')).map((line) => JSON.parse(line).rule);
  assert.deepEqual(findings, ['generated-drift'], result.stdout + result.stderr);
  assert.deepEqual(readFileSync(path), before);
});
