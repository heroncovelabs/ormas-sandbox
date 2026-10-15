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
    check(['admin_changelist.tests.ChangeListTests.test_many_search_terms'])


def test_f2p_001():
    check(['admin_changelist.tests.ChangeListTests.test_multiple_search_fields'])


def test_f2p_002():
    check(['admin_changelist.tests.ChangeListTests.test_related_field_multiple_search_terms'])


def test_p2p_000():
    check(['admin_changelist.tests.GetAdminLogTests.test_custom_user_pk_not_named_id', 'admin_changelist.tests.GetAdminLogTests.test_missing_args', 'admin_changelist.tests.GetAdminLogTests.test_no_user', 'admin_changelist.tests.GetAdminLogTests.test_non_integer_limit', 'admin_changelist.tests.GetAdminLogTests.test_without_as', 'admin_changelist.tests.GetAdminLogTests.test_without_for_user', 'admin_changelist.tests.ChangeListTests.test_builtin_lookup_in_search_fields', 'admin_changelist.tests.ChangeListTests.test_changelist_search_form_validation', 'admin_changelist.tests.ChangeListTests.test_changelist_view_list_editable_changed_objects_uses_filter', 'admin_changelist.tests.ChangeListTests.test_clear_all_filters_link', 'admin_changelist.tests.ChangeListTests.test_clear_all_filters_link_callable_filter', 'admin_changelist.tests.ChangeListTests.test_computed_list_display_localization', 'admin_changelist.tests.ChangeListTests.test_custom_lookup_in_search_fields', 'admin_changelist.tests.ChangeListTests.test_custom_lookup_with_pk_shortcut', 'admin_changelist.tests.ChangeListTests.test_custom_paginator', 'admin_changelist.tests.ChangeListTests.test_deterministic_order_for_model_ordered_by_its_manager', 'admin_changelist.tests.ChangeListTests.test_deterministic_order_for_unordered_model', 'admin_changelist.tests.ChangeListTests.test_dynamic_list_display', 'admin_changelist.tests.ChangeListTests.test_dynamic_list_display_links', 'admin_changelist.tests.ChangeListTests.test_dynamic_list_filter'])


def test_p2p_020():
    check(['admin_changelist.tests.ChangeListTests.test_dynamic_search_fields', 'admin_changelist.tests.ChangeListTests.test_pk_in_search_fields', 'admin_changelist.tests.ChangeListTests.test_repr', 'admin_changelist.tests.ChangeListTests.test_result_list_editable', 'admin_changelist.tests.ChangeListTests.test_result_list_editable_html', 'admin_changelist.tests.ChangeListTests.test_result_list_empty_changelist_value', 'admin_changelist.tests.ChangeListTests.test_result_list_html', 'admin_changelist.tests.ChangeListTests.test_result_list_set_empty_value_display_in_model_admin', 'admin_changelist.tests.ChangeListTests.test_result_list_set_empty_value_display_on_admin_site', 'admin_changelist.tests.ChangeListTests.test_search_help_text', 'admin_changelist.tests.ChangeListTests.test_select_related_as_empty_tuple', 'admin_changelist.tests.ChangeListTests.test_select_related_as_tuple', 'admin_changelist.tests.ChangeListTests.test_select_related_preserved', 'admin_changelist.tests.ChangeListTests.test_select_related_preserved_when_multi_valued_in_search_fields', 'admin_changelist.tests.ChangeListTests.test_show_all', 'admin_changelist.tests.ChangeListTests.test_spanning_relations_with_custom_lookup_in_search_fields', 'admin_changelist.tests.ChangeListTests.test_specified_ordering_by_f_expression', 'admin_changelist.tests.ChangeListTests.test_specified_ordering_by_f_expression_without_asc_desc', 'admin_changelist.tests.ChangeListTests.test_total_ordering_optimization', 'admin_changelist.tests.ChangeListTests.test_total_ordering_optimization_meta_constraints'])


def test_p2p_040():
    check(['admin_changelist.tests.ChangeListTests.test_tuple_list_display'])
