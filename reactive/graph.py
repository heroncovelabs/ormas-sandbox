class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        deps = set(deps)
        if deps:
            self._deps[node] = deps
        else:
            self._deps.pop(node, None)

    def dependencies(self, node):
        """Direct dependencies: the set of nodes `node` depends on."""
        return set(self._deps.get(node, ()))

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, deps in self._deps.items() if node in deps}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = {start}
        stack = [start]
        while stack:
            for dep in self.dependents(stack.pop()):
                if dep not in affected:
                    affected.add(dep)
                    stack.append(dep)

        indegree = {n: len(self._deps.get(n, set()) & affected) for n in affected}
        ready = sorted((n for n, d in indegree.items() if d == 0), key=repr)
        order = []
        while ready:
            node = ready.pop(0)
            order.append(node)
            for dep in sorted(self.dependents(node) & affected, key=repr):
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    ready.append(dep)
        if len(order) != len(affected):
            raise CycleError("dependency cycle among: %r" % sorted(
                (n for n in affected if n not in order), key=repr))
        return order
