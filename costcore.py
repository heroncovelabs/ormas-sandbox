"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

MAX_QTY = 999_999
LAYER_COST_CAP = 9_000_000


class Engine:
    def __init__(self, out=None):
        # Keys are case-folded; the first spelling seen is retained for output.
        self.layers: dict[str, list[list[int]]] = {}
        self.display: dict[str, str] = {}
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
        line = line.rstrip("\r\n")
        if not line:
            return
        # Reproduce "%7s %63s %63s %63s": reaching a field's width leaves
        # the remainder of that token to be scanned as the next field.
        parts: list[str] = []
        position = 0
        for width in (7, 63, 63, 63):
            while position < len(line) and line[position].isspace():
                position += 1
            start = position
            while (
                position < len(line)
                and not line[position].isspace()
                and position - start < width
            ):
                position += 1
            if position == start:
                break
            parts.append(line[start:position])
        if not parts:
            parts = [""]
        kind = parts[0]
        raw_sku = parts[1] if len(parts) > 1 else ""
        sku_ok = (
            1 <= len(raw_sku) <= 8
            and raw_sku.isascii()
            and raw_sku.isalnum()
        )
        # Extra tokens are ignored. Only the required leading tokens are
        # needed for the movement to be syntactically valid.
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._emit(f"E {raw_sku if sku_ok else '????????'} FMT")
            self.count_rej += 1
            return
        sku = raw_sku.upper()
        display = raw_sku
        qty_tok = parts[2]
        if not (
            qty_tok.isascii()
            and qty_tok.isdigit()
            and 1 <= len(qty_tok) <= 6
        ):
            self._reject(display, "QTY")
            return
        qty = int(qty_tok)
        if qty > MAX_QTY:
            self._reject(display, "QTY")
            return
        # Zero-quantity movements produce no response and leave all counters
        # and stock untouched, even when later tokens would be invalid.
        if qty == 0:
            return
        if kind == "I":
            display = self.display.setdefault(sku, raw_sku)
        if kind == "R":
            cost_tok = parts[3]
            if not (
                cost_tok.isascii()
                and cost_tok.isdigit()
                and 1 <= len(cost_tok) <= 7
            ):
                self._reject(raw_sku, "COST")
                return
            cost = min(int(cost_tok), LAYER_COST_CAP)
            stack = self.layers.setdefault(sku, [])
            # Consecutive receipts at the same (capped) cost share a layer.
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self.display.setdefault(sku, raw_sku)
            self._emit(f"A {self.display[sku]} {self._onhand(sku)}")
            self.count_rcpt += 1
            return

        # The newest layer is excluded from this traversal. Shortfalls of up
        # to the consumable stock are accepted as partial fills; larger ones
        # reject without consuming anything.
        stack = self.layers.get(sku, [])
        consumable = stack if len(stack) <= 1 else stack[:-1]
        available = sum(layer[0] for layer in consumable)
        if available == 0 or qty > 2 * available:
            self._reject(display, "STOCK")
            return
        remaining = qty
        cogs = 0
        consumed_layers = 0
        for index, layer in enumerate(consumable):
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                consumed_layers = index + 1
            if remaining == 0:
                break
        del stack[:consumed_layers]
        # Emptying a bin whose consumable stock was at least 100 units adds
        # a 2% surcharge, rounded half-up to the nearest cent.
        if available >= 100 and not stack:
            cogs += (2 * cogs + 50) // 100
        self._emit(f"C {display} {cogs} {self._onhand(sku)}")
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
