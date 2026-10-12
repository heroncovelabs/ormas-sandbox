'use strict';
const isNumber = require('is-number');

// Clamp value into the inclusive range [min, max].
function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

const [value, min, max] = process.argv.slice(2);
if (![value, min, max].every((arg) => isNumber(arg))) {
  console.log('invalid');
  process.exit(2);
}
console.log(String(clamp(Number(value), Number(min), Number(max))));
