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
SCORE_MIN, SCORE_MAX = -999_999, 999_999


class Store:
    def __init__(self, out=None):
        self.rows: list[dict | None] = []  # physical slot order
        self.free_slots: list[int] = []  # most recently deleted slot first
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _find(self, record_id: str) -> dict | None:
        for row in self.rows:
            if row is not None and row["id"] == record_id:
                return row
        return None

    # -- commands -----------------------------------------------------------

    def ins(self, record_id: str, name: str, score_token: str) -> None:
        score = _parse_score(score_token)
        if not _alnum(record_id, 1, 8) or not _alnum(name, 1, 16) or score is None:
            self._emit("ERR FMT")
            return
        row = self._find(record_id)
        if row is not None:
            row["score"] = score
            self._emit("OK")
            return
        row = {"id": record_id, "name": name[:12], "score": score}
        if self.free_slots:
            self.rows[self.free_slots.pop()] = row
        elif len(self.rows) < CAPACITY:
            self.rows.append(row)
        else:
            self._emit("ERR FULL")
            return
        self._emit("OK")

    def delete(self, record_id: str) -> None:
        if not _alnum(record_id, 1, 8):
            self._emit("ERR FMT")
            return
        row = self._find(record_id)
        if row is None:
            self._emit("ERR NOTFOUND")
            return
        slot = self.rows.index(row)
        self.rows[slot] = None
        self.free_slots.append(slot)
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
        needle = pattern.encode("utf-8", "surrogateescape")
        if not 0 < len(needle) <= 17:
            self._emit("ERR FMT")
            return
        prefix = needle.endswith(b"*")
        if prefix:
            needle = needle[:-1]
        # The initial byte is case-sensitive; subsequent bytes use ASCII folding.
        needle = needle[:1] + needle[1:].lower()
        count = 0
        for row in self.rows:
            if row is None:
                continue
            name = row["name"].encode("ascii")
            name = name[:1] + name[1:].lower()
            if (name.startswith(needle) if prefix else name == needle):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def range(self, lo_token: str, hi_token: str) -> None:
        lo, hi = _parse_score(lo_token), _parse_score(hi_token)
        if lo is None or hi is None:
            self._emit("ERR FMT")
            return
        count = 0
        for row in self.rows:
            if row is not None and (
                lo <= row["score"] < hi or lo == hi == row["score"]
            ):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        for row in self.rows:
            if row is not None:
                self._emit(_row(row))
        self._emit(f"END {len(self.rows) - len(self.free_slots)}")

    def sum_scores(self) -> None:
        total = sum(row["score"] for row in self.rows if row is not None)
        total = (total + (1 << 31)) % (1 << 32) - (1 << 31)
        self._emit(f"SUM {total}")

    def avg_scores(self) -> None:
        count = len(self.rows) - len(self.free_slots)
        if not count:
            self._emit("ERR EMPTY")
            return
        total = sum(row["score"] for row in self.rows if row is not None)
        average = abs(total) // count
        self._emit(f"AVG {-average if total < 0 else average}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        parts = re.findall(r"\S+", line, re.ASCII)
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


def _alnum(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isascii() and value.isalnum()


def _parse_score(token: str) -> int | None:
    if re.fullmatch(r"[+-]?[0-9]+", token) is None:
        return None
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
