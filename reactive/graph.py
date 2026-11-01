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
        # Collect start and every transitive dependent.
        affected = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for dep in self.dependents(node):
                if dep not in affected:
                    affected.add(dep)
                    stack.append(dep)

        # In-degree restricted to the affected set (self-loops count as edges).
        indegree = {
            n: len({d for d in self._deps.get(n, ()) if d in affected})
            for n in affected
        }
        ready = [n for n in affected if indegree[n] == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for dep in self.dependents(node):
                if dep in affected:
                    indegree[dep] -= 1
                    if indegree[dep] == 0:
                        ready.append(dep)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected among affected cells")
        return order
