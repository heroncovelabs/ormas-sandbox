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
    check(['sympy/geometry/tests/test_point.py::test_issue_22684'])


def test_p2p_000():
    check(['sympy/geometry/tests/test_point.py::test_point', 'sympy/geometry/tests/test_point.py::test_point3D', 'sympy/geometry/tests/test_point.py::test_Point2D', 'sympy/geometry/tests/test_point.py::test_issue_9214', 'sympy/geometry/tests/test_point.py::test_issue_11617', 'sympy/geometry/tests/test_point.py::test_transform', 'sympy/geometry/tests/test_point.py::test_concyclic_doctest_bug', 'sympy/geometry/tests/test_point.py::test_arguments', 'sympy/geometry/tests/test_point.py::test_unit', 'sympy/geometry/tests/test_point.py::test_dot', 'sympy/geometry/tests/test_point.py::test__normalize_dimension'])
