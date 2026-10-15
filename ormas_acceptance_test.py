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
    check(['file_storage.tests.FieldCallableFileStorageTests.test_deconstruction_storage_callable_default'])


def test_p2p_000():
    check(['file_storage.tests.FileSystemStorageTests.test_deconstruction', 'file_storage.tests.FileSystemStorageTests.test_lazy_base_url_init', 'file_storage.tests.GetStorageClassTests.test_deprecation_warning', 'file_storage.tests.GetStorageClassTests.test_get_filesystem_storage', 'file_storage.tests.GetStorageClassTests.test_get_invalid_storage_module', 'file_storage.tests.GetStorageClassTests.test_get_nonexistent_storage_class', 'file_storage.tests.GetStorageClassTests.test_get_nonexistent_storage_module', 'file_storage.tests.ContentFileStorageTestCase.test_content_saving', 'file_storage.tests.FieldCallableFileStorageTests.test_callable_base_class_error_raises', 'file_storage.tests.FieldCallableFileStorageTests.test_callable_class_storage_file_field', 'file_storage.tests.FieldCallableFileStorageTests.test_callable_function_storage_file_field', 'file_storage.tests.FieldCallableFileStorageTests.test_callable_storage_file_field_in_model', 'file_storage.tests.FieldCallableFileStorageTests.test_deconstruction', 'file_storage.tests.FieldCallableFileStorageTests.test_file_field_storage_none_uses_default_storage', 'file_storage.tests.FileStoragePathParsing.test_directory_with_dot', 'file_storage.tests.FileStoragePathParsing.test_first_character_dot', 'file_storage.tests.StorageHandlerTests.test_defaults', 'file_storage.tests.StorageHandlerTests.test_nonexistent_alias', 'file_storage.tests.StorageHandlerTests.test_nonexistent_backend', 'file_storage.tests.StorageHandlerTests.test_same_instance'])


def test_p2p_020():
    check(['file_storage.tests.CustomStorageTests.test_file_methods_pathlib_path', 'file_storage.tests.CustomStorageTests.test_file_save_abs_path', 'file_storage.tests.CustomStorageTests.test_save_doesnt_close', 'file_storage.tests.DiscardingFalseContentStorageTests.test_custom_storage_discarding_empty_content', 'file_storage.tests.DiscardingFalseContentStorageTests.test_delete_deletes_directories', 'file_storage.tests.DiscardingFalseContentStorageTests.test_file_get_accessed_time_timezone', 'file_storage.tests.DiscardingFalseContentStorageTests.test_file_get_created_time_timezone', 'file_storage.tests.DiscardingFalseContentStorageTests.test_file_get_modified_time_timezone', 'file_storage.tests.DiscardingFalseContentStorageTests.test_file_methods_pathlib_path', 'file_storage.tests.DiscardingFalseContentStorageTests.test_file_save_abs_path', 'file_storage.tests.DiscardingFalseContentStorageTests.test_save_doesnt_close', 'file_storage.tests.FileStorageTests.test_delete_deletes_directories', 'file_storage.tests.FileStorageTests.test_file_get_accessed_time_timezone', 'file_storage.tests.FileStorageTests.test_file_get_created_time_timezone', 'file_storage.tests.FileStorageTests.test_file_get_modified_time_timezone', 'file_storage.tests.FileStorageTests.test_file_methods_pathlib_path', 'file_storage.tests.FileStorageTests.test_file_save_abs_path', 'file_storage.tests.FileStorageTests.test_save_doesnt_close', 'file_storage.tests.FileLikeObjectTestCase.test_urllib_request_urlopen', 'file_storage.tests.FileSaveRaceConditionTest.test_race_condition'])
