import { defineCollection } from 'astro:content';
import type { Loader, LoaderContext } from 'astro/loaders';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';
import { readFile } from 'node:fs/promises';
import { join, posix } from 'node:path';
import { pathToFileURL } from 'node:url';

const root: string = import.meta.env.REPO_ROOT;
const repository = 'https://github.com/agentcourses/agentcourses';

/** Repository files that become whole pages. The file's first heading becomes the page title. */
const pages = {
  specification: {
    file: 'spec/specification.md',
    description: 'The whole format, and the rules every runner follows, on one page.',
  },
  changelog: { file: 'CHANGELOG.md', description: 'Every change to the format, newest first.' },
};

/** Repository files shown inside a page, with their headings one level lower. */
const embeds = ['conformance/protocol.md', 'conformance/runner-checklist.md'];

/** Where each rendered repository file appears on the site. Relative links to these files point here. */
const routes: Record<string, string> = {
  'spec/specification.md': '/specification/',
  'CHANGELOG.md': '/changelog/',
  'conformance/protocol.md': '/conformance/#conformance-suite',
  'conformance/runner-checklist.md': '/conformance/#runner-checklist',
};

/**
 * Points a link from a repository file at the site. Rendered files go to their page, schemas to
 * their copy under /schemas/0.1/, and anything else to the file on GitHub.
 */
function siteHref(href: string, from: string): string {
  if (/^([a-z][a-z0-9+.-]*:|#|\/)/i.test(href)) return href;
  const [path = '', hash] = href.split('#');
  const target = posix.normalize(posix.join(posix.dirname(from), path));
  const anchor = hash ? `#${hash}` : '';
  const route = routes[target];
  if (route) return hash ? route.replace(/#.*$/, '') + anchor : route;
  if (/^schemas\/[^/]+\.json$/.test(target)) return `/schemas/0.1/${posix.basename(target)}${anchor}`;
  return `${repository}/blob/main/${target}${anchor}`;
}

/** Renders a repository Markdown file without its first heading, which Starlight shows as the title. */
async function render(context: LoaderContext, file: string, { demote = false } = {}) {
  const path = join(root, file);
  const source = await readFile(path, 'utf8');
  const heading = source.match(/^# (.+)\n+/);
  if (!heading) throw new Error(`${file} must start with a "# " heading`);
  const body = source.slice(heading[0].length);
  const rendered = await context.renderMarkdown(body, { fileURL: pathToFileURL(path) });
  let html = rendered.html.replace(/href="([^"]*)"/g, (_, href: string) => `href="${siteHref(href, file)}"`);
  if (demote) html = html.replace(/(<\/?h|level-h)([1-5])\b/g, (_, tag: string, level: string) => tag + (Number(level) + 1));
  return { title: heading[1]!.trim(), body, rendered: { ...rendered, html } };
}

/** Re-runs a load in `astro dev` when one of its repository files changes. */
function watch(context: LoaderContext, files: string[], load: () => Promise<void>) {
  const paths = files.map((file) => join(root, file));
  context.watcher?.add(paths);
  context.watcher?.on('change', (changed) => {
    if (paths.includes(changed)) load().catch((error) => context.logger.error(String(error)));
  });
}

/** Starlight's docs, plus the pages rendered from repository files. */
function docsAndRepositoryPages(): Loader {
  const docs = docsLoader();
  return {
    name: 'agentcourses-docs',
    async load(context) {
      await docs.load(context);
      const load = async () => {
        for (const [id, { file, description }] of Object.entries(pages)) {
          const { title, body, rendered } = await render(context, file);
          const editUrl = `${repository}/edit/main/${file}`;
          const data = await context.parseData({ id, data: { title, description, editUrl } });
          context.store.set({ id, data, body, rendered, filePath: `../${file}`, digest: context.generateDigest(body) });
        }
      };
      await load();
      watch(context, Object.values(pages).map((page) => page.file), load);
    },
  };
}

/** Repository files rendered for embedding in a page, by path. */
const embedLoader: Loader = {
  name: 'agentcourses-embeds',
  async load(context) {
    const load = async () => {
      // Render afresh each time: a cached entry with an unchanged digest would keep stale HTML.
      context.store.clear();
      for (const file of embeds) {
        const { title, body, rendered } = await render(context, file, { demote: true });
        context.store.set({ id: file, data: { title }, body, rendered, digest: context.generateDigest(body) });
      }
    };
    await load();
    watch(context, embeds, load);
  },
};

export const collections = {
  docs: defineCollection({ loader: docsAndRepositoryPages(), schema: docsSchema() }),
  embeds: defineCollection({ loader: embedLoader }),
};
