"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys


class Job:
    __slots__ = (
        "name", "prio", "deps", "defseq", "executed", "resolved",
        "invalidations", "retryseq",
    )

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.prio = prio
        self.deps = deps
        self.defseq = defseq
        self.executed = False
        self.resolved: list[Job | None] | None = None
        self.invalidations = 0
        self.retryseq = 0

    def rank(self) -> tuple[int, int, int]:
        # Every teardown after the first costs seven priority points.
        prio = max(1, self.prio - 7 * max(0, self.invalidations - 1))
        if self.invalidations == 0 and len(self.deps) >= 2 and self.prio % 10 == 0:
            prio += 1
        return prio, self.retryseq, -self.defseq


class Engine:
    def __init__(self, out=None):
        self.jobs: list[Job] = []
        self.by_name: dict[str, Job] = {}
        self.def_next = 1
        self.retry_next = 1
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
        # The first scheduling attempt permanently binds dependency references,
        # including missing jobs. Later definitions leave these bindings intact.
        if j.resolved is None:
            j.resolved = [self.by_name.get(d) for d in j.deps]
        return all(k is not None and k.executed for k in j.resolved)

    def _invalidate(self, j: Job) -> None:
        j.executed = False
        j.invalidations += 1
        j.retryseq = self.retry_next
        self.retry_next += 1

    def handle(self, line: str) -> None:
        parts = re.findall(r"\S+", line, flags=re.ASCII)
        if not parts:
            return
        kind = parts[0]
        job = parts[1] if len(parts) > 1 else ""
        job_ok = 1 <= len(job) <= 8 and job.isascii() and job.isalnum()
        echo = job if job_ok else "????????"

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
                    if not (1 <= len(part) <= 8 and part.isascii() and part.isalnum()):
                        bad = True
                        break
                    part = part.upper()
                    if part == job.upper():  # self-dependency
                        bad = True
                        break
                    if part not in deps:
                        deps.append(part)
            if bad:
                self._reject(job, "DEPS")
                return
            if job.upper() in self.by_name:
                self._reject(self.by_name[job.upper()].name, "DUP")
                return
            j = Job(job, prio, deps, self.def_next)
            self.def_next += 1
            self.jobs.append(j)
            self.by_name[job.upper()] = j
            self.c_def += 1
            self._emit(f"OK {self.c_def}")
            return

        if kind == "G":
            executed_this = 0
            while True:
                best: Job | None = None
                for j in self.jobs:
                    if j.executed:
                        continue
                    if not self._deps_ready(j):
                        continue
                    if best is None or j.rank() > best.rank():
                        best = j
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
            j = self.by_name.get(job.upper())
            if j is None or not j.executed:
                self._reject(j.name if j is not None else job, "STATE")
                return
            self._invalidate(j)
            invalidated = {j.name.upper()}
            count = 1
            changed = True
            while changed:
                changed = False
                for k in self.jobs:
                    if not k.executed:
                        continue
                    if any(d in invalidated for d in k.deps):
                        self._invalidate(k)
                        invalidated.add(k.name.upper())
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
