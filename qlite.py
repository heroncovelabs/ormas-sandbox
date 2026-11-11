"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).

Engine behaviors that differ from the spec (reproduced deliberately):

- Records live in fixed slots; deleted slots go on a LIFO free list and are
  reused by later inserts. Scans walk slots in index order.
- Names accept 1-16 alphanumerics but only the first 12 are stored.
- ``INS`` of an existing id updates the score only (the name is kept).
- ``FIND`` compares the first character exactly and the rest
  case-insensitively. ``*`` is a wildcard only as the final character
  (prefix match); anywhere else it is a literal.
- ``RANGE lo hi`` is half-open (``lo <= score < hi``), except that
  ``lo == hi`` matches that exact score.
- ``SUM`` wraps to a signed 32-bit integer; ``AVG`` divides the exact sum,
  truncating toward zero.
- Extra trailing arguments are ignored; missing arguments are ``ERR FMT``.
  Empty lines are skipped silently; whitespace-only lines are ``ERR FMT``.
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
        self.slots: list[dict | None] = []
        self.free: list[int] = []  # LIFO stack of vacated slot indexes
        self.index: dict[str, int] = {}
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _rows(self):
        return (row for row in self.slots if row is not None)

    # -- commands -----------------------------------------------------------

    def ins(self, record_id: str, name: str, score_token: str) -> None:
        score = _parse_score(score_token)
        if not _alnum(record_id, 1, 8) or not _alnum(name, 1, 16) or score is None:
            self._emit("ERR FMT")
            return
        slot = self.index.get(record_id)
        if slot is not None:
            self.slots[slot]["score"] = score
            self._emit("OK")
            return
        row = {"id": record_id, "name": name[:NAME_STORED], "score": score}
        if self.free:
            slot = self.free.pop()
            self.slots[slot] = row
        elif len(self.slots) < CAPACITY:
            slot = len(self.slots)
            self.slots.append(row)
        else:
            self._emit("ERR FULL")
            return
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
        slot = self.index.get(record_id)
        if slot is None:
            self._emit("ERR NOTFOUND")
            return
        self._emit(_row(self.slots[slot]))

    def find(self, pattern: str) -> None:
        if not 0 < len(pattern) <= 17:
            self._emit("ERR FMT")
            return
        if pattern.endswith("*"):
            needle, prefix = pattern[:-1], True
        else:
            needle, prefix = pattern, False
        count = 0
        for row in self._rows():
            name = row["name"]
            if prefix:
                if len(name) < len(needle):
                    continue
                name = name[: len(needle)]
            elif len(name) != len(needle):
                continue
            if _name_eq(name, needle):
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
        total = sum(row["score"] for row in self._rows())
        total = (total + 2**31) % 2**32 - 2**31
        self._emit(f"SUM {total}")

    def avg_scores(self) -> None:
        scores = [row["score"] for row in self._rows()]
        if not scores:
            self._emit("ERR EMPTY")
            return
        total = sum(scores)
        avg = abs(total) // len(scores)
        self._emit(f"AVG {-avg if total < 0 else avg}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        cmd = parts[0] if parts else ""
        if cmd == "INS" and len(parts) >= 4:
            self.ins(parts[1], parts[2], parts[3])
        elif cmd == "DEL" and len(parts) >= 2:
            self.delete(parts[1])
        elif cmd == "GET" and len(parts) >= 2:
            self.get(parts[1])
        elif cmd == "FIND" and len(parts) >= 2:
            self.find(parts[1])
        elif cmd == "RANGE" and len(parts) >= 3:
            self.range(parts[1], parts[2])
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


def _name_eq(name: str, needle: str) -> bool:
    if not needle:
        return True
    return name[0] == needle[0] and name[1:].lower() == needle[1:].lower()


def _alnum(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and _ALNUM.fullmatch(value) is not None


def _parse_score(token: str) -> int | None:
    if not _INT.fullmatch(token):
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
