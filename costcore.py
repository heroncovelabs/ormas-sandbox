"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

MAX_QTY = 999_999
MAX_COST = 9_999_999


def _scan_fields(line: str) -> list[str]:
    """Match the legacy sscanf("%7s %63s %63s %63s") conversion."""
    fields = []
    pos = 0
    for width in (7, 63, 63, 63):
        while pos < len(line) and line[pos] in " \t\n\v\f\r":
            pos += 1
        start = pos
        while pos < len(line) and line[pos] not in " \t\n\v\f\r" and pos - start < width:
            pos += 1
        if pos == start:
            break
        fields.append(line[start:pos])
    return fields


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers: sku -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        self.display_names: dict[str, str] = {}
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
        if not line.strip("\r\n"):
            return
        parts = _scan_fields(line)
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = 1 <= len(sku) <= 8 and all(c.isascii() and c.isalnum() for c in sku)
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
        key = sku.upper()
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isascii() and cost_tok.isdigit() and 1 <= len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            display = self.display_names.get(key)
            if display is None:
                display = self.display_names.setdefault(key, sku)
            cost = min(int(cost_tok), 9_000_000)
            stack = self.layers.setdefault(key, [])
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {display} {self._onhand(key)}")
            self.count_rcpt += 1
            return
        display = self.display_names.get(key)
        if display is None:
            display = self.display_names.setdefault(key, sku)
        stack = self.layers.get(key, [])
        available = self._onhand(key)
        if len(stack) > 1:
            available -= stack[-1][0]
        remaining = qty if qty <= available else available
        if qty > available and qty > 2 * available:
            self._reject(display, "STOCK")
            return
        cogs = 0
        while remaining > 0:
            layer = stack[0]
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                stack.pop(0)
        onhand = self._onhand(key)
        if onhand == 0 and available > 99:
            cogs += (2 * cogs + 50) // 100
        self._emit(f"C {display} {cogs} {onhand}")
        self.count_iss += 1
        self.sum_cogs += cogs

    def finish(self) -> None:
        self._emit(
            f"X {self.count_rcpt} {self.count_iss} {self.count_rej} {self.sum_cogs}"
        )


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
