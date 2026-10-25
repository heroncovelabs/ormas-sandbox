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
        # Names of folded bins, permanently reserved for the session.
        self.reserved: set[str] = set()
        # Ordering uses historical measures, independently of physical sacks.
        self.history: dict[str, dict] = {}
        self.season_deposits = 0
        self.season_draws = 0
        self.last_favor = None
        self.last_tail = None
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
            self.history[parts[1]] = {
                "measure": 0,
                "draws": set(),
                "deposit": False,
                "move": False,
                "seasons": [],
            }
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
                "drawn": False,
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
            b["holds"][parts[1]] = b["holds"].get(parts[1], 0) + count
            if parts[1] not in b["holders"]:
                b["holders"].append(parts[1])
            b["keep"] += count
            h = self.history[parts[1]]
            h["measure"] += count
            h["deposit"] = True
            self.season_deposits += 1
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
            b["holds"][parts[1]] -= count
            b["keep"] -= count + count // 6
            b["drawn"] = True
            h = self.history[parts[1]]
            h["measure"] -= count + count // 4
            h["draws"].add(b["seq"])
            self.season_draws += 1
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
            src["holds"][parts[1]] -= count
            self._drop_if_empty(src, parts[1])
            dst["total"] += count
            dst["holds"][parts[1]] = dst["holds"].get(parts[1], 0) + count
            if parts[1] not in dst["holders"]:
                dst["holders"].append(parts[1])
            src["keep"] -= count
            dst["keep"] += count - count // 10
            h = self.history[parts[1]]
            h["measure"] -= 1
            h["move"] = True
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

            favor = None
            tail = None
            if order:
                name, head = order[0]
                if (head["total"] == head["cap"] and len(head["holders"]) >= 2
                        and self.season_deposits and not self.season_draws):
                    favor = head["seq"]
                name, last = order[-1]
                tail = (last["seq"], last["total"])

            for name, b in order:
                if name not in self.bins:
                    continue
                if b["total"] == 0:
                    self._emit(f"SHUT {name}")
                    del self.bins[name]
                elif 2 * b["keep"] < b["total"]:
                    for dest_name, dest in order:
                        if (dest_name == name or dest_name not in self.bins
                                or 2 * dest["keep"] < dest["total"]
                                or dest["total"] + b["total"] > dest["cap"]):
                            continue
                        for member in b["holders"]:
                            count = b["holds"][member]
                            if count:
                                dest["holds"][member] = dest["holds"].get(member, 0) + count
                                if member not in dest["holders"]:
                                    dest["holders"].append(member)
                        dest["total"] += b["total"]
                        dest["keep"] += b["total"]
                        self._emit(f"FOLD {name} {dest_name}")
                        del self.bins[name]
                        self.reserved.add(name)
                        self.c_m += 1
                        break

            for b in self.bins.values():
                if b["keep"] > 0:
                    b["keep"] -= b["keep"] // 16
                if tail == self.last_tail and tail == (b["seq"], b["total"]) and b["drawn"]:
                    b["keep"] = b["total"]
                if favor == self.last_favor and favor == b["seq"]:
                    for member in b["holders"]:
                        if b["holds"][member]:
                            self.history[member]["measure"] += self.shares[member]
                b["drawn"] = False
            self.last_favor = favor
            self.last_tail = tail
            self.season_deposits = 0
            self.season_draws = 0
            for h in self.history.values():
                h["seasons"].insert(0, (h["draws"], h["deposit"], h["move"]))
                del h["seasons"][3:]
                h["draws"] = set()
                h["deposit"] = False
                h["move"] = False
            return

        if kind == "Y":
            if len(parts) != 1:
                self._reject("FMT")
                return
            self.c_y += 1
            for name, h in self.history.items():
                seasons = h["seasons"]
                if (len(seasons) == 3 and all(not p and not m for _, p, m in seasons)
                        and set.intersection(*(d for d, _, _ in seasons))):
                    h["measure"] -= 2 * self.shares[name]
            for b in self.bins.values():
                b["keep"] += (b["total"] - b["keep"]) // 2
            ranked = sorted(
                self.morder, key=lambda n: (-self.history[n]["measure"], self.mseq[n])
            )
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
