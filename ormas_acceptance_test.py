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
    check(['inspectdb.tests.InspectDBTestCase.test_foreign_key_to_field'])


def test_p2p_000():
    check(['inspectdb.tests.InspectDBTransactionalTests.test_include_views', 'inspectdb.tests.InspectDBTestCase.test_attribute_name_not_python_keyword', 'inspectdb.tests.InspectDBTestCase.test_char_field_db_collation', 'inspectdb.tests.InspectDBTestCase.test_digits_column_name_introspection', 'inspectdb.tests.InspectDBTestCase.test_field_types', 'inspectdb.tests.InspectDBTestCase.test_number_field_types', 'inspectdb.tests.InspectDBTestCase.test_introspection_errors', 'inspectdb.tests.InspectDBTestCase.test_json_field', 'inspectdb.tests.InspectDBTestCase.test_managed_models', 'inspectdb.tests.InspectDBTestCase.test_special_column_name_introspection', 'inspectdb.tests.InspectDBTestCase.test_stealth_table_name_filter_option', 'inspectdb.tests.InspectDBTestCase.test_table_name_introspection', 'inspectdb.tests.InspectDBTestCase.test_table_option', 'inspectdb.tests.InspectDBTestCase.test_text_field_db_collation', 'inspectdb.tests.InspectDBTestCase.test_unique_together_meta'])
