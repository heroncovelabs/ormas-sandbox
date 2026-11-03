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
        self.st: dict[str, dict] = {}
        self.clock = 0
        self.slot: dict = {}
        self.u_epoch = 0
        self.ent: dict = {}
        self.lead_in: dict = {}
        self.lead_pend: dict = {}
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

    def _vkey(self, n):
        p = self.st[n]
        eff = self.build[n] + p["settled"] + p["h"] - p["l"] + p["adj"]
        if p["home"] and self.c_u >= 4 and p["ht"] >= 2:
            eff -= 1000
        cur = self.where[n]
        if cur is not None and self.fields[cur]["reopened"]:
            return (-eff, 1, -self.pseq[n])
        return (-eff, 0, self.pseq[n])

    def _dev(self, n):
        p = self.st[n]
        return p["settled"] + p["h"] - p["l"] + p["adj"]

    def _ukey(self, n):
        return (-(self.build[n] + self.st[n]["lt"]), self.pseq[n])

    def _enter(self, f, fname, pony):
        idx = self.slot.get((pony, fname))
        if idx is None or idx >= len(f["roster"]):
            f["roster"].append(pony)
        else:
            f["roster"].insert(idx, pony)

    def _leave(self, fname, pony):
        r = self.fields[fname]["roster"]
        self.slot[(pony, fname)] = r.index(pony)
        r.remove(pony)

    def _touch(self, fname):
        self.clock += 1
        self.fields[fname]["touch"] = self.clock

    def _open_fields(self) -> list[dict]:
        return [self.fields[n] for n in self.forder if not self.fields[n]["resting"]]

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
            self.st[parts[1]] = {"h": 0, "l": 0, "settled": 0, "adj": 0, "lt": 0, "home": False, "ht": 0}
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
                "touch": 0,
                "had": False,
                "reopened": False,
                "displaced": [],
            }
            self.forder.append(parts[1])
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
            self._enter(f, parts[2], parts[1])
            self.where[parts[1]] = parts[2]
            self._touch(parts[2])
            self.ent[(parts[1], parts[2])] = self.ent.get((parts[1], parts[2]), 0) + 1
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
            self._leave(cur, parts[1])
            self.where[parts[1]] = None
            self.st[parts[1]]["h"] += 1
            self.st[parts[1]]["ht"] += 1
            for d in (self.lead_in, self.lead_pend):
                for key in [k for k in d if k[0] == parts[1]]:
                    del d[key]
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
            self._leave(cur, parts[1])
            self._enter(f, parts[2], parts[1])
            self.where[parts[1]] = parts[2]
            self.ent[(parts[1], parts[2])] = self.ent.get((parts[1], parts[2]), 0) + 1
            self.st[parts[1]]["l"] += 1
            self.st[parts[1]]["lt"] += 1
            key = (parts[1], parts[2])
            self.lead_pend[key] = self.lead_pend.get(key, 0) + 1
            self._touch(parts[2])
            self.c_l += 1
            self._emit("OK")
            return

        if kind == "V":
            if len(parts) != 1:
                self._reject("FORM")
                return
            outs = [n for n in self.porder if self.where[n] is not None]
            outs.sort(key=self._vkey)
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
            self.u_epoch = 0
            self.shift_count += 1
            waking = [
                n for n in self.forder
                if self.fields[n]["resting"]
                and self.shift_count
                >= self.fields[n]["rest_shift"] + (1 if self.fields[n]["had"] else 2)
            ]
            for name in waking:
                self.fields[name]["resting"] = False
                self.fields[name]["reopened"] = True
                self._emit(f"WAKE {name}")
            for name in waking:
                wf = self.fields[name]
                for pony in wf["displaced"]:
                    cur = self.where[pony]
                    if (
                        self.ent.get((pony, name), 0) >= 3
                        and cur is not None
                        and cur != name
                        and len(wf["roster"]) < wf["span"]
                    ):
                        self._leave(cur, pony)
                        self._enter(wf, name, pony)
                        self.where[pony] = name
                        self._touch(name)
                        self.c_l += 1
                        self._emit(f"PUT {pony} {name}")
                wf["displaced"] = []
            for name in waking:
                if self.fields[name]["had"]:
                    self.forder.remove(name)
                    self.forder.append(name)
            # rest the next open field in stake-order rotation
            open_fields = self._open_fields()
            rested = None
            if open_fields:
                rested = min(open_fields, key=lambda f: (f["touch"], f["seq"]))
                rname = next(n for n in self.forder if self.fields[n] is rested)
                self._emit(f"REST {rname}")
                rested["resting"] = True
                rested["rest_shift"] = self.shift_count
                rested["had"] = bool(rested["roster"])
                # leads into a field that now rests lose their standing
                for pony in self.porder:
                    if self.where[pony] == rname:
                        continue
                    k = self.lead_in.pop((pony, rname), 0)
                    if k:
                        self.st[pony]["settled"] -= 3 * k
            # move its ponies out, roster order, most room first
            if rested is not None and rested["roster"]:
                rname = next(n for n in self.forder if self.fields[n] is rested)
                for pony in sorted(rested["roster"], key=self._vkey):
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
                        self.st[pony]["home"] = True
                        self._emit(f"BARN {pony}")
                    else:
                        self.fields[dest]["roster"].append(pony)
                        self.where[pony] = dest
                        self._touch(dest)
                        rested["displaced"].append(pony)
                        self._emit(f"PUT {pony} {dest}")
            # list the open fields in stake order
            listed = [n for n in self.forder if not self.fields[n]["resting"]]
            self._emit(f"SHIFT {len(listed)}")
            for name in listed:
                self._emit(f"F {name}")
            for n in self.porder:
                p = self.st[n]
                p["settled"] += -p["h"] + 2 * p["l"]
                p["h"] = 0
                p["l"] = 0
                p["adj"] = 0
            for key, k in self.lead_pend.items():
                self.lead_in[key] = self.lead_in.get(key, 0) + k
            self.lead_pend = {}
            return

        if kind == "U":
            if len(parts) != 1:
                self._reject("FORM")
                return
            self.c_u += 1
            ranked = sorted(
                self.porder,
                key=lambda n: (self.where[n] is None,) + self._ukey(n),
            )
            for n in self.porder:
                d = self._dev(n)
                if d > 0:
                    nd = d // 2 if self.u_epoch > 0 else (d + 1) // 2
                elif d < 0:
                    m = -d
                    if self.u_epoch > 0:
                        nd = -(m // 2 + 1)
                    else:
                        nd = 0 if m == 1 else -((m + 1) // 2)
                else:
                    nd = 0
                self.st[n]["adj"] += nd - d
            self.u_epoch += 1
            self._emit(f"MUSTER {len(ranked)}")
            for name in ranked:
                self._emit(f"P {name}")
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
