"""TallyCore ranked-ballot tally engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads tally
commands on stdin (``C`` registers a candidate, ``V`` casts a ranked
ballot and reports the running leader, ``W`` runs the instant-runoff
recount and starts a new round), writes one reply per command and an
``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the drift
warning at the top of that file; the legacy engine's behavior is the
contract).

Engine behaviors that differ from the spec and are reproduced here:

- Commands are split on single spaces (runs collapse); tokens after the
  argument are ignored for ``C`` and ``V``. ``W`` must be exactly ``W``.
- Candidate ids compare case-insensitively; replies use the spelling
  given at registration.
- Unregistered entries in a ranking are skipped; the ballot is rejected
  with ``CAND`` only when no entry names a registered candidate.
- Recount weights: a ballot ranking every candidate registered when it
  was cast counts double. Ballots ranking exactly two candidates exhaust
  instead of transferring when their first choice is eliminated.
- Momentum: each candidate's tally from the previous recount carries
  into the next round's recount as a bonus of ``tally // 4``.
- Elimination ties eliminate the longest id first, then the last
  registered.
"""

from __future__ import annotations

import sys

ID_MAX = 8
CAND_MAX = 64
BALLOT_MAX = 4096
FULL_RANK_WEIGHT = 2
MOMENTUM_DIV = 4


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Ranked-ballot tally engine with recount rounds and batch counters."""

    def __init__(self) -> None:
        self.cands: list[str] = []  # registration order
        self.keys: list[str] = []  # case-folded ids, parallel to cands
        # current round: (candidate indices, weight)
        self.ballots: list[tuple[list[int], int]] = []
        self.momentum: list[int] = []  # per-candidate bonus for next recount
        self.total_ballots = 0
        self.rounds = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line == "W":
            return self._recount()
        tokens = [t for t in line.split(" ") if t]
        if line.startswith("C ") or line == "C":
            return [self._register(tokens)]
        if line.startswith("V ") or line == "V":
            return [self._vote(tokens)]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return (
            f"X {len(self.cands)} {self.total_ballots} "
            f"{self.rounds} {self.rejected}"
        )

    def _reject(self, echo: str, code: str) -> str:
        self.rejected += 1
        return f"N {echo} {code}"

    def _find(self, token: str) -> int:
        key = token.lower()
        return self.keys.index(key) if key in self.keys else -1

    def _register(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        cand = tokens[1]
        if not _valid_id(cand):
            return self._reject("????????", "FMT")
        if self.ballots:
            return self._reject(cand, "LATE")
        if self._find(cand) < 0:
            if len(self.cands) >= CAND_MAX:
                return self._reject("????????", "FMT")
            self.cands.append(cand)
            self.keys.append(cand.lower())
            self.momentum.append(0)
        return f"OK {len(self.cands)}"

    def _vote(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        entries = tokens[1].split(",")
        if any(not _valid_id(e) for e in entries):
            return self._reject("????????", "FMT")
        kept: list[int] = []
        unknown = ""
        for entry in entries:
            c = self._find(entry)
            if c < 0:
                if not unknown:
                    unknown = entry
                continue
            if c in kept:
                return self._reject(entry, "DUP")
            kept.append(c)
        if not kept:
            return self._reject(unknown, "CAND")
        if len(self.ballots) >= BALLOT_MAX:
            return self._reject("????????", "FMT")
        weight = FULL_RANK_WEIGHT if len(kept) == len(self.cands) else 1
        self.ballots.append((kept, weight))
        self.total_ballots += 1
        # Running leader: unweighted first-choice counts, ties broken by
        # registration order.
        counts = [0] * len(self.cands)
        for ballot, _ in self.ballots:
            counts[ballot[0]] += 1
        lead = max(range(len(self.cands)), key=lambda c: (counts[c], -c))
        return f"LEAD {self.cands[lead]}"

    def _recount(self) -> list[str]:
        if not self.ballots:
            return [self._reject("????????", "FMT")]
        n = len(self.cands)
        alive = [True] * n
        # current holder of each ballot, or -1 once exhausted
        holder = [ballot[0] for ballot, _ in self.ballots]
        out: list[str] = []
        remaining = n
        last = [0] * n
        while True:
            tally = list(self.momentum)
            for b, (ballot, weight) in enumerate(self.ballots):
                if holder[b] == ballot[0]:
                    tally[holder[b]] += weight
                elif holder[b] >= 0:
                    tally[holder[b]] += 1
            for c in range(n):
                if alive[c]:
                    last[c] = tally[c]
            if remaining <= 1:
                break
            victim = -1
            for c in range(n):
                if not alive[c]:
                    continue
                if (
                    victim < 0
                    or tally[c] < tally[victim]
                    or (
                        tally[c] == tally[victim]
                        and len(self.cands[c]) >= len(self.cands[victim])
                    )
                ):
                    victim = c
            out.append(f"ELIM {self.cands[victim]}")
            alive[victim] = False
            remaining -= 1
            for b, (ballot, _) in enumerate(self.ballots):
                if holder[b] != victim:
                    continue
                holder[b] = -1
                if len(ballot) == 2:
                    continue
                for c in ballot:
                    if alive[c]:
                        holder[b] = c
                        break
        winner = next(c for c in range(n) if alive[c])
        out.append(f"WIN {self.cands[winner]}")
        self.momentum = [t // MOMENTUM_DIV for t in last]
        self.ballots = []
        self.rounds += 1
        return out


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
