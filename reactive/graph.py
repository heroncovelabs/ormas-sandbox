class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        self._deps[node] = set(deps)

    def dependencies(self, node):
        """Direct dependencies: the set of nodes that `node` depends on."""
        return set(self._deps.get(node, ()))

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, deps in self._deps.items() if node in deps}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = {start}
        stack = [start]
        while stack:
            for dep in self.dependents(stack.pop()):
                if dep not in affected:
                    affected.add(dep)
                    stack.append(dep)

        # Kahn's algorithm restricted to the affected set.
        indegree = {n: len(self._deps.get(n, set()) & affected) for n in affected}
        ready = [n for n, d in indegree.items() if d == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for dep in self.dependents(node) & affected:
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    ready.append(dep)
        if len(order) != len(affected):
            raise CycleError(f"dependency cycle involving {start!r}")
        return order
