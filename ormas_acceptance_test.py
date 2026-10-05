"""Ormas external acceptance for vbcii4-legacy-paddockcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-paddockcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_stir():
    _check('oss_tests.py::test_stir')


def test_f2p_square():
    _check('oss_tests.py::test_square')


def test_f2p_leadbook():
    _check('oss_tests.py::test_leadbook')


def test_f2p_haul():
    _check('oss_tests.py::test_haul')


def test_f2p_restpick():
    _check('oss_tests.py::test_restpick')


def test_f2p_wake():
    _check('oss_tests.py::test_wake')


def test_f2p_muster():
    _check('oss_tests.py::test_muster')


def test_f2p_true():
    _check('oss_tests.py::test_true')


def test_f2p_slot():
    _check('oss_tests.py::test_slot')


def test_f2p_seat():
    _check('oss_tests.py::test_seat')


def test_f2p_book():
    _check('oss_tests.py::test_book')


def test_f2p_home():
    _check('oss_tests.py::test_home')


def test_f2p_levy():
    _check('oss_tests.py::test_levy')


def test_f2p_gate():
    _check('oss_tests.py::test_gate')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_paths():
    _check('reg_tests.py::test_paths')


def test_p2p_shift():
    _check('reg_tests.py::test_shift')


def test_p2p_muster_guard():
    _check('reg_tests.py::test_muster')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
