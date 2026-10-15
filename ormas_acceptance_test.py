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
    check(['schema.tests.SchemaTests.test_add_field_o2o_nullable'])


def test_p2p_000():
    check(['schema.tests.SchemaTests.test_add_datefield_and_datetimefield_use_effective_default', 'schema.tests.SchemaTests.test_add_field', 'schema.tests.SchemaTests.test_add_field_binary', 'schema.tests.SchemaTests.test_add_field_db_collation', 'schema.tests.SchemaTests.test_add_field_default_dropped', 'schema.tests.SchemaTests.test_add_field_default_nullable', 'schema.tests.SchemaTests.test_add_field_default_transform', 'schema.tests.SchemaTests.test_add_field_durationfield_with_default', 'schema.tests.SchemaTests.test_add_field_remove_field', 'schema.tests.SchemaTests.test_add_field_temp_default', 'schema.tests.SchemaTests.test_add_field_temp_default_boolean', 'schema.tests.SchemaTests.test_add_field_use_effective_default', 'schema.tests.SchemaTests.test_add_foreign_key_long_names', 'schema.tests.SchemaTests.test_add_foreign_key_quoted_db_table', 'schema.tests.SchemaTests.test_add_foreign_object', 'schema.tests.SchemaTests.test_add_remove_index', 'schema.tests.SchemaTests.test_add_textfield_default_nullable', 'schema.tests.SchemaTests.test_add_textfield_unhashable_default', 'schema.tests.SchemaTests.test_alter', 'schema.tests.SchemaTests.test_rename'])


def test_p2p_020():
    check(['schema.tests.SchemaTests.test_alter_auto_field_quoted_db_column', 'schema.tests.SchemaTests.test_primary_key', 'schema.tests.SchemaTests.test_referenced_field_without_constraint_rename_inside_atomic_block', 'schema.tests.SchemaTests.test_referenced_table_without_constraint_rename_inside_atomic_block', 'schema.tests.SchemaTests.test_remove_constraints_capital_letters', 'schema.tests.SchemaTests.test_remove_db_index_doesnt_remove_custom_indexes', 'schema.tests.SchemaTests.test_remove_field_check_does_not_remove_meta_constraints', 'schema.tests.SchemaTests.test_remove_field_unique_does_not_remove_meta_constraints', 'schema.tests.SchemaTests.test_remove_index_together_does_not_remove_meta_indexes', 'schema.tests.SchemaTests.test_remove_unique_together_does_not_remove_meta_constraints', 'schema.tests.SchemaTests.test_rename_keep_null_status', 'schema.tests.SchemaTests.test_rename_referenced_field', 'schema.tests.SchemaTests.test_rename_table_renames_deferred_sql_references', 'schema.tests.SchemaTests.test_text_field_with_db_index', 'schema.tests.SchemaTests.test_text_field_with_db_index_to_fk', 'schema.tests.SchemaTests.test_unique', 'schema.tests.SchemaTests.test_unique_constraint', 'schema.tests.SchemaTests.test_unique_constraint_field_and_expression', 'schema.tests.SchemaTests.test_unique_name_quoting', 'schema.tests.SchemaTests.test_unique_together'])


def test_p2p_040():
    check(['schema.tests.SchemaTests.test_unique_together_with_fk', 'schema.tests.SchemaTests.test_unique_together_with_fk_with_existing_index'])
