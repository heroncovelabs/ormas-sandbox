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
    check(['aggregation.tests.AggregateAnnotationPruningTests.test_referenced_window_requires_wrapping'])


def test_p2p_000():
    check(['aggregation.tests.AggregateAnnotationPruningTests.test_non_aggregate_annotation_pruned', 'aggregation.tests.AggregateAnnotationPruningTests.test_referenced_aggregate_annotation_kept', 'aggregation.tests.AggregateAnnotationPruningTests.test_referenced_group_by_annotation_kept', 'aggregation.tests.AggregateAnnotationPruningTests.test_referenced_subquery_requires_wrapping', 'aggregation.tests.AggregateAnnotationPruningTests.test_unreferenced_aggregate_annotation_pruned', 'aggregation.tests.AggregateAnnotationPruningTests.test_unused_aliased_aggregate_pruned', 'aggregation.tests.AggregateTestCase.test_add_implementation', 'aggregation.tests.AggregateTestCase.test_aggregate_alias', 'aggregation.tests.AggregateTestCase.test_aggregate_annotation', 'aggregation.tests.AggregateTestCase.test_aggregate_in_order_by', 'aggregation.tests.AggregateTestCase.test_aggregate_join_transform', 'aggregation.tests.AggregateTestCase.test_aggregate_multi_join', 'aggregation.tests.AggregateTestCase.test_aggregate_over_aggregate', 'aggregation.tests.AggregateTestCase.test_aggregate_over_complex_annotation', 'aggregation.tests.AggregateTestCase.test_aggregate_transform', 'aggregation.tests.AggregateTestCase.test_aggregation_default_after_annotation', 'aggregation.tests.AggregateTestCase.test_aggregation_default_compound_expression', 'aggregation.tests.AggregateTestCase.test_aggregation_default_expression', 'aggregation.tests.AggregateTestCase.test_aggregation_default_group_by', 'aggregation.tests.AggregateTestCase.test_aggregation_default_integer'])


def test_p2p_020():
    check(['aggregation.tests.AggregateTestCase.test_group_by_subquery_annotation', 'aggregation.tests.AggregateTestCase.test_grouped_annotation_in_group_by', 'aggregation.tests.AggregateTestCase.test_more_aggregation', 'aggregation.tests.AggregateTestCase.test_multi_arg_aggregate', 'aggregation.tests.AggregateTestCase.test_multiple_aggregate_references', 'aggregation.tests.AggregateTestCase.test_multiple_aggregates', 'aggregation.tests.AggregateTestCase.test_non_grouped_annotation_not_in_group_by', 'aggregation.tests.AggregateTestCase.test_nonaggregate_aggregation_throws', 'aggregation.tests.AggregateTestCase.test_nonfield_annotation', 'aggregation.tests.AggregateTestCase.test_order_of_precedence', 'aggregation.tests.AggregateTestCase.test_related_aggregate', 'aggregation.tests.AggregateTestCase.test_reverse_fkey_annotate', 'aggregation.tests.AggregateTestCase.test_single_aggregate', 'aggregation.tests.AggregateTestCase.test_sum_distinct_aggregate', 'aggregation.tests.AggregateTestCase.test_sum_duration_field', 'aggregation.tests.AggregateTestCase.test_ticket11881', 'aggregation.tests.AggregateTestCase.test_ticket12886', 'aggregation.tests.AggregateTestCase.test_ticket17424', 'aggregation.tests.AggregateTestCase.test_values_aggregation', 'aggregation.tests.AggregateTestCase.test_values_annotation_with_expression'])
