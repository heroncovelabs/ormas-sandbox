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
    check(['sympy/utilities/tests/test_codegen.py::test_ccode_unused_array_arg'])


def test_p2p_000():
    check(['sympy/utilities/tests/test_codegen.py::test_Routine_argument_order', 'sympy/utilities/tests/test_codegen.py::test_empty_c_code', 'sympy/utilities/tests/test_codegen.py::test_empty_c_code_with_comment', 'sympy/utilities/tests/test_codegen.py::test_empty_c_header', 'sympy/utilities/tests/test_codegen.py::test_simple_c_code', 'sympy/utilities/tests/test_codegen.py::test_c_code_reserved_words', 'sympy/utilities/tests/test_codegen.py::test_numbersymbol_c_code', 'sympy/utilities/tests/test_codegen.py::test_c_code_argument_order', 'sympy/utilities/tests/test_codegen.py::test_simple_c_header', 'sympy/utilities/tests/test_codegen.py::test_simple_c_codegen', 'sympy/utilities/tests/test_codegen.py::test_multiple_results_c', 'sympy/utilities/tests/test_codegen.py::test_no_results_c', 'sympy/utilities/tests/test_codegen.py::test_ansi_math1_codegen', 'sympy/utilities/tests/test_codegen.py::test_ansi_math2_codegen', 'sympy/utilities/tests/test_codegen.py::test_complicated_codegen', 'sympy/utilities/tests/test_codegen.py::test_loops_c', 'sympy/utilities/tests/test_codegen.py::test_dummy_loops_c', 'sympy/utilities/tests/test_codegen.py::test_partial_loops_c', 'sympy/utilities/tests/test_codegen.py::test_output_arg_c', 'sympy/utilities/tests/test_codegen.py::test_output_arg_c_reserved_words'])


def test_p2p_020():
    check(['sympy/utilities/tests/test_codegen.py::test_intrinsic_math_codegen', 'sympy/utilities/tests/test_codegen.py::test_intrinsic_math2_codegen', 'sympy/utilities/tests/test_codegen.py::test_complicated_codegen_f95', 'sympy/utilities/tests/test_codegen.py::test_loops', 'sympy/utilities/tests/test_codegen.py::test_dummy_loops_f95', 'sympy/utilities/tests/test_codegen.py::test_loops_InOut', 'sympy/utilities/tests/test_codegen.py::test_partial_loops_f', 'sympy/utilities/tests/test_codegen.py::test_output_arg_f', 'sympy/utilities/tests/test_codegen.py::test_inline_function', 'sympy/utilities/tests/test_codegen.py::test_f_code_call_signature_wrap', 'sympy/utilities/tests/test_codegen.py::test_check_case', 'sympy/utilities/tests/test_codegen.py::test_check_case_false_positive', 'sympy/utilities/tests/test_codegen.py::test_c_fortran_omit_routine_name', 'sympy/utilities/tests/test_codegen.py::test_fcode_matrix_output', 'sympy/utilities/tests/test_codegen.py::test_fcode_results_named_ordered', 'sympy/utilities/tests/test_codegen.py::test_fcode_matrixsymbol_slice', 'sympy/utilities/tests/test_codegen.py::test_fcode_matrixsymbol_slice_autoname', 'sympy/utilities/tests/test_codegen.py::test_global_vars', 'sympy/utilities/tests/test_codegen.py::test_custom_codegen', 'sympy/utilities/tests/test_codegen.py::test_c_with_printer'])
