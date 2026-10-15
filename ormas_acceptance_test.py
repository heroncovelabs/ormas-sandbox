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
    check(['annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_in_subquery'])


def test_f2p_001():
    check(['annotations.tests.NonAggregateAnnotationTestCase.test_annotation_and_alias_filter_related_in_subquery'])


def test_p2p_000():
    check(['annotations.tests.AliasTests.test_aggregate_alias', 'annotations.tests.AliasTests.test_alias_after_annotation', 'annotations.tests.AliasTests.test_alias_annotate_with_aggregation', 'annotations.tests.AliasTests.test_alias_annotation_expression', 'annotations.tests.AliasTests.test_alias_default_alias_expression', 'annotations.tests.AliasTests.test_alias_sql_injection', 'annotations.tests.AliasTests.test_basic_alias', 'annotations.tests.AliasTests.test_basic_alias_annotation', 'annotations.tests.AliasTests.test_basic_alias_f_annotation', 'annotations.tests.AliasTests.test_basic_alias_f_transform_annotation', 'annotations.tests.AliasTests.test_dates_alias', 'annotations.tests.AliasTests.test_datetimes_alias', 'annotations.tests.AliasTests.test_defer_only_alias', 'annotations.tests.AliasTests.test_filter_alias_agg_with_double_f', 'annotations.tests.AliasTests.test_filter_alias_with_double_f', 'annotations.tests.AliasTests.test_filter_alias_with_f', 'annotations.tests.AliasTests.test_joined_alias_annotation', 'annotations.tests.AliasTests.test_order_by_alias', 'annotations.tests.AliasTests.test_order_by_alias_aggregate', 'annotations.tests.AliasTests.test_overwrite_alias_with_annotation'])


def test_p2p_020():
    check(['annotations.tests.NonAggregateAnnotationTestCase.test_filter_annotation_with_double_f', 'annotations.tests.NonAggregateAnnotationTestCase.test_filter_annotation_with_f', 'annotations.tests.NonAggregateAnnotationTestCase.test_filter_decimal_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_filter_wrong_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_full_expression_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_full_expression_annotation_with_aggregation', 'annotations.tests.NonAggregateAnnotationTestCase.test_grouping_by_q_expression_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_joined_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_joined_transformed_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_mixed_type_annotation_date_interval', 'annotations.tests.NonAggregateAnnotationTestCase.test_mixed_type_annotation_numbers', 'annotations.tests.NonAggregateAnnotationTestCase.test_mti_annotations', 'annotations.tests.NonAggregateAnnotationTestCase.test_null_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_order_by_aggregate', 'annotations.tests.NonAggregateAnnotationTestCase.test_order_by_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_q_expression_annotation_with_aggregation', 'annotations.tests.NonAggregateAnnotationTestCase.test_raw_sql_with_inherited_field', 'annotations.tests.NonAggregateAnnotationTestCase.test_update_with_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_values_annotation', 'annotations.tests.NonAggregateAnnotationTestCase.test_values_with_pk_annotation'])
