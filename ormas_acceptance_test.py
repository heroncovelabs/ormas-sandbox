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
    check(['sympy/printing/tests/test_mathml.py::test_presentation_symbol'])


def test_p2p_000():
    check(['sympy/printing/tests/test_mathml.py::test_mathml_printer', 'sympy/printing/tests/test_mathml.py::test_content_printmethod', 'sympy/printing/tests/test_mathml.py::test_content_mathml_core', 'sympy/printing/tests/test_mathml.py::test_content_mathml_functions', 'sympy/printing/tests/test_mathml.py::test_content_mathml_limits', 'sympy/printing/tests/test_mathml.py::test_content_mathml_integrals', 'sympy/printing/tests/test_mathml.py::test_content_mathml_matrices', 'sympy/printing/tests/test_mathml.py::test_content_mathml_sums', 'sympy/printing/tests/test_mathml.py::test_content_mathml_tuples', 'sympy/printing/tests/test_mathml.py::test_content_mathml_add', 'sympy/printing/tests/test_mathml.py::test_content_mathml_Rational', 'sympy/printing/tests/test_mathml.py::test_content_mathml_constants', 'sympy/printing/tests/test_mathml.py::test_content_mathml_trig', 'sympy/printing/tests/test_mathml.py::test_content_mathml_relational', 'sympy/printing/tests/test_mathml.py::test_content_symbol', 'sympy/printing/tests/test_mathml.py::test_content_mathml_greek', 'sympy/printing/tests/test_mathml.py::test_content_mathml_order', 'sympy/printing/tests/test_mathml.py::test_content_settings', 'sympy/printing/tests/test_mathml.py::test_presentation_printmethod', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_core'])


def test_p2p_020():
    check(['sympy/printing/tests/test_mathml.py::test_presentation_mathml_functions', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_limits', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_integrals', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_matrices', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_sums', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_add', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_Rational', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_constants', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_trig', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_relational', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_greek', 'sympy/printing/tests/test_mathml.py::test_presentation_mathml_order', 'sympy/printing/tests/test_mathml.py::test_presentation_settings', 'sympy/printing/tests/test_mathml.py::test_toprettyxml_hooking', 'sympy/printing/tests/test_mathml.py::test_print_basic', 'sympy/printing/tests/test_mathml.py::test_root_notation_print', 'sympy/printing/tests/test_mathml.py::test_print_matrix_symbol'])
