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


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


CAP = 9999999
GRACE = 20
WRITEOFF_MIN_DRAIN = 51


class Tank:
    def __init__(self, name: str, pigment: str) -> None:
        self.name = name
        self.pigment = pigment
        self.volume = 0   # live (physical) volume
        self.ledger = 0   # book volume baseline
        self.filled = 0   # cumulative fills, capped
        self.drain = 0    # live handling loss since last reconcile


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
        if line == "R":
            replies = self._reconcile()
        elif line[0] == "T" and line[1:2] == " ":
            replies = [self._fill([t for t in line.split(" ") if t])]
        elif line[0] == "D" and line[1:2] == " ":
            replies = [self._dispense([t for t in line.split(" ") if t])]
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
        else:
            t = Tank(tokens[1], tokens[2])
            self.tanks[key] = t
        new_filled = min(t.filled + volume, CAP)
        delta = new_filled - t.filled
        t.filled = new_filled
        t.volume += delta
        t.ledger += delta
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
        if amount > t.volume + GRACE:
            return f"N {tank} DRY"
        granted = min(amount, t.volume)
        extra = amount // 500
        if "W" in t.pigment and amount >= 1000:
            extra *= 2
        t.volume = max(0, t.volume - granted - extra)
        t.ledger -= granted
        t.drain += extra
        job = self.jobs.get(tokens[1].lower())
        if job is None:
            job = self.jobs[tokens[1].lower()] = [tokens[1], 0]
        job[1] += granted
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            if t.drain >= WRITEOFF_MIN_DRAIN:
                t.ledger -= t.drain // 2
            t.drain = 0
            t.ledger = max(t.ledger, 0)
            t.volume = t.ledger
            t.filled = t.ledger
            replies.append(f"B {t.name} {t.ledger}")
        replies.append(f"REND {len(self.tanks)}")
        self.reconciles += 1
        return replies


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\n")
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
