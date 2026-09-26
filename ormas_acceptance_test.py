"""Ormas external acceptance for vbcii1-oss-sqlglot-multi-table-ddl.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-sqlglot-multi-table-ddl@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_mysql_analyze_multi():
    _check('oss_tests.py::test_mysql_analyze_multiple_tables')


def test_f2p_mysql_analyze_local():
    _check('oss_tests.py::test_mysql_analyze_local_qualified_tables')


def test_f2p_postgres_analyze_multi():
    _check('oss_tests.py::test_postgres_analyze_multiple_tables')


def test_f2p_drop_view_multi():
    _check('oss_tests.py::test_drop_view_multiple')


def test_f2p_tsql_catalog_strip():
    _check('oss_tests.py::test_tsql_drop_view_strips_catalog')


def test_f2p_ast_uniform_list():
    _check('oss_tests.py::test_drop_multiple_tables_ast_lists_all')


def test_p2p_drop_table_multi():
    _check('reg_tests.py::test_drop_table_multiple_still_works')


def test_p2p_single_drop():
    _check('reg_tests.py::test_single_table_drop_forms')


def test_p2p_single_analyze():
    _check('reg_tests.py::test_single_table_analyze_forms')


def test_p2p_select_untouched():
    _check('reg_tests.py::test_plain_select_untouched')
