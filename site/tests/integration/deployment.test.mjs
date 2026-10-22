import test from 'node:test';
import assert from 'node:assert/strict';
import { deploymentProfile, withBase, deploymentLinks } from '../../scripts/deployment.mjs';

test('production defaults to the fixed GitHub Pages project profile', () => {
  assert.deepEqual(deploymentProfile(), { site: 'https://agentcourses.github.io', base: '/agentcourses/' });
  assert.deepEqual(deploymentProfile('production', 'custom-domain'), { site: 'https://agentcourses.io', base: '/' });
  assert.deepEqual(deploymentProfile('design', 'github-pages'), { site: 'https://agentcourses.io', base: '/' });
  assert.throws(() => deploymentProfile('production', 'https://other.invalid'), /Unsupported deployment profile/);
});
test('local destinations receive the base exactly once; external and fragment links retain their bytes', () => {
  for (const href of ['/specification/#format', '/schemas/manifest.json', '/mark.svg']) {
    assert.equal(withBase(href, '/agentcourses/'), `/agentcourses${href}`);
    assert.equal(withBase(`/agentcourses${href}`, '/agentcourses/'), `/agentcourses${href}`);
    assert.equal(withBase(href, '/'), href);
  }
  for (const href of ['#format', 'relative/', 'https://agentcourses.io/schemas/course.json', '//example.invalid/file', 'mailto:owner@example.invalid']) assert.equal(withBase(href, '/agentcourses/'), href);
});
test('the Satteri visitor prefixes Markdown and literal HTML destinations without changing identifiers', async () => {
  const { createRequire } = await import('node:module');
  const { pathToFileURL } = await import('node:url');
  const require = createRequire(import.meta.url);
  const locked = createRequire(require.resolve('@astrojs/markdown-satteri'));
  const { mdxToJs } = await import(pathToFileURL(locked.resolve('satteri')));
  const source = '[Markdown](/specification/#format) <a id="format" href="/authors/checks/">HTML</a>\n\n<a href="/runners/">Block</a>';
  const { code } = mdxToJs(source, { hastPlugins: [deploymentLinks('/agentcourses/')] });
  for (const href of ['/agentcourses/specification/#format', '/agentcourses/authors/checks/', '/agentcourses/runners/']) assert.ok(code.includes(JSON.stringify(href)), href);
  assert.match(code, /id: "format"/);
});
