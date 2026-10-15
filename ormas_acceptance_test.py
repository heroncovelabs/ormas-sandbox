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
    check(['async.test_async_related_managers.AsyncRelatedManagersOperationTest.test_acreate'])


def test_f2p_001():
    check(['async.test_async_related_managers.AsyncRelatedManagersOperationTest.test_acreate_reverse'])


def test_f2p_002():
    check(['async.test_async_related_managers.AsyncRelatedManagersOperationTest.test_aget_or_create'])


def test_f2p_003():
    check(['async.test_async_related_managers.AsyncRelatedManagersOperationTest.test_aget_or_create_reverse'])


def test_f2p_004():
    check(['async.test_async_related_managers.AsyncRelatedManagersOperationTest.test_aupdate_or_create'])


def test_f2p_005():
    check(['async.test_async_related_managers.AsyncRelatedManagersOperationTest.test_aupdate_or_create_reverse'])


def test_f2p_006():
    check(['generic_relations.tests.GenericRelationsTests.test_generic_async_acreate'])


def test_f2p_007():
    check(['generic_relations.tests.GenericRelationsTests.test_generic_async_aget_or_create'])


def test_f2p_008():
    check(['generic_relations.tests.GenericRelationsTests.test_generic_async_aupdate_or_create'])


def test_p2p_000():
    check(['generic_relations.tests.TestInitWithNoneArgument.test_none_allowed', 'generic_relations.tests.ProxyRelatedModelTest.test_default_behavior', 'generic_relations.tests.ProxyRelatedModelTest.test_generic_relation', 'generic_relations.tests.ProxyRelatedModelTest.test_generic_relation_set', 'generic_relations.tests.ProxyRelatedModelTest.test_proxy_is_returned', 'generic_relations.tests.ProxyRelatedModelTest.test_query', 'generic_relations.tests.ProxyRelatedModelTest.test_query_proxy', 'generic_relations.tests.ProxyRelatedModelTest.test_works_normally', 'generic_relations.tests.GenericRelationsTests.test_access_content_object', 'generic_relations.tests.GenericRelationsTests.test_access_via_content_type', 'generic_relations.tests.GenericRelationsTests.test_add_after_prefetch', 'generic_relations.tests.GenericRelationsTests.test_add_bulk', 'generic_relations.tests.GenericRelationsTests.test_add_bulk_false', 'generic_relations.tests.GenericRelationsTests.test_add_rejects_unsaved_objects', 'generic_relations.tests.GenericRelationsTests.test_add_rejects_wrong_instances', 'generic_relations.tests.GenericRelationsTests.test_add_then_remove_after_prefetch', 'generic_relations.tests.GenericRelationsTests.test_assign', 'generic_relations.tests.GenericRelationsTests.test_assign_content_object_in_init', 'generic_relations.tests.GenericRelationsTests.test_assign_with_queryset', 'generic_relations.tests.GenericRelationsTests.test_cache_invalidation_for_content_type_id'])


def test_p2p_020():
    check(['generic_relations.tests.GenericRelationsTests.test_multiple_gfk', 'generic_relations.tests.GenericRelationsTests.test_object_deletion_with_generic_relation', 'generic_relations.tests.GenericRelationsTests.test_object_deletion_without_generic_relation', 'generic_relations.tests.GenericRelationsTests.test_prefetch_related_custom_object_id', 'generic_relations.tests.GenericRelationsTests.test_prefetch_related_different_content_types', 'generic_relations.tests.GenericRelationsTests.test_queries_across_generic_relations', 'generic_relations.tests.GenericRelationsTests.test_queries_content_type_restriction', 'generic_relations.tests.GenericRelationsTests.test_query_content_object', 'generic_relations.tests.GenericRelationsTests.test_query_content_type', 'generic_relations.tests.GenericRelationsTests.test_remove', 'generic_relations.tests.GenericRelationsTests.test_remove_after_prefetch', 'generic_relations.tests.GenericRelationsTests.test_set', 'generic_relations.tests.GenericRelationsTests.test_set_after_prefetch', 'generic_relations.tests.GenericRelationsTests.test_set_foreign_key', 'generic_relations.tests.GenericRelationsTests.test_subclasses_with_gen_rel', 'generic_relations.tests.GenericRelationsTests.test_subclasses_with_parent_gen_rel', 'generic_relations.tests.GenericRelationsTests.test_tag_deletion_related_objects_unaffected', 'generic_relations.tests.GenericRelationsTests.test_unsaved_generic_foreign_key_parent_bulk_create', 'generic_relations.tests.GenericRelationsTests.test_unsaved_generic_foreign_key_parent_save', 'generic_relations.tests.GenericRelationsTests.test_update_or_create_defaults'])
