"""Ormas adapted public benchmark acceptance; generated, immutable."""
from ormas_acceptance import run

ARGV = ['python3', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--tb=short']
DJANGO = False

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
    check(['sympy/sets/tests/test_sets.py::test_Eq'])


def test_f2p_001():
    check(['sympy/sets/tests/test_sets.py::test_issue_19378'])


def test_p2p_000():
    check(['sympy/sets/tests/test_sets.py::test_imageset', 'sympy/sets/tests/test_sets.py::test_is_empty', 'sympy/sets/tests/test_sets.py::test_is_finiteset', 'sympy/sets/tests/test_sets.py::test_deprecated_is_EmptySet', 'sympy/sets/tests/test_sets.py::test_interval_arguments', 'sympy/sets/tests/test_sets.py::test_interval_symbolic_end_points', 'sympy/sets/tests/test_sets.py::test_interval_is_empty', 'sympy/sets/tests/test_sets.py::test_union', 'sympy/sets/tests/test_sets.py::test_union_iter', 'sympy/sets/tests/test_sets.py::test_union_is_empty', 'sympy/sets/tests/test_sets.py::test_difference', 'sympy/sets/tests/test_sets.py::test_Complement', 'sympy/sets/tests/test_sets.py::test_set_operations_nonsets', 'sympy/sets/tests/test_sets.py::test_complement', 'sympy/sets/tests/test_sets.py::test_intersect1', 'sympy/sets/tests/test_sets.py::test_intersection', 'sympy/sets/tests/test_sets.py::test_issue_9623', 'sympy/sets/tests/test_sets.py::test_is_disjoint', 'sympy/sets/tests/test_sets.py::test_ProductSet__len__', 'sympy/sets/tests/test_sets.py::test_ProductSet'])


def test_p2p_020():
    check(['sympy/sets/tests/test_sets.py::test_issue_10248', 'sympy/sets/tests/test_sets.py::test_issue_9447', 'sympy/sets/tests/test_sets.py::test_issue_10337', 'sympy/sets/tests/test_sets.py::test_issue_10326', 'sympy/sets/tests/test_sets.py::test_issue_2799', 'sympy/sets/tests/test_sets.py::test_issue_9706', 'sympy/sets/tests/test_sets.py::test_issue_8257', 'sympy/sets/tests/test_sets.py::test_issue_10931', 'sympy/sets/tests/test_sets.py::test_issue_11174', 'sympy/sets/tests/test_sets.py::test_issue_18505', 'sympy/sets/tests/test_sets.py::test_finite_set_intersection', 'sympy/sets/tests/test_sets.py::test_union_intersection_constructor', 'sympy/sets/tests/test_sets.py::test_Union_contains', 'sympy/sets/tests/test_sets.py::test_DisjointUnion', 'sympy/sets/tests/test_sets.py::test_DisjointUnion_is_empty', 'sympy/sets/tests/test_sets.py::test_DisjointUnion_is_iterable', 'sympy/sets/tests/test_sets.py::test_DisjointUnion_contains', 'sympy/sets/tests/test_sets.py::test_DisjointUnion_iter', 'sympy/sets/tests/test_sets.py::test_DisjointUnion_len', 'sympy/sets/tests/test_sets.py::test_issue_20089'])
