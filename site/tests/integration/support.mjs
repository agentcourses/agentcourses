import { execFileSync, spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
export const root = fileURLToPath(new URL('../../../', import.meta.url));
export const read = (path) => readFileSync(path, 'utf8');
export function fixture(t) {
  const directory = mkdtempSync(join(tmpdir(), 'ac-integration-'));
  for (const name of ['.github/workflows', 'spec', 'schemas', 'tools', 'examples', 'docs', 'experiments', 'fixtures', 'tests/contracts/fixtures', 'site/src/content/docs']) {
    mkdirSync(dirname(join(directory, name)), { recursive: true });
    cpSync(join(root, name), join(directory, name), { recursive: true });
  }
  writeFileSync(join(directory, 'tools/document-stage.json'), '{"stage":"candidate"}\n');
  for (const name of ['pyproject.toml', 'uv.lock', 'README.md', 'CHANGELOG.md', 'AGENTS.md', 'REVIEW.md', 'CLAUDE.md', 'LICENSE', '.node-version']) cpSync(join(root, name), join(directory, name));
  symlinkSync(join(root, '.venv'), join(directory, '.venv'));
  mkdirSync(join(directory, 'site'), { recursive: true });
  symlinkSync(join(root, 'site/node_modules'), join(directory, 'site/node_modules'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  return directory;
}
export function cli(script, directory, ...args) {
  return spawnSync(process.execPath, [join(root, 'site/scripts', script), '--root', directory, ...args], { encoding: 'utf8' });
}
export function git(directory, ...args) { return execFileSync('git', ['-C', directory, ...args], { encoding: 'utf8' }).trim(); }
export function initialise(directory) {
  git(directory, 'init', '-q');
  git(directory, 'config', 'user.name', 'Fixture');
  git(directory, 'config', 'user.email', 'fixture@example.invalid');
  writeFileSync(join(directory, '.gitignore'), '.venv\nsite/node_modules\nsite/public/schemas\nsite/dist\nsite/.astro\n');
  commit(directory);
}
export function commit(directory) { git(directory, 'add', '.'); git(directory, 'commit', '-qm', 'fixture', '--allow-empty'); return git(directory, 'rev-parse', 'HEAD'); }
export function rules(result) {
  const lines = result.stderr.trim().split('\n').filter(Boolean);
  return lines.map((line) => JSON.parse(line).rule).sort();
}
