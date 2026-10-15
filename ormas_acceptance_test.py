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
    check(['sympy/functions/elementary/tests/test_miscellaneous.py::test_Min'])


def test_f2p_001():
    check(['sympy/functions/elementary/tests/test_miscellaneous.py::test_Max'])


def test_p2p_000():
    check(['sympy/functions/elementary/tests/test_miscellaneous.py::test_minmax_assumptions', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_issue_8413', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_root', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_real_root', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_rewrite_MaxMin_as_Heaviside', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_rewrite_MaxMin_as_Piecewise', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_issue_11099', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_issue_12638', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_instantiation_evaluation', 'sympy/functions/elementary/tests/test_miscellaneous.py::test_rewrite_as_Abs'])
