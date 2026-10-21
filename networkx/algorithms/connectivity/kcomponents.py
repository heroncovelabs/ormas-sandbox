"""
Moody and White algorithm for k-components
"""

from collections import defaultdict
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
    Moody and White [1]_ (appendix A) provide an algorithm for identifying
    k-components in a graph, which is based on Kanevsky's algorithm [2]_
    for finding all minimum-size node cut-sets of a graph (implemented in
    :meth:`all_node_cuts`).

    This implementation searches induced subgraphs using a single minimum
    node cut for each candidate. Starting with the biconnected components,
    it records each candidate at its measured connectivity. A noncomplete
    candidate H with minimum cut S is split into the subgraphs induced by
    C union S, for every connected component C of H - S. Every child is a
    proper subset of H, and repeated candidates are processed once.

    To see why one cut suffices, let K be a maximal k-connected node set
    contained in H. Either K = H, or H has connectivity less than k.
    In the latter case, removing its minimum cut S leaves K - S connected,
    so K is contained in one child. Thus every maximal k-connected subgraph
    is eventually recorded. The search continues through candidates whose
    connectivity decreases after splitting.

    At each level k, the result contains the inclusion-maximal recorded
    sets with measured connectivity at least k.

    See also
    --------
    node_connectivity
    minimum_node_cut
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
    # Define default flow function
    if flow_func is None:
        flow_func = default_flow_func

    # Maps each recorded candidate (frozenset of nodes) to its measured
    # node connectivity.
    recorded = {}

    # Level 1: connected components with more than one node.
    for component in nx.connected_components(G):
        if len(component) > 1:
            recorded[frozenset(component)] = 1

    # Level 2: biconnected components, avoiding dyads.
    bicomponents = [frozenset(B) for B in nx.biconnected_components(G)]
    for bicomp in bicomponents:
        if len(bicomp) > 2:
            recorded[bicomp] = 2

    # Exhaustive separator search over induced candidate subgraphs.
    stack = [b for b in bicomponents if len(b) > 2]
    seen = set()
    while stack:
        nodes = stack.pop()
        if nodes in seen:
            continue
        seen.add(nodes)
        if len(nodes) <= 2:
            continue
        H = G.subgraph(nodes)
        if not nx.is_connected(H):
            stack.extend(frozenset(cc) for cc in nx.connected_components(H))
            continue
        # The minimum cut gives both the connectivity and a separator.
        cut = nx.minimum_node_cut(H, flow_func=flow_func)
        # Complete graphs have connectivity n - 1, including with self-loops.
        k = min(len(cut), len(H) - 1)
        recorded[nodes] = k
        if k == len(H) - 1:
            continue
        stack.extend(frozenset(child) for child in _generate_partition(H, cut))

    # Group recorded candidates by measured connectivity level.
    k_comps = defaultdict(list)
    for nodes, level in recorded.items():
        k_comps[level].append(set(nodes))

    # k-components may only be recorded at their maximum k level, but the
    # returned dictionary must contain every connectivity level.
    return _reconstruct_k_components(k_comps)


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


def _generate_partition(G, cut):
    """Yield each component of G - cut together with the entire separator.

    Every subgraph with connectivity greater than len(cut) lies in one
    child, since removing cut leaves that subgraph connected. Each child
    is a proper subset of G, so the search terminates.
    """
    H = G.subgraph(set(G) - cut)
    for cc in nx.connected_components(H):
        child = set(cc) | cut
        if len(child) < len(G):
            yield child


def _reconstruct_k_components(k_comps):
    """Return, for each level k, the inclusion-maximal sets with level >= k.

    ``k_comps`` maps a measured connectivity level to the sets recorded at
    that level. A set recorded at level j is j-connected, hence also
    k-connected for every k <= j.
    """
    result = {}
    max_k = max(k_comps) if k_comps else 0
    # Pool all sets with their measured level, largest sets first.
    pool = sorted(
        ((level, s) for level, sets in k_comps.items() for s in sets),
        key=lambda item: len(item[1]),
        reverse=True,
    )
    for k in range(1, max_k + 1):
        kept = []
        for level, s in pool:
            if level < k:
                continue
            if any(s <= other for other in kept):
                continue
            kept.append(s)
        result[k] = kept
    return result


def build_k_number_dict(kcomps):
    return {
        node: k
        for k, comps in sorted(kcomps.items(), key=itemgetter(0))
        for comp in comps
        for node in comp
    }
