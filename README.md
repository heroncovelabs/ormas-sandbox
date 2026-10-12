Ormas Node fixture (linux-node-test-v1). `node src/clamp.cjs <value> <min> <max>` prints the value clamped to [min, max],
or `invalid` with exit code 2 when any argument is not a number. Acceptance: `node --test test/clamp.test.cjs`.
