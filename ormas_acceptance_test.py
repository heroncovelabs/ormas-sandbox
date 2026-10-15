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
    check(['sympy/solvers/tests/test_diophantine.py::test_diophantine'])


def test_p2p_000():
    check(['sympy/solvers/tests/test_diophantine.py::test_input_format', 'sympy/solvers/tests/test_diophantine.py::test_univariate', 'sympy/solvers/tests/test_diophantine.py::test_classify_diop', 'sympy/solvers/tests/test_diophantine.py::test_linear', 'sympy/solvers/tests/test_diophantine.py::test_quadratic_simple_hyperbolic_case', 'sympy/solvers/tests/test_diophantine.py::test_quadratic_elliptical_case', 'sympy/solvers/tests/test_diophantine.py::test_quadratic_parabolic_case', 'sympy/solvers/tests/test_diophantine.py::test_quadratic_perfect_square', 'sympy/solvers/tests/test_diophantine.py::test_quadratic_non_perfect_square', 'sympy/solvers/tests/test_diophantine.py::test_issue_9106', 'sympy/solvers/tests/test_diophantine.py::test_issue_18138', 'sympy/solvers/tests/test_diophantine.py::test_DN', 'sympy/solvers/tests/test_diophantine.py::test_bf_pell', 'sympy/solvers/tests/test_diophantine.py::test_length', 'sympy/solvers/tests/test_diophantine.py::test_transformation_to_pell', 'sympy/solvers/tests/test_diophantine.py::test_find_DN', 'sympy/solvers/tests/test_diophantine.py::test_ldescent', 'sympy/solvers/tests/test_diophantine.py::test_diop_ternary_quadratic_normal', 'sympy/solvers/tests/test_diophantine.py::test_transformation_to_normal', 'sympy/solvers/tests/test_diophantine.py::test_diop_ternary_quadratic'])


def test_p2p_020():
    check(['sympy/solvers/tests/test_diophantine.py::test_parametrize_ternary_quadratic', 'sympy/solvers/tests/test_diophantine.py::test_no_square_ternary_quadratic', 'sympy/solvers/tests/test_diophantine.py::test_descent', 'sympy/solvers/tests/test_diophantine.py::test_general_pythagorean', 'sympy/solvers/tests/test_diophantine.py::test_diop_general_sum_of_squares_quick', 'sympy/solvers/tests/test_diophantine.py::test_diop_partition', 'sympy/solvers/tests/test_diophantine.py::test_prime_as_sum_of_two_squares', 'sympy/solvers/tests/test_diophantine.py::test_sum_of_three_squares', 'sympy/solvers/tests/test_diophantine.py::test_sum_of_four_squares', 'sympy/solvers/tests/test_diophantine.py::test_power_representation', 'sympy/solvers/tests/test_diophantine.py::test_assumptions', 'sympy/solvers/tests/test_diophantine.py::test_diopcoverage', 'sympy/solvers/tests/test_diophantine.py::test_holzer', 'sympy/solvers/tests/test_diophantine.py::test_issue_9539', 'sympy/solvers/tests/test_diophantine.py::test_issue_8943', 'sympy/solvers/tests/test_diophantine.py::test_diop_sum_of_even_powers', 'sympy/solvers/tests/test_diophantine.py::test_sum_of_squares_powers', 'sympy/solvers/tests/test_diophantine.py::test__can_do_sum_of_squares', 'sympy/solvers/tests/test_diophantine.py::test_diophantine_permute_sign', 'sympy/solvers/tests/test_diophantine.py::test_issue_9538'])
