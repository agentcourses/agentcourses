import { expect, type Page } from '@playwright/test';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export type Scheme = 'light' | 'dark';

/** The nine candidate destinations, in sidebar order, each backed by one design fixture. */
export const destinations = [
  { path: '/', label: 'Overview', fixture: 'index.mdx', group: null },
  { path: '/specification/', label: 'Specification', fixture: 'specification.mdx', group: null },
  { path: '/runners/', label: 'Runner showcase', fixture: 'runners.mdx', group: null },
  { path: '/authors/quickstart/', label: 'Quickstart', fixture: 'authors/quickstart.mdx', group: 'For course authors' },
  { path: '/authors/best-practices/', label: 'Best practices', fixture: 'authors/best-practices.mdx', group: 'For course authors' },
  { path: '/authors/checks/', label: 'Writing checks', fixture: 'authors/checks.mdx', group: 'For course authors' },
  { path: '/authors/explain-back/', label: 'Explain-back and rubrics', fixture: 'authors/explain-back.mdx', group: 'For course authors' },
  { path: '/implementers/support/', label: 'Add course support', fixture: 'implementers/support.mdx', group: 'For runner implementers' },
  { path: '/implementers/conformance/', label: 'Conformance', fixture: 'implementers/conformance.mdx', group: 'For runner implementers' },
] as const;

/** A long article fixture with code, a wide table, callouts, cards and steps. */
export const article = '/authors/checks/';

export const phone = { width: 390, height: 844 };
export const desktop = { width: 1440, height: 1000 };
export const schemes: Scheme[] = ['light', 'dark'];

export function fixturePath(fixture: string): string {
  return fileURLToPath(new URL(`./fixtures/${fixture}`, import.meta.url));
}

export function missingFixtures(): string[] {
  return destinations.map((d) => d.fixture).filter((fixture) => !existsSync(fixturePath(fixture)));
}

/** Opens a page with the viewer's system colour scheme set, so the site's automatic theme applies. */
export async function open(page: Page, path: string, scheme: Scheme = 'light'): Promise<void> {
  await page.emulateMedia({ colorScheme: scheme });
  const response = await page.goto(path);
  expect(response?.status(), `${path} should be served`).toBe(200);
  await expect(page.locator('html')).toHaveAttribute('data-theme', scheme);
}

/** Parses a computed `rgb()`/`rgba()` colour into channels. */
export function channels(colour: string): [number, number, number, number] {
  const match = colour.match(/rgba?\(([^)]+)\)/);
  if (!match) throw new Error(`Unexpected colour format: ${colour}`);
  const parts = match[1].split(/[\s,/]+/).filter(Boolean).map(Number);
  return [parts[0], parts[1], parts[2], parts[3] ?? 1];
}

function luminance([r, g, b]: [number, number, number, number]): number {
  const linear = [r, g, b].map((value) => {
    const c = value / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

/** WCAG contrast ratio between two opaque computed colours. */
export function contrast(foreground: string, background: string): number {
  const a = luminance(channels(foreground));
  const b = luminance(channels(background));
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/** A colour is neutral when its channels differ by at most a rounding step. */
export function isNeutral(colour: string): boolean {
  const [r, g, b, alpha] = channels(colour);
  return alpha === 0 || Math.max(r, g, b) - Math.min(r, g, b) <= 4;
}
