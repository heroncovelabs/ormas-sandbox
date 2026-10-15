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
    check(['admin_widgets.tests.AdminFormfieldForDBFieldTests.test_radio_fields_foreignkey_formfield_overrides_empty_label'])


def test_p2p_000():
    check(['admin_widgets.tests.AdminFormfieldForDBFieldTests.test_CharField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_DateField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_DateTimeField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_EmailField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_FileField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_ForeignKey', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_IntegerField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_TextField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_TimeField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_URLField', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_choices_with_radio_fields', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_field_with_choices', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_filtered_many_to_many', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_formfield_overrides', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_formfield_overrides_for_custom_field', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_formfield_overrides_for_datetime_field', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_formfield_overrides_m2m_filter_widget', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_formfield_overrides_widget_instances', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_inheritance', 'admin_widgets.tests.AdminFormfieldForDBFieldTests.test_m2m_widgets'])


def test_p2p_020():
    check(['admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_fk_related_model_not_in_admin', 'admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_fk_to_self_model_not_in_admin', 'admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_proper_manager_for_label_lookup', 'admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_relations_to_non_primary_key', 'admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_render', 'admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_render_fk_as_pk_model', 'admin_widgets.tests.ForeignKeyRawIdWidgetTest.test_render_unsafe_limit_choices_to', 'admin_widgets.tests.ManyToManyRawIdWidgetTest.test_m2m_related_model_not_in_admin', 'admin_widgets.tests.ManyToManyRawIdWidgetTest.test_render', 'admin_widgets.tests.AdminFormfieldForDBFieldWithRequestTests.test_filter_choices_by_request_user', 'admin_widgets.tests.AdminForeignKeyWidgetChangeList.test_changelist_ForeignKey', 'admin_widgets.tests.AdminFileWidgetTests.test_readonly_fields', 'admin_widgets.tests.AdminFileWidgetTests.test_render', 'admin_widgets.tests.AdminFileWidgetTests.test_render_disabled', 'admin_widgets.tests.AdminFileWidgetTests.test_render_required', 'admin_widgets.tests.AdminForeignKeyRawIdWidget.test_invalid_target_id', 'admin_widgets.tests.AdminForeignKeyRawIdWidget.test_label_and_url_for_value_invalid_uuid', 'admin_widgets.tests.AdminForeignKeyRawIdWidget.test_nonexistent_target_id', 'admin_widgets.tests.AdminForeignKeyRawIdWidget.test_url_params_from_lookup_dict_any_iterable', 'admin_widgets.tests.AdminForeignKeyRawIdWidget.test_url_params_from_lookup_dict_callable'])
