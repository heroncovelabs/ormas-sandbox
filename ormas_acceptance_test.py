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
    check(['prefetch_related.tests.NestedPrefetchTests.test_nested_prefetch_is_not_overwritten_by_related_object'])


def test_p2p_000():
    check(['prefetch_related.tests.Ticket21410Tests.test_bug', 'prefetch_related.tests.Ticket19607Tests.test_bug', 'prefetch_related.tests.DefaultManagerTests.test_m2m_then_m2m', 'prefetch_related.tests.ReadPrefetchedObjectsCacheTests.test_retrieves_results_from_prefetched_objects_cache', 'prefetch_related.tests.Ticket21760Tests.test_bug', 'prefetch_related.tests.ForeignKeyToFieldTest.test_foreignkey', 'prefetch_related.tests.ForeignKeyToFieldTest.test_m2m', 'prefetch_related.tests.ForeignKeyToFieldTest.test_m2m_manager_reused', 'prefetch_related.tests.RawQuerySetTests.test_basic', 'prefetch_related.tests.RawQuerySetTests.test_clear', 'prefetch_related.tests.RawQuerySetTests.test_prefetch_before_raw', 'prefetch_related.tests.NullableTest.test_in_bulk', 'prefetch_related.tests.NullableTest.test_prefetch_nullable', 'prefetch_related.tests.NullableTest.test_traverse_nullable', 'prefetch_related.tests.LookupOrderingTest.test_order', 'prefetch_related.tests.DirectPrefetchedObjectCacheReuseTests.test_add_clears_prefetched_objects', 'prefetch_related.tests.DirectPrefetchedObjectCacheReuseTests.test_detect_is_fetched', 'prefetch_related.tests.DirectPrefetchedObjectCacheReuseTests.test_detect_is_fetched_with_to_attr', 'prefetch_related.tests.DirectPrefetchedObjectCacheReuseTests.test_prefetch_reverse_foreign_key', 'prefetch_related.tests.DirectPrefetchedObjectCacheReuseTests.test_remove_clears_prefetched_objects'])


def test_p2p_020():
    check(['prefetch_related.tests.PrefetchRelatedTests.test_reverse_one_to_one_then_m2m', 'prefetch_related.tests.PrefetchRelatedTests.test_survives_clone', 'prefetch_related.tests.CustomPrefetchTests.test_ambiguous', 'prefetch_related.tests.CustomPrefetchTests.test_custom_qs', 'prefetch_related.tests.CustomPrefetchTests.test_filter_deferred', 'prefetch_related.tests.CustomPrefetchTests.test_generic_rel', 'prefetch_related.tests.CustomPrefetchTests.test_m2m', 'prefetch_related.tests.CustomPrefetchTests.test_m2m_through_fk', 'prefetch_related.tests.CustomPrefetchTests.test_m2m_through_gfk', 'prefetch_related.tests.CustomPrefetchTests.test_nested_prefetch_related_are_not_overwritten', 'prefetch_related.tests.CustomPrefetchTests.test_nested_prefetch_related_with_duplicate_prefetcher', 'prefetch_related.tests.CustomPrefetchTests.test_o2m_through_m2m', 'prefetch_related.tests.CustomPrefetchTests.test_raw_queryset', 'prefetch_related.tests.CustomPrefetchTests.test_reverse_m2m', 'prefetch_related.tests.CustomPrefetchTests.test_to_attr_cached_property', 'prefetch_related.tests.CustomPrefetchTests.test_to_attr_doesnt_cache_through_attr_as_list', 'prefetch_related.tests.CustomPrefetchTests.test_traverse_multiple_items_property', 'prefetch_related.tests.CustomPrefetchTests.test_traverse_qs', 'prefetch_related.tests.CustomPrefetchTests.test_traverse_single_item_property', 'prefetch_related.tests.CustomPrefetchTests.test_values_queryset'])
