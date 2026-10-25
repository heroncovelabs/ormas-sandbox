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
        if key in self._data:
            previous_value = self._data[key]

            def undo():
                self._data[key] = previous_value
        else:

            def undo():
                self._data.pop(key, None)

        self._journal.record(undo)
        self._data[key] = value

    def delete(self, key):
        """Delete ``key`` (``KeyError`` if absent), recording how to undo it."""
        previous_value = self._data[key]

        def undo():
            self._data[key] = previous_value

        self._journal.record(undo)
        del self._data[key]

    def keys(self):
        """Return the current set of keys."""
        return set(self._data)

    def begin(self):
        """Open a new transaction (transactions may nest)."""
        self._journal.push()

    def commit(self):
        """Commit the innermost open transaction. ``RuntimeError`` if none is open."""
        self._journal.commit()

    def rollback(self):
        """Roll back the innermost open transaction. ``RuntimeError`` if none is open."""
        self._journal.rollback()
