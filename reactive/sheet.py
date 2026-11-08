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
        deps = list(deps)
        old_deps = set(self._graph._deps.get(name, ()))
        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, old_deps)
            raise
        self._formulas[name] = (deps, fn)
        self._recompute_all(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _propagate(self, name):
        self._recompute_all(self._graph.affected_order(name)[1:])

    def _recompute_all(self, nodes):
        for node in nodes:
            self._recompute(node)

    def _recompute(self, node):
        formula = self._formulas.get(node)
        if formula is None:
            return
        deps, fn = formula
        if any(d not in self._values for d in deps):
            # Not all inputs are available yet; leave the cell unset.
            self._values.pop(node, None)
            return
        self._values[node] = fn({d: self._values[d] for d in deps})
