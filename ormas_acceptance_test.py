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
    check(['xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-3-True-1]'])


def test_f2p_001():
    check(['xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-3-True-2]'])


def test_f2p_002():
    check(['xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-7-True-1]'])


def test_p2p_000():
    check(['xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-1-True-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-1-True-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-1-False-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-1-False-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-2-True-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-2-True-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-2-False-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-2-False-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-3-False-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-3-False-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-7-True-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-7-False-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[numpy-7-False-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-1-True-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-1-True-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-1-False-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-1-False-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-2-True-1]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-2-True-2]', 'xarray/tests/test_rolling.py::TestDataArrayRolling::test_rolling_iter[dask-2-False-1]'])


def test_p2p_020():
    check(['xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_reduce[dask-False-sum-1-True-2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_reduce[dask-False-sum-1-False-2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_reduce[dask-False-max-None-True-2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_reduce[dask-False-max-None-False-2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_reduce[dask-False-max-1-True-2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_reduce[dask-False-max-1-False-2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[True-nan-True]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[True-nan-False]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[True-nan-center2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[True-0.0-True]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[True-0.0-False]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[True-0.0-center2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[False-nan-True]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[False-nan-False]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[False-nan-center2]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[False-0.0-True]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[False-0.0-False]', 'xarray/tests/test_rolling.py::TestDatasetRolling::test_ndrolling_construct[False-0.0-center2]', 'xarray/tests/test_rolling.py::TestDatasetRollingExp::test_rolling_exp[1-numpy]', 'xarray/tests/test_rolling.py::TestDatasetRollingExp::test_rolling_exp_keep_attrs[1-numpy]'])
