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
    check(['sympy/core/tests/test_symbol.py::test_symbols'])


def test_p2p_000():
    check(['sympy/core/tests/test_symbol.py::test_Str', 'sympy/core/tests/test_symbol.py::test_Symbol', 'sympy/core/tests/test_symbol.py::test_Dummy', 'sympy/core/tests/test_symbol.py::test_Dummy_force_dummy_index', 'sympy/core/tests/test_symbol.py::test_lt_gt', 'sympy/core/tests/test_symbol.py::test_no_len', 'sympy/core/tests/test_symbol.py::test_ineq_unequal', 'sympy/core/tests/test_symbol.py::test_Wild_properties', 'sympy/core/tests/test_symbol.py::test_symbols_become_functions_issue_3539', 'sympy/core/tests/test_symbol.py::test_unicode', 'sympy/core/tests/test_symbol.py::test_uniquely_named_symbol_and_Symbol'])
