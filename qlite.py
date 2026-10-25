"""QLite record store, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One store
per process: commands on stdin, responses on stdout. Protocol reference:
``docs/SPEC.md`` (mind the drift warning; the engine's behavior is the
contract).
"""

from __future__ import annotations

import sys

CAPACITY = 4096
SCORE_MIN, SCORE_MAX = -999_999, 999_999


class Store:
    def __init__(self, out=None):
        self.rows: list[dict | None] = []  # physical slots, not insertion order
        self.free: list[int] = []
        self.size = 0
        self.sum = 0
        self.out = out if out is not None else sys.stdout

    def _occupied(self):
        return (row for row in self.rows if row is not None)

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
        existing = self._find(record_id)
        if existing is not None:
            self.sum += score - existing["score"]
            existing["score"] = score
            self._emit("OK")
            return
        if self.size >= CAPACITY:
            self._emit("ERR FULL")
            return
        row = {"id": record_id, "name": name[:12], "score": score}
        if self.free:
            self.rows[self.free.pop()] = row
        else:
            self.rows.append(row)
        self.size += 1
        self.sum += score
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
        self.free.append(slot)
        self.size -= 1
        self.sum -= row["score"]
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
        if not 0 < len(pattern.encode()) <= 17:
            self._emit("ERR FMT")
            return
        count = 0
        for row in self._occupied():
            if _matches(row["name"], pattern):
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def range(self, lo_token: str, hi_token: str) -> None:
        lo, hi = _parse_score(lo_token), _parse_score(hi_token)
        if lo is None or hi is None:
            self._emit("ERR FMT")
            return
        count = 0
        for row in self._occupied():
            if lo <= row["score"] < hi or row["score"] == lo == hi:
                self._emit(_row(row))
                count += 1
        self._emit(f"END {count}")

    def list_all(self) -> None:
        for row in self._occupied():
            self._emit(_row(row))
        self._emit(f"END {self.size}")

    def sum_scores(self) -> None:
        value = (self.sum + 2**31) % 2**32 - 2**31
        self._emit(f"SUM {value}")

    def avg_scores(self) -> None:
        if not self.size:
            self._emit("ERR EMPTY")
            return
        quotient = abs(self.sum) // self.size
        if self.sum < 0:
            quotient = -quotient
        self._emit(f"AVG {quotient}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        if not parts:
            self._emit("ERR FMT")
            return
        cmd = parts[0]
        # Recognized commands consume their arguments and ignore the rest.
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
    return lo <= len(value) <= hi and all("0" <= c <= "9" or "A" <= c <= "Z" or "a" <= c <= "z" for c in value)


def _matches(name: str, pattern: str) -> bool:
    # The engine compares the first byte exactly, folds only the rest, and
    # treats a final '*' as a prefix marker; other '*' bytes are literal.
    name, pattern = name.encode(), pattern.encode()
    if pattern == b"*":
        return True
    if not name or name[0] != pattern[0]:
        return False
    if pattern.endswith(b"*"):
        pattern = pattern[:-1]
        return len(name) >= len(pattern) and _ascii_lower(name[1:len(pattern)]) == _ascii_lower(pattern[1:])
    return len(name) == len(pattern) and _ascii_lower(name[1:]) == _ascii_lower(pattern[1:])


def _ascii_lower(value: bytes) -> bytes:
    return bytes(c + 32 if 65 <= c <= 90 else c for c in value)


def _parse_score(token: str) -> int | None:
    digits = token[1:] if token[:1] in ("+", "-") else token
    if not digits or not all("0" <= c <= "9" for c in digits):
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
