from reactive.graph import DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        # A constant has no dependencies; this also drops any previous formula edges.
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        self._recompute(self._graph.affected_order(name))

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        dep_seq = list(dict.fromkeys(deps))  # stable, de-duplicated
        # Raises CycleError before any state is committed (graph restores itself).
        self._graph.set_dependencies(name, dep_seq)
        self._formulas[name] = (dep_seq, fn)
        self._recompute(self._graph.affected_order(name))

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _recompute(self, order):
        """Evaluate each formula in `order` once, using current dependency values.

        Constants are left untouched. A formula whose dependencies are not all
        set yet stays unset."""
        for node in order:
            if node not in self._formulas:
                continue
            deps, fn = self._formulas[node]
            if any(d not in self._values for d in deps):
                self._values.pop(node, None)
                continue
            env = {d: self._values[d] for d in deps}
            self._values[node] = fn(env)
