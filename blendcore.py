"""BlendCore ink-blending controller, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
blending commands on stdin (``T`` fills a tank with a pigment stock,
``D`` dispenses from a tank into a job, ``R`` reconciles every tank's
book volume from its ledger), writes one reply per command and an ``X``
trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Engine behavior that the spec does not describe:

- Tank and job ids are matched case-insensitively; replies use the
  spelling first seen. Pigments compare exactly.
- Tokens are separated by runs of spaces only; the command letter must
  be the first character of the line. Tokens past the documented arity
  are ignored (except for ``R``, which must stand alone).
- Every granted dispense loses ``amount // 500`` to drip in the physical
  tank (doubled for pigments containing ``W`` once the pour is at least
  1000), clamped so the tank never goes below empty.
- A dispense up to ``NEAR_DRY`` beyond the physical volume is granted
  short (the remaining physical volume) instead of rejected.
- Book fills are capped at ``VOL_CAP``; the physical tank is capped
  separately.
- ``R`` writes off half the drip lost since the previous reconcile when it
  exceeds ``WRITEOFF_MIN``, and the result becomes the tank's new
  baseline for both the book and the physical volume.
"""

from __future__ import annotations

import sys

ID_MAX = 8
NO_TANK = "????????"
VOL_CAP = 9999999
DRIP_UNIT = 500
WHITE_MARK = "W"
WHITE_MIN = 1000
NEAR_DRY = 20
WRITEOFF_MIN = 50


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Tank:
    def __init__(self, name: str, pigment: str) -> None:
        self.name = name
        self.pigment = pigment
        self.fills = 0
        self.dispensed = 0
        self.physical = 0
        self.lost = 0

    def fill(self, volume: int) -> None:
        self.fills = min(self.fills + volume, VOL_CAP)
        self.physical = min(self.physical + volume, VOL_CAP)

    def drip(self, amount: int) -> int:
        loss = amount // DRIP_UNIT
        if WHITE_MARK in self.pigment and amount >= WHITE_MIN:
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
        if not line:
            return []
        tokens = [tok for tok in line.split(" ") if tok]
        if line == "R":
            replies = self._reconcile()
        elif line[0] == "T" and (len(line) == 1 or line[1] == " "):
            replies = [self._fill(tokens)]
        elif line[0] == "D" and (len(line) == 1 or line[1] == " "):
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
        else:
            t = Tank(tokens[1], tokens[2])
            self.tanks[key] = t
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
        if amount > t.physical:
            if amount - t.physical > NEAR_DRY:
                return f"N {tank} DRY"
            amount = t.physical
        loss = min(t.drip(amount), t.physical - amount)
        t.physical -= amount + loss
        t.lost += loss
        t.dispensed += amount
        job = self.jobs.setdefault(tokens[1].lower(), [tokens[1], 0])
        job[1] += amount
        self.dispenses += 1
        return f"J {job[0]} {job[1]}"

    def _reconcile(self) -> list[str]:
        replies = []
        for t in self.tanks.values():
            book = t.fills - t.dispensed
            if t.lost > WRITEOFF_MIN:
                book -= t.lost // 2
            book = max(book, 0)
            t.fills = book
            t.dispensed = 0
            t.physical = book
            t.lost = 0
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
