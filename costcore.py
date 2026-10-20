"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

MAX_QTY = 999_999
MAX_COST = 9_000_000


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers, keyed by case-folded SKU:
        # key -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        # Display spelling of each SKU: first-seen spelling wins.
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

    def _onhand(self, key: str) -> int:
        return sum(qty for qty, _cost in self.layers.get(key, []))

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = 1 <= len(sku) <= 8 and sku.isalnum()
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._emit(f"E {sku if sku_ok else '????????'} FMT")
            self.count_rej += 1
            return
        key = sku.upper()
        qty_tok = parts[2]
        if qty_tok.isdigit() and len(qty_tok) <= 6 and int(qty_tok) == 0:
            # Zero quantity is silently ignored and not counted.
            return
        if key not in self.display:
            self.display[key] = sku
        name = self.display[key]
        if not (qty_tok.isdigit() and 1 <= len(qty_tok) <= 6):
            self._reject(name, "QTY")
            return
        qty = int(qty_tok)
        if not 1 <= qty <= MAX_QTY:
            self._reject(name, "QTY")
            return
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isdigit() and 1 <= len(cost_tok) <= 7):
                self._reject(name, "COST")
                return
            cost = min(int(cost_tok), MAX_COST)
            # Every receipt opens its own cost layer, newest last.
            stack = self.layers.setdefault(key, [])
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {name} {self._onhand(key)}")
            self.count_rcpt += 1
            return
        # Issue: FIFO, oldest layers consumed first.
        stack = self.layers.get(key, [])
        # Plan the draw first: the head layer is always drawn on, and a
        # deeper layer is only drawn whole when it holds fewer units than
        # the issue still needs.
        plan: list[int] = []
        remaining = qty
        # The newest layer is only drawn on when it is the sole layer.
        drawable = stack[:-1] if len(stack) > 1 else stack
        for layer in drawable:
            if remaining == 0:
                break
            got = min(layer[0], remaining)
            plan.append(got)
            remaining -= got
        plan += [0] * (len(stack) - len(plan))
        take = qty - remaining
        if 2 * take < qty:
            self._reject(name, "STOCK")
            return
        cogs = 0
        for layer, got in zip(stack, plan):
            cogs += got * layer[1]
            layer[0] -= got
        self.layers[key] = [layer for layer in stack if layer[0] > 0]
        onhand = self._onhand(key)
        if onhand == 0 and take >= 100:
            # Clearing a bin with a large issue carries a 2% surcharge.
            cogs = (cogs * 102 + 50) // 100
        self._emit(f"C {name} {cogs} {onhand}")
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
