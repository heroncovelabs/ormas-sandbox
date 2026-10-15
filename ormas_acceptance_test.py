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
    check(['sympy/core/tests/test_basic.py::test_immutable'])


def test_p2p_000():
    check(['sympy/core/tests/test_basic.py::test__aresame', 'sympy/core/tests/test_basic.py::test_structure', 'sympy/core/tests/test_basic.py::test_equality', 'sympy/core/tests/test_basic.py::test_matches_basic', 'sympy/core/tests/test_basic.py::test_has', 'sympy/core/tests/test_basic.py::test_subs', 'sympy/core/tests/test_basic.py::test_subs_with_unicode_symbols', 'sympy/core/tests/test_basic.py::test_atoms', 'sympy/core/tests/test_basic.py::test_free_symbols_empty', 'sympy/core/tests/test_basic.py::test_doit', 'sympy/core/tests/test_basic.py::test_S', 'sympy/core/tests/test_basic.py::test_xreplace', 'sympy/core/tests/test_basic.py::test_preorder_traversal', 'sympy/core/tests/test_basic.py::test_sorted_args', 'sympy/core/tests/test_basic.py::test_call', 'sympy/core/tests/test_basic.py::test_rewrite', 'sympy/core/tests/test_basic.py::test_literal_evalf_is_number_is_zero_is_comparable', 'sympy/core/tests/test_basic.py::test_as_Basic', 'sympy/core/tests/test_basic.py::test_atomic', 'sympy/core/tests/test_basic.py::test_as_dummy'])


def test_p2p_020():
    check(['sympy/core/tests/test_basic.py::test_canonical_variables'])
