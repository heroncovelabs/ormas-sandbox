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
        # Collect the closure of start and its transitive dependents.
        closure = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for d in self.dependents(node):
                if d not in closure:
                    closure.add(d)
                    stack.append(d)

        # Indegree counts only dependencies that lie inside the closure.
        indegree = {n: len(self._deps.get(n, set()) & closure) for n in closure}

        # Reverse edges restricted to the closure.
        children = {n: [] for n in closure}
        for n in closure:
            for dep in self._deps.get(n, set()) & closure:
                children[dep].append(n)

        # Kahn's algorithm.
        queue = [n for n in closure if indegree[n] == 0]
        order = []
        while queue:
            node = queue.pop()
            order.append(node)
            for child in children[node]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if len(order) < len(closure):
            raise CycleError("dependency cycle detected among affected cells")
        return order
