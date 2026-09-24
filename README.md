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
python -m pytest -q tests/acceptance_greet.py
```

After the accepted first result is reviewed and merged into this pilot branch,
the repeat task implements `farewell` in the same module: return `Goodbye, Ormas.`,
trim names, and return `Goodbye.` for an empty name. It must preserve the first
task's behavior. Its check is:

```sh
python -m pytest -q tests/acceptance_greet.py tests/acceptance_farewell.py
```

Only `sandbox/greet.py` is writable by either task. Tests, the dependency lock,
and all other files remain immutable. `requirements.lock` is the qualified
hash-pinned Python/pytest dependency set. The client passes these ordinary test
commands to Ormas preparation and submits the returned packet unchanged.

These named checks use the declared `linux-python-pytest-v1` command-output
interface. Ormas supplies `ormas_acceptance.run` in the separate test driver;
candidate code runs in another container and the assertions inspect its output.
The checks require that environment, rather than a local installation of pytest
alone. They demonstrate this supported acceptance interface only.

The original `tests/test_greet.py` and `tests/test_farewell.py` remain ordinary
unit-test regressions. The unmodified first command was refused by the installed
preparer at seed `cd3e9363bcb866256df33f4f71096c8b273c32e1`: the external driver
does not import candidate modules, so collection failed before any assertion.
That refusal is preserved. The pilot does not establish that arbitrary existing
unit suites are accepted as the independent payable check.

The seed does not authorize a client job, provider expense, account access,
production admission, or a change to this repository's default branch.
