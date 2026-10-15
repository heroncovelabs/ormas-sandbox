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
    check(['sympy/utilities/tests/test_iterables.py::test_partitions'])


def test_f2p_001():
    check(['sympy/utilities/tests/test_iterables.py::test_uniq'])


def test_p2p_000():
    check(['sympy/utilities/tests/test_iterables.py::test_is_palindromic', 'sympy/utilities/tests/test_iterables.py::test_postorder_traversal', 'sympy/utilities/tests/test_iterables.py::test_flatten', 'sympy/utilities/tests/test_iterables.py::test_iproduct', 'sympy/utilities/tests/test_iterables.py::test_group', 'sympy/utilities/tests/test_iterables.py::test_subsets', 'sympy/utilities/tests/test_iterables.py::test_variations', 'sympy/utilities/tests/test_iterables.py::test_cartes', 'sympy/utilities/tests/test_iterables.py::test_filter_symbols', 'sympy/utilities/tests/test_iterables.py::test_numbered_symbols', 'sympy/utilities/tests/test_iterables.py::test_sift', 'sympy/utilities/tests/test_iterables.py::test_take', 'sympy/utilities/tests/test_iterables.py::test_dict_merge', 'sympy/utilities/tests/test_iterables.py::test_prefixes', 'sympy/utilities/tests/test_iterables.py::test_postfixes', 'sympy/utilities/tests/test_iterables.py::test_topological_sort', 'sympy/utilities/tests/test_iterables.py::test_strongly_connected_components', 'sympy/utilities/tests/test_iterables.py::test_connected_components', 'sympy/utilities/tests/test_iterables.py::test_rotate', 'sympy/utilities/tests/test_iterables.py::test_multiset_partitions'])


def test_p2p_020():
    check(['sympy/utilities/tests/test_iterables.py::test_multiset_combinations', 'sympy/utilities/tests/test_iterables.py::test_multiset_permutations', 'sympy/utilities/tests/test_iterables.py::test_binary_partitions', 'sympy/utilities/tests/test_iterables.py::test_bell_perm', 'sympy/utilities/tests/test_iterables.py::test_involutions', 'sympy/utilities/tests/test_iterables.py::test_derangements', 'sympy/utilities/tests/test_iterables.py::test_necklaces', 'sympy/utilities/tests/test_iterables.py::test_bracelets', 'sympy/utilities/tests/test_iterables.py::test_generate_oriented_forest', 'sympy/utilities/tests/test_iterables.py::test_unflatten', 'sympy/utilities/tests/test_iterables.py::test_common_prefix_suffix', 'sympy/utilities/tests/test_iterables.py::test_minlex', 'sympy/utilities/tests/test_iterables.py::test_ordered', 'sympy/utilities/tests/test_iterables.py::test_runs', 'sympy/utilities/tests/test_iterables.py::test_reshape', 'sympy/utilities/tests/test_iterables.py::test_kbins', 'sympy/utilities/tests/test_iterables.py::test_has_dups', 'sympy/utilities/tests/test_iterables.py::test__partition', 'sympy/utilities/tests/test_iterables.py::test_ordered_partitions', 'sympy/utilities/tests/test_iterables.py::test_rotations'])
