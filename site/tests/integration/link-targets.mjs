/**
 * Check every URL while loading each fragment-free target only once.
 * @param {Iterable<string>} hrefs
 * @param {(url: string, needsIDs: boolean) => Promise<{status: number, ids: Iterable<string>}>} loadTarget
 */
export async function inspectLinkTargets(hrefs, loadTarget) {
  const targets = new Map();
  for (const href of hrefs) {
    const url = new URL(href);
    const fragment = decodeURIComponent(url.hash.slice(1));
    url.hash = '';
    if (!targets.has(url.href)) targets.set(url.href, []);
    targets.get(url.href).push({ href, fragment });
  }
  const checks = [];
  for (const [target, links] of targets) {
    const snapshot = await loadTarget(target, links.some(({ fragment }) => fragment !== ''));
    const ids = new Set(snapshot.ids);
    for (const { href, fragment } of links) {
      checks.push({ href, status: snapshot.status, fragmentPresent: !fragment || ids.has(fragment) });
    }
  }
  return checks;
}
