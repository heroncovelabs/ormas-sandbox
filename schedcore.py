"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behaviors that differ from the spec and are reproduced here:

- Job ids are case-insensitive (the first definition's spelling is kept
  and echoed for ``DUP``/``STATE`` rejects and ``E`` lines).
- Repeated dependency entries are accepted.
- Tokens past the ones a command takes are ignored.
- A job with a dependency that is undefined at a ``G`` is blocked for
  the rest of the session.
- Every teardown (``F`` invalidation) stamps the job; among equal
  priorities the most recently torn-down job runs first, fresh jobs
  last (in definition order).
- From its second teardown on, a job loses 7 priority per extra
  teardown (floor 1).
- A never-torn-down job with 2+ distinct dependencies and a priority
  divisible by 10 wins ties against other jobs of the same priority.
"""

from __future__ import annotations

import sys

PENALTY = 7


class Job:
    __slots__ = (
        "name", "prio", "deps", "defseq", "executed",
        "stale", "teardowns", "stamp", "fanin",
    )

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.prio = prio
        self.deps = deps  # lowercased keys
        self.defseq = defseq
        self.executed = False
        self.stale = False
        self.teardowns = 0
        self.stamp = 0
        self.fanin = len(set(deps)) >= 2

    def key(self) -> tuple:
        eff = self.prio
        if self.teardowns > 1:
            eff = max(1, eff - PENALTY * (self.teardowns - 1))
        boost = 1 if (self.teardowns == 0 and self.fanin and self.prio % 10 == 0) else 0
        return (eff, boost, self.stamp, -self.defseq)


class Engine:
    def __init__(self, out=None):
        self.jobs: list[Job] = []
        self.by_name: dict[str, Job] = {}
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
            k = self.by_name.get(d)
            if k is None or not k.executed:
                return False
        return True

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        job = parts[1] if len(parts) > 1 else ""
        job_ok = 1 <= len(job) <= 8 and job.isalnum() and job.isascii()
        echo = job if job_ok else "????????"
        jkey = job.lower()

        if kind == "J":
            if len(parts) < 4 or not job_ok:
                self._reject(echo, "FMT")
                return
            ptok = parts[2]
            if not (ptok.isdigit() and ptok.isascii() and 1 <= len(ptok) <= 2):
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
                    if not (1 <= len(part) <= 8 and part.isalnum() and part.isascii()):
                        bad = True
                        break
                    if part.lower() == jkey:  # self-dependency
                        bad = True
                        break
                    deps.append(part.lower())
            if bad:
                self._reject(job, "DEPS")
                return
            existing = self.by_name.get(jkey)
            if existing is not None:
                self._reject(existing.name, "DUP")
                return
            j = Job(job, prio, deps, self.def_next)
            self.def_next += 1
            self.jobs.append(j)
            self.by_name[jkey] = j
            self.c_def += 1
            self._emit(f"OK {self.c_def}")
            return

        if kind == "G":
            for j in self.jobs:
                if not j.executed and not j.stale:
                    if any(d not in self.by_name for d in j.deps):
                        j.stale = True
            executed_this = 0
            while True:
                best: Job | None = None
                best_key = None
                for j in self.jobs:
                    if j.executed or j.stale:
                        continue
                    if not self._deps_ready(j):
                        continue
                    k = j.key()
                    if best is None or k > best_key:
                        best, best_key = j, k
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
            j = self.by_name.get(jkey)
            if j is None or not j.executed:
                self._reject(j.name if j is not None else job, "STATE")
                return
            invalidated = set()

            def teardown(k: Job) -> None:
                k.executed = False
                k.teardowns += 1
                k.stamp = self.stamp_next
                self.stamp_next += 1
                invalidated.add(self.by_name_key(k))

            teardown(j)
            count = 1
            changed = True
            while changed:
                changed = False
                for k in self.jobs:
                    if not k.executed:
                        continue
                    if any(d in invalidated for d in k.deps):
                        teardown(k)
                        count += 1
                        changed = True
            self.c_fail += 1
            self._emit(f"OK {count}")
            return

        self._reject(echo, "FMT")

    @staticmethod
    def by_name_key(j: Job) -> str:
        return j.name.lower()

    def finish(self) -> None:
        self._emit(f"X {self.c_def} {self.c_exec} {self.c_fail} {self.c_rej}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
