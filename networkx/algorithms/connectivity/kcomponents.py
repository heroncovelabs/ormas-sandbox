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
    :meth:`all_node_cuts` function):

        1. Compute node connectivity, k, of the input graph G.

        2. Identify all k-cutsets at the current level of connectivity using
           Kanevsky's algorithm.

        3. Generate new graph components based on the removal of
           these cutsets. Nodes in a cutset belong to both sides
           of the induced cut.

        4. If the graph is neither complete nor trivial, return to 1;
           else end.

    This implementation computes the levels in increasing order of `k`:
    each `(k-1)`-component is split recursively along minimum node cuts of
    size less than `k` (nodes in a cut belong to every side) until all
    pieces are `k`-connected, and only the maximal pieces are kept. The
    `k`-core is used to prune nodes that cannot belong to a `k`-component
    (see [3]_ for related heuristics).

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
    # Dictionary with connectivity level (k) as keys and a list of
    # sets of nodes that form a k-component as values. Note that
    # k-components can overlap (but only k - 1 nodes).
    k_components = defaultdict(list)
    # Define default flow function
    if flow_func is None:
        flow_func = default_flow_func
    # Bicomponents as a base to check for higher order k-components
    for component in nx.connected_components(G):
        # isolated nodes have connectivity 0
        comp = set(component)
        if len(comp) > 1:
            k_components[1].append(comp)
    bicomponents = [G.subgraph(c) for c in nx.biconnected_components(G)]
    for bicomponent in bicomponents:
        bicomp = set(bicomponent)
        # avoid considering dyads as bicomponents
        if len(bicomp) > 2:
            k_components[2].append(bicomp)
    # Every k-component is contained in some (k-1)-component, so higher
    # levels are computed by splitting the components of the previous level.
    k = 2
    while k_components[k]:
        k += 1
        for comp in k_components[k - 1]:
            k_components[k].extend(_maximal_k_connected(G, comp, k, flow_func))
    del k_components[k]
    return {k: k_components[k] for k in sorted(k_components, reverse=True)}


def _maximal_k_connected(G, nodes, k, flow_func):
    """Returns the maximal k-connected node sets of the subgraph of G
    induced by `nodes`.

    Any k-connected subgraph survives the removal of a node cut of size
    less than k, so it is contained in one of the components of the cut
    plus the cut itself. Splitting recursively along minimum node cuts
    thus finds every maximal k-connected subgraph, possibly along with
    duplicates or non-maximal ones, which are filtered at the end.
    """
    found = []
    stack = [set(nodes)]
    while stack:
        nodes = stack.pop()
        if len(nodes) <= k:
            continue
        # Nodes of degree less than k can't be in a k-connected subgraph.
        H = nx.k_core(G.subgraph(nodes), k)
        if len(H) <= k:
            continue
        if not nx.is_connected(H):
            stack.extend(set(c) for c in nx.connected_components(H))
            continue
        n = len(H)
        if H.number_of_edges() == n * (n - 1) // 2:
            found.append(set(H))
            continue
        cut = nx.minimum_node_cut(H, flow_func=flow_func)
        if len(cut) >= k:
            found.append(set(H))
            continue
        rest = H.subgraph(set(H) - cut)
        stack.extend(set(c) | cut for c in nx.connected_components(rest))
    # Keep only the maximal sets (removing duplicates and strict subsets).
    found.sort(key=len, reverse=True)
    result = []
    for c in found:
        if not any(c <= other for other in result):
            result.append(c)
    return result


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
