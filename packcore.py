"""PackCore bin-allocator engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behaviors that differ from the spec (all reproduced here):

- Item ids are case-insensitive. ``DUP``/``STATE`` replies for a known id
  echo the spelling it was first placed under.
- Tokens after the ones a command needs are ignored.
- A whitespace-only line is a ``FMT`` reject; an empty line is skipped.
- A size of zero is silently dropped: no reply, nothing counted.
- Compaction repacks first-fit DECREASING by size (ties keep placement
  order).
- An id placed again after being freed passes over the first bin it
  fits in and takes the second one ("scar").
- A size-50 item never joins the bin when only one bin is open (outside
  compaction).
- When a free empties bin ``b > 0``, the freed size keeps counting in the
  digest as part of bin ``b - 1`` until the next compaction.
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
        self.ghost: list[int] = []
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
        """Index of the (skip+1)-th bin with room for ``size``, or -1."""
        for i, u in enumerate(self.used):
            if u + size <= CAP:
                if skip == 0:
                    return i
                skip -= 1
        return -1

    def _choose(self, size: int, reused: bool) -> int:
        # A re-placed id passes over the first bin it fits in.
        b = self._fit(size, 1 if reused else 0)
        # A half-capacity item never joins the sole open bin.
        if b == 0 and size * 2 == CAP and len(self.used) == 1:
            b = -1
        if b < 0:
            b = self._open()
        return b

    def _open(self) -> int:
        self.used.append(0)
        self.ghost.append(0)
        return len(self.used) - 1

    def _digest(self) -> int:
        d = 0
        for i, u in enumerate(self.used):
            w = 2 if i % 2 == 0 else 7
            d = (d + w * (u + self.ghost[i])) % DMOD
        return d

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        kind = parts[0] if parts else ""
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
        echo = item if item_ok else "????????"
        key = item.upper()

        if kind == "P":
            if len(parts) < 3 or not item_ok:
                self._reject(echo, "FMT")
                return
            stok = parts[2]
            if not (stok.isascii() and stok.isdigit() and 1 <= len(stok) <= 3):
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
            b = self._choose(size, key in self.name)
            self.name.setdefault(key, item)
            self.used[b] += size
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
                self.ghost[b - 1] += self.size[key]
            self.live.discard(key)
            self.c_free += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "K":
            order = sorted(self.live, key=lambda it: (-self.size[it], self.seq[it]))
            self.used = []
            self.ghost = []
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
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
