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
VOLUME_MAX = 9_999_999
DRY_TOLERANCE = 20


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, tank_id: str, pigment: str, volume: int) -> None:
        self.tank_id = tank_id
        self.pigment = pigment
        self.volume = volume
        self.fills = volume
        self.dispensed = 0
        self.spilled = 0


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
        # The wire reader ends a command at CR or NUL. Only literal spaces
        # separate fields; leading spaces do not introduce a command.
        line = line.split("\r", 1)[0].split("\0", 1)[0].split("\n", 1)[0]
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
        t = self.tanks.get(tokens[1].lower())
        if t is not None:
            if t.pigment != tokens[2]:
                return f"N {tank} PIGMENT"
            # The physical tank and the fill ledger are capped independently.
            t.volume = min(VOLUME_MAX, t.volume + volume)
            t.fills = min(VOLUME_MAX, t.fills + volume)
        else:
            self.tanks[tokens[1].lower()] = Tank(tokens[1], tokens[2], volume)
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
        if amount > t.volume + DRY_TOLERANCE:
            return f"N {tank} DRY"
        granted = min(amount, t.volume)
        t.volume -= granted
        t.dispensed += granted

        # Spill is uncredited physical loss, limited by what remains in the
        # tank. White stock has an additional loss on bulk grants only.
        spill = granted // 500
        if "W" in t.pigment and granted >= 1000:
            spill += granted // 500
        spill = min(spill, t.volume)
        t.volume -= spill
        t.spilled += spill

        job_key = tokens[1].lower()
        job_id, total = self.jobs.get(job_key, (tokens[1], 0))
        total += granted
        self.jobs[job_key] = (job_id, total)
        self.dispenses += 1
        return f"J {job_id} {total}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            # Small spills are restored from the book. Once accumulated spill
            # exceeds 50 units, half is written off instead. Each reconcile
            # makes the adjusted book the new physical and ledger baseline.
            writeoff = t.spilled // 2 if t.spilled > 50 else 0
            book = max(0, t.fills - t.dispensed - writeoff)
            t.volume = book
            t.fills = book
            t.dispensed = 0
            t.spilled = 0
            replies.append(f"B {t.tank_id} {book}")
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
    # Do not let universal-newline translation turn an embedded CR into a
    # second command; the legacy wire reader discards the rest of that line.
    lines = sys.stdin.buffer.read().decode("utf-8", "surrogateescape").split("\n")
    process(lines, out=sys.stdout)


if __name__ == "__main__":
    main()
