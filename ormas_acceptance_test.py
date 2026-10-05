"""Ormas external acceptance for vbcii4-legacy-quotacore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-quotacore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_burst_bank():
    _check('oss_tests.py::test_burst_bank')


def test_f2p_crossing_rate():
    _check('oss_tests.py::test_crossing_rate')


def test_f2p_growth_rate():
    _check('oss_tests.py::test_growth_rate')


def test_f2p_round_fifty():
    _check('oss_tests.py::test_round_fifty')


def test_f2p_tier_upgrade():
    _check('oss_tests.py::test_tier_upgrade')


def test_f2p_region_case():
    _check('oss_tests.py::test_region_case')


def test_f2p_zero_calls():
    _check('oss_tests.py::test_zero_calls')


def test_f2p_key_case():
    _check('oss_tests.py::test_key_case')


def test_f2p_trailing():
    _check('oss_tests.py::test_trailing')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_within_small():
    _check('reg_tests.py::test_within_small')


def test_p2p_deep_overage():
    _check('reg_tests.py::test_deep_overage')


def test_p2p_regions():
    _check('reg_tests.py::test_regions')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')
