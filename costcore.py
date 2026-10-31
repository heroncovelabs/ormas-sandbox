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
        # FIFO layers keyed by the spelling registered by the first movement.
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

    def _onhand(self, sku: str) -> int:
        return sum(qty for qty, _cost in self.layers.get(sku, []))

    def handle(self, line: str) -> None:
        # The legacy reader terminates a record at its first CR, LF, or NUL.
        line = re.split(r"[\r\n\x00]", line, maxsplit=1)[0]
        if not line:
            return
        # Match the bounded scanf fields, including splitting overlong tokens.
        parts = []
        rest = line
        for width in (7, 63, 63, 63):
            rest = rest.lstrip(" \t\v\f")
            if not rest:
                break
            token = re.split(r"[ \t\v\f]", rest, maxsplit=1)[0][:width]
            parts.append(token)
            rest = rest[len(token):]
        kind = parts[0] if parts else ""
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = 1 <= len(sku) <= 8 and sku.isascii() and sku.isalnum()
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._reject(sku if sku_ok else "????????", "FMT")
            return
        qty_tok = parts[2]
        if not (qty_tok.isascii() and qty_tok.isdigit()
                and 1 <= len(qty_tok) <= 6):
            self._reject(sku, "QTY")
            return
        qty = int(qty_tok)
        # Zero movements disappear before cost validation or SKU registration.
        if qty == 0:
            return
        if qty > MAX_QTY:
            self._reject(sku, "QTY")
            return
        if kind == "R":
            cost_tok = parts[3]
            if not (cost_tok.isascii() and cost_tok.isdigit()
                    and 1 <= len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), MAX_COST)

        # A stock rejection registers a name; validation rejects leave it alone.
        sku = self.names.setdefault(sku.upper(), sku)
        stack = self.layers.setdefault(sku, [])
        if kind == "R":
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {sku} {self._onhand(sku)}")
            self.count_rcpt += 1
            return

        onhand = self._onhand(sku)
        # With multiple layers, the newest layer is display-only for this issue.
        available = onhand - stack[-1][0] if len(stack) > 1 else onhand
        if available == 0 or qty > 2 * available:
            self._reject(sku, "STOCK")
            return
        issued = min(qty, available)
        remaining = issued
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
        # Stock-clearing issues of at least 100 units incur rounded 2% shrinkage.
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
    # Match fgets(buffer, 512): long physical lines become 511-byte records.
    while True:
        line = sys.stdin.buffer.readline(511)
        if not line:
            break
        engine.handle(line.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
