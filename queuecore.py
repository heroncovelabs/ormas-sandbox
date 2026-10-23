"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behavior that differs from the spec:
- item ids are case-insensitive; the first spelling seen is the one shown.
- tokens after the ones a command needs are ignored.
- a requeued item loses 10 priority per failure (999 counts as 1000,
  never below 1) and keeps its original arrival order among equal
  priorities; drained items arrive anew.
- a requeue landing on a nonzero multiple of 100 dead-letters instead.
- the last two dequeues can be failed, most recent first.
- rejections echo the item as typed, except STATE, which shows the
  first spelling seen.
"""

from __future__ import annotations

import sys

PENALTY = 10
UNDO_DEPTH = 2
OPEN, FAILED, VOID = "open", "failed", "void"


class Engine:
    def __init__(self, out=None):
        self.name: dict[str, str] = {}  # key -> first spelling seen
        self.orig: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.arrival: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (key, prio, seq)
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # last dequeues as [key, state], most recent last; slots are never
        # popped, a fail or a re-enqueue of the item only changes the state
        self.undo: list[list] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, key: str, prio: int, seq: int | None = None) -> None:
        if seq is None:
            seq = self.seq_next
            self.seq_next += 1
        self.arrival[key] = seq
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
        if not line:
            return
        parts = line.split()
        if not parts:
            self._emit("R ???????? FMT")
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and item.isascii() and item.isalnum()
        key = item.upper()
        shown = self.name.get(key, item)
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
            if key in self.live or key in self.dead:
                self._emit(f"R {shown} STATE")
                return
            self.name.setdefault(key, item)
            if key not in self.orig:
                self.fails[key] = 0
            self.orig[key] = prio
            self._push(key, prio)
            for slot in self.undo:
                if slot[0] == key:
                    slot[1] = VOID
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            if not self.queue:
                self._emit("EMPTY")
                return
            key = self._pop_best()
            self.undo.append([key, OPEN])
            del self.undo[:-UNDO_DEPTH]
            self.c_deq += 1
            self._emit(f"I {self.name[key]}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            # the top slot, or the one under it once the top has failed
            target = None
            if self.undo and self.undo[-1][1] == OPEN:
                target = self.undo[-1]
            elif len(self.undo) >= 2 and self.undo[-1][1] == FAILED:
                target = self.undo[-2]
            if target is None or target != [key, OPEN]:
                self._emit(f"R {shown} STATE")
                return
            target[1] = FAILED
            self.fails[key] += 1
            self.c_fail += 1
            base = 1000 if self.orig[key] == 999 else self.orig[key]
            prio = max(1, base - PENALTY * self.fails[key])
            if self.fails[key] >= 3 or (prio >= 100 and prio % 100 == 0):
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {shown}")
                return
            self._push(key, prio, self.arrival[key])
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "K":
            for key in self.dead:
                self.fails[key] = 0
                self._push(key, self.orig[key])
            self.dead = []
            self._emit(f"OK {len(self.queue)}")
            return

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
