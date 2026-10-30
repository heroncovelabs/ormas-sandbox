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
WHITESPACE = " \t\n\r\v\f"


def _fields(line: str) -> list[str]:
    """Match the legacy scanner's five fixed-width, ASCII-space fields."""
    fields = []
    pos = 0
    for width in (7, 63, 63, 63, 63):
        while pos < len(line) and line[pos] in WHITESPACE:
            pos += 1
        start = pos
        while pos < len(line) and pos - start < width and line[pos] not in WHITESPACE:
            pos += 1
        if start == pos:
            break
        fields.append(line[start:pos])
    return fields


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
        # The C input path terminates a record at its first NUL, CR, or LF.
        line = line.split("\x00", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            return
        parts = _fields(line)
        key = parts[1] if len(parts) > 1 else ""
        key_ok = 1 <= len(key) <= 8 and key.isascii() and key.isalnum()
        if len(parts) != 5 or parts[0] != "Q" or not key_ok:
            self._reject(key if key_ok else "????????", "FMT")
            return
        _, key, calls_tok, tier, region = parts
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
        # Heartbeats validate their fields, then leave all per-key state alone.
        if calls == 0:
            return

        identity = key.lower()
        first = identity not in self.tier
        if first:
            self.tier[identity] = tier
            self.used[identity] = 0
            self.names[identity] = key
        else:
            previous = self.tier[identity]
            if tier != previous and (previous, tier) not in (("F", "S"), ("S", "P")):
                self._reject(self.names[identity], "TIER")
                return
            self.tier[identity] = tier

        limit = QUOTAS[tier]
        used = self.used[identity]
        remaining = max(0, limit - used)
        over = max(0, calls - remaining)
        # A later event that crosses a positive balance bills its entire size.
        if used > 0 and remaining > 0 and over > 0:
            over = calls
        blocks, remainder = divmod(over, 100)
        if remainder and remainder != 50:
            blocks += 1
        rate = 5 if tier == "P" and region.upper() in ("BR", "IN") else RATES[tier]
        charge = blocks * rate

        # Only an included first event banks ten percent of its calls.
        credit = calls // 10 if first and calls <= limit else 0
        self.used[identity] = used + calls - credit
        left = max(0, limit - self.used[identity])
        self._emit(f"B {self.names[identity]} {charge} {left}")
        self.count_ok += 1
        self.sum_charges += charge

    def finish(self) -> None:
        self._emit(f"X {self.count_ok} {self.count_rej} {self.sum_charges}")


def main() -> None:
    engine = Engine()
    # fgets(buffer, 512, stdin) processes at most 511 bytes per record.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
