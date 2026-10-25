class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        new_deps = set(deps)
        had_previous = node in self._deps
        previous = self._deps.get(node)

        self._deps[node] = new_deps
        try:
            self.affected_order(node)
        except CycleError:
            if had_previous:
                self._deps[node] = previous
            else:
                self._deps.pop(node, None)
            raise

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, ds in self._deps.items() if node in ds}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Build reverse edges once for both traversal and topological sorting.
        downstream = {}
        for node, deps in self._deps.items():
            for dependency in deps:
                downstream.setdefault(dependency, set()).add(node)

        # Collect the transitive dependent closure, including start.
        closure = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for dep in downstream.get(current, ()):
                if dep not in closure:
                    closure.add(dep)
                    stack.append(dep)

        # In-degree restricted to the closure: count dependencies inside it.
        pending = {}
        for n in closure:
            pending[n] = sum(1 for d in self._deps.get(n, ()) if d in closure)

        # Kahn's algorithm over the induced subgraph.
        ready = [n for n in closure if pending[n] == 0]
        order = []
        while ready:
            current = ready.pop()
            order.append(current)
            for dep in downstream.get(current, ()):
                if dep in closure:
                    pending[dep] -= 1
                    if pending[dep] == 0:
                        ready.append(dep)

        if len(order) != len(closure):
            raise CycleError("dependency cycle detected involving cells: "
                             + ", ".join(sorted(map(repr, closure - set(order)))))
        return order
