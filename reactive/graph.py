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
        return {
            other
            for other, direct_deps in self._deps.items()
            if node in direct_deps
        }

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Discover start plus everything reachable through direct dependents.
        affected = {start}
        pending = [start]
        while pending:
            node = pending.pop()
            for dependent in self.dependents(node):
                if dependent not in affected:
                    affected.add(dependent)
                    pending.append(dependent)

        # Kahn's algorithm restricted to the affected subgraph.
        pending_deps = {}
        for node in affected:
            pending_deps[node] = len(self._deps.get(node, set()) & affected)

        ready = sorted(node for node, count in pending_deps.items() if count == 0)
        order = []
        while ready:
            node = ready.pop(0)
            order.append(node)
            for dependent in sorted(self.dependents(node) & affected):
                pending_deps[dependent] -= 1
                if pending_deps[dependent] == 0:
                    ready.append(dependent)
            ready.sort()

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected")

        return order
