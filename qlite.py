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
        self.rows: list[dict | None] = []  # stable physical slots
        self._free_slots: list[int] = []  # most recently deleted slot first
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _live_rows(self):
        return (row for row in self.rows if row is not None)

    def _find(self, record_id: str) -> dict | None:
        for row in self._live_rows():
            if row["id"] == record_id:
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
        if not self._free_slots and len(self.rows) >= CAPACITY:
            self._emit("ERR FULL")
            return
        row = {"id": record_id, "name": name[:12], "score": score}
        if self._free_slots:
            self.rows[self._free_slots.pop()] = row
        else:
            self.rows.append(row)
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
        self._free_slots.append(slot)
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
        if not 0 < len(pattern.encode("utf-8", "surrogateescape")) <= 17:
            self._emit("ERR FMT")
            return
        # Only the final star is special; earlier stars remain literal.
        prefix_match = pattern.endswith("*")
        needle = pattern[:-1] if prefix_match else pattern
        count = 0
        for row in self._live_rows():
            name = row["name"]
            matches = (
                not needle
                or (name[0] == needle[0] and name.lower().startswith(needle.lower()))
            ) if prefix_match else (
                name[0] == needle[0] and name.lower() == needle.lower()
            )
            if matches:
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def range(self, lo_token: str, hi_token: str) -> None:
        lo, hi = _parse_score(lo_token), _parse_score(hi_token)
        if lo is None or hi is None:
            self._emit("ERR FMT")
            return
        count = 0
        for row in self._live_rows():
            if lo <= row["score"] < hi or lo == hi == row["score"]:
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        for row in self._live_rows():
            self._emit(_row(row))
        self._emit(f"END {len(self.rows) - len(self._free_slots)}")

    def sum_scores(self) -> None:
        total = sum(row["score"] for row in self._live_rows())
        # SUM exposes a signed 32-bit accumulator; AVG uses a wide total.
        total = (total + (1 << 31)) % (1 << 32) - (1 << 31)
        self._emit(f"SUM {total}")

    def avg_scores(self) -> None:
        count = len(self.rows) - len(self._free_slots)
        if not count:
            self._emit("ERR EMPTY")
            return
        total = sum(row["score"] for row in self._live_rows())
        average = abs(total) // count
        self._emit(f"AVG {-average if total < 0 else average}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        # The engine scans four fields of at most 63 bytes each, accepting
        # surplus arguments. CR and NUL terminate the command before scanning.
        raw = line.encode("utf-8", "surrogateescape")
        raw = re.split(rb"[\r\n\x00]", raw, maxsplit=1)[0]
        if not raw:
            return
        parts = [
            match.group().decode("utf-8", "surrogateescape")
            for match in re.finditer(rb"[^ \t\v\f]{1,63}", raw)
        ][:4]
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
        elif cmd == "LIST" and len(parts) >= 1:
            self.list_all()
        elif cmd == "SUM" and len(parts) >= 1:
            self.sum_scores()
        elif cmd == "AVG" and len(parts) >= 1:
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
    # fgets in the retired engine consumes at most 255 bytes per command.
    while line := sys.stdin.buffer.readline(255):
        store.handle(line.decode("utf-8", "surrogateescape"))


if __name__ == "__main__":
    main()
