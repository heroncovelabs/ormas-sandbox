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
# Engine behavior the spec omits (the engine is the contract):
VOL_CAP = 9999999      # tank volume saturates here on refill
LOSS_STEP = 500        # each full 500 of a pour loses 1 to line residue
WHITE_BULK = 1000      # pours this large of a 'W' stock lose double
DRY_SLACK = 20         # shortfall up to this much grants what is left
WRITEOFF_GAP = 50      # reconcile writes off half of a book/physical gap above this


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str, volume: int) -> None:
        self.name = name
        self.pigment = pigment
        # filled: ledger fill total since the last reconcile baseline,
        # capped at VOL_CAP; book: filled minus grants; physical: what
        # the next dispense can actually draw.
        self.filled = min(volume, VOL_CAP)
        self.book = self.filled
        self.physical = self.filled


class Engine:
    """Blending controller with live dispense, reconcile, and counters."""

    def __init__(self) -> None:
        # Tank and job ids are case-insensitive; the first-seen spelling
        # is the one echoed back.
        self.tanks: dict[str, Tank] = {}
        self.jobs: dict[str, list] = {}
        self.fills = 0
        self.dispenses = 0
        self.reconciles = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line == "R":
            replies = self._reconcile()
        elif len(line) >= 2 and line[1] == " " and line[0] in "TD":
            # The engine splits on single spaces only (tabs stay inside
            # tokens) and ignores tokens past the documented arity.
            tokens = [tok for tok in line.split(" ") if tok]
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
            credit = max(0, min(volume, VOL_CAP - t.filled))
            t.filled += credit
            t.book += credit
            t.physical += credit
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
        if amount <= t.physical:
            granted = amount
        elif amount - t.physical <= DRY_SLACK:
            granted = t.physical
        else:
            return f"N {tank} DRY"
        loss = amount // LOSS_STEP
        if "W" in t.pigment and amount >= WHITE_BULK:
            loss *= 2
        t.book -= granted
        t.physical = max(0, t.physical - granted - loss)
        job = self.jobs.setdefault(tokens[1].lower(), [tokens[1], 0])
        job[1] += granted
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            gap = t.book - t.physical
            if gap > WRITEOFF_GAP:
                t.book -= gap // 2
            # The reconciled book becomes the new ledger baseline.
            t.physical = t.book
            t.filled = t.book
            replies.append(f"B {t.name} {t.book}")
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
