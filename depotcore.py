"""DepotCore parcel-depot engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One depot
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

BAY, SHELVED, OUT, LEDGE, GONE, WAIVED = 0, 1, 2, 3, 4, 5
CAP = 4
WORN_CAP = 3     # round size once a lane has run WORN_AFTER rounds
WORN_AFTER = 3
LIFT = 15        # every LIFT_EVERY-th lodge by a sender
LIFT_EVERY = 3
WEAR = 5         # per round the lane had run when the parcel was lodged
SAG = 40         # per bounce
DISTRUST = 10    # sender already had DISTRUST_AFTER bounces at lodge time
DISTRUST_AFTER = 2
NOTCH = 25       # an adjusted score landing on a multiple of this gains 1


class Parcel:
    __slots__ = (
        "pid", "sender", "lane", "heft", "state", "stamp", "bounced",
        "lift", "wear", "distrust", "bounces", "seq", "worn", "lodge_runs",
        "put", "lodge_seq",
    )

    def __init__(self, pid, sender, lane, heft):
        self.pid = pid
        self.sender = sender
        self.lane = lane
        self.heft = heft
        self.state = BAY
        self.stamp = 0
        self.bounced = False
        self.lift = False
        self.wear = 0
        self.distrust = False
        self.bounces = 0
        self.seq = 0  # ledger position of the latest LODGE/BOUNCE event
        self.worn = False  # wear is fixed at the first shelving
        self.lodge_runs = 0
        self.put = False  # ever placed by SHELVE
        self.lodge_seq = 0

    def score(self):
        adj = (
            (LIFT if self.lift else 0)
            - WEAR * self.wear
            - (DISTRUST if self.distrust else 0)
            - SAG * self.bounces
        )
        if not (self.lift or self.wear or self.distrust or self.bounces):
            return self.heft
        s = self.heft + adj
        if s < 1:
            s = 1
        if s % NOTCH == 0:
            s += 1
        return s


class Engine:
    def __init__(self, out=None):
        self.out = out if out is not None else sys.stdout
        self.senders: dict[str, bool] = {}  # registration order
        self.lane_order: list[str] = []
        self.shelves: dict[str, list[str]] = {}
        self.parcels: dict[str, Parcel] = {}
        self.bay: list[str] = []    # lodge order
        self.ledge: list[str] = []  # bounce order
        self.stamp_next = 0
        self.seq_next = 1
        self.window: list[str] = []
        self.window_open = False
        self.window_bounced: set[str] = set()
        self.lodges_by: dict[str, int] = {}
        self.bounces_by: dict[str, int] = {}
        self.lane_rounds: dict[str, int] = {}   # VOID included
        self.lane_runs: dict[str, int] = {}     # departed rounds only
        self.c_reg = 0
        self.c_lane = 0
        self.c_lodge = 0
        self.c_round = 0
        self.c_bounce = 0
        self.c_waive = 0
        self.c_square = 0

    def _emit(self, line):
        self.out.write(line + "\n")

    @staticmethod
    def _tok_ok(tok):
        return 1 <= len(tok) <= 8 and tok.isalnum()

    def _close_window(self):
        for pid in self.window:
            p = self.parcels[pid]
            if p.state == OUT:
                p.state = GONE
        self.window = []
        self.window_open = False
        self.window_bounced = set()

    def handle(self, line):
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        if kind == "REG":
            self._cmd_reg(parts)
        elif kind == "LANE":
            self._cmd_lane(parts)
        elif kind == "LODGE":
            self._cmd_lodge(parts)
        elif kind == "SHELVE":
            self._cmd_shelve(parts)
        elif kind == "ROUND":
            self._cmd_round(parts)
        elif kind == "BOUNCE":
            self._cmd_bounce(parts)
        elif kind == "WAIVE":
            self._cmd_waive(parts)
        elif kind == "SQUARE":
            self._cmd_square(parts)
        elif kind == "LIST":
            self._cmd_list(parts)
        elif kind == "HELD":
            self._cmd_held(parts)
        elif kind == "ROLL":
            self._cmd_roll(parts)
        else:
            self._emit(f"R {kind} FMT")

    def _cmd_reg(self, parts):
        if len(parts) != 2:
            self._emit("R REG FMT")
            return
        s = parts[1]
        if not self._tok_ok(s):
            self._emit(f"R {s} FMT")
            return
        if s in self.senders:
            self._emit(f"R {s} DUP")
            return
        self.senders[s] = True
        self.c_reg += 1
        self._emit(f"OK {s}")

    def _cmd_lane(self, parts):
        if len(parts) != 2:
            self._emit("R LANE FMT")
            return
        l = parts[1]
        if not self._tok_ok(l):
            self._emit(f"R {l} FMT")
            return
        if l in self.shelves:
            self._emit(f"R {l} DUP")
            return
        self.shelves[l] = []
        self.lane_rounds[l] = 0
        self.lane_runs[l] = 0
        self.lane_order.append(l)
        self.c_lane += 1
        self._emit(f"OK {l}")

    def _cmd_lodge(self, parts):
        if len(parts) != 5:
            self._emit("R LODGE FMT")
            return
        s, pid, l, htok = parts[1], parts[2], parts[3], parts[4]
        for tok in (s, pid, l):
            if not self._tok_ok(tok):
                self._emit(f"R {tok} FMT")
                return
        if not (htok.isdigit() and 1 <= len(htok) <= 3):
            self._emit(f"R {htok} HEFT")
            return
        heft = int(htok)
        if not 1 <= heft <= 999:
            self._emit(f"R {htok} HEFT")
            return
        if s not in self.senders:
            self._emit(f"R {s} WHO")
            return
        if l not in self.shelves:
            self._emit(f"R {l} DEST")
            return
        if pid in self.parcels:
            self._emit(f"R {pid} DUP")
            return
        p = Parcel(pid, s, l, heft)
        n = self.lodges_by.get(s, 0) + 1
        self.lodges_by[s] = n
        p.lift = n % LIFT_EVERY == 0
        p.lodge_runs = self.lane_runs[l]
        p.distrust = self.bounces_by.get(s, 0) >= DISTRUST_AFTER
        p.seq = p.lodge_seq = self.seq_next
        self.seq_next += 1
        self.parcels[pid] = p
        self.bay.append(pid)
        self.c_lodge += 1
        self._emit(f"OK {pid}")

    def _place(self, p):
        p.stamp = self.stamp_next
        self.stamp_next += 1
        if not p.worn:
            p.wear = self.lane_rounds[p.lane]
            p.worn = True
        p.put = True
        p.state = SHELVED
        self.shelves[p.lane].append(p.pid)
        self._emit(f"PUT {p.pid} {p.lane}")

    def _cmd_shelve(self, parts):
        if len(parts) != 1:
            self._emit("R SHELVE FMT")
            return
        n = 0
        for pid in self.ledge:
            self._place(self.parcels[pid])
            n += 1
        self.ledge = []
        for l in self.lane_order:
            for pid in self.bay:
                p = self.parcels[pid]
                if p.lane == l:
                    self._place(p)
                    n += 1
        self.bay = []
        self._emit(f"OK {n}")

    def _cmd_round(self, parts):
        if len(parts) != 2:
            self._emit("R ROUND FMT")
            return
        l = parts[1]
        if not self._tok_ok(l):
            self._emit(f"R {l} FMT")
            return
        if l not in self.shelves:
            self._emit(f"R {l} DEST")
            return
        shelf = self.shelves[l]
        self.c_round += 1
        prior = self.lane_rounds[l]
        self.lane_rounds[l] += 1
        if not shelf:
            self._emit(f"VOID {l}")
            return
        self.lane_runs[l] += 1
        self._close_window()
        manifest = []
        cap = WORN_CAP if prior >= WORN_AFTER else CAP
        k = min(cap, len(shelf))
        for _ in range(k):
            best = None
            best_score = 0
            for pid in shelf:
                p = self.parcels[pid]
                sc = p.score()
                if (
                    best is None
                    or sc > best_score
                    or (sc == best_score and p.stamp < best.stamp)
                ):
                    best = p
                    best_score = sc
            shelf.remove(best.pid)
            best.state = OUT
            manifest.append(best.pid)
            self._emit(f"OUT {best.pid}")
        self.window = manifest
        self.window_open = True
        self.window_bounced = set()
        self._emit(f"RAN {l} {k}")

    def _cmd_bounce(self, parts):
        if len(parts) != 2:
            self._emit("R BOUNCE FMT")
            return
        pid = parts[1]
        if not self._tok_ok(pid):
            self._emit(f"R {pid} FMT")
            return
        if (
            pid not in self.parcels
            or not self.window_open
            or pid not in self.window
            or pid in self.window_bounced
        ):
            self._emit(f"R {pid} STATE")
            return
        p = self.parcels[pid]
        self.window_bounced.add(pid)
        p.state = LEDGE
        p.bounced = True
        p.bounces += 1
        p.seq = self.seq_next
        self.seq_next += 1
        self.bounces_by[p.sender] = self.bounces_by.get(p.sender, 0) + 1
        self.ledge.append(pid)
        self.c_bounce += 1
        self._emit(f"OK {pid}")

    def _cmd_waive(self, parts):
        if len(parts) != 2:
            self._emit("R WAIVE FMT")
            return
        pid = parts[1]
        if not self._tok_ok(pid):
            self._emit(f"R {pid} FMT")
            return
        p = self.parcels.get(pid)
        if p is None or p.state not in (BAY, SHELVED):
            self._emit(f"R {pid} STATE")
            return
        if p.state == BAY:
            self.bay.remove(pid)
        else:
            self.shelves[p.lane].remove(pid)
        p.state = WAIVED
        self.c_waive += 1
        self._emit(f"OK {pid}")

    def _cmd_square(self, parts):
        if len(parts) != 1:
            self._emit("R SQUARE FMT")
            return
        self.c_square += 1
        # The recount re-derives every lane from the ledger: anything lodged
        # and not delivered is shelved again (bay, ledge, and withdrawn
        # parcels alike), VOID rounds drop out of the lane's history, and
        # the return window closes.
        self._close_window()
        for l in self.lane_order:
            self.shelves[l] = []
        # The ledger only knows whether (and last when) a parcel bounced,
        # not how often; distrust is replayed against that.
        bounced = [p for p in self.parcels.values() if p.bounces]
        placed = 0
        for p in sorted(self.parcels.values(), key=lambda p: p.seq):
            if p.state in (BAY, SHELVED, LEDGE, WAIVED):
                if p.put:
                    placed += 1
                p.state = SHELVED
                p.bounces = min(p.bounces, 1)
                p.wear = p.lodge_runs
                p.worn = True
                prior = sum(
                    1 for b in bounced if b.sender == p.sender and b.seq < p.lodge_seq
                )
                p.distrust = prior >= DISTRUST_AFTER
                self.shelves[p.lane].append(p.pid)
        # Rebuilt parcels are restamped 0.. in ledger order; the arrival
        # counter restarts at the count of rebuilt parcels that SHELVE ever
        # placed, so later arrivals may tie or predate rebuilt ones.
        rebuilt = [p for p in self.parcels.values() if p.state == SHELVED]
        rebuilt.sort(key=lambda p: p.seq)
        for i, p in enumerate(rebuilt):
            p.stamp = i
        self.stamp_next = placed
        self.bay = []
        self.ledge = []
        for l in self.lane_order:
            self.lane_rounds[l] = self.lane_runs[l]
        for l in self.lane_order:
            names = " ".join(self.shelves[l])
            self._emit(f"SQ {l} {names}" if names else f"SQ {l}")
        self._emit(f"OK {len(self.lane_order)}")

    def _cmd_list(self, parts):
        if len(parts) != 2:
            self._emit("R LIST FMT")
            return
        l = parts[1]
        if not self._tok_ok(l):
            self._emit(f"R {l} FMT")
            return
        if l not in self.shelves:
            self._emit(f"R {l} DEST")
            return
        names = " ".join(self.shelves[l])
        self._emit(f"SHELF {l} {names}" if names else f"SHELF {l}")

    def _cmd_held(self, parts):
        if len(parts) != 2:
            self._emit("R HELD FMT")
            return
        s = parts[1]
        if not self._tok_ok(s):
            self._emit(f"R {s} FMT")
            return
        if s not in self.senders:
            self._emit(f"R {s} WHO")
            return
        held = [
            pid
            for l in self.lane_order
            for pid in self.shelves[l]
            if self.parcels[pid].sender == s
        ]
        joined = " ".join(held)
        self._emit(f"FOR {s} {joined}" if joined else f"FOR {s}")

    def _cmd_roll(self, parts):
        if len(parts) != 1:
            self._emit("R ROLL FMT")
            return
        snds = " ".join(self.senders)
        self._emit(f"SND {snds}" if snds else "SND")
        lns = " ".join(self.lane_order)
        self._emit(f"LNS {lns}" if lns else "LNS")

    def finish(self):
        self._emit(
            f"X {self.c_reg} {self.c_lane} {self.c_lodge}"
            f" {self.c_round} {self.c_bounce} {self.c_waive} {self.c_square}"
        )


def main():
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
