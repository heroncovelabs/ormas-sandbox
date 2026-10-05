"""Ormas external acceptance for vbcii4-legacy-matchcore-order-book-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-matchcore-order-book-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_priority_class():
    _check('oss_tests.py::test_priority_class')


def test_f2p_self_trade_prevention():
    _check('oss_tests.py::test_self_trade_prevention')


def test_f2p_cancel_replace():
    _check('oss_tests.py::test_cancel_replace')


def test_f2p_cancel_ack_quantity():
    _check('oss_tests.py::test_cancel_ack_quantity')


def test_f2p_volatility_band():
    _check('oss_tests.py::test_volatility_band')


def test_f2p_tick_regime():
    _check('oss_tests.py::test_tick_regime')


def test_f2p_book_hash():
    _check('oss_tests.py::test_book_hash')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_full_session_parity():
    _check('oss_tests.py::test_full_session_parity')


def test_p2p_basic_matching():
    _check('reg_tests.py::test_basic_matching')


def test_p2p_time_priority():
    _check('reg_tests.py::test_time_priority')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')


def test_p2p_cancel_unfilled():
    _check('reg_tests.py::test_cancel_unfilled')
