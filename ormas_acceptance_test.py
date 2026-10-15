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
    check(['model_fields.test_jsonfield.TestMethods.test_get_transforms'])


def test_f2p_001():
    check(['custom_lookups.tests.LookupTests.test_lookups_caching'])


def test_p2p_000():
    check(['model_fields.test_jsonfield.TestFormField.test_formfield', 'model_fields.test_jsonfield.TestFormField.test_formfield_custom_encoder_decoder', 'custom_lookups.tests.SubqueryTransformTests.test_subquery_usage', 'custom_lookups.tests.LookupTransformCallOrderTests.test_call_order', 'custom_lookups.tests.CustomisedMethodsTests.test_overridden_get_lookup', 'custom_lookups.tests.CustomisedMethodsTests.test_overridden_get_lookup_chain', 'custom_lookups.tests.CustomisedMethodsTests.test_overridden_get_transform', 'custom_lookups.tests.CustomisedMethodsTests.test_overridden_get_transform_chain', 'custom_lookups.tests.YearLteTests.test_custom_implementation_year_exact', 'custom_lookups.tests.YearLteTests.test_postgres_year_exact', 'custom_lookups.tests.YearLteTests.test_year_lte_sql', 'model_fields.test_jsonfield.TestMethods.test_deconstruct', 'model_fields.test_jsonfield.TestMethods.test_deconstruct_custom_encoder_decoder', 'model_fields.test_jsonfield.TestMethods.test_key_transform_text_lookup_mixin_non_key_transform', 'model_fields.test_jsonfield.TestValidation.test_custom_encoder', 'model_fields.test_jsonfield.TestValidation.test_invalid_decoder', 'model_fields.test_jsonfield.TestValidation.test_invalid_encoder', 'model_fields.test_jsonfield.TestValidation.test_validation_error', 'model_fields.test_jsonfield.JSONFieldTests.test_custom_encoder_decoder', 'model_fields.test_jsonfield.JSONFieldTests.test_db_check_constraints'])


def test_p2p_020():
    check(['schema.tests.SchemaTests.test_referenced_field_without_constraint_rename_inside_atomic_block', 'schema.tests.SchemaTests.test_referenced_table_without_constraint_rename_inside_atomic_block', 'schema.tests.SchemaTests.test_remove_constraints_capital_letters', 'schema.tests.SchemaTests.test_remove_db_index_doesnt_remove_custom_indexes', 'schema.tests.SchemaTests.test_remove_field', 'schema.tests.SchemaTests.test_remove_field_check_does_not_remove_meta_constraints', 'schema.tests.SchemaTests.test_remove_field_unique_does_not_remove_meta_constraints', 'schema.tests.SchemaTests.test_remove_index_together_does_not_remove_meta_indexes', 'schema.tests.SchemaTests.test_remove_unique_together_does_not_remove_meta_constraints', 'schema.tests.SchemaTests.test_rename_keep_null_status', 'schema.tests.SchemaTests.test_rename_referenced_field', 'schema.tests.SchemaTests.test_rename_table_renames_deferred_sql_references', 'schema.tests.SchemaTests.test_text_field_with_db_index', 'schema.tests.SchemaTests.test_text_field_with_db_index_to_fk', 'schema.tests.SchemaTests.test_unique', 'schema.tests.SchemaTests.test_unique_constraint', 'schema.tests.SchemaTests.test_unique_constraint_field_and_expression', 'schema.tests.SchemaTests.test_unique_name_quoting', 'schema.tests.SchemaTests.test_unique_together', 'schema.tests.SchemaTests.test_unique_together_with_fk'])


def test_p2p_040():
    check(['schema.tests.SchemaTests.test_unique_together_with_fk_with_existing_index'])
