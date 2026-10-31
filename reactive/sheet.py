from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def _recompute(self, order):
        """Evaluate every formula in `order` (dependency-first)."""
        for node in order:
            formula = self._formulas.get(node)
            if formula is None:
                continue
            deps, fn = formula
            args = {d: self._values[d] for d in deps}
            self._values[node] = fn(args)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._graph.set_dependencies(name, ())
        self._formulas.pop(name, None)
        self._values[name] = value
        order = self._graph.affected_order(name)
        self._recompute(order)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = tuple(deps)
        previous = self._formulas.get(name)
        prev_deps = previous[0] if previous is not None else ()

        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, prev_deps)
            raise

        self._formulas[name] = (deps, fn)
        self._recompute(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
