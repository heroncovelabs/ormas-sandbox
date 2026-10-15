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
    check(['migrations.test_commands.MakeMigrationsTests.test_makemigrations_check'])


def test_p2p_000():
    check(['migrations.test_commands.AppLabelErrorTests.test_makemigrations_app_name_specified_as_label', 'migrations.test_commands.AppLabelErrorTests.test_makemigrations_nonexistent_app_label', 'migrations.test_commands.AppLabelErrorTests.test_migrate_app_name_specified_as_label', 'migrations.test_commands.AppLabelErrorTests.test_migrate_nonexistent_app_label', 'migrations.test_commands.AppLabelErrorTests.test_optimizemigration_app_name_specified_as_label', 'migrations.test_commands.AppLabelErrorTests.test_optimizemigration_nonexistent_app_label', 'migrations.test_commands.AppLabelErrorTests.test_showmigrations_app_name_specified_as_label', 'migrations.test_commands.AppLabelErrorTests.test_showmigrations_nonexistent_app_label', 'migrations.test_commands.AppLabelErrorTests.test_sqlmigrate_app_name_specified_as_label', 'migrations.test_commands.AppLabelErrorTests.test_sqlmigrate_nonexistent_app_label', 'migrations.test_commands.AppLabelErrorTests.test_squashmigrations_app_name_specified_as_label', 'migrations.test_commands.AppLabelErrorTests.test_squashmigrations_nonexistent_app_label', 'migrations.test_commands.OptimizeMigrationTests.test_ambigious_prefix', 'migrations.test_commands.OptimizeMigrationTests.test_app_without_migrations', 'migrations.test_commands.OptimizeMigrationTests.test_creates_replace_migration_manual_porting', 'migrations.test_commands.OptimizeMigrationTests.test_fails_squash_migration_manual_porting', 'migrations.test_commands.OptimizeMigrationTests.test_no_optimization_possible', 'migrations.test_commands.OptimizeMigrationTests.test_optimization', 'migrations.test_commands.OptimizeMigrationTests.test_optimization_no_verbosity', 'migrations.test_commands.OptimizeMigrationTests.test_optimizemigration_check'])


def test_p2p_020():
    check(['migrations.test_commands.MakeMigrationsTests.test_makemigrations_no_common_ancestor', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_no_init', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_non_interactive_auto_now_add_addition', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_non_interactive_not_null_addition', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_non_interactive_not_null_alteration', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_non_interactive_no_field_rename', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_non_interactive_no_model_rename', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_non_interactive_unique_callable_default_addition', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_order', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_scriptable', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_scriptable_merge', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_unspecified_app_with_conflict_merge', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_unspecified_app_with_conflict_no_merge', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update_applied_migration', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update_dependency_migration', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update_existing_name', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update_manual_porting', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update_no_migration', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_update_squash_migration'])


def test_p2p_040():
    check(['migrations.test_commands.MakeMigrationsTests.test_makemigrations_with_custom_name', 'migrations.test_commands.MakeMigrationsTests.test_makemigrations_with_invalid_custom_name'])
