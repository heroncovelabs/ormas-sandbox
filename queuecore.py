"""QueueCore work-queue engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: commands on stdin, result lines on stdout, trailer at end
of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

# Match the engine's ASCII scanf fields, including their width limits.
_FIELD = re.compile(r"[ \t\r\n\x0b\x0c]*([^ \t\r\n\x0b\x0c]{1,63})")
_LINE_END = re.compile(r"[\x00\r\n]")
# Item ids are 1-8 ASCII alphanumerics.
_ITEM = re.compile(r"[A-Za-z0-9]{1,8}")
# Priorities are 1-3 ASCII digits.
_PRIO = re.compile(r"[0-9]{1,3}")


class Engine:
    def __init__(self, out=None):
        # Internal keys are case-folded item ids. Keep the first accepted
        # spelling for dequeues, dead-letter replies, and STATE rejections.
        self.disp: dict[str, str] = {}
        self.orig: dict[str, int] = {}
        self.fails: dict[str, int] = {}
        self.live: set[str] = set()
        self.dead: list[str] = []
        self.queue: list[tuple[str, int, int]] = []  # (key, prio, seq)
        self.seq_next = 1
        self.age: dict[str, int] = {}
        # Keep the last two successful dequeues, including consumed records.
        # A new dequeue displaces the oldest record even after an undo.
        self.history: list[tuple[str, bool]] = []
        self.c_enq = 0
        self.c_deq = 0
        self.c_fail = 0
        self.c_dead = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _push(self, key: str, prio: int, *, retry: bool = False) -> None:
        # Retrying keeps the age of the enqueue that originally admitted the
        # item. Explicit enqueues and dead-letter drains establish a new age.
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

    def handle(self, line: str) -> None:
        # The C reader terminates a command at the first CR, LF, or NUL.
        raw = _LINE_END.split(line, maxsplit=1)[0]
        if raw == "":
            return
        parts = []
        pos = 0
        for width in (7, 63, 63):
            field = _FIELD.match(raw, pos)
            if field is None:
                break
            token = field[1][:width]
            parts.append(token)
            pos = field.start(1) + len(token)
        if not parts:
            # Whitespace-only line: an empty command word, which is malformed.
            self._emit("R ???????? FMT")
            return
        kind = parts[0]
        item = parts[1] if len(parts) > 1 else ""
        item_ok = _ITEM.fullmatch(item) is not None
        echo = item if item_ok else "????????"
        key = item.lower()

        if kind == "N":
            if len(parts) < 3 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            ptok = parts[2]
            if not (_PRIO.fullmatch(ptok) and 1 <= int(ptok) <= 999):
                self._emit(f"R {item} PRIO")
                return
            prio = int(ptok)
            if key in self.live or key in self.dead:
                self._emit(f"R {self.disp.get(key, item)} STATE")
                return
            if key not in self.orig:
                # Completed items retain their records for the whole session.
                if len(self.orig) >= 4096:
                    self._emit(f"R {item} FMT")
                    return
                self.fails[key] = 0
                self.disp[key] = item
            self.orig[key] = prio
            self._push(key, prio)
            self.c_enq += 1
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "D":
            # Trailing tokens are ignored.
            if not self.queue:
                self._emit("EMPTY")
                return
            key = self._pop_best()
            self.history.append((key, True))
            self.history = self.history[-2:]
            self.c_deq += 1
            self._emit(f"I {self.disp[key]}")
            return

        if kind == "F":
            if len(parts) < 2 or not item_ok:
                self._emit(f"R {echo} FMT")
                return
            pending = next(
                (
                    i for i in range(len(self.history) - 1, -1, -1)
                    if self.history[i][1]
                ),
                None,
            )
            if (
                pending is None or self.history[pending][0] != key
                or key in self.live or key in self.dead
            ):
                self._emit(f"R {self.disp.get(key, item)} STATE")
                return
            self.history[pending] = (key, False)
            self.fails[key] += 1
            self.c_fail += 1
            # Priority 999 is the engine's internal 1000 cap. Penalties are
            # cumulative across retries and explicit re-enqueues; K resets them.
            base = 1000 if self.orig[key] == 999 else self.orig[key]
            prio = max(1, base - 10 * self.fails[key])
            # Positive hundreds are reserved dead-letter sentinel priorities.
            if self.fails[key] >= 3 or prio % 100 == 0:
                self.dead.append(key)
                self.c_dead += 1
                self._emit(f"DLQ {self.disp[key]}")
                return
            self._push(key, prio, retry=True)
            self._emit(f"OK {len(self.queue)}")
            return

        if kind == "K":
            # Trailing tokens are ignored.
            for dkey in self.dead:
                self.fails[dkey] = 0
                self._push(dkey, self.orig[dkey])
            self.dead = []
            self._emit(f"OK {len(self.queue)}")
            return

        self._emit(f"R {echo} FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_enq} {self.c_deq} {self.c_fail} {self.c_dead}")


def main() -> None:
    engine = Engine()
    # fgets used a 512-byte buffer: overlong lines become multiple commands.
    # Read bytes so CRs and non-ASCII input retain the engine's parsing rules.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("ascii", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
