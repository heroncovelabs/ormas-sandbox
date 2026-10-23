"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).

Engine behaviors that differ from the spec (all reproduced here):

- Records live in fixed slots; deleted slots go on a LIFO free list and
  are reused by later inserts, so scan order is slot order, not
  insertion order.
- Names are stored truncated to 12 characters.
- Inserting an existing id updates its score (the name is kept).
- FIND compares the first character case-sensitively and the rest
  case-insensitively; ``*`` is a wildcard only as the final character
  (prefix match), anywhere else it is literal.
- RANGE excludes ``hi`` unless ``lo == hi``.
- SUM wraps to a signed 32-bit integer; AVG truncates toward zero.
- Extra arguments after a command's operands are ignored.
"""

from __future__ import annotations

import re
import sys

CAPACITY = 4096
NAME_STORED = 12
SCORE_MIN, SCORE_MAX = -999_999, 999_999

_ALNUM = re.compile(r"[A-Za-z0-9]+")
_INT = re.compile(r"[+-]?[0-9]+")
_WS = re.compile(r"[ \t\v\f\r\n]+")  # ASCII whitespace only

# operand count per command
_ARITY = {"INS": 3, "DEL": 1, "GET": 1, "FIND": 1, "RANGE": 2, "LIST": 0, "SUM": 0, "AVG": 0}


class Store:
    def __init__(self, out=None):
        self.slots: list[dict | None] = []  # scan order is slot order
        self.free: list[int] = []  # LIFO free list of slot indexes
        self.count = 0
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
        if self.count >= CAPACITY:
            self._emit("ERR FULL")
            return
        row = {"id": record_id, "name": name[:NAME_STORED], "score": score}
        if self.free:
            self.slots[self.free.pop()] = row
        else:
            self.slots.append(row)
        self.count += 1
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
        self.count -= 1
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
            if _match(pattern, row["name"]):
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
            if lo <= score and (score < hi or (lo == hi and score == lo)):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        for row in self._rows():
            self._emit(_row(row))
        self._emit(f"END {self.count}")

    def sum_scores(self) -> None:
        total = sum(row["score"] for row in self._rows()) & 0xFFFFFFFF
        if total >= 0x80000000:
            total -= 0x100000000
        self._emit(f"SUM {total}")

    def avg_scores(self) -> None:
        if not self.count:
            self._emit("ERR EMPTY")
            return
        total = sum(row["score"] for row in self._rows())
        avg = abs(total) // self.count
        self._emit(f"AVG {-avg if total < 0 else avg}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        line = line.rstrip("\n").split("\r", 1)[0]  # the engine stops at "\r"
        if not line:
            return  # empty lines are skipped; whitespace-only ones are not
        parts = _WS.split(line.strip(" \t\v\f\r\n"))
        cmd, args = parts[0], parts[1:]
        arity = _ARITY.get(cmd)
        if arity is None or len(args) < arity:
            self._emit("ERR FMT")
            return
        if cmd == "INS":
            self.ins(args[0], args[1], args[2])
        elif cmd == "DEL":
            self.delete(args[0])
        elif cmd == "GET":
            self.get(args[0])
        elif cmd == "FIND":
            self.find(args[0])
        elif cmd == "RANGE":
            self.range(args[0], args[1])
        elif cmd == "LIST":
            self.list_all()
        elif cmd == "SUM":
            self.sum_scores()
        elif cmd == "AVG":
            self.avg_scores()


def _row(row: dict) -> str:
    return f"ROW {row['id']} {row['name']} {row['score']}"


def _alnum(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and _ALNUM.fullmatch(value) is not None


def _same(a: str, b: str) -> bool:
    """First character exact, the rest case-insensitive (ASCII)."""
    if len(a) != len(b):
        return False
    if not a:
        return True
    return a[0] == b[0] and _lower(a[1:]) == _lower(b[1:])


def _lower(value: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in value)


def _match(pattern: str, name: str) -> bool:
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        return _same(prefix, name[: len(prefix)])
    return _same(pattern, name)


def _parse_score(token: str) -> int | None:
    if _INT.fullmatch(token) is None:
        return None
    value = int(token)
    if not SCORE_MIN <= value <= SCORE_MAX:
        return None
    return value


def main() -> None:
    store = Store()
    # raw bytes: text mode would turn a lone "\r" into a line break
    for raw in sys.stdin.buffer:
        store.handle(raw.decode("utf-8", "surrogateescape"))


if __name__ == "__main__":
    main()
