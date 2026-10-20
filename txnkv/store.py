from txnkv.journal import UndoJournal


class Store:
    """An in-memory key/value store with nested transactions.

    Mutations made inside a transaction can be rolled back; ``begin`` opens a
    (possibly nested) transaction, ``commit`` keeps its changes, and ``rollback``
    discards them, restoring the exact prior state (including keys that did not
    previously exist). Mutations made with no open transaction are durable.
    """

    def __init__(self):
        self._data = {}
        self._journal = UndoJournal()

    def get(self, key):
        """Return the value for ``key`` or raise ``KeyError`` if absent."""
        return self._data[key]

    def _restore(self, key):
        """Return an inverse that puts ``key`` back to its current state."""
        if key in self._data:
            old = self._data[key]
            return lambda: self._data.__setitem__(key, old)
        return lambda: self._data.pop(key, None)

    def set(self, key, value):
        """Set ``key`` to ``value``, recording how to undo it."""
        undo = self._restore(key)
        self._data[key] = value
        self._journal.record(undo)

    def delete(self, key):
        """Delete ``key`` (``KeyError`` if absent), recording how to undo it."""
        if key not in self._data:
            raise KeyError(key)
        undo = self._restore(key)
        del self._data[key]
        self._journal.record(undo)

    def keys(self):
        """Return the current set of keys."""
        return set(self._data)

    def begin(self):
        """Open a new transaction (transactions may nest)."""
        self._journal.push()

    def commit(self):
        """Commit the innermost open transaction. ``RuntimeError`` if none is open."""
        if not self._journal.in_transaction():
            raise RuntimeError("no open transaction to commit")
        self._journal.commit()

    def rollback(self):
        """Roll back the innermost open transaction. ``RuntimeError`` if none is open."""
        if not self._journal.in_transaction():
            raise RuntimeError("no open transaction to roll back")
        self._journal.rollback()
