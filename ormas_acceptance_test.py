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
    check(['sympy/utilities/tests/test_lambdify.py::test_issue_14941'])


def test_p2p_000():
    check(['sympy/utilities/tests/test_lambdify.py::test_no_args', 'sympy/utilities/tests/test_lambdify.py::test_single_arg', 'sympy/utilities/tests/test_lambdify.py::test_list_args', 'sympy/utilities/tests/test_lambdify.py::test_nested_args', 'sympy/utilities/tests/test_lambdify.py::test_str_args', 'sympy/utilities/tests/test_lambdify.py::test_own_namespace_1', 'sympy/utilities/tests/test_lambdify.py::test_own_namespace_2', 'sympy/utilities/tests/test_lambdify.py::test_own_module', 'sympy/utilities/tests/test_lambdify.py::test_bad_args', 'sympy/utilities/tests/test_lambdify.py::test_atoms', 'sympy/utilities/tests/test_lambdify.py::test_sympy_lambda', 'sympy/utilities/tests/test_lambdify.py::test_math_lambda', 'sympy/utilities/tests/test_lambdify.py::test_mpmath_lambda', 'sympy/utilities/tests/test_lambdify.py::test_number_precision', 'sympy/utilities/tests/test_lambdify.py::test_mpmath_precision', 'sympy/utilities/tests/test_lambdify.py::test_math_transl', 'sympy/utilities/tests/test_lambdify.py::test_mpmath_transl', 'sympy/utilities/tests/test_lambdify.py::test_empty_modules', 'sympy/utilities/tests/test_lambdify.py::test_exponentiation', 'sympy/utilities/tests/test_lambdify.py::test_sqrt'])


def test_p2p_020():
    check(['sympy/utilities/tests/test_lambdify.py::test_curly_matrix_symbol', 'sympy/utilities/tests/test_lambdify.py::test_python_keywords', 'sympy/utilities/tests/test_lambdify.py::test_lambdify_docstring', 'sympy/utilities/tests/test_lambdify.py::test_special_printers', 'sympy/utilities/tests/test_lambdify.py::test_true_false', 'sympy/utilities/tests/test_lambdify.py::test_issue_2790', 'sympy/utilities/tests/test_lambdify.py::test_issue_12092', 'sympy/utilities/tests/test_lambdify.py::test_issue_14911', 'sympy/utilities/tests/test_lambdify.py::test_ITE', 'sympy/utilities/tests/test_lambdify.py::test_Min_Max', 'sympy/utilities/tests/test_lambdify.py::test_issue_12173', 'sympy/utilities/tests/test_lambdify.py::test_sinc_mpmath', 'sympy/utilities/tests/test_lambdify.py::test_lambdify_dummy_arg', 'sympy/utilities/tests/test_lambdify.py::test_lambdify_mixed_symbol_dummy_args', 'sympy/utilities/tests/test_lambdify.py::test_lambdify_inspect', 'sympy/utilities/tests/test_lambdify.py::test_lambdify_Derivative_arg_issue_16468', 'sympy/utilities/tests/test_lambdify.py::test_imag_real', 'sympy/utilities/tests/test_lambdify.py::test_single_e', 'sympy/utilities/tests/test_lambdify.py::test_beta_math', 'sympy/utilities/tests/test_lambdify.py::test_lambdify_cse'])
