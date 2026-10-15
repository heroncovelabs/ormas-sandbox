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
    check(['sympy/printing/tests/test_pycode.py::test_MpmathPrinter'])


def test_p2p_000():
    check(['sympy/printing/tests/test_pycode.py::test_PythonCodePrinter', 'sympy/printing/tests/test_pycode.py::test_NumPyPrinter', 'sympy/printing/tests/test_pycode.py::test_SciPyPrinter', 'sympy/printing/tests/test_pycode.py::test_pycode_reserved_words', 'sympy/printing/tests/test_pycode.py::test_printmethod', 'sympy/printing/tests/test_pycode.py::test_codegen_ast_nodes', 'sympy/solvers/tests/test_numeric.py::test_nsolve_denominator', 'sympy/solvers/tests/test_numeric.py::test_nsolve', 'sympy/solvers/tests/test_numeric.py::test_issue_6408', 'sympy/solvers/tests/test_numeric.py::test_increased_dps', 'sympy/solvers/tests/test_numeric.py::test_nsolve_precision', 'sympy/solvers/tests/test_numeric.py::test_nsolve_complex', 'sympy/solvers/tests/test_numeric.py::test_nsolve_dict_kwarg'])
