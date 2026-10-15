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
    check(['sympy/physics/units/tests/test_quantities.py::test_issue_24211'])


def test_p2p_000():
    check(['sympy/physics/units/tests/test_quantities.py::test_str_repr', 'sympy/physics/units/tests/test_quantities.py::test_eq', 'sympy/physics/units/tests/test_quantities.py::test_convert_to', 'sympy/physics/units/tests/test_quantities.py::test_Quantity_definition', 'sympy/physics/units/tests/test_quantities.py::test_abbrev', 'sympy/physics/units/tests/test_quantities.py::test_print', 'sympy/physics/units/tests/test_quantities.py::test_Quantity_eq', 'sympy/physics/units/tests/test_quantities.py::test_add_sub', 'sympy/physics/units/tests/test_quantities.py::test_quantity_abs', 'sympy/physics/units/tests/test_quantities.py::test_check_unit_consistency', 'sympy/physics/units/tests/test_quantities.py::test_mul_div', 'sympy/physics/units/tests/test_quantities.py::test_units', 'sympy/physics/units/tests/test_quantities.py::test_issue_quart', 'sympy/physics/units/tests/test_quantities.py::test_issue_5565', 'sympy/physics/units/tests/test_quantities.py::test_find_unit', 'sympy/physics/units/tests/test_quantities.py::test_Quantity_derivative', 'sympy/physics/units/tests/test_quantities.py::test_quantity_postprocessing', 'sympy/physics/units/tests/test_quantities.py::test_factor_and_dimension', 'sympy/physics/units/tests/test_quantities.py::test_dimensional_expr_of_derivative', 'sympy/physics/units/tests/test_quantities.py::test_get_dimensional_expr_with_function'])


def test_p2p_020():
    check(['sympy/physics/units/tests/test_quantities.py::test_binary_information', 'sympy/physics/units/tests/test_quantities.py::test_conversion_with_2_nonstandard_dimensions', 'sympy/physics/units/tests/test_quantities.py::test_eval_subs', 'sympy/physics/units/tests/test_quantities.py::test_issue_14932', 'sympy/physics/units/tests/test_quantities.py::test_issue_14547', 'sympy/physics/units/tests/test_quantities.py::test_deprecated_quantity_methods', 'sympy/physics/units/tests/test_quantities.py::test_issue_22164', 'sympy/physics/units/tests/test_quantities.py::test_issue_22819', 'sympy/physics/units/tests/test_quantities.py::test_issue_20288', 'sympy/physics/units/tests/test_quantities.py::test_issue_24062', 'sympy/physics/units/tests/test_quantities.py::test_prefixed_property'])
