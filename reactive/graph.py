class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}        # node -> set of nodes it directly depends on
        self._dependents = {}  # node -> set of nodes that directly depend on it

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        new_deps = set(deps)
        old_deps = self._deps.get(node, set())
        for removed in old_deps - new_deps:
            self._dependents[removed].discard(node)
        for added in new_deps - old_deps:
            self._dependents.setdefault(added, set()).add(node)
        self._deps[node] = new_deps

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._dependents.get(node, ()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in affected:
                continue
            affected.add(node)
            stack.extend(self._dependents.get(node, ()))

        indegree = dict.fromkeys(affected, 0)
        for node in affected:
            indegree[node] = sum(
                1 for dep in self._deps.get(node, ()) if dep in affected
            )

        ready = [node for node in affected if indegree[node] == 0]
        order = []
        while ready:
            node = ready.pop()
            order.append(node)
            for dependent in self._dependents.get(node, ()):
                if dependent in affected:
                    indegree[dependent] -= 1
                    if indegree[dependent] == 0:
                        ready.append(dependent)

        if len(order) != len(affected):
            raise CycleError("cycle detected among affected cells")
        return order
