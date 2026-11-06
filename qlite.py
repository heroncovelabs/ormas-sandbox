"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).

Engine behavior that differs from the spec, reproduced here:

- Records live in fixed slots; deleted slots go on a LIFO free list and are
  reused by later inserts. ``LIST``/``FIND``/``RANGE`` scan in slot order.
- ``FIND`` compares the first character exactly and the rest
  case-insensitively. ``*`` is a wildcard only as the last pattern
  character (prefix match); anywhere else it is a literal.
- ``RANGE lo hi`` is half-open (``lo <= score < hi``), except that
  ``lo == hi`` matches that exact score.
- ``INS`` of an existing id updates its score (the name is kept).
- Names are stored truncated to 12 characters.
- ``AVG`` truncates toward zero; ``SUM`` wraps as a signed 32-bit integer.
- Arguments beyond those a command needs are ignored.
"""

from __future__ import annotations

import re
import sys

CAPACITY = 4096
SCORE_MIN, SCORE_MAX = -999_999, 999_999
NAME_STORED = 12

_WS = re.compile(r"[ \t\n\v\f\r]+")
_SCORE = re.compile(r"[+-]?[0-9]+\Z")
_ALNUM = re.compile(r"[A-Za-z0-9]+\Z")


class Store:
    def __init__(self, out=None):
        self.slots: list[dict | None] = []
        self.free: list[int] = []  # LIFO stack of vacated slot indexes
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _rows(self):
        return (row for row in self.slots if row is not None)

    def _find(self, record_id: str) -> int | None:
        for index, row in enumerate(self.slots):
            if row is not None and row["id"] == record_id:
                return index
        return None

    # -- commands -----------------------------------------------------------

    def ins(self, record_id: str, name: str, score_token: str) -> None:
        score = _parse_score(score_token)
        if not _alnum(record_id, 1, 8) or not _alnum(name, 1, 16) or score is None:
            self._emit("ERR FMT")
            return
        index = self._find(record_id)
        if index is not None:
            self.slots[index]["score"] = score
            self._emit("OK")
            return
        row = {"id": record_id, "name": name[:NAME_STORED], "score": score}
        if self.free:
            self.slots[self.free.pop()] = row
        elif len(self.slots) < CAPACITY:
            self.slots.append(row)
        else:
            self._emit("ERR FULL")
            return
        self._emit("OK")

    def delete(self, record_id: str) -> None:
        if not _alnum(record_id, 1, 8):
            self._emit("ERR FMT")
            return
        index = self._find(record_id)
        if index is None:
            self._emit("ERR NOTFOUND")
            return
        self.slots[index] = None
        self.free.append(index)
        self._emit("OK")

    def get(self, record_id: str) -> None:
        if not _alnum(record_id, 1, 8):
            self._emit("ERR FMT")
            return
        index = self._find(record_id)
        if index is None:
            self._emit("ERR NOTFOUND")
            return
        self._emit(_row(self.slots[index]))

    def find(self, pattern: str) -> None:
        if not 0 < len(pattern) <= 17:
            self._emit("ERR FMT")
            return
        count = 0
        for row in self._rows():
            if _match(row["name"], pattern):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def range(self, lo_token: str, hi_token: str) -> None:
        lo, hi = _parse_score(lo_token), _parse_score(hi_token)
        if lo is None or hi is None:
            self._emit("ERR FMT")
            return
        count = 0
        for row in self._rows():
            score = row["score"]
            if lo <= score < hi or lo == hi == score:
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        count = 0
        for row in self._rows():
            self._emit(_row(row))
            count += 1
        self._emit(f"END {count}")

    def sum_scores(self) -> None:
        total = sum(row["score"] for row in self._rows()) & 0xFFFFFFFF
        if total >= 0x80000000:
            total -= 0x100000000
        self._emit(f"SUM {total}")

    def avg_scores(self) -> None:
        scores = [row["score"] for row in self._rows()]
        if not scores:
            self._emit("ERR EMPTY")
            return
        total = sum(scores)
        mean = abs(total) // len(scores)
        self._emit(f"AVG {-mean if total < 0 else mean}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        line = line.split("\0", 1)[0]
        parts = [part for part in _WS.split(line) if part]
        if not parts:
            return
        cmd, args = parts[0], parts[1:]
        if cmd == "INS" and len(args) >= 3:
            self.ins(args[0], args[1], args[2])
        elif cmd == "DEL" and len(args) >= 1:
            self.delete(args[0])
        elif cmd == "GET" and len(args) >= 1:
            self.get(args[0])
        elif cmd == "FIND" and len(args) >= 1:
            self.find(args[0])
        elif cmd == "RANGE" and len(args) >= 2:
            self.range(args[0], args[1])
        elif cmd == "LIST":
            self.list_all()
        elif cmd == "SUM":
            self.sum_scores()
        elif cmd == "AVG":
            self.avg_scores()
        else:
            self._emit("ERR FMT")


def _row(row: dict) -> str:
    return f"ROW {row['id']} {row['name']} {row['score']}"


def _alnum(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and _ALNUM.match(value) is not None


def _same(name: str, pattern: str) -> bool:
    """First character exact, remaining characters case-insensitive."""
    if len(name) != len(pattern):
        return False
    if not pattern:
        return True
    return name[0] == pattern[0] and name[1:].lower() == pattern[1:].lower()


def _match(name: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        return _same(name[: len(prefix)], prefix)
    return _same(name, pattern)


def _parse_score(token: str) -> int | None:
    if _SCORE.match(token) is None:
        return None
    value = int(token)
    if not SCORE_MIN <= value <= SCORE_MAX:
        return None
    return value


def main() -> None:
    stdin = open(sys.stdin.fileno(), "r", encoding="latin-1", newline="\n", closefd=False)
    sys.stdout.reconfigure(encoding="latin-1")
    store = Store()
    for line in stdin:
        store.handle(line)


if __name__ == "__main__":
    main()
