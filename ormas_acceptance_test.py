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
    check(['sympy/physics/quantum/tests/test_dagger.py::test_dagger_mul'])


def test_f2p_001():
    check(['sympy/physics/quantum/tests/test_operator.py::test_identity'])


def test_p2p_000():
    check(['sympy/physics/quantum/tests/test_dagger.py::test_scalars', 'sympy/physics/quantum/tests/test_dagger.py::test_matrix', 'sympy/physics/quantum/tests/test_dagger.py::test_eval_adjoint', 'sympy/physics/quantum/tests/test_operator.py::test_operator', 'sympy/physics/quantum/tests/test_operator.py::test_operator_inv', 'sympy/physics/quantum/tests/test_operator.py::test_hermitian', 'sympy/physics/quantum/tests/test_operator.py::test_unitary', 'sympy/physics/quantum/tests/test_operator.py::test_outer_product', 'sympy/physics/quantum/tests/test_operator.py::test_operator_dagger'])
