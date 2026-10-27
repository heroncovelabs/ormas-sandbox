"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behaviors the spec omits or gets wrong, reproduced here:

- Job ids are case-insensitive; the spelling of the first definition is
  the one reported. Duplicate dependency entries are collapsed.
- Commands may carry trailing tokens; they are ignored.
- A job whose dependency is undefined when a ``G`` runs is permanently
  blocked (stale), even if the dependency is defined later.
- Ordering among ready jobs: effective priority (base priority, minus 7
  per teardown beyond the first, floor 1; being invalidated by a
  dependency's failure counts as a teardown), then fan-in boost (a job that
  has never executed, with 2+ distinct deps and a priority that is a
  multiple of 10, wins ties), then most recently torn down first, then
  definition order.
"""

from __future__ import annotations

import sys


class Job:
    __slots__ = ("name", "prio", "deps", "defseq", "executed", "ever_run",
                 "fails", "teardown", "stale")

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.prio = prio
        self.deps = deps  # lowercased keys
        self.defseq = defseq
        self.executed = False
        self.ever_run = False
        self.fails = 0
        self.teardown = 0
        self.stale = False

    def sort_key(self) -> tuple:
        eff = max(1, self.prio - 7 * max(0, self.fails - 1))
        boost = (not self.ever_run and len(self.deps) >= 2
                 and self.prio % 10 == 0)
        return (-eff, 0 if boost else 1, -self.teardown, self.defseq)


class Engine:
    def __init__(self, out=None):
        self.jobs: list[Job] = []
        self.by_name: dict[str, Job] = {}
        self.def_next = 1
        self.teardown_next = 1
        self.c_def = 0
        self.c_exec = 0
        self.c_fail = 0
        self.c_rej = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, echo: str, code: str) -> None:
        self._emit(f"R {echo} {code}")
        self.c_rej += 1

    def _deps_ready(self, j: Job) -> bool:
        if j.stale:
            return False
        for d in j.deps:
            k = self.by_name.get(d)
            if k is None or not k.executed:
                return False
        return True

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()  # whitespace-only lines fall through to FMT
        kind = parts[0] if parts else ""
        job = parts[1] if len(parts) > 1 else ""
        job_ok = 1 <= len(job) <= 8 and job.isascii() and job.isalnum()
        echo = job if job_ok else "????????"
        key = job.lower()

        if kind == "J":
            if len(parts) < 4 or not job_ok:
                self._reject(echo, "FMT")
                return
            ptok = parts[2]
            if not (ptok.isascii() and ptok.isdigit() and 1 <= len(ptok) <= 2):
                self._reject(job, "PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 99:
                self._reject(job, "PRIO")
                return
            dtok = parts[3]
            deps: list[str] = []
            bad = False
            if dtok != "0":
                for part in dtok.split(","):
                    if not (1 <= len(part) <= 8 and part.isascii()
                            and part.isalnum()):
                        bad = True
                        break
                    part = part.lower()
                    if part == key:  # self-dependency
                        bad = True
                        break
                    if part not in deps:
                        deps.append(part)
            if bad:
                self._reject(job, "DEPS")
                return
            if key in self.by_name:
                self._reject(self.by_name[key].name, "DUP")
                return
            j = Job(job, prio, deps, self.def_next)
            self.def_next += 1
            self.jobs.append(j)
            self.by_name[key] = j
            self.c_def += 1
            self._emit(f"OK {self.c_def}")
            return

        if kind == "G":
            for j in self.jobs:
                if not j.executed and any(d not in self.by_name for d in j.deps):
                    j.stale = True
            executed_this = 0
            while True:
                best: Job | None = None
                for j in self.jobs:
                    if j.executed:
                        continue
                    if not self._deps_ready(j):
                        continue
                    if best is None or j.sort_key() < best.sort_key():
                        best = j
                if best is None:
                    break
                best.executed = True
                best.ever_run = True
                self.c_exec += 1
                executed_this += 1
                self._emit(f"E {best.name}")
            blocked = sum(1 for j in self.jobs if not j.executed)
            self._emit(f"GEND {executed_this} {blocked}")
            return

        if kind == "F":
            if len(parts) < 2 or not job_ok:
                self._reject(echo, "FMT")
                return
            j = self.by_name.get(key)
            if j is None or not j.executed:
                self._reject(j.name if j is not None else job, "STATE")
                return
            j.executed = False
            j.fails += 1
            j.teardown = self.teardown_next
            self.teardown_next += 1
            invalidated = {key}
            count = 1
            changed = True
            while changed:
                changed = False
                for k in self.jobs:
                    if not k.executed:
                        continue
                    if any(d in invalidated for d in k.deps):
                        k.executed = False
                        k.fails += 1
                        k.teardown = self.teardown_next
                        self.teardown_next += 1
                        invalidated.add(k.name.lower())
                        count += 1
                        changed = True
            self.c_fail += 1
            self._emit(f"OK {count}")
            return

        self._reject(echo, "FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_def} {self.c_exec} {self.c_fail} {self.c_rej}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
