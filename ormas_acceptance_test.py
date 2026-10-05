"""Ormas external acceptance for vbcii4-legacy-codeccore-binary-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-codeccore-binary-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_memo_squeeze():
    _check('oss_tests.py::test_memo_squeeze')


def test_f2p_january_audit_flag():
    _check('oss_tests.py::test_january_audit_flag')


def test_f2p_prefix_case_leniency():
    _check('oss_tests.py::test_prefix_case_leniency')


def test_f2p_acct_padding_leniency():
    _check('oss_tests.py::test_acct_padding_leniency')


def test_f2p_null_date_decode():
    _check('oss_tests.py::test_null_date_decode')


def test_f2p_comma_memo_padding():
    _check('oss_tests.py::test_comma_memo_padding')


def test_f2p_check_override():
    _check('oss_tests.py::test_check_override')


def test_f2p_lenient_tokens():
    _check('oss_tests.py::test_lenient_tokens')


def test_f2p_round_trips():
    _check('oss_tests.py::test_round_trips')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_nominal_round_trips():
    _check('reg_tests.py::test_nominal_round_trips')


def test_p2p_reject_lanes():
    _check('reg_tests.py::test_reject_lanes')


def test_p2p_empty_batch_trailer():
    _check('reg_tests.py::test_empty_batch_trailer')


def test_p2p_empty_memo_handling():
    _check('reg_tests.py::test_empty_memo_handling')


def test_p2p_trailer_counts():
    _check('reg_tests.py::test_trailer_counts')
