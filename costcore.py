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
        # First valid, nonzero movement establishes the spelling, even if
        # an issue subsequently fails its stock check.
        self.skus: dict[str, str] = {}
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

    def handle(self, line: str) -> None:
        # Records end at the first NUL, CR, or LF, with ASCII token spacing.
        record = re.split(r"[\0\r\n]", line, maxsplit=1)[0]
        parts = re.findall(r"[^ \t\v\f]+", record)
        if not parts:
            return
        kind = parts[0]
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
        if not 0 <= qty <= MAX_QTY:
            self._reject(sku, "QTY")
            return
        # Zero movements disappear before cost validation and SKU lookup.
        if qty == 0:
            return
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isascii() and cost_tok.isdigit() and 1 <= len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), MAX_COST)
            sku = self.skus.setdefault(sku.upper(), sku)
            stack = self.layers.setdefault(sku, [])
            # Adjacent equal-priced receipts share a layer after capping.
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {sku} {self._onhand(sku)}")
            self.count_rcpt += 1
            return
        sku = self.skus.setdefault(sku.upper(), sku)
        stack = self.layers.get(sku, [])
        onhand = self._onhand(sku)
        # The newest of multiple layers is reserved as display stock.
        available = onhand - stack[-1][0] if len(stack) > 1 else onhand
        if qty > 2 * available:
            self._reject(sku, "STOCK")
            return
        # Accept a partial shipment through twice the available quantity.
        remaining = min(qty, available)
        cogs = 0
        while remaining > 0:
            layer = stack[0]
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                stack.pop(0)
        after = self._onhand(sku)
        # Emptying a bin of at least 100 units adds 2%, rounded half up.
        if after == 0 and onhand >= 100:
            cogs += (cogs * 2 + 50) // 100
        self._emit(f"C {sku} {cogs} {after}")
        self.count_iss += 1
        self.sum_cogs += cogs

    def finish(self) -> None:
        self._emit(
            f"X {self.count_rcpt} {self.count_iss} {self.count_rej} {self.sum_cogs}"
        )


def main() -> None:
    engine = Engine()
    # Match the legacy 512-byte fgets buffer and preserve embedded CRs.
    while line := sys.stdin.buffer.readline(511):
        engine.handle(line.decode("utf-8", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
