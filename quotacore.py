"""QuotaCore metering engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: usage events on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behaviors that differ from the spec:

- Keys are matched case-insensitively; output uses the first-seen spelling.
- Region codes are accepted in any case. Premium overage in BR and IN is
  priced at 5 cents per block.
- Overage blocks round up, except an overage ending in exactly 50 calls
  rounds down.
- An event that crosses into overage on a key's later event is billed on
  all its calls; only a key's first event is billed on its overage portion.
- A key's first event, if within quota, banks calls // 10 extra included
  calls for the key.
- The next tier up (F to S, S to P) upgrades the key; any other tier
  change is rejected ``TIER``.
- Zero-call events produce no output and are not counted.
- Fields after the region are ignored.
"""

from __future__ import annotations

import sys

QUOTAS = {"F": 10_000, "S": 100_000, "P": 1_000_000}
RATES = {"F": 12, "S": 9, "P": 6}
RANK = {"F": 0, "S": 1, "P": 2}
REGION_RATES = {("P", "BR"): 5, ("P", "IN"): 5}


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
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and key.isascii() and key.isalnum()
        if parts[0] != "Q" or len(parts) < 5 or not key_ok:
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
        if calls == 0:
            return

        ukey = key.upper()
        first = ukey not in self.tier
        if first:
            self.name[ukey] = key
            self.tier[ukey] = tier
            self.used[ukey] = 0
        elif RANK[tier] - RANK[self.tier[ukey]] not in (0, 1):
            self._reject(self.name[ukey], "TIER")
            return
        else:
            self.tier[ukey] = tier
        key = self.name[ukey]

        if first:
            self.bank[ukey] = calls // 10 if calls <= QUOTAS[tier] else 0
        limit = QUOTAS[tier] + self.bank[ukey]
        used = self.used[ukey]
        if first or used >= limit:
            over = max(0, used + calls - max(used, limit))
        elif used + calls > limit:
            over = calls
        else:
            over = 0
        rate = REGION_RATES.get((tier, region), RATES[tier])
        blocks = -(-over // 100)
        if over % 100 == 50:
            blocks -= 1
        charge = blocks * rate
        self.used[ukey] = used + calls

        left = max(0, limit - self.used[ukey])
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
