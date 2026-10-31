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
TABLE_MAX = 4096
VOLUME_MAX = 9999999
NO_TANK = "????????"


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str, volume: int) -> None:
        self.name = name
        self.pigment = pigment
        self.volume = volume
        self.fills = volume
        self.dispensed = 0
        self.loss = 0


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
        # The wire parser terminates at the first CR, LF, or NUL. Only
        # literal spaces separate fields; command prefixes are positional.
        for terminator in ("\r", "\n", "\0"):
            line = line.split(terminator, 1)[0]
        if not line:
            return []
        tokens = [token for token in line.split(" ") if token]
        if line == "R":
            replies = self._reconcile()
        elif line.startswith("T "):
            replies = [self._fill(tokens)]
        elif line.startswith("D "):
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
        key = tank.lower()
        t = self.tanks.get(key)
        if t is not None:
            if t.pigment != tokens[2]:
                return f"N {tank} PIGMENT"
            # Physical stock and the current ledger's fill baseline cap
            # independently, even when pours have opened physical headroom.
            t.volume = min(VOLUME_MAX, t.volume + volume)
            t.fills = min(VOLUME_MAX, t.fills + volume)
        else:
            if len(self.tanks) >= TABLE_MAX:
                return f"N {tank} FMT"
            self.tanks[key] = Tank(tank, tokens[2], volume)
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
        t = self.tanks.get(tank.lower())
        if t is None:
            return f"N {tank} FMT"
        if amount > t.volume + 20:
            return f"N {tank} DRY"
        granted = min(amount, t.volume)
        t.volume -= granted
        t.dispensed += granted

        # Uncredited stock loss is rounded per pour, doubled for bulk
        # uppercase-W stock, and limited to the stock remaining after it.
        loss = granted // 500
        if granted >= 1000 and "W" in t.pigment:
            loss *= 2
        loss = min(loss, t.volume)
        t.volume -= loss
        t.loss += loss

        # The legacy engine draws stock before trying to create a job.
        # A full job table therefore rejects after updating the tank ledger.
        key = tokens[1].lower()
        if key not in self.jobs:
            if len(self.jobs) >= TABLE_MAX:
                return f"N {tank} FMT"
            self.jobs[key] = (tokens[1], 0)
        name, total = self.jobs[key]
        total += granted
        self.jobs[key] = (name, total)
        self.dispenses += 1
        return f"J {name} {total}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            # Small accumulated losses are restored. Above fifty units,
            # half the loss (rounded down) becomes a permanent writeoff.
            writeoff = t.loss // 2 if t.loss > 50 else 0
            book = max(0, t.fills - t.dispensed - writeoff)
            t.volume = book
            t.fills = book
            t.dispensed = 0
            t.loss = 0
            replies.append(f"B {t.name} {book}")
        replies.append(f"REND {len(self.tanks)}")
        self.reconciles += 1
        return replies


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        replies.extend(engine.handle(raw))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Read LF-delimited wire lines without universal-newline translation:
    # CR terminates a command and discards the rest of that same wire line.
    lines = [raw.decode("utf-8", "surrogateescape") for raw in sys.stdin.buffer]
    process(lines, out=sys.stdout)


if __name__ == "__main__":
    main()
