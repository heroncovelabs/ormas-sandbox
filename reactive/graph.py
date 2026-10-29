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
        return {n for n, ds in self._deps.items() if node in ds}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # 1. Discover the transitive dependent closure, including start.
        closure = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for dep in self.dependents(current):
                if dep not in closure:
                    closure.add(dep)
                    stack.append(dep)

        # 2. Indegrees counting only dependencies inside the closure.
        indegree = {n: 0 for n in closure}
        out_edges = {n: [] for n in closure}
        for n in closure:
            for d in self._deps.get(n, ()):
                if d in closure:
                    indegree[n] += 1
                    out_edges[d].append(n)

        # 3. Kahn's algorithm over the closure.
        ready = [n for n in closure if indegree[n] == 0]
        order = []
        while ready:
            n = ready.pop()
            order.append(n)
            for m in out_edges[n]:
                indegree[m] -= 1
                if indegree[m] == 0:
                    ready.append(m)

        # 4. Any unprocessed node means a cycle within the affected set.
        if len(order) < len(closure):
            raise CycleError("dependency cycle detected among affected nodes")
        return order
