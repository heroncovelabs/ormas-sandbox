"""Ormas external acceptance for vbcii4-legacy-cellarcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-cellarcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_mull():
    _check('oss_tests.py::test_mull')


def test_f2p_creel():
    _check('oss_tests.py::test_creel')


def test_f2p_haul():
    _check('oss_tests.py::test_haul')


def test_f2p_grain():
    _check('oss_tests.py::test_grain')


def test_f2p_stale():
    _check('oss_tests.py::test_stale')


def test_f2p_pip():
    _check('oss_tests.py::test_pip')


def test_f2p_quell():
    _check('oss_tests.py::test_quell')


def test_f2p_swale():
    _check('oss_tests.py::test_swale')


def test_f2p_brand():
    _check('oss_tests.py::test_brand')


def test_f2p_keel():
    _check('oss_tests.py::test_keel')


def test_f2p_wake():
    _check('oss_tests.py::test_wake')


def test_f2p_hale():
    _check('oss_tests.py::test_hale')


def test_f2p_revenant():
    _check('oss_tests.py::test_revenant')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_basic():
    _check('reg_tests.py::test_basic')


def test_p2p_flow():
    _check('reg_tests.py::test_flow')


def test_p2p_turn():
    _check('reg_tests.py::test_turn')


def test_p2p_grade():
    _check('reg_tests.py::test_grade')


def test_p2p_survey():
    _check('reg_tests.py::test_survey')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
