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
    check(['basic.tests.ManagerTest.test_manager_method_signature'])


def test_p2p_000():
    check(['basic.tests.ModelInstanceCreationTests.test_autofields_generate_different_values_for_each_instance', 'basic.tests.ModelInstanceCreationTests.test_can_create_instance_using_kwargs', 'basic.tests.ModelInstanceCreationTests.test_can_initialize_model_instance_using_positional_arguments', 'basic.tests.ModelInstanceCreationTests.test_can_leave_off_value_for_autofield_and_it_gets_value_on_save', 'basic.tests.ModelInstanceCreationTests.test_can_mix_and_match_position_and_kwargs', 'basic.tests.ModelInstanceCreationTests.test_cannot_create_instance_with_invalid_kwargs', 'basic.tests.ModelInstanceCreationTests.test_for_datetimefields_saves_as_much_precision_as_was_given', 'basic.tests.ModelInstanceCreationTests.test_leaving_off_a_field_with_default_set_the_default_will_be_saved', 'basic.tests.ModelInstanceCreationTests.test_object_is_not_written_to_database_until_save_was_called', 'basic.tests.ModelInstanceCreationTests.test_positional_and_keyword_args_for_the_same_field', 'basic.tests.ModelInstanceCreationTests.test_querysets_checking_for_membership', 'basic.tests.ModelInstanceCreationTests.test_save_parent_primary_with_default', 'basic.tests.ModelInstanceCreationTests.test_save_primary_with_default', 'basic.tests.ModelInstanceCreationTests.test_saving_an_object_again_does_not_create_a_new_object', 'basic.tests.ManagerTest.test_manager_method_attributes', 'basic.tests.ManagerTest.test_manager_methods', 'basic.tests.SelectOnSaveTests.test_select_on_save', 'basic.tests.SelectOnSaveTests.test_select_on_save_lying_update', 'basic.tests.ModelLookupTest.test_all_lookup', 'basic.tests.ModelLookupTest.test_does_not_exist'])


def test_p2p_020():
    check(['basic.tests.ModelTest.test_emptyqs', 'basic.tests.ModelTest.test_emptyqs_customqs', 'basic.tests.ModelTest.test_emptyqs_values', 'basic.tests.ModelTest.test_emptyqs_values_order', 'basic.tests.ModelTest.test_eq', 'basic.tests.ModelTest.test_extra_method_select_argument_with_dashes', 'basic.tests.ModelTest.test_extra_method_select_argument_with_dashes_and_values', 'basic.tests.ModelTest.test_hash', 'basic.tests.ModelTest.test_hash_function', 'basic.tests.ModelTest.test_manually_specify_primary_key', 'basic.tests.ModelTest.test_microsecond_precision', 'basic.tests.ModelTest.test_missing_hash_not_inherited', 'basic.tests.ModelTest.test_multiple_objects_max_num_fetched', 'basic.tests.ModelTest.test_not_equal_and_equal_operators_behave_as_expected_on_instances', 'basic.tests.ModelTest.test_objects_attribute_is_only_available_on_the_class_itself', 'basic.tests.ModelTest.test_queryset_delete_removes_all_items_in_that_queryset', 'basic.tests.ModelTest.test_specified_parent_hash_inherited', 'basic.tests.ModelTest.test_ticket_20278', 'basic.tests.ModelTest.test_unicode_data', 'basic.tests.ModelTest.test_year_lookup_edge_case'])
