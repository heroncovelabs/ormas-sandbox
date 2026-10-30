"""PackCore bin-allocator engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
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
        self.live: set[str] = set()
        self.used: list[int] = []
        self.names: dict[str, str] = {}
        self.scarred: set[str] = set()
        self.digest_residue = 0
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

    def _fit(self, size: int, skip_first: bool = False) -> int:
        for i, u in enumerate(self.used):
            if u + size <= CAP:
                if skip_first:
                    skip_first = False
                    continue
                return i
        return -1

    def _open(self) -> int:
        self.used.append(0)
        return len(self.used) - 1

    def _digest(self) -> int:
        d = self.digest_residue
        for i, u in enumerate(self.used):
            w = 2 if i % 2 == 0 else 7
            d = (d + w * u) % DMOD
        return d

    def handle(self, line: str) -> None:
        line = line.split("\0", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            return
        # Match the reference's bounded sscanf fields and ASCII whitespace.
        parts = []
        pos = 0
        for width in (7, 63, 63, 63):
            while pos < len(line) and line[pos] in " \t\n\r\v\f":
                pos += 1
            start = pos
            while (pos < len(line) and pos - start < width
                   and line[pos] not in " \t\n\r\v\f"):
                pos += 1
            if start == pos:
                break
            parts.append(line[start:pos])
        kind = parts[0] if parts else ""
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
        echo = item if item_ok else "????????"

        if kind == "P":
            if len(parts) < 3 or not item_ok:
                self._reject(echo, "FMT")
                return
            stok = parts[2]
            if not (stok.isascii() and stok.isdigit() and 1 <= len(stok) <= 3):
                self._reject(item, "SIZE")
                return
            size = int(stok)
            if size > CAP:
                self._reject(item, "SIZE")
                return
            # Zero-sized placements are silent, even for an already live ID.
            if size == 0:
                return
            item = item.lower()
            if item in self.live:
                self._reject(self.names[item], "DUP")
                return
            self.names.setdefault(item, echo)
            # With exactly one open bin, a half-capacity item opens its pair.
            b = (-1 if size == 50 and len(self.used) == 1
                 else self._fit(size, item in self.scarred))
            if b < 0:
                b = self._open()
            self.used[b] += size
            self.size[item] = size
            self.seq[item] = self.seq_next
            self.seq_next += 1
            self.bin[item] = b
            self.live.add(item)
            self.c_place += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._reject(echo, "FMT")
                return
            item = item.lower()
            if item not in self.live:
                self._reject(self.names.get(item, echo), "STATE")
                return
            b = self.bin[item]
            self.used[b] -= self.size[item]
            if b > 0 and self.used[b] == 0:
                # Empty-bin merges leave a digest-only residue on the left.
                weight = 2 if (b - 1) % 2 == 0 else 7
                self.digest_residue += weight * self.size[item]
            self.live.discard(item)
            self.scarred.add(item)
            self.c_free += 1
            self._emit(f"B {len(self.used)}")
            return

        if kind == "K":
            order = sorted(self.live, key=lambda it: (-self.size[it], self.seq[it]))
            self.used = []
            self.digest_residue = 0
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
