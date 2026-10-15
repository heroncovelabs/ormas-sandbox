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
    check(['migrations.test_operations.OperationTests.test_rename_model_with_db_table_noop'])


def test_p2p_000():
    check(['migrations.test_operations.TestCreateModel.test_references_model_mixin', 'migrations.test_operations.FieldOperationTests.test_reference_field_by_through_fields', 'migrations.test_operations.FieldOperationTests.test_references_field_by_from_fields', 'migrations.test_operations.FieldOperationTests.test_references_field_by_name', 'migrations.test_operations.FieldOperationTests.test_references_field_by_remote_field_model', 'migrations.test_operations.FieldOperationTests.test_references_field_by_through', 'migrations.test_operations.FieldOperationTests.test_references_field_by_to_fields', 'migrations.test_operations.FieldOperationTests.test_references_model', 'migrations.test_operations.OperationTests.test_add_field', 'migrations.test_operations.SwappableOperationTests.test_add_field_ignore_swapped', 'migrations.test_operations.SwappableOperationTests.test_create_ignore_swapped', 'migrations.test_operations.SwappableOperationTests.test_delete_ignore_swapped', 'migrations.test_operations.SwappableOperationTests.test_indexes_ignore_swapped', 'migrations.test_operations.OperationTests.test_add_binaryfield', 'migrations.test_operations.OperationTests.test_add_charfield', 'migrations.test_operations.OperationTests.test_add_textfield', 'migrations.test_operations.OperationTests.test_add_constraint', 'migrations.test_operations.OperationTests.test_add_constraint_combinable', 'migrations.test_operations.OperationTests.test_add_constraint_percent_escaping', 'migrations.test_operations.OperationTests.test_add_covering_unique_constraint'])


def test_p2p_020():
    check(['migrations.test_operations.OperationTests.test_add_deferred_unique_constraint', 'migrations.test_operations.OperationTests.test_add_field_m2m', 'migrations.test_operations.OperationTests.test_rename_model_state_forwards', 'migrations.test_operations.OperationTests.test_rename_model_with_m2m', 'migrations.test_operations.OperationTests.test_rename_model_with_self_referential_fk', 'migrations.test_operations.OperationTests.test_rename_model_with_self_referential_m2m', 'migrations.test_operations.OperationTests.test_rename_model_with_superclass_fk', 'migrations.test_operations.OperationTests.test_rename_referenced_field_state_forward', 'migrations.test_operations.OperationTests.test_repoint_field_m2m', 'migrations.test_operations.OperationTests.test_run_python', 'migrations.test_operations.OperationTests.test_run_python_atomic', 'migrations.test_operations.OperationTests.test_run_python_noop', 'migrations.test_operations.OperationTests.test_run_python_related_assignment', 'migrations.test_operations.OperationTests.test_run_sql', 'migrations.test_operations.OperationTests.test_run_sql_add_missing_semicolon_on_collect_sql', 'migrations.test_operations.OperationTests.test_run_sql_noop', 'migrations.test_operations.OperationTests.test_run_sql_params', 'migrations.test_operations.OperationTests.test_run_sql_params_invalid', 'migrations.test_operations.OperationTests.test_separate_database_and_state', 'migrations.test_operations.OperationTests.test_separate_database_and_state2'])


def test_p2p_040():
    check(['migrations.test_operations.OperationTests.test_smallfield_autofield_foreignfield_growth', 'migrations.test_operations.OperationTests.test_smallfield_bigautofield_foreignfield_growth'])
