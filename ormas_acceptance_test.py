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
    check(['sympy/polys/tests/test_polytools.py::test_issue_5786'])


def test_p2p_000():
    check(['sympy/polys/tests/test_polytools.py::test_Poly_mixed_operations', 'sympy/polys/tests/test_polytools.py::test_Poly_from_dict', 'sympy/polys/tests/test_polytools.py::test_Poly_from_list', 'sympy/polys/tests/test_polytools.py::test_Poly_from_poly', 'sympy/polys/tests/test_polytools.py::test_Poly_from_expr', 'sympy/polys/tests/test_polytools.py::test_Poly__new__', 'sympy/polys/tests/test_polytools.py::test_Poly__args', 'sympy/polys/tests/test_polytools.py::test_Poly__gens', 'sympy/polys/tests/test_polytools.py::test_Poly_zero', 'sympy/polys/tests/test_polytools.py::test_Poly_one', 'sympy/polys/tests/test_polytools.py::test_Poly__unify', 'sympy/polys/tests/test_polytools.py::test_Poly_free_symbols', 'sympy/polys/tests/test_polytools.py::test_PurePoly_free_symbols', 'sympy/polys/tests/test_polytools.py::test_Poly__eq__', 'sympy/polys/tests/test_polytools.py::test_PurePoly__eq__', 'sympy/polys/tests/test_polytools.py::test_PurePoly_Poly', 'sympy/polys/tests/test_polytools.py::test_Poly_get_domain', 'sympy/polys/tests/test_polytools.py::test_Poly_set_domain', 'sympy/polys/tests/test_polytools.py::test_Poly_get_modulus', 'sympy/polys/tests/test_polytools.py::test_Poly_set_modulus'])


def test_p2p_020():
    check(['sympy/polys/tests/test_polytools.py::test_cancel', 'sympy/polys/tests/test_polytools.py::test_reduced', 'sympy/polys/tests/test_polytools.py::test_groebner', 'sympy/polys/tests/test_polytools.py::test_fglm', 'sympy/polys/tests/test_polytools.py::test_is_zero_dimensional', 'sympy/polys/tests/test_polytools.py::test_GroebnerBasis', 'sympy/polys/tests/test_polytools.py::test_poly', 'sympy/polys/tests/test_polytools.py::test_keep_coeff', 'sympy/polys/tests/test_polytools.py::test_poly_matching_consistency', 'sympy/polys/tests/test_polytools.py::test_noncommutative', 'sympy/polys/tests/test_polytools.py::test_to_rational_coeffs', 'sympy/polys/tests/test_polytools.py::test_factor_terms', 'sympy/polys/tests/test_polytools.py::test_as_list', 'sympy/polys/tests/test_polytools.py::test_issue_11198', 'sympy/polys/tests/test_polytools.py::test_Poly_precision', 'sympy/polys/tests/test_polytools.py::test_issue_12400', 'sympy/polys/tests/test_polytools.py::test_issue_14364', 'sympy/polys/tests/test_polytools.py::test_issue_15669', 'sympy/polys/tests/test_polytools.py::test_issue_17988', 'sympy/polys/tests/test_polytools.py::test_issue_18205'])
