from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def _recompute(self, name):
        """Evaluate formula `name` from current values, if all its inputs are set."""
        deps, fn = self._formulas[name]
        if all(d in self._values for d in deps):
            args = {d: self._values[d] for d in deps}
            self._values[name] = fn(args)
        else:
            # Inputs not yet available: leave the cell without a stale value.
            self._values.pop(name, None)

    def _propagate(self, order):
        """Recompute every formula in `order`, skipping the head constant if any."""
        for node in order:
            if node in self._formulas:
                self._recompute(node)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._formulas.pop(name, None)
        self._graph.set_dependencies(name, ())
        self._values[name] = value
        order = self._graph.affected_order(name)
        self._propagate(order)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        previous = self._formulas.get(name)
        previous_deps = previous[0] if previous is not None else ()

        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, previous_deps)
            raise

        self._formulas[name] = (deps, fn)
        self._propagate(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
