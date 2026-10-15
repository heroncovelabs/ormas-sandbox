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
    check(['sympy/codegen/tests/test_ast.py::test_String'])


def test_p2p_000():
    check(['sympy/codegen/tests/test_ast.py::test_Assignment', 'sympy/codegen/tests/test_ast.py::test_AugAssign', 'sympy/codegen/tests/test_ast.py::test_Assignment_printing', 'sympy/codegen/tests/test_ast.py::test_CodeBlock', 'sympy/codegen/tests/test_ast.py::test_CodeBlock_topological_sort', 'sympy/codegen/tests/test_ast.py::test_CodeBlock_free_symbols', 'sympy/codegen/tests/test_ast.py::test_CodeBlock_cse', 'sympy/codegen/tests/test_ast.py::test_CodeBlock_cse__issue_14118', 'sympy/codegen/tests/test_ast.py::test_For', 'sympy/codegen/tests/test_ast.py::test_none', 'sympy/codegen/tests/test_ast.py::test_Comment', 'sympy/codegen/tests/test_ast.py::test_Node', 'sympy/codegen/tests/test_ast.py::test_Type', 'sympy/codegen/tests/test_ast.py::test_Type__from_expr', 'sympy/codegen/tests/test_ast.py::test_Type__cast_check__integers', 'sympy/codegen/tests/test_ast.py::test_Attribute', 'sympy/codegen/tests/test_ast.py::test_Variable', 'sympy/codegen/tests/test_ast.py::test_Pointer', 'sympy/codegen/tests/test_ast.py::test_Declaration', 'sympy/codegen/tests/test_ast.py::test_IntBaseType'])


def test_p2p_020():
    check(['sympy/codegen/tests/test_ast.py::test_FloatType', 'sympy/codegen/tests/test_ast.py::test_Type__cast_check__floating_point', 'sympy/codegen/tests/test_ast.py::test_Type__cast_check__complex_floating_point', 'sympy/codegen/tests/test_ast.py::test_While', 'sympy/codegen/tests/test_ast.py::test_Scope', 'sympy/codegen/tests/test_ast.py::test_Print', 'sympy/codegen/tests/test_ast.py::test_FunctionPrototype_and_FunctionDefinition', 'sympy/codegen/tests/test_ast.py::test_Return', 'sympy/codegen/tests/test_ast.py::test_FunctionCall'])
