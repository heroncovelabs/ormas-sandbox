"""Ormas external acceptance for vbv1-py-expr-eval.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-expr-eval@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
with pytest inside the isolated candidate container, and asserts it passed.

A check that ran and failed is an assertion failure. A check that could not
run (collection/import/usage error, no tests collected, timeout) raises
RuntimeError instead, so the verifier reports a setup problem rather than a
behavioral failure.
"""
import re

from ormas_acceptance import run

PYTEST = ['python3', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--tb=short']
_ERRORS = re.compile(r"\b\d+ errors?\b")


def _check(selector):
    result = run(PYTEST + [selector], timeout_s=60)
    output = result["output"]
    lines = [line for line in output.splitlines() if line.strip()]
    summary = lines[-1] if lines else ""
    if result["returncode"] not in (0, 1) or _ERRORS.search(summary):
        raise RuntimeError(
            "candidate check did not complete (exit %s): %s"
            % (result["returncode"], output[-4000:])
        )
    assert result["returncode"] == 0, output[-4000:]


def test_f2p_add_then_mul():
    _check('test_precedence.py::test_add_then_mul')


def test_f2p_sub_then_mul():
    _check('test_precedence.py::test_sub_then_mul')


def test_f2p_mul_then_pow():
    _check('test_precedence.py::test_mul_then_pow')


def test_f2p_pow_right_assoc():
    _check('test_precedence.py::test_pow_is_right_associative')


def test_f2p_unary_below_power():
    _check('test_precedence.py::test_unary_minus_below_power')


def test_f2p_add_then_pow():
    _check('test_precedence.py::test_add_then_pow')


def test_f2p_mixed_chain():
    _check('test_precedence.py::test_mixed_chain')


def test_f2p_true_div_prec():
    _check('test_precedence.py::test_true_division_precedence')


def test_f2p_floor_div_prec():
    _check('test_precedence.py::test_floor_division_precedence')


def test_f2p_mod_prec():
    _check('test_precedence.py::test_modulo_precedence')


def test_p2p_basic():
    _check('test_basic.py')
