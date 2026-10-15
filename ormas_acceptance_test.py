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
    check(['decorators.tests.MethodDecoratorTests.test_wrapper_assignments'])


def test_p2p_000():
    check(['decorators.tests.CacheControlDecoratorTest.test_cache_control_decorator_http_request', 'decorators.tests.XFrameOptionsDecoratorsTests.test_deny_decorator', 'decorators.tests.XFrameOptionsDecoratorsTests.test_exempt_decorator', 'decorators.tests.XFrameOptionsDecoratorsTests.test_sameorigin_decorator', 'decorators.tests.DecoratorsTest.test_attributes', 'decorators.tests.DecoratorsTest.test_cache_page', 'decorators.tests.DecoratorsTest.test_require_safe_accepts_only_safe_methods', 'decorators.tests.DecoratorsTest.test_user_passes_test_composition', 'decorators.tests.NeverCacheDecoratorTest.test_never_cache_decorator', 'decorators.tests.NeverCacheDecoratorTest.test_never_cache_decorator_http_request', 'decorators.tests.MethodDecoratorTests.test_argumented', 'decorators.tests.MethodDecoratorTests.test_bad_iterable', 'decorators.tests.MethodDecoratorTests.test_class_decoration', 'decorators.tests.MethodDecoratorTests.test_descriptors', 'decorators.tests.MethodDecoratorTests.test_invalid_method_name_to_decorate', 'decorators.tests.MethodDecoratorTests.test_invalid_non_callable_attribute_decoration', 'decorators.tests.MethodDecoratorTests.test_new_attribute', 'decorators.tests.MethodDecoratorTests.test_preserve_attributes', 'decorators.tests.MethodDecoratorTests.test_preserve_signature', 'decorators.tests.MethodDecoratorTests.test_tuple_of_decorators'])
