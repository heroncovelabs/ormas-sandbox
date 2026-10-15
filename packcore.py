"""PackCore bin-allocator engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Behavior below follows the legacy engine wherever ``docs/SPEC.md`` is
silent or wrong:

- item ids are case-insensitive; DUP reports the spelling the id was
  first placed with, STATE and SIZE/FMT echo the spelling sent;
- a size-0 placement is dropped silently (no reply, not counted);
- trailing tokens after the required ones are ignored;
- a size-50 placement cannot use the only open bin;
- a re-placed id takes the second bin that fits (first-fit otherwise);
- freeing the last item of a bin ``b > 0`` leaves its size in the
  digest with the weight of bin ``b - 1`` (cleared by compaction);
- compaction packs largest items first, ties in placement order.
"""

from __future__ import annotations

import sys

CAP = 100
DMOD = 99991


class Engine:
    def __init__(self, out=None):
        self.size: dict[str, int] = {}
        self.seq: dict[str, int] = {}
        self.bin: dict[str, int] = {}
        self.name: dict[str, str] = {}
        self.live: set[str] = set()
        self.used: list[int] = []
        self.ghost: dict[int, int] = {}
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

    def _choose(self, size: int, reuse: bool) -> int:
        fits = [i for i, u in enumerate(self.used) if u + size <= CAP]
        if reuse:
            return fits[1] if len(fits) > 1 else -1
        return fits[0] if fits else -1

    def _open(self) -> int:
        self.used.append(0)
        return len(self.used) - 1

    def _digest(self) -> int:
        d = 0
        for i, u in enumerate(self.used):
            w = 2 if i % 2 == 0 else 7
            d = (d + w * (u + self.ghost.get(i, 0))) % DMOD
        return d

    def handle(self, line: str) -> None:
        raw = line.rstrip("\r\n")
        if raw == "":
            return
        parts = raw.split()
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isalnum()
        echo = item if item_ok else "????????"

        if kind == "P":
            if len(parts) < 3 or not item_ok:
                self._reject(echo, "FMT")
                return
            stok = parts[2]
            if not (stok.isdigit() and 1 <= len(stok) <= 3):
                self._reject(item, "SIZE")
                return
            size = int(stok)
            if size == 0:
                return
            if size > 100:
                self._reject(item, "SIZE")
                return
            key = item.lower()
            if key in self.live:
                self._reject(self.name[key], "DUP")
                return
            if size == 50 and len(self.used) < 2:
                b = -1
            else:
                b = self._choose(size, key in self.bin)
            if b < 0:
                b = self._open()
            self.used[b] += size
            self.size[key] = size
            self.seq[key] = self.seq_next
            self.seq_next += 1
            self.bin[key] = b
            self.name.setdefault(key, item)
            self.live.add(key)
            self.c_place += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._reject(echo, "FMT")
                return
            key = item.lower()
            if key not in self.live:
                self._reject(self.name.get(key, item), "STATE")
                return
            b = self.bin[key]
            self.used[b] -= self.size[key]
            self.live.discard(key)
            if self.used[b] == 0 and b > 0:
                self.ghost[b - 1] = self.ghost.get(b - 1, 0) + self.size[key]
            self.c_free += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "K":
            order = sorted(self.live, key=lambda k: (-self.size[k], self.seq[k]))
            self.used = []
            self.ghost = {}
            for it in order:
                b = self._choose(self.size[it], False)
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
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
