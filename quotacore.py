"""QuotaCore metering engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: usage events on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behaviors not (or wrongly) described in the spec:
- keys are case-insensitive; the first-seen spelling is kept;
- tokens after the region are ignored; regions are case-insensitive;
- zero-call events are validated, then dropped (no output, not counted);
- a key may upgrade one tier step at a time (F->S, S->P);
- a first event within the base quota banks 10% of its calls as extra quota;
- an event after the first that runs past the quota is billed on all of its
  calls, not just the overage portion;
- blocks round up, except an exact half block (x50) rounds down;
- premium in BR and IN is billed 5 cents per block.
"""

from __future__ import annotations

import re
import sys

ASCII_WS = re.compile(r"[ \t\v\f\r\n]+")
QUOTAS = {"F": 10_000, "S": 100_000, "P": 1_000_000}
RATES = {"F": 12, "S": 9, "P": 6}
UPGRADES = {"F": "S", "S": "P"}
PREMIUM_DISCOUNT_REGIONS = ("BR", "IN")
ASCII_ALNUM = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
ASCII_ALPHA = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
DIGITS = set("0123456789")


def _blocks(calls: int) -> int:
    if calls % 100 == 50:
        return calls // 100
    return -(-calls // 100)


class Engine:
    def __init__(self, out=None):
        self.name: dict[str, str] = {}
        self.tier: dict[str, str] = {}
        self.used: dict[str, int] = {}
        self.bank: dict[str, int] = {}
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
        line = line.rstrip("\n").split("\r", 1)[0]
        if not line:
            return
        parts = ASCII_WS.split(line.strip(" \t\v\f\r\n"))
        if parts == [""]:
            parts = []
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and set(key) <= ASCII_ALNUM
        if not parts or parts[0] != "Q" or len(parts) < 5 or not key_ok:
            self._reject(key if key_ok else "????????", "FMT")
            return
        _, key, calls_tok, tier, region = parts[:5]
        if not (1 <= len(calls_tok) <= 7 and set(calls_tok) <= DIGITS):
            self._reject(key, "CALLS")
            return
        calls = int(calls_tok)
        if tier not in QUOTAS:
            self._reject(key, "TIER")
            return
        if not (len(region) == 2 and set(region) <= ASCII_ALPHA):
            self._reject(key, "REGION")
            return
        region = region.upper()
        if calls == 0:
            return

        k = key.lower()
        first = k not in self.tier
        if first:
            self.name[k] = key
            self.tier[k] = tier
            self.used[k] = 0
            self.bank[k] = 0
        elif tier != self.tier[k]:
            if UPGRADES.get(self.tier[k]) != tier:
                self._reject(self.name[k], "TIER")
                return
            self.tier[k] = tier
        key = self.name[k]

        limit = QUOTAS[tier] + self.bank[k]
        used = self.used[k] + calls
        if first:
            over = max(0, used - limit)
        else:
            over = calls if used > limit else 0
        rate = RATES[tier]
        if tier == "P" and region in PREMIUM_DISCOUNT_REGIONS:
            rate = 5
        charge = _blocks(over) * rate
        self.used[k] = used
        if first and calls <= QUOTAS[tier]:
            self.bank[k] = calls // 10
            limit += self.bank[k]

        left = max(0, limit - used)
        self._emit(f"B {key} {charge} {left}")
        self.count_ok += 1
        self.sum_charges += charge

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_charges}")


def main() -> None:
    sys.stdin.reconfigure(errors="surrogateescape", newline="\n")
    sys.stdout.reconfigure(errors="surrogateescape")
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
