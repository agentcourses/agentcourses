import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, isAbsolute } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { expected, drift, schemaOutputs, routes, hash, files, git, fail, report } from './generate.mjs';

const require = createRequire(new URL('../package.json', import.meta.url));
const locked = createRequire(require.resolve('@astrojs/mdx'));
const { parse: parseYAML } = await import(pathToFileURL(locked.resolve('yaml')));
const { fromMarkdown } = await import(pathToFileURL(locked.resolve('mdast-util-from-markdown')));
const { parse: parseHTML } = await import(pathToFileURL(locked.resolve('parse5')));
export function sourceDigest(root) {
  const names = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z').split('\0').filter(Boolean);
  return hash([...new Set(names)].sort().map((name) => `${name}\0${hash(readFileSync(resolve(root, name)))}\n`).join(''));
}
export function distDigest(root) {
  const directory = resolve(root, 'site/dist');
  const names = files(directory);
  if (!names.length) fail('build-provenance', 'Production dist is missing or empty');
  return hash(names.map((name) => `${name}\0${hash(readFileSync(resolve(directory, name)))}\n`).join(''));
}
function clean(root) {
  if (git(root, 'status', '--porcelain', '--untracked-files=normal')) fail('dirty-source', 'Inspect a clean committed source tree');
}
function metadata(text) {
  if (!text.startsWith('---\n')) return {};
  const end = text.indexOf('\n---', 4);
  if (end < 0) return {};
  try { return parseYAML(text.slice(4, end)) ?? {}; } catch { return {}; }
}
function closure(root, manifest) {
  const page = resolve(root, 'docs/releases/candidate.md');
  if (!existsSync(page)) fail('candidate-blocker', 'Candidate closure record is missing');
  const record = metadata(readFileSync(page, 'utf8'));
  if (record.candidate !== manifest.candidate || !Array.isArray(record.blockers) || record.blockers.length || !record.contract_approval || !record.receipt_approval) fail('candidate-blocker', 'Candidate needs no blockers and linked contract and receipt approvals');
  for (const key of ['contract_approval', 'receipt_approval']) {
    try { if (typeof record[key] !== 'string' || new URL(record[key]).protocol !== 'https:') throw new Error(); } catch { fail('candidate-blocker', `Candidate ${key} must link to HTTPS owner evidence`); }
  }
  try {
    execFileSync('uv', ['run', '--locked', '--no-sync', 'python', 'tools/check_docs.py', '--root', root, '--scope', 'candidate'], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
    const pending = execFileSync('uv', ['run', '--locked', '--no-sync', 'python', '-c', 'import sys; from pathlib import Path; sys.path.insert(0,"tools"); from check_docs import table_rows; print(sum(row.get("state", "").lower() == "pending" for row in table_rows(Path("spec/requirements.md").read_text())))'], { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } }).trim();
    if (pending !== '0') fail('candidate-blocker', 'Requirement register still contains pending obligations');
  } catch (error) { if (error.rule) throw error; fail('candidate-blocker', `Candidate source closure failed: ${error.stderr ?? error.message}`); }
}
function workflowSafety(root) {
  let workflow;
  try { workflow = parseYAML(readFileSync(resolve(root, '.github/workflows/pages.yml'), 'utf8')); } catch { fail('workflow-safety', 'Publication workflow is missing or invalid'); }
  const jobs = workflow.jobs ?? {};
  const checkJobs = Object.entries(jobs).filter(([, job]) => (job.steps ?? []).some((step) => /(^|\n)\s*make check\s*(\n|$)/.test(step.run ?? '')));
  if (checkJobs.length !== 1) fail('workflow-safety', 'Exactly one checks job must run ordinary make check');
  const [checkName, check] = checkJobs[0];
  if (check.if !== undefined || check['continue-on-error'] || check.permissions === 'write-all' || workflow.permissions === 'write-all') fail('workflow-safety', 'The checks job must run without failure bypasses or write permissions');
  const gateSteps = (check.steps ?? []).filter((step) => (step.run ?? '').trim() === 'make check');
  if (gateSteps.length !== 1 || gateSteps[0].if !== undefined || gateSteps[0]['continue-on-error'] || (gateSteps[0].shell && gateSteps[0].shell !== 'bash')) fail('workflow-safety', 'Ordinary make check must be an unconditional failing step');
  const steps = check.steps ?? [];
  const uploads = steps.filter((step) => (step.uses ?? '').startsWith('actions/upload-pages-artifact@'));
  const deploys = Object.values(jobs).filter((job) => (job.steps ?? []).some((step) => (step.uses ?? '').startsWith('actions/deploy-pages@')));
  const expressionValue = (condition) => String(condition ?? '').trim().replace(/^\$\{\{\s*/, '').replace(/\s*\}\}$/, '').replace(/\s+/g, ' ');
  const guard = (condition) => expressionValue(condition) === 'success() && !inputs.prove_failure';
  const input = workflow.on?.workflow_dispatch?.inputs?.prove_failure;
  if (input?.type !== 'boolean' || input.default !== false || Object.keys(workflow.on ?? {}).some((event) => !['push', 'workflow_dispatch'].includes(event)) || !workflow.on?.push) fail('workflow-safety', 'Workflow must expose a false-default boolean failure proof and exclude PR events');
  const branches = workflow.on.push.branches;
  const publication = 'agent-courses-specification/ac-14-publish-and-freeze-the-reviewed-candidate';
  if (!Array.isArray(branches) || branches.length !== 2 || !branches.includes('main') || !branches.includes(publication)) fail('workflow-safety', 'Only the reviewed publication branch and main may deploy');
  const permissions = workflow.permissions ?? {};
  if (permissions.pages === 'write' || permissions['id-token'] === 'write' || check.permissions?.pages === 'write' || check.permissions?.['id-token'] === 'write') fail('workflow-safety', 'Only deployment may request Pages or OIDC writes');
  const upload = uploads[0];
  if (uploads.length !== 1 || steps.at(-1) !== upload || upload.with?.path !== 'site/dist' || !guard(upload.if)) fail('workflow-safety', 'Only a successful normal check may upload its tested dist as the final step');
  if (!steps.some((step) => expressionValue(step.if) === 'inputs.prove_failure' && (step.run ?? '').includes('tools/prove_gate_failure.py --prepare-only') && /make check\s+CHECK_ROOT=/.test(step.run ?? ''))) fail('workflow-safety', 'Failure proof must inspect a temporary bad input with ordinary make check');
  if (deploys.length !== 1) fail('workflow-safety', 'Exactly one deployment job is required');
  const deploy = deploys[0];
  const dependencies = Array.isArray(deploy.needs) ? deploy.needs : [deploy.needs];
  const expression = expressionValue(deploy.if);
  // OR is allowed only inside the explicit, closed ref allow-list.
  const refs = `(github.ref == 'refs/heads/main' || github.ref == 'refs/heads/${publication}')`;
  if (dependencies.length !== 1 || dependencies[0] !== checkName || expression !== `success() && !inputs.prove_failure && github.event_name != 'pull_request' && ${refs}` || !deploy.environment || deploy.permissions?.pages !== 'write' || deploy.permissions?.['id-token'] !== 'write') fail('workflow-safety', 'Deployment requires successful checks, an allowed ref, an approved environment and a non-failure non-PR event');
  for (const [name, job] of Object.entries(jobs)) {
    if (job === deploy) continue;
    if ((job.steps ?? []).some((step) => (step.uses ?? '').startsWith('actions/deploy-pages@') || ((step.uses ?? '').startsWith('actions/upload-pages-artifact@') && name !== checkName))) fail('workflow-safety', 'Unexpected upload or deploy job');
  }
}
function freeze(root, options, manifest) {
  if (!options.approvalRecord || !isAbsolute(options.approvalRecord) || !existsSync(options.approvalRecord)) fail('approval-record', 'An existing absolute approval-record path is required');
  clean(root);
  let record;
  const evidence = readFileSync(options.approvalRecord, 'utf8');
  try { record = JSON.parse(evidence); } catch {
    const records = [];
    const frontmatter = metadata(evidence);
    if (frontmatter.decision) records.push(frontmatter);
    const visit = (node) => {
      if (node.type === 'code' && ['json', 'yaml', 'yml'].includes(node.lang)) {
        try { const value = node.lang === 'json' ? JSON.parse(node.value) : parseYAML(node.value); if (value?.decision) records.push(value); } catch { /* Unrelated examples are not approval evidence. */ }
      }
      for (const child of node.children ?? []) visit(child);
    };
    visit(fromMarkdown(evidence));
    if (records.length !== 1) fail('approval-record', 'Supply exactly one structured freeze decision in the evidence record');
    [record] = records;
  }
  const commit = options.frozenRef ? git(root, 'rev-parse', `${options.frozenRef}^{commit}`) : git(root, 'rev-parse', 'HEAD');
  const tree = git(root, 'rev-parse', `${commit}^{tree}`);
  const required = ['candidate', 'build_commit', 'build_tree', 'manifest_sha256', 'deployment_run_url', 'owner', 'approved_at', 'decision_link'];
  if (!record || typeof record !== 'object' || Array.isArray(record) || required.some((key) => typeof record[key] !== 'string' || !record[key].trim()) || record.decision !== 'approved' || record.candidate !== manifest.candidate || record.build_commit !== commit || record.build_tree !== tree || record.manifest_sha256 !== hash(readFileSync(resolve(root, 'schemas/manifest.json'))) || !Number.isFinite(Date.parse(record.approved_at))) fail('approval-binding', 'Owner approval must bind the exact candidate, clean commit/tree and manifest');
  for (const key of ['deployment_run_url', 'decision_link']) {
    try { if (new URL(record[key]).protocol !== 'https:') throw new Error(); } catch { fail('approval-binding', `Approval ${key} must be an HTTPS evidence link`); }
  }
}
function htmlIdentity(bytes) {
  const tree = parseHTML(bytes.toString('utf8'));
  const result = { title: '', h1: '', canonical: [] };
  const text = (node) => node.nodeName === '#text' ? node.value : (node.childNodes ?? []).map(text).join('');
  const visit = (node) => {
    if (node.tagName === 'title') result.title = text(node).trim();
    if (node.tagName === 'h1') result.h1 = text(node).trim();
    if (node.tagName === 'link') {
      const attrs = Object.fromEntries(node.attrs.map(({ name, value }) => [name, value]));
      if ((attrs.rel ?? '').split(/\s+/).includes('canonical')) result.canonical.push(attrs.href);
    }
    for (const child of node.childNodes ?? []) visit(child);
  };
  visit(tree); return result;
}
export async function verifyRelease(options) {
  const root = resolve(options.root ?? process.cwd());
  let origin;
  if (options.url) {
    try {
      const url = new URL(options.url);
      if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error();
      origin = url.origin;
    } catch { fail('invalid-arguments', '--url requires an HTTPS origin without credentials, path, query or fragment'); }
  }
  if (options.frozenRef) {
    clean(root);
    let tree;
    try {
      if (!/^agentcourses-v[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$/.test(options.frozenRef)) throw new Error();
      git(root, 'show-ref', '--verify', `refs/tags/${options.frozenRef}`);
      tree = git(root, 'rev-parse', `refs/tags/${options.frozenRef}^{tree}`);
    } catch { fail('missing-history', `Missing frozen reference ${options.frozenRef}`); }
    if (tree !== git(root, 'rev-parse', 'HEAD^{tree}')) fail('frozen-tree', 'Current clean source tree differs from the frozen tag');
  }
  const { manifest } = schemaOutputs(root);
  if (options.frozenRef && options.frozenRef !== `agentcourses-v${manifest.candidate}`) fail('frozen-tree', 'Frozen reference must identify the inspected manifest candidate');
  if (options.preflight || options.requireFreeze) closure(root, manifest);
  if (options.preflight) workflowSafety(root);
  if (options.requireFreeze) freeze(root, options, manifest);
  const differences = drift(root, expected(root));
  if (differences.length) fail('generated-drift', differences.join(', '));
  const result = { candidate: manifest.candidate };
  if (!origin) return result;
  clean(root);
  const source = sourceDigest(root); const built = distDigest(root);
  let provenance;
  try { provenance = JSON.parse(readFileSync(resolve(root, 'site/.astro/production-build.json'))); } catch { fail('build-provenance', 'Build this clean production source before live verification'); }
  if (provenance.source_digest !== source || provenance.dist_digest !== built) fail('build-provenance', 'Production artefact does not match this clean source and dist inventory');
  const transport = options.transport ?? (async (url) => {
    const response = await fetch(url, { redirect: 'manual' });
    return { status: response.status, headers: Object.fromEntries(response.headers), body: Buffer.from(await response.arrayBuffer()), url: response.url };
  });
  async function response(path, allowedTypes) {
    let url = new URL(path, origin).href;
    for (let redirects = 0; redirects < 6; redirects++) {
      let result;
      try { result = await transport(url); } catch (error) { fail('live-network', `${url}: ${error.message}`); }
      const headers = Object.fromEntries(Object.entries(result.headers ?? {}).map(([key, value]) => [key.toLowerCase(), value]));
      if (result.url && new URL(result.url).origin !== origin) fail('live-redirect', `Response escaped the approved origin: ${result.url}`);
      if (result.status >= 300 && result.status < 400) {
        let target;
        try { target = new URL(headers.location, url); } catch { fail('live-redirect', `Invalid redirect from ${url}`); }
        if (!headers.location || target.protocol !== 'https:' || target.origin !== origin) fail('live-redirect', `Unsafe redirect from ${url}`);
        url = target.href; continue;
      }
      if (result.status !== 200) fail('live-status', `${path}: HTTP ${result.status}`);
      const type = String(headers['content-type'] ?? '').split(';')[0].trim().toLowerCase();
      if (allowedTypes && !allowedTypes.includes(type)) fail('live-type', `${path}: ${type || 'missing content type'}`);
      return Buffer.from(result.body);
    }
    fail('live-redirect', `Too many redirects from ${path}`);
  }
  for (const path of routes) {
    const file = path === '/' ? 'index.mdx' : `${path.slice(1, -1)}.mdx`;
    const title = metadata(readFileSync(resolve(root, 'site/src/content/docs', file), 'utf8')).title;
    const identity = htmlIdentity(await response(path, ['text/html']));
    if (identity.h1 !== title || ![title, `${title} | Agent Courses`].includes(identity.title)) fail('live-title', `Wrong page identity at ${path}; expected ${title}`);
    if (identity.canonical.length !== 1 || identity.canonical[0] !== `${origin}${path}`) fail('live-canonical', `Wrong canonical URL at ${path}`);
  }
  const publicManifest = await response('/schemas/manifest.json', ['application/json']);
  if (!publicManifest.equals(readFileSync(resolve(root, 'site/public/schemas/manifest.json')))) fail('live-bytes', 'Release inventory bytes differ');
  for (const release of manifest.releases) for (const schema of release.schemas) {
    const uri = new URL(schema.id);
    if (uri.origin !== origin) fail('live-schema-id', `Schema ID is outside the live origin: ${schema.id}`);
    const bytes = await response(uri.pathname, ['application/schema+json', 'application/json']);
    let payload;
    try { payload = JSON.parse(bytes); } catch { fail('live-schema-id', `Invalid schema JSON at ${schema.id}`); }
    if (payload.$id !== schema.id) fail('live-schema-id', schema.id);
    if (hash(bytes) !== schema.sha256) fail('live-bytes', schema.id);
  }
  const names = files(resolve(root, 'site/dist')); const live = [];
  for (const name of names) {
    const path = name === 'index.html' ? '/' : name.endsWith('/index.html') ? `/${name.slice(0, -10)}` : `/${name}`;
    const bytes = await response(path);
    if (!bytes.equals(readFileSync(resolve(root, 'site/dist', name)))) fail('live-bytes', `Deployed asset differs: ${name}`);
    live.push(`${name}\0${hash(bytes)}\n`);
  }
  return { ...result, source_digest: source, build_digest: built, live_digest: hash(live.join('')) };
}
if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  try {
    const options = { root: process.cwd() };
    const values = { '--root': 'root', '--url': 'url', '--frozen-ref': 'frozenRef', '--approval-record': 'approvalRecord' };
    const flags = { '--preflight': 'preflight', '--check-history': 'checkHistory', '--require-freeze': 'requireFreeze' };
    for (let i = 2; i < process.argv.length; i++) {
      const arg = process.argv[i];
      if (values[arg]) { if (!process.argv[i + 1] || process.argv[i + 1].startsWith('--')) fail('invalid-arguments', `${arg} requires a value`); options[values[arg]] = process.argv[++i]; }
      else if (flags[arg]) options[flags[arg]] = true;
      else fail('invalid-arguments', `Unknown option ${arg}`);
    }
    console.log(JSON.stringify(await verifyRelease(options)));
  } catch (error) { report(error); }
}
