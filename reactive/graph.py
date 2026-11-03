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
        return self._dependents.get(node, set()).copy()

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Collect start and every transitive dependent.
        affected = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for dep in self.dependents(current):
                if dep not in affected:
                    affected.add(dep)
                    stack.append(dep)

        # Kahn's algorithm on the induced subgraph: count only in-set dependencies.
        pending = {}
        rdeps = {n: [] for n in affected}
        for n in affected:
            in_set = self._deps.get(n, set()) & affected
            pending[n] = len(in_set)
            for d in in_set:
                rdeps[d].append(n)

        ready = [n for n in affected if pending[n] == 0]
        order = []
        while ready:
            n = ready.pop()
            order.append(n)
            for m in rdeps[n]:
                pending[m] -= 1
                if pending[m] == 0:
                    ready.append(m)

        if len(order) != len(affected):
            raise CycleError("dependency cycle detected among affected nodes")
        return order
