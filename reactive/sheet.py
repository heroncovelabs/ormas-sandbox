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

        for node in self._graph.affected_order(name):
            formula = self._formulas.get(node)
            if formula is not None:
                self._recompute(node, formula)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        previous = self._formulas.get(name)
        previous_deps = list(previous[0]) if previous is not None else []

        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, previous_deps)
            raise

        self._formulas[name] = (deps, fn)
        self._recompute(name, self._formulas[name])

        for node in order:
            if node == name:
                continue
            formula = self._formulas.get(node)
            if formula is not None:
                self._recompute(node, formula)

    def _recompute(self, name, formula):
        deps, fn = formula
        values = {}
        for dep in deps:
            values[dep] = self._values[dep]
        self._values[name] = fn(values)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
