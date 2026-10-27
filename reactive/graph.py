class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on
        self._dependents = {}  # dependency -> set of nodes that read it

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        deps = set(deps)
        old_deps = self._deps.get(node, set())
        for dep in old_deps - deps:
            self._dependents[dep].remove(node)
            if not self._dependents[dep]:
                del self._dependents[dep]
        for dep in deps - old_deps:
            self._dependents.setdefault(dep, set()).add(node)
        self._deps[node] = deps

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._dependents.get(node, ()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Discover the complete transitive dependent closure, including start.
        affected = {start}
        stack = [start]
        while stack:
            m = stack.pop()
            for k in self._dependents.get(m, ()):
                if k not in affected:
                    affected.add(k)
                    stack.append(k)

        # In-degree counts only dependencies inside the affected set.
        indegree = {n: 0 for n in affected}
        for n in affected:
            for d in self._deps.get(n, ()):
                if d in affected:
                    indegree[n] += 1

        # Kahn's algorithm: dependency-first order.
        ready = [n for n in affected if indegree[n] == 0]
        order = []
        while ready:
            m = ready.pop()
            order.append(m)
            for k in self._dependents.get(m, ()):
                if k in affected:
                    indegree[k] -= 1
                    if indegree[k] == 0:
                        ready.append(k)

        if len(order) < len(affected):
            raise CycleError("dependency cycle detected among affected nodes")
        return order
