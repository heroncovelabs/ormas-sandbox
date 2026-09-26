"""Ormas external acceptance for vbv1-py-reactive-sheet.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-reactive-sheet@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
with pytest inside the isolated candidate container, and asserts it passed.

A check that ran and failed is an assertion failure. A check that could not
run (collection/import/usage error, no tests collected, timeout) raises
RuntimeError instead, so the verifier reports a setup problem rather than a
behavioral failure.
"""
import re

from ormas_acceptance import run

PYTEST = ['python3', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--tb=short']
_ERRORS = re.compile(r"\b\d+ errors?\b")


def _check(selector):
    result = run(PYTEST + [selector], timeout_s=60)
    output = result["output"]
    lines = [line for line in output.splitlines() if line.strip()]
    summary = lines[-1] if lines else ""
    if result["returncode"] not in (0, 1) or _ERRORS.search(summary):
        raise RuntimeError(
            "candidate check did not complete (exit %s): %s"
            % (result["returncode"], output[-4000:])
        )
    assert result["returncode"] == 0, output[-4000:]


def test_f2p_basic_formula():
    _check('test_reactive.py::test_basic_formula')


def test_f2p_transitive_update():
    _check('test_reactive.py::test_transitive_update')


def test_f2p_topological_order():
    _check('test_reactive.py::test_topological_order_diamond')


def test_f2p_formula_rebind():
    _check('test_reactive.py::test_formula_rebind_clears_old_deps')


def test_f2p_cycle_detection():
    _check('test_reactive.py::test_cycle_detection')


def test_f2p_get_unknown():
    _check('test_reactive.py::test_get_unknown_raises')


def test_p2p_construct():
    _check('test_reactive.py::test_construct')
