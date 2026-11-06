"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

MAX_QTY = 999_999
MAX_COST = 9_000_000


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers: sku -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        # Registration happens after numeric validation, even for stockouts.
        # The first registered spelling is retained for inventory responses.
        self.names: dict[str, str] = {}
        self.count_rcpt = 0
        self.count_iss = 0
        self.count_rej = 0
        self.sum_cogs = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, sku: str, code: str) -> None:
        self._emit(f"E {sku} {code}")
        self.count_rej += 1

    def _onhand(self, sku: str) -> int:
        return sum(qty for qty, _cost in self.layers.get(sku, []))

    def handle(self, line: str | bytes) -> None:
        # Parsing is byte-oriented, including the scanner's field widths.
        if isinstance(line, str):
            line = line.encode("utf-8", errors="surrogateescape")
        line = line.decode("latin-1")
        # The legacy line reader terminates at CR, LF, or NUL. Only a
        # genuinely empty line is skipped; whitespace-only lines reject.
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        # Match the four width-limited scanf fields. Extra tokens are ignored;
        # an overlong token continues into the next field without a separator.
        parts = []
        for width in (7, 63, 63, 63):
            line = line.lstrip(" \t\v\f")
            token = re.match(r"[^ \t\v\f]+", line)
            if token is None:
                break
            value = token[0][:width]
            parts.append(value)
            line = line[len(value):]
        kind = parts[0] if parts else ""
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = 1 <= len(sku) <= 8 and sku.isascii() and sku.isalnum()
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._emit(f"E {sku if sku_ok else '????????'} FMT")
            self.count_rej += 1
            return
        qty_tok = parts[2]
        if not (qty_tok.isascii() and qty_tok.isdigit() and 1 <= len(qty_tok) <= 6):
            self._reject(sku, "QTY")
            return
        qty = int(qty_tok)
        if qty == 0:
            return
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isascii() and cost_tok.isdigit() and 1 <= len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), MAX_COST)
        sku = self.names.setdefault(sku.lower(), sku)
        stack = self.layers.setdefault(sku, [])
        if kind == "R":
            # Adjacent equal prices coalesce after applying the cost cap.
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {sku} {self._onhand(sku)}")
            self.count_rcpt += 1
            return
        # With multiple layers, the newest is display stock: it is included
        # in on-hand output but remains reserved throughout this issue.
        onhand = self._onhand(sku)
        issuable = onhand - stack[-1][0] if len(stack) > 1 else onhand
        if issuable == 0 or qty > 2 * issuable:
            self._reject(sku, "STOCK")
            return
        remaining = min(qty, issuable)
        issued = remaining
        cogs = 0
        while remaining > 0:
            layer = stack[0]
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                stack.pop(0)
        onhand -= issued
        # A bin-clearing shipment of at least 100 units carries 2% shrinkage,
        # rounded to the nearest cent with halves rounded upward.
        if onhand == 0 and issued >= 100:
            cogs = (cogs * 102 + 50) // 100
        self._emit(f"C {sku} {cogs} {onhand}")
        self.count_iss += 1
        self.sum_cogs += cogs

    def finish(self) -> None:
        self._emit(
            f"X {self.count_rcpt} {self.count_iss} {self.count_rej} {self.sum_cogs}"
        )


def main() -> None:
    engine = Engine()
    # Match fgets' 512-byte buffer, including its terminating NUL slot.
    # Embedded CR terminates a record without becoming a second movement.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
