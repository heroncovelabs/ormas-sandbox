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
_WHITESPACE = b" \t\n\r\v\f"


def _tokens(data: bytes) -> list[bytes]:
    """Match the legacy scanner's four width-limited ASCII string fields."""
    parts = []
    pos = 0
    for width in (7, 63, 63, 63):
        while pos < len(data) and data[pos] in _WHITESPACE:
            pos += 1
        start = pos
        while pos < min(start + width, len(data)) and data[pos] not in _WHITESPACE:
            pos += 1
        if pos == start:
            break
        parts.append(data[start:pos])
    return parts


class Engine:
    def __init__(self, out=None):
        # Per-SKU FIFO cost layers, keyed by the first registered spelling.
        self.layers: dict[str, list[list[int]]] = {}
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
        # C strings end at NUL; the legacy reader also discards everything
        # from the first CR or LF in each input record.
        data = line.encode("utf-8", errors="surrogateescape")
        for terminator in (b"\0", b"\r", b"\n"):
            data = data.split(terminator, 1)[0]
        if not data:
            return
        parts = _tokens(data)
        kind = parts[0] if parts else b""
        sku_tok = parts[1] if len(parts) > 1 else b""
        sku_ok = 1 <= len(sku_tok) <= 8 and sku_tok.isalnum()
        sku = sku_tok.decode("ascii") if sku_ok else "????????"
        need = 4 if kind == b"R" else 3 if kind == b"I" else 0
        if need == 0 or not sku_ok or len(parts) < need:
            self._reject(sku, "FMT")
            return
        qty_tok = parts[2]
        if not (qty_tok.isdigit() and 1 <= len(qty_tok) <= 6):
            self._reject(sku, "QTY")
            return
        qty = int(qty_tok)
        if qty > MAX_QTY:
            self._reject(sku, "QTY")
            return
        # Zero movements disappear before cost validation or SKU registration.
        if qty == 0:
            return
        if kind == b"R":
            cost_tok = parts[3]
            if not (cost_tok.isdigit() and 1 <= len(cost_tok) <= 7):
                self._reject(sku, "COST")
                return
            cost = min(int(cost_tok), MAX_COST)
            sku = self.skus.setdefault(sku.upper(), sku)
            stack = self.layers.setdefault(sku, [])
            # Only adjacent layers merge, using the effective (capped) cost.
            if stack and stack[-1][1] == cost:
                stack[-1][0] += qty
            else:
                stack.append([qty, cost])
            self._emit(f"A {sku} {self._onhand(sku)}")
            self.count_rcpt += 1
            return

        # Even a stock-rejected issue registers its SKU spelling.
        sku = self.skus.setdefault(sku.upper(), sku)
        stack = self.layers.get(sku, [])
        onhand = self._onhand(sku)
        # With multiple layers the newest layer is held out of display stock.
        available = onhand - stack[-1][0] if len(stack) > 1 else onhand
        if qty > 2 * available:
            self._reject(sku, "STOCK")
            return
        filled = min(qty, available)
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
        onhand -= filled
        # Clearing at least 100 units attracts 2% shrinkage, rounded half up.
        if onhand == 0 and filled >= 100:
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
    # Match fgets' 512-byte buffer, including its splitting of long lines.
    for record in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(record.decode("utf-8", errors="surrogateescape"))
    engine.finish()


if __name__ == "__main__":
    main()
