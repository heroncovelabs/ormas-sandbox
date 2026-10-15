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
    check(['sympy/core/tests/test_arit.py::test_Add_is_zero'])


def test_p2p_000():
    check(['sympy/core/tests/test_arit.py::test_bug1', 'sympy/core/tests/test_arit.py::test_Symbol', 'sympy/core/tests/test_arit.py::test_arit0', 'sympy/core/tests/test_arit.py::test_div', 'sympy/core/tests/test_arit.py::test_pow', 'sympy/core/tests/test_arit.py::test_pow2', 'sympy/core/tests/test_arit.py::test_pow3', 'sympy/core/tests/test_arit.py::test_mod_pow', 'sympy/core/tests/test_arit.py::test_pow_E', 'sympy/core/tests/test_arit.py::test_pow_issue_3516', 'sympy/core/tests/test_arit.py::test_pow_im', 'sympy/core/tests/test_arit.py::test_real_mul', 'sympy/core/tests/test_arit.py::test_ncmul', 'sympy/core/tests/test_arit.py::test_ncpow', 'sympy/core/tests/test_arit.py::test_powerbug', 'sympy/core/tests/test_arit.py::test_Mul_doesnt_expand_exp', 'sympy/core/tests/test_arit.py::test_Add_Mul_is_integer', 'sympy/core/tests/test_arit.py::test_Add_Mul_is_finite', 'sympy/core/tests/test_arit.py::test_Mul_is_even_odd', 'sympy/core/tests/test_arit.py::test_evenness_in_ternary_integer_product_with_even'])


def test_p2p_020():
    check(['sympy/core/tests/test_arit.py::test_Mod_is_integer', 'sympy/core/tests/test_arit.py::test_Mod_is_nonposneg', 'sympy/core/tests/test_arit.py::test_issue_6001', 'sympy/core/tests/test_arit.py::test_polar', 'sympy/core/tests/test_arit.py::test_issue_6040', 'sympy/core/tests/test_arit.py::test_issue_6082', 'sympy/core/tests/test_arit.py::test_issue_6077', 'sympy/core/tests/test_arit.py::test_mul_flatten_oo', 'sympy/core/tests/test_arit.py::test_add_flatten', 'sympy/core/tests/test_arit.py::test_issue_5160_6087_6089_6090', 'sympy/core/tests/test_arit.py::test_float_int', 'sympy/core/tests/test_arit.py::test_issue_6611a', 'sympy/core/tests/test_arit.py::test_denest_add_mul', 'sympy/core/tests/test_arit.py::test_mul_coeff', 'sympy/core/tests/test_arit.py::test_mul_zero_detection', 'sympy/core/tests/test_arit.py::test_Mul_with_zero_infinite', 'sympy/core/tests/test_arit.py::test_Mul_does_not_cancel_infinities', 'sympy/core/tests/test_arit.py::test_Mul_does_not_distribute_infinity', 'sympy/core/tests/test_arit.py::test_issue_8247_8354', 'sympy/core/tests/test_arit.py::test_issue_14392'])
