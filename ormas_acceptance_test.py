"""Ormas external acceptance for vbcii1-legacy-brokercore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-brokercore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_portfolio_dilution():
    _check('oss_tests.py::test_portfolio_dilution')


def test_f2p_settlement_drop_adjust():
    _check('oss_tests.py::test_settlement_drop_adjust')


def test_f2p_second_drop_penalty():
    _check('oss_tests.py::test_second_drop_penalty')


def test_f2p_preferred_lane():
    _check('oss_tests.py::test_preferred_lane')


def test_f2p_soured_rebooking():
    _check('oss_tests.py::test_soured_rebooking')


def test_f2p_empty_settlement():
    _check('oss_tests.py::test_empty_settlement')


def test_f2p_late_joiner_haircut():
    _check('oss_tests.py::test_late_joiner_haircut')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_board_flows():
    _check('reg_tests.py::test_board_flows')


def test_p2p_settlement_checksum():
    _check('reg_tests.py::test_settlement_checksum')


def test_p2p_reject_lanes():
    _check('reg_tests.py::test_reject_lanes')


def test_p2p_empty_state():
    _check('reg_tests.py::test_empty_state')


def test_p2p_trailer_counts():
    _check('reg_tests.py::test_trailer_counts')
