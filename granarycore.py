"""GranaryCore co-op ledger engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, a
trailer at end of input. Format reference: ``docs/SPEC.md`` (mind the
drift warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys


def _id_ok(s: str) -> bool:
    return 1 <= len(s) <= 8 and s.isalnum() and s.isascii()


def _num_ok(s: str, maxlen: int) -> bool:
    return 1 <= len(s) <= maxlen and s.isdigit() and s.isascii()


class Engine:
    def __init__(self, out=None):
        self.out = out if out is not None else sys.stdout
        self.shares: dict[str, int] = {}
        self.mseq: dict[str, int] = {}
        self.morder: list[str] = []
        self.bins: dict[str, dict] = {}
        self.next_mseq = 0
        self.next_bseq = 0
        self.reserved: set[str] = set()
        self.toll: dict[str, int] = {}
        self.favor: dict[str, int] = {}
        self.season_put = False
        self.season_draw = False
        self.last_head = None
        self.last_tail = None
        self.c_j = 0
        self.c_o = 0
        self.c_p = 0
        self.c_w = 0
        self.c_m = 0
        self.c_t = 0
        self.c_y = 0

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, code: str) -> None:
        self._emit(f"R {code}")

    def _drop_holding_if_empty(self, b: dict, name: str) -> None:
        # Physical holding only; roster membership is kept (W retains the slot).
        if b["holds"].get(name, 0) == 0:
            b["holds"].pop(name, None)

    def _drop_if_empty(self, b: dict, name: str) -> None:
        # Holding and roster removal together (used when M moves final sacks out).
        if b["holds"].get(name, 0) == 0:
            b["holds"].pop(name, None)
            if name in b["holders"]:
                b["holders"].remove(name)

    def _held_total(self, name: str) -> int:
        return sum(b["holds"].get(name, 0) for b in self.bins.values())

    def _measure(self, name: str) -> int:
        levy = sum(
            2 * self.shares[name]
            for b in self.bins.values()
            if b["streak"] >= 3 and b["holds"].get(name, 0) > 0
        )
        return self._held_total(name) - self.toll[name] + self.favor[name] - levy

    def _turn(self) -> None:
        # Keep is the engine's retained fill, distinct from the physical sacks.
        order = sorted(
            self.bins.items(),
            key=lambda kv: (-kv[1]["keep"], len(kv[1]["holders"]), kv[1]["seq"]),
        )
        self._emit(f"TURN {len(order)}")
        for name, _ in order:
            self._emit(f"B {name}")

        for name, b in order:
            if name not in self.bins:
                continue
            if b["total"] == 0:
                self._emit(f"SHUT {name}")
                del self.bins[name]
            elif 2 * b["keep"] < b["total"]:
                for target, dst in order:
                    if target == name or target not in self.bins:
                        continue
                    if dst["total"] + b["total"] > dst["cap"]:
                        continue
                    for member in b["holders"]:
                        amount = b["holds"].get(member, 0)
                        if amount:
                            dst["holds"][member] = dst["holds"].get(member, 0) + amount
                            if member not in dst["holders"]:
                                dst["holders"].append(member)
                    dst["total"] += b["total"]
                    dst["keep"] += b["total"]
                    self._emit(f"FOLD {name} {target}")
                    self.reserved.add(name)
                    del self.bins[name]
                    self.c_m += 1
                    break

        for b in self.bins.values():
            if b["keep"] > 0:
                b["keep"] -= b["keep"] // 16
            if b["draw"] and not b["put"] and not b["moved"]:
                b["streak"] += 1
            else:
                b["streak"] = 0

        head = order[0] if order else None
        tail = order[-1] if order else None
        quiet = self.season_put and not self.season_draw
        head_state = None
        if head and head[0] in self.bins:
            b = head[1]
            if quiet and b["total"] == b["cap"] and len(b["holds"]) >= 2:
                head_state = b["seq"]
                if self.last_head == head_state:
                    for member in b["holds"]:
                        self.favor[member] += self.shares[member]
        self.last_head = head_state

        tail_state = None
        if tail and tail[0] in self.bins:
            b = tail[1]
            tail_state = (b["seq"], b["total"])
            if self.last_tail == tail_state and b["draw"]:
                b["keep"] = b["total"]
        self.last_tail = tail_state
        for b in self.bins.values():
            b["put"] = b["draw"] = b["moved"] = False
        self.season_put = self.season_draw = False

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]

        if kind == "J":
            if len(parts) != 3 or not _id_ok(parts[1]) or not _num_ok(parts[2], 2):
                self._reject("FMT")
                return
            val = int(parts[2])
            if not 1 <= val <= 99:
                self._reject("RNG")
                return
            if parts[1] in self.shares:
                self._reject("DUP")
                return
            self.next_mseq += 1
            self.shares[parts[1]] = val
            self.mseq[parts[1]] = self.next_mseq
            self.toll[parts[1]] = 0
            self.favor[parts[1]] = 0
            self.morder.append(parts[1])
            self.c_j += 1
            self._emit(f"OK {len(self.morder)}")
            return

        if kind == "O":
            if len(parts) != 3 or not _id_ok(parts[1]) or not _num_ok(parts[2], 3):
                self._reject("FMT")
                return
            cap = int(parts[2])
            if not 1 <= cap <= 999:
                self._reject("RNG")
                return
            if parts[1] in self.bins or parts[1] in self.reserved:
                self._reject("DUP")
                return
            self.next_bseq += 1
            self.bins[parts[1]] = {
                "cap": cap,
                "seq": self.next_bseq,
                "total": 0,
                "keep": 0,
                "put": False,
                "draw": False,
                "moved": False,
                "streak": 0,
                "holders": [],
                "holds": {},
            }
            self.c_o += 1
            self._emit(f"OK {len(self.bins)}")
            return

        if kind == "P":
            if len(parts) != 4 or not _id_ok(parts[1]) or not _id_ok(parts[2]) \
                    or not _num_ok(parts[3], 3):
                self._reject("FMT")
                return
            count = int(parts[3])
            if not 1 <= count <= 999:
                self._reject("RNG")
                return
            if parts[1] not in self.shares:
                self._reject("WHO")
                return
            if parts[2] not in self.bins:
                self._reject("LOC")
                return
            b = self.bins[parts[2]]
            if b["total"] + count > b["cap"]:
                self._reject("FULL")
                return
            b["total"] += count
            b["keep"] += count
            b["put"] = True
            self.season_put = True
            b["holds"][parts[1]] = b["holds"].get(parts[1], 0) + count
            if parts[1] not in b["holders"]:
                b["holders"].append(parts[1])
            self.c_p += 1
            self._emit("OK")
            return

        if kind == "W":
            if len(parts) != 4 or not _id_ok(parts[1]) or not _id_ok(parts[2]) \
                    or not _num_ok(parts[3], 3):
                self._reject("FMT")
                return
            count = int(parts[3])
            if not 1 <= count <= 999:
                self._reject("RNG")
                return
            if parts[1] not in self.shares:
                self._reject("WHO")
                return
            if parts[2] not in self.bins:
                self._reject("LOC")
                return
            b = self.bins[parts[2]]
            if b["holds"].get(parts[1], 0) < count:
                self._reject("LOW")
                return
            b["total"] -= count
            b["keep"] -= count + count // 6
            b["draw"] = True
            self.season_draw = True
            self.toll[parts[1]] += count // 4
            b["holds"][parts[1]] -= count
            self._drop_holding_if_empty(b, parts[1])
            self.c_w += 1
            self._emit("OK")
            return

        if kind == "M":
            if len(parts) != 5 or not _id_ok(parts[1]) or not _id_ok(parts[2]) \
                    or not _id_ok(parts[3]) or not _num_ok(parts[4], 3):
                self._reject("FMT")
                return
            count = int(parts[4])
            if not 1 <= count <= 999:
                self._reject("RNG")
                return
            if parts[1] not in self.shares:
                self._reject("WHO")
                return
            if parts[2] not in self.bins:
                self._reject("LOC")
                return
            if parts[3] not in self.bins:
                self._reject("LOC")
                return
            if parts[2] == parts[3]:
                self._reject("DUP")
                return
            src = self.bins[parts[2]]
            dst = self.bins[parts[3]]
            if src["holds"].get(parts[1], 0) < count:
                self._reject("LOW")
                return
            if dst["total"] + count > dst["cap"]:
                self._reject("FULL")
                return
            src["total"] -= count
            src["keep"] -= count
            src["moved"] = dst["moved"] = True
            self.toll[parts[1]] += 1
            src["holds"][parts[1]] -= count
            self._drop_if_empty(src, parts[1])
            dst["total"] += count
            dst["keep"] += count - count // 10
            dst["holds"][parts[1]] = dst["holds"].get(parts[1], 0) + count
            if parts[1] not in dst["holders"]:
                dst["holders"].append(parts[1])
            self.c_m += 1
            self._emit("OK")
            return

        if kind == "T":
            if len(parts) != 1:
                self._reject("FMT")
                return
            self.c_t += 1
            self._turn()
            return

        if kind == "Y":
            if len(parts) != 1:
                self._reject("FMT")
                return
            self.c_y += 1
            ranked = sorted(
                self.morder, key=lambda n: (-self._measure(n), self.mseq[n])
            )
            for b in self.bins.values():
                b["keep"] += (b["total"] - b["keep"]) // 2
            self._emit(f"RECK {len(ranked)}")
            for name in ranked:
                self._emit(f"S {name}")
            return

        if kind == "L":
            if len(parts) != 2 or not _id_ok(parts[1]):
                self._reject("FMT")
                return
            if parts[1] not in self.bins:
                self._reject("LOC")
                return
            b = self.bins[parts[1]]
            self._emit(f"HELD {parts[1]} {len(b['holders'])}")
            for name in b["holders"]:
                self._emit(f"H {name}")
            return

        self._reject("FMT")

    def finish(self) -> None:
        self._emit(
            f"Z {self.c_j} {self.c_o} {self.c_p} {self.c_w} "
            f"{self.c_m} {self.c_t} {self.c_y}"
        )


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
