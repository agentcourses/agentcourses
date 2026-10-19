import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

const loader = process.env.AC_SITE_MODE === 'design'
  ? glob({ pattern: '**/[^_]*.{md,mdx}', base: './tests/design/fixtures' })
  : docsLoader();
export const collections = {
  docs: defineCollection({ loader, schema: docsSchema() }),
};
