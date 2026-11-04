"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).

Engine behaviors that differ from the spec, reproduced here:

- Records live in a fixed slot table; deleted slots go on a LIFO free
  list and are reused before fresh slots. Scans walk the table in slot
  order, not insertion order.
- Names are accepted up to 16 characters but stored truncated to 12.
- ``INS`` of an existing id (after validation) updates its score only.
- ``FIND``: the first character compares case-sensitively, the rest
  case-insensitively. A trailing ``*`` makes it a prefix match; any other
  ``*`` is literal.
- ``RANGE`` is ``lo <= score < hi``, except ``lo == hi`` matches that score.
- ``SUM`` wraps to a signed 32-bit value; ``AVG`` divides the exact sum,
  truncating toward zero.
- Extra trailing arguments are ignored; a whitespace-only line is ``ERR FMT``.
"""

from __future__ import annotations

import re
import sys

CAPACITY = 4096
NAME_STORED = 12
SCORE_MIN, SCORE_MAX = -999_999, 999_999

_ALNUM = re.compile(r"[A-Za-z0-9]+")
_INT = re.compile(r"[+-]?[0-9]+")


class Store:
    def __init__(self, out=None):
        self.slots: list[dict | None] = []  # slot order
        self.free: list[int] = []  # LIFO of vacated slots
        self.index: dict[str, int] = {}  # id -> slot
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _find(self, record_id: str) -> dict | None:
        slot = self.index.get(record_id)
        return None if slot is None else self.slots[slot]

    def _rows(self):
        return (row for row in self.slots if row is not None)

    # -- commands -----------------------------------------------------------

    def ins(self, record_id: str, name: str, score_token: str) -> None:
        score = _parse_score(score_token)
        if not _alnum(record_id, 1, 8) or not _alnum(name, 1, 16) or score is None:
            self._emit("ERR FMT")
            return
        existing = self._find(record_id)
        if existing is not None:
            existing["score"] = score
            self._emit("OK")
            return
        if len(self.index) >= CAPACITY:
            self._emit("ERR FULL")
            return
        row = {"id": record_id, "name": name[:NAME_STORED], "score": score}
        if self.free:
            slot = self.free.pop()
            self.slots[slot] = row
        else:
            slot = len(self.slots)
            self.slots.append(row)
        self.index[record_id] = slot
        self._emit("OK")

    def delete(self, record_id: str) -> None:
        if not _alnum(record_id, 1, 8):
            self._emit("ERR FMT")
            return
        slot = self.index.pop(record_id, None)
        if slot is None:
            self._emit("ERR NOTFOUND")
            return
        self.slots[slot] = None
        self.free.append(slot)
        self._emit("OK")

    def get(self, record_id: str) -> None:
        if not _alnum(record_id, 1, 8):
            self._emit("ERR FMT")
            return
        row = self._find(record_id)
        if row is None:
            self._emit("ERR NOTFOUND")
            return
        self._emit(_row(row))

    def find(self, pattern: str) -> None:
        if not 0 < len(pattern) <= 17:
            self._emit("ERR FMT")
            return
        prefix = pattern.endswith("*")
        if prefix:
            pattern = pattern[:-1]
        count = 0
        for row in self._rows():
            if _name_matches(row["name"], pattern, prefix):
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
        if not self.index:
            self._emit("ERR EMPTY")
            return
        total = sum(row["score"] for row in self._rows())
        count = len(self.index)
        avg = abs(total) // count
        self._emit(f"AVG {-avg if total < 0 else avg}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        if not parts:
            self._emit("ERR FMT")
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
    return lo <= len(value) <= hi and _ALNUM.fullmatch(value) is not None


def _name_matches(name: str, pattern: str, prefix: bool) -> bool:
    if prefix:
        if len(name) < len(pattern):
            return False
        name = name[: len(pattern)]
    elif len(name) != len(pattern):
        return False
    if not pattern:
        return True
    return name[0] == pattern[0] and name[1:].lower() == pattern[1:].lower()


def _parse_score(token: str) -> int | None:
    if _INT.fullmatch(token) is None:
        return None
    value = int(token)
    if not SCORE_MIN <= value <= SCORE_MAX:
        return None
    return value


def main() -> None:
    store = Store()
    for line in sys.stdin:
        store.handle(line)


if __name__ == "__main__":
    main()
