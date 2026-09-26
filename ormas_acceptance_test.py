"""Ormas external acceptance for vbcii1-legacy-tariffcore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/legacy-tariffcore-binary-parity@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_duty_rounding():
    _check('oss_tests.py::test_duty_rounding')


def test_f2p_weight_ceiling():
    _check('oss_tests.py::test_weight_ceiling')


def test_f2p_dense_air_band():
    _check('oss_tests.py::test_dense_air_band')


def test_f2p_origin_levy():
    _check('oss_tests.py::test_origin_levy')


def test_f2p_audit_mode():
    _check('oss_tests.py::test_audit_mode')


def test_f2p_jpy_sea_waiver():
    _check('oss_tests.py::test_jpy_sea_waiver')


def test_f2p_cap_scope():
    _check('oss_tests.py::test_cap_scope')


def test_f2p_chapter98():
    _check('oss_tests.py::test_chapter98')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_rate_bands():
    _check('reg_tests.py::test_rate_bands')


def test_p2p_rejects():
    _check('reg_tests.py::test_rejects')


def test_p2p_weight_exact():
    _check('reg_tests.py::test_weight_exact')


def test_p2p_trailer():
    _check('reg_tests.py::test_trailer')
