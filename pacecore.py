"""PaceCore ad-spend pacing engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
pacing commands on stdin (``C`` creates a campaign with a daily budget,
``S`` requests spend for an hour, ``U`` runs the end-of-day true-up),
writes one reply per command and an ``X`` trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import sys

ID_MAX = 8
HOURS = 24
CARRY_CAP_DIV = 5  # carry is capped at 20 percent of the daily budget
NO_CAMP = "????????"


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _digits(token: str) -> bool:
    return token.isascii() and token.isdigit()


class Campaign:
    def __init__(self, daily: int) -> None:
        self.daily = daily
        self.carry = 0
        self.avail = 0
        self.spent = 0
        self.grants = [0] * HOURS
        self.accrued = -1
        self.debt = 0
        self.exhausted = False


class Engine:
    """Pacing engine with live spend, true-up, and batch counters."""

    def __init__(self) -> None:
        self.camps: dict[str, Campaign] = {}
        self.created = 0
        self.requests = 0
        self.trueups = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        tokens = [t for t in line.split(" ") if t][:64]
        if not tokens:
            return ""
        if len(tokens[0]) != 1 or tokens[0] not in "CSU":
            reply = f"N {NO_CAMP} FMT"
        elif tokens[0] == "C":
            reply = self._create(tokens)
        elif tokens[0] == "S":
            reply = self._spend(tokens)
        else:
            reply = self._trueup(tokens)
        if reply.startswith("N "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.created} {self.requests} {self.trueups} {self.rejected}"

    def _find(self, camp: str) -> Campaign | None:
        return self.camps.get(camp.lower())

    def _create(self, tokens: list[str]) -> str:
        camp = tokens[1] if len(tokens) >= 2 else NO_CAMP
        if len(tokens) < 3:
            return f"N {camp} FMT"
        if not _valid_id(tokens[1]):
            return f"N {camp} FMT"
        budget = tokens[2]
        if not _digits(budget) or not 4 <= len(budget) <= 9:
            return f"N {camp} BUDGET"
        if self._find(tokens[1]) is not None:
            return f"N {camp} DUP"
        self.camps[tokens[1].lower()] = Campaign(int(budget))
        self.created += 1
        return f"OK {len(self.camps)}"

    def _accrue(self, c: Campaign, hour: int) -> None:
        if hour > c.accrued:
            slice_ = (c.daily + c.carry) // HOURS
            for h in range(c.accrued + 1, hour + 1):
                v = slice_
                if h == 0:
                    v = max(0, v - c.debt)
                    c.debt = 0
                c.avail += v
            c.exhausted = False
        c.accrued = hour

    def _spend(self, tokens: list[str]) -> str:
        camp = tokens[1] if len(tokens) >= 2 else NO_CAMP
        if len(tokens) < 4:
            return f"N {camp} FMT"
        if not _valid_id(tokens[1]):
            return f"N {camp} FMT"
        hour_tok, req_tok = tokens[2], tokens[3]
        if not _digits(hour_tok) or len(hour_tok) > 2 or int(hour_tok) > 23:
            return f"N {camp} HOUR"
        hour = int(hour_tok)
        if not _digits(req_tok) or len(req_tok) > 7 or int(req_tok) < 1:
            return f"N {camp} REQ"
        req = int(req_tok)
        c = self._find(tokens[1])
        if c is None:
            return f"N {camp} FMT"
        if c.accrued > hour:
            return f"N {camp} ORDER"
        if hour == c.accrued and c.exhausted:
            return f"N {camp} REQ"
        self._accrue(c, hour)
        cap = c.avail
        if hour <= 5 and c.daily >= 1000000:
            cap = cap // 2
        granted = min(req, cap)
        c.avail -= granted
        c.spent += granted
        c.grants[hour] += granted
        if req == cap:
            c.exhausted = True
        self.requests += 1
        return f"P {granted}"

    def _trueup(self, tokens: list[str]) -> str:
        camp = tokens[1] if len(tokens) >= 2 else NO_CAMP
        if len(tokens) < 2:
            return f"N {camp} FMT"
        if not _valid_id(tokens[1]):
            return f"N {camp} FMT"
        c = self._find(tokens[1])
        if c is None:
            return f"N {camp} FMT"
        sl = c.daily // HOURS
        total = sum(min(g, sl) for g in c.grants)
        raw = max(0, c.daily - total)
        cap = c.daily // CARRY_CAP_DIV
        carry = min(raw, cap)
        if raw > cap:
            c.debt += raw - cap
        c.carry = carry
        c.spent = 0
        c.grants = [0] * HOURS
        c.avail = 0
        c.accrued = -1
        self.trueups += 1
        return f"U {total} {carry}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        reply = engine.handle(line)
        if reply:
            replies.append(reply)
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
