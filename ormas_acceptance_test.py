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
    check(['sympy/printing/tests/test_latex.py::test_latex_subs'])


def test_p2p_000():
    check(['sympy/printing/tests/test_latex.py::test_printmethod', 'sympy/printing/tests/test_latex.py::test_latex_basic', 'sympy/printing/tests/test_latex.py::test_latex_builtins', 'sympy/printing/tests/test_latex.py::test_latex_SingularityFunction', 'sympy/printing/tests/test_latex.py::test_latex_cycle', 'sympy/printing/tests/test_latex.py::test_latex_permutation', 'sympy/printing/tests/test_latex.py::test_latex_Float', 'sympy/printing/tests/test_latex.py::test_latex_vector_expressions', 'sympy/printing/tests/test_latex.py::test_latex_symbols', 'sympy/printing/tests/test_latex.py::test_latex_functions', 'sympy/printing/tests/test_latex.py::test_function_subclass_different_name', 'sympy/printing/tests/test_latex.py::test_hyper_printing', 'sympy/printing/tests/test_latex.py::test_latex_bessel', 'sympy/printing/tests/test_latex.py::test_latex_fresnel', 'sympy/printing/tests/test_latex.py::test_latex_brackets', 'sympy/printing/tests/test_latex.py::test_latex_indexed', 'sympy/printing/tests/test_latex.py::test_latex_derivatives', 'sympy/printing/tests/test_latex.py::test_latex_integrals', 'sympy/printing/tests/test_latex.py::test_latex_sets', 'sympy/printing/tests/test_latex.py::test_latex_SetExpr'])


def test_p2p_020():
    check(['sympy/printing/tests/test_latex.py::test_MatrixElement_printing', 'sympy/printing/tests/test_latex.py::test_MatrixSymbol_printing', 'sympy/printing/tests/test_latex.py::test_KroneckerProduct_printing', 'sympy/printing/tests/test_latex.py::test_Quaternion_latex_printing', 'sympy/printing/tests/test_latex.py::test_TensorProduct_printing', 'sympy/printing/tests/test_latex.py::test_WedgeProduct_printing', 'sympy/printing/tests/test_latex.py::test_issue_14041', 'sympy/printing/tests/test_latex.py::test_issue_9216', 'sympy/printing/tests/test_latex.py::test_latex_printer_tensor', 'sympy/printing/tests/test_latex.py::test_multiline_latex', 'sympy/printing/tests/test_latex.py::test_issue_15353', 'sympy/printing/tests/test_latex.py::test_trace', 'sympy/printing/tests/test_latex.py::test_print_basic', 'sympy/printing/tests/test_latex.py::test_MatrixSymbol_bold', 'sympy/printing/tests/test_latex.py::test_imaginary_unit', 'sympy/printing/tests/test_latex.py::test_text_re_im', 'sympy/printing/tests/test_latex.py::test_DiffGeomMethods', 'sympy/printing/tests/test_latex.py::test_unit_printing', 'sympy/printing/tests/test_latex.py::test_issue_17092', 'sympy/printing/tests/test_latex.py::test_latex_decimal_separator'])
