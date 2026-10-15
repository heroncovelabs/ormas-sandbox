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
    check(['sympy/simplify/tests/test_simplify.py::test_posify'])


def test_p2p_000():
    check(['sympy/simplify/tests/test_simplify.py::test_issue_7263', 'sympy/simplify/tests/test_simplify.py::test_issue_3557', 'sympy/simplify/tests/test_simplify.py::test_simplify_other', 'sympy/simplify/tests/test_simplify.py::test_simplify_complex', 'sympy/simplify/tests/test_simplify.py::test_simplify_ratio', 'sympy/simplify/tests/test_simplify.py::test_simplify_measure', 'sympy/simplify/tests/test_simplify.py::test_simplify_rational', 'sympy/simplify/tests/test_simplify.py::test_simplify_issue_1308', 'sympy/simplify/tests/test_simplify.py::test_issue_5652', 'sympy/simplify/tests/test_simplify.py::test_simplify_fail1', 'sympy/simplify/tests/test_simplify.py::test_nthroot', 'sympy/simplify/tests/test_simplify.py::test_nthroot1', 'sympy/simplify/tests/test_simplify.py::test_separatevars', 'sympy/simplify/tests/test_simplify.py::test_separatevars_advanced_factor', 'sympy/simplify/tests/test_simplify.py::test_hypersimp', 'sympy/simplify/tests/test_simplify.py::test_nsimplify', 'sympy/simplify/tests/test_simplify.py::test_issue_9448', 'sympy/simplify/tests/test_simplify.py::test_extract_minus_sign', 'sympy/simplify/tests/test_simplify.py::test_diff', 'sympy/simplify/tests/test_simplify.py::test_logcombine_1'])


def test_p2p_020():
    check(['sympy/simplify/tests/test_simplify.py::test_logcombine_complex_coeff', 'sympy/simplify/tests/test_simplify.py::test_issue_5950', 'sympy/simplify/tests/test_simplify.py::test_issue_4194', 'sympy/simplify/tests/test_simplify.py::test_as_content_primitive', 'sympy/simplify/tests/test_simplify.py::test_signsimp', 'sympy/simplify/tests/test_simplify.py::test_besselsimp', 'sympy/simplify/tests/test_simplify.py::test_Piecewise', 'sympy/simplify/tests/test_simplify.py::test_polymorphism', 'sympy/simplify/tests/test_simplify.py::test_issue_from_PR1599', 'sympy/simplify/tests/test_simplify.py::test_issue_6811', 'sympy/simplify/tests/test_simplify.py::test_issue_6920', 'sympy/simplify/tests/test_simplify.py::test_issue_7001', 'sympy/simplify/tests/test_simplify.py::test_inequality_no_auto_simplify', 'sympy/simplify/tests/test_simplify.py::test_issue_9398', 'sympy/simplify/tests/test_simplify.py::test_issue_9324_simplify', 'sympy/simplify/tests/test_simplify.py::test_issue_13474', 'sympy/simplify/tests/test_simplify.py::test_simplify_function_inverse', 'sympy/simplify/tests/test_simplify.py::test_clear_coefficients'])
