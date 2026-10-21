from reactive.graph import DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def _propagate(self, name):
        """Recompute `name` (if it is a formula) and every downstream formula,
        in dependency order. Each formula is evaluated exactly once."""
        for node in self._graph.affected_order(name):
            if node in self._formulas:
                deps, fn = self._formulas[node]
                self._values[node] = fn({d: self._values[d] for d in deps})

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        self._propagate(name)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        # Validate the cycle first; the graph restores itself on failure,
        # so formulas and values stay untouched if this raises.
        self._graph.set_dependencies(name, deps)
        self._formulas[name] = (deps, fn)
        self._propagate(name)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]
