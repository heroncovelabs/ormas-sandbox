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
        self.orig: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.names: dict[str, str] = {}  # Case-insensitive key -> first spelling.
        self.age: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (item, prio, seq)
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # Successful dequeues shift two fixed undo slots. Closing a slot
        # does not remove it: a later dequeue still shifts the closed slot.
        self.undo: list[tuple[str, bool]] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, item: str, prio: int, *, fresh: bool = True) -> None:
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

    def handle(self, line: str) -> None:
        # The reference scans a C string, with fixed-width byte fields.
        # Empty lines are skipped, but whitespace-only lines are malformed.
        text = re.split(rb"[\x00\r\n]", line.encode("utf-8", "surrogateescape"), 1)[0]
        if not text:
            return
        parts = []
        pos = 0
        whitespace = b" \t\v\f"
        for width in (7, 63, 63):
            while pos < len(text) and text[pos] in whitespace:
                pos += 1
            start = pos
            while pos < len(text) and text[pos] not in whitespace and pos - start < width:
                pos += 1
            if pos == start:
                break
            parts.append(text[start:pos].decode("ascii", "replace"))
        kind = parts[0] if parts else ""
        raw_item = parts[1] if len(parts) > 1 else ""
        item_ok = re.fullmatch(r"[A-Za-z0-9]{1,8}", raw_item) is not None
        echo = raw_item if item_ok else "????????"
        item = raw_item.lower()

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if re.fullmatch(r"[0-9]{1,3}", ptok) is None or int(ptok) == 0:
                self._emit(f"R {raw_item} PRIO")
                return
            prio = int(ptok)
            if item in self.live or item in self.dead:
                self._emit(f"R {self.names[item]} STATE")
                return
            if item not in self.orig:
                self.fails[item] = 0
                self.names[item] = raw_item
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
            self.undo = (self.undo + [(item, True)])[-2:]
            self.c_deq += 1
            self._emit(f"I {self.names[item]}")
            return

        if kind == "F":
            if not item_ok:
                self._emit(f"R {echo} FMT")
                return
            name = self.names.get(item, raw_item)
            slot = next((i for i in range(len(self.undo) - 1, -1, -1)
                         if self.undo[i][1]), None)
            if (slot is None or self.undo[slot][0] != item
                    or item in self.live or item in self.dead):
                self._emit(f"R {name} STATE")
                return
            self.undo[slot] = (item, False)
            self.fails[item] += 1
            self.c_fail += 1
            # The maximum input priority denotes an internal base of 1000.
            # Retries keep their enqueue age, but lose ten points per strike.
            base = 1000 if self.orig[item] == 999 else self.orig[item]
            prio = max(1, base - 10 * self.fails[item])
            if self.fails[item] >= 3 or prio % 100 == 0:
                self.dead.append(item)
                self.c_dead += 1
                self._emit(f"DLQ {name}")
                return
            self._push(item, prio, fresh=False)
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
    # Match the reference's 512-byte fgets buffer (511 input bytes), keeping
    # carriage returns and arbitrary bytes intact for the C-string scanner.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("utf-8", "surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
