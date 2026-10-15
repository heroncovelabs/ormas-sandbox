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
        self._graph.set_dependencies(name, [])
        self._values[name] = value
        self._propagate(name)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        old_formula = self._formulas.get(name)
        old_deps = old_formula[0] if old_formula else []
        self._graph.set_dependencies(name, deps)
        try:
            # affected_order raises CycleError if the new deps create a cycle.
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, old_deps)
            raise
        self._formulas[name] = (list(deps), fn)
        self._recompute(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _propagate(self, name):
        self._recompute(self._graph.affected_order(name))

    def _recompute(self, order):
        for node in order:
            formula = self._formulas.get(node)
            if formula is None:
                continue
            deps, fn = formula
            if all(d in self._values for d in deps):
                self._values[node] = fn({d: self._values[d] for d in deps})
