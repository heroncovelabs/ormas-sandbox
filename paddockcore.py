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
        self.clock = 0
        self.ponies: dict[str, dict] = {}
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

    def _touch(self, *names: str) -> None:
        self.clock += 1
        for name in names:
            self.fields[name]["touch"] = self.clock

    def _arrive(self, pony: str, name: str, automatic: bool = False) -> None:
        f = self.fields[name]
        if automatic and pony in f["slots"]:
            f["slots"].remove(pony)
        if pony not in f["slots"]:
            if len(f["slots"]) >= f["span"]:
                vacant = next(n for n in f["slots"] if self.where[n] != name)
                f["slots"].remove(vacant)
            f["slots"].append(pony)
        if not automatic:
            f["visits"][pony] = f["visits"].get(pony, 0) + 1
        if automatic:
            f["temporary"].add(pony)
        else:
            f["temporary"].discard(pony)
        self.where[pony] = name
        f["roster"] = [n for n in f["slots"] if self.where[n] == name]

    def _depart(self, pony: str, name: str) -> None:
        f = self.fields[name]
        f["roster"].remove(pony)
        if pony in f["temporary"]:
            f["temporary"].remove(pony)
            f["slots"].remove(pony)

    def _seat_key(self, pony: str) -> tuple:
        cur = self.where[pony]
        epoch = self.fields[cur]["epoch"] if cur is not None else 0
        return (epoch, -self.pseq[pony] if epoch % 2 else self.pseq[pony])

    def _out_key(self, pony: str) -> tuple:
        return (-self.build[pony] - self.ponies[pony]["heat"],
                *self._seat_key(pony))

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
            self.ponies[parts[1]] = {
                "g": 0, "h": 0, "l": 0, "heat": 0,
                "home": None, "gate": 0, "stranded": False, "missed": 0,
            }
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
                "delay": 2,
                "slots": [],
                "temporary": set(),
                "visits": {},
                "epoch": 0,
                "leads": {},
                "touch": 0,
            }
            self.forder.append(parts[1])
            self._touch(parts[1])
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
            pony = parts[1]
            self._arrive(pony, parts[2])
            self._touch(parts[2])
            p = self.ponies[pony]
            p["g"] += 1
            credit = sum(field["leads"].pop(pony, 0) for field in self.fields.values())
            f["leads"][pony] = p["l"]
            p["heat"] += 1 + 3 * (p["l"] - credit)
            p["home"] = parts[2]
            p["gate"] = 0
            p["stranded"] = False
            p["missed"] = 0
            p["return"] = None
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
            self._depart(parts[1], cur)
            self.where[parts[1]] = None
            p = self.ponies[parts[1]]
            p["h"] += 1
            p["stranded"] = False
            p["return"] = None
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
            self._depart(parts[1], cur)
            self._arrive(parts[1], parts[2])
            self._touch(parts[2])
            p = self.ponies[parts[1]]
            p["l"] += 1
            f["leads"][parts[1]] = f["leads"].get(parts[1], 0) + 1
            p["heat"] -= 1
            p["return"] = None
            self.c_l += 1
            self._emit("OK")
            return

        if kind == "V":
            if len(parts) != 1:
                self._reject("FORM")
                return
            outs = [n for n in self.porder if self.where[n] is not None]
            outs.sort(key=self._out_key)
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
            waking = [n for n in self.forder if self.fields[n]["resting"]
                      and self.shift_count >= self.fields[n]["rest_shift"]
                      + self.fields[n]["delay"]]
            waking.sort(key=lambda n: self.fields[n]["seq"])
            for name in waking:
                f = self.fields[name]
                f["resting"] = False
                f["epoch"] += 1
                self.forder.remove(name)
                self.forder.append(name)
                self._emit(f"WAKE {name}")
                for pony in self.porder:
                    p = self.ponies[pony]
                    cur = self.where[pony]
                    if p.get("return") != name or cur is None or cur == name:
                        continue
                    if len(f["roster"]) >= f["span"]:
                        continue
                    self._depart(pony, cur)
                    self._arrive(pony, name)
                    self._touch(name)
                    p["return"] = None
                    self.c_l += 1
                    self._emit(f"PUT {pony} {name}")
            open_fields = self._open_fields()
            rested = None
            if open_fields:
                rested = min(open_fields, key=lambda f: (f["touch"], f["seq"]))
                rname = next(n for n in self.forder if self.fields[n] is rested)
                self._emit(f"REST {rname}")
                rested["resting"] = True
                rested["rest_shift"] = self.shift_count
                rested["delay"] = 1 if rested["roster"] else 2
                if not rested["roster"]:
                    rested["leads"].clear()

            # move its ponies out, roster order, most room first
            if rested is not None and rested["roster"]:
                rname = next(n for n in self.forder if self.fields[n] is rested)
                for pony in sorted(rested["roster"], key=self._out_key):
                    dest = None
                    dest_key = None
                    for n in self.forder:
                        f = self.fields[n]
                        if f["resting"] or n == rname:
                            continue
                        room = f["span"] - len(f["roster"])
                        if room <= 0:
                            continue
                        key = (-room, self.forder.index(n))
                        if dest is None or key < dest_key:
                            dest, dest_key = n, key
                    self._depart(pony, rname)
                    p = self.ponies[pony]
                    if dest is None:
                        self.where[pony] = None
                        p["stranded"] = True
                        p["return"] = None
                        self._emit(f"BARN {pony}")
                    else:
                        credit = rested["leads"].pop(pony, 0)
                        df = self.fields[dest]
                        df["leads"][pony] = df["leads"].get(pony, 0) + credit
                        self._arrive(pony, dest, automatic=True)
                        self._touch(dest)
                        p["home"] = dest
                        p["gate"] = 0
                        p["return"] = rname if rested["visits"].get(pony, 0) >= 3 else None
                        self._emit(f"PUT {pony} {dest}")
            for n, p in self.ponies.items():
                credit = sum(f["leads"].get(n, 0) for f in self.fields.values())
                p["heat"] = p["g"] - 2 * p["h"] - p["l"] + 3 * credit
            # Reopened fields move to the end of the field listing.
            listed = [n for n in self.forder if not self.fields[n]["resting"]]
            self._emit(f"SHIFT {len(listed)}")
            for name in listed:
                self._emit(f"F {name}")
            return

        if kind == "U":
            if len(parts) != 1:
                self._reject("FORM")
                return
            self.c_u += 1
            ranked = sorted(self.porder, key=lambda n: (
                self.where[n] is None,
                -self.build[n] - self.ponies[n]["g"]
                + self.ponies[n]["h"] - self.ponies[n]["l"],
                *self._seat_key(n),
            ))
            self._emit(f"MUSTER {len(ranked)}")
            for name in ranked:
                self._emit(f"P {name}")
            for p in self.ponies.values():
                p["heat"] //= 2
                if p["stranded"]:
                    p["missed"] += 1
                    if p["g"] >= 3 and p["missed"] >= 4:
                        p["heat"] -= 200
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
