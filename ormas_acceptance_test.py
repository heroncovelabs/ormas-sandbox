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
    check(['model_formsets.tests.ModelFormsetTest.test_edit_only'])


def test_f2p_001():
    check(['model_formsets.tests.ModelFormsetTest.test_edit_only_inlineformset_factory'])


def test_f2p_002():
    check(['model_formsets.tests.ModelFormsetTest.test_edit_only_object_outside_of_queryset'])


def test_p2p_000():
    check(['model_formsets.tests.DeletionTests.test_add_form_deletion_when_invalid', 'model_formsets.tests.DeletionTests.test_change_form_deletion_when_invalid', 'model_formsets.tests.DeletionTests.test_deletion', 'model_formsets.tests.DeletionTests.test_outdated_deletion', 'model_formsets.tests.ModelFormsetTest.test_callable_defaults', 'model_formsets.tests.ModelFormsetTest.test_commit_false', 'model_formsets.tests.ModelFormsetTest.test_custom_form', 'model_formsets.tests.ModelFormsetTest.test_custom_pk', 'model_formsets.tests.ModelFormsetTest.test_custom_queryset_init', 'model_formsets.tests.ModelFormsetTest.test_custom_save_method', 'model_formsets.tests.ModelFormsetTest.test_foreign_keys_in_parents', 'model_formsets.tests.ModelFormsetTest.test_initial_form_count_empty_data', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_save_as_new', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_with_custom_pk', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_with_custom_save_method', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_with_custom_save_method_related_instance', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_with_multi_table_inheritance', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_with_nullable_unique_together', 'model_formsets.tests.ModelFormsetTest.test_inline_formsets_with_wrong_fk_name'])


def test_p2p_020():
    check(['model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_absolute_max', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_absolute_max_with_max_num', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_can_delete_extra', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_can_not_delete_extra', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_error_messages_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_field_class_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_help_text_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_labels_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_passes_renderer', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_inlineformset_factory_widgets', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_absolute_max', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_absolute_max_with_max_num', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_can_delete_extra', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_disable_delete_extra', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_error_messages_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_field_class_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_help_text_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_labels_overrides', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_passes_renderer', 'model_formsets.tests.TestModelFormsetOverridesTroughFormMeta.test_modelformset_factory_widgets'])
