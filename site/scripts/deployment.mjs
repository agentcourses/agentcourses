// These are the two supported publication destinations; production defaults to the custom domain.
// Schema identifiers keep their permanent custom-domain identity independently of the deployment host.
export function deploymentProfile(mode = 'production', profile = process.env.AC_DEPLOYMENT ?? 'custom-domain') {
  if (!['github-pages', 'custom-domain'].includes(profile)) throw new Error(`Unsupported deployment profile: ${profile}`);
  return mode === 'design' || profile === 'custom-domain'
    ? { site: 'https://agentcourses.io', base: '/' }
    : { site: 'https://agentcourses.github.io', base: '/agentcourses/' };
}
export function withBase(href, base) {
  if (typeof href !== 'string' || !href.startsWith('/') || href.startsWith('//') || base === '/' || href.startsWith(base)) return href;
  return base.replace(/\/$/, '') + href;
}
export function deploymentLinks(base) {
  const jsx = {
    filter: ['a', 'img'],
    visit(node) {
      return { ...node, attributes: node.attributes.map((attribute) =>
        ['href', 'src'].includes(attribute.name) && typeof attribute.value === 'string'
          ? { ...attribute, value: withBase(attribute.value, base) } : attribute) };
    },
  };
  return {
    name: 'deployment-links',
    element: {
      filter: ['a', 'img'],
      visit(node, ctx) {
        for (const key of ['href', 'src']) {
          if (typeof node.properties?.[key] === 'string') ctx.setProperty(node, key, withBase(node.properties[key], base));
        }
      },
    },
    mdxJsxFlowElement: jsx,
    mdxJsxTextElement: jsx,
  };
}
