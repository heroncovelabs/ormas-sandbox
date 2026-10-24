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
        self.retired_bins: set[str] = set()
        self.favor: dict[str, int] = {}
        self.toll: dict[str, int] = {}
        self.activity: dict[str, int] = {}
        self.draw_bin: dict[str, str] = {}
        self.draw_streak: dict[str, int] = {}
        self.previous_draw_bin: dict[str, str] = {}
        self.season_activity = 0
        self.previous_quiet = False
        self.previous_top = None
        self.previous_tail = None
        self.next_mseq = 0
        self.next_bseq = 0
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

    def _drop_if_empty(self, b: dict, name: str) -> None:
        if b["holds"].get(name, 0) == 0:
            b["holds"].pop(name, None)
            if name in b["holders"]:
                b["holders"].remove(name)

    def _held_total(self, name: str) -> int:
        return sum(b["holds"].get(name, 0) for b in self.bins.values())

    @staticmethod
    def _quotient(value: int, divisor: int) -> int:
        # The ledger's signed integer divisions truncate toward zero.
        return value // divisor if value >= 0 else -((-value) // divisor)

    def _book_activity(self, member: str, flag: int) -> None:
        self.activity[member] = self.activity.get(member, 0) | flag
        self.season_activity |= flag

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
            self.morder.append(parts[1])
            self.favor[parts[1]] = 0
            self.draw_streak[parts[1]] = 0
            self.toll[parts[1]] = 0
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
            if parts[1] in self.bins or parts[1] in self.retired_bins:
                self._reject("DUP")
                return
            self.next_bseq += 1
            self.bins[parts[1]] = {
                "cap": cap,
                "seq": self.next_bseq,
                "total": 0,
                "keep": 0,
                "activity": 0,
                "last_total": None,
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
            b["activity"] |= 1
            self._book_activity(parts[1], 1)
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
            b["activity"] |= 2
            self._book_activity(parts[1], 2)
            self.draw_bin[parts[1]] = parts[2]
            self.toll[parts[1]] += count // 4
            b["holds"][parts[1]] -= count
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
            src["activity"] |= 4
            dst["activity"] |= 4
            self._book_activity(parts[1], 4)
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
            order = sorted(
                self.bins.items(),
                key=lambda kv: (-kv[1]["keep"], len(kv[1]["holders"]), kv[1]["seq"]),
            )
            self._emit(f"TURN {len(order)}")
            for name, _ in order:
                self._emit(f"B {name}")

            quiet = self.season_activity == 1
            if order:
                top_name, top = order[0]
                if (quiet and self.previous_quiet and top_name == self.previous_top
                        and top["total"] == top["cap"] and len(top["holders"]) >= 2):
                    for member in top["holders"]:
                        if top["holds"][member] > 0:
                            self.favor[member] += self.shares[member]
                tail_name, tail = order[-1]
                if (tail_name == self.previous_tail
                        and tail["total"] == tail["last_total"]
                        and tail["activity"] == 3):
                    tail["keep"] = tail["total"]
                self.previous_top = top_name
                self.previous_tail = tail_name
            else:
                self.previous_top = self.previous_tail = None
            self.previous_quiet = quiet

            for member in self.morder:
                if self.activity.get(member, 0) == 2:
                    location = self.draw_bin[member]
                    if self.previous_draw_bin.get(member) == location:
                        self.draw_streak[member] += 1
                    else:
                        self.draw_streak[member] = 1
                    self.previous_draw_bin[member] = location
                else:
                    self.draw_streak[member] = 0
                    self.previous_draw_bin.pop(member, None)
            self.activity.clear()
            self.draw_bin.clear()
            self.season_activity = 0

            # A sagging bin can fold into the first healthy bin with room.
            # Folding carries actual sacks, rather than the source's score.
            for name, src in order:
                if name not in self.bins:
                    continue
                if src["total"] == 0:
                    self._emit(f"SHUT {name}")
                    del self.bins[name]
                    continue
                if 2 * src["keep"] >= src["total"]:
                    continue
                for dst_name, dst in order:
                    if (dst_name == name or dst_name not in self.bins
                            or 2 * dst["keep"] < dst["total"]
                            or dst["total"] + src["total"] > dst["cap"]):
                        continue
                    for member in src["holders"]:
                        count = src["holds"][member]
                        if count:
                            if member not in dst["holders"]:
                                dst["holders"].append(member)
                            dst["holds"][member] = dst["holds"].get(member, 0) + count
                    dst["total"] += src["total"]
                    dst["keep"] += src["total"]
                    del self.bins[name]
                    self.retired_bins.add(name)
                    self.c_m += 1
                    self._emit(f"FOLD {name} {dst_name}")
                    break
            for name, b in order:
                if name not in self.bins:
                    continue
                b["keep"] -= self._quotient(b["keep"], 16)
                b["last_total"] = b["total"]
                b["activity"] = 0
            return

        if kind == "Y":
            if len(parts) != 1:
                self._reject("FMT")
                return
            self.c_y += 1
            ranked = sorted(
                self.morder,
                key=lambda n: (
                    -(self._held_total(n) - self.toll[n] + self.favor[n]
                      - (2 * self.shares[n] if self.draw_streak[n] >= 3 else 0)),
                    self.mseq[n],
                ),
            )
            self._emit(f"RECK {len(ranked)}")
            for name in ranked:
                self._emit(f"S {name}")
            for b in self.bins.values():
                b["keep"] += (b["total"] - b["keep"]) // 2
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
