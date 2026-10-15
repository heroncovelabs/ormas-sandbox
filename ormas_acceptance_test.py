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
    check(['model_fields.tests.BasicFieldTests.test_hash_immutability'])


def test_p2p_000():
    check(['model_fields.tests.ChoicesTests.test_check', 'model_fields.tests.ChoicesTests.test_choices', 'model_fields.tests.ChoicesTests.test_flatchoices', 'model_fields.tests.ChoicesTests.test_formfield', 'model_fields.tests.ChoicesTests.test_invalid_choice', 'model_fields.tests.GetChoicesTests.test_blank_in_choices', 'model_fields.tests.GetChoicesTests.test_blank_in_grouped_choices', 'model_fields.tests.GetChoicesTests.test_empty_choices', 'model_fields.tests.GetChoicesTests.test_lazy_strings_not_evaluated', 'model_fields.tests.GetChoicesOrderingTests.test_get_choices', 'model_fields.tests.GetChoicesOrderingTests.test_get_choices_default_ordering', 'model_fields.tests.GetChoicesOrderingTests.test_get_choices_reverse_related_field', 'model_fields.tests.GetChoicesOrderingTests.test_get_choices_reverse_related_field_default_ordering', 'model_fields.tests.GetFieldDisplayTests.test_choices_and_field_display', 'model_fields.tests.GetFieldDisplayTests.test_empty_iterator_choices', 'model_fields.tests.GetFieldDisplayTests.test_get_FIELD_display_translated', 'model_fields.tests.GetFieldDisplayTests.test_iterator_choices', 'model_fields.tests.GetFieldDisplayTests.test_overriding_FIELD_display', 'model_fields.tests.GetFieldDisplayTests.test_overriding_inherited_FIELD_display', 'model_fields.tests.BasicFieldTests.test_abstract_inherited_fields'])


def test_p2p_020():
    check(['model_fields.tests.BasicFieldTests.test_choices_form_class', 'model_fields.tests.BasicFieldTests.test_deconstruct_nested_field', 'model_fields.tests.BasicFieldTests.test_field_instance_is_picklable', 'model_fields.tests.BasicFieldTests.test_field_name', 'model_fields.tests.BasicFieldTests.test_field_ordering', 'model_fields.tests.BasicFieldTests.test_field_repr', 'model_fields.tests.BasicFieldTests.test_field_repr_nested', 'model_fields.tests.BasicFieldTests.test_field_str', 'model_fields.tests.BasicFieldTests.test_field_verbose_name', 'model_fields.tests.BasicFieldTests.test_formfield_disabled', 'model_fields.tests.BasicFieldTests.test_show_hidden_initial', 'model_fields.tests.GetChoicesLimitChoicesToTests.test_get_choices', 'model_fields.tests.GetChoicesLimitChoicesToTests.test_get_choices_reverse_related_field'])
