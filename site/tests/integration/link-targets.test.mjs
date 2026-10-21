import test from 'node:test';
import assert from 'node:assert/strict';
import { inspectLinkTargets } from './link-targets.mjs';

const root = 'http://127.0.0.1:4321';
const links = [
  `${root}/reference/#first`, `${root}/reference/#second`, `${root}/reference/`,
  `${root}/reference/#encoded%20id`, `${root}/reference/?version=2#first`,
  `${root}/download.json`, `${root}/other/#third`, `${root}/reference/#first`,
];
const targets = [
  [`${root}/reference/`, { status: 200, ids: ['first', 'second', 'encoded id'] }],
  [`${root}/reference/?version=2`, { status: 200, ids: ['first'] }],
  [`${root}/download.json`, { status: 200, ids: [] }],
  [`${root}/other/`, { status: 200, ids: ['third'] }],
];
const mutations = [
  ['all links resolve', () => {}, []],
  ['missing fragment', (pages) => pages.get(`${root}/reference/`).ids.splice(1, 1), [
    { href: `${root}/reference/#second`, status: 200, fragmentPresent: false },
  ]],
  ['non-200 response', (pages) => { pages.get(`${root}/other/`).status = 404; }, [
    { href: `${root}/other/#third`, status: 404, fragmentPresent: true },
  ]],
];

for (const [name, mutate, expectedFailures] of mutations) {
  test(`complete link inventory: ${name}`, async () => {
    const pages = new Map(structuredClone(targets)); mutate(pages);
    const calls = [];
    const checks = await inspectLinkTargets(links, async (target, needsIDs) => {
      calls.push([target, needsIDs]);
      assert.ok(pages.has(target), `Unexpected target: ${target}`);
      return pages.get(target);
    });
    assert.deepEqual(checks.map(({ href }) => href).sort(), [...links].sort());
    assert.deepEqual(calls, targets.map(([target]) => [target, target !== `${root}/download.json`]));
    assert.deepEqual(checks.filter(({ status, fragmentPresent }) => status !== 200 || !fragmentPresent), expectedFailures);
  });
}
