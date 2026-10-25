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
            candidate
            for candidate, dependencies in self._deps.items()
            if node in dependencies
        }

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = {start}
        pending = [start]
        while pending:
            current = pending.pop()
            for dependent in self.dependents(current):
                if dependent not in affected:
                    affected.add(dependent)
                    pending.append(dependent)

        # Kahn's algorithm, counting only dependencies inside the affected set.
        indegree = {
            node: len(self._deps.get(node, set()) & affected)
            for node in affected
        }
        ready = [node for node, count in indegree.items() if count == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for dependent in self.dependents(node):
                if dependent not in indegree:
                    continue
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected")
        return order
