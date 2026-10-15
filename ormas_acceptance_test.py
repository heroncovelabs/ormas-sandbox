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
    check(['migrations.test_autodetector.AutodetectorTests.test_create_with_through_model_separate_apps'])


def test_p2p_000():
    check(['migrations.test_autodetector.MigrationSuggestNameTests.test_auto', 'migrations.test_autodetector.MigrationSuggestNameTests.test_many_operations_suffix', 'migrations.test_autodetector.MigrationSuggestNameTests.test_no_operations', 'migrations.test_autodetector.MigrationSuggestNameTests.test_no_operations_initial', 'migrations.test_autodetector.MigrationSuggestNameTests.test_none_name', 'migrations.test_autodetector.MigrationSuggestNameTests.test_none_name_with_initial_true', 'migrations.test_autodetector.MigrationSuggestNameTests.test_operation_with_no_suggested_name', 'migrations.test_autodetector.MigrationSuggestNameTests.test_single_operation', 'migrations.test_autodetector.MigrationSuggestNameTests.test_single_operation_long_name', 'migrations.test_autodetector.MigrationSuggestNameTests.test_two_create_models', 'migrations.test_autodetector.MigrationSuggestNameTests.test_two_create_models_with_initial_true', 'migrations.test_autodetector.MigrationSuggestNameTests.test_two_operations', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_add_field_and_index_together', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_add_index_together', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_add_model_order_with_respect_to_index_together', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_alter_field_and_index_together', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_create_model_and_index_together', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_empty_index_together', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_index_together_no_changes', 'migrations.test_autodetector.AutodetectorIndexTogetherTests.test_index_together_ordering'])


def test_p2p_020():
    check(['migrations.test_autodetector.AutodetectorTests.test_same_app_circular_fk_dependency', 'migrations.test_autodetector.AutodetectorTests.test_same_app_circular_fk_dependency_with_unique_together_and_indexes', 'migrations.test_autodetector.AutodetectorTests.test_same_app_no_fk_dependency', 'migrations.test_autodetector.AutodetectorTests.test_set_alter_order_with_respect_to', 'migrations.test_autodetector.AutodetectorTests.test_set_alter_order_with_respect_to_index_constraint_unique_together', 'migrations.test_autodetector.AutodetectorTests.test_supports_functools_partial', 'migrations.test_autodetector.AutodetectorTests.test_swappable', 'migrations.test_autodetector.AutodetectorTests.test_swappable_changed', 'migrations.test_autodetector.AutodetectorTests.test_swappable_circular_multi_mti', 'migrations.test_autodetector.AutodetectorTests.test_swappable_first_inheritance', 'migrations.test_autodetector.AutodetectorTests.test_swappable_first_setting', 'migrations.test_autodetector.AutodetectorTests.test_swappable_lowercase', 'migrations.test_autodetector.AutodetectorTests.test_swappable_many_to_many_model_case', 'migrations.test_autodetector.AutodetectorTests.test_trim_apps', 'migrations.test_autodetector.AutodetectorTests.test_unique_together_no_changes', 'migrations.test_autodetector.AutodetectorTests.test_unique_together_ordering', 'migrations.test_autodetector.AutodetectorTests.test_unique_together_remove_fk', 'migrations.test_autodetector.AutodetectorTests.test_unmanaged_create', 'migrations.test_autodetector.AutodetectorTests.test_unmanaged_custom_pk', 'migrations.test_autodetector.AutodetectorTests.test_unmanaged_delete'])


def test_p2p_040():
    check(['migrations.test_autodetector.AutodetectorTests.test_unmanaged_to_managed'])
