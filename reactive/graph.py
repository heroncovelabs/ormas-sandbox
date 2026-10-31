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
        for dependency in previous - deps:
            dependents = self._dependents[dependency]
            dependents.remove(node)
            if not dependents:
                del self._dependents[dependency]
        for dependency in deps - previous:
            self._dependents.setdefault(dependency, set()).add(node)
        self._deps[node] = deps

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._dependents.get(node, ()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Collect affected set via traversal over direct dependents.
        affected = {start}
        stack = [start]
        while stack:
            cur = stack.pop()
            for dep in self._dependents.get(cur, ()):
                if dep not in affected:
                    affected.add(dep)
                    stack.append(dep)

        # Indegree restricted to edges inside the affected set.
        indegree = {n: 0 for n in affected}
        for n in affected:
            for d in self._deps.get(n, ()):
                if d in affected:
                    indegree[n] += 1

        # Kahn's algorithm (deterministic ordering by repr for stable output).
        ready = deque(sorted((n for n in affected if indegree[n] == 0), key=repr))
        order = []
        while ready:
            n = ready.popleft()
            order.append(n)
            newly = []
            for m in self._dependents.get(n, ()):
                indegree[m] -= 1
                if indegree[m] == 0:
                    newly.append(m)
            ready.extend(sorted(newly, key=repr))

        if len(order) < len(affected):
            raise CycleError("dependency cycle detected among affected cells")
        return order
