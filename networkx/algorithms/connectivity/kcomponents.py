"""
Moody and White algorithm for k-components
"""

from collections import defaultdict, deque
from itertools import combinations
from operator import itemgetter

import networkx as nx

# Define the default maximum flow function.
from networkx.algorithms.flow import edmonds_karp
from networkx.utils import not_implemented_for

default_flow_func = edmonds_karp

__all__ = ["k_components"]


@not_implemented_for("directed")
@nx._dispatchable
def k_components(G, flow_func=None):
    r"""Returns the k-component structure of a graph G.

    A `k`-component is a maximal subgraph of a graph G that has, at least,
    node connectivity `k`: we need to remove at least `k` nodes to break it
    into more components. `k`-components have an inherent hierarchical
    structure because they are nested in terms of connectivity: a connected
    graph can contain several 2-components, each of which can contain
    one or more 3-components, and so forth.

    Parameters
    ----------
    G : NetworkX graph

    flow_func : function
        Function to perform the underlying flow computations. Default value
        :meth:`edmonds_karp`. This function performs better in sparse graphs with
        right tailed degree distributions. :meth:`shortest_augmenting_path` will
        perform better in denser graphs.

    Returns
    -------
    k_components : dict
        Dictionary with all connectivity levels `k` in the input Graph as keys
        and a list of sets of nodes that form a k-component of level `k` as
        values.

    Raises
    ------
    NetworkXNotImplemented
        If the input graph is directed.

    Examples
    --------
    >>> # Petersen graph has 10 nodes and it is triconnected, thus all
    >>> # nodes are in a single component on all three connectivity levels
    >>> G = nx.petersen_graph()
    >>> k_components = nx.k_components(G)

    Notes
    -----
    The search starts from the bicomponents and examines induced subgraphs.
    For a candidate of connectivity `q`, its `(q + 1)`-core contains every
    subgraph with higher connectivity, so smaller cores can be safely split
    into bicomponents for further searching. If the core is unchanged, a
    minimum node cut separates the candidate into smaller sides, each
    including the cut. Every higher-connectivity subgraph lies entirely in
    one of these sides, since the cut would otherwise disconnect it. Recursive
    splitting finds all maximal k-components, including those in sides with
    lower connectivity than their parent. Reconstruction combines the
    certified candidates at each level with all components inherited from
    the next level and retains the inclusion-maximal node sets.

    See also
    --------
    node_connectivity
    all_node_cuts
    biconnected_components : special case of this function when k=2
    k_edge_components : similar to this function, but uses edge-connectivity
        instead of node-connectivity

    References
    ----------
    .. [1]  Moody, J. and D. White (2003). Social cohesion and embeddedness:
            A hierarchical conception of social groups.
            American Sociological Review 68(1), 103--28.
            http://www2.asanet.org/journals/ASRFeb03MoodyWhite.pdf

    .. [2]  Kanevsky, A. (1993). Finding all minimum-size separating vertex
            sets in a graph. Networks 23(6), 533--541.
            http://onlinelibrary.wiley.com/doi/10.1002/net.3230230604/abstract

    .. [3]  Torrents, J. and F. Ferraro (2015). Structural Cohesion:
            Visualization and Heuristics for Fast Computation.
            https://arxiv.org/pdf/1503.04476v1

    """
    k_components = defaultdict(list)
    if flow_func is None:
        flow_func = default_flow_func

    # Node connectivity depends only on distinct non-self neighbors. The
    # flow-based connectivity routines use degree, so give them a simple,
    # loop-free graph when the input has loops or parallel edges.
    if G.is_multigraph() or nx.number_of_selfloops(G):
        simple = nx.Graph()
        simple.add_nodes_from(G)
        simple.add_edges_from((u, v) for u, v in G.edges() if u is not v and u != v)
    else:
        simple = G

    for component in nx.connected_components(G):
        # Isolated nodes have connectivity 0.
        if len(component) > 1:
            k_components[1].append(set(component))

    worklist = []
    for component in nx.biconnected_components(G):
        # Dyads are not 2-components under this function's convention.
        if len(component) > 2:
            k_components[2].append(set(component))
            worklist.append(frozenset(component))

    seen = set()
    while worklist:
        nodes = worklist.pop()
        if nodes in seen:
            continue
        seen.add(nodes)
        C = G.subgraph(nodes)
        H = C if simple is G else simple.subgraph(nodes)
        q = nx.node_connectivity(H, flow_func=flow_func)
        if q > 2:
            # Record the actual connectivity even if it decreased from the
            # parent: this candidate is still a certified q-connected graph.
            k_components[q].append(set(nodes))

        # Peel the (q + 1)-core using distinct, non-self neighbors. Every
        # subgraph of connectivity greater than q survives this process.
        degree = {v: len(C[v]) - (v in C[v]) for v in C}
        remaining = set(nodes)
        queue = deque(v for v in C if degree[v] <= q)
        while queue:
            v = queue.popleft()
            if v not in remaining:
                continue
            remaining.remove(v)
            for neighbor in C[v]:
                if neighbor in remaining:
                    degree[neighbor] -= 1
                    if degree[neighbor] == q:
                        queue.append(neighbor)

        if not remaining:
            continue
        if len(remaining) < len(nodes):
            # Higher components are biconnected and lie wholly in one of
            # these pieces. Each piece is a proper subset of this candidate.
            core = G.subgraph(remaining)
            worklist.extend(
                frozenset(component)
                for component in nx.biconnected_components(core)
                if len(component) > 2
            )
            continue

        # The unchanged core is non-complete: a complete candidate has
        # connectivity |C|-1 and its (q + 1)-core is empty. A minimum cut
        # splits every higher-connected component into at least one proper
        # separator-side candidate without losing any of its vertices.
        cut = nx.minimum_node_cut(H, flow_func=flow_func)
        worklist.extend(
            frozenset(component) for component in _generate_partition(C, [cut], q)
        )

    return _reconstruct_k_components(k_components)


def _consolidate(sets, k):
    """Merge sets that share k or more elements.

    See: http://rosettacode.org/wiki/Set_consolidation

    The iterative python implementation posted there is
    faster than this because of the overhead of building a
    Graph and calling nx.connected_components, but it's not
    clear for us if we can use it in NetworkX because there
    is no licence for the code.

    """
    G = nx.Graph()
    nodes = dict(enumerate(sets))
    G.add_nodes_from(nodes)
    G.add_edges_from(
        (u, v) for u, v in combinations(nodes, 2) if len(nodes[u] & nodes[v]) >= k
    )
    for component in nx.connected_components(G):
        yield set.union(*[nodes[n] for n in component])


def _generate_partition(G, cuts, k):
    """Yield smaller separator-side candidates for components above level k.

    A subgraph with connectivity greater than the size of a separator S
    cannot meet two components of G - S: deleting its vertices in S would
    disconnect it. Thus each such subgraph lies in one side together with
    the entire separator.
    """
    nodes = set(G)
    seen = set()
    for cut in cuts:
        separator = set(cut)
        for side in nx.connected_components(G.subgraph(nodes - separator)):
            candidate = side | separator
            # Connectivity greater than k requires at least k + 2 vertices.
            if not k + 1 < len(candidate) < len(nodes):
                continue
            key = frozenset(candidate)
            if key not in seen:
                seen.add(key)
                yield candidate


def _reconstruct_k_components(k_comps):
    """Build the maximal antichain of certified candidates at every level."""
    result = {}
    max_k = max(k_comps) if k_comps else 0
    for k in range(max_k, 0, -1):
        # A higher-level component is also k-connected. Compare whole sets,
        # since distinct maximal components may overlap without containing one
        # another. The search guarantees every maximal component is recorded
        # at this level or inherited from a higher level.
        maximal = []
        for component in k_comps.get(k, []) + result.get(k + 1, []):
            candidate = frozenset(component)
            if any(candidate <= other for other in maximal):
                continue
            maximal = [other for other in maximal if not other < candidate]
            maximal.append(candidate)
        result[k] = [set(component) for component in maximal]
    return result


def build_k_number_dict(kcomps):
    return {
        node: k
        for k, comps in sorted(kcomps.items(), key=itemgetter(0))
        for comp in comps
        for node in comp
    }
