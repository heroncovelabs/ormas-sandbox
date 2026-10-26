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

    def set(self, key, value):
        """Set ``key`` to ``value``, recording how to undo it."""
        existed = key in self._data
        old_value = self._data.get(key)

        if existed:
            def undo():
                self._data[key] = old_value
        else:
            def undo():
                self._data.pop(key, None)

        self._data[key] = value
        self._journal.record(undo)

    def delete(self, key):
        """Delete ``key`` (``KeyError`` if absent), recording how to undo it."""
        old_value = self._data.pop(key)  # raises KeyError before any recording

        def undo():
            self._data[key] = old_value

        self._journal.record(undo)

    def keys(self):
        """Return the current set of keys."""
        return set(self._data.keys())

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
