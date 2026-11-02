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
        return {dependent for dependent, deps in self._deps.items() if node in deps}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Build the reverse edges once for both discovery and ordering.
        reverse = {}
        for node, deps in self._deps.items():
            for dep in deps:
                reverse.setdefault(dep, set()).add(node)

        affected = {start}
        pending = [start]
        while pending:
            node = pending.pop()
            for dependent in reverse.get(node, ()):
                if dependent not in affected:
                    affected.add(dependent)
                    pending.append(dependent)

        # Count only edges within the affected subgraph.
        remaining = {
            node: sum(dep in affected for dep in self._deps.get(node, ()))
            for node in affected
        }
        ready = [node for node in affected if remaining[node] == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for dependent in reverse.get(node, ()):
                if dependent in affected:
                    remaining[dependent] -= 1
                    if remaining[dependent] == 0:
                        ready.append(dependent)

        if len(order) != len(affected):
            raise CycleError("Dependency cycle detected")
        return order
