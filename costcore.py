"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

MAX_QTY = 999_999
COST_CAP = 9_000_000


class Engine:
    def __init__(self, out=None):
        # Keys are folded, while the first stock movement fixes display case.
        self.layers: dict[str, list[list[int]]] = {}
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
        raw = line.split("\r", 1)[0].rstrip("\n")
        spaced = raw.replace("\t", " ").replace("\v", " ").replace("\f", " ")
        parts = [token for token in spaced.split(" ") if token]
        if not parts:
            if not raw:
                return
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = 1 <= len(sku) <= 8 and sku.isascii() and sku.isalnum()
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._reject(sku if sku_ok else "????????", "FMT")
            return
        qty_tok = parts[2]
        if not (qty_tok.isascii() and qty_tok.isdigit() and len(qty_tok) <= 6):
            self._reject(sku, "QTY")
            return
        qty = int(qty_tok)
        if qty == 0:
            return
        key = sku.upper()
        display = self.names.get(key, sku)
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isascii() and cost_tok.isdigit() and len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), COST_CAP)
            stack = self.layers.setdefault(key, [])
            self.names.setdefault(key, sku)
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {self.names[key]} {self._onhand(key)}")
            self.count_rcpt += 1
            return
        # The legacy consumer never takes from the newest of several layers.
        # A rejected stock lookup also fixes the SKU's saved display spelling.
        self.names.setdefault(key, sku)
        display = self.names[key]
        stack = self.layers.get(key, [])
        onhand = self._onhand(key)
        available = onhand - (stack[-1][0] if len(stack) > 1 else 0)
        if not stack or qty > 2 * available:
            self._reject(display, "STOCK")
            return
        issued = min(qty, available)
        remaining = issued
        cogs = 0
        while remaining:
            layer = stack[0]
            got = min(layer[0], remaining)
            cogs += got * layer[1]
            layer[0] -= got
            remaining -= got
            if layer[0] == 0:
                stack.pop(0)
        if issued == onhand and onhand >= 100:
            cogs += (cogs + 25) // 50
        self._emit(f"C {display} {cogs} {self._onhand(key)}")
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
