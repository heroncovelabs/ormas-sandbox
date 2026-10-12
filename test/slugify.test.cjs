'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {run} = require('ormas_acceptance');

const slug = async (text) => {
  const r = await run(['node', '--no-warnings', 'src/cli.ts', text]);
  assert.equal(r.returncode, 0);
  return r.output.trim();
};

test('lower-cases and hyphenates words', async () => {
  assert.equal(await slug('Hello, World!'), 'hello-world');
});
test('collapses whitespace and trims hyphens', async () => {
  assert.equal(await slug('  Ormas   Outcomes  '), 'ormas-outcomes');
});
test('removes accents', async () => {
  assert.equal(await slug('Café Crème'), 'cafe-creme');
});
