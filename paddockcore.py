"""PaddockCore pony field co-op engine, Python implementation.

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
        self.build: dict[str, int] = {}
        self.pseq: dict[str, int] = {}
        self.porder: list[str] = []
        self.where: dict[str, str | None] = {}
        self.fields: dict[str, dict] = {}
        self.forder: list[str] = []
        self.next_pseq = 0
        self.next_fseq = 0
        self.shift_count = 0
        self.rota_ptr = 0
        self.c_n = 0
        self.c_f = 0
        self.c_g = 0
        self.c_h = 0
        self.c_l = 0
        self.c_s = 0
        self.c_u = 0
        self.ph: dict[str, int] = {}
        self.pl: dict[str, int] = {}
        self.book: dict[str, int] = {}
        self.tick = 0
        self.ltot: dict[str, int] = {}
        self.gcount: dict[tuple[str, str], int] = {}
        self.lorder: list[str] = []
        self.leads: dict[str, list] = {}
        self.rbarn: dict[str, dict] = {}
        self.madj: dict[str, int] = {}
        self.mcount: dict[str, int] = {}

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, code: str) -> None:
        self._emit(f"NAY {code}")

    def _score(self, n: str) -> int:
        return (
            self.build[n] + self.ph[n] - self.pl[n] + self.book[n]
            + self.madj.get(n, 0)
        )

    @staticmethod
    def _decay(x: int, k: int) -> int:
        if k == 1:
            if x >= 0:
                return (x + 1) // 2
            if x == -1:
                return 0
            return -((1 - x) // 2)
        if x >= 0:
            return x // 2
        if x == -3:
            return -2
        return x

    def _place(self, pony: str, fname: str) -> None:
        f = self.fields[fname]
        if pony not in f["hist"]:
            f["hist"].append(pony)
        pos = f["hist"].index(pony)
        roster = f["roster"]
        idx = len(roster)
        for i, other in enumerate(roster):
            if other in f["hist"] and f["hist"].index(other) > pos:
                idx = i
                break
        roster.insert(idx, pony)

    def _touch(self, name: str) -> None:
        self.fields[name]["touch"] = self.tick

    def _open_fields(self) -> list[dict]:
        return [self.fields[n] for n in self.forder if not self.fields[n]["resting"]]

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        self.tick += 1

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
            self.ph[parts[1]] = 0
            self.pl[parts[1]] = 0
            self.book[parts[1]] = 0
            self.ltot[parts[1]] = 0
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
                "wake_at": 0,
                "touch": self.tick,
                "hist": [],
                "woken": False,
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
            self._place(parts[1], parts[2])
            self.where[parts[1]] = parts[2]
            self._touch(parts[2])
            key = (parts[1], parts[2])
            self.gcount[key] = self.gcount.get(key, 0) + 1
            self.rbarn.pop(parts[1], None)
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
            self.fields[cur]["roster"].remove(parts[1])
            self.where[parts[1]] = None
            self._touch(cur)
            self.ph[parts[1]] += 1
            for rec in self.leads.get(parts[1], []):
                rec[2] = True
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
            self.fields[cur]["roster"].remove(parts[1])
            self._place(parts[1], parts[2])
            self.where[parts[1]] = parts[2]
            self._touch(cur)
            self._touch(parts[2])
            self.pl[parts[1]] += 1
            self.ltot[parts[1]] += 1
            self.leads.setdefault(parts[1], []).append([parts[2], False, False])
            self.c_l += 1
            self._emit("OK")
            return

        if kind == "V":
            if len(parts) != 1:
                self._reject("FORM")
                return
            outs = [n for n in self.porder if self.where[n] is not None]
            def _tie(n: str) -> tuple:
                if self.fields[self.where[n]]["woken"]:
                    return (1, -self.pseq[n])
                return (0, self.pseq[n])

            outs.sort(key=lambda n: (-self._score(n),) + _tie(n))
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
            # rested fields wake at the start of the second shift after
            waking = [
                self.fields[n] for n in self.forder
                if self.fields[n]["resting"]
                and self.shift_count >= self.fields[n]["wake_at"]
            ]
            waking.sort(key=lambda f: f["seq"])
            for f in waking:
                f["resting"] = False
                f["woken"] = True
                name = next(n for n in self.forder if self.fields[n] is f)
                self._emit(f"WAKE {name}")
                self.lorder.remove(name)
                self.lorder.append(name)
                for pony in self.porder:
                    cur = self.where[pony]
                    if (
                        cur is None or cur == name
                        or self.gcount.get((pony, name), 0) < 3
                        or len(f["roster"]) >= f["span"]
                    ):
                        continue
                    self.fields[cur]["roster"].remove(pony)
                    self._place(pony, name)
                    self.where[pony] = name
                    self._touch(name)
                    self.c_l += 1
                    self._emit(f"PUT {pony} {name}")
            # rest the next open field in stake-order rotation
            open_fields = self._open_fields()
            rested = None
            if open_fields:
                rested = min(open_fields, key=lambda f: (f["touch"], f["seq"]))
                self.rota_ptr = rested["seq"]
                rname = next(n for n in self.forder if self.fields[n] is rested)
                self._emit(f"REST {rname}")
                rested["resting"] = True
                rested["rest_shift"] = self.shift_count
                rested["wake_at"] = self.shift_count + (
                    1 if rested["roster"] else 2
                )
                for pony, lst in self.leads.items():
                    for rec in lst:
                        if rec[0] == rname and rec[1] and not rec[2]:
                            rec[2] = True
                            self.book[pony] -= 3
            # move its ponies out, roster order, most room first
            if rested is not None and rested["roster"]:
                rname = next(n for n in self.forder if self.fields[n] is rested)
                movers = sorted(
                    rested["roster"],
                    key=lambda n: (-self._score(n), self.pseq[n]),
                )
                for pony in movers:
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
                    rested["roster"].remove(pony)
                    if dest is None:
                        self.where[pony] = None
                        self.book[pony] += 2
                        self.rbarn[pony] = {"m": 0, "s": False}
                        self._emit(f"BARN {pony}")
                    else:
                        self._place(pony, dest)
                        self.where[pony] = dest
                        self._touch(dest)
                        self._emit(f"PUT {pony} {dest}")
            for n in self.porder:
                self.book[n] += 2 * self.pl[n] - self.ph[n]
                self.ph[n] = 0
                self.pl[n] = 0
                self.madj[n] = 0
                self.mcount[n] = 0
                for rec in self.leads.get(n, []):
                    rec[1] = True
                rb = self.rbarn.get(n)
                if rb is not None and rb["m"] > 0:
                    rb["s"] = True
            if rested is not None:
                rested["hist"] = []
            # list the open fields
            listed = [n for n in self.lorder if not self.fields[n]["resting"]]
            self._emit(f"SHIFT {len(listed)}")
            for name in listed:
                self._emit(f"F {name}")
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
                    -(self.build[n] + self.ltot[n]),
                    self.pseq[n],
                ),
            )
            self._emit(f"MUSTER {len(ranked)}")
            for name in ranked:
                self._emit(f"P {name}")
            for n in self.porder:
                rb = self.rbarn.get(n)
                if rb is not None:
                    rb["m"] += 1
                    dev = self._score(n) - self.build[n]
                    if rb["m"] == 1 and dev < 2:
                        self.book[n] += 1
                    elif rb["m"] >= 4 and rb["s"] and dev <= 1:
                        self.book[n] -= 1000
                        del self.rbarn[n]
                    continue
                self.mcount[n] = self.mcount.get(n, 0) + 1
                cur = self._score(n) - self.build[n]
                new = self._decay(cur, self.mcount[n])
                self.madj[n] = self.madj.get(n, 0) + new - cur
            return

        self._reject("FORM")

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
