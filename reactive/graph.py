from collections import deque


class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on
        self._dependents = {}  # node -> set of nodes that directly depend on it

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        new_deps = set(deps)
        old_deps = self._deps.get(node, set())

        for dependency in old_deps - new_deps:
            self._dependents[dependency].discard(node)
        for dependency in new_deps - old_deps:
            self._dependents.setdefault(dependency, set()).add(node)

        self._deps[node] = new_deps
        self._dependents.setdefault(node, set())

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._dependents.get(node, ()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = {start}
        pending = [start]
        while pending:
            node = pending.pop()
            for dependent in self._dependents.get(node, ()):
                if dependent not in affected:
                    affected.add(dependent)
                    pending.append(dependent)

        indegree = {
            node: len(self._deps.get(node, set()) & affected)
            for node in affected
        }
        ready = deque(node for node in affected if indegree[node] == 0)
        order = []

        while ready:
            node = ready.popleft()
            order.append(node)
            for dependent in self._dependents.get(node, ()):
                if dependent not in affected:
                    continue
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected")
        return order
