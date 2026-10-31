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
        self.reserved: set[str] = set()
        self.measure: dict[str, int] = {}
        self.member_activity: dict[str, dict] = {}
        self.draw_runs: dict[str, tuple[str, int]] = {}
        self.last_head: str | None = None
        self.last_tail: tuple[str, int] | None = None
        self.season_deposits = 0
        self.season_disturbed = False
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

    def _activity(self, name: str) -> dict:
        return self.member_activity.setdefault(name, {"draws": set(), "other": False})

    def _turn(self) -> None:
        order = sorted(
            self.bins.items(),
            key=lambda kv: (-kv[1]["keep"], len(kv[1]["holders"]), kv[1]["seq"]),
        )
        self._emit(f"TURN {len(order)}")
        for name, _ in order:
            self._emit(f"B {name}")

        head = order[0][0] if order else None
        tail = (order[-1][0], order[-1][1]["total"]) if order else None
        if head is not None:
            b = self.bins[head]
            if (head == self.last_head and b["total"] == b["cap"]
                    and len(b["holders"]) >= 2 and self.season_deposits
                    and not self.season_disturbed):
                for member in b["holders"]:
                    self.measure[member] += self.shares[member]

        for member in self.morder:
            activity = self.member_activity.get(member)
            if activity and not activity["other"] and len(activity["draws"]) == 1:
                source = next(iter(activity["draws"]))
                old_source, run = self.draw_runs.get(member, ("", 0))
                run = run + 1 if source == old_source else 1
                self.draw_runs[member] = (source, run)
            else:
                self.draw_runs.pop(member, None)

        for name, b in order:
            if name not in self.bins:
                continue
            if b["total"] == 0:
                self._emit(f"SHUT {name}")
                del self.bins[name]
            elif 2 * b["keep"] < b["total"]:
                for dest_name, dst in order:
                    if (dest_name != name and dest_name in self.bins
                            and 2 * dst["keep"] >= dst["total"]
                            and dst["total"] + b["total"] <= dst["cap"]):
                        dst["total"] += b["total"]
                        dst["keep"] += b["total"]
                        for member in b["holders"]:
                            if b["holds"][member] == 0:
                                continue
                            dst["holds"][member] = (dst["holds"].get(member, 0)
                                                      + b["holds"][member])
                            if member not in dst["holders"]:
                                dst["holders"].append(member)
                        self._emit(f"FOLD {name} {dest_name}")
                        self.reserved.add(name)
                        del self.bins[name]
                        self.c_m += 1
                        break

        for name, b in self.bins.items():
            b["keep"] -= max(0, b["keep"]) // 16
            if (tail == self.last_tail and tail is not None and name == tail[0]
                    and b["deposits"] and b["draws"] and not b["moves"]):
                b["keep"] = b["total"]
            b["deposits"] = b["draws"] = b["moves"] = 0
        self.last_head = (
            head if head is not None and self.bins.get(head, {}).get("total")
            == self.bins.get(head, {}).get("cap") and self.season_deposits
            and not self.season_disturbed else None
        )
        self.last_tail = tail
        self.member_activity.clear()
        self.season_deposits = 0
        self.season_disturbed = False

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
            self.measure[parts[1]] = 0
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
                "deposits": 0,
                "draws": 0,
                "moves": 0,
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
            b["deposits"] += count
            self.measure[parts[1]] += count
            self._activity(parts[1])["other"] = True
            self.season_deposits += 1
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
            b["draws"] += count
            self.measure[parts[1]] -= count + count // 4
            self._activity(parts[1])["draws"].add(parts[2])
            self.season_disturbed = True
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
            dst["keep"] += count - count // 10
            src["moves"] += count
            dst["moves"] += count
            self.measure[parts[1]] -= 1
            self._activity(parts[1])["other"] = True
            src["holds"][parts[1]] -= count
            self._drop_if_empty(src, parts[1])
            dst["total"] += count
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
            for member, (_, run) in self.draw_runs.items():
                if run >= 3:
                    self.measure[member] -= 2 * self.shares[member]
            ranked = sorted(
                self.morder, key=lambda n: (-self.measure[n], self.mseq[n])
            )
            self._emit(f"RECK {len(ranked)}")
            for name in ranked:
                self._emit(f"S {name}")
            for b in self.bins.values():
                b["keep"] = (b["keep"] + b["total"]) // 2
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
