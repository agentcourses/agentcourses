export type ReadingSource = {
  candidate: string;
  author: { label: string; href: string }[];
  runner: { label: string; href: string }[];
  exchange: { speaker: 'tutor' | 'learner'; text: string }[];
  licence: { label: string; href: string };
};

/** Validate the source boundary before rendering any reading path. */
export function readingPaths(source: ReadingSource): ReadingSource {
  const text = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0;
  const link = (value: unknown): boolean => {
    if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || /[\\\s]/.test(value)) return false;
    try {
      const decoded = decodeURIComponent(value);
      return !/[\\\s]/.test(decoded) && !decoded.startsWith('//') &&
        !decoded.split(/[/?#]/).some((part) => part === '.' || part === '..') &&
        new URL(value, 'https://agentcourses.invalid').origin === 'https://agentcourses.invalid';
    } catch { return false; }
  };
  const task = (item: { label: string; href: string }) => item && text(item.label) && link(item.href);
  if (!source || !text(source.candidate) ||
    !Array.isArray(source.author) || source.author.length === 0 || !source.author.every(task) ||
    !Array.isArray(source.runner) || source.runner.length === 0 || !source.runner.every(task) ||
    !Array.isArray(source.exchange) || source.exchange.length === 0 ||
    !source.exchange.every((line) => line && ['tutor', 'learner'].includes(line.speaker) && text(line.text)) ||
    !task(source.licence)) throw new Error('Invalid reading source: candidate, reader tasks, teaching exchange and contained site links are required');
  return source;
}

export const sampleReadingSource: ReadingSource = readingPaths({
  candidate: 'Design candidate',
  author: [
    { label: 'Write a small course', href: '/authors/quickstart/' },
    { label: 'Check author requirements', href: '/specification/#sample-section-one' },
  ],
  runner: [
    { label: 'Add course support', href: '/implementers/support/' },
    { label: 'Check runner duties', href: '/specification/#sample-section-two' },
  ],
  exchange: [
    { speaker: 'tutor', text: 'What should your project help someone do?' },
    { speaker: 'learner', text: 'Make a clear first contribution.' },
    { speaker: 'tutor', text: 'Choose the first change. Then explain why it helps.' },
  ],
  licence: { label: 'Apache-2.0', href: '/specification/#licence' },
});
