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
    check(['apps.tests.AppsTests.test_clear_cache'])


def test_p2p_000():
    check(['apps.tests.AppConfigTests.test_app_default_auto_field', 'apps.tests.AppConfigTests.test_default_auto_field_setting', 'apps.tests.AppConfigTests.test_dunder_path', 'apps.tests.AppConfigTests.test_duplicate_dunder_path_no_dunder_file', 'apps.tests.AppConfigTests.test_empty_dunder_path_fallback_to_dunder_file', 'apps.tests.AppConfigTests.test_empty_dunder_path_no_dunder_file', 'apps.tests.AppConfigTests.test_explicit_path_overrides', 'apps.tests.AppConfigTests.test_invalid_label', 'apps.tests.AppConfigTests.test_multiple_dunder_path_fallback_to_dunder_file', 'apps.tests.AppConfigTests.test_multiple_dunder_path_no_dunder_file', 'apps.tests.AppConfigTests.test_no_dunder_path_fallback_to_dunder_file', 'apps.tests.AppConfigTests.test_no_dunder_path_or_dunder_file', 'apps.tests.AppConfigTests.test_path_set_explicitly', 'apps.tests.AppConfigTests.test_repr', 'apps.tests.NamespacePackageAppTests.test_multiple_paths', 'apps.tests.NamespacePackageAppTests.test_multiple_paths_explicit_path', 'apps.tests.NamespacePackageAppTests.test_single_path', 'apps.tests.AppsTests.test_bad_app_config', 'apps.tests.AppsTests.test_duplicate_labels', 'apps.tests.AppsTests.test_duplicate_names'])


def test_p2p_020():
    check(['apps.tests.AppsTests.test_get_containing_app_config_apps_not_ready', 'apps.tests.AppsTests.test_get_model', 'apps.tests.AppsTests.test_import_exception_is_not_masked', 'apps.tests.AppsTests.test_is_installed', 'apps.tests.AppsTests.test_lazy_model_operation', 'apps.tests.AppsTests.test_model_clash', 'apps.tests.AppsTests.test_models_not_loaded', 'apps.tests.AppsTests.test_models_py', 'apps.tests.AppsTests.test_no_config_app', 'apps.tests.AppsTests.test_no_such_app', 'apps.tests.AppsTests.test_no_such_app_config', 'apps.tests.AppsTests.test_no_such_app_config_with_choices', 'apps.tests.AppsTests.test_not_an_app_config', 'apps.tests.AppsTests.test_one_config_app', 'apps.tests.AppsTests.test_ready', 'apps.tests.AppsTests.test_relabeling', 'apps.tests.AppsTests.test_singleton_main', 'apps.tests.AppsTests.test_two_configs_app', 'apps.tests.AppsTests.test_two_configs_one_default_app', 'apps.tests.AppsTests.test_two_default_configs_app'])
