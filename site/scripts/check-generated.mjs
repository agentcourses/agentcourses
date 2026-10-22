import { expected, drift, argumentsFor, fail, report } from './generate.mjs';
try {
  const options = argumentsFor(process.argv.slice(2), ['--spec-only']);
  const differences = drift(options.root, expected(options.root), options['spec-only']);
  if (differences.length) fail('generated-drift', `Generated output differs: ${differences.join(', ')}`);
  console.log('Generated output matches canonical source bytes.');
} catch (error) { report(error); }
