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
    check(['model_inheritance_regress.tests.ModelInheritanceTest.test_mti_update_grand_parent_through_child'])


def test_f2p_001():
    check(['model_inheritance_regress.tests.ModelInheritanceTest.test_mti_update_parent_through_child'])


def test_p2p_000():
    check(['model_inheritance_regress.tests.ModelInheritanceTest.test_abstract_base_class_m2m_relation_inheritance', 'model_inheritance_regress.tests.ModelInheritanceTest.test_abstract_base_class_m2m_relation_inheritance_manager_reused', 'model_inheritance_regress.tests.ModelInheritanceTest.test_abstract_verbose_name_plural_inheritance', 'model_inheritance_regress.tests.ModelInheritanceTest.test_all_fields_from_abstract_base_class', 'model_inheritance_regress.tests.ModelInheritanceTest.test_concrete_abstract_concrete_pk', 'model_inheritance_regress.tests.ModelInheritanceTest.test_create_new_instance_with_pk_equals_none', 'model_inheritance_regress.tests.ModelInheritanceTest.test_create_new_instance_with_pk_equals_none_multi_inheritance', 'model_inheritance_regress.tests.ModelInheritanceTest.test_filter_with_parent_fk', 'model_inheritance_regress.tests.ModelInheritanceTest.test_get_next_previous_by_date', 'model_inheritance_regress.tests.ModelInheritanceTest.test_id_field_update_on_ancestor_change', 'model_inheritance_regress.tests.ModelInheritanceTest.test_inheritance_joins', 'model_inheritance_regress.tests.ModelInheritanceTest.test_inheritance_resolve_columns', 'model_inheritance_regress.tests.ModelInheritanceTest.test_inheritance_select_related', 'model_inheritance_regress.tests.ModelInheritanceTest.test_inherited_fields', 'model_inheritance_regress.tests.ModelInheritanceTest.test_inherited_nullable_exclude', 'model_inheritance_regress.tests.ModelInheritanceTest.test_inherited_unique_field_with_form', 'model_inheritance_regress.tests.ModelInheritanceTest.test_issue_11764', 'model_inheritance_regress.tests.ModelInheritanceTest.test_issue_21554', 'model_inheritance_regress.tests.ModelInheritanceTest.test_issue_6755', 'model_inheritance_regress.tests.ModelInheritanceTest.test_issue_7105'])


def test_p2p_020():
    check(['model_inheritance_regress.tests.ModelInheritanceTest.test_issue_7276', 'model_inheritance_regress.tests.ModelInheritanceTest.test_issue_7853', 'model_inheritance_regress.tests.ModelInheritanceTest.test_model_inheritance', 'model_inheritance_regress.tests.ModelInheritanceTest.test_ptr_accessor_assigns_state', 'model_inheritance_regress.tests.ModelInheritanceTest.test_queries_on_parent_access', 'model_inheritance_regress.tests.ModelInheritanceTest.test_queryset_update_on_parent_model', 'model_inheritance_regress.tests.ModelInheritanceTest.test_related_filtering_query_efficiency_ticket_15844', 'model_inheritance_regress.tests.ModelInheritanceTest.test_use_explicit_o2o_to_parent_as_pk', 'model_inheritance_regress.tests.ModelInheritanceTest.test_use_explicit_o2o_to_parent_from_abstract_model'])
