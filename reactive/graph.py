class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        if deps:
            self._deps[node] = set(deps)
        else:
            self._deps.pop(node, None)

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, ds in self._deps.items() if node in ds}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Collect start and all transitive dependents.
        affected = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for d in self.dependents(node):
                if d not in affected:
                    affected.add(d)
                    stack.append(d)

        # Kahn's algorithm restricted to the affected subgraph.
        indegree = {n: len(self._deps.get(n, set()) & affected) for n in affected}
        ready = [n for n in affected if indegree[n] == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for d in affected:
                if node in self._deps.get(d, ()):
                    indegree[d] -= 1
                    if indegree[d] == 0:
                        ready.append(d)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected")
        return order
