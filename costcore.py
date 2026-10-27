"""CostCore inventory cost-layer engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One batch
per process: movement lines on stdin, result lines on stdout, trailer at
end of input. Format reference: ``docs/SPEC.md`` (mind the drift warning;
the engine's behavior is the contract).

Engine behavior that differs from (or is missing in) the spec:

- SKUs are case-insensitive; output shows the spelling first seen on an
  accepted receipt or on an issue that reached the stock check.
- Extra trailing tokens are ignored; only missing tokens are ``FMT``.
- A well-formed zero quantity line (1-6 digits, value 0) is dropped
  silently: no output, not counted.
- A whitespace-only line is ``FMT`` (``????????``); a truly empty line is
  skipped.
- Unit costs above 9,000,000 are capped at 9,000,000.
- A receipt at the same (capped) unit cost as the SKU's newest layer
  merges into that layer.
- Issues only draw from the layers before the newest one (or from the
  sole layer when there is just one). An issue for more than twice that
  available quantity is ``STOCK``; otherwise it fills up to what is
  available.
- An issue that empties the SKU after filling 100+ units is surcharged
  2% (rounded half up).
"""

from __future__ import annotations

import re
import sys

_CUT = re.compile("[\r\0]")
_SEP = re.compile("[ \t\v\f]+")

MAX_QTY = 999_999
COST_CAP = 9_000_000
CLEAR_MIN_QTY = 100

_ALNUM = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
_DIGITS = set("0123456789")


def _is_digits(tok: str, max_len: int) -> bool:
    return 1 <= len(tok) <= max_len and set(tok) <= _DIGITS


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers: key -> list of [qty, unit_cost].
        self.layers: dict[str, list[list[int]]] = {}
        # Display spelling per case-folded SKU key.
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

    def _name(self, key: str, sku: str) -> str:
        return self.names.setdefault(key, sku)

    def handle(self, line: str) -> None:
        # The engine reads each line only up to the first CR or NUL.
        line = _CUT.split(line.rstrip("\n"), 1)[0]
        if not line:
            return
        parts = [p for p in _SEP.split(line) if p]
        kind = parts[0] if parts else ""
        sku = parts[1] if len(parts) > 1 else ""
        sku_ok = 1 <= len(sku) <= 8 and set(sku) <= _ALNUM
        need = 4 if kind == "R" else 3 if kind == "I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._reject(sku if sku_ok else "????????", "FMT")
            return
        qty_tok = parts[2]
        if not _is_digits(qty_tok, 6):
            self._reject(sku, "QTY")
            return
        qty = int(qty_tok)
        if qty == 0:
            return
        key = sku.upper()
        if kind == "R":
            cost_tok = parts[3]
            if not _is_digits(cost_tok, 7):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), COST_CAP)
            name = self._name(key, sku)
            stack = self.layers.setdefault(key, [])
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {name} {self._onhand(key)}")
            self.count_rcpt += 1
            return
        # Issue: FIFO over every layer but the newest (unless it is the only one).
        name = self._name(key, sku)
        stack = self.layers.get(key, [])
        usable = stack[:-1] if len(stack) > 1 else stack
        avail = sum(layer[0] for layer in usable)
        if avail == 0 or qty > 2 * avail:
            self._reject(name, "STOCK")
            return
        filled = min(qty, avail)
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
        if onhand == 0 and filled >= CLEAR_MIN_QTY:
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
    for raw in sys.stdin.buffer.read().split(b"\n"):
        engine.handle(raw.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
