'use strict';
const count = Number(process.argv[2] || '0');
if (count > 0) {
  process.stdout.write('<span class="badge">' + count + ' new</span>\n');
}
