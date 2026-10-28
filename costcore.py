"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behavior that differs from the written spec:

- SKUs are case-insensitive; a SKU is displayed with the spelling it had
  when it first passed validation.
- A quantity of 0 (after FMT/QTY checks) is silently dropped: no output,
  not counted.
- Extra tokens after the required fields are ignored.
- Unit costs above 9,000,000 are capped at 9,000,000.
- A receipt at the same unit cost as the SKU's newest layer merges into it.
- Issues consume FIFO but never touch the newest layer while older layers
  remain. An issue is accepted (and partially filled) if at least half of
  it can be filled that way.
- An issue of 100+ units that empties the SKU is surcharged 2% shrinkage
  (rounded half up).
"""

from __future__ import annotations

import re
import sys

MAX_QTY = 999_999
COST_CAP = 9_000_000

_SKU = re.compile(r"[A-Za-z0-9]{1,8}")
_QTY = re.compile(r"[0-9]{1,6}")
_COST = re.compile(r"[0-9]{1,7}")


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers: key -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        # Case-folded key -> display spelling.
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
        line = line.rstrip("\r\n")
        if not line:
            return
        # A whitespace-only line is a FMT reject, not a skipped line.
        parts = line.split()
        kind = parts[0] if parts else ""
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = _SKU.fullmatch(sku) is not None
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._reject(sku if sku_ok else "????????", "FMT")
            return
        qty_tok = parts[2]
        if not _QTY.fullmatch(qty_tok):
            self._reject(sku, "QTY")
            return
        qty = int(qty_tok)
        if qty == 0:
            return
        if kind == "R":
            cost_tok = parts[3]
            if not _COST.fullmatch(cost_tok):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), COST_CAP)
        key = sku.upper()
        name = self.names.setdefault(key, sku)
        stack = self.layers.setdefault(key, [])
        if kind == "R":
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {name} {self._onhand(key)}")
            self.count_rcpt += 1
            return
        # Issue: FIFO, but the newest layer is held back unless it is the
        # only one left.
        usable = stack if len(stack) <= 1 else stack[:-1]
        filled = min(qty, sum(lqty for lqty, _cost in usable))
        if 2 * filled < qty:
            self._reject(name, "STOCK")
            return
        remaining = filled
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
        if onhand == 0 and filled >= 100:
            cogs += (cogs * 2 + 50) // 100
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
