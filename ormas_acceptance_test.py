"""Ormas external acceptance for vbcii4-legacy-hedgecore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-hedgecore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_reval_cent():
    _check('oss_tests.py::test_reval_cent')


def test_f2p_washout():
    _check('oss_tests.py::test_washout')


def test_f2p_jpy_fixing():
    _check('oss_tests.py::test_jpy_fixing')


def test_f2p_flat_drop():
    _check('oss_tests.py::test_flat_drop')


def test_f2p_amount_zero():
    _check('oss_tests.py::test_amount_zero')


def test_f2p_book_case():
    _check('oss_tests.py::test_book_case')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_live_flows():
    _check('reg_tests.py::test_live_flows')


def test_p2p_revaluations():
    _check('reg_tests.py::test_revaluations')


def test_p2p_reject_lanes():
    _check('reg_tests.py::test_reject_lanes')


def test_p2p_trailer_counts():
    _check('reg_tests.py::test_trailer_counts')
