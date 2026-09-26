"""Ormas external acceptance for vbv1-py-bytecode-vm.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:v1/py-bytecode-vm@d668dd28adaf0f911bd541c9c91c0d0232b7729b)
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


def test_f2p_arithmetic():
    _check('test_vmlang.py::test_arithmetic')


def test_f2p_variables_and_compare():
    _check('test_vmlang.py::test_variables_and_compare')


def test_f2p_unknown_variable():
    _check('test_vmlang.py::test_unknown_variable_raises')


def test_f2p_not():
    _check('test_vmlang.py::test_not')


def test_f2p_if_branch():
    _check('test_vmlang.py::test_if_selects_branch_by_condition')


def test_f2p_nested_if_jumps():
    _check('test_vmlang.py::test_nested_if_jump_targets')


def test_f2p_and_or_values():
    _check('test_vmlang.py::test_and_or_values')


def test_f2p_short_circuit():
    _check('test_vmlang.py::test_short_circuit_skips_faulty_branch')


def test_f2p_flat_isa():
    _check('test_vmlang.py::test_compiles_to_flat_isa_instructions')


def test_p2p_construct():
    _check('test_vmlang.py::test_construct')
