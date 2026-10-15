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
    check(['forms_tests.field_tests.test_datefield.DateFieldTest.test_form_field'])


def test_f2p_001():
    check(['forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_value_from_datadict'])


def test_p2p_000():
    check(['forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_1', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_2', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_3', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_4', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_5', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_changed', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_datefield_strptime', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_form_label_association', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_l10n_date_changed', 'forms_tests.field_tests.test_datefield.DateFieldTest.test_l10n_invalid_date_in', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_custom_input_format', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_custom_months', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_fieldset', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_format_value', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_l10n', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_render_datetime', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_render_empty', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_render_invalid_date', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_render_none', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_render_string'])


def test_p2p_020():
    check(['forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_selectdate_empty_label', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_selectdate_required', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_value_omitted_from_data', 'forms_tests.widget_tests.test_selectdatewidget.SelectDateWidgetTest.test_years_rendered_without_separator'])
