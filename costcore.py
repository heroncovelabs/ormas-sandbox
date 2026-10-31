"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behavior that differs from the spec:

- SKUs are case-insensitive; a SKU is echoed with the spelling it was
  first registered under (by an accepted receipt or a STOCK reject).
- Extra trailing tokens are ignored; a quantity of 0 is silently dropped
  (no output, not counted) once the quantity token itself is valid.
- Unit costs above ``COST_CAP`` are valued at the cap; a cost of 0 is
  accepted.
- A receipt at the same unit cost as the SKU's newest layer merges into it.
- While a SKU has more than one layer, its newest layer is not available
  to issues. An issue for more than twice the available stock is rejected
  ``STOCK``; otherwise it is filled up to the available stock, FIFO.
- An issue that empties the SKU after consuming ``SHRINK_MIN`` or more
  units is charged a 2% shrinkage surcharge, rounded half up.
"""

from __future__ import annotations

import sys

MAX_QTY = 999_999
MAX_COST = 9_999_999
COST_CAP = 9_000_000
SHRINK_MIN = 100


def _sku_ok(sku: str) -> bool:
    return 1 <= len(sku) <= 8 and sku.isascii() and sku.isalnum()


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers: folded sku -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        # Folded sku -> spelling it is echoed with.
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

    def _onhand(self, key: str) -> int:
        return sum(qty for qty, _cost in self.layers.get(key, []))

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = _sku_ok(sku)
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._reject(sku if sku_ok else "????????", "FMT")
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
            cost = min(int(cost_tok), COST_CAP)
            name = self.names.setdefault(key, sku)
            stack = self.layers.setdefault(key, [])
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {name} {self._onhand(key)}")
            self.count_rcpt += 1
            return
        # Issue: FIFO over the available layers, oldest consumed first.
        name = self.names.setdefault(key, sku)
        stack = self.layers.get(key, [])
        onhand = self._onhand(key)
        avail = onhand - stack[-1][0] if len(stack) > 1 else onhand
        if qty > 2 * avail:
            self._reject(name, "STOCK")
            return
        take = min(qty, avail)
        remaining = take
        cogs = 0
        while remaining > 0:
            layer = stack[0]
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                stack.pop(0)
        left = onhand - take
        if left == 0 and take >= SHRINK_MIN:
            cogs = (cogs * 102 + 50) // 100
        self._emit(f"C {name} {cogs} {left}")
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
