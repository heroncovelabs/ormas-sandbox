from reactive.graph import CycleError, DependencyGraph


class Sheet:
    """A spreadsheet of cells; each is a constant or a formula over other cells."""

    def __init__(self):
        self._graph = DependencyGraph()
        self._values = {}
        self._formulas = {}  # node -> (deps tuple, fn)

    def set_value(self, name, value):
        """Set `name` to a constant, then recompute its dependents."""
        self._values[name] = value
        if name in self._formulas:
            del self._formulas[name]
            self._graph.set_dependencies(name, ())
        for node in self._graph.affected_order(name):
            self._recompute(node)

    def set_formula(self, name, deps, fn):
        """Set `name` to fn(values_of_deps); recompute it and its dependents.

        Raises CycleError if this introduces a dependency cycle."""
        deps = tuple(deps)
        if self._creates_cycle(name, deps):
            raise CycleError("setting %r would create a dependency cycle" % (name,))
        self._formulas[name] = (deps, fn)
        self._graph.set_dependencies(name, deps)
        for node in self._graph.affected_order(name):
            self._recompute(node)

    def get(self, name):
        """Return the current value of `name` (KeyError if unset)."""
        return self._values[name]

    def _creates_cycle(self, name, deps):
        """True if making `name` depend on `deps` closes a dependency cycle."""
        stack = list(deps)
        seen = set()
        while stack:
            node = stack.pop()
            if node == name:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(self._graph.dependents(node))
        return False

    def _recompute(self, name):
        entry = self._formulas.get(name)
        if entry is None:
            return
        deps, fn = entry
        values = {dep: self._values[dep] for dep in deps}
        self._values[name] = fn(values)
