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
    check(['sympy/core/tests/test_relational.py::test_issue_18188'])


def test_p2p_000():
    check(['sympy/core/tests/test_relational.py::test_rel_ne', 'sympy/core/tests/test_relational.py::test_rel_subs', 'sympy/core/tests/test_relational.py::test_wrappers', 'sympy/core/tests/test_relational.py::test_Eq', 'sympy/core/tests/test_relational.py::test_as_poly', 'sympy/core/tests/test_relational.py::test_rel_Infinity', 'sympy/core/tests/test_relational.py::test_infinite_symbol_inequalities', 'sympy/core/tests/test_relational.py::test_bool', 'sympy/core/tests/test_relational.py::test_rich_cmp', 'sympy/core/tests/test_relational.py::test_doit', 'sympy/core/tests/test_relational.py::test_new_relational', 'sympy/core/tests/test_relational.py::test_relational_arithmetic', 'sympy/core/tests/test_relational.py::test_relational_bool_output', 'sympy/core/tests/test_relational.py::test_relational_logic_symbols', 'sympy/core/tests/test_relational.py::test_univariate_relational_as_set', 'sympy/core/tests/test_relational.py::test_Not', 'sympy/core/tests/test_relational.py::test_evaluate', 'sympy/core/tests/test_relational.py::test_imaginary_compare_raises_TypeError', 'sympy/core/tests/test_relational.py::test_complex_compare_not_real', 'sympy/core/tests/test_relational.py::test_imaginary_and_inf_compare_raises_TypeError'])


def test_p2p_020():
    check(['sympy/core/tests/test_relational.py::test_reversed', 'sympy/core/tests/test_relational.py::test_canonical', 'sympy/core/tests/test_relational.py::test_issue_8444_workingtests', 'sympy/core/tests/test_relational.py::test_issue_10304', 'sympy/core/tests/test_relational.py::test_issue_10401', 'sympy/core/tests/test_relational.py::test_issue_10633', 'sympy/core/tests/test_relational.py::test_issue_10927', 'sympy/core/tests/test_relational.py::test_issues_13081_12583_12534', 'sympy/core/tests/test_relational.py::test_binary_symbols', 'sympy/core/tests/test_relational.py::test_rel_args', 'sympy/core/tests/test_relational.py::test_Equality_rewrite_as_Add', 'sympy/core/tests/test_relational.py::test_issue_15847', 'sympy/core/tests/test_relational.py::test_negated_property', 'sympy/core/tests/test_relational.py::test_reversedsign_property', 'sympy/core/tests/test_relational.py::test_reversed_reversedsign_property', 'sympy/core/tests/test_relational.py::test_improved_canonical', 'sympy/core/tests/test_relational.py::test_set_equality_canonical', 'sympy/core/tests/test_relational.py::test_trigsimp', 'sympy/core/tests/test_relational.py::test_polynomial_relation_simplification', 'sympy/core/tests/test_relational.py::test_multivariate_linear_function_simplification'])
