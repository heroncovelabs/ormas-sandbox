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
NAME_WIDTH = 12
LINE_WIDTH = 255


class Store:
    def __init__(self, out=None):
        # Scans visit physical slots; deleted slots are reused in LIFO order.
        self.rows: list[dict | None] = []
        self.free_slots: list[int] = []
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
        if not self.free_slots and len(self.rows) >= CAPACITY:
            self._emit("ERR FULL")
            return
        row = {"id": record_id, "name": name[:NAME_WIDTH], "score": score}
        if self.free_slots:
            self.rows[self.free_slots.pop()] = row
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
        if not 0 < len(pattern) <= 17:
            self._emit("ERR FMT")
            return
        prefix_mode = pattern.endswith("*")
        target = pattern[:-1] if prefix_mode else pattern
        count = 0
        for row in self._live_rows():
            if _name_matches(row["name"], target, prefix_mode):
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
            if _in_range(row["score"], lo, hi):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        for row in self._live_rows():
            self._emit(_row(row))
        self._emit(f"END {len(self.rows) - len(self.free_slots)}")

    def sum_scores(self) -> None:
        # The engine accumulates in signed 32-bit width: wrap the exact total.
        total = sum(row["score"] for row in self._live_rows())
        wrapped = ((total + 2**31) % 2**32) - 2**31
        self._emit(f"SUM {wrapped}")

    def avg_scores(self) -> None:
        count = len(self.rows) - len(self.free_slots)
        if not count:
            self._emit("ERR EMPTY")
            return
        # Exact (unwrapped) total over live records, divided by the live count,
        # truncated toward zero via magnitude division with the sign restored.
        total = sum(row["score"] for row in self._live_rows())
        magnitude = abs(total) // count
        avg = magnitude if total >= 0 else -magnitude
        self._emit(f"AVG {avg}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        # The C engine terminates at NUL/CR/LF, then scans four %63s fields.
        # Each field consumes at most 63 bytes, even within a longer token.
        line = re.split(r"[\x00\r\n]", line, maxsplit=1)[0]
        if not line:
            return
        parts = re.findall(r"[^ \t\n\r\v\f]{1,63}", line)[:4]
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


def _row(row: dict) -> str:
    return f"ROW {row['id']} {row['name']} {row['score']}"


def _name_matches(name: str, target: str, prefix_mode: bool) -> bool:
    # The first character compares case-sensitively; the remainder compares
    # case-insensitively. A trailing '*' selects prefix matching; every other
    # '*' is an ordinary character and never matches a stored name.
    if not target:
        return True
    if prefix_mode:
        if len(name) < len(target):
            return False
        head = name[: len(target)]
    else:
        if len(name) != len(target):
            return False
        head = name
    return head[0] == target[0] and head[1:].lower() == target[1:].lower()


def _in_range(score: int, lo: int, hi: int) -> bool:
    # Engine semantics: lo inclusive, hi exclusive when lo < hi; equal
    # endpoints select exact matches; reversed endpoints select nothing.
    if lo < hi:
        return lo <= score < hi
    if lo == hi:
        return score == lo
    return False


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
