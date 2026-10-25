from reactive.graph import DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        old_formula = self._formulas.get(name)
        old_values = dict(self._values)

        # A constant has no dependencies.
        self._graph.set_dependencies(name, [])
        self._formulas.pop(name, None)
        self._values[name] = value
        try:
            self._recompute(name)
        except Exception:
            self._values = old_values
            if old_formula is not None:
                self._formulas[name] = old_formula
                self._graph.set_dependencies(name, old_formula[0])
            raise

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = list(deps)
        old_formula = self._formulas.get(name)
        old_values = dict(self._values)

        # Validates for cycles; the graph restores its previous state on error.
        self._graph.set_dependencies(name, deps)
        self._formulas[name] = (deps, fn)
        try:
            self._recompute(name)
        except Exception:
            self._values = old_values
            if old_formula is None:
                self._formulas.pop(name, None)
            else:
                self._formulas[name] = old_formula
            self._graph.set_dependencies(
                name, old_formula[0] if old_formula is not None else []
            )
            raise

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _recompute(self, start):
        """Recompute formulas in `start` and its dependents, in dependency order."""
        for node in self._graph.affected_order(start):
            formula = self._formulas.get(node)
            if formula is None:
                continue  # constant cells are left unchanged
            deps, fn = formula
            current = {d: self._values[d] for d in deps}
            self._values[node] = fn(current)
