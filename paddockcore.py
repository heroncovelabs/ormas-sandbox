"""PaddockCore pony field co-op engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, a
trailer at end of input. Format reference: ``docs/SPEC.md`` (mind the
drift warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys


SINK = 15


def _id_ok(s: str) -> bool:
    return 1 <= len(s) <= 8 and s.isalnum() and s.isascii()


def _num_ok(s: str, maxlen: int) -> bool:
    return 1 <= len(s) <= maxlen and s.isdigit() and s.isascii()


class Engine:
    def __init__(self, out=None):
        self.out = out if out is not None else sys.stdout
        self.build: dict[str, int] = {}
        self.pseq: dict[str, int] = {}
        self.porder: list[str] = []
        self.where: dict[str, str | None] = {}
        self.fields: dict[str, dict] = {}
        self.forder: list[str] = []
        # per-pony standing adjustments (turnout V/U ranking)
        self.hp: dict[str, int] = {}
        self.lp: dict[str, int] = {}
        self.settled: dict[str, int] = {}
        # per (pony, field) first-entry stamp and turnout count
        self.barnb: dict[str, int] = {}
        self.sink: dict[str, int] = {}
        self.hc: dict[str, int] = {}
        self.lc: dict[str, int] = {}
        self.slot: dict[tuple, int] = {}
        self.stamp: dict[tuple, int] = {}
        self.gcount: dict[tuple, int] = {}
        self.clock = 0
        self.lorder: list[str] = []
        self.next_pseq = 0
        self.next_fseq = 0
        self.shift_count = 0
        self.c_n = 0
        self.c_f = 0
        self.c_g = 0
        self.c_h = 0
        self.c_l = 0
        self.c_s = 0
        self.c_u = 0

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, code: str) -> None:
        self._emit(f"NAY {code}")

    def _open_fields(self) -> list[dict]:
        return [self.fields[n] for n in self.forder if not self.fields[n]["resting"]]

    def _eff(self, n: str) -> int:
        return (self.build[n] + self.settled[n] + self.hp[n] - self.lp[n]
                - self.sink[n])

    def _add(self, pony: str, fname: str) -> None:
        f = self.fields[fname]
        self.clock += 1
        f["touch"] = self.clock
        key = (pony, fname)
        if key not in self.stamp:
            self.stamp[key] = self.clock
        idx = self.slot.get(key)
        if idx is None or idx >= len(f["roster"]):
            f["roster"].append(pony)
        else:
            f["roster"].insert(idx, pony)
        self.where[pony] = fname

    def _settle(self) -> None:
        for n in self.porder:
            self.settled[n] += 2 * self.lp[n] - self.hp[n]
            self.hp[n] = 0
            self.lp[n] = 0

    def _leave(self, pony: str, fname: str) -> None:
        roster = self.fields[fname]["roster"]
        self.slot[(pony, fname)] = roster.index(pony)
        roster.remove(pony)

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]

        if kind == "N":
            if len(parts) != 3 or not _id_ok(parts[1]) or not _num_ok(parts[2], 2):
                self._reject("FORM")
                return
            val = int(parts[2])
            if not 1 <= val <= 99:
                self._reject("WIDE")
                return
            if parts[1] in self.build:
                self._reject("TWICE")
                return
            self.next_pseq += 1
            self.build[parts[1]] = val
            self.pseq[parts[1]] = self.next_pseq
            self.porder.append(parts[1])
            self.where[parts[1]] = None
            self.hp[parts[1]] = 0
            self.lp[parts[1]] = 0
            self.barnb[parts[1]] = 0
            self.sink[parts[1]] = 0
            self.hc[parts[1]] = 0
            self.lc[parts[1]] = 0
            self.settled[parts[1]] = 0
            self.c_n += 1
            self._emit(f"OK {len(self.porder)}")
            return

        if kind == "F":
            if len(parts) != 3 or not _id_ok(parts[1]) or not _num_ok(parts[2], 2):
                self._reject("FORM")
                return
            span = int(parts[2])
            if not 1 <= span <= 99:
                self._reject("WIDE")
                return
            if parts[1] in self.fields:
                self._reject("TWICE")
                return
            self.next_fseq += 1
            self.fields[parts[1]] = {
                "span": span,
                "seq": self.next_fseq,
                "roster": [],
                "resting": False,
                "rest_shift": 0,
                "gap": 2,
                "touch": 0,
                "reopened": False,
            }
            self.forder.append(parts[1])
            self.lorder.append(parts[1])
            self.c_f += 1
            self._emit(f"OK {len(self.forder)}")
            return

        if kind == "G":
            if len(parts) != 3 or not _id_ok(parts[1]) or not _id_ok(parts[2]):
                self._reject("FORM")
                return
            if parts[1] not in self.build:
                self._reject("STRAY")
                return
            if parts[2] not in self.fields:
                self._reject("WILD")
                return
            f = self.fields[parts[2]]
            if f["resting"]:
                self._reject("SHUT")
                return
            if self.where[parts[1]] is not None:
                self._reject("TWICE")
                return
            if len(f["roster"]) >= f["span"]:
                self._reject("CRAM")
                return
            self._add(parts[1], parts[2])
            self.barnb[parts[1]] = 0
            key = (parts[1], parts[2])
            self.gcount[key] = self.gcount.get(key, 0) + 1
            self.c_g += 1
            self._emit("OK")
            return

        if kind == "H":
            if len(parts) != 2 or not _id_ok(parts[1]):
                self._reject("FORM")
                return
            if parts[1] not in self.build:
                self._reject("STRAY")
                return
            cur = self.where[parts[1]]
            if cur is None:
                self._reject("IDLE")
                return
            self._leave(parts[1], cur)
            self.where[parts[1]] = None
            self.hp[parts[1]] += 1
            self.hc[parts[1]] += 1
            self.c_h += 1
            self._emit("OK")
            return

        if kind == "L":
            if len(parts) != 3 or not _id_ok(parts[1]) or not _id_ok(parts[2]):
                self._reject("FORM")
                return
            if parts[1] not in self.build:
                self._reject("STRAY")
                return
            if parts[2] not in self.fields:
                self._reject("WILD")
                return
            f = self.fields[parts[2]]
            if f["resting"]:
                self._reject("SHUT")
                return
            cur = self.where[parts[1]]
            if cur is None:
                self._reject("IDLE")
                return
            if cur == parts[2]:
                self._reject("TWICE")
                return
            if len(f["roster"]) >= f["span"]:
                self._reject("CRAM")
                return
            self._leave(parts[1], cur)
            self._add(parts[1], parts[2])
            self.lp[parts[1]] += 1
            self.lc[parts[1]] += 1
            self.c_l += 1
            self._emit("OK")
            return

        if kind == "V":
            if len(parts) != 1:
                self._reject("FORM")
                return
            outs = [n for n in self.porder if self.where[n] is not None]
            outs.sort(key=lambda n: (-self._eff(n), self.pseq[n]))
            i = 0
            while i < len(outs):
                j = i
                while j < len(outs) and self._eff(outs[j]) == self._eff(outs[i]):
                    j += 1
                for fname in {self.where[n] for n in outs[i:j]}:
                    if not self.fields[fname]["reopened"]:
                        continue
                    idxs = [k for k in range(i, j) if self.where[outs[k]] == fname]
                    names = [outs[k] for k in idxs][::-1]
                    for k, n in zip(idxs, names):
                        outs[k] = n
                i = j
            self._emit(f"OUT {len(outs)}")
            for name in outs:
                self._emit(f"P {name}")
            return

        if kind == "R":
            if len(parts) != 2 or not _id_ok(parts[1]):
                self._reject("FORM")
                return
            if parts[1] not in self.fields:
                self._reject("WILD")
                return
            f = self.fields[parts[1]]
            self._emit(f"FLD {parts[1]} {len(f['roster'])}")
            for name in f["roster"]:
                self._emit(f"P {name}")
            return

        if kind == "S":
            if len(parts) != 1:
                self._reject("FORM")
                return
            self.c_s += 1
            self.shift_count += 1
            # rested fields wake (one shift sooner if they rested occupied)
            waking = [
                n for n in self.forder
                if self.fields[n]["resting"]
                and self.shift_count >= self.fields[n]["rest_shift"] + self.fields[n]["gap"]
            ]
            waking.sort(key=lambda n: self.fields[n]["seq"])
            for name in waking:
                self.fields[name]["resting"] = False
                self.fields[name]["reopened"] = True
                if self.fields[name]["gap"] == 1:
                    self.lorder.remove(name)
                    self.lorder.append(name)
                self._emit(f"WAKE {name}")
                self._home(name)
            # rest the open field longest untouched
            open_fields = self._open_fields()
            rested = None
            if open_fields:
                rested = min(open_fields, key=lambda f: (f["touch"], f["seq"]))
                rname = next(n for n in self.forder if self.fields[n] is rested)
                self._emit(f"REST {rname}")
                rested["resting"] = True
                rested["rest_shift"] = self.shift_count
                rested["gap"] = 1 if rested["roster"] else 2
            # move its ponies out, roster order, most room first
            if rested is not None and rested["roster"]:
                rname = next(n for n in self.forder if self.fields[n] is rested)
                order = sorted(
                    rested["roster"], key=lambda n: (-self._eff(n), self.pseq[n])
                )
                self._settle()
                for pony in order:
                    dest = None
                    dest_key = None
                    for n in self.forder:
                        f = self.fields[n]
                        if f["resting"] or n == rname:
                            continue
                        room = f["span"] - len(f["roster"])
                        if room <= 0:
                            continue
                        key = (-room, f["seq"])
                        if dest is None or key < dest_key:
                            dest, dest_key = n, key
                    self._leave(pony, rname)
                    if dest is None:
                        self.where[pony] = None
                        self.hp[pony] += 1
                        self.barnb[pony] = 1
                        self._emit(f"BARN {pony}")
                    else:
                        self._add(pony, dest)
                        self._emit(f"PUT {pony} {dest}")
            # list the open fields in stake order
            listed = [n for n in self.lorder if not self.fields[n]["resting"]]
            self._emit(f"SHIFT {len(listed)}")
            for name in listed:
                self._emit(f"F {name}")
            if not (rested is not None and rested["roster"]):
                self._settle()
            return

        if kind == "U":
            if len(parts) != 1:
                self._reject("FORM")
                return
            self.c_u += 1
            ranked = sorted(
                self.porder,
                key=lambda n: (
                    self.where[n] is None,
                    -(self.build[n] + self.lp[n] - self.hp[n] + self.barnb[n]),
                    self.pseq[n],
                ),
            )
            for n in self.porder:
                if self.where[n] is None and self.barnb[n]:
                    self.sink[n] += SINK
                self.settled[n] = 0
                self.hp[n] = 0
                self.lp[n] = 0
            self._emit(f"MUSTER {len(ranked)}")
            for name in ranked:
                self._emit(f"P {name}")
            return

        self._reject("FORM")

    def _home(self, fname: str) -> None:
        """Ponies turned out here often enough return when it reopens."""
        f = self.fields[fname]
        for pony in self.porder:
            if self.gcount.get((pony, fname), 0) < 3:
                continue
            cur = self.where[pony]
            if cur is None or cur == fname:
                continue
            if len(f["roster"]) >= f["span"]:
                continue
            self._leave(pony, cur)
            self._add(pony, fname)
            self.c_l += 1
            self._emit(f"PUT {pony} {fname}")

    def finish(self) -> None:
        self._emit(
            f"END {self.c_n} {self.c_f} {self.c_g} {self.c_h} "
            f"{self.c_l} {self.c_s} {self.c_u}"
        )


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
