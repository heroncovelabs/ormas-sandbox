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
VOL_CAP = 9999999
SLACK = 20
LOSS_DIV = 500
WRITEOFF_MIN = 50
WHITE_PHYS_MIN = 1000


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str, volume: int) -> None:
        self.name = name
        self.pigment = pigment
        self.volume = volume  # physical volume the dispensers can draw
        self.fills = volume  # ledger baseline
        self.dispensed = 0  # ledger dispensed since the last reconcile

    @property
    def white(self) -> bool:
        return "W" in self.pigment


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
        if not line:
            return []
        tokens = [tok for tok in line.split(" ") if tok]
        if line == "R":
            replies = self._reconcile()
        elif line[0] == " " or not tokens:
            replies = [f"N {NO_TANK} FMT"]
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
            added = min(t.fills + volume, VOL_CAP) - t.fills
            t.volume += added
            t.fills += added
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
        if amount > t.volume + SLACK:
            return f"N {tank} DRY"
        grant = min(amount, t.volume)
        loss = grant // LOSS_DIV
        if t.white and grant >= WHITE_PHYS_MIN:
            loss += grant // LOSS_DIV
        t.volume = max(t.volume - grant - loss, 0)
        t.dispensed += grant
        job = self.jobs.get(tokens[1].lower())
        if job is None:
            job = self.jobs[tokens[1].lower()] = [tokens[1], 0]
        job[1] += grant
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = t.fills - t.dispensed
            shortfall = book - t.volume
            if shortfall > WRITEOFF_MIN:
                book -= shortfall // 2
            book = max(book, 0)
            t.fills = t.volume = book
            t.dispensed = 0
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
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
