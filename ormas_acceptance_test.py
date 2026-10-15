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
    check(['modeladmin.tests.ModelAdminTests.test_lookup_allowed_foreign_primary'])


def test_p2p_000():
    check(['modeladmin.tests.ModelAdminPermissionTests.test_has_add_permission', 'modeladmin.tests.ModelAdminPermissionTests.test_has_change_permission', 'modeladmin.tests.ModelAdminPermissionTests.test_has_delete_permission', 'modeladmin.tests.ModelAdminPermissionTests.test_has_module_permission', 'modeladmin.tests.ModelAdminPermissionTests.test_has_view_permission', 'modeladmin.tests.ModelAdminPermissionTests.test_inline_has_add_permission_uses_obj', 'modeladmin.tests.ModelAdminTests.test_custom_form_meta_exclude', 'modeladmin.tests.ModelAdminTests.test_custom_form_meta_exclude_with_readonly', 'modeladmin.tests.ModelAdminTests.test_custom_form_validation', 'modeladmin.tests.ModelAdminTests.test_custom_formfield_override_readonly', 'modeladmin.tests.ModelAdminTests.test_default_attributes', 'modeladmin.tests.ModelAdminTests.test_default_fields', 'modeladmin.tests.ModelAdminTests.test_default_fieldsets', 'modeladmin.tests.ModelAdminTests.test_default_foreign_key_widget', 'modeladmin.tests.ModelAdminTests.test_field_arguments', 'modeladmin.tests.ModelAdminTests.test_field_arguments_restricted_on_form', 'modeladmin.tests.ModelAdminTests.test_foreign_key_as_radio_field', 'modeladmin.tests.ModelAdminTests.test_form_exclude_kwarg_override', 'modeladmin.tests.ModelAdminTests.test_formset_exclude_kwarg_override', 'modeladmin.tests.ModelAdminTests.test_formset_overriding_get_exclude_with_form_exclude'])


def test_p2p_020():
    check(['modeladmin.tests.ModelAdminTests.test_formset_overriding_get_exclude_with_form_fields', 'modeladmin.tests.ModelAdminTests.test_get_autocomplete_fields', 'modeladmin.tests.ModelAdminTests.test_get_deleted_objects', 'modeladmin.tests.ModelAdminTests.test_get_deleted_objects_with_custom_has_delete_permission', 'modeladmin.tests.ModelAdminTests.test_get_exclude_overrides_exclude', 'modeladmin.tests.ModelAdminTests.test_get_exclude_takes_obj', 'modeladmin.tests.ModelAdminTests.test_get_fieldsets', 'modeladmin.tests.ModelAdminTests.test_log_actions', 'modeladmin.tests.ModelAdminTests.test_lookup_allowed_allows_nonexistent_lookup', 'modeladmin.tests.ModelAdminTests.test_lookup_allowed_onetoone', 'modeladmin.tests.ModelAdminTests.test_modeladmin_repr', 'modeladmin.tests.ModelAdminTests.test_modeladmin_str', 'modeladmin.tests.ModelAdminTests.test_overriding_get_exclude', 'modeladmin.tests.ModelAdminTests.test_queryset_override', 'modeladmin.tests.ModelAdminTests.test_raw_id_fields_widget_override', 'modeladmin.tests.ModelAdminTests.test_regression_for_ticket_15820'])
