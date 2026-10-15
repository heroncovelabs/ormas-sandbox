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
    check(['xarray/tests/test_coarsen.py::TestCoarsenConstruct::test_coarsen_construct_keeps_all_coords'])


def test_p2p_000():
    check(['xarray/tests/test_coarsen.py::test_coarsen_absent_dims_error[1-numpy]', 'xarray/tests/test_coarsen.py::test_coarsen_absent_dims_error[1-dask]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-numpy-trim-left-True]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-numpy-trim-left-False]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-numpy-pad-right-True]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-numpy-pad-right-False]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-dask-trim-left-True]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-dask-trim-left-False]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-dask-pad-right-True]', 'xarray/tests/test_coarsen.py::test_coarsen_dataset[1-dask-pad-right-False]', 'xarray/tests/test_coarsen.py::test_coarsen_coords[1-numpy-True]', 'xarray/tests/test_coarsen.py::test_coarsen_coords[1-numpy-False]', 'xarray/tests/test_coarsen.py::test_coarsen_coords[1-dask-True]', 'xarray/tests/test_coarsen.py::test_coarsen_coords[1-dask-False]', 'xarray/tests/test_coarsen.py::test_coarsen_coords_cftime', 'xarray/tests/test_coarsen.py::test_coarsen_keep_attrs[reduce-argument0]', 'xarray/tests/test_coarsen.py::test_coarsen_keep_attrs[mean-argument1]', 'xarray/tests/test_coarsen.py::test_coarsen_reduce[numpy-sum-1-1]', 'xarray/tests/test_coarsen.py::test_coarsen_reduce[numpy-sum-1-2]', 'xarray/tests/test_coarsen.py::test_coarsen_reduce[numpy-sum-2-1]'])


def test_p2p_020():
    check(['xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-mean-3-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-mean-3-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-mean-4-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-mean-4-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-1-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-2-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-2-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-3-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-3-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-4-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-std-4-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-1-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-2-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-2-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-3-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-3-2]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-4-1]', 'xarray/tests/test_coarsen.py::test_coarsen_da_reduce[dask-max-4-2]', 'xarray/tests/test_coarsen.py::TestCoarsenConstruct::test_coarsen_construct[True]', 'xarray/tests/test_coarsen.py::TestCoarsenConstruct::test_coarsen_construct[False]'])
