"""Ormas external acceptance for vbcii1-oss-networkx-digraph-node-cuts.

Generated from manifest.json by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one of
VulcanBench's hidden checks (vulcanbench:cii-v1/oss-networkx-digraph-node-cuts@88df1c9756ff93105190591e05cd97ad28d4dea5)
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


def test_f2p_triangle_cut_valid():
    _check('oss_tests.py::test_directed_triangle_minimum_node_cut')


def test_f2p_st_cut_reverse_edge():
    _check('oss_tests.py::test_directed_st_cut_ignores_reverse_edge')


def test_f2p_weak_digraph_zero():
    _check('oss_tests.py::test_weakly_connected_digraph_connectivity_zero')


def test_f2p_both_orders_weak():
    _check('oss_tests.py::test_digraph_connectivity_considers_both_orders')


def test_f2p_both_orders_strong():
    _check('oss_tests.py::test_strongly_connected_digraph_both_orders_cut')


def test_f2p_self_loops():
    _check('oss_tests.py::test_self_loops_do_not_inflate_connectivity')


def test_f2p_parallel_edges():
    _check('oss_tests.py::test_parallel_edges_do_not_inflate_connectivity')


def test_p2p_undirected_complete():
    _check('reg_tests.py::test_undirected_complete_graph_connectivity')


def test_p2p_undirected_petersen():
    _check('reg_tests.py::test_undirected_petersen_connectivity')


def test_p2p_directed_cycle():
    _check('reg_tests.py::test_directed_cycle_connectivity')


def test_p2p_undirected_st_cut():
    _check('reg_tests.py::test_undirected_st_cut_adjacent_nodes_empty')


def test_p2p_disconnected():
    _check('reg_tests.py::test_disconnected_undirected_graph')
