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
        for old in self._deps.get(node, set()) - new_deps:
            users = self._dependents.get(old)
            if users is not None:
                users.discard(node)
                if not users:
                    del self._dependents[old]
        for d in new_deps:
            self._dependents.setdefault(d, set()).add(node)
        if new_deps:
            self._deps[node] = new_deps
        else:
            self._deps.pop(node, None)

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return set(self._dependents.get(node, set()))

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Iterative DFS over dependent edges; reverse postorder is topological.
        WHITE, GRAY, BLACK = 0, 1, 2
        state = {start: GRAY}
        postorder = []
        stack = [(start, iter(self._dependents.get(start, ())))]
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                s = state.get(child, WHITE)
                if s == GRAY:
                    raise CycleError("dependency cycle involving %r" % (child,))
                if s == WHITE:
                    state[child] = GRAY
                    stack.append((child, iter(self._dependents.get(child, ()))))
                    advanced = True
                    break
            if not advanced:
                stack.pop()
                state[node] = BLACK
                postorder.append(node)
        postorder.reverse()
        return postorder
