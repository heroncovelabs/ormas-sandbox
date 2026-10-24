"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).
"""

from __future__ import annotations

import re
import sys

CAPACITY = 4096
NAME_MAX = 12
SCORE_MIN, SCORE_MAX = -999_999, 999_999


class Store:
    def __init__(self, out=None):
        self.slots: list[dict | None] = []  # slot array
        self.free: list[int] = []  # freed slot indices, reused LIFO
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _rows(self) -> list[dict]:
        return [row for row in self.slots if row is not None]

    def _find(self, record_id: str) -> dict | None:
        for row in self._rows():
            if row["id"] == record_id:
                return row
        return None

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
        row = {"id": record_id, "name": name[:NAME_MAX], "score": score}
        if self.free:
            self.slots[self.free.pop()] = row
        elif len(self.slots) >= CAPACITY:
            self._emit("ERR FULL")
            return
        else:
            self.slots.append(row)
        self._emit("OK")

    def delete(self, record_id: str) -> None:
        if not _alnum(record_id, 1, 8):
            self._emit("ERR FMT")
            return
        for i, slot in enumerate(self.slots):
            if slot is not None and slot["id"] == record_id:
                self.slots[i] = None
                self.free.append(i)
                self._emit("OK")
                return
        self._emit("ERR NOTFOUND")

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
        # Only a trailing '*' is a wildcard (prefix match); anything else is
        # an exact, case-sensitive comparison (a '*' elsewhere matches nothing).
        # The first character must match exactly; the rest compare
        # case-insensitively (engine behaviour).
        if pattern.endswith("*"):
            target, whole = pattern[:-1], False
        else:
            target, whole = pattern, True
        count = 0
        for row in self._rows():
            if _name_matches(row["name"], target, whole):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def range(self, lo_token: str, hi_token: str) -> None:
        lo, hi = _parse_score(lo_token), _parse_score(hi_token)
        if lo is None or hi is None:
            self._emit("ERR FMT")
            return
        # Lower bound inclusive, upper bound exclusive; lo == hi is equality.
        if lo == hi:
            in_range = lambda s: s == lo  # noqa: E731
        else:
            in_range = lambda s: lo <= s < hi  # noqa: E731
        count = 0
        for row in self._rows():
            if in_range(row["score"]):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        rows = self._rows()
        for row in rows:
            self._emit(_row(row))
        self._emit(f"END {len(rows)}")

    def sum_scores(self) -> None:
        total = sum(row["score"] for row in self._rows())
        self._emit(f"SUM {_wrap32(total)}")

    def avg_scores(self) -> None:
        rows = self._rows()
        if not rows:
            self._emit("ERR EMPTY")
            return
        total = sum(row["score"] for row in rows)
        quotient = abs(total) // len(rows)  # truncate toward zero
        self._emit(f"AVG {quotient if total >= 0 else -quotient}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            self._emit("ERR FMT")
            return
        cmd = parts[0]
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


def _name_matches(name: str, target: str, whole: bool) -> bool:
    if not target:
        return True
    if name[:1] != target[:1]:
        return False
    if whole and len(name) != len(target):
        return False
    if len(name) < len(target):
        return False
    return name[1 : len(target)].lower() == target[1:].lower()


def _wrap32(value: int) -> int:
    return (value + 2**31) % 2**32 - 2**31


def _row(row: dict) -> str:
    return f"ROW {row['id']} {row['name']} {row['score']}"


def _alnum(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isalnum()


def _parse_score(token: str) -> int | None:
    try:
        value = int(token)
    except ValueError:
        return None
    if not SCORE_MIN <= value <= SCORE_MAX:
        return None
    return value


def main() -> None:
    store = Store()
    for line in sys.stdin:
        store.handle(line)


if __name__ == "__main__":
    main()
