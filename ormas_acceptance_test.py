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
    check(['admin_checks.tests.SystemChecksTestCase.test_nonexistent_field'])


def test_f2p_001():
    check(['admin_checks.tests.SystemChecksTestCase.test_nonexistent_field_on_inline'])


def test_p2p_000():
    check(['admin_checks.tests.SystemChecksTestCase.test_admin_check_ignores_import_error_in_middleware', 'admin_checks.tests.SystemChecksTestCase.test_allows_checks_relying_on_other_modeladmins', 'admin_checks.tests.SystemChecksTestCase.test_app_label_in_admin_checks', 'admin_checks.tests.SystemChecksTestCase.test_apps_dependencies', 'admin_checks.tests.SystemChecksTestCase.test_cannot_include_through', 'admin_checks.tests.SystemChecksTestCase.test_check_fieldset_sublists_for_duplicates', 'admin_checks.tests.SystemChecksTestCase.test_check_sublists_for_duplicates', 'admin_checks.tests.SystemChecksTestCase.test_checks_are_performed', 'admin_checks.tests.SystemChecksTestCase.test_context_processor_dependencies', 'admin_checks.tests.SystemChecksTestCase.test_context_processor_dependencies_model_backend_subclass', 'admin_checks.tests.SystemChecksTestCase.test_custom_adminsite', 'admin_checks.tests.SystemChecksTestCase.test_custom_get_form_with_fieldsets', 'admin_checks.tests.SystemChecksTestCase.test_custom_modelforms_with_fields_fieldsets', 'admin_checks.tests.SystemChecksTestCase.test_editable', 'admin_checks.tests.SystemChecksTestCase.test_exclude_duplicate_values', 'admin_checks.tests.SystemChecksTestCase.test_exclude_in_inline', 'admin_checks.tests.SystemChecksTestCase.test_exclude_inline_model_admin', 'admin_checks.tests.SystemChecksTestCase.test_exclude_values', 'admin_checks.tests.SystemChecksTestCase.test_explicit_through_override', 'admin_checks.tests.SystemChecksTestCase.test_extra'])


def test_p2p_020():
    check(['admin_checks.tests.SystemChecksTestCase.test_list_filter_works_on_through_field_even_when_apps_not_ready', 'admin_checks.tests.SystemChecksTestCase.test_middleware_dependencies', 'admin_checks.tests.SystemChecksTestCase.test_middleware_subclasses', 'admin_checks.tests.SystemChecksTestCase.test_nested_fields', 'admin_checks.tests.SystemChecksTestCase.test_nested_fieldsets', 'admin_checks.tests.SystemChecksTestCase.test_no_template_engines', 'admin_checks.tests.SystemChecksTestCase.test_non_model_fields', 'admin_checks.tests.SystemChecksTestCase.test_non_model_first_field', 'admin_checks.tests.SystemChecksTestCase.test_nonfirst_fieldset', 'admin_checks.tests.SystemChecksTestCase.test_pk_not_editable', 'admin_checks.tests.SystemChecksTestCase.test_readonly', 'admin_checks.tests.SystemChecksTestCase.test_readonly_and_editable', 'admin_checks.tests.SystemChecksTestCase.test_readonly_dynamic_attribute_on_modeladmin', 'admin_checks.tests.SystemChecksTestCase.test_readonly_fields_not_list_or_tuple', 'admin_checks.tests.SystemChecksTestCase.test_readonly_lambda', 'admin_checks.tests.SystemChecksTestCase.test_readonly_method_on_model', 'admin_checks.tests.SystemChecksTestCase.test_readonly_on_method', 'admin_checks.tests.SystemChecksTestCase.test_readonly_on_modeladmin', 'admin_checks.tests.SystemChecksTestCase.test_several_templates_backends', 'admin_checks.tests.SystemChecksTestCase.test_valid_generic_inline_model_admin'])
