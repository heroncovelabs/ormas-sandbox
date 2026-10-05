"""Ormas external acceptance for vbcii4-legacy-qlite-store-parity.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v4/legacy-qlite-store-parity@b44558e3617c75dabe30e21907502f48e00d6906)
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


def test_f2p_slot_reuse_ordering():
    _check('oss_tests.py::test_slot_reuse_ordering')


def test_f2p_find_case_rule():
    _check('oss_tests.py::test_find_case_rule')


def test_f2p_wildcard_semantics():
    _check('oss_tests.py::test_wildcard_semantics')


def test_f2p_range_bounds():
    _check('oss_tests.py::test_range_bounds')


def test_f2p_duplicate_insert_update():
    _check('oss_tests.py::test_duplicate_insert_update')


def test_f2p_name_truncation():
    _check('oss_tests.py::test_name_truncation')


def test_f2p_avg_truncation():
    _check('oss_tests.py::test_avg_truncation')


def test_f2p_sum_wrap():
    _check('oss_tests.py::test_sum_wrap')


def test_f2p_full_corpus_parity():
    _check('oss_tests.py::test_full_corpus_parity')


def test_p2p_crud():
    _check('reg_tests.py::test_crud')


def test_p2p_find_exact_case():
    _check('reg_tests.py::test_find_exact_case')


def test_p2p_range_interior():
    _check('reg_tests.py::test_range_interior')


def test_p2p_fmt_errors():
    _check('reg_tests.py::test_fmt_errors')
