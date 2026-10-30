class CycleError(Exception):
    """Raised when a dependency cycle is detected among affected cells."""


class DependencyGraph:
    """Tracks which cells depend on which other cells."""

    def __init__(self):
        self._deps = {}  # node -> set of nodes it directly depends on

    def _reachable_from(self, sources):
        """Nodes reachable from `sources` by following dependency edges."""
        seen = set()
        stack = list(sources)
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self._deps.get(cur, ()))
        return seen

    def set_dependencies(self, node, deps):
        """Replace node's direct dependencies with deps (clearing any previous)."""
        new_deps = set(deps)
        # A cycle would form if node is reachable from any proposed dependency
        # (this also covers direct self-reference).
        if node in self._reachable_from(new_deps):
            raise CycleError(f"dependency cycle through {node!r}")
        # Validation passed; commit atomically.
        self._deps[node] = new_deps

    def dependents(self, node):
        """Direct dependents: the set of nodes that depend on `node`."""
        return {n for n, ds in self._deps.items() if node in ds}

    def affected_order(self, start):
        """`start` plus all transitive dependents, ordered so each node comes
        after every dependency of it that is in the set. Raises CycleError on a
        cycle among the affected nodes."""
        # Build reverse index once: dependency -> nodes that directly depend on it.
        rev = {}
        for n, ds in self._deps.items():
            for d in ds:
                rev.setdefault(d, set()).add(n)

        # Collect start and all transitive dependents iteratively.
        affected = {start}
        stack = [start]
        while stack:
            cur = stack.pop()
            for c in rev.get(cur, ()):
                if c not in affected:
                    affected.add(c)
                    stack.append(c)

        # Kahn's algorithm restricted to the affected subgraph.
        indeg = {n: 0 for n in affected}
        for n in affected:
            for d in self._deps.get(n, ()):
                if d in affected:
                    indeg[n] += 1

        ready = [n for n in affected if indeg[n] == 0]
        order = []
        while ready:
            cur = ready.pop()
            order.append(cur)
            for c in rev.get(cur, ()):
                if c in affected:
                    indeg[c] -= 1
                    if indeg[c] == 0:
                        ready.append(c)

        if len(order) != len(affected):
            raise CycleError("dependency cycle among affected nodes")
        return order
