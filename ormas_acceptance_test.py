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
    check(['proxy_models.tests.ProxyModelTests.test_select_related_only'])


def test_p2p_000():
    check(['proxy_models.tests.ProxyModelTests.test_abstract_base_with_model_fields', 'proxy_models.tests.ProxyModelTests.test_basic_proxy', 'proxy_models.tests.ProxyModelTests.test_basic_proxy_reverse', 'proxy_models.tests.ProxyModelTests.test_concrete_model', 'proxy_models.tests.ProxyModelTests.test_content_type', 'proxy_models.tests.ProxyModelTests.test_correct_type_proxy_of_proxy', 'proxy_models.tests.ProxyModelTests.test_eq', 'proxy_models.tests.ProxyModelTests.test_filter_proxy_relation_reverse', 'proxy_models.tests.ProxyModelTests.test_inheritance_new_table', 'proxy_models.tests.ProxyModelTests.test_myperson_manager', 'proxy_models.tests.ProxyModelTests.test_new_fields', 'proxy_models.tests.ProxyModelTests.test_no_base_classes', 'proxy_models.tests.ProxyModelTests.test_no_proxy', 'proxy_models.tests.ProxyModelTests.test_otherperson_manager', 'proxy_models.tests.ProxyModelTests.test_permissions_created', 'proxy_models.tests.ProxyModelTests.test_proxy_bug', 'proxy_models.tests.ProxyModelTests.test_proxy_delete', 'proxy_models.tests.ProxyModelTests.test_proxy_for_model', 'proxy_models.tests.ProxyModelTests.test_proxy_included_in_ancestors', 'proxy_models.tests.ProxyModelTests.test_proxy_load_from_fixture'])


def test_p2p_020():
    check(['proxy_models.tests.ProxyModelTests.test_proxy_model_signals', 'proxy_models.tests.ProxyModelTests.test_proxy_update', 'proxy_models.tests.ProxyModelTests.test_same_manager_queries', 'proxy_models.tests.ProxyModelTests.test_select_related', 'proxy_models.tests.ProxyModelTests.test_swappable', 'proxy_models.tests.ProxyModelTests.test_too_many_concrete_classes', 'proxy_models.tests.ProxyModelTests.test_user_proxy_models', 'proxy_models.tests.ProxyModelAdminTests.test_cascade_delete_proxy_model_admin_warning', 'proxy_models.tests.ProxyModelAdminTests.test_delete_str_in_model_admin'])
