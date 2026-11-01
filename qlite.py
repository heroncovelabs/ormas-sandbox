"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).

Engine behaviors that differ from the spec, reproduced here:

- Records live in fixed slots; a deleted record's slot goes on a free
  stack and is reused (last freed, first reused). Scans walk slot order.
- Names are validated as 1-16 alphanumerics but stored truncated to 12.
- Inserting an existing id updates its score (name kept), even when full.
- FIND: the first character matches case-sensitively, the rest
  case-insensitively; ``*`` is a wildcard only as the final character
  (prefix match), anywhere else it is literal.
- RANGE: ``lo <= score < hi``; when ``lo == hi`` the single value matches.
- SUM wraps to a signed 32-bit integer; AVG divides the exact sum and
  truncates toward zero.
- Extra arguments after a command's operands are ignored.
"""

from __future__ import annotations

import re
import sys

CAPACITY = 4096
SCORE_MIN, SCORE_MAX = -999_999, 999_999
NAME_STORED = 12

_SCORE_RE = re.compile(r"[+-]?[0-9]+")
_ALNUM_RE = re.compile(r"[A-Za-z0-9]+")
_WS_RE = re.compile(r"[ \t\r\n\v\f]+")


class Store:
    def __init__(self, out=None):
        self.slots: list[dict | None] = []
        self.free: list[int] = []  # stack of freed slot indexes
        self.index: dict[str, int] = {}
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
            if _name_match(pattern, row["name"], prefix):
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
            if lo <= score < hi or score == lo == hi:
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
        parts = [part for part in _WS_RE.split(line) if part]
        if not parts:
            # A blank line is skipped, but whitespace-only is malformed.
            self._emit("ERR FMT")
            return
        cmd, nargs = parts[0], len(parts) - 1
        if cmd == "INS" and nargs >= 3:
            self.ins(parts[1], parts[2], parts[3])
        elif cmd == "DEL" and nargs >= 1:
            self.delete(parts[1])
        elif cmd == "GET" and nargs >= 1:
            self.get(parts[1])
        elif cmd == "FIND" and nargs >= 1:
            self.find(parts[1])
        elif cmd == "RANGE" and nargs >= 2:
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
    return lo <= len(value) <= hi and _ALNUM_RE.fullmatch(value) is not None


def _lower(text: str) -> str:
    return text.translate(_LOWER)


_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _name_match(pattern: str, name: str, prefix: bool) -> bool:
    if not pattern:
        return prefix
    if prefix:
        name = name[: len(pattern)]
    if len(name) != len(pattern) or name[0] != pattern[0]:
        return False
    return _lower(name[1:]) == _lower(pattern[1:])


def _parse_score(token: str) -> int | None:
    if _SCORE_RE.fullmatch(token) is None:
        return None
    value = int(token)
    if not SCORE_MIN <= value <= SCORE_MAX:
        return None
    return value


def main() -> None:
    store = Store()
    data = sys.stdin.buffer.read().decode("latin-1")
    for line in data.split("\n"):
        store.handle(line)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
