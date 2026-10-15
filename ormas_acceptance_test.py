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
    check(['sympy/simplify/tests/test_fu.py::test__TR56'])


def test_f2p_001():
    check(['sympy/simplify/tests/test_simplify.py::test_issue_17137'])


def test_p2p_000():
    check(['sympy/simplify/tests/test_fu.py::test_TR1', 'sympy/simplify/tests/test_fu.py::test_TR2', 'sympy/simplify/tests/test_fu.py::test_TR2i', 'sympy/simplify/tests/test_fu.py::test_TR3', 'sympy/simplify/tests/test_fu.py::test_TR5', 'sympy/simplify/tests/test_fu.py::test_TR6', 'sympy/simplify/tests/test_fu.py::test_TR7', 'sympy/simplify/tests/test_fu.py::test_TR8', 'sympy/simplify/tests/test_fu.py::test_TR9', 'sympy/simplify/tests/test_fu.py::test_TR10', 'sympy/simplify/tests/test_fu.py::test_TR10i', 'sympy/simplify/tests/test_fu.py::test_TR11', 'sympy/simplify/tests/test_fu.py::test_TR12', 'sympy/simplify/tests/test_fu.py::test_TR13', 'sympy/simplify/tests/test_fu.py::test_L', 'sympy/simplify/tests/test_fu.py::test_fu', 'sympy/simplify/tests/test_fu.py::test_objective', 'sympy/simplify/tests/test_fu.py::test_process_common_addends', 'sympy/simplify/tests/test_fu.py::test_trig_split', 'sympy/simplify/tests/test_fu.py::test_TRmorrie'])


def test_p2p_020():
    check(['sympy/simplify/tests/test_simplify.py::test_issue_5950', 'sympy/simplify/tests/test_simplify.py::test_posify', 'sympy/simplify/tests/test_simplify.py::test_issue_4194', 'sympy/simplify/tests/test_simplify.py::test_as_content_primitive', 'sympy/simplify/tests/test_simplify.py::test_signsimp', 'sympy/simplify/tests/test_simplify.py::test_besselsimp', 'sympy/simplify/tests/test_simplify.py::test_Piecewise', 'sympy/simplify/tests/test_simplify.py::test_polymorphism', 'sympy/simplify/tests/test_simplify.py::test_issue_from_PR1599', 'sympy/simplify/tests/test_simplify.py::test_issue_6811', 'sympy/simplify/tests/test_simplify.py::test_issue_6920', 'sympy/simplify/tests/test_simplify.py::test_issue_7001', 'sympy/simplify/tests/test_simplify.py::test_inequality_no_auto_simplify', 'sympy/simplify/tests/test_simplify.py::test_issue_9398', 'sympy/simplify/tests/test_simplify.py::test_issue_9324_simplify', 'sympy/simplify/tests/test_simplify.py::test_issue_13474', 'sympy/simplify/tests/test_simplify.py::test_simplify_function_inverse', 'sympy/simplify/tests/test_simplify.py::test_clear_coefficients', 'sympy/simplify/tests/test_simplify.py::test_nc_simplify', 'sympy/simplify/tests/test_simplify.py::test_issue_15965'])
