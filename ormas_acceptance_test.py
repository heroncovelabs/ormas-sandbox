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
    check(['sympy/polys/tests/test_rings.py::test_PolyElement_as_expr'])


def test_p2p_000():
    check(['sympy/polys/tests/test_rings.py::test_PolyRing___init__', 'sympy/polys/tests/test_rings.py::test_PolyRing___hash__', 'sympy/polys/tests/test_rings.py::test_PolyRing___eq__', 'sympy/polys/tests/test_rings.py::test_PolyRing_ring_new', 'sympy/polys/tests/test_rings.py::test_PolyRing_drop', 'sympy/polys/tests/test_rings.py::test_PolyRing___getitem__', 'sympy/polys/tests/test_rings.py::test_PolyRing_is_', 'sympy/polys/tests/test_rings.py::test_PolyRing_add', 'sympy/polys/tests/test_rings.py::test_PolyRing_mul', 'sympy/polys/tests/test_rings.py::test_sring', 'sympy/polys/tests/test_rings.py::test_PolyElement___hash__', 'sympy/polys/tests/test_rings.py::test_PolyElement___eq__', 'sympy/polys/tests/test_rings.py::test_PolyElement__lt_le_gt_ge__', 'sympy/polys/tests/test_rings.py::test_PolyElement__str__', 'sympy/polys/tests/test_rings.py::test_PolyElement_copy', 'sympy/polys/tests/test_rings.py::test_PolyElement_from_expr', 'sympy/polys/tests/test_rings.py::test_PolyElement_degree', 'sympy/polys/tests/test_rings.py::test_PolyElement_tail_degree', 'sympy/polys/tests/test_rings.py::test_PolyElement_degrees', 'sympy/polys/tests/test_rings.py::test_PolyElement_tail_degrees'])


def test_p2p_020():
    check(['sympy/polys/tests/test_rings.py::test_PolyElement_l1_norm', 'sympy/polys/tests/test_rings.py::test_PolyElement_diff', 'sympy/polys/tests/test_rings.py::test_PolyElement___call__', 'sympy/polys/tests/test_rings.py::test_PolyElement_evaluate', 'sympy/polys/tests/test_rings.py::test_PolyElement_subs', 'sympy/polys/tests/test_rings.py::test_PolyElement_compose', 'sympy/polys/tests/test_rings.py::test_PolyElement_is_', 'sympy/polys/tests/test_rings.py::test_PolyElement_drop', 'sympy/polys/tests/test_rings.py::test_PolyElement_pdiv', 'sympy/polys/tests/test_rings.py::test_PolyElement_gcdex', 'sympy/polys/tests/test_rings.py::test_PolyElement_subresultants', 'sympy/polys/tests/test_rings.py::test_PolyElement_resultant', 'sympy/polys/tests/test_rings.py::test_PolyElement_discriminant', 'sympy/polys/tests/test_rings.py::test_PolyElement_decompose', 'sympy/polys/tests/test_rings.py::test_PolyElement_shift', 'sympy/polys/tests/test_rings.py::test_PolyElement_sturm', 'sympy/polys/tests/test_rings.py::test_PolyElement_gff_list', 'sympy/polys/tests/test_rings.py::test_PolyElement_sqf_norm', 'sympy/polys/tests/test_rings.py::test_PolyElement_sqf_list', 'sympy/polys/tests/test_rings.py::test_PolyElement_factor_list'])
