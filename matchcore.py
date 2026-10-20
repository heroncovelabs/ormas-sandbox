"""MatchCore matching engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
matching session per process: messages on stdin, responses on stdout.
Protocol reference: ``docs/SPEC.md`` (mind the drift warning at the top;
the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import string
import sys

PRICE_MAX = 10_000_000
QTY_MAX = 999_999
PRIORITY_QTY = 1000
TICK_THRESHOLD = 100_000
TICK_SIZE = 5
SWEEP_BAND = 500
HASH_MIN_QTY = 100
HASH_MOD = 1_000_000_007

# Field separators accepted by the engine (ASCII only; NBSP and \x1c are not).
_FIELD_SPLIT = re.compile(r"[ \t\v\f\r]+")
_LINE_END = re.compile(r"[\x00\r]")
_ALNUM = frozenset(string.ascii_letters + string.digits)
_DIGITS = frozenset(string.digits)


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
        # Ranking key: best price first, then priority class at that price
        # (large orders, by original quantity, ahead of the rest), then
        # arrival sequence (FIFO within a class).
        best: Order | None = None
        best_key: tuple[int, int, int] | None = None
        for order in self.book:
            if not order.live or order.side == side:
                continue
            if not is_market:
                if side == "B" and order.price > limit:
                    continue
                if side == "S" and order.price < limit:
                    continue
            price_rank = order.price if side == "B" else -order.price
            key = (price_rank, _priority_class(order), order.seq)
            if best_key is None or key < best_key:
                best = order
                best_key = key
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
            if price >= TICK_THRESHOLD and price % TICK_SIZE:
                self._emit(f"R {clordid} TICK")
                return
        # A valid new order reusing the clordid of a live order from the same
        # account replaces it: the old order is cancelled (acknowledged with
        # its submitted quantity) and the new order is processed as fresh
        # arrival, so it loses its place in the queue.
        replaced = self._find_live(acct, clordid)
        if replaced is not None:
            replaced.live = False
            self._emit(f"X {replaced.clordid} {replaced.orig}")

        remaining = qty
        first_fill_price = None
        while remaining:
            counter = self._best_counter(side, price, is_market)
            if counter is None:
                break
            # Cancel the resting self order and continue with the incoming
            # quantity intact. Self cancellations precede the band check and
            # do not establish the sweep's reference price.
            if counter.acct == acct:
                self.cancel(counter.acct, counter.clordid)
                continue
            # Every order type is limited to 500 price units from its first
            # execution; a limit remainder can therefore leave a crossed book.
            if first_fill_price is None:
                first_fill_price = counter.price
            elif abs(counter.price - first_fill_price) > SWEEP_BAND:
                break
            take = min(remaining, counter.qty)
            self._emit(f"F {counter.clordid} {clordid} {counter.price} {take}")
            counter.qty -= take
            remaining -= take
            if counter.qty == 0:
                counter.live = False

        if remaining and type_ == "L":
            self.seq += 1
            self.book.append(Order(acct, clordid, side, price, remaining, self.seq))
            self.book[-1].orig = qty
            self._emit(f"A {clordid} {remaining}")
        else:
            self._emit(f"A {clordid} 0")

    def cancel(self, acct: str, clordid: str) -> None:
        order = self._find_live(acct, clordid)
        if order is None:
            self._emit(f"R {clordid} UNKNOWN")
            return
        order.live = False
        # Acknowledge the submitted quantity, not the remaining quantity.
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
            # Odd-lot remainders still set the best price, but contribute
            # to the hash only while at least 100 units remain.
            if order.qty >= HASH_MIN_QTY:
                book_hash = (book_hash + order.price * order.qty) % HASH_MOD
        self._emit(f"S {bid} {ask} {book_hash}")

    # -- line protocol ------------------------------------------------------

    def handle(self, line: str) -> None:
        # The engine truncates each message at the first NUL or CR (the rest
        # of the line is discarded, not treated as a new message).
        line = _LINE_END.split(line, 1)[0].rstrip("\n")
        if not line:
            return
        if line == "E":
            self.end_session()
            return
        # Command letter must be the first character; the remainder is split
        # on ASCII whitespace with no separator required after the letter.
        if line[0] in ("N", "C"):
            parts = [field for field in _FIELD_SPLIT.split(line[1:]) if field]
            if line[0] == "N":
                if len(parts) >= 6:
                    acct, clordid, side, type_, price, qty = parts[:6]
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
            elif len(parts) >= 2:
                acct, clordid = parts[:2]
                if _token(acct, 4, 4) and _token(clordid, 1, 8):
                    self.cancel(acct, clordid)
                    return
            echo = parts[1] if len(parts) > 1 and _token(parts[1], 1, 8) else "????????"
            self._emit(f"R {echo} FMT")
            return
        self._emit("R ???????? FMT")


def _priority_class(order: Order) -> int:
    # Orders placed with original quantity at or above PRIORITY_QTY rank ahead
    # of smaller orders at the same price. Class follows the original size,
    # so it survives partial fills.
    return 0 if order.orig >= PRIORITY_QTY else 1


def _token(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and all(ch in _ALNUM for ch in value)


def _digits(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and all(ch in _DIGITS for ch in value)


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)


if __name__ == "__main__":
    main()
