class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous).

        Raises CycleError, leaving the graph unchanged, if the replacement
        introduces a cycle."""
        _absent = object()
        previous = self._deps.get(node, _absent)
        self._deps[node] = set(deps)
        try:
            self.affected_order(node)
        except CycleError:
            if previous is _absent:
                del self._deps[node]
            else:
                self._deps[node] = previous
            raise

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, deps in self._deps.items() if node in deps}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Collect start and every node reachable through dependents.
        affected = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for dep in self.dependents(current):
                if dep not in affected:
                    affected.add(dep)
                    stack.append(dep)

        # Count, for each affected node, how many of its dependencies are
        # also affected; those must be emitted before it.
        pending = {
            n: len(self._deps.get(n, set()) & affected) for n in affected
        }
        ready = [n for n in affected if pending[n] == 0]
        order = []
        while ready:
            current = ready.pop()
            order.append(current)
            for dep in self.dependents(current):
                if dep in pending:
                    pending[dep] -= 1
                    if pending[dep] == 0:
                        ready.append(dep)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected among affected cells")
        return order
