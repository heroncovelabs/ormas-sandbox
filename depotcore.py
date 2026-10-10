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
    __slots__ = (
        "pid", "sender", "lane", "heft", "state", "stamp", "bounced",
        "lift", "wear", "recount",
    )

    def __init__(self, pid, sender, lane, heft):
        self.pid = pid
        self.sender = sender
        self.lane = lane
        self.heft = heft
        self.state = BAY
        self.stamp = 0
        self.bounced = 0
        self.lift = 0
        self.wear = 0
        self.recount = False


class Engine:
    def __init__(self, out=None):
        self.out = out if out is not None else sys.stdout
        self.senders: dict[str, bool] = {}  # registration order
        self.lane_order: list[str] = []
        self.shelves: dict[str, list[str]] = {}
        self.parcels: dict[str, Parcel] = {}
        self.bay: list[str] = []    # lodge order
        self.ledge: list[str] = []  # bounce order
        self.lodged: dict[str, int] = {}
        self.returned: dict[str, int] = {}
        self.wear: dict[str, int] = {}
        self.ledger: list[tuple] = []
        self.stamp_next = 1
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
        self.lodged[s] = 0
        self.returned[s] = 0
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
        p = self.parcels[pid] = Parcel(pid, s, l, heft)
        self._rate_lodge(p)
        self.ledger.append(("lodge", pid))
        self.bay.append(pid)
        self.c_lodge += 1
        self._emit(f"OK {pid}")

    def _rate_lodge(self, p):
        # Only accepted lodges advance a sender's three-parcel cadence.
        self.lodged[p.sender] += 1
        p.lift = 15 if self.lodged[p.sender] % 3 == 0 else 0
        if self.returned[p.sender] >= 2:
            p.lift -= 10
        p.wear = self.wear[p.lane] * 5

    @staticmethod
    def _priority(p):
        # Live returns accumulate sag; recount returns carry a single flag.
        sag = 40 if p.recount else 35
        score = max(1, p.heft + p.lift - p.wear - sag * p.bounced)
        if score != p.heft and score % 25 == 0:
            score += 1
        return score

    def _place(self, p, emit=True, keep_stamp=False):
        if emit:
            p.wear = self.wear[p.lane] * 5
        p.recount = not emit
        if not keep_stamp and p.state != LEDGE:
            p.stamp = self.stamp_next
        self.stamp_next += 1
        p.state = SHELVED
        self.shelves[p.lane].append(p.pid)
        if emit:
            self._emit(f"PUT {p.pid} {p.lane}")

    def _cmd_shelve(self, parts):
        if len(parts) != 1:
            self._emit("R SHELVE FMT")
            return
        n = len(self.ledge) + len(self.bay)
        # Returns form one block, then arrivals form lane-open-order blocks.
        for pid in self.ledge:
            self._place(self.parcels[pid])
        for lane in self.lane_order:
            for pid in self.bay:
                p = self.parcels[pid]
                if p.lane == lane:
                    self._place(p)
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
        capacity = CAP if self.wear[l] < 3 else CAP - 1
        self.wear[l] += 1
        self.c_round += 1
        if not shelf:
            self._emit(f"VOID {l}")
            return
        self._close_window()
        manifest = []
        k = min(capacity, len(shelf))
        for _ in range(k):
            best = None
            for pid in shelf:
                p = self.parcels[pid]
                if best is None or (-self._priority(p), p.stamp) < (
                    -self._priority(best), best.stamp
                ):
                    best = p
            shelf.remove(best.pid)
            best.state = OUT
            manifest.append(best.pid)
            self._emit(f"OUT {best.pid}")
        self.ledger.append(("round", l, tuple(manifest)))
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
        p.bounced += 1
        self.returned[p.sender] += 1
        self.ledger.append(("bounce", pid))
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
        self.shelves = {lane: [] for lane in self.lane_order}
        self.wear = {lane: 0 for lane in self.lane_order}
        self.lodged = {sender: 0 for sender in self.senders}
        returned = self.returned
        self.returned = {sender: 0 for sender in self.senders}
        self.bay = []
        self.ledge = []
        # Replay uses its own event clock, not the live shelving clock.
        stamp_next = self.stamp_next
        self.stamp_next = 1
        for p in self.parcels.values():
            p.state = GONE
            p.bounced = 0
        # The recount consumes lodge, departed-round and return events only.
        # Shelving, empty rounds and withdrawals are absent from this ledger.
        for event in self.ledger:
            if event[0] == "lodge":
                p = self.parcels[event[1]]
                self._rate_lodge(p)
                self._place(p, emit=False)
            elif event[0] == "round":
                lane, manifest = event[1:]
                self.wear[lane] += 1
                self.stamp_next += len(manifest)
                for pid in manifest:
                    p = self.parcels[pid]
                    self.shelves[lane].remove(pid)
                    p.state = GONE
            else:
                p = self.parcels[event[1]]
                if not p.bounced:
                    self.returned[p.sender] += 1
                p.bounced = 1
                self._place(p, emit=False, keep_stamp=True)
        self.stamp_next = stamp_next
        self.returned = returned
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
            pid for lane in self.lane_order for pid in self.shelves[lane]
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
