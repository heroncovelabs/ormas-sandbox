"""QuotaCore metering engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: usage events on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

QUOTAS = {"F": 10_000, "S": 100_000, "P": 1_000_000}
RATES = {"F": 12, "S": 9, "P": 6}
# Premium customers in these regions are billed below the published rate.
PREMIUM_DISCOUNT_REGIONS = ("BR", "IN")
PREMIUM_DISCOUNT_RATE = 5
# Tiers may only be upgraded one step at a time.
UPGRADE = {"F": "S", "S": "P"}

_WS = re.compile(r"[ \t\n\v\f\r]+")
_ALNUM = re.compile(r"[A-Za-z0-9]+")
_DIGITS = re.compile(r"[0-9]+")
_ALPHA2 = re.compile(r"[A-Za-z]{2}")


def _blocks(n: int) -> int:
    """Started blocks of 100; an exact half block (remainder 50) rounds down."""
    q, r = divmod(n, 100)
    if r == 0 or r == 50:
        return q
    return q + 1


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
        line = line.rstrip("\r\n")
        if line == "":
            return
        parts = [p for p in _WS.split(line) if p]
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and _ALNUM.fullmatch(key) is not None
        if parts[:1] != ["Q"] or len(parts) < 5 or not key_ok:
            self._emit(f"R {key if key_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, key, calls_tok, tier, region = parts[:5]
        if not (_DIGITS.fullmatch(calls_tok) and 1 <= len(calls_tok) <= 7):
            self._reject(key, "CALLS")
            return
        calls = int(calls_tok)
        if tier not in ("F", "S", "P"):
            self._reject(key, "TIER")
            return
        if not _ALPHA2.fullmatch(region):
            self._reject(key, "REGION")
            return
        if calls == 0:
            return

        folded = key.lower()
        if folded not in self.tier:
            self.name[folded] = key
            self.tier[folded] = tier
            self.used[folded] = 0
        elif tier != self.tier[folded]:
            if UPGRADE.get(self.tier[folded]) != tier:
                self._reject(self.name[folded], "TIER")
                return
            self.tier[folded] = tier

        cur = self.tier[folded]
        limit = QUOTAS[cur]
        used = self.used[folded]
        rate = RATES[cur]
        if cur == "P" and region.upper() in PREMIUM_DISCOUNT_REGIONS:
            rate = PREMIUM_DISCOUNT_RATE

        if used >= limit:
            over = calls
        elif used + calls > limit:
            # An event crossing into overage is billed on all of its calls;
            # a key's very first event is billed on its overage portion only.
            over = calls - limit if used == 0 else calls
        else:
            over = 0
        charge = _blocks(over) * rate

        if used == 0 and calls <= limit:
            # Burst bank: a key's first event only consumes 90% of its calls.
            self.used[folded] = calls - calls // 10
        else:
            self.used[folded] = used + calls

        left = max(0, limit - self.used[folded])
        self._emit(f"B {self.name[folded]} {charge} {left}")
        self.count_ok += 1
        self.sum_charges += charge

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_charges}")


def main() -> None:
    engine = Engine()
    for raw in sys.stdin.buffer:
        engine.handle(raw.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
