"""BlendCore ink-blending controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
blending commands on stdin (``T`` fills a tank with a pigment stock,
``D`` dispenses from a tank into a job, ``R`` reconciles every tank's
book volume from its ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Where the engine departs from the spec:

- A line ends at its first ``\\r``; tokens are separated by spaces only
  (runs collapse), and a line starting with a space is unrecognized.
- Tank and job ids are matched case-insensitively; replies use the
  spelling first seen. Pigments stay case-sensitive.
- Tokens beyond the documented ones on ``T``/``D`` are ignored.
- The fill ledger (book) and the physical volume are each capped at
  9999999 on fill.
- Each dispense loses ``amount // 500`` to the physical tank (doubled for
  pigments containing ``W`` when ``amount >= 1000``), never more than is
  left; the book does not see this loss.
- A dispense exceeding the physical volume by at most 20 is granted the
  physical volume instead of being rejected.
- ``R`` reports the book volume, less half the loss accumulated since the
  last reconcile when that loss exceeds 50 (floored at 0). The reported
  value becomes the tank's new physical and book baseline.
- At most 4096 tanks and 4096 jobs; a new one beyond that is ``FMT``
  (for a dispense, after the tank has already been drawn).
"""

from __future__ import annotations

import sys

ID_MAX = 8
NO_TANK = "????????"
VOL_CAP = 9999999
TANK_MAX = 4096
JOB_MAX = 4096
NEAR_DRY = 20
WRITEOFF_MIN = 50
_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
_DIGITS = frozenset("0123456789")


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and all(c in _ALNUM for c in token)


def _digits(token: str) -> bool:
    return bool(token) and all(c in _DIGITS for c in token)


def _key(token: str) -> str:
    return token.lower()


def _loss(pigment: str, amount: int) -> int:
    loss = amount // 500
    if "W" in pigment and amount >= 1000:
        loss *= 2
    return loss


class Tank:
    def __init__(self, name: str, pigment: str, volume: int) -> None:
        self.name = name
        self.pigment = pigment
        self.rebase(volume)

    def rebase(self, volume: int) -> None:
        # The fill ledger is capped as a running total; the physical
        # volume is capped on its own.
        self.filled = volume
        self.dispensed = 0
        self.lost = 0
        self.physical = volume

    @property
    def book(self) -> int:
        return self.filled - self.dispensed


class Engine:
    """Blending controller with live dispense, reconcile, and counters."""

    def __init__(self) -> None:
        self.tanks: dict[str, Tank] = {}
        self.jobs: dict[str, list] = {}
        self.fills = 0
        self.dispenses = 0
        self.reconciles = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line.startswith(" "):
            tokens = [""] + [t for t in line.split(" ") if t]
        else:
            tokens = [t for t in line.split(" ") if t]
        if line == "R":
            replies = self._reconcile()
        elif tokens[0] == "T":
            replies = [self._fill(tokens)]
        elif tokens[0] == "D":
            replies = [self._dispense(tokens)]
        else:
            replies = [f"N {NO_TANK} FMT"]
        if replies and replies[0].startswith("N "):
            self.rejected += 1
        return replies

    def trailer(self) -> str:
        return (
            f"X {self.fills} {self.dispenses} "
            f"{self.reconciles} {self.rejected}"
        )

    def _fill(self, tokens: list[str]) -> str:
        tank = tokens[1] if len(tokens) >= 2 else NO_TANK
        if len(tokens) < 4:
            return f"N {tank} FMT"
        if not _valid_id(tokens[1]) or not _valid_id(tokens[2]):
            return f"N {tank} FMT"
        vol_tok = tokens[3]
        if not _digits(vol_tok) or not 2 <= len(vol_tok) <= 7:
            return f"N {tank} VOL"
        volume = int(vol_tok)
        t = self.tanks.get(_key(tokens[1]))
        if t is not None:
            if t.pigment != tokens[2]:
                return f"N {tank} PIGMENT"
            t.filled = min(t.filled + volume, VOL_CAP)
            t.physical = min(t.physical + volume, VOL_CAP)
        elif len(self.tanks) >= TANK_MAX:
            return f"N {tank} FMT"
        else:
            self.tanks[_key(tokens[1])] = Tank(tokens[1], tokens[2], volume)
        self.fills += 1
        return f"OK {len(self.tanks)}"

    def _dispense(self, tokens: list[str]) -> str:
        tank = tokens[2] if len(tokens) >= 3 else NO_TANK
        if len(tokens) < 4:
            return f"N {tank} FMT"
        if not _valid_id(tokens[1]) or not _valid_id(tokens[2]):
            return f"N {tank} FMT"
        amt_tok = tokens[3]
        if not _digits(amt_tok) or len(amt_tok) > 6 or int(amt_tok) < 1:
            return f"N {tank} AMT"
        amount = int(amt_tok)
        t = self.tanks.get(_key(tokens[2]))
        if t is None:
            return f"N {tank} FMT"
        if amount > t.physical:
            if amount - t.physical > NEAR_DRY:
                return f"N {tank} DRY"
            amount = t.physical
        # The loss can't take more than what's left in the tank.
        loss = min(_loss(t.pigment, amount), t.physical - amount)
        t.dispensed += amount
        t.lost += loss
        t.physical -= amount + loss
        job = self.jobs.get(_key(tokens[1]))
        if job is None:
            if len(self.jobs) >= JOB_MAX:
                # The tank has already been drawn; the job is not credited.
                return f"N {tank} FMT"
            job = self.jobs[_key(tokens[1])] = [tokens[1], 0]
        job[1] += amount
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = t.book
            if t.lost > WRITEOFF_MIN:
                book -= t.lost // 2
            book = max(book, 0)
            t.rebase(book)
            replies.append(f"B {t.name} {book}")
        replies.append(f"REND {len(self.tanks)}")
        self.reconciles += 1
        return replies


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\n").split("\r", 1)[0].split("\0", 1)[0]
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    data = sys.stdin.buffer.read().decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    replies = process(lines)
    sys.stdout.buffer.write("".join(r + "\n" for r in replies).encode("latin-1"))


if __name__ == "__main__":
    main()
