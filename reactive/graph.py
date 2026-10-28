class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        self._deps[node] = set(deps)

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, ds in self._deps.items() if node in ds}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Build the dependents adjacency restricted to the reachable set.
        reverse = {}
        for n, ds in self._deps.items():
            for d in ds:
                reverse.setdefault(d, set()).add(n)

        visiting = set()  # on the current DFS path
        done = set()
        postorder = []

        # Iterative DFS over dependents producing reverse topological order.
        stack = [(start, iter(reverse.get(start, set())))]
        visiting.add(start)
        while stack:
            node, it = stack[-1]
            advanced = False
            for nxt in it:
                if nxt in visiting:
                    raise CycleError("dependency cycle involving %r" % (nxt,))
                if nxt not in done:
                    visiting.add(nxt)
                    stack.append((nxt, iter(reverse.get(nxt, set()))))
                    advanced = True
                    break
            if not advanced:
                stack.pop()
                visiting.discard(node)
                done.add(node)
                postorder.append(node)

        postorder.reverse()
        return postorder
