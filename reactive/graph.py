class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        new = set(deps)
        if node in new:
            raise CycleError(f"self-reference in {node!r}")

        had_previous = node in self._deps
        previous = self._deps.get(node)
        self._deps[node] = new
        try:
            self.affected_order(node)
        except CycleError:
            if had_previous:
                self._deps[node] = previous
            else:
                del self._deps[node]
            raise

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, ds in self._deps.items() if node in ds}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Reverse adjacency: node -> direct dependents.
        rev = {}
        for n, ds in self._deps.items():
            for d in ds:
                rev.setdefault(d, set()).add(n)

        # Collect start and all transitive dependents.
        affected = {start}
        stack = [start]
        while stack:
            cur = stack.pop()
            for m in rev.get(cur, ()):
                if m not in affected:
                    affected.add(m)
                    stack.append(m)

        # Kahn's algorithm restricted to the affected subgraph.
        indegree = {
            n: sum(1 for d in self._deps.get(n, ()) if d in affected)
            for n in affected
        }
        ready = [n for n in affected if indegree[n] == 0]
        order = []
        while ready:
            n = ready.pop()
            order.append(n)
            for m in rev.get(n, ()):
                if m in affected:
                    indegree[m] -= 1
                    if indegree[m] == 0:
                        ready.append(m)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected among affected nodes")
        return order
