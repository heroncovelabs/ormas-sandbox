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
    check(['sympy/combinatorics/tests/test_perm_groups.py::test_sylow_subgroup'])


def test_p2p_000():
    check(['sympy/combinatorics/tests/test_perm_groups.py::test_has', 'sympy/combinatorics/tests/test_perm_groups.py::test_generate', 'sympy/combinatorics/tests/test_perm_groups.py::test_order', 'sympy/combinatorics/tests/test_perm_groups.py::test_equality', 'sympy/combinatorics/tests/test_perm_groups.py::test_stabilizer', 'sympy/combinatorics/tests/test_perm_groups.py::test_center', 'sympy/combinatorics/tests/test_perm_groups.py::test_centralizer', 'sympy/combinatorics/tests/test_perm_groups.py::test_coset_rank', 'sympy/combinatorics/tests/test_perm_groups.py::test_coset_factor', 'sympy/combinatorics/tests/test_perm_groups.py::test_orbits', 'sympy/combinatorics/tests/test_perm_groups.py::test_is_normal', 'sympy/combinatorics/tests/test_perm_groups.py::test_eq', 'sympy/combinatorics/tests/test_perm_groups.py::test_derived_subgroup', 'sympy/combinatorics/tests/test_perm_groups.py::test_is_solvable', 'sympy/combinatorics/tests/test_perm_groups.py::test_rubik1', 'sympy/combinatorics/tests/test_perm_groups.py::test_direct_product', 'sympy/combinatorics/tests/test_perm_groups.py::test_orbit_rep', 'sympy/combinatorics/tests/test_perm_groups.py::test_schreier_vector', 'sympy/combinatorics/tests/test_perm_groups.py::test_random_pr', 'sympy/combinatorics/tests/test_perm_groups.py::test_is_alt_sym'])


def test_p2p_020():
    check(['sympy/combinatorics/tests/test_perm_groups.py::test_pointwise_stabilizer', 'sympy/combinatorics/tests/test_perm_groups.py::test_make_perm', 'sympy/combinatorics/tests/test_perm_groups.py::test_elements', 'sympy/combinatorics/tests/test_perm_groups.py::test_is_group', 'sympy/combinatorics/tests/test_perm_groups.py::test_PermutationGroup', 'sympy/combinatorics/tests/test_perm_groups.py::test_coset_transvesal', 'sympy/combinatorics/tests/test_perm_groups.py::test_coset_table', 'sympy/combinatorics/tests/test_perm_groups.py::test_subgroup', 'sympy/combinatorics/tests/test_perm_groups.py::test_generator_product', 'sympy/combinatorics/tests/test_perm_groups.py::test_polycyclic', 'sympy/combinatorics/tests/test_perm_groups.py::test_elementary', 'sympy/combinatorics/tests/test_perm_groups.py::test_perfect', 'sympy/combinatorics/tests/test_perm_groups.py::test_index', 'sympy/combinatorics/tests/test_perm_groups.py::test_cyclic', 'sympy/combinatorics/tests/test_perm_groups.py::test_abelian_invariants', 'sympy/combinatorics/tests/test_perm_groups.py::test_composition_series', 'sympy/combinatorics/tests/test_perm_groups.py::test_is_symmetric', 'sympy/combinatorics/tests/test_perm_groups.py::test_conjugacy_class', 'sympy/combinatorics/tests/test_perm_groups.py::test_conjugacy_classes', 'sympy/combinatorics/tests/test_perm_groups.py::test_coset_class'])
