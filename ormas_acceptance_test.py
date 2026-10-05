"""Ormas external acceptance for vbcii4-legacy-blendcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-blendcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_book_vs_physical():
    _check('oss_tests.py::test_book_vs_physical')


def test_f2p_writeoff():
    _check('oss_tests.py::test_writeoff')


def test_f2p_white_bulk():
    _check('oss_tests.py::test_white_bulk')


def test_f2p_near_dry_partial():
    _check('oss_tests.py::test_near_dry_partial')


def test_f2p_overfill_cap():
    _check('oss_tests.py::test_overfill_cap')


def test_f2p_case_fold():
    _check('oss_tests.py::test_case_fold')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_reconcile_feedback():
    _check('oss_tests.py::test_reconcile_feedback')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_fill_flows():
    _check('reg_tests.py::test_fill_flows')


def test_p2p_reconcile_identity():
    _check('reg_tests.py::test_reconcile_identity')


def test_p2p_reject_lanes():
    _check('reg_tests.py::test_reject_lanes')


def test_p2p_empty_state():
    _check('reg_tests.py::test_empty_state')


def test_p2p_trailer_counts():
    _check('reg_tests.py::test_trailer_counts')
