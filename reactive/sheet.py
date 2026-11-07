from reactive.graph import DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        self._recompute(self._graph.affected_order(name))

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        previous = self._graph.dependencies(name)
        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except Exception:
            self._graph.set_dependencies(name, previous)
            raise
        self._formulas[name] = (deps, fn)
        self._recompute(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _recompute(self, order):
        for node in order:
            formula = self._formulas.get(node)
            if formula is None:
                continue
            deps, fn = formula
            self._values[node] = fn({d: self._values[d] for d in deps})
