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
    check(['xarray/tests/test_computation.py::test_where_attrs'])


def test_p2p_000():
    check(['xarray/tests/test_computation.py::test_signature_properties', 'xarray/tests/test_computation.py::test_result_name', 'xarray/tests/test_computation.py::test_ordered_set_union', 'xarray/tests/test_computation.py::test_ordered_set_intersection', 'xarray/tests/test_computation.py::test_join_dict_keys', 'xarray/tests/test_computation.py::test_collect_dict_values', 'xarray/tests/test_computation.py::test_apply_identity', 'xarray/tests/test_computation.py::test_apply_two_inputs', 'xarray/tests/test_computation.py::test_apply_1d_and_0d', 'xarray/tests/test_computation.py::test_apply_two_outputs', 'xarray/tests/test_computation.py::test_apply_dask_parallelized_two_outputs', 'xarray/tests/test_computation.py::test_apply_input_core_dimension', 'xarray/tests/test_computation.py::test_apply_output_core_dimension', 'xarray/tests/test_computation.py::test_apply_exclude', 'xarray/tests/test_computation.py::test_apply_groupby_add', 'xarray/tests/test_computation.py::test_unified_dim_sizes', 'xarray/tests/test_computation.py::test_broadcast_compat_data_1d', 'xarray/tests/test_computation.py::test_broadcast_compat_data_2d', 'xarray/tests/test_computation.py::test_keep_attrs', 'xarray/tests/test_computation.py::test_keep_attrs_strategies_variable[default]'])


def test_p2p_020():
    check(['xarray/tests/test_computation.py::test_dot_align_coords[False]', 'xarray/tests/test_computation.py::test_where', 'xarray/tests/test_computation.py::test_polyval[True-True]', 'xarray/tests/test_computation.py::test_polyval[True-False]', 'xarray/tests/test_computation.py::test_polyval[False-True]', 'xarray/tests/test_computation.py::test_polyval[False-False]', 'xarray/tests/test_computation.py::test_cross[a0-b0-ae0-be0-dim_0--1-False]', 'xarray/tests/test_computation.py::test_cross[a0-b0-ae0-be0-dim_0--1-True]', 'xarray/tests/test_computation.py::test_cross[a1-b1-ae1-be1-dim_0--1-False]', 'xarray/tests/test_computation.py::test_cross[a1-b1-ae1-be1-dim_0--1-True]', 'xarray/tests/test_computation.py::test_cross[a2-b2-ae2-be2-dim_0--1-False]', 'xarray/tests/test_computation.py::test_cross[a2-b2-ae2-be2-dim_0--1-True]', 'xarray/tests/test_computation.py::test_cross[a3-b3-ae3-be3-dim_0--1-False]', 'xarray/tests/test_computation.py::test_cross[a3-b3-ae3-be3-dim_0--1-True]', 'xarray/tests/test_computation.py::test_cross[a4-b4-ae4-be4-cartesian-1-False]', 'xarray/tests/test_computation.py::test_cross[a4-b4-ae4-be4-cartesian-1-True]', 'xarray/tests/test_computation.py::test_cross[a5-b5-ae5-be5-cartesian--1-False]', 'xarray/tests/test_computation.py::test_cross[a5-b5-ae5-be5-cartesian--1-True]', 'xarray/tests/test_computation.py::test_cross[a6-b6-ae6-be6-cartesian--1-False]', 'xarray/tests/test_computation.py::test_cross[a6-b6-ae6-be6-cartesian--1-True]'])
