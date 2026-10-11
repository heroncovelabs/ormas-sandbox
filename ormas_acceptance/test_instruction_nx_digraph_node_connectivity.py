"""Authored by Ormas from the public nx-digraph-node-connectivity instruction.

These are independent Ormas acceptance tests, not VulcanBench scoring tests.
Source: VulcanBench 36e2764128f1010b9590714e851ac9dfda95ff68,
tasks/frontier-v5/nx-digraph-node-connectivity/instruction.md.
Only that instruction and pristine public upstream code/tests were used.
No private hidden directory or gold scoring file was opened during authoring.
"""

import networkx as nx
from networkx.algorithms.connectivity import minimum_st_node_cut


def test_public_directed_triangle_cut_actually_disconnects():
    graph = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
    cut = nx.minimum_node_cut(graph)
    assert len(cut) == 1, "The public directed triangle needs a one-node cut."
    remaining = graph.copy()
    remaining.remove_nodes_from(cut)
    assert not nx.is_strongly_connected(remaining)


def test_public_weakly_connected_digraph_has_zero_connectivity():
    graph = nx.DiGraph([(0, 3), (1, 2), (2, 1), (3, 0), (3, 1), (3, 2)])
    assert nx.is_weakly_connected(graph)
    assert not nx.is_strongly_connected(graph)
    assert nx.node_connectivity(graph) == 0
    assert nx.minimum_node_cut(graph) == set()


def test_public_complete_graph_self_loops_do_not_change_connectivity():
    graph = nx.complete_graph(5)
    graph.add_edges_from((node, node) for node in graph)
    assert nx.node_connectivity(graph) == 4
    cut = nx.minimum_node_cut(graph)
    assert len(cut) == 4


def test_parallel_edges_do_not_add_vertex_connectivity():
    simple = nx.complete_graph(5)
    parallel = nx.MultiGraph(simple)
    parallel.add_edges_from(simple.edges)
    assert nx.node_connectivity(parallel) == 4
    assert len(nx.minimum_node_cut(parallel)) == 4


def test_local_directed_cut_separates_nonadjacent_endpoints():
    graph = nx.DiGraph([(0, 1), (1, 2), (2, 3)])
    for function in (minimum_st_node_cut, nx.minimum_node_cut):
        cut = function(graph, 0, 3)
        assert len(cut) == 1
        assert cut <= {1, 2}
        remaining = graph.copy()
        remaining.remove_nodes_from(cut)
        assert not nx.has_path(remaining, 0, 3)
    assert nx.node_connectivity(graph, 0, 3) == 1
    assert nx.node_connectivity(graph, 3, 0) == 0
