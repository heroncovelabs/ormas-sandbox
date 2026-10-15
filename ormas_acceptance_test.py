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
    check(['expressions_case.tests.CaseExpressionTests.test_annotate_with_full_when'])


def test_p2p_000():
    check(['expressions_case.tests.CaseWhenTests.test_empty_q_object', 'expressions_case.tests.CaseWhenTests.test_invalid_when_constructor_args', 'expressions_case.tests.CaseWhenTests.test_only_when_arguments', 'expressions_case.tests.CaseDocumentationExamples.test_conditional_aggregation_example', 'expressions_case.tests.CaseDocumentationExamples.test_conditional_update_example', 'expressions_case.tests.CaseDocumentationExamples.test_filter_example', 'expressions_case.tests.CaseDocumentationExamples.test_hash', 'expressions_case.tests.CaseDocumentationExamples.test_lookup_example', 'expressions_case.tests.CaseDocumentationExamples.test_simple_example', 'expressions_case.tests.CaseExpressionTests.test_aggregate', 'expressions_case.tests.CaseExpressionTests.test_aggregate_with_expression_as_condition', 'expressions_case.tests.CaseExpressionTests.test_aggregate_with_expression_as_value', 'expressions_case.tests.CaseExpressionTests.test_aggregation_empty_cases', 'expressions_case.tests.CaseExpressionTests.test_annotate', 'expressions_case.tests.CaseExpressionTests.test_annotate_exclude', 'expressions_case.tests.CaseExpressionTests.test_annotate_filter_decimal', 'expressions_case.tests.CaseExpressionTests.test_annotate_values_not_in_order_by', 'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_condition', 'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_predicate', 'expressions_case.tests.CaseExpressionTests.test_annotate_with_aggregation_in_value'])


def test_p2p_020():
    check(['expressions_case.tests.CaseExpressionTests.test_update_fk', 'expressions_case.tests.CaseExpressionTests.test_update_float', 'expressions_case.tests.CaseExpressionTests.test_update_generic_ip_address', 'expressions_case.tests.CaseExpressionTests.test_update_image', 'expressions_case.tests.CaseExpressionTests.test_update_null_boolean', 'expressions_case.tests.CaseExpressionTests.test_update_positive_big_integer', 'expressions_case.tests.CaseExpressionTests.test_update_positive_integer', 'expressions_case.tests.CaseExpressionTests.test_update_positive_small_integer', 'expressions_case.tests.CaseExpressionTests.test_update_slug', 'expressions_case.tests.CaseExpressionTests.test_update_small_integer', 'expressions_case.tests.CaseExpressionTests.test_update_string', 'expressions_case.tests.CaseExpressionTests.test_update_text', 'expressions_case.tests.CaseExpressionTests.test_update_time', 'expressions_case.tests.CaseExpressionTests.test_update_url', 'expressions_case.tests.CaseExpressionTests.test_update_uuid', 'expressions_case.tests.CaseExpressionTests.test_update_with_expression_as_condition', 'expressions_case.tests.CaseExpressionTests.test_update_with_expression_as_value', 'expressions_case.tests.CaseExpressionTests.test_update_with_join_in_condition_raise_field_error', 'expressions_case.tests.CaseExpressionTests.test_update_with_join_in_predicate_raise_field_error', 'expressions_case.tests.CaseExpressionTests.test_update_without_default'])
