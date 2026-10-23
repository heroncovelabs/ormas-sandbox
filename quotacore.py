"""QuotaCore metering engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: usage events on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import math
import sys

QUOTAS = {"F": 10_000, "S": 100_000, "P": 1_000_000}
RATES = {"F": 12, "S": 9, "P": 6}
TIER_ORDER = {"F": 0, "S": 1, "P": 2}


class Engine:
    def __init__(self, out=None):
        self.tier: dict[str, str] = {}
        self.used: dict[str, int] = {}
        self.bank: dict[str, int] = {}
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
        # Trailing tokens beyond the fifth are ignored by the engine.
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
        # The engine accepts region codes in any case.
        if not (len(region) == 2 and region.isascii() and region.isalpha()):
            self._reject(key, "REGION")
            return
        region = region.upper()

        # Zero-call heartbeats are silently dropped: no output, not counted,
        # and they do not register the key.
        if calls == 0:
            return

        # Keys are matched case-insensitively; output keeps the first spelling.
        canon = key.lower()
        first = canon not in self.tier
        if first:
            self.tier[canon] = tier
            self.used[canon] = 0
            self.bank[canon] = 0
            self.name[canon] = key
        elif TIER_ORDER[tier] - TIER_ORDER[self.tier[canon]] not in (0, 1):
            self._reject(self.name[canon], "TIER")
            return
        else:
            # One-step upgrades are allowed; consumption carries over.
            self.tier[canon] = tier
        key = self.name[canon]

        tier = self.tier[canon]
        limit = QUOTAS[tier] + self.bank[canon]
        used = self.used[canon]
        if used + calls <= limit:
            over = 0
        elif used >= limit or first:
            over = used + calls - max(used, limit)
        else:
            # An event crossing from quota into overage is billed in full.
            over = calls
        blocks = over // 100 if over % 100 == 50 else -(-over // 100)
        rate = RATES[tier]
        if tier == "P" and region in ("BR", "IN"):
            rate = 5
        charge = blocks * rate
        self.used[canon] = used + calls
        if first and over == 0:
            # Burst bank: a first event within quota credits a tenth of its
            # calls to the key's quota.
            self.bank[canon] = calls // 10
            limit = QUOTAS[tier] + self.bank[canon]

        left = max(0, limit - self.used[canon])
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
