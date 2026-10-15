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
    check(['sympy/physics/tests/test_secondquant.py::test_create'])


def test_f2p_001():
    check(['sympy/physics/tests/test_secondquant.py::test_commutation'])


def test_f2p_002():
    check(['sympy/physics/tests/test_secondquant.py::test_create_f'])


def test_f2p_003():
    check(['sympy/physics/tests/test_secondquant.py::test_NO'])


def test_f2p_004():
    check(['sympy/physics/tests/test_secondquant.py::test_Tensors'])


def test_f2p_005():
    check(['sympy/physics/tests/test_secondquant.py::test_issue_19661'])


def test_p2p_000():
    check(['sympy/physics/tests/test_secondquant.py::test_PermutationOperator', 'sympy/physics/tests/test_secondquant.py::test_index_permutations_with_dummies', 'sympy/physics/tests/test_secondquant.py::test_dagger', 'sympy/physics/tests/test_secondquant.py::test_operator', 'sympy/physics/tests/test_secondquant.py::test_annihilate', 'sympy/physics/tests/test_secondquant.py::test_basic_state', 'sympy/physics/tests/test_secondquant.py::test_basic_apply', 'sympy/physics/tests/test_secondquant.py::test_complex_apply', 'sympy/physics/tests/test_secondquant.py::test_number_operator', 'sympy/physics/tests/test_secondquant.py::test_inner_product', 'sympy/physics/tests/test_secondquant.py::test_symbolic_matrix_elements', 'sympy/physics/tests/test_secondquant.py::test_matrix_elements', 'sympy/physics/tests/test_secondquant.py::test_fixed_bosonic_basis', 'sympy/physics/tests/test_secondquant.py::test_annihilate_f', 'sympy/physics/tests/test_secondquant.py::test_create_b', 'sympy/physics/tests/test_secondquant.py::test_annihilate_b', 'sympy/physics/tests/test_secondquant.py::test_wicks', 'sympy/physics/tests/test_secondquant.py::test_sorting', 'sympy/physics/tests/test_secondquant.py::test_contraction', 'sympy/physics/tests/test_secondquant.py::test_evaluate_deltas'])


def test_p2p_020():
    check(['sympy/physics/tests/test_secondquant.py::test_substitute_dummies_substitution_order', 'sympy/physics/tests/test_secondquant.py::test_dummy_order_inner_outer_lines_VT1T1T1', 'sympy/physics/tests/test_secondquant.py::test_dummy_order_inner_outer_lines_VT1T1T1T1', 'sympy/physics/tests/test_secondquant.py::test_get_subNO', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT1T1', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT2conjT2', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT2conjT2_ambiguous_order', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT2', 'sympy/physics/tests/test_secondquant.py::test_internal_external_VT2T2', 'sympy/physics/tests/test_secondquant.py::test_internal_external_pqrs', 'sympy/physics/tests/test_secondquant.py::test_dummy_order_well_defined', 'sympy/physics/tests/test_secondquant.py::test_dummy_order_ambiguous', 'sympy/physics/tests/test_secondquant.py::test_dummy_order_inner_outer_lines_VT1T1T1_AT', 'sympy/physics/tests/test_secondquant.py::test_dummy_order_inner_outer_lines_VT1T1T1T1_AT', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT1T1_AT', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT2conjT2_AT', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT2conjT2_ambiguous_order_AT', 'sympy/physics/tests/test_secondquant.py::test_equivalent_internal_lines_VT2_AT', 'sympy/physics/tests/test_secondquant.py::test_internal_external_VT2T2_AT', 'sympy/physics/tests/test_secondquant.py::test_internal_external_pqrs_AT'])
