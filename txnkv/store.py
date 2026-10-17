from txnkv.journal import UndoJournal


class Store:
    """An in-memory key/value store with nested transactions."""

    def __init__(self):
        self._data = {}
        self._journal = UndoJournal()

    def get(self, key):
        return self._data[key]

    def _record_restore(self, key):
        if key in self._data:
            old = self._data[key]
            self._journal.record(lambda: self._data.__setitem__(key, old))
        else:
            self._journal.record(lambda: self._data.pop(key, None))

    def set(self, key, value):
        self._record_restore(key)
        self._data[key] = value

    def delete(self, key):
        if key not in self._data:
            raise KeyError(key)
        self._record_restore(key)
        del self._data[key]

    def keys(self):
        return set(self._data)

    def begin(self):
        self._journal.push()

    def commit(self):
        if not self._journal.in_transaction():
            raise RuntimeError("no open transaction")
        self._journal.commit()

    def rollback(self):
        if not self._journal.in_transaction():
            raise RuntimeError("no open transaction")
        self._journal.rollback()
