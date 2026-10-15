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
    check(['sympy/printing/tests/test_repr.py::test_dict'])


def test_p2p_000():
    check(['sympy/printing/tests/test_repr.py::test_printmethod', 'sympy/printing/tests/test_repr.py::test_more_than_255_args_issue_10259', 'sympy/printing/tests/test_repr.py::test_Function', 'sympy/printing/tests/test_repr.py::test_Geometry', 'sympy/printing/tests/test_repr.py::test_Singletons', 'sympy/printing/tests/test_repr.py::test_Integer', 'sympy/printing/tests/test_repr.py::test_list', 'sympy/printing/tests/test_repr.py::test_Matrix', 'sympy/printing/tests/test_repr.py::test_empty_Matrix', 'sympy/printing/tests/test_repr.py::test_Rational', 'sympy/printing/tests/test_repr.py::test_Float', 'sympy/printing/tests/test_repr.py::test_Symbol', 'sympy/printing/tests/test_repr.py::test_Symbol_two_assumptions', 'sympy/printing/tests/test_repr.py::test_Symbol_no_special_commutative_treatment', 'sympy/printing/tests/test_repr.py::test_Wild', 'sympy/printing/tests/test_repr.py::test_Dummy', 'sympy/printing/tests/test_repr.py::test_Dummy_assumption', 'sympy/printing/tests/test_repr.py::test_Dummy_from_Symbol', 'sympy/printing/tests/test_repr.py::test_tuple', 'sympy/printing/tests/test_repr.py::test_WildFunction'])


def test_p2p_020():
    check(['sympy/printing/tests/test_repr.py::test_settins', 'sympy/printing/tests/test_repr.py::test_AlgebraicNumber', 'sympy/printing/tests/test_repr.py::test_PolyRing', 'sympy/printing/tests/test_repr.py::test_FracField', 'sympy/printing/tests/test_repr.py::test_PolyElement', 'sympy/printing/tests/test_repr.py::test_FracElement', 'sympy/printing/tests/test_repr.py::test_FractionField', 'sympy/printing/tests/test_repr.py::test_PolynomialRingBase', 'sympy/printing/tests/test_repr.py::test_DMP', 'sympy/printing/tests/test_repr.py::test_FiniteExtension', 'sympy/printing/tests/test_repr.py::test_ExtensionElement', 'sympy/printing/tests/test_repr.py::test_BooleanAtom', 'sympy/printing/tests/test_repr.py::test_Integers', 'sympy/printing/tests/test_repr.py::test_Naturals', 'sympy/printing/tests/test_repr.py::test_Naturals0', 'sympy/printing/tests/test_repr.py::test_Reals', 'sympy/printing/tests/test_repr.py::test_matrix_expressions', 'sympy/printing/tests/test_repr.py::test_Cycle', 'sympy/printing/tests/test_repr.py::test_Permutation', 'sympy/printing/tests/test_repr.py::test_diffgeom'])
