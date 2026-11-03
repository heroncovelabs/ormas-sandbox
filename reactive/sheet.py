from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def _recompute(self, name):
        """Recompute a formula cell from its dependencies' current values."""
        deps, fn = self._formulas[name]
        if any(d not in self._values for d in deps):
            self._values.pop(name, None)
            return
        d = {dep: self._values[dep] for dep in deps}
        self._values[name] = fn(d)

    def _propagate(self, order):
        """Recompute every formula in `order` (which starts with the changed cell)."""
        for node in order[1:]:
            if node in self._formulas:
                self._recompute(node)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._formulas.pop(name, None)
        self._graph.set_dependencies(name, [])
        self._values[name] = value
        self._propagate(self._graph.affected_order(name))

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        old_formula = self._formulas.get(name)
        old_deps = set(self._graph._deps.get(name, set()))

        self._formulas[name] = (deps, fn)
        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            # Roll back so the sheet stays consistent.
            if old_formula is None:
                self._formulas.pop(name, None)
            else:
                self._formulas[name] = old_formula
            self._graph.set_dependencies(name, old_deps)
            raise

        self._recompute(name)
        self._propagate(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
