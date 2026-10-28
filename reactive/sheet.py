from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def _recompute(self, order):
        """Evaluate formulas in `order`, skipping constants.

        A formula whose dependencies are not all set becomes unset."""
        for node in order:
            if node not in self._formulas:
                continue
            deps, fn = self._formulas[node]
            if all(d in self._values for d in deps):
                args = {d: self._values[d] for d in deps}
                self._values[node] = fn(args)
            else:
                self._values.pop(node, None)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        # A constant has no dependencies; clear any formula edges and binding.
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        order = self._graph.affected_order(name)
        self._recompute(order)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        old_deps = set(self._graph._deps.get(name, set()))

        self._graph.set_dependencies(name, deps)
        try:
            order = self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, old_deps)
            raise

        self._formulas[name] = (deps, fn)
        self._recompute(order)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
