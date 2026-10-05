"""Ormas external acceptance for vbcii4-legacy-queuecore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-queuecore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_requeue_penalty():
    _check('oss_tests.py::test_requeue_penalty')


def test_f2p_tie_aging():
    _check('oss_tests.py::test_tie_aging')


def test_f2p_sentinel():
    _check('oss_tests.py::test_sentinel')


def test_f2p_cap999():
    _check('oss_tests.py::test_cap999')


def test_f2p_undo_two_deep():
    _check('oss_tests.py::test_undo_two_deep')


def test_f2p_item_case():
    _check('oss_tests.py::test_item_case')


def test_f2p_trailing():
    _check('oss_tests.py::test_trailing')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_order():
    _check('reg_tests.py::test_order')


def test_p2p_drain():
    _check('reg_tests.py::test_drain')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
