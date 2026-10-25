from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._graph.set_dependencies(name, ())
        self._formulas.pop(name, None)
        self._values[name] = value
        self._recompute(self._graph.affected_order(name)[1:])

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        dependencies = tuple(deps)
        old_dependencies = self._formulas.get(name, ((), None))[0]
        self._graph.set_dependencies(name, dependencies)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, old_dependencies)
            raise

        self._formulas[name] = (dependencies, fn)
        self._recompute(order)

    def _recompute(self, order):
        for name in order:
            formula = self._formulas.get(name)
            if formula is None:
                continue
            deps, fn = formula
            self._values[name] = fn({dep: self._values[dep] for dep in deps})

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
