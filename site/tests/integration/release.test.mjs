import test from 'node:test';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { mkdirSync, readFileSync, writeFileSync, appendFileSync, rmSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { fixture, cli, root, initialise, commit, git, read } from './support.mjs';
const moduleURL = pathToFileURL(join(root, 'site/scripts/verify-release.mjs'));
const paths = ['/', '/specification/', '/runners/', '/authors/quickstart/', '/authors/best-practices/', '/authors/checks/', '/authors/explain-back/', '/implementers/support/', '/implementers/conformance/'];
const titles = ['Agent Courses', 'Specification', 'Runners', 'Quickstart', 'Best practices', 'Writing checks', 'Explain-back and rubrics', 'Support Agent Courses', 'Conformance'];
const workflow = `name: Publish
on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      prove_failure:
        type: boolean
        default: false
permissions:
  contents: read
jobs:
  checks:
    env:
      AC_DEPLOYMENT: custom-domain
    runs-on: ubuntu-latest
    steps:
      - run: make check
      - if: inputs.prove_failure
        run: |
          uv run python tools/prove_gate_failure.py --prepare-only /tmp/bad-tree
          make check CHECK_ROOT=/tmp/bad-tree
      - uses: actions/upload-pages-artifact@pinned
        if: success() && !inputs.prove_failure
        with:
          path: site/dist
  deploy:
    needs: checks
    if: success() && !inputs.prove_failure && github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
    environment: github-pages
    permissions:
      pages: write
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/deploy-pages@pinned
`;
async function setup(t, url = 'https://agentcourses.io/') {
  const dir = fixture(t);
  mkdirSync(join(dir, '.github/workflows'), { recursive: true });
  writeFileSync(join(dir, '.github/workflows/pages.yml'), workflow);
  mkdirSync(join(dir, 'docs/releases'), { recursive: true });
  writeFileSync(join(dir, 'docs/releases/candidate.md'), '---\ntitle: Candidate\ncandidate: 1.0.0-rc.1\nblockers: []\ncontract_approval: https://example.invalid/contract\nreceipt_approval: https://example.invalid/receipt\n---\n\nCandidate review; stable release remains deferred.\n');
  const verifier = await import(moduleURL);
  const generated = cli('generate.mjs', dir); assert.equal(generated.status, 0, generated.stderr);
  initialise(dir);
  for (let i = 0; i < paths.length; i++) {
    const path = join(dir, 'site/dist', paths[i].slice(1), 'index.html'); mkdirSync(join(path, '..'), { recursive: true });
    writeFileSync(path, `<!doctype html><html><head><title>${titles[i]} | Agent Courses</title><link rel="canonical" href="${url.replace(/\/$/, '')}${paths[i]}"></head><body><h1>${titles[i]}</h1></body></html>`);
  }
  for (const [path, bytes] of (await import(pathToFileURL(join(root, 'site/scripts/generate.mjs')))).schemaOutputs(dir).output) {
    mkdirSync(join(dir, 'site/dist', path, '..'), { recursive: true }); writeFileSync(join(dir, 'site/dist', path), bytes);
  }
  mkdirSync(join(dir, 'site/dist/_astro'), { recursive: true }); writeFileSync(join(dir, 'site/dist/_astro/app.js'), 'console.log("static");\n');
  mkdirSync(join(dir, 'site/.astro'), { recursive: true });
  writeFileSync(join(dir, 'site/.astro/production-build.json'), JSON.stringify({ source_digest: verifier.sourceDigest(dir), dist_digest: verifier.distDigest(dir), deployment_url: url }));
  return { dir, ...verifier };
}
function approval(dir, overrides = {}) {
  const path = join(dir, '..', `approval-${dir.split('/').at(-1)}.json`);
  const manifest = readFileSync(join(dir, 'schemas/manifest.json'));
  const record = {
    candidate: '1.0.0-rc.1', build_commit: git(dir, 'rev-parse', 'HEAD'), build_tree: git(dir, 'rev-parse', 'HEAD^{tree}'),
    manifest_sha256: hash(manifest), deployment_run_url: 'https://github.com/agentcourses/agentcourses/actions/runs/123',
    owner: 'Fixture owner', approved_at: '2026-10-21T12:00:00Z', decision_link: 'https://example.invalid/owner-message', decision: 'approved', ...overrides,
  };
  writeFileSync(path, JSON.stringify(record)); return path;
}
import { createHash } from 'node:crypto';
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
async function rejectsRule(run, rule) { await assert.rejects(run, (error) => { assert.deepEqual([error.rule], [rule]); return true; }); }
function transport(dir, mutate = (response) => response, base = '/') {
  return async (url) => {
    const parsed = new URL(url);
    assert.ok(parsed.pathname.startsWith(base), `Request escaped base: ${url}`);
    const relative = parsed.pathname.slice(base.length);
    const path = relative.endsWith('/') || !relative ? `${relative}index.html` : relative;
    let bytes;
    try { bytes = readFileSync(join(dir, 'site/dist', path)); } catch { return { status: 404, headers: { 'content-type': 'text/plain' }, body: Buffer.from('missing'), url }; }
    const type = path.endsWith('.html') ? 'text/html; charset=utf-8' : path.endsWith('.json') ? 'application/json; charset=utf-8' : 'application/octet-stream';
    return mutate({ status: 200, headers: { 'content-type': type }, body: bytes, url }, parsed.pathname);
  };
}
test('preflight proves closure and safe workflows without requiring a freeze; verifier never writes', async (t) => {
  const { dir, verifyRelease, sourceDigest } = await setup(t);
  const before = sourceDigest(dir); await verifyRelease({ root: dir, preflight: true }); assert.equal(sourceDigest(dir), before);
});
test('preflight rejects a candidate blocker', async (t) => {
  const { dir, verifyRelease } = await setup(t);
  writeFileSync(join(dir, 'docs/releases/candidate.md'), read(join(dir, 'docs/releases/candidate.md')).replace('blockers: []', 'blockers: [Unresolved]'));
  await rejectsRule(() => verifyRelease({ root: dir, preflight: true }), 'candidate-blocker');
});
for (const [name, transform] of [
  ['reversed failure guard', (s) => s.replace('if: success() && !inputs.prove_failure', 'if: success() && !inputs.prove_failure == false')],
  ['PR target event', (s) => s.replace('  push:', '  pull_request_target:\n  push:')],
  ['skipped gate', (s) => s.replace('- run: make check', '- if: false\n        run: make check')],
  ['ignored failed gate', (s) => s.replace('- run: make check', '- continue-on-error: true\n        run: make check')],
  ['missing check dependency', (s) => s.replace('needs: checks', 'needs: another-job')],
  ['failure-proof upload', (s) => s.replace('if: success() && !inputs.prove_failure', 'if: success()')],
  ['failure-proof deployment', (s) => s.replace("if: success() && !inputs.prove_failure && github.event_name", "if: always() && github.event_name")],
]) test(name + ' fails workflow safety', async (t) => {
  const { dir, verifyRelease } = await setup(t); writeFileSync(join(dir, '.github/workflows/pages.yml'), transform(workflow));
  await rejectsRule(() => verifyRelease({ root: dir, preflight: true }), 'workflow-safety');
});
for (const bad of [undefined, 'relative.json']) test(`freeze rejects ${bad ?? 'missing'} approval path`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, requireFreeze: true, approvalRecord: bad }), 'approval-record');
});
test('absolute approval works from nested cwd; a different commit with the same tree fails before freeze', async (t) => {
  const { dir, verifyRelease } = await setup(t); const path = approval(dir); t.after(() => rmSync(path, { force: true }));
  await verifyRelease({ root: dir, requireFreeze: true, approvalRecord: path });
  const result = spawnSync(process.execPath, [join(root, 'site/scripts/verify-release.mjs'), '--root', dir, '--require-freeze', '--approval-record', path], { cwd: join(dir, 'site'), encoding: 'utf8' }); assert.equal(result.status, 0, result.stderr);
  git(dir, 'commit', '--allow-empty', '-qm', 'same tree different commit');
  await rejectsRule(() => verifyRelease({ root: dir, requireFreeze: true, approvalRecord: path }), 'approval-binding');
});
test('freeze rejects dirty sources', async (t) => {
  const { dir, verifyRelease } = await setup(t); const path = approval(dir); t.after(() => rmSync(path, { force: true }));
  appendFileSync(join(dir, 'README.md'), '\nDirty\n');
  await rejectsRule(() => verifyRelease({ root: dir, requireFreeze: true, approvalRecord: path }), 'dirty-source');
});
test('frozen-ref allows a clean identical tree at another commit, and rejects a changed tree', async (t) => {
  const { dir, verifyRelease } = await setup(t); const path = approval(dir); t.after(() => rmSync(path, { force: true }));
  git(dir, 'tag', 'agentcourses-v1.0.0-rc.1'); git(dir, 'commit', '--allow-empty', '-qm', 'merge equivalent');
  await verifyRelease({ root: dir, frozenRef: 'agentcourses-v1.0.0-rc.1', requireFreeze: true, approvalRecord: path });
  appendFileSync(join(dir, 'README.md'), '\nNew tree\n'); commit(dir);
  await rejectsRule(() => verifyRelease({ root: dir, frozenRef: 'agentcourses-v1.0.0-rc.1' }), 'frozen-tree');
});
test('history detects omitted frozen output and rewritten current checksums', async (t) => {
  const { dir, verifyRelease } = await setup(t); git(dir, 'tag', 'agentcourses-v1.0.0-rc.1');
  rmSync(join(dir, 'site/public/schemas/1.0.0-rc.1/course.schema.json'));
  await rejectsRule(() => verifyRelease({ root: dir, checkHistory: true }), 'generated-drift');
  cli('generate.mjs', dir);
  appendFileSync(join(dir, 'schemas/course.schema.json'), ' ');
  const manifest = JSON.parse(read(join(dir, 'schemas/manifest.json'))); manifest.releases[0].schemas[0].sha256 = hash(readFileSync(join(dir, 'schemas/course.schema.json')));
  writeFileSync(join(dir, 'schemas/manifest.json'), JSON.stringify(manifest));
  await rejectsRule(() => verifyRelease({ root: dir, checkHistory: true }), 'frozen-identity');
});
test('all live pages schemas and assets match source/build digests only after full success', async (t) => {
  const { dir, verifyRelease } = await setup(t);
  const result = await verifyRelease({ root: dir, url: 'https://agentcourses.io', transport: transport(dir) });
  assert.equal(result.build_digest, result.live_digest); assert.match(result.source_digest, /^[0-9a-f]{64}$/);
});
for (const path of paths) for (const [label, rule, mutate] of [
  ['404', 'live-status', (r) => ({ ...r, status: 404 })],
  ['fallback', 'live-title', (r) => ({ ...r, body: Buffer.from('<html><head><title>Wrong overview</title></head><body><h1>Wrong overview</h1></body></html>') })],
  ['canonical', 'live-canonical', (r) => ({ ...r, body: Buffer.from(r.body.toString().replace(`https://agentcourses.io${path}`, 'https://agentcourses.io/wrong/')) })],
  ['type', 'live-type', (r) => ({ ...r, headers: { 'content-type': 'application/json' } })],
]) test(`${path} rejects independent live ${label}`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, url: 'https://agentcourses.io', transport: transport(dir, (r, p) => p === path ? mutate(r) : r) }), rule);
});
for (const path of ['/schemas/manifest.json', '/schemas/1.0.0-rc.1/course.schema.json']) test(`${path} rejects HTML MIME despite matching JSON bytes`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, url: 'https://agentcourses.io', transport: transport(dir, (r, p) => p === path ? { ...r, headers: { 'content-type': 'text/html' } } : r) }), 'live-type');
});
for (const [label, path, rule, mutate] of [
  ['schema ID', '/schemas/1.0.0-rc.1/course.schema.json', 'live-schema-id', (r) => ({ ...r, body: Buffer.from(r.body.toString().replace('https://agentcourses.io/schemas/1.0.0-rc.1/course.schema.json', 'https://agentcourses.io/schemas/wrong/course.schema.json')) })],
  ['schema bytes', '/schemas/1.0.0-rc.1/course.schema.json', 'live-bytes', (r) => ({ ...r, body: Buffer.concat([r.body, Buffer.from(' ')]) })],
  ['missing asset', '/_astro/app.js', 'live-status', (r) => ({ ...r, status: 404 })],
  ['insecure redirect', '/', 'live-redirect', (r) => ({ ...r, status: 302, headers: { location: 'http://agentcourses.io/' } })],
  ['cross-origin redirect', '/', 'live-redirect', (r) => ({ ...r, status: 302, headers: { location: 'https://other.invalid/' } })],
]) test(`live verification rejects ${label}`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, url: 'https://agentcourses.io', transport: transport(dir, (r, p) => p === path ? mutate(r) : r) }), rule);
});
test('real CLI rejects HTTP before transport and uses exit two for invalid arguments', (t) => {
  const dir = fixture(t); const result = cli('verify-release.mjs', dir, '--url', 'http://localhost:4321');
  assert.equal(result.status, 2); assert.match(result.stderr, /invalid-arguments/);
});
test('Markdown execution evidence accepts one structured owner decision', async (t) => {
  const { dir, verifyRelease } = await setup(t); const path = approval(dir); t.after(() => rmSync(path, { force: true }));
  writeFileSync(path, '# Execution record\n\n```json\n' + read(path) + '\n```\n');
  await verifyRelease({ root: dir, requireFreeze: true, approvalRecord: path });
});
test('frozen-ref rejects an arbitrary branch even at an identical tree', async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, frozenRef: 'HEAD' }), 'missing-history');
});
test('a removed dist asset invalidates the source-bound production build inventory', async (t) => {
  const { dir, verifyRelease } = await setup(t); rmSync(join(dir, 'site/dist/_astro/app.js'));
  await rejectsRule(() => verifyRelease({ root: dir, url: 'https://agentcourses.io', transport: transport(dir) }), 'build-provenance');
});
test('invalid approval evidence fields fail binding explicitly', async (t) => {
  const { dir, verifyRelease } = await setup(t); const path = approval(dir); t.after(() => rmSync(path, { force: true }));
  writeFileSync(path, 'null');
  await rejectsRule(() => verifyRelease({ root: dir, requireFreeze: true, approvalRecord: path }), 'approval-binding');
});
for (const key of ['contract_approval', 'receipt_approval']) test(`preflight rejects a ${key} value without an owner-evidence link`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  const page = join(dir, 'docs/releases/candidate.md'); writeFileSync(page, read(page).replace(new RegExp(`${key}: .+`), `${key}: true`));
  await rejectsRule(() => verifyRelease({ root: dir, preflight: true }), 'candidate-blocker');
});

const projectURL = 'https://agentcourses.github.io/agentcourses/';
test('default Pages verifies unchanged schema identifiers and every byte below its project base', async (t) => {
  const { dir, verifyRelease } = await setup(t, projectURL);
  const result = await verifyRelease({ root: dir, url: projectURL, transport: transport(dir, undefined, '/agentcourses/') });
  assert.equal(result.build_digest, result.live_digest);
});
for (const [label, mutate] of [
  ['same-origin redirect outside base', (r) => ({ ...r, status: 302, headers: { location: '/specification/' } })],
  ['response URL outside base', (r) => ({ ...r, url: 'https://agentcourses.github.io/specification/' })],
  ['response URL with credentials', (r) => ({ ...r, url: 'https://user@agentcourses.github.io/agentcourses/' })],
  ['encoded traversal redirect', (r) => ({ ...r, status: 302, headers: { location: '/agentcourses/%2e%2e/specification/' } })],
  ['base lookalike redirect', (r) => ({ ...r, status: 302, headers: { location: '/agentcourses-other/' } })],
]) test(`default Pages rejects ${label}`, async (t) => {
  const { dir, verifyRelease } = await setup(t, projectURL);
  await rejectsRule(() => verifyRelease({ root: dir, url: projectURL, transport: transport(dir, mutate, '/agentcourses/') }), 'live-redirect');
});
test('default Pages rejects a root deployment build provenance', async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, url: projectURL, transport: transport(dir, undefined, '/agentcourses/') }), 'build-provenance');
});
for (const url of ['https://agentcourses.github.io/', 'https://agentcourses.github.io/agentcourses', 'https://agentcourses.github.io/other/', 'https://other.invalid/agentcourses/', 'https://user@agentcourses.github.io/agentcourses/', projectURL + '?q=1', projectURL + '#fragment']) test(`rejects unsupported deployment URL ${url}`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  await rejectsRule(() => verifyRelease({ root: dir, url }), 'invalid-arguments');
});
test('a publication branch allowlist cannot bypass main-only deployment', async (t) => {
  const { dir, verifyRelease } = await setup(t);
  writeFileSync(join(dir, '.github/workflows/pages.yml'), workflow.replace('branches: [main]', 'branches: [main, publication]'));
  await rejectsRule(() => verifyRelease({ root: dir, preflight: true }), 'workflow-safety');
});
for (const [label, path, rule, mutate] of [
  ['wrong page identity', '/', 'live-title', (r) => ({ ...r, body: Buffer.from('<title>Wrong</title><h1>Wrong</h1>') })],
  ['root-domain canonical', '/', 'live-canonical', (r) => ({ ...r, body: Buffer.from(r.body.toString().replace(projectURL, 'https://agentcourses.io/')) })],
  ['schema HTML MIME', '/schemas/1.0.0-rc.1/course.schema.json', 'live-type', (r) => ({ ...r, headers: { 'content-type': 'text/html' } })],
  ['changed schema bytes', '/schemas/1.0.0-rc.1/course.schema.json', 'live-bytes', (r) => ({ ...r, body: Buffer.concat([r.body, Buffer.from(' ')]) })],
  ['missing browser asset', '/_astro/app.js', 'live-status', (r) => ({ ...r, status: 404 })],
]) test(`default Pages retains rejection of ${label}`, async (t) => {
  const { dir, verifyRelease } = await setup(t, projectURL);
  await rejectsRule(() => verifyRelease({ root: dir, url: projectURL, transport: transport(dir, (r, p) => p === '/agentcourses' + path ? mutate(r) : r, '/agentcourses/') }), rule);
});
for (const profile of ['', 'github-pages']) test(`publication preflight rejects an absent or wrong deployment profile: ${profile}`, async (t) => {
  const { dir, verifyRelease } = await setup(t);
  writeFileSync(join(dir, '.github/workflows/pages.yml'), workflow.replace('AC_DEPLOYMENT: custom-domain', `AC_DEPLOYMENT: ${profile}`));
  await rejectsRule(() => verifyRelease({ root: dir, preflight: true }), 'workflow-safety');
});
