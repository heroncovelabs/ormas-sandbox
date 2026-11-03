from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        self._propagate(name, skip_start=True)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        prev_deps = self._formulas[name][0] if name in self._formulas else []

        self._graph.set_dependencies(name, deps)
        try:
            self._graph.affected_order(name)
        except CycleError:
            self._graph.set_dependencies(name, prev_deps)
            raise

        self._formulas[name] = (deps, fn)
        self._propagate(name, skip_start=False)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _propagate(self, start, skip_start):
        """Recompute formulas in affected_order starting from `start`."""
        for node in self._graph.affected_order(start):
            if node == start and skip_start:
                continue
            if node not in self._formulas:
                continue
            node_deps, fn = self._formulas[node]
            if all(d in self._values for d in node_deps):
                self._values[node] = fn({d: self._values[d] for d in node_deps})
            else:
                self._values.pop(node, None)
