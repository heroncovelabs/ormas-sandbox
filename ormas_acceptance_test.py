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
    check(['migrations.test_optimizer.OptimizerTests.test_add_remove_index'])


def test_p2p_000():
    check(['migrations.test_optimizer.OptimizerTests.test_add_field_alter_field', 'migrations.test_optimizer.OptimizerTests.test_add_field_delete_field', 'migrations.test_optimizer.OptimizerTests.test_add_field_rename_field', 'migrations.test_optimizer.OptimizerTests.test_alter_alter_field', 'migrations.test_optimizer.OptimizerTests.test_alter_alter_index_model', 'migrations.test_optimizer.OptimizerTests.test_alter_alter_owrt_model', 'migrations.test_optimizer.OptimizerTests.test_alter_alter_table_model', 'migrations.test_optimizer.OptimizerTests.test_alter_alter_unique_model', 'migrations.test_optimizer.OptimizerTests.test_alter_field_delete_field', 'migrations.test_optimizer.OptimizerTests.test_alter_field_rename_field', 'migrations.test_optimizer.OptimizerTests.test_create_alter_index_delete_model', 'migrations.test_optimizer.OptimizerTests.test_create_alter_index_field', 'migrations.test_optimizer.OptimizerTests.test_create_alter_model_managers', 'migrations.test_optimizer.OptimizerTests.test_create_alter_model_options', 'migrations.test_optimizer.OptimizerTests.test_create_alter_owrt_delete_model', 'migrations.test_optimizer.OptimizerTests.test_create_alter_owrt_field', 'migrations.test_optimizer.OptimizerTests.test_create_alter_unique_delete_model', 'migrations.test_optimizer.OptimizerTests.test_create_alter_unique_field', 'migrations.test_optimizer.OptimizerTests.test_create_delete_model', 'migrations.test_optimizer.OptimizerTests.test_create_model_add_field'])


def test_p2p_020():
    check(['migrations.test_optimizer.OptimizerTests.test_create_model_add_field_not_through_m2m_through', 'migrations.test_optimizer.OptimizerTests.test_create_model_alter_field', 'migrations.test_optimizer.OptimizerTests.test_create_model_and_remove_model_options', 'migrations.test_optimizer.OptimizerTests.test_create_model_no_reordering_for_unrelated_fk', 'migrations.test_optimizer.OptimizerTests.test_create_model_no_reordering_of_inherited_model', 'migrations.test_optimizer.OptimizerTests.test_create_model_remove_field', 'migrations.test_optimizer.OptimizerTests.test_create_model_rename_field', 'migrations.test_optimizer.OptimizerTests.test_create_model_reordering', 'migrations.test_optimizer.OptimizerTests.test_create_model_reordering_circular_fk', 'migrations.test_optimizer.OptimizerTests.test_create_rename_model', 'migrations.test_optimizer.OptimizerTests.test_none_app_label', 'migrations.test_optimizer.OptimizerTests.test_optimize_elidable_operation', 'migrations.test_optimizer.OptimizerTests.test_optimize_through_create', 'migrations.test_optimizer.OptimizerTests.test_optimize_through_fields', 'migrations.test_optimizer.OptimizerTests.test_rename_index', 'migrations.test_optimizer.OptimizerTests.test_rename_model_self', 'migrations.test_optimizer.OptimizerTests.test_single', 'migrations.test_optimizer.OptimizerTests.test_swapping_fields_names'])
