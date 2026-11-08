"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behaviors that differ from the written spec:

- Job ids are case-insensitive; a job keeps the spelling it was first
  defined with, and that spelling is echoed for ``DUP`` and ``STATE``.
- Extra trailing tokens on any command are ignored.
- Repeated dependency entries are accepted.
- A job whose dependency is undefined when a ``G`` runs is permanently
  blocked, even if the dependency is defined later.
- Every invalidation stamps the job from a session-wide counter; among
  equal effective priorities, higher stamps (more recently torn down)
  go first. Each invalidation beyond the first costs 7 priority points
  (floor 1).
- A never-invalidated job with 2+ distinct dependencies and a priority
  that is a multiple of 10 wins ties against everything else.
"""

from __future__ import annotations

import re
import sys

_ID = re.compile(r"[A-Za-z0-9]{1,8}\Z")
_PRIO = re.compile(r"[0-9]{1,2}\Z")


class Job:
    __slots__ = ("name", "key", "prio", "deps", "defseq", "executed",
                 "stale", "fails", "stamp", "fanin")

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.key = name.upper()
        self.prio = prio
        self.deps = deps  # canonical (upper-cased) ids
        self.defseq = defseq
        self.executed = False
        self.stale = False
        self.fails = 0
        self.stamp = 0
        self.fanin = len(set(deps)) >= 2 and prio % 10 == 0

    def rank(self) -> tuple:
        eff = max(1, self.prio - 7 * (self.fails - 1)) if self.fails > 1 else self.prio
        boost = 1 if (self.fanin and self.fails == 0) else 0
        return (eff, boost, self.stamp, -self.defseq)


class Engine:
    def __init__(self, out=None):
        self.jobs: list[Job] = []
        self.by_key: dict[str, Job] = {}
        self.def_next = 1
        self.stamp_next = 1
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
        for d in j.deps:
            k = self.by_key.get(d)
            if k is None or not k.executed:
                return False
        return True

    def handle(self, line: str) -> None:
        line = line.rstrip("\r\n")
        if not line:
            return
        parts = line.split()
        kind = parts[0] if parts else ""
        job = parts[1] if len(parts) > 1 else ""
        job_ok = bool(_ID.match(job))
        echo = job if job_ok else "????????"

        if kind == "J":
            if len(parts) < 4 or not job_ok:
                self._reject(echo, "FMT")
                return
            ptok = parts[2]
            if not _PRIO.match(ptok):
                self._reject(job, "PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 99:
                self._reject(job, "PRIO")
                return
            key = job.upper()
            dtok = parts[3]
            deps: list[str] = []
            bad = False
            if dtok != "0":
                for part in dtok.split(","):
                    if not _ID.match(part):
                        bad = True
                        break
                    if part.upper() == key:  # self-dependency
                        bad = True
                        break
                    deps.append(part.upper())
            if bad:
                self._reject(job, "DEPS")
                return
            if key in self.by_key:
                self._reject(self.by_key[key].name, "DUP")
                return
            j = Job(job, prio, deps, self.def_next)
            self.def_next += 1
            self.jobs.append(j)
            self.by_key[key] = j
            self.c_def += 1
            self._emit(f"OK {self.c_def}")
            return

        if kind == "G":
            for j in self.jobs:
                if not j.executed and any(d not in self.by_key for d in j.deps):
                    j.stale = True
            executed_this = 0
            while True:
                best: Job | None = None
                best_rank = None
                for j in self.jobs:
                    if j.executed or j.stale:
                        continue
                    if not self._deps_ready(j):
                        continue
                    r = j.rank()
                    if best is None or r > best_rank:
                        best = j
                        best_rank = r
                if best is None:
                    break
                best.executed = True
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
            j = self.by_key.get(job.upper())
            if j is None or not j.executed:
                self._reject(j.name if j is not None else job, "STATE")
                return
            self._invalidate(j)
            invalidated = {j.key}
            count = 1
            changed = True
            while changed:
                changed = False
                for k in self.jobs:
                    if not k.executed:
                        continue
                    if any(d in invalidated for d in k.deps):
                        self._invalidate(k)
                        invalidated.add(k.key)
                        count += 1
                        changed = True
            self.c_fail += 1
            self._emit(f"OK {count}")
            return

        self._reject(echo, "FMT")

    def _invalidate(self, j: Job) -> None:
        j.executed = False
        j.fails += 1
        j.stamp = self.stamp_next
        self.stamp_next += 1

    def finish(self) -> None:
        self._emit(f"X {self.c_def} {self.c_exec} {self.c_fail} {self.c_rej}")


def main() -> None:
    engine = Engine()
    data = sys.stdin.buffer.read().decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for line in lines:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
