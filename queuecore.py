"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import sys


class Engine:
    def __init__(self, out=None):
        self.orig: dict[str, int] = {}
        self.arrival: dict[str, int] = {}
        self.names: dict[str, str] = {}
        self.fails: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (item, prio, seq)
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        self.last: str | None = None
        self.prev: str | None = None
        self.last_open = False
        self.prev_open = False
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _name(self, item: str) -> str:
        return self.names.get(item.lower(), item)

    def _push(self, key: str, prio: int, seq: int | None = None) -> None:
        if seq is None:
            seq = self.seq_next
            self.seq_next += 1
        self.queue.append((key, prio, seq))
        self.live.add(key)

    def _pop_best(self) -> str:
        best = 0
        for i in range(1, len(self.queue)):
            if self.queue[i][1] > self.queue[best][1] or (
                self.queue[i][1] == self.queue[best][1]
                and self.queue[i][2] < self.queue[best][2]
            ):
                best = i
        key = self.queue.pop(best)[0]
        self.live.discard(key)
        return key

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        parts = line.split()
        if not parts:
            if line:
                self._emit("R ???????? FMT")
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
        echo = item if item_ok else "????????"
        key = item.lower()

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if not (ptok.isascii() and ptok.isdigit() and 1 <= len(ptok) <= 3):
                self._emit(f"R {item} PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 999:
                self._emit(f"R {item} PRIO")
                return
            if key in self.live or key in self.dead:
                self._emit(f"R {self._name(item)} STATE")
                return
            if key not in self.orig:
                self.fails[key] = 0
            self.orig[key] = prio
            self.arrival[key] = self.seq_next
            self.names.setdefault(key, item)
            self._push(key, prio)
            if self.last == key:
                self.last_open = False
                self.prev_open = False
            if self.prev == key:
                self.prev_open = False
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            if not self.queue:
                self._emit("EMPTY")
                return
            key = self._pop_best()
            self.prev = self.last
            self.prev_open = self.last_open
            self.last = key
            self.last_open = True
            self.c_deq += 1
            self._emit(f"I {self._name(key)}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            if self.last_open and self.last == key:
                slot = "last"
            elif not self.last_open and self.prev_open and self.prev == key:
                slot = "prev"
            else:
                self._emit(f"R {self._name(item)} STATE")
                return
            if slot == "last":
                self.last_open = False
            else:
                self.prev_open = False
            self.fails[key] += 1
            self.c_fail += 1
            base = 1000 if self.orig[key] == 999 else self.orig[key]
            reduced = base - 10 * self.fails[key]
            if (reduced > 0 and reduced % 100 == 0) or self.fails[key] >= 3:
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {self._name(key)}")
                return
            self._push(key, max(1, reduced), self.arrival[key])
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "K":
            for key in self.dead:
                self.fails[key] = 0
                self.arrival[key] = self.seq_next
                self._push(key, self.orig[key])
            self.dead = []
            self._emit(f"OK {len(self.queue)}")
            return

        if len(kind) >= 8:
            item = kind[7:]
            item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
            echo = item if item_ok else "????????"
        self._emit(f"R {echo} FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_enq} {self.c_deq} {self.c_fail} {self.c_dead}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
