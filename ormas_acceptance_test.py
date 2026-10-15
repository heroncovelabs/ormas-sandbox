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
    check(['sympy/printing/tests/test_str.py::test_Mul'])


def test_p2p_000():
    check(['sympy/printing/tests/test_str.py::test_printmethod', 'sympy/printing/tests/test_str.py::test_Abs', 'sympy/printing/tests/test_str.py::test_Add', 'sympy/printing/tests/test_str.py::test_Catalan', 'sympy/printing/tests/test_str.py::test_ComplexInfinity', 'sympy/printing/tests/test_str.py::test_Derivative', 'sympy/printing/tests/test_str.py::test_dict', 'sympy/printing/tests/test_str.py::test_Dict', 'sympy/printing/tests/test_str.py::test_Dummy', 'sympy/printing/tests/test_str.py::test_EulerGamma', 'sympy/printing/tests/test_str.py::test_Exp', 'sympy/printing/tests/test_str.py::test_factorial', 'sympy/printing/tests/test_str.py::test_Function', 'sympy/printing/tests/test_str.py::test_Geometry', 'sympy/printing/tests/test_str.py::test_GoldenRatio', 'sympy/printing/tests/test_str.py::test_TribonacciConstant', 'sympy/printing/tests/test_str.py::test_ImaginaryUnit', 'sympy/printing/tests/test_str.py::test_Infinity', 'sympy/printing/tests/test_str.py::test_Integer', 'sympy/printing/tests/test_str.py::test_Integral'])


def test_p2p_020():
    check(['sympy/printing/tests/test_str.py::test_MatrixSlice', 'sympy/printing/tests/test_str.py::test_true_false', 'sympy/printing/tests/test_str.py::test_Equivalent', 'sympy/printing/tests/test_str.py::test_Xor', 'sympy/printing/tests/test_str.py::test_Complement', 'sympy/printing/tests/test_str.py::test_SymmetricDifference', 'sympy/printing/tests/test_str.py::test_UnevaluatedExpr', 'sympy/printing/tests/test_str.py::test_MatrixElement_printing', 'sympy/printing/tests/test_str.py::test_MatrixSymbol_printing', 'sympy/printing/tests/test_str.py::test_MatrixExpressions', 'sympy/printing/tests/test_str.py::test_Subs_printing', 'sympy/printing/tests/test_str.py::test_issue_15716', 'sympy/printing/tests/test_str.py::test_str_special_matrices', 'sympy/printing/tests/test_str.py::test_issue_14567', 'sympy/printing/tests/test_str.py::test_issue_21119_21460', 'sympy/printing/tests/test_str.py::test_Str', 'sympy/printing/tests/test_str.py::test_diffgeom', 'sympy/printing/tests/test_str.py::test_NDimArray', 'sympy/printing/tests/test_str.py::test_Predicate', 'sympy/printing/tests/test_str.py::test_AppliedPredicate'])
