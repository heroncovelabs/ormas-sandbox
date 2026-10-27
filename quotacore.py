"""QuotaCore metering engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: usage events on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

QUOTAS = {"F": 10_000, "S": 100_000, "P": 1_000_000}
RATES = {"F": 12, "S": 9, "P": 6}
# Premium customers in these regions are priced below the rate card.
PREMIUM_RATE_OVERRIDES = {"BR": 5, "IN": 5}
# Tier changes the engine accepts for an existing key (upgrades, one step).
UPGRADES = {("F", "F"), ("F", "S"), ("S", "S"), ("S", "P"), ("P", "P")}


def blocks_for(over: int) -> int:
    """Overage blocks: started blocks of 100, except an excess that ends in
    exactly 50 is not rounded up."""
    q, r = divmod(over, 100)
    if r == 50:
        return q
    return q + (1 if r else 0)


class Engine:
    def __init__(self, out=None):
        self.tier: dict[str, str] = {}
        self.used: dict[str, int] = {}
        self.name: dict[str, str] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_charges = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, key: str, code: str) -> None:
        self._emit(f"R {key} {code}")
        self.count_rej += 1

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and key.isalnum()
        if parts[0] != "Q" or len(parts) < 5 or not key_ok:
            self._emit(f"R {key if key_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, key, calls_tok, tier, region = parts[:5]
        if not (calls_tok.isdigit() and 1 <= len(calls_tok) <= 7):
            self._reject(key, "CALLS")
            return
        calls = int(calls_tok)
        if tier not in ("F", "S", "P"):
            self._reject(key, "TIER")
            return
        if not (len(region) == 2 and region.isalpha()):
            self._reject(key, "REGION")
            return

        if calls == 0:
            # zero-call heartbeats are valid no-ops: no output, no state
            return

        fold = key.lower()
        if fold not in self.tier:
            self.tier[fold] = tier
            self.used[fold] = 0
            self.name[fold] = key
            first = True
        else:
            first = False
            if tier != self.tier[fold] and (self.tier[fold], tier) not in UPGRADES:
                self._reject(self.name[fold], "TIER")
                return
            if tier != self.tier[fold]:
                self.tier[fold] = tier

        key = self.name[fold]
        current = self.tier[fold]
        limit = QUOTAS[current]
        rate = RATES[current]
        if current == "P" and region.upper() in PREMIUM_RATE_OVERRIDES:
            rate = PREMIUM_RATE_OVERRIDES[region.upper()]
        used = self.used[fold]
        if first:
            # burst credit: 10% of a first event that fits in the quota
            if calls <= limit:
                consumed = calls - calls // 10
            else:
                consumed = calls
            over = max(0, calls - limit)
        else:
            remaining = limit - used
            consumed = calls
            over = calls if calls > remaining else 0
        charge = blocks_for(over) * rate
        self.used[fold] = used + consumed

        left = max(0, limit - self.used[fold])
        self._emit(f"B {key} {charge} {left}")
        self.count_ok += 1
        self.sum_charges += charge

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_charges}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
