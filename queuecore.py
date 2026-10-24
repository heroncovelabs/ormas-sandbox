"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys


class Engine:
    def __init__(self, out=None):
        self.names: dict[str, str] = {}  # folded id -> first accepted spelling
        self.orig: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.age: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (item, prio, seq)
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # Keep both recent dequeue slots even after a failure consumes one.
        self.undo: list[str | None] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, item: str, prio: int, *, retry: bool = False) -> None:
        # N and K give an item a fresh FIFO age; F preserves its current age.
        if not retry:
            self.age[item] = self.seq_next
            self.seq_next += 1
        self.queue.append((item, prio, self.age[item]))
        self.live.add(item)

    def _pop_best(self) -> str:
        best = 0
        for i in range(1, len(self.queue)):
            if self.queue[i][1] > self.queue[best][1] or (
                self.queue[i][1] == self.queue[best][1]
                and self.queue[i][2] < self.queue[best][2]
            ):
                best = i
        item = self.queue.pop(best)[0]
        self.live.discard(item)
        return item

    def handle(self, line: str) -> None:
        # Match the legacy C-string reader and ASCII whitespace/token rules.
        line = re.split(r"[\x00\r\n]", line, maxsplit=1)[0]
        if not line:
            return
        parts = re.findall(r"[^ \t\v\f]+", line)
        if parts and len(parts[0]) > 7:
            # The command scanner consumes at most seven bytes of its token.
            parts[:1] = [parts[0][:7], parts[0][7:]]
        kind = parts[0] if parts else ""
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
        echo = item if item_ok else "????????"

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
            item = self.names.setdefault(item.lower(), item)
            if item in self.live or item in self.dead:
                self._emit(f"R {item} STATE")
                return
            if item not in self.orig:
                self.fails[item] = 0
            self.orig[item] = prio
            self._push(item, prio)
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            if not self.queue:
                self._emit("EMPTY")
                return
            item = self._pop_best()
            self.undo.append(item)
            self.undo = self.undo[-2:]
            self.c_deq += 1
            self._emit(f"I {item}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            item = self.names.get(item.lower(), item)
            slot = len(self.undo) - 1
            if slot >= 0 and self.undo[slot] is None:
                slot -= 1
            if (
                slot < 0
                or self.undo[slot] != item
                or item in self.live
                or item in self.dead
            ):
                self._emit(f"R {item} STATE")
                return
            self.undo[slot] = None
            self.fails[item] += 1
            self.c_fail += 1
            # The top-priority code represents 1000 for retry arithmetic.
            base = 1000 if self.orig[item] == 999 else self.orig[item]
            prio = max(1, base - 10 * self.fails[item])
            # Exact hundreds are reserved dead-letter sentinels.
            if self.fails[item] >= 3 or prio % 100 == 0:
                self.dead.append(item)
                self.c_dead += 1
                self._emit(f"DLQ {item}")
                return
            self._push(item, prio, retry=True)
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "K":
            for item in self.dead:
                self.fails[item] = 0
                self._push(item, self.orig[item])
            self.dead = []
            self._emit(f"OK {len(self.queue)}")
            return

        self._emit(f"R {echo} FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_enq} {self.c_deq} {self.c_fail} {self.c_dead}")


def main() -> None:
    engine = Engine()
    # fgets used a 512-byte buffer, including its terminating NUL. Read raw
    # bytes so embedded CRs and non-ASCII whitespace keep their legacy meaning.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("ascii", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
