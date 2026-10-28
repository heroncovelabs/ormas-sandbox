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
        self.adj: dict[str, int] = {}
        self.bins: dict[str, dict] = {}
        self.border: list[str] = []
        self.dead: set[str] = set()
        self.next_mseq = 0
        self.next_bseq = 0
        self.dep_since = 0
        self.draw_since = 0
        self.qs = 0
        self.last_top = None
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

    def _held_total(self, name: str) -> int:
        return sum(b["holds"].get(name, 0) for b in self.bins.values())

    def _draw(self, b: dict, name: str, count: int) -> None:
        b["total"] -= count
        b["holds"][name] -= count
        b["key"] -= count + count // 6
        b["l"] -= count + count // 6
        b["drew"] = True
        self.draw_since += 1
        self.adj[name] -= count // 4

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
            self.adj[parts[1]] = 0
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
            if parts[1] in self.bins or parts[1] in self.dead:
                self._reject("DUP")
                return
            self.next_bseq += 1
            self.bins[parts[1]] = {
                "cap": cap,
                "seq": self.next_bseq,
                "total": 0,
                "key": 0,
                "b": 0,
                "l": 0,
                "holders": [],
                "holds": {},
                "drew": False,
                "deposited": False,
                "dstreak": 0,
                "prev": 0,
            }
            self.border.append(parts[1])
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
            b["key"] += count
            b["b"] += count
            b["l"] += count
            b["deposited"] = True
            self.dep_since += 1
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
            self._draw(b, parts[1], count)
            b["wd"] = True
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
            self._draw(src, parts[1], count)
            src["key"] += count // 6
            src["l"] += count // 6 + count // 8
            self.adj[parts[1]] += count // 4 - 1
            if src["holds"][parts[1]] == 0:
                src["holds"].pop(parts[1])
                src["holders"].remove(parts[1])
            dst["total"] += count
            dst["key"] += count - count // 8
            dst["b"] += count - count // 5
            dst["l"] += count - count // 5
            self.draw_since += 0
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
                self.border,
                key=lambda n: (-self.bins[n]["key"], len(self.bins[n]["holders"]),
                         self.bins[n]["seq"]),
            )
            self.border = order[:]
            self._emit(f"TURN {len(order)}")
            for name in order:
                self._emit(f"B {name}")
            top = order[0] if order else None
            quiet = self.dep_since > 0 and self.draw_since == 0
            if quiet:
                self.qs += 1
            elif self.draw_since:
                self.qs = 0
            if (quiet and self.qs >= 2 and top is not None
                    and top == self.last_top
                    and self.bins[top]["total"] == self.bins[top]["cap"]):
                for h in self.bins[top]["holders"]:
                    self.adj[h] += self.shares[h]
            self.last_top = top
            fold_line = None
            if len(order) > 1 and self.bins[order[0]]["total"] > 0:
                for idx, name in enumerate(order[1:], 1):
                    s = self.bins[name]
                    if not (s.get("wd") and 0 < s["total"]
                            and (s["l"] + 1) * 8 <= s["b"]):
                        continue
                    dname = next(
                        (n for n in order[:idx]
                         if self.bins[n]["total"] > 0
                         and self.bins[n]["total"] + s["total"] <= self.bins[n]["cap"]),
                        None,
                    )
                    if dname is not None:
                        dst = self.bins[dname]
                        fold_line = f"FOLD {name} {dname}"
                        dst["total"] += s["total"]
                        dst["key"] += s["total"]
                        dst["b"] += s["total"]
                        dst["l"] += s["total"]
                        for h in s["holders"]:
                            dst["holds"][h] = dst["holds"].get(h, 0) + s["holds"][h]
                            if h not in dst["holders"]:
                                dst["holders"].append(h)
                        del self.bins[name]
                        self.border.remove(name)
                        self.dead.add(name)
                        self.c_m += 1
                        order = [n for n in order if n != name]
                        break
            for name in order:
                b = self.bins[name]
                was_dep = b["deposited"]
                was_drew = b.get("wd", False)
                if b["drew"] and not b["deposited"]:
                    b["dstreak"] += 1
                else:
                    b["dstreak"] = 0
                if b["dstreak"] == 3:
                    for h in b["holders"]:
                        self.adj[h] -= 2 * self.shares[h]
                b["wd"] = False
                b["drew"] = False
                b["deposited"] = False
                d = b["key"] >> 4
                b["b"] -= 2 * d
                b["l"] -= 2 * d
                if b["total"] == b["prev"] and (was_dep or was_drew):
                    b["key"] = b["total"]
                else:
                    b["key"] -= d
                b["prev"] = b["total"]
            self.dep_since = 0
            self.draw_since = 0
            for name in order:
                if self.bins[name]["total"] == 0:
                    self._emit(f"SHUT {name}")
                    del self.bins[name]
                    self.border.remove(name)
            if fold_line:
                self._emit(fold_line)
            return

        if kind == "Y":
            if len(parts) != 1:
                self._reject("FMT")
                return
            self.c_y += 1
            for b in self.bins.values():
                delta = (b["total"] - b["key"]) // 2
                b["key"] += delta
                b["b"] += 2 * delta
                b["l"] += 2 * delta
            ranked = sorted(
                self.morder,
                key=lambda n: (-(self._held_total(n) + self.adj[n]), self.mseq[n]),
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
