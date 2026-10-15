"""
Moody and White algorithm for k-components
"""

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
    for finding minimum-size node cut-sets of a graph.

    The implementation computes, for every connectivity level `k`, the
    maximal node sets whose induced subgraph has node connectivity at least
    `k`. For a given level it repeatedly takes a minimum node cut `S` of the
    current candidate `H` with connectivity `c < k`: every `k`-connected
    subgraph of `H` lies inside `S` together with a single component of
    `H - S`, so the recursion only needs to continue on those pieces. Leaves
    that are `k`-connected are then filtered down to the maximal ones.

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
    if flow_func is None:
        flow_func = default_flow_func
    result = {}
    k = 1
    while True:
        comps = _maximal_k_connected_sets(G, k, flow_func)
        if not comps:
            break
        result[k] = comps
        k += 1
    return result


def _maximal_k_connected_sets(G, k, flow_func):
    """Return the maximal node sets inducing a subgraph of connectivity >= k.

    Every such set is found exactly: if a candidate ``H`` has node
    connectivity ``c < k`` and ``S`` is a minimum node cut of ``H``, then any
    subgraph of ``H`` with connectivity >= k has at most ``c < k`` nodes
    removed by ``S`` and so stays connected in ``H - S``; hence it is
    contained in ``S`` plus one component of ``H - S``.
    """
    found = []
    stack = [frozenset(G)]
    while stack:
        nodes = stack.pop()
        # A subgraph on at most k nodes cannot have connectivity >= k.
        if len(nodes) <= k:
            continue
        H = G.subgraph(nodes)
        if not nx.is_connected(H):
            for comp in nx.connected_components(H):
                stack.append(frozenset(comp))
            continue
        c = nx.node_connectivity(H, flow_func=flow_func)
        if c >= k:
            found.append(nodes)
            continue
        cut = nx.minimum_node_cut(H, flow_func=flow_func)
        rest = G.subgraph(nodes - cut)
        for comp in nx.connected_components(rest):
            stack.append(frozenset(comp) | cut)

    # Keep only the maximal sets (and each one once).
    found = sorted(set(found), key=len, reverse=True)
    maximal = []
    for nodes in found:
        if not any(nodes < other for other in maximal):
            maximal.append(nodes)
    return [set(nodes) for nodes in maximal]


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


def build_k_number_dict(kcomps):
    return {
        node: k
        for k, comps in sorted(kcomps.items(), key=itemgetter(0))
        for comp in comps
        for node in comp
    }
