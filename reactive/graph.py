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
        deps = set(deps)
        previous = self._deps.get(node, set())
        for dep in previous - deps:
            self._dependents[dep].remove(node)
            if not self._dependents[dep]:
                del self._dependents[dep]
        for dep in deps - previous:
            self._dependents.setdefault(dep, set()).add(node)
        self._deps[node] = deps

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

        remaining = {
            node: len(self._deps.get(node, set()) & affected)
            for node in affected
        }
        ready = deque(node for node, count in remaining.items() if count == 0)
        order = []
        while ready:
            node = ready.popleft()
            order.append(node)
            for dependent in self._dependents.get(node, ()):
                if dependent in remaining:
                    remaining[dependent] -= 1
                    if remaining[dependent] == 0:
                        ready.append(dependent)

        if len(order) != len(affected):
            raise CycleError("Dependency cycle among affected cells")
        return order
