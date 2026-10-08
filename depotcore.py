"""DepotCore parcel-depot engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One depot
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

BAY, SHELVED, OUT, LEDGE, GONE = 0, 1, 2, 3, 4
CAP = 4


class Parcel:
    __slots__ = ("pid", "sender", "lane", "heft", "credit", "score", "state", "stamp", "bounced")

    def __init__(self, pid, sender, lane, heft):
        self.pid = pid
        self.sender = sender
        self.lane = lane
        self.heft = heft
        self.credit = 0
        self.score = heft
        self.state = BAY
        self.stamp = 0
        self.bounced = False


class Engine:
    def __init__(self, out=None):
        self.out = out if out is not None else sys.stdout
        self.senders: dict[str, bool] = {}  # registration order
        self.lane_order: list[str] = []
        self.shelves: dict[str, list[str]] = {}
        self.parcels: dict[str, Parcel] = {}
        self.bay: list[str] = []    # lodge order
        self.ledge: list[str] = []  # bounce order
        self.stamp_next = 1
        self.lodges: dict[str, int] = {}
        self.returns: dict[str, int] = {}
        self.wear: dict[str, int] = {}
        self.ledger: list[tuple] = []
        self.window: list[str] = []
        self.window_open = False
        self.window_bounced: set[str] = set()
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
        return 1 <= len(tok) <= 8 and tok.isascii() and tok.isalnum()

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
        self.lodges[s] = 0
        self.returns[s] = 0
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
        self.wear[l] = 0
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
        if not (htok.isascii() and htok.isdigit() and 1 <= len(htok) <= 3):
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
        self.lodges[s] += 1
        p.credit = (15 if self.lodges[s] % 3 == 0 else 0) - (
            10 if self.returns[s] >= 2 else 0
        )
        self.parcels[pid] = p
        self.ledger.append(("LODGE", pid))
        self.bay.append(pid)
        self.c_lodge += 1
        self._emit(f"OK {pid}")

    @staticmethod
    def _adjust(heft, delta):
        if not delta:
            return heft
        score = max(1, heft + delta)
        # The legacy adjustment skips exact multiples of twenty-five.
        return score + (score % 25 == 0)

    def _place(self, p):
        if p.state == BAY:
            p.score = self._adjust(p.heft, p.credit - 5 * self.wear[p.lane])
        p.stamp = self.stamp_next
        self.stamp_next += 1
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
        for l in self.lane_order:
            for pid in self.bay:
                p = self.parcels[pid]
                if p.lane == l:
                    self._place(p)
                    n += 1
        self.bay = []
        self.ledge = []
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
        capacity = 3 if self.wear[l] >= 3 else CAP
        self.wear[l] += 1
        if not shelf:
            self._emit(f"VOID {l}")
            return
        self._close_window()
        manifest = []
        k = min(capacity, len(shelf))
        for _ in range(k):
            best = min((self.parcels[pid] for pid in shelf),
                       key=lambda p: (-p.score, p.stamp))
            shelf.remove(best.pid)
            best.state = OUT
            manifest.append(best.pid)
            self._emit(f"OUT {best.pid}")
        self.ledger.append(("ROUND", l, tuple(manifest)))
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
        p.score = self._adjust(p.score, -40)
        self.returns[p.sender] += 1
        self.ledger.append(("BOUNCE", pid))
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
        p.state = GONE
        self.c_waive += 1
        self._emit(f"OK {pid}")

    def _cmd_square(self, parts):
        if len(parts) != 1:
            self._emit("R SQUARE FMT")
            return
        self.c_square += 1
        self._close_window()
        self.bay = []
        self.ledge = []
        self.shelves = {l: [] for l in self.lane_order}
        self.wear = {l: 0 for l in self.lane_order}
        replay_stamp = 1
        bases = {}
        lodges = dict.fromkeys(self.senders, 0)
        for p in self.parcels.values():
            p.state = GONE
            p.bounced = False
        # Only lodgements, actual departures and returns enter the recount.
        # Shelving, empty rounds and withdrawals have no ledger counterpart.
        for event in self.ledger:
            kind = event[0]
            if kind == "ROUND":
                _, l, manifest = event
                self.wear[l] += 1
                for pid in manifest:
                    p = self.parcels[pid]
                    self.shelves[l].remove(pid)
                    p.state = GONE
                continue
            p = self.parcels[event[1]]
            if kind == "LODGE":
                lodges[p.sender] += 1
                credit = 15 if lodges[p.sender] % 3 == 0 else 0
                p.score = self._adjust(p.heft, credit - 5 * self.wear[p.lane])
                bases[p.pid] = p.score
            else:
                # Replay returns derive from the lodged score, not the score
                # of the previous dispatch: repeated sag is lost on recount.
                p.score = self._adjust(bases[p.pid], -40)
                p.bounced = True
            p.state = SHELVED
            p.stamp = replay_stamp
            replay_stamp += 1
            self.shelves[p.lane].append(p.pid)
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
            self.parcels[pid]
            for l in self.lane_order
            for pid in self.shelves[l]
            if self.parcels[pid].sender == s
        ]
        joined = " ".join(p.pid for p in held)
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
