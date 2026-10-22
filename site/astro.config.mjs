import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { satteri } from '@astrojs/markdown-satteri';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { buildSearch } from './scripts/generate.mjs';
import { sourceDigest, distDigest } from './scripts/verify-release.mjs';
import { fileURLToPath } from 'node:url';
import { deploymentProfile, deploymentLinks } from './scripts/deployment.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const design = process.env.AC_SITE_MODE === 'design';
const deployment = deploymentProfile(design ? 'design' : 'production');

// Preserve Starlight's configuration and UI defaults. Its build-done callback
// only indexes search; replace that callback with the completed-process writer.
function completedSearch(integration) {
  if (Array.isArray(integration) || integration?.name !== '@astrojs/starlight' ||
      typeof integration.hooks?.['astro:build:done'] !== 'function') {
    throw new Error('Expected one Starlight integration with its search indexing hook');
  }
  return {
    ...integration,
    hooks: {
      ...integration.hooks,
      'astro:build:done': ({ dir }) => { buildSearch(fileURLToPath(dir)); },
    },
  };
}

// The sidebar frame for the nine candidate destinations, in reading order.
// Each mode passes Starlight only the slugs that exist in its own collection.
const frame = [
  { slug: '', label: 'Overview' },
  { slug: 'specification', label: 'Specification' },
  { slug: 'runners', label: 'Runner showcase' },
  {
    label: 'For course authors',
    items: [
      { slug: 'authors/quickstart', label: 'Quickstart' },
      { slug: 'authors/best-practices', label: 'Best practices' },
      { slug: 'authors/checks', label: 'Writing checks' },
      { slug: 'authors/explain-back', label: 'Explain-back and rubrics' },
    ],
  },
  {
    label: 'For runner implementers',
    items: [
      { slug: 'implementers/support', label: 'Add course support' },
      { slug: 'implementers/conformance', label: 'Conformance' },
    ],
  },
];
const slugs = frame.flatMap((entry) => (entry.items ?? [entry]).map((item) => item.slug));
if (design) {
  for (const slug of slugs) {
    if (!existsSync(new URL(`./tests/design/fixtures/${slug || 'index'}.mdx`, import.meta.url))) {
      throw new Error(`Design collection requires all nine fixtures; missing ${slug || 'index'}.mdx`);
    }
  }
}
const map = design ? null : JSON.parse(execFileSync('uv', ['run', '--locked', 'python', 'tools/check_docs.py', '--site-map'], { cwd: root, encoding: 'utf8' }));
const routes = design ? slugs.map((slug) => `/${slug}${slug ? '/' : ''}`) : map.routes;
const active = new Set(routes.map((route) => (route === '/' ? '' : route.slice(1, -1))));
for (const slug of active) {
  if (!slugs.includes(slug)) throw new Error(`Active route /${slug} has no place in the sidebar frame`);
}
const sidebar = frame.flatMap((entry) => {
  if (!entry.items) return active.has(entry.slug) ? [entry] : [];
  const items = entry.items.filter((item) => active.has(item.slug));
  return items.length > 0 ? [{ label: entry.label, items }] : [];
});

// Code panels are dark slate in both colour modes and carry no syntax colours.
const codeTheme = {
  name: 'agent-courses-code',
  type: 'dark',
  colors: { 'editor.background': '#161616', 'editor.foreground': '#ECECEA' },
  tokenColors: [
    { scope: ['comment', 'punctuation.definition.comment'], settings: { foreground: '#9C9C98' } },
    { scope: ['markup.bold'], settings: { fontStyle: 'bold' } },
  ],
};

// Each Markdown table sits in a frame that scrolls, so the table itself can fill the reading
// column. Only tables written in Markdown are wrapped; components render their own markup.
const tableFrame = {
  name: 'table-frame',
  element: {
    filter: ['table'],
    visit(node, ctx) {
      const nameEmptyHeaders = (element) => {
        if (element.tagName === 'th' && !(element.children ?? []).some((child) => child.type !== 'text' || child.value.trim())) {
          ctx.appendChild(element, { type: 'element', tagName: 'span', properties: { className: ['sr-only'] }, children: [{ type: 'text', value: 'Comparison feature' }] });
        }
        for (const child of element.children ?? []) nameEmptyHeaders(child);
      };
      if (!design) nameEmptyHeaders(node);
      ctx.wrapNode(node, { type: 'element', tagName: 'div', properties: { className: ['ac-table'] }, children: [] });
    },
  },
};

export default defineConfig({
  site: deployment.site,
  base: deployment.base,
  markdown: { processor: satteri({ hastPlugins: [tableFrame, deploymentLinks(deployment.base)] }) },
  vite: { define: { 'import.meta.env.AC_EXAMPLES_ROOT': JSON.stringify(fileURLToPath(new URL('../examples/', import.meta.url))) } },
  integrations: [{
    name: 'canonical-candidate-sources',
    hooks: {
      'astro:config:setup': ({ command, injectScript }) => {
        if (!design) injectScript('page', `
          document.querySelectorAll('main .expressive-code pre').forEach((region, index) => {
            region.setAttribute('aria-label', 'Code example ' + (index + 1));
          });
        `);
        if (!design && command === 'build') execFileSync(process.execPath, ['site/scripts/generate.mjs', '--root', root], { cwd: root, stdio: 'inherit' });
      },
    },
  }, completedSearch(starlight({
    title: 'Agent Courses',
    locales: { root: { label: 'English', lang: 'en-GB' } },
    favicon: '/mark.svg',
    customCss: ['./src/styles/tokens.css', './src/styles/site.css'],
    components: {
      Banner: './src/components/Banner.astro',
      SiteTitle: './src/components/SiteTitle.astro',
      ThemeSelect: './src/components/ThemeSelect.astro',
      PageTitle: './src/components/PageTitle.astro',
      PageFrame: './src/components/PageFrame.astro',
      TwoColumnContent: './src/components/TwoColumnContent.astro',
      PageSidebar: './src/components/PageSidebar.astro',
      Search: './src/components/Search.astro',
      MarkdownContent: './src/components/MarkdownContent.astro',
    },
    expressiveCode: {
      themes: [codeTheme],
      useStarlightDarkModeSwitch: false,
      useStarlightUiThemeColors: false,
      styleOverrides: {
        borderRadius: '12px',
        borderColor: 'var(--code-line)',
        codeBackground: 'var(--code-bg)',
        codeForeground: 'var(--code-fg)',
        codeFontFamily: 'var(--f-mono)',
        codeFontSize: '13.25px',
        codeLineHeight: '1.7',
        codePaddingBlock: '16px',
        codePaddingInline: '18px',
        uiFontFamily: 'var(--f-mono)',
        uiFontSize: '12px',
        frames: {
          shadowColor: 'transparent',
          frameBoxShadowCssValue: 'none',
          editorBackground: 'var(--code-bg)',
          editorTabBarBackground: 'var(--code-bg)',
          editorTabBarBorderColor: 'var(--code-line)',
          editorTabBarBorderBottomColor: 'var(--code-line)',
          editorActiveTabBackground: 'var(--code-bg)',
          editorActiveTabForeground: 'var(--code-mute)',
          editorActiveTabBorderColor: 'transparent',
          editorActiveTabIndicatorTopColor: 'transparent',
          editorActiveTabIndicatorBottomColor: 'transparent',
          terminalBackground: 'var(--code-bg)',
          terminalTitlebarBackground: 'var(--code-bg)',
          terminalTitlebarForeground: 'var(--code-mute)',
          terminalTitlebarBorderBottomColor: 'var(--code-line)',
          terminalTitlebarDotsForeground: 'var(--code-mute)',
          inlineButtonBackground: 'var(--code-line)',
          inlineButtonForeground: 'var(--code-fg)',
          inlineButtonBorder: 'var(--code-line)',
          tooltipSuccessBackground: 'var(--code-fg)',
          tooltipSuccessForeground: 'var(--code-bg)',
        },
      },
    },
    sidebar,
  })), {
    name: 'production-byte-inventory',
    hooks: {
      'astro:build:done': () => {
        if (design) return;
        mkdirSync(new URL('./.astro/', import.meta.url), { recursive: true });
        writeFileSync(new URL('./.astro/production-build.json', import.meta.url), JSON.stringify({ source_digest: sourceDigest(root), dist_digest: distDigest(root), deployment_url: deployment.site + deployment.base }) + '\n');
      },
    },
  }],
});
