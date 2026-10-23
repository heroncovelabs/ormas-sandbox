"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import string
import sys

_ITEM_CHARS = frozenset(string.ascii_letters + string.digits)
_PRIO_DIGITS = frozenset(string.digits)


def _item_ok(token: str) -> bool:
    return 1 <= len(token) <= 8 and all(c in _ITEM_CHARS for c in token)


def _item_key(token: str) -> str:
    # Identity is ASCII-case-insensitive. Only validated ASCII tokens
    # reach this point, so lower() never performs Unicode folding.
    return token.lower()


class Engine:
    def __init__(self, out=None):
        self.orig: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (key, prio, seq)
        self.names: dict[str, str] = {}  # key -> spelling of first accepted N
        self.seq_next = 1
        self.age: dict[str, int] = {}
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # Keep the two latest successful dequeues, including consumed slots.
        # A new dequeue evicts the oldest slot even after a failure used the
        # newest one. Empty dequeues and other commands leave these intact.
        self.recent: list[tuple[str, bool]] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, item: str, prio: int, *, fresh: bool = True) -> None:
        # Explicit enqueues and dead-letter drains start a new FIFO age;
        # retries keep the age of the enqueue that originally admitted them.
        if fresh:
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

    def handle(self, line: str | bytes) -> None:
        if isinstance(line, str):
            line = line.encode("utf-8", "surrogateescape")
        # The legacy record reader terminates commands at CR or NUL, and its
        # scanner recognizes ASCII whitespace with a seven-byte opcode field.
        line = line.split(b"\0", 1)[0].split(b"\r", 1)[0].split(b"\n", 1)[0]
        if not line:
            return
        tokens = line.split()
        if tokens and len(tokens[0]) > 7:
            tokens[:1] = [tokens[0][:7], tokens[0][7:]]
        parts = [token.decode("ascii", "surrogateescape") for token in tokens]
        kind = parts[0] if parts else ""
        raw = parts[1] if len(parts) > 1 else ""
        item_ok = _item_ok(raw)
        echo = raw if item_ok else "????????"
        key = _item_key(raw) if item_ok else ""

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if not (
                1 <= len(ptok) <= 3 and all(c in _PRIO_DIGITS for c in ptok)
            ):
                self._emit(f"R {raw} PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 999:
                self._emit(f"R {raw} PRIO")
                return
            if key in self.live or key in self.dead:
                self._emit(f"R {self.names[key]} STATE")
                return
            if key not in self.orig:
                self.fails[key] = 0
                self.names[key] = raw
            self.orig[key] = prio
            self._push(key, prio)
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            if not self.queue:
                self._emit("EMPTY")
                return
            key = self._pop_best()
            self.recent.append((key, True))
            self.recent = self.recent[-2:]
            self.c_deq += 1
            self._emit(f"I {self.names[key]}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            slot = next(
                (
                    i for i in range(len(self.recent) - 1, -1, -1)
                    if self.recent[i][1]
                ),
                None,
            )
            if (
                slot is None
                or self.recent[slot][0] != key
                or key in self.live
                or key in self.dead
            ):
                self._emit(f"R {self.names.get(key, raw)} STATE")
                return
            self.recent[slot] = (key, False)
            self.fails[key] += 1
            self.c_fail += 1
            # Retries treat priority 999 as a base of 1000. Penalties
            # accumulate against the original value across accepted failures.
            base = 1000 if self.orig[key] == 999 else self.orig[key]
            prio = max(1, base - 10 * self.fails[key])
            # Exact hundreds are legacy dead-letter sentinels.
            if self.fails[key] >= 3 or prio % 100 == 0:
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {self.names[key]}")
                return
            self._push(key, prio, fresh=False)
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
    # The retired engine reads at most 511 bytes per record; long
    # physical lines therefore produce multiple independently parsed commands.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
