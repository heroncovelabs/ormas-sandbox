"""Ormas external acceptance for vbcii1-legacy-tollcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-tollcore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_weekend_freight_bypass():
    _check('oss_tests.py::test_weekend_freight_bypass')


def test_f2p_morning_stagger():
    _check('oss_tests.py::test_morning_stagger')


def test_f2p_sidecar_reclass():
    _check('oss_tests.py::test_sidecar_reclass')


def test_f2p_bus_peak_multiplier():
    _check('oss_tests.py::test_bus_peak_multiplier')


def test_f2p_rounding_mode():
    _check('oss_tests.py::test_rounding_mode')


def test_f2p_dow_zero_alias():
    _check('oss_tests.py::test_dow_zero_alias')


def test_f2p_time_2400_alias():
    _check('oss_tests.py::test_time_2400_alias')


def test_f2p_evening_stagger():
    _check('oss_tests.py::test_evening_stagger')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_nominal_passages():
    _check('reg_tests.py::test_nominal_passages')


def test_p2p_error_codes():
    _check('reg_tests.py::test_error_codes')


def test_p2p_empty_batch_trailer():
    _check('reg_tests.py::test_empty_batch_trailer')


def test_p2p_multi_record_batch():
    _check('reg_tests.py::test_multi_record_batch')
