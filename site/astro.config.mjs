import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { fileURLToPath } from 'node:url';

const repository = 'https://github.com/agentcourses/agentcourses';

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

export default defineConfig({
  site: 'https://agentcourses.io',
  vite: {
    // Pages read the specification, the examples and other repository files at build time.
    define: { 'import.meta.env.REPO_ROOT': JSON.stringify(fileURLToPath(new URL('../', import.meta.url))) },
  },
  integrations: [
    starlight({
      title: 'Agent Courses',
      description: 'An open format for courses that an AI agent teaches in your own project.',
      locales: { root: { label: 'English', lang: 'en-GB' } },
      favicon: '/mark.svg',
      social: [{ icon: 'github', label: 'GitHub', href: repository }],
      editLink: { baseUrl: `${repository}/edit/main/site/` },
      // The content loader renders repository files outside the docs folder, such as the
      // specification. This gives them Starlight's heading links too.
      markdown: { processedDirs: ['..'] },
      customCss: ['./src/styles/tokens.css', './src/styles/site.css'],
      components: {
        SiteTitle: './src/components/SiteTitle.astro',
        ThemeSelect: './src/components/ThemeSelect.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      // Grouped by reader: everyone, then course authors, then runner implementers.
      sidebar: [
        { label: 'Overview', slug: 'index' },
        { label: 'Specification', slug: 'specification' },
        { label: 'Runner showcase', slug: 'showcase' },
        { label: 'Changelog', slug: 'changelog' },
        {
          label: 'For course authors',
          items: [
            { label: 'Quickstart', slug: 'quickstart' },
            { label: 'Examples', slug: 'examples' },
          ],
        },
        {
          label: 'For runner implementers',
          items: [
            { label: 'Adding course support', slug: 'runners' },
            { label: 'Conformance', slug: 'conformance' },
          ],
        },
      ],
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
    }),
  ],
});
