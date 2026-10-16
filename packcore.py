"""PackCore bin-allocator engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

CAP = 100
DMOD = 99991

_SEP = re.compile("[ \t]+")


class Engine:
    def __init__(self, out=None):
        self.size: dict[str, int] = {}
        self.seq: dict[str, int] = {}
        self.bin: dict[str, int] = {}
        self.name: dict[str, str] = {}
        self.scar: dict[str, int] = {}
        self.live: set[str] = set()
        self.used: list[int] = []
        self.ghost = 0
        self.last_bin = -1
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

    def _fit(self, size: int, skip=()) -> int:
        for i, u in enumerate(self.used):
            if i in skip:
                continue
            if u + size <= CAP:
                return i
        return -1

    def _open(self) -> int:
        self.used.append(0)
        return len(self.used) - 1

    def _digest(self) -> int:
        d = self.ghost
        for i, u in enumerate(self.used):
            w = 2 if i % 2 == 0 else 7
            d = (d + w * u) % DMOD
        return d % DMOD

    def handle(self, line: str) -> None:
        line = line.split("\n", 1)[0].split("\r", 1)[0]
        if not line:
            return
        parts = [p for p in _SEP.split(line) if p]
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
        echo = item if item_ok else "????????"
        key = item.lower()

        if kind == "P":
            if len(parts) < 3 or not item_ok:
                self._reject(echo, "FMT")
                return
            stok = parts[2]
            if not (stok.isascii() and stok.isdigit() and 1 <= len(stok) <= 3):
                self._reject(item, "SIZE")
                return
            size = int(stok)
            if size > 100:
                self._reject(item, "SIZE")
                return
            if size == 0:
                return
            if key in self.live:
                self._reject(self.name[key], "DUP")
                return
            b = self._fit(size)
            if b >= 0 and (
                (size == 50 and len(self.used) == 1) or key in self.scar
            ):
                b = self._fit(size, (b,))
            if b < 0:
                b = self._open()
            self.used[b] += size
            self.size[key] = size
            self.seq[key] = self.seq_next
            self.seq_next += 1
            self.bin[key] = b
            self.name.setdefault(key, item)
            self.live.add(key)
            self.last_bin = b
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
                self.ghost += self.size[key] * (2 if (b - 1) % 2 == 0 else 7)
            self.scar[key] = b
            self.live.discard(key)
            self.c_free += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "K":
            order = sorted(self.live, key=lambda it: (-self.size[it], self.seq[it]))
            self.used = []
            self.ghost = 0
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
    data = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
    for line in data.split("\n"):
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
