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
MAX_COST = 9_999_999
EFFECTIVE_COST_CEILING = 9_000_000

# Match the legacy scanner's fixed-width fields and ASCII whitespace.
_FIELD_SCANNERS = tuple(
    re.compile(rf"\s*(\S{{1,{width}}})", re.ASCII) for width in (7, 63, 63, 63)
)


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers: sku -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        # Keep the first spelling used by a valid, nonzero movement.
        self._sku_names: dict[str, str] = {}
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

    def _consume_fifo(self, stack: list[list[int]], qty: int) -> int:
        remaining = qty
        cogs = 0
        while remaining > 0:
            layer = stack[0]
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                stack.pop(0)
        return cogs

    def handle(self, line: str) -> None:
        # CR, LF, and NUL end the record; only an empty record is ignored.
        line = re.split(r"[\x00\r\n]", line, maxsplit=1)[0]
        if not line:
            return
        parts = []
        offset = 0
        for scanner in _FIELD_SCANNERS:
            match = scanner.match(line, offset)
            if match is None:
                break
            parts.append(match[1])
            offset = match.end()
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
        if qty > MAX_QTY:
            self._reject(sku, "QTY")
            return
        if qty == 0:
            return
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isascii() and cost_tok.isdigit() and 1 <= len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            cost = int(cost_tok)
            if cost > MAX_COST:
                self._reject(sku, "COST")
                return
            cost = min(cost, EFFECTIVE_COST_CEILING)

        # Invalid movements retain their supplied spelling in errors; valid
        # issues establish an identity even when they are rejected for stock.
        sku = self._sku_names.setdefault(sku.casefold(), sku)
        if kind == "R":
            stack = self.layers.setdefault(sku, [])
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {sku} {self._onhand(sku)}")
            self.count_rcpt += 1
            return
        stack = self.layers.get(sku, [])
        onhand = self._onhand(sku)
        # With multiple layers, reserve the newest layer for the whole issue.
        # The shortage limit is twice the remaining issuable stock.
        available = onhand - stack[-1][0] if len(stack) > 1 else onhand
        if available == 0 or qty > 2 * available:
            self._reject(sku, "STOCK")
            return
        fulfilled = min(qty, available)
        cogs = self._consume_fifo(stack, fulfilled)
        onhand -= fulfilled
        if onhand == 0 and fulfilled >= 100:
            # The depletion surcharge is rounded half up to whole cents.
            cogs = (102 * cogs + 50) // 100
        self._emit(f"C {sku} {cogs} {onhand}")
        self.count_iss += 1
        self.sum_cogs += cogs

    def finish(self) -> None:
        self._emit(
            f"X {self.count_rcpt} {self.count_iss} {self.count_rej} {self.sum_cogs}"
        )


def main() -> None:
    engine = Engine()
    # The legacy reader uses a 512-byte buffer, including its terminating NUL.
    # Binary reads preserve CR and non-ASCII input for identical validation.
    while line := sys.stdin.buffer.readline(511):
        engine.handle(line.decode("ascii", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
