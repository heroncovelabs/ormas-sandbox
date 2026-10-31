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
TIERS = ("F", "S", "P")


class Engine:
    def __init__(self, out=None):
        self.keys: dict[str, str] = {}
        self.tier: dict[str, str] = {}
        self.used: dict[str, int] = {}
        self.bonus: dict[str, int] = {}
        self.count_ok = 0
        self.count_rej = 0
        self.sum_charges = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, key: str, code: str) -> None:
        self._emit(f"R {key} {code}")
        self.count_rej += 1

    def handle(self, line: str | bytes) -> None:
        # The legacy reader and scanner operate on bytes, with bounded fields.
        if isinstance(line, str):
            line = line.encode("utf-8", errors="surrogateescape")
        line = re.split(rb"[\r\n\x00]", line, maxsplit=1)[0].decode("latin1")
        if not line:
            return
        parts = []
        for width in (7, 63, 63, 63, 63):
            field = re.match(rf"\s*(\S{{1,{width}}})", line, flags=re.ASCII)
            if field is None:
                break
            parts.append(field[1])
            line = line[field.end():]
        key = parts[1] if len(parts) > 1 else ""
        key_ok = re.fullmatch(r"[A-Za-z0-9]{1,8}", key) is not None
        if len(parts) < 5 or parts[0] != "Q" or not key_ok:
            self._reject(key if key_ok else "????????", "FMT")
            return
        _, key, calls_tok, tier, region = parts[:5]
        if re.fullmatch(r"[0-9]{1,7}", calls_tok) is None:
            self._reject(key, "CALLS")
            return
        calls = int(calls_tok)
        if tier not in TIERS:
            self._reject(key, "TIER")
            return
        if re.fullmatch(r"[A-Za-z]{2}", region) is None:
            self._reject(key, "REGION")
            return
        # Heartbeats undergo field validation, then leave all state untouched.
        if calls == 0:
            return

        identity = key.upper()
        first = identity not in self.keys
        if first:
            self.keys[identity] = key
            self.tier[key] = tier
            self.used[key] = 0
            # Only a first event wholly within quota earns a 10% burst bank.
            self.bonus[key] = calls // 10 if calls <= QUOTAS[tier] else 0
        else:
            key = self.keys[identity]
            step = TIERS.index(tier) - TIERS.index(self.tier[key])
            if step not in (0, 1):
                self._reject(key, "TIER")
                return
            self.tier[key] = tier

        limit = QUOTAS[tier] + self.bonus[key]
        used = self.used[key]
        remaining = max(0, limit - used)
        over = max(0, calls - remaining)
        # A later event crossing the boundary is charged on its entire size.
        if not first and 0 < remaining < calls:
            over = calls
        blocks, remainder = divmod(over, 100)
        # Exact half-blocks are the legacy exception to started-block rounding.
        if remainder and remainder != 50:
            blocks += 1
        rate = 5 if tier == "P" and region.upper() in ("BR", "IN") else RATES[tier]
        charge = blocks * rate
        self.used[key] = used + calls

        left = max(0, limit - self.used[key])
        self._emit(f"B {key} {charge} {left}")
        self.count_ok += 1
        self.sum_charges += charge

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_charges}")


def main() -> None:
    engine = Engine()
    # Match fgets into the legacy 512-byte buffer, including long-line splits.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
