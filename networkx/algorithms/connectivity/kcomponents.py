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
    k-components by recursively splitting a graph along minimum-size node
    cutsets. Their algorithm uses Kanevsky's algorithm [2]_ to enumerate
    cutsets (implemented in :meth:`all_node_cuts`). This implementation
    splits along one minimum cut at a time:

        1. Compute node connectivity, k, of the current subgraph and record
           it as a candidate k-component.

        2. Find a minimum node cut using :meth:`minimum_node_cut`.

        3. Generate new induced subgraphs from each connected component
           left by the cut, including all cut vertices in each subgraph.

        4. Recurse to find components of higher connectivity, until the
           remaining subgraphs are complete or too small.

    A subgraph with connectivity greater than the size of a cut is contained
    entirely in one of its sides together with the cut vertices. Thus recursive
    splitting preserves every higher-connectivity component. Core pruning
    (see [3]_) removes vertices whose degree is too low for the level sought.

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
    # Higher-connectivity components are contained in the corresponding core.
    # Core computations use distinct neighbors and ignore self-loops.
    H = nx.Graph(G)
    H.remove_edges_from(nx.selfloop_edges(H))
    stack = [(set(B), 3) for B in bicomponents if len(B) > 2]
    seen = set()
    while stack:
        nodes, min_k = stack.pop()
        C = nx.k_core(H.subgraph(nodes), k=min_k)
        for component in nx.connected_components(C):
            key = (frozenset(component), min_k)
            if key in seen:
                continue
            seen.add(key)
            S = H.subgraph(component)
            cut = nx.minimum_node_cut(S, flow_func=flow_func)
            this_k = len(cut)
            if this_k >= min_k:
                k_components[this_k].append(set(S))
                child_k = this_k + 1
            else:
                # A core, or a side of a cut, can have lower connectivity
                # than its parent. Keep splitting until min_k is reached.
                child_k = min_k
            if len(S) <= child_k:
                continue
            # A component of connectivity greater than the cut's size lies
            # wholly on one side, together with any vertices of the cut.
            stack.extend(
                (part, child_k)
                for part in _generate_partition(S, [cut], child_k - 1)
            )

    # This is necessary because k-components may only be reported at their
    # maximum k level. But we want to return a dictionary in which keys are
    # connectivity levels and values list of sets of components, without
    # skipping any connectivity level. Cut sides can produce duplicate or
    # nested candidates, so reconstruction also retains only the maximal
    # components at each connectivity level.
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
    """Split candidates along each cut, retaining its vertices on every side.

    Every subgraph with connectivity greater than k lies in one of these
    candidates when the cuts have size at most k. Processing cuts separately
    preserves components whose vertices occur in several different cutsets.
    """
    components = {frozenset(G)}
    for cut in cuts:
        new_components = set()
        for component in components:
            separator = component & cut
            for cc in nx.connected_components(G.subgraph(component - cut)):
                candidate = frozenset(cc) | separator
                if len(candidate) > k:
                    new_components.add(candidate)
        components = new_components
    yield from (set(component) for component in components)


def _reconstruct_k_components(k_comps):
    """Fill connectivity levels and retain only maximal components at each."""
    result = {}
    max_k = max(k_comps) if k_comps else 0
    for k in range(max_k, 0, -1):
        # Containment is tested against individual components: their union
        # can cover a higher-level component without any one containing it.
        candidates = k_comps.get(k, []) + result.get(k + 1, [])
        components = sorted(candidates, key=len, reverse=True)
        maximal = []
        for component in components:
            if not any(component <= other for other in maximal):
                maximal.append(component)
        result[k] = maximal
    return result


def build_k_number_dict(kcomps):
    return {
        node: k
        for k, comps in sorted(kcomps.items(), key=itemgetter(0))
        for comp in comps
        for node in comp
    }
