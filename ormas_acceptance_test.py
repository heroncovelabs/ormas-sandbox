"""Ormas external acceptance for vbcii4-legacy-lodgecore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-lodgecore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_late_lag():
    _check('oss_tests.py::test_late_lag')


def test_f2p_return_momentum():
    _check('oss_tests.py::test_return_momentum')


def test_f2p_early_chain():
    _check('oss_tests.py::test_early_chain')


def test_f2p_rota_tax():
    _check('oss_tests.py::test_rota_tax')


def test_f2p_rota_reverse():
    _check('oss_tests.py::test_rota_reverse')


def test_f2p_settle_forgive():
    _check('oss_tests.py::test_settle_forgive')


def test_f2p_settle_order():
    _check('oss_tests.py::test_settle_order')


def test_f2p_settle_pointer():
    _check('oss_tests.py::test_settle_pointer')


def test_f2p_porch():
    _check('oss_tests.py::test_porch')


def test_f2p_doubling():
    _check('oss_tests.py::test_doubling')


def test_f2p_aired_tieflip():
    _check('oss_tests.py::test_aired_tieflip')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_basic():
    _check('reg_tests.py::test_basic')


def test_p2p_flow():
    _check('reg_tests.py::test_flow')


def test_p2p_rota():
    _check('reg_tests.py::test_rota')


def test_p2p_settle():
    _check('reg_tests.py::test_settle')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
