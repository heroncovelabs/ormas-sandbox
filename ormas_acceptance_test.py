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
    check(['model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data'])


def test_p2p_000():
    check(['model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_ignores_default_pks_on_submit', 'model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_nulls_default_pks', 'model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_nulls_default_pks_alternate_key_relation', 'model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_nulls_default_pks_auto_parent_uuid_child', 'model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_nulls_default_pks_child_editable_pk', 'model_formsets.test_uuid.InlineFormsetTests.test_inlineformset_factory_nulls_default_pks_uuid_parent_auto_child'])
