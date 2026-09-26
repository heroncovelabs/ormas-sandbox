"""Ormas external acceptance for vbcii1-oss-networkx-kcomponents-exact-epic.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-networkx-kcomponents-exact-epic@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_two_icosahedra():
    _check('oss_tests.py::test_two_icosahedra_joined_by_connectors')


def test_f2p_exact_sparse():
    _check('oss_tests.py::test_exact_decomposition_sparse_graphs')


def test_f2p_exact_medium():
    _check('oss_tests.py::test_exact_decomposition_medium_graphs')


def test_f2p_exact_dense():
    _check('oss_tests.py::test_exact_decomposition_dense_graphs')


def test_p2p_petersen():
    _check('reg_tests.py::test_petersen_decomposition')


def test_p2p_pinned_random():
    _check('reg_tests.py::test_pinned_random_graph_decompositions')


def test_p2p_output_contract():
    _check('reg_tests.py::test_output_contract_no_nesting_and_connectivity')


def test_p2p_directed_rejected():
    _check('reg_tests.py::test_directed_graph_rejected')


def test_p2p_approximation_unchanged():
    _check('reg_tests.py::test_approximation_module_unchanged')
