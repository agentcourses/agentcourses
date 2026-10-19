import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const design = process.env.AC_SITE_MODE === 'design';
const slugs = ['', 'specification', 'runners', 'authors/quickstart', 'authors/best-practices', 'authors/checks', 'authors/explain-back', 'implementers/support', 'implementers/conformance'];
if (design) {
  for (const slug of slugs) {
    if (!existsSync(new URL(`./tests/design/fixtures/${slug || 'index'}.mdx`, import.meta.url))) {
      throw new Error(`Design collection requires all nine fixtures; missing ${slug || 'index'}.mdx`);
    }
  }
}
const map = design ? null : JSON.parse(execFileSync('uv', ['run', '--locked', 'python', 'tools/check_docs.py', '--site-map'], { cwd: root, encoding: 'utf8' }));
const routes = design ? slugs.map((slug) => `/${slug}${slug ? '/' : ''}`) : map.routes;
export default defineConfig({
  vite: { define: { 'import.meta.env.AC_EXAMPLES_ROOT': JSON.stringify(fileURLToPath(new URL('../examples/', import.meta.url))) } },
  integrations: [starlight({
    title: 'Agent Courses',
    sidebar: routes.map((route) => ({ label: route === '/' ? 'Overview' : route.split('/').filter(Boolean).join(' / '), slug: route === '/' ? '' : route.slice(1, -1) })),
  })],
});
