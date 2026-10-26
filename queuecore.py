"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

# The engine scans byte-sized fields with sscanf-style width limits.
_TOKEN = re.compile(r"[^ \t\n\r\x0b\x0c]+")
_LINE_END = re.compile(r"[\x00\r\n]")


def _is_item(s: str) -> bool:
    """Engine item token: 1-8 ASCII letters or digits."""
    return 1 <= len(s) <= 8 and s.isascii() and s.isalnum()


class Engine:
    def __init__(self, out=None):
        # All identity-keyed maps use the canonical key (ASCII lowercase).
        self.orig: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.display: dict[str, str] = {}  # key -> spelling from first accepted enqueue
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (key, prio, seq)
        self.age: dict[str, int] = {}
        self.seq_next = 1
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        # The two latest dequeues, oldest first. Consumed slots stay in the
        # window so a new dequeue also ages out already-undone history.
        self.hist: list[str | None] = []
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, key: str, prio: int, *, retry: bool = False) -> None:
        # Retries retain their enqueue age; N and K start a new FIFO age.
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

    def handle(self, line: str | bytes) -> None:
        if isinstance(line, str):
            line = line.encode("utf-8", "surrogateescape")
        # Latin-1 preserves byte widths; accepted item spellings are ASCII.
        rest = _LINE_END.split(line.decode("latin1"), maxsplit=1)[0]
        if not rest:
            return
        parts = []
        for width in (7, 63, 63):
            rest = rest.lstrip(" \t\n\r\x0b\x0c")
            match = _TOKEN.match(rest)
            if match is None:
                break
            token = match.group()[:width]
            parts.append(token)
            rest = rest[len(token):]
        if not parts:
            self._emit("R ???????? FMT")
            return
        kind = parts[0]
        raw = parts[1] if len(parts) > 1 else ""
        item_ok = _is_item(raw)
        echo = raw if item_ok else "????????"
        key = raw.lower() if item_ok else ""

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if not (ptok.isascii() and ptok.isdigit() and 1 <= len(ptok) <= 3):
                self._emit(f"R {raw} PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 999:
                self._emit(f"R {raw} PRIO")
                return
            if key in self.live or key in self.dead:
                self._emit(f"R {self.display[key]} STATE")
                return
            if key not in self.orig:
                # Completed jobs still occupy the engine's identity table.
                if len(self.orig) >= 4096:
                    self._emit(f"R {raw} FMT")
                    return
                self.fails[key] = 0
                self.display[key] = raw
            if key in self.hist:
                # Enqueuing a dequeued item closes it and every older slot.
                end = self.hist.index(key) + 1
                self.hist[:end] = [None] * end
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
            self.hist.append(key)
            if len(self.hist) > 2:
                del self.hist[0]
            self.c_deq += 1
            self._emit(f"I {self.display[key]}")
            return

        if kind == "F":
            if not item_ok:
                self._emit(f"R {echo} FMT")
                return
            slot = next(
                (
                    i for i in range(len(self.hist) - 1, -1, -1)
                    if self.hist[i] is not None
                ),
                None,
            )
            if slot is None or self.hist[slot] != key:
                self._emit(f"R {self.display.get(key, raw)} STATE")
                return
            self.hist[slot] = None
            self.fails[key] += 1
            self.c_fail += 1
            # The top-priority encoding represents 1000 during retry math.
            base = 1000 if self.orig[key] == 999 else self.orig[key]
            prio = max(1, base - 10 * self.fails[key])
            # Positive hundred boundaries are the engine's dead-letter sentinels.
            if self.fails[key] >= 3 or prio % 100 == 0:
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {self.display[key]}")
                return
            self._push(key, prio, retry=True)
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
    # Match the retired engine's 512-byte fgets buffer, including its
    # treatment of oversized lines as successive command chunks.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
