import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readdirSync, cpSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import * as generation from '../../scripts/generate.mjs';

test('completed Pagefind output validates every bootstrap runtime reference', async (t) => {
  assert.equal(typeof generation.buildSearch, 'function', 'The build must own completed search output');
  assert.equal(typeof generation.validateSearchOutput, 'function', 'The build must reject incomplete search output');
  const root = mkdtempSync(join(tmpdir(), 'ac-search-output-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const site = join(root, 'site');
  mkdirSync(site);
  for (const [language, word] of [['en-GB', 'quillwort'], ['fr', 'bonjour']]) {
    writeFileSync(join(site, `${language}.html`), `<html lang="${language}"><head><title>${word}</title></head><body><main data-pagefind-body><h1>${word}</h1><p>${word} searchable body.</p></main></body></html>`);
  }
  const entry = generation.buildSearch(site);
  assert.deepEqual(Object.keys(entry.languages).sort(), ['en-gb', 'fr']);
  assert.ok(Object.values(entry.languages).every((language) => language.page_count === 1));
  const original = join(site, 'pagefind');
  const required = ['pagefind-entry.json', 'pagefind.js', 'pagefind-worker.js',
    ...Object.values(entry.languages).flatMap((language) => [`pagefind.${language.hash}.pf_meta`, `wasm.${language.wasm || 'unknown'}.pagefind`])];
  const check = async (name, mutate, valid = false) => t.test(name, () => {
    const output = join(root, 'mutated');
    cpSync(original, output, { recursive: true });
    try {
      mutate(output);
      if (valid) assert.deepEqual(generation.validateSearchOutput(output), entry);
      else assert.throws(() => generation.validateSearchOutput(output), { rule: 'search-output' });
    } finally { rmSync(output, { recursive: true, force: true }); }
  });
  await check('complete output is accepted', () => {}, true);
  for (const name of required) {
    await check(`missing ${name} fails`, (output) => rmSync(join(output, name)));
    await check(`empty ${name} fails`, (output) => writeFileSync(join(output, name), ''));
  }
  for (const [name, value] of [
    ['malformed JSON', '{'], ['null metadata', 'null'], ['empty inventory', JSON.stringify({ version: '1.5.2', languages: {} })],
    ['array inventory', JSON.stringify({ version: '1.5.2', languages: [] })],
    ['unsafe reference', JSON.stringify({ ...entry, languages: { en: { hash: '../outside', page_count: 1 } } })],
    ['missing hash', JSON.stringify({ ...entry, languages: { en: { page_count: 1 } } })],
    ['invalid page count', JSON.stringify({ ...entry, languages: { en: { hash: 'en_hash', page_count: 0 } } })],
  ]) await check(name, (output) => writeFileSync(join(output, 'pagefind-entry.json'), value));
  for (const language of Object.values(entry.languages)) {
    await check(`corrupt metadata ${language.hash}`, (output) => writeFileSync(join(output, `pagefind.${language.hash}.pf_meta`), 'broken gzip'));
    await check(`invalid WASM ${language.wasm}`, (output) => writeFileSync(join(output, `wasm.${language.wasm}.pagefind`), gzipSync('pagefind_dcdinvalid wasm')));
  }
  await check('empty unused assets remain valid', (output) => {
    writeFileSync(join(output, 'wasm.unknown.pagefind'), '');
    writeFileSync(join(output, 'pagefind-component-ui.css'), '');
    writeFileSync(join(output, 'pagefind-ui.css'), '');
    writeFileSync(join(output, 'pagefind-ui.js'), '');
  }, true);
  for (const kind of ['index', 'fragment']) {
    const name = `${kind}/${readdirSync(join(original, kind))[0]}`;
    await check(`corrupt emitted ${kind} fails`, (output) => writeFileSync(join(output, name), 'broken gzip'));
  }
  const fragment = `fragment/${readdirSync(join(original, 'fragment'))[0]}`;
  await check('malformed fragment JSON fails', (output) => writeFileSync(join(output, fragment), gzipSync('pagefind_dcd{')));
});
