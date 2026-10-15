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
    check(['sympy/tensor/array/tests/test_immutable_ndim_array.py::test_ndim_array_initiation'])


def test_p2p_000():
    check(['sympy/tensor/array/tests/test_immutable_ndim_array.py::test_reshape', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_iterator', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_sparse', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_calculation', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_ndim_array_converting', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_converting_functions', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_equality', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_arithmetic', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_higher_dimenions', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_rebuild_immutable_arrays', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_slices', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_diff_and_applyfunc', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_op_priority', 'sympy/tensor/array/tests/test_immutable_ndim_array.py::test_symbolic_indexing'])
