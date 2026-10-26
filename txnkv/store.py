from txnkv.journal import UndoJournal

_MISSING = object()


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
        data = self._data
        old = data.get(key, _MISSING)
        if old is _MISSING:
            def undo():
                data.pop(key, None)
        else:
            def undo():
                data[key] = old
        data[key] = value
        self._journal.record(undo)

    def delete(self, key):
        """Delete ``key`` (``KeyError`` if absent), recording how to undo it."""
        old = self._data[key]
        del self._data[key]
        self._journal.record(lambda: self._data.__setitem__(key, old))

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
