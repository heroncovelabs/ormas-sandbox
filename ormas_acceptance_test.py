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
    check(['sympy/core/tests/test_numbers.py::test_zero_not_false'])


def test_p2p_000():
    check(['sympy/core/tests/test_numbers.py::test_seterr', 'sympy/core/tests/test_numbers.py::test_mod', 'sympy/core/tests/test_numbers.py::test_divmod', 'sympy/core/tests/test_numbers.py::test_igcd', 'sympy/core/tests/test_numbers.py::test_igcd_lehmer', 'sympy/core/tests/test_numbers.py::test_igcd2', 'sympy/core/tests/test_numbers.py::test_ilcm', 'sympy/core/tests/test_numbers.py::test_igcdex', 'sympy/core/tests/test_numbers.py::test_Integer_new', 'sympy/core/tests/test_numbers.py::test_Rational_new', 'sympy/core/tests/test_numbers.py::test_Number_new', 'sympy/core/tests/test_numbers.py::test_Number_cmp', 'sympy/core/tests/test_numbers.py::test_Rational_cmp', 'sympy/core/tests/test_numbers.py::test_Float', 'sympy/core/tests/test_numbers.py::test_float_mpf', 'sympy/core/tests/test_numbers.py::test_Float_RealElement', 'sympy/core/tests/test_numbers.py::test_Float_default_to_highprec_from_str', 'sympy/core/tests/test_numbers.py::test_Float_eval', 'sympy/core/tests/test_numbers.py::test_Float_issue_2107', 'sympy/core/tests/test_numbers.py::test_issue_14289'])


def test_p2p_020():
    check(['sympy/core/tests/test_numbers.py::test_simplify_AlgebraicNumber', 'sympy/core/tests/test_numbers.py::test_Float_idempotence', 'sympy/core/tests/test_numbers.py::test_comp1', 'sympy/core/tests/test_numbers.py::test_issue_9491', 'sympy/core/tests/test_numbers.py::test_issue_10063', 'sympy/core/tests/test_numbers.py::test_issue_10020', 'sympy/core/tests/test_numbers.py::test_invert_numbers', 'sympy/core/tests/test_numbers.py::test_mod_inverse', 'sympy/core/tests/test_numbers.py::test_golden_ratio_rewrite_as_sqrt', 'sympy/core/tests/test_numbers.py::test_tribonacci_constant_rewrite_as_sqrt', 'sympy/core/tests/test_numbers.py::test_comparisons_with_unknown_type', 'sympy/core/tests/test_numbers.py::test_NumberSymbol_comparison', 'sympy/core/tests/test_numbers.py::test_Integer_precision', 'sympy/core/tests/test_numbers.py::test_Integer_ceiling_floor', 'sympy/core/tests/test_numbers.py::test_ComplexInfinity', 'sympy/core/tests/test_numbers.py::test_Infinity_floor_ceiling_power', 'sympy/core/tests/test_numbers.py::test_One_power', 'sympy/core/tests/test_numbers.py::test_NegativeInfinity', 'sympy/core/tests/test_numbers.py::test_issue_6133', 'sympy/core/tests/test_numbers.py::test_abc'])
