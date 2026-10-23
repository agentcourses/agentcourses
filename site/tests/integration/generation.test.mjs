import test from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { writeFileSync, appendFileSync, rmSync, readdirSync } from 'node:fs';
import { fixture, cli, read, rules, git, initialise, commit, root } from './support.mjs';
const page = 'site/src/content/docs/specification.mdx';
const generate = (dir) => cli('generate.mjs', dir);
const check = (dir) => cli('check-generated.mjs', dir);
test('canonical composition works without a generated page and is deterministic', (t) => {
  const dir = fixture(t); rmSync(join(dir, page), { force: true });
  const out = generate(dir); assert.equal(out.status, 0, out.stderr);
  const text = read(join(dir, page));
  let previous = -1;
  for (const stem of ['format', 'execution', 'consent', 'records', 'identity']) {
    const offset = text.indexOf(`id="${stem}"`); assert.ok(offset > previous); previous = offset;
    assert.ok(text.includes(`spec/${stem}.md`));
  }
  assert.match(text, /Edit the canonical sources/);
  assert.equal(check(dir).status, 0);
  assert.equal(generate(dir).status, 0); assert.equal(read(join(dir, page)), text);
  rmSync(join(dir, page)); const missing = check(dir);
  assert.equal(missing.status, 1); assert.deepEqual(rules(missing), ['generated-drift']);
  assert.throws(() => read(join(dir, page)));
});
for (const [name, mutate] of [
  ['changed canonical source', (d) => appendFileSync(join(d, 'spec/format.md'), '\nChanged canonical text.\n')],
  ['stale schema copy', (d) => appendFileSync(join(d, 'site/public/schemas/1.0.0-rc.1/course.schema.json'), ' ')],
  ['unexpected generated payload', (d) => writeFileSync(join(d, 'site/public/schemas/unexpected.json'), '{}')],
]) test(name + ' produces exactly generated-drift', (t) => {
  const dir = fixture(t); assert.equal(generate(dir).status, 0); mutate(dir);
  const result = check(dir); assert.equal(result.status, 1); assert.deepEqual(rules(result), ['generated-drift']);
});
for (const [name, path, text, rule] of [
  ['unknown reference', 'spec/format.md', '\n[Unknown](execution.md#not-real)\n', 'source-map'],
  ['duplicate ID', 'spec/format.md', '\n<a id="course-shape"></a>\n', 'source-map'],
  ['private register', 'spec/format.md', '\n[Private](../docs/delivery/contracts.md)\n', 'private-register-link'],
  ['unlisted schema', 'schemas/extra.schema.json', '{}', 'unlisted-schema'],
  ['identity bytes changed', 'schemas/course.schema.json', ' ', 'schema-checksum'],
]) test(name + ' fails its exact named rule', (t) => {
  const dir = fixture(t); if (name === 'private register') writeFileSync(join(dir, 'docs/delivery/contracts.md'), '# Private register\n'); appendFileSync(join(dir, path), text);
  const result = generate(dir); assert.equal(result.status, 1); assert.deepEqual(rules(result), [rule]);
});
test('a missing normative source never becomes an empty success', (t) => {
  const dir = fixture(t); rmSync(join(dir, 'spec/identity.md'));
  const result = generate(dir); assert.equal(result.status, 1); assert.deepEqual(rules(result), ['source-map']);
});
export function nextRelease(dir, candidate) {
  const manifest = JSON.parse(read(join(dir, 'schemas/manifest.json')));
  const old = manifest.candidate; manifest.candidate = candidate;
  for (const release of manifest.releases) {
    release.candidate = candidate;
    for (const schema of release.schemas) {
      const path = join(dir, schema.path);
      const payload = read(path).replaceAll(`/schemas/${old}/`, `/schemas/${candidate}/`);
      writeFileSync(path, payload);
      schema.id = schema.id.replace(`/schemas/${old}/`, `/schemas/${candidate}/`);
      schema.sha256 = (awaitHash(payload));
    }
  }
  writeFileSync(join(dir, 'schemas/manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
}
import { createHash } from 'node:crypto';
const awaitHash = (bytes) => createHash('sha256').update(bytes).digest('hex');
test('two historical flat release tags reconstruct bytes and reject omitted history or changed identity', (t) => {
  const dir = fixture(t); initialise(dir);
  assert.equal(generate(dir).status, 0); const original = read(join(dir, 'schemas/course.schema.json'));
  git(dir, 'tag', 'agentcourses-v1.0.0-rc.1');
  nextRelease(dir, '1.0.0-rc.2'); commit(dir); git(dir, 'tag', 'agentcourses-v1.0.0-rc.2');
  nextRelease(dir, '1.0.0-rc.3'); commit(dir);
  assert.equal(generate(dir).status, 0);
  assert.equal(read(join(dir, 'site/public/schemas/1.0.0-rc.1/course.schema.json')), original);
  assert.equal(JSON.parse(read(join(dir, 'site/public/schemas/manifest.json'))).releases.length, 3);
  rmSync(join(dir, 'site/public/schemas/1.0.0-rc.2/course.schema.json'));
  assert.deepEqual(rules(check(dir)), ['generated-drift']);
  generate(dir); git(dir, 'tag', '-d', 'agentcourses-v1.0.0-rc.2');
  assert.deepEqual(rules(generate(dir)), ['missing-history']);
});
test('a frozen candidate identity cannot be reused with newly checksummed bytes', (t) => {
  const dir = fixture(t); initialise(dir); git(dir, 'tag', 'agentcourses-v1.0.0-rc.1');
  const manifest = JSON.parse(read(join(dir, 'schemas/manifest.json')));
  appendFileSync(join(dir, 'schemas/course.schema.json'), ' ');
  manifest.releases[0].schemas[0].sha256 = awaitHash(read(join(dir, 'schemas/course.schema.json')));
  writeFileSync(join(dir, 'schemas/manifest.json'), JSON.stringify(manifest));
  assert.deepEqual(rules(generate(dir)), ['frozen-identity']);
});
test('a release tag with a missing historical payload fails explicitly', (t) => {
  const dir = fixture(t); initialise(dir);
  const payload = read(join(dir, 'schemas/course.schema.json'));
  git(dir, 'rm', '-q', 'schemas/course.schema.json'); commit(dir); git(dir, 'tag', 'agentcourses-v1.0.0-rc.1');
  writeFileSync(join(dir, 'schemas/course.schema.json'), payload); nextRelease(dir, '1.0.0-rc.2'); commit(dir);
  assert.deepEqual(rules(generate(dir)), ['history-input']);
});
test('external private strategy register links are rejected', (t) => {
  const dir = fixture(t); appendFileSync(join(dir, 'spec/format.md'), '\n[Private](https://github.com/tutr-dev/tutr-strategy/blob/main/bench/contracts.md)\n');
  const result = generate(dir); assert.equal(result.status, 1); assert.deepEqual(rules(result), ['private-register-link']);
});
const identifierCases = [
  ['canonical', (id) => id],
  ['username', (id) => id.replace('https://', 'https://user@')],
  ['password only', (id) => id.replace('https://', 'https://:secret@')],
  ['username and password', (id) => id.replace('https://', 'https://user:secret@')],
  ['empty user information', (id) => id.replace('https://', 'https://@')],
  ['default port', (id) => id.replace('agentcourses.io', 'agentcourses.io:443')],
  ['uppercase host', (id) => id.replace('agentcourses.io', 'AGENTCOURSES.IO')],
  ['uppercase scheme', (id) => id.replace('https:', 'HTTPS:')],
  ['dot segment', (id) => id.replace('/schemas/', '/ignored/../schemas/')],
  ['surrounding whitespace', (id) => ` ${id} `],
  ['empty query', (id) => `${id}?`],
  ['empty fragment', (id) => `${id}#`],
];
for (const input of ['current', 'historical']) for (const [label, transform] of identifierCases) {
  test(`schema public identifiers: ${input} ${label}`, (t) => {
    const dir = fixture(t);
    assert.equal(generate(dir).status, 0);
    const manifestPath = join(dir, 'schemas/manifest.json');
    const originalManifest = read(manifestPath);
    const manifest = JSON.parse(originalManifest);
    const schema = manifest.releases[0].schemas[0];
    const payloadPath = join(dir, schema.path);
    const originalPayload = read(payloadPath);
    const id = transform(schema.id);
    const payload = originalPayload.replace(schema.id, id);
    writeFileSync(payloadPath, payload);
    schema.id = id; schema.sha256 = awaitHash(payload);
    writeFileSync(manifestPath, JSON.stringify(manifest));
    if (input === 'historical') {
      initialise(dir); git(dir, 'tag', 'agentcourses-v1.0.0-rc.1');
      writeFileSync(manifestPath, originalManifest); writeFileSync(payloadPath, originalPayload);
      nextRelease(dir, '1.0.0-rc.2'); commit(dir);
    }
    const consumers = [
      ['generate.mjs'], ['check-generated.mjs'], ['verify-release.mjs', '--check-history'],
    ];
    // Invalid IDs must fail before a live request, even when their parsed URI looks canonical.
    if (label !== 'canonical') consumers.push(['verify-release.mjs', '--url', 'https://agentcourses.io']);
    for (const [script, ...args] of consumers) {
      const result = cli(script, dir, ...args);
      assert.equal(result.status, label === 'canonical' ? 0 : 1, `${script} ${args}: ${result.stderr}`);
      if (label !== 'canonical') assert.deepEqual(rules(result), ['schema-manifest'], `${script} ${args}`);
    }
  });
}

// Public articles teach today's format. Learner progress history and explicit
// course-content upgrades remain valid subjects and are deliberately allowed.
test('public documentation describes only the current course format', () => {
  function markdown(directory) {
    return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
      const path = join(directory, entry.name);
      return entry.isDirectory() ? markdown(path) : /\.mdx?$/.test(path) ? [path] : [];
    });
  }
  const pages = [...markdown(join(root, 'site/src/content/docs')), ...markdown(join(root, 'spec')).filter((path) => !path.endsWith('/requirements.md')), join(root, 'README.md')];
  const stale = /1\.0\.0-rc\.1|\bmigrat(?:ion|e|ed|ing)\b|historical (?:baseline|layout|trace|context|feedback)|Historically|candidate-migration|checks\/checks\.yaml[^\n]*(?:declares|as a list)|file="(?:checks\/|feedback\.yaml)/i;
  const findings = pages.filter((path) => stale.test(read(path).replace(/<a id="[^"]*"><\/a>/g, ''))).map((path) => path.slice(root.length));
  assert.deepEqual(findings, [], 'every public source, including the generated reference, must teach the current format');
  const format = read(join(root, 'spec/format.md'));
  assert.match(format, /format: "1\.0\.0-rc\.2"/);
  assert.match(format, /assets\/starter\//);
  assert.match(format, /scripts\/fixtures\//);
  assert.match(format, /\| `checks` \| No \|/);
  assert.match(format, /\| `feedback` \| No \|/);
  assert.ok(/explicit upgrade request/.test(read(join(root, 'spec/records.md'))), 'learner course-content upgrades remain documented');
  assert.ok(read(join(root, 'spec/records.md')).includes('`history`'), 'learner progress history remains documented');
});
