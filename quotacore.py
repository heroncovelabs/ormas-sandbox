"""QuotaCore metering engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: usage events on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

# The engine tokenizes on ASCII whitespace only.
_TOKEN_SPLIT = re.compile(r"[ \t\n\r\f\v]+")

QUOTAS = {"F": 10_000, "S": 100_000, "P": 1_000_000}
RATES = {"F": 12, "S": 9, "P": 6}


class Engine:
    def __init__(self, out=None):
        self.tier: dict[str, str] = {}
        self.used: dict[str, int] = {}
        self.bank: dict[str, int] = {}
        self.names: dict[str, str] = {}
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
        text = line.rstrip("\r\n")
        if not text:
            return
        # A line with only whitespace is a malformed record, not a blank line.
        parts = [tok for tok in _TOKEN_SPLIT.split(text) if tok]
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and key.isascii() and key.isalnum()
        # Extra tokens after the region are ignored, as the engine does.
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
        # Region validation and pricing are case-insensitive.
        if not (len(region) == 2 and region.isascii() and region.isalpha()):
            self._reject(key, "REGION")
            return
        region = region.upper()

        # Zero-call heartbeats are valid no-ops: no output, no counters,
        # no key registration, and no tier check.
        if calls == 0:
            return

        # Key identity is case-insensitive; account results use the spelling
        # from registration. Earlier validation failures echo the input key.
        norm = key.lower()
        if norm not in self.tier:
            self.tier[norm] = tier
            self.used[norm] = 0
            # The first billable event earns a permanent burst bank when
            # it fits entirely within the plan's original included quota.
            self.bank[norm] = calls // 10 if calls <= QUOTAS[tier] else 0
            self.names[norm] = key
        elif tier != self.tier[norm]:
            # Only adjacent upward changes are supported. Usage and the
            # original burst bank carry forward to the larger plan.
            if (self.tier[norm], tier) not in (("F", "S"), ("S", "P")):
                self._reject(self.names[norm], "TIER")
                return
            self.tier[norm] = tier
        name = self.names[norm]

        limit = QUOTAS[tier] + self.bank[norm]
        used = self.used[norm]
        within = max(0, min(calls, limit - used))
        over = calls - within
        if used > 0 and within > 0 and over > 0:
            # An established key's crossing event is charged in full.
            over = calls
        # A remainder of exactly fifty rounds down; all other nonzero
        # remainders start another block.
        blocks, remainder = divmod(over, 100)
        blocks += remainder not in (0, 50)
        rate = 5 if tier == "P" and region in ("BR", "IN") else RATES[tier]
        charge = blocks * rate
        self.used[norm] = used + calls

        left = max(0, limit - self.used[norm])
        self._emit(f"B {name} {charge} {left}")
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
