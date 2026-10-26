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
VOLUME_MAX = 9_999_999
RECORD_MAX = 4096
NO_TANK = "????????"


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


def _tokens(line: str) -> list[str]:
    # The legacy tokenizer treats only a literal space as a delimiter.
    return [token for token in line.split(" ") if token]


class Tank:
    def __init__(self, tank_id: str, pigment: str, volume: int) -> None:
        self.tank_id = tank_id
        self.pigment = pigment
        self.volume = min(volume, VOLUME_MAX)
        self.fills = self.volume
        self.dispensed = 0
        self.residue = 0


class Job:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.total = 0


class Engine:
    """Blending controller with live dispense, reconcile, and counters."""

    def __init__(self) -> None:
        self.tanks: dict[str, Tank] = {}
        self.jobs: dict[str, Job] = {}
        self.fills = 0
        self.dispenses = 0
        self.reconciles = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        tokens = _tokens(line)
        if line == "R":
            replies = self._reconcile()
        elif line == "T" or line.startswith("T "):
            replies = [self._fill(tokens)]
        elif line == "D" or line.startswith("D "):
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
        key = tokens[1].upper()
        t = self.tanks.get(key)
        if t is not None:
            if t.pigment != tokens[2]:
                return f"N {tank} PIGMENT"
            t.volume = min(t.volume + volume, VOLUME_MAX)
            t.fills = min(t.fills + volume, VOLUME_MAX)
        else:
            if len(self.tanks) >= RECORD_MAX:
                return f"N {tank} FMT"
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
        t = self.tanks.get(tokens[2].upper())
        if t is None:
            return f"N {tank} FMT"
        if amount > t.volume and amount - t.volume > 20:
            return f"N {tank} DRY"
        granted = min(amount, t.volume)
        residue = granted // 500
        if granted > 999 and "W" in t.pigment:
            residue *= 2
        residue = min(residue, t.volume - granted)
        t.volume -= granted + residue
        t.dispensed += granted
        t.residue += residue
        key = tokens[1].upper()
        job = self.jobs.get(key)
        if job is None:
            if len(self.jobs) >= RECORD_MAX:
                return f"N {tank} FMT"
            job = Job(tokens[1])
            self.jobs[key] = job
        job.total += granted
        self.dispenses += 1
        return f"J {job.job_id} {job.total}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = t.fills - t.dispensed
            if t.residue > 50:
                book -= t.residue // 2
            book = max(book, 0)
            replies.append(f"B {t.tank_id} {book}")
            t.volume = book
            t.fills = book
            t.dispensed = 0
            t.residue = 0
        replies.append(f"REND {len(self.tanks)}")
        self.reconciles += 1
        return replies


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line == "":
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
