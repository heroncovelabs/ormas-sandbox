from reactive.graph import DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        # A constant depends on nothing; drop any previous formula binding.
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        self._recompute(name)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        # Graph validates and commits atomically; on CycleError nothing changes.
        self._graph.set_dependencies(name, deps)
        self._formulas[name] = (deps, fn)
        self._recompute(name)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _recompute(self, start):
        """Recompute `start` and its transitive dependents in dependency order."""
        for node in self._graph.affected_order(start):
            binding = self._formulas.get(node)
            if binding is None:
                continue  # constants keep their stored value
            deps, fn = binding
            if any(d not in self._values for d in deps):
                # Some input has never been set; leave the cell without a value.
                self._values.pop(node, None)
                continue
            args = {d: self._values[d] for d in deps}
            self._values[node] = fn(args)
