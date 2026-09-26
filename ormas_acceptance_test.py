"""Ormas external acceptance for vbcii1-legacy-costcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-costcore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_display_stock():
    _check('oss_tests.py::test_display_stock')


def test_f2p_cost_merge():
    _check('oss_tests.py::test_cost_merge')


def test_f2p_shrinkage():
    _check('oss_tests.py::test_shrinkage')


def test_f2p_cost_cap():
    _check('oss_tests.py::test_cost_cap')


def test_f2p_partial_fill():
    _check('oss_tests.py::test_partial_fill')


def test_f2p_case_fold():
    _check('oss_tests.py::test_case_fold')


def test_f2p_zero_qty():
    _check('oss_tests.py::test_zero_qty')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_single_layer():
    _check('reg_tests.py::test_single_layer')


def test_p2p_fifo_two_layer():
    _check('reg_tests.py::test_fifo_two_layer')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')


def test_p2p_empty_batch():
    _check('reg_tests.py::test_empty_batch')


def test_p2p_trailer_mix():
    _check('reg_tests.py::test_trailer_mix')
