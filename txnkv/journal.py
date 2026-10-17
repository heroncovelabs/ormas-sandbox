class UndoJournal:
    """A stack of transaction frames holding inverse operations."""

    def __init__(self):
        self._frames = []

    def in_transaction(self):
        return bool(self._frames)

    def push(self):
        self._frames.append([])

    def record(self, undo):
        if self._frames:
            self._frames[-1].append(undo)

    def rollback(self):
        frame = self._frames.pop()
        for undo in reversed(frame):
            undo()

    def commit(self):
        frame = self._frames.pop()
        if self._frames:
            self._frames[-1].extend(frame)
