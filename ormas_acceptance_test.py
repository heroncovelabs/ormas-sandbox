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
    check(['sympy/sets/tests/test_conditionset.py::test_subs_CondSet'])


def test_p2p_000():
    check(['sympy/sets/tests/test_conditionset.py::test_CondSet', 'sympy/sets/tests/test_conditionset.py::test_CondSet_intersect', 'sympy/sets/tests/test_conditionset.py::test_issue_9849', 'sympy/sets/tests/test_conditionset.py::test_simplified_FiniteSet_in_CondSet', 'sympy/sets/tests/test_conditionset.py::test_free_symbols', 'sympy/sets/tests/test_conditionset.py::test_subs_CondSet_tebr', 'sympy/sets/tests/test_conditionset.py::test_dummy_eq', 'sympy/sets/tests/test_conditionset.py::test_contains'])
