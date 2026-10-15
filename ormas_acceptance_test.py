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
    check(['sympy/simplify/tests/test_sqrtdenest.py::test_issue_12420'])


def test_p2p_000():
    check(['sympy/simplify/tests/test_sqrtdenest.py::test_sqrtdenest', 'sympy/simplify/tests/test_sqrtdenest.py::test_sqrtdenest2', 'sympy/simplify/tests/test_sqrtdenest.py::test_sqrtdenest_rec', 'sympy/simplify/tests/test_sqrtdenest.py::test_issue_6241', 'sympy/simplify/tests/test_sqrtdenest.py::test_sqrtdenest3', 'sympy/simplify/tests/test_sqrtdenest.py::test_sqrtdenest4', 'sympy/simplify/tests/test_sqrtdenest.py::test_sqrt_symbolic_denest', 'sympy/simplify/tests/test_sqrtdenest.py::test_issue_5857', 'sympy/simplify/tests/test_sqrtdenest.py::test_subsets', 'sympy/simplify/tests/test_sqrtdenest.py::test_issue_5653'])
