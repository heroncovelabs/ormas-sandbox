"""Ormas external acceptance for vbcii1-oss-sqlglot-json-operator-precedence.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-sqlglot-json-operator-precedence@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_cast_binds_operand():
    _check('oss_tests.py::test_cast_binds_to_the_operand_not_the_extraction')


def test_f2p_arith_binds_tighter():
    _check('oss_tests.py::test_arithmetic_binds_tighter_than_json_operators')


def test_f2p_subscript_binds_operand():
    _check('oss_tests.py::test_subscript_binds_to_the_operand')


def test_f2p_duckdb_shares_tier():
    _check('oss_tests.py::test_duckdb_shares_the_precedence_tier')


def test_p2p_left_assoc():
    _check('reg_tests.py::test_json_operators_stay_left_associative')


def test_p2p_lambda_dialects():
    _check('reg_tests.py::test_lambda_dialects_keep_arrow_as_lambda')


def test_p2p_ordinary_precedence():
    _check('reg_tests.py::test_ordinary_precedence_unchanged')


def test_p2p_paren_roundtrip():
    _check('reg_tests.py::test_parenthesized_reading_survives_roundtrip')


def test_p2p_question_roundtrip():
    _check('reg_tests.py::test_question_operator_roundtrips')


def test_p2p_transpile():
    _check('reg_tests.py::test_postgres_to_duckdb_transpile_unchanged')
