// Copies the JSON Schemas into public/schemas/0.1/, so each schema's $id URL resolves on the site.
// The copy is build output: public/schemas/ is gitignored.
import { copyFileSync, mkdirSync, readFileSync, readdirSync, rmSync } from 'node:fs';

const from = new URL('../../schemas/', import.meta.url);
const to = new URL('../public/schemas/0.1/', import.meta.url);

rmSync(to, { recursive: true, force: true });
mkdirSync(to, { recursive: true });
for (const name of readdirSync(from).filter((file) => file.endsWith('.json')).sort()) {
  const expected = `https://agentcourses.io/schemas/0.1/${name}`;
  const { $id } = JSON.parse(readFileSync(new URL(name, from), 'utf8'));
  if ($id !== expected) throw new Error(`schemas/${name} has $id ${$id}; expected ${expected}`);
  copyFileSync(new URL(name, from), new URL(name, to));
  console.log(`copied schemas/${name} to public/schemas/0.1/${name}`);
}
