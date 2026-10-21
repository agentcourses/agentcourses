// Use the same locked MDX grammar as the site; parsing never executes author JavaScript.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const siteRequire = createRequire(new URL('../site/package.json', import.meta.url));
const mdxRequire = createRequire(siteRequire.resolve('@astrojs/mdx'));
const { createProcessor } = await import(pathToFileURL(mdxRequire.resolve('@mdx-js/mdx')));
const source = readFileSync(0, 'utf8');
const includes = [];

function visit(node) {
  if ((node.type === 'mdxJsxFlowElement' || node.type === 'mdxJsxTextElement') && node.name === 'ExampleCode') {
    const properties = {};
    for (const attribute of node.attributes) {
      if (attribute.type === 'mdxJsxExpressionAttribute') {
        // A spread may replace either source. Later explicit properties can make them known again.
        delete properties.example;
        delete properties.file;
      } else if (attribute.name === 'example' || attribute.name === 'file') {
        const value = attribute.value;
        properties[attribute.name] = typeof value === 'string'
          ? ['literal', value]
          : ['expression', value === null ? '{true}' : `{${value.value}}`];
      }
    }
    includes.push(properties);
  }
  for (const child of node.children ?? []) visit(child);
}

try {
  visit(createProcessor().parse(source));
  process.stdout.write(JSON.stringify({ includes }));
} catch (error) {
  process.stdout.write(JSON.stringify({ error: String(error.message) }));
}
