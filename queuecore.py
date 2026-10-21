"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

# Match the engine's bounded ASCII scans and character classes.
_SPLIT = re.compile(r"[ \t\r\n\x0b\x0c]+")
_LINE_END = re.compile(r"[\x00\r\n]")
_MAX_ITEMS = 4096
_LINE_SIZE = 511
_ITEM_CHARS = re.compile(r"[A-Za-z0-9]+")
_DIGITS = re.compile(r"[0-9]+")


class Engine:
    def __init__(self, out=None):
        # Identity is case-insensitive: internal keys are lowercase.
        self.orig: dict[str, int] = {}  # key -> priority
        self.fails: dict[str, int] = {}  # key -> failure count
        self.names: dict[str, str] = {}  # key -> first-seen spelling
        self.ages: dict[str, int] = {}  # age assigned by N or K
        self.live: set[str] = set()
        self.dead: list[str] = []  # keys, oldest first
        self.queue: list[tuple[str, int, int]] = []  # (key, prio, seq)
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # Keep the last two dequeues, including entries already failed.
        # A new dequeue replaces the older slot even after an undo.
        self.history: list[tuple[str, bool]] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, key: str, prio: int, *, fresh: bool = True) -> None:
        if fresh:
            self.ages[key] = self.seq_next
            self.seq_next += 1
        self.queue.append((key, prio, self.ages[key]))
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
        return self.names[key]

    def handle(self, line: str) -> None:
        # fgets/sscanf compatibility: CR and NUL terminate the command,
        # and scan widths can split a long token into successive fields.
        line = _LINE_END.split(line, maxsplit=1)[0]
        if not line:
            return
        parts = []
        for width in (7, 63, 63):
            line = line.lstrip(" \t\x0b\x0c")
            if not line:
                break
            token = _SPLIT.split(line, maxsplit=1)[0][:width]
            parts.append(token)
            line = line[len(token):]
        if not parts:
            self._emit("R ???????? FMT")
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = 1 <= len(item) <= 8 and _ITEM_CHARS.fullmatch(item) is not None
        echo = item if item_ok else "????????"
        key = item.lower()

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if not (_DIGITS.fullmatch(ptok) and 1 <= len(ptok) <= 3):
                self._emit(f"R {item} PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 999:
                self._emit(f"R {item} PRIO")
                return
            if key in self.live or key in self.dead:
                self._emit(f"R {self.names[key]} STATE")
                return
            if key not in self.orig:
                if len(self.orig) >= _MAX_ITEMS:
                    self._emit(f"R {item} FMT")
                    return
                self.names[key] = item
                self.fails[key] = 0
            # The top input priority uses an internal value of 1000.
            self.orig[key] = 1000 if prio == 999 else prio
            self._push(key, self.orig[key])
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            if not self.queue:
                self._emit("EMPTY")
                return
            name = self._pop_best()
            self.history.append((name.lower(), True))
            self.history = self.history[-2:]
            self.c_deq += 1
            self._emit(f"I {name}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            pending = next(
                (
                    i
                    for i in range(len(self.history) - 1, -1, -1)
                    if self.history[i][1]
                ),
                None,
            )
            if (
                pending is None
                or self.history[pending][0] != key
                or key in self.live
                or key in self.dead
            ):
                shown = self.names.get(key, item)
                self._emit(f"R {shown} STATE")
                return
            self.history[pending] = (key, False)
            self.fails[key] += 1
            self.c_fail += 1
            prio = max(1, self.orig[key] - 10 * self.fails[key])
            # Exact hundreds are reserved retry sentinels in the engine.
            if self.fails[key] >= 3 or prio % 100 == 0:
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {self.names[key]}")
                return
            self._push(key, prio, fresh=False)
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
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    while True:
        # The legacy reader consumes at most 511 bytes, through LF if present.
        line = stream.readline(_LINE_SIZE)
        if not line:
            break
        if isinstance(line, bytes):
            line = line.decode("latin-1")
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
