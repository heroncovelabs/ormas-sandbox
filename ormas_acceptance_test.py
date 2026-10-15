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
    check(['model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choice_value_hash'])


def test_p2p_000():
    check(['model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_basics', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choice_iterator_passes_model_to_widget', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choices', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choices_bool', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choices_bool_empty_label', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choices_freshness', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choices_not_fetched_when_not_rendering', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_choices_radio_blank', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_clean_model_instance', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_clean_to_field_name', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_custom_choice_iterator_passes_model_to_widget', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_deepcopies_widget', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_disabled_modelchoicefield', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_disabled_modelchoicefield_has_changed', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_disabled_modelchoicefield_initial_model_instance', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_disabled_modelmultiplechoicefield_has_changed', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_disabled_multiplemodelchoicefield', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_no_extra_query_when_accessing_attrs', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_num_queries', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_overridable_choice_iterator'])


def test_p2p_020():
    check(['model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_queryset_manager', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_queryset_none', 'model_forms.test_modelchoicefield.ModelChoiceFieldTests.test_result_cache_not_shared'])
