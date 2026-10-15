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
    check(['backends.base.test_creation.TestDbCreationTests.test_migrate_test_setting_false_ensure_schema'])


def test_f2p_001():
    check(['migrations.test_executor.ExecutorTests.test_migrate_skips_schema_creation'])


def test_p2p_000():
    check(['backends.base.test_creation.TestMarkTests.test_mark_expected_failures_and_skips', 'backends.base.test_creation.TestDbSignatureTests.test_custom_test_name', 'backends.base.test_creation.TestDbSignatureTests.test_custom_test_name_with_test_prefix', 'backends.base.test_creation.TestDbSignatureTests.test_default_name', 'migrations.test_executor.ExecutorUnitTests.test_backwards_nothing_to_do', 'migrations.test_executor.ExecutorUnitTests.test_minimize_rollbacks', 'migrations.test_executor.ExecutorUnitTests.test_minimize_rollbacks_branchy', 'backends.base.test_creation.TestDbCreationTests.test_mark_expected_failures_and_skips_call', 'backends.base.test_creation.TestDbCreationTests.test_migrate_test_setting_false', 'backends.base.test_creation.TestDbCreationTests.test_migrate_test_setting_true', 'backends.base.test_creation.TestDeserializeDbFromString.test_circular_reference', 'backends.base.test_creation.TestDeserializeDbFromString.test_circular_reference_with_natural_key', 'backends.base.test_creation.TestDeserializeDbFromString.test_self_reference', 'backends.base.test_creation.TestDeserializeDbFromString.test_serialize_db_to_string_base_manager', 'migrations.test_executor.ExecutorTests.test_alter_id_type_with_fk', 'migrations.test_executor.ExecutorTests.test_apply_all_replaced_marks_replacement_as_applied', 'migrations.test_executor.ExecutorTests.test_atomic_operation_in_non_atomic_migration', 'migrations.test_executor.ExecutorTests.test_custom_user', 'migrations.test_executor.ExecutorTests.test_detect_soft_applied_add_field_manytomanyfield', 'migrations.test_executor.ExecutorTests.test_empty_plan'])


def test_p2p_020():
    check(['migrations.test_executor.ExecutorTests.test_migrate_backward_to_squashed_migration', 'migrations.test_executor.ExecutorTests.test_migrate_marks_replacement_applied_even_if_it_did_nothing', 'migrations.test_executor.ExecutorTests.test_migrate_marks_replacement_unapplied', 'migrations.test_executor.ExecutorTests.test_migrations_applied_and_recorded_atomically', 'migrations.test_executor.ExecutorTests.test_migrations_not_applied_on_deferred_sql_failure', 'migrations.test_executor.ExecutorTests.test_mixed_plan_not_supported', 'migrations.test_executor.ExecutorTests.test_non_atomic_migration', 'migrations.test_executor.ExecutorTests.test_process_callback', 'migrations.test_executor.ExecutorTests.test_run', 'migrations.test_executor.ExecutorTests.test_run_with_squashed', 'migrations.test_executor.ExecutorTests.test_soft_apply', 'migrations.test_executor.ExecutorTests.test_unrelated_applied_migrations_mutate_state', 'migrations.test_executor.ExecutorTests.test_unrelated_model_lookups_backwards', 'migrations.test_executor.ExecutorTests.test_unrelated_model_lookups_forwards'])
