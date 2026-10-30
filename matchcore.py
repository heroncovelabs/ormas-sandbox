"""MatchCore matching engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
matching session per process: messages on stdin, responses on stdout.
Protocol reference: ``docs/SPEC.md`` (mind the drift warning at the top;
the engine's behavior is the contract).

Engine behaviors that differ from (or are missing in) the spec:

- Priority class: at equal price, resting orders whose original quantity
  is >= 1000 (block orders) match before smaller orders; time priority
  applies within a class.
- Self-trade prevention cancels the resting order of the same account
  (``X``) and matching continues; there is no ``STP`` reject.
- A new order reusing the client order id of a live order from the same
  account replaces it (``X`` for the old one, then the new order is
  processed); there is no ``DUP`` reject. Rejected orders replace nothing.
- ``X`` reports the order's original quantity, not what remained.
- Volatility band: once an order has filled, it stops matching at prices
  more than 500 away from its first fill price.
- Tick regime: limit/IOC prices >= 100000 must be multiples of 5 (``TICK``).
- Book hash only counts resting orders with remaining quantity >= 100.
- Parsing follows the engine's ``sscanf``: extra trailing tokens are
  ignored, side/type are single characters, whitespace is flexible.
"""

from __future__ import annotations

import sys

PRICE_MAX = 10_000_000
QTY_MAX = 999_999
HASH_MOD = 1_000_000_007
BLOCK_QTY = 1000
BAND = 500
TICK_FROM = 100_000
TICK = 5
HASH_MIN_QTY = 100
WS = " \t\n\v\f\r"
LINE_MAX = 255


class Order:
    __slots__ = ("acct", "clordid", "side", "price", "qty", "orig", "seq", "live")

    def __init__(self, acct: str, clordid: str, side: str, price: int, qty: int, seq: int):
        self.acct = acct
        self.clordid = clordid
        self.side = side
        self.price = price
        self.qty = qty
        self.orig = qty
        self.seq = seq
        self.live = True


class Engine:
    def __init__(self, out=None):
        self.book: list[Order] = []
        self.seq = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _find_live(self, acct: str, clordid: str) -> Order | None:
        for order in self.book:
            if order.live and order.acct == acct and order.clordid == clordid:
                return order
        return None

    def _best_counter(self, side: str, limit: int, is_market: bool) -> Order | None:
        best: Order | None = None
        for order in self.book:
            if not order.live or order.side == side:
                continue
            if not is_market:
                if side == "B" and order.price > limit:
                    continue
                if side == "S" and order.price < limit:
                    continue
            if best is None:
                better = True
            elif order.price != best.price:
                better = order.price < best.price if side == "B" else order.price > best.price
            else:
                big, best_big = order.orig >= BLOCK_QTY, best.orig >= BLOCK_QTY
                better = big if big != best_big else order.seq < best.seq
            if better:
                best = order
        return best

    # -- message handlers ---------------------------------------------------

    def new_order(self, acct: str, clordid: str, side: str, type_: str, price: int, qty: int):
        if not 0 < qty <= QTY_MAX:
            self._emit(f"R {clordid} QTY")
            return
        is_market = type_ == "M"
        if not is_market:
            if not 0 < price < PRICE_MAX:
                self._emit(f"R {clordid} PRICE")
                return
            if price >= TICK_FROM and price % TICK:
                self._emit(f"R {clordid} TICK")
                return
        old = self._find_live(acct, clordid)
        if old is not None:
            old.live = False
            self._emit(f"X {old.clordid} {old.orig}")

        remaining = qty
        first_fill = None
        while remaining:
            counter = self._best_counter(side, price, is_market)
            if counter is None:
                break
            if counter.acct == acct:
                counter.live = False
                self._emit(f"X {counter.clordid} {counter.orig}")
                continue
            if first_fill is None:
                first_fill = counter.price
            elif abs(counter.price - first_fill) > BAND:
                break
            take = min(remaining, counter.qty)
            self._emit(f"F {counter.clordid} {clordid} {counter.price} {take}")
            counter.qty -= take
            remaining -= take
            if counter.qty == 0:
                counter.live = False

        if remaining and type_ == "L":
            self.seq += 1
            order = Order(acct, clordid, side, price, remaining, self.seq)
            order.orig = qty
            self.book.append(order)
            self._emit(f"A {clordid} {remaining}")
        else:
            self._emit(f"A {clordid} 0")

    def cancel(self, acct: str, clordid: str) -> None:
        order = self._find_live(acct, clordid)
        if order is None:
            self._emit(f"R {clordid} UNKNOWN")
            return
        order.live = False
        self._emit(f"X {order.clordid} {order.orig}")

    def end_session(self) -> None:
        bid = ask = 0
        book_hash = 0
        for order in self.book:
            if not order.live:
                continue
            if order.side == "B":
                bid = max(bid, order.price)
            elif ask == 0 or order.price < ask:
                ask = order.price
            if order.qty >= HASH_MIN_QTY:
                book_hash = (book_hash + order.price * order.qty) % HASH_MOD
        self._emit(f"S {bid} {ask} {book_hash}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        # The engine cuts each line at its first CR or LF (or NUL).
        line = line.split("\n", 1)[0].split("\r", 1)[0].split("\0", 1)[0]
        if not line:
            return
        if line == "E":
            self.end_session()
            return
        if line[0] == "N":
            fields = _scan(line[1:], "ssccss")
            if len(fields) == 6:
                acct, clordid, side, type_, price, qty = fields
                if (
                    _token(acct, 4, 4)
                    and _token(clordid, 1, 8)
                    and side in ("B", "S")
                    and type_ in ("L", "M", "I")
                    and _digits(price, 1, 7)
                    and _digits(qty, 1, 6)
                ):
                    self.new_order(acct, clordid, side, type_, int(price), int(qty))
                    return
            clordid = fields[1] if len(fields) > 1 else ""
            self._emit(f"R {clordid if _token(clordid, 1, 8) else '????????'} FMT")
            return
        if line[0] == "C":
            fields = _scan(line[1:], "ss")
            if len(fields) == 2:
                acct, clordid = fields
                if _token(acct, 4, 4) and _token(clordid, 1, 8):
                    self.cancel(acct, clordid)
                    return
            clordid = fields[1] if len(fields) > 1 else ""
            self._emit(f"R {clordid if _token(clordid, 1, 8) else '????????'} FMT")
            return
        self._emit("R ???????? FMT")


def _scan(rest: str, spec: str) -> list[str]:
    """Mimic ``sscanf`` with whitespace-separated ``%63s``/``%c``
    conversions per ``spec``; returns the fields converted."""
    fields: list[str] = []
    pos = 0
    for kind in spec:
        while pos < len(rest) and rest[pos] in WS:
            pos += 1
        if pos >= len(rest):
            break
        if kind == "c":
            fields.append(rest[pos])
            pos += 1
        else:
            end = pos
            while end < len(rest) and end - pos < 63 and rest[end] not in WS:
                end += 1
            fields.append(rest[pos:end])
            pos = end
    return fields


def _token(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isascii() and value.isalnum()


def _digits(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isascii() and value.isdigit()


def _engine_lines(data: str):
    """Split input the way the engine's ``fgets`` into a 256-byte buffer
    does: a line longer than 255 bytes is read as several lines."""
    pos = 0
    while pos < len(data):
        end = data.find("\n", pos, pos + LINE_MAX)
        end = end + 1 if end != -1 else min(pos + LINE_MAX, len(data))
        yield data[pos:end]
        pos = end


def main() -> None:
    engine = Engine()
    for line in _engine_lines(sys.stdin.buffer.read().decode("latin-1")):
        engine.handle(line)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
