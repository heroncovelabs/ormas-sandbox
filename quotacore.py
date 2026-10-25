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


class Engine:
    def __init__(self, out=None):
        self.tier: dict[str, str] = {}
        self.display: dict[str, str] = {}
        self.used: dict[str, int] = {}
        self.burst_used: dict[str, int] = {}
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
        if not line:
            return
        parts = line.split()
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and key.isascii() and key.isalnum()
        if not parts or parts[0] != "Q" or len(parts) < 5 or not key_ok:
            self._emit(f"R {key if key_ok else '????????'} FMT")
            self.count_rej += 1
            return
        _, key, calls_tok, tier, region = parts[:5]
        if not (calls_tok.isascii() and calls_tok.isdigit() and 1 <= len(calls_tok) <= 7):
            self._reject(key, "CALLS")
            return
        calls = int(calls_tok)
        if tier not in ("F", "S", "P"):
            self._reject(key, "TIER")
            return
        if not (len(region) == 2 and region.isascii() and region.isalpha()):
            self._reject(key, "REGION")
            return
        region = region.upper()

        # The engine matches keys without regard to case, but retains the
        # spelling from the first event for all subsequent output.
        canonical = key.upper()
        if calls == 0:
            return
        if canonical not in self.tier:
            self.tier[canonical] = tier
            self.display[canonical] = key
            self.used[canonical] = 0
            self.burst_used[canonical] = 0
        elif tier != self.tier[canonical]:
            order = {"F": 0, "S": 1, "P": 2}
            if order[tier] != order[self.tier[canonical]] + 1:
                self._reject(self.display[canonical], "TIER")
                return
            self.tier[canonical] = tier

        key = self.display[canonical]
        tier = self.tier[canonical]
        limit = QUOTAS[tier]
        used = self.used[canonical]
        within = max(0, min(calls, limit + self.burst_used[canonical] - used))
        over = calls - within

        # Fully included events credit a tenth of their calls to the legacy
        # burst bank. An event crossing the raw quota boundary is instead
        # charged on its entire call count.
        crossing = used > 0 and over > 0
        rounded_over = calls if crossing else over
        if rounded_over % 100 == 50:
            blocks = rounded_over // 100
        else:
            blocks = math.ceil(rounded_over / 100)
        rate = RATES[tier]
        if tier == "P" and region in ("BR", "IN"):
            rate = 5
        charge = blocks * rate
        if used == 0 and over == 0:
            self.burst_used[canonical] = calls // 10
        self.used[canonical] = used + calls

        left = max(0, limit - self.used[canonical] + self.burst_used[canonical])
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
