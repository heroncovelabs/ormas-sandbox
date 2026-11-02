from reactive.graph import CycleError, DependencyGraph


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
        self._recompute(self._graph.affected_order(name))

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = tuple(deps)
        previous = self._formulas.get(name)
        previous_deps = previous[0] if previous is not None else ()
        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, previous_deps)
            raise

        self._formulas[name] = (deps, fn)
        self._recompute(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _recompute(self, order):
        """Recompute formula cells in dependency-first order."""
        for node in order:
            if node in self._formulas:
                deps, fn = self._formulas[node]
                values = {dep: self._values[dep] for dep in deps}
                self._values[node] = fn(values)
