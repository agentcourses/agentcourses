// Serve current schemas alongside the immutable 0.1.0 release schemas.
// public/schemas/ is ignored build output. CI fetches history for the pinned source.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = new URL('../../', import.meta.url);
const from = new URL('schemas/', root);
const to = new URL('../public/schemas/', import.meta.url);
const published01 = '616002d0869870fc9fc6a1cca17887f28d55f645'; // v0.1.0
const names = readdirSync(from).filter((file) => file.endsWith('.json')).sort();
const releases = [
  ['0.1', names.map((name) => [name, execFileSync('git', ['show', `${published01}:schemas/${name}`], { cwd: fileURLToPath(root) })])],
  ['0.2', names.map((name) => [name, readFileSync(new URL(name, from))])],
];

// Validate every address before replacing an earlier build's output.
for (const [version, schemas] of releases) {
  for (const [name, bytes] of schemas) {
    const expected = `https://agentcourses.io/schemas/${version}/${name}`;
    const { $id } = JSON.parse(bytes.toString('utf8'));
    if ($id !== expected) throw new Error(`${version}/${name} has $id ${$id}; expected ${expected}`);
  }
}
rmSync(to, { recursive: true, force: true });
for (const [version, schemas] of releases) {
  const destination = new URL(`${version}/`, to);
  mkdirSync(destination, { recursive: true });
  for (const [name, bytes] of schemas) {
    writeFileSync(new URL(name, destination), bytes);
    console.log(`copied schemas/${version}/${name}`);
  }
}
