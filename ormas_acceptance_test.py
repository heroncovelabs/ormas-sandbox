"""Ormas external acceptance for vbcii1-legacy-diffcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-diffcore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_delta_chains():
    _check('oss_tests.py::test_delta_chains')


def test_f2p_shrink_grow():
    _check('oss_tests.py::test_shrink_grow')


def test_f2p_full_cadence():
    _check('oss_tests.py::test_full_cadence')


def test_f2p_same_value_sets():
    _check('oss_tests.py::test_same_value_sets')


def test_f2p_store_after_restore():
    _check('oss_tests.py::test_store_after_restore')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_basic_flows():
    _check('reg_tests.py::test_basic_flows')


def test_p2p_snapshot_restore_flows():
    _check('reg_tests.py::test_snapshot_restore_flows')


def test_p2p_reject_lanes():
    _check('reg_tests.py::test_reject_lanes')


def test_p2p_empty_state():
    _check('reg_tests.py::test_empty_state')


def test_p2p_trailer_counts():
    _check('reg_tests.py::test_trailer_counts')
