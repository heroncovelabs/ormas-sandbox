from reactive.graph import DependencyGraph, CycleError


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def _recompute_from(self, order):
        """Evaluate every formula in `order`, in the given (topological) order."""
        for node in order:
            if node in self._formulas:
                deps, fn = self._formulas[node]
                inputs = {d: self._values[d] for d in deps}
                self._values[node] = fn(inputs)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        order = self._graph.affected_order(name)
        self._formulas.pop(name, None)
        self._graph.set_dependencies(name, [])
        self._values[name] = value
        self._recompute_from(order)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        new_deps = list(deps)
        old_deps = self._formulas[name][0] if name in self._formulas else []
        self._graph.set_dependencies(name, new_deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, old_deps)
            raise
        self._formulas[name] = (new_deps, fn)
        self._recompute_from(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
