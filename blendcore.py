"""BlendCore ink-blending controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
blending commands on stdin (``T`` fills a tank with a pigment stock,
``D`` dispenses from a tank into a job, ``R`` reconciles every tank's
book volume from its ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Engine behavior that differs from the spec:

- Lines are cut at the first ``\\r`` or NUL; only spaces separate tokens
  (runs of spaces collapse); a line starting with a space is FMT.
- ``T`` and ``D`` ignore tokens past the documented arity.
- Tank and job ids are case-insensitive; replies show the first-seen
  spelling. Pigments are compared case-sensitively.
- A tank's filled total since its last reconcile is capped at
  ``VOLUME_CAP``; fills beyond the cap are silently dropped.
- Every live dispense loses ``amount // 500`` from the physical volume
  (doubled for pours of 1000+ from pigments containing an uppercase
  ``W``); the book volume does not see the loss.
- A dispense up to ``DRY_SLACK`` over the physical volume is granted
  short (whatever is left); beyond that it is DRY.
- ``R`` compares book with physical: a gap over ``WRITEOFF_GAP`` writes
  off half of it from the book; the tank's physical volume and fill
  baseline are then reset to the reconciled book.
"""

from __future__ import annotations

import sys

ID_MAX = 8
NO_TANK = "????????"
VOLUME_CAP = 9999999
LOSS_STEP = 500
WHITE_BULK = 1000
DRY_SLACK = 20
WRITEOFF_GAP = 50


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str) -> None:
        self.name = name
        self.pigment = pigment
        self.white = "W" in pigment
        self.fills = 0  # filled since the last reconcile (the baseline)
        self.dispensed = 0  # granted since the last reconcile
        self.physical = 0

    @property
    def book(self) -> int:
        return self.fills - self.dispensed

    def fill(self, volume: int) -> None:
        added = min(VOLUME_CAP, self.fills + volume) - self.fills
        self.fills += added
        self.physical += added

    def loss(self, amount: int) -> int:
        loss = amount // LOSS_STEP
        if self.white and amount >= WHITE_BULK:
            loss *= 2
        return loss


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
        tokens = [tok for tok in line.split(" ") if tok]
        if line == "R":
            replies = self._reconcile()
        elif tokens and tokens[0] == "T" and line[0] == "T":
            replies = [self._fill(tokens)]
        elif tokens and tokens[0] == "D" and line[0] == "D":
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
        if t is None:
            t = Tank(tokens[1], tokens[2])
            self.tanks[key] = t
        elif t.pigment != tokens[2]:
            return f"N {tank} PIGMENT"
        t.fill(volume)
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
        if amount > t.physical + DRY_SLACK:
            return f"N {tank} DRY"
        granted = min(amount, t.physical)
        t.physical = max(0, t.physical - granted - t.loss(amount))
        t.dispensed += granted
        job = self.jobs.setdefault(tokens[1].lower(), [tokens[1], 0])
        job[1] += granted
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = t.book
            gap = book - t.physical
            if gap > WRITEOFF_GAP:
                book -= gap // 2
            t.fills = book
            t.dispensed = 0
            t.physical = book
            replies.append(f"B {t.name} {book}")
        replies.append(f"REND {len(self.tanks)}")
        self.reconciles += 1
        return replies


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\n")
        for stop in ("\r", "\0"):
            line = line.split(stop, 1)[0]
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        out.write("".join(reply + "\n" for reply in replies))
    return replies


def main() -> None:
    data = sys.stdin.buffer.read().decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    stdout = open(sys.stdout.fileno(), "w", encoding="latin-1", closefd=False)
    process(lines, out=stdout)
    stdout.flush()


if __name__ == "__main__":
    main()
