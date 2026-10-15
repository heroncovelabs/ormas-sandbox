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
    check(['sympy/sets/tests/test_fancysets.py::test_imageset_intersect_real'])


def test_p2p_000():
    check(['sympy/sets/tests/test_fancysets.py::test_naturals', 'sympy/sets/tests/test_fancysets.py::test_naturals0', 'sympy/sets/tests/test_fancysets.py::test_integers', 'sympy/sets/tests/test_fancysets.py::test_ImageSet', 'sympy/sets/tests/test_fancysets.py::test_image_is_ImageSet', 'sympy/sets/tests/test_fancysets.py::test_halfcircle', 'sympy/sets/tests/test_fancysets.py::test_ImageSet_iterator_not_injective', 'sympy/sets/tests/test_fancysets.py::test_inf_Range_len', 'sympy/sets/tests/test_fancysets.py::test_Range_set', 'sympy/sets/tests/test_fancysets.py::test_Range_symbolic', 'sympy/sets/tests/test_fancysets.py::test_range_range_intersection', 'sympy/sets/tests/test_fancysets.py::test_range_interval_intersection', 'sympy/sets/tests/test_fancysets.py::test_range_is_finite_set', 'sympy/sets/tests/test_fancysets.py::test_Integers_eval_imageset', 'sympy/sets/tests/test_fancysets.py::test_Range_eval_imageset', 'sympy/sets/tests/test_fancysets.py::test_fun', 'sympy/sets/tests/test_fancysets.py::test_Reals', 'sympy/sets/tests/test_fancysets.py::test_Complex', 'sympy/sets/tests/test_fancysets.py::test_intersections', 'sympy/sets/tests/test_fancysets.py::test_infinitely_indexed_set_1'])


def test_p2p_020():
    check(['sympy/sets/tests/test_fancysets.py::test_ComplexRegion_contains', 'sympy/sets/tests/test_fancysets.py::test_ComplexRegion_intersect', 'sympy/sets/tests/test_fancysets.py::test_ComplexRegion_union', 'sympy/sets/tests/test_fancysets.py::test_ComplexRegion_from_real', 'sympy/sets/tests/test_fancysets.py::test_ComplexRegion_measure', 'sympy/sets/tests/test_fancysets.py::test_normalize_theta_set', 'sympy/sets/tests/test_fancysets.py::test_ComplexRegion_FiniteSet', 'sympy/sets/tests/test_fancysets.py::test_union_RealSubSet', 'sympy/sets/tests/test_fancysets.py::test_issue_9980', 'sympy/sets/tests/test_fancysets.py::test_issue_11732', 'sympy/sets/tests/test_fancysets.py::test_issue_11730', 'sympy/sets/tests/test_fancysets.py::test_issue_11938', 'sympy/sets/tests/test_fancysets.py::test_issue_11914', 'sympy/sets/tests/test_fancysets.py::test_issue_9543', 'sympy/sets/tests/test_fancysets.py::test_issue_16871', 'sympy/sets/tests/test_fancysets.py::test_issue_18050', 'sympy/sets/tests/test_fancysets.py::test_Rationals', 'sympy/sets/tests/test_fancysets.py::test_NZQRC_unions', 'sympy/sets/tests/test_fancysets.py::test_imageset_intersection', 'sympy/sets/tests/test_fancysets.py::test_issue_17858'])
