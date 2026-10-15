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
    check(['utils_tests.test_autoreload.TestChildArguments.test_xoptions'])


def test_p2p_000():
    check(['utils_tests.test_autoreload.TestCommonRoots.test_common_roots', 'utils_tests.test_autoreload.TestRaiseLastException.test_no_exception', 'utils_tests.test_autoreload.TestRaiseLastException.test_raises_custom_exception', 'utils_tests.test_autoreload.TestRaiseLastException.test_raises_exception', 'utils_tests.test_autoreload.TestRaiseLastException.test_raises_exception_with_context', 'utils_tests.test_autoreload.GetReloaderTests.test_watchman_available', 'utils_tests.test_autoreload.GetReloaderTests.test_watchman_unavailable', 'utils_tests.test_autoreload.TestUtilities.test_is_django_module', 'utils_tests.test_autoreload.TestUtilities.test_is_django_path', 'utils_tests.test_autoreload.RestartWithReloaderTests.test_manage_py', 'utils_tests.test_autoreload.RestartWithReloaderTests.test_python_m_django', 'utils_tests.test_autoreload.RunWithReloaderTests.test_calls_start_django', 'utils_tests.test_autoreload.RunWithReloaderTests.test_calls_sys_exit', 'utils_tests.test_autoreload.RunWithReloaderTests.test_swallows_keyboard_interrupt', 'utils_tests.test_autoreload.TestCheckErrors.test_mutates_error_files', 'utils_tests.test_autoreload.TestChildArguments.test_entrypoint_fallback', 'utils_tests.test_autoreload.TestChildArguments.test_exe_fallback', 'utils_tests.test_autoreload.TestChildArguments.test_module_no_spec', 'utils_tests.test_autoreload.TestChildArguments.test_raises_runtimeerror', 'utils_tests.test_autoreload.TestChildArguments.test_run_as_module'])


def test_p2p_020():
    check(['utils_tests.test_autoreload.StatReloaderTests.test_multiple_globs', 'utils_tests.test_autoreload.StatReloaderTests.test_multiple_recursive_globs', 'utils_tests.test_autoreload.StatReloaderTests.test_nested_glob_recursive', 'utils_tests.test_autoreload.StatReloaderTests.test_overlapping_glob_recursive', 'utils_tests.test_autoreload.StatReloaderTests.test_overlapping_globs', 'utils_tests.test_autoreload.StatReloaderTests.test_snapshot_files_ignores_missing_files', 'utils_tests.test_autoreload.StatReloaderTests.test_snapshot_files_updates', 'utils_tests.test_autoreload.StatReloaderTests.test_snapshot_files_with_duplicates', 'utils_tests.test_autoreload.StatReloaderTests.test_tick_does_not_trigger_twice', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_bytecode_conversion_to_source', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_check_errors', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_check_errors_catches_all_exceptions', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_file_added', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_main_module_is_resolved', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_main_module_without_file_is_not_resolved', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_module_without_spec', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_path_with_embedded_null_bytes', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_paths_are_pathlib_instances', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_weakref_in_sys_module', 'utils_tests.test_autoreload.TestIterModulesAndFiles.test_zip_reload'])
