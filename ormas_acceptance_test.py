"""Ormas external acceptance for vbcii4-legacy-granarycore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-granarycore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_turn_keep():
    _check('oss_tests.py::test_turn_keep')


def test_f2p_transfer_seep():
    _check('oss_tests.py::test_transfer_seep')


def test_f2p_turn_wear():
    _check('oss_tests.py::test_turn_wear')


def test_f2p_fold_sag():
    _check('oss_tests.py::test_fold_sag')


def test_f2p_fold_reserve():
    _check('oss_tests.py::test_fold_reserve')


def test_f2p_turn_tie():
    _check('oss_tests.py::test_turn_tie')


def test_f2p_measure_toll():
    _check('oss_tests.py::test_measure_toll')


def test_f2p_favor():
    _check('oss_tests.py::test_favor')


def test_f2p_levy():
    _check('oss_tests.py::test_levy')


def test_f2p_resquare():
    _check('oss_tests.py::test_resquare')


def test_f2p_slot():
    _check('oss_tests.py::test_slot')


def test_f2p_true():
    _check('oss_tests.py::test_true')


def test_f2p_carry():
    _check('oss_tests.py::test_carry')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_paths():
    _check('reg_tests.py::test_paths')


def test_p2p_turn():
    _check('reg_tests.py::test_turn')


def test_p2p_reckon():
    _check('reg_tests.py::test_reckon')


def test_p2p_look():
    _check('reg_tests.py::test_look')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
