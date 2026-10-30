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

    This implementation also uses some heuristics (see [3]_ for details)
    to speed up the computation.

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
    # Connected components seed level 1.
    for component in nx.connected_components(G):
        # isolated nodes have connectivity 0
        comp = set(component)
        if len(comp) > 1:
            k_components[1].append(comp)
    # Biconnected components seed level 2 (dyads are not bicomponents).
    bicomponents = [G.subgraph(c) for c in nx.biconnected_components(G)]
    for bicomponent in bicomponents:
        bicomp = set(bicomponent)
        if len(bicomp) > 2:
            k_components[2].append(bicomp)
    # Induced candidate subgraphs are identified by their node sets, so the
    # same candidate is never expanded twice.
    seen = set()
    for B in bicomponents:
        if len(B) <= 2:
            continue
        root = frozenset(B)
        if root in seen:
            continue
        seen.add(root)
        stack = [root]
        while stack:
            nodes = stack.pop()
            C = G.subgraph(nodes)
            if len(C) <= 2:
                continue
            if not nx.is_connected(C):
                # A disconnected candidate is handled by its components.
                for cc in nx.connected_components(C):
                    child = frozenset(cc)
                    if child not in seen:
                        seen.add(child)
                        stack.append(child)
                continue
            this_k = nx.node_connectivity(C, flow_func=flow_func)
            if this_k > 2:
                k_components[this_k].append(set(nodes))
            # A complete candidate has no separator and nothing to descend into.
            if C.number_of_edges() == len(C) * (len(C) - 1) // 2:
                continue
            cuts = nx.all_node_cuts(C, k=this_k, flow_func=flow_func)
            separator = next(iter(cuts), None)
            if separator is None:
                continue
            for child in _generate_partition(C, [separator], this_k):
                child = frozenset(child)
                if child < nodes and child not in seen:
                    seen.add(child)
                    stack.append(child)

    # This is necessary because k-components may only be reported at their
    # maximum k level. But we want to return a dictionary in which keys are
    # connectivity levels and values list of sets of components, without
    # skipping any connectivity level. Also, it's possible that subsets of
    # an already detected k-component appear at a level k. Checking for this
    # in the while loop above penalizes the common case. Thus we also have to
    # _consolidate all connectivity levels in _reconstruct_k_components.
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
    """Yield the sides of a separator of G, each joined with the separator.

    ``cuts`` must contain at least one separator. The first one is used.
    For each connected component of ``G`` minus that separator, the
    component together with the entire separator is yielded. Any component
    with node connectivity greater than the separator size lies wholly
    within at least one such child, so repeated strict descent preserves
    every higher-connectivity maximal component.
    """
    separator = next(iter(cuts), None)
    if not separator:
        return
    separator = set(separator)
    H = G.subgraph(set(G) - separator)
    for cc in nx.connected_components(H):
        yield set(cc) | separator


def _reconstruct_k_components(k_comps):
    result = {}
    max_k = max(k_comps) if k_comps else 0
    for k in range(max_k, 0, -1):
        # Every (k + 1)-component is also k-connected, so it competes with the
        # level-k candidates. Candidates are deduplicated by node set, and only
        # the inclusion-maximal sets are kept at this level.
        candidates = list(k_comps.get(k, [])) + result.get(k + 1, [])
        unique = {}
        for comp in candidates:
            unique.setdefault(frozenset(comp), set(comp))
        result[k] = [
            comp
            for key, comp in unique.items()
            if not any(key < other for other in unique)
        ]
    return result


def build_k_number_dict(kcomps):
    return {
        node: k
        for k, comps in sorted(kcomps.items(), key=itemgetter(0))
        for comp in comps
        for node in comp
    }
