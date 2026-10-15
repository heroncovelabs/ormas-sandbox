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
    check(['bulk_create.tests.BulkCreateTests.test_update_conflicts_unique_fields_update_fields_db_column'])


def test_p2p_000():
    check(['bulk_create.tests.BulkCreateTests.test_batch_same_vals', 'bulk_create.tests.BulkCreateTests.test_bulk_insert_expressions', 'bulk_create.tests.BulkCreateTests.test_bulk_insert_nullable_fields', 'bulk_create.tests.BulkCreateTests.test_efficiency', 'bulk_create.tests.BulkCreateTests.test_empty_model', 'bulk_create.tests.BulkCreateTests.test_explicit_batch_size', 'bulk_create.tests.BulkCreateTests.test_explicit_batch_size_efficiency', 'bulk_create.tests.BulkCreateTests.test_explicit_batch_size_respects_max_batch_size', 'bulk_create.tests.BulkCreateTests.test_ignore_conflicts_ignore', 'bulk_create.tests.BulkCreateTests.test_ignore_update_conflicts_exclusive', 'bulk_create.tests.BulkCreateTests.test_invalid_batch_size_exception', 'bulk_create.tests.BulkCreateTests.test_large_batch', 'bulk_create.tests.BulkCreateTests.test_large_batch_efficiency', 'bulk_create.tests.BulkCreateTests.test_large_batch_mixed', 'bulk_create.tests.BulkCreateTests.test_large_batch_mixed_efficiency', 'bulk_create.tests.BulkCreateTests.test_large_single_field_batch', 'bulk_create.tests.BulkCreateTests.test_long_and_short_text', 'bulk_create.tests.BulkCreateTests.test_long_non_ascii_text', 'bulk_create.tests.BulkCreateTests.test_multi_table_inheritance_unsupported', 'bulk_create.tests.BulkCreateTests.test_non_auto_increment_pk'])


def test_p2p_020():
    check(['bulk_create.tests.BulkCreateTests.test_non_auto_increment_pk_efficiency', 'bulk_create.tests.BulkCreateTests.test_proxy_inheritance_supported', 'bulk_create.tests.BulkCreateTests.test_set_pk_and_insert_single_item', 'bulk_create.tests.BulkCreateTests.test_set_pk_and_query_efficiency', 'bulk_create.tests.BulkCreateTests.test_set_state', 'bulk_create.tests.BulkCreateTests.test_set_state_with_pk_specified', 'bulk_create.tests.BulkCreateTests.test_simple', 'bulk_create.tests.BulkCreateTests.test_unsaved_parent', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_invalid_unique_fields', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_invalid_update_fields', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_no_update_fields', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_nonexistent_update_fields', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_pk_in_update_fields', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_two_fields_unique_fields_both', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_two_fields_unique_fields_first', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_two_fields_unique_fields_second', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_unique_fields', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_unique_fields_pk', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_unique_fields_required', 'bulk_create.tests.BulkCreateTests.test_update_conflicts_unique_two_fields_unique_fields_both'])


def test_p2p_040():
    check(['bulk_create.tests.BulkCreateTests.test_update_conflicts_unique_two_fields_unique_fields_one'])
