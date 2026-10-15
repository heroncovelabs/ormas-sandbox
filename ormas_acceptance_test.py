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
    check(['queries.test_bulk_update.BulkUpdateTests.test_f_expression'])


def test_p2p_000():
    check(['queries.test_bulk_update.BulkUpdateNoteTests.test_batch_size', 'queries.test_bulk_update.BulkUpdateNoteTests.test_foreign_keys_do_not_lookup', 'queries.test_bulk_update.BulkUpdateNoteTests.test_functions', 'queries.test_bulk_update.BulkUpdateNoteTests.test_multiple_fields', 'queries.test_bulk_update.BulkUpdateNoteTests.test_set_field_to_null', 'queries.test_bulk_update.BulkUpdateNoteTests.test_set_mixed_fields_to_null', 'queries.test_bulk_update.BulkUpdateNoteTests.test_simple', 'queries.test_bulk_update.BulkUpdateNoteTests.test_unsaved_models', 'queries.test_bulk_update.BulkUpdateTests.test_booleanfield', 'queries.test_bulk_update.BulkUpdateTests.test_custom_db_columns', 'queries.test_bulk_update.BulkUpdateTests.test_custom_pk', 'queries.test_bulk_update.BulkUpdateTests.test_datetime_field', 'queries.test_bulk_update.BulkUpdateTests.test_empty_objects', 'queries.test_bulk_update.BulkUpdateTests.test_falsey_pk_value', 'queries.test_bulk_update.BulkUpdateTests.test_field_references', 'queries.test_bulk_update.BulkUpdateTests.test_inherited_fields', 'queries.test_bulk_update.BulkUpdateTests.test_invalid_batch_size', 'queries.test_bulk_update.BulkUpdateTests.test_ipaddressfield', 'queries.test_bulk_update.BulkUpdateTests.test_json_field', 'queries.test_bulk_update.BulkUpdateTests.test_large_batch'])


def test_p2p_020():
    check(['queries.test_bulk_update.BulkUpdateTests.test_no_fields', 'queries.test_bulk_update.BulkUpdateTests.test_nonexistent_field', 'queries.test_bulk_update.BulkUpdateTests.test_nullable_fk_after_related_save', 'queries.test_bulk_update.BulkUpdateTests.test_only_concrete_fields_allowed', 'queries.test_bulk_update.BulkUpdateTests.test_unsaved_parent', 'queries.test_bulk_update.BulkUpdateTests.test_unspecified_unsaved_parent', 'queries.test_bulk_update.BulkUpdateTests.test_update_custom_primary_key', 'queries.test_bulk_update.BulkUpdateTests.test_update_primary_key', 'queries.test_bulk_update.BulkUpdateTests.test_updated_rows_when_passing_duplicates'])
