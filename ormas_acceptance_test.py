"""Ormas external acceptance for vbcii4-legacy-schedcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-schedcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_retry_tie():
    _check('oss_tests.py::test_retry_tie')


def test_f2p_double_penalty():
    _check('oss_tests.py::test_double_penalty')


def test_f2p_fanin_boost():
    _check('oss_tests.py::test_fanin_boost')


def test_f2p_stale_dep():
    _check('oss_tests.py::test_stale_dep')


def test_f2p_dup_deps():
    _check('oss_tests.py::test_dup_deps')


def test_f2p_job_case():
    _check('oss_tests.py::test_job_case')


def test_f2p_trailing():
    _check('oss_tests.py::test_trailing')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_order():
    _check('reg_tests.py::test_order')


def test_p2p_blocked():
    _check('reg_tests.py::test_blocked')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
