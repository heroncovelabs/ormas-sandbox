Ormas browser fixture (linux-node-browser-v1). `node src/badge.cjs <count>` prints an HTML badge
`<span class="badge"><count> new</span>`, or nothing when the count is 0.
Acceptance: `node node_modules/@playwright/test/cli.js test test/badge.spec.cjs`.
