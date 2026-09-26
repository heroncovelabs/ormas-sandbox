"""Ormas external acceptance for vbcii1-oss-sqlglot-pushdown-semantics.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-sqlglot-pushdown-semantics@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_gball_keys_survive():
    _check('oss_tests.py::test_group_by_all_keeps_its_implicit_grouping_keys')


def test_f2p_gball_rollup():
    _check('oss_tests.py::test_group_by_all_rollup_totals_unchanged')


def test_f2p_intersect_all():
    _check('oss_tests.py::test_intersect_all_operands_keep_their_columns')


def test_f2p_except_all():
    _check('oss_tests.py::test_except_all_operands_keep_their_columns')


def test_p2p_plain_pruning():
    _check('reg_tests.py::test_unused_columns_are_still_pruned_from_plain_subqueries')


def test_p2p_filtered_pruning():
    _check('reg_tests.py::test_unused_columns_pruned_when_outer_filters')


def test_p2p_intersect_distinct():
    _check('reg_tests.py::test_intersect_distinct_still_prunes_nothing_extra_is_kept')


def test_p2p_plain_aggregate():
    _check('reg_tests.py::test_plain_aggregate_roundtrip_unchanged')


def test_p2p_used_aggregation():
    _check('reg_tests.py::test_fully_used_aggregation_subquery_unchanged')


def test_p2p_explicit_gb_pruning():
    _check('reg_tests.py::test_explicit_group_by_still_allows_pruning_unused_projections')
