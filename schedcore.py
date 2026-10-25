"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys


_ALNUM = re.compile(r"[A-Za-z0-9]+\Z")


class Job:
    __slots__ = (
        "name", "key", "prio", "deps", "defseq", "executed",
        "failures", "retryseq", "stale",
    )

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.key = name.upper()
        self.prio = prio
        self.deps = deps
        self.defseq = defseq
        self.executed = False
        self.failures = 0
        self.retryseq = 0
        self.stale = False


class Engine:
    def __init__(self, out=None):
        self.jobs: list[Job] = []
        self.by_name: dict[str, Job] = {}
        self.def_next = 1
        self.retry_next = 0
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
        ready = True
        for d in j.deps:
            k = self.by_name.get(d)
            if k is None:
                # A dependency missing when a run examines the job is
                # permanently unresolved, even if it is defined later.
                j.stale = True
                ready = False
            elif not k.executed:
                ready = False
        return ready and not j.stale

    def _priority(self, j: Job) -> int:
        # The first failure only changes retry ordering. Subsequent
        # failures cost seven priority points each, down to priority one.
        prio = max(1, j.prio - 7 * max(0, j.failures - 1))
        if j.retryseq == 0 and len(set(j.deps)) >= 2 and j.prio % 10 == 0:
            prio += 1
        return prio

    def handle(self, line: str) -> None:
        raw = line.rstrip("\r\n").split("\0", 1)[0]
        parts = raw.split()
        if not raw:
            return
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        job = parts[1] if len(parts) > 1 else ""
        job_ok = 1 <= len(job) <= 8 and _ALNUM.fullmatch(job) is not None
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
            key = job.upper()
            if dtok != "0":
                for part in dtok.split(","):
                    if not (1 <= len(part) <= 8 and _ALNUM.fullmatch(part)):
                        bad = True
                        break
                    if part.upper() == key:  # self-dependency
                        bad = True
                        break
                    # Repeated dependencies are accepted; their identity
                    # is case-insensitive just like a job's own identity.
                    deps.append(part.upper())
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
            executed_this = 0
            while True:
                best: Job | None = None
                best_key: tuple[int, int, int] | None = None
                for j in self.jobs:
                    if j.executed:
                        continue
                    if not self._deps_ready(j):
                        continue
                    # Retried jobs precede fresh jobs at equal priority.
                    # Their invalidation sequence is LIFO; fresh jobs FIFO.
                    candidate = (
                        self._priority(j),
                        1 if j.retryseq else 0,
                        j.retryseq if j.retryseq else -j.defseq,
                    )
                    if best_key is None or candidate > best_key:
                        best = j
                        best_key = candidate
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
            if j is None:
                self._reject(job, "STATE")
                return
            if not j.executed:
                self._reject(j.name, "STATE")
                return
            invalidated = {j.key}
            frontier = {j.key}
            count = 0
            while frontier:
                next_frontier: set[str] = set()
                for k in self.jobs:
                    if (
                        k.executed
                        and k.key not in invalidated
                        and any(d in frontier for d in k.deps)
                    ):
                        next_frontier.add(k.key)
                wave = [k for k in self.jobs if k.key in frontier]
                for failed in wave:
                    failed.executed = False
                    failed.failures += 1
                    self.retry_next += 1
                    failed.retryseq = self.retry_next
                    count += 1
                invalidated.update(next_frontier)
                frontier = next_frontier
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
