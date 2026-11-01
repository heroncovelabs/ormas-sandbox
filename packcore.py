"""PackCore bin-allocator engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behaviors that differ from the spec:

- Item ids are ASCII and case-insensitive; DUP/STATE replies echo the
  first spelling seen, FMT echoes the token as sent.
- Tokens past the ones a command needs are ignored.
- A size of zero (``0``, ``00``, ``000``) is dropped silently: no reply,
  not counted anywhere. It is checked after the item/size format checks
  and before DUP.
- A size-50 placement never joins the bin when only one bin is open
  (compaction is exempt).
- Scar: an id that has been freed before never re-places into bin 0, and
  bin i only takes it if the least-used of bins 0..i-1 would also fit it.
- Compaction repacks first-fit DECREASING by size (ties in placement order).
- Freeing the last item from bin i > 0 leaves its size as a ghost on bin
  i-1 in the digest; ghosts clear at compaction.
"""

from __future__ import annotations

import sys

CAP = 100
DMOD = 99991
HALF = 50
ALNUM = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


class Engine:
    def __init__(self, out=None):
        self.size: dict[str, int] = {}
        self.seq: dict[str, int] = {}
        self.bin: dict[str, int] = {}
        self.scar: dict[str, int] = {}
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

    def _fit(self, size: int, scar=None, repack: bool = False) -> int:
        if size == HALF and len(self.used) == 1 and not repack:
            return -1
        lim = None
        for i, u in enumerate(self.used):
            if scar is not None:
                prev, lim = lim, u if lim is None else min(lim, u)
                if prev is None or prev + size > CAP:
                    continue
            if u + size <= CAP:
                return i
        return -1

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
        parts = line.split()
        if not parts:
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and all(c in ALNUM for c in item)
        key = item.lower()
        raw = item if item_ok else "????????"
        echo = self.name.get(key, item) if item_ok else raw

        if kind == "P":
            if len(parts) < 3 or not item_ok:
                self._reject(raw, "FMT")
                return
            stok = parts[2]
            if not (1 <= len(stok) <= 3 and all(c in "0123456789" for c in stok)):
                self._reject(echo, "SIZE")
                return
            size = int(stok)
            if size == 0:
                return
            if size > CAP:
                self._reject(echo, "SIZE")
                return
            if key in self.live:
                self._reject(echo, "DUP")
                return
            b = self._fit(size, self.scar.get(key))
            if b < 0:
                b = self._open()
            self.used[b] += size
            self.name.setdefault(key, item)
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
                self._reject(raw, "FMT")
                return
            if key not in self.live:
                self._reject(echo, "STATE")
                return
            b = self.bin[key]
            self.scar[key] = b
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
                b = self._fit(self.size[it], repack=True)
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

        self._reject(raw, "FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_place} {self.c_free} {self.c_comp} {self.c_rej}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
