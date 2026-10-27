"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

_TOKENS = re.compile(r"\S+", re.ASCII)
_LINE_END = re.compile(r"[\x00\r\n]")
_INPUT_CHUNK_SIZE = 511
_ITEM_LIMIT = 4096
_ASCII_ALNUM = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
)
_ASCII_DIGITS = frozenset("0123456789")


def _valid_item(item: str) -> bool:
    return 1 <= len(item) <= 8 and all(c in _ASCII_ALNUM for c in item)


def _valid_prio_token(tok: str) -> bool:
    return 1 <= len(tok) <= 3 and all(c in _ASCII_DIGITS for c in tok)


class Engine:
    def __init__(self, out=None):
        # Internal state is keyed by the case-folded item id. ``names``
        # maps each key to the spelling the item was first accepted with,
        # which is the spelling the engine reports back.
        self.names: dict[str, str] = {}
        self.orig: dict[str, int] = {}
        self.age: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (key, prio, seq)
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # Keep the last two dequeue slots, including consumed/invalidated
        # slots. F moves backward through them; each D advances the window.
        self.hist: list[str | None] = [None, None]
        self.undo_next = 1
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, key: str, prio: int, *, retry: bool = False) -> None:
        # Retries keep their arrival age; N and K start a fresh FIFO age.
        if not retry:
            self.age[key] = self.seq_next
            self.seq_next += 1
        self.queue.append((key, prio, self.age[key]))
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

    def _name(self, key: str, raw: str) -> str:
        return self.names.get(key, raw)

    def handle(self, line: str) -> None:
        stripped = line.rstrip("\r\n")
        if stripped == "":
            return
        parts = stripped.split()
        if not parts:
            self._emit("R ???????? FMT")
            return
        kind = parts[0]
        raw = parts[1] if len(parts) > 1 else ""
        item_ok = _valid_item(raw)
        echo = raw if item_ok else "????????"
        key = raw.lower()

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if not _valid_prio_token(ptok):
                self._emit(f"R {raw} PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 999:
                self._emit(f"R {raw} PRIO")
                return
            if key in self.live or key in self.dead:
                self._emit(f"R {self._name(key, raw)} STATE")
                return
            if key not in self.orig:
                self.names[key] = raw
                self.fails[key] = 0
            self.orig[key] = prio
            self._push(key, prio)
            for i in range(2):
                if self.hist[i] == key:
                    self.hist[i] = None
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            if not self.queue:
                self._emit("EMPTY")
                return
            key = self._pop_best()
            self.hist = [self.hist[1], key]
            self.undo_next = 1
            self.c_deq += 1
            self._emit(f"I {self._name(key, key)}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            if self.undo_next < 0 or self.hist[self.undo_next] != key:
                self._emit(f"R {self._name(key, raw)} STATE")
                return
            self.hist[self.undo_next] = None
            self.undo_next -= 1
            self.fails[key] += 1
            self.c_fail += 1
            # The capped input 999 represents a retry base of 1000.
            # Penalties are cumulative from the latest accepted N priority.
            base = 1000 if self.orig[key] == 999 else self.orig[key]
            prio = max(1, base - 10 * self.fails[key])
            if self.fails[key] >= 3 or prio % 100 == 0:
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {self._name(key, raw)}")
                return
            self._push(key, prio, retry=True)
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "K":
            for k in self.dead:
                self.fails[k] = 0
                self._push(k, self.orig[k])
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
