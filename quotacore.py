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
TIERS = "FSP"
MAX_KEYS = 4096
WHITESPACE = " \t\r\n\v\f"


def _fields(line: str) -> list[str]:
    """Reproduce the reference's bounded, ASCII-whitespace token scans."""
    parts = []
    pos = 0
    for width in (7, 63, 63, 63, 63):
        while pos < len(line) and line[pos] in WHITESPACE:
            pos += 1
        start = pos
        while (pos < len(line) and pos - start < width
               and line[pos] not in WHITESPACE):
            pos += 1
        if start == pos:
            break
        parts.append(line[start:pos])
    return parts


class Engine:
    def __init__(self, out=None):
        self.tier: dict[str, str] = {}
        self.used: dict[str, int] = {}
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
        line = line.partition("\0")[0].partition("\r")[0].partition("\n")[0]
        if not line:
            return
        parts = _fields(line)
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and key.isascii() and key.isalnum()
        if len(parts) < 5 or parts[0] != "Q" or not key_ok:
            self._reject(key if key_ok else "????????", "FMT")
            return
        _, key, calls_tok, tier, region = parts
        if not (calls_tok.isascii() and calls_tok.isdigit()
                and 1 <= len(calls_tok) <= 7):
            self._reject(key, "CALLS")
            return
        calls = int(calls_tok)
        if tier not in QUOTAS:
            self._reject(key, "TIER")
            return
        if not (len(region) == 2 and region.isascii() and region.isalpha()):
            self._reject(key, "REGION")
            return
        # Heartbeats validate their fields, then leave all key state untouched.
        if calls == 0:
            return

        identity = key.upper()
        first = identity not in self.tier
        if first:
            if len(self.tier) >= MAX_KEYS:
                self._reject(key, "FMT")
                return
            self.names[identity] = key
            self.tier[identity] = tier
            self.used[identity] = 0
        else:
            key = self.names[identity]
            step = TIERS.index(tier) - TIERS.index(self.tier[identity])
            if step not in (0, 1):
                self._reject(key, "TIER")
                return
            self.tier[identity] = tier

        limit = QUOTAS[tier]
        used = self.used[identity]
        if first and calls <= limit:
            # Carry the first event's burst bank across subsequent upgrades.
            used -= calls // 10
        within = max(0, min(calls, limit - used))
        over = calls - within
        if 0 < used < limit and used + calls > limit:
            over = calls
        blocks = (over + 99) // 100
        if over % 100 == 50:
            blocks -= 1
        rate = 5 if tier == "P" and region.upper() in ("BR", "IN") else RATES[tier]
        charge = blocks * rate
        self.used[identity] = used + calls

        left = max(0, limit - self.used[identity])
        self._emit(f"B {key} {charge} {left}")
        self.count_ok += 1
        self.sum_charges += charge

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_charges}")


def main() -> None:
    engine = Engine()
    # The reference uses fgets with a 512-byte buffer. Decode one byte per
    # character so scan widths and ASCII validation also match on UTF-8 input.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("latin1"))
    engine.finish()


if __name__ == "__main__":
    main()
