import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import { existsSync, readFileSync, readdirSync, mkdirSync, writeFileSync, realpathSync } from 'node:fs';
import { resolve, dirname, posix } from 'node:path';
import { createRequire, findPackageJSON } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(new URL('../package.json', import.meta.url));
const locked = createRequire(require.resolve('@astrojs/mdx'));
const { fromMarkdown } = await import(pathToFileURL(locked.resolve('mdast-util-from-markdown')));
const { parseFragment } = await import(pathToFileURL(locked.resolve('parse5')));
export const sources = ['format', 'execution', 'consent', 'records', 'identity'].map((stem) => `spec/${stem}.md`);
export const routes = ['/', '/specification/', '/runners/', '/authors/quickstart/', '/authors/best-practices/', '/authors/checks/', '/authors/explain-back/', '/implementers/support/', '/implementers/conformance/'];
export const specification = 'site/src/content/docs/specification.mdx';
export const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
export function fail(rule, message) { const error = new Error(message); error.rule = rule; throw error; }
export function git(root, ...args) { return execFileSync('git', ['-C', root, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' } }).trim(); }
export function files(root) {
  if (!existsSync(root)) return [];
  return readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isSymbolicLink()) fail('unsafe-path', `Generated input/output cannot be a symlink: ${entry.name}`);
    return entry.isDirectory() ? files(resolve(root, entry.name)).map((p) => `${entry.name}/${p}`) : [entry.name];
  }).sort();
}
function safe(root, name) {
  const target = resolve(root, name);
  if (!target.startsWith(resolve(root) + '/')) fail('unsafe-path', name);
  if (existsSync(target) && !realpathSync(target).startsWith(realpathSync(root) + '/')) fail('unsafe-path', name);
  return target;
}
// Pagefind's runtime loads these bootstrap assets before it can answer any query.
// Resolve its CLI through Starlight so the existing lockfile owns the exact version.
const pagefindPackage = findPackageJSON('pagefind', import.meta.resolve('@astrojs/starlight'));
const pagefindCli = resolve(dirname(pagefindPackage), JSON.parse(readFileSync(pagefindPackage, 'utf8')).bin);
export function validateSearchOutput(directory) {
  const required = (name) => {
    const path = safe(directory, name);
    if (!existsSync(path)) fail('search-output', `Missing Pagefind runtime asset: ${name}`);
    const bytes = readFileSync(path);
    if (!bytes.length) fail('search-output', `Empty Pagefind runtime asset: ${name}`);
    return bytes;
  };
  let entry;
  try { entry = JSON.parse(required('pagefind-entry.json').toString()); }
  catch (error) { fail('search-output', `Invalid Pagefind bootstrap metadata: ${error.message}`); }
  if (!entry || typeof entry.version !== 'string' || !entry.version || !entry.languages ||
      typeof entry.languages !== 'object' || Array.isArray(entry.languages) || !Object.keys(entry.languages).length) {
    fail('search-output', 'Invalid Pagefind bootstrap language inventory');
  }
  for (const name of ['pagefind.js', 'pagefind-worker.js']) required(name);
  const decompress = (name) => {
    try {
      const bytes = gunzipSync(required(name));
      const prefix = Buffer.from('pagefind_dcd');
      if (!bytes.subarray(0, prefix.length).equals(prefix) || bytes.length === prefix.length) throw new Error('Missing Pagefind payload');
      return bytes.subarray(prefix.length);
    } catch (error) { fail('search-output', `Invalid Pagefind payload ${name}: ${error.message}`); }
  };
  for (const language of Object.values(entry.languages)) {
    if (!language || typeof language.hash !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(language.hash) ||
        (language.wasm != null && (typeof language.wasm !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(language.wasm))) ||
        !Number.isInteger(language.page_count) || language.page_count < 1) {
      fail('search-output', 'Invalid Pagefind language reference');
    }
    decompress(`pagefind.${language.hash}.pf_meta`);
    const wasm = `wasm.${language.wasm || 'unknown'}.pagefind`;
    if (!WebAssembly.validate(decompress(wasm))) fail('search-output', `Invalid Pagefind WebAssembly: ${wasm}`);
  }
  // Check emitted search data too. Optional UI variants and unused language WASM
  // are not runtime requirements and may legitimately be empty.
  for (const name of files(directory)) {
    if (/^(index|filter|fragment)\/.*\.pf_(index|filter|fragment)$/.test(name)) {
      const payload = decompress(name);
      if (name.startsWith('fragment/')) {
        try { JSON.parse(payload.toString()); }
        catch { fail('search-output', `Invalid Pagefind fragment JSON: ${name}`); }
      }
    }
  }
  return entry;
}
export function buildSearch(directory) {
  // Process completion owns all writes; no service shutdown can truncate them.
  execFileSync(process.execPath, [pagefindCli, '--site', directory, '--output-path', resolve(directory, 'pagefind')], { stdio: 'inherit' });
  return validateSearchOutput(resolve(directory, 'pagefind'));
}
export function sourceMap(root) {
  try {
    return JSON.parse(execFileSync('uv', ['run', '--locked', '--no-sync', 'python', 'tools/check_docs.py', '--root', root, '--site-map'], {
      cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
    }));
  } catch (error) { fail('source-map', `Canonical source map failed: ${error.stderr ?? error.message}`); }
}
function walk(node, visit) { visit(node); for (const child of node.children ?? []) walk(child, visit); }
function compose(root, mapping) {
  const lookup = new Map(mapping.anchors.map((entry) => [`${entry.source}#${entry.anchor}`, entry.public]));
  if (lookup.size !== mapping.anchors.length) fail('duplicate-anchor', 'Canonical map contains repeated source IDs');
  const publicIDs = mapping.anchors.map((entry) => entry.public);
  if (new Set(publicIDs).size !== publicIDs.length) fail('duplicate-anchor', 'Canonical map contains repeated output IDs');
  const sections = sources.map((name) => {
    if (!existsSync(safe(root, name))) fail('source-map', `Missing canonical source ${name}`);
    const source = readFileSync(safe(root, name), 'utf8');
    const tree = fromMarkdown(source);
    const stem = posix.basename(name, '.md');
    const edits = [];
    let previousHeading = 1;
    const change = (node, text) => edits.push({ start: node.position.start.offset, end: node.position.end.offset, text });
    function destination(href) {
      if (href.includes('tutr-strategy') || /(?:^|\/)bench\//.test(href) || /(?:^|\/)docs\/(?:scenarios|decisions)\//.test(href) || href.includes('/docs/delivery/contracts.md')) fail('private-register-link', `${name}: ${href}`);
      if (/^[a-z][\w+.-]*:/i.test(href) || href.startsWith('//')) return href;
      const url = new URL(href, `https://source.invalid/${name}`);
      const target = decodeURIComponent(url.pathname).slice(1);
      const anchor = decodeURIComponent(url.hash.slice(1));
      if (target === 'docs/delivery/contracts.md' || target.startsWith('bench/') || target.startsWith('docs/decisions/') || target.startsWith('docs/scenarios/') || target.includes('tutr-strategy')) {
        fail('private-register-link', `Private source reference in ${name}: ${href}`);
      }
      if (sources.includes(target)) {
        const mapped = lookup.get(`${target}#${anchor}`);
        if (!mapped) fail('unknown-anchor', `${name}: ${href}`);
        return mapped;
      }
      if (url.pathname.startsWith('/specification/')) {
        if (url.pathname !== '/specification/' || (anchor && !publicIDs.includes(`/specification/#${anchor}`))) fail('unknown-anchor', href);
        return href;
      }
      if (url.pathname.startsWith('/') && routes.includes(url.pathname)) return href;
      if (!existsSync(safe(root, target))) fail('missing-source-link', `${name}: ${href}`);
      return `https://github.com/agentcourses/agentcourses/blob/main/${target}${url.hash}`;
    }
    walk(tree, (node) => {
      if (node.type === 'heading') {
        const start = node.position.start.offset;
        // Keep source headings below the page title without skipping accessible heading levels.
        const depth = Math.min(node.depth + 1, previousHeading + 1, 6);
        previousHeading = depth;
        edits.push({ start, end: start + node.depth, text: '#'.repeat(depth) });
      } else if (node.type === 'link' || node.type === 'image') {
        const original = source.slice(node.position.start.offset, node.position.end.offset);
        const next = destination(node.url);
        if (next !== node.url) {
          const opening = original.lastIndexOf('](');
          if (opening < 0) fail('source-link', `Unsupported link form in ${name}`);
          const begin = node.position.start.offset + opening + 2;
          edits.push({ start: begin, end: begin + node.url.length, text: next });
        }
      } else if (node.type === 'definition') {
        const next = destination(node.url);
        if (next !== node.url) {
          const raw = source.slice(node.position.start.offset, node.position.end.offset);
          const offset = raw.indexOf(node.url);
          edits.push({ start: node.position.start.offset + offset, end: node.position.start.offset + offset + node.url.length, text: next });
        }
      } else if (node.type === 'html') {
        const fragment = parseFragment(node.value, { sourceCodeLocationInfo: true });
        const visitHTML = (element) => {
          if (element.tagName === 'summary' && element.sourceCodeLocation?.startOffset > 0 && node.value[element.sourceCodeLocation.startOffset - 1] !== '\n') {
            const offset = node.position.start.offset + element.sourceCodeLocation.startOffset;
            edits.push({ start: offset, end: offset, text: '\n' });
          }
          for (const attribute of element.attrs ?? []) {
            const location = element.sourceCodeLocation?.attrs?.[attribute.name];
            if (!location || !['id', 'href', 'src'].includes(attribute.name)) continue;
            let value;
            if (attribute.name === 'id') {
              const mapped = lookup.get(`${name}#${attribute.value}`);
              if (!mapped) fail('unknown-anchor', `${name}#${attribute.value}`);
              value = mapped.split('#')[1];
            } else value = destination(attribute.value);
            const start = node.position.start.offset + location.startOffset;
            edits.push({ start, end: node.position.start.offset + location.endOffset, text: `${attribute.name}="${value.replaceAll('"', '&quot;')}"` });
          }
          for (const child of element.childNodes ?? []) visitHTML(child);
        };
        visitHTML(fragment);
      } else if (node.type === 'text') {
        const raw = source.slice(node.position.start.offset, node.position.end.offset);
        const escaped = raw.replaceAll('{', '&#123;').replaceAll('}', '&#125;').replaceAll('<', '&lt;');
        if (escaped !== raw) change(node, escaped);
      }
    });
    let output = source;
    for (const edit of edits.sort((a, b) => b.start - a.start || b.end - a.end)) output = output.slice(0, edit.start) + edit.text + output.slice(edit.end);
    return `<a id="${stem}"></a>\n\n${output.trim()}\n\nSource: [${name}](https://github.com/agentcourses/agentcourses/blob/main/${name}).`;
  });
  return `---\ntitle: Specification\ndescription: The complete candidate course, execution, consent, records and identity contracts.\n---\n\n{/* Generated by site/scripts/generate.mjs. Edit the canonical sources, then regenerate. */}\n\nThis reference is composed from five canonical specification sources in their fixed reading order. Edit the canonical sources linked below.\n\n${sections.join('\n\n---\n\n')}\n`;
}
function manifestInput(root, ref) {
  const seen = new Set();
  const candidates = new Set();
  function read(name, retained = false) {
    try {
      if (ref) return execFileSync('git', ['-C', root, 'show', `${ref}:${name}`], { stdio: ['ignore', 'pipe', 'pipe'] });
      return readFileSync(safe(root, name));
    } catch { fail(ref || retained ? 'history-input' : 'schema-input', `Missing ${name}${ref ? ` at ${ref}` : ''}`); }
  }
  const version = /^[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$/;
  function load(name, retained = false, expectedCandidate) {
    let manifest;
    const bytes = read(name, retained);
    try { manifest = JSON.parse(bytes); } catch { fail('schema-manifest', 'Invalid schema manifest JSON'); }
    if (!version.test(manifest.candidate) || candidates.has(manifest.candidate) || expectedCandidate && manifest.candidate !== expectedCandidate || manifest.dialect !== 'https://json-schema.org/draft/2020-12/schema' || manifest.releases?.length !== 1 || manifest.releases[0].candidate !== manifest.candidate || !manifest.releases[0].schemas?.length) fail('schema-manifest', 'Source manifest must describe exactly its current candidate');
    candidates.add(manifest.candidate);
    if (retained && manifest.retained?.length) fail('schema-manifest', 'Retained manifests cannot retain further candidates');
    const payloads = new Map();
    for (const schema of manifest.releases[0].schemas) {
      let uri;
      try { uri = new URL(schema.id); } catch { fail('schema-manifest', 'Schema ID must be an absolute HTTPS URL'); }
      const filename = posix.basename(uri.pathname);
      const canonicalID = `https://agentcourses.io/schemas/${manifest.candidate}/${filename}`;
      const sourcePath = manifest.retained?.length && !retained ? `schemas/${manifest.candidate}/${filename}` : `schemas/${filename}`;
      // Old flat releases keep their exact source paths; new inventories own nested payloads explicitly.
      if (schema.id !== canonicalID || !/^[a-z][a-z0-9-]*\.schema\.json$/.test(filename) || schema.path !== sourcePath || seen.has(schema.path)) fail('schema-manifest', `Unsafe or repeated schema identifier: ${schema.id}`);
      seen.add(schema.path);
      const payload = read(schema.path, retained);
      if (hash(payload) !== schema.sha256) fail('schema-checksum', schema.path);
      let data;
      try { data = JSON.parse(payload); } catch { fail('schema-json', schema.path); }
      if (data.$id !== schema.id || data.$schema !== manifest.dialect) fail('schema-id', schema.path);
      payloads.set(uri.pathname.slice(1), payload);
    }
    const history = [];
    if (manifest.retained !== undefined && !Array.isArray(manifest.retained)) fail('schema-manifest', 'Retained inventory must be a list');
    for (const entry of manifest.retained ?? []) {
      if (!version.test(entry.candidate) || entry.manifest_path !== `schemas/history/${entry.candidate}/manifest.json` || !/^[0-9a-f]{40}$|^[0-9a-f]{64}$/.test(entry.source_commit) || entry.status !== 'retained-unfrozen') fail('schema-manifest', 'Unsafe retained inventory');
      history.push(load(entry.manifest_path, true, entry.candidate));
    }
    return { manifest, payloads, history, bytes };
  }
  const current = load('schemas/manifest.json');
  const listed = ref ? git(root, 'ls-tree', '-r', '--name-only', ref, 'schemas').split('\n').filter((name) => name.endsWith('.schema.json')) : files(resolve(root, 'schemas')).filter((name) => name.endsWith('.schema.json')).map((name) => `schemas/${name}`);
  if (listed.some((name) => !seen.has(name))) fail('unlisted-schema', 'Every recursive schema source must have one inventory owner');
  return current;
}
export function schemaOutputs(root) {
  const current = manifestInput(root);
  let tags = [];
  if (existsSync(resolve(root, '.git'))) {
    if (git(root, 'rev-parse', '--is-shallow-repository') === 'true') fail('missing-history', 'Fetch complete release tags before generating');
    tags = git(root, 'tag', '--list', 'agentcourses-v*').split('\n').filter(Boolean).sort();
  }
  const versions = new Map(current.history.map((release) => [release.manifest.candidate, release]));
  function sameRelease(a, b) {
    return a.bytes.equals(b.bytes) && a.payloads.size === b.payloads.size && [...a.payloads].every(([name, bytes]) => b.payloads.get(name)?.equals(bytes));
  }
  for (const tag of tags) {
    const release = manifestInput(root, tag);
    if (tag !== `agentcourses-v${release.manifest.candidate}`) fail('history-input', `Release tag and candidate disagree: ${tag}`);
    const retained = versions.get(release.manifest.candidate);
    if (retained && !sameRelease(retained, release)) fail('frozen-identity', 'Retained candidate differs from its protected release tag');
    versions.set(release.manifest.candidate, release);
    for (const historical of release.history) {
      const existing = versions.get(historical.manifest.candidate);
      if (existing && !sameRelease(existing, historical)) fail('frozen-identity', 'Historical candidates disagree');
      versions.set(historical.manifest.candidate, historical);
    }
  }
  const oldInventory = resolve(root, 'site/public/schemas/manifest.json');
  if (existsSync(oldInventory)) {
    let previous;
    try { previous = JSON.parse(readFileSync(oldInventory)); } catch { fail('schema-manifest', 'Invalid generated inventory'); }
    for (const release of previous.releases ?? []) if (release.candidate !== current.manifest.candidate && !versions.has(release.candidate)) fail('missing-history', `Missing protected release tag for ${release.candidate}`);
  }
  const frozen = versions.get(current.manifest.candidate);
  if (frozen && !sameRelease(frozen, current)) fail('frozen-identity', 'Candidate identity already names different frozen bytes');
  versions.set(current.manifest.candidate, current);
  const releases = [...versions.values()].sort((a, b) => a.manifest.candidate.localeCompare(b.manifest.candidate));
  const output = new Map(releases.flatMap((entry) => [...entry.payloads]));
  const manifest = { candidate: current.manifest.candidate, dialect: current.manifest.dialect, releases: releases.map((entry) => entry.manifest.releases[0]) };
  output.set('schemas/manifest.json', Buffer.from(JSON.stringify(manifest, null, 2) + '\n'));
  return { output, manifest };
}
export function expected(root) {
  const mapping = sourceMap(root);
  const output = new Map([[specification, Buffer.from(compose(root, mapping))]]);
  for (const [name, bytes] of schemaOutputs(root).output) output.set(`site/public/${name}`, bytes);
  return output;
}
export function drift(root, output, specOnly = false) {
  const differences = [];
  for (const [name, bytes] of output) {
    if (specOnly && name !== specification) continue;
    if (!existsSync(safe(root, name)) || !readFileSync(safe(root, name)).equals(bytes)) differences.push(name);
  }
  if (!specOnly) for (const name of files(resolve(root, 'site/public/schemas'))) if (!output.has(`site/public/schemas/${name}`)) differences.push(`site/public/schemas/${name}`);
  return differences.sort();
}
export function argumentsFor(argv, flags = []) {
  const options = { root: process.cwd() };
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    if (flag === '--root') { if (!argv[i + 1] || argv[i + 1].startsWith('--')) fail('invalid-arguments', '--root requires a path'); options.root = resolve(argv[++i]); }
    else if (flags.includes(flag)) options[flag.slice(2)] = true;
    else fail('invalid-arguments', `Unknown option ${flag}`);
  }
  return options;
}
export function report(error) { console.error(JSON.stringify({ rule: error.rule ?? 'verification-error', message: error.message })); process.exitCode = error.rule === 'invalid-arguments' ? 2 : 1; }
if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  try {
    const { root } = argumentsFor(process.argv.slice(2));
    const output = expected(root);
    const extra = files(resolve(root, 'site/public/schemas')).filter((name) => !output.has(`site/public/schemas/${name}`));
    if (extra.length) fail('unlisted-output', extra.join(', '));
    for (const [name, bytes] of output) { mkdirSync(dirname(safe(root, name)), { recursive: true }); writeFileSync(safe(root, name), bytes); }
    console.log(`Generated specification and ${output.size - 1} schema inventory/payload files.`);
  } catch (error) { report(error); }
}
