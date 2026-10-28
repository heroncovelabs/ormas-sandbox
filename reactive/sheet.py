from reactive.graph import DependencyGraph


class _Missing:
    """Sentinel for a dependency that has no value yet."""

    def __repr__(self):
        return "<missing>"


MISSING = _Missing()


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
        self._recompute_affected(name)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        self._graph.set_dependencies(name, deps)  # raises CycleError on a cycle
        self._formulas[name] = (deps, fn)
        self._recompute_affected(name)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        if name not in self._values:
            raise KeyError(name)
        return self._values[name]

    def _recompute_affected(self, start):
        for node in self._graph.affected_order(start):
            formula = self._formulas.get(node)
            if formula is None:
                continue
            deps, fn = formula
            values = {dep: self._values.get(dep, MISSING) for dep in deps}
            self._values[node] = fn(values)
