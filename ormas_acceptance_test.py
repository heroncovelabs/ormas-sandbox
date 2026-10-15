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
    check(['admin_scripts.tests.ManageRunserver.test_zero_ip_addr'])


def test_p2p_000():
    check(['admin_scripts.tests.ExecuteFromCommandLine.test_program_name_from_argv', 'admin_scripts.tests.ManageTestserver.test_params_to_runserver', 'admin_scripts.tests.ManageTestserver.test_testserver_handle_params', 'admin_scripts.tests.ManageRunserverMigrationWarning.test_migration_warning_multiple_apps', 'admin_scripts.tests.ManageRunserverMigrationWarning.test_migration_warning_one_app', 'admin_scripts.tests.ManageRunserver.test_no_database', 'admin_scripts.tests.ManageRunserver.test_readonly_database', 'admin_scripts.tests.ManageRunserver.test_runner_addrport_ipv6', 'admin_scripts.tests.ManageRunserver.test_runner_ambiguous', 'admin_scripts.tests.ManageRunserver.test_runner_custom_defaults', 'admin_scripts.tests.ManageRunserver.test_runner_custom_defaults_ipv6', 'admin_scripts.tests.ManageRunserver.test_runner_hostname', 'admin_scripts.tests.ManageRunserver.test_runner_hostname_ipv6', 'admin_scripts.tests.ManageRunserver.test_runserver_addrport', 'admin_scripts.tests.ManageRunserver.test_skip_checks', 'admin_scripts.tests.Discovery.test_precedence', 'admin_scripts.tests.MainModule.test_program_name_in_help', 'admin_scripts.tests.ManageRunserverHelpOutput.test_suppressed_options', 'admin_scripts.tests.ManageManuallyConfiguredSettings.test_non_existent_command_output', 'admin_scripts.tests.ManageRunserverEmptyAllowedHosts.test_empty_allowed_hosts_error'])


def test_p2p_020():
    check(['admin_scripts.tests.CommandTypes.test_version_alternative', 'admin_scripts.tests.StartProject.test_custom_project_destination_missing', 'admin_scripts.tests.StartProject.test_custom_project_template', 'admin_scripts.tests.StartProject.test_custom_project_template_from_tarball_by_path', 'admin_scripts.tests.StartProject.test_custom_project_template_from_tarball_by_url', 'admin_scripts.tests.StartProject.test_custom_project_template_context_variables', 'admin_scripts.tests.StartProject.test_custom_project_template_exclude_directory', 'admin_scripts.tests.StartProject.test_custom_project_template_from_tarball_by_url_django_user_agent', 'admin_scripts.tests.StartProject.test_custom_project_template_from_tarball_to_alternative_location', 'admin_scripts.tests.StartProject.test_custom_project_template_hidden_directory_default_excluded', 'admin_scripts.tests.StartProject.test_custom_project_template_hidden_directory_included', 'admin_scripts.tests.StartProject.test_custom_project_template_with_non_ascii_templates', 'admin_scripts.tests.StartProject.test_file_without_extension', 'admin_scripts.tests.StartProject.test_honor_umask', 'admin_scripts.tests.StartProject.test_importable_project_name', 'admin_scripts.tests.StartProject.test_invalid_project_name', 'admin_scripts.tests.StartProject.test_no_escaping_of_project_variables', 'admin_scripts.tests.StartProject.test_project_template_tarball_url', 'admin_scripts.tests.StartProject.test_simple_project', 'admin_scripts.tests.StartProject.test_simple_project_different_directory'])


def test_p2p_040():
    check(['admin_scripts.tests.StartProject.test_template_dir_with_trailing_slash', 'admin_scripts.tests.StartProject.test_wrong_args'])
