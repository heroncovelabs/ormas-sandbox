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
    check(['migrations.test_writer.WriterTests.test_sorted_imports'])


def test_p2p_000():
    check(['migrations.test_writer.OperationWriterTests.test_args_kwargs_signature', 'migrations.test_writer.OperationWriterTests.test_args_signature', 'migrations.test_writer.OperationWriterTests.test_empty_signature', 'migrations.test_writer.OperationWriterTests.test_expand_args_signature', 'migrations.test_writer.OperationWriterTests.test_kwargs_signature', 'migrations.test_writer.OperationWriterTests.test_multiline_args_signature', 'migrations.test_writer.OperationWriterTests.test_nested_args_signature', 'migrations.test_writer.OperationWriterTests.test_nested_operation_expand_args_signature', 'migrations.test_writer.WriterTests.test_custom_operation', 'migrations.test_writer.WriterTests.test_deconstruct_class_arguments', 'migrations.test_writer.WriterTests.test_migration_file_header_comments', 'migrations.test_writer.WriterTests.test_migration_path', 'migrations.test_writer.WriterTests.test_models_import_omitted', 'migrations.test_writer.WriterTests.test_register_non_serializer', 'migrations.test_writer.WriterTests.test_register_serializer', 'migrations.test_writer.WriterTests.test_serialize_builtin_types', 'migrations.test_writer.WriterTests.test_serialize_builtins', 'migrations.test_writer.WriterTests.test_serialize_choices', 'migrations.test_writer.WriterTests.test_serialize_class_based_validators', 'migrations.test_writer.WriterTests.test_serialize_collections'])


def test_p2p_020():
    check(['migrations.test_writer.WriterTests.test_serialize_functools_partialmethod', 'migrations.test_writer.WriterTests.test_serialize_iterators', 'migrations.test_writer.WriterTests.test_serialize_lazy_objects', 'migrations.test_writer.WriterTests.test_serialize_local_function_reference', 'migrations.test_writer.WriterTests.test_serialize_managers', 'migrations.test_writer.WriterTests.test_serialize_multiline_strings', 'migrations.test_writer.WriterTests.test_serialize_nested_class', 'migrations.test_writer.WriterTests.test_serialize_numbers', 'migrations.test_writer.WriterTests.test_serialize_path_like', 'migrations.test_writer.WriterTests.test_serialize_pathlib', 'migrations.test_writer.WriterTests.test_serialize_range', 'migrations.test_writer.WriterTests.test_serialize_set', 'migrations.test_writer.WriterTests.test_serialize_settings', 'migrations.test_writer.WriterTests.test_serialize_strings', 'migrations.test_writer.WriterTests.test_serialize_timedelta', 'migrations.test_writer.WriterTests.test_serialize_type_model', 'migrations.test_writer.WriterTests.test_serialize_type_none', 'migrations.test_writer.WriterTests.test_serialize_unbound_method_reference', 'migrations.test_writer.WriterTests.test_serialize_uuid', 'migrations.test_writer.WriterTests.test_simple_migration'])
