from reactive.graph import DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._formulas.pop(name, None)
        self._graph.set_dependencies(name, ())
        self._values[name] = value
        for node in self._graph.affected_order(name):
            if node == name:
                continue
            self._recompute(node)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        previous = self._formulas.get(name)
        self._graph.set_dependencies(name, deps)
        self._formulas[name] = (deps, fn)
        try:
            order = self._graph.affected_order(name)
        except Exception:
            # Roll back to the previous binding so the sheet stays consistent.
            self._graph.set_dependencies(name, previous[0] if previous else ())
            if previous is None:
                self._formulas.pop(name, None)
            raise
        for node in order:
            self._recompute(node)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _recompute(self, node):
        formula = self._formulas.get(node)
        if formula is None:
            return
        deps, fn = formula
        self._values[node] = fn({dep: self._values[dep] for dep in deps})
