"""Ormas adapted public benchmark acceptance; generated, immutable."""
from ormas_acceptance import run

ARGV = ['env', 'PYTHONPATH=.', 'python3', 'tests/runtests.py', '--parallel', '1']
DJANGO = True

def check(selectors):
    result = run(ARGV + selectors, timeout_s=60)
    code, output = result['returncode'], result['output']
    if code not in (0, 1):
        raise RuntimeError('candidate setup/collection/timeout: ' + output[-3000:])
    if code and (('Ran ' not in output if DJANGO else ' failed' not in output)
                 or 'ERROR collecting' in output or 'Failed to import test module' in output):
        raise RuntimeError('candidate did not execute behavioral tests: ' + output[-3000:])
    assert code == 0, output[-6000:]


def test_f2p_000():
    check(['expressions.tests.ExistsTests.test_negated_empty_exists'])


def test_p2p_000():
    check(['expressions.tests.OrderByTests.test_equal', 'expressions.tests.OrderByTests.test_hash', 'expressions.tests.ReprTests.test_aggregates', 'expressions.tests.ReprTests.test_distinct_aggregates', 'expressions.tests.ReprTests.test_expressions', 'expressions.tests.ReprTests.test_filtered_aggregates', 'expressions.tests.ReprTests.test_functions', 'expressions.tests.CombinedExpressionTests.test_resolve_output_field', 'expressions.tests.FTests.test_deconstruct', 'expressions.tests.FTests.test_deepcopy', 'expressions.tests.FTests.test_equal', 'expressions.tests.FTests.test_hash', 'expressions.tests.FTests.test_not_equal_Value', 'expressions.tests.CombinableTests.test_and', 'expressions.tests.CombinableTests.test_negation', 'expressions.tests.CombinableTests.test_or', 'expressions.tests.CombinableTests.test_reversed_and', 'expressions.tests.CombinableTests.test_reversed_or', 'expressions.tests.ExpressionWrapperTests.test_empty_group_by', 'expressions.tests.ExpressionWrapperTests.test_non_empty_group_by'])


def test_p2p_020():
    check(['expressions.tests.BasicExpressionsTests.test_pickle_expression', 'expressions.tests.BasicExpressionsTests.test_subquery', 'expressions.tests.BasicExpressionsTests.test_subquery_eq', 'expressions.tests.BasicExpressionsTests.test_subquery_filter_by_aggregate', 'expressions.tests.BasicExpressionsTests.test_subquery_filter_by_lazy', 'expressions.tests.BasicExpressionsTests.test_subquery_group_by_outerref_in_filter', 'expressions.tests.BasicExpressionsTests.test_subquery_in_filter', 'expressions.tests.BasicExpressionsTests.test_subquery_references_joined_table_twice', 'expressions.tests.BasicExpressionsTests.test_subquery_sql', 'expressions.tests.BasicExpressionsTests.test_ticket_11722_iexact_lookup', 'expressions.tests.BasicExpressionsTests.test_ticket_16731_startswith_lookup', 'expressions.tests.BasicExpressionsTests.test_ticket_18375_chained_filters', 'expressions.tests.BasicExpressionsTests.test_ticket_18375_join_reuse', 'expressions.tests.BasicExpressionsTests.test_ticket_18375_kwarg_ordering', 'expressions.tests.BasicExpressionsTests.test_ticket_18375_kwarg_ordering_2', 'expressions.tests.BasicExpressionsTests.test_update', 'expressions.tests.BasicExpressionsTests.test_update_inherited_field_value', 'expressions.tests.BasicExpressionsTests.test_update_with_fk', 'expressions.tests.BasicExpressionsTests.test_update_with_none', 'expressions.tests.BasicExpressionsTests.test_uuid_pk_subquery'])
