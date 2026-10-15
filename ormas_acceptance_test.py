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
    check(['model_forms.tests.FormFieldCallbackTests.test_custom_callback_from_base_form_meta'])


def test_f2p_001():
    check(['model_forms.tests.FormFieldCallbackTests.test_custom_callback_in_meta'])


def test_p2p_000():
    check(['model_forms.tests.CustomMetaclassTestCase.test_modelform_factory_metaclass', 'model_forms.tests.CustomCleanTests.test_model_form_clean_applies_to_model', 'model_forms.tests.CustomCleanTests.test_override_clean', 'model_forms.tests.FormFieldCallbackTests.test_bad_callback', 'model_forms.tests.FormFieldCallbackTests.test_baseform_with_widgets_in_meta', 'model_forms.tests.FormFieldCallbackTests.test_custom_callback', 'model_forms.tests.FormFieldCallbackTests.test_factory_with_widget_argument', 'model_forms.tests.FormFieldCallbackTests.test_inherit_after_custom_callback', 'model_forms.tests.FormFieldCallbackTests.test_modelform_factory_with_all_fields', 'model_forms.tests.FormFieldCallbackTests.test_modelform_factory_without_fields', 'model_forms.tests.StrictAssignmentTests.test_setattr_raises_validation_error_field_specific', 'model_forms.tests.StrictAssignmentTests.test_setattr_raises_validation_error_non_field', 'model_forms.tests.ValidationTest.test_notrequired_overrides_notblank', 'model_forms.tests.ValidationTest.test_validates_with_replaced_field_excluded', 'model_forms.tests.ValidationTest.test_validates_with_replaced_field_not_specified', 'model_forms.tests.ModelFormInheritanceTests.test_field_removal', 'model_forms.tests.ModelFormInheritanceTests.test_field_removal_name_clashes', 'model_forms.tests.ModelFormInheritanceTests.test_form_subclass_inheritance', 'model_forms.tests.ModelToDictTests.test_many_to_many', 'model_forms.tests.LocalizedModelFormTest.test_model_form_applies_localize_to_all_fields'])


def test_p2p_020():
    check(['model_forms.tests.LocalizedModelFormTest.test_model_form_applies_localize_to_some_fields', 'model_forms.tests.ModelFormBasicTests.test_m2m_initial_callable', 'model_forms.tests.ModelFormBasicTests.test_multi_fields', 'model_forms.tests.ModelFormBasicTests.test_recleaning_model_form_instance', 'model_forms.tests.ModelFormBasicTests.test_runtime_choicefield_populated', 'model_forms.tests.ModelFormBasicTests.test_save_commit_false', 'model_forms.tests.ModelFormBasicTests.test_save_with_data_errors', 'model_forms.tests.ModelFormBasicTests.test_subset_fields', 'model_forms.tests.ModelFormBasicTests.test_validate_foreign_key_to_model_with_overridden_manager', 'model_forms.tests.ModelFormBasicTests.test_validate_foreign_key_uses_default_manager', 'model_forms.tests.FileAndImageFieldTests.test_clean_false', 'model_forms.tests.FileAndImageFieldTests.test_clean_false_required', 'model_forms.tests.FileAndImageFieldTests.test_clear_and_file_contradiction', 'model_forms.tests.FileAndImageFieldTests.test_custom_file_field_save', 'model_forms.tests.FileAndImageFieldTests.test_file_field_data', 'model_forms.tests.FileAndImageFieldTests.test_file_field_multiple_save', 'model_forms.tests.FileAndImageFieldTests.test_file_path_field_blank', 'model_forms.tests.FileAndImageFieldTests.test_filefield_required_false', 'model_forms.tests.FileAndImageFieldTests.test_full_clear', 'model_forms.tests.FileAndImageFieldTests.test_image_field'])


def test_p2p_040():
    check(['model_forms.tests.FileAndImageFieldTests.test_render_empty_file_field'])
