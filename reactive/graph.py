class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on
        self._rdeps = {}  # node -> set of nodes that directly depend on it

    def dependencies(self, node):
        """Direct dependencies: the set of nodes `node` depends on."""
        return set(self._deps.get(node, ()))

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        for old in self._deps.get(node, ()):
            self._rdeps[old].discard(node)
        new = set(deps)
        self._deps[node] = new
        for dep in new:
            self._rdeps.setdefault(dep, set()).add(node)

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._rdeps.get(node, ()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for dependent in self._rdeps.get(node, ()):
                if dependent not in affected:
                    affected.add(dependent)
                    stack.append(dependent)

        indegree = {
            node: sum(1 for dep in self._deps.get(node, ()) if dep in affected)
            for node in affected
        }
        ready = [node for node in affected if indegree[node] == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for dependent in self._rdeps.get(node, ()):
                if dependent in affected:
                    indegree[dependent] -= 1
                    if indegree[dependent] == 0:
                        ready.append(dependent)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected involving %r" % (start,))
        return order
