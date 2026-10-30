"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys


def _job_ok(name: str) -> bool:
    return 1 <= len(name) <= 8 and name.isascii() and name.isalnum()


def _fields(line: str) -> list[str]:
    """Reproduce the reference scanner's four bounded string fields."""
    parts = []
    pos = 0
    for width in (7, 63, 63, 127):
        while pos < len(line) and line[pos] in " \t\r\n\v\f":
            pos += 1
        start = pos
        while (
            pos < len(line)
            and pos - start < width
            and line[pos] not in " \t\r\n\v\f"
        ):
            pos += 1
        if pos == start:
            break
        parts.append(line[start:pos])
    return parts


class Job:
    __slots__ = (
        "name", "prio", "deps", "defseq", "executed", "resolved_deps",
        "retries", "retryseq",
    )

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.prio = prio
        self.deps = deps
        self.defseq = defseq
        self.executed = False
        self.resolved_deps: list[Job | None] | None = None
        self.retries = 0
        self.retryseq = 0

    def schedule_key(self) -> tuple[int, int, int]:
        priority = max(1, self.prio - 7 * max(0, self.retries - 1))
        if self.retries == 0 and len(self.deps) >= 2 and self.prio % 10 == 0:
            priority += 1
        return (-priority, -self.retryseq, self.defseq)


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
        # Cache the complete first lookup, including missing dependencies.
        if j.resolved_deps is None:
            j.resolved_deps = [self.by_name.get(d) for d in j.deps]
        return all(k is not None and k.executed for k in j.resolved_deps)

    def handle(self, line: str) -> None:
        line = line.split("\0", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            return
        parts = _fields(line)
        kind = parts[0] if parts else ""
        job = parts[1] if len(parts) > 1 else ""
        job_ok = _job_ok(job)
        echo = job if job_ok else "????????"
        key = job.upper()

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
                    if not _job_ok(part) or part.upper() == key:
                        bad = True
                        break
                    part = part.upper()
                    if part in deps:
                        continue
                    if len(deps) == 32:
                        bad = True
                        break
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
            executed_this = 0
            while True:
                best: Job | None = None
                for j in self.jobs:
                    if j.executed:
                        continue
                    if not self._deps_ready(j):
                        continue
                    if best is None or j.schedule_key() < best.schedule_key():
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
            j = self.by_name.get(key)
            if j is None or not j.executed:
                self._reject(j.name if j is not None else job, "STATE")
                return
            invalidated = {key}
            changed = True
            while changed:
                changed = False
                for k in self.jobs:
                    name = k.name.upper()
                    if not k.executed or name in invalidated:
                        continue
                    if any(d in invalidated for d in k.deps):
                        invalidated.add(name)
                        changed = True
            # Tear down the whole closure in definition order. Each teardown
            # gets a new retry stamp; the newest stamp wins equal-priority ties.
            for k in self.jobs:
                if k.name.upper() in invalidated:
                    k.executed = False
                    k.retries += 1
                    k.retryseq = self.retry_next
                    self.retry_next += 1
            self.c_fail += 1
            self._emit(f"OK {len(invalidated)}")
            return

        self._reject(echo, "FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_def} {self.c_exec} {self.c_fail} {self.c_rej}")


def main() -> None:
    engine = Engine()
    # fgets in the reference consumes at most 511 bytes per command chunk.
    for line in iter(lambda: sys.stdin.buffer.readline(511), b""):
        engine.handle(line.decode("latin-1"))
    engine.finish()


if __name__ == "__main__":
    main()
