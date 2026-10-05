"""Ormas external acceptance for vbcii4-legacy-payrollcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-payrollcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_household_surtax():
    _check('oss_tests.py::test_household_surtax')


def test_f2p_levy_cap_crossing():
    _check('oss_tests.py::test_levy_cap_crossing')


def test_f2p_married_relief_order():
    _check('oss_tests.py::test_married_relief_order')


def test_f2p_state_sd():
    _check('oss_tests.py::test_state_sd')


def test_f2p_flag_recapture():
    _check('oss_tests.py::test_flag_recapture')


def test_f2p_bonus_period():
    _check('oss_tests.py::test_bonus_period')


def test_f2p_zero_gross():
    _check('oss_tests.py::test_zero_gross')


def test_f2p_id_case_fold():
    _check('oss_tests.py::test_id_case_fold')


def test_f2p_rounding_regime():
    _check('oss_tests.py::test_rounding_regime')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_brackets():
    _check('reg_tests.py::test_brackets')


def test_p2p_states_and_status():
    _check('reg_tests.py::test_states_and_status')


def test_p2p_levy_under_cap():
    _check('reg_tests.py::test_levy_under_cap')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
