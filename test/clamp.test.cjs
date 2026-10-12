'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {run} = require('ormas_acceptance');

const clamp = (...args) => run(['node', 'src/clamp.cjs', ...args]);

test('clamps a value above the range', async () => {
  const r = await clamp('5', '0', '3');
  assert.equal(r.returncode, 0);
  assert.equal(r.output.trim(), '3');
});
test('clamps a value below the range', async () => {
  const r = await clamp('-4', '0', '3');
  assert.equal(r.returncode, 0);
  assert.equal(r.output.trim(), '0');
});
test('keeps a value inside the range', async () => {
  const r = await clamp('2', '0', '3');
  assert.equal(r.returncode, 0);
  assert.equal(r.output.trim(), '2');
});
test('rejects a non-number', async () => {
  const r = await clamp('x', '0', '3');
  assert.equal(r.returncode, 2);
  assert.equal(r.output.trim(), 'invalid');
});
