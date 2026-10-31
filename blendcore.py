"""BlendCore ink-blending controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
blending commands on stdin (``T`` fills a tank with a pigment stock,
``D`` dispenses from a tank into a job, ``R`` reconciles every tank's
book volume from its ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Engine behavior that differs from the spec:

* Tank and job ids are case-insensitive (first-seen spelling is kept);
  pigments compare case-sensitively. Tokens are separated by spaces only
  and trailing tokens after the documented ones are ignored.
* The fills ledger is capped at ``FILL_CAP``; the physical volume is not.
* Every pour loses ``amount // 500`` physically (doubled for pours of at
  least 1000 from pigments containing an uppercase ``W``), never more
  than what is left in the tank. The loss is invisible to the book until
  a reconcile.
* A request at most ``DRY_SLACK`` over the physical volume is granted
  short (the whole physical volume) instead of being rejected.
* ``R`` writes off half of the loss accumulated since the last reconcile
  when it exceeds ``WRITEOFF_MIN``; the resulting book volume becomes the
  tank's new baseline (ledger and physical volume).
"""

from __future__ import annotations

import sys

ID_MAX = 8
NO_TANK = "????????"
FILL_CAP = 9999999
LOSS_UNIT = 500
WHITE_MIN = 1000
DRY_SLACK = 20
WRITEOFF_MIN = 50


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str) -> None:
        self.name = name
        self.pigment = pigment
        self.white = "W" in pigment
        self.fills = 0
        self.dispensed = 0
        self.physical = 0
        self.loss = 0

    def fill(self, volume: int) -> None:
        self.fills = min(self.fills + volume, FILL_CAP)
        self.physical += volume

    def book(self) -> int:
        return self.fills - self.dispensed


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
        if line == "R":
            replies = self._reconcile()
        elif line[0] in "TD" and (len(line) == 1 or line[1] == " "):
            tokens = [t for t in line[1:].split(" ") if t]
            if line[0] == "T":
                replies = [self._fill(tokens)]
            else:
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
        tank = tokens[0] if tokens else NO_TANK
        if len(tokens) < 3:
            return f"N {tank} FMT"
        if not _valid_id(tokens[0]) or not _valid_id(tokens[1]):
            return f"N {tank} FMT"
        vol_tok = tokens[2]
        if not _digits(vol_tok) or not 2 <= len(vol_tok) <= 7:
            return f"N {tank} VOL"
        volume = int(vol_tok)
        key = tokens[0].lower()
        t = self.tanks.get(key)
        if t is None:
            t = Tank(tokens[0], tokens[1])
            self.tanks[key] = t
        elif t.pigment != tokens[1]:
            return f"N {tank} PIGMENT"
        t.fill(volume)
        self.fills += 1
        return f"OK {len(self.tanks)}"

    def _dispense(self, tokens: list[str]) -> str:
        tank = tokens[1] if len(tokens) >= 2 else NO_TANK
        if len(tokens) < 3:
            return f"N {tank} FMT"
        if not _valid_id(tokens[0]) or not _valid_id(tokens[1]):
            return f"N {tank} FMT"
        amt_tok = tokens[2]
        if not _digits(amt_tok) or len(amt_tok) > 6 or int(amt_tok) < 1:
            return f"N {tank} AMT"
        amount = int(amt_tok)
        t = self.tanks.get(tokens[1].lower())
        if t is None:
            return f"N {tank} FMT"
        if amount > t.physical:
            if amount - t.physical > DRY_SLACK:
                return f"N {tank} DRY"
            amount = t.physical
        t.physical -= amount
        t.dispensed += amount
        loss = amount // LOSS_UNIT
        if t.white and amount >= WHITE_MIN:
            loss *= 2
        loss = min(loss, t.physical)
        t.physical -= loss
        t.loss += loss
        job = self.jobs.setdefault(tokens[0].lower(), [tokens[0], 0])
        job[1] += amount
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = t.book()
            if t.loss > WRITEOFF_MIN:
                book -= t.loss // 2
            t.fills = book
            t.dispensed = 0
            t.physical = book
            t.loss = 0
            replies.append(f"B {t.name} {book}")
        replies.append(f"REND {len(self.tanks)}")
        self.reconciles += 1
        return replies


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    data = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
    process(data.split("\n"), out=sys.stdout)


if __name__ == "__main__":
    main()
