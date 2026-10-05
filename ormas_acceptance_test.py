"""Ormas external acceptance for vbcii4-legacy-depotcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-depotcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_lift():
    _check('oss_tests.py::test_lift')


def test_f2p_notch():
    _check('oss_tests.py::test_notch')


def test_f2p_wear_drag():
    _check('oss_tests.py::test_wear_drag')


def test_f2p_short_round():
    _check('oss_tests.py::test_short_round')


def test_f2p_shelve_blocks():
    _check('oss_tests.py::test_shelve_blocks')


def test_f2p_ledge_return():
    _check('oss_tests.py::test_ledge_return')


def test_f2p_sag():
    _check('oss_tests.py::test_sag')


def test_f2p_distrust():
    _check('oss_tests.py::test_distrust')


def test_f2p_held_grouping():
    _check('oss_tests.py::test_held_grouping')


def test_f2p_square_rebuild():
    _check('oss_tests.py::test_square_rebuild')


def test_f2p_square_wear():
    _check('oss_tests.py::test_square_wear')


def test_f2p_square_chain():
    _check('oss_tests.py::test_square_chain')


def test_f2p_square_resurrect():
    _check('oss_tests.py::test_square_resurrect')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_flow():
    _check('reg_tests.py::test_flow')


def test_p2p_square():
    _check('reg_tests.py::test_square')


def test_p2p_void():
    _check('reg_tests.py::test_void')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
