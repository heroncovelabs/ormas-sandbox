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
    check(['expressions.tests.ValueTests.test_output_field_does_not_create_broken_validators'])


def test_f2p_001():
    check(['expressions.tests.ValueTests.test_raise_empty_expressionlist'])


def test_p2p_000():
    check(['expressions.tests.ExpressionWrapperTests.test_empty_group_by', 'expressions.tests.ExpressionWrapperTests.test_non_empty_group_by', 'expressions.tests.CombinableTests.test_and', 'expressions.tests.CombinableTests.test_negation', 'expressions.tests.CombinableTests.test_or', 'expressions.tests.CombinableTests.test_reversed_and', 'expressions.tests.CombinableTests.test_reversed_or', 'expressions.tests.FTests.test_deconstruct', 'expressions.tests.FTests.test_deepcopy', 'expressions.tests.FTests.test_equal', 'expressions.tests.FTests.test_hash', 'expressions.tests.FTests.test_not_equal_Value', 'expressions.tests.OrderByTests.test_equal', 'expressions.tests.OrderByTests.test_hash', 'expressions.tests.ReprTests.test_aggregates', 'expressions.tests.ReprTests.test_distinct_aggregates', 'expressions.tests.ReprTests.test_expressions', 'expressions.tests.ReprTests.test_filtered_aggregates', 'expressions.tests.ReprTests.test_functions', 'expressions.tests.CombinedExpressionTests.test_resolve_output_field'])


def test_p2p_020():
    check(['expressions.tests.FTimeDeltaTests.test_date_subtraction', 'expressions.tests.FTimeDeltaTests.test_datetime_subquery_subtraction', 'expressions.tests.FTimeDeltaTests.test_datetime_subtraction', 'expressions.tests.FTimeDeltaTests.test_datetime_subtraction_microseconds', 'expressions.tests.FTimeDeltaTests.test_delta_add', 'expressions.tests.FTimeDeltaTests.test_delta_subtract', 'expressions.tests.FTimeDeltaTests.test_delta_update', 'expressions.tests.FTimeDeltaTests.test_duration_expressions', 'expressions.tests.FTimeDeltaTests.test_duration_with_datetime', 'expressions.tests.FTimeDeltaTests.test_duration_with_datetime_microseconds', 'expressions.tests.FTimeDeltaTests.test_durationfield_add', 'expressions.tests.FTimeDeltaTests.test_durationfield_multiply_divide', 'expressions.tests.FTimeDeltaTests.test_exclude', 'expressions.tests.FTimeDeltaTests.test_invalid_operator', 'expressions.tests.FTimeDeltaTests.test_mixed_comparisons2', 'expressions.tests.FTimeDeltaTests.test_multiple_query_compilation', 'expressions.tests.FTimeDeltaTests.test_negative_timedelta_update', 'expressions.tests.FTimeDeltaTests.test_query_clone', 'expressions.tests.FTimeDeltaTests.test_time_subquery_subtraction', 'expressions.tests.FTimeDeltaTests.test_time_subtraction'])
