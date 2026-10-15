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
    check(['forms_tests.tests.test_formsets.FormsFormsetTestCase.test_disable_delete_extra_formset_forms'])


def test_f2p_001():
    check(['forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_disable_delete_extra_formset_forms'])


def test_p2p_000():
    check(['forms_tests.tests.test_formsets.AllValidTests.test_invalid', 'forms_tests.tests.test_formsets.AllValidTests.test_valid', 'forms_tests.tests.test_formsets.TestEmptyFormSet.test_empty_formset_is_multipart', 'forms_tests.tests.test_formsets.TestEmptyFormSet.test_empty_formset_is_valid', 'forms_tests.tests.test_formsets.TestEmptyFormSet.test_empty_formset_media', 'forms_tests.tests.test_formsets.FormsetAsTagTests.test_as_div', 'forms_tests.tests.test_formsets.FormsetAsTagTests.test_as_p', 'forms_tests.tests.test_formsets.FormsetAsTagTests.test_as_table', 'forms_tests.tests.test_formsets.FormsetAsTagTests.test_as_ul', 'forms_tests.tests.test_formsets.Jinja2FormsetAsTagTests.test_as_div', 'forms_tests.tests.test_formsets.Jinja2FormsetAsTagTests.test_as_p', 'forms_tests.tests.test_formsets.Jinja2FormsetAsTagTests.test_as_table', 'forms_tests.tests.test_formsets.Jinja2FormsetAsTagTests.test_as_ul', 'forms_tests.tests.test_formsets.TestIsBoundBehavior.test_customize_management_form_error', 'forms_tests.tests.test_formsets.TestIsBoundBehavior.test_empty_forms_are_unbound', 'forms_tests.tests.test_formsets.TestIsBoundBehavior.test_form_errors_are_caught_by_formset', 'forms_tests.tests.test_formsets.TestIsBoundBehavior.test_management_form_invalid_data', 'forms_tests.tests.test_formsets.TestIsBoundBehavior.test_no_data_error', 'forms_tests.tests.test_formsets.TestIsBoundBehavior.test_with_management_data_attrs_work_fine', 'forms_tests.tests.test_formsets.FormsFormsetTestCase.test_absolute_max'])


def test_p2p_020():
    check(['forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_default_absolute_max', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_empty_permitted_ignored_empty_form', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_form_kwargs_empty_form', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formset_total_error_count_with_non_form_errors', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formset_validate_max_flag_custom_error', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formset_validate_min_excludes_empty_forms', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formset_validate_min_flag_custom_formatted_error', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formset_validation', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formset_with_deletion_custom_widget', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_formsets_with_ordering_custom_widget', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_html_safe', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_limited_max_forms_two', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_max_num_with_initial_data', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_max_num_zero_with_initial', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_non_form_errors', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_repr', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_repr_do_not_trigger_validation', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_template_name_can_be_overridden', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_template_name_uses_renderer_value', 'forms_tests.tests.test_formsets.Jinja2FormsFormsetTestCase.test_validate_max_ignores_forms_marked_for_deletion'])
