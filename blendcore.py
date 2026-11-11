"""BlendCore ink-blending controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
blending commands on stdin (``T`` fills a tank with a pigment stock,
``D`` dispenses from a tank into a job, ``R`` reconciles every tank's
book volume from its ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import sys

ID_MAX = 8
NO_TANK = "????????"
CAP = 9999999
TOLERANCE = 20


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str, volume: int) -> None:
        self.name = name
        self.pigment = pigment
        self.volume = min(CAP, volume)  # physical volume
        self.fills = volume  # book: filled since last reconcile
        self.dispensed = 0  # book: dispensed since last reconcile
        self.loss = 0  # physical loss since last reconcile

    @property
    def white(self) -> bool:
        return "W" in self.pigment


class Engine:
    """Blending controller with live dispense, reconcile, and counters."""

    def __init__(self) -> None:
        self.tanks: dict[str, Tank] = {}
        self.jobs: dict[str, tuple[str, int]] = {}
        self.fills = 0
        self.dispenses = 0
        self.reconciles = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        tokens = line.split()
        if not tokens:
            return []
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
        key = tokens[1].lower()
        t = self.tanks.get(key)
        if t is not None:
            if t.pigment != tokens[2]:
                return f"N {tank} PIGMENT"
            t.volume = min(CAP, t.volume + volume)
            t.fills += volume
        else:
            self.tanks[key] = Tank(tokens[1], tokens[2], volume)
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
        t = self.tanks.get(tokens[2].lower())
        if t is None:
            return f"N {tank} FMT"
        if amount > t.volume + TOLERANCE:
            return f"N {tank} DRY"
        delivered = min(amount, t.volume)
        per_mille = 4 if t.white and delivered >= 1000 else 2
        loss = delivered * per_mille // 1000
        t.volume = max(0, t.volume - delivered - loss)
        t.dispensed += delivered
        t.loss += loss
        job = tokens[1].lower()
        name, prev = self.jobs.get(job, (tokens[1], 0))
        total = prev + delivered
        self.jobs[job] = (name, total)
        self.dispenses += 1
        return f"J {name} {total}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = min(CAP, t.fills) - t.dispensed
            if t.loss >= (52 if t.white else 51):
                book -= t.loss // 2
            replies.append(f"B {t.name} {book}")
            t.fills = book
            t.dispensed = 0
            t.loss = 0
            t.volume = book
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
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
