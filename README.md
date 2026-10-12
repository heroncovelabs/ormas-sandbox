Ormas TypeScript smoke (linux-node-test-v1). `node src/cli.ts "<text>"` prints a URL slug:
lower-case ASCII letters and digits joined by single hyphens, accents removed, no leading or trailing hyphen.
Acceptance: `node --test test/slugify.test.cjs`.
