"""Ormas external acceptance for vbcii4-legacy-freightcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-freightcore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_x_fuel_band():
    _check('oss_tests.py::test_x_fuel_band')


def test_f2p_low_class_floor():
    _check('oss_tests.py::test_low_class_floor')


def test_f2p_dim_divisor():
    _check('oss_tests.py::test_dim_divisor')


def test_f2p_dim_rounding():
    _check('oss_tests.py::test_dim_rounding')


def test_f2p_svc_order():
    _check('oss_tests.py::test_svc_order')


def test_f2p_remote_zone():
    _check('oss_tests.py::test_remote_zone')


def test_f2p_zero_weight():
    _check('oss_tests.py::test_zero_weight')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_nominal_shipments():
    _check('reg_tests.py::test_nominal_shipments')


def test_p2p_reject_codes():
    _check('reg_tests.py::test_reject_codes')


def test_p2p_empty_batch_trailer():
    _check('reg_tests.py::test_empty_batch_trailer')


def test_p2p_multi_shipment_batch():
    _check('reg_tests.py::test_multi_shipment_batch')
