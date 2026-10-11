"""Authored by Ormas from the public nx-group-betweenness-epic instruction.

These are independent Ormas acceptance tests, not VulcanBench scoring tests.
Source: VulcanBench 36e2764128f1010b9590714e851ac9dfda95ff68,
tasks/frontier-v5/nx-group-betweenness-epic/instruction.md.
The definition, pair counting and normalization are grounded in the public
upstream group_betweenness_centrality docstring and test_group.py at
NetworkX a7d049b4992a1f7e9bd376ce7378d3825d0cfa0e.
No private hidden directory or gold scoring file was opened during authoring.
"""

from itertools import combinations, permutations

import networkx as nx
import pytest


def _path_fraction_definition(graph, group, *, endpoints, normalized):
    """Directly count shortest paths, independently of group-centrality code."""
    members = set(group)
    nodes = tuple(graph) if endpoints else tuple(node for node in graph if node not in members)
    pairs = permutations(nodes, 2) if graph.is_directed() else combinations(nodes, 2)
    total = 0.0
    for source, target in pairs:
        try:
            paths = tuple(nx.all_shortest_paths(graph, source, target))
        except nx.NetworkXNoPath:
            continue
        counted = sum(
            bool(members.intersection(path if endpoints else path[1:-1]))
            for path in paths
        )
        total += counted / len(paths)
    if normalized:
        outside = len(graph) - len(members)
        total *= (1 if graph.is_directed() else 2) / (outside * (outside - 1))
    return total


def test_reference_agrees_with_pristine_public_regression_examples():
    graph = nx.path_graph(5)
    assert _path_fraction_definition(graph, [1], endpoints=False, normalized=False) == 3
    assert _path_fraction_definition(graph, [1], endpoints=True, normalized=False) == 7
    assert _path_fraction_definition(graph, [1, 3], endpoints=False, normalized=True) == 1


def test_directed_unreachable_pairs_contribute_zero():
    graph = nx.DiGraph([(0, 1), (1, 2), (2, 3), (0, 3)])
    # Outside {1}, only the ordered pair (0, 2) has a shortest path through 1.
    expected = _path_fraction_definition(graph, [1], endpoints=False, normalized=False)
    assert expected == 1
    actual = nx.group_betweenness_centrality(
        graph, [1], normalized=False, endpoints=False
    )
    assert actual == expected


@pytest.mark.parametrize("normalized", [False, True])
@pytest.mark.parametrize("endpoints", [False, True])
@pytest.mark.parametrize("case", ["connected", "disconnected", "directed"])
def test_definition_and_group_order_across_publicly_required_cases(case, endpoints, normalized):
    if case == "connected":
        graph = nx.Graph([(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (1, 3)])
        group = [1, 3]
    elif case == "disconnected":
        graph = nx.Graph([(0, 1), (1, 2), (3, 4), (4, 5)])
        group = [1, 4]
    else:
        graph = nx.DiGraph([(0, 1), (1, 2), (2, 3), (0, 3)])
        group = [1]
    expected = _path_fraction_definition(
        graph, group, endpoints=endpoints, normalized=normalized
    )
    forward = nx.group_betweenness_centrality(
        graph, group, endpoints=endpoints, normalized=normalized
    )
    reverse = nx.group_betweenness_centrality(
        graph, list(reversed(group)), endpoints=endpoints, normalized=normalized
    )
    assert forward == pytest.approx(expected)
    assert reverse == pytest.approx(expected)
