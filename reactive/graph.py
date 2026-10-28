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

        # Drop old reverse links.
        for old in self._deps.get(node, ()):
            parents = self._dependents.get(old)
            if parents is not None:
                parents.discard(node)
                if not parents:
                    del self._dependents[old]

        self._deps[node] = set(deps)
        for dep in deps:
            self._dependents.setdefault(dep, set()).add(node)

        try:
            if self._has_cycle():
                raise CycleError("dependency cycle involving %r" % (node,))
        except CycleError:
            # Roll back to the previous dependency set before propagating.
            self._deps[node] = set()
            for dep in deps:
                parents = self._dependents[dep]
                parents.discard(node)
                if not parents:
                    del self._dependents[dep]
            raise

    def _has_cycle(self):
        """True if any node reachable backwards from any node forms a cycle."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {}
        for root in self._deps:
            if color.get(root, WHITE) != WHITE:
                continue
            stack = [(root, iter(self._deps.get(root, ())))]
            color[root] = GRAY
            while stack:
                node, it = stack[-1]
                advanced = False
                for dep in it:
                    state = color.get(dep, WHITE)
                    if state == GRAY:
                        return True
                    if state == WHITE:
                        color[dep] = GRAY
                        stack.append((dep, iter(self._deps.get(dep, ()))))
                        advanced = True
                        break
                if not advanced:
                    color[node] = BLACK
                    stack.pop()
        return False

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._dependents.get(node, ()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        affected = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for child in self._dependents.get(node, ()):
                if child not in affected:
                    affected.add(child)
                    stack.append(child)

        # Count in-set dependencies for each affected node.
        pending = {}
        for node in affected:
            pending[node] = len(self._deps.get(node, set()) & affected)

        order = []
        ready = [n for n in affected if pending[n] == 0]
        while ready:
            node = ready.pop()
            order.append(node)
            for child in self._dependents.get(node, ()):
                if child in affected:
                    pending[child] -= 1
                    if pending[child] == 0:
                        ready.append(child)

        if len(order) != len(affected):
            raise CycleError("dependency cycle among affected cells")
        return order
