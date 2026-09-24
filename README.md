# ormas-sandbox

Public sandbox for Ormas acceptance-path rehearsals (Loop A, 2026-09-13): a cross-tenant miner
claims a seeded task here, the reference validator re-verifies it, settlement waits on the quorum.
Nothing in this repository is a product. Result branches `ormas/job/<id>` are expected litter.

## September 24 public-client pilot

Branch `public-pilot/20260924` is an isolated trial seed. Its tests intentionally
fail behavioral assertions. This is a delivery and billing rehearsal, not a
model-quality or commercial-performance benchmark.

The first task fixes `greet` in `sandbox/greet.py`: return `Hello, Ormas.` for
`Ormas`, and trim surrounding whitespace from names. Its check is:

```sh
python -m pytest -q tests/test_greet.py
```

After the accepted first result is reviewed and merged into this pilot branch,
the repeat task implements `farewell` in the same module: return `Goodbye, Ormas.`,
trim names, and return `Goodbye.` for an empty name. It must preserve the first
task's behavior. Its check is:

```sh
python -m pytest -q tests/test_greet.py tests/test_farewell.py
```

Only `sandbox/greet.py` is writable by either task. Tests, the dependency lock,
and all other files remain immutable. `requirements.lock` is the qualified
hash-pinned Python/pytest dependency set. The client passes these ordinary test
commands to Ormas preparation and submits the returned packet unchanged.

The seed does not authorize a client job, provider expense, account access,
production admission, or a change to this repository's default branch.
