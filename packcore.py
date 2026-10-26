"""PackCore bin-allocator engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behaviors that differ from the spec, reproduced here:

- Item ids are case-insensitive. The spelling of the first accepted
  placement is the registered name, echoed on ``DUP`` and on ``STATE``
  for known ids; ``SIZE`` and unknown-id ``STATE`` echo the id as typed.
- Extra trailing tokens are ignored. An empty line is skipped; a
  whitespace-only line is ``FMT``.
- A size whose value is 0 (1-3 digits) is dropped silently: no reply,
  not counted.
- An id placed again after a free skips the first bin it fits in and
  takes the second (opening a new bin if no second one fits); compaction
  places every item plain first-fit.
- A size-50 item opens a new bin whenever exactly one bin is open.
- Compaction is first-fit decreasing by size, ties in placement order
  (latest placement of each id).
- A free that empties bin b >= 1 leaves ``w(b-1) * size`` in the digest
  until the next compaction.
"""

from __future__ import annotations

import re
import sys

CAP = 100
DMOD = 99991
HALF = CAP // 2

_ITEM = re.compile(r"[A-Za-z0-9]{1,8}")
_SIZE = re.compile(r"[0-9]{1,3}")
_WS = re.compile(r"[ \t\n\v\f\r]+")


def _weight(i: int) -> int:
    return 2 if i % 2 == 0 else 7


class Engine:
    def __init__(self, out=None):
        self.name: dict[str, str] = {}
        self.size: dict[str, int] = {}
        self.seq: dict[str, int] = {}
        self.bin: dict[str, int] = {}
        self.live: set[str] = set()
        self.used: list[int] = []
        self.phantom = 0
        self.seq_next = 1
        self.c_place = 0
        self.c_free = 0
        self.c_comp = 0
        self.c_rej = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, item: str, code: str) -> None:
        self._emit(f"N {item} {code}")
        self.c_rej += 1

    def _fit(self, size: int, skip: int = 0) -> int:
        for i, u in enumerate(self.used):
            if u + size <= CAP:
                if skip == 0:
                    return i
                skip -= 1
        return -1

    def _open(self) -> int:
        self.used.append(0)
        return len(self.used) - 1

    def _digest(self) -> int:
        d = self.phantom
        for i, u in enumerate(self.used):
            d += _weight(i) * u
        return d % DMOD

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = [p for p in _WS.split(line) if p]
        kind = parts[0] if parts else ""
        item = parts[1] if len(parts) > 1 else ""
        item_ok = _ITEM.fullmatch(item) is not None
        echo = item if item_ok else "????????"
        key = item.lower()

        if kind == "P":
            if len(parts) < 3 or not item_ok:
                self._reject(echo, "FMT")
                return
            stok = parts[2]
            if not _SIZE.fullmatch(stok):
                self._reject(item, "SIZE")
                return
            size = int(stok)
            if size == 0:
                return
            if size > CAP:
                self._reject(item, "SIZE")
                return
            if key in self.live:
                self._reject(self.name[key], "DUP")
                return
            if size == HALF and len(self.used) == 1:
                b = -1
            else:
                b = self._fit(size, 1 if key in self.name else 0)
            if b < 0:
                b = self._open()
            self.used[b] += size
            if key not in self.name:
                self.name[key] = item
            self.size[key] = size
            self.seq[key] = self.seq_next
            self.seq_next += 1
            self.bin[key] = b
            self.live.add(key)
            self.c_place += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._reject(echo, "FMT")
                return
            if key not in self.live:
                self._reject(self.name.get(key, item), "STATE")
                return
            b = self.bin[key]
            self.used[b] -= self.size[key]
            if self.used[b] == 0 and b > 0:
                self.phantom += _weight(b - 1) * self.size[key]
            self.live.discard(key)
            self.c_free += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "K":
            order = sorted(self.live, key=lambda it: (-self.size[it], self.seq[it]))
            self.used = []
            self.phantom = 0
            for it in order:
                b = self._fit(self.size[it])
                if b < 0:
                    b = self._open()
                self.used[b] += self.size[it]
                self.bin[it] = b
            self.c_comp += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "D":
            self._emit(f"D {self._digest()}")
            return

        self._reject(echo, "FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_place} {self.c_free} {self.c_comp} {self.c_rej}")


def main() -> None:
    engine = Engine()
    data = sys.stdin.buffer.read().decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for line in lines:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
