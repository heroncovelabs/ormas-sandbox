"""TallyCore ranked-ballot tally engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads tally
commands on stdin (``C`` registers a candidate, ``V`` casts a ranked
ballot and reports the running leader, ``W`` runs the instant-runoff
recount and starts a new round), writes one reply per command and an
``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the drift
warning at the top of that file; the legacy engine's behavior is the
contract).
"""

from __future__ import annotations

import sys

ID_MAX = 8
CAND_MAX = 64
BALLOT_MAX = 4096
RANK_MAX = 256


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Ranked-ballot tally engine with recount rounds and batch counters."""

    def __init__(self) -> None:
        self.cands: list[str] = []  # registration order
        self.ballots: list[list[int]] = []  # current round, candidate indices
        self.cand_indices: dict[str, int] = {}  # case-folded ids
        self.first_counts: list[int] = []  # running leader, current round only
        self.previous_tallies: list[int] = []  # each candidate's last live tally
        self.total_ballots = 0
        self.rounds = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line == "W":
            return self._recount()
        # The legacy tokenizer uses literal spaces and consumes only the
        # command and its first argument. Tabs remain part of an id.
        if line == "C" or line.startswith("C "):
            return [self._register([t for t in line.split(" ") if t])]
        if line == "V" or line.startswith("V "):
            return [self._vote([t for t in line.split(" ") if t])]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return (
            f"X {len(self.cands)} {self.total_ballots} "
            f"{self.rounds} {self.rejected}"
        )

    def _reject(self, echo: str, code: str) -> str:
        self.rejected += 1
        return f"N {echo} {code}"

    def _register(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        cand = tokens[1]
        if not _valid_id(cand):
            return self._reject("????????", "FMT")
        if self.ballots:
            return self._reject(cand, "LATE")
        key = cand.lower()
        if key not in self.cand_indices:
            if len(self.cands) >= CAND_MAX:
                return self._reject("????????", "FMT")
            self.cand_indices[key] = len(self.cands)
            self.cands.append(cand)
            self.first_counts.append(0)
            self.previous_tallies.append(0)
        return f"OK {len(self.cands)}"

    def _vote(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        entries = tokens[1].split(",")
        if len(entries) > RANK_MAX or any(not _valid_id(e) for e in entries):
            return self._reject("????????", "FMT")
        kept: list[int] = []
        for entry in entries:
            c = self.cand_indices.get(entry.lower())
            if c is None:
                continue
            if c in kept:
                return self._reject(entry, "DUP")
            kept.append(c)
        if not kept:
            return self._reject(entries[0], "CAND")
        if len(self.ballots) >= BALLOT_MAX:
            return self._reject("????????", "FMT")
        self.ballots.append(kept)
        self.total_ballots += 1
        # Running leader: first-choice counts, ties broken by
        # registration order.
        self.first_counts[kept[0]] += 1
        lead = max(range(len(self.cands)), key=lambda c: (self.first_counts[c], -c))
        return f"LEAD {self.cands[lead]}"

    def _tallies(
        self, alive: list[bool], dead: list[bool], carry: list[int]
    ) -> list[int]:
        tally = carry.copy()
        for b, ballot in enumerate(self.ballots):
            if dead[b]:
                continue
            for c in ballot:
                if alive[c]:
                    # A complete ranking earns one extra vote while its
                    # original first choice survives. Transfers count once.
                    tally[c] += 1 + (len(ballot) == len(self.cands) and c == ballot[0])
                    break
        return tally

    def _recount(self) -> list[str]:
        if not self.ballots:
            return [self._reject("????????", "FMT")]
        n = len(self.cands)
        alive = [True] * n
        dead = [False] * len(self.ballots)
        # Carry is fixed throughout this recount. Each candidate retains its
        # final live tally, including carry, for the next round's quarter share.
        carry = [tally // 4 for tally in self.previous_tallies]
        out: list[str] = []
        remaining = n
        while True:
            tally = self._tallies(alive, dead, carry)
            for c in range(n):
                if alive[c]:
                    self.previous_tallies[c] = tally[c]
            if remaining == 1:
                winner = next(c for c in range(n) if alive[c])
                out.append(f"WIN {self.cands[winner]}")
                break
            # Ties eliminate the longest id, then the latest registration.
            victim = min(
                (c for c in range(n) if alive[c]),
                key=lambda c: (tally[c], -len(self.cands[c]), -c),
            )
            out.append(f"ELIM {self.cands[victim]}")
            alive[victim] = False
            # The legacy engine exhausts two-choice ballots with their first
            # choice; longer rankings transfer to their next surviving choice.
            for b, ballot in enumerate(self.ballots):
                if len(ballot) == 2 and ballot[0] == victim:
                    dead[b] = True
            remaining -= 1
        self.ballots = []
        self.first_counts = [0] * n
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
